from classLog import Log
from classRedescription import  Redescription
from classSParts import SParts
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
        
    def setRedLength(self, n):
        self.credLength = n
    def redLength(self):
        return self.credLength

    def minItmSuppIn(self):
        if self.credLength > 0:
            return self.cminSuppIn
        else:
            return 0
    def minItmSuppOut(self):
        return self.cminSuppOut
        # if self.credLength > 0:
        #     return self.cminSuppOut
        # else:
        #     return 0
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
                   and red.lenO() >= self.minFinSuppOut() \
                   and red.lenI() >= self.minFinSuppIn() \
                   and red.acc()  >= self.minFinAcc() \
                   and red.pVal() <= self.maxFinPVal():
            Constraints.logger.printL(3, 'Redescription complies with final constraints ... (%s)' %(red))
            return True
        else:
            Constraints.logger.printL(3, 'Redescription non compliant with final constraints ...(%s)' % (red))
            return False

    def compAcc(self, side, op, neg, lparts, lmiss, lin):
        lout = [lparts[i] - lmiss[i] - lin[i] for i in range(len(lparts))]
        return SParts.compAcc(side, op, neg, (lin, lout, lmiss, lparts))

    def compAdv(self, t, side, op, neg, lparts, lmiss, lin):
        lout = [lparts[i] - lmiss[i] - lin[i] for i in range(len(lparts))]
        return SParts.compAdv(t, side, op, neg, (lin, lout, lmiss, lparts), (self.minItmC(), self.minItmSuppIn(), self.minItmSuppOut()))

    def queryTypes(self):
        return self.cqueryTypes

    def queryTypesOp(self):
        if self.credLength == 0:
            return [True]
        else:
            return [i for i in self.cqueryTypes.keys() if len(self.cqueryTypes[i])> 0]

    def negTypesInit(self):
        if True in self.cqueryTypes[True] or True in self.cqueryTypes[False]:
            return [(0, False, False), (1, False, True), (2, True, False), (3, True, True)]
        else:
            return [(0, False, False)]

    def queryTypesNP(self, opOR):
        if self.credLength == 0:
            return self.cqueryTypes[True] | self.cqueryTypes[False] 
        else:
            return self.cqueryTypes[opOR]

    def inSuppBounds(self, side, op, lparts):
        return SParts.sumPartsId(side, SParts.IDS_varnum[op] + SParts.IDS_fixnum[op], lparts) >= self.minItmSuppIn() \
               and SParts.sumPartsId(side, SParts.IDS_cont[op], lparts) >= self.minItmC()
    
    def inSuppBoundsMode(self, lenModeL, lenModeR, N, nbBuksL=1, nbBuksR=1):
        return (lenMode >= self.minItmSuppIn() and lenMode >= self.minItmC()) 
