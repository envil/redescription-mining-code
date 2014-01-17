import multiprocessing, sys
from reremi.classMiner import Miner
from classWorkInactive import WorkInactive
import Queue

import pdb

##### WITH MULTIPROCESSING
###############################################

##### For THREADING
### 1) import threading
### 2) replace multiprocessing.Process by threading.Thread 

class WorkerProcess(multiprocessing.Process):
    def __init__(self, id, boss, queue_in, cust_params={}):
        multiprocessing.Process.__init__(self)
        # print "WProcess logs to:", boss.getLogger().disp()
        self.miner = Miner(boss.getData(), boss.getPreferences(), boss.getLogger(), id, qin=queue_in, cust_params=cust_params)
        self.cust_params = cust_params
        self.start()

    def run(self):
        pass

class MinerProcess(WorkerProcess):
    def run(self):
        self.miner.full_run(self.cust_params)

class ExpanderProcess(WorkerProcess):
    def run(self):
        self.miner.part_run(self.cust_params)

class ProjectorProcess(multiprocessing.Process):
    def __init__(self, pid, boss, queue_in, proj=None):
        multiprocessing.Process.__init__(self)
        self.id = pid
        self.logger = boss.getLogger()
        if proj is not None:
            self.proj = proj
            self.start()

    def stop(self):
        self.proj.stop()
        self.logger.printL(1, self.proj, "result", self.id)
        self.logger.printL(1, None, "progress", self.id)

    def run(self):        
        try:
            self.proj.do()
        except ValueError as e: #Exception as e:
            pdb.set_trace()
            self.proj.clearCoords()
            self.logger.printL(1, "Projection Failed!\n[ %s ]" % e, "error", self.id)
        finally:
            self.logger.printL(1, self.proj, "result", self.id)
            self.logger.printL(1, None, "progress", self.id)

class WorkLocal(WorkInactive):

    cqueue = multiprocessing.Queue
    type_workers = {"expander": ExpanderProcess, "miner": MinerProcess, "projector": ProjectorProcess}
    type_messages = {'log': "self.updateLog", 'result': None, 'progress': "self.updateProgress",
                     'status': "self.updateStatus", 'error': "self.updateError"}

    @classmethod
    def sendMessage(tcl, output, message, type_message, source):
        if type_message in tcl.type_messages and output is not None:
            output.put({"message": message, "type_message": type_message, "source": source})

    def __init__(self):
        self.next_workerid = 0
        self.work_server = ("local", None, None)
        self.workers = {}
        self.off = {}
        self.retired = {}
        self.comm_queues = {"out": self.cqueue()}

    def isActive(self):
        return True

    def getParametersD(self):
        return {"workserver_ip": self.work_server[0]}

    def getDetailedInfos(self):
        return "OK\t" + self.getLoadStr()
    def infoStr(self):
        return "Local"
    def getLoadStr(self):
        if len(self.workers) == 0:
            return "No process running"
        elif len(self.workers) == 1:
            return "One process running"
        else:
            return "%d processes running" % len(self.workers)


    def getOutQueue(self):
        return self.comm_queues["out"]

    def cleanUp(self, qid):
        while True:
            try:
                self.comm_queues[qid].get_nowait()
            except Queue.Empty:
                break

    def addWorker(self, wtype, boss, more=None, details={}):
        if wtype in self.type_workers:
            self.next_workerid += 1
            self.comm_queues[self.next_workerid] = self.cqueue()
            self.workers[self.next_workerid] = {"worker": self.type_workers[wtype](self.next_workerid, boss, self.comm_queues[self.next_workerid], more),
                                                "wtyp": wtype,
                                                "work_progress":0,
                                                "work_estimate":0}
            self.workers[self.next_workerid].update(details)
        
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
        self.cleanUp("out")

    def layOff(self, wid):
        if wid is not None and wid in self.workers:
            if self.workers[wid]["wtyp"] == "projector" and wid in self.comm_queues:
                #self.workers[wid]["worker"].terminate()
                self.workers[wid]["worker"].stop()
                #os.kill(self.workers[wid]["worker"].get_ppid(), signal.SIGTERM)
                # self.retire(wid)
            else:
                self.sendMessage(self.comm_queues[wid], "stop", "progress", "plant")
                self.off[wid] = self.workers.pop(wid)
            return wid
        return None

    def retire(self, wid):
        if wid in self.off:
            self.retired[wid] = self.off.pop(wid)
        elif wid in self.workers:
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

    def checkResults(self, parent):
        updates = {}
        while self.nbWorking() > 0:
            try:
                piece_result = self.comm_queues["out"].get_nowait()
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
                parent.readyReds(tmp, worker_info["results_tab"])
        elif worker_info["wtyp"] in ["projector"]:
            parent.readyProj(worker_info["vid"], message)
