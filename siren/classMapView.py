### TODO check which imports are needed 
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

from matplotlib.lines import Line2D

from reremi.classQuery import Query
from reremi.classRedescription import Redescription
from classGView import GView

import pdb

class MapView(GView):

    TID = "MAP"
    
    def getId(self):
        return (MapView.TID, self.vid)
        
    def drawMap(self):
        """ Draws the map
        """
        
        self.highl = {}
        self.points_ids = []
        self.lines = []
        self.high = []
        if self.parent.dw.getCoords() is None:
            self.coords_proj = None
            return
        self.MapfigMap = plt.figure()
        self.Mapcurr_mapi = 0
        self.MapcanvasMap = FigCanvas(self.mapFrame, -1, self.MapfigMap)
        
        self.MaptoolbarMap = NavigationToolbar(self.MapcanvasMap)

        self.MapfigMap.clear()
        llon, ulon, llat, ulat = self.parent.dw.getCoordsExtrema()
        m = Basemap(llcrnrlon=llon, llcrnrlat=llat, urcrnrlon=ulon, urcrnrlat=ulat, \
                    resolution = 'c', projection = 'mill', \
                    lon_0 = llon + (ulon-llon)/2.0, \
                    lat_0 = llat + (ulat-llat)/2.04)
        self.axe = m
        m.ax = self.MapfigMap.add_axes([0, 0, 1, 1])

        m.drawcoastlines(color=GView.LINES_COLOR)
        m.drawcountries(color=GView.LINES_COLOR)
        m.drawmapboundary(fill_color=GView.WATER_COLOR) 
        m.fillcontinents(color=GView.GROUND_COLOR, lake_color=GView.WATER_COLOR) #'#EEFFFF')
            #m.etopo()

        if self.parent.dw.getCoords() is not None:
            self.coords_proj = m(self.parent.dw.getCoords()[0], self.parent.dw.getCoords()[1])
            height = 3; width = 3
            self.gca = plt.gca()

        self.MapcanvasMap.draw()
            
    def updateMap(self, red = None):
        """ Redraws the map
        """

        if red is not None and self.coords_proj is not None:
            m = self.axe
            draw_settings = self.getDrawSettings()
            self.points_ids = []
            while len(self.lines):
                #plt.gca().patches.remove(self.lines.pop())
                self.gca.axes.lines.remove(self.lines.pop())
            if self.getMissDetails():
                parts = red.partsAll()
            else:
                parts = red.partsThree()
            for pi, part in enumerate(parts):
                if len(part) > 0 and draw_settings.has_key(pi):
                    lip = list(part)
                    self.points_ids.append(lip)
                    ids = np.array(lip)
                    self.lines.extend(m.plot(self.coords_proj[0][ids], self.coords_proj[1][ids],
                                             mfc=draw_settings[pi]["color_f"], mec=draw_settings[pi]["color_e"],
                                             marker=draw_settings[pi]["shape"], markersize=draw_settings[pi]["size"],
                                             linestyle='None', alpha=draw_settings[pi]["alpha"], picker=2))
                else:
                    self.lines.extend(m.plot([],[]))

            #plt.legend(('Left query only', 'Right query only', 'Both queries'), 'upper left', shadow=True, fancybox=True)
            self.MapfigMap.canvas.mpl_connect('pick_event', self.OnPick)
            self.MapcanvasMap.draw()
        return red

    def additionalElements(self):
        tmp = []
        tmp.append(self.MaptoolbarMap)
        self.buttons = []
        self.buttons.append({"element": wx.Button(self.mapFrame, size=(80,-1), label="Expand"),
                             "function": self.OnExpand})
        tmp.append(self.buttons[-1]["element"])
        return tmp

    def clearEmphasize(self, lids = None):
        if lids is None:
            lids = self.highl.keys()
        for lid in lids:
            if self.highl.has_key(lid):
                while len(self.highl[lid]) > 0:
                    self.gca.axes.lines.remove(self.highl[lid].pop())
                del self.highl[lid]
        self.MapcanvasMap.draw()

    def emphasizeLine(self, lid, colhigh='#FFFF00'):
        if self.highl.has_key(lid):
        #     self.clearEmphasize([lid])
            return

        draw_settings = self.getDrawSettings()
        scale_p = 0.1
        m = self.axe

        ids = np.array([lid])
        self.highl[lid] = []
        self.highl[lid].extend(m.plot(self.coords_proj[0][lid], self.coords_proj[1][ids],
                                      mfc=colhigh,marker=".", markersize=10,
                                      linestyle='None'))
        self.MapcanvasMap.draw()



    def OnPick(self, event):
        if isinstance(event.artist, Line2D):
            for ind in event.ind:
                si = self.points_ids[self.lines.index(event.artist)][ind]
                if si in self.high:
                    self.high.remove(si)
                    self.clearEmphasize([si])
                    self.sendHighlight(si, False)
                else:
                    self.high.append(si)
                    self.emphasizeLine(si)
                    self.sendHighlight(si, True)

                
        #     xdata = thisline.get_xdata()
        #     ydata = thisline.get_ydata()
        #     print len(xdata), len(ydata)
        #     ind = event.ind
        #     print('onpick1 line:', zip(np.take(xdata, ind), np.take(ydata, ind)))
        # return
        
        # #### TODO drafting for info on click, uncomment binding  (mpl_connect)
        # # , self.coords_proj[0][self.points_ids[ind]], self.coords_proj[1][self.points_ids[ind]]
        # inds = event.ind
        # for ind in inds:

    def sendHighlight(self, lid, turn_on=True):
        if self.source_list is not None and self.parent.tabs.has_key(self.source_list):
            self.parent.tabs[self.source_list]["tab"].sendHighlight(self.getId(), lid, turn_on)
