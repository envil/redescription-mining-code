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
    ordN = 1
    geo = True
    MAP_POLY = True #False

    WATER_COLOR = "#FFFFFF"
    GROUND_COLOR = "#FFFFFF"
    LINES_COLOR = "gray"

            
    def drawMap(self):
        """ Draws the map
        """
        
        if self.parent.dw.getCoords() is None:
            self.coords_proj = None
            return

        self.mapoly = self.getMapPoly()
        
        self.MapfigMap = plt.figure()
        self.MapcanvasMap = FigCanvas(self.mapFrame, -1, self.MapfigMap)
        self.MaptoolbarMap = NavigationToolbar(self.MapcanvasMap)
        self.MapfigMap.clear()
        llon, ulon, llat, ulat = self.parent.dw.getCoordsExtrema()
        blon, blat = (ulon-llon)/100.0, (ulat-llat)/100.0
        self.bm = Basemap(llcrnrlon=llon-blon, llcrnrlat=llat-blat, urcrnrlon=ulon+blon, urcrnrlat=ulat+blat, \
                    resolution = 'c', projection = 'mill', \
                    lon_0 = llon + (ulon-llon)/2.0, \
                    lat_0 = llat + (ulat-llat)/2.0)
        self.bm.ax = self.MapfigMap.add_axes([0, 0, 1, 1])
        self.axe = self.bm.ax

        self.mc = MaskCreator(self.axe, None, buttons_t=[], callback_change=self.makeMenu)
        if self.parent.dw.getCoords() is not None:
            self.coords_proj = self.bm(self.parent.dw.getCoords()[0], self.parent.dw.getCoords()[1])
            if self.mapoly:
                pdp = zip(range(len(self.coords_proj[0])), self.coords_proj[0], self.coords_proj[1])
                bx, by = self.bm([llon-blon+0.001, ulon+blon-0.001], [llat-blat+0.001, ulat+blat-0.001])
                self.polys = self.makePolys(pdp, [by[1], bx[0], by[0], bx[1]])

        self.el = Ellipse((2, -1), 0.5, 0.5)
        self.axe.add_patch(self.el)

        self.MapfigMap.canvas.mpl_connect('pick_event', self.OnPick)
        self.MapfigMap.canvas.mpl_connect('key_press_event', self.key_press_callback)
        self.MapfigMap.canvas.mpl_connect('key_release_event', self.key_release_callback)
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

            ### SELECTED DATA
            selected = self.parent.dw.data.selectedRows()
            selp = 0.5
            if self.sld_sel is not None:
                selp = self.sld_sel.GetValue()/100.0
            selv = np.ones((self.parent.dw.data.nbRows(), 1))
            if len(selected) > 0:
                selv[np.array(list(selected))] = selp

            for idp, pi in enumerate(self.suppABCD):
                if pi != SParts.delta and draw_settings.has_key(pi) and selv[idp] > 0:
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
            self.MapfigMap.canvas.SetFocus()

    def emphasizeOn(self, lids,  colhigh='#FFFF00'):
        draw_settings = self.getDrawSettings()
        for lid in lids:
            if self.highl.has_key(lid):
                continue
            pi = self.suppABCD[lid]
            self.highl[lid] = []
            if self.suppABCD[lid] == SParts.delta:
                self.highl[lid].extend(self.axe.plot(self.getCoords(0,lid), self.getCoords(1,lid),
                                                     mfc=colhigh, mec=draw_settings[pi]["color_e"],
                                                     marker=draw_settings["shape"], markersize=draw_settings[pi]["size"],
                                                     markeredgewidth=1, linestyle='None', picker=2, gid="%d.%d" % (lid, 1)))

            else:
                self.highl[lid].extend(self.axe.plot(self.getCoords(0,lid), self.getCoords(1,lid),
                                                     mfc=colhigh, mec=draw_settings[pi]["color_e"],
                                                     marker=draw_settings["shape"], markersize=draw_settings[pi]["size"],
                                                     markeredgewidth=1, linestyle='None'))

            if len(lids) == 1:
                self.hight[lid] = []
                self.hight[lid].append(self.axe.annotate('%d' % lid, xy=(self.getCoords(0,lid), self.getCoords(1,lid)),  xycoords='data',
                                                     xytext=(-10, 15), textcoords='offset points', color= draw_settings[pi]["color_e"],
                                                     size=10, va="center", backgroundcolor="#FFFFFF",
                                                     bbox=dict(boxstyle="round", facecolor="#FFFFFF", ec=draw_settings[pi]["color_e"]),
                                                     arrowprops=dict(arrowstyle="wedge,tail_width=1.", fc="#FFFFFF", ec=draw_settings[pi]["color_e"],
                                                                     patchA=None, patchB=self.el, relpos=(0.2, 0.5))
                                                     ))

    def additionalElements(self):
        add_box = wx.BoxSizer(wx.HORIZONTAL)
        flags = wx.ALIGN_CENTER | wx.ALL

        add_box.Add(self.MaptoolbarMap, 0, border=3, flag=flags | wx.EXPAND)
        add_box.AddSpacer((20,-1))
        self.buttons = []
        self.buttons.append({"element": wx.Button(self.mapFrame, size=(80,-1), label="Expand"),
                             "function": self.OnExpandSimp})
        add_box.Add(self.buttons[-1]["element"], 0, border=3, flag=flags | wx.EXPAND)
        add_box.AddSpacer((20,-1))

        self.sld_sel = wx.Slider(self.mapFrame, -1, 50, 0, 100, wx.DefaultPosition, (150, -1), wx.SL_HORIZONTAL)
        v_box = wx.BoxSizer(wx.VERTICAL)
        label = wx.StaticText(self.mapFrame, wx.ID_ANY,"-  opac. disabled  +")
        v_box.Add(label, 0, border=3, flag=wx.ALIGN_CENTER | wx.ALL)
        v_box.Add(self.sld_sel, 0, border=3, flag=flags)
        add_box.Add(v_box, 0, border=3, flag=flags)

        return [add_box]

    def additionalBinds(self):
        for button in self.buttons:
            button["element"].Bind(wx.EVT_BUTTON, button["function"])
        self.sld_sel.Bind(wx.EVT_SCROLL_THUMBRELEASE, self.OnSlide)
        ##self.sld_sel.Bind(wx.EVT_SCROLL_CHANGED, self.OnSlide)

    def OnSlide(self, event):
        self.updateMap()

    def makePolys(self, pdp, boundaries):
        return self.parent.dw.getPolys(pdp, boundaries)

    def getCoords(self, axi=None, ids=None):
        if self.coords_proj is None:
            return self.coords_proj
        if axi is None:
            return self.coords_proj
        elif ids is None:
            return self.coords_proj[axi]
        return self.coords_proj[axi][ids]

    def apply_mask(self, path, radius=0.0):
        if path is not None and self.getCoords() is not None:
            points = np.transpose((self.getCoords(0), self.getCoords(1)))
            return [i for i,point in enumerate(points) if (path.contains_point(point, radius=radius)) and (self.suppABCD[i] != SParts.delta)]
        return []

    def getMapPoly(self):
        t = self.parent.dw.getPreferences()
        try:
            mapoly = t["map_poly"]["data"] == "Yes"
        except:
            mapoly = MapView.MAP_POLY
        return mapoly
