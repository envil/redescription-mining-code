import wx, numpy, re
# The recommended way to use wx with mpl is with the WXAgg backend. 
import matplotlib
matplotlib.use('WXAgg')

from matplotlib.backends.backend_wxagg import \
    FigureCanvasWxAgg as FigCanvas, \
    NavigationToolbar2WxAgg as NavigationToolbar
from matplotlib.figure import Figure

from ..clired.classQuery import SYM, Query
from ..clired.classSParts import SSetts
from ..clired.classRedescription import Redescription
from ..interface.classContentTable import RedsTable, VarsTable

import pdb

class CustToolbar(NavigationToolbar):
    """ 
    Customized Toolbar for action on the plot including saving, attaching to main window, etc.
    Sets the different mouse cursors depending on context. 
    """
    
    def __init__(self, plotCanvas, parent):
        self.toolitems = (('Home', 'Reset original view', 'home', 'home'), ('Back', 'Back to  previous view', 'back', 'back'), ('Forward', 'Forward to next view', 'forward', 'forward'), (None, None, None, None), ('Pan', 'Pan axes with left mouse, zoom with right', 'move', 'pan'), ('Zoom', 'Zoom to rectangle', 'zoom_to_rect', 'zoom'))
        # , (None, None, None, None), ('Subplots', 'Configure subplots', 'subplots', 'configure_subplots'), ('Save', 'Save the figure', 'filesave', 'save_figure')
        if not parent.hasParent():
            self.toolitems = tuple(list(self.toolitems) +[('Save', 'Save the figure', 'filesave', 'save_figure')])
        NavigationToolbar.__init__(self, plotCanvas)
        self.parent = parent
        self.drawer = None

        # self.toolitems = (('Home', 'Reset original view', 'home', 'home'), ('Back', 'Back to  previous view', 'back', 'back'), ('Forward', 'Forward to next view', 'forward', 'forward'), (None, None, None, None), ('Pan', 'Pan axes with left mouse, zoom with right', 'move', 'pan'), ('Zoom', 'Zoom to rectangle', 'zoom_to_rect', 'zoom'), (None, None, None, None), ('Subplots', 'Configure subplots', 'subplots', 'configure_subplots'), ('Save', 'Save the figure', 'filesave', 'save_figure'))

    def set_history_buttons(self):
        pass

    def setDrawer(self, drawer):
        self.drawer = drawer

    def has_active_button(self):
        return len("%s" % self.mode) > 0
        # return self._active is not None
    def mouse_move(self, event=None):
        if event is not None:
            NavigationToolbar.mouse_move(self, event)
        if self.drawer is not None and self.drawer.q_active_poly():
            self.set_cursor(2)
        elif self.drawer is not None and self.drawer.q_active_info():
            self.set_cursor(0)
        else:
            self.set_cursor(1)

