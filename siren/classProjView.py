### TODO check which imports are needed 
import re
import wx
import numpy as np
# The recommended way to use wx with mpl is with the WXAgg
# backend. 
import matplotlib
#matplotlib.use('WXAgg')
import matplotlib.pyplot as plt
from mpl_toolkits.basemap import Basemap
from matplotlib.backends.backend_wxagg import \
    FigureCanvasWxAgg as FigCanvas, \
    NavigationToolbar2WxAgg as NavigationToolbar
from matplotlib.patches import Ellipse
from matplotlib.lines import Line2D

from reremi.classQuery import Query
from reremi.classRedescription import Redescription
from classGView import GView
from classProj import ProjFactory, Proj

import pdb

class ProjView(GView):

    TID = "PRJ"
    label_projkey=""
    
    def __init__(self, parent, vid):
        self.parent = parent
        self.source_list = None
        self.vid = vid
        self.proj = None
        self.buttons = []
        self.highl = {}
        self.hight = {}
        self.mapFrame = wx.Frame(None, -1, self.parent.titleMap)
        self.panel = wx.Panel(self.mapFrame, -1)
        self.drawMap()
        self.drawFrame()
        self.binds()
        self.project()
        self.mapFrame.Show()
        self.queries = [Query(), Query()]

    def getId(self):
        return (ProjView.TID, self.vid)

    def additionalElements(self):
        tmp = []
        tmp.append(self.MaptoolbarMap)
        self.buttons = []
        self.buttons.append({"element": wx.Button(self.mapFrame, size=(80,-1), label="Expand"),
                             "function": self.OnExpand})
        tmp.append(self.buttons[-1]["element"])
        self.buttons.append({"element": wx.Button(self.mapFrame, size=(80,-1), label="Reproject"),
                             "function": self.OnReproject})
        tmp.append(self.buttons[-1]["element"])

        lsizetxt = 90
        txt = wx.StaticText(self.mapFrame, size=(lsizetxt,-1), style=wx.ALIGN_RIGHT|wx.ALL)
        self.projkeyf = wx.TextCtrl(self.mapFrame, wx.NewId(), style=wx.TE_PROCESS_ENTER)
        tmp.append(txt)
        tmp.append(self.projkeyf)

        txt.SetLabel(self.label_projkey)
        if self.proj is not None:
            self.projkeyf.ChangeValue(self.proj.getCode())
        return tmp

    def OnReproject(self, rid=None):
        tmp_id = self.projkeyf.GetValue().strip()
        if tmp_id != self.proj.getCode() or (self.proj is None and len(tmp_id) > 0):
            self.project(tmp_id)
        else:
            self.project()
        red = Redescription.fromQueriesPair(self.queries, self.parent.dw.getData())
        self.updateMap(red)


    def project(self, rid=None):
        self.proj = ProjFactory.getProj(self.parent.dw.getData(), rid)
        if self.projkeyf is not None:
            self.projkeyf.ChangeValue(self.proj.getCode())
        
    def drawMap(self):
        """ Draws the map
        """
        self.lines = []
        self.MapfigMap = plt.figure()
        self.Mapcurr_mapi = 0
        self.MapcanvasMap = FigCanvas(self.mapFrame, -1, self.MapfigMap)
        
        self.MaptoolbarMap = NavigationToolbar(self.MapcanvasMap)

        self.MapfigMap.clear()
        self.axe = self.MapfigMap.add_subplot(111)
        self.gca = plt.gca()

        self.el = Ellipse((2, -1), 0.5, 0.5)
        self.axe.add_patch(self.el)
        self.MapcanvasMap.draw()
            
    def updateMap(self, red = None):
        """ Redraws the map
        """

        if red is not None and self.proj is not None:
            self.highl = {}
            self.hight = {}
            self.lines = []
            self.points_ids = []
            
            m = self.axe
            m.cla()
            draw_settings = self.getDrawSettings()
            if self.getMissDetails():
                parts = red.partsAll()
            else:
                parts = red.partsThree()
            for pi, part in enumerate(parts):
                if len(part) > 0 and draw_settings.has_key(pi):
                    lip = list(part)
                    self.points_ids.append(lip)
                    ids = np.array(lip)
                    self.lines.extend(m.plot(self.proj.getCoords(0,ids), self.proj.getCoords(1, ids),
                           mfc=draw_settings[pi]["color_f"], mec=draw_settings[pi]["color_e"],
                           marker=draw_settings[pi]["shape"], markersize=draw_settings[pi]["size"],
                           linestyle='None', alpha=draw_settings[pi]["alpha"], picker=3))
                else:
                    self.lines.extend(m.plot([],[]))

            m.set_xlabel(self.proj.getAxisLabel(0),fontsize=12)
            m.set_ylabel(self.proj.getAxisLabel(1),fontsize=12)
            m.axis(self.proj.getAxisLims())
            self.updateEmphasize(ProjView.COLHIGH)
            self.MapfigMap.canvas.mpl_connect('pick_event', self.OnPick)
            self.MapcanvasMap.draw()
        return red

    def emphasizeLine(self, lid, colhigh='#FFFF00'):
        if self.highl.has_key(lid):
        #     self.clearEmphasize([lid])
            return

        draw_settings = self.getDrawSettings()
        scale_p = 0.1
        m = self.axe
        red = Redescription.fromQueriesPair(self.queries, self.parent.dw.data)
        pid = red.supports().getVectorABCD()[lid]
        ids = np.array([lid])
        self.highl[lid] = []
        self.highl[lid].extend(m.plot(self.proj.getCoords(0,ids), self.proj.getCoords(1,ids),
                                      mfc=colhigh,marker=".", markersize=10,
                                      linestyle='None'))

        self.hight[lid] = []
        self.hight[lid].append(m.annotate('%d' % lid, xy=(self.proj.getCoords(0,lid), self.proj.getCoords(1,lid)),  xycoords='data',
                          xytext=(-10, 15), textcoords='offset points', color= draw_settings[pid]["color_e"],
                          size=10, va="center", backgroundcolor="#FFFFFF",
                          bbox=dict(boxstyle="round", facecolor="#FFFFFF", ec="gray"),
                          arrowprops=dict(arrowstyle="wedge,tail_width=1.", fc="#FFFFFF", ec="gray",
                                          patchA=None, patchB=self.el, relpos=(0.2, 0.5))
                                            ))
        self.MapcanvasMap.draw()


    def OnPick(self, event):
        if isinstance(event.artist, Line2D):
            for ind in event.ind:
                si = self.points_ids[self.lines.index(event.artist)][ind]
                self.sendHighlight(si)
