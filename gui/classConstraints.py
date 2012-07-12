from classLog import Log
from classRedescription import  Redescription
from classSParts import SParts
import re
import pdb
class Constraints:
    
    # def __init__(self, data, setts_cust=None):
    #     self.cminPairsScore = setts_cust.param['min_score']        
    #     (self.cminC, self.cminSuppIn, self.cminSuppOut) = data.scaleSuppParams(setts_cust.param['contribution'], setts_cust.param['min_suppin'], setts_cust.param['min_suppout'])
    #     (self.cminLen, self.cminAcc, self.cmaxPVal) = (setts_cust.param['min_length'], setts_cust.param['min_acc'], setts_cust.param['max_pval'])
    #     self.cqueryTypes = setts_cust.param['query_types']
    #     self.draft_out, self.draft_cap, self.min_imprv = setts.param['draft_capacity'], setts.param['draft_output'], setts.param['min_improvement'] 
    #     self.credLength = 0
        
    # def setRedLength(self, n):
    #     self.credLength = n
    # def redLength(self):
    #     return self.credLength

    # def minItmSuppIn(self):
    #     if self.credLength > 0:
    #         return self.cminSuppIn
    #     else:
    #         return 0
    # def minItmSuppOut(self):
    #     return self.cminSuppOut
    #     # if self.credLength > 0:
    #     #     return self.cminSuppOut
    #     # else:
    #     #     return 0
    # def minItmC(self):
    #     return self.cminC
    # def minFinSuppIn(self):
    #     return self.cminSuppIn
    # def minFinSuppOut(self):
    #     return self.cminSuppOut
    # def minFinLength(self):
    #     return self.cminLen
    # def maxFinPVal(self):
    #     return self.cmaxPVal    
    # def minFinAcc(self):
    #     return self.cminAcc
    # def minPairsScore(self):
    #     return self.cminPairsScore
    # def queryTypes(self):
    #     return self.cqueryTypes

    # def queryTypesOp(self):
    #     if self.credLength == 0:
    #         return [True]
    #     else:
    #         return [i for i in self.cqueryTypes.keys() if len(self.cqueryTypes[i])> 0]

    # def negTypesInit(self):
    #     if True in self.cqueryTypes[True] or True in self.cqueryTypes[False]:
    #         return [(0, False, False), (1, False, True), (2, True, False), (3, True, True)]
    #     else:
    #         return [(0, False, False)]

    # def queryTypesNP(self, opOR):
    #     if self.credLength == 0:
    #         return self.cqueryTypes[True] | self.cqueryTypes[False] 
    #     else:
    #         return self.cqueryTypes[opOR]

    def __init__(self, data, setts=None):
        self._amnesic = False
        self._constraints_final = constraints_final
        self._constraints_nextge = constraints_nextge
        self._constraints_partial = constraints_partial
        self._divL = 1
        self._divR = 1
        self._max_agg = 15
        self._max_prodbuckets = 5000
        self._max_red = 10
        self._max_seg = 20
        self._max_sidebuckets = 20
        self._max_var = 3
        self._min_itm_c = 3
        self._min_itm_in = 100
        self._min_itm_out = 100
        self._min_fin_c = 3
        self._min_fin_in = 100
        self._min_fin_out = 100
        self._min_fin_var = 2
        self._min_fin_acc = 0.5
        self._max_fin_pval = 0.05
        self._min_pairscore = 0.01
        self._neg_query = [False]
        self._ops_query = [True, False]
        self._pair_sel = "alternate"
        self._score_coeffs = {"impacc": 1, "relimpacc": 0, "pVal_red": 0.05, "pVal_query": 0.05, "pVal_fact": 1 }

    def draft_out(self):
        return self._score_out
    def dratf_cap(self):
        return self._draft_cap
    def amnesic(self):
        return self._amnesic
    def divL(self):
        return self._divL
    def divR(self):
        return self._divR
    def max_agg(self):
        return self._max_agg
    def max_prodbuckets(self):
        return self._max_prodbuckets
    def max_red(self):
        return self._max_red
    def max_seg(self):
        return self._max_seg
    def max_sidebuckets(self):
        return self._max_sidebuckets
    def max_var(self):
        return self._max_var
    def min_itm_c(self):
        return self._min_itm_c
    def min_itm_in(self):
        return self._min_itm_in
    def min_itm_out(self):
        return self._min_itm_out
    def min_fin_c(self):
        return self._min_fin_c
    def min_fin_in(self):
        return self._min_fin_in
    def min_fin_out(self):
        return self._min_fin_out
    def min_fin_var(self):
        return self._min_fin_var
    def min_fin_acc(self):
        return self._min_fin_acc
    def max_fin_pval(self):
        return self._max_fin_pval
    def min_pairscore(self):
        return self._min_pairscore
    def neg_query(self):
        return self._neg_query
    def ops_query(self):
        return self._ops_query
    def pair_sel(self):
        return self._pair_sel
    def score_coeffs(self):
        return self._score_coeffs

    def filter_nextge(self, red):
        ### could add check disabled
        return red.nbAvailableCols() > 0

    def sort_nextge(self, red):
        red.acc()

    def sort_nextge(self, red):
        red.acc()

    def constraints_nextge(self):
        return { "cutoff_nb": self._draft_cap,
                 "cutoff_type": 0,
                 "indiv_filter_A": self.filter_nextge,
                 "sort_key_B": self.sort_nextge,
                 "sort_reverse_B": True }
    
    def filter_partial(self,red):
        if red.length(0) + red.length(1) >= self.min_fin_var() \
                   and red.lenO() >= self.min_fin_out()\
                   and red.lenI() >= self.min_fin_in() \
                   and red.acc()  >= self.min_fin_acc() \
                   and red.pVal() <= self.max_fin_pval():
            # Constraints.logger.printL(3, 'Redescription complies with final constraints ... (%s)' %(red))
            return True
        else:
            # Constraints.logger.printL(3, 'Redescription non compliant with final constraints ...(%s)' % (red))
            return False

    def pair_filter_partial(self, redA, redB):
        if redA.oneSideIdentical(redB) and not redA.equivalent(redB):
            return 1
        return 0

    def constraints_partial(self):
        return { "cutoff_nb": self.draft_out(),
                 "cutoff_type": 0,
                 "indiv_filter_A": self.filter_partial,
                 "sort_key_A": self.sort_partial,
                 "sort_reverse_A": True,
                 "pair_filter": self.pair_filter_partial,
                 "pair_maxmatch": 2}

    def constraints_final(self):
        return constraints_partial()

        # possibly useful functions for reds comparison:
        #     .oneSideIdentical(self.draft[compare], count_iden, max_iden)
        #     .equivalent(self.draft[compare])


# self.amnesic = amnesic
# self.constraints_final = constraints_final
# self.constraints_nextge = constraints_nextge
# self.constraints_partial = constraints_partial
# self.divL = divL
# self.divR = divR
# self.max_agg = max_agg
# self.max_prodbuckets = max_prodbuckets 
# self.max_red = max_red
# self.max_seg = max_seg
# self.max_sidebuckets = max_sidebuckets
# self.max_var = max_var
# self.min_itm_c = max_itm_c
# self.min_itm_in = min_itm_in 
# self.min_itm_out = min_itm_out
# self.min_pairscore = min_pairscore
# self.neg_query = neg_query
# self.ops_query = ops_query
# self.pair_sel = pair_sel
# self.score_coeffs = score_coeffs
