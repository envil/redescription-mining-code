import re, wx, numpy

from ..clired.classData import Data
from ..clired.classSParts import SSetts
from ..clired.classRedescription import Redescription


from .classPltDtHandler import PltDtHandlerBasis, PltDtHandlerWithCoords

import pdb

def vect_avg(x, y):
    return numpy.add(x,y)/2.

def mat_min(x, y):
    return numpy.vstack([numpy.minimum(y,xx) for xx in x])
def mat_max(x, y):
    return numpy.vstack([numpy.maximum(y,xx) for xx in x])

def mat_sum(x, y):
    return numpy.vstack([y+xx for xx in x])
def mat_avg(x, y):
    return mat_sum(x,y)/2.

def div_min_max(x,y):
    return numpy.minimum(x, y)/(1.*numpy.maximum(1, numpy.maximum(x, y)))

def mm_div(x, y):
    return numpy.min(x)/numpy.maximum(numpy.max(x), 1.)
def mat_div(x, y):
    return numpy.vstack([div_min_max(xx, y) for xx in x])
def vect_div(x, y):
    return div_min_max(x, y)


### takes one vector or matrix
compare_funs = {"max": numpy.max, "min": numpy.min}

### takes a matrix and return value
merge_mm_funs = {"sum": numpy.sum, "prod": numpy.prod, "div": mm_div, "avg": numpy.mean, "min": numpy.min, "max": numpy.max}
### takes two vectors and return matrix
merge_mat_funs = {"sum": mat_sum, "prod": numpy.outer, "div": mat_div, "avg": mat_avg, "min": mat_min, "max": mat_max}
### takes two vectors and return vector, or two values and return value
merge_vect_funs = {"sum": numpy.add, "prod": numpy.multiply, "div": vect_div, "avg": vect_avg, "min": numpy.minimum, "max": numpy.maximum}

def get_bests(scoring, cxs=None, cys=None, init_ids=None):
    dt = None
    if cxs is None:
        if "matrix" in scoring:
            if init_ids is not None:
                dt = scoring["matrix"][init_ids, :][:, init_ids]
            else:
                dt = scoring["matrix"]
        elif "vector" in scoring:
            if scoring["combine"] in mat_functions_map:
                if init_ids is not None:
                    dt = merge_mat_funs[scoring["combine"]](scoring["vector"][init_ids], scoring["vector"][init_ids])
                else:
                    dt = merge_mat_funs[scoring["combine"]](scoring["vector"], scoring["vector"])
        if dt is not None:
            bv = compare_funs[scoring["compare"]](dt)
            xids, yids = numpy.where(dt == bv)
            if init_ids is not None:
                return init_ids[xids], init_ids[yids], bv
            else:
                return xids, yids, bv
    elif len(cxs) > 1:
        if "matrix" in scoring:
            dt = scoring["matrix"][cxs, cys]
        elif "vector" in scoring:
            if scoring["combine"] in merge_vect_funs:
                dt = merge_vect_funs[scoring["combine"]](scoring["vector"][cxs], scoring["vector"][cys])
        if dt is not None:
            bv = compare_funs[scoring["compare"]](dt)
            ids = numpy.where(dt == bv)
            return cxs[ids], cys[ids], bv
    elif len(cxs) == 1:
        if "matrix" in scoring:
            return cxs, cys, scoring["matrix"][cxs[0], cys[0]]
        elif "vector" in scoring:
            if scoring["combine"] in merge_vect_funs:
                return cxs, cys, merge_vect_funs[scoring["combine"]](scoring["vector"][cxs[0]], scoring["vector"][cys[0]])
    return cxs, cys, scoring["null"]

def merge(scorings, cx, cy):
    for scoring in scorings:
        if "matrix" in scoring:
            d = scoring["matrix"][cx, cx]
            scoring["matrix"][cx, :] = merge_vect_funs[scoring["merge"]](scoring["matrix"][cx, :], scoring["matrix"][cy, :])
            scoring["matrix"][:, cx] = merge_vect_funs[scoring["merge"]](scoring["matrix"][:, cx], scoring["matrix"][:, cy])
            scoring["matrix"][cy, :] = scoring["null"]
            scoring["matrix"][:, cy] = scoring["null"]
            scoring["matrix"][cx, cx] = d
        elif "vector" in scoring:
            scoring["vector"][cx] = merge_vect_funs[scoring["merge"]](scoring["vector"][cx], scoring["vector"][cy])
            scoring["vector"][cy] = scoring["null"]
        
