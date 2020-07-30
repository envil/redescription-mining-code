import wx, numpy
import re

from ..clired.classSParts import SSetts
from ..clired.classRedescription import Redescription
from ..clired.classQuery import Query, TimeTools, NA_str_c

import pdb

class PltDtHandlerBasis(object):

    def __init__(self, view):
        self.view = view
        self.pltdt = {}

    def getDrawer(self):
        return self.view.getDrawer()
    def getLayH(self):
        return self.view.getLayH()
    def getSettV(self, key, default=False):
        return self.view.getSettV(key, default)    

    #### SEC: PARENT ACCESS
    ###########################################

    def getId(self):
        return self.view.getId()
    def hasParent(self):
        return self.view.hasParent()
    def getParent(self):
        return self.view.getParent()
    def getParentTab(self, which):
        return self.view.getParentTab(which)
    def getParentViewsm(self):
        return self.view.getParentViewsm()
    def getParentData(self):
        return self.view.getParentData()
    def getParentCoords(self):
        if self.hasParent():
            return self.view.parent.dw.getCoords()
        return [[[0]],[[0]]]
    def getCoordsExtrema(self):
        if self.hasParent():
            return self.view.parent.dw.getCoordsExtrema()
        return (-1., 1., -1., 1.)

    def OnExpandAdv(self, event):
        pass
    def q_expand(self, more):
        if not self.hasQueries():
            return False
        if more is None:
            return True
        res = True
        if "side" in more:
            res &= len(self.getQuery(1-more["side"])) > 0
        if "in_weight" in more or "out_weight" in more:
            res &= self.getDrawer().q_has_selected()
        return res
            

    #### SEC: DATA HANDLING
    ###########################################
    def updateRSets(self, new_rsets):
        if self.pltdt.get("rsets") != new_rsets:
            self.pltdt["rsets"] = new_rsets
            self.setCurrent(self.getRed())
    def getDetailsFolds(self):
        return self.pltdt.get("rsets")
    def getVizRows(self):
        if self.getParentData() is not None:
            return self.getParentData().getVizRows(self.getDetailsFolds()) 
        return set()
    def getUnvizRows(self):
        if self.getParentData() is not None:
            return self.getParentData().getUnvizRows(self.getDetailsFolds())
        return set()

    def hasQueries(self):
        return False
    def getQuery(self, side):
        pass
    def getQueries(self):
        pass
    def hasClusters(self):
        return False
    def getQueries(self):
        pass
    def getCopyRed(self):
        pass
    def getCoords(self):
        pass
    def getVec(self, more=None):
        pass
    def getVecDets(self, inter_params=None):
        pass
    def getRed(self):
        pass

    def isSingleVar(self):
        return False
    
    def setCurrent(self, data, iid=None):
        pass
    def getWhat(self):
        return self.pltdt.get("red")

    def uptodateIParams(self, inter_params=None):
        return True
    def updatedIParams(self, inter_params=None):
        pass
    def getIParams(self):
        return self.pltdt.get("inter_params")

    
class PltDtHandlerWithCoords(PltDtHandlerBasis):

    def __init__(self, view):
        PltDtHandlerBasis.__init__(self, view)
        self.pltdt["coords_org"] = self.getParentCoords()
        self.pltdt["coords"] = self.mapCoords(self.getParentCoords())
    
    def setBM(self, bm):
        self.pltdt["bm"] = bm
        self.pltdt["coords_proj"] = self.mapCoords(self.pltdt["coords_org"], self.getBM())
        
    def getBM(self):
        return self.pltdt.get("bm")

    def getCoords(self, axi=None, ids=None):
        coords = self.pltdt.get("coords_proj")
        if coords is None and "coords" in self.pltdt:
            coords = self.pltdt["coords"]
        if coords is None:
            return coords
        if axi is None:
            return coords[0][:,:,0]
        elif ids is None:
            return coords[0][axi,:,0]
        return coords[0][axi,ids,0]
    def getCoordsP(self, id):
        coords = self.pltdt.get("coords_proj")
        if coords is None and "coords" in self.pltdt:
            coords = self.pltdt["coords"]
        if coords is None:
            return coords
        return coords[0][:,id,1:coords[1][id]].T
    def getCoordsXY(self, id):
        coords = self.pltdt.get("coords_proj")
        if coords is None and "coords" in self.pltdt:
            coords = self.pltdt["coords"]
        if coords is None:
            return (0,0)
        else:
            return coords[0][:,id,0]
    def getCoordsXYA(self, id):
        return self.getCoordsXY(id)

    def hasPolyCoords(self):
        return self.pltdt.get("has_poly", False)

    def mapCoords(self, coords, bm=None):
        self.pltdt["has_poly"] = False
        if coords is None:
            return None
        self.pltdt["has_poly"] = (min([len(cs) for cs in coords[0]]) > 2)

        nbc_max = max([len(c) for c in coords[0]])
        proj_coords = [numpy.zeros((2, len(coords[0]), nbc_max+1)), []]

        for i in range(len(coords[0])):
            if bm is None:
                p0, p1 = (coords[0][i], coords[1][i])
            else:
                p0, p1 = bm(coords[0][i], coords[1][i])
            proj_coords[1].append(len(p0)+1)
            proj_coords[0][0,i,0] = numpy.mean(p0)
            proj_coords[0][0,i,1:proj_coords[1][-1]] = p0
            proj_coords[0][1,i,0] = numpy.mean(p1)
            proj_coords[0][1,i,1:proj_coords[1][-1]] = p1
        return proj_coords
    

