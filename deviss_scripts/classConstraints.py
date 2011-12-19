from classLog import Log
from classRedescription import  Redescription
from classSParts import SParts
import re
import pdb
class Constraints:
    logger = Log(0)
    
    def __init__(self, data, setts_cust=None):
        self.cminPairsScore = 0 #setts_cust.param['min_score']        
        (self.cminC, self.cminSuppIn, self.cminSuppOut) = data.scaleSuppParams(setts_cust.param['contribution'], setts_cust.param['min_suppin'], setts_cust.param['min_suppout'])
        (self.cminLen, self.cminAcc, self.cmaxPVal) = (setts_cust.param['min_length'], setts_cust.param['min_acc'], setts_cust.param['max_pval'])
        (self.cmaxOvP, self.cmaxBestAccRP) = (setts_cust.param['max_ovp'], setts_cust.param['max_accrp'])
        self.cqueryTypes = setts_cust.param['query_types']
        self.credLength = 0

    def redLength(self):
        return self.credLength
    def setRedLength(self, n):
        self.credLength = n
    def incRedLength(self):
        self.credLength += 1

    def redLength(self):
        return self.credLength

    def maxPVal(self):
        return self.cmaxPVal    

    def maxOvP(self):
        return self.cmaxOvP
    def maxBestAccRP(self):
        return self.cmaxBestAccRP

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

    def queryTypesOp(self, side):
        if self.credLength == 0:
            return [True]
        else:
            return [i for i in self.cqueryTypes[side].keys() if len(self.cqueryTypes[side][i])> 0]

    def negTypesInit(self):
        tmp = [(0, False, False)]
        if True in self.cqueryTypes[1][True]:
            tmp.append((1, False, True))
            if True in self.cqueryTypes[0][False]:
                tmp.append((2, True, False))
                tmp.append((3, True, True))
        else:
            if True in self.cqueryTypes[0][False]:
                tmp.append((2, True, False))
        return tmp

    def queryTypesNP(self, opOR, side):
        if self.credLength == 0:
            return self.cqueryTypes[side][True] | self.cqueryTypes[side][False] 
        else:
            return self.cqueryTypes[side][opOR]

    def inSuppBounds(self, side, op, lparts):
        return SParts.sumPartsId(side, SParts.IDS_varnum[op] + SParts.IDS_fixnum[op], lparts) >= self.minItmSuppIn() \
               and SParts.sumPartsId(side, SParts.IDS_cont[op], lparts) >= self.minItmC()
    
    def inSuppBoundsMode(self, lenModeL, lenModeR, N, nbBuksL=1, nbBuksR=1):
        return (lenMode >= self.minItmSuppIn() and lenMode >= self.minItmC()) 

    def isGoodKid(self, redE, redsO, op):
        return (redE.pVal() < self.maxPVal() and redE.acc() > max([red[1]['acc'] for red in redsO]))
# #        pdb.set_trace()
#         print 25*"-"
#         print redA.dispSimple()
#         print redB.dispSimple()
#         print redE.dispSimple()
#        return (redE.pVal() < self.maxPVal() and min(redE.acc(), redE.opacc()) > 0.95*max([max(red.acc(), red.opacc()) for red in redsO]))

         
