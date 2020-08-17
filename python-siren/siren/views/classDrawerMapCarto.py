import wx, numpy, re
# The recommended way to use wx with mpl is with the WXAgg backend. 
import matplotlib
matplotlib.use('WXAgg')

from matplotlib.collections import LineCollection

import matplotlib.pyplot as plt
from matplotlib.patches import Polygon
import cartopy.crs as ccrs
import cartopy.feature as cfeature

from .classDrawerBasis import DrawerEntitiesTD, DrawerBasis
from .classDrawerClust import DrawerClustTD

import pdb
    
class CartoBase:

    geodetic = ccrs.Geodetic()
    # circ_equ=2*numpy.pi*6378137.
    # circ_pol=2*numpy.pi*6356752.
    # circ_avg=2*numpy.pi*6371000.
    circ_def=2*numpy.pi*6370997.

    marg_f = 100.0
    overlay_zorder = 10
    proj_def = "Miller"    
    resolution_def = "110m" ## "10m", "50m", "110m" # 1:10 000 000, 1:50 000 000, 1:110 000 000
    map_resolutions = {"crude": "110m", "low": "110m", "intermediate": "50m", "high": "10m","full": "10m"}
    colors_def = {"line_color": "gray", "sea_color": "#F0F8FF", "land_color": "white"}
    proj_all = [# ("OSGB", ccrs.OSGB, {}), ("OSNI", ccrs.OSNI, {}), ("EuroPP", ccrs.EuroPP, {}),
                # ("UTM", ccrs.UTM, {"zone", "southern_hemisphere":False}),
                ("Plate Carree", ccrs.PlateCarree, {"central_longitude": 0.0}),
                ("Transverse Mercator", ccrs.TransverseMercator, {"central_longitude": 0.0, "central_latitude": 0.0, "false_easting": 0.0, "false_northing": 0.0, "scale_factor": 1.0}),
                ("Mercator", ccrs.Mercator, {"central_longitude": 0.0, "min_latitude": -80.0, "max_latitude": 84.0}),
                ("Lambert Cylindrical", ccrs.LambertCylindrical, {"central_longitude": 0.0}),
                ("Lambert Conformal", ccrs.LambertConformal, {"central_longitude": -96.0, "central_latitude": 39.0, "false_easting": 0.0, "false_northing": 0.0, "secant_latitudes": None, "standard_parallels": None, "cutoff": -30}),
                ("Lambert Azimuthal Equal Area", ccrs.LambertAzimuthalEqualArea, {"central_longitude": 0.0, "central_latitude": 0.0, "false_easting": 0.0, "false_northing": 0.0}),
                ("Miller", ccrs.Miller, {"central_longitude": 0.0}),
                ("Rotated Pole", ccrs.RotatedPole, {"pole_longitude": 0.0, "pole_latitude": 90.0, "central_rotated_longitude": 0.0}),
                ("Gnomonic", ccrs.Gnomonic, {"central_latitude": 0.0}),
                ("Stereographic", ccrs.Stereographic, {"central_latitude": 0.0, "central_longitude": 0.0, "false_easting": 0.0, "false_northing": 0.0, "true_scale_latitude": None}),
                ("North Polar Stereo", ccrs.NorthPolarStereo, {"central_longitude": 0.0}),
                ("South Polar Stereo", ccrs.SouthPolarStereo, {"central_longitude": 0.0}),
                ("Orthographic", ccrs.Orthographic, {"central_longitude": 0.0, "central_latitude": 0.0}),
                ("Mollweide", ccrs.Mollweide, {"central_longitude": 0}),
                ("Robinson", ccrs.Robinson, {"central_longitude": 0}),
                ("Interrupted Goode Homolosine", ccrs.InterruptedGoodeHomolosine, {"central_longitude": 0}),
                ("Geostationary", ccrs.Geostationary, {"central_longitude": 0.0, "satellite_height": 35785831, "false_easting": 0, "false_northing": 0}),
                ("Albers Equal Area", ccrs.AlbersEqualArea, {"central_longitude": 0.0, "central_latitude": 0.0, "false_easting": 0.0, "false_northing": 0.0, "standard_parallels": (20.0, 50.0)}),
                ("Azimuthal Equidistant", ccrs.AzimuthalEquidistant, {"central_longitude": 0.0, "central_latitude": 0.0, "false_easting": 0.0, "false_northing": 0.0}),
                ("Sinusoidal", ccrs.Sinusoidal, {"central_longitude": 0.0, "false_easting": 0.0, "false_northing": 0.0}),
                # ("EckertI", ccrs.EckertI, {"central_longitude": 0.0, "false_easting": 0.0, "false_northing": 0.0}),
                # ("EckertII", ccrs.EckertII, {"central_longitude": 0.0, "false_easting": 0.0, "false_northing": 0.0}),
                # ("EckertIII", ccrs.EckertIII, {"central_longitude": 0.0, "false_easting": 0.0, "false_northing": 0.0}),
                # ("EckertIV", ccrs.EckertIV, {"central_longitude": 0.0, "false_easting": 0.0, "false_northing": 0.0}),
                # ("EckertI", ccrs.EckertV, {"central_longitude": 0.0, "false_easting": 0.0, "false_northing": 0.0}),
                # ("EckertVI", ccrs.EckertVI, {"central_longitude": 0.0, "false_easting": 0.0, "false_northing": 0.0}),
                # ("Equidistant Conic", ccrs.AlbersEqualArea, {"central_longitude": 0.0, "central_latitude": 0.0, "false_easting": 0.0, "false_northing": 0.0, "standard_parallels": (20.0, 50.0)}),
                # ("Near-Sided Perspective", ccrs.Geostationary, {"central_longitude": 0.0, "central_latitude": 0.0, "satellite_height": 35785831, "false_easting": 0, "false_northing": 0}),
                # ("Equal Earth", ccrs.EqualEarth, {"central_longitude": 0.0, "false_easting": 0.0, "false_northing": 0.0}),
        ]
    proj_cls = dict([(p[0], p[1]) for p in proj_all])
    proj_pk = dict([(p[0], list(p[2].keys())) for p in proj_all])

    bounds_global = {"llon": -180., "ulon": 180., "llat": -90., "ulat": 90.}
    bounds_def = {"llon": -180., "ulon": 180., "llat": -90., "ulat": 90.}
    # https://www.naturalearthdata.com/downloads/
    ### tcl.background_zorder
    NED_features = [
      {"feature": cfeature.LAND, "what": "continents", "fcolor": "land_color", "category": "physical", "name":"land"},
      {"feature": cfeature.OCEAN, "what": "seas", "fcolor": "sea_color", "category": "physical", "name": "ocean"},
      {"feature": cfeature.LAKES, "what": "lakes", "fcolor": "sea_color", "category": "physical", "name": "lakes"},
      {"feature": cfeature.RIVERS, "what": "rivers", "ecolor": "sea_color", "category": "physical", "name": "rivers_lake_centerlines"},
      {"feature": cfeature.COASTLINE, "what": "coasts", "ecolor": "line_color", "category": "physical", "name": "coastline", "linewidth": 0.6},
      {"what": "geolines", "ecolor": "line_color", "category": "physical", "name": "geographic_lines"},        
      {"feature": cfeature.BORDERS, "what": "countries", "ecolor": "line_color", "category": "cultural", "name":"admin_0_boundary_lines_land"},
      {"what": "states", "ecolor": "line_color", "category": "cultural", "name":"admin_1_states_provinces_lines"},
      {"what": "cities", "ecolor": "line_color", "category": "cultural", "name":"populated_places"}]

    @classmethod
    def getCartoProjName(tcl, prefs):
        pro = tcl.proj_def
        if "map_proj" in prefs:
            tpro = re.sub(" *\(.*\)$", "", prefs["map_proj"]["data"])
            if tpro in tcl.proj_cls:
                pro = tpro
        return pro

    @classmethod
    def getCartoBackSetts(tcl, prefs):
        # draws_def = {"rivers": False, "coasts": False, "countries": False,
        #          "states": False, "parallels": False, "meridians": False,
        #          "continents": False, "lakes": False, "seas": False}
        colors = dict(tcl.colors_def)
        draws = {}
        more = {}

        zorder = tcl.overlay_zorder if prefs["map_lines_overlay"]["data"] else None
        resolution = tcl.resolution_def
        if "map_resolution" in prefs and prefs["map_resolution"]["data"] in tcl.map_resolutions:
            resolution = tcl.map_resolutions[prefs["map_resolution"]["data"]]
            
        for typ_elem in ["map_elem_area", "map_elem_natural", "map_elem_geop", "map_elem_circ"]:
            if typ_elem in prefs:
                for elem in prefs[typ_elem]["data"]:                    
                    draws[elem] = True
                    
        for k in ["map_back_alpha", "map_back_scale"]:
            if k in prefs:
                more[k] = prefs[k]["data"]/100.0
            else:
                more[k] = 1.
        for k in ["map_back"]:
            if k in prefs:
                more[k] = prefs[k]["value"]
            else:
                more[k] = 0
            
        for color_k in colors.keys():
            if color_k in prefs:
                colors[color_k] = "#"+"".join([ v.replace("x", "")[-2:] for v in map(hex, prefs[color_k]["data"])]) 
        return resolution, draws, colors, zorder, more

    @classmethod
    def getParallelsRange(tcl, carto_args):
        span = float(carto_args["urcrnrlat"] - carto_args["llcrnrlat"])
        opts = [60, 30, 10, 5, 1]
        p = numpy.argmin(numpy.array([((span/k)-5.)**2 for k in opts]))
        step = opts[p]
        return numpy.arange(int(carto_args["llcrnrlat"]/step)*step, (int(carto_args["urcrnrlat"]/step)+1)*step, step)

    @classmethod
    def getMeridiansRange(tcl, carto_args):
        if carto_args["llcrnrlon"] < carto_args["urcrnrlon"]:
            span = float(carto_args["urcrnrlon"] - carto_args["llcrnrlon"])
        else:
            span = (180. - carto_args["llcrnrlon"]) + (carto_args["urcrnrlon"] + 180.)
        opts = [60, 30, 10, 5, 1]
        p = numpy.argmin(numpy.array([((span/k)-5.)**2 for k in opts]))
        step = opts[p]
        if carto_args["llcrnrlon"] < carto_args["urcrnrlon"]:
            return numpy.arange(int(carto_args["llcrnrlon"]/step)*step, (int(carto_args["urcrnrlon"]/step)+1)*step, step)
        else:
            return numpy.concatenate([numpy.arange(int(carto_args["llcrnrlon"]/step)*step, (int(180./step)+1)*step, step),
                                          numpy.arange(int(-180./step)*step, (int(carto_args["urcrnrlon"]/step)+1)*step, step)])
        
    @classmethod
    def getCorners(tcl, prefs, cextrema):
        coords = ["llon", "ulon", "llat", "ulat"]
        allundef = True
        ## try_bounds = {"llon": -30., "ulon": 30., "llat": 30., "ulat": 110.}

        mbounds = dict([("c_"+c, v) for (c,v) in tcl.bounds_def.items()])
        mbounds.update(dict([("margc_"+c, 1./tcl.marg_f) for (c,v) in tcl.bounds_def.items()]))
        for c in coords:
            ### get corners from settings
            if c in prefs:
                mbounds["c_"+c] = prefs[c]["data"]
            allundef &=  (mbounds["c_"+c] == -1)
        if allundef:
            ### if all equal -1, set corners to def, globe wide
            mbounds.update(tcl.bounds_def)
        else:
            ### get corners from data
            mbounds["llon"], mbounds["ulon"], mbounds["llat"], mbounds["ulat"] = cextrema #self.getCoordsExtrema()
            for coord in coords:
                ### if corners coords from settings lower than 180,
                ### replace that from data, and drop margin
                if numpy.abs(mbounds["c_"+coord]) <= 180: #numpy.abs(tcl.bounds_def[coord]):
                    mbounds[coord] = mbounds["c_"+coord]                    
                    mbounds["margc_"+coord] = 0.

        for coord in ["lon", "lat"]:
            mbounds["marg_l"+coord] = mbounds["margc_l"+coord] * (mbounds["u"+coord]-mbounds["l"+coord]) 
            mbounds["marg_u"+coord] = mbounds["margc_u"+coord] * (mbounds["u"+coord]-mbounds["l"+coord])
        return mbounds
        
    @classmethod
    def greatCircleAngle(tcl, x0, x1):
        ### compute great circle distance for degree coordinates (lat, long)
        rd0 = numpy.radians(x0)
        rd1 = numpy.radians(x1)
        return numpy.arccos(numpy.sin(rd0[0]) * numpy.sin(rd1[0]) \
            + numpy.cos(rd0[0]) * numpy.cos(rd1[0]) * numpy.cos(rd0[1] - rd1[1]))
    @classmethod
    def greatCircleAngleXY(tcl, x0, x1):
        ### compute great circle distance for degree coordinates (x,y)
        rd0 = numpy.radians(x0)
        rd1 = numpy.radians(x1)
        return numpy.arccos(numpy.sin(rd0[1]) * numpy.sin(rd1[1]) \
            + numpy.cos(rd0[1]) * numpy.cos(rd1[1]) * numpy.cos(rd0[0] - rd1[0]))

    @classmethod
    def greatCircleDist(tcl, x0, x1):
        ### compute great circle distance for degree coordinates (lat, long)
        return tcl.circ_def * tcl.greatCircleAngle(x0, x1)
    @classmethod
    def greatCircleDistXY(tcl, x0, x1):
        ### compute great circle distance for degree coordinates (x,y)
        return tcl.circ_def * tcl.greatCircleAngleXY(x0, x1)
    
    @classmethod
    def makeCartoProj(tcl, prefs, cextrema):
        proj = CartoBase.getCartoProjName(prefs)
        if proj is None:
            return None, None, None
        mbounds = tcl.getCorners(prefs, cextrema)

        llcrnrlon = numpy.max([tcl.bounds_def["llon"], mbounds["llon"]-mbounds["marg_llon"]])
        urcrnrlon = numpy.min([tcl.bounds_def["ulon"], mbounds["ulon"]+mbounds["marg_ulon"]])
        if urcrnrlon <= llcrnrlon:
            if "central_longitude" in tcl.proj_pk[proj]:
                span_lon = (360+urcrnrlon-llcrnrlon)
            else:
                urcrnrlon = tcl.bounds_def["ulon"]
                llcrnrlon = tcl.bounds_def["llon"]
                span_lon = (urcrnrlon-llcrnrlon)
        else:
            span_lon = (urcrnrlon-llcrnrlon)

        lon_0 = llcrnrlon + span_lon/2.0
        if lon_0 > 180:
            lon_0 -= 360
            
        llcrnrlat = numpy.max([tcl.bounds_def["llat"], mbounds["llat"]-mbounds["marg_llat"]])
        urcrnrlat = numpy.min([tcl.bounds_def["ulat"], mbounds["ulat"]+mbounds["marg_ulat"]])
        if urcrnrlat <= llcrnrlat:
            urcrnrlat = tcl.bounds_def["ulat"]
            llcrnrlat = tcl.bounds_def["llat"]
        if "central_latitude" in tcl.proj_pk[proj]:
            llcrnrlatT = numpy.max([2*tcl.bounds_def["llat"], mbounds["llat"]-mbounds["marg_llat"]])
            urcrnrlatT = numpy.min([2*tcl.bounds_def["ulat"], mbounds["ulat"]+mbounds["marg_ulat"]])
        else:
            llcrnrlatT = llcrnrlat
            urcrnrlatT = urcrnrlat 
        span_lat = (urcrnrlatT-llcrnrlatT)

        lat_0 = llcrnrlatT + span_lat/2.0
        if numpy.abs(lat_0) > 90:
            lat_0 = numpy.sign(lat_0)*(180 - numpy.abs(lat_0))
        is_global = (span_lat > .95*(tcl.bounds_global["ulat"]-tcl.bounds_global["llat"])) and (span_lon > .95*(tcl.bounds_global["ulon"]-tcl.bounds_global["llon"]))
            
        args_all = {"central_longitude": lon_0, "central_latitude": lat_0,
                    # "lon_1": lon_0, "lat_1": lat_0,
                    # "lon_2": lon_0+5, "lat_2": lat_0-5, 
                    "llcrnrlon": llcrnrlon, "llcrnrlat": llcrnrlat,
                    "urcrnrlon": urcrnrlon, "urcrnrlat": urcrnrlat,
                    "satellite_height": 35785831, # 30*10**6
                    "is_global": is_global,
                    "xmin": lon_0-.525*abs(span_lon), "xmid": lon_0, "xmax": lon_0+.525*abs(span_lon),
                    "ymin": lat_0-.525*abs(span_lat), "ymid": lat_0, "ymax": lat_0+.525*abs(span_lat)}
        
        args_p = dict([(param_k, args_all[param_k]) for param_k in tcl.proj_pk[proj] if param_k in args_all])
        try:
            pcls = tcl.proj_cls[proj](**args_p)
        except ValueError:
            pcls = None 
        return pcls, proj, args_all

    @classmethod
    def makeCartoBack(tcl, prefs, carto_args, axe):
        resolution, draws, colors, zorder, more = tcl.getCartoBackSetts(prefs)

        # axe.stock_img()
        # "cross-blend-hypso", "natural-earth-1", "natural-earth-2", "ocean-bottom", "bathymetry", "shaded-relief", "gray-earth", "manual-shaded-relief", "prisma-shaded-relief"                
        # raster_resolution = resolution
        # if resolution == "110m":
        #     raster_resolution = "50m"
        # feature = cfeature.NaturalEarthFeature(category="raster", name="natural-earth-1", scale=raster_resolution)
        # axe.add_feature(feature)
            
        for feat in tcl.NED_features:
            if draws.get(feat["what"]):
                if feat.get("feature") is not None and resolution == "110m":
                    feature = feat.get("feature")
                else:
                    feature = cfeature.NaturalEarthFeature(category=feat["category"], name=feat["name"], scale=resolution)
                args = {}
                if feat.get("fcolor") in colors:
                    args["facecolor"] = colors[feat.get("fcolor")]
                if feat.get("ecolor") in colors:
                    args["edgecolor"] = colors[feat.get("ecolor")]
                    args["zorder"] = zorder
                for k,v in feat.items():
                    if k not in ["what", "feature", "category", "name", "ecolor", "fcolor"]:
                        args[k] = v
                axe.add_feature(feature, **args)
            
        if draws.get("parallels") or draws.get("meridians"):
            ylocs = tcl.getParallelsRange(carto_args)
            xlocs = tcl.getMeridiansRange(carto_args)
            axe.gridlines(color=colors["line_color"], linestyle=(0, (1, 1)), linewidth=0.5,
                      zorder=zorder,
                      xlocs=xlocs, ylocs=ylocs)

    def __init__(self, prefs, cextrema, fig=None, axe_nbr=1, axe_nbc=1, axe_idx=1):
        self.carto_proj, self.proj_name, self.carto_args = CartoBase.makeCartoProj(prefs, cextrema)
        if fig is None:
            fig = plt.figure()
        self.axe = fig.add_subplot(axe_nbr, axe_nbc, axe_idx, projection = self.carto_proj)

    def getExtent(self):
        if "xlim" in self.carto_args and "ylim" in self.carto_args:
            return (self.carto_args["xlim"][0], self.carto_args["xlim"][1], self.carto_args["ylim"][0], self.carto_args["ylim"][1])
        xx = self.axe.get_xlim()
        yy = self.axe.get_ylim()
        return (xx[0], xx[1], yy[0], yy[1])
        
    def setExtent(self, xlim=None, ylim=None):
        if xlim is not None and ylim is not None:
            self.axe.set_xlim(xlim)
            self.axe.set_ylim(ylim)
        elif "xlim" in self.carto_args and "ylim" in self.carto_args:
            self.axe.set_xlim(self.carto_args["xlim"])
            self.axe.set_ylim(self.carto_args["ylim"])
        elif self.isGlobal():
            self.axe.set_global()
        else:
            px, py = self.projPoints(numpy.array([self.carto_args["xmin"], self.carto_args["xmin"], self.carto_args["xmin"],
                                                  self.carto_args["xmid"], self.carto_args["xmid"], self.carto_args["xmid"],
                                                  self.carto_args["xmax"], self.carto_args["xmax"], self.carto_args["xmax"]]),
                                     numpy.array([self.carto_args["ymin"], self.carto_args["ymid"], self.carto_args["ymax"],
                                                  self.carto_args["ymin"], self.carto_args["ymid"], self.carto_args["ymax"],
                                                  self.carto_args["ymin"], self.carto_args["ymid"], self.carto_args["ymax"]]))
            if numpy.all(numpy.isfinite(px)) and numpy.all(numpy.isfinite(py)):
                self.axe.set_xlim([numpy.min(px), numpy.max(px)])
                self.axe.set_ylim([numpy.min(py), numpy.max(py)])
        self.carto_args["xlim"] = self.axe.get_xlim()
        self.carto_args["ylim"] = self.axe.get_ylim()
        
    def makeBack(self, prefs):
        if self.isTrueProj():
            CartoBase.makeCartoBack(prefs, self.carto_args, self.axe)
    def projPoints(self, xs, ys):
        if self.carto_proj is not None:
            if isinstance(xs, int) or isinstance(xs, float):
                pxys = self.carto_proj.transform_points(self.geodetic, numpy.array([xs]), numpy.array([ys]))
                return pxys[0,0], pxys[0,1]
            if type(xs) is list:
                pxys = self.carto_proj.transform_points(self.geodetic, numpy.array(xs), numpy.array(ys))
            else:
                pxys = self.carto_proj.transform_points(self.geodetic, xs, ys)
            return pxys[:,0], pxys[:,1]
        return xs, ys
    def reversePoints(self, xs, ys):
        if self.carto_proj is not None:
            if isinstance(xs, int) or isinstance(xs, float):
                pxys = self.geodetic.transform_points(self.carto_proj, numpy.array([xs]), numpy.array([ys]))
                return pxys[0,0], pxys[0,1]
            if type(xs) is list:
                pxys = self.geodetic.transform_points(self.carto_proj, numpy.array(xs), numpy.array(ys))
            else:
                pxys = self.geodetic.transform_points(self.carto_proj, xs, ys)
            return pxys[:,0], pxys[:,1]
        return xs, ys
    def getAxe(self):
        return self.axe
    def getProj(self):
        return self.carto_proj
    def getProjArgs(self):
        return self.carto_args
    def isTrueProj(self):
        return self.carto_proj is not None
    def isGlobal(self):
        return self.isTrueProj() and self.carto_args.get("is_global", False)
    
