from classLog import Log
import utilsStats
import pdb

class SParts:
    # Default log: silent
    logger = Log(0)

    ## TRUTH TABLE:
    ## A B    OR    AND
    ## T T    T     T
    ## T F    T     F
    ## T M    T     M
    ## F F    F     F
    ## F M    M     F
    ## M M    M     M

    ## PARTS:
    ##         A  |  B
    ## ----------------
    ## alpha   T  |  F
    ## beta    F  |  T
    ## gamma   T  |  T
    ## delta   F  |  F
    ## mu_a    T  |  M
    ## mu_b    M  |  T
    ## mu_aB   F  |  M
    ## mu_bB   M  |  F
    ## mu_d    M  |  M

    # Default method to compute the p-values
    methodpVal = 'Marg'
    # indexes of the parts
    (alpha, beta, gamma, delta, mua, mub, muaB, mubB, mud) = range(9)
    # indexes from the parts when looking from the right (A=L, B=R) or the left (A=R,B=L) 
    side_index = [[0,1,2,3,4,5,6,7,8], [1,0,2,3,5,4,7,6,8]]
    labels = ['alpha', 'beta', 'gamma', 'delta', 'mua', 'mub', 'muaB', 'mubB', 'mud' ]
    #labels = ['\t|  \n', '\t  |\n', '\t| |\n', '\t   \n', '\t| :\n', '\t: |\n', '\t  :\n', '\t:  \n', '\t: :\n' ]
    #labels = ['**', '__', '==', '  ', '*.', '"_', '..', '""', '::' ]

    # indexes for the intersections with parts
    #(into: part inter X_True, out: part inter X_False, miss: part inter X_Missing, tot: total part = into + out + miss)
    (into, out, miss, tot) = range(4)
    # indexed for the intersections with parts when considering positive or negative X
    neg_index = [[0, 1, 2, 3], [1, 0, 2, 3]]

    ##### TO COMPUTE ADVANCE while building, INDEXED BY OPERATOR (0: AND, 1: OR)
    # Parts in numerator (BLUE), independent of X 
    IDS_fixnum = [[], [(tot, gamma)]]
    # Parts in numerator (BLUE), dependent of X: toBlue
    IDS_varnum = [[(into, gamma)] ,[(into, beta), (into, mub)]]
    # Parts in denominator (RED), independent of X
    IDS_fixden = [[(into, gamma), (out, gamma), (tot, beta)], [(tot, gamma), (tot, alpha), (into, beta), (out, beta)]]
    # Parts in denominator (RED), dependent of X: toRed
    IDS_varden = [[(into, alpha), (out, mub)], [(into, mub), (into, mubB), (into, delta)]]
    # Parts left uncovered (OUT), (always dependent of X)
    IDS_out = [[(out, alpha), (out, mubB), (tot, delta)], [(out, delta)]]
    # Parts in contribution (CONT), (always dependent of X)
    # Contribution: AND entities removed from alpha, OR: entities added to gamma
    IDS_cont = [[(out, alpha)], [(into, beta), (into, mub)]]
    # Parts in the new support of the extended rule
    IDS_nsupp = [[(into, alpha), (into, gamma), (into, mua)], [(tot, alpha), (tot, gamma), (tot, mua), (into, mub), (into, beta), (into, delta), (into, mubB), (into, mud)]]

    #### TO COMPUTE ACCURACY after building, INDEXED BY TYPE OF ACCURRACY (0: grounded, 1: optimistic, 2: pessimistic)
    IDS_diff = [[alpha, beta], [alpha, beta], [alpha, beta, mub, mua, mubB, muaB]]
    IDS_inter = [[gamma], [gamma, mub, mua], [gamma]]
    IDS_uncovered = [[delta], [delta], [delta]]

    #### TO COMPUTE SUPPORTS, no index
    IDS_supp = (gamma, alpha, mua)
    IDS_miss = (mub, mubB, mud)
    # indexes swaping when negating one side (0: negating A, 1: negating B)
    IDS_negated = [(delta, gamma, beta, alpha, muaB, mub, mua, mubB, mud), \
                   (gamma, delta, alpha, beta, mua, mubB, muaB, mub, mud)]

    # return the index corresponding to part_id when looking from given side 
    def partId(part_id, side=0):
        return SParts.side_index[side][part_id]
    partId = staticmethod(partId)

    # return the index corresponding to part_id when negating given side 
    def negatedPartId(part_id, side=0):
        return SParts.IDS_negated[side][part_id]
    negatedPartId = staticmethod(negatedPartId)
    
    # return the index corresponding to inout and possible negation
    def inOutId(inout_id, neg=0):
        return SParts.neg_index[neg][inout_id]
    inOutId = staticmethod(inOutId)

    # sums the values in parts that correspond to part_id indexes given in parts_id
    ## parts_id can be
    ##  * a list of pairs (inout, part_id), inout are then ignored 
    ##  * a list of values part_id
    def sumPartsId(side, parts_id, parts):
        if type(parts) == list  and len(parts_id) > 0:
            if type(parts_id[0]) == int:
                 ids = parts_id    
            elif len(parts_id[0]) == 2:
                (inout, ids) = zip(*parts_id)
            else:
                ids = []
            return sum([parts[SParts.partId(part_id, side)] for part_id in set(ids)])
        elif type(parts) == int :
            return 1*(parts in [SParts.partId(part_id[1], side) for part_id in parts_id])
        return 0
    sumPartsId = staticmethod(sumPartsId)


    # sums the values in parts that correspond to inout and part_id indexes given in parts_id
    ## parts_id must be
    ##  * a list of pairs (inout, part_id)
    def sumPartsIdInOut(side, neg, parts_id, parts):
        return sum([parts[SParts.inOutId(part_id[0], neg)][SParts.partId(part_id[1], side)] for part_id in parts_id])
    sumPartsIdInOut = staticmethod(sumPartsIdInOut)

    # return parts reordered to match the new indexes of parts corresponding to negation of given side
    def negateParts(side, parts):
        return [parts[SParts.negatedPartId(p, side)] for p in range(len(parts))]
    negateParts = staticmethod(negateParts)

    # compute the resulting support and missing when combining X and Y with given operator
    def partsSuppMiss(OR, XSuppMiss, YSuppMiss):
        if XSuppMiss == None:
            return YSuppMiss
        elif YSuppMiss == None:
            return XSuppMiss
        elif OR:
            supp = set(XSuppMiss[0] | YSuppMiss[0])
            miss = set(XSuppMiss[1] | YSuppMiss[1]) - supp
        else:
            miss = set((XSuppMiss[1] & YSuppMiss[1]) | (XSuppMiss[1] & YSuppMiss[0]) | (YSuppMiss[1] & XSuppMiss[0]))
            supp = set(XSuppMiss[0] & YSuppMiss[0])
        return (supp, miss)
    partsSuppMiss = staticmethod(partsSuppMiss)

    # compute the ratio of BLUE/RED parts depending on intersection with X
    def compRatioVar(side, op, parts):
        den = SParts.sumPartsId(side, SParts.IDS_varden[op], parts)
        if den != 0:
            return float(SParts.sumPartsId(side, SParts.IDS_varnum[op], parts))/den
        else:
            return float('Inf')
    compRatioVar = staticmethod(compRatioVar)

    # compute the accuracy resulting of appending X on given side with given operator and negation
    # from intersections of X with parts (lParts)
    def compAcc(side, op, neg, lParts):
        return float(SParts.sumPartsIdInOut(side, neg, SParts.IDS_varnum[op] + SParts.IDS_fixnum[op], lParts))/ \
               SParts.sumPartsIdInOut(side, neg, SParts.IDS_varden[op] + SParts.IDS_fixden[op], lParts)
    compAcc = staticmethod(compAcc)

    # compute the advance resulting of appending X on given side with given operator and negation
    # from intersections of X with parts (lParts)            
    def compAdv(t, side, op, neg, lParts, bounds):
        b = None
        contri = SParts.sumPartsIdInOut(side, neg, SParts.IDS_cont[op], lParts)
        if ( contri >= bounds[0] \
             and SParts.sumPartsIdInOut(side, neg, SParts.IDS_fixnum[op] + SParts.IDS_varnum[op], lParts) >= bounds[1] \
             and  SParts.sumPartsIdInOut(side, neg, SParts.IDS_out[op], lParts) >= bounds[2] ):

            varBlue = SParts.sumPartsIdInOut(side, neg, SParts.IDS_varnum[op], lParts)
            varRed = SParts.sumPartsIdInOut(side, neg, SParts.IDS_varden[op], lParts)
            fixBlue = SParts.sumPartsIdInOut(side, neg, SParts.IDS_fixnum[op], lParts) 
            fixRed = SParts.sumPartsIdInOut(side, neg, SParts.IDS_fixden[op], lParts)
            
            b= {'acc': float( varBlue + fixBlue ) / ( varRed + fixRed ) , \
                'toRed': varRed, 'toBlue': varBlue, 'term': t, 'side': side, 'op': op, 'neg': neg, 'lparts': lParts, 'cont': contri}
        return b
    compAdv = staticmethod(compAdv)

    # sets the method to compute p-values
    def setMethodPVal(methodpVal):
        try:
            SParts.methodpVal = methodpVal
            SParts.pValRuleCand = staticmethod(eval('SParts.pVal%sRuleCand' % (SParts.methodpVal)))
            SParts.pValRedCand = staticmethod(eval('SParts.pVal%sRedCand' % (SParts.methodpVal)))
        except AttributeError:
            raise Exception('Oups method to compute the p-value does not exist !')
    setMethodPVal = staticmethod(setMethodPVal)

    # rule p-value using support probabilities (binomial), for candidates
    def pValSuppRuleCand(side, op, neg, lParts, N, prs = None):
        if prs == None:
            return 0
        else:
            lInter = SParts.sumPartsId(side, SParts.IDS_supp, lParts[SParts.inOutId(SParts.into, neg)])
            lX = float(sum(lParts[SParts.inOutId(SParts.into, neg)]))     
            if op:
                return 1-utilsStats.pValSupp(N, lInter, prs[cand['side']] + lX/N - prs[cand['side']]*lX/N)
            else: 
                return utilsStats.pValSupp(N, lInter, prs[cand['side']]*lX/N)
    pValSuppRuleCand = staticmethod(pValSuppRuleCand)

    # rule p-value using marginals (binomial), for candidates
    def pValMargRuleCand(side, op, neg, lParts, N, prs = None):
        if prs == None:
            return 0
        else:
            lInter = SParts.sumPartsId(side, SParts.IDS_supp, lParts[SParts.inOutId(SParts.into, neg)])
            lsupp = SParts.sumPartsId(side, SParts.IDS_supp, lParts[SParts.inOutId(SParts.tot, neg)])
            lX = float(sum(lParts[SParts.inOutId(SParts.into, neg)]))     
            if op:
                return 1-utilsStats.pValSupp(N, lInter, lsupp*lX/(N*N))
            else: 
                return utilsStats.pValSupp(N, lInter, lsupp*lX/(N*N))
    pValMargRuleCand = staticmethod(pValMargRuleCand)

    # rule p-value using support sizes (hypergeom), for candidates
    def pValOverRuleCand(side, op, neg, lParts, N, prs = None):
        if prs == None:
            return 0
        else:
            lInter = SParts.sumPartsId(side, SParts.IDS_supp, lParts[SParts.inOutId(SParts.into, neg)])
            lsupp = SParts.sumPartsId(side, SParts.IDS_supp, lParts[SParts.inOutId(SParts.tot, neg)])
            lX = float(sum(lParts[SParts.inOutId(SParts.into, neg)]))     
            if op:
                return 1-utilsStats.pValOver(lInter, N, lsupp, lX)
            else: 
                return utilsStats.pValOver(lInter, N, lsupp, lX)
    pValOverRuleCand = staticmethod(pValOverRuleCand)
    
    # redescription p-value using support probabilities (binomial), for candidates
    def pValSuppRedCand(side, op, neg, lParts, N, prs = None):
        lInter = SParts.sumPartsIdInOut(side, neg, SParts.IDS_fixnum[op] + SParts.IDS_varnum[op], lParts)
        lX = float(sum(lParts[SParts.inOutId(SParts.into, neg)]))     
        if prs == None :
            lO = SParts.sumPartsId(1-side, SParts.IDS_supp, lParts[SParts.inOutId(SParts.tot, neg)])
            return utilsStats.pValSupp(N, lInter, float(lO*lX)/(N*N))
        elif op:
            return utilsStats.pValSupp(N, lInter, prs[1-cand['side']]*(prs[cand['side']] + lX/N - prs[cand['side']]*lX/N))
        else: 
            return utilsStats.pValSupp(N, lInter, prs[1-cand['side']]*(prs[cand['side']] * lX/N))
    pValSuppRedCand = staticmethod(pValSuppRedCand)

    # redescription p-value using marginals (binomial), for candidates
    def pValMargRedCand(side, op, neg, lParts, N, prs = None):
        lInter = SParts.sumPartsIdInOut(side, neg, SParts.IDS_fixnum[op] + SParts.IDS_varnum[op], lParts)
        lO = SParts.sumPartsId(1-side, SParts.IDS_supp, lParts[SParts.inOutId(SParts.tot, neg)])
        lS = SParts.sumPartsIdInOut(side, neg, SParts.IDS_nsupp[op], lParts)
        return utilsStats.pValSupp(N, lInter, float(lO*lS)/(N*N))
    pValMargRedCand = staticmethod(pValMargRedCand)
    
    # redescription p-value using support sizes (hypergeom), for candidates
    def pValOverRedCand(op, neg, lParts, N, prs = None):
        lInter = SParts.sumPartsIdInOut(side, neg, SParts.IDS_fixnum[op] + SParts.IDS_varnum[op], lParts)
        lO = SParts.sumPartsId(1-side, SParts.IDS_supp, lParts[SParts.inOutId(SParts.tot, neg)])
        lS = SParts.sumPartsIdInOut(side, neg, SParts.IDS_nsupp[op], lParts)
        return utilsStats.pValOver(lInter, N, lO, lS)
    pValOverRedCand = staticmethod(pValOverRedCand)

    # initialize parts counts
    # default count for every part is zero
    # pairs contains a list of (part_id, value)
    # if value is non negative, the count of part_id is set to that value
    # if value is negative, the count of part_id is set to - value - sum of the other parts set so far
    def makeLParts(pairs=[], side=0):
        lp = [0 for i in range(SParts.mud+1)]
        for (part_id, val) in pairs:
            if val < 0:
                tmp = sum(lp)
                lp[SParts.partId(part_id, side)] = -val- tmp
            else:
                lp[SParts.partId(part_id, side)] = val
        return lp
    makeLParts = staticmethod(makeLParts)

    # adds to parts counts
    # lpartsY can be a part_id in wich case the result of the addition
    # is lpartsX where that part in incremented by one
    def addition(lpartsX, lpartsY):
        if type(lpartsY) == list:
            lp = [lpartsX[i]+lpartsY[i] for i in range(len(lpartsX))]    
        else:
            lp = list(lpartsX)
            if type(lpartsY) == int :
                lp[lpartsY] += 1
        return lp
    addition = staticmethod(addition)

    def __init__(self, N, supports, prs = [1,1]):
        try:
            self.pVal = eval('self.pVal%s' % (SParts.methodpVal))
        except AttributeError:
              raise Exception('Oups method to compute the p-value does not exist !')
        
        self.N = N 
        self.prs = prs
        self.vect = None
        ### if include all empty missing parts, remove 
        if type(supports) == list and len(supports) == 4 and len(supports[2]) + len(supports[3]) == 0 :
            supports = supports[0:2]
        elif type(supports) == list and len(supports) == 9 and len(supports[8]) + len(supports[7]) + len(supports[6]) + len(supports[5]) + len(supports[4]) == 0 :
            supports = supports[0:3]
            
        ### sParts is a partition of the rows (delta is not explicitely stored when there are no missing values)
        ## two supports: interpreted as (suppL, suppR)
        if type(supports) == list and len(supports) == 2 :
            (suppL, suppR) = supports
            self.missing = False
            self.sParts = [ set(suppL - suppR), \
                       set(suppR - suppL), \
                       set(suppL & suppR)]
        ## three supports: interpreted as (alpha, beta, gamma)
        elif type(supports) == list and len(supports) == 3:
            self.missing = False
            self.sParts = [ set(supports[0]), set(supports[1]), set(supports[2])]
        ## four supports: interpreted as (suppL, suppR, missL, missR)
        elif type(supports) == list and len(supports) == 4:
            self.missing = True
            (suppL, suppR, missL, missR) = supports
            self.sParts = [ set(suppL - suppR - missR), \
                       set(suppR - suppL - missL), \
                       set(suppL & suppR), \
                       set(range(self.N)) - suppL -suppR - missL - missR, \
                       set(suppL & missR), \
                       set(suppR & missL), \
                       set(missR - suppL - missL), \
                       set(missL - suppR - missR), \
                       set(missL & missR) ]
        ## four supports: interpreted as (alpha, beta, gamma, delta, mua, mub, muaB, mubB, mud)
        elif type(supports) == list and len(supports) == 9:
            self.missing = True
            self.sParts = [set(support) for support in supports]
        ## else: set all empty
        else:
            self.missing = False
            self.sParts = [set(), set(), set(), set(), set(), set(), set(), set(), set()]

    # contains missing values
    def hasMissing(self):
        return self.missing

    # return copy of the probas
    def probas(self):
        return list(self.prs)

    # return support (used to create new instance of SParts)
    def copSupp(self):
        return self.sParts

    # return new instance of SParts corresponding to negating given side
    def negate(self, side=0):
        if self.missing:
            return SParts(self.N, SParts.negateParts(side, self.sParts))
        else:
            self.sParts.append(self.part(SParts.delta))
            n = SParts.negateParts(side, self.sParts)
            return SParts(self.N, n[0:-1])

    def part(self, part_id, side=0):
        if self.missing or part_id < SParts.delta:
            return self.sParts[SParts.partId(part_id, side)]
        elif part_id > SParts.delta:
            return set()
        elif part_id == SParts.delta:
            return set(range(self.N)) - self.sParts[0] - self.sParts[1] - self.sParts[2]
        
    def lpart(self, part_id, side=0):
        if self.missing  or part_id < SParts.delta:
            return len(self.sParts[SParts.partId(part_id, side)])
        elif part_id > SParts.delta:
            return 0
        elif part_id == SParts.delta:
            return self.N - len(self.sParts[0]) - len(self.sParts[1]) - len(self.sParts[2])

    def parts(self, side=0):
        return [self.part(i, side) for i in range(SParts.mud+1)]
    
    def lparts(self, side=0):
        return [self.lpart(i, side) for i in range(SParts.mud+1)]
    
    def partInterX(self, suppX, part_id, side=0):
        if self.missing or part_id < SParts.delta:
            return set(suppX & self.sParts[SParts.partId(part_id, side)])
        elif part_id > SParts.delta:
            return set()
        elif part_id == SParts.delta:
            return set(suppX - self.sParts[0] - self.sParts[1] - self.sParts[2])
        
    def lpartInterX(self, suppX, part_id, side=0):
        if self.missing  or part_id < SParts.delta:
            return len(suppX & self.sParts[SParts.partId(part_id, side)])
        elif part_id > SParts.delta:
            return 0
        elif part_id == SParts.delta:
            return len(suppX - self.sParts[0] - self.sParts[1] - self.sParts[2])

    def partsInterX(self, suppX, side=0):
        return [self.partInterX(suppX, i, side) for i in range(SParts.mud+1)]
    
    def lpartsInterX(self, suppX, side=0):
        if self.missing:
            return [self.lpartInterX(suppX, i, side) for i in range(SParts.mud+1)]
        else:
            la = self.lpartInterX(suppX, SParts.alpha, side)
            lb = self.lpartInterX(suppX, SParts.beta, side)
            lc = self.lpartInterX(suppX, SParts.gamma, side)
            return [la, lb, lc, len(suppX) - la - lb - lc, 0, 0, 0, 0, 0]

    def nbParts(self):
        return SParts.mud+1
        
    def lparts_union(self, ids, side=0):
        return sum([self.lpart(i, side) for i in ids])

    def part_union(self, ids, side=0):
        union = set()
        for i in ids:
            union |= self.part(i, side)
        return union

    def supp(self, side=0):
        return self.part_union(SParts.IDS_supp, side)
    def nonSupp(self, side=0):
        if not self.missing:
            return set(range(self.N)) - self.supp(side)
        else:
            return self.part_union(set(range(SParts.mud+1)) - set(SParts.IDS_supp + SParts.IDS_miss), side)
    def miss(self, side=0):
        if not self.missing:
            return set()
        else:
            return self.part_union(SParts.IDS_miss, side)

    def lenSupp(self, side=0):
        return self.lparts_union(SParts.IDS_supp, side)
    def lenNonSupp(self, side=0):
        return self.N - self.lenSupp(side) - self.lenMiss(side)
    def lenMiss(self, side=0):
        if not self.missing:
            return 0
        else:
            return self.lparts_union(SParts.miss_ids, side)

    # return support of symmetrical difference (suppA + suppB - (suppA inter suppB))
    def suppD(self, typ=0, side=0):
        if not self.missing: typ=0
        return self.part_union(SParts.IDS_diff[typ], side)
    # return support of intersection (suppA inter suppB)
    def suppI(self, typ=0, side=0):
        if not self.missing: typ=0
        return self.part_union(SParts.IDS_inter[typ], side)
    # return support of union (suppA union suppB)
    def suppU(self, typ=0, side=0):
        return self.suppI(typ, side) | self.suppD(typ, side)

    ## corresponding lengths
    def lenD(self, typ=0, side=0):
        if not self.missing: typ=0
        return self.lparts_union(SParts.IDS_diff[typ], side)
    def lenI(self, typ=0, side=0):
        if not self.missing: typ=0
        return self.lparts_union(SParts.IDS_inter[typ], side)
    def lenO(self, typ=0, side=0):
        if not self.missing: typ=0
        return self.lparts_union(SParts.IDS_uncovered[typ], side)
    def lenU(self, typ=0, side=0):
        return self.lenD(typ, side)+self.lenI(typ, side)

    # accuracy
    def acc(self, typ=0, side=0):
        lenI = self.lenI(typ, side)
        if lenI == 0:
            return 0
        else:
            return lenI/float(lenI+self.lenD(typ, side))

    # redescription p-value using support probabilities (binomial), for redescriptions
    def pValSupp(self):
        if self.prs == [-1,-1] or self.N == -1:
            return -1
        else:
            return utilsStats.pValSupp(self.N, self.lenI(), self.prs[0]*self.prs[1]) 

    # redescription p-value using marginals (binomial), for redescriptions
    def pValMarg(self):
        if self.N == -1:
            return -1
        else:
            return utilsStats.pValSupp(self.N, self.lenI(), float(self.lenSupp(0)*self.lenSupp(1))/(self.N*self.N)) 

    # redescription p-value using support sizes (hypergeom), for redescriptions
    def pValOver(self):
        if self.N == -1:
            return -1
        else:
            return utilsStats.pValOver(self.lenI(), self.N, self.lenSupp(0) ,self.lenSupp(1))

    # moves the instersection of supp with part with index id_from to part with index id_to
    def moveInter(self, side, id_from, id_to, supp):
        self.sParts[SParts.partId(id_to, side)] |= (self.sParts[SParts.partId(id_from,side)] & supp)
        self.sParts[SParts.partId(id_from,side)] -= supp

    # update support probabilities
    def updateProba(prA, prB, OR):
        if prA == -1:
            return prB
        elif OR :
            return prA + prB - prA*prB
        else :
            return prA*prB
    updateProba = staticmethod(updateProba)

    # update supports and probabilities resulting from appending X to given side with given operator
    def update(self, side, OR, suppX, missX):
        self.vect = None
        self.prs[side] = SParts.updateProba(self.prs[side], len(suppX)/float(self.N), OR)
            
        if not self.missing and (type(missX) == set and len(missX) > 0):
            self.missing = True
            self.sParts.extend( [ set(range(self.N)) - self.sParts[0] - self.sParts[1] -self.sParts[2],
                       set(), set(), set(), set(), set() ])
            
        if self.missing :
            if OR : ## OR
                ids_from_to_supp = [(SParts.beta, SParts.gamma ), (SParts.delta, SParts.alpha ),
                                    (SParts.mub, SParts.gamma ), (SParts.mubB, SParts.alpha ),
                                    (SParts.muaB, SParts.mua ), (SParts.mud, SParts.mua )]
                for (id_from, id_to) in ids_from_to_supp:
                    self.moveInter(side, id_from, id_to, suppX)

                if (type(missX) == set and len(missX) > 0):
                    ids_from_to_miss = [(SParts.beta, SParts.mub ), (SParts.delta, SParts.mubB ),
                                        (SParts.muaB, SParts.mud )]
                    for (id_from, id_to) in ids_from_to_miss:
                        self.moveInter(side, id_from, id_to, missX)
            
            else: ## AND
                if (type(missX) == set and len(missX) > 0):
                    suppXB  = set(range(self.N)) - suppX - missX
                else:
                    suppXB  = set(range(self.N)) - suppX
                ids_from_to_suppB = [(SParts.alpha, SParts.delta ), (SParts.gamma, SParts.beta ),
                                    (SParts.mua, SParts.muaB ), (SParts.mub, SParts.beta ),
                                    (SParts.mubB, SParts.delta ), (SParts.mud, SParts.muaB )]
                for (id_from, id_to) in ids_from_to_suppB:
                    self.moveInter(side, id_from, id_to, suppXB)
                
                if (type(missX) == set and len(missX) > 0):
                    ids_from_to_miss = [(SParts.alpha, SParts.mubB ), (SParts.gamma, SParts.mub ),
                                        (SParts.mua, SParts.mud )]
                    for (id_from, id_to) in ids_from_to_miss:
                        self.moveInter(side, id_from, id_to, missX)
                
        else :
            if OR : ## OR
                self.sParts[SParts.partId(SParts.alpha,side)] |= (suppX
                                                                       - self.sParts[SParts.partId(SParts.beta, side)]
                                                                       - self.sParts[SParts.partId(SParts.gamma, side)])
                self.sParts[SParts.partId(SParts.gamma,side)] |= (suppX
                                                                       & self.sParts[SParts.partId(SParts.beta, side)])
                self.sParts[SParts.partId(SParts.beta,side)] -= suppX
            
            else: ## AND
                self.sParts[SParts.partId(SParts.beta,side)] |= (self.sParts[SParts.partId(SParts.gamma, side)]
                                                                       - suppX )
                self.sParts[SParts.partId(SParts.gamma,side)] &= suppX
                self.sParts[SParts.partId(SParts.alpha,side)] &= suppX

    # computes vector ABCD (vector containg for each row the index of the part it belongs to)
    def makeVectorABCD(self):
        if self.vect == None: 
            self.vect = [SParts.delta for i in range(self.N)]
            for partId in range(len(self.sParts)):
                for i in self.sParts[partId]:
                    self.vect[i] = partId
        
    # returns the index of the part the given row belongs to, vectorABCD need to have been computed 
    def partRow(self, row):
        return self.vect[row]

    # return the index of the part the given row belongs to
    # or the intersection of the mode of X with the different parts if row == -1, vectorABCD need to have been computed 
    def lpartsRow(self, row, X=None):
        lp = None
        if row == -1 and X != None :
            if self.missing:
                lp = [len(X.interMode(self.sParts[i])) for i in range(SParts.mud+1)]
            else:
                lp = [0 for i in range(self.nbParts())]
                lp[0] = len(X.interMode(self.sParts[0]))
                lp[1] = len(X.interMode(self.sParts[1]))
                lp[2] = len(X.interMode(self.sParts[2]))
                lp[3] = self.N - lp[0] - lp[1] - lp[2]
        elif row != None:
            lp = self.vect[row]
        return lp



