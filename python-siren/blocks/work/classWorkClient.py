#!/usr/bin/env python
import multiprocessing
from multiprocessing.managers import SyncManager  # needed, the above is not enough
import time
import sys
import socket
import uuid
import re
import queue

try:
    from classWorkInactive import WorkInactive
except ModuleNotFoundError:
    from .classWorkInactive import WorkInactive

import pdb

IP = '127.0.0.1'
PORT = 55444
AUTHKEY = 'sesame'
CLIENTID = 0


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

    # One client (WorkClient) corresponds to one handler (WorkHandler) on the server, identified through their hid,
    # which might have several workers (WorkProcess on the server, details dict stored in workers attribute of the handler on the client, identified through their wid)
    resumable_tasks = ["mine", "expand"]

    @classmethod
    def questionReturnLater(tcl, clientid):
        return 'Some computations are underway (client id %s).\nDo you intend to collect the results later on?' % clientid

    def __init__(self, ip=IP, port=PORT, authkey=AUTHKEY, clientid=CLIENTID):
        self.hid = None
        if ip == 'localhost':
            ip = IP
        self.work_server = (ip, port, authkey, clientid)
        self.shared_job_q = None  # queue
        self.ids_d = None  # queue
        self.shared_result_q = None  # queue
        self.workers = {}
        self.off = {}
        self.retired = {}
        self.type = []
        self.active = True
        # if clientid != CLIENTID:
        #     self.resetHS(ip, port, authkey, clientid)

    def isActive(self):
        return self.active

    def isDistributed(self):
        return True

    def getParametersD(self):
        return {"workserver_ip": self.work_server[0],
                "workserver_port": self.work_server[1],
                "workserver_authkey": self.work_server[2],
                "workserver_clientid": self.work_server[3]}

    def getHid(self):  # Handler id
        return self.hid

    def getOutQueue(self):
        return None

    def getResultsQueue(self):
        return self.shared_result_q

    def getJobsQueue(self):
        return self.shared_job_q

    def sendJob(self, job):
        self.getJobsQueue().put(job)

    def resetClientId(self, clientid=None):
        self.work_server = (self.work_server[0], self.work_server[1], self.work_server[2], clientid)

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
                self.onServerDeath()  # just starting, nothing killed needs to be notified to the boss
                info = "Maybe the server died, in any case, it did not respond...\n"
                counter = 0
            else:
                self.shared_job_q = manager.get_job_q()
                self.ids_d = manager.get_ids_d()
        uid = uuid.uuid4()
        if counter > 0:
            try:
                self.getJobsQueue().put({"task": "info", "cid": uid})
            except (socket.error, IOError, EOFError):
                self.onServerDeath()  # just starting, nothing killed needs to be notified to the boss
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
                working, pending, retired = (0, 0, 0)
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
                    info = "%d clients."  # , in total %d tasks, of which %d currently running." % (len(parts), working+pending+retired, working)
                info = info + "\n(" + ", ".join(["#%s" % item for item in parts]) + ")"
        return status, info, client_ids

    def infoStr(self):
        numc = ""
        if self.getHid() is not None and self.getHid() != CLIENTID:
            numc = " [%s]" % self.getHid()
        return "Server %s:%d%s" % (self.work_server[0], self.work_server[1], numc)

    def resetHS(self, ip=None, numport=None, authkey=None, clientid=None):
        if self.getHid() is not None and self.nbWorkers() == 0:
            # check results before calling this
            self.getJobsQueue().put({"hid": self.getHid(), "task": "shutdown"})
            self.shared_job_q = None
            self.shared_result_q = None
            self.hid = None

        if self.getHid() is None:
            if ip is not None:
                self.work_server = (ip, numport, authkey, clientid)
            manager = make_client_manager(self.work_server[0], self.work_server[1], self.work_server[2])
            self.shared_job_q = manager.get_job_q()
            self.ids_d = manager.get_ids_d()
            uid = uuid.uuid4()
            wkr_reconnect = []
            if clientid != CLIENTID and clientid is not None:  # if it is an older client
                self.hid = clientid
                wkr_reconnect = self.reconnect(uid, manager)
            if len(wkr_reconnect) == 0:
                self.getJobsQueue().put({"task": "startup", "cid": uid})
                counter = 10
                while uid not in self.ids_d._callmethod("keys") and counter > 0:
                    time.sleep(1)
                    counter -= 1
                if uid in self.ids_d._callmethod("keys"):
                    self.hid = self.ids_d._callmethod("pop", (uid,))
            hc_manager = make_hc_manager(self.work_server[0], self.getHid(), self.work_server[2])
            self.shared_result_q = hc_manager.get_result_q()
            return self.getHid(), wkr_reconnect

    # give the order to reconnect and get the type's workers back
    def reconnect(self, uid, manager):
        wkr_reconnect = []
        self.getJobsQueue().put({"hid": self.getHid(), "wid": 0, "task": "reconnect", "cid": uid})
        try:
            shared_reconnect_q = manager.get_reconnect_q()
            wkr_reconnect = shared_reconnect_q.get()
        except queue.Empty:
            wkr_reconnect = []
        return wkr_reconnect

    def reconnection(self, boss):
        if self.work_server[3] != CLIENTID:  # if there is a client id to reconnect, should not have ongoing work to reset
            hid, wkr_reconnect = self.resetHS(self.work_server[0], self.work_server[1], self.work_server[2], self.work_server[3])
            for (wid, t, stat) in wkr_reconnect:
                if t in self.resumable_tasks:
                    self.addWorker(boss, {"task": t}, wid=wid)

    def addWorker(self, boss, params=None, details={}, wid=None):
        if self.getHid() is None:
            self.resetHS()
        if self.getHid() is not None:
            if wid is None:
                wid = self.generateNextWid()
            wdetails, job = self.prepareWorkerDetailsAndJob(boss, params, details, wid)
            self.workers[wid] = details
            try:
                self.getJobsQueue().put(job)
            except (socket.error, IOError, EOFError):
                return self.onServerDeath()

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

    def closeDown(self, boss, collectLater=False):
        # if the user wants to collect the results later on, the server is not notifed
        # else, request shutdown of associated handler on the server
        if not collectLater and self.hid is not None:
            self.shutdown()
            time.sleep(1)
            boss.checkResults(once=True)
            self.cleanUpResults()

    def layOff(self, wid):
        if self.getJobsQueue() is None:  # if there isn't any job to be done
            return
        if wid is not None and wid in self.workers:  # if the worker id is a number and is in the list of workers
            job = {"hid": self.getHid(), "wid": wid, "task": "layoff"}  # create the job
            self.getJobsQueue().put(job)  # add the job
            # self.off[wid] = self.workers.pop(wid)
            return wid
        return None

    # log out of the server
    def shutdown(self):
        job = {"hid": self.getHid(), "task": "shutdown"}
        self.getJobsQueue().put(job)
        self.active = False

    def retire(self, wid):
        if wid in self.off:
            self.retired[wid] = self.off.pop(wid)
        elif wid in self.workers and self.getJobsQueue() is not None:
            job = {"hid": self.getHid(), "wid": wid, "task": "retire"}
            self.getJobsQueue().put(job)
            self.retired[wid] = self.workers.pop(wid)
        return None

    def checkInComm(self):
        in_comm = []
        if self.getJobsQueue() is not None:
            while self.nbWorking() > 0:
                try:
                    # piece_result = self.getResultsQueue().get_nowait()
                    piece = self.getResultsQueue().get(False, 1)
                    if piece is not None:
                        self.handlePieceComm(piece)  # check communication for own use
                        in_comm.append(piece)  # forward to boss
                except queue.Empty:
                    break
                except (IOError, EOFError, socket.error):
                    in_comm.extend(self.onServerDeath())
        return in_comm

    def onServerDeath(self):
        wkis = list(self.workers.keys())
        death_notice = []
        for wki in wkis:
            if self.workers[wki]["task"] in ["project"]:
                death_notice.append({"type_message": "result", "source": wki, "message": None})
            else:
                death_notice.append({"type_message": "progress", "source": wki, "message": None})
            self.retired[wki] = self.workers.pop(wki)
        self.shared_job_q = None
        self.shared_result_q = None
        self.hid = None
        death_notice.append({"type_message": "error", "source": "WP-!", "message": "Work server died!"})
        return death_notice
