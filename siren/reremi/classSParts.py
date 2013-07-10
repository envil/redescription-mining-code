from scipy.special import gammaln
from scipy.stats import binom
import numpy, random
import pdb

def tool_hypergeomPMF(k, M, n, N):
    tot, good = M, n
    bad = tot - good
    return numpy.exp(gammaln(good+1) - gammaln(good-k+1) - gammaln(k+1) + gammaln(bad+1) \
                              - gammaln(bad-N+k+1) - gammaln(N-k+1) - gammaln(tot+1) \
                              + gammaln(tot-N+1) + gammaln(N+1))
#same as the following but numerically more precise
#return comb(good,k) * comb(bad,N-k) / comb(tot,N)

def tool_pValOver(kInter, nbRows, suppL, suppR):
    ## probability that two sets of these size have intersection equal or larger than kInter
    return sum([ tool_hypergeomPMF(k, nbRows, suppL, suppR) for k in range(kInter, min(suppL, suppR)+1)])

def tool_pValSupp(nbRows, supp, pr):
    ## probability that an termset with marginal probability pr has support equal or larger than supp
    return 1-binom.cdf(supp-1, nbRows, pr) 

class SParts:

    infos = {"acc": "self.acc()", "pval": "self.pVal()"}
    type_parts = None

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
    (into, out, tot, imiss) = range(4)
    # indexed for the intersections with parts when considering positive or negative X
    neg_index = [[0, 1, 2, 3], [1, 0, 2, 3]]

############################################################################################################################
############################                             WITHOUT MISSING VALUES                        #####################
############################################################################################################################

    def resetPartsIds(type_parts):
        if SParts.type_parts == type_parts:
            return
        SParts.type_parts = type_parts
        (into, out, tot, imiss) = (SParts.into, SParts.out, SParts.tot, SParts.imiss)
        (alpha, beta, gamma, delta, mua, mub, muaB, mubB, mud) = (SParts.alpha, SParts.beta, SParts.gamma, SParts.delta, SParts.mua, SParts.mub, SParts.muaB, SParts.mubB, SParts.mud)
        if type_parts == "none":

            SParts.bottom = alpha
            SParts.top = delta
            ##############################################################
            #### BASIC
            ##############################################################

            ##### TO COMPUTE ADVANCE while building, INDEXED BY OPERATOR (0: AND, 1: OR)
            # Parts in numerator (BLUE), independent of X 
            SParts.IDS_fixnum = [[], [(tot, gamma)]]
            # Parts in numerator (BLUE), dependent of X: toBlue
            SParts.IDS_varnum = [[(into, gamma)] ,[(into, beta)]]
            # Parts in denominator (RED), independent of X
            SParts.IDS_fixden = [[(tot, gamma), (tot, beta)], [(tot, gamma), (tot, alpha), (tot, beta)]]
            # Parts in denominator (RED), dependent of X: toRed
            SParts.IDS_varden = [[(into, alpha)], [(into, delta)]]
            # Parts left uncovered (OUT), (always dependent of X)
            SParts.IDS_out = [[(out, alpha), (tot, delta)], [(out, delta)]]
            # Parts in contribution (CONT), (always dependent of X)
            # Contribution: AND entities removed from alpha, OR: entities added to gamma
            SParts.IDS_cont = [[(out, alpha)], [(into, beta)]]
            # Parts in the new support of the extended query
            SParts.IDS_nsupp = [[(into, alpha), (into, gamma)], [(tot, alpha), (tot, gamma), (into, beta), (into, delta)]]

            #### TO COMPUTE ACCURACY after building
            SParts.IDS_diff = [alpha, beta]
            SParts.IDS_dL = [alpha]
            SParts.IDS_dR = [beta]
            SParts.IDS_inter = [gamma]
            SParts.IDS_uncovered = [delta]

            ##############################################################

            #### TO COMPUTE SUPPORTS, no index
            SParts.IDS_supp = (gamma, alpha)
            SParts.IDS_miss = ()
            # indexes swaping when negating one side (0: negating A, 1: negating B)
            SParts.IDS_negated = [(delta, gamma, beta, alpha), \
                           (gamma, delta, alpha, beta)]

#### END NO MISSING VALUES
############################################################################################################################


