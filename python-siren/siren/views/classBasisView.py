import wx
import numpy
# The recommended way to use wx with mpl is with the WXAgg backend. 
# import matplotlib
# matplotlib.use('WXAgg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_wxagg import \
    FigureCanvasWxAgg as FigCanvas, \
    NavigationToolbar2WxAgg as NavigationToolbar
from matplotlib.figure import Figure
from matplotlib.lines import Line2D
from matplotlib.text import Annotation
from matplotlib.patches import Polygon
from matplotlib.path import Path

from ..reremi.classQuery import SYM, Query
from ..reremi.classSParts import SSetts
from ..reremi.classRedescription import Redescription

### updateHist moved to CtrlTable

import pdb

class CustToolbar(NavigationToolbar):
    def __init__(self, plotCanvas, parent):
        self.toolitems = [(None, None, None, None)] #  (('Save', 'Save the figure', 'filesave', 'save_figure'),)
        NavigationToolbar.__init__(self, plotCanvas)
        self.parent = parent

        # self.toolitems = (('Home', 'Reset original view', 'home', 'home'), ('Back', 'Back to  previous view', 'back', 'back'), ('Forward', 'Forward to next view', 'forward', 'forward'), (None, None, None, None), ('Pan', 'Pan axes with left mouse, zoom with right', 'move', 'pan'), ('Zoom', 'Zoom to rectangle', 'zoom_to_rect', 'zoom'), (None, None, None, None), ('Subplots', 'Configure subplots', 'subplots', 'configure_subplots'), ('Save', 'Save the figure', 'filesave', 'save_figure'))

    def set_history_buttons(self):
        pass

    def mouse_move(self, event=None):
        if event is not None:
            NavigationToolbar.mouse_move(self, event)
        if self.parent.q_active_poly():
            self.set_cursor(2)
        elif self.parent.q_active_info():
            self.set_cursor(0)
        else:
            self.set_cursor(1)


