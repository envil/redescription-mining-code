import multiprocessing
import time
import os
import argparse
from multiprocessing.managers import SyncManager

from ..mine.classMiner import instMiner
from ..mine.classRedescription import Redescription
from ..mine.toolLog import Log

import pdb
# to clean up: sudo netstat -nlp | grep python


PORT = 55444
AUTHKEY = 'sesame'
MAXK = 4


def sendMessage(output, message, type_message, source):
    output.put({"message": message, "type_message": type_message, "source": source})


class WorkerProcess(multiprocessing.Process):
    def __init__(self, pid, data, preferences, queue_in, result_q, cust_params={}):
        multiprocessing.Process.__init__(self)
        verbosity = preferences.get("verbosity", 0)
        logger = Log("inter", verbosity, output=result_q, method_comm=sendMessage)
        self.miner = instMiner(data, preferences, logger, pid, qin=queue_in, cust_params=cust_params)
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
    def __init__(self, pid, data, preferences, queue_in, result_q, proj={}):
        multiprocessing.Process.__init__(self)
        self.id = pid
        verbosity = preferences.get("verbosity", 0)
        self.logger = Log("inter", verbosity, output=result_q, method_comm=sendMessage)
        if proj is not None:
            self.proj = proj
            self.start()

    def getId(self):
        return self.id

    def stop(self):
        self.proj.stop()
        self.logger.printL(1, self.proj, "result", self.getId())
        self.logger.printL(1, None, "progress", self.getId())
        self.terminate()

    def run(self):
        print("\t--- Projection running...")
        try:
            self.proj.do()
        except Exception as e:
            print("\t--- Projection ERROR!")
            self.proj.clearCoords()
            self.logger.printL(1, "Projection Failed!\n[ %s ]" % e, "error", self.getId())
        finally:
            print("\t--- Projection done")
            self.logger.printL(1, self.proj, "result", self.getId())
            self.logger.printL(1, None, "progress", self.getId())


def make_server_manager(port, authkey):

    job_q = multiprocessing.Queue()
    reconnect_q = multiprocessing.Queue()
    ids_d = dict()

    class JobQueueManager(SyncManager):
        pass

    JobQueueManager.register('get_job_q', callable=lambda: job_q)
    JobQueueManager.register('get_reconnect_q', callable=lambda: reconnect_q)
    JobQueueManager.register('get_ids_d', callable=lambda: ids_d)

    manager = JobQueueManager(address=("", port), authkey=authkey.encode('ascii'))
    manager.start()

    print('Central server started at port %s' % port)
    return manager


