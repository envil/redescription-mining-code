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
from matplotlib import nxutils
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

        return [setts_box, add_box]

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
        self.Mapcurr_mapi = 0
        self.MapcanvasMap = FigCanvas(self.mapFrame, -1, self.MapfigMap)
        
        self.MaptoolbarMap = NavigationToolbar(self.MapcanvasMap)

        self.MapfigMap.clear()
        self.axe = self.MapfigMap.add_subplot(111)
        self.gca = plt.gca()
        self.mc = MaskCreator(self.axe, None, self.receive_mask)
        self.el = Ellipse((2, -1), 0.5, 0.5)
        self.axe.add_patch(self.el)
        self.MapfigMap.canvas.mpl_connect('pick_event', self.OnPick)
        self.MapcanvasMap.draw()
            
    def updateMap(self, red = None):
        """ Redraws the map
        """

        if ( red is not None or self.suppABCD is not None) and self.proj is not None and self.proj.getCoords() is not None:
            self.highl = {}
            self.hight = {}
            
            m = self.axe
            m.cla()
            draw_settings = self.getDrawSettings()
            for pi in draw_settings["draw_pord"]:
                if red is not None:
                    part = red.sParts.part(pi)
                else:
                    part = [i for i,e in enumerate(self.suppABCD) if e == pi]
                if len(part) > 0 and draw_settings.has_key(pi):
                    for idp in part:
                        m.plot(self.proj.getCoords(0,idp), self.proj.getCoords(1, idp), gid="%d.%d" % (idp, 0),
                               mfc=draw_settings[pi]["color_f"], mec=draw_settings[pi]["color_e"],
                               marker=draw_settings[pi]["shape"], markersize=draw_settings[pi]["size"],
                               linestyle='None', alpha=draw_settings[pi]["alpha"], picker=3)

            if self.proj.getTitle() is not None:
                m.set_title(self.proj.getTitle(),fontsize=12)
            if self.proj.getAxisLabel(0) is not None:
                m.set_xlabel(self.proj.getAxisLabel(0),fontsize=12)
            if self.proj.getAxisLabel(1) is not None:
                m.set_ylabel(self.proj.getAxisLabel(1),fontsize=12)
            m.axis(self.proj.getAxisLims())
            self.updateEmphasize(ProjView.COLHIGH)
            self.MapcanvasMap.draw()

        return red

    def emphasizeLine(self, lid, colhigh='#FFFF00'):
        if self.highl.has_key(lid):
        #     self.clearEmphasize([lid])
            return

        draw_settings = self.getDrawSettings()
        m = self.axe
        self.highl[lid] = []
        self.highl[lid].extend(m.plot(self.proj.getCoords(0,lid), self.proj.getCoords(1,lid),
                                      mfc=colhigh,marker=".", markersize=10,
                                      linestyle='None'))

        self.hight[lid] = []
        self.hight[lid].append(m.annotate('%d' % lid, xy=(self.proj.getCoords(0,lid), self.proj.getCoords(1,lid)),  xycoords='data',
                          xytext=(-10, 15), textcoords='offset points', color= draw_settings[self.suppABCD[lid]]["color_e"],
                          size=10, va="center", backgroundcolor="#FFFFFF",
                          bbox=dict(boxstyle="round", facecolor="#FFFFFF", ec="gray"),
                          arrowprops=dict(arrowstyle="wedge,tail_width=1.", fc="#FFFFFF", ec="gray",
                                          patchA=None, patchB=self.el, relpos=(0.2, 0.5))
                                            ))
        self.MapcanvasMap.draw()

    def receive_mask(self, vertices, event=None):
        if vertices is not None and vertices.shape[0] > 3 and self.proj is not None:
            points = np.transpose((self.proj.getCoords(0), self.proj.getCoords(1)))
            mask = np.where(nxutils.points_inside_poly(points, vertices))[0]
            print mask
            # return mask.reshape(h, w)
