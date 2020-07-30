try:
    from classQuery import Op, Query
    from classRedescription import Redescription
except ModuleNotFoundError:
    from .classQuery import Op, Query
    from .classRedescription import Redescription

import pdb

class ExtensionError(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)

class Extension(object):

    def __init__(self, ssetts, adv=None, clp=None, sol=None):
        ### self.adv is a tuple: acc, varBlue, varRed, contrib, fixBlue, fixRed
        self.ssetts = ssetts
        self.condition = None
        if adv is not None and len(adv) == 3 and len(adv[2]) == 4 and clp==None and sol==None:
            self.adv = adv[0]
            self.clp = adv[1]
            self.side, self.op, tmp_neg, self.literal = adv[2]
        else:
            self.adv = adv
            self.clp = clp
            if sol is not None:
                self.side, self.op, tmp_neg, self.literal = sol
            else:
                self.side, self.op, self.literal = None, None, None

    def reval(self, red, data):
        pass
                
    def setClp(self, clp, neg=False):
        if clp is None:
            self.clp = clp
        else:
            if len(clp) == 2:
                lin = clp[0]
                lparts = clp[1]
                lout = [lparts[i] - lin[i] for i in range(len(lparts))]
                if neg:
                    self.clp = [lout, lin, lparts]
                else:
                    self.clp = [lin, lout, lparts]

    def setCondition(self, condition):
        self.condition = condition

    def getCondition(self):
        return self.condition
    def hasCondition(self):
        return self.condition is not None

    def dispLiteral(self):
        lit = self.getLiteral()
        if lit is None:
            return "-"
        elif type(lit) is list:
            return " AND ".join(["%s" % ll for ll in lit])
        return "%s" % lit

    def getLiteral(self):
        if self.isValid():
            return self.literal
    def setLiteral(self, literal):
        self.literal = literal

    def getPos(self):
        if self.isValid():
            return (self.getSide(), self.getOp())
        
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
        tmp = red.kid(data, self.getSide(), self.getOp(), self.getLiteral(), supp, miss)
        if self.hasCondition():
            litC = self.getCondition().getLiteral()
            if type(litC) is list:
                # if len(litC) > 1: pdb.set_trace()
                qC = Query(OR=False, buk=litC) 
            else:
                qC = Query(buk=[litC])
            supp_cond, miss_cond = qC.recompute(-1, data)
            tmp.setCondition(qC, supp_cond)
        return tmp

    def isValid(self):
        return self.adv is not None and len(self.adv) > 2

    def isNeg(self):
        if self.isValid():
            if type(self.getLiteral()) is list:
                return False
            return self.getLiteral().isNeg()

    def __str__(self):
        tmp = "Empty extension"
        if self.isValid():
            tmp = ("Extension:\t (%d, %s, %s) -> %f CLP:%s ADV:%s" % (self.getSide(), Op(self.getOp()), self.dispLiteral(), self.getAcc(), str(self.clp), str(self.adv)))
            if self.hasCondition():
                tmp += "\nCOND_%s" % self.getCondition()
        return tmp 

    def disp(self, base_acc=None, N=0, prs=None, coeffs=None):
        strPieces = ["", "", "", ""]
        score_of = self
        if self.isValid():
            strPieces[self.getSide()] = "%s %s" % (Op(self.getOp()), self.dispLiteral()) 
            if self.hasCondition():
                # score_of = self.getCondition()
                strPieces[2] = self.getCondition().dispLiteral()

            if base_acc is None:
                strPieces[-1] = '----\t%1.7f\t----\t----\t% 5i\t% 5i' \
                                % (score_of.getAcc(), score_of.getVarBlue(), score_of.getVarRed())
            else:
                strPieces[-1] = '\t\t%+1.7f \t%1.7f \t%1.7f \t%1.7f\t% 5i\t% 5i' \
                                % (score_of.score(base_acc, N, prs, coeffs), score_of.getAcc(), \
                                   score_of.pValQuery(N, prs), score_of.pValRed(N, prs) , score_of.getVarBlue(), score_of.getVarRed())

        return '* %20s <==> * %20s %20s %s' % tuple(strPieces) # + "\n\tCLP:%s" % str(self.clp)
            
    def score(self, base_acc, N, prs, coeffs):
        ### HERE: HOW TO SCORE WITH CONDITION?
        if self.isValid():
            sc = coeffs["impacc"]*self.impacc(base_acc) \
                   + coeffs["rel_impacc"]*self.relImpacc(base_acc) \
                   + self.pValRedScore(N, prs, coeffs) \
                   + self.pValQueryScore(N, prs, coeffs)
            if False: #self.hasCondition():
                sc += self.getCondition().score(base_acc, N, prs, coeffs)
            return sc

                   
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
            if coeffs is None or coeffs["pval_query"] < 0:
                return coeffs["pval_query"] * self.ssetts.pValQuery(N, prs)
            elif coeffs["pval_query"] > 0:
                return -coeffs["pval_fact"]*(coeffs["pval_query"] < self.pValQuery(N, prs))
            else:
                return 0

    def pValRedScore(self, N, prs, coeffs=None):
        if self.isValid():
            if coeffs is None or coeffs["pval_red"] < 0:
                return coeffs["pval_red"] * self.pValRed(N, prs)
            elif coeffs["pval_red"] > 0:
                return -coeffs["pval_fact"]*(coeffs["pval_red"] < self.pValRed(N, prs))
            else:
                return 0

    def pValQuery(self, N=0, prs=None):
        if self.isValid():
            return self.ssetts.pValQueryCand(self.side, self.op, self.isNeg(), self.clp, N, prs)

    def pValRed(self, N=0, prs=None):
        if self.isValid():
            return self.ssetts.pValRedCand(self.side, self.op, self.isNeg(), self.clp, N, prs)

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

