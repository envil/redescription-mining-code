import multiprocessing, time, socket, uuid, re
from multiprocessing.managers import SyncManager
import queue

try:
    from classWorkInactive import WorkInactive
except ModuleNotFoundError:
    from .classWorkInactive import WorkInactive

import pdb

IP = '127.0.0.1'
PORTNUM = 55444
AUTHKEY = 'sesame'
NUMCLIENT = 0

def make_client_manager(ip, port, authkey):
    class ServerQueueManager(SyncManager):
        pass

    ServerQueueManager.register('get_job_q')
    ServerQueueManager.register('get_ids_d')
    ServerQueueManager.register('get_reconnect_q')

    manager = ServerQueueManager(address=(ip, port), authkey=authkey.encode('ascii'))
    manager.connect()
    return manager

def make_hc_manager(ip, port, authkey):

    class HCQueueManager(SyncManager):
        pass

    HCQueueManager.register('get_job_q', callable=lambda: job_q)
    HCQueueManager.register('get_result_q', callable=lambda: result_q)
    
    manager = HCQueueManager(address=(ip, port), authkey=authkey.encode('ascii'))
    manager.connect()
    return manager

class WorkClient(WorkInactive):

    resumable_tasks = ["mine", "expand"]
    type_messages = {'tracks': None, 'result': None, 
                     'log': "self.updateLog", 'progress': "self.updateProgress",
                     'status': "self.updateStatus", 'error': "self.updateError"}
        
    def __init__(self, ip=IP, portnum=PORTNUM, authkey=AUTHKEY,numclient=NUMCLIENT):
        self.hid = None
        self.map_rids = {}
        if ip == 'localhost':
            ip = IP
        self.work_server = (ip, portnum, authkey, numclient)
        self.shared_job_q = None #queue
        self.ids_d = None #queue
        self.shared_result_q = None #queue
        self.workers = {}
        self.off = {}
        self.retired = {}
        self.type=[]
        self.active=True
   #     if numclient != NUMCLIENT:
    #        self.resetHS(ip, portnum, authkey, numclient)

    def isActive(self):
        return self.active

    def getParametersD(self):
        return {"workserver_ip": self.work_server[0],
                "workserver_port": self.work_server[1],
                "workserver_authkey": self.work_server[2],
                "workserver_client": self.work_server[3]}

    def resetNumClient(self, numclient=None):
        self.work_server = (self.work_server[0], self.work_server[1], self.work_server[2], numclient)
        
    def __del__(self):
        if self.hid is not None:
            self.shared_job_q.put({"hid": self.hid, "task": "layoff"})

    def testConnect(self):
        try:
            manager = make_client_manager(self.work_server[0], self.work_server[1], self.work_server[2])
            return True
        except socket.error:
            return False

    def getDetailedInfos(self):
        counter = 10
        status = "KO"
        info = ""
        client_ids = []
        if self.getHid() is None:
            try:
                manager = make_client_manager(self.work_server[0], self.work_server[1], self.work_server[2])
            except (socket.error, IOError, EOFError):
                self.onServerDeath()
                info = "Maybe the server died, in any case, it did not respond...\n"
                counter = 0
            else:
                self.shared_job_q = manager.get_job_q()
                self.ids_d = manager.get_ids_d()
        uid = uuid.uuid4()
        if counter > 0:
            try:
                self.shared_job_q.put({"task": "info", "cid": uid})
            except (socket.error, IOError, EOFError):
                self.onServerDeath()
                info = "Maybe the server died, in any case, it did not respond...\n"
                counter = 0
        while counter > 0 and uid not in self.ids_d._callmethod("keys"):
            time.sleep(1)
            counter -= 1
        if counter > 0 and uid in self.ids_d._callmethod("keys"):
            tmp = self.ids_d._callmethod("pop", (uid,))
            parts = tmp.strip().split()
            if len(parts) == 0:
                status = "OK"
                info = "Does not have any client.\n"
            else:
                working, pending, retired = (0,0,0)
                for p in parts:                   
                    tmp = re.match("^(?P<cid>[a-zA-Z0-9]*):w(?P<working>[0-9]*)\+p(?P<pending>[0-9]*)\+r(?P<retired>[0-9]*)$", p)
                    client_ids.append(int(tmp.group("cid")))
                    # if tmp is not None:
                    #     working += int(tmp.group("working"))
                    #     pending += int(tmp.group("pending"))
                    #     retired += int(tmp.group("retired")) 
                if len(parts) == 1:
                    status = "OK"
                    info = "One client."
                else:
                    status = "OK"
                    info = "%d clients." #, in total %d tasks, of which %d currently running." % (len(parts), working+pending+retired, working)
                info = info +"\n("+ ", ".join(["#%s" % item for item in parts]) + ")"
        return status, info, client_ids

    def infoStr(self):
        return "Server %s:%d" % (self.work_server[0], self.work_server[1])

    def resetHS(self, ip=None, numport=None, authkey=None, numclient=None):
        if self.getHid() is not None and self.nbWorkers() == 0:
            ## check results before calling this
            self.shared_job_q.put({"hid": self.getHid(), "task": "layoff"})
            self.shared_job_q = None
            self.shared_result_q= None
            self.hid = None
        
        if self.getHid() is None:
            if ip is not None:
                self.work_server = (ip, numport, authkey, numclient)
            manager = make_client_manager(self.work_server[0], self.work_server[1], self.work_server[2])
            self.shared_job_q = manager.get_job_q()
            self.ids_d = manager.get_ids_d()
            uid = uuid.uuid4()
            wkr_reconnect = []
            if numclient != NUMCLIENT and numclient is not None: ##if it is an older client
                self.hid = numclient
                wkr_reconnect = self.reconnect(uid, manager)
            if len(wkr_reconnect) == 0:
                self.shared_job_q.put({"task": "startup", "cid": uid})
                counter = 10
                while uid not in self.ids_d._callmethod("keys") and counter > 0:
                    time.sleep(1)
                    counter -= 1
                if uid in self.ids_d._callmethod("keys"):                    
                    self.hid = self.ids_d._callmethod("pop", (uid,))
            hc_manager = make_hc_manager(self.work_server[0], self.getHid(), self.work_server[2])
            self.shared_result_q = hc_manager.get_result_q()
            return self.getHid(), wkr_reconnect

    ###give the order to reconnect and get the type's workers back 
    def reconnect(self, uid, manager):
        job = {"hid": self.getHid(), "wid": 0, "task": "reconnect", "cid":uid}
        wkr_reconnect = []
        self.getJobsQueue().put(job)
        try:
            shared_reconnect_q = manager.get_reconnect_q()
            wkr_reconnect = shared_reconnect_q.get()
        except queue.Empty:
            wkr_reconnect = []
        return wkr_reconnect

    def reconnection(self, boss):
        if self.work_server[3] != NUMCLIENT: ### if there is a client id to reconnect
            hid, wkr_reconnect = self.resetHS(self.work_server[0], self.work_server[1], self.work_server[2], self.work_server[3])
            for (wid, t, stat) in wkr_reconnect:
                if t in self.resumable_tasks:
                    self.addWorker(boss, {"task": t}, wid=wid)
            
    def getOutQueue(self):
        return None
    def getResultsQueue(self):
        return self.shared_result_q
    def getJobsQueue(self):
        return self.shared_job_q
    def getHid(self):
        return self.hid
    
    def addWorker(self, boss, params=None, details={}, wid=None):
        if self.getHid() is None:
            self.resetHS()
        if self.getHid() is not None:
            if wid is None:
                wid = self.generateNextWid()
            wdetails, job = self.prepareWorkerDetails(boss, params, details, wid)
            self.workers[wid] = details
            try:
                self.getJobsQueue().put(job)
            except (socket.error, IOError, EOFError):
                self.onServerDeath(boss)
 
    def cleanUpResults(self):
        if self.getResultsQueue() is None:
            return
        while self.getResultsQueue() is not None:
            try:
                # self.getResultsQueue().get_nowait()
                self.getResultsQueue().get(False, 1)
            except queue.Empty:
                break
            except (socket.error, IOError, EOFError):
                self.onServerDeath()

    def closeDown(self, parent, collectLater = False):
        if not collectLater: # if the user wants to collect the results later on
        #for wid in self.workers.keys():
         #   self.layOff(wid)
            self.shutdown()
        time.sleep(1)
        # self.checkResults(parent)
        parent.checkResults(once=True)
        self.cleanUpResults()

    def layOff(self, wid):
        if self.getJobsQueue() is None: # if there isn't any job to be done
            return
        if wid is not None and wid in self.workers: # if the worker id is a number and is in the list of workers
            job = {"hid": self.getHid(), "wid": wid, "task": "layoff"} # create the job
            self.getJobsQueue().put(job) # add the job
            # self.off[wid] = self.workers.pop(wid)
            return wid
        return None

	##log out of the server
    def shutdown(self):
        job={"hid":self.getHid(), "wid": "all", "task":"shutdownClient"}
        self.getJobsQueue().put(job)
        self.active=False
        
    def retire(self, wid):
        if wid in self.off:
            self.retired[wid] = self.off.pop(wid)
        elif wid in self.workers and self.getJobsQueue() is not None:
            job = {"hid": self.getHid(), "wid": wid, "task": "retire"}
            self.getJobsQueue().put(job)            
            self.retired[wid] = self.workers.pop(wid)
        return None

    def monitorResults(self, parent):
        updates = {}
        if self.getJobsQueue() is not None:
            while self.nbWorking() > 0:
                try:
                    piece_result = self.getResultsQueue().get(False, 1)
                    if piece_result is not None:
                        self.handlePieceResult(piece_result, updates, parent)
                        if "status"in updates:
                            print(updates["status"])
                except (socket.error, IOError, EOFError):
                    self.onServerDeath(parent)

        return updates

    def checkResults(self, parent):
        updates = {}
        if self.getJobsQueue() is not None:
            while self.nbWorking() > 0:
                try:
                    # piece_result = self.getResultsQueue().get_nowait()
                    piece_result = self.getResultsQueue().get(False, 1)
                    if piece_result is not None:
                        self.handlePieceResult(piece_result, updates, parent)
                except queue.Empty:
                    break
                except (IOError, EOFError, socket.error):
                    self.onServerDeath(updates, parent)
        return updates

    def finishingWki(self, wki, updates=None, parent=None):
        if wki in self.workers:
            if updates is not None:
                if self.workers[wki]["task"] in ["project"]:
                    parent.readyProj(self.workers[wki]["vid"], None)
            self.retired[wki] = self.workers.pop(wki)

    def onServerDeath(self, updates=None, parent=None):
        wkis = self.workers.keys()
        for wki in wkis:
            self.finishingWki(wki, updates, parent)
        self.shared_job_q = None
        self.shared_result_q = None
        self.hid = None
        if updates is not None:
            self.updateStatus("WP", "Work server died!", updates)
            self.updateError("WP", "Work server died!", updates)
            updates["menu"] = True
            updates["progress"] = True

    def mapRid(self, red, source):
        if red.getUid() < 0:
            k = (red.getUid(), source)
            if k in self.map_rids:
                redc = red.copy(self.map_rids[k])
            else:
                redc = red.copy()
                self.map_rids[k] = redc.getUid()
        else:
            redc = red 
        return redc

    def mappedRid(self, iid, source):
        if iid < 0:
            return self.map_rids.get((iid, source), iid)
        return iid 
    
    def mapTracks(self, in_tracks, source=None):
        tracks = []
        for t in in_tracks:                
            tracks.append({})
            tracks[-1].update(t)
            if "src" in t:
                tracks[-1]["src"] = [self.mappedRid(iid, source) for iid in t["src"]]
            if "trg" in t:
                tracks[-1]["trg"] = [self.mappedRid(iid, source) for iid in t["trg"]]
        return tracks


if __name__ == '__main__':
    wp = WorkClient(IP, PORTNUM, AUTHKEY, NUMCLIENT)
    wp.testConnect()
    print(wp.getDetailedInfos())
    wp.shutdown()
