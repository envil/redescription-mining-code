### TODO check which imports are needed 
import wx
import numpy as np
# The recommended way to use wx with mpl is with the WXAgg
# backend. 
import matplotlib
#matplotlib.use('WXAgg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_wxagg import \
    FigureCanvasWxAgg as FigCanvas, \
    NavigationToolbar2WxAgg as NavigationToolbar
from matplotlib.lines import Line2D
from matplotlib.patches import Polygon
from matplotlib.path import Path

from reremi.classQuery import Query
from reremi.classSParts import SParts
from reremi.classRedescription import Redescription
import factView

import pdb

class CustToolbar(NavigationToolbar):
    def __init__(self, plotCanvas, parent):
        NavigationToolbar.__init__(self, plotCanvas)
        self.parent = parent

    def mouse_move(self, event=None):
        if event is not None:
            NavigationToolbar.mouse_move(self, event)
        if self.parent.q_active_poly():
            self.set_cursor(2)
        elif self.parent.q_active_info():
            self.set_cursor(0)
        else:
            self.set_cursor(1)

class GView(object):

    label_jacc="J ="
    label_pval="p-value ="
    label_cardAlpha=u"|E\u2081\u2080| ="
    label_cardBeta=u"|E\u2080\u2081| ="
    label_cardU=u"|E\u2216E\u2080\u2080| ="
    label_cardI=u"|E\u2081\u2081| ="
    label_cardO=u"|E\u2080\u2080| ="
    label_cardT=u"|E| ="

    colors_def = [("color_l", (255,0,0)), ("color_r", (0,0,255)), ("color_i", (160,32,240))]
    DOT_ALPHA = 0.6
        
    COLHIGH='#FFFF00'

    DOT_SHAPE = 's'
    DOT_SIZE = 3

    map_select_supp = [("l", u"E\u2081\u2080", [SParts.alpha]), ("r", u"E\u2080\u2081", [SParts.beta]),
                       ("i", u"E\u2081\u2081", [SParts.gamma]), ("o", u"E\u2080\u2080", [SParts.delta])]

    TID = "G"
    SDESC = "Viz"
    ordN = 0
    title_str = "View"
    geo = False
    typesI = ["Var", "Reds", "Row"]
    fwidth = 600

    @classmethod
    def getViewsDetails(tcl):
        return {tcl.TID: {"title": tcl.title_str, "class": tcl, "more": None, "ord": tcl.ordN}}

    def __init__(self, parent, vid, more=None):
        self.active_info = False
        self.parent = parent
        self.queries = [Query(), Query()]
        self.source_list = None
        self.mc = None
        self.sld_sel = None
        self.vid = vid
        self.circle = None
        self.buttons = []
        self.act_butt = [1]
        self.highl = {}
        self.hight = {}
        self.mapFrame = wx.Frame(None, -1, "%s%s" % (self.parent.titlePref, self.getTitleDesc()))
        self.mapFrame.SetMinSize((self.fwidth,-1))
        self.panel = wx.Panel(self.mapFrame, -1)
        self.drawMap()
        self.drawFrame()
        self.binds()
        self.prepareActions()
        self.setKeys()
        self.prepareProcesses()
        self.makeMenu()
        self.mapFrame.Show()
        self.suppABCD = None

    def getActionsDetails(self):
        details = []
        for action, dtl in self.actions_map.items():
            details.append({"label": "%s[%s]" % (dtl["label"].ljust(30), dtl["key"]),
                            "legend": dtl["legend"], "active": dtl["active_q"](),
                            "key": dtl["key"], "order": dtl["order"], "type": dtl["type"]})
        if self.mc is not None:
            details.extend(self.mc.getActionsDetails(6))
        return details

    def q_expand(self, more):
        if more is None:
            return True
        res = True
        if "side" in more:
            res &= len(self.queries[1-more["side"]]) > 0
        if "in_weight" in more or "out_weight" in more:
            res &= self.q_has_selected()
        return res
            
    def q_has_poly(self):
        return self.mc is not None and self.mc.q_has_poly()

    def q_active_poly(self):
        return self.mc is not None and self.mc.isActive()

    def q_active_info(self):
        return self.active_info

    def q_has_selected(self):
        return len(self.getSelected()) > 0

    def getSelected(self):
        return self.highl.keys()


    def q_true(self):
        return True

    def getWeightCover(self, params):
        params["area"] = self.getSelected()
        return params

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
        self.actions_map = {"deselect_all": {"method": self.do_deselect_all, "label": "&Deselect all",
                                             "legend": "Deselect all dots", "more": None, "type": "main",
                                             "order":1, "active_q":self.q_has_selected},
                            "flip_able": {"method": self.do_flip_emphasized, "label": "(Dis)able selected",
                                             "legend": "(Dis)able selected dots", "more": None, "type": "main",
                                             "order":0, "active_q":self.q_has_selected},
                            "noggle_info": {"method": self.do_toggle_info, "label": "Toggle i&nfo",
                                               "legend": "Toggle info", "more": None,  "type": "check",
                                               "order":101, "active_q":self.q_active_info}
                            }

        for setk, setl, setp in self.map_select_supp:
            self.actions_map[setk+"_set"] = {"method": self.do_set_select, "label": "(De)select "+setl,
                                             "legend": "(De)select dots in "+setl, "more": setp, "type": "main",
                                             "order":2, "active_q":self.q_true}

        if self.mc is not None:
            self.actions_map["poly_set"] = {"method": self.do_select_poly, "label": "(De)select &polygon",
                                               "legend": "Select dots inside the polygon", "more": None,  "type": "main",
                                               "order":3, "active_q":self.q_has_poly}
            self.actions_map["toggle_draw"] = {"method": self.do_toggle_poly, "label": "&Toggle polygon",
                                               "legend": "Toggle polygon drawing", "more": None,  "type": "check",
                                               "order":100, "active_q":self.q_active_poly}


    def setKeys(self, keys=None):
        self.keys_map = {}
        if keys is None:
            for action, details in self.actions_map.items():
                details["key"] = action[0]
                self.keys_map[details["key"]] = action
        else:
            for action, details in self.actions_map.items():
                details["key"] = None
            for key, action in keys.items():
                if action in self.actions_map:
                    self.actions_map[action]["key"] = key
                    self.keys_map[key] = action

    def getRedId(self):
        if self.source_list is not None:
            return self.parent.tabs[self.source_list]["tab"].getRedIdOID(self.getId())
        return "?"

    def getShortDesc(self):
        return "%s %s" % (self.getRedId(), self.SDESC)

    def getTitleDesc(self):
        return "%s %s" % (self.getRedId(), self.title_str)

    def updateTitle(self):
        self.mapFrame.SetTitle("%s%s" % (self.parent.titlePref, self.getTitleDesc()))

    def getId(self):
        return (self.TID, self.vid)

    def getVId(self):
        return self.vid

    def toTop(self):
        self.mapFrame.Raise()
        try:
            self.MapfigMap.canvas.SetFocus()
        except AttributeError:
            self.mapFrame.SetFocus()

    def makeMenu(self, frame=None):
        if frame is None:
            frame = self.mapFrame
        self.menu_map_act = {}
        self.ids_viewT = {}
        self.menu_map_pro = {}
        menuBar = wx.MenuBar()
        menuBar.Append(self.parent.makeFileMenu(frame), "&File")
        menuBar.Append(self.makeActionsMenu(frame), "&Edit")
        menuBar.Append(self.makeVizMenu(frame), "&View")
        menuBar.Append(self.makeProcessMenu(frame), "&Process")
        menuBar.Append(self.parent.makeViewsMenu(frame), "&Windows")
        menuBar.Append(self.parent.makeHelpMenu(frame), "&Help")
        frame.SetMenuBar(menuBar)
        frame.Layout()

    def makeVizMenu(self, frame, menuViz=None):
        if menuViz is None:
            menuViz = wx.Menu()
        for item in factView.ViewFactory.getViewsInfo(self.parent.dw.isGeospatial()):
            if item["viewT"] != self.getId()[0]:
                ID_NEWV = wx.NewId()
                m_newv = menuViz.Append(ID_NEWV, "%s" % item["title"],
                                         "Plot %s in new window." % item["title"])
                frame.Bind(wx.EVT_MENU, self.OnOtherV, m_newv)
                self.ids_viewT[ID_NEWV] = item["viewT"]
        return menuViz

    def makeActionsMenu(self, frame, menuAct=None):
        if menuAct is None:
            menuAct = wx.Menu()
        for action in sorted(self.getActionsDetails(), key=lambda x:(x["order"],x["key"])):
            ID_ACT = wx.NewId()
            if action["type"] == "check":
                m_act = menuAct.AppendCheckItem(ID_ACT, action["label"], action["legend"])
                frame.Bind(wx.EVT_MENU, self.OnMenuAction, m_act)
                self.menu_map_act[ID_ACT] = action["key"]
                if action["active"]:
                    m_act.Check()
            else:
                m_act = menuAct.Append(ID_ACT, action["label"], action["legend"])
                if action["active"]:
                    if action["type"] == "mc":
                        frame.Bind(wx.EVT_MENU, self.OnMenuMCAction, m_act)
                    else:
                        frame.Bind(wx.EVT_MENU, self.OnMenuAction, m_act)
                    self.menu_map_act[ID_ACT] = action["key"]
                else:
                    menuAct.Enable(ID_ACT, False)
        return menuAct

    def makeProcessMenu(self, frame, menuPro=None):
        if menuPro is None:
            menuPro = wx.Menu()
        for process, details in sorted(self.processes_map.items(), key=lambda x: (x[1]["order"], x[1]["label"])):
            ID_PRO = wx.NewId()
            m_pro = menuPro.Append(ID_PRO, details["label"], details["legend"])
            if self.q_expand(details["more"]):
                frame.Bind(wx.EVT_MENU, self.OnExpandAdv, m_pro)
                self.menu_map_pro[ID_PRO] = process
            else:
                menuPro.Enable(ID_PRO, False)
        ct = menuPro.GetMenuItemCount()
        menuPro = self.parent.makeStoppersMenu(frame, menuPro)
        if ct < menuPro.GetMenuItemCount():
            menuPro.InsertSeparator(ct)
        return menuPro

    def do_toggle_info(self, event):
        self.active_info = not self.active_info

    def do_toggle_poly(self, event):
        self.togglePoly()

    def togglePoly(self):
        if self.mc is not None:
             if self.mc.isActive():
                 self.mc.setButtons([])
                 self.act_butt = [1]
             else:
                 self.mc.setButtons([1])
                 self.act_butt = []
             self.makeMenu()
             self.MaptoolbarMap.mouse_move()
        
    def OnMenuAction(self, event):
        if event.GetId() in self.menu_map_act:
            self.doActionForKey(self.menu_map_act[event.GetId()])

    def OnMenuMCAction(self, event):
        if self.mc is not None and event.GetId() in self.menu_map_act:
            self.mc.doActionForKey(self.menu_map_act[event.GetId()])

    def OnOtherV(self, event):
        self.parent.tabs[self.source_list]["tab"].viewData(self.ids_viewT[event.GetId()], oid=self.getId())
        
    def drawFrame(self):
        self.QIds = [wx.NewId(), wx.NewId()]
        self.MapredMapQ = [wx.TextCtrl(self.mapFrame, self.QIds[0], style=wx.TE_PROCESS_ENTER),
                           wx.TextCtrl(self.mapFrame, self.QIds[1], style=wx.TE_PROCESS_ENTER)]
        colors = self.getColors()
        self.MapredMapQ[0].SetForegroundColour(colors[0])
        self.MapredMapQ[1].SetForegroundColour(colors[1])
        styRL = wx.ALIGN_RIGHT|wx.ALL
        styFL = wx.ALIGN_LEFT|wx.ALL
        self.MapredMapInfoJL = wx.StaticText(self.mapFrame,  style=styRL)
        self.MapredMapInfoVL = wx.StaticText(self.mapFrame,  style=styRL)
        self.MapredMapInfoJV = wx.StaticText(self.mapFrame,  style=styFL)
        self.MapredMapInfoVV = wx.StaticText(self.mapFrame,  style=styFL)
        self.MapredMapInfoIL = wx.StaticText(self.mapFrame,  style=styRL)
        self.MapredMapInfoUL = wx.StaticText(self.mapFrame,  style=styRL)
        self.MapredMapInfoIV = wx.StaticText(self.mapFrame,  style=styFL)
        self.MapredMapInfoUV = wx.StaticText(self.mapFrame,  style=styFL)
        self.MapredMapInfoRL = wx.StaticText(self.mapFrame,  style=styRL)
        self.MapredMapInfoBL = wx.StaticText(self.mapFrame,  style=styRL)
        self.MapredMapInfoRV = wx.StaticText(self.mapFrame,  style=styFL)
        self.MapredMapInfoBV = wx.StaticText(self.mapFrame,  style=styFL)
        self.MapredMapInfoOL = wx.StaticText(self.mapFrame,  style=styRL)
        self.MapredMapInfoTL = wx.StaticText(self.mapFrame,  style=styRL)
        self.MapredMapInfoOV = wx.StaticText(self.mapFrame,  style=styFL)
        self.MapredMapInfoTV = wx.StaticText(self.mapFrame,  style=styFL)

        colors = self.getColors()
        self.MapredMapInfoBV.SetForegroundColour(colors[0])
        self.MapredMapInfoRV.SetForegroundColour(colors[1])
        self.MapredMapInfoIV.SetForegroundColour(colors[2])
        
        flagsL = wx.LEFT | wx.ALIGN_RIGHT | wx.EXPAND
        flagsV = wx.RIGHT |wx.ALIGN_LEFT | wx.EXPAND
        # statsBox = wx.GridSizer(rows=3, cols=8, hgap=5, vgap=5)

        suppBox = wx.GridSizer(rows=2, cols=8, hgap=1, vgap=1)

        suppBox.Add(self.MapredMapInfoJL, 0, border=5, flag=flagsL)
        suppBox.Add(self.MapredMapInfoJV, 0, border=5, flag=flagsV)
        suppBox.Add(self.MapredMapInfoBL, 0, border=5, flag=flagsL)
        suppBox.Add(self.MapredMapInfoBV, 0, border=5, flag=flagsV)
        suppBox.Add(self.MapredMapInfoIL, 0, border=5, flag=flagsL)
        suppBox.Add(self.MapredMapInfoIV, 0, border=5, flag=flagsV)
        suppBox.Add(self.MapredMapInfoRL, 0, border=5, flag=flagsL)
        suppBox.Add(self.MapredMapInfoRV, 0, border=5, flag=flagsV) 

        suppBox.Add(self.MapredMapInfoVL, 0, border=5, flag=flagsL)
        suppBox.Add(self.MapredMapInfoVV, 0, border=5, flag=flagsV)
        suppBox.Add(self.MapredMapInfoUL, 0, border=5, flag=flagsL)
        suppBox.Add(self.MapredMapInfoUV, 0, border=5, flag=flagsV)
        suppBox.Add(self.MapredMapInfoOL, 0, border=5, flag=flagsL)
        suppBox.Add(self.MapredMapInfoOV, 0, border=5, flag=flagsV)
        suppBox.Add(self.MapredMapInfoTL, 0, border=5, flag=flagsL)
        suppBox.Add(self.MapredMapInfoTV, 0, border=5, flag=flagsV)


        allinfosBox = wx.BoxSizer(wx.VERTICAL)
        flags = wx.ALIGN_CENTER | wx.ALL | wx.ALIGN_CENTER_VERTICAL  | wx.EXPAND
        ## if self.parent.dw.getCoords() is not None:
        allinfosBox.Add(self.MapcanvasMap, 0, wx.ALL| wx.ALIGN_CENTER | wx.TOP | wx.EXPAND)
        
        allinfosBox.Add(self.MapredMapQ[0], 0, border=0, flag=flags)
        allinfosBox.Add(self.MapredMapQ[1], 0, border=0, flag=flags)
        # allinfosBox.Add(statsBox, 0, border=1, flag=flags)
        allinfosBox.Add(suppBox, 0, border=15, flag=flags)

        flags = wx.ALIGN_CENTER | wx.ALL | wx.ALIGN_CENTER_VERTICAL
        for add_box in self.additionalElements():
            allinfosBox.Add(add_box, 0, border=1, flag=flags)

        self.mapFrame.SetSizer(allinfosBox)
        allinfosBox.Fit(self.mapFrame)

    def additionalElements(self):
        return []

    def additionalBinds(self):
        for button in self.buttons:
            button["element"].Bind(wx.EVT_BUTTON, button["function"])

    def binds(self):
        # self.mapFrame.Bind(wx.EVT_KEY_UP, self.mkey_press_callback)
        self.mapFrame.Bind(wx.EVT_CLOSE, self.OnQuit)
        self.MapredMapQ[0].Bind(wx.EVT_TEXT_ENTER, self.OnEditQuery)
        self.MapredMapQ[1].Bind(wx.EVT_TEXT_ENTER, self.OnEditQuery)
        self.additionalBinds()

    def getCopyRed(self):
        return Redescription.fromQueriesPair([self.queries[0].copy(), self.queries[1].copy()], self.parent.dw.data)
        
    def OnExpandAdv(self, event):
        params = {"red": self.getCopyRed()}
        if event.GetId() in self.menu_map_pro:
            more = self.processes_map[self.menu_map_pro[event.GetId()]]["more"]
            if more is not None:
                params.update(more)
            for k in self.processes_map[self.menu_map_pro[event.GetId()]]["more_dyn"]:
                params = k(params)
        self.parent.expandFV(params)

    def OnExpandSimp(self, event):
        params = {"red": self.getCopyRed()}
        self.parent.expandFV(params)
        
    def OnQuit(self, event=None, upMenu=True):
        self.parent.deleteView(self.getId())
        if self.source_list is not None and self.source_list in self.parent.tabs:
            self.parent.tabs[self.source_list]["tab"].unregisterView(self.getId(), upMenu)

    def OnEditQuery(self, event):
        if event.GetId() in self.QIds:
            side = self.QIds.index(event.GetId())
            self.updateQuery(side)

    def refresh(self):
        red = Redescription.fromQueriesPair(self.queries, self.parent.dw.data)
        red.setRestrictedSupp(self.parent.dw.data)
        self.suppABCD = red.supports().getVectorABCD()
        self.updateText(red)
        self.updateMap()

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
            red = Redescription.fromQueriesPair(self.queries, self.parent.dw.data)
            red.setRestrictedSupp(self.parent.dw.data)
            self.suppABCD = red.supports().getVectorABCD()
            self.updateText(red)
            self.makeMenu()
            self.updateOriginal(red)
            self.updateHist(red)
            self.updateMap()
        else: ### wrongly formatted query or not edits, revert
            for side in [0,1]:
                self.updateQueryText(self.queries[side], side)
            red = Redescription.fromQueriesPair(self.queries, self.parent.dw.data)
        return red

    def setSource(self, source_list=None):
        self.source_list=source_list

    def setCurrent(self, qr=None, source_list=None):
        if qr is not None:
            if type(qr) in [list, tuple]:
                queries = qr
                red = Redescription.fromQueriesPair(qr, self.parent.dw.data)
            else:
                red = qr
                queries = [red.query(0), red.query(1)]
            self.queries = queries
            red.setRestrictedSupp(self.parent.dw.data)
            self.suppABCD = red.supports().getVectorABCD()
            self.setSource(source_list)
            self.updateText(red)
            self.updateMap()
            self.makeMenu()
            self.updateHist(red)
            return red

    def parseQuery(self, side):
        stringQ = self.MapredMapQ[side].GetValue().strip()
        try:
            query = Query.parse(stringQ, self.parent.dw.data.getNames(side))
        except:
            query = None
        if query is not None and (len(stringQ) > 0 and len(query) == 0):
            query = None
        return query                    
        
    def drawMap(self):
        """ Draws the map
        """
        pass
            
    def updateMap(self):
        """ Redraws the map
        """
        pass


    def updateHist(self, red = None):
        if red is not None:
            if self.source_list != "hist":
                self.parent.tabs["hist"]["tab"].insertItem(red, -1)

    def updateOriginal(self, red = None):
        if red is not None and self.source_list is not None and self.source_list in self.parent.tabs:
            self.parent.tabs[self.source_list]["tab"].updateEdit(self.getId(), red)

    def updateQueryText(self, query, side):
        self.MapredMapQ[side].ChangeValue(query.dispU(self.parent.dw.data.getNames(side)))

    def updateText(self, red = None):
        """ Reset red fields and info
        """
        if red is not None:
            for side in [0, 1]:
                self.updateQueryText(red.queries[side], side)
            self.setMapredInfo(red)

    def setMapredInfo(self, red = None, details=None):
        if red is None:
            self.MapredMapInfoJL.SetLabel("")
            self.MapredMapInfoJV.SetLabel("")
            self.MapredMapInfoVL.SetLabel("")
            self.MapredMapInfoVV.SetLabel("")
            self.MapredMapInfoIL.SetLabel("")
            self.MapredMapInfoIV.SetLabel("")
            self.MapredMapInfoUL.SetLabel("")
            self.MapredMapInfoUV.SetLabel("")
            self.MapredMapInfoBL.SetLabel("")
            self.MapredMapInfoBV.SetLabel("")
            self.MapredMapInfoRL.SetLabel("")
            self.MapredMapInfoRV.SetLabel("")
            self.MapredMapInfoOL.SetLabel("")
            self.MapredMapInfoOV.SetLabel("")
            self.MapredMapInfoTL.SetLabel("")
            self.MapredMapInfoTV.SetLabel("")

        else:
            self.MapredMapInfoJL.SetLabel(self.label_jacc)
            self.MapredMapInfoJV.SetLabel("%1.3f" % red.getRoundAcc())
            self.MapredMapInfoVL.SetLabel(self.label_pval)
            self.MapredMapInfoVV.SetLabel("%1.3f" % red.getRoundPVal())
            self.MapredMapInfoIL.SetLabel(self.label_cardI)
            self.MapredMapInfoIV.SetLabel("%i" % red.getLenI())
            self.MapredMapInfoUL.SetLabel(self.label_cardU)
            self.MapredMapInfoUV.SetLabel("%i" % red.getLenU())
            self.MapredMapInfoBL.SetLabel(self.label_cardAlpha)
            self.MapredMapInfoBV.SetLabel("%i" % red.getLenA())
            self.MapredMapInfoRL.SetLabel(self.label_cardBeta)
            self.MapredMapInfoRV.SetLabel("%i" % red.getLenB())

            self.MapredMapInfoOL.SetLabel(self.label_cardO)
            self.MapredMapInfoOV.SetLabel("%i" % red.getLenO())
            self.MapredMapInfoTL.SetLabel(self.label_cardT)
            self.MapredMapInfoTV.SetLabel("%i" % red.getLenT())

    def updateEmphasize(self, colhigh='#FFFF00', review=True):
        if self.source_list is not None:
            lids = self.parent.tabs[self.source_list]["tab"].getEmphasizedR(self.getId())
            self.emphasizeOnOff(turn_on=lids, turn_off=None, colhigh=colhigh, review=review)

    def emphasizeOnOff(self, turn_on=set(), turn_off=set(), colhigh='#FFFF00', review=True):
        self.emphasizeOff(turn_off)
        self.emphasizeOn(turn_on, colhigh)
        self.makeMenu()
        if review:
            self.MapcanvasMap.draw()

    def emphasizeOn(self, lids,  colhigh='#FFFF00'):
        draw_settings = self.getDrawSettings()
        for lid in lids:
            if lid in self.highl:
                continue
            pi = self.suppABCD[lid]
            self.highl[lid] = []
            self.highl[lid].extend(self.axe.plot(self.getCoords(0,lid), self.getCoords(1,lid),
                                          mfc=colhigh, mec=draw_settings[pi]["color_e"],
                                          marker=draw_settings["shape"], markersize=draw_settings[pi]["size"],
                                          markeredgewidth=1, linestyle='None'))

            if len(lids) == 1:
                tag = self.parent.dw.data.getRName(lid)
                self.hight[lid] = []
                self.hight[lid].append(self.axe.annotate(tag, xy=(self.getCoords(0,lid), self.getCoords(1,lid)),  xycoords='data',
                                                     xytext=(-10, 15), textcoords='offset points', color= draw_settings[pi]["color_e"],
                                                     size=10, va="center", backgroundcolor="#FFFFFF",
                                                     bbox=dict(boxstyle="round", facecolor="#FFFFFF", ec=draw_settings[pi]["color_e"]),
                                                     arrowprops=dict(arrowstyle="wedge,tail_width=1.", fc="#FFFFFF", ec=draw_settings[pi]["color_e"],
                                                                     patchA=None, patchB=self.el, relpos=(0.2, 0.5))
                                                     ))
            
    def emphasizeOff(self, lids = None):
        if lids is None:
            lids = self.highl.keys()
        for lid in lids:
            if lid in self.hight:
                while len(self.hight[lid]) > 0:
                    t = self.hight[lid].pop()
                    if t in self.axe.texts:
                        self.axe.texts.remove(t)
                del self.hight[lid]

            if lid in self.highl:
                while len(self.highl[lid]) > 0:
                    t = self.highl[lid].pop()
                    if isinstance(t, Line2D) and t in self.axe.lines:
                        self.axe.lines.remove(t)
                    elif isinstance(t, Polygon) and t in self.axe.patches:
                        self.axe.patches.remove(t)
                del self.highl[lid]

    def sendEmphasize(self, lids):
        if self.source_list is not None and self.source_list in self.parent.tabs:
            self.parent.tabs[self.source_list]["tab"].setEmphasizedR(self.getId(), lids, show_info=self.q_active_info())

    def sendFlipEmphasizedR(self):
        if self.source_list is not None and self.source_list in self.parent.tabs:
            self.parent.tabs[self.source_list]["tab"].doFlipEmphasizedR(self.getId())

    def OnPick(self, event):
        if event.mouseevent.button in self.act_butt and (isinstance(event.artist, Line2D) or isinstance(event.artist, Polygon)): 
            self.sendEmphasize([int(event.artist.get_gid().split(".")[0])])

    def doActionForKey(self, key):
        if self.keys_map.get(key, None in self.actions_map):
            act = self.actions_map[self.keys_map[key]]
            if act["type"] == "check" or act["active_q"]():
                self.actions_map[self.keys_map[key]]["method"](self.actions_map[self.keys_map[key]]["more"])
                return True
        return False

    def key_press_callback(self, event):
        self.doActionForKey(event.key)

    def mkey_press_callback(self, event):
        self.doActionForKey(chr(event.GetKeyCode()).lower())

    def do_select_poly(self, more=None):
        points = self.apply_mask(self.mc.get_path())
        self.mc.clear()
        if points != set():
            self.sendEmphasize(points)

    def do_flip_emphasized(self, more=None):
        self.sendFlipEmphasizedR()

    def do_deselect_all(self, more=None):
        points = None
        self.sendEmphasize(points)

    def do_set_select(self, setp):
        points = [i for (i,p) in enumerate(self.suppABCD) if p in setp]
        self.sendEmphasize(points)
            
    def apply_mask(self, path, radius=0.0):
        if path is not None and self.getCoords() is not None:
            points = np.transpose((self.getCoords(0), self.getCoords(1)))
            return [i for i,point in enumerate(points) if path.contains_point(point, radius=radius)]
        return []

    def getCoords(axi=None, ids=None):
        return None

    def getColors(self):
        t = self.parent.dw.getPreferences()
        colors = []
        for color_k, color in GView.colors_def:
            try:
                color_t = t[color_k]["data"]
            except:
                color_t = color
            colors.append(color_t)
        return colors

    def getDot(self):
        t = self.parent.dw.getPreferences()
        try:
            dot_shape = t["dot_shape"]["data"]
            dot_size = t["dot_size"]["data"]
        except:
            dot_shape = GView.DOT_SHAPE
            dot_size = GView.DOT_SIZE
        return (dot_shape, dot_size)

    def getMissDetails(self):
        t = self.parent.dw.getPreferences()
        if t["miss_details"]["data"] == "Yes":
            return True
        return False

    def getDrawSettings(self):
        colors = self.getColors()
        dot_shape, dot_size = self.getDot()
        return {"draw_pord": dict([(v,p) for (p,v) in enumerate([SParts.mud, SParts.mua, SParts.mub, SParts.muaB, SParts.mubB,
                              SParts.delta, SParts.beta, SParts.alpha, SParts.gamma])]),
                "shape": dot_shape,
                SParts.alpha: {"color_e": [i/255.0 for i in colors[0]],
                               "color_f": [i/255.0 for i in colors[0]],
                               "shape": dot_shape,
                               "alpha": GView.DOT_ALPHA, "size": dot_size},
                SParts.beta: {"color_e": [i/255.0 for i in colors[1]],
                              "color_f": [i/255.0 for i in colors[1]],
                              "shape": dot_shape,
                               "alpha": GView.DOT_ALPHA, "size": dot_size},
                SParts.gamma: {"color_e": [i/255.0 for i in colors[2]],
                               "color_f": [i/255.0 for i in colors[2]],
                               "shape": dot_shape,
                               "alpha": GView.DOT_ALPHA, "size": dot_size},
                SParts.mua: {"color_e": [i/255.0 for i in colors[0]],
                             "color_f": [0.5,0.5,0.5],
                             "shape": dot_shape,
                             "alpha": GView.DOT_ALPHA, "size": dot_size-1},
                SParts.mub: {"color_e": [i/255.0 for i in colors[1]],
                             "color_f": [0.5,0.5,0.5],
                             "shape": dot_shape,
                             "alpha": GView.DOT_ALPHA, "size": dot_size-1},
                SParts.muaB: {"color_e": [0.5,0.5,0.5],
                              "color_f": [i/255.0 for i in colors[1]],
                             "shape": dot_shape,
                              "alpha": GView.DOT_ALPHA, "size": dot_size-1},
                SParts.mubB: {"color_e": [0.5,0.5,0.5],
                              "color_f": [i/255.0 for i in colors[0]],
                             "shape": dot_shape,
                              "alpha": GView.DOT_ALPHA, "size": dot_size-1},
                SParts.mud: {"color_e": [0.5,0.5,0.5],
                             "color_f": [0.5, 0.5, 0.5],
                             "shape": dot_shape,
                             "alpha": GView.DOT_ALPHA, "size": dot_size-1},
                SParts.delta: {"color_e": [0.5,0.5,0.5],
                               "color_f": [0.5, 0.5, 0.5],
                               "shape": dot_shape,
                               "alpha": GView.DOT_ALPHA, "size": dot_size}
                }
        
def HTMLColorToRGB(colorstring):
    """ convert #RRGGBB to an (R, G, B) tuple """
    colorstring = colorstring.strip()
    if colorstring[0] == '#': colorstring = colorstring[1:]
    if len(colorstring) != 6:
        raise ValueError, "input #%s is not in #RRGGBB format" % colorstring
    r, g, b = colorstring[:2], colorstring[2:4], colorstring[4:]
    r, g, b = [int(n, 16) for n in (r, g, b)]
    return (r, g, b)
