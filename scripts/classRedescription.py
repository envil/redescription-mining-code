import re, pickle, sys, pdb
from scipy.stats import binom, hypergeom
from classRule import  *

class Redescription:
    nbVariables = 3
    diff_terms = Rule.diff_terms
    diff_cols = Rule.diff_cols
    diff_op = Rule.diff_op
    diff_balance = Rule.diff_balance
    diff_length = Rule.diff_length
    diff_score = diff_length + 1
    
    def __init__(self, nruleL, nruleR, nsupps = None, nN = -1, navailableCols = [set(),set()]):
        self.rules = [nruleL, nruleR]
        if nsupps == None:
            self.sAlpha = set()
            self.sBeta = set()
            self.sGamma = set([-1])
        elif type(nsupps) == list and len(nsupps) == 3:
            self.sAlpha = nsupps[0]
            self.sBeta = nsupps[1]
            self.sGamma = nsupps[2]
        elif type(nsupps) == list and len(nsupps) == 2:
            self.sAlpha = nsupps[0] - nsupps[1]
            self.sBeta = nsupps[1] - nsupps[0]
            self.sGamma =  nsupps[0] & nsupps[1]
        else:
            raise Exception('Non interpretable redescription !\n')
        self.N = nN
        self.lAvailableCols = navailableCols
        
    def fromInitialPair(initialPair, data, souvenirs):
        ruleL = Rule()
        ruleR = Rule()
        ruleL.extend(None, initialPair[1])
        ruleR.extend(None, initialPair[2])
        r = Redescription(ruleL, ruleR, [data.supp(0, initialPair[1]), data.supp(1, initialPair[2])], data.N) 
        r.lAvailableCols = [set(souvenirs.availableMo[0]), set(souvenirs.availableMo[1])] 
        return r
    fromInitialPair = staticmethod(fromInitialPair)

    def compare(x, y):
        if x.score() > y.score():
            return Redescription.diff_score
        elif x.score() == y.score():
            return Rule.comparePair(x.rules[0], x.rules[1], y.rules[0], y.rules[1])
        else:
            return -Redescription.diff_score
    compare = staticmethod(compare)
    
    def equivalent(self, y):
       return abs(Redescription.compare(self, y)) < Redescription.diff_balance

    def __cmp__(self, other):
        if other == None:
            return 1
        else:
            return Redescription.compare(self,other)
        
    def __hash__(self):
        return int(hash(self.rules[0])+ hash(self.rules[1])*100*self.score())
        
    def __len__(self):
        return len(self.rules[0]) + len(self.rules[1])
        
    def oneSideIdentical(self, redescription, count_ids= [0,0], max_iden = 0):
        found = False
        if self.rules[0] == redescription.rules[0]:
            count_ids[0] += 1
            found |= (count_ids[0] >= max_iden)
        if self.rules[1] == redescription.rules[1]:
            count_ids[1] += 1
            found |= (count_ids[1] >= max_iden)
        return found

    def score(self):
        return self.acc()
    
    def suppL(self):
        return self.sAlpha | self.sGamma
    def suppR(self):
        return self.sBeta | self.sGamma
    def suppI(self):
        return self.sGamma
    def suppU(self):
        return self.sAlpha | self.sBeta | self.sGamma
    def acc(self):
        return float(len(self.sGamma))/(len(self.sAlpha) + len(self.sBeta) + len(self.sGamma))

