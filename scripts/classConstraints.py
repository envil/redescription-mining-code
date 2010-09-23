from classLog import Log
from classRedescription import  Redescription
from classSParts import SParts
import re
import pdb
        
class Constraints:
    default = {'min_length': 2, 'contribution': 3, 'min_score': 0.01, 'forbid_rules' : '',	                
              'min_suppin': 0.1, 'min_suppout': 0.7, 'min_acc': 0.0, 'max_pval': 0.05 }

    logger = Log(0)

    def __init__(self, data, setts_cust={}):
        setts = dict(Constraints.default)
        setts.update(setts_cust)
        self.cminPairsScore = setts['min_score']
        (self.cminC, self.cminSuppIn, self.cminSuppOut) = data.scaleSuppParams(setts['contribution'], setts['min_suppin'], setts['min_suppout'])
        (self.cminLen, self.cminAcc, self.cmaxPVal) = (setts['min_length'], setts['min_acc'], setts['max_pval'])

        #pdb.set_trace()
        self.cruleTypes = {False: set([False, True]), True: set([False, True])}
        if re.search('(^|,)andnots($|,)', setts['forbid_rules']): self.cruleTypes[False].remove(True)
        if re.search('(^|,)ornots($|,)', setts['forbid_rules']): self.cruleTypes[True].remove(True)
        if re.search('(^|,)nots($|,)', setts['forbid_rules']): self.cruleTypes[False].remove(True); self.cruleTypes[True].remove(True)
        if re.search('(^|,)ands($|,)', setts['forbid_rules']): self.cruleTypes[False] = set()
        if re.search('(^|,)ors($|,)', setts['forbid_rules']): self.cruleTypes[True] = set()
        
        self.credLength = 0
        

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
                   and red.sParts.lenO() >= self.minFinSuppOut() \
                   and red.sParts.lenI() >= self.minFinSuppIn() \
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

    def ruleTypesOp(self):
        if self.credLength == 0:
            return [True]
        else:
            return [i for i in self.cruleTypes.keys() if len(self.cruleTypes[i])> 0]

    def negTypesInit(self):
        if True in self.cruleTypes[True] or True in self.cruleTypes[False]:
            return [(0, False, False), (1, False, True), (2, True, False), (3, True, True)]
        else:
            return [(0, False, False)]

    def ruleTypesNP(self, opOR):
        if self.credLength == 0:
            return self.cruleTypes[True] | self.cruleTypes[False] 
        else:
            return self.cruleTypes[opOR]

    def inSuppBounds(self, side, op, lparts):
        return SParts.sumPartsId(side, SParts.IDS_varnum[op] + SParts.IDS_fixnum[op], lparts) >= self.minItmSuppIn() \
               and SParts.sumPartsId(side, SParts.IDS_cont[op], lparts) >= self.minItmC()
    
    def inSuppBoundsMode(self, lenModeL, lenModeR, N, nbBuksL=1, nbBuksR=1):
        return (lenMode >= self.minItmSuppIn() and lenMode >= self.minItmC()) 
