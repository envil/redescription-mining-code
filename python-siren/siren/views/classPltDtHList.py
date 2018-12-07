import re, wx, numpy

from ..reremi.classData import Data
from ..reremi.classSParts import SSetts
from ..reremi.classRedescription import Redescription


from classPltDtHandler import PltDtHandlerBasis, PltDtHandlerWithCoords

import pdb

def isWeightedAgg(choice_agg=None):
    if choice_agg is None:
        return False
    return re.match("w", choice_agg)
def getOpAgg(choice_agg=None):
    if choice_agg is not None and re.search("sum", choice_agg):
        return "sum"
    return "min"


def get_cover_far(dists, nb=0, choice_agg=None, dets=None):
    weighted = isWeightedAgg(choice_agg)
    op = getOpAgg(choice_agg)
    if weighted and dets is not None and "wdists" in dets:
        dists = dets["wdists"]
    
    nodesc = numpy.zeros(dists.shape[0], dtype=int)
    dds = numpy.zeros(dists.shape[0], dtype=int)
    uniq_dds = []
    if dists.shape[0] == 1:
        nodesc[0] = 1
        order = numpy.zeros(1)
        return nodesc, order, dds, uniq_dds
    ### find the two representatives further apart
    x,y = numpy.unravel_index(numpy.argmax(dists), dists.shape)
    nodesc[x] = 1
    nodesc[y] = 2
    dds[x] = dists[x,y]
    dds[y] = dists[x,y]
    ordns = [x, y] 
    uniq_dds.append(dds[x])
    i = 2
    while numpy.sum(nodesc==0) > 0 and (len(uniq_dds) < nb or nb == 0):
        i+=1
        cands = numpy.where(nodesc==0)[0]
        if op == "sum":
            cz = numpy.argmax(numpy.sum(dists[nodesc>0,:][:, cands], axis=0))
            z = cands[cz]
        else:
            z = numpy.argmax(numpy.min(dists[nodesc>0,:], axis=0))
        dds[z] = numpy.min(dists[nodesc>0,z])
        if dds[z] < uniq_dds[-1]:
            uniq_dds.append(dds[z])
        ## print "ASSIGNED", numpy.sum(nodesc==0), z, numpy.min(dists[nodesc>0,z])
        if nodesc[z] > 0:
            print "OUPS! Already picked", z, numpy.where(nodesc>0)
            pdb.set_trace()
        else:
            xsor = numpy.argsort(dists[ordns,z])
            if xsor[1] < xsor[0]:
                ordns.insert(xsor[0], z)
            else:
                ordns.insert(xsor[0]+1, z)
            nodesc[z] = i
    ordns.append(len(ordns))
    return nodesc, ordns, dds, uniq_dds


class PltDtHandlerList(PltDtHandlerBasis):

    
    parts_map = {"Exx": SSetts.Exx, "Exo": SSetts.Exo, "Eox": SSetts.Eox, "Eoo": SSetts.Eoo}
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
        if i >= -1 and i < len(choices):
            return choices[i]
        elif len(choices) > 0:
            return choices[0]
        return None
    
    def getSettSuppParts(self):
        t = self.getParentPreferences()
        try:
            v = t["supp_part_clus"]["data"]
        except:            
            v = self.SPARTS_DEF
        return [self.parts_map[x] for x in v]

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

    
class PltDtHandlerListBlocks(PltDtHandlerWithCoords, PltDtHandlerList):

    def __init__(self, view):
        PltDtHandlerWithCoords.__init__(self, view)    

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


