### TODO check which imports are needed 
import wx
import numpy
import re
# The recommended way to use wx with mpl is with the WXAgg
# backend. 
import matplotlib
#matplotlib.use('WXAgg')
import matplotlib.pyplot as plt
import scipy.spatial.distance
from matplotlib.widgets import Cursor
#from mpl_toolkits.basemap import Basemap
import mpl_toolkits.basemap
from matplotlib.backends.backend_wxagg import \
    FigureCanvasWxAgg as FigCanvas
from matplotlib.patches import Ellipse, Polygon

from reremi.classQuery import Query
from reremi.classSParts import SSetts
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
        try:
            self.bm, args_all = self.makeBasemapProj()
        except ValueError:
            self.bm = None

        self.coords_proj = self.mapCoords(self.parent.dw.getCoords(), self.bm)
        

        if self.bm is not None:
            self.axe = self.MapfigMap.add_axes([0, 0, 1, 1])
            self.bm.ax = self.axe
        else:
            llon, ulon, llat, ulat = self.parent.dw.getCoordsExtrema()
            midlon, midlat = (llon + ulon)/2, (llat + ulat)/2
            mside = max(abs(llon-midlon), abs(llat-midlat))
            self.axe = self.MapfigMap.add_subplot(111,
                                                  xlim=[midlon-1.05*mside, midlon+1.05*mside],
                                                  ylim=[midlat-1.05*mside, midlat+1.05*mside])
            self.MapcanvasMap.draw()
            # self.axe = self.MapfigMap.add_axes([llon, llat, ulat-llat, ulon-llon])

        self.mc = MaskCreator(self.axe, None, buttons_t=[], callback_change=self.makeMenu)

        self.el = Ellipse((2, -1), 0.5, 0.5)
        self.axe.add_patch(self.el)

        self.MapfigMap.canvas.mpl_connect('pick_event', self.OnPick)
        self.MapfigMap.canvas.mpl_connect('key_press_event', self.key_press_callback)
        self.MapfigMap.canvas.mpl_connect('motion_notify_event', self.on_motion)
        self.MapcanvasMap.draw()
            
    def updateMap(self):
        """ Redraws the map
        """

        if self.suppABCD is not None and self.hasProjCoords() is not None:
            self.highl = {}
            self.hight = {}
            self.hover_access = [i for (i, v) in enumerate(self.suppABCD) if v != SSetts.delta] 
            
            self.axe.cla()
            self.makeBasemapBack(self.bm)
            draw_settings = self.getDrawSettings()

            ### SELECTED DATA
            selected = self.parent.dw.getData().selectedRows()
            selp = 0.5
            if self.sld_sel is not None:
                selp = self.sld_sel.GetValue()/100.0
            selv = numpy.ones((self.parent.dw.getData().nbRows(), 1))
            if len(selected) > 0:
                selv[numpy.array(list(selected))] = selp

            lims = self.axe.get_xlim(), self.axe.get_ylim()
            for idp, pi in enumerate(self.suppABCD):
                if pi != SSetts.delta and pi in draw_settings and selv[idp] > 0:
                    self.drawEntity(idp, draw_settings[pi], picker=True, selv=selv[idp])
            self.axe.set_xlim(lims[0])
            self.axe.set_ylim(lims[1])

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
            self.highl[lid].extend(self.drawEntity(lid, dsetts, picker=self.suppABCD[lid] == SSetts.delta))

            if len(lids) == 1:
                tag = self.parent.dw.getData().getRName(lid)
                self.hight[lid] = []
                self.hight[lid].append(self.axe.annotate(tag, xy=self.getCoordsM(lid),  xycoords='data',
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

    def hasProjCoords(self):
        return self.coords_proj is not None

    def getPCoords(self):
        if self.hasProjCoords():
            return zip(*[self.coords_proj[0][0,:,0], self.coords_proj[0][1,:,0]])
        return []

    def getCoordsM(self, id):
        return self.coords_proj[0][:,id,0]

    def getCoordsP(self, id):
        return self.coords_proj[0][:,id,1:self.coords_proj[1][id]].T

    def apply_mask(self, path, radius=0.0):
        if path is not None and self.hasProjCoords():
            return [i for i,point in enumerate(self.getPCoords()) if (path.contains_point(point, radius=radius)) and (self.suppABCD[i] != SSetts.delta)]
        return []

    def mapCoords(self, coords, bm=None):
        self.mapoly = self.getMapPoly() & (min([len(cs) for cs in coords[0]]) > 2)
        if bm is None:
            return coords
        nbc_max = max([len(c) for c in coords[0]])
        proj_coords = [numpy.zeros((2, len(coords[0]), nbc_max+1)), []]

        for i in range(len(coords[0])):
            p0, p1 = bm(coords[0][i], coords[1][i])
            proj_coords[1].append(len(p0)+1)
            proj_coords[0][0,i,0] = numpy.mean(p0)
            proj_coords[0][0,i,1:proj_coords[1][-1]] = p0
            proj_coords[0][1,i,0] = numpy.mean(p1)
            proj_coords[0][1,i,1:proj_coords[1][-1]] = p1
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
            return [self.axe.add_patch(Polygon(self.getCoordsP(idp), closed=True, fill=True,
                                              fc=dsetts["color_f"], ec=dsetts["color_e"], alpha=dsetts["alpha"]*selv, **args))]
                    
        else:
            x, y = self.getCoordsM(idp)
            return self.axe.plot(x, y,
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
        return numpy.arange(int(llat/step)*step,(int(ulat/step)+1)*step,step), numpy.arange(int(llon/step)*step,(int(ulon/step)+1)*step,step)

    def makeBasemapProj(self):
        proj, resolution = self.getBasemapProjSetts()
        if proj is None:
            return None, None
        llon, ulon, llat, ulat = self.parent.dw.getCoordsExtrema()
        blon, blat = (ulon-llon)/self.marg_f, (ulat-llat)/self.marg_f
        rsphere=6370997.0
        pi=3.1415926 
        
        width = 2*pi*rsphere*numpy.cos((min(abs(llon), abs(ulon))-blon)/180)*(ulat-llat+2*blat)/360
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


    def on_motion(self, event):
        if not self.mc.isActive():            
            lid = None
            if event.inaxes == self.axe:
                lid = self.getLidAt(event.xdata, event.ydata)
                if lid is not None and lid != self.current_hover:
                    if self.current_hover is not None:
                        emph_off = set([self.current_hover])
                    else:
                        emph_off = set()
                    self.emphasizeOnOff(turn_on=set([lid]), turn_off=emph_off, review=True)
                    self.current_hover = lid
            if lid is None and lid != self.current_hover:
                self.emphasizeOnOff(turn_on=set(), turn_off=set([self.current_hover]), review=True)
                self.current_hover = None
            # if self.ri is not None:
            #     self.drs[self.ri].do_motion(event)

    def getLidAt(self, x, y):
        d = scipy.spatial.distance.cdist(self.coords_proj[0][:,self.hover_access,0].T, [(x,y)])
        cands = [self.hover_access[i] for i in numpy.argsort(d, axis=0)[:5]]
        i = 0
        while i < len(cands):
            path = Polygon(self.getCoordsP(cands[i]), closed=True)
            if path.contains_point((x,y), radius=0.0):
                return cands[i]
            i += 1
        return None
