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
from matplotlib.patches import Ellipse, Polygon
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
        m = Basemap(llcrnrlon=llon-2, llcrnrlat=llat+2, urcrnrlon=ulon-2, urcrnrlat=ulat+2, \
                    resolution = 'c', projection = 'mill', \
                    lon_0 = llon + (ulon-llon)/2.0, \
                    lat_0 = llat + (ulat-llat)/2.04)
        self.axe = m
        m.ax = self.MapfigMap.add_axes([0, 0, 1, 1])

            #m.etopo()

        if self.parent.dw.getCoords() is not None:
            self.coords_proj = m(self.parent.dw.getCoords()[0], self.parent.dw.getCoords()[1])
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
            self.points_ids = []
            self.lines = []
            
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
                    lip = list(part)
                    ids = np.array(lip)
                    for idp in lip:
                        for ppi, p in enumerate(self.polys[idp]):
                            m.ax.add_patch(Polygon(p, closed=True, fill=True, gid="%d.%d" % (idp, ppi), picker=True,
                                                   fc=draw_settings[pi]["color_f"], ec=draw_settings[pi]["color_e"], alpha=draw_settings[pi]["alpha"]))

            #plt.legend(('Left query only', 'Right query only', 'Both queries'), 'upper left', shadow=True, fancybox=True)
            self.updateEmphasize(MapView.COLHIGH)
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
        self.highl[lid].extend(m.plot(self.coords_proj[0][lid], self.coords_proj[1][ids],
                                      mfc=colhigh,marker=".", markersize=10,
                                      linestyle='None'))


        self.hight[lid] = []
        self.hight[lid].append(m.ax.annotate('%d' % lid, xy=(self.coords_proj[0][lid], self.coords_proj[1][lid]),  xycoords='data',
                          xytext=(-10, 15), textcoords='offset points', color= draw_settings[pid]["color_e"],
                          size=10, va="center", backgroundcolor="#FFFFFF",
                          bbox=dict(boxstyle="round", facecolor="#FFFFFF", ec="gray"),
                          arrowprops=dict(arrowstyle="wedge,tail_width=1.", fc="#FFFFFF", ec="gray",
                                          patchA=None, patchB=self.el, relpos=(0.2, 0.5))
                                            ))
        self.MapcanvasMap.draw()

    def OnPick(self, event):
        if isinstance(event.artist, Polygon):
            self.sendHighlight(int(event.artist.get_gid().split(".")[0]))

    def makePolys(self, pdp, upd):
        return self.parent.dw.getPolys(pdp, upd)