def next_best(scorings, init_cands=None):
    init_ids = numpy.where(init_cands)[0]
    score = [scoring["null"] for scoring in scorings]
    cxs, cys, score[0] = get_bests(scorings[0], init_ids=init_ids)
    # print("best", 0, cxs, cys, score[0])
    for i in range(1, len(scorings)):
        cxs, cys, score[i] = get_bests(scorings[i], cxs, cys)
        # print("best", i, cxs, cys, score[i])
    if cxs[0] ==  cys[0]:
        raise Warning("Pair of same element %s!" % cxs[0])
    return cxs[0], cys[0], score
    
def agg_bottom_up(scorings, dists, init_cands):
    pairs = []
    assignment = numpy.arange(init_cands.shape[0])
    ass_store = [assignment.copy()]
    distances = numpy.zeros(init_cands.shape[0], dtype=int)
    while numpy.sum(init_cands) > 1:
        cx, cy, sc = next_best(scorings, init_cands)

        gy = numpy.where(assignment == cy)[0]
        gx = numpy.where(assignment == cx)[0]
        d = numpy.sum([numpy.sum([dists[ix, iy] for ix in gx]) for iy in gy])

        gd = distances[cx] + distances[cy] + d
        distances[cx] = gd
        distances[cy] = 0
        totd = numpy.sum(distances)
        
        pairs.append((cx, cy, (sc, d, gd, totd)))
        assignment[gy] = assignment[cx]        
        ass_store.append(assignment.copy())
        init_cands[cy] = False
        merge(scorings, cx, cy)
    return pairs[::-1], ass_store[-2::-1]

def order_clusts(pairs, ass_store, scoring, nbc=0):
    if len(pairs) == 0:
        if nbc == 0:
            return numpy.array([])
        elif nbc == 1:
            return numpy.array([1])
        else:
            return numpy.arange(nbc, dtype=int)//(nbc-1)
    clust_ord = [pairs[0][0], pairs[0][1]]
    clust_pos = -numpy.ones(ass_store[0].shape, dtype=int)
    clust_pos[pairs[0][0]] = 0
    clust_pos[pairs[0][1]] = 1
    for i in range(1, len(pairs)):
        x, y, _ = pairs[i]
        gx = (ass_store[i] == x)
        gy = (ass_store[i] == y)

        pos_x = clust_pos[x]
        prev_dx, prev_dy, next_dx, next_dy = (0,0,0,0)
        if pos_x > 0:
            prev_n = clust_ord[pos_x-1]        
            gn = (ass_store[i] == prev_n)
            prev_dx = merge_mm_funs[scoring["merge"]](scoring["matrix"][gx, :][:, gn])
            prev_dy = merge_mm_funs[scoring["merge"]](scoring["matrix"][gy, :][:, gn])

        if pos_x+1 < len(clust_ord):
            next_n = clust_ord[pos_x+1]        
            gn = (ass_store[i] == next_n)
            next_dx = merge_mm_funs[scoring["merge"]](scoring["matrix"][gx, :][:, gn])
            next_dy = merge_mm_funs[scoring["merge"]](scoring["matrix"][gy, :][:, gn])

        clust_pos[clust_ord[pos_x+1:]] += 1
        dt = [prev_dy + next_dx, prev_dx + next_dy]
        if compare_funs[scoring["compare"]](dt) == dt[0]: ### insert y before x
            clust_pos[y] = pos_x
            clust_pos[x] += 1
            clust_ord.insert(pos_x, y)
        else:  ### insert y after x
            clust_pos[y] = pos_x+1
            clust_ord.insert(pos_x+1, y)                
    return clust_pos