class DrawerMap(DrawerBasis):
    
    MAP_POLY = True    
    def initPlot(self):
        self.cb = CartoBase(self.view.getParentPreferences(), cextrema=self.getPltDtH().getCoordsExtrema(), fig=self.getFigure())
        self.getPltDtH().setBM(self.cb.projPoints)
        self.setAxe(self.cb.getAxe())
        self.cb.setExtent()
        
    def getAxisLims(self):
        if self.cb.isTrueProj():
            return self.cb.getExtent()
        xx = self.axe.get_xlim()
        yy = self.axe.get_ylim()
        return (xx[0], xx[1], yy[0], yy[1])

    def makeFinish(self, xylims=(0,1,0,1), xybs=(.1,.1)):
        self.cb.setExtent(xylims[:2], xylims[2:4])
        self.drawCondionArea()
        
    def drawCondionArea(self):
        if self.getParentData() is not None and self.getParentData().isGeoConditional():
            red = self.getPltDtH().getRed()
            if red is not None and red.hasCondition():
                qC = red.getQueryC()
                if len(qC) == 0:
                    return
                ax_lims = list(self.getAxisLims())
                cond_lims = list(self.getPltDtH().getCoordsExtrema())
                for term in qC.invTerms():
                    cid = term.colId()
                    if term.isLowbounded():
                        cond_lims[2*cid] = term.getLowb()
                    if term.isUpbounded():
                        cond_lims[2*cid+1] = term.getUpb()
                # corners = [self.getCoordXYtoP(cond_lims[xi], cond_lims[2+yi]) for xi, yi in [(0,0), (0,1), (1,1), (1,0)]]
                edges = []
                stp = 0.05
                edges.extend([self.getCoordXYtoP(cond_lims[0], cond_lims[2] + x*(cond_lims[3]-cond_lims[2])) for x in numpy.arange(0.,1., stp)])
                edges.extend([self.getCoordXYtoP(cond_lims[0] + x*(cond_lims[1]-cond_lims[0]), cond_lims[3]) for x in numpy.arange(0.,1., stp)])
                edges.extend([self.getCoordXYtoP(cond_lims[1], cond_lims[2] + x*(cond_lims[3]-cond_lims[2])) for x in numpy.arange(1., 0., -stp)])                
                edges.extend([self.getCoordXYtoP(cond_lims[0] + x*(cond_lims[1]-cond_lims[0]), cond_lims[2]) for x in numpy.arange(1., 0., -stp)])

                self.axe.add_patch(Polygon(edges, closed=True, fill=True, fc="yellow", ec="yellow", zorder=9, alpha=.3))
                # cxs, cys = zip(*corners)
                # self.axe.plot(cxs, cys, "o", color="red", zorder=10)
                # cxs, cys = zip(*edges)
                # self.axe.plot(cxs, cys, "s", color="blue", zorder=10)

                
    def makeBackground(self):
        self.cb.makeBack(self.view.getParentPreferences())

    def drawPoly(self):
        return self.getPltDtH().hasPolyCoords() & self.getSettV("map_poly", self.MAP_POLY)
    def getPosInfo(self, x, y):
        return self.cb.reversePoints(x, y)
    def getCoordXYtoP(self, x, y):
        return self.cb.projPoints(x, y)

    def getProjP(self, cpoly):
        ##### for polygons
        if not self.cb.isTrueProj():
            xs, ys, nxs, nys = zip(*cpoly)
        else:
            xs, ys = zip(*[self.cb.projPoints(x,y) for (x,y,nx,ny) in cpoly])
        return xs, ys
    def getProjT(self, edges_coords):
        ##### for multi-dimensional arrays
        if not self.cb.isTrueProj():
            edges_tensor = numpy.array([[edges_coords[:,0], edges_coords[:,2]], [edges_coords[:,1], edges_coords[:,3]]]).T
        else:
            xA, yA = self.cb.projPoints(edges_coords[:,0], edges_coords[:,1])
            xZ, yZ = self.cb.projPoints(edges_coords[:,2], edges_coords[:,3])
            edges_tensor = numpy.array([[xA, xZ], [yA, yZ]]).T
            # edges = numpy.array([zip(*self.bm(*zip(*edge.get("cut_edge", edge["edge"])))) for edge in pp_data["edges"]])
            # edges = numpy.array([zip(*self.bm(*zip(*edge["edge"]))) for edge in pp_data["edges"]])
        return edges_tensor
        
    
class DrawerEntitiesMap(DrawerMap, DrawerEntitiesTD): pass
    
class DrawerClustMap(DrawerMap, DrawerClustTD): pass
