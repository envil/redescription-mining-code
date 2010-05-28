import re, pdb
from classLog import Log
from classRule import  *
from classSParts import  SParts


class Redescription:
    logger = Log(0)
    nbVariables = 3
    diff_terms = Rule.diff_terms
    diff_cols = Rule.diff_cols
    diff_op = Rule.diff_op
    diff_balance = Rule.diff_balance
    diff_length = Rule.diff_length
    diff_score = diff_length + 1
    
    def __init__(self, nruleL, nruleR, nsupps = None, nN = -1, navailableCols = [set(),set()], nPrs = [-1,-1]):
        self.rules = [nruleL, nruleR]
        if nsupps != None:
            self.sParts = SParts(nN, nsupps, nPrs)
        else:
            self.sParts = None
            self.readInfo = []
        self.lAvailableCols = navailableCols
        self.vectorABCD = None
        
    def fromInitialPair(initialPair, data):
        ruleL = Rule()
        ruleR = Rule()
        ruleL.extend(None, initialPair[0])
        ruleR.extend(None, initialPair[1])
        (suppL, missL) = data.termSuppMiss(0, initialPair[0])
        (suppR, missR) = data.termSuppMiss(1, initialPair[1])
        r = Redescription(ruleL, ruleR, [suppL, suppR, missL, missR], data.nbRows(), data.nonFull(), [len(suppL)/float(data.N),len(suppR)/float(data.N)])  
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

    def acc(self):
        return self.sParts.acc()

    def pVal(self):
        return self.sParts.pVal()

    def score(self):
        return self.acc()

    def supports(self):
        return self.sParts
    
    def rule(self, side):
        return self.rules[side]
    
    def probas(self):
        return self.sParts.probas()
    
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

    def removeAvailables(self):
        self.lAvailableCols = [set(),set()]

    def update(self, data=None, side= -1, opBool = None, term= None, suppX=None, missX=None):
        if side == -1 :
            self.removeAvailables()
        else:
            op = Op(opBool)
            self.rules[side].extend(op, term)
            self.sParts.update(side, op.isOr(), suppX, missX)
            if len(self.rules[side]) >= self.nbVariables :
                self.lAvailableCols[side] = set()
            else:
                self.lAvailableCols[side].remove(term.col())
                
    def kid(self, data, side= -1, op = None, term= None, suppX= None, missX=None):
        kid = self.copy()
        kid.update(data, side, op, term, suppX, missX)
        return kid
            
    def copy(self):
        return Redescription(self.rules[0].copy(), self.rules[1].copy(), \
                             self.sParts.copSupp(), self.sParts.N, \
                             [set(self.lAvailableCols[0]),set(self.lAvailableCols[1] )], self.probas())

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
        (nsuppL, missL) = self.recomputeRule(0, data)
        (nsuppR, missR) = self.recomputeRule(1, data)
        if len(missL) + len(missR) > 0:
            self.sParts = SParts(data.N, [nsuppL, nsuppR, missL, missR])
        else:
            self.sParts = SParts(data.N, [nsuppL, nsuppR])
        self.prs = [self.rules[0].proba(0, data), self.rules[1].proba(1, data)]
    
    def check(self, data):
        if self.sParts != None:
            (nsuppL, missL) = self.recomputeRule(0, data)
            (nsuppR, missR) = self.recomputeRule(1, data)
            
            return ( len(nsuppL.symmetric_difference(self.sParts.supp(0))) == 0, \
                     len(nsuppR.symmetric_difference(self.sParts.supp(1))) == 0, \
                     len(missL.symmetric_difference(self.sParts.miss(0))) == 0, \
                     len(missR.symmetric_difference(self.sParts.miss(1))) == 0 )        


    def __str__(self):
        return '%i + %i items:\t (%i): %s' \
               % (self.nbAvailableColsSide(0), self.nbAvailableColsSide(1), \
                  len(self), self.disp())
         
    def dispLPartsSimple(self):
        if self.sParts == None:
            return SParts.dispCharListSimple(self.readInfo)
        else:
            return SParts.dispCharListSimple(self.sParts.listLPartsChar())
        
    def dispLParts(self):
        if self.sParts == None:
            return SParts.dispCharList(self.readInfo)
        else:
            return SParts.dispCharList(self.sParts.listLPartsChar())
        
    def dispSimple(self, lenIndex=0, names= [None, None]):
        return '%s\t%s\t%s' % (self.rules[0].disp(lenIndex, names[0]), self.rules[1].disp(lenIndex, names[1]), self.dispLPartsSimple())

    def disp(self, lenIndex=0, names= [None, None]):
        return '%s\t<==>\t%s\t%s' % (self.rules[0].disp(lenIndex, names[0]), self.rules[1].disp(lenIndex, names[1]), self.dispLParts())
        
    def write(self, output, suppOutput):
        output.write(self.dispSimple()+'\n')
        output.flush()
        if suppOutput != None:
            suppOutput.write(self.sParts.dispSupp()+'\n')
            suppOutput.flush()

    def parseRules(string):
        parts = string.rsplit('\t')

        if len(parts) >= 2:
            ruleL = Rule.parse(parts[0])
            ruleR = Rule.parse(parts[1])
        else:
            ruleL = Rule()
            ruleR = Rule()

        if len(parts) >= 3:
            lpartsList = SParts.parseLPartsChar(parts[2])
        else:
            lpartsList = []
        return (ruleL, ruleR, lpartsList)
    parseRules = staticmethod(parseRules)

    def parse(stringRules, stringSupport = None, data = None):
        (ruleL, ruleR, lpartsList) = Redescription.parseRules(stringRules)

        r = None
        if data != None and stringSupport != None and type(stringSupport) == str and re.search('\t', stringSupport) :
            supports = SParts.parseSupport(stringSupport, data.N)
            if supports != None:
                r = Redescription(ruleL, ruleR, supports.copSupp(), data.nbRows(), [set(),set()], [ ruleL.proba(0, data), ruleR.proba(1, data)])

                if lpartsList[2:] != r.sParts.listLPartsChar()[2:]:
                    raise Warning("Something wrong in the supports ! (%s ~ %s)\n" \
                                  % (SParts.dispCharList(lpartsList), SParts.dispCharList(r.supports.listLPartsChar()) ))
        if r == None:
            r = Redescription(ruleL, ruleR)
            r.readInfo = lpartsList
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