class PltDtHandlerList(PltDtHandlerBasis):

    parts_map = {"Exx": SSetts.Exx, "Exo": SSetts.Exo, "Eox": SSetts.Eox, "Eoo": SSetts.Eoo,
                 "Emx": SSetts.Emx, "Exm": SSetts.Exm, "Emo": SSetts.Emo, "Eom": SSetts.Eom, "Emm": SSetts.Emm}
    SPARTS_DEF = ["Exx"]

    CHOICES = {}
    def getChoices(self, key):
        if key in self.CHOICES:
            return self.CHOICES[key]["options"]
        return []

    def getChoice(self, key, i=None):
        if i is None:
            i = self.getIParams()
        if type(i) is dict and key in i:
            i = i[key]
        if type(i) is str:
            return i
        choices = self.getChoices(key)
        if type(i) is int and i >= -1 and len(choices) > 0 and i < len(choices):
            return choices[i]
        elif len(choices) > 0:
            return choices[0]
        return None
    
    def getSettSuppParts(self):
        v = self.getSettV("supp_part_clus", self.SPARTS_DEF)
        m = self.getSettV("miss_part_clus", [])
        return [self.parts_map[x] for x in v+m]

    def hasQueries(self):
        return False
    def getCoords(self):
        pass

    def isSingleVar(self):
        return self.pltdt.get("single_var", False)
    
    def getReds(self):
        ### the actual queries, not copies, to test, etc. not for modifications
        return self.pltdt.get("reds")

    def getWhat(self):
        if self.isSingleVar():
            return self.pltdt["vars"]
        else:
            return self.getReds()
    def getLid(self):
        return self.pltdt["lid"]   

    def setCurrent(self, reds_map, iid=None):
        self.pltdt["lid"] = iid
        if len(reds_map) == 0 or isinstance(reds_map[0][1], Redescription):
            self.pltdt["single_var"] = False
            self.pltdt["reds"] = reds_map
            self.pltdt["srids"] = [rid for (rid, red) in reds_map]
            self.pltdt["spids"] = self.getSettSuppParts()
        else:
            self.pltdt["single_var"] = True
            self.pltdt["vars"] = reds_map

    def getEtoR(self):
        if self.pltdt.get("etor") is None:
            if self.isSingleVar():
                tmp = Data.getMatrixCols([c[1] for c in self.pltdt["vars"]]).T
                if all([Data.isTypeId(c[1].typeId(), "Boolean") for c in self.pltdt["vars"]]):
                    self.pltdt["etor"] = numpy.array(tmp, dtype=bool)
                else:
                    self.pltdt["etor"] = tmp
            elif self.pltdt.get("srids") is not None:
                self.pltdt["etor"] = self.view.parent.getERCache().getEtoR(self.pltdt["srids"], spids=self.pltdt["spids"])
        return self.pltdt.get("etor")
    
    def getDeduplicateER(self):
        if self.pltdt.get("ddER") is None:
            if self.isSingleVar():
                if self.pltdt.get("etor") is not None:
                    self.pltdt["ddER"] = self.view.parent.getERCache().computeDeduplicateER(self.pltdt["etor"])
            elif self.pltdt.get("srids") is not None:
                self.pltdt["ddER"] = self.view.parent.getERCache().getDeduplicateER(self.pltdt["srids"], spids=self.pltdt["spids"])
        return self.pltdt.get("ddER")


    
class PltDtHandlerListBlocks(PltDtHandlerList):


    def getVec(self, inter_params=None):
        if "vec" not in self.pltdt or not self.uptodateIParams(inter_params):
            vec, dets = self.getVecAndDets(inter_params)
            return vec
        return self.pltdt["vec"]

    def getVecDets(self, inter_params=None):
        if "vec_dets" not in self.pltdt or not self.uptodateIParams(inter_params):            
            vec, dets = self.getVecAndDets(inter_params)
            return dets
        return self.pltdt["vec_dets"]
    
    def getVecAndDets(self, inter_params=None):
        vec = numpy.empty((0))
        etor = self.getEtoR()
        vec_dets = {"etor": etor}

        self.pltdt["vec"] = vec
        self.pltdt["vec_dets"] = vec_dets
        return vec, vec_dets
    
    def setCurrent(self, reds_map, iid=None):
        PltDtHandlerList.setCurrent(self, reds_map, iid)
        self.getEtoR()
        self.setPreps()
        self.getDrawer().update()
        self.view.makeMenu()

    def setPreps(self):
        pass