#     def pOverlap(self):
#         return sum(hypergeom.pmf(range(self.lenI()+1,min(self.lenL(),self.lenR())+1), self.N, self.lenL(), self.lenR()))
    
    def lenL(self):
        return len(self.sAlpha) + len(self.sGamma)
    def lenR(self):
        return len(self.sBeta) + len(self.sGamma)
    def lenI(self):
        return len(self.sGamma)
    def lenU(self):
        return len(self.sAlpha) + len(self.sBeta) + len(self.sGamma)
    def acc(self):
        return float(self.lenI())/(self.lenU())

    def delta(self):
        return set(range(self.N)) - self.sAlpha - self.sBeta - self.sGamma

    def parts(self):
        return ( self.sAlpha, self.sBeta, self.sGamma, self.delta())
    
    def rule(self, side):
        return self.rules[side]
    
    def cutShort(self):
        return not self.hasAvailableCols() and (not self.fullLength(0) or not self.fullLength(1))
    
    def fullLength(self, side):
        return len(self.rules[side]) >= self.nbVariables
    def length(self, side):
        return len(self.rules[side])
        
    def availableColsSide(self, side):
        return self.lAvailableCols[side]
    def nbAvailableColsSide(self, side):
        return len(self.lAvailableCols[side])
    def nbAvailableCols(self):
        return self.nbAvailableColsSide(0) + self.nbAvailableColsSide(1)
    def updateAvailable(self, souvenirs):
        nb_extensions = [0,0]
        for side in [0,1]:
            if self.nbAvailableColsSide(side) > 0:
                self.lAvailableCols[side] =  souvenirs.availableMo[side] - souvenirs.extOneStep(self, side)
                nb_extensions[side] = len(souvenirs.availableMo[side]) - self.length(side) - self.nbAvailableColsSide(side)
        return nb_extensions[0]+nb_extensions[1]


    def update(self, data, side= -1, op = None, term= None):
        if side == -1 :
            self.lAvailableCols = [set(),set()]
        else:
            self.rules[side].extend(op, term)
            suppX = data.supp(side, term)
            if side == 0:
                if op.isOr():
                    self.sAlpha |= (suppX - self.sBeta - self.sGamma)
                    self.sGamma |= (self.sBeta & suppX) 
                    self.sBeta  -=  suppX
                else :
                    self.sBeta |= (self.sGamma - suppX)
                    self.sGamma &= suppX 
                    self.sAlpha &= suppX
            else:
                if op.isOr():
                    self.sBeta  |= (suppX - self.sAlpha - self.sGamma)
                    self.sGamma |= (self.sAlpha & suppX) 
                    self.sAlpha -=  suppX
                else :
                    self.sAlpha |= (self.sGamma - suppX)
                    self.sGamma &= suppX 
                    self.sBeta &= suppX
                    
            if len(self.rules[side]) >= self.nbVariables :
                self.lAvailableCols[side] = set()
            else:
                self.lAvailableCols[side].remove(term.col())

    def kid(self, data, side= -1, op = None, term= None):
        ##pdb.set_trace()
        kid = self.copy()
        if side == -1 :
            kid.lAvailableCols = [set(),set()]
        else:
            kid.rules[side].extend(op, term)
            suppX = data.supp(side, term)
            if side == 0:
                if op.isOr():
                    kid.sAlpha |= (suppX - kid.sBeta - kid.sGamma)
                    kid.sGamma |= (kid.sBeta & suppX) 
                    kid.sBeta  -=  suppX
                else :
                    kid.sBeta |= (kid.sGamma - suppX)
                    kid.sGamma &= suppX 
                    kid.sAlpha &= suppX
            else:
                if op.isOr():
                    kid.sBeta  |= (suppX - kid.sAlpha - kid.sGamma)
                    kid.sGamma |= (kid.sAlpha & suppX) 
                    kid.sAlpha -=  suppX
                else :
                    kid.sAlpha |= (kid.sGamma - suppX)
                    kid.sGamma &= suppX 
                    kid.sBeta &= suppX
                    
            if len(kid.rules[side]) >= kid.nbVariables :
                kid.lAvailableCols[side] = set()
            else:
                kid.lAvailableCols[side].remove(term.col())

        return kid
            
    def copy(self):
        return Redescription(self.rules[0].copy(), self.rules[1].copy(), [set(self.sAlpha), set(self.sBeta), set(self.sGamma)], self.N, [set(self.lAvailableCols[0]),set(self.lAvailableCols[1] )])

    ## return the support associated to a rule and a list of the items involved in it
    ## the list contains pairs (column id, negated)
    def recompute(self, side, data= None):
        return self.rules[side].recompute(side, data)
    
    def invTermsSide(self, side):
        return self.rules[side].invTerms()

    def invTerms(self):
        return [self.invTermsSide(0), self.invTermsSide(1)]
    
    def invColsSide(self, side):
        return self.rules[side].invCols()

    def invCols(self):
        return [self.invColsSide(0), self.invColsSide(1)]
    
    def check(self, data):
        if self.sGamma != set([-1]):
            nsuppL = self.recompute(0, data)
            nsuppR = self.recompute(1, data)
            nsAlpha = nsuppL - nsuppR
            nsBeta = nsuppR - nsuppL
            nsGamma =  nsuppL & nsuppR

            res= ( len(nsAlpha.symmetric_difference(self.sAlpha)) == 0, \
                     len(nsBeta.symmetric_difference(self.sBeta)) == 0, \
                     len(nsGamma.symmetric_difference(self.sGamma)) == 0 )
            if res[0] *res[1] *res[2] == 0:
                pdb.set_trace()
            return res


    def compliesWith(self, criterions):
        complies = True
        for crit in criterions:
            complies &= eval(crit.replace(':red:', 'self.')) 
        return complies
        

    def __str__(self):
        return '(%i %i,  %i / %i\t = %f) %i + %i items:\t (%i): %s <=> %s' \
                  % (self.lenL(), self.lenR(), \
                     self.lenI(), self.lenU(), self.acc(), \
                     self.nbAvailableColsSide(0), self.nbAvailableColsSide(1), \
                     len(self), self.rules[0], self.rules[1])

 #    def dispLong(self):
