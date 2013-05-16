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

from reremi.classQuery import Query
from reremi.classRedescription import Redescription
from classGView import GView

import pdb

class ProjView(GView):

    TID = "PRJ"
    label_projkey=""
    
    def __init__(self, parent, vid):
        self.parent = parent
        self.source_list = None
        self.vid = vid
        self.lines = []
        self.coords_proj = None
        self.MaptoolbarMap = None
        self.projkeyf = None
        self.buttons_details = [{"function": self.OnExpand, "label": "Expand"}]
        #self.buttons_details.append({"function": self.OnReproject, "label": "Reproject"})
        self.axis_ids = [0,0]
        self.ax_labels = ["", ""]
        self.proj_id = ""
        self.mapFrame = wx.Frame(None, -1, self.parent.titleMap)
        self.panel = wx.Panel(self.mapFrame, -1)
        self.drawMap()
        self.drawFrame()
        self.binds()
        self.mapFrame.Show()
        self.queries = [Query(), Query()]
    
    def getId(self):
        return (ProjView.TID, self.vid)

    def additionalElements(self):
        addbox = wx.BoxSizer(wx.HORIZONTAL)
        lsizetxt = 90
        txt = wx.StaticText(self.mapFrame, size=(lsizetxt,-1), style=wx.ALIGN_RIGHT|wx.ALL)
        self.projkeyk = wx.NewId()
        self.projkeyf = wx.TextCtrl(self.mapFrame, self.projkeyk, style=wx.TE_PROCESS_ENTER)
        self.rep_button = wx.Button(self.mapFrame, size=(80,-1), label="Reproject")
        flags = wx.ALL        
        addbox.Add(txt, 0, border=0, flag=flags)
        addbox.Add(self.projkeyf, 0, border=0, flag=flags)
        addbox.Add(self.rep_button, 0, border=0, flag=flags)

        txt.SetLabel(self.label_projkey)
        self.projkeyf.ChangeValue(self.proj_id)
        return [addbox]

    def additionalBinds(self):
        self.rep_button.Bind(wx.EVT_BUTTON, self.OnReproject)

    def OnReproject(self, rid=None):
        tmp_id = self.projkeyf.GetValue().strip()
        if tmp_id != self.proj_id:
            self.project(tmp_id)
        else:
            self.project()
        red = Redescription.fromQueriesPair(self.queries, self.parent.dw.data)
        self.updateMap(red)

    def project(self, rid=None):
        totcols = self.parent.dw.getData().nbCols(0)+self.parent.dw.getData().nbCols(1)

        for axi in [0,1]:
            self.axis_ids[axi] = np.random.randint(self.parent.dw.getData().nbCols(0)+1, totcols)

        if rid is not None:
            tmp = re.match("^(?P<alg>[A-Z]*):(?P<par>.*)$", rid)
            if tmp is not None:
                if tmp.group("alg") == "R":
                    tmpr = re.match("^(?P<axis0>[0-9]*)-(?P<axis1>[0-9]*)$", tmp.group("par"))
                    if tmpr is not None:
                        axis0 = int(tmpr.group("axis0"))
                        axis1 = int(tmpr.group("axis1"))
                        if axis0 < totcols:
                            self.axis_ids[0] = axis0
                        if axis1 < totcols:
                            self.axis_ids[1] = axis1

        mat, details = self.parent.dw.getDataMatrix()
        for axi in [0,1]:
            self.ax_labels[axi] = "axis %d" % self.axis_ids[axi]
        self.proj_id = "R:%d-%d" % (self.axis_ids[0], self.axis_ids[1])
        self.coords_proj = (mat[self.axis_ids[0]], mat[self.axis_ids[1]])
        if self.projkeyf is not None:
            self.projkeyf.ChangeValue(self.proj_id)
#        self.coords_proj = (np.random.rand(self.parent.dw.getNbRows(),1), np.random.rand(self.parent.dw.getNbRows(),1))

        
    def drawMap(self):
        """ Draws the map
        """

        self.project()
        self.MapfigMap = plt.figure()
        self.Mapcurr_mapi = 0
        self.MapcanvasMap = FigCanvas(self.mapFrame, -1, self.MapfigMap)
        
        self.MaptoolbarMap = NavigationToolbar(self.MapcanvasMap)

        self.MapfigMap.clear()
        self.axe = self.MapfigMap.add_subplot(111)
        self.gca = plt.gca()
        self.MapcanvasMap.draw()
            
    def updateMap(self, red = None):
        """ Redraws the map
        """

        if red is not None and self.coords_proj is not None:
            m = self.axe
            m.cla()
            draw_settings = self.getDrawSettings()
            self.points_ids = []
            if self.getMissDetails():
                parts = red.partsAll()
            else:
                parts = red.partsThree()
            for pi, part in enumerate(parts):
                if len(part) > 0 and draw_settings.has_key(pi):
                    lip = list(part)
                    self.points_ids.extend(lip)
                    ids = np.array(lip)
                    m.plot(self.coords_proj[0][ids], self.coords_proj[1][ids],
                           mfc=draw_settings[pi]["color_f"], mec=draw_settings[pi]["color_e"],
                           marker=draw_settings[pi]["shape"], markersize=draw_settings[pi]["size"],
                           linestyle='None', alpha=draw_settings[pi]["alpha"], picker=3)
            m.set_xlabel(self.ax_labels[0],fontsize=12)
            m.set_ylabel(self.ax_labels[1],fontsize=12)
            #self.MapfigMap.canvas.mpl_connect('pick_event', self.OnPick)
            self.MapcanvasMap.draw()
        return red

    # def OnPick(self, event):
    #     #### TODO drafting for info on click, uncomment binding  (mpl_connect)
    #     inds = event.ind
    #     for ind in inds:
    #         print self.points_ids[ind], self.coords_proj[0][self.points_ids[ind]], self.coords_proj[1][self.points_ids[ind]]