class PltDtHandlerListRanges(PltDtHandlerListBlocks):

    def getVRanges(self):  #### HERE
        if self.pltdt.get("ranges") is None and not self.isSingleVar():
            side_proj = 1
            supp_part = ["x", "x"]
            supp_part[side_proj] = "m"
            supp_id = "E"+"".join(supp_part)
            sides = [side_proj]

            # supp_id = "I"
            # sides = [0, 1]
            data = self.getParentData()
            map_vars = {}
            for rid, r in self.getReds():
                supp = r.supports().getProp("supp", supp_id)
                for side in sides:
                    for li, l in enumerate(r.invLiteralsSide(side, ex_anon=True)):
                        cid = l.colId()
                        k = (side, cid)
                        if k not in map_vars:
                            map_vars[k] = {"ranges": [], "ranges_neg": [], "rids": []}
                        if l.isNeg():
                            map_vars[k]["ranges_neg"].append((l.values(), rid, li, supp))
                        else:
                            map_vars[k]["ranges"].append((l.values(), rid, li, supp))
                        map_vars[k]["rids"].append(rid)

            ks = map_vars.keys()
            for k in ks:
                values = None
                col = data.col(k[0], k[1])
                if Data.isTypeId(col.typeId(), "Numerical"):
                    minv, maxv = (col.getMin(), col.getMax())
                    splits = [{"v": minv, "ids": []}, {"v": maxv, "ids": []}]
                    for i in range(len(map_vars[k]["ranges"])):
                        low, high = map_vars[k]["ranges"][i][0]
                        lowi = 0
                        if not numpy.isinf(low):
                            while splits[lowi]["v"] < low:
                                lowi += 1
                            if splits[lowi]["v"] > low:
                                if lowi == 0: pdb.set_trace()
                                splits.insert(lowi, {"v": low, "ids": list(splits[lowi-1]["ids"])})
                        if numpy.isinf(high):
                            highi = len(splits)-1
                        else:
                            highi = lowi
                            while splits[highi]["v"] < high:
                                highi += 1
                            if splits[highi]["v"] > high:
                                splits.insert(highi, {"v": high, "ids": list(splits[highi-1]["ids"])})
                        for j in range(lowi, highi):
                            splits[j]["ids"].append(i)
                            
                    # #### cap values to 500
                    # if maxv > 500:
                    #     maxv = 500
                    #     splits = [sss for ssi, sss in enumerate(splits) if ssi == 0 or splits[ssi-1]["v"] < 500]                        
                    #     splits[-1]["v"] = 500
                    #     print("range", col, [sss["v"] for sss in splits])
                    
                    
                    w = float(maxv-minv)                    
                    map_vars[k]["ticks"] = [(splt["v"]-minv)/w for splt in splits]
                    
                    lminv, lmaxv = 0, numpy.log10(maxv-minv+1)
                    lw = lmaxv - lminv
                    map_vars[k]["log_ticks"] = [(numpy.log10(splt["v"]-minv+1)-lminv)/lw for splt in splits]
                    map_vars[k]["map_values"] = dict([(vv["v"],vvi) for (vvi,vv) in enumerate(splits)])
                    map_vars[k]["map_values"][float("-inf")] = 0
                    map_vars[k]["map_values"][float("inf")] = len(splits)-1

                if Data.isTypeId(col.typeId(), ["Categorical", "Boolean"]):
                    values = col.getOrd()
                    step = 1./len(values)
                    map_vs = dict([(vv,vvi) for (vvi,vv) in enumerate(values)])
                    splits = [{"v": v, "ids": []} for v in range(len(values))]
                    for i in range(len(map_vars[k]["ranges"])):
                        for j in map_vars[k]["ranges"][i][0]:
                            splits[map_vs[j]]["ids"].append(i)
                    map_vars[k]["values"] = values
                    map_vars[k]["ticks"] = [(i+.5)*step for i in range(len(values))]
                    map_vars[k]["map_values"] = map_vs
                            
                map_vars[k]["splits"] = splits
                map_vars[k]["vname"] = col.getName()
                map_vars[k]["tid"] = col.typeId()
            self.pltdt["ranges"] = map_vars
        return self.pltdt.get("ranges")
    
    def getVecAndDets(self, inter_params=None):
        ranges = self.getVRanges()
        self.pltdt["vec"] = None
        self.pltdt["vec_dets"] = {"ranges": ranges}
        return None, ranges

    
