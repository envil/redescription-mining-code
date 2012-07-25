from classSParts import SParts
from classRedescription import  Redescription
import pdb

class Constraints:
    
    #     self.cminPairsScore = setts_cust.param['min_score']        
    config_def = "miner_confdef.xml"

    def __init__(self, N, params):
        self.N = N
        self._pv = {}
        for k, v in params.items():
            self._pv[k] = v["data"]

        if self._pv["amnesic"] == "Yes":
            self._pv["amnesic"] = True
        else:
            self._pv["amnesic"] = False
        
        self._pv["min_itm_c"], self._pv["min_itm_in"], self._pv["min_itm_out"] = self.scaleSuppParams(self._pv["min_itm_c"], self._pv["min_itm_in"], self._pv["min_itm_out"])
        self._pv["min_itm_c"], self._pv["min_fin_in"], self._pv["min_fin_out"] = self.scaleSuppParams(self._pv["min_itm_c"], self._pv["min_fin_in"], self._pv["min_fin_out"])

        self._pv["neg_query"] = []
        for v in params["neg_query"]["value"]:
            self._pv["neg_query"].append(bool(v))

        self._pv["ops_query"] = []
        for v in params["ops_query"]["value"]:
            self._pv["ops_query"].append(bool(v))

        self._pv["score_coeffs"] = {"impacc": self._pv["score.impacc"],
                                 "rel_impacc": self._pv["score.rel_impacc"],
                                 "pVal_red": self._pv["score.pVal_red"],
                                 "pVal_query": self._pv["score.pVal_query"],
                                 "pVal_fact": self._pv["score.pVal_fact"]}

        SParts.setMethodPVal(self._pv["method_pVal"])

    def scaleF(self, f):
        if f >= 1:
            return int(f)
        elif f >= 0 and f < 1 and self.N != 0:
            return  int(round(f*self.N))
        return 0
    
    def scaleSuppParams(self, min_c, min_in=None, min_out=None):
        sc_min_c = self.scaleF(min_c)
        if min_in == -1:
            sc_min_in = sc_min_c
        else:
            sc_min_in = self.scaleF(min_in)
        if min_out == -1:
            sc_min_out = sc_min_in
        else:
            sc_min_out = self.scaleF(min_out)
        return (sc_min_c, sc_min_in, sc_min_out)


    def amnesic(self):
        return self._pv["amnesic"]
    def batch_out(self):
        return self._pv["batch_out"]
    def batch_cap(self): 
        return self._pv["batch_cap"]
    def divL(self):
        return self._pv["divL"]
    def divR(self):
        return self._pv["divR"]
    def max_agg(self):
        return self._pv["max_agg"]
    def max_prodbuckets(self):
        return self._pv["max_prodbuckets"]
    def max_red(self):
        return self._pv["max_red"]
    def max_seg(self):
        return self._pv["max_seg"]
    def max_sidebuckets(self):
        return self._pv["max_sidebuckets"]
    def max_var(self):
        return self._pv["max_var"]
    def min_impr(self):
        return self._pv["min_impr"]
    def min_itm_c(self):
        return self._pv["min_itm_c"]
    def min_itm_in(self):
        return self._pv["min_itm_in"]
    def min_itm_out(self):
        return self._pv["min_itm_out"]
    def min_fin_c(self):
        return self._pv["min_fin_c"]
    def min_fin_in(self):
        return self._pv["min_fin_in"]
    def min_fin_out(self):
        return self._pv["min_fin_out"]
    def min_fin_var(self):
        return self._pv["min_fin_var"]
    def min_fin_acc(self):
        return self._pv["min_fin_acc"]
    def max_fin_pval(self):
        return self._pv["max_fin_pval"]
    def min_pairscore(self):
        return self._pv["min_pairscore"]
    def max_overlaparea(self):
        return self._pv["max_overlaparea"]
    def neg_query(self, side):
        return self._pv["neg_query"]
    def ops_query(self, side, init=False):
        if init != 0:
            return [True]
        else:
            return self._pv["ops_query"]
    def pair_sel(self):
        return self._pv["pair_sel"]
    def score_coeffs(self):
        return self._pv["score_coeffs"]

    def filter_nextge(self, red):
        ### could add check disabled
        return red.nbAvailableCols() == 0

    def sort_nextge(self, red):
        return red.acc()

    def sort_partial(self, red):
        return (red.acc(), -(red.length(0) + red.length(1)), -abs(red.length(0) - red.length(1)))  

                 
    def filter_partial(self,red):
        if red.length(0) + red.length(1) >= self.min_fin_var() \
                   and red.lenO() >= self.min_fin_out()\
                   and red.lenI() >= self.min_fin_in() \
                   and red.acc()  >= self.min_fin_acc() \
                   and red.pVal() <= self.max_fin_pval():
            # Constraints.logger.printL(3, 'Redescription complies with final constraints ... (%s)' %(red))
            return False
        else:
            # Constraints.logger.printL(3, 'Redescription non compliant with final constraints ...(%s)' % (red))
            return True

    def pair_filter_partial(self, redA, redB):
        return redA.oneSideIdentical(redB) and not redA.equivalent(redB)

    def pair_filter_redundant(self, redA, redB):
        return redA.overlapAreaMax(redB)

    def actions_nextge(self):
        return [("filtersingle", {"filter_funct": self.filter_nextge}),
                ("sort", {"sort_funct": self.sort_nextge, "sort_reverse": True }),
                ("cut", { "cutoff_nb": self.batch_cap(), "cutoff_direct": 0})]

    def actions_partial(self):
        return [("filtersingle", {"filter_funct": self.filter_partial}),
                ("sort", {"sort_funct": self.sort_partial, "sort_reverse": True }),
                ("filterpairs", {"filter_funct": self.pair_filter_partial, "filter_max": 0}),
                ("cut", { "cutoff_nb": self.batch_out(), "cutoff_direct": 1, "equal_funct": self.sort_partial})]

    def actions_final(self):
       return [("filtersingle", {"filter_funct": self.filter_partial}),
               ("sort", {"sort_funct": self.sort_partial, "sort_reverse": True }),
               ("filterpairs", {"filter_funct": self.pair_filter_partial, "filter_max": 0})]

    def parameters_filterredundant(self):
       return {"filter_funct": self.pair_filter_redundant, "filter_thres": self.max_overlaparea(), "filter_max":0}

        # possibly useful functions for reds comparison:
        # they should be symmetric
        #     .oneSideIdentical(self.batch[compare])
        #     .equivalent(self.batch[compare])
        #     .redundantArea(self.batch[compare])

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

######################################################################
######################################################################
        
        # self.N = N
        # self._amnesic = False
        # self._batch_out = 1
        # self._batch_cap = 4
        # self._divL = 1
        # self._divR = 1
        # self._max_agg = 15
        # self._max_prodbuckets = 5000
        # self._max_red = 100
        # self._max_seg = 20
        # self._max_sidebuckets = 20
        # self._max_var = 4
        # self._min_impr = 0
        # self._min_itm_c = 3
        # self._min_itm_in = 15
        # self._min_itm_out = 500
        # self._min_fin_c = 3
        # self._min_fin_in = 15
        # self._min_fin_out = 500
        # self._min_fin_var = 2
        # self._min_fin_acc = 0.5
        # self._max_fin_pval = 0.01
        # self._min_pairscore = 0.2
        # self._max_overlaparea = 0.5
        # self._pair_sel = "alternate"
        # self._method_pVal = "marg"
