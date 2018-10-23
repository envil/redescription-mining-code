import wx, numpy

from ..reremi.classData import Data
from ..reremi.classSParts import SSetts
from ..reremi.classRedescription import Redescription


from classPltDtHandler import PltDtHandlerBasis, PltDtHandlerWithCoords

import pdb

def get_cover_far(dists, nb):
    order = -numpy.ones(dists.shape[0])
    nodesc = numpy.zeros(dists.shape[0], dtype=int)
    dds = numpy.zeros(dists.shape[0], dtype=int)
    uniq_dds = []
    if dists.shape[0] == 1:
        nodesc[0] = 1
        order[0] = 0
        return nodesc, order, dds, uniq_dds
    x,y = numpy.unravel_index(numpy.argmax(dists), dists.shape)
    nodesc[x] = 1
    nodesc[y] = 2
    dds[x] = dists[x,y]
    dds[y] = dists[x,y]
    order[x] = 0.
    order[y] = 1.
    uniq_dds.append(dds[x])
    i = 2
    while numpy.sum(nodesc==0) > 0 and (len(uniq_dds) < nb or nb == 0):
        i+=1
        # z = numpy.argmax(numpy.sum(dists[nodesc>0,:], axis=0))
        z = numpy.argmax(numpy.min(dists[nodesc>0,:], axis=0))
        dds[z] = numpy.min(dists[nodesc>0,z])
        if dds[z] < uniq_dds[-1]:
            uniq_dds.append(dds[z])
        ## print "ASSIGNED", numpy.sum(nodesc==0), z, numpy.min(dists[nodesc>0,z])
        if nodesc[z] > 0:
            print "OUPS! Already picked", z, numpy.where(nodesc>0)
            pdb.set_trace()
        else:
            ww = numpy.max(dists[z, nodesc>0])+1 - dists[z, nodesc>0]
            order[z] = numpy.dot(order[nodesc>0], ww)/numpy.sum(ww)
            nodesc[z] = i
    o = numpy.zeros(numpy.sum(nodesc>0)+1)
    o[nodesc[nodesc>0][numpy.argsort(order[nodesc>0])]-1] = numpy.arange(numpy.sum(nodesc>0))
    return nodesc, o, dds, uniq_dds

class PltDtHandlerList(PltDtHandlerBasis):

    
    parts_map = {"Exx": SSetts.Exx, "Exo": SSetts.Exo, "Eox": SSetts.Eox, "Eoo": SSetts.Eoo}
    SPARTS_DEF = ["Exx"]   
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
    
    def setCurrent(self, reds_map):
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

    def getVec(self, nbc=None):
        if "vec" not in self.pltdt:
            vec, dets = self.getVecAndDets(nbc)        
            return vec
        return self.pltdt["vec"]

    def getVecDets(self, nbc=None):
        if "vec_dets" not in self.pltdt:
            vec, dets = self.getVecAndDets(nbc)        
            return dets
        return self.pltdt["vec_dets"]
    
    def getVecAndDets(self, nbc=None):
        vec = numpy.empty((0))
        etor = self.getEtoR()
        vec_dets = {"etor": etor}

        self.pltdt["vec"] = vec
        self.pltdt["vec_dets"] = vec_dets
        return vec, vec_dets
    
    def setCurrent(self, reds_map):
        PltDtHandlerList.setCurrent(self, reds_map)
        self.getEtoR()
        self.setPreps()
        self.getDrawer().update()
        self.view.makeMenu()

    def setPreps(self):
        pass
    
class PltDtHandlerListClust(PltDtHandlerListBlocks):

    NBC_DEF = 2
    MAXC_DEF = 12
    
    def getSettMaxClust(self):
        t = self.getParentPreferences()
        try:
            v = t["max_clus"]["data"]
        except:            
            v = self.MAXC_DEF
        return v
        
    def getClusters(self):
        if self.pltdt.get("clusters") is None:
            self.pltdt["clusters"] = self.computeClusters()
        return self.pltdt["clusters"]
        
    def computeClusters(self):
        ddER = self.getDeduplicateER()
        nodesc, order, dds, uniq_dds = get_cover_far(ddER["dists"], self.getSettMaxClust())
        return {"nodesc": nodesc, "order": order, "dds": dds, "uniq_dds": uniq_dds, "nbc_max": numpy.sum(nodesc>0)}    

    def setInterParams(self):
        ielems = self.getDrawer().getInterElements()
        if "choice_nbc" in ielems:
            opts = self.getDistOpts()
            sel = numpy.min([len(opts)-1, 2])
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

    def getVecAndDets(self, nbc=None):
        if nbc is None:
            nbc = self.NBC_DEF
        vec = numpy.empty((0))
    
        details = {}
        etor = self.getEtoR()
        ddER = self.getDeduplicateER()
        clusters = self.getClusters()

        blocks =  False
        if set(1*numpy.unique(etor)) <= set([0, 1]):
            blocks =  True
        if clusters is not None:
            max_dist = 0
            v_out = -1           
            if len(clusters.get("uniq_dds", [])) > 0:
                nnb = numpy.min([nbc, len(clusters["uniq_dds"])-1])
                max_dist = clusters["uniq_dds"][nnb]
            nn = sorted(numpy.where(clusters["dds"]>=max_dist)[0], key=lambda x: clusters["nodesc"][x])
            ## nn = sorted(numpy.where((self.clusters["nodesc"]>0) & (self.clusters["nodesc"]<nb+2))[0], key=lambda x: self.clusters["nodesc"][x])
            orids = sorted(range(len(nn)), key=lambda x: clusters["order"][x])
            details["orids"] = orids
            # print "NBC", v_out, nb, len(nn), nn
            assign_rprt = numpy.argmin(ddER["dists"][:, nn], axis=1)
            ## for i, v in enumerate(assign_rprt):
            for i in range(numpy.max(assign_rprt)+1):
                nodes = numpy.where(assign_rprt==i)[0]
                normm = 1+len(nodes)*numpy.max(ddER["dists"][nodes,:][:,nodes])
                center = numpy.argmin(numpy.max(ddER["dists"][nodes,:][:,nodes], axis=0)+numpy.sum(ddER["dists"][nodes,:][:,nodes], axis=0)/normm)
                max_d = numpy.max(ddER["dists"][nodes[center],nodes])
                occ_avg = numpy.mean(1*etor[ddER["e_rprt"][nodes],:], axis=0)
                occ_cnt = 1*etor[ddER["e_rprt"][nodes[center]],:]
                details[i] = {"center": center, "max_d": max_d, "occ_avg": occ_avg, "occ_cnt": occ_cnt}
                # print i, max_d, nodes[center_n]
                
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

        