class PltDtHandlerWithTime(PltDtHandlerBasis):


    YVAL_LOW, YVAL_HIGH = (-.2, 0.)
    YVAL_BASE = (YVAL_HIGH+YVAL_LOW)/2.
    
    def __init__(self, view):
        PltDtHandlerBasis.__init__(self, view)
        self.pltdt["time_org"] = None
        if self.getParentData().isTimeConditional():
            self.pltdt["time_org"] = self.getParentData().getTimeCoord()
            
        # self.pltdt["time"] = self.mapCoords(self.getParentCoords())

    def getCoordsY(self):
        return self.YVAL_BASE

    def getCoordsExtrema(self):
        coord = self.pltdt["time_org"]
        if coord is None:
            return (-1., 1., -1., 1.)
        return (numpy.min(coord), numpy.max(coord), self.YVAL_LOW, self.YVAL_HIGH)

    def getCoordTicks(self, nb=10, nb_min=3):
        cc = self.getParentData().getTimeCoordCol()
        if cc is None:
            return numpy.arange(-1,1,0.1)
        time_prec = cc.getTimePrec()
        cmin, cmax = (cc.getMin(), cc.getMax())
        vals = numpy.linspace(cmin, cmax, nb)

        ll = TimeTools.lower_time_prec(time_prec)
        llbls = [TimeTools.format_time(val, ll) for val in vals]
        if len(set(llbls)) >= nb_min:
            vvals = [TimeTools.parse_time(lll) for lll in set(llbls)]
            vvals = sorted([v for v in vvals if v >= cmin and v <= cmax])
            if len(vvals) >= nb_min:
                lbls = [TimeTools.format_time(val, time_prec) for val in vvals]
                return vvals, lbls
                
        lbls = [TimeTools.format_time(val, time_prec) for val in vals]
        return vals, lbls

    def getCoords(self, axi=None, ids=None):
        coords = self.pltdt.get("time_org")
        # if coords is None and "coords" in self.pltdt:
        #     coords = self.pltdt["coords"]
        if coords is None:
            return coords
        if ids is None:
            if axi == 1:
                return 0*coords+self.YVAL_BASE
            return coords
        if axi == 1:
            return 0*coords[ids]+self.YVAL_BASE
        return coords[ids]
    def getCoordsP(self, id):
        return self.getCoords(ids=id)
    def getCoordsXY(self, id):
        x = self.getCoordsP(id)
        if x is None:
            return (0,self.YVAL_BASE)
        else:
            return (x, self.YVAL_BASE)
    def getCoordsXYA(self, id):
        return self.getCoordsXY(id)
    
    def hasPolyCoords(self):
        return False
    
