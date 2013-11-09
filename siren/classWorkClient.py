import multiprocessing, time, socket
from multiprocessing.managers import SyncManager
import Queue

import pdb

IP = '127.0.0.1'
PORTNUM = 55444
AUTHKEY = 'shufflin'

def make_client_manager(ip, port, authkey):
    class ServerQueueManager(SyncManager):
        pass

    ServerQueueManager.register('get_job_q')
    ServerQueueManager.register('get_ids_d')

    manager = ServerQueueManager(address=(ip, port), authkey=authkey)
    manager.connect()
    return manager

def make_hc_manager(ip, port, authkey):

    class HCQueueManager(SyncManager):
        pass

    HCQueueManager.register('get_job_q', callable=lambda: job_q)
    HCQueueManager.register('get_result_q', callable=lambda: result_q)

    manager = HCQueueManager(address=(ip, port), authkey=authkey)
    manager.connect()
    return manager

class WorkClient:

    type_messages = {'log': "self.updateLog", 'result': None, 'progress': "self.updateProgress",
                     'status': "self.updateStatus", 'error': "self.updateError"}

    def __init__(self, ip=IP, portnum=PORTNUM, authkey=AUTHKEY):
        self.hid = None
        self.work_server = (ip, portnum, authkey)
        self.shared_job_q = None
        self.shared_result_q = None
        self.next_workerid = 0
        self.workers = {}
        self.off = {}
        self.retired = {}

    def __del__(self):
        if self.hid is not None:
            self.shared_job_q.put({"hid": self.hid, "task": "shutdown"})

    def testConnect(self):
        try:
            manager = make_client_manager(self.work_server[0], self.work_server[1], self.work_server[2])
            return True
        except socket.error:
            return False

    def resetHS(self, ip=None, numport=None, authkey=None):
        if self.hid is not None and self.nbWorkers() == 0:
            ## check results before caling this
            self.shared_job_q.put({"hid": self.hid, "task": "shutdown"})
            self.shared_job_q = None
            self.shared_result_q= None
            self.hid = None
            
        if self.hid is None:
            if ip is not None:
                self.work_server = (ip, nunmport, authkey)
            manager = make_client_manager(self.work_server[0], self.work_server[1], self.work_server[2])
            self.shared_job_q = manager.get_job_q()
            ids_d = manager.get_ids_d()
            ### TODO generate uid
            uid = 1
            self.shared_job_q.put({"task": "startup", "cid": uid})
            counter = 10
            while not ids_d.has_key(uid) and counter > 0:
                time.sleep(1)
                counter -= 1
            if ids_d.has_key(uid):
                self.hid = ids_d.pop(uid)
                hc_manager = make_hc_manager(self.work_server[0], self.hid, self.work_server[2])
                self.shared_result_q = hc_manager.get_result_q()
                return self.hid
                
    def getOutQueue(self):
        return None
    def getResultsQueue(self):
        return self.shared_result_q
    def getJobsQueue(self):
        return self.shared_job_q

    def addWorker(self, wtype, boss, more=None, details={}):
        if self.hid is None:
            self.resetHS()

        if self.hid is not None:
            self.next_workerid += 1
            self.workers[self.next_workerid] = {"wtyp": wtype,
                                                "work_progress":0,
                                                "work_estimate":0}
            self.workers[self.next_workerid].update(details)
            job = {"hid": self.hid, "wid":self.next_workerid, "task": wtype, "more": more, "data": boss.getData(), "preferences": boss.getPreferences()}
            self.getJobsQueue().put(job)
            
    def cleanUpResults(self):
        if self.getResultsQueue() is None:
            return
        while True:
            try:
                self.getResultsQueue().get_nowait()
            except Queue.Empty:
                break

    def getWorkEstimate(self):
        work_estimate = 0
        work_progress = 0
        for worker in self.workers.values():
            work_estimate += worker["work_estimate"]
            work_progress += worker["work_progress"]
        ### progress should not go over estimate, but well...
        work_progress = min(work_progress, work_estimate)
        return work_estimate, work_progress
        
    def nbWorkers(self):
        return len(self.workers)

    def nbWorking(self):
        return len(self.workers)+len(self.off)

    def closeDown(self, parent):
        for wid in self.workers.keys():
            self.layOff(wid)
        self.checkResults(parent)
        self.cleanUpResults()

    def layOff(self, wid):
        if self.getJobsQueue() is None:
            return
        if wid is not None and wid in self.workers:
            job = {"hid": self.hid, "wid": wid, "task": "layoff"}
            self.getJobsQueue().put(job)
            self.off[wid] = self.workers.pop(wid)
            return wid
        return None

    def retire(self, wid):
        if wid in self.off:
            self.retired[wid] = self.off.pop(wid)
        elif wid in self.workers and self.getJobsQueue() is not None:
            job = {"hid": self.hid, "wid": wid, "task": "retire"}
            self.getJobsQueue().put(job)            
            self.retired[wid] = self.workers.pop(wid)
        return None

    def findWid(self, fields):
        for wid, worker in sorted(self.workers.items()):
            found = True
            for f,v in fields:
                found &= (worker.get(f, None) == v)
            if found:
                return wid
        return None

    def getWorkersDetails(self):
        details = []
        for wid, worker in sorted(self.workers.items()):
            details.append({"wid": wid, "wtyp": worker["wtyp"]})
        return details


    def monitorResults(self, parent):
        updates = {}
        if self.getJobsQueue() is not None:
            while self.nbWorking() > 0:
                piece_result = self.getResultsQueue().get()
                self.handlePieceResult(piece_result, updates, parent)
        return updates

    def checkResults(self, parent):
        updates = {}
        if self.getJobsQueue() is not None:
            while self.nbWorking() > 0:
                try:
                    piece_result = self.getResultsQueue().get_nowait()
                    self.handlePieceResult(piece_result, updates, parent)
                except Queue.Empty:
                    break
        return updates

    def handlePieceResult(self, note, updates, parent):
        if note["type_message"] in self.type_messages:
            if note["type_message"] == "result":
                self.sendResult(note["source"], note["message"], updates, parent)
            else:
                method = eval(self.type_messages[note["type_message"]])
                if callable(method):
                    method(note["source"], note["message"], updates)

    def updateLog(self, source, message, updates):
        text = "%s" % message
        header = "@%s:\t" % source
        text = text.replace("\n", "\n"+header)
        if "log" not in updates:
            updates["log"] = ""
        updates["log"] += header+text+"\n"

    def updateError(self, source, message, updates):
        updates["error"] = "@%s:%s" % (source, message) 

    def updateStatus(self, source, message, updates):
        updates["status"] = "@%s:%s" % (source, message) 

    def updateProgress(self, source, message, updates):
        if source in self.workers:
            if message is None:
                self.retire(source)
                updates["menu"] = True
            elif len(message) > 1:
                self.workers[source]["work_progress"] = message[1]
                self.workers[source]["work_estimate"] = message[0]
            updates["progress"] = True
            
    def sendResult(self, source, message, updates, parent):
        if source not in self.workers:
            return
        
        worker_info = self.workers[source]
        if worker_info["wtyp"] in ["expander", "miner"]:
            tap = message[worker_info["batch_type"]]
            nb_tap = len(tap)
            if nb_tap > worker_info["results_track"]:
                tmp = []
                for red in tap[worker_info["results_track"]:nb_tap]:
                    redc = red.copy()
                    redc.track.insert(0, (source, "W"))
                    tmp.append(redc)
                worker_info["results_track"] = nb_tap
                if parent is None:
                    print "Ready reds %s %s" % (tmp, worker_info["results_tab"])
                else:
                    parent.readyReds(tmp, worker_info["results_tab"])
        elif worker_info["wtyp"] in ["projector"]:
            if parent is None:
                print "Ready proj %s %s" % (worker_info["vid"], message)
            else:
                parent.readyProj(worker_info["vid"], message)
