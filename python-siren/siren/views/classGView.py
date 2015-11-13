### TODO check which imports are needed 
import wx
import numpy
# The recommended way to use wx with mpl is with the WXAgg
# backend. 
import matplotlib
#matplotlib.use('WXAgg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_wxagg import \
    FigureCanvasWxAgg as FigCanvas, \
    NavigationToolbar2WxAgg as NavigationToolbar
from matplotlib.figure import Figure
from matplotlib.lines import Line2D
from matplotlib.patches import Polygon
from matplotlib.path import Path

from ..reremi.classQuery import SYM, Query
from ..reremi.classSParts import SSetts
from ..reremi.classRedescription import Redescription

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
    label_cardAlpha="|E"+SYM.SYM_ALPHA+"| ="
    label_cardBeta="|E"+SYM.SYM_BETA+"| ="
    label_cardU="|E"+SYM.SYM_SETMIN+"E"+SYM.SYM_DELTA+"| ="
    label_cardI="|E"+SYM.SYM_GAMMA+"| ="
    label_cardO="|E"+SYM.SYM_DELTA+"| ="
    label_cardT="|E| ="

    label_learn = SYM.SYM_LEARN+":"
    label_test = SYM.SYM_TEST+":"
    label_ratio = SYM.SYM_RATIO+":"

    colors_def = [("color_l", (255,0,0)), ("color_r", (0,0,255)), ("color_i", (160,32,240))]
    DOT_ALPHA = 0.6
        
    COLHIGH='#FFFF00'

    DOT_SHAPE = 's'
    DOT_SIZE = 3

    map_select_supp = [("l", "|E"+SYM.SYM_ALPHA+"|", [SSetts.alpha]), ("r", "|E"+SYM.SYM_BETA+"|", [SSetts.beta]),
                       ("i", "|E"+SYM.SYM_GAMMA+"|", [SSetts.gamma]), ("o", "|E"+SYM.SYM_DELTA+"|", [SSetts.delta])]

    infos_details = [{"id": "jacc", "label": label_jacc, "meth": "getRoundAcc", "format": "%1.3f"},
                     {"id": "lenI", "label": label_cardI, "meth": "getLenI", "format": "%i", "color":2},
                     {"id": "lenA", "label": label_cardAlpha, "meth": "getLenA", "format": "%i", "color":0},
                     {"id": "lenT", "label": label_cardT, "meth": "getLenT", "format": "%i"},
                     {"id": "pval", "label": label_pval, "meth": "getRoundPVal", "format": "%1.3f"},
                     {"id": "lenO", "label": label_cardO, "meth": "getLenO", "format": "%i"},
                     {"id": "lenB", "label": label_cardBeta, "meth": "getLenB", "format": "%i", "color":1},
                     {"id": "lenU", "label": label_cardU, "meth": "getLenU", "format": "%i"},]
    
    TID = "G"
    SDESC = "Viz"
    ordN = 0
    title_str = "View"
    geo = False
    typesI = ["Var", "Reds", "Row"]

    max_emphlbl = 5

    nb_cols = 4
    spacer_w = 20
    spacer_h = 10
    nbadd_boxes = 0 
    butt_w = 75
    fwidth = 400
    info_band_height = 205

    def getSpacerW(self):
        return self.spacer_w
    def getSpacerH(self):
        return self.spacer_h
    def getInfoH(self):
        return self.info_band_height+self.nbadd_boxes*22

    @classmethod
    def getViewsDetails(tcl):
        return {tcl.TID: {"title": tcl.title_str, "class": tcl, "more": None, "ord": tcl.ordN}}

    @classmethod
    def suitableView(tcl, geo=False, queries=None, tabT=None):
        return (tabT is None or tabT in tcl.typesI) and (not tcl.geo or geo)

    def __init__(self, parent, vid, more=None):
        self.active_info = False
        self.parent = parent
        self.queries = [Query(), Query()]
        self.source_list = None
        self.mc = None
        self.sld_sel = None
        self.boxL = None
        self.boxT = None
        self.rsets = None
        self.vid = vid
        self.circle = None
        self.buttons = []
        self.act_butt = [1]
        self.highl = {}
        self.hight = {}
        self.current_hover = None
        self.mapFrame = wx.Frame(None, -1, "%s%s" % (self.parent.titlePref, self.getTitleDesc()))
        self.mapFrame.SetMinSize((self.fwidth, 2*self.info_band_height))
        self.panel = wx.Panel(self.mapFrame, -1)
        self.drawFrame()
        self.binds()
        self.prepareActions()
        self.setKeys()
        self.prepareProcesses()
        self.makeMenu()
        self.initSizeRelative()
        self.mapFrame.Show()
        self.suppABCD = None

    def initSizeRelative(self):
        ds = wx.DisplaySize()
        self.mapFrame.SetClientSizeWH(ds[0]/2.5, ds[1]/1.5)
        self._SetSize()


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

    def q_true(self):
        return True

    def hoverActive(self):
        return self.parent.dw.getPreferences()['hover_entities']['data'] == 'yes' 

    def getSelected(self):
        return self.highl.keys()

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
            return self.parent.callOnTab(self.source_list, meth="getRedIdOID", args={"oid": self.getId()})
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

    def getDetailsSplit(self):
        return self.rsets

    def getVizRows(self):
        return self.parent.dw.getData().getVizRows(self.getDetailsSplit())
    def getUnvizRows(self):
        return self.parent.dw.getData().getUnvizRows(self.getDetailsSplit())

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
        for item in self.parent.getViewsItems(queries=self.getQueries(), excludeT=[self.getId()[0]]):
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
        self.parent.callOnTab(self.source_list, meth="viewData",
                              args={"viewT": self.ids_viewT[event.GetId()], "oid": self.getId()})

    def showSplitsBoxes(self, show=True):
        self.boxL.Show(show)
        self.boxT.Show(show)

    def autoShowSplitsBoxes(self):
        if self.parent.dw.getData().hasLT():
            self.showSplitsBoxes(True)
        else:
            self.showSplitsBoxes(False)

        
    def OnSplitsChange(self, event):
        new_rsets = None
        buttons = [self.boxL, self.boxT]
        part = ["learn", "test"]
        if event.GetId() == self.boxL.GetId():
            which = 0
        else:
            which = 1
            
        if buttons[which].GetValue():
            if buttons[1-which].GetValue():
                buttons[1-which].SetValue(False)
            new_rsets = {"rset_id": part[which]}

        else:
            if buttons[1-which].GetValue():
                new_rsets = {"rset_id": part[1-which]}
            else:
                new_rsets =None
        # if self.boxL is not None and self.boxT is not None:
        #     if self.boxL.GetValue() and not self.boxT.GetValue():

        #     elif not self.boxL.GetValue() and self.boxT.GetValue():
        #         new_rsets = {"rset_id": "test"}
        if self.rsets != new_rsets:
            self.rsets = new_rsets
            self.refresh()

        
    def additionalElements(self):
        return []

    def additionalBinds(self):
        for button in self.buttons:
            button["element"].Bind(wx.EVT_BUTTON, button["function"])

    def binds(self):
        self.mapFrame.Bind(wx.EVT_CLOSE, self.OnQuit)
        self.mapFrame.Bind(wx.EVT_SIZE, self._onSize)
        self.MapredMapQ[0].Bind(wx.EVT_TEXT_ENTER, self.OnEditQuery)
        self.MapredMapQ[1].Bind(wx.EVT_TEXT_ENTER, self.OnEditQuery)
        self.additionalBinds()
        self.autoShowSplitsBoxes()
        
    def getQueries(self):
        ### the actual queries, not copies, to test, etc. not for modifications
        return self.queries

    def getCopyRed(self):
        return Redescription.fromQueriesPair([self.queries[0].copy(), self.queries[1].copy()], self.parent.dw.getData())
        
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

    def _onSize(self, event=None):
        self._SetSize()

    def _SetSize( self):
        pixels = tuple(self.mapFrame.GetClientSize() )
        self.panel.SetSize( pixels )
        figsize = (pixels[0], max(pixels[1]-self.getInfoH(), 10))
        # self.MapfigMap.set_size_inches( float( figsize[0] )/(self.MapfigMap.get_dpi()),
        #                                 float( figsize[1] )/(self.MapfigMap.get_dpi() ))
        self.MapcanvasMap.SetMinSize(figsize )
        # #self.fillBox.SetMinSize((figsize[0], figsize[1]))
        curr = self.innerBox1.GetMinSize()
        self.innerBox1.SetMinSize((1*figsize[0], curr[1]))
        self.MapredMapQ[0].SetMinSize((1*figsize[0], -1))
        self.MapredMapQ[1].SetMinSize((1*figsize[0], -1))
        self.masterBox.Layout()
        self.MapfigMap.set_size_inches( float( figsize[0] )/(self.MapfigMap.get_dpi()),
                                        float( figsize[1] )/(self.MapfigMap.get_dpi() ))

        # self.MapfigMap.set_size_inches(1, 1)

        
    def OnQuit(self, event=None, upMenu=True):
        self.parent.deleteView(self.getId())
        self.parent.callOnTab(self.source_list, meth="unregisterView", args={"key": self.getId(), "upMenu": upMenu})

    def OnEditQuery(self, event):
        if event.GetId() in self.QIds:
            side = self.QIds.index(event.GetId())
            self.updateQuery(side)

    def refresh(self):
        self.autoShowSplitsBoxes()
        red = Redescription.fromQueriesPair(self.queries, self.parent.dw.getData())
        red.setRestrictedSupp(self.parent.dw.getData())
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
            red = Redescription.fromQueriesPair(self.queries, self.parent.dw.getData())
            red.setRestrictedSupp(self.parent.dw.getData())
            self.suppABCD = red.supports().getVectorABCD()
            self.updateText(red)
            self.makeMenu()
            self.updateOriginal(red)
            self.updateHist(red)
            self.updateMap()
        else: ### wrongly formatted query or not edits, revert
            for side in [0,1]:
                self.updateQueryText(self.queries[side], side)
            red = Redescription.fromQueriesPair(self.queries, self.parent.dw.getData())
        return red

    def setSource(self, source_list=None):
        self.source_list=source_list

    def setCurrent(self, qr=None, source_list=None):
        if qr is not None:
            if type(qr) in [list, tuple]:
                queries = qr
                red = Redescription.fromQueriesPair(qr, self.parent.dw.getData())
            else:
                red = qr
                queries = [red.query(0), red.query(1)]
            self.queries = queries
            red.setRestrictedSupp(self.parent.dw.getData())
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
            query = Query.parse(stringQ, self.parent.dw.getData().getNames(side))
        except:
            query = None
        if query is not None and (len(stringQ) > 0 and len(query) == 0):
            query = None
        return query                    
        
    def drawMap(self):
        """ Draws the map
        """
        if not hasattr( self, 'subplot' ):
            self.subplot = self.MapfigMap.add_subplot( 111 )

        theta = numpy.arange( 0, 45*2*numpy.pi, 0.02 )

        rad0 = (0.8*theta/(2*numpy.pi) + 1)
        r0 = rad0*(8 + numpy.sin( theta*7 + rad0/1.8 ))
        x0 = r0*numpy.cos( theta )
        y0 = r0*numpy.sin( theta )

        rad1 = (0.8*theta/(2*numpy.pi) + 1)
        r1 = rad1*(6 + numpy.sin( theta*7 + rad1/1.9 ))
        x1 = r1*numpy.cos( theta )
        y1 = r1*numpy.sin( theta )

        self.point_lists = [[(xi,yi) for xi,yi in zip( x0, y0 )],
                            [(xi,yi) for xi,yi in zip( x1, y1 )]]
        self.clr_list = [[225,200,160], [219,112,147]]
            
        for i, pt_list in enumerate( self.point_lists ):
            plot_pts = numpy.array( pt_list )
            clr = [float( c )/255. for c in self.clr_list[i]]
            self.subplot.plot( plot_pts[:,0], plot_pts[:,1], color=clr )
        
        
    def drawFrame(self):
        # initialize matplotlib stuff
        self.MapfigMap = Figure(None)
        self.MapcanvasMap = FigCanvas(self.mapFrame, -1, self.MapfigMap)
        self.MaptoolbarMap = CustToolbar(self.MapcanvasMap, self)
        self.QIds = [wx.NewId(), wx.NewId()]
        self.MapredMapQ = [wx.TextCtrl(self.panel, self.QIds[0], style=wx.TE_PROCESS_ENTER),
                           wx.TextCtrl(self.panel, self.QIds[1], style=wx.TE_PROCESS_ENTER)]
        # self.MapredMapQ = [wx.TextCtrl(self.mapFrame, self.QIds[0]),
        #                    wx.TextCtrl(self.mapFrame, self.QIds[1])]
        colors = self.getColors()
        self.MapredMapQ[0].SetForegroundColour(colors[0])
        self.MapredMapQ[1].SetForegroundColour(colors[1])

        # styL = wx.ALIGN_RIGHT | wx.EXPAND
        # styV = wx.ALIGN_LEFT | wx.EXPAND
        # sizz = (70,-1)
        
        self.info_items = {}
        for info_item in self.infos_details:
            # self.info_items[info_item["id"]] = (wx.StaticText(self.panel, label=info_item["label"], style=styL, size=sizz),
            #                                     wx.StaticText(self.panel, label="--", style=styV, size=sizz))
            self.info_items[info_item["id"]] = (wx.StaticText(self.panel, label=info_item["label"]),
                                                wx.StaticText(self.panel, label="XXX"))


            if info_item.get("color") is not None:
                self.info_items[info_item["id"]][1].SetForegroundColour(colors[info_item.get("color")])

        adds = self.additionalElements()
        self.drawMap()

        self.masterBox =  wx.FlexGridSizer(rows=2, cols=1, vgap=0, hgap=0)
        #self.masterBox = wx.BoxSizer(wx.VERTICAL)

        #self.fillBox = wx.BoxSizer(wx.HORIZONTAL)
        self.innerBox = wx.BoxSizer(wx.HORIZONTAL)
        self.innerBox1 = wx.BoxSizer(wx.VERTICAL)
        self.masterBox.Add(self.MapcanvasMap, 0, border=1,  flag= wx.EXPAND)
        #self.masterBox.Add(self.fillBox, 0, border=1,  flag= wx.EXPAND)

        self.innerBox1.Add(self.MapredMapQ[0], 0, border=1,  flag= wx.ALIGN_CENTER)
        self.innerBox1.Add(self.MapredMapQ[1], 0, border=1,  flag= wx.ALIGN_CENTER)

        self.innerBox1.AddSpacer((-1,self.getSpacerH()))
        
        cols = [wx.BoxSizer(wx.VERTICAL) for i in range(2*self.nb_cols)]
        for pi, elem in enumerate(self.infos_details):
            ci = 2*(pi % self.nb_cols)
            cols[ci].Add(self.info_items[elem["id"]][0], 1, border=1,  flag= wx.ALL|wx.ALIGN_RIGHT)
            cols[ci+1].Add(self.info_items[elem["id"]][1], 1, border=1,  flag= wx.ALL|wx.ALIGN_RIGHT)

        lineB = wx.BoxSizer(wx.HORIZONTAL)
        for ci, col in enumerate(cols):
            lineB.Add(col, 0, border=1,  flag= wx.ALIGN_CENTER|wx.EXPAND)
            if ci % 2 == 1 and ci < len(cols)-1:
                lineB.AddSpacer((self.getSpacerW(),-1))
        self.innerBox1.Add(lineB, 0, border=1,  flag= wx.ALIGN_CENTER)

        self.innerBox1.AddSpacer((-1,self.getSpacerH()))
        for add in adds:
            self.innerBox1.Add(add, 0, border=1,  flag= wx.ALIGN_CENTER)

        self.innerBox.Add(self.innerBox1, 0, border=1,  flag= wx.ALIGN_CENTER)
        self.masterBox.Add(self.innerBox, 0, border=1, flag= wx.EXPAND| wx.ALIGN_CENTER| wx.ALIGN_BOTTOM)
        self.panel.SetSizer(self.masterBox)
        self._SetSize()

            
    def updateMap(self):
        """ Redraws the map
        """
        pass


    def updateHist(self, red = None):
        if red is not None:
            if self.source_list != "hist":
                self.parent.callOnTab("hist", meth="insertItem", args={"item": red, "row": -1})

    def updateOriginal(self, red = None):
        if red is not None:
            self.parent.callOnTab(self.source_list, meth="updateEdit",
                                  args={"edit_key": self.getId(), "red": red})

    def updateQueryText(self, query, side):
        self.MapredMapQ[side].ChangeValue(query.disp(style="U", names=self.parent.dw.getData().getNames(side)))
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
            if red is not None:
                meth = getattr(red,det["meth"], None)
            else:
                meth = None
                
            if meth is not None:
                self.info_items[det["id"]][1].SetLabel(det["format"] % meth(self.getDetailsSplit()))
            else:
                self.info_items[det["id"]][1].SetLabel("XX")

    def updateEmphasize(self, colhigh='#FFFF00', review=True):
        if self.source_list is not None:
            lids = self.parent.callOnTab(self.source_list, meth="getEmphasizedR", args={"edit_key": self.getId()})
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

            if len(lids) <= self.max_emphlbl and not lid in self.hight:
                tag = self.parent.dw.getData().getRName(lid)
                self.hight[lid] = []
                self.hight[lid].append(self.axe.annotate(tag, xy=(self.getCoords(0,lid), self.getCoords(1,lid)),
                                                         xycoords='data', xytext=(-10, 15), textcoords='offset points',
                                                         color= draw_settings[pi]["color_e"], size=10,
                                                         va="center", backgroundcolor="#FFFFFF",
                                                         bbox=dict(boxstyle="round", facecolor="#FFFFFF",
                                                                   ec=draw_settings[pi]["color_e"]),
                                                         arrowprops=dict(arrowstyle="wedge,tail_width=1.",
                                                                         fc="#FFFFFF", ec=draw_settings[pi]["color_e"],
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
        return self.parent.callOnTab(self.source_list, meth="setEmphasizedR",
                                     args={"edit_key": self.getId(), "lids": lids, "show_info":self.q_active_info()})

    def sendFlipEmphasizedR(self):
        return self.parent.callOnTab(self.source_list, meth="doFlipEmphasizedR",
                                     args={"edit_key": self.getId()})

    def OnPick(self, event):
        if event.mouseevent.button in self.act_butt and (isinstance(event.artist, Line2D) or isinstance(event.artist, Polygon)): 
            gid_parts = event.artist.get_gid().split(".")
            if gid_parts[-1] == "1":
                self.sendEmphasize([int(gid_parts[0])])
            else:
                self.sendOtherPick(gid_parts)

    def sendOtherPick(self, gid_parts):
        pass

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
            points = numpy.transpose((self.getCoords(0), self.getCoords(1)))
            return [i for i,point in enumerate(points) if path.contains_point(point, radius=radius)]
        return []

    def getCoords(axi=None, ids=None):
        return None

    def getColors(self):
        t = self.parent.dw.getPreferences()
        colors = []
        for color_k, color in self.colors_def:
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
            dot_shape = self.DOT_SHAPE
            dot_size = self.DOT_SIZE
        return (dot_shape, dot_size)

    def getMissDetails(self):
        t = self.parent.dw.getPreferences()
        if t["miss_details"]["data"] == "Yes":
            return True
        return False

    def getDrawSettings(self):
        colors = self.getColors()
        dot_shape, dot_size = self.getDot()
        draw_pord = dict([(v,p) for (p,v) in enumerate([SSetts.mud, SSetts.mua, SSetts.mub,
                                                        SSetts.muaB, SSetts.mubB,
                                                        SSetts.delta, SSetts.beta,
                                                        SSetts.alpha, SSetts.gamma])])
            
        dd = numpy.nan*numpy.ones(numpy.max(draw_pord.keys())+1)
        for (p,v) in enumerate([SSetts.delta, SSetts.beta, SSetts.alpha, SSetts.gamma]):
            dd[v] = p

        basic_grey = [0.5,0.5,0.5]
        light_grey = [0.66,0.66,0.66]
        return {"draw_pord": draw_pord,
                "draw_ppos": dd,
                "shape": dot_shape,
                SSetts.alpha: {"color_e": [i/255.0 for i in colors[0]],
                               "color_f": [i/255.0 for i in colors[0]],
                               "color_l": [i/255.0 for i in colors[0]],
                               "shape": dot_shape,
                               "alpha": self.DOT_ALPHA, "size": dot_size},
                SSetts.beta: {"color_e": [i/255.0 for i in colors[1]],
                              "color_f": [i/255.0 for i in colors[1]],
                              "color_l": [i/255.0 for i in colors[1]],
                              "shape": dot_shape,
                               "alpha": self.DOT_ALPHA, "size": dot_size},
                SSetts.gamma: {"color_e": [i/255.0 for i in colors[2]],
                               "color_f": [i/255.0 for i in colors[2]],
                               "color_l": [i/255.0 for i in colors[2]],
                               "shape": dot_shape,
                               "alpha": self.DOT_ALPHA, "size": dot_size},
                SSetts.mua: {"color_e": [i/255.0 for i in colors[0]],
                             "color_f": basic_grey,
                             "color_l": light_grey,
                             "shape": dot_shape,
                             "alpha": self.DOT_ALPHA, "size": dot_size-1},
                SSetts.mub: {"color_e": [i/255.0 for i in colors[1]],
                             "color_f": basic_grey,
                             "color_l": light_grey,
                             "shape": dot_shape,
                             "alpha": self.DOT_ALPHA, "size": dot_size-1},
                SSetts.muaB: {"color_e": basic_grey,
                              "color_f": [i/255.0 for i in colors[1]],
                             "color_l": light_grey,
                             "shape": dot_shape,
                              "alpha": self.DOT_ALPHA, "size": dot_size-1},
                SSetts.mubB: {"color_e": basic_grey,
                              "color_f": [i/255.0 for i in colors[0]],
                             "color_l": light_grey,
                             "shape": dot_shape,
                              "alpha": self.DOT_ALPHA, "size": dot_size-1},
                SSetts.mud: {"color_e": basic_grey,
                             "color_f": basic_grey,
                             "color_l": light_grey,
                             "shape": dot_shape,
                             "alpha": self.DOT_ALPHA, "size": dot_size-1},
                SSetts.delta: {"color_e": basic_grey,
                               "color_f": basic_grey,
                               "color_l": basic_grey,
                               "shape": dot_shape,
                               "alpha": self.DOT_ALPHA, "size": dot_size},
                -1: {"color_e": basic_grey,
                             "color_f": basic_grey,
                             "color_l": light_grey,
                             "shape": dot_shape,
                             "alpha": self.DOT_ALPHA, "size": dot_size-1}
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
