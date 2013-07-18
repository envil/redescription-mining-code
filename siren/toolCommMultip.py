import multiprocessing
from reremi.classMiner import Miner

import pdb

##### WITH MULTIPROCESSING
###############################################

##### For THREADING
### 1) import threading
### 2) replace multiprocessing.Process by threading.Thread 

class WorkerProcess(multiprocessing.Process):
    def __init__(self, id, boss, queue_in, params=None):
        multiprocessing.Process.__init__(self)
        self.miner = Miner(boss.getData(), boss.getPreferences(), boss.getLogger(), id, qin=queue_in)
        self.params = params
        self.start()

    def run(self):
        pass

class MinerProcess(WorkerProcess):
    def run(self):
        self.miner.full_run()

class ExpanderProcess(WorkerProcess):
    def run(self):
        self.miner.part_run(self.params)

class ProjProcess(multiprocessing.Process):
    def __init__(self, pid, boss, queue_in, proj=None):
        multiprocessing.Process.__init__(self)
        self.id = pid
        self.logger = boss.getLogger()
        if proj is not None:
            self.proj = proj
            self.start()

    def run(self):
        try:
            self.proj.do()
            self.logger.printL(1, self.proj, "result", self.id)
        except:
            self.logger.printL(1, "Projection Failed!", "error", self.id)
        finally:
            self.logger.printL(1, None, "progress", self.id)


class WorkPlant:

    cqueue = multiprocessing.Queue
    type_workers = {"expander": ExpanderProcess, "miner": MinerProcess, "project": ProjProcess}
    type_messages = {'log': "self.updateLog", 'result': None, 'progress': "self.updateProgress",
                     'status': "self.updateStatus", 'error': "self.updateError"}

    @classmethod
    def sendMessage(tcl, output, message, type_message, source):
        if tcl.type_messages.has_key(type_message) and output is not None:
            output.put({"message": message, "type_message": type_message, "source": source})

    def __init__(self):
        self.next_workerid = 0
        self.workers = {}
        self.off = {}
        self.retired = {}
        self.comm_queues = {"out": self.cqueue()}

    def getOutQueue(self):
        return self.comm_queues["out"]

    def cleanUp(self, qid):
        while True:
            try:
                self.comm_queues[qid].get_nowait()
            except:
                break

    def addWorker(self, wtype, boss, more=None, details={}):
        if self.type_workers.has_key(wtype):
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

    def layOff(self, wid, mess=True):
        if wid is not None and self.workers.has_key(wid):
            if mess and self.comm_queues.has_key(wid):
                self.sendMessage(self.comm_queues[wid], "stop", "progress", "plant")
            self.off[wid] = self.workers.pop(wid)
            return wid
        return None

    def retire(self, wid):
        if self.off.has_key(wid):
            self.retired[wid] = self.off.pop(wid)
        elif self.workers.has_key(wid):
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
            except:
                break
        return updates

    def handlePieceResult(self, note, updates, parent):
        if self.type_messages.has_key(note["type_message"]):
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
        if not updates.has_key("log"):
            updates["log"] = ""
        updates["log"] += header+text+"\n"

    def updateError(self, source, message, updates):
        updates["error"] = "@%s:%s" % (source, message) 

    def updateStatus(self, source, message, updates):
        updates["status"] = "@%s:%s" % (source, message) 

    def updateProgress(self, source, message, updates):
        if self.workers.has_key(source):
            if message is None:
                self.retire(source)
                updates["menu"] = True
            elif len(message) > 1:
                self.workers[source]["work_progress"] = message[1]
                self.workers[source]["work_estimate"] = message[0]
            updates["progress"] = True
            
    def sendResult(self, source, message, updates, parent):
        if not self.workers.has_key(source):
            return
        
        worker_info = self.workers[source]
        if worker_info["wtyp"] in ["expand", "miner"]:
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
        elif worker_info["wtyp"] in ["project"]:
            parent.readyProj(worker_info["vid"], message)
