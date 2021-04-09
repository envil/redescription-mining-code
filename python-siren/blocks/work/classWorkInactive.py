import time

from ..mine.toolLog import Log

import pdb


class Boss:  # the ordering and receiving end of the work

    incomm_meths = {}

    def __init__(self, wp, data, preferences, filter_lids=None):
        self.wp = wp
        self.data = data
        self.preferences = preferences
        self.logger_comm = None
        self.resetLoggerComm()
        self.nb_checks = 0
        self.filter_lids = filter_lids

    def isGUI(self):
        return False

    def getWP(self):
        return self.wp

    def getFilterLids(self):
        return self.filter_lids

    def setFilterLids(self, lids=None):
        self.filter_lids = lids

    def getNbchecks(self):
        if hasattr(self, "nb_checks"):
            return self.nb_checks
        return 0

    def getData(self):
        return self.data

    def getPreferences(self):
        return self.preferences

    def getLoggerComm(self):
        # Log instance that wraps the out going queue
        return self.logger_comm

    def resetLoggerComm(self):
        # after setting up WorkInactive instance, integrate out queue to logger
        pass

    def rescheduleCheck(self, countdown=-1):
        # MAKE RECURRENT checkResults
        pass

    def checkResults(self, once=False, countdown=-1):
        in_comm = self.getWP().checkInComm()
        self.processInComm(in_comm)
        if hasattr(self, "nb_checks"):
            self.nb_checks += 1
        else:
            self.nb_checks = 1
        if not once:
            self.rescheduleCheck(countdown)

    def processInComm(self, in_comm, **kargs):
        for piece in in_comm:
            meth = self.incomm_meths.get(None)  # default meth if there is one
            if piece["type_message"] in self.incomm_meths:
                meth = self.incomm_meths[piece["type_message"]]
            if meth is not None:
                meth(self, piece["message"], piece["type_message"], piece["source"], **kargs)

    def processTracks(self, message, type_message, source_logid, **kargs):
        # need to map rids for those coming from different id generator (distributed)
        self.readyTracks(self.mapTracks(message, source_logid), source_logid)
    incomm_meths["tracks"] = processTracks

    def processResult(self, message, type_message, source_logid, **kargs):
        # transfer keeping track of seen reds to boss (results_last, src_lid, etc)
        # need to map rids for those coming from different id generator (distributed)
        worker_info = self.getWP().getWorkerDetails(source_logid)
        if worker_info is not None:
            if worker_info.get("task") in ["project"]:
                self.readyProj(worker_info["vid"], message)

            else:
                latest_reds = {}
                flids = self.getFilterLids()
                if flids is None:
                    flids = list(message.keys())
                for flid in flids:
                    if flid in message:
                        latest_reds[flid] = [self.mapRid(red, source_logid) for red in message[flid]]
                if sum([len(vs) for (k, vs) in latest_reds.items()]) > 0:
                    self.readyReds(latest_reds, (source_logid, worker_info["task"]), source_logid)  # (source, worker_info["task"], worker_info["results_tab"])
    incomm_meths["result"] = processResult

    def readyTracks(self, tracks, source):
        pass

    def readyReds(self, reds, wdets, source_logid):
        pass

    def readyProj(self, vid, proj):
        pass

    def mapRid(self, red, source):
        if self.getWP().isDistributed():
            if not hasattr(self, "map_rids"):
                self.map_rids = {}
            # red coming from server (see WorkServer init)
            # print(red.getUid(), source)
            if red.getUid() < 0:
                k = (red.getUid(), source)
                if k in self.map_rids:
                    redc = red.copy(self.map_rids[k])
                else:
                    redc = red.copy()
                    self.map_rids[k] = redc.getUid()
                return redc
        return red

    def mappedRid(self, iid, source):
        if iid < 0:
            return self.map_rids.get((iid, source), iid)
        return iid

    def mapTracks(self, in_tracks, source=None):
        if self.getWP().isDistributed() and hasattr(self, "map_rids"):
            tracks = []
            for t in in_tracks:
                tracks.append({})
                tracks[-1].update(t)
                if "src" in t:
                    tracks[-1]["src"] = [self.mappedRid(iid, source) for iid in t["src"]]
                if "trg" in t:
                    tracks[-1]["trg"] = [self.mappedRid(iid, source) for iid in t["trg"]]
            return tracks
        return in_tracks


