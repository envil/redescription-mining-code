import wx
### from wx import ALIGN_CENTER, ALL, EXPAND, HORIZONTAL, ID_ANY, SL_HORIZONTAL, VERTICAL
### from wx import FONTFAMILY_DEFAULT, FONTSTYLE_NORMAL, FONTWEIGHT_NORMAL
### from wx import EVT_BUTTON, EVT_SCROLL_CHANGED, EVT_SCROLL_THUMBRELEASE
### from wx import BoxSizer, Button, DefaultPosition, Font, Slider, StaticText


import numpy
import re
# The recommended way to use wx with mpl is with the WXAgg
# backend. 
# import matplotlib
# matplotlib.use('WXAgg')
import matplotlib.pyplot as plt
import scipy.spatial.distance
#from mpl_toolkits.basemap import Basemap
import mpl_toolkits.basemap
from matplotlib.patches import Polygon

from ..reremi.classQuery import Query
from ..reremi.classSParts import SSetts
from ..reremi.classRedescription import Redescription
from classTDView import TDView


import pdb

class MapView(TDView):

    TID = "MAP"
    SDESC = "Map"
    title_str = "Map"
    ordN = 1
    geo = True
    MAP_POLY = True #False
    typesI = "vr"

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

        if not hasattr( self, 'axe' ):
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
            ## self.MapcanvasMap.draw()
            # self.axe = self.MapfigMap.add_axes([llon, llat, ulat-llat, ulon-llon])

            self.prepareInteractive()
            self.MapcanvasMap.draw()

            
    def additionalElements(self):
        t = self.parent.dw.getPreferences()
        
        flags = wx.ALIGN_CENTER | wx.ALL # | wx.EXPAND

        self.buttons = []
        self.buttons.append({"element": wx.Button(self.panel, size=(self.butt_w,-1), label="Expand"),
                             "function": self.OnExpandSimp})
        self.buttons[-1]["element"].SetFont(wx.Font(8, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
        
        self.sld_sel = wx.Slider(self.panel, -1, 10, 0, 100, wx.DefaultPosition, (self.sld_w, -1), wx.SL_HORIZONTAL)

        ##############################################
        add_boxB = wx.BoxSizer(wx.HORIZONTAL)
        add_boxB.AddSpacer((self.getSpacerWn()/2.,-1))

        v_box = wx.BoxSizer(wx.VERTICAL)
        label = wx.StaticText(self.panel, wx.ID_ANY,u"- opac. disabled +")
        label.SetFont(wx.Font(8, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
        v_box.Add(label, 0, border=1, flag=flags) #, userData={"where": "*"})
        v_box.Add(self.sld_sel, 0, border=1, flag=flags) #, userData={"where":"*"})
        add_boxB.Add(v_box, 0, border=1, flag=flags)

        add_boxB.AddSpacer((self.getSpacerWn(),-1))
        add_boxB.Add(self.buttons[-1]["element"], 0, border=1, flag=flags)

        add_boxB.AddSpacer((self.getSpacerWn()/2.,-1))

        #return [add_boxbis, add_box]
        return [add_boxB]

    def makeBackground(self):   
        self.makeBasemapBack(self.bm)
    def makeFinish(self, xylims, xybs):
        self.axe.axis([xylims[0], xylims[1], xylims[2], xylims[3]])

    def plotSimple(self):
        return not self.drawPoly()
    def isReadyPlot(self):
        return self.suppABCD is not None and self.getCoords() is not None    
    def getAxisLims(self):
        xx = self.axe.get_xlim()
        yy = self.axe.get_ylim()
        return (xx[0], xx[1], yy[0], yy[1])

    def getPCoords(self):
        if self.coords_proj is not None:
            return zip(*[self.coords_proj[0][0,:,0], self.coords_proj[0][1,:,0]])
        return []

    def getCoordsXY(self, id):
	if self.coords_proj is None:
            return (0,0)
	else:
            return self.coords_proj[0][:,id,0]
    def getCoords(self, axi=None, ids=None):
        if self.coords_proj is None:
            return self.coords_proj
        if axi is None:
            self.coords_proj[0][:,:,0]
        elif ids is None:
            return self.coords_proj[0][axi,:,0]
        return self.coords_proj[0][axi,ids,0]

    def getCoordsP(self, id):
        return self.coords_proj[0][:,id,1:self.coords_proj[1][id]].T

    def apply_mask(self, path, radius=0.0):
        if path is not None and self.getCoords() is not None:
            return [i for i, point in enumerate(self.getPCoords()) if (self.dots_draws["draw_dots"][i] and path.contains_point(point, radius=radius))]
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
            mapoly = t["map_poly"]["data"] == "yes"
        except:
            mapoly = MapView.MAP_POLY
        return mapoly

    def drawEntity(self, idp, fc, ec, sz=1, dsetts={}):
        if self.drawPoly():
            return [self.axe.add_patch(Polygon(self.getCoordsP(idp), closed=True, fill=True, fc=fc, ec=ec))]
                    
        else:
            ## print idp, fc, ec
            x, y = self.getCoordsXY(idp)
            return self.axe.plot(x, y, mfc=fc, mec=ec, marker=dsetts["shape"], markersize=sz, linestyle='None')

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



    def getLidAt(self, x, y):
        ids_drawn = numpy.where(self.dots_draws["draw_dots"])[0]
        d = scipy.spatial.distance.cdist(self.coords_proj[0][:, ids_drawn, 0].T, [(x,y)])
        cands = [ids_drawn[i[0]] for i in numpy.argsort(d, axis=0)[:5]]
        i = 0
        while i < len(cands):
            path = Polygon(self.getCoordsP(cands[i]), closed=True)
            if path.contains_point((x,y), radius=0.0):
                return cands[i]
            i += 1
        return None