class LayoutHandlerBare(object):
    #### SEC: WINDOW LAYOUT INTAB / STANDALONE
    ###########################################
    
    spacer_w = 15
    spacer_h = 10
    nbadd_boxes = 0 
    butt_w = 90
    sld_w = 115
    butt_shape = (27, 27)
    fwidth = {"i": 400, "t": 400, "s": 250}
    fheight = {"i": 400, "t": 300, "s": 200}
    
    def __init__(self, view):
        
        self.view = view
        self.layout_infos = {}
        self.layout_elements = {}
        self.isInTab = (self.hasParent() and self.getParentVizm().showVizIntab())
        self.pos = None
        
        if self.hasParent() and self.isInTab:
            self.setFrame(self.getParentTab("viz"))
        else:
            self.setFrame(self.initExtFrame())
        self.panel = wx.Panel(self.getFrame(), -1, style=wx.RAISED_BORDER)

    def finalize_init(self, addBoxes=[]):
        utilityBox = self.makeUtilityBox()
        innerBox = wx.BoxSizer(wx.VERTICAL)
        self.makeFrameSpecific(innerBox)
        self.arrangeAll(innerBox, utilityBox, addBoxes)
        self.layout_elements["innerBox"] = innerBox
        self.getFrame().Layout()
        self.initSizeRelative()
        if not self.isInTab:
            self.getFrame().Show()
            self.prepareProcesses()
            self.hideShowOpt()
            self._SetSize()

    def getPanel(self):
        return self.panel
    def getFrame(self):
        return self.frame
    def setFrame(self, value):
        self.frame = value
        if not self.isInTab:
            self.frame.Bind(wx.EVT_CLOSE, self.OnQuit)
            self.frame.Bind(wx.EVT_SIZE, self.OnSize)

    def getTable(self):
        return None    
    def getFigure(self):
        return None
    def getCanvas(self):
        return None
    def getToolbar(self):
        return None

    def hasTable(self):
        return self.getTable() is not None
    def hasFigure(self):
        return self.getFigure() is not None
    
    def setToolbarDrawer(self, drawer=None):
        if drawer is not None and self.hasFigure():
            self.getToolbar().setDrawer(drawer)

    
    #### SEC: PARENT ACCESS
    ###########################################

    def getId(self):
        return self.view.getId()
    def hasParent(self):
        return self.view.hasParent()
    def getParent(self):
        return self.view.getParent()
    def getDrawer(self):
        return self.view.getDrawer()
    def hasDrawer(self):
        return self.view.hasDrawer()

    def getPltDtH(self):
        return self.view.getPltDtH()

    def getParentVizm(self):
        return self.view.getParentVizm()
    def getParentViewsm(self):
        return self.view.getParentViewsm()
    def getParentTab(self, which):
        return self.view.getParentTab(which)
    def getParentData(self):
        return self.view.getParentData()
    def getParentIcon(self, key=None):
        tmp = self.view.getParentIcon(key)
        if tmp is None:
            tmp = wx.NullBitmap
        return tmp
    def getParentTitlePref(self):
        return self.view.getParentTitlePref()
    def getViewTitleDesc(self):
        return self.view.getTitleDesc()

    def makeUtilityBox(self):
        self.layout_elements["info_title"] = wx.StaticText(self.getPanel(), label="? ?")
        self.opt_hide = []

        ### UTILITIES BUTTONS
        self.layout_elements["savef"] = wx.StaticBitmap(self.getPanel(), wx.NewId(), self.getParentIcon("save"))
        self.layout_elements["boxL"] = wx.StaticBitmap(self.getPanel(), wx.NewId(), self.getParentIcon("learn_dis"))
        self.layout_elements["boxT"] = wx.StaticBitmap(self.getPanel(), wx.NewId(), self.getParentIcon("test_dis"))

        if self.isInTab:
            self.layout_elements["boxPop"] = wx.StaticBitmap(self.getPanel(), wx.NewId(), self.getParentIcon("inout"))
        else:
            self.layout_elements["boxPop"] = wx.StaticBitmap(self.getPanel(), wx.NewId(), self.getParentIcon("outin"))

        self.layout_elements["boxKil"] = wx.StaticBitmap(self.getPanel(), wx.NewId(), self.getParentIcon("kil"))
        if not self.hasParent() or not self.getParentVizm().hasVizIntab():
            self.layout_elements["boxPop"].Hide()
            self.layout_elements["boxKil"].Hide()

        ### Bind
        for (elem, meth) in [("savef", self.OnSaveFig),
                             ("boxL", self.OnFoldsChange), ("boxT", self.OnFoldsChange),
                             ("boxPop", self.OnPop), ("boxKil", self.OnKil)]:
            self.layout_elements[elem].Bind(wx.EVT_LEFT_UP, meth)

            
        flags = wx.ALIGN_CENTER | wx.ALL # | wx.EXPAND
        add_boxB = wx.BoxSizer(wx.HORIZONTAL)
        add_boxB.AddSpacer(self.getSpcWnHalf()) #, userData={"where": "*"})
        
        add_boxB.Add(self.layout_elements["info_title"], 0, border=1, flag=flags, userData={"where": "ts"})
        add_boxB.AddSpacer(self.getSpcWnTwo()) #, userData={"where": "ts"})

        if self.getFigure():
            add_boxB.Add(self.getToolbar(), 0, border=0, userData={"where": "*"})
        add_boxB.Add(self.layout_elements["boxL"], 0, border=0, flag=flags, userData={"where": "*"})
        add_boxB.Add(self.layout_elements["boxT"], 0, border=0, flag=flags, userData={"where": "*"})
        add_boxB.AddSpacer(self.getSpcWnTwo()) #, userData={"where": "*"})

        add_boxB.Add(self.layout_elements["boxPop"], 0, border=0, flag=flags, userData={"where": "*"})
        add_boxB.Add(self.layout_elements["boxKil"], 0, border=0, flag=flags, userData={"where": "*"})
        add_boxB.AddSpacer(self.getSpcWnTwo())

        add_boxB.Add(self.layout_elements["savef"], 0, border=0, flag=flags, userData={"where": "*"})
        ## add_boxB.Add(self.stamp, 0, border=0, flag=flags, userData={"where": "*"})
        add_boxB.AddSpacer(self.getSpcWnTwo())
        return add_boxB

    def arrangeAll(self, innerBox, utilityBox, addBoxes=[]):
        if len(addBoxes) > 0:
            innerBox.AddSpacer(self.getSpcH()) #, userData={"where": "it"})
            for add in addBoxes:
                innerBox.Add(add, 0, border=1,  flag= wx.ALIGN_CENTER)

        innerBox.AddSpacer(self.getSpcHHalf()) #, userData={"where": "it"})
        innerBox.Add(utilityBox, 0, border=1,  flag= wx.ALIGN_CENTER)
        innerBox.AddSpacer(self.getSpcHHalf()) #, userData={"where": "*"})

        outerBox = wx.BoxSizer(wx.HORIZONTAL)
        outerBox.Add(innerBox, 0, border=1,  flag= wx.ALIGN_CENTER)

        masterBox = wx.FlexGridSizer(rows=2, cols=1, vgap=0, hgap=0)
        self.addContentDisp(masterBox)
        masterBox.Add(outerBox, 0, border=1, flag= wx.EXPAND)#| wx.ALIGN_CENTER| wx.ALIGN_BOTTOM
        self.getPanel().SetSizer(masterBox)
        if self.isInTab:
            self.pos = self.getParentVizm().getVizPlotPos(self.getId())
            self.frame.GetSizer().Add(self.getPanel(), pos=self.pos, flag=wx.ALL, border=0)
        else:
            self.frame.GetSizer().Add(self.getPanel())
                            
    def updateTitle(self):
        if self.hasParent() and not self.isInTab:
            self.frame.SetTitle("%s%s" % (self.getParentTitlePref(), self.getViewTitleDesc()))
        if "info_title" in self.layout_elements:
            self.layout_elements["info_title"].SetLabel(self.getViewTitleDesc())

    def getSpacerW(self):
        return self.spacer_w
    def getSpacerWn(self):
        return self.spacer_w/4.
    def getSpacerH(self):
        return self.spacer_h

    def getSpcWnHalf(self):
        return self.getSpacerWn()/2
    def getSpcWn(self):
        return self.getSpacerWn()
    def getSpcWnTwo(self):
        return 2*self.getSpacerWn()
    def getSpcH(self):
        return self.getSpacerH()
    def getSpcHHalf(self):
        return self.getSpacerH()/2
    def getSpcTen(self):
        return 10
    # def getSpcWnHalf(self):
    #     return (self.getSpacerWn()/2.,-1)
    # def getSpcWn(self):
    #     return (self.getSpacerWn(),-1)
    # def getSpcWnTwo(self):
    #     return (2*self.getSpacerWn(),-1)
    # def getSpcH(self):
    #     return (-1,self.getSpacerH())
    # def getSpcHHalf(self):
    #     return (-1,self.getSpacerH()/2)
    # def getSpcTen(self):
    #     return (10,-1)

    
    def getVizType(self):
        if self.isInTab:
            if self.getParentVizm().isVizSplit():
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
        self.frame.GetSizer().Detach(self.getPanel())
        self.pos = npos
        self.frame.GetSizer().Add(self.getPanel(), pos=self.getGPos(), flag=wx.EXPAND, border=0)#|wx.ALIGN_CENTER

    def GetRoundBitmap(self, w, h, r=10):
        maskColour = wx.Colour(0,0,0)
        shownColour = wx.Colour(5,5,5)
        b = wx.EmptyBitmap(w,h)
        dc = wx.MemoryDC(b)
        dc.SetBrush(wx.Brush(maskColour))
        dc.DrawRectangle(0,0,w,h)
        dc.SetBrush(wx.Brush(shownColour))
        dc.SetPen(wx.Pen(shownColour))
        dc.DrawCircle(w/2,h/2,w/2)
        dc.SelectObject(wx.NullBitmap)
        b.SetMaskColour(maskColour)
        return b

    def toTop(self):
        self.frame.Raise()
        self.setContentFocus()
    
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

    def showFoldsBoxes(self, show=True):
        self.layout_elements["boxL"].Show(show)
        self.layout_elements["boxT"].Show(show)

    def autoShowFoldsBoxes(self):
        if self.getParentData() is not None and self.getParentData().hasLT():
            self.showFoldsBoxes(True)
        else:
            self.showFoldsBoxes(False)
                 
    def hideShowOpt(self):
        self.hideShowOptRec(self.layout_elements["innerBox"], self.getVizType())
        self.autoShowFoldsBoxes()

    def initSizeRelative(self):
        ds = wx.DisplaySize()
        self.frame.SetClientSize(ds[0]/2.5, ds[1]/1.5)
            
    def _SetSize(self, initSize=None): 
        if initSize is None:
            pixels = tuple(self.frame.GetClientSize() )
        else:
            pixels = initSize
        if self.layout_infos.get("store_size") == pixels:
            return
        self.layout_infos["store_size"] = pixels
        boxsize = self.layout_elements["innerBox"].GetMinSize()
        ## min_size = (self.getFWidth(), self.getFHeight())
        if self.isInTab:
            # sz = (laybox.GetCols(), laybox.GetRows())
            sz = self.getParentVizm().getVizGridSize()
            ## min_size = (self.getFWidth(), self.getFHeight())
            ## max_size = ((pixels[0]-2*self.getParentVizm().getVizBb())/float(sz[1]),
            ##             (pixels[1]-2*self.getParentVizm().getVizBb())/float(sz[0]))
            pixels = (max(self.getFWidth(), (pixels[0]-2*self.getParentVizm().getVizBb())/float(sz[1])),
                      max(self.getFHeight(), (pixels[1]-2*self.getParentVizm().getVizBb())/float(sz[0])))
            ## print("Redraw", pixels, tuple(self.frame.GetClientSize()))
        else:
            pixels = (max(self.getFWidth(), pixels[0]),
                      max(self.getFHeight(), pixels[1]))  
            ## max_size = (-1, -1)
        self.getPanel().SetSize( pixels )
        figsize = (pixels[0], max(pixels[1]-boxsize[1], 10))
        # self.figure.set_size_inches( float( figsize[0] )/(self.figure.get_dpi()),
        #                                 float( figsize[1] )/(self.figure.get_dpi() ))
        self.setContentMinSize(figsize)
        self.layout_elements["innerBox"].SetMinSize((1*figsize[0], -1)) #boxsize[1]))
        self.setSizeSpec(figsize)
        self.frame.GetSizer().Layout()
        self.setContentSize(figsize)
        ### The line below is primarily for Windows, works fine without in Linux...
        self.panel.SetClientSize(pixels[0], pixels[1])
        # print("Height\tmin=%.2f\tmax=%.2f\tactual=%.2f\tfig=%.2f\tbox=%.2f" % ( min_size[1], max_size[1], pixels[1], figsize[1], boxsize[1]))
        # self.figure.set_size_inches(1, 1)

    def initExtFrame(self):
        pref = self.getParentTitlePref()
        extFrame = wx.Frame(None, -1, "%s%s" % (pref, self.getViewTitleDesc()))
        extFrame.SetMinSize((self.getFWidth(), self.getFHeight()))
        extFrame.SetSizer(wx.BoxSizer(wx.HORIZONTAL))
        return extFrame
            
    def OnSize(self, event=None):        
        self._SetSize()
        if self.hasDrawer():
            self.getDrawer().adjust()

    def OnPop(self, event=None):
        pos = self.getGPos()
        self.popSizer()
        if self.isInTab:
            self.isInTab = False
            self.setFrame(self.initExtFrame())
            self.layout_elements["boxPop"].SetBitmap(self.getParentIcon("outin"))
            self.getParentVizm().setVizcellFreeded(pos)
            self.getPanel().Reparent(self.frame)
            self.frame.GetSizer().Add(self.getPanel())
        else:
            self.isInTab = True

            self.frame.Destroy()
            self.setFrame(self.getParentTab("viz"))
            self.layout_elements["boxPop"].SetBitmap(self.getParentIcon("inout"))

            self.getPanel().Reparent(self.frame)
            self.pos = self.getParentVizm().getVizPlotPos(self.getId())
            self.frame.GetSizer().Add(self.getPanel(), pos=self.getGPos(), flag=wx.ALL, border=0)
            
        if not self.isInTab:
            self.getFrame().Layout()
            self.initSizeRelative()
            self.getFrame().Show()
        self.hideShowOpt()
        self._SetSize()

    def OnFoldsChange(self, event):
        new_rsets = None
        parts = [{"butt": self.layout_elements["boxL"], "id": "learn",
                  "act_icon": self.getParentIcon("learn_act"), "dis_icon": self.getParentIcon("learn_dis")},
                 {"butt": self.layout_elements["boxT"], "id": "test",
                  "act_icon": self.getParentIcon("test_act"), "dis_icon": self.getParentIcon("test_dis")}]
        if event.GetId() == parts[0]["butt"].GetId():
            which = 0
        else:
            which = 1
        if self.layout_infos.get("rwhich") is None: ### None active
            self.layout_infos["rwhich"] = which
            new_rsets = {"rset_id": parts[which]["id"]}
            parts[which]["butt"].SetBitmap(parts[which]["act_icon"])
            
        elif self.layout_infos.get("rwhich") == which:  ### Current active
            self.layout_infos["rwhich"] = None
            new_rsets = None
            parts[which]["butt"].SetBitmap(parts[which]["dis_icon"])
            
        else:  ### Other active
            self.layout_infos["rwhich"] = which
            new_rsets = {"rset_id": parts[which]["id"]}
            parts[which]["butt"].SetBitmap(parts[which]["act_icon"])
            parts[1-which]["butt"].SetBitmap(parts[1-which]["dis_icon"])
        self.view.updateRSets(new_rsets)       
            
    def OnKil(self, event=None):
        self.OnQuit()
        
    def OnQuit(self, event=None, upMenu=True, freeing=True):
        self.view.OnQuit(event, upMenu, freeing)

    def destroyFrame(self):
        self.frame.Destroy()
        
    def destroy(self):
        if self.isInTab:
            self.popSizer()
            self.isInTab = False
            frame = wx.Frame(None, -1, "X")            
            self.setFrame(frame)
            self.getPanel().Reparent(self.frame)
        self.frame.Destroy()
        
    def popSizer(self):
        self.frame.GetSizer().Detach(self.getPanel())
        if self.isInTab:
            self.pos = None
            self.frame.GetSizer().Layout()
        return self.getPanel()
   
    #### SEC: MENU PROCESSES
    ###########################################

    def prepareProcesses(self):
        self.processes_map = {}
    def getProcesses(self):
        return sorted(self.processes_map.items(), key=lambda x: (x[1]["order"], x[1]["label"]))
    def setFocus(self):
        self.setContentFocus()
    
    def kill(self):
        pass
    def wasKilled(self):
        False
    def draw(self):
        pass
    def setSizeSpec(self, figsize):
        pass
    def makeFrameSpecific(self, innerBox):
        pass
    def refresh(self):
        pass
    def OnSaveFig(self, event=None):
        pass
    def savefig(self, fname, **kwargs):
        pass
    def setContentMinSize(self, figsize):
        pass
    def setContentSize(self, figsize):
        pass
    def setContentFocus(self):
        pass
    def addContentDisp(self, masterBox):
        pass
    