############################################################################################################################
############################                         WITH MISSING VALUES                               #####################
############################################################################################################################
        else:

            SParts.bottom = alpha
            SParts.top = mud
            ##############################################################
            #### GROUNDED
            ##############################################################

            if type_parts == "grounded":

                ##### TO COMPUTE ADVANCE while building, INDEXED BY OPERATOR (0: AND, 1: OR)
                # Parts in numerator (BLUE), independent of X 
                SParts.IDS_fixnum = [[],
                              [(tot, gamma)]]
                # Parts in numerator (BLUE), dependent of X: toBlue
                SParts.IDS_varnum = [[(into, gamma)] ,
                              [(into, beta), (into, mub)]]
                # Parts in denominator (RED), independent of X
                SParts.IDS_fixden = [[(tot, beta)],
                              [(tot, gamma), (tot, alpha)]]
                # Parts in denominator (RED), dependent of X: toRed
                SParts.IDS_varden = [[(into, alpha), (into, gamma), (out, gamma), (out, mub)],
                              [(into, mub), (into, mubB), (into, delta), (into, beta), (out, beta)]]

                # Parts left uncovered (OUT), (always dependent of X)
                SParts.IDS_out = [[(out, alpha), (out, mubB), (tot, delta)],
                           [(out, delta)]]
                # Parts in contribution (CONT), (always dependent of X)
                # Contribution: AND entities removed from alpha, OR: entities added to gamma
                SParts.IDS_cont = [[(out, alpha)],
                            [(into, beta), (into, mub)]]
                # Parts in the new support of the extended query
                SParts.IDS_nsupp = [[(into, alpha), (into, gamma)],
                             [(tot, alpha), (tot, gamma), (tot, mua), (into, mub), (into, beta), (into, delta), (into, mubB), (into, muaB), (into, mud)]]

                #### TO COMPUTE ACCURACY after building
                SParts.IDS_diff = [alpha, beta]
                SParts.IDS_dL = [alpha]
                SParts.IDS_dR = [beta]
                SParts.IDS_inter = [gamma]
                SParts.IDS_uncovered = [delta]


            ##############################################################
            #### OPTIMISTIC
            ##############################################################

            elif type_parts == "optimistic":

                ##### TO COMPUTE ADVANCE while building, INDEXED BY OPERATOR (0: AND, 1: OR)
                SParts.IDS_fixnum = [[(imiss, mua), (imiss, mub), (imiss, mud), (imiss, gamma)],
                                     [(tot, mua), (tot, gamma), (tot, mud), (tot, mub), (imiss, muaB), (imiss, beta)]]
                SParts.IDS_varnum = [[(into, mua), (into, gamma), (into, mub), (into, mud)],
                                     [(into, muaB), (into, beta), (imiss, muaB), (imiss, beta)]]
                SParts.IDS_fixden = [[(tot, gamma), (tot, mub), (tot, beta)],
                                     [(tot, mua), (tot, gamma), (tot, mub), (tot,  mud), (imiss, muaB), (tot, beta), (tot, alpha)]]
                SParts.IDS_varden = [[(into, alpha), (into, mua), (into, mud), (imiss, mua), (imiss, mud)],
                                     [(into, delta), (into, mubB), (into, muaB)]]

                SParts.IDS_out = [[(out, alpha), (imiss, alpha), (out, mua), (tot, delta), (tot, mubB), (out, mud), (tot, muaB)],
                                  [(out, delta), (imiss, delta), (out, mubB), (imiss,mubB), (out,muaB)]]
                SParts.IDS_cont = [[(out, alpha)],
                                   [(into, beta), (into, mub)]]
                SParts.IDS_nsupp = [[(into, alpha), (into, mua), (into, gamma), (into, mub), (into, mud)],
                                    [(tot, alpha), (tot, gamma), (tot, mua), (into, mub), (into, beta), (into, delta), (into, mubB), (into, mud), (into, muaB)]]

                #### TO COMPUTE ACCURACY after building
                SParts.IDS_diff = [alpha, beta]
                SParts.IDS_dL = [alpha]
                SParts.IDS_dR = [beta]
                SParts.IDS_inter = [gamma, mub, mua, mud]
                SParts.IDS_uncovered = [delta, mubB, muaB]


            ##############################################################
            #### PESSIMISTIC
            ##############################################################

            elif type_parts == "pessimistic":

                ##### TO COMPUTE ADVANCE while building, INDEXED BY OPERATOR (0: AND, 1: OR)
                SParts.IDS_fixnum = [[],
                                     [(tot, gamma)]]
                SParts.IDS_varnum = [[(into, gamma)] ,
                                     [(into, beta), (into, mub)]]
                SParts.IDS_fixden = [[(imiss, alpha), (tot, mua), (tot, gamma), (tot, mub), (tot, beta), (imiss, mubB), (tot, mud), (tot, muaB)],
                                     [(tot, gamma), (tot, alpha), (tot, beta), (tot, mua), (tot, muaB), (tot, mub), (tot, mubB), (tot, mud)]]
                SParts.IDS_varden = [[(into, alpha), (into, mubB)],
                                     [(into, delta), (imiss, delta)]]

                SParts.IDS_out = [[(out, alpha), (out, mubB), (tot, delta)],
                                  [(out, delta)]]
                SParts.IDS_cont = [[(out, alpha)],
                                   [(into, beta), (into, mub)]]
                SParts.IDS_nsupp = [[(into, alpha), (into, gamma), (into, mua)],
                                    [(tot, alpha), (tot, gamma), (tot, mua), (into, mub), (into, beta), (into, delta), (into, mubB), (into, mud)]]

                #### TO COMPUTE ACCURACY after building
                SParts.IDS_diff = [alpha, beta, mub, mua, mubB, muaB, mud]
                SParts.IDS_dL = [alpha, mua, mubB]
                SParts.IDS_dR = [beta, mub, muaB, mud]
                SParts.IDS_inter =  [gamma]
                SParts.IDS_uncovered = [delta]

            ##############################################################

            ### TO COMPUTE SUPPORTS, no index
            SParts.IDS_supp = (gamma, alpha, mua)
            SParts.IDS_miss = (mub, mubB, mud)
            ### indexes swaping when negating one side (0: negating A, 1: negating B)
            SParts.IDS_negated = [(delta, gamma, beta, alpha, muaB, mub, mua, mubB, mud), \
                           (gamma, delta, alpha, beta, mua, mubB, muaB, mub, mud)]
    resetPartsIds = staticmethod(resetPartsIds)