class CLIBoss(Boss):

    incomm_meths = dict(Boss.incomm_meths)
    extend_lids = []  # "P"]

    def __init__(self, wp, data, preferences, logger, results_delay=1, filter_lids=None):
        Boss.__init__(self, wp, data, preferences, filter_lids)
        self.logger_out = logger
        self.results_delay = results_delay
        self.rc = {}  # just a dict, filtering etc is done on the server side

    def getLoggerOut(self):
        return self.logger_out

    def getResultsDelay(self):
        return self.results_delay

    def getReds(self, lid=None):
        return self.rc.get(lid, [])

    def resetLoggerComm(self):
        # after setting up WorkInactive instance, integrate out queue to logger
        self.logger_comm = Log("comm", self.getPreferences()["verbosity"],
                               self.getWP().getOutQueue(), self.getWP().sendMessage)

    def rescheduleCheck(self, countdown=-1):
        if self.getWP().nbWorking() > 0 and (countdown != 0) and self.results_delay > 0:
            # print("Checking...", countdown)
            time.sleep(self.results_delay)
            self.checkResults(once=False, countdown=countdown-1)

    def pieceToLog(self, message, type_message, source_logid, **kargs):
        self.getLoggerOut().printL(1, message, type_message, source_logid)
    incomm_meths[None] = pieceToLog

    def errorToLog(self, message, type_message, source_logid, **kargs):
        self.getLoggerOut().printL(1, message, "log", source_logid)
    incomm_meths["error"] = errorToLog

    incomm_meths["progress"] = None

    def readyReds(self, reds, wdets, source_logid):
        for lid, rs in reds.items():
            # these messages already come through status
            # if len(rs) > 0:
            #     self.getLoggerOut().printL(1, "%d redescriptions [%s]" % (len(rs), lid), 'status', source_logid)
            #     for red in rs:
            #         self.getLoggerOut().printL(10, "--- %s" % red, source=source_logid)
            # else:
            #     self.getLoggerOut().printL(1, "No redescription [%s]" % lid, 'status', source_logid)
            if lid in self.rc and lid in self.extend_lids:  # extend existing list
                self.rc[lid].extend(rs)
            else:
                self.rc[lid] = rs


class GUIBoss(Boss):

    incomm_meths = dict(Boss.incomm_meths)

    def isGUI(self):
        return True

    def updateLog(self, message, type_message, source_logid, **kargs):
        updates = kargs.get("updates", {})
        text = "%s" % message
        header = "@%s:\t" % source_logid
        text = text.replace("\n", "\n"+header)
        if "log" not in updates:
            updates["log"] = ""
        updates["log"] += header+text+"\n"
    incomm_meths["log"] = updateLog
    incomm_meths["time"] = updateLog

    def updateError(self, message, type_message, source_logid, **kargs):
        updates = kargs.get("updates", {})
        if source_logid[-1] == "!":  # Error causing the end of worker
            updates["menu"] = True
        updates["error"] = "@%s:%s" % (source_logid, message)
    incomm_meths["error"] = updateError

    def updateStatus(self, message, type_message, source_logid, **kargs):
        updates = kargs.get("updates", {})
        updates["status"] = "@%s:%s" % (source_logid, message)
    incomm_meths["status"] = updateStatus

    def updateProgress(self, message, type_message, source_logid, **kargs):
        updates = kargs.get("updates", {})
        if message is None:
            updates["menu"] = True
        updates["progress"] = True
    incomm_meths["progress"] = updateProgress