class LayoutHandlerText(LayoutHandlerBare):
    def __init__(self, view):
        LayoutHandlerBare.__init__(self, view)
        self.content_table = RedsTable(self.getParent(), -1, "r", self.getPanel(), single=True, detached_handle=view, activate=False)
        
    def getTable(self):
        return self.content_table
    def getCanvas(self):
        if self.hasTable():
            return self.getTable().getSW()

    def kill(self):
        pass
    def wasKilled(self):
        False
    def draw(self):
        pass
    def setSizeSpec(self, figsize):
        pass
    def makeFrameSpecific(self, innerBox):
        pass
    def refresh(self):
        pass
    def OnSaveFig(self, event=None):
        self.getParent().saveRedListAs(self.getTable().getTab(), self.getFrame())
    def savefig(self, fname, **kwargs):
        print("IMPLEMENT SAVE AS")
        pass
    def setContentSize(self, figsize):
        self.getCanvas().SetMinSize(figsize)
    def setContentFocus(self):
        pass
    def addContentDisp(self, masterBox):
        if self.hasTable():
            masterBox.Add(self.getCanvas(), 0, border=1,  flag= wx.EXPAND)

        
class LayoutHandlerBasis(LayoutHandlerBare):

    def __init__(self, view):
        LayoutHandlerBare.__init__(self, view)

        self.figure = Figure(None) #, facecolor='white')
        self._canvas = FigCanvas(self.getPanel(), -1, self.figure)
        self._toolbar = CustToolbar(self._canvas, self)

    def getFigure(self):
        return self.figure
    def getCanvas(self):
        return self._canvas
    def getToolbar(self):
        return self._toolbar

    def kill(self):
        if self.hasFigure():
            self._canvas = None
    def wasKilled(self):
        if self.hasFigure():
            return not self.getCanvas() is not None
    def draw(self):
        if self.hasFigure():
            self.getCanvas().draw()
    def OnSaveFig(self, event=None):
        if self.hasFigure() and self.getToolbar() is not None:
            self.getToolbar().save_figure(event)
    def savefig(self, fname, **kwargs):
        if self.hasFigure():
            self.getFigure().savefig(fname, **kwargs)
    def setContentMinSize(self, figsize):
        if self.hasFigure():
            self.getCanvas().SetMinSize(figsize)
    def setContentSize(self, figsize):
        if self.hasFigure():
            self.getFigure().set_size_inches( float(figsize[0])/(self.getFigure().get_dpi()),
                                        float(figsize[1])/(self.getFigure().get_dpi()))

    def setContentFocus(self):
        if self.hasFigure():
            try:
                self.getFigure().canvas.SetFocus()
            except AttributeError:
                self.frame.SetFocus()
        else:
            self.frame.SetFocus()
    def addContentDisp(self, masterBox):
        if self.hasFigure():
            masterBox.Add(self.getCanvas(), 0, border=1,  flag= wx.EXPAND)

    
