import multiprocessing
import multiprocessing.queues
import queue

from ..mine.classMiner import instMiner
from .classWorkInactive import WorkInactive

import pdb

DEBUG = False
# DEBUG = True

# WITHOUT MULTIPROCESSING --> for debugging
###############################################
if DEBUG:

    class WorkerProcess:
        def __init__(self, id, boss, queue_in, cust_params={}):
            # print("WProcess logs to:", boss.getLoggerComm().disp())
            self.miner = instMiner(boss.getData(), boss.getPreferences(), boss.getLoggerComm(), id, qin=queue_in, cust_params=cust_params)
            self.cust_params = cust_params
            self.start()

        def start(self):
            self.run()

        def run(self):
            pass

    class MinerProcess(WorkerProcess):
        def run(self):
            self.miner.full_run(self.cust_params)

    class ExpanderProcess(WorkerProcess):
        def run(self):
            self.miner.part_run(self.cust_params)

    class ProjectorProcess:
        def __init__(self, pid, boss, queue_in, proj=None):
            self.id = pid
            self.logger = boss.getLoggerComm()
            if proj is not None:
                self.proj = proj
                self.start()

        def getId(self):
            return self.id

        def stop(self):
            self.proj.stop()
            self.logger.printL(1, self.proj, "result", self.getId())
            self.logger.printL(1, None, "progress", self.getId())

        def start(self):
            self.run()

        def run(self):
            try:
                self.proj.do()
            except ValueError as e:  # Exception as e:
                self.proj.clearCoords()
                self.logger.printL(1, "Projection Failed!\n[ %s ]" % e, "error", self.getId())
            finally:
                self.logger.printL(1, self.proj, "result", self.getId())
                self.logger.printL(1, None, "progress", self.getId())

else:
   # WITH MULTIPROCESSING
   ###############################################

   # For THREADING
   # 1) import threading
   # 2) replace multiprocessing.Process by threading.Thread

    class WorkerProcess(multiprocessing.Process):
        def __init__(self, id, boss, queue_in, cust_params={}):
            multiprocessing.Process.__init__(self)
            # print("WProcess logs to:", boss.getLoggerComm().disp())
            self.miner = instMiner(boss.getData(), boss.getPreferences(), boss.getLoggerComm(), id, qin=queue_in, cust_params=cust_params)
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
            self.logger = boss.getLoggerComm()
            if proj is not None:
                self.proj = proj
                self.start()

        def getId(self):
            return self.id

        def stop(self):
            self.proj.stop()
            self.logger.printL(1, self.proj, "result", self.getId())
            self.logger.printL(1, None, "progress", self.getId())

        def run(self):
            try:
                self.proj.do()
            except ValueError as e:  # Exception as e:
                self.proj.clearCoords()
                self.logger.printL(1, "Projection Failed!\n[ %s ]" % e, "error", self.getId())
            finally:
                self.logger.printL(1, self.proj, "result", self.getId())
                self.logger.printL(1, None, "progress", self.getId())

############################################
############################################


class WorkLocal(WorkInactive):

    cqueue = multiprocessing.Queue
    #cqueue = multiprocessing.queues.SimpleQueue
    type_workers = {"expand": ExpanderProcess, "improve": ExpanderProcess, "mine": MinerProcess, "project": ProjectorProcess}

    @classmethod
    def getWorkClassForTask(tcl, task):
        return tcl.type_workers.get(task)

    def __init__(self):
        self.work_server = ("local", None, None, None)
        self.workers = {}
        self.off = {}
        self.retired = {}
        self.comm_queues = {"out": self.cqueue()}

    def isActive(self):
        return True

    def isDistributed(self):
        return False

    def getParametersD(self):
        return {"workserver_ip": self.work_server[0]}

    def getDetailedInfos(self):
        return "OK", self.getLoadStr()+"\n", []

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
            except queue.Empty:
                break

    def addWorker(self, boss, params=None, details={}):
        details, job = self.prepareWorkerDetailsAndJob(boss, params, details)
        w_class = self.getWorkClassForTask(job["task"])
        if w_class is not None:
            wid = self.generateNextWid()
            self.comm_queues[wid] = self.cqueue()
            job["worker"] = w_class(wid, boss, self.comm_queues[wid], params)
            self.workers[wid] = job
            self.workers[wid].update(details)
        else:
            raise Warning("Unknown work task %s!" % job["task"])

    def closeDown(self, boss, collectLater=False):
        wks = list(self.workers.keys())
        for wid in wks:
            self.layOff(wid)
        boss.checkResults(once=True)
        self.cleanUp("out")

    def layOff(self, wid):
        if wid is not None and wid in self.workers:
            if self.workers[wid]["task"] == "project" and wid in self.comm_queues:
                # self.workers[wid]["worker"].terminate()
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

    def checkInComm(self):
        in_comm = []
        while self.nbWorking() > 0:
            try:
                piece = self.comm_queues["out"].get(False, 1)
                self.handlePieceComm(piece)  # check communication for own use
                in_comm.append(piece)  # forward to boss
            except queue.Empty:
                break
        return in_comm