#### END WITH MISSING VALUES
############################################################################################################################


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
        if XSuppMiss is None:
            return YSuppMiss
        elif YSuppMiss is None:
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
    def advRatioVar(side, op, parts):
        den = SParts.sumPartsId(side, SParts.IDS_varden[op], parts)
        if den != 0:
            return float(SParts.sumPartsId(side, SParts.IDS_varnum[op], parts))/den
        else:
            return float('Inf')
    advRatioVar = staticmethod(advRatioVar)

    # compute the accuracy resulting of appending X on given side with given operator and negation
    # from intersections of X with parts (clp)
    def advAcc(side, op, neg, lparts, lmiss, lin):
        lout = [lparts[i] - lmiss[i] - lin[i] for i in range(len(lparts))]
        clp = (lin, lout, lparts, lmiss)
        return float(SParts.sumPartsIdInOut(side, neg, SParts.IDS_varnum[op] + SParts.IDS_fixnum[op], clp))/ \
               SParts.sumPartsIdInOut(side, neg, SParts.IDS_varden[op] + SParts.IDS_fixden[op], clp)
    advAcc = staticmethod(advAcc)

    # sets the method to compute p-values
    def setMethodPVal(methodpVal):
        try:
            SParts.methodpVal = methodpVal.capitalize()
            SParts.pValQueryCand = staticmethod(eval('SParts.pVal%sQueryCand' % (SParts.methodpVal)))
            SParts.pValRedCand = staticmethod(eval('SParts.pVal%sRedCand' % (SParts.methodpVal)))
        except AttributeError:
            raise Exception('Oups method to compute the p-value does not exist !')
    setMethodPVal = staticmethod(setMethodPVal)

    # def pValRedCand(side, op, neg, lParts, N, prs = None, method=""):
    #     return SParts.pValSuppRedCand(side, op, neg, lParts, N, prs)
    # pValRedCand = staticmethod(pValRedCand)

    # def pValQueryCand(side, op, neg, lParts, N, prs = None):
    #     return SParts.pValSuppQueryCand(side, op, neg, lParts, N, prs)
    # pValQueryCand = staticmethod(pValQueryCand)
    
    # query p-value using support probabilities (binomial), for candidates
    def pValSuppQueryCand(side, op, neg, lParts, N, prs = None):
        if prs is None:
            return 0
        else:
            lInter = SParts.sumPartsId(side, SParts.IDS_supp, lParts[SParts.inOutId(SParts.into, neg)])
            lX = float(sum(lParts[SParts.inOutId(SParts.into, neg)]))     
            if op:
                return 1-tool_pValSupp(N, lInter, prs[side] + lX/N - prs[side]*lX/N)
            else: 
                return tool_pValSupp(N, lInter, prs[side]*lX/N)
    pValSuppQueryCand = staticmethod(pValSuppQueryCand)

    # query p-value using marginals (binomial), for candidates
    def pValMargQueryCand(side, op, neg, lParts, N, prs = None):
        if prs is None:
            return 0
        else:
            lInter = SParts.sumPartsId(side, SParts.IDS_supp, lParts[SParts.inOutId(SParts.into, neg)])
            lsupp = SParts.sumPartsId(side, SParts.IDS_supp, lParts[SParts.inOutId(SParts.tot, neg)])
            lX = float(sum(lParts[SParts.inOutId(SParts.into, neg)]))     
            if op:
                return 1-tool_pValSupp(N, lInter, lsupp*lX/(N*N))
            else: 
                return tool_pValSupp(N, lInter, lsupp*lX/(N*N))
    pValMargQueryCand = staticmethod(pValMargQueryCand)

    # query p-value using support sizes (hypergeom), for candidates
    def pValOverQueryCand(side, op, neg, lParts, N, prs = None):
        if prs is None:
            return 0
        else:
            lInter = SParts.sumPartsId(side, SParts.IDS_supp, lParts[SParts.inOutId(SParts.into, neg)])
            lsupp = SParts.sumPartsId(side, SParts.IDS_supp, lParts[SParts.inOutId(SParts.tot, neg)])
            lX = float(sum(lParts[SParts.inOutId(SParts.into, neg)]))     
            if op:
                return 1-tool_pValOver(lInter, N, lsupp, lX)
            else: 
                return tool_pValOver(lInter, N, lsupp, lX)
    pValOverQueryCand = staticmethod(pValOverQueryCand)
        
    # redescription p-value using support probabilities (binomial), for candidates
    def pValSuppRedCand(side, op, neg, lParts, N, prs = None):
        lInter = SParts.sumPartsIdInOut(side, neg, SParts.IDS_fixnum[op] + SParts.IDS_varnum[op], lParts)
        lX = float(sum(lParts[SParts.inOutId(SParts.into, neg)]))     
        if prs is None :
            lO = SParts.sumPartsId(1-side, SParts.IDS_supp, lParts[SParts.inOutId(SParts.tot, neg)])
            return tool_pValSupp(N, lInter, float(lO*lX)/(N*N))
        elif op:
            return tool_pValSupp(N, lInter, prs[1-side]*(prs[side] + lX/N - prs[side]*lX/N))
        else: 
            return tool_pValSupp(N, lInter, prs[1-side]*(prs[side] * lX/N))
    pValSuppRedCand = staticmethod(pValSuppRedCand)

    # redescription p-value using marginals (binomial), for candidates
    def pValMargRedCand(side, op, neg, lParts, N, prs = None):
        lInter = SParts.sumPartsIdInOut(side, neg, SParts.IDS_fixnum[op] + SParts.IDS_varnum[op], lParts)
        lO = SParts.sumPartsId(1-side, SParts.IDS_supp, lParts[SParts.inOutId(SParts.tot, neg)])
        lS = SParts.sumPartsIdInOut(side, neg, SParts.IDS_nsupp[op], lParts)
        return tool_pValSupp(N, lInter, float(lO*lS)/(N*N))
    pValMargRedCand = staticmethod(pValMargRedCand)
    
    # redescription p-value using support sizes (hypergeom), for candidates
    def pValOverRedCand(op, neg, lParts, N, prs = None):
        lInter = SParts.sumPartsIdInOut(side, neg, SParts.IDS_fixnum[op] + SParts.IDS_varnum[op], lParts)
        lO = SParts.sumPartsId(1-side, SParts.IDS_supp, lParts[SParts.inOutId(SParts.tot, neg)])
        lS = SParts.sumPartsIdInOut(side, neg, SParts.IDS_nsupp[op], lParts)
        return tool_pValOver(lInter, N, lO, lS)
    pValOverRedCand = staticmethod(pValOverRedCand)

    # initialize parts counts
    # default count for every part is zero
    # pairs contains a list of (part_id, value)
    # if value is non negative, the count of part_id is set to that value
    # if value is negative, the count of part_id is set to - value - sum of the other parts set so far
    def makeLParts(pairs=[], side=0):
        lp = [0 for i in range(SParts.top+1)]
        for (part_id, val) in pairs:
            if SParts.partId(part_id, side) < len(lp):
                if val < 0:
                    tmp = sum(lp)
                    lp[SParts.partId(part_id, side)] = -val- tmp
                else:
                    lp[SParts.partId(part_id, side)] = val
            else:
                if val > 0:
                    raise Exception("Some missin data where there should not be any!")
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

    # Make binary out of supp set
    def suppVect(N, supp, val=1):
        vect = None
        if 2*len(supp) < N:
            st = supp
            v = val
            if val == 1:
                vect = numpy.zeros(N)
            else:
                vect = numpy.ones(N)
        else:
            st = set(range(N)) - supp
            v = 1-val
            if val == 0:
                vect = numpy.zeros(N)
            else:
                vect = numpy.ones(N)
        for i in st:
            vect[i] = v
        return vect
    suppVect = staticmethod(suppVect)


    def __init__(self, N, supports, prs = [1,1]):
        try:
            self.pVal = eval('self.pVal%s' % (SParts.methodpVal))
        except AttributeError:
              raise Exception('Oups method to compute the p-value does not exist !')

        #### init from dict_info
        if type(N) == dict:
            self.missing = False
            self.sParts = [set() for i in range(len(SParts.labels))]
            self.prs = [-1, -1]
            self.N = 0
            supp_keys = sdict.keys()
            for i, supp_key in enumerate(SParts.labels):
                if sdict.has_key(supp_key):
                    if i > 3 and len(sdict[supp_key]) > 0:
                        self.missing = True
                    self.sParts[i] = set(sdict.pop(supp_key))

            if sdict.has_key('pr_0'):
                self.prs[0] = sdict.pop('pr_0')
            if sdict.has_key('pr_1'):
                self.prs[1] = sdict.pop('pr_1')
            if sdict.has_key('N'):
                self.N = sdict.pop('N')
            if not self.missing:
                del self.sParts[4:]
        else:
            if type(N) is set:
                self.N = len(N)
                bk = N
            else:
                self.N = N
                bk = None
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
            ## nine supports: interpreted as (alpha, beta, gamma, delta, mua, mub, muaB, mubB, mud)
            elif type(supports) == list and len(supports) == 9:
                self.missing = True
                self.sParts = [set(support) for support in supports]
            ## else: set all empty
            else:
                self.missing = False
                self.sParts = [set(), set(), set(), set(), set(), set(), set(), set(), set()]
                bk = None
            if bk is not None:
                if len(self.sParts) == 3:
                    self.sParts.append(set(bk))
                else:
                    self.sParts[SParts.delta] = set(bk)
                for si, sp in enumerate(self.sParts):
                    if si != SParts.delta:
                        self.sParts[SParts.delta] -= sp

    def nbRows(self):
        return self.N

    def toDict(self):
        sdict = {}
        for i in range(len(self.sParts)):
                 sdict[SParts.labels[i]] = self.part(i)
                 sdict["card_" + SParts.labels[i]] = self.lpart(i)
        for side in [0, 1]:
                 if self.prs[side] != -1:
                     sdict["pr_" + str(side)] = self.prs[side]
        sdict["N"] = self.N
        for info_key, info_meth in SParts.infos.items():
            sdict[info_key] = eval(info_meth)
        return sdict
            
    # contains missing values
    def hasMissing(self):
        return self.missing

    # return copy of the probas
    def probas(self):
        return list(self.prs)

    # return support (used to create new instance of SParts)
    def supparts(self):
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
        pid = SParts.partId(part_id, side)
        if pid < len(self.sParts):
            return self.sParts[pid]
        elif part_id == SParts.delta:
            return set(range(self.N)) - self.sParts[0] - self.sParts[1] - self.sParts[2]
        else:
            return set()
        
    def lpart(self, part_id, side=0):
        pid = SParts.partId(part_id, side)
        if pid < len(self.sParts):
            return len(self.sParts[pid])
        elif part_id == SParts.delta:
            return self.N - len(self.sParts[0]) - len(self.sParts[1]) - len(self.sParts[2])
        else:
            return 0

    def parts(self, side=0):
        return [self.part(i, side) for i in range(SParts.top+1)]
            
    def lparts(self, side=0):
        return [self.lpart(i, side) for i in range(SParts.top+1)]
    
    def partInterX(self, suppX, part_id, side=0):
        pid = SParts.partId(part_id, side)
        if pid < len(self.sParts):
            return set(suppX & self.sParts[pid])
        elif part_id == SParts.delta:
            return set(suppX - self.sParts[0] - self.sParts[1] - self.sParts[2])
        else:
            return set()
        
    def lpartInterX(self, suppX, part_id, side=0):
        pid = SParts.partId(part_id, side)
        if pid < len(self.sParts):
            return len(suppX & self.sParts[pid])
        elif part_id == SParts.delta:
            return len(suppX - self.sParts[0] - self.sParts[1] - self.sParts[2])
        else:
            return 0

    def partsInterX(self, suppX, side=0):
        return [self.partInterX(suppX, i, side) for i in range(SParts.top+1)]
    
    def lpartsInterX(self, suppX, side=0):
        if self.missing:
            return [self.lpartInterX(suppX, i, side) for i in range(SParts.top+1)]
        else:
            la = self.lpartInterX(suppX, SParts.alpha, side)
            lb = self.lpartInterX(suppX, SParts.beta, side)
            lc = self.lpartInterX(suppX, SParts.gamma, side)
            tmp = [la, lb, lc, len(suppX) - la - lb - lc]
            for i in range(len(tmp), SParts.top+1):
                tmp.append(0)
            return tmp

    def nbParts(self):
        return SParts.top+1
        
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
            return self.part_union(set(range(SParts.top+1)) - set(SParts.IDS_supp + SParts.IDS_miss), side)
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

    ### SUPPORTS
    def suppSide(self, side):
        if side == 0:
            return self.part_union(SParts.IDS_dL+SParts.IDS_inter, 0)
        else:
            return self.part_union(SParts.IDS_dR+SParts.IDS_inter, 0)
    def suppD(self, side=0):
        return self.part_union(SParts.IDS_diff, side)
    
    def suppI(self, side=0):
        return self.part_union(SParts.IDS_inter, side)
    def suppU(self, side=0):
        return self.part_union(SParts.IDS_inter+SParts.IDS_diff, side)
    def suppL(self, side=0):
        return self.suppSide(0)
    def suppR(self, side=0):
        return self.suppSide(1)
    def suppO(self, side=0):
        return self.part_union(SParts.IDS_uncovered, side)
    def suppT(self, side=0):
        if len(self.sParts) == 4:
            return self.part_union(range(4), side)
        else:
            return set(range(self.N))
    def suppA(self, side=0):
        return self.part_union(SParts.IDS_dL, side)
    def suppB(self, side=0):
        return self.part_union(SParts.IDS_dR, side)

    ### LENGHTS
    def lenSide(self, side):
        if side == 0:
            return self.lparts_union(SParts.IDS_dL+SParts.IDS_inter, 0)
        else:
            return self.lparts_union(SParts.IDS_dR+SParts.IDS_inter, 0)
    def lenD(self, side=0):
        return self.lparts_union(SParts.IDS_diff, side)
    
    def lenI(self, side=0):
        return self.lparts_union(SParts.IDS_inter, side)
    def lenU(self, side=0):
        return self.lparts_union(SParts.IDS_inter+SParts.IDS_diff, side)
        return self.suppI(side) | self.suppD(side)
    def lenL(self, side=0):
        return self.lenSide(0)
    def lenR(self, side=0):
        return self.lenSide(1)
    def lenO(self, side=0):
        return self.lparts_union(SParts.IDS_uncovered, side)
    def lenT(self, side=0):
        if len(self.sParts) == 4:
            return self.lparts_union(range(4), side)
        else:
            return self.N
    def lenA(self, side=0):
        return self.lparts_union(SParts.IDS_dL, side)
    def lenB(self, side=0):
        return self.lparts_union(SParts.IDS_dR, side)


    ## corresponding lengths
    def lenD(self, side=0):
        return self.lparts_union(SParts.IDS_diff, side)
    def lenI(self, side=0):
        return self.lparts_union(SParts.IDS_inter, side)
    def lenO(self, side=0):
        return self.lparts_union(SParts.IDS_uncovered, side)
    def lenU(self, side=0):
        return self.lenD(side)+self.lenI(side)
    def lenL(self, side=0):
        return self.lparts_union(SParts.IDS_dL, side)
    def lenR(self, side=0):
        return self.lparts_union(SParts.IDS_dR, side)

    # accuracy
    def acc(self, side=0):
        lenI = self.lenI(side)
        if lenI == 0:
            return 0
        else:
            return lenI/float(lenI+self.lenD(side))

    # redescription p-value using support probabilities (binomial), for redescriptions
    def pValSupp(self):
        if self.prs == [-1,-1] or self.N == -1:
            return -1
        elif self.lenSupp(0)*self.lenSupp(1) == 0:
            return 0
        else:
            return tool_pValSupp(self.N, self.lenI(), self.prs[0]*self.prs[1]) 

    # redescription p-value using marginals (binomial), for redescriptions
    def pValMarg(self):
        if self.N == -1:
            return -1
        elif self.lenSupp(0)*self.lenSupp(1) == 0:
            return 0
        else:
            return tool_pValSupp(self.N, self.lenI(), float(self.lenSupp(0)*self.lenSupp(1))/(self.N*self.N)) 

    # redescription p-value using support sizes (hypergeom), for redescriptions
    def pValOver(self):
        if self.N == -1:
            return -1
        elif self.lenSupp(0)*self.lenSupp(1) == 0:
            return 0
        else:
            return tool_pValOver(self.lenI(), self.N, self.lenSupp(0) ,self.lenSupp(1))

    # moves the instersection of supp with part with index id_from to part with index id_to
    def moveInter(self, side, id_from, id_to, supp):
        self.sParts[SParts.partId(id_to, side)] |= (self.sParts[SParts.partId(id_from,side)] & supp)
        self.sParts[SParts.partId(id_from,side)] -= supp

    # update support probabilities
    def updateProba(prA, prB, OR):
        if type(prA) == int and prA == -1:
            return prB
        elif OR :
            return prA + prB - prA*prB
        else :
            return prA*prB
    updateProba = staticmethod(updateProba)

    # update supports and probabilities resulting from appending X to given side with given operator
    def update(self, side, OR, suppX, missX):
        self.vect = None
        union = None
        self.prs[side] = SParts.updateProba(self.prs[side], len(suppX)/float(self.N), OR)
            
        if not self.missing and (type(missX) == set and len(missX) > 0):
            self.missing = True
            if len(self.sParts) == 3:
                self.sParts.append(set(range(self.N)) - self.sParts[0] - self.sParts[1] -self.sParts[2])
            else:
                union = set(self.sParts[0] | self.sParts[1] | self.sParts[2] | self.sParts[3])
            self.sParts.extend( [set(), set(), set(), set(), set() ])
            
        if self.missing and SParts.top > SParts.delta:
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
        if union is not None:
            self.sParts[SParts.delta] = union - self.sParts[SParts.gamma] - self.sParts[SParts.beta] - self.sParts[SParts.alpha]
        
    # computes vector ABCD (vector containg for each row the index of the part it belongs to)
    def makeVectorABCD(self):
        if self.vect is None:
            if len(self.sParts) == 4:
                svect = {}
                for partId in range(len(self.sParts)):
                    for i in self.sParts[partId]:
                        self.vect[i] = partId
            else:
                self.vect = [SParts.delta for i in range(self.N)]
                for partId in range(len(self.sParts)):
                    for i in self.sParts[partId]:
                        self.vect[i] = partId
                        
                        
    def getVectorABCD(self):
        self.makeVectorABCD()
        if type(self.vect) is dict:
            return None
        return list(self.vect)

    # returns the index of the part the given row belongs to, vectorABCD need to have been computed 
    def partRow(self, row):
        return self.vect[row]

    # return the index of the part the given row belongs to
    # or the intersection of the mode of X with the different parts if row == -1, vectorABCD need to have been computed 
    def lpartsRow(self, row, X=None):
        lp = None
        if row == -1 and X is not None :
            if self.missing:
                lp = [len(X.interMode(self.sParts[i])) for i in range(SParts.top+1)]
            else:
                lp = [0 for i in range(self.nbParts())]
                lp[0] = len(X.interMode(self.sParts[0]))
                lp[1] = len(X.interMode(self.sParts[1]))
                lp[2] = len(X.interMode(self.sParts[2]))
                lp[3] = X.lenMode() - lp[0] - lp[1] - lp[2]
        elif row is not None:
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

    def __str__(self):
        return "SUPPORT:" + (" ".join(["card_" + SParts.labels[i]+":" + str(len(self.sParts[i]))         for i in range(len(self.sParts))]))
