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
            self.bm, self.bm_args = self.makeBasemapProj()

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

        nbc_max = max([len(c) for c in coords[0]])
        proj_coords = [numpy.zeros((2, len(coords[0]), nbc_max+1)), []]

        for i in range(len(coords[0])):
            if bm is None:
                p0, p1 = (coords[0][i], coords[1][i])
            else:
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

    def getParallelsRange(self):
        span = float(self.bm_args["urcrnrlat"] - self.bm_args["llcrnrlat"])
        # if self.bm_args["llcrnrlat"] < self.bm_args["urcrnrlat"]:
        #     span = float(self.bm_args["urcrnrlat"] - self.bm_args["llcrnrlat"])
        # else:
        #     span = (180. - self.bm_args["llcrnrlon"]) + (self.bm_args["urcrnrlon"] + 180.)
        opts = [60, 30, 10, 5, 1]
        p = numpy.argmin(numpy.array([((span/k)-5.)**2 for k in opts]))
        step = opts[p]
        # if self.bm_args["llcrnrlon"] < self.bm_args["urcrnrlon"]:
        return numpy.arange(int(self.bm_args["llcrnrlat"]/step)*step, (int(self.bm_args["urcrnrlat"]/step)+1)*step, step)
        # else:
        #     return numpy.concatenate([numpy.arange(int(self.bm_args["llcrnrlon"]/step)*step, (int(180./step)+1)*step, step),
        #                                   numpy.arange(int(-180./step)*step, (int(self.bm_args["urcrnrlon"]/step)+1)*step, step)])

        
    def getMeridiansRange(self):
        if self.bm_args["llcrnrlon"] < self.bm_args["urcrnrlon"]:
            span = float(self.bm_args["urcrnrlon"] - self.bm_args["llcrnrlon"])
        else:
            span = (180. - self.bm_args["llcrnrlon"]) + (self.bm_args["urcrnrlon"] + 180.)
        opts = [60, 30, 10, 5, 1]
        p = numpy.argmin(numpy.array([((span/k)-5.)**2 for k in opts]))
        step = opts[p]
        if self.bm_args["llcrnrlon"] < self.bm_args["urcrnrlon"]:
            return numpy.arange(int(self.bm_args["llcrnrlon"]/step)*step, (int(self.bm_args["urcrnrlon"]/step)+1)*step, step)
        else:
            return numpy.concatenate([numpy.arange(int(self.bm_args["llcrnrlon"]/step)*step, (int(180./step)+1)*step, step),
                                          numpy.arange(int(-180./step)*step, (int(self.bm_args["urcrnrlon"]/step)+1)*step, step)])

    def makeBasemapProj(self):
        proj, resolution = self.getBasemapProjSetts()
        if proj is None:
            return None, None
        coords = ["llon", "ulon", "llat", "ulat"]
        mbounds = {}
        allundef = True
        ## try_bounds = {"llon": -30., "ulon": 30., "llat": 30., "ulat": 110.}
        cust_bounds = {"llon": -180., "ulon": 180., "llat": -90., "ulat": 90.}
        for c in coords:
            mbounds["c"+c] = self.parent.dw.getPreferences()[c]["data"]
            ## mbounds["c"+c] = try_bounds[c] #self.parent.dw.getPreferences()[c]["data"]
            allundef &=  (mbounds["c"+c] == -1)
        if allundef:
            mbounds = cust_bounds
        else:
            mbounds["llon"], mbounds["ulon"], mbounds["llat"], mbounds["ulat"] = self.parent.dw.getCoordsExtrema()
            for coord in ["llon", "ulon", "llat", "ulat"]:
                if numpy.abs(mbounds["c"+coord]) <= 180: #numpy.abs(cust_bounds[coord]):
                    mbounds[coord] = mbounds["c"+coord]
            
        llon, ulon, llat, ulat = (mbounds["llon"], mbounds["ulon"], mbounds["llat"], mbounds["ulat"])
        ## print "Org", llon, ulon, llat, ulat
        blon, blat = (ulon-llon)/self.marg_f, (ulat-llat)/self.marg_f
        # blon, blat = 0.,0.
        ## proj = "cass"
        # circ_equ=2*numpy.pi*6378137.
        # circ_pol=2*numpy.pi*6356752.
        # circ_avg=2*numpy.pi*6371000.
        circ_def=2*numpy.pi*6370997.

        llcrnrlon = numpy.max([-180., llon-blon])
        urcrnrlon = numpy.min([180., ulon+blon])
        if urcrnrlon <= llcrnrlon:
            if "width" in self.proj_pk[proj]:
                span_lon = (360+urcrnrlon-llcrnrlon)
            else:
                urcrnrlon = cust_bounds["ulon"]
                llcrnrlon = cust_bounds["llon"]
                span_lon = (urcrnrlon-llcrnrlon)
        else:
            span_lon = (urcrnrlon-llcrnrlon)

        lon_0 = llcrnrlon + span_lon/2.0
        if lon_0 > 180:
            lon_0 -= 360

            
        llcrnrlat = numpy.max([-90., llat-blat])
        urcrnrlat = numpy.min([90., ulat+blat])
        if urcrnrlat <= llcrnrlat:
            urcrnrlat = cust_bounds["ulat"]
            llcrnrlat = cust_bounds["llat"]
        if "width" in self.proj_pk[proj]:
            llcrnrlatT = numpy.max([-180., llat-blat])
            urcrnrlatT = numpy.min([180., ulat+blat])
        else:
            llcrnrlatT = llcrnrlat
            urcrnrlatT = urcrnrlat 
        span_lat = (urcrnrlatT-llcrnrlatT)
        lat_0 = llcrnrlatT + span_lat/2.0
        if numpy.abs(lat_0) > 90:
            lat_0 = numpy.sign(lat_0)*(180 - numpy.abs(lat_0))
        
        height = span_lat/360.
        if numpy.sign(urcrnrlat) == numpy.sign(llcrnrlat):
            width = numpy.cos((numpy.pi/2.)*numpy.min([numpy.abs(urcrnrlat),numpy.abs(llcrnrlat)])/90.)*span_lon/360.
        else: ### contains equator, the largest, factor 1
            width = span_lon/360.
        ## print "Corners", (llcrnrlon, llcrnrlat), (urcrnrlon, urcrnrlat)
        # print "H", height, "W", width
        args_all = {"width": circ_def*width, "height": circ_def*height,
                    "lon_0": lon_0, "lat_0": lat_0,
                    "lon_1": lon_0-20, "lat_1": lat_0-5,
                    "lon_2": lon_0+5, "lat_2": lat_0+5,
                    "llcrnrlon": llcrnrlon, "llcrnrlat": llcrnrlat,
                    "urcrnrlon": urcrnrlon, "urcrnrlat": urcrnrlat,
                    "boundinglat": llcrnrlat, 'satellite_height': 30*10**6}
        args_p = {"projection": proj, "resolution":resolution}
        for param_k in self.proj_pk[proj]:
            args_p[param_k] = args_all[param_k]
        ## print args_all
        try:
            bm = mpl_toolkits.basemap.Basemap(**args_p)
        except ValueError:
            bm = None 
        ### print "BM Corners", (bm.llcrnrlon, bm.llcrnrlat), (bm.urcrnrlon, bm.urcrnrlat)
        return bm, args_all
        
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
            
        if draws["parallels"]:
            tt = self.getParallelsRange()
            # print "parallels", tt
            bm.drawparallels(tt, linewidth=0.5, labels=[1,0,0,1])
        if draws["meridians"]:
            tt = self.getMeridiansRange()
            # print "meridians", tt
            bm.drawmeridians(tt, linewidth=0.5, labels=[0,1,1,0])

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
