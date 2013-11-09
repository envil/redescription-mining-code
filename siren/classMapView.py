### TODO check which imports are needed 
import wx
import numpy as np
import re
# The recommended way to use wx with mpl is with the WXAgg
# backend. 
import matplotlib
#matplotlib.use('WXAgg')
import matplotlib.pyplot as plt
from matplotlib.widgets import Cursor
#from mpl_toolkits.basemap import Basemap
import mpl_toolkits.basemap
from matplotlib.backends.backend_wxagg import \
    FigureCanvasWxAgg as FigCanvas
from matplotlib.patches import Ellipse, Polygon

from reremi.classQuery import Query
from reremi.classSParts import SParts
from reremi.classRedescription import Redescription
from classGView import GView, CustToolbar
from classInterObjects import MaskCreator

import pdb

class MapView(GView):

    TID = "MAP"
    SDESC = "Map"
    title_str = "Map"
    ordN = 1
    geo = True
    MAP_POLY = True #False

    marg_f = 100.0
    proj_def = "mill"
    proj_names = {"None": None,
                  "Azimuthal Equidistant": "aeqd",
                  "Gnomonic": "gnom",
                  "Mollweide": "moll",
                  "North-Polar Lambert Azimuthal": "nplaea",
                  "Gall Stereographic Cylindrical": "gall",
                  "Miller Cylindrical": "mill",
                  "Mercator": "merc",
                  "Stereographic": "stere",
                  "North-Polar Stereographic": "npstere",
                  "Hammer": "hammer",
                  "Geostationary": "geos",
                  "Near-Sided Perspective": "nsper",
                  "van der Grinten": "vandg",
                  "Lambert Azimuthal Equal Area": "laea",
                  "McBryde-Thomas Flat-Polar Quartic": "mbtfpq",
                  "Sinusoidal": "sinu",
                  "South-Polar Stereographic": "spstere",
                  "Lambert Conformal": "lcc",
                  "Equidistant Conic": "eqdc",
                  "Cylindrical Equidistant": "cyl",
                  "Oblique Mercator": "omerc",
                  "Albers Equal Area": "aea",
                  "South-Polar Azimuthal Equidistant": "spaeqd",
                  "Orthographic": "ortho",
                  "Cassini-Soldner": "cass",
                  "Robinson": "robin"}
    
    proj_pk = {"aeqd": ["lat_0", "lon_0", "width", "height"],
               "gnom": ["lat_0", "lon_0", "width", "height"],
               "cass": ["lat_0", "lon_0", "width", "height"],
               "laea": ["lat_0", "lon_0","width", "height"],
               "stere": ["lat_0", "lon_0","width", "height"],
               "ortho": ["lat_0", "lon_0"],
               "geos": ["lon_0"],
               "vandg": ["lon_0"],
               "moll": ["lon_0"],
               "hammer": ["lon_0"],
               "robin": ["lon_0"],
               "mbtfpq": ["lon_0"],
               "sinu": ["lon_0"],
               "nsper": ["lat_0", "lon_0", "satellite_height"],
               "npstere": ["lon_0", "boundinglat"],
               "nplaea": ["lon_0", "boundinglat"],
               "cyl": ["llcrnrlat", "llcrnrlon", "urcrnrlat", "urcrnrlon"],
               "merc": ["llcrnrlat", "llcrnrlon", "urcrnrlat", "urcrnrlon"],
               "mill": ["llcrnrlat", "llcrnrlon", "urcrnrlat", "urcrnrlon"],
               "gall": ["llcrnrlat", "llcrnrlon", "urcrnrlat", "urcrnrlon"],
               "omerc": ["lat_0", "lon_0","lat_1", "lon_1", "lat_2", "lon_2","width", "height"],
               "lcc": ["lat_0", "lon_0","lat_1", "lon_1", "lat_2", "lon_2","width", "height"],
               "eqdc": ["lat_0", "lon_0", "lat_1", "lat_2","width", "height"],
               "aea": ["lat_0", "lon_0", "lat_1", "lat_2","width", "height"]}
            
    def drawMap(self):
        """ Draws the map
        """

        if self.parent.dw.getCoords() is None:
            self.coords_proj = None
            return
        
        self.MapfigMap = plt.figure()
        self.MapcanvasMap = FigCanvas(self.mapFrame, -1, self.MapfigMap)
        self.MaptoolbarMap = CustToolbar(self.MapcanvasMap, self)
        self.MapfigMap.clear()
        self.bm, args_all = self.makeBasemapProj()

        self.coords_proj = self.mapCoords(self.parent.dw.getCoords(), self.bm)
        
        self.axe = self.MapfigMap.add_axes([0, 0, 1, 1])
        if self.bm is not None:
            self.bm.ax = self.axe

        self.mc = MaskCreator(self.axe, None, buttons_t=[], callback_change=self.makeMenu)

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
            self.makeBasemapBack(self.bm)
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
                if pi != SParts.delta and pi in draw_settings and selv[idp] > 0:
                    self.drawEntity(idp, draw_settings[pi], picker=True, selv=selv[idp])

            #plt.legend(('Left query only', 'Right query only', 'Both queries'), 'upper left', shadow=True, fancybox=True)
            self.updateEmphasize(self.COLHIGH, review=False)
            self.MapcanvasMap.draw()
            self.MapfigMap.canvas.SetFocus()

    def emphasizeOn(self, lids,  colhigh='#FFFF00'):
        draw_settings = self.getDrawSettings()
        for lid in lids:
            if lid in self.highl:
                continue
            pi = self.suppABCD[lid]
            self.highl[lid] = []
            dsetts = {"shape": draw_settings[pi]["shape"],
                      "color_f": colhigh,
                      "color_e": draw_settings[pi]["color_e"],
                      "size": draw_settings[pi]["size"],
                      "alpha": draw_settings[pi]["alpha"]}
            self.highl[lid].extend(self.drawEntity(lid, dsetts, picker=self.suppABCD[lid] == SParts.delta))

            if len(lids) == 1:
                tag = self.parent.dw.data.getRName(lid)
                self.hight[lid] = []
                self.hight[lid].append(self.axe.annotate(tag, xy=(self.getCoords(0,lid)[0], self.getCoords(1,lid)[0]),  xycoords='data',
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

    def getPCoords(self):
        if self.coords_proj is None:
            return []
        return [(self.coords_proj[0][i][0], self.coords_proj[1][i][0]) for i in range(len(self.coords_proj[0]))]

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
            return [i for i,point in enumerate(self.getPCoords()) if (path.contains_point(point, radius=radius)) and (self.suppABCD[i] != SParts.delta)]
        return []

    def mapCoords(self, coords, bm=None):
        self.mapoly = self.getMapPoly() & (min([len(cs) for cs in coords[0]]) > 2)
        if bm is None:
            return coords
        proj_coords = [[],[]]
        for i in range(len(coords[0])):
            p0, p1 = bm(coords[0][i], coords[1][i])
            proj_coords[0].append([np.mean(p0)] + list(p0))
            proj_coords[1].append([np.mean(p1)] + list(p1))
        return proj_coords

    def drawPoly(self):
        return self.mapoly 

    def getMapPoly(self):
        t = self.parent.dw.getPreferences()
        try:
            mapoly = t["map_poly"]["data"] == "Yes"
        except:
            mapoly = MapView.MAP_POLY
        return mapoly

    def drawEntity(self, idp, dsetts, picker=False, selv=1):
        if picker:
            args = {"picker": dsetts["size"], "gid": "%d.%d" % (idp, 1)}
        else:
            args = {}
        if self.drawPoly():
            return [self.axe.add_patch(Polygon(zip(self.getCoords(0,idp)[1:], self.getCoords(1,idp)[1:]), closed=True, fill=True,
                                              fc=dsetts["color_f"], ec=dsetts["color_e"], alpha=dsetts["alpha"]*selv, **args))]
                    
        else:
            return self.axe.plot(self.getCoords(0,idp)[:1], self.getCoords(1,idp)[:1],
                                 mfc=dsetts["color_f"], mec=dsetts["color_e"],
                                 marker=dsetts["shape"], markersize=dsetts["size"],
                                 linestyle='None', alpha=dsetts["alpha"]*selv, **args)
        

    def getBasemapProjSetts(self):
        proj = self.proj_def 
        t = self.parent.dw.getPreferences()
        if "map_proj" in t:
            tpro = re.sub(" *\(.*\)$", "", t["map_proj"]["data"])
            if tpro in self.proj_names:
                proj = self.proj_names[tpro]
        resolution = 1
        if "map_resolution" in t:
            resolution = t["map_resolution"]["data"][0]

        return proj, resolution
            
    def getBasemapBackSetts(self):
        t = self.parent.dw.getPreferences()
#                 "states": False, "parallels": False, "meridians": False,
        draws = {"rivers": False, "coasts": False, "countries": False,
                 "states": False, "parallels": False, "meridians": False,
                 "continents":False, "lakes": False, "seas": False}
        more = {"bluemarble": 0}
        colors = {"line_color": "gray", "sea_color": "#F0F8FF", "land_color": "white", "none":"white"}

        for typ_elem in ["map_elem_area", "map_elem_natural", "map_elem_geop", "map_elem_circ"]:
            if typ_elem in t:
                for elem in t[typ_elem]["data"]:
                    draws[elem] = True

        if "bluemarble" in t:
            more["bluemarble"] = 1 - t["bluemarble"]["data"]/100.0
                
        for color_k in colors.keys():
            if color_k in t:
                colors[color_k] = "#"+"".join([ v.replace("x", "")[-2:] for v in map(hex, t[color_k]["data"])]) 
        return draws, colors, more

    def getParallelsMeridiansRange(self, parallels=True, meridians=True):
        llon, ulon, llat, ulat = self.parent.dw.getCoordsExtrema()
        if not meridians:
            wmin = ulat-llat
        elif not parallels:
            wmin = ulon-llon
        else:
            wmin = min(ulat - llat, ulon - llon)
        step = 100
        while step > 0 and wmin / step < 2: 
            step -= 10
        if step == 0:
            step = 1
        return np.arange(int(llat/step)*step,(int(ulat/step)+1)*step,step), np.arange(int(llon/step)*step,(int(ulon/step)+1)*step,step)

    def makeBasemapProj(self):
        proj, resolution = self.getBasemapProjSetts()
        if proj is None:
            return None, None
        llon, ulon, llat, ulat = self.parent.dw.getCoordsExtrema()
        blon, blat = (ulon-llon)/self.marg_f, (ulat-llat)/self.marg_f
        rsphere=6370997.0
        pi=3.1415926 
        
        width = 2*pi*rsphere*np.cos((min(abs(llon), abs(ulon))-blon)/180)*(ulat-llat+2*blat)/360
        height = 2*pi*rsphere*(ulon-llon+2*blat)/360
        lon_0 = llon + (ulon-llon)/2.0
        lat_0 = llat + (ulat-llat)/2.0
        args_all = {"width": width, "height":height,
                    "lon_0": lon_0, "lat_0": lat_0,
                    "lon_1": lon_0-20, "lat_1": lat_0-5,
                    "lon_2": lon_0+5, "lat_2": lat_0+5, 
                    "llcrnrlon": llon-blon, "llcrnrlat": llat-blat,
                    "urcrnrlon": ulon+blon, "urcrnrlat": ulat+blat,
                    "boundinglat":llat-blat, 'satellite_height': 30*10**6}
        args_p = {"projection": proj, "resolution":resolution}
        for param_k in self.proj_pk[proj]:
            args_p[param_k] = args_all[param_k]
        return mpl_toolkits.basemap.Basemap(**args_p), args_all
        
    def makeBasemapBack(self, bm=None):
        if bm is None:
            return
        draws, colors, more = self.getBasemapBackSetts()
        bounds_color, sea_color, contin_color, lake_color = colors["none"], colors["none"], colors["none"], colors["none"]
        if draws["rivers"]:
            bm.drawrivers(color=colors["sea_color"])
        if draws["coasts"]:
            bounds_color = colors["line_color"]
            bm.drawcoastlines(color=colors["line_color"])
        if draws["countries"]:
            bounds_color = colors["line_color"]
            bm.drawcountries(color=colors["line_color"])
        if draws["states"]:
            bounds_color = colors["line_color"]
            bm.drawstates(color=colors["line_color"])
        if draws["continents"]:
            contin_color = colors["land_color"]
        if draws["seas"]:
            sea_color = colors["sea_color"]
        if draws["lakes"]:
            lake_color = colors["sea_color"]

        parallels, meridians = self.getParallelsMeridiansRange(draws["parallels"], draws["meridians"]) 
        if draws["parallels"]:
            bm.drawparallels(parallels, linewidth=0.5, labels=[1,0,0,1])
        if draws["meridians"]:
            bm.drawmeridians(meridians, linewidth=0.5, labels=[1,0,0,1])

        if more["bluemarble"] > 0:
            bm.bluemarble(alpha=more["bluemarble"])
        else:
            if bounds_color != colors["none"] or sea_color != colors["none"]:
                bm.drawmapboundary(color=bounds_color, fill_color=sea_color)
            if contin_color != colors["none"] or lake_color != colors["none"] or sea_color != colors["none"]:
                bm.fillcontinents(color=contin_color, lake_color=lake_color)