class PltDtHandlerListVarSplits(PltDtHandlerListBlocks):

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
            vec = numpy.ones(data.nbRows())
 
        occs_list = []
        uvals = sorted(set(numpy.unique(vec)).difference([-1]))
        # if len(uvals) == 12:
        #     uvals = [0, 2, 8, 10, 7, 3, 11, 4, 9, 5, 6, 1]
        vec_dets = {"typeId": 2, "single": True, "blocks": True,
                    "binLbls": [], "binVals": uvals}                           

        for i in uvals:
            nodes = numpy.where(vec==i)[0]       
            occ_avg = numpy.average(1*etor[nodes,:], axis=0)
            occ_cnt = numpy.around(occ_avg)
            occs_list.append(occ_avg)
            details[i] = {"occ_avg": occ_avg, "occ_cnt": occ_cnt}
            if col is not None:
                vec_dets["binLbls"].append("%s %d" % (col.getValFromNum(i), len(nodes)))
            else:
                vec_dets["binLbls"].append("c%d %d" % (i, len(nodes)))

        ### FIXING THE ORDER AND LABELS OF REDS
        if False: #True: # for custom order
            tmp = []
            for ri in reversed([10,1,7,15,9,4,14,2,19,8,5,18,17,6,0,11,13,3,16,12]):
                rid = self.pltdt.get("srids")[ri]
                if rid >= 10:
                    tmp.append((ri, "r2.%d" % (rid-9)))
                else:
                    tmp.append((ri, "r1.%d" % (rid+1)))
            details["ord_rids"] = tmp
            occs_list = []
        elif self.pltdt.get("srids") is not None:
            details["ord_rids"] = [(ri, "r%s" % self.pltdt.get("srids")[ri]) for ri in range(etor.shape[1])]
        else:
            details["ord_rids"] = [(ri, "#%d" % ri) for ri in range(etor.shape[1])]
        details["ord_cids"] = uvals

        if len(occs_list) > 0:                
            occ_tots = numpy.array(occs_list).T
            D = numpy.zeros((occ_tots.shape[0], occ_tots.shape[0]))
            for ii in range(occ_tots.shape[0]):
                for jj in range(ii):
                    D[jj,ii] = numpy.sqrt(numpy.sum((occ_tots[ii, :]-occ_tots[jj, :])**2))
                    D[ii, jj] = D[jj,ii] 
            xx = get_cover_far(D)
            #details["ord_rids"].sort(key=lambda x: tuple(occ_tots[x[0],:]))
            details["ord_rids"] = [details["ord_rids"][ii] for ii in xx[1][:-1]]

        nb = [v-0.5 for v in vec_dets["binVals"]]
        nb.append(nb[-1]+1)
        
        vec_dets["binHist"] = nb        
        vec_dets["more"] = details
        vec_dets["min_max"] = (numpy.min(uvals), numpy.max(uvals)) 

        self.pltdt["vec"] = vec
        self.pltdt["vec_dets"] = vec_dets
        return vec, vec_dets

    