class PltDtHandlerListBlocksCoords(PltDtHandlerWithCoords, PltDtHandlerListBlocks):

    def __init__(self, view):
        PltDtHandlerWithCoords.__init__(self, view)    
   
class PltDtHandlerListVarSplits(PltDtHandlerListBlocksCoords):
    
    CUSTOM_ORD_CIDS = None #[0, 2, 8, 10, 7, 6, 1, 9, 4, 5, 3, 11]
    CUSTOM_ORD_RIDS = None #[(ii, "r%d.%02d" % (1+(ii>9), (ii%10)+1)) for ii in [12, 16, 2, 13, 11, 0, 17, 8, 6, 18, 5, 19, 3, 14, 9, 4, 15, 7, 1, 10]]
    
    CHOICES = {"choice_var": {"label": "var.", "options": []}}
    def getChoices(self, key):
        if key == "choice_var":
            return self.getVarOpts()
        elif key in self.CHOICES:
            return self.CHOICES[key]["options"]
        return []
    
    def getIParamsChoices(self):
        return self.CHOICES.items()

    def uptodateIParams(self, inter_params=None):
        if inter_params is None:
            return True
        if self.pltdt.get("inter_params") is not None:
            return all([self.pltdt["inter_params"].get(p) == inter_params.get(p) for p in ["choice_agg"]])
        return False
            
    def updatedIParams(self, inter_params=None):
        self.pltdt["inter_params"] = inter_params
        self.setInterParams()

    def setInterParams(self):        
        ielems = self.getDrawer().getInterElements()
        if "choice_var" in ielems:
            opts = self.getChoices("choice_var")
            if len(opts) > 0:
                _, lbls = zip(*opts)
                ielems["choice_var"].SetItems(lbls)
                ielems["choice_var"].SetSelection(0)

    def getVarOpts(self):
        data = self.getParentData()
        cols = []
        for side in data.getSides():
            for col in data.colsSide(side):
                if not Data.isTypeId(col.typeId(), "Numerical"):
                    cols.append((col, "%d:%d %s" % (col.getSide(), col.getId(), col.getName())))
        return cols
            
    def setPreps(self):
        self.setInterParams()

    def getClustDetails(self, nodes, etor, cols=None, rows=None, counts=None):
        disp_values = self.getSettV("blocks_disp_values")
        if len(nodes) == 0:
            return {"occ_avg": [], "occ_str": []}
        if cols is None:
            cols = range(etor.shape[1])

        if rows is not None:
            nn = rows[nodes]
        else:
            nn = nodes
                            
        if counts is not None:
            occ_avg = numpy.average(1*etor[nn,:][:, cols], axis=0, weights=counts[nodes])
            sumw = numpy.sum(counts[nodes])
        else:
            occ_avg = numpy.average(1*etor[nn,:][:, cols], axis=0)
            sumw = len(nodes)
            
        if disp_values == "Counts":
            occ_str = ["%d" % int(sumw*v) for v in occ_avg]
        elif disp_values == "Percentages":
            occ_str = ["%d" % 100*v for v in occ_avg]
        else:
            occ_str = ["%.2f" % v for v in occ_avg]
        return {"occ_avg": occ_avg, "occ_str": occ_str}
        
    def getVecAndDets(self, inter_params=None):           
        details = {}
        etor = self.getEtoR()  
        data = self.getParentData()
        cc = self.getChoice("choice_var", inter_params)
        if cc is not None:
            col = cc[0]
            vec = col.getVect()
        else:
            col = None
            vec = numpy.ones(data.nbRows(), dtype=int)
 
        uvals = sorted(set(numpy.unique(vec)).difference([-1]))
        if self.CUSTOM_ORD_CIDS is not None and len(self.CUSTOM_ORD_CIDS) == len(uvals): # for custom order
            uvals = self.CUSTOM_ORD_CIDS

        vec_dets = {"typeId": 2, "single": True, "blocks": True,
                    "binLbls": [], "binVals": uvals, "cols": range(etor.shape[1])}

        for i in uvals:
            nodes = numpy.where(vec==i)[0]
            details[i] = self.getClustDetails(nodes, etor)
            if col is not None:
                vec_dets["binLbls"].append("%s %d" % (col.getValFromNum(i), len(nodes)))
            else:
                vec_dets["binLbls"].append("c%d %d" % (i, len(nodes)))

        ### FIXING THE ORDER AND LABELS OF REDS
        if self.CUSTOM_ORD_RIDS is not None and len(self.CUSTOM_ORD_RIDS) == etor.shape[1]: # for custom order
            details["ord_rids"] = self.CUSTOM_ORD_RIDS
        elif self.pltdt.get("srids") is not None:
            details["ord_rids"] = [(ri, "r%s" % self.pltdt.get("srids")[ri]) for ri in range(etor.shape[1])]
        else:
            details["ord_rids"] = [(ri, "#%d" % ri) for ri in range(etor.shape[1])]
        details["ord_cids"] = uvals
        
        nb = [v-0.5 for v in vec_dets["binVals"]]
        nb.append(nb[-1]+1)
        
        vec_dets["binHist"] = nb        
        vec_dets["more"] = details
        vec_dets["min_max"] = (numpy.min(uvals), numpy.max(uvals)) 
        
        self.pltdt["vec"] = vec
        self.pltdt["vec_dets"] = vec_dets
        return vec, vec_dets

    
