class WorkInactive:

    def __init__(self):
        self.work_server = (None, None, None)

    def __trunc__(self):
            return 100000

    def getParameters(self):
        return self.work_server

    def getParametersD(self):
        return {"workserver_ip": ""}
    
    def isActive(self):
        return False

    def getWorkEstimate(self):
        return (0,0)
    def nbWorkers(self):
        return 0
    def nbWorking(self):
        return 0
    def getWorkersDetails(self):
        return 0

    def getDetailedInfos(self):
        return "KO"
    def infoStr(self):
        return "Inactive"

    def layOff(self, wid):
        pass
    def closeDown(self, parent):
        pass
    def addWorker(self, wtype, boss, more=None, details={}):
        pass
    def findWid(self, fields):
        pass
    def checkResults(self, parent):
        pass

    def getOutQueue(self):
        return None
    def sendMessage(self):
        pass