class LayoutHandlerQueries(LayoutHandlerBasis):

    nb_cols = 4
    label_jacc="J ="
    label_pval="p-value ="
    label_typeP="J-type ="

    label_cardN="|E| ="
    label_cardU="|E"+SYM.SYM_SETMIN+"E"+SSetts.sym_sparts[SSetts.Eoo]+"| ="    

    label_cardP="|E%s| ="
    
    label_cardAlpha="|E"+SSetts.sym_sparts[SSetts.Exo]+"| ="
    label_cardBeta="|E"+SSetts.sym_sparts[SSetts.Eox]+"| ="
    label_cardI="|E"+SSetts.sym_sparts[SSetts.Exx]+"| ="
    label_cardO="|E"+SSetts.sym_sparts[SSetts.Eoo]+"| ="
    
    label_learn = SYM.SYM_LEARN #+":"
    label_test = SYM.SYM_TEST #+":"
    label_ratio = SYM.SYM_RATIO #+":"

    label_inout = SYM.SYM_INOUT
    label_outin = SYM.SYM_OUTIN 
    label_cross = SYM.SYM_CROSS

    infos_details = []

    for status in [(True, True), (False, False), (True, False), (False, True)]:
        i = SSetts.mapStatusToSPart(status)
        whl = re.sub("_", "", SSetts.labels[i])
        infos_details.append({"id": "x%s" % SSetts.labels_sparts[i], "part_id": i,
                              "label": label_cardP % SSetts.sym_sparts[i],
                              "fk": ":len:%s" % whl})
                
    for status in [(None, None), (False, None), (True, None), (None, True), (None, False)]:
        i = SSetts.mapStatusToSPart(status)
        whl = re.sub("_", "", SSetts.labels[i])
        infos_details.append({"id": "x%s" % SSetts.labels_sparts[i], "part_id": i, "miss": True,
                              "label": label_cardP % SSetts.sym_sparts[i],
                              "fk": ":len:%s" % whl})

    infos_details.insert(0, {"id": "jacc", "label": label_jacc, "fk": ":acc:"})
    infos_details.insert(3, {"id": "lenN", "label": label_cardN, "fk": ":len:N"})
    infos_details.insert(4, {"id": "pval", "label": label_pval, "fk": ":pval:"})

    infos_details_cond = []
    for f in infos_details:
        infos_details_cond.append(dict(f))
        infos_details_cond[-1]["id"] += ":C"
        infos_details_cond[-1]["label"] = infos_details_cond[-1]["label"]
        infos_details_cond[-1]["fk"] = "cond"+infos_details_cond[-1]["fk"]
    
    # for status in [(True, True), (False, False), (True, False), (False, True)]:
    #     i = SSetts.mapStatusToSPart(status)
    #     pdb.set_trace()
    #     infos_details.append({"id": "x%s" % SSetts.labels_sparts[i],
    #                            "label": label_cardP % SSetts.sym_sparts[i],
    #                            "meth": "getLenP", "format": "%i", "details": {"part_id": i}})
                
    # for status in [(None, None), (False, None), (True, None), (None, True), (None, False)]:
    #     i = SSetts.mapStatusToSPart(status)
    #     infos_details.append( {"id": "x%s" % SSetts.labels_sparts[i],
    #                            "label": label_cardP % SSetts.sym_sparts[i],
    #                            "meth": "getLenP", "format": "%i", "miss": True, "details": {"part_id": i}})

    # infos_details.insert(0, {"id": "jacc", "label": label_jacc, "meth": "getRoundAcc", "format": "%1.3f"})
    # infos_details.insert(3, {"id": "lenN", "label": label_cardN, "meth": "getLenN", "format": "%i"})
    # infos_details.insert(4, {"id": "pval", "label": label_pval, "meth": "getRoundPVal", "format": "%1.3f"})
    # # infos_details.insert(8, {"id": "typP", "label": label_typeP, "meth": "getTypeParts", "format": "%s", "miss": True})

    def withCond(self):
        return self.getParentData() is not None and self.getParentData().isConditional()
        
    def setSizeSpec(self, figsize):
        self.layout_elements["queries_text"][0].SetMinSize((1*figsize[0], -1))
        self.layout_elements["queries_text"][1].SetMinSize((1*figsize[0], -1))
        if self.withCond():
            self.layout_elements["queries_text"][-1].SetMinSize((1*figsize[0], -1))

    def makeFrameSpecific(self, innerBox):
        self.layout_elements["qtxt_ids"] = [wx.NewId(), wx.NewId()]
        self.layout_elements["queries_text"] = [wx.TextCtrl(self.panel, self.layout_elements["qtxt_ids"][0], style=wx.TE_PROCESS_ENTER),
                                                wx.TextCtrl(self.panel, self.layout_elements["qtxt_ids"][1], style=wx.TE_PROCESS_ENTER)]
        colors = self.view.getColors255()
        self.layout_elements["queries_text"][0].SetForegroundColour(colors[0])
        self.layout_elements["queries_text"][1].SetForegroundColour(colors[1])
        
        self.info_items = {}
        for info_item in self.infos_details:
            if not info_item.get("miss", False) or (self.getParentData() is not None and self.getParentData().hasMissing()):
                # self.info_items[info_item["id"]] = (wx.StaticText(self.panel, label=info_item["label"], style=styL, size=sizz),
                #                                     wx.StaticText(self.panel, label="--", style=styV, size=sizz))
                self.info_items[info_item["id"]] = (wx.StaticText(self.panel, label=info_item["label"]),
                                                    wx.StaticText(self.panel, label="XXX"))
                if info_item.get("part_id", SSetts.Eoo) < SSetts.Eoo:
                    self.info_items[info_item["id"]][1].SetForegroundColour(colors[info_item["part_id"]])

        innerBox.Add(self.layout_elements["queries_text"][0], 0, border=1,  flag= wx.ALIGN_CENTER, userData={"where": "it"})
        innerBox.Add(self.layout_elements["queries_text"][1], 0, border=1,  flag= wx.ALIGN_CENTER, userData={"where": "it"})

        self.layout_elements["queries_text"][0].Bind(wx.EVT_TEXT_ENTER, self.OnEditQuery)
        self.layout_elements["queries_text"][1].Bind(wx.EVT_TEXT_ENTER, self.OnEditQuery)
        blocks = [self.infos_details]
        
        ######################################
        ######### CONDITIONAL
        if self.withCond():

            self.layout_elements["qtxt_ids"].append(wx.NewId())
            self.layout_elements["queries_text"].append(wx.TextCtrl(self.panel, self.layout_elements["qtxt_ids"][-1], style=wx.TE_PROCESS_ENTER))

            for info_item in self.infos_details_cond:
                if not info_item.get("miss", False) or (self.getParentData() is not None and self.getParentData().hasMissing()):
                    # self.info_items[info_item["id"]] = (wx.StaticText(self.panel, label=info_item["label"], style=styL, size=sizz),
                    #                                     wx.StaticText(self.panel, label="--", style=styV, size=sizz))
                    self.info_items[info_item["id"]] = (wx.StaticText(self.panel, label=info_item["label"]),
                                                        wx.StaticText(self.panel, label="XXX"))
                    if info_item.get("part_id", SSetts.Eoo) < SSetts.Eoo:
                        self.info_items[info_item["id"]][1].SetForegroundColour(colors[info_item["part_id"]])

            innerBox.Add(self.layout_elements["queries_text"][-1], 0, border=1,  flag= wx.ALIGN_CENTER, userData={"where": "it"})
            self.layout_elements["queries_text"][-1].Bind(wx.EVT_TEXT_ENTER, self.OnEditQuery)
            blocks.append(self.infos_details_cond)
            
        for bi, block in enumerate(blocks):
            innerBox.AddSpacer(self.getSpacerH()) #, userData={"where": "*"})
            if bi > 0:
                # innerBox.Add(wx.StaticLine(self.panel), 0, wx.EXPAND|wx.ALL, 5)
                innerBox.Add(wx.StaticText(self.panel, label="Conditional"), 0, wx.ALIGN_CENTER)
                innerBox.Add(wx.StaticLine(self.panel, size=(200, -1), style=wx.LI_HORIZONTAL), 0, wx.ALIGN_CENTER)
        
            cols = [wx.BoxSizer(wx.VERTICAL) for i in range(2*self.nb_cols)]
            for pi, elem in enumerate(block):
                if not elem.get("miss", False) or (self.getParentData() is not None and self.getParentData().hasMissing()):
                    ci = 2*(pi % self.nb_cols)
                    cols[ci].Add(self.info_items[elem["id"]][0], 1, border=1,  flag= wx.ALL|wx.ALIGN_RIGHT, userData={"where": "it"})
                    cols[ci+1].Add(self.info_items[elem["id"]][1], 1, border=1,  flag= wx.ALL|wx.ALIGN_RIGHT, userData={"where": "it"})
            # self.opt_hide.extend(cols)

            lineB = wx.BoxSizer(wx.HORIZONTAL)
            for ci, col in enumerate(cols):
                lineB.Add(col, 0, border=1,  flag=wx.EXPAND) # wx.ALIGN_CENTER|
                if ci % 2 == 1 and ci < len(cols)-1:
                    lineB.AddSpacer(self.getSpcWnTwo()) #, userData={"where": "it"})                    
            innerBox.Add(lineB, 0, border=1,  flag= wx.ALIGN_CENTER)
        
    def prepareProcesses(self):
        self.processes_map = {"E*": {"label": "Expand", "legend": "Expand the current redescription.",
                                     "more": None, "more_dyn":[], "order": 0},
                              "EL": {"label": "Expand LHS", "legend": "Expand the LHS query of the current redescription.",
                                     "more": {"side":0}, "more_dyn":[], "order":1},
                              "ER": {"label": "Expand RHS", "legend": "Expand the RHS query of the current redescription.",
                                     "more": {"side":1}, "more_dyn":[], "order":2},
                              "OL": {"label": "Overfit LHS", "legend": "Overfit LHS wrt the selected area.",
                                     "more": {"side":0, "in_weight":10}, "more_dyn":[self.view.getWeightCover], "order":3},
                              "OR": {"label": "Overfit RHS", "legend": "Overfit RHS wrt the selected area.",
                                     "more": {"side":1, "in_weight":10}, "more_dyn":[self.view.getWeightCover], "order":4} }

    def getProcessesParams(self, ppd, params=None):
        if params is None:
            params = {}
        more = self.processes_map[ppd]["more"]
        if more is not None:
            params.update(more)
        for k in self.processes_map[ppd]["more_dyn"]:
            params = k(params)
        return params

    def setRedInfo(self, red = None, details={}):
        blocks = self.infos_details
        if self.withCond():
            blocks = self.infos_details + self.infos_details_cond
        rp = Redescription.getRP()
        for det in blocks:
            if not det.get("miss", False) or (self.getParentData() is not None and self.getParentData().hasMissing()):
                if red is not None:
                    fk = det.get("fk")
                    params = self.getPltDtH().getDetailsFolds()
                    fk_all = "%s%s" % ("all", fk)
                    if params is not None:
                        fk = "%s%s" % (params["rset_id"], fk)
                    elif red.hasActiveRS():
                        fk = "%s%s" % ("active", fk)
                    else:
                        fk_all = None
                        
                    v = red.getEValGUI({"rp": rp, "k": fk, "to_str": True, "replace_none": "-"})
                    if fk_all is not None:
                        v_all = red.getEValGUI({"rp": rp, "k": fk_all, "to_str": True, "replace_none": "-"})
                        v = "%s (%s)" % (v, v_all)
                    self.info_items[det["id"]][1].SetLabel(v)
                else:
                    self.info_items[det["id"]][1].SetLabel("-")
        
    #### SEC: UPDATE
    ###########################################            
    def OnEditQuery(self, event):
        if event.GetId() in self.layout_elements["qtxt_ids"]:
            side = self.layout_elements["qtxt_ids"].index(event.GetId())
            if side > 1:
                side = -1
            self.view.updateQuery(side)
            
    def getQueryText(self, side):
        return self.layout_elements["queries_text"][side].GetValue().strip()            
        
    def updateQueryText(self, query, side):
        if query is not None:
            self.layout_elements["queries_text"][side].ChangeValue(query.disp(style="U", names=self.getParentData().getNames(side), fmts=self.getParentData().getFmts(side)))

    def updateText(self, red=None):
        """ Reset red fields and info
        """
        if red is not None:
            for side in [0, 1]:
                self.updateQueryText(red.query(side), side)
                if self.withCond():
                    self.updateQueryText(red.query(-1), -1)
            self.setRedInfo(red)