class ExtensionComb(Extension):

    def __init__(self, ssetts, red, lits, op=None, pos=0):
        ### self.adv is a tuple: acc, varBlue, varRed, contrib, fixBlue, fixRed
        self.ssetts = ssetts
        self.pos = pos
        self.condition = None
        self.adv = None
        self.clp = None
        self.org_qs = [red.query(0).copy(), red.query(1).copy()]
        self.exts = []
        for lit in lits:
            if lit[1][0] == -1 or lit[1][0] is None:
                #### side, pos, literal
                self.exts.append(lit)
            else:
                self.org_qs[lit[0]].setBukElemAt(lit[-1], lit[1])
        self.op = op
        if len(self.exts) == 1:
            self.side, _, self.literal = self.exts[0]
        self.red = None
                
    def replaceBetter(self, variant):
        self.red = variant               
        self.clearDets()

    def reval(self, red, data):
        if data is not None and len(self.exts) == 1:
            self.clearDets()
            new_red = self.kid(red, data)
            cmp_red = self.prepareRed(data, extended=False)

            #### side, pos, literal
            side1, ind1, lit1 = self.exts[0]
            supp = data.supp(side1, lit1)

            supports = cmp_red.supports()
            lparts = supports.lparts()
            lin = supports.lpartsInterX(supp)
            self.setClp([lin, lparts], lit1.isNeg())

            acc, dU, dI = (new_red.getAcc(), cmp_red.getLenU() - new_red.getLenU(), cmp_red.getLenI() - new_red.getLenI())
            if self.op: ### DISJ
                self.adv = [acc, -dU, -dI, -dI]
            else:
                self.adv = [acc, dU, dI, dI]
                
    def getPos(self):
        if self.isValid():
            return self.pos
           
    def clearDets(self):
        self.adv = None
        self.clp = None
    def kid(self, red, data):
        if self.red is None:
            self.red = self.prepareRed(data)
        return self.red

    def prepareRed(self, data, extended=True):
        if extended:
            ext_qs = [self.org_qs[0].copy(), self.org_qs[1].copy()]
            for ext in self.exts:
                ext_qs[ext[0]].extend(self.op, ext[-1], resort=False)
            red = Redescription(ext_qs[0], ext_qs[1])
            red.recompute(data)
            return red
        else:
            red = Redescription(self.org_qs[0], self.org_qs[1])
            red.recompute(data)
            return red


    def __str__(self):
        qs_str = [self.org_qs[0].disp(), self.org_qs[1].disp()]
        for ext in self.exts:
            qs_str[ext[0]] += "+ %s %s" % (ext[1], ext[-1])
        tmp = "Ext combination:\n%s\t%s" % (qs_str[0], qs_str[1])
        if self.isValid():
            tmp += "\n\t\tACC:%f CLP:%s ADV:%s" % (self.getAcc(), str(self.clp), str(self.adv))
        if self.hasCondition():
            tmp += "\n\t\tCOND_%s" % self.getCondition()
        return tmp 

    def disp(self, base_acc=None, N=0, prs=None, coeffs=None):
        score_of = self
        stats = ""
        if self.isValid():
            if base_acc is None:
                stats = '----\t%1.7f\t----\t----\t% 5i\t% 5i' \
                                % (score_of.getAcc(), score_of.getVarBlue(), score_of.getVarRed())
            else:
                stats = '\t\t%+1.7f \t%1.7f \t%1.7f \t%1.7f\t% 5i\t% 5i' \
                                % (score_of.score(base_acc, N, prs, coeffs), score_of.getAcc(), \
                                   score_of.pValQuery(N, prs), score_of.pValRed(N, prs) , score_of.getVarBlue(), score_of.getVarRed())

        qs_str = [self.org_qs[0].disp(), self.org_qs[1].disp()]
        for ext in self.exts:
            qs_str[ext[0]] += "+ %s %s" % (ext[1], ext[-1])
        return '%25s <==> %25s %s' % (qs_str[0], qs_str[1], stats)
       