class WorkInactive:

    type_workers = {}

    # type_messages = set(['tracks', 'result', 'log', 'progress', 'status', 'error', 'time'])
    @classmethod
    def sendMessage(tcl, output, message, type_message, source):
        # if type_message == "progress":
        #     print("PROGRESS", message)
        if output is not None:
            output.put({"message": message, "type_message": type_message, "source": source})

    next_wid = 0
    step_wid = 1
    @classmethod
    def generateNextWid(tcl):
        tcl.next_wid += tcl.step_wid
        return "%s" % tcl.next_wid

    @classmethod
    def setWidGen(tcl, nv=0, step=1):
        if type(nv) is tuple:
            if len(nv) >= 2:
                tcl.next_wid = nv[0]
                tcl.step_wid = nv[1]
        else:
            tcl.next_wid = nv
            tcl.step_wid = step

    @classmethod
    def getWidGen(tcl):
        return (tcl.next_wid, tcl.step_wid)

    @classmethod
    def getSourceWid(tcl, source_logid):
        # Warning, changing the logid of miner processes impacts this
        return source_logid.split("-")[0]  # in case the miner is multiprocess

    def __init__(self):
        self.work_server = (None, None, None, None)
        self.workers = {}
        self.off = {}
        self.retired = {}

    def __trunc__(self):
        return 100000

    def isActive(self):
        return False

    def isDistributed(self):
        return False

    def getParametersD(self):
        return {"workserver_ip": ""}

    def getDetailedInfos(self):
        return "KO", "", []

    def infoStr(self):
        return "Inactive"

    def checkInComm(self):
        return []

    def getOutQueue(self):
        return None

    def layOff(self, wid):
        pass

    def closeDown(self, boss, collectLater=False):
        pass

    def addWorker(self, boss, params=None, details={}):
        pass

    def getHid(self):
        return -1

    def getTask(self, params=None, details={}):
        if "vid" in details:
            return "project"
        else:
            return params.get("task", "mine")

    def getWorkerDetails(self, source_logid):
        wid = self.getSourceWid(source_logid)
        if wid in self.workers:
            return self.workers[wid]
        elif wid in self.retired:
            return self.retired[wid]
        return None

    def prepareWorkerDetailsAndJob(self, boss, params=None, details={}, wid=None):
        task = self.getTask(params, details)
        details.update({"task": task, "work_progress": 0, "work_estimate": 0})
        # if task != "project":
        #     details.update({"results_last": 0})
        job = {"hid": self.getHid(), "wid": wid, "task": task, "more": params, "data": boss.getData(), "preferences": boss.getPreferences()}
        return details, job
    # DUMMY METHODS END

    # SHARED METHODS START
    def getParameters(self):
        return self.work_server

    def getWorkEstimate(self):
        work_estimate = 0
        work_progress = 0
        for worker in self.workers.values():
            work_estimate += worker["work_estimate"]
            work_progress += worker["work_progress"]
        # progress should not go over estimate, but well...
        work_progress = min(work_progress, work_estimate)
        return work_estimate, work_progress

    def nbWorkers(self):
        return len(self.workers)

    def nbWorking(self):
        return len(self.workers)+len(self.off)

    def findWid(self, fields):
        for wid, worker in sorted(self.workers.items()):
            found = True
            for f, v in fields:
                found &= (worker.get(f, None) == v)
            if found:
                return wid
        return None

    def getWorkersDetails(self):
        details = []
        for wid, worker in sorted(self.workers.items()):
            details.append({"wid": wid, "task": worker["task"]})
        return details

    # Warning, changing the logid of miner processes impacts handling of results below

    def handlePieceComm(self, piece):
        source = self.getSourceWid(piece["source"])  # in case the miner is multiprocess
        # Error causing the end of worker
        if piece["type_message"] == "error" and source in self.workers and piece["source"][-1] == "!":
            self.retire(piece["source"])
        # Natural end of worker
        elif piece["type_message"] == "progress":
            # print("Progress")
            if piece.get("message") is None and (source in self.workers or source in self.off):
                self.retire(source)
            elif len(piece.get("message", [])) > 1 and source in self.workers:
                self.workers[source]["work_progress"] = piece["message"][1]
                self.workers[source]["work_estimate"] = piece["message"][0]
    # SHARED METHODS END
