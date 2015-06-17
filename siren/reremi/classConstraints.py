from classRedescription import  Redescription
import pdb

class Constraints:
    
    #     self.cminPairsScore = setts_cust.param['min_score']        
    config_def = "miner_confdef.xml"

    def __init__(self, data, params):
        self._pv = {}
        for k, v in params.items():
            self._pv[k] = v["data"]

        if data is not None:
            self.N = data.nbRows()
            if data.hasMissing() is False:
                self._pv["parts_type"] = "grounded"

            data.getSSetts().reset(self.partsType(), self._pv["method_pval"])
            self.ssetts = data.getSSetts() 
        else:
            self.N = -1
            self.ssetts = None

        if self._pv["amnesic"] == "yes":
            self._pv["amnesic"] = True
        else:
            self._pv["amnesic"] = False
        
        self._pv["min_itm_c"], self._pv["min_itm_in"], self._pv["min_itm_out"] = self.scaleSuppParams(self._pv["min_itm_c"], self._pv["min_itm_in"], self._pv["min_itm_out"])
        self._pv["min_itm_c"], self._pv["min_fin_in"], self._pv["min_fin_out"] = self.scaleSuppParams(self._pv["min_itm_c"], self._pv["min_fin_in"], self._pv["min_fin_out"])
        
        for type_id in [1,2,3]:
            self._pv["lhs_neg_query_%d" % type_id] = []
            for v in params["lhs_neg_query_%d" % type_id]["value"]:
                self._pv["lhs_neg_query_%d" % type_id].append(bool(v))

            self._pv["rhs_neg_query_%d" % type_id] = []
            for v in params["rhs_neg_query_%d" % type_id]["value"]:
                self._pv["rhs_neg_query_%d" % type_id].append(bool(v))

        self._pv["lhs_ops_query"] = []
        for v in params["lhs_ops_query"]["value"]:
            self._pv["lhs_ops_query"].append(bool(v))

        self._pv["rhs_ops_query"] = []
        for v in params["rhs_ops_query"]["value"]:
            self._pv["rhs_ops_query"].append(bool(v))

        self._pv["score_coeffs"] = {"impacc": self._pv["score.impacc"],
                                 "rel_impacc": self._pv["score.rel_impacc"],
                                 "pval_red": self._pv["score.pval_red"],
                                 "pval_query": self._pv["score.pval_query"],
                                 "pval_fact": self._pv["score.pval_fact"]}


    def getSSetts(self):
        return self.ssetts
        
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


    def partsType(self):
        return self._pv["parts_type"]
    def amnesic(self):
        return self._pv["amnesic"]
    def batch_out(self):
        return self._pv["batch_out"]
    def batch_cap(self): 
        return self._pv["batch_cap"]
    def mod_lhs(self):
        return self._pv["mod_lhs"]
    def mod_rhs(self):
        return self._pv["mod_rhs"]
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
    def max_var(self, side=None):
        if "lhs_max_var" in self._pv and "rhs_max_var" in self._pv:
            return [self._pv["lhs_max_var"], self._pv["rhs_max_var"]]
        elif "max_var" in self._pv:
            return [self._pv["max_var"], self._pv["max_var"]]
        return -1
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
    def neg_query(self, side, type_id):
        if side == 1:
            return self._pv["rhs_neg_query_%d" % type_id]
        else:
            return self._pv["lhs_neg_query_%d" % type_id]
    def ops_query(self, side, init=False):
        if init > 0:
            return [True]
        else:
            if side == 1:
                tmp = self._pv["rhs_ops_query"]
            else:
                tmp = self._pv["lhs_ops_query"]
            if init < 0 and self._pv["single_side_or"]=="yes":
                tmp = [o for o in tmp if not o]
            return tmp
    def pair_sel(self):
        return self._pv["pair_sel"]
    def score_coeffs(self):
        return self._pv["score_coeffs"]
    def dl_score(self):
        return self._pv["dl_score"] == "yes"
    def min_node_size(self):
        return self._pv["min_node_size"]
    def max_depth(self):
        return self._pv["max_depth"]
    def mine_algo(self):
        return self._pv["mine_algo"]
    def tree_mine_algo(self):
        return self._pv["tree_mine_algo"]



    def filter_nextge(self, red):
        ### could add check disabled
        return red.nbAvailableCols() == 0

    def sort_nextge(self, red):
        return red.getAcc()

    def sort_partial(self, red):
        return (red.getAcc(), -(red.length(0) + red.length(1)), -abs(red.length(0) - red.length(1)))  

                 
    def filter_partial(self,red):
        if red.length(0) + red.length(1) >= self.min_fin_var() \
                   and red.getLenO() >= self.min_fin_out()\
                   and red.getLenI() >= self.min_fin_in() \
                   and red.getAcc()  >= self.min_fin_acc() \
                   and red.getPVal() <= self.max_fin_pval():
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

    def actions_redundant(self):
       return [("filterpairs", self.parameters_filterredundant())]

    def parameters_filterredundant(self):
       return {"filter_funct": self.pair_filter_redundant, "filter_thres": self.max_overlaparea(), "filter_max":0}

        # possibly useful functions for reds comparison:
        # they should be symmetric
        #     .oneSideIdentical(self.batch[compare])
        #     .equivalent(self.batch[compare])
        #     .redundantArea(self.batch[compare])