#         return '(%i %i,  %i / %i\t = %f, %s) %i + %i items:\t (%i): %s <=> %s' \
#                   % (self.lenL(), self.lenR(), \
#                      self.lenI(), self.lenU(), self.acc(), self.surp(), \
#                      len(self.availableCols(0)), len(self.availableCols(1)), \
#                      self.rules[0].length() + self.rules[1].length(), self.rules[0].dispIds(), self.rules[1].dispIds())

    def dispCarateristiques(self):
        return 'acc:%f lenSuppL:%i lenSuppR:%i lenSupp:%i' \
             % (self.acc(), self.lenL(), self.lenR(), self.lenI())

    def dispCarateristiquesSimple(self):
        return '%f\t%i\t%i\t%i' \
             % (self.acc(), self.lenL(), self.lenR(), self.lenI())

    def disp(self, lenIndex=0, names= [None, None]):
        return self.rules[0].disp(lenIndex, names[0])+'\t<==>\t'+self.rules[1].disp(lenIndex, names[1])+'\n\t\t'+self.dispCarateristiques()

    def dispSimple(self, lenIndex=0, names = [None, None]):
        return self.rules[0].disp(lenIndex, names[0])+'\t'+self.rules[1].disp(lenIndex, names[1])+'\t'+self.dispCarateristiquesSimple()+'\n'

    def dispSupp(self):
        supportStr = ''
        for i in sorted(self.suppL()): supportStr += "%i "%i
        supportStr +="\t"
        for i in sorted(self.suppR()): supportStr += "%i "%i
        supportStr +="\n"
        return supportStr

#     def pValSupp(self, pr):
#         return 1-binom.cdf(self.lenI()-1,self.N,pr)

#     def pValOver(self):
#         ## It seems cdf doen't work => sum the pmf instead
#         return sum(hypergeom.pmf(range(self.lenI()+1,min(self.lenL(),self.lenR())+1), self.N, self.lenL(),self.lenR()))
#         ## return 1- sum(hypergeom.pmf(range(kInter), n, kOne, kTwo))
    
#     def minMaxExpAcc(self):
#     ##pdb.set_trace()
#         A = float(self.lenL());
#         B = float(self.lenR());
#         N = float(self.N);
#         return (max(0,(A+B)-N)/min(N, (A+B)), min(A,B)/max(A,B), A*B/(N*(A+B)-A*B))

#     def surp(self):
#         (min_acc, max_acc, exp_acc) = self.minMaxExpAcc()
#         return 'exp_acc: %f, min_acc: %f, max_acc: %f, d: %f, ratio: %f, pOver: %f' %(exp_acc, min_acc, max_acc, self.acc() -exp_acc, (self.acc()- min_acc)/max(0.001,(max_acc - min_acc)), self.pOverlap())
        

    def write(self, output, suppOutput):
        output.write(self.dispSimple())
        suppOutput.write(self.dispSupp())
        output.flush()
        suppOutput.flush()

    def parseSupport(string):
        nsupp = set()
        for i in string.strip().rsplit():
            try:
                nsupp.add(int(i))
            except TypeError, detail:
                raise Exception('Unexpected element in the support: %s\n' %i)
        return nsupp
    parseSupport = staticmethod(parseSupport)

    def parseRules(string):
        parts = string.rsplit('\t')

        if len(parts) >= 2:
            ruleL = Rule.parse(parts[0])
            ruleR = Rule.parse(parts[1])
        else:
            ruleL = Rule()
            ruleR = Rule()

        if len(parts) >= 3:
            try :
                acc = float(parts[2])
            except TypeError, detail:
                raise Exception('Unexpected accurracy in the rule: %s\n' %string)
        else:
            acc = -1

        if len(parts) >= 6:
            try :
                left = int(parts[3])
                right = int(parts[4])
                inter = int(parts[5])
            except TypeError, detail:
                raise Exception('Unexpected support in the rule: %s\n' %string)
        else:
            (left, right, inter) = (-1, -1, -1)

        return (ruleL, ruleR, acc, left, right, inter)
    parseRules = staticmethod(parseRules)

    def parse(stringRules, stringSupport = None):
        (ruleL, ruleR, acc, left, right, inter) = Redescription.parseRules(stringRules)

        if stringSupport != None and type(stringSupport) == str and re.search('\t', stringSupport) :
            partsSupp = stringSupport.rsplit('\t')
            nsuppL = Redescription.parseSupport(partsSupp[0])
            nsuppR = Redescription.parseSupport(partsSupp[1])

            r = Redescription(ruleL, ruleR, [nsuppL, nsuppR])
            
            if r.lenL() != left or r.lenR() != right or r.lenI() != inter :
                raise Warning("Something wrong in the supports ! (%i ~ %i, %i ~ %i, %i ~ %i)\n" \
                                 % (r.lenL(), left,  r.lenR(), right,  r.lenI(), inter))
        else:
            r = Redescription(ruleL, ruleR)
        return r
    parse = staticmethod(parse)
        
            
    def load(rulesFp, supportsFp = None):
        stringRules = rulesFp.readline()
        if type(supportsFp) == file :
            stringSupp = supportsFp .readline()
        else: stringSupp= None
        return Redescription.parse(stringRules, stringSupp)
    load = staticmethod(load)