class BasisView(object):

    colors_def = [("color_l", (255,0,0)), ("color_r", (0,0,255)), ("color_i", (160,32,240))]
    DOT_ALPHA = 0.6
        
    COLHIGH='#FFFF00'

    DOT_SHAPE = 's'
    DOT_SIZE = 3
    
    TID = "-"
    SDESC = "-"
    ordN = 0
    title_str = "Basis View"
    geo = False
    typesI = ""

    nb_cols = 4
    spacer_w = 15
    spacer_h = 10
    nbadd_boxes = 0 
    butt_w = 90
    sld_w = 115
    butt_shape = (27, 27)
    fwidth = {"i": 400, "t": 400, "s": 250}
    fheight = {"i": 400, "t": 300, "s": 200}


    def getSpacerW(self):
        return self.spacer_w
    def getSpacerWn(self):
        return self.spacer_w/4.
    def getSpacerH(self):
        return self.spacer_h
    def getVizType(self):
        if self.isIntab():
            if self.parent.getVizm().isVizSplit():
                return "s"
            return "t"
        return "i"
    def getFWidth(self):
        return self.fwidth[self.getVizType()]    
    def getFHeight(self):
        return self.fheight[self.getVizType()]
    def getGPos(self):
        return self.pos
    def resetGPos(self, npos):
        self.mapFrame.GetSizer().Detach(self.panel)
        self.pos = npos
        self.mapFrame.GetSizer().Add(self.panel, pos=self.getGPos(), flag=wx.EXPAND|wx.ALIGN_CENTER, border=0)

    @classmethod
    def getViewsDetails(tcl):
        return {tcl.TID: {"title": tcl.title_str, "class": tcl, "more": None, "ord": tcl.ordN}}

    @classmethod
    def suitableView(tcl, geo=False, what=None, tabT=None):
        return (tabT is None or tabT in tcl.typesI) and (not tcl.geo or geo)

    def __init__(self, parent, vid, more=None):
        self.initVars(parent, vid, more)
        self.initView()

    def initVars(self, parent, vid, more=None):
        self.active_info = False
        self.parent = parent
        self.mc = None
        self.pos = None
        self.sld_sel = None
        self.savef = None
        self.boxL = None
        self.boxT = None
        self.icons = self.parent.icons
        self.rsets = None
        self.rwhich = None
        self.vid = vid
        self.buttons = []
        self.act_butt = [1]
        self.highl = {}
        self.hight = {}
        self.current_hover = None
        self.intab = self.parent.getVizm().showVizIntab()

    def initView(self):
        if self.isIntab():
            self.mapFrame = self.parent.tabs["viz"]["tab"]
            # self.panel = self.parent.tabs["viz"]["tab"]
        else:        
            self.mapFrame = wx.Frame(None, -1, "%s%s" % (self.parent.titlePref, self.getTitleDesc()))
            self.mapFrame.SetMinSize((self.getFWidth(), self.getFHeight()))
            self.mapFrame.SetSizer(wx.BoxSizer(wx.HORIZONTAL))
        self.panel = wx.Panel(self.mapFrame, -1, style=wx.RAISED_BORDER)
        self.drawFrame()
        self.doBinds()
        self.prepareActions()
        self.setKeys()
        self.prepareProcesses()
        self.makeMenu()
        self.initSizeRelative()
        if not self.isIntab():
            self.mapFrame.Show()

    def lastStepInit(self):
        pass

    def isIntab(self):
        return self.intab

    def hideShowOptRec(self, box, where):
        if isinstance(box, wx.SizerItem) and box.IsSizer():
            box = box.GetSizer()
        if isinstance(box, wx.Sizer) or box.IsSizer():
            for child in box.GetChildren():
                self.hideShowOptRec(child, where)
        else:
            ww = (box.GetUserData() or {"where": "i"}).get("where")
            if where in ww or ww == "*":
                box.Show(True)
            else:
                box.Show(False)

    def hideShowOpt(self):
        self.hideShowOptRec(self.innerBox1, self.getVizType())
        self.autoShowSplitsBoxes()

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
        self.processes_map = {}
    def prepareActions(self):
        self.actions_map = {}

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
                    
    def getItemId(self):
        return self.parent.viewsm.getItemId(self.getId())

    def getShortDesc(self):
        return "%s %s" % (self.getItemId(), self.SDESC)

    def getTitleDesc(self):
        return "%s %s" % (self.getItemId(), self.title_str)

    def updateTitle(self):
        if not self.isIntab():
            self.mapFrame.SetTitle("%s%s" % (self.parent.titlePref, self.getTitleDesc()))
        self.info_title.SetLabel(self.getTitleDesc())

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
        if self.isIntab():
            return
        
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

    def enumerateVizItems(self):
        return self.parent.viewsm.getViewsItems(vkey=self.getId())

    def makeVizMenu(self, frame, menuViz=None):
        if menuViz is None:
            menuViz = wx.Menu()
        for item in self.enumerateVizItems():
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
        self.parent.viewsm.viewOther(viewT=self.ids_viewT[event.GetId()], vkey=self.getId())

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
        parts = [{"butt": self.boxL, "id": "learn",
                  "act_icon": self.icons["learn_act"], "dis_icon": self.icons["learn_dis"]},
                 {"butt": self.boxT, "id": "test",
                  "act_icon": self.icons["test_act"], "dis_icon": self.icons["test_dis"]}]
        if event.GetId() == parts[0]["butt"].GetId():
            which = 0
        else:
            which = 1
        if self.rwhich is None: ### None active
            self.rwhich = which
            new_rsets = {"rset_id": parts[which]["id"]}
            parts[which]["butt"].SetBitmap(parts[which]["act_icon"])
            
        elif self.rwhich == which:  ### Current active
            self.rwhich = None
            new_rsets =None
            parts[which]["butt"].SetBitmap(parts[which]["dis_icon"])
            
        else:  ### Other active
            self.rwhich = which
            new_rsets = {"rset_id": parts[which]["id"]}
            parts[which]["butt"].SetBitmap(parts[which]["act_icon"])
            parts[1-which]["butt"].SetBitmap(parts[1-which]["dis_icon"])

        if self.rsets != new_rsets:
            self.rsets = new_rsets
            self.refresh()

        
    def additionalElements(self):
        return []

    def additionalBinds(self):
        for button in self.buttons:
            button["element"].Bind(wx.EVT_BUTTON, button["function"])

    def bindsToFrame(self):
        if not self.isIntab():
            self.mapFrame.Bind(wx.EVT_CLOSE, self.OnQuit)
            self.mapFrame.Bind(wx.EVT_SIZE, self._onSize)

    def bindsOther(self):
        self.savef.Bind(wx.EVT_LEFT_UP, self.OnSaveFig)
        self.boxL.Bind(wx.EVT_LEFT_UP, self.OnSplitsChange)
        self.boxT.Bind(wx.EVT_LEFT_UP, self.OnSplitsChange)
        self.boxPop.Bind(wx.EVT_LEFT_UP, self.OnPop)
        self.boxKil.Bind(wx.EVT_LEFT_UP, self.OnKil)

        # self.boxL.Bind(wx.EVT_TOGGLEBUTTON, self.OnSplitsChange)
        # self.boxT.Bind(wx.EVT_TOGGLEBUTTON, self.OnSplitsChange)
        # self.boxPop.Bind(wx.EVT_TOGGLEBUTTON, self.OnPop)
        # self.boxKil.Bind(wx.EVT_TOGGLEBUTTON, self.OnKil)

        # self.panel.Bind(wx.EVT_ENTER_WINDOW, self.onMouseOver)
        # self.panel.Bind(wx.EVT_LEAVE_WINDOW, self.onMouseLeave)


    def doBinds(self):
        self.bindsToFrame()
        self.bindsOther()

        self.additionalBinds()
        self.autoShowSplitsBoxes()


    # def onMouseOver(self, event):
    #     print "Entering", self.vid, self.panel.GetBackgroundColour()
    #     for elem in [self.panel, self.MapcanvasMap, self.MaptoolbarMap]:
    #         elem.SetBackgroundColour((230, 230, 230))
    #         elem.Refresh()

    # def onMouseLeave(self, event):
    #     print "Exiting", self.vid, self.panel.GetBackgroundColour()
    #     for elem in [self.panel, self.MapcanvasMap, self.MaptoolbarMap]:
    #         elem.SetBackgroundColour((249, 249, 248))
    #         elem.Refresh()

        
    def initSizeRelative(self):
        ds = wx.DisplaySize()
        self.mapFrame.SetClientSizeWH(ds[0]/2.5, ds[1]/1.5)
        # print "Init size", (ds[0]/2.5, ds[1]/1.5)
        # self._SetSize((ds[0]/2.5, ds[1]/1.5))

    def _onSize(self, event=None):
        self._SetSize()


    def setSizeSpec(self, figsize):
        pass

    def _SetSize(self, initSize=None): 
        if initSize is None:
            pixels = tuple(self.mapFrame.GetClientSize() )
        else:
            pixels = initSize
        boxsize = self.innerBox1.GetMinSize()
        min_size = (self.getFWidth(), self.getFHeight())
        if self.isIntab():
            # sz = (laybox.GetCols(), laybox.GetRows())
            sz = self.parent.getVizm().getVizGridSize()
            min_size = (self.getFWidth(), self.getFHeight())
            max_size = ((pixels[0]-2*self.parent.getVizm().getVizBb())/float(sz[1]),
                        (pixels[1]-2*self.parent.getVizm().getVizBb())/float(sz[0]))
            pixels = (max(self.getFWidth(), (pixels[0]-2*self.parent.getVizm().getVizBb())/float(sz[1])),
                      max(self.getFHeight(), (pixels[1]-2*self.parent.getVizm().getVizBb())/float(sz[0])))
            ## print "Redraw", pixels, tuple(self.mapFrame.GetClientSize())
        else:
            pixels = (max(self.getFWidth(), pixels[0]),
                      max(self.getFHeight(), pixels[1]))  
            max_size = (-1, -1)
        self.panel.SetSize( pixels )
        figsize = (pixels[0], max(pixels[1]-boxsize[1], 10))
        # self.MapfigMap.set_size_inches( float( figsize[0] )/(self.MapfigMap.get_dpi()),
        #                                 float( figsize[1] )/(self.MapfigMap.get_dpi() ))
        self.MapcanvasMap.SetMinSize(figsize)
        # #self.fillBox.SetMinSize((figsize[0], figsize[1]))
        self.innerBox1.SetMinSize((1*figsize[0], -1)) #boxsize[1]))
        ## print "\tMapcanvasMap:", figsize, "\tinnerBox1:", (1*figsize[0], curr[1])
        self.setSizeSpec(figsize)
        self.mapFrame.GetSizer().Layout()
        self.MapfigMap.set_size_inches( float( figsize[0] )/(self.MapfigMap.get_dpi()),
                                        float( figsize[1] )/(self.MapfigMap.get_dpi() ))
        ### The line below is primarily for Windows, works fine without in Linux...
        self.panel.SetClientSizeWH(pixels[0], pixels[1])
        # print "Height\tmin=%.2f\tmax=%.2f\tactual=%.2f\tfig=%.2f\tbox=%.2f" % ( min_size[1], max_size[1], pixels[1], figsize[1], boxsize[1])
        # self.MapfigMap.set_size_inches(1, 1)

    def OnSaveFig(self, event=None):
        self.MaptoolbarMap.save_figure(event)

    def OnPop(self, event=None):
        pos = self.getGPos()
        panel = self.popSizer()
        if self.isIntab():
            self.intab = False
            self.mapFrame = wx.Frame(None, -1, "%s%s" % (self.parent.titlePref, self.getTitleDesc()))
            self.mapFrame.SetMinSize((self.getFWidth(), self.getFHeight()))
            self.mapFrame.SetSizer(wx.BoxSizer(wx.HORIZONTAL))

            self.boxPop.SetBitmap(self.icons["outin"])
            # self.boxPop.SetLabel(self.label_outin)
            # self.boxPop.SetValue(False)
            self.parent.getVizm().setVizcellFreeded(pos)
            self.panel.Reparent(self.mapFrame)
            self.mapFrame.GetSizer().Add(self.panel)

        else:
            self.intab = True
            self.mapFrame.Destroy()
            self.mapFrame = self.parent.tabs["viz"]["tab"]
            
            self.boxPop.SetBitmap(self.icons["inout"])
            # self.boxPop.SetLabel(self.label_inout)
            # self.boxPop.SetValue(False)
            self.panel.Reparent(self.mapFrame)
            self.pos = self.parent.getVizm().getVizPlotPos(self.getId())
            self.mapFrame.GetSizer().Add(self.panel, pos=self.getGPos(), flag=wx.ALL, border=0)
            
        self.bindsToFrame()
        self.makeMenu()
        if not self.isIntab():
            self.mapFrame.Show()
        self.hideShowOpt()
        self._SetSize()
            
    def OnKil(self, event=None):
        self.OnQuit()

    def OnQuit(self, event=None, upMenu=True, freeing=True):
        self.parent.viewsm.deleteView(self.getId(), freeing)
        self.parent.viewsm.unregisterView(vkey=self.getId(), upMenu=upMenu)

    def refresh(self):
        pass

    def setCurrent(self, data):
        pass
            
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

        
    def drawFrameSpecific(self):
        pass

    def addFrameSpecific(self):
        pass

    def drawFrame(self):
        # initialize matplotlib stuff
        self.opt_hide = []
        self.MapfigMap = Figure(None) #, facecolor='white')
        self.MapcanvasMap = FigCanvas(self.panel, -1, self.MapfigMap)
        self.MaptoolbarMap = CustToolbar(self.MapcanvasMap, self)

        # styL = wx.ALIGN_RIGHT | wx.EXPAND
        # styV = wx.ALIGN_LEFT | wx.EXPAND
        # sizz = (70,-1)

        self.info_title = wx.StaticText(self.panel, label="? ?")
        self.drawFrameSpecific()

        adds = self.additionalElements()

        ### UTILITIES BUTTONS
        self.savef = wx.StaticBitmap(self.panel, wx.NewId(), self.icons["save"])
        self.boxL = wx.StaticBitmap(self.panel, wx.NewId(), self.icons["learn_dis"])
        self.boxT = wx.StaticBitmap(self.panel, wx.NewId(), self.icons["test_dis"])
        # self.boxL = wx.ToggleButton(self.panel, wx.NewId(), self.label_learn, style=wx.ALIGN_CENTER, size=self.butt_shape)
        # self.boxT = wx.ToggleButton(self.panel, wx.NewId(), self.label_test, style=wx.ALIGN_CENTER, size=self.butt_shape)

        if self.isIntab():
            # self.boxPop = wx.ToggleButton(self.panel, wx.NewId(), self.label_inout, style=wx.ALIGN_CENTER, size=self.butt_shape)
            self.boxPop = wx.StaticBitmap(self.panel, wx.NewId(), self.icons["inout"])
        else:
            # self.boxPop = wx.ToggleButton(self.panel, wx.NewId(), self.label_outin, style=wx.ALIGN_CENTER, size=self.butt_shape)
            self.boxPop = wx.StaticBitmap(self.panel, wx.NewId(), self.icons["outin"])
        # self.boxKil = wx.ToggleButton(self.panel, wx.NewId(), self.label_cross, style=wx.ALIGN_CENTER, size=self.butt_shape)
        self.boxKil = wx.StaticBitmap(self.panel, wx.NewId(), self.icons["kil"])
        if not self.parent.getVizm().hasVizIntab():
            self.boxPop.Hide()
            self.boxKil.Hide()

        self.drawMap()

        ### PUTTING EVERYTHING IN SIZERS
        flags = wx.ALIGN_CENTER | wx.ALL # | wx.EXPAND
        add_boxB = wx.BoxSizer(wx.HORIZONTAL)
        add_boxB.AddSpacer((self.getSpacerWn()/2.,-1), userData={"where": "*"})
        
        add_boxB.Add(self.info_title, 0, border=1, flag=flags, userData={"where": "ts"})
        add_boxB.AddSpacer((2*self.getSpacerWn(),-1), userData={"where": "ts"})

        add_boxB.Add(self.MaptoolbarMap, 0, border=0, userData={"where": "*"})
        add_boxB.Add(self.boxL, 0, border=0, flag=flags, userData={"where": "*"})
        add_boxB.Add(self.boxT, 0, border=0, flag=flags, userData={"where": "*"})
        add_boxB.AddSpacer((2*self.getSpacerWn(),-1), userData={"where": "*"})

        add_boxB.Add(self.boxPop, 0, border=0, flag=flags, userData={"where": "*"})
        add_boxB.Add(self.boxKil, 0, border=0, flag=flags, userData={"where": "*"})
        add_boxB.AddSpacer((2*self.getSpacerWn(),-1))

        add_boxB.Add(self.savef, 0, border=0, flag=flags, userData={"where": "*"})
        add_boxB.AddSpacer((2*self.getSpacerWn(),-1))

        self.masterBox =  wx.FlexGridSizer(rows=2, cols=1, vgap=0, hgap=0)
        #self.masterBox = wx.BoxSizer(wx.VERTICAL)

        #self.fillBox = wx.BoxSizer(wx.HORIZONTAL)
        self.innerBox = wx.BoxSizer(wx.HORIZONTAL)
        self.innerBox1 = wx.BoxSizer(wx.VERTICAL)
        self.masterBox.Add(self.MapcanvasMap, 0, border=1,  flag= wx.EXPAND)
        #self.masterBox.Add(self.fillBox, 0, border=1,  flag= wx.EXPAND)

        self.addFrameSpecific()
        
        self.innerBox1.AddSpacer((-1,self.getSpacerH()), userData={"where": "it"})
        for add in adds:
            self.innerBox1.Add(add, 0, border=1,  flag= wx.ALIGN_CENTER)
        self.innerBox1.AddSpacer((-1,self.getSpacerH()/2), userData={"where": "it"})
        self.innerBox1.Add(add_boxB, 0, border=1,  flag= wx.ALIGN_CENTER)
        self.innerBox1.AddSpacer((-1,self.getSpacerH()/2), userData={"where": "*"})
            
        self.innerBox.Add(self.innerBox1, 0, border=1,  flag= wx.ALIGN_CENTER)
        self.masterBox.Add(self.innerBox, 0, border=1, flag= wx.EXPAND| wx.ALIGN_CENTER| wx.ALIGN_BOTTOM)
        self.panel.SetSizer(self.masterBox)
        if self.isIntab():
            self.pos = self.parent.getVizm().getVizPlotPos(self.getId())
            self.mapFrame.GetSizer().Add(self.panel, pos=self.pos, flag=wx.ALL, border=0)
        else:
            self.mapFrame.GetSizer().Add(self.panel)
            # self.panel.GetSizer().Fit(self.panel)
            # self.mapFrame.GetSizer().Add(self.masterBox, pos=pos, flag=wx.ALL, border=2)

        self.hideShowOpt()
        self._SetSize()


    def popSizer(self):
        if self.isIntab():
            self.pos = None
            self.mapFrame.GetSizer().Detach(self.panel)
            self.mapFrame.GetSizer().Layout()
        return self.panel

            
    def updateMap(self):
        """ Redraws the map
        """
        pass


    # def updateHist(self, red = None, init=False):
    #     ### if this is an history update on opening viz, only do if no other viz open for red
    #     if red is not None:
    #         if init and self.parent.viewsm.getItemViewCount(self.getId()) > 1:
    #             return
    #         self.parent.appendToHist(red)

    def sendEditBack(self, red = None):
        if red is not None:
            self.parent.viewsm.dispatchEdit(red, vkey=self.getId())

    def updateText(self, red = None):
        pass

    def updateEmphasize(self, review=True):
        lids = self.parent.viewsm.getEmphasizedR(vkey=self.getId())
        self.emphasizeOnOff(turn_on=lids, turn_off=None, review=review)

    def emphasizeOnOff(self, turn_on=set(), turn_off=set(), review=True):
        self.emphasizeOff(turn_off)
        self.emphasizeOn(turn_on)
        self.makeMenu()
        # if review:
        #     print "draw"
        #     self.MapcanvasMap.draw()

    def emphasizeOn(self, lids):
        pass
    
    def emphasizeOff(self, lids = None):
        pass

    def sendEmphasize(self, lids):
        return self.parent.viewsm.setEmphasizedR(vkey=self.getId(), lids=lids, show_info=self.q_active_info())

    def sendFlipEmphasizedR(self):
        return self.parent.viewsm.doFlipEmphasizedR(vkey=self.getId())

    def OnPick(self, event):
        if event.mouseevent.button in self.act_butt:
            gid_parts = event.artist.get_gid().split(".")
            if (isinstance(event.artist, Line2D) or isinstance(event.artist, Polygon)): 
                if gid_parts[-1] == "1":
                    self.sendEmphasize([int(gid_parts[0])])
                else:
                    self.sendOtherPick(gid_parts)
    #         elif isinstance(event.artist, Annotation):
    #             if gid_parts[-1] == "T":
    #                 self.sendEntFocus([int(gid_parts[0])])

    # def sendEntFocus(self, gid_parts):
    #     pass

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
        pass
            
    def apply_mask(self, path, radius=0.0):
        pass

    def getColorHigh(self):        
        t = self.parent.dw.getPreferences()
        if "color_h" in t:
            return [i/255.0 for i in t["color_h"]["data"]]
        else:
            return self.COLHIGH

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
        if t["miss_details"]["data"] == "yes":
            return True
        return False

    def getDrawSettings(self):
        colors = self.getColors()
        colhigh = self.getColorHigh()
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
                "colhigh": colhigh,
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