class ExtensionsBatch(object):
    def __init__(self, N=0, constraints=None, current=None):
        self.setCurrent(current)
        self.base_acc = self.getCurrentR().getAcc()
        self.N = N
        self.prs = self.getCurrentR().probas()
        
        if constraints is not None:
            self.coeffs = constraints.getCstr("score_coeffs")
            self.min_impr = constraints.getCstr("min_impr")
            self.max_var = [constraints.getCstr("max_var", side=0), constraints.getCstr("max_var", side=1)]
        else:
            self.coeffs, self.min_impr, self.max_var = (None, 0, [-1, -1])
            
        self.bests = {}
        self.tmpsco = {}
    def getMinImpr(self):
        return self.min_impr
    def setMinImpr(self, min_impr):
        self.min_impr = min_impr
    def getCurrentR(self):
        return self.current
    def setCurrent(self, current):        
        self.current = current
        
    def scoreCand(self, cand):
        if cand is not None:
            return cand.score(self.base_acc, self.N, self.prs, self.coeffs)

    def get(self, pos):
        if pos in self.bests:
            return self.bests[pos]
        else:
            return None
        
    def update(self, cands, data=None):
        for cand in cands:
            cand.reval(self.getCurrentR(), data)
            cand.score(self.base_acc, self.N, self.prs, self.coeffs)
            pos = cand.getPos()
            if pos is not None and ( pos not in self.bests or self.scoreCand(cand) > self.scoreCand(self.bests[pos])):
                self.bests[pos] = cand
                    
    def updateDL(self, cands, rm, data):
        for cand in cands:
            kid = cand.kid(self.getCurrentR(), data)
            top = rm.getTopDeltaRed(kid, data)
            pos = cand.getPos()
            self.scoreCand(cand)
            if pos is not None and ( pos not in self.bests or -top[0] > self.tmpsco[pos]):
                self.bests[pos] = cand
                self.tmpsco[pos] = -top[0]

    def items(self):
        return self.bests.items()
        # x = []
        # for k in [(0, True), (1, False), (0, False), (1, True)]:
        #     if k in self.bests:
        #         x.append((k, self.bests[k]))
        # return x
                
    def improving(self):
        return dict([(pos, cand)  for (pos, cand) in self.items() \
                     if self.scoreCand(cand) >= self.getMinImpr()])

    def improvingKids(self, data):
        kids = []
        for (pos, cand) in self.items():
            if self.scoreCand(cand) >= self.getMinImpr():
                kid = cand.kid(self.getCurrentR(), data)
                kid.setFull(self.max_var)
                if kid.getAcc() != cand.getAcc():
                    raise ExtensionError("[in Extension.improvingKids]\n%s\n\t%s\n\t~> %s" % (self.getCurrentR(), cand, kid))                
                if kid.hasCondition() and kid.getAcc("cond") != cand.getCondition().getAcc(): ### cand must have condition for kid to have, not inherited from parent red
                    raise ExtensionError("[in Extension.improvingKids COND]\n%s\n\t%s\n\t~> %s" % (self.getCurrentR(), cand, kid))
                kids.append(kid)
        return kids
    

    def improvingKidsDL(self, data, rm=None):
        tc = rm.getTopDeltaRed(self.getCurrentR(), data)
        min_impr = -tc[0]
        # print("DL impr---", min_impr, self.tmpsco)
        kids = []
        for (pos, cand) in self.items():
            if self.tmpsco[pos] >= self.getMinImpr():
                kid = cand.kid(self.getCurrentR(), data)
                kid.setFull(self.max_var)
                if kid.getAcc() != cand.getAcc():
                    raise ExtensionError("[in Extension.improvingKidsDL]\n%s\n\t%s\n\t~> %s" % (self.getCurrentR(), cand, kid))
            
                kids.append(kid)
        return kids

        
    def __str__(self):
        dsp  = 'Extensions Batch:\n' #(min_imprv=%f, max_var=%d:%d)\n' % (self.min_impr, self.max_var[0], self.max_var[1]) 
        dsp += 'Redescription: %s' % self.getCurrentR()
        dsp += '\n\t  %20s        %20s        %20s' \
                  % ('LHS extension', 'RHS extension', 'Condition')
            
        dsp += '\t\t%10s \t%9s \t%9s \t%9s\t% 5s\t% 5s' \
                      % ('score', 'Accuracy',  'Query pV','Red pV', 'toBlue', 'toRed')
            
        for k,cand in self.items(): ## Do not print the last: current redescription
            dsp += '\n\t%s' % cand.disp(self.base_acc, self.N, self.prs, self.coeffs)
        return dsp

