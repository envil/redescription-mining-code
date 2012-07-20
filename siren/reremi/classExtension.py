from classQuery import Op
from classRedescription import Redescription
from classSParts import SParts
import pdb

class Extension:

    def __init__(self, adv=None, clp=None, sol=None):
        ### self.adv is a tuple: acc, varBlue, varRed, contrib, fixBlue, fixRed
        
        if adv is not None and len(adv) == 3 and len(adv[2]) == 3 and clp==None and sol==None:
            self.adv = adv[0]
            self.clp = adv[1]
            self.side, self.op, self.literal = adv[2]

        else:
            self.adv = adv
            self.clp = clp
            if sol is not None:
                self.side, self.op, self.literal = sol
            else:
                self.side, self.op, self.literal = None, None, None

    def getLiteral(self):
        if self.isValid():
            return self.literal

    def getOp(self):
        if self.isValid():
            return self.op

    def getSide(self):
        if self.isValid():
            return self.side

    def getAcc(self):
        if self.isValid():
            return self.adv[0]

    def getVarBlue(self):
        if self.isValid():
            return self.adv[1]

    def getVarRed(self):
        if self.isValid():
            return self.adv[2]

    def getCLP(self):
        if self.isValid():
            return self.clp
    
    def kid(self, red, data):
        supp = data.supp(self.getSide(), self.getLiteral())
        miss = data.miss(self.getSide(), self.getLiteral())
        return red.kid(data, self.getSide(), self.getOp(), self.getLiteral(), supp, miss)

    def isValid(self):
        return self.adv is not None and len(self.adv) > 2

    def isNeg(self):
        if self.isValid():
            return self.getLiteral().isNeg()

    def __str__(self):
        if self.isValid():
            return "Extension:\t (%d, %s, %s) -> %f" % (self.getSide(), Op(self.getOp()), self.getLiteral(), self.getAcc()) 
        else:
            return "Empty extension"

    def disp(self, base_acc=None, N=0, prs=None, coeffs=None):
        strPieces = ["", "", ""]
        if self.isValid():
            strPieces[self.getSide()] = str(Op(self.getOp())) + " " + str(self.getLiteral()) 
            if base_acc is None:
                strPieces[-1] = '----\t%1.7f\t----\t----\t% 5i\t% 5i' \
                                % (self.getAcc(), self.getVarBlue(), self.getVarRed())
            else:
                strPieces[-1] = '\t\t%+1.7f \t%1.7f \t%1.7f \t%1.7f\t% 5i\t% 5i' \
                                % (self.score(base_acc, N, prs, coeffs), self.getAcc(), \
                                   self.pValQuery(N, prs), self.pValRed(N, prs) , self.getVarBlue(), self.getVarRed())

        return '* %20s <==> * %20s %s' % tuple(strPieces)
            
    def score(self, base_acc, N, prs, coeffs):
        if self.isValid():
            return coeffs["impacc"]*self.impacc(base_acc) \
                   + coeffs["rel_impacc"]*self.relImpacc(base_acc) \
                   + self.pValRedScore(N, prs, coeffs) \
                   + self.pValQueryScore(N, prs, coeffs)

    def relImpacc(self, base_acc=0):
        if self.isValid():
            if base_acc != 0:
                return (self.adv[0] - base_acc)/base_acc
            else:
                return self.adv[0]
        
    def impacc(self, base_acc=0):
        if self.isValid():
            return (self.adv[0] - base_acc)
        
    def pValQueryScore(self, N, prs, coeffs=None):
        if self.isValid():
            if coeffs is None or coeffs["pVal_query"] < 0:
                return coeffs["pVal_query"] * SParts.pValQuery(N, prs)
            elif coeffs["pVal_query"] > 0:
                return -coeffs["pVal_fact"]*(coeffs["pVal_query"] < self.pValQuery(N, prs))
            else:
                return 0

    def pValRedScore(self, N, prs, coeffs=None):
        if self.isValid():
            if coeffs is None or coeffs["pVal_red"] < 0:
                return coeffs["pVal_red"] * self.pValRed(N, prs)
            elif coeffs["pVal_red"] > 0:
                return -coeffs["pVal_fact"]*(coeffs["pVal_red"] < self.pValRed(N, prs))
            else:
                return 0

    def pValQuery(self, N=0, prs=None):
        if self.isValid():
            return SParts.pValQueryCand(self.side, self.op, self.isNeg(), self.clp, N, prs)

    def pValRed(self, N=0, prs=None):
        if self.isValid():
            return SParts.pValRedCand(self.side, self.op, self.isNeg(), self.clp, N, prs)

    def __cmp__(self, other):
        return self.compare(other)
    
    def compare(self, other):
        tmp = self.compareAdv(other)
        if tmp == 0:
            return cmp(self.getLiteral(), other.getLiteral())

    def compareAdv(self, other):
        if other is None:
            return 1
        if not self.isValid():
            return -1

        if type(other) in [tuple, list]:
            other_adv = other
        else:
            other_adv = other.adv

        return cmp(self.adv, other_adv)
        
    
class ExtensionsBatch:
    def __init__(self, N=0, coeffs=None, current=None):
        self.current = current
        self.base_acc = self.current.acc()
        self.N = N
        self.prs = self.current.probas()
        self.coeffs = coeffs
        self.bests = {}

    def scoreCand(self, cand):
        if cand is not None:
            #if cand.literal.term.col == 1: pdb.set_trace()
            return cand.score(self.base_acc, self.N, self.prs, self.coeffs)

    def pos(self, cand):
        if cand.isValid():
            return (cand.getSide(), cand.getOp())

    def get(self, pos):
        if self.bests.has_key(pos):
            return self.bests[pos]
        else:
            return None
        
    def update(self, cands):
        for cand in cands:
            pos = self.pos(cand)
            self.scoreCand(cand)
            if pos is not None and (not self.bests.has_key(pos) or self.scoreCand(cand) > self.scoreCand(self.bests[pos])):
                self.bests[pos] = cand

    def improving(self, min_impr=0):
        return dict([(pos, cand)  for (pos, cand) in self.bests.items() \
                     if self.scoreCand(cand) >= min_impr])

    def improvingKids(self, data, min_impr=0, max_var=-1):
        kids = []
        for (pos, cand) in self.bests.items():
            if self.scoreCand(cand) >= min_impr:
                kid = cand.kid(self.current, data)
                kid.setFull(max_var)
                if kid.acc() != cand.getAcc(): raise Error('Something went badly wrong during expansion\nof %s\n\t%s ~> %s' % (self.current, cand, kid))
                kids.append(kid)
        return kids
        
    def __str__(self):
        dsp  = 'Extensions Batch:\n' 
        dsp += 'Redescription: %s' % self.current
        dsp += '\n\t  %20s        %20s' \
                  % ('LHS extension', 'RHS extension')
            
        dsp += '\t\t%10s \t%9s \t%9s \t%9s\t% 5s\t% 5s' \
                      % ('score', 'Accuracy',  'Query pV','Red pV', 'toBlue', 'toRed')
            
        for k,cand in self.bests.items(): ## Do not print the last: current redescription
            dsp += '\n\t%s' % cand.disp(self.base_acc, self.N, self.prs, self.coeffs)
        return dsp
