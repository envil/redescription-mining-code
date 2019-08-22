import pdb
class WorkInactive:

    type_workers = {}

    next_wid = 0
    step_wid = 1
    @classmethod
    def generateNextWid(tcl):        
        tcl.next_wid += tcl.step_wid
        return tcl.next_wid

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
    
    def __init__(self):
        self.work_server = (None, None, None, None)
        self.workers = {}
        self.off = {}
        self.retired = {}

#### DUMMY METHODS START, inactive
    def __trunc__(self):
        return 100000

    def isActive(self):
        return False

    def getParametersD(self):
        return {"workserver_ip": ""}

    def getDetailedInfos(self):
        return "KO", "", []
    def infoStr(self):
        return "Inactive"
    
    def checkResults(self, parent):
        pass
    def getOutQueue(self):
        return None
    def sendMessage(self):
        pass
    def layOff(self, wid):
        pass
    def closeDown(self, parent, collectLater = False):
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
        
    def prepareWorkerDetails(self, boss, params=None, details={}, wid=None):
        task = self.getTask(params, details)
        details.update({"task": task, "work_progress":0, "work_estimate":0})
        if task != "project":
            details.update({"results_last": 0, "src_lid": "P", "results_tab": "exp"})
        if task == "mine":
            details["batch_type"] = "F"
        job = {"hid": self.getHid(), "wid": wid, "task": task, "more": params, "data": boss.getData(), "preferences": boss.getPreferences()}
        return details, job
    
#### DUMMY METHODS END

#### SHARED METHODS START
    def getParameters(self):
        return self.work_server

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
            details.append({"wid": wid, "task": worker["task"]})
        return details

    def handlePieceResult(self, note, updates, parent):
        if note["type_message"] in self.type_messages:
            if note["type_message"] == "result":
                self.sendResult(note["source"], note["message"], updates, parent)
            elif note["type_message"] == "tracks":
                self.sendTracks(note["source"], note["message"], updates, parent)
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
        elif source in self.off and message is None:
            self.retire(source)
            updates["menu"] = True
            updates["progress"] = True
            
    def sendTracks(self, source, message, updates, parent):
        if source not in self.workers or parent is None:
            return        
        latest_tracks = self.mapTracks(message, source)
        parent.readyTracks(latest_tracks, source)

    def sendResult(self, source, message, updates, parent):
        if source not in self.workers:
            return
        
        worker_info = self.workers[source]
        if worker_info["task"] in ["project"]:
            if parent is None:
                print("Ready proj %s %s %s" % ((source, worker_info["task"]), worker_info["vid"], message))
            else:
                parent.readyProj((source, worker_info["task"]), worker_info["vid"], message)

        elif worker_info.get("src_lid") is not None and worker_info.get("src_lid") in message:
            tap = message[worker_info["src_lid"]]
            nb_tap = len(tap)
            if nb_tap > worker_info["results_last"]:
                latest_reds = [self.mapRid(red, source) for red in tap[worker_info["results_last"]:nb_tap]]
                if worker_info["src_lid"] != "P": ### WARNING!!!
                    worker_info["results_last"] = nb_tap                                       
                if parent is None:
                    print("Ready reds [%s] %s %s" % ((source, worker_info["task"]), latest_reds, worker_info["results_tab"]))
                else:
                    parent.readyReds((source, worker_info["task"]), latest_reds, worker_info["results_tab"])
                    
    def mapRid(self, red, source):
        return red

    def mapTracks(self, in_tracks, source=None):
        return in_tracks
#### SHARED METHODS END
