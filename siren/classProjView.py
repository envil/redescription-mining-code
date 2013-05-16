### TODO check which imports are needed 
import wx
import numpy as np
# The recommended way to use wx with mpl is with the WXAgg
# backend. 
import matplotlib
matplotlib.use('WXAgg')
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

    def __init__(self, parent, vid):
        self.parent = parent
        self.source_list = None
        self.vid = vid
        self.lines = []
        self.coords_proj = None
        self.MaptoolbarMap = None
        self.buttons_details = [{"function": self.OnExpand, "label": "Expand"}]
        self.buttons_details.append({"function": self.OnReproject, "label": "Reproject"})
        self.axis_ids = [0,0]
        self.ax_labels = ["", ""]
        self.mapFrame = wx.Frame(None, -1, self.parent.titleMap)
        self.panel = wx.Panel(self.mapFrame, -1)
        self.drawMap()
        self.drawFrame()
        self.binds()
        self.mapFrame.Show()
        self.queries = [Query(), Query()]
    
    def getId(self):
        return (ProjView.TID, self.vid)

    def OnReproject(self, rid=None):
        self.project()
        red = Redescription.fromQueriesPair(self.queries, self.parent.dw.data)
        self.updateMap(red)

    def project(self, rid=None):
        mat, details = self.parent.dw.getDataMatrix()
        for axi in [0,1]:
            self.axis_ids[axi] = np.random.randint(self.parent.dw.getData().nbCols(0)+1, self.parent.dw.getData().nbCols(0)+self.parent.dw.getData().nbCols(1))
            self.ax_labels[axi] = "axis %d" % self.axis_ids[axi]
        self.coords_proj = (mat[self.axis_ids[0]], mat[self.axis_ids[1]])
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
            self.MapcanvasMap.draw()
        return red

    # def OnPick(self, event):
    #     #### TODO drafting for info on click, uncomment binding  (mpl_connect)
    #     inds = event.ind
    #     for ind in inds:
    #         print self.points_ids[ind], self.coords_proj[0][self.points_ids[ind]], self.coords_proj[1][self.points_ids[ind]]
