import wx
### from wx import ALIGN_BOTTOM, ALIGN_CENTER, ALIGN_LEFT, ALIGN_RIGHT, ALL, EXPAND, HORIZONTAL, RAISED_BORDER, TE_PROCESS_ENTER, VERTICAL
### from wx import BoxSizer, DisplaySize, FlexGridSizer, Frame, Menu, MenuBar, NewId, Panel, Sizer, SizerItem, StaticBitmap, StaticText, TextCtrl, ToggleButton
### from wx import EVT_BUTTON, EVT_CLOSE, EVT_ENTER_WINDOW, EVT_LEAVE_WINDOW, EVT_LEFT_UP, EVT_MENU, EVT_SIZE, EVT_TEXT_ENTER, EVT_TOGGLEBUTTON, EVT_TOOL

import numpy
# The recommended way to use wx with mpl is with the WXAgg
# backend. 
# import matplotlib
# matplotlib.use('WXAgg')

from classBasisView import BasisView

from ..reremi.classQuery import SYM, Query
from ..reremi.classSParts import SSetts
from ..reremi.classRedescription import Redescription

import pdb


class GView(BasisView):

    label_jacc="J ="
    label_pval="p-value ="
    label_typeP="J-type ="

    label_cardT="|E| ="
    label_cardU="|E"+SYM.SYM_SETMIN+"E"+SSetts.sym_sparts[SSetts.E_oo]+"| ="    

    label_cardP="|E%s| ="
    
    label_cardAlpha="|E"+SSetts.sym_sparts[SSetts.E_xo]+"| ="
    label_cardBeta="|E"+SSetts.sym_sparts[SSetts.E_ox]+"| ="
    label_cardI="|E"+SSetts.sym_sparts[SSetts.E_xx]+"| ="
    label_cardO="|E"+SSetts.sym_sparts[SSetts.E_oo]+"| ="
    
    label_learn = SYM.SYM_LEARN #+":"
    label_test = SYM.SYM_TEST #+":"
    label_ratio = SYM.SYM_RATIO #+":"

    label_inout = SYM.SYM_INOUT
    label_outin = SYM.SYM_OUTIN 
    label_cross = SYM.SYM_CROSS

    map_select_supp = [("l", "|E"+SSetts.sym_sparts[SSetts.E_xo]+"|", [SSetts.E_xo]),
                       ("r", "|E"+SSetts.sym_sparts[SSetts.E_ox]+"|", [SSetts.E_ox]),
                       ("i", "|E"+SSetts.sym_sparts[SSetts.E_xx]+"|", [SSetts.E_xx]),
                       ("o", "|E"+SSetts.sym_sparts[SSetts.E_oo]+"|", [SSetts.E_oo])]

    infos_details = [] # {"id": "jacc", "label": label_jacc, "meth": "getRoundAcc", "format": "%1.3f"},
                     # {"id": "lenI", "label": label_cardI, "meth": "getLenI", "format": "%i", "color":2},
                     # {"id": "lenA", "label": label_cardAlpha, "meth": "getLenA", "format": "%i", "color":0},
                     # {"id": "lenT", "label": label_cardT, "meth": "getLenT", "format": "%i"},
                     # {"id": "pval", "label": label_pval, "meth": "getRoundPVal", "format": "%1.3f"},
                     # {"id": "lenO", "label": label_cardO, "meth": "getLenO", "format": "%i"},
                     # {"id": "lenB", "label": label_cardBeta, "meth": "getLenB", "format": "%i", "color":1},
                     # {"id": "lenU", "label": label_cardU, "meth": "getLenU", "format": "%i"},
                     # {"id": "typP", "label": label_typeP, "meth": "getTypeParts", "format": "%s", "miss": True},]
                     #####################################################################
    for status in [(True, True), (False, False), (True, False), (False, True)]:
        i = SSetts.mapStatusToSPart(status)
        infos_details.append( {"id": "x%s" % SSetts.labels_sparts[i],
                               "label": label_cardP % SSetts.sym_sparts[i],
                               "meth": "getLenP", "format": "%i", "details": {"part_id": i}})
                
    for status in [(None, None), (False, None), (True, None), (None, True), (None, False)]:
        i = SSetts.mapStatusToSPart(status)
        infos_details.append( {"id": "x%s" % SSetts.labels_sparts[i],
                               "label": label_cardP % SSetts.sym_sparts[i],
                               "meth": "getLenP", "format": "%i", "miss": True, "details": {"part_id": i}})

    infos_details.insert(0, {"id": "jacc", "label": label_jacc, "meth": "getRoundAcc", "format": "%1.3f"})
    infos_details.insert(3, {"id": "lenT", "label": label_cardT, "meth": "getLenT", "format": "%i"})
    infos_details.insert(4, {"id": "pval", "label": label_pval, "meth": "getRoundPVal", "format": "%1.3f"})
    # infos_details.insert(8, {"id": "typP", "label": label_typeP, "meth": "getTypeParts", "format": "%s", "miss": True})
    
    max_emphlbl = 5
    
    TID = "G"
    SDESC = "Viz"
    ordN = 0
    title_str = "View"
    geo = False
    typesI = "evr"

    
    def __init__(self, parent, vid, more=None):
        self.initVars(parent, vid, more)
        self.queries = [Query(), Query()]
        self.initView()
        self.dots_draws = None
        self.suppABCD = None
        self.redStamp = None

    def getValVec(self):
        vec = numpy.empty((0)) 
        vec_dets = {"typeId": 2, "binLbls": None, "binVals": None, "single": False} ### HERE bin lbls
        if self.isSingleVar():
            ccs = self.getQCols()
            col = self.getCol(ccs[0][0], ccs[0][1])
            vec = col.getVector()
            vec_dets["typeId"] = col.typeId()
            if vec_dets["typeId"] == 2:
                vec_dets["binVals"] = numpy.unique(vec)
                vec_dets["binLbls"] = [col.getCatForVal(b, "NA") for b in vec_dets["binVals"]]
            vec_dets["single"] = True
        elif self.suppABCD is not None:
            vec = numpy.array(self.suppABCD)
        return vec, vec_dets
        
    def prepareProcesses(self):
        self.processes_map = {"E*": {"label": "Expand", "legend": "Expand the current redescription.",
                                     "more": None, "more_dyn":[], "order": 0},
                              "EL": {"label": "Expand LHS", "legend": "Expand the LHS query of the current redescription.",
                                     "more": {"side":0}, "more_dyn":[], "order":1},
                              "ER": {"label": "Expand RHS", "legend": "Expand the RHS query of the current redescription.",
                                     "more": {"side":1}, "more_dyn":[], "order":2},
                              "OL": {"label": "Overfit LHS", "legend": "Overfit LHS wrt the selected area.",
                                     "more": {"side":0, "in_weight":10}, "more_dyn":[self.getWeightCover], "order":3},
                              "OR": {"label": "Overfit RHS", "legend": "Overfit RHS wrt the selected area.",
                                     "more": {"side":1, "in_weight":10}, "more_dyn":[self.getWeightCover], "order":4} }
        
    def prepareActions(self):
        ### First letter of action is the key, should be unique
        self.actions_map = {"deselect_all": {"method": self.do_deselect_all, "label": "&Deselect all",
                                             "legend": "Deselect all dots", "more": None, "type": "main",
                                             "order":1, "active_q":self.q_has_selected},
                            "flip_able": {"method": self.do_flip_emphasized, "label": "(Dis)able selected",
                                             "legend": "(Dis)able selected dots", "more": None, "type": "main",
                                             "order":0, "active_q":self.q_has_selected},
                            "noggle_info": {"method": self.do_toggle_info, "label": "Toggle i&nfo",
                                               "legend": "Toggle info", "more": None,  "type": "check",
                                               "order":101, "active_q":self.q_active_info},
                            "vave_sel_var": {"method": self.save_sel_var, "label": "Save selection as variable",
                                               "legend": "Save the selection as a new data variable",
                                               "more": None,  "type": "main",
                                               "order":10, "active_q":self.q_has_selected},
                            "save_supp_var": {"method": self.save_supp_var, "label": "Save supp as variable",
                                                "legend": "Save the support as a new data variable",
                                                "more": None,  "type": "main",
                                                "order":11, "active_q":self.q_not_svar}
                            }

        for setk, setl, setp in self.map_select_supp:
            self.actions_map[setk+"_set"] = {"method": self.do_set_select, "label": "(De)select "+setl,
                                                 "legend": "(De)select dots in "+setl, "more": setp, "type": "main",
                                                 "order":2, "active_q":self.q_not_svar}

        if self.mc is not None:
            self.actions_map["poly_set"] = {"method": self.do_select_poly, "label": "(De)select &polygon",
                                               "legend": "Select dots inside the polygon", "more": None,  "type": "main",
                                               "order":3, "active_q":self.q_has_poly}
            self.actions_map["toggle_draw"] = {"method": self.do_toggle_poly, "label": "&Toggle polygon",
                                               "legend": "Toggle polygon drawing", "more": None,  "type": "check",
                                               "order":100, "active_q":self.q_active_poly}

        
    def enumerateVizItems(self):
        if self.hasParent():
            return self.parent.viewsm.getViewsItems(what=self.getQueries(), vkey=self.getId())
        return []

    def additionalBinds(self):
        self.MapredMapQ[0].Bind(wx.EVT_TEXT_ENTER, self.OnEditQuery)
        self.MapredMapQ[1].Bind(wx.EVT_TEXT_ENTER, self.OnEditQuery)
        for button in self.buttons:
            button["element"].Bind(wx.EVT_BUTTON, button["function"])
        
    def getQueries(self):
        ### the actual queries, not copies, to test, etc. not for modifications
        return self.queries

    def getCopyRed(self):
        return Redescription.fromQueriesPair([self.queries[0].copy(), self.queries[1].copy()], self.getParentData())
        
    def OnExpandAdv(self, event):
        params = {"red": self.getCopyRed()}
        if event.GetId() in self.menu_map_pro:
            more = self.processes_map[self.menu_map_pro[event.GetId()]]["more"]
            if more is not None:
                params.update(more)
            for k in self.processes_map[self.menu_map_pro[event.GetId()]]["more_dyn"]:
                params = k(params)
        self.parent.expandFromView(params)

    def OnExpandSimp(self, event):
        params = {"red": self.getCopyRed()}
        self.parent.expandFromView(params)

    def setSizeSpec(self, figsize):
        self.MapredMapQ[0].SetMinSize((1*figsize[0], -1))
        self.MapredMapQ[1].SetMinSize((1*figsize[0], -1))

    def OnEditQuery(self, event):
        if event.GetId() in self.QIds:
            side = self.QIds.index(event.GetId())
            self.updateQuery(side)

    def refresh(self):
        self.autoShowSplitsBoxes()
        red = Redescription.fromQueriesPair(self.queries, self.getParentData())
        red.setRestrictedSupp(self.getParentData())
        self.suppABCD = red.supports().getVectorABCD()
        self.updateText(red)
        self.updateMap()
        if self.isIntab():
            self._SetSize()

    def updateQuery(self, sd=None, query=None):
        if sd is None:
            queries = [self.parseQuery(0), self.parseQuery(1)]
        else:
            queries = [None, None]
            if query is None:
                queries[sd] = self.parseQuery(sd)
            else:
                queries[sd] = query

        changed = False
        for side in [0,1]:
            if queries[side] != None and queries[side] != self.queries[side]:
                self.queries[side] = queries[side]
                changed = True

        if changed:
            red = Redescription.fromQueriesPair(self.queries, self.getParentData())
            red.setRestrictedSupp(self.getParentData())
            self.suppABCD = red.supports().getVectorABCD()
            self.updateText(red)
            self.makeMenu()
            self.sendEditBack(red)
            self.updateMap()
        else: ### wrongly formatted query or not edits, revert
            for side in [0,1]:
                self.updateQueryText(self.queries[side], side)
            red = Redescription.fromQueriesPair(self.queries, self.getParentData())
        return red

    def setCurrent(self, qr=None):
        if qr is not None:
            if type(qr) in [list, tuple]:
                queries = qr
                red = Redescription.fromQueriesPair(qr, self.getParentData())
            else:
                red = qr
                queries = [red.query(0), red.query(1)]
            self.queries = queries
            red.setRestrictedSupp(self.getParentData())
            self.suppABCD = red.supports().getVectorABCD()
            self.updateText(red)
            self.updateMap()
            self.makeMenu()
            return red
        
    def isSingleVar(self):
        return (len(self.queries[0]) == 0 and self.queries[1].isBasis(1, self.getParentData())) or \
          (len(self.queries[1]) == 0 and self.queries[0].isBasis(0, self.getParentData()))

    def getQCols(self):
        return [(0,c) for c in self.queries[0].invCols()]+[(1,c) for c in self.queries[1].invCols()]
    
    def getCol(self, side, c):
        return self.getParentData().col(side, c)
        
    def parseQuery(self, side):
        stringQ = self.MapredMapQ[side].GetValue().strip()
        try:
            query = Query.parse(stringQ, self.getParentData().getNames(side))
        except:
            query = None
        if query is not None and (len(stringQ) > 0 and len(query) == 0):
            query = None
        return query                    
       

    def drawFrameSpecific(self):
        self.QIds = [wx.NewId(), wx.NewId()]
        self.MapredMapQ = [wx.TextCtrl(self.panel, self.QIds[0], style=wx.TE_PROCESS_ENTER),
                           wx.TextCtrl(self.panel, self.QIds[1], style=wx.TE_PROCESS_ENTER)]
        # self.MapredMapQ = [wx.TextCtrl(self.mapFrame, self.QIds[0]),
        #                    wx.TextCtrl(self.mapFrame, self.QIds[1])]
        colors = self.getColors255()
        self.MapredMapQ[0].SetForegroundColour(colors[0])
        self.MapredMapQ[1].SetForegroundColour(colors[1])

        self.info_items = {}
        for info_item in self.infos_details:
            if not info_item.get("miss", False) or (self.getParentData() is not None and self.getParentData().hasMissing()):
                # self.info_items[info_item["id"]] = (wx.StaticText(self.panel, label=info_item["label"], style=styL, size=sizz),
                #                                     wx.StaticText(self.panel, label="--", style=styV, size=sizz))
                self.info_items[info_item["id"]] = (wx.StaticText(self.panel, label=info_item["label"]),
                                                    wx.StaticText(self.panel, label="XXX"))


                if info_item.get("details", {}).get("part_id", SSetts.E_oo) < SSetts.E_oo:
                    self.info_items[info_item["id"]][1].SetForegroundColour(colors[info_item["details"]["part_id"]])

    def addFrameSpecific(self):
        self.innerBox1.Add(self.MapredMapQ[0], 0, border=1,  flag= wx.ALIGN_CENTER, userData={"where": "it"})
        self.innerBox1.Add(self.MapredMapQ[1], 0, border=1,  flag= wx.ALIGN_CENTER, userData={"where": "it"})

        self.innerBox1.AddSpacer((-1,self.getSpacerH()), userData={"where": "*"})
        
        cols = [wx.BoxSizer(wx.VERTICAL) for i in range(2*self.nb_cols)]
        for pi, elem in enumerate(self.infos_details):
            if not elem.get("miss", False) or (self.getParentData() is not None and self.getParentData().hasMissing()):
                ci = 2*(pi % self.nb_cols)
                cols[ci].Add(self.info_items[elem["id"]][0], 1, border=1,  flag= wx.ALL|wx.ALIGN_RIGHT, userData={"where": "it"})
                cols[ci+1].Add(self.info_items[elem["id"]][1], 1, border=1,  flag= wx.ALL|wx.ALIGN_RIGHT, userData={"where": "it"})
        # self.opt_hide.extend(cols)

        lineB = wx.BoxSizer(wx.HORIZONTAL)
        for ci, col in enumerate(cols):
            lineB.Add(col, 0, border=1,  flag= wx.ALIGN_CENTER|wx.EXPAND)
            if ci % 2 == 1 and ci < len(cols)-1:
                lineB.AddSpacer((self.getSpacerW(),-1), userData={"where": "it"})
        self.innerBox1.Add(lineB, 0, border=1,  flag= wx.ALIGN_CENTER)

 

    def updateQueryText(self, query, side):
        self.MapredMapQ[side].ChangeValue(query.disp(style="U", names=self.getParentData().getNames(side)))
        #self.MapredMapQ[side].ChangeValue(query.disp()) #, unicd=True), unicd=True))

    def updateText(self, red = None):
        """ Reset red fields and info
        """
        if red is not None:
            for side in [0, 1]:
                self.updateQueryText(red.queries[side], side)
            self.setMapredInfo(red)

    def setMapredInfo(self, red = None, details=None):
        for det in self.infos_details:
            if not det.get("miss", False) or (self.getParentData() is not None and self.getParentData().hasMissing()):
                if red is not None:
                    meth = getattr(red,det["meth"], None)
                else:
                    meth = None
                
                if meth is not None:
                    params = self.getDetailsSplit()
                    if params is None:
                        params = {}
                    if "details" in det:
                        params.update(det["details"])
                    self.info_items[det["id"]][1].SetLabel(det["format"] % meth(params))
                else:
                    self.info_items[det["id"]][1].SetLabel("XX")
 

    def apply_mask(self, path, radius=0.0):
        if path is not None and self.getCoords() is not None:
            points = numpy.transpose((self.getCoords(0), self.getCoords(1)))
            return [i for i,point in enumerate(points) if path.contains_point(point, radius=radius)]
        return []
                
    def do_deselect_all(self, more=None):
        self.sendEmphasize(None)

    def do_set_select(self, setp):
        points = [i for (i,p) in enumerate(self.suppABCD) if p in setp]
        self.sendEmphasize(points)
                
    def do_select_poly(self, more=None):
        points = self.apply_mask(self.mc.get_path())
        self.mc.clear()
        if points != set():
            self.sendEmphasize(points)

    def do_flip_emphasized(self, more=None):
        self.sendFlipEmphasizedR()
    def save_supp_var(self, more=None):
        if self.hasParent():
            self.parent.OnSaveSuppAsVar(self.suppABCD, "%s" % self.parent.viewsm.getItemId(self.getId()))
    def save_sel_var(self, more=None):
        if self.hasParent():
            lids = self.parent.viewsm.getEmphasizedR(vkey=self.getId())
            self.parent.OnSaveSelAsVar(lids, "S%s" % self.parent.viewsm.getItemId(self.getId()))
    
    def hasDotsReady(self):
        return self.dots_draws is not None
    
    def getCoords(axi=None, ids=None):
        return None
    def getCoordsXY(self, id):
        return (0,0)
    def getCoordsXYA(self, id):
        return self.getCoordsXY(id)

    def getAnnXY(self):
        return self.ann_xy

    def drawEntity(self, idp, fc, ec, sz, zo=4, dsetts={}):
        x, y = self.getCoordsXY(idp)
        return self.axe.plot(x, y, mfc=fc, mec=ec, marker=dsetts.get("shape"), markersize=sz, linestyle=dsetts.get("linestyle", 'None'), zorder=zo)
    
    def drawAnnotation(self, xy, ec, tag, xytext=(-10, 15)):
        return [self.axe.annotate(tag, xy=xy, zorder=8,
                                xycoords='data', xytext=xytext, textcoords='offset points',
                                color=ec, size=10, va="center", backgroundcolor="#FFFFFF",
                                bbox=dict(boxstyle="round", facecolor="#FFFFFF", ec=ec),
                                arrowprops=dict(arrowstyle="wedge,tail_width=1.", fc="#FFFFFF", ec=ec,
                                                    patchA=None, patchB=self.el, relpos=(0.2, 0.5)))]
    
    def emphasizeOn(self, lids, hover=False):
        dsetts = self.getDrawSettDef()
        if not self.hasDotsReady():
            return

        hgs = {}
        for lid in self.needingHighlight(lids):
            hg = self.drawEntity(lid, self.getColorHigh(), self.getPlotColor(lid, "ec"), self.getPlotProp(lid, "sz"), self.getPlotProp(lid, "zord"), dsetts)
            if lid not in hgs:
                hgs[lid] = []
            hgs[lid].extend(hg)
            
        for lid in self.needingHighLbl(lids):
            tag = self.getParentData().getRName(lid)
            hg = self.drawAnnotation(self.getCoordsXYA(lid), self.getPlotColor(lid, "ec"), tag, self.getAnnXY())
            if lid not in hgs:
                hgs[lid] = []
            hgs[lid].extend(hg)

        self.addHighlighted(hgs, hover)

            
    def inCapture(self, event):
        return event.inaxes == self.axe and numpy.abs(numpy.around(event.xdata) - event.xdata) < self.flat_space \
          and event.ydata >= self.missing_yy-.1 and event.ydata <= 1

    def on_motion(self, event):
        if self.hoverActive() and self.inCapture(event):
            lid = self.getLidAt(event.xdata, event.ydata)
            if lid is None:
                self.emphasizeOnOff(turn_off=None, hover=True, review=True)
            elif not self.isHovered(lid):
                self.emphasizeOnOff(turn_on=[lid], turn_off=None, hover=True, review=True)
                
    def on_click(self, event):
        if self.clickActive() and self.inCapture(event):
            lid = self.getLidAt(event.xdata, event.ydata)
            if lid is not None:
                self.sendEmphasize([lid])


    def OnStamp(self, event=None):
        if self.redStamp is not None:
            self.delStamp()
        else:
            self.addStamp()
            
    def delStamp(self):
        if self.redStamp is not None:
            # pos1 = self.axe.get_position()
            # print "PosC", pos1
            self.axe.set_position(self.redStamp["old_pos"])
            # pos1 = self.axe.get_position()
            # print "PosD", pos1

            self.redStamp["text"].remove()
            self.redStamp = None
            self.MapcanvasMap.draw()
            
    def addStamp(self, pref=""):
        if self.redStamp is None:
            old_pos = self.axe.get_position()
            # print "PosA", old_pos
            new_pos = [old_pos.x0, old_pos.y0,  old_pos.width, 7./8*old_pos.height]
            # # pos2 = [0., 0.,  1., 1.0]
            self.axe.set_position(new_pos)
            # pos1 = self.axe.get_position()
            # print "PosB", pos1

        qrs = self.getQueries()

        red = Redescription.fromQueriesPair(qrs, self.getParentData())
        tex_fields = ["U_query_LHS_named", "U_query_RHS_named", "Tex_acc", "Tex_card_gamma", "Tex_pval"]
        headers = ["qL", "qR", "J", "|E11|", "pV"]
        # rr = "(%s)   " % self.getItemId()
        rr = pref
        tex_str = red.disp(self.getParentData().getNames(), list_fields=tex_fields, sep=" ", headers=headers, delim="", nblines=3, styleX="T") #, rid=rr)
        if self.redStamp is None:
            self.redStamp = {"old_pos": old_pos}
            self.redStamp["text"] = self.MapfigMap.text(0.5, 1-1./(8*2), tex_str, ha="center", va="center")
        else:
            self.redStamp["text"].set_text(tex_str)
        self.MapcanvasMap.draw()