class PltDtHandlerRed(PltDtHandlerBasis):
     
    def hasQueries(self):
        return True
    def getQuery(self, side):
        return self.pltdt.get("queries", {side: None})[side]
    def getQueries(self):
        return self.pltdt.get("queries")
    def getCopyRed(self):
        return Redescription.fromQueriesPair([self.getQuery(0).copy(), self.getQuery(1).copy()], self.getParentData())

    def hasClusters(self):
        return True
    def getVec(self, more=None):
        return self.pltdt.get("vec")
    def getVecDets(self, inter_params=None):
        return self.pltdt.get("vec_dets")
    def getRed(self):
        return self.pltdt.get("red")
    def getSuppABCD(self):
        return self.pltdt.get("suppABCD")

    def isSingleVar(self):
        r = self.getRed()
        return r is not None and r.isBasis()
               
    def getQCols(self):
        return [(0,c) for c in self.getQuery(0).invCols()]+[(1,c) for c in self.getQuery(1).invCols()]
    
    def getCol(self, side, c):
        if c == -1 and self.getQuery(side).isXpr():            
            return self.getQuery(side).getXprTerm().getCol()
        return self.getParentData().col(side, c)

    def sendEditBack(self, red=None):
        if red is not None:
            self.getParentViewsm().dispatchEdit(red, vkey=self.getId())

    def parseQuery(self, side):
        stringQ = self.getLayH().getQueryText(side)
        try:
            if Query.hasXpr(stringQ):
                query = Query.parseXpr(stringQ, side, self.getParentData())
            else:
                query = Query.parse(stringQ, self.getParentData().getNames(side))
        except IOError:
            query = None
        if query is not None and (len(stringQ) > 0 and len(query) == 0):
            query = None
        return query

    def prepareValVec(self):
        vec = numpy.empty((0)) 
        vec_dets = {"typeId": 2, "binLbls": None, "binVals": None, "single": False} ### HERE bin lbls
        if self.isSingleVar():
            ccs = self.getQCols()
            col = self.getCol(ccs[0][0], ccs[0][1])
            vec = col.getVector()
            vec_dets["typeId"] = col.typeId()
            if vec_dets["typeId"] == 2:
                vec_dets["binVals"] = numpy.unique(vec)
                vec_dets["binLbls"] = [col.getCatForVal(b, NA_str_c) for b in vec_dets["binVals"]]
            elif vec_dets["typeId"] == 1:
                vec_dets["binVals"] = numpy.unique(vec)
                vec_dets["binLbls"] = [str(bool(b)) if b >= 0 else NA_str_c for b in vec_dets["binVals"]]                
            vec_dets["single"] = True
        elif self.pltdt.get("suppABCD") is not None:
            vec = self.pltdt["suppABCD"].copy()
        return vec, vec_dets
    
    def setCurrent(self, qr=None, iid=None):
        red = None
        if isinstance(qr, Redescription):
            red = qr                
            queries = [red.query(0), red.query(1), red.query(-1)]
        if red is not None:
            # red.setRestrictedSupp(self.getParentData())
            self.pltdt["queries"] = queries
            # self.pltdt["suppABCD"] = numpy.array(red.getRSetABCD(self.getDetailsFolds()), dtype=int)
            self.pltdt["suppABCD"] = numpy.array(red.supports().getVectorABCD(), dtype=int)
            self.pltdt["red"] = red
            self.pltdt["vec"], self.pltdt["vec_dets"] = self.prepareValVec()
            self.getLayH().updateText(red)
            self.getDrawer().update()
            self.view.makeMenu()
            return red

    def updateQuery(self, sd=None, query=None, force=False, upAll=True, update_trees=True):
        # sides = [0,1]
        sides = [0,1,-1]
        if sd is None:
            queries = [self.parseQuery(0), self.parseQuery(1), None]
        else:
            queries = [None, None, None]
            if query is None:
                queries[sd] = self.parseQuery(sd)
            else:
                queries[sd] = query

        changed = False
        old = [None, None, None]
        for side in sides:
            old[side] = self.pltdt["queries"][side]
            if queries[side] != None and queries[side] != self.pltdt["queries"][side]:
                self.pltdt["queries"][side] = queries[side]
                changed = True

        red = None

        if changed or force:
            try:
                red = Redescription.fromQueriesPair(self.pltdt["queries"], self.getParentData())
            except Exception:
                ### Query could be parsed but not recomputed
                red = None
                self.pltdt["queries"] = old

        if red is not None:
            #### SEND BACK
            self.sendEditBack(red)
            # if self.getParentData().hasLT():
            #     red.setRestrictedSupp(self.getParentData())
            # # self.pltdt["suppABCD"] = numpy.array(red.getRSetABCD(self.getDetailsFolds()), dtype=int)
            # self.pltdt["suppABCD"] = numpy.array(red.supports().getVectorABCD(), dtype=int)
            # self.pltdt["red"] = red
            # self.pltdt["vec"], self.pltdt["vec_dets"] = self.prepareValVec()
            # self.getDrawer().update(update_trees)
            # if upAll:
            #     self.getLayH().updateText(red)
            #     self.view.makeMenu()
            #     self.sendEditBack(red)
            return red
        else: ### wrongly formatted query or not edits, revert
            for side in sides:
                self.getLayH().updateQueryText(self.pltdt["queries"][side], side)
        #     red = Redescription.fromQueriesPair(self.pltdt["queries"], self.getParentData())
        # return red
        return None

class PltDtHandlerRedWithCoords(PltDtHandlerWithCoords, PltDtHandlerRed):

    def __init__(self, view):
        PltDtHandlerWithCoords.__init__(self, view)
        
class PltDtHandlerRedWithTime(PltDtHandlerWithTime, PltDtHandlerRed):

    def __init__(self, view):
        PltDtHandlerWithTime.__init__(self, view)
    