class ExtensionsCombBatch(ExtensionsBatch):
    def getCurrentR(self):
        return self.current[0]
    def setCurrent(self, current):
        self.current = current

    def __str__(self):
        dsp  = 'Extensions Comb Batch:\n' #(min_imprv=%f, max_var=%d:%d)\n' % (self.min_impr, self.max_var[0], self.max_var[1]) 
        dsp += 'Redescriptions:\n\t%s' % "\n\t".join(["%s" % r for r in self.current])
        dsp += '\n\t  %20s        %20s        ' \
                  % ('LHS extension', 'RHS extension')
            
        dsp += '\t\t%10s \t%9s \t%9s \t%9s\t% 5s\t% 5s' \
                      % ('score', 'Accuracy',  'Query pV','Red pV', 'toBlue', 'toRed')
            
        for k,cand in self.items(): ## Do not print the last: current redescription
            dsp += '\n\t%s' % cand.disp(self.base_acc, self.N, self.prs, self.coeffs)
        return dsp



class ExtPairsBatch(object):
    def __init__(self, N=0, constraints=None, current=None):
        self.N = N
        self.current = current
        self.pairs = []

        if constraints is not None:
            self.min_pairscore = constraints.getCstr("min_pairscore")
        else:
            self.min_pairscore = 0
            
    def getCurrentR(self):
        return self.current

    def scoreCand(self, cand):
        if type(cand) is dict:
            return cand.get("score", -1.)
        return -1.

    def get(self, pos):
        if pos >= -1 and pos < len(self.pairs):
            return self.pairs[pos]
        else:
            return None
        
    def update(self, cands):
        self.pairs.extend(cands)

    def improving(self):
        return dict([(pos, cand)  for (pos, cand) in enumerate(self.pairs) \
                     if self.scoreCand(cand) >= self.min_pairscore])

    def improvingKids(self, data):
        kids = []
        for (pos, cand) in enumerate(self.pairs):
            if self.scoreCand(cand) >= self.min_pairscore:
                kid = Redescription.fromInitialPair((cand["litL"], cand["litR"]), data)
                if self.getCurrentR() is not None:
                    for side in [0, 1]:
                        kid.restrictAvailable(side, self.getCurrentR().lAvailableCols[side])
                kids.append(kid)
        return kids
            
    def __str__(self):
        dsp  = 'ExtPairs Batch: (%f)\n' % self.min_pairscore   
        dsp += '\t\t%10s \t%s \t%s' % ('score', 'litLHS',  'litRHS')
            
        for k,cand in enumerate(self.pairs): ## Do not print the last: current redescription
            dsp += '\n\t%10s \t%s \t%s' % (cand["score"], cand["litL"], cand["litR"])
        return dsp


def newExtensionsBatch(N=0, constraints=None, current=None):
    if current is None:
        return ExtensionsBatch(N, constraints, current)
    elif isinstance(current, Redescription):
        if len(current) == 0: ### empty redescription, eg. starting from anon lits -> actually yields pairs
            return ExtPairsBatch(N, constraints, current)
        else:
            return ExtensionsBatch(N, constraints, current)
    else:
        return ExtensionsCombBatch(N, constraints, current)
