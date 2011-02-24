from classLog import Log
from classRedescription import  Redescription
import re
import pdb
        
class Constraints:
    logger = Log(0)

    def __init__(self, data, setts_cust=None):
        self.cminPairsScore = setts_cust.param['min_score']
        (self.cminC, self.cminSuppIn, self.cminSuppOut) = data.scaleSuppParams(setts_cust.param['contribution'], setts_cust.param['min_suppin'], setts_cust.param['min_suppout'])
        (self.cminLen, self.cminAcc, self.cmaxPVal) = (setts_cust.param['min_length'], setts_cust.param['min_acc'], setts_cust.param['max_pval'])
        self.cqueryTypes = setts_cust.param['query_types']
        self.credLength = 0

    def queryTypes(self):
        return self.cqueryTypes

    def setRedLength(self, n):
        self.credLength = n
    def redLength(self):
        return self.cRedLength

    def minItmSuppIn(self):
        return self.cminSuppIn
    def minItmSuppOut(self):
        return self.cminSuppOut
    def minItmC(self):
        return self.cminC
    def minFinSuppIn(self):
        return self.cminSuppIn
    def minFinSuppOut(self):
        return self.cminSuppOut
    def minFinLength(self):
        return self.cminLen
    def maxFinPVal(self):
        return self.cmaxPVal    
    def minFinAcc(self):
        return self.cminAcc
    def minPairsScore(self):
        return self.cminPairsScore
    
    def checkFinalConstraints(self,red):
        if red.length(0) + red.length(1) >= self.minFinLength() \
                   and red.lenU() >= self.minFinSuppOut() \
                   and red.lenI() >= self.minFinSuppIn() \
                   and red.acc()  >= self.minFinAcc() \
                   and red.pVal() <= self.maxFinPVal():
            Constraints.logger.printL(3, 'Redescription complies with final constraints ... (%s)' %(red))
            return True
        else:
            Constraints.logger.printL(3, 'Redescription non compliant with final constraints ...(%s)' % (red))
            return False

