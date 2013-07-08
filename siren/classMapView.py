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
from matplotlib import nxutils
from matplotlib.patches import Ellipse, Polygon

from reremi.classQuery import Query
from reremi.classRedescription import Redescription
from classGView import GView
from classInterObjects import MaskCreator

import pdb

class MapView(GView):

    TID = "MAP"
    title_str = "Map"
    geo = True
    mapoly = False
    
    def getId(self):
        return (MapView.TID, self.vid)
        
    def drawMap(self):
        """ Draws the map
        """
        
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
        m = Basemap(llcrnrlon=llon-2, llcrnrlat=llat+2, urcrnrlon=ulon-2, urcrnrlat=ulat+2, \
                    resolution = 'c', projection = 'mill', \
                    lon_0 = llon + (ulon-llon)/2.0, \
                    lat_0 = llat + (ulat-llat)/2.04)
        self.axe = m
        m.ax = self.MapfigMap.add_axes([0, 0, 1, 1])

            #m.etopo()

        self.mc = MaskCreator(self.axe.ax, None, self.receive_mask)
        if self.parent.dw.getCoords() is not None:
            self.coords_proj = m(self.parent.dw.getCoords()[0], self.parent.dw.getCoords()[1])
            if self.mapoly:
                pdp = zip(range(len(self.coords_proj[0])), self.coords_proj[0], self.coords_proj[1])
                self.polys = self.makePolys(pdp, self.parent.dw.getCoords())

            height = 3; width = 3
            self.gca = plt.gca()

        self.el = Ellipse((2, -1), 0.5, 0.5)
        m.ax.add_patch(self.el)

        self.MapcanvasMap.draw()
            
    def updateMap(self, red = None):
        """ Redraws the map
        """

        if red is not None and self.coords_proj is not None:
            self.highl = {}
            self.hight = {}
            
            m = self.axe
            m.ax.cla()
            m.drawcoastlines(color=GView.LINES_COLOR)
            m.drawcountries(color=GView.LINES_COLOR)
            m.drawmapboundary(fill_color=GView.WATER_COLOR) 
            m.fillcontinents(color=GView.GROUND_COLOR, lake_color=GView.WATER_COLOR) #'#EEFFFF')

            draw_settings = self.getDrawSettings()

            if self.getMissDetails():
                parts = red.partsAll()
            else:
                parts = red.partsThree()
            for pi, part in enumerate(parts):
                if len(part) > 0 and draw_settings.has_key(pi):
                    for idp in part:
                        if self.mapoly:
                            for ppi, p in enumerate(self.polys[idp]):
                                m.ax.add_patch(Polygon(p, closed=True, fill=True, gid="%d.%d" % (idp, ppi), picker=True,
                                                       fc=draw_settings[pi]["color_f"], ec=draw_settings[pi]["color_e"],
                                                       alpha=draw_settings[pi]["alpha"]))
                                
                        else:
                            m.plot(self.coords_proj[0][idp], self.coords_proj[1][idp], gid="%d.%d" % (idp, 0),
                                   mfc=draw_settings[pi]["color_f"], mec=draw_settings[pi]["color_e"],
                                   marker=draw_settings[pi]["shape"], markersize=draw_settings[pi]["size"],
                                   linestyle='None', alpha=draw_settings[pi]["alpha"], picker=2)

            #plt.legend(('Left query only', 'Right query only', 'Both queries'), 'upper left', shadow=True, fancybox=True)
            self.updateEmphasize(MapView.COLHIGH)
            self.MapfigMap.canvas.mpl_connect('pick_event', self.OnPick)
            self.MapcanvasMap.draw()
        return red

    def additionalElements(self):
        add_box = wx.BoxSizer(wx.HORIZONTAL)
        flags = wx.ALIGN_CENTER | wx.ALL

        add_box.Add(self.MaptoolbarMap, 0, border=3, flag=flags | wx.EXPAND)
        self.buttons = []
        self.buttons.append({"element": wx.Button(self.mapFrame, size=(80,-1), label="Expand"),
                             "function": self.OnExpand})
        add_box.Add(self.buttons[-1]["element"], 0, border=3, flag=flags | wx.EXPAND)
        return [add_box]

    def emphasizeLine(self, lid, colhigh='#FFFF00'):
        if self.highl.has_key(lid):
        #     self.clearEmphasize([lid])
            return

        draw_settings = self.getDrawSettings()
        m = self.axe
        self.highl[lid] = []
        self.highl[lid].extend(m.plot(self.coords_proj[0][lid], self.coords_proj[1][lid],
                                      mfc=colhigh,marker=".", markersize=10,
                                      linestyle='None'))


        self.hight[lid] = []
        self.hight[lid].append(m.ax.annotate('%d' % lid, xy=(self.coords_proj[0][lid], self.coords_proj[1][lid]),  xycoords='data',
                          xytext=(-10, 15), textcoords='offset points', color= draw_settings[self.suppABCD[lid]]["color_e"],
                          size=10, va="center", backgroundcolor="#FFFFFF",
                          bbox=dict(boxstyle="round", facecolor="#FFFFFF", ec="gray"),
                          arrowprops=dict(arrowstyle="wedge,tail_width=1.", fc="#FFFFFF", ec="gray",
                                          patchA=None, patchB=self.el, relpos=(0.2, 0.5))
                                            ))
        self.MapcanvasMap.draw()

    def receive_mask(self, vertices, event=None):
        if vertices is not None and vertices.shape[0] > 3 and self.coords_proj is not None:
            points = np.transpose((self.coords_proj[0], self.coords_proj[1]))
            mask = np.where(nxutils.points_inside_poly(points, vertices))[0]
            print mask
            # return mask.reshape(h, w)

    def makePolys(self, pdp, upd):
        return self.parent.dw.getPolys(pdp, upd)