class WorkServer(object):

    def __init__(self, port=PORT, authkey=AUTHKEY, max_k=MAXK):
        print("PID", os.getpid())
        # MAKES REDS TO HAVE NEGATIVE IDS SO THEY CAN BE RECOGNIZED HAS EZTERNAL
        Redescription.setUidGen(nv=-1, step=-1, mp_lock=True)
        self.handlers = {}
        self.manager = make_server_manager(port, authkey)
        self.shared_job_q = self.manager.get_job_q()  # queue
        self.shared_ids_d = self.manager.get_ids_d()  # dict
        self.shared_reconnect_q = self.manager.get_reconnect_q()  # queue

        self.max_k = max_k
        self.port = port
        self.authkey = authkey
        self.nextHandlerId = 0

    def run(self):
        if True:
            while True:
                # read tasks from queue
                job = self.getJobsQueue().get()
                if type(job) is dict:
                    if job.get("task") == "startup":
                        # create new handler
                        self.nextHandlerId += 1
                        hid = self.port + self.nextHandlerId
                        self.handlers[hid] = WorkHandler(self, hid, self.authkey, self.max_k)
                        self.shared_ids_d.update({job.get("cid"): hid})
                        # print(type(self.shared_ids_d))
                        print("--- Creating new handler\tHID+%s\t(%s)" % (hid, job.get("cid")))

                    elif job.get("task") == "info":
                        # create new handler
                        hid = self.port + self.nextHandlerId
                        ld_str = self.getLoadStr()
                        self.shared_ids_d.update({job.get("cid"): ld_str})
                        print("--- Sending info\t%s\t(%s)" % (ld_str, job.get("cid")))

                    elif job.get("task") == "reconnect":
                        if job.get("hid") in self.handlers:
                            hid = job.get("hid")
                            wids = [(k, v.get("task"), "pending") for (k, v) in self.handlers[hid].pending.items()]
                            wids += [(k, v.get("task"), "working") for (k, v) in self.handlers[hid].working.items()]
                            wids += [(k, v.get("task"), "retired") for (k, v) in self.handlers[hid].retired.items()]
                            rwids = [w for w in wids if w[1] in WorkHandler.types_reconnect]
                            nwids = [w for w in wids if w[1] not in WorkHandler.types_reconnect]
                            rwids_str = ", ".join([":".join(map(str, w)) for w in rwids])
                            nwids_str = ", ".join([":".join(map(str, w)) for w in nwids])
                            print("--- Reconnecting handler\tHID=%s\tworkers: %s (%s)\t(%s)" % (hid, rwids_str, nwids_str, job.get("cid")))  # details: rwids
                            self.shared_ids_d.update({job.get("cid"): hid})
                            self.shared_reconnect_q.put(rwids, False)
                        else:
                            h_str = ", ".join(["%s" % hh for hh in self.handlers.keys()])
                            print("--- Could not find handler to reconnect\tHID?%s\tamong: %s\t(%s)" % (hid, h_str, job.get("cid")))  # details: rwids

                    # other, handler specific task, forward
                    elif job.get("hid") in self.handlers:
                        print("--- Forwarding task to handler\tHID=%s WID=%s %s" % (job.get("hid"), job.get("wid", "?"), job["task"]))
                        for hdl in self.getHandlers(job.get("hid")):
                            hdl.handleJob(job)

    def getHandlers(self, hid=None):
        if hid == "all":
            return
        if hid in self.handlers:
            return [self.handlers[h] for h in self.handlers.keys()]
        return []

    def getLoadStr(self):
        return " ".join([hd.getLoadStr() for (hdid, hd) in self.handlers.items()])

    def __del__(self):
        hids = list(self.handlers.keys())
        for hid in hids:
            self.handlers[hid].shutdown()
        self.manager.shutdown()

    def unregister(self, hid):
        # unregister handler upon shutdown
        if hid in self.handlers:
            del self.handlers[hid]

    def getJobsQueue(self):
        return self.shared_job_q

    def getIdsDict(self):
        return self.shared_ids_d


def make_hs_manager(port, authkey):
    job_q = multiprocessing.Queue()
    result_q = multiprocessing.Queue()
    reconnect_q = multiprocessing.Queue()

    class HSQueueManager(SyncManager):
        pass

    HSQueueManager.register('get_job_q', callable=lambda: job_q)
    HSQueueManager.register('get_result_q', callable=lambda: result_q)

    manager = HSQueueManager(address=("", port), authkey=authkey.encode('ascii'))
    manager.start()
    print("Work server started at port %s" % port)
    return manager


