### TODO check which imports are needed 
import re
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
from matplotlib.patches import Ellipse
from matplotlib.lines import Line2D
import matplotlib.animation as animation

from reremi.toolLog import Log
from reremi.classQuery import Query
from reremi.classRedescription import Redescription
from classGView import GView
from classProj import ProjFactory
from classInterObjects import MaskCreator

import pdb

class EProjView(GView):

    TID = "EPJ"
    ordN = 3
    what = "entities"
    title_str = "Entities Projection"
    typesI = ["Var", "Reds", "Row"]
    defaultViewT = ProjFactory.defaultView.PID + "_" + what
    wait_delay = 300

    @classmethod
    def getViewsDetails(tcl):
        return ProjFactory.getViewsDetails(tcl, what=tcl.what)
    
    def __init__(self, parent, vid, more=None):
        self.repbut = None
        self.ctrl_on = False
        self.parent = parent
        self.queries = [Query(), Query()]
        self.source_list = None
        self.vid = vid
        self.buttons = []
        self.act_butt = [1]
        self.highl = {}
        self.hight = {}
        self.mapFrame = wx.Frame(None, -1, "%s%s" % (self.parent.titlePref, self.title_str))
        self.panel = wx.Panel(self.mapFrame, -1)
        self.initProject(more)
        self.drawMap()
        self.drawFrame()
        self.binds()
        self.prepareActions()
        self.setKeys()
        self.prepareProcesses()
        self.makeMenu()
        self.mapFrame.Show()
        self.suppABCD = None
        self.runProject()

    def getId(self):
        return (self.proj.PID, self.vid)

    def additionalElements(self):
        setts_box = wx.BoxSizer(wx.HORIZONTAL)
        flags = wx.ALIGN_BOTTOM | wx.ALL

        self.boxes = self.proj.makeBoxes(self.mapFrame)
        for box in self.boxes:
            setts_box.Add(box["label"], 0, border=3, flag=flags | wx.EXPAND)
            for c in box["ctrls"]:
                setts_box.Add(c, 0, border=3, flag=flags | wx.EXPAND)

        add_box = wx.BoxSizer(wx.HORIZONTAL)
        flags = wx.ALIGN_CENTER | wx.ALL
        add_box.Add(self.MaptoolbarMap, 0, border=3, flag=flags | wx.EXPAND)
        self.buttons = []
        self.buttons.append({"element": wx.Button(self.mapFrame, size=(80,-1), label="Expand"),
                             "function": self.OnExpandSimp})
        add_box.Add(self.buttons[-1]["element"], 0, border=3, flag=flags | wx.EXPAND)
        self.buttons.append({"element": wx.Button(self.mapFrame, size=(100,-1), label="Reproject"),
                             "function": self.OnReproject})
        add_box.Add(self.buttons[-1]["element"], 0, border=3, flag=flags | wx.EXPAND)
        self.repbut = self.buttons[-1]["element"]

        self.sld_sel = wx.Slider(self.mapFrame, -1, 50, 0, 100, wx.DefaultPosition, (100, -1), wx.SL_HORIZONTAL)
        v_box = wx.BoxSizer(wx.VERTICAL)
        label = wx.StaticText(self.mapFrame, wx.ID_ANY,"-  disabled  +")
        v_box.Add(label, 0, border=3, flag=wx.ALIGN_CENTER | wx.ALL )
        v_box.Add(self.sld_sel, 0, border=3, flag=flags)
        add_box.Add(v_box, 0, border=3, flag=flags)

        return [setts_box, add_box]

    def additionalBinds(self):
        for button in self.buttons:
            button["element"].Bind(wx.EVT_BUTTON, button["function"])
        self.sld_sel.Bind(wx.EVT_SCROLL_THUMBRELEASE, self.OnSlide)
        ##self.sld_sel.Bind(wx.EVT_SCROLL_CHANGED, self.OnSlide)

    def OnSlide(self, event):
        self.updateMap()

    def OnReproject(self, rid=None):
        self.proj.initParameters(self.boxes)
        # tmp_id = self.projkeyf.GetValue().strip(":, ")
        # if (self.proj is None and len(tmp_id) > 0) or tmp_id != self.proj.getCode():
        #     self.initProject(tmp_id)
        # else:
        #     self.initProject()
        self.runProject()

    def initProject(self, rid=None):
        ### print ProjFactory.dispProjsInfo()
        self.proj = ProjFactory.getProj(self.parent.dw.getData(), rid)

    def runProject(self):
        self.init_wait()
        self.parent.project(self.proj, self.getId())
        if self.repbut is not None:
            self.repbut.Disable()
            self.repbut.SetLabel("Wait...")
                      
    def readyProj(self, proj):
        self.proj = proj
        self.kill_wait()
        self.updateMap()
        if self.repbut is not None:
            self.repbut.Enable()
            self.repbut.SetLabel("Reproject")
            
        
    def drawMap(self):
        """ Draws the map
        """
        
        self.MapfigMap = plt.figure()
        self.MapcanvasMap = FigCanvas(self.mapFrame, -1, self.MapfigMap)
        self.MaptoolbarMap = NavigationToolbar(self.MapcanvasMap)
        self.MapfigMap.clear()
        self.axe = self.MapfigMap.add_subplot(111)

        self.mc = MaskCreator(self.axe, None, buttons_t=[], callback_change=self.makeMenu)

        self.el = Ellipse((2, -1), 0.5, 0.5)
        self.axe.add_patch(self.el)

        self.MapfigMap.canvas.mpl_connect('pick_event', self.OnPick)
        self.MapfigMap.canvas.mpl_connect('key_press_event', self.key_press_callback)
        self.MapfigMap.canvas.mpl_connect('key_release_event', self.key_release_callback)

        self.MapcanvasMap.draw()

    def init_wait(self):
        self.call_wait = wx.CallLater(1, self.plot_wait)
        self.cp = 0

    def kill_wait(self):
        self.call_wait.Stop()
        self.axe.cla()
        self.axe.plot([r/10.0+0.3 for r in [1,3]], [0.5, 0.5], 's', markersize=10, mfc="#DDDDDD", mec="#DDDDDD")
        self.axe.plot([r/10.0+0.3 for r in [0,2,4]], [0.5, 0.5, 0.5], 'ks', markersize=10)
        self.axe.axis([0,1,0,1])
        self.MapcanvasMap.draw()

    def plot_wait(self):
        self.axe.cla()
        self.axe.plot([r/10.0+0.3 for r in range(5)], [0.5 for r in range(5)], 'ks', markersize=10, mfc="#DDDDDD", mec="#DDDDDD")
        self.axe.plot(((self.cp)%5)/10.0+0.3, 0.5, 'ks', markersize=10)
        self.axe.axis([0,1,0,1])
        self.MapcanvasMap.draw()
        self.cp += 1
        self.call_wait.Restart(self.wait_delay)
            
    def updateMap(self):
        """ Redraws the map
        """

        if self.suppABCD is not None and self.getCoords() is not None:
            self.highl = {}
            self.hight = {}
            
            self.axe.cla()
            draw_settings = self.getDrawSettings()

            ### SELECTED DATA
            selected = self.parent.dw.data.selectedRows()
            selp = 0.5
            if self.sld_sel is not None:
                selp = self.sld_sel.GetValue()/100.0
            selv = np.ones((self.parent.dw.data.nbRows(), 1))
            if len(selected) > 0:
                selv[np.array(list(selected))] = selp

            # for pi in draw_settings["draw_pord"]:
            #     part = [i for i,e in enumerate(self.suppABCD) if e == pi]
            #     if len(part) > 0 and draw_settings.has_key(pi):
            #         for idp in part:

            for idp, pi in enumerate(self.suppABCD):
                if draw_settings.has_key(pi) and selv[idp] > 0:

                    self.axe.plot(self.proj.getCoords(0,idp), self.proj.getCoords(1, idp), gid="%d.%d" % (idp, 1),
                           mfc=draw_settings[pi]["color_f"], mec=draw_settings[pi]["color_e"],
                           marker=draw_settings["shape"], markersize=draw_settings[pi]["size"],
                           linestyle='None', alpha=draw_settings[pi]["alpha"]*selv[idp], picker=3)

            if self.proj.getTitle() is not None:
                self.axe.set_title(self.proj.getTitle(),fontsize=12)
            if self.proj.getAxisLabel(0) is not None:
                self.axe.set_xlabel(self.proj.getAxisLabel(0),fontsize=12)
            if self.proj.getAxisLabel(1) is not None:
                self.axe.set_ylabel(self.proj.getAxisLabel(1),fontsize=12)
            self.axe.axis(self.proj.getAxisLims())
            self.updateEmphasize(self.COLHIGH, review=False)
            self.MapcanvasMap.draw()


    def getCoords(self, axi=None, ids=None):
        if self.proj is None:
            return None
        else:
            return self.proj.getCoords(axi, ids)
