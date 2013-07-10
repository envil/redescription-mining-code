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

from reremi.classQuery import Query
from reremi.classSParts import SParts
from reremi.classRedescription import Redescription
from classGView import GView
from classInterObjects import MaskCreator

import pdb

class MapView(GView):

    TID = "MAP"
    title_str = "Map"
    geo = True
    mapoly = False

    WATER_COLOR = "#FFFFFF"
    GROUND_COLOR = "#FFFFFF"
    LINES_COLOR = "gray"

            
    def drawMap(self):
        """ Draws the map
        """
        
        if self.parent.dw.getCoords() is None:
            self.coords_proj = None
            return
        
        self.MapfigMap = plt.figure()
        self.MapcanvasMap = FigCanvas(self.mapFrame, -1, self.MapfigMap)
        self.MaptoolbarMap = NavigationToolbar(self.MapcanvasMap)
        self.MapfigMap.clear()
        llon, ulon, llat, ulat = self.parent.dw.getCoordsExtrema()
        self.bm = Basemap(llcrnrlon=llon-2, llcrnrlat=llat+2, urcrnrlon=ulon-2, urcrnrlat=ulat+2, \
                    resolution = 'c', projection = 'mill', \
                    lon_0 = llon + (ulon-llon)/2.0, \
                    lat_0 = llat + (ulat-llat)/2.04)
        self.bm.ax = self.MapfigMap.add_axes([0, 0, 1, 1])
        self.axe = self.bm.ax

        self.mc = MaskCreator(self.axe, None)
        if self.parent.dw.getCoords() is not None:
            self.coords_proj = self.bm(self.parent.dw.getCoords()[0], self.parent.dw.getCoords()[1])
            if self.mapoly:
                pdp = zip(range(len(self.coords_proj[0])), self.coords_proj[0], self.coords_proj[1])
                self.polys = self.makePolys(pdp, self.parent.dw.getCoords())

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
            self.bm.drawcoastlines(color=self.LINES_COLOR)
            self.bm.drawcountries(color=self.LINES_COLOR)
            self.bm.drawmapboundary(fill_color=self.WATER_COLOR) 
            self.bm.fillcontinents(color=self.GROUND_COLOR, lake_color=self.WATER_COLOR) #'#EEFFFF')

            draw_settings = self.getDrawSettings()
            draw_settings[SParts.delta]["alpha"] = 0

            ### SELECTED DATA
            selected = self.parent.dw.data.selectedRows()
            selp = 0.5
            if self.sld_sel is not None:
                selp = self.sld_sel.GetValue()/100.0
            selv = np.ones((self.parent.dw.data.nbRows(), 1))
            if len(selected) > 0:
                selv[np.array(list(selected))] = selp
                selv[np.array(list(selected))] = selp

            for idp, pi in enumerate(self.suppABCD):
                if draw_settings.has_key(pi) and selv[idp] > 0:
                    if self.mapoly:
                        for ppi, p in enumerate(self.polys[idp]):
                            self.axe.add_patch(Polygon(p, closed=True, fill=True, gid="%d.%d" % (idp, ppi+1), picker=True,
                                                   fc=draw_settings[pi]["color_f"], ec=draw_settings[pi]["color_e"],
                                                   alpha=draw_settings[pi]["alpha"]*selv[idp]))
                                
                    else:
                        self.bm.plot(self.getCoords(0,idp), self.getCoords(1,idp), gid="%d.%d" % (idp, 1),
                               mfc=draw_settings[pi]["color_f"], mec=draw_settings[pi]["color_e"],
                               marker=draw_settings["shape"], markersize=draw_settings[pi]["size"],
                               linestyle='None', alpha=draw_settings[pi]["alpha"]*selv[idp], picker=2)

            #plt.legend(('Left query only', 'Right query only', 'Both queries'), 'upper left', shadow=True, fancybox=True)
            self.updateEmphasize(self.COLHIGH, review=False)
            self.MapcanvasMap.draw()

    def additionalElements(self):
        add_box = wx.BoxSizer(wx.HORIZONTAL)
        flags = wx.ALIGN_CENTER | wx.ALL

        add_box.Add(self.MaptoolbarMap, 0, border=3, flag=flags | wx.EXPAND)
        self.buttons = []
        self.buttons.append({"element": wx.Button(self.mapFrame, size=(80,-1), label="Expand"),
                             "function": self.OnExpand})
        add_box.Add(self.buttons[-1]["element"], 0, border=3, flag=flags | wx.EXPAND)

        self.sld_sel = wx.Slider(self.mapFrame, -1, 50, 0, 100, wx.DefaultPosition, (100, -1), wx.SL_HORIZONTAL)
        v_box = wx.BoxSizer(wx.VERTICAL)
        label = wx.StaticText(self.mapFrame, wx.ID_ANY,"disabled")
        v_box.Add(label, 0, border=3, flag=flags)
        v_box.Add(self.sld_sel, 0, border=3, flag=flags)
        add_box.Add(v_box, 0, border=3, flag=flags)

        return [add_box]

    def additionalBinds(self):
        for button in self.buttons:
            button["element"].Bind(wx.EVT_BUTTON, button["function"])
        self.sld_sel.Bind(wx.EVT_SCROLL_CHANGED, self.OnSlide)

    def OnSlide(self, event):
        self.updateMap()

    def makePolys(self, pdp, upd):
        return self.parent.dw.getPolys(pdp, upd)

    def getCoords(self, axi=None, ids=None):
        if self.coords_proj is None:
            return self.coords_proj
        if axi is None:
            return self.coords_proj
        elif ids is None:
            return self.coords_proj[axi]
        return self.coords_proj[axi][ids]

