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

from reremi.toolLog import Log
from reremi.classQuery import Query
from reremi.classRedescription import Redescription
from toolsComm import ProjThread, Message
from classGView import GView
from classProj import ProjFactory
from classInterObjects import MaskCreator

import pdb

class ProjView(GView):

    TID = "PRJ"
    title_str = "Projection"
    typesI = ["Var", "Reds", "Row"]
    defaultViewT = ProjFactory.defaultViewT

    @classmethod
    def getViewsDetails(tcl):
        return ProjFactory.getViewsDetails(tcl)
    
    def __init__(self, parent, vid, more=None):
        self.worker = None
        self.repbut = None
        self.parent = parent
        self.source_list = None
        self.vid = vid
        self.buttons = []
        self.highl = {}
        self.hight = {}
        self.mapFrame = wx.Frame(None, -1, "%s%s" % (self.parent.titlePref, self.title_str))
        self.panel = wx.Panel(self.mapFrame, -1)
        self.initLogger()
        self.initProject(more)
        self.drawMap()
        self.drawFrame()
        self.binds()
        self.mapFrame.Show()
        self.queries = [Query(), Query()]
        self.suppABCD = None
        self.runProject()

    def initLogger(self):
        self.logger = Log()
        self.logger.resetOut()
        self.logger.addOut({"*": 1, "progress":2, "result":1}, self.mapFrame, Message.sendMessage)
        self.logger.addOut({"error":1}, "stderr")
        self.mapFrame.Connect(-1, -1, Message.TYPES_MESSAGES['result'], self.OnMessResult)

    def getId(self):
        return (self.proj.PID, self.vid)

    def OnQuit(self, event):
        if self.proj is not None:
            self.proj.kill()
            if self.worker is not None and self.worker.isAlive():
                self.worker._Thread__stop()
        GView.OnQuit(self, event)

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
                             "function": self.OnExpand})
        add_box.Add(self.buttons[-1]["element"], 0, border=3, flag=flags | wx.EXPAND)
        self.buttons.append({"element": wx.Button(self.mapFrame, size=(100,-1), label="Reproject"),
                             "function": self.OnReproject})
        add_box.Add(self.buttons[-1]["element"], 0, border=3, flag=flags | wx.EXPAND)
        self.repbut = self.buttons[-1]["element"]

        self.sld_sel = wx.Slider(self.mapFrame, -1, 50, 0, 100, wx.DefaultPosition, (100, -1), wx.SL_HORIZONTAL)
        v_box = wx.BoxSizer(wx.VERTICAL)
        label = wx.StaticText(self.mapFrame, wx.ID_ANY,"disabled")
        v_box.Add(label, 0, border=3, flag=flags)
        v_box.Add(self.sld_sel, 0, border=3, flag=flags)
        add_box.Add(v_box, 0, border=3, flag=flags)

        return [setts_box, add_box]

    def additionalBinds(self):
        for button in self.buttons:
            button["element"].Bind(wx.EVT_BUTTON, button["function"])
        self.sld_sel.Bind(wx.EVT_SCROLL_CHANGED, self.OnSlide)

    def OnSlide(self, event):
        self.updateMap()


    def OnReproject(self, rid=None):
        if self.worker is not None:
            return
        self.proj.initParameters(self.boxes)
        # tmp_id = self.projkeyf.GetValue().strip(":, ")
        # if (self.proj is None and len(tmp_id) > 0) or tmp_id != self.proj.getCode():
        #     self.initProject(tmp_id)
        # else:
        #     self.initProject()
        self.runProject()

    def initProject(self, rid=None):
        ### print ProjFactory.dispProjsInfo()
        self.proj = ProjFactory.getProj(self.parent.dw.getData(), rid, logger=self.logger)

    def runProject(self):
        if self.worker is None:
            self.worker = ProjThread(wx.NewId(), self.proj)
            if self.repbut is not None:
                self.repbut.Disable()
                self.repbut.SetLabel("Plz Wait...")
                      
    def OnMessResult(self, event):
        self.worker = None
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

        self.mc = MaskCreator(self.axe, None)

        self.el = Ellipse((2, -1), 0.5, 0.5)
        self.axe.add_patch(self.el)

        self.MapfigMap.canvas.mpl_connect('pick_event', self.OnPick)
        self.MapfigMap.canvas.mpl_connect('key_press_event', self.key_press_callback)

        self.MapcanvasMap.draw()
            
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