class PltDtHandlerListClust(PltDtHandlerListVarSplits):

    NBC_DEF = 2
    MAXC_DEF = 12
    CHOICES = {"choice_agg": {"label": "agg.", "options": ["wmin", "wsum", "min", "sum"]},
               "choice_nbc": {"label": "dist.", "options": []}}
    
    def hasClusters(self):
        return True
    
    def getSettMaxClust(self):
        t = self.getParentPreferences()
        try:
            v = t["max_clus"]["data"]
        except:            
            v = self.MAXC_DEF
        return v
    
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
        ddER = self.getDeduplicateER()
        nodesc, order, dds, uniq_dds = get_cover_far(ddER["dists"], self.getSettMaxClust(), choice_agg, ddER)
        return {"nodesc": nodesc, "order": order, "dds": dds, "uniq_dds": uniq_dds, "nbc_max": numpy.sum(nodesc>0)}    
    
    def setInterParams(self):
        ielems = self.getDrawer().getInterElements()
        if "choice_nbc" in ielems:
            opts = self.getDistOpts()
            sel = numpy.min([len(opts)-1, self.NBC_DEF])
            ielems["choice_nbc"].SetItems(opts)
            ielems["choice_nbc"].SetSelection(sel)
            
    def getDistOpts(self):
        if self.pltdt.get("clusters") is not None:
            nb = numpy.max(self.pltdt["clusters"]["nodesc"])+1
            # return ["%d" % d for d in range(1,nb)]
            return ["%d" % d for d in self.pltdt["clusters"]["uniq_dds"]]
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
            max_dist = 0
            v_out = -1
            ### HAND FIXING THE ORDER, COLORS AND LABELS OF CLUSTERS
            # clusters["order"] = [49, 115, 85, 86, 84]+ [99, 281, 195, 208, 210, 325, 319, 259, 241, 374, 306, 406, 279, 427, 407, 296, 21] 

            if len(clusters.get("uniq_dds", [])) > 0:
                nnb = numpy.min([nbc, len(clusters["uniq_dds"])-1])
                max_dist = clusters["uniq_dds"][nnb]
            nn = sorted(numpy.where(clusters["dds"]>=max_dist)[0], key=lambda x: clusters["nodesc"][x])
            ## nn = sorted(numpy.where((self.clusters["nodesc"]>0) & (self.clusters["nodesc"]<nb+2))[0], key=lambda x: self.clusters["nodesc"][x])
            ord_cids = sorted(range(len(nn)), key=lambda x: clusters["order"][x])
            details["ord_cids"] = ord_cids
            
            # print "NBC", v_out, nb, len(nn), nn
            ### nn contains the representative entities to use as cluster center
            ### next, assign representative entities to the closest entity center
            assign_rprt = numpy.argmin(ddER["dists"][:, nn], axis=1)
            ## for i, v in enumerate(assign_rprt):
            occs_list = []
            choice_agg = self.getChoice("choice_agg", inter_params)
            weighted = isWeightedAgg(choice_agg)
            for i in range(numpy.max(assign_rprt)+1):
                nodes = numpy.where(assign_rprt==i)[0]
                normm = 1+len(nodes)*numpy.max(ddER["dists"][nodes,:][:,nodes])
                center = numpy.argmin(numpy.max(ddER["dists"][nodes,:][:,nodes], axis=0)+numpy.sum(ddER["dists"][nodes,:][:,nodes], axis=0)/normm)
                max_d = numpy.max(ddER["dists"][nodes[center],nodes])
                if weighted:
                    occ_avg = numpy.average(1*etor[ddER["e_rprt"][nodes],:][:, ddER["r_rprt"]], axis=0, weights=ddER["e_counts"][nodes])
                else:
                    occ_avg = numpy.average(1*etor[ddER["e_rprt"][nodes],:][:, ddER["r_rprt"]], axis=0)
                occ_cnt = 1*etor[ddER["e_rprt"][nodes[center]], ddER["r_rprt"]]
                occs_list.append(occ_avg)
                details[i] = {"center": center, "max_d": max_d, "occ_avg": occ_avg, "occ_cnt": occ_cnt}
                # print i, max_d, nodes[center_n]

            ### FIXING THE ORDER AND LABELS OF REDS
            if self.pltdt.get("srids") is not None:
                details["ord_rids"] = [(ri, " ".join(["r%s" % self.pltdt.get("srids")[rx] for rx in numpy.where(ddER["r_to_rep"] == ri)[0]])) for ri, rii in enumerate(ddER["r_rprt"])]
            else:
                details["ord_rids"] = [(ri, "#%d" % rii) for ri, rii in enumerate(ddER["r_rprt"])]

            # ### SPECIFIC ORDERINGS
            # if self.pltdt["lid"] == -1:
            #     details["ord_rids"] = [(ii, ("r1.%02d" % (ii+1))) for ii in [1, 7, 4, 9, 2, 0, 8, 6, 5, 3]]
            # elif self.pltdt["lid"] == -2:
            #     details["ord_rids"] = [(ii, ("r2.%02d" % (ii+1))) for ii in [0, 5, 4, 9, 8, 7, 1, 3, 6, 2]]
            # elif self.pltdt["lid"] == -3:
            #     details["ord_rids"] = [(ii, "r%d.%02d" % (1+(ii>9), (ii%10)+1)) for ii in [12, 16, 3, 13, 11, 0, 6, 17, 18, 5, 8, 19, 2, 14, 4, 9, 15, 7, 1, 10]]
            # elif len(occs_list) > 0:                
            if len(occs_list) > 0:                
                occ_tots = numpy.array(occs_list).T
                D = numpy.zeros((occ_tots.shape[0], occ_tots.shape[0]))
                for ii in range(occ_tots.shape[0]):
                    for jj in range(ii):
                        D[jj,ii] = numpy.sqrt(numpy.sum((occ_tots[ii, :]-occ_tots[jj, :])**2))
                        D[ii, jj] = D[jj,ii] 
                xx = get_cover_far(D)
                #details["ord_rids"].sort(key=lambda x: tuple(occ_tots[x[0],:]))
                details["ord_rids"] = [details["ord_rids"][ii] for ii in xx[1][:-1]]

            if ddER["e_to_rep"] is not None:
                vec = v_out*numpy.ones(ddER["e_to_rep"].shape, dtype=int)
                for i,v in enumerate(assign_rprt):
                    vec[ddER["e_to_rep"] == i] = clusters["order"][v]
            else:
                vec = clusters["order"][assign_rprt]

        vec_dets = {"typeId": 2, "single": True, "blocks": blocks} ### HERE bin lbls        
        vec_dets["binVals"] = numpy.unique(vec[vec>=0]) #numpy.concatenate([numpy.unique(vec[vec>=0]),[-1]])
        vec_dets["binLbls"] = ["c%d %d" % (b,numpy.sum(vec==b)) for b in vec_dets["binVals"]]
        
        nb = [v-0.5 for v in vec_dets["binVals"]]
        nb.append(nb[-1]+1)
        
        vec_dets["binHist"] = nb        
        vec_dets["more"] = details
        vec_dets["min_max"] = (0, numpy.max(clusters["order"])) 

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