############## PRINTING
##############
    # def __str__(self):
#         s = '|'
#         r = '||\n|'
#         if self.missing: up_to = SParts.mud
#         else: up_to = SParts.delta
#         for i in range(up_to+1):
#             s += '|%s' % (3*SParts.labels[i])
#             r += '| % 4i ' % self.lpart(i,0)
#         return s+r+'||'

    def dispSupp(self):
        supportStr = ''
        for i in sorted(self.supp(0)): supportStr += "%i "%i
        supportStr +="\t"
        for i in sorted(self.supp(1)): supportStr += "%i "%i
        if self.missing:
            supportStr +="\t"
            for i in sorted(self.miss(0)): supportStr += "%i "%i
            supportStr +="\t"
            for i in sorted(self.miss(1)): supportStr += "%i "%i
        return supportStr

    def parseSupport(stringSupp, N):
        partsSupp = stringSupp.rsplit('\t')
        if len(partsSupp) == 2:
            return SParts(N, [SParts.parseSupportPart(partsSupp[0]), SParts.parseSupportPart(partsSupp[1])])
        elif len(partsSupp) == 4:
            return SParts(N, [SParts.parseSupportPart(partsSupp[0]), SParts.parseSupportPart(partsSupp[1]), \
                          SParts.parseSupportPart(partsSupp[2]), SParts.parseSupportPart(partsSupp[3])])
        return None
    parseSupport = staticmethod(parseSupport)

    def parseSupportPart(string):
        nsupp = set()
        for i in string.strip().rsplit():
            try:
                nsupp.add(int(i))
            except TypeError, detail:
                raise Exception('Unexpected element in the support: %s\n' %i)
        return nsupp
    parseSupportPart = staticmethod(parseSupportPart)

    def parseLPartsChar(parts):
        cparts = parts.strip().split()
        partsList = [('acc', '%f',  float(cparts[0])), ('pval', '%f',  float(cparts[1]))]
        for i in range(2,len(cparts)):
            partsList.append( (SParts.labels[i-2], '%i',  int(cparts[i])))
        return partsList
    parseLPartsChar = staticmethod(parseLPartsChar)

    def listLPartsChar(self):
        partsList= [('acc', '%f',  self.acc()),('pval', '%f',  self.pVal())]
        if self.missing: up_to = SParts.mud
        else: up_to = SParts.delta
        for i in range(up_to+1):
            partsList.append( (SParts.labels[i], '%i',  self.lpart(i,0)))
        return partsList

    def dispCharList(list):
        p = ''
        for (label, format_str, value) in list:
            p += ' ' + label + ':' + (format_str % ( value ) )
        return p
    dispCharList = staticmethod(dispCharList)
    
    def dispCharListSimple(list):
        p = ''
        for (label, format_str, value) in list:
            p += ' ' + format_str % ( value ) 
        return p
    dispCharListSimple = staticmethod(dispCharListSimple)

    def __str__(self):
        return SParts.dispCharList(self.listLPartsChar())