class WorkHandler(object):

    type_workers = {"mine": {"launch": MinerProcess, "stop": "message"},
                    "expand": {"launch": ExpanderProcess, "stop": "message"},
                    "improve": {"launch": ExpanderProcess, "stop": "message"},
                    "project": {"launch": ProjectorProcess, "stop": "terminate"}}
    types_reconnect = ["mine", "expand", "improve"]

    @classmethod
    def getWorkClassForTask(tcl, task):
        if task in tcl.type_workers:
            return tcl.type_workers[task]["launch"]

    @classmethod
    def getDetForTask(tcl, task):
        if task in tcl.type_workers:
            return tcl.type_workers.get(task)
        return {}

    @classmethod
    def knownTaskWork(tcl, task):
        return task in tcl.type_workers

    def __init__(self, work_server, port, authkey, max_k=MAXK):
        self.manager = make_hs_manager(port, authkey)
        self.shared_result_q = self.manager.get_result_q()  # queue
        self.work_server = work_server
        self.id = port
        self.max_k = max_k
        self.pending = {}
        self.working = {}
        self.retired = {}

    def getId(self):
        return self.id

    def getResultsQueue(self):
        return self.shared_result_q

    def getLoadStr(self):
        return "%d:w%d+p%d+r%d" % (self.getId(), len(self.working), len(self.pending), len(self.retired))

    def handleJob(self, job):
        # retire and layoff are for workers, shutdown for the whole handler
        # if retire: stop work in process, move to retire, and launch any pending job
        if job.get("task") == "retire":
            if job.get("wid") in self.working:
                self.retired[job.get("wid")] = self.working.pop(job.get("wid"))
                self.launchPending()

        # if layoff: remove from pending or stop work in process
        elif job.get("task") == "layoff":
            if job.get("wid") in self.pending:
                self.pending.pop("wid")
            elif job.get("wid") in self.working:
                self.stopJob(job.get("wid"))
                self.retired[job.get("wid")] = self.working.pop(job.get("wid"))
                self.launchPending()

        # shutdown this handler
        elif job.get("task") == "shutdown":
            self.shutdown()

        # other, unknown task, notify, so the worker on client side don't hang waiting
        elif not self.knownTaskWork(job.get("task")):
            self.notifyFatalErrorWid("Fatal: Unknown task for worker!", job.get("wid"))
            return False

        # if acceptable task: launch work if there are free processes, else add job to pending
        # if already in pending or working, comes from attempt to reconnect, do nothing
        elif job.get("wid") not in self.pending and job.get("wid") not in self.working:
            if len(self.working) < self.max_k:
                tmp = self.launchJob(job)
                if tmp is not None:
                    self.working[job.get("wid")] = tmp
            else:
                self.pending[job.get("wid")] = job
        return True

    def notifyFatalErrorWid(self, msg, wid):
        sendMessage(self.getResultsQueue(), msg, "error", "%s-!" % wid)

    def launchPending(self):
        # if pending tasks launch oldest one
        while len(self.working) < self.max_k and len(self.pending) > 0:
            oldest_wid = min(self.pending.keys())
            tmp = self.launchJob(self.pending[oldest_wid])
            if tmp is not None:
                self.working[oldest_wid] = tmp
            self.pending.pop(oldest_wid)

    def launchJob(self, job):
        if self.knownTaskWork(job.get("task")):
            # print("--- Handler launching task\tHID=%s WID=%s %s" % (job.get("hid"), job.get("wid"), job["task"]))
            if self.getDetForTask(job.get("task")).get("stop") == "message":
                queue = multiprocessing.Queue()
            else:
                queue = None
            p = self.getWorkClassForTask(job.get("task"))(job.get("wid"), job.get("data"), job.get("preferences"), queue, self.getResultsQueue(), job.get("more"))
            return {"process": p, "queue": queue, "task": job.get("task")}

    def stopJob(self, wid):
        if self.working[wid]["queue"] is not None:
            self.working[wid]["queue"].put({"message": "stop", "type_message": "progress", "source": "plant"})
        else:
            self.working[wid]["process"].stop()
            # self.working[wid]["process"].terminate()

    # close this handler
    def shutdown(self):
        workers = list(self.working.keys())
        for wid in workers:
            self.stopJob(wid)
            self.working.pop(wid)
        time.sleep(5)
        try:
            del self.working
            del self.pending
            del self.retired
        except AttributeError:
            pass
        finally:
            self.manager.shutdown()
            self.work_server.unregister(self.getId())


# main entry point

def run_server(sargs):

    parser = argparse.ArgumentParser(description='Launch server for off-loading redescription mining computations.')
    parser.add_argument("-p", "--port", type=int, help="address on which the manager process listens for new connections", default=PORT)
    parser.add_argument("-a", "--authkey", type=str, help="authentication key which will be used to check the validity of incoming connections to the server process", default=AUTHKEY)
    parser.add_argument("-m", "--max_k", type=int, help="maximum number of computational tasks handled at once", default=MAXK)
    parser.add_argument("-c", "--chroot", type=str, help="change the root directory of the current process to this path", default=argparse.SUPPRESS)
    parser.add_argument("-u", "--uid", type=int, help="set the current process's user id", default=argparse.SUPPRESS)
    parser.add_argument("-g", "--gid", type=int, help="set the current process's group id", default=argparse.SUPPRESS)

    args = vars(parser.parse_args(sargs[1:]))
    if "uid" in args:
        if "gid" in args:
            # We drop GID before we drop UID
            os.setgid(args.pop("gid"))
        os.setuid(args.pop("uid"))
    else:  # uid not in args
        if "gid" in args:
            os.setgid(args.pop("gid"))
        if "chroot" in args:
            os.chroot(args.pop("chroot"))

    ws = WorkServer(**args)
    try:
        ws.run()
    except KeyboardInterrupt:
        print("Stopped...")
    finally:
        del ws
