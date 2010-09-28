import re, pickle, sys, pdb
from classLog import Log
import utilsStats
# from scipy.stats import binom, hypergeom
from classRule import  *

class Redescription:
    logger = Log(0)
    nbVariables = 3
    sym_alpha = 0
    sym_beta = 1
    sym_gamma = 2
    sym_delta = 3
    diff_terms = Rule.diff_terms
    diff_cols = Rule.diff_cols
    diff_op = Rule.diff_op
    diff_balance = Rule.diff_balance
    diff_length = Rule.diff_length
    diff_score = diff_length + 1
    methodpVal = 'Marg'
    
    def __init__(self, nruleL, nruleR, nsupps = None, nN = -1, navailableCols = [set(),set()], nPrs = [-1,-1]):
        try:
            self.pVal = eval('self.pVal%s' % (Redescription.methodpVal))
        except AttributeError:
              raise Exception('Oups method to compute the p-value does not exist !')
        
        self.rules = [nruleL, nruleR]
        self.prs = nPrs
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
        self.vectorABCD = None #Redescription.makeVectorABCD(self.nbAvailableCols()>0, self.N, self.sAlpha, self.sBeta, self.sGamma)
        
    def fromInitialPair(initialPair, data):
        ruleL = Rule()
        ruleR = Rule()
        ruleL.extend(None, initialPair[0])
        ruleR.extend(None, initialPair[1])
        suppL = data.supp(0, initialPair[0])
        suppR = data.supp(1, initialPair[1])
        r = Redescription(ruleL, ruleR, [suppL, suppR], data.N, data.nonFull(), [float(len(suppL))/data.N, float(len(suppR))/data.N]) 
        r.vectorABCD = data.makeVectorABCD(r.sAlpha, r.sBeta, r.sGamma)
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

    def lenX(self, side):
        if side == 0:
            return self.lenL()
        else:
            return self.lenR()
    def lenAlpha(self):
        return len(self.sAlpha)
    def lenBeta(self):
        return len(self.sBeta)
    def lenGamma(self):
        return len(self.sGamma)
    def lenDelta(self):
        return self.N - len(self.sAlpha) - len(self.sBeta) - len(self.sGamma)
    def lenL(self):
        return len(self.sAlpha) + len(self.sGamma)
    def lenR(self):
        return len(self.sBeta) + len(self.sGamma)
    def lenI(self):
        return len(self.sGamma)
    def lenU(self):
        return len(self.sAlpha) + len(self.sBeta) + len(self.sGamma)
    def acc(self):
        lU = self.lenU()
        if lU > 0:
            return float(self.lenI())/lU
        else:
            return 0

    def proba(self, side, data):
        return self.rules[side].proba(side, data)

    def delta(self):
        return set(range(self.N)) - self.sAlpha - self.sBeta - self.sGamma

    def parts(self):
        return ( self.sAlpha, self.sBeta, self.sGamma, self.delta(), self.vectorABCD)
    
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


    def update(self, data, side= -1, op = None, term= None, suppX=None):
        if side == -1 :
            self.lAvailableCols = [set(),set()]
        else:
            self.rules[side].extend(op, term)
            self.prs[side] = Rule.updateProba(self.prs[side], len(suppX)/float(data.N), op)
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
            if self.nbAvailableCols() > 0:
                self.vectorABCD = data.makeVectorABCD(self.sAlpha, self.sBeta, self.sGamma)
            else:
                self.vectorABCD = None
                

    def kid(self, data, side= -1, op = None, term= None, suppX=None):
        
        kid = self.copy()
        if side == -1 :
            kid.lAvailableCols = [set(),set()]
        else:
            kid.rules[side].extend(op, term)
            kid.prs[side] = Rule.updateProba(kid.prs[side], len(suppX)/float(data.N), op)
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
                
            if kid.nbAvailableCols() > 0:
                kid.vectorABCD = data.makeVectorABCD(kid.sAlpha, kid.sBeta, kid.sGamma)
            else:
                kid.vectorABCD = None
                
        return kid
            
    def copy(self):
        return Redescription(self.rules[0].copy(), self.rules[1].copy(), \
                             [set(self.sAlpha), set(self.sBeta), set(self.sGamma)], self.N, \
                             [set(self.lAvailableCols[0]),set(self.lAvailableCols[1] )], [self.prs[0], self.prs[1]])

    ## return the support associated to a rule and a list of the items involved in it
    ## the list contains pairs (column id, negated)
    def recomputeRule(self, side, data= None):
        return self.rules[side].recompute(side, data)
    
    def invTermsSide(self, side):
        return self.rules[side].invTerms()

    def invTerms(self):
        return [self.invTermsSide(0), self.invTermsSide(1)]
    
    def invColsSide(self, side):
        return self.rules[side].invCols()

    def invCols(self):
        return [self.invColsSide(0), self.invColsSide(1)]

    def recompute(self, data):

        nsuppL = self.recomputeRule(0, data)
        nsuppR = self.recomputeRule(1, data)
        self.sAlpha = nsuppL - nsuppR
        self.sBeta = nsuppR - nsuppL
        self.sGamma =  nsuppL & nsuppR
        self.N = data.N
        self.prs = [self.rules[0].proba(0, data), self.rules[1].proba(1, data)]
    
    def check(self, data):
        if self.sGamma != set([-1]):
            nsuppL = self.recomputeRule(0, data)
            nsuppR = self.recomputeRule(1, data)
            nsAlpha = nsuppL - nsuppR
            nsBeta = nsuppR - nsuppL
            nsGamma =  nsuppL & nsuppR

            return ( len(nsAlpha.symmetric_difference(self.sAlpha)) == 0, \
                     len(nsBeta.symmetric_difference(self.sBeta)) == 0, \
                     len(nsGamma.symmetric_difference(self.sGamma)) == 0 )        

    def __str__(self):
        if self.sGamma != set([-1]):
            return '(%i %i,  %i / %i\t = %f, %f) %i + %i items:\t (%i): %s <=> %s' \
                  % (self.lenL(), self.lenR(), \
                     self.lenI(), self.lenU(), self.acc(), self.pVal(), \
                     self.nbAvailableColsSide(0), self.nbAvailableColsSide(1), \
                     len(self), self.rules[0], self.rules[1])
        elif hasattr(self, 'readInfo'):
            return '(%i %i,  %i / %i\t = %f, %f): %s <=> %s' \
                  % (self.readInfo['A'] + self.readInfo['C'], self.readInfo['B'] + self.readInfo['C'], \
                     self.readInfo['C'], self.readInfo['A'] + self.readInfo['C'] + self.readInfo['B'], self.readInfo['acc'], self.readInfo['pVal'], \
                     self.rules[0], self.rules[1])
        else:
            return 'Non printable redescription'
            
    def dispCaracteristiques(self):
        if self.sGamma != set([-1]):
            return 'acc:%f pVal:%f lenSuppAlpha:%i lenSuppBeta:%i lenSuppGamma:%i lenSuppDelta:%i' \
             % (self.acc(), self.pVal(), self.lenAlpha(), self.lenBeta(), self.lenGamma(), self.lenDelta())
        elif hasattr(self, 'readInfo'):
            return 'acc:%f pVal:%f lenSuppAlpha:%i lenSuppBeta:%i lenSuppGamma:%i lenSuppDelta:%i' \
             % (self.readInfo['acc'], self.pVal(), self.readInfo['A'], self.readInfo['B'], self.readInfo['C'], self.readInfo['D'])
        else:
            return 'Non printable redescription'
        

    def dispCaracteristiquesSimple(self):
        if self.sGamma != set([-1]):
            return '%f %f %i %i %i %i' \
             % (self.acc(), self.pVal(), self.lenAlpha(), self.lenBeta(), self.lenGamma(), self.lenDelta())
        elif hasattr(self, 'readInfo'):
            return '%f %f %i %i %i %i' \
             % (self.readInfo['acc'], self.readInfo['pVal'], self.readInfo['A'], self.readInfo['B'], self.readInfo['C'], self.readInfo['D'])
        else:
            return 'Non printable redescription'
        
    def disp(self, lenIndex=0, names= [None, None]):
        return self.rules[0].disp(lenIndex, names[0])+'\t<==>\t'+self.rules[1].disp(lenIndex, names[1])+'\t'+self.dispCaracteristiques()

    def dispSimple(self, lenIndex=0, names = [None, None]):
        return self.rules[0].disp(lenIndex, names[0])+'\t'+self.rules[1].disp(lenIndex, names[1])+'\t'+self.dispCaracteristiquesSimple()

    def dispSupp(self):
        supportStr = ''
        for i in sorted(self.suppL()): supportStr += "%i "%i
        supportStr +="\t"
        for i in sorted(self.suppR()): supportStr += "%i "%i
        return supportStr
    
    def pValSupp(self):
        if self.prs == [-1,-1] or self.N == -1:
            return -1
        else:
            return utilsStats.pValSupp(self.N, self.lenI(), self.prs[0]*self.prs[1]) 

    def pValMarg(self):
        if self.N == -1:
            return -1
        else:
            return utilsStats.pValSupp(self.N, self.lenI(), float(self.lenL()*self.lenR())/(self.N*self.N)) 

    def pValOver(self):
        if self.N == -1:
            return -1
        else:
            return utilsStats.pValOver(self.lenI(), self.N, self.lenL() ,self.lenR())
    
    def minMaxExpAcc(self):
        if self.N == -1:
            return (-1, -1, -1)
        else:
            A = float(self.lenL());
            B = float(self.lenR());
            N = float(self.N);
            return (max(0,(A+B)-N)/min(N, (A+B)), min(A,B)/max(A,B), A*B/(N*(A+B)-A*B))

    def write(self, output, suppOutput):
        output.write(self.dispSimple()+'\n')
        output.flush()
        if suppOutput != None:
            suppOutput.write(self.dispSupp()+'\n')
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
		chparts=parts[2].rsplit(' ')
	else: chparts = []	
	
	if len(chparts) >= 1:
            try :
                acc = float(chparts[0])
            except TypeError, detail:
                raise Exception('Unexpected accurracy in the rule: %s\n' %string)
        else:
            acc = -1

        if len(chparts) >= 2:
            try :
                pVal = float(chparts[1])
            except TypeError, detail:
                raise Exception('Unexpected support in the rule: %s\n' %string)
        else:
            pVal = -1

	if len(chparts) >= 6:
            try :
                alpha = int(chparts[2])
                beta = int(chparts[3])
                gamma = int(chparts[4])
                delta = int(chparts[5])
            except TypeError, detail:
                raise Exception('Unexpected support in the rule: %s\n' %string)
        else:
            (alpha, beta, gamma, delta) = (-1, -1, -1, -1)

        

        return (ruleL, ruleR, acc, pVal, alpha, beta, gamma, delta)
    parseRules = staticmethod(parseRules)

    def parse(stringRules, stringSupport = None, data = None):
        (ruleL, ruleR, acc, pVal, alpha, beta, gamma, delta) = Redescription.parseRules(stringRules)

        if stringSupport != None and type(stringSupport) == str and re.search('\t', stringSupport) :
            partsSupp = stringSupport.rsplit('\t')
            nsuppL = Redescription.parseSupport(partsSupp[0])
            nsuppR = Redescription.parseSupport(partsSupp[1])

            if data == None:
                r = Redescription(ruleL, ruleR, [nsuppL, nsuppR])
            else:
                r = Redescription(ruleL, ruleR, [nsuppL, nsuppR], data.N, [set(),set()], [ ruleL.proba(0, data), ruleR.proba(1, data)])
                
            if r.lenAlpha() != alpha or r.lenBeta() != beta or r.lenGamma() != gamma  or r.lenDelta() != delta :
                raise Warning("Something wrong in the supports ! (%i ~ %i, %i ~ %i, %i ~ %i, %i ~ %i)\n" \
                                 % (r.lenAlpha(), alpha, r.lenBeta(), r.lenGamma(), r.lenDelta(), delta))
        else:
            r = Redescription(ruleL, ruleR)
            r.readInfo = {'acc':acc, 'pVal':pVal, 'A':alpha, 'B':beta, 'C':gamma, 'D':delta}
        return r
    parse = staticmethod(parse)
        
            
    def load(rulesFp, supportsFp = None, data= None):
        stringRules = rulesFp.readline()
        indComm = stringRules.find('#')
        comment = ''
        if indComm != -1 :
            comment = stringRules[indComm:].rstrip()
            stringRules = stringRules[:indComm]
        
        if type(supportsFp) == file :
            stringSupp = supportsFp .readline()
            indComm = stringSupp.find('#')
            commentSupp = ''
            if indComm != -1 :
                commentSupp = stringSupp[indComm:].rstrip()
                stringSupp = stringSupp[:indComm]

        else: stringSupp= None; commentSupp = ''
        return (Redescription.parse(stringRules, stringSupp, data), comment, commentSupp)
    load = staticmethod(load)