class PltDtHandlerListClust(PltDtHandlerListVarSplits):

    #[49, 0, 1, 36, 43, 23]
    #[0, 1, 36, 43, 23] China teeth
    CUSTOM_ORD_CIDS = None
    
    @classmethod
    def computeDists(tcl, data, weighted=False):
        d = data["nb_other"] - (data["matches_ones"] + data["matches_zeroes"])
        if weighted and "counts" in data:
            d *= numpy.outer(data["counts"], data["counts"])
        return d

    SCORING_METHS = {}
    @classmethod
    def computeScoringsAgg(tcl, data, choice_agg="default_agg"):
        if choice_agg in tcl.SCORING_METHS:
            return tcl.SCORING_METHS[choice_agg](data)
        return tcl.SCORING_METHS["default_agg"](data)
    @classmethod
    def computeScoringOrd(tcl, data, choice_ord="default_ord"):
        ### expects a matrix scoring
        if choice_ord in tcl.SCORING_METHS:
            return tcl.SCORING_METHS[choice_ord](data)[0]
        return tcl.SCORING_METHS["default_ord"](data)[0]
    
    def getScoringsWDist(data):
        #### simple edit distances accounting for cluster sizes
        wdist = float(data["nb_other"]) - (data["matches_ones"] + data["matches_zeroes"])
        wdist *= numpy.outer(data["counts"], data["counts"])
        numpy.fill_diagonal(wdist, float("inf"))
        return [{"matrix": wdist, "compare": "min", "merge": "sum", "null":  float("inf")}]
    
    def getScoringsDistOnes(data):
        #### simple edit distances, favoring common ones
        wdist = float(data["nb_other"]) - (data["matches_ones"] + data["matches_zeroes"])
        numpy.fill_diagonal(wdist, float("inf"))
        return [{"matrix": wdist, "compare": "min", "merge": "max", "null":  float("inf")},
                {"matrix": data["matches_ones"].copy(), "compare": "max", "merge": "min", "null": -1},
                {"vector": data["counts"].copy(), "combine": "div", "compare": "min", "merge": "sum", "null": data["nb"]+1}]
    
    def getScoringsDistSizes(data):
        #### simple edit distances first, sizes diff second
        wdist = float(data["nb_other"]) - (data["matches_ones"] + data["matches_zeroes"])
        numpy.fill_diagonal(wdist, float("inf"))
        return [{"matrix": wdist, "compare": "min", "merge": "max", "null":  float("inf")},
                {"vector": data["counts"].copy(), "combine": "div", "compare": "min", "merge": "sum", "null": data["nb"]+1}]

    SCORING_METHS_L = [("wdist", getScoringsWDist),
                       ("dist-ones", getScoringsDistOnes),
                       ("dist-sizes", getScoringsDistSizes)]
    SCORING_METHS = {"default_agg": getScoringsWDist,
                     "default_ord": getScoringsWDist}
    SCORING_METHS.update(dict(SCORING_METHS_L))    
    
    NBC_DEF = 3
    MAXC_DEF = 12
    CHOICES = {"choice_agg": {"label": "agg.", "options": [l[0] for l in SCORING_METHS_L]},
               "choice_nbc": {"label": "dist.", "options": []}}
        
    def hasClusters(self):
        return True
    
    def getSettMaxClust(self):
        return self.getSettV("max_clus", self.MAXC_DEF)
    
    def uptodateIParams(self, inter_params=None):
        if inter_params is None:
            return True
        if self.pltdt.get("inter_params") is not None:
            return all([self.pltdt["inter_params"].get(p) == inter_params.get(p) for p in ["choice_agg"]])
        return False
            
    def updatedIParams(self, inter_params=None):
        self.pltdt["inter_params"] = inter_params
        self.setInterParams()
        
    def getClusters(self, inter_params=None):
        if self.pltdt.get("clusters") is None or not self.uptodateIParams(inter_params):
            self.pltdt["clusters"] = self.computeClusters(inter_params)
            self.updatedIParams(inter_params)
        return self.pltdt["clusters"]
    
    def computeClusters(self, inter_params=None):
        choice_agg = self.getChoice("choice_agg", inter_params)
        choice_agg = choice_agg.split("_")[0]
        ddER = self.getDeduplicateER()
        if ddER is not None and len(ddER["E"]["rprt"]) > 0:
            dists = self.computeDists(ddER["E"], weighted=True)
            scorings = self.computeScoringsAgg(ddER["E"], choice_agg)
            sc_ord = self.computeScoringOrd(ddER["E"])
            init_cands = numpy.ones(ddER["E"]["rprt"].shape[0], dtype=bool)
            pairs, ass_store = agg_bottom_up(scorings, dists, init_cands)
            clust_pos = order_clusts(pairs, ass_store, sc_ord, init_cands.shape[0])
        else:
            pairs, ass_store, clust_pos = ([], [], numpy.array([]))

        if ddER is not None and len(ddER["R"]["rprt"]) > 0:
            rdists = self.computeDists(ddER["R"], weighted=True)
            rscorings = self.computeScoringsAgg(ddER["R"], choice_agg)
            rsc_ord = self.computeScoringOrd(ddER["R"])
            rinit_cands = numpy.ones(ddER["R"]["rprt"].shape[0], dtype=bool)
            rpairs, rass_store = agg_bottom_up(rscorings, rdists, rinit_cands)
            r_pos = order_clusts(rpairs, rass_store, rsc_ord, rinit_cands.shape[0])
        else:
            r_pos = numpy.array([])
            
        return {"pairs": pairs, "assignments": ass_store, "clust_pos": clust_pos, "r_pos": r_pos}
      
    def setInterParams(self):
        ielems = self.getDrawer().getInterElements()
        if "choice_nbc" in ielems:
            opts = self.getDistOpts()
            sel = numpy.min([len(opts)-1, self.NBC_DEF])
            ielems["choice_nbc"].SetItems(opts)
            ielems["choice_nbc"].SetSelection(sel)
            
    def getDistOpts(self):
        if self.pltdt.get("clusters") is not None:
            return ["%d" % d[-1][-1] for d in self.pltdt["clusters"]["pairs"]]
        else:
            return ["%d" % d for d in range(1,3)]
        
    def setPreps(self):
        self.getClusters()
        self.setInterParams()
        
    def getVecAndDets(self, inter_params=None):
        if inter_params is None:
            inter_params = self.getIParams()

        nbc = self.NBC_DEF
        if type(inter_params) is dict and "choice_nbc" in inter_params:
            nbc = inter_params["choice_nbc"]
            
        vec = numpy.empty((0))
    
        details = {}
        etor = self.getEtoR()
        ddER = self.getDeduplicateER()
        clusters = self.getClusters(inter_params)

        blocks =  False
        ### TESTS WHETHER etor really is a membership matrix, containing only [0,1]
        if set(1*numpy.unique(etor)) <= set([0, 1]):
            blocks =  True
            
        if clusters is not None:
            v_out = -1
            vec = v_out*numpy.ones(ddER["E"]["to_rep"].shape, dtype=int)
            vvec = v_out*numpy.ones(ddER["E"]["to_rep"].shape, dtype=int)

            if len(clusters["assignments"]) > 0:
                assign = clusters["assignments"][nbc]
            else:
                assign = numpy.arange(len(clusters["clust_pos"]))

            details["ord_cids"] = sorted(numpy.unique(assign), key=lambda x: clusters["clust_pos"][x])
            if self.CUSTOM_ORD_CIDS is not None and len(self.CUSTOM_ORD_CIDS) == len(details["ord_cids"]): # for custom order
                details["ord_cids"] = self.CUSTOM_ORD_CIDS


            for i, bid in enumerate(details["ord_cids"]):
                nodes = numpy.where(assign==bid)[0]
                vvec[ddER["E"]["rprt"][nodes]] = i
                for n in nodes:
                    vec[ddER["E"]["to_rep"] == n] = i

                details[bid] = self.getClustDetails(nodes, etor, cols=ddER["R"]["rprt"], rows=ddER["E"]["rprt"], counts=ddER["E"]["counts"])

            ### FIXING THE ORDER AND LABELS OF REDS
            if self.getSettV("blocks_reorder_rids", True):
                Rs = numpy.argsort(clusters["r_pos"])
            else:
                Rs = range(len(ddER["R"]["rprt"]))
            if self.CUSTOM_ORD_RIDS is not None and len(self.CUSTOM_ORD_RIDS) == len(Rs): # for custom order
                details["ord_rids"] = self.CUSTOM_ORD_RIDS                
            elif self.pltdt.get("srids") is not None:
                details["ord_rids"] = [(ri, " ".join(["r%s" % self.pltdt.get("srids")[rx] for rx in numpy.where(ddER["R"]["to_rep"] == ri)[0]])) for ri in Rs]
            else:
                details["ord_rids"] = [(ri, "#%d" % ddER["R"]["rprt"][ri]) for ri in Rs]

        vec_dets = {"typeId": 2, "single": True, "blocks": blocks, "cols": ddER["R"]["rprt"]} ### HERE bin lbls        
        vec_dets["binVals"] = numpy.unique(vec[vec>=0]) #numpy.concatenate([numpy.unique(vec[vec>=0]),[-1]])
        vec_dets["binLbls"] = ["c%d %d" % (details["ord_cids"][b], numpy.sum(vec==b)) for b in vec_dets["binVals"]]

        nb = [v-0.5 for v in vec_dets["binVals"]]
        if len(nb) > 0:
            nb.append(nb[-1]+1)

        vec_dets["binHist"] = nb        
        vec_dets["more"] = details
        vec_dets["min_max"] = (0, len(details["ord_cids"])-1) 

        #### WRITE CLUSTERS DATA OUT
        # Ccs = numpy.array([[details[i]["occ_avg"][j] for j, rid in details["ord_rids"]] for pi, i in enumerate(details["ord_cids"])])
        # header_str = "RIDS: "+",".join([rid for j, rid in details["ord_rids"]])+"\tCIDS: "+",".join(["%d" % cid for cid in details["ord_cids"]])
        # numpy.savetxt("clusters.csv", Ccs, fmt='%.5f', delimiter=',', header=header_str)
        
        ### debugging: for drawing clustering tree
        # vec_dets["clusters"] = clusters  ### for debugging
        # vec_dets["ddER"] = ddER  ### for debugging
        # vec_dets["etor"] = etor  ### for debugging
        
        self.pltdt["vec"] = vec
        self.pltdt["vec_dets"] = vec_dets
        return vec, vec_dets

        
class PltDtHandlerTextList(PltDtHandlerBasis):

    
    def hasQueries(self):
        return False
    def getCoords(self):
        pass

    def isSingleVar(self):
        return False
    
    def getReds(self):
        ### the actual queries, not copies, to test, etc. not for modifications
        return self.pltdt.get("reds")

    def getWhat(self):
        return self.getReds()
    def getLid(self):
        return self.pltdt["lid"]
    
    def setCurrent(self, reds_map, iid=None):
        self.pltdt["reds"] = reds_map
        self.pltdt["lid"] = iid
