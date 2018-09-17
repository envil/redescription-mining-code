import codecs, re
from StringIO import StringIO
import numpy
import voronoi_poly

import pdb

IN_PACK = True
if __name__=="__main__":
    IN_PACK = False

    
TIK = "types_index"
# TYPES legend
# -----------
# outer: cut from an edge from the frame
# inner: cut from edges not from the frame
# org: from the voronoi tessalation
# frame: frame edge, external bounding box
# cut: cut edge
# isolated: part of a cell unconnected to surrounding (all edges cut)
# projected: indirectly joining existing end points
# fill: directly joining two existing end points
# residue: side of a cut edge
TYPES_MAP = {"outer": -10, "inner": -11, "org": 0, "frame": -2, "cut": 1, "isolated": 10, "projected": 20, "fill": 21, "residue": 22}
OUTER_MAP = {True: "outer", False: "inner"}

LOG_ON = False

def getFp(filename, write=False):
    fcl = False
    f = None
    if type(filename) is str or type(filename) is unicode:
        if write:
            f = open(filename, 'w')
        else:
            f = open(filename, 'rU')
        fcl = True
    elif isinstance(filename, file):
        f = filename
    else:        
        ### Because ZIPext files don't have a seek method...
        f = StringIO(filename.read())
    return f, fcl


## PLOTTING
#####################    

if IN_PACK:
    ## OFF
    def plot_edges(eids, list_edges, lbl=None, linestyle="-", marker="", color="k", linewidth=1, kedge="edge"):
        pass
    def plot_filled(eids, list_edges, lbl=None, linestyle="-", marker="", color="k", linewidth=1, kedge="edge"):
        pass
    def plot_edges_colordered(eids, list_edges, lbl=None, linestyle="-", marker="o", linewidth=1, ccolor=None, simple=False, kedge="edge"):
        pass
    def plot_esets_colordered(esets, list_edges, lbls=None, linestyle="-", marker="o", linewidth=1, simple=False, kedge="edge"):
        pass
    def plot_show(block=False):
        pass

else:
    ## ON
    import matplotlib.pyplot as plt
    import matplotlib.cm as mcm
    def plot_edges(eids, list_edges, lbl=None, linestyle="-", marker="", color="k", linewidth=1, kedge="edge"):
        for pi, pp in enumerate(eids):
            edge = get_ordered_edge(pp, list_edges, kedge=kedge)
            x, y = zip(*edge)
            plt.plot(x, y, marker=marker, color=color, linewidth=linewidth, linestyle=linestyle)
            if lbl == "IDS":
                plt.text((x[0]+x[1])/2., (y[0]+y[1])/2., "%d:%d" % (pi,pp), color=color)
            elif lbl is not None and pi == 0:
                plt.text(x[0], y[0], lbl)
    
    def plot_filled(eids, list_edges, lbl=None, linestyle="-", marker="", color="k", linewidth=1, kedge="edge"):
        fe = get_ordered_edge(eids[0], list_edges, kedge=kedge)
        points = [fe[0], fe[1]]+[get_ordered_edge(pp, list_edges, kedge=kedge)[1] for pp in eids[1:]]
        xs, ys = zip(*points)
        plt.fill(xs, ys, color=color, linewidth=linewidth, linestyle=linestyle)
        if lbl is not None and pi == 0:
            plt.text(xs[0], ys[0], lbl)
                
    def plot_edges_colordered(eids, list_edges, lbl=None, linestyle="-", marker="o", linewidth=1, ccolor=None, simple=False, kedge="edge"):
        if ccolor is None:
            color = None
            cmap = mcm.get_cmap('rainbow')
        else:
            color = ccolor
        lp = len(eids)-1.
        for pi, pp in enumerate(eids):
            if ccolor is None:
                color = cmap(pi/lp)
            edge = get_ordered_edge(pp, list_edges, kedge=kedge)
            x, y = zip(*edge)
            plt.plot(x, y, marker="", color=color, linewidth=linewidth, linestyle=linestyle)
            if not simple:
                plt.plot(x[0], y[0], marker=marker, color=color)
                plt.text((x[0]+2*x[1])/3., (y[0]+2*y[1])/3., "%d:%d" % (pi, pp))
            if lbl is not None and pi == 0:
                plt.text(x[0], y[0], lbl)
    
    def plot_esets_colordered(esets, list_edges, lbls=None, linestyle="-", marker="o", linewidth=1, simple=False, kedge="edge"):
        cmap = mcm.get_cmap('rainbow')
        lp = numpy.maximum(1., len(esets)-1.)
        for pi, pp in enumerate(esets):
            color = cmap(pi/lp)
            lbl = None
            if lbls is not None:
                lbl = lbls[pi]
            plot_edges_colordered(pp, list_edges, lbl, linestyle, marker, linewidth, color, simple, kedge=kedge)
    
    def plot_show(block=False):
        plt.show(block)
    
#######################################################

## READING
#####################
# parameters = {
#     "NAMES_CID": 0,
#     "LAT_CID": 2,
#     "LNG_CID": 1,
#     "SEP": ",",
#     "ID_INT": False
#     }

if IN_PACK:
    def read_coords_csv(filename, csv_params={}, unknown_string=None):
        return [], []
else:   
    import csv
    
    LATITUDE = ('lat', 'latitude', 'Lat', 'Latitude','lats', 'latitudes', 'Lats', 'Latitudes')
    LONGITUDE = ('long', 'longitude', 'Long', 'Longitude','longs', 'longitudes', 'Longs', 'Longitudes')
    IDENTIFIERS = ('id', 'identifier', 'Id', 'Identifier', 'ids', 'identifiers', 'Ids', 'Identifiers', 'ID', 'IDS')
    COND_COL = ('cond_var', 'cond_col', 'cond_time')
    
    
    ENABLED_ROWS = ('enabled_row', 'enabled_rows')
    ENABLED_COLS = ('enabled_col', 'enabled_cols')
    GROUPS_COLS = ('groups_col', 'groups_cols')
    
    COLVAR = ['cid', 'CID', 'cids', 'CIDS', 'variable', 'Variable', 'variables', 'Variables']
    COLVAL = ['value', 'Value', 'values', 'Values']
    
    def read_coords_csv(filename, csv_params={}, unknown_string=None):
        f, fcl = getFp(filename)
        if f is not None:
            try:
                dialect = csv.Sniffer().sniff(f.read(2048))
            except Exception:
                dialect = "excel"
            f.seek(0)
            #header = csv.Sniffer().has_header(f.read(2048))
            #f.seek(0)
            csvreader = csv.reader(f, dialect=dialect, **csv_params)
            ### Try to read headers
            head = [codecs.decode(h, 'utf-8','replace') for h in csvreader.next()]
           
            cpos = {}
            for i, h in enumerate(head):
                for clbls in [LATITUDE, LONGITUDE, IDENTIFIERS]:
                    if h in clbls:
                        cpos[clbls[0]] = i
    
            if not (LATITUDE[0] in cpos and LONGITUDE[0] in cpos):
                return None, None
            cmax = max(cpos.values())
            coords = []
            if IDENTIFIERS[0] in cpos:
                rnames = []
            else:
                rnames = None
                
            for row in csvreader:
                if re.match("\s*#", row[0]) or row[0] in ENABLED_ROWS+ENABLED_COLS+GROUPS_COLS:
                    continue
                if len(row) < cmax+1:
                    raise ValueError('number of columns does not match (is '+
                                     str(len(row))+', should be at least'+
                                     str(cmax+1)+')')

                cc = (float(row[cpos[LONGITUDE[0]]].strip()), float(row[cpos[LATITUDE[0]]].strip()))
                if cc[0] > -20 or cc[1] > -40:
                    continue
                coords.append(cc)
                # coords.append((float(row[cpos[LATITUDE[0]]].strip()), float(row[cpos[LONGITUDE[0]]].strip())))
                if rnames is not None:
                    tmp = row[cpos[IDENTIFIERS[0]]].strip()
                    if tmp != type(tmp)(unknown_string):
                        if type(tmp) is str:
                            tmp = codecs.decode(tmp, 'utf-8','replace')
                        rnames.append(tmp)
                    else:
                        rnames.append(None)        
        if fcl:
            f.close()
        return coords, rnames
#######################################################

    
            
######################################
#### PREPARING POLYGON FROM COORDS
######################################
def getInterYV(x1, y1, x2, y2, xv):
    ### get intersection of vertical line x=xv, with line going through (x1, y1) and (x2, y2)
    return y1+(xv-x1)*(y2-y1)/(x2-x1)
def getInterXH(x1, y1, x2, y2, yh):
    ### get intersection of horizontal line y=yh, with line going through (x1, y1) and (x2, y2)
    return x1+(yh-y1)*(x2-x1)/(y2-y1)

FACT_CUT = 0.8
def getCutPoint(PointsMap, edge_data, end_cut, gridHW):
    ### cut edge on end_cut
    f = FACT_CUT
    edge = edge_data["edge"]
    nA, nB = edge_data["nodes"]
    midX = (PointsMap[nA][0] + PointsMap[nB][0])/2.
    midY = (PointsMap[nA][1] + PointsMap[nB][1])/2.

    cancel = {"V": False, "H": False}
    (xv, yv) = (edge[end_cut][0], edge[end_cut][1])
    (xh, yh) = (edge[end_cut][0], edge[end_cut][1])
    if edge[end_cut][0] < edge[1-end_cut][0]: ### end to cut is to the left
        xv = midX - f*getRectW(midX, midY, gridHW)
        yv = getInterYV(edge[0][0], edge[0][1], edge[1][0], edge[1][1], xv)
    elif edge[end_cut][0] > edge[1-end_cut][0]: ### end to cut is to the right
        xv = midX + f*getRectW(midX, midY, gridHW)
        yv = getInterYV(edge[0][0], edge[0][1], edge[1][0], edge[1][1], xv)
    else: # vertical edge
        cancel["V"] = True
        # print "No horizontal intersection"
    if edge[end_cut][1] < edge[1-end_cut][1]: ### end to cut is at the bottom
        yh = midY - f*getRectH(midX, midY, gridHW)
        xh = getInterXH(edge[0][0], edge[0][1], edge[1][0], edge[1][1], yh)
    elif edge[end_cut][1] > edge[1-end_cut][1]: ### end to cut is at the top
        yh = midY + f*getRectH(midX, midY, gridHW)
        xh = getInterXH(edge[0][0], edge[0][1], edge[1][0], edge[1][1], yh)
    else: # horizontal edge
        cancel["H"] = True
        # print "No vertical intersection"

    if xv < numpy.minimum(edge[0][0], edge[1][0]) or xv > numpy.maximum(edge[0][0], edge[1][0]) or yv < numpy.minimum(edge[0][1], edge[1][1]) or yv > numpy.maximum(edge[0][1], edge[1][1]):
        (xv, yv) = (edge[end_cut][0], edge[end_cut][1])
        cancel["V"] = True
    if xh < numpy.minimum(edge[0][0], edge[1][0]) or xh > numpy.maximum(edge[0][0], edge[1][0]) or yh < numpy.minimum(edge[0][1], edge[1][1]) or yh > numpy.maximum(edge[0][1], edge[1][1]):
        (xh, yh) = (edge[end_cut][0], edge[end_cut][1])
        cancel["H"] = True
    if cancel["H"] and cancel["V"]:
        ### print "Cancel cut", nA, nB
        if edge_data["n_closer"] == end_cut:
            (xh, yh) = (edge[edge_data["n_closer"]][0], edge[edge_data["n_closer"]][1])
        else:
            (xh, yh) = ((2*edge[end_cut][0]+1*edge[1-end_cut][0])/3., (2*edge[end_cut][1]+1*edge[1-end_cut][1])/3.)
        
    dh = (xh-edge[1-end_cut][0])**2 + (yh-edge[1-end_cut][1])**2
    dv = (xv-edge[1-end_cut][0])**2 + (yv-edge[1-end_cut][1])**2
    dorg = (edge[end_cut][0]-edge[1-end_cut][0])**2 + (edge[end_cut][1]-edge[1-end_cut][1])**2
    select_cut = None    
    if dh < dorg:
        if dv < dh:
            select_cut = (xv, yv)
        else:
            select_cut = (xh, yh)
    elif dv < dorg:
        select_cut = (xv, yv)
    return select_cut

def getRectW(x, y, gridHW):
    return gridHW["W"]
def getRectH(x, y, gridHW):
    ### get height of standard edge for coordinates (x, y) 
    return gridHW["H"]
def getPolyRect(x, y, gridHW, f):
    ### get standard rectangle for coordinates (x, y) 
    w = getRectW(x, y, gridHW)
    h = getRectH(x, y, gridHW)
    return [(x+fx*f*w, y+fy*f*h) for (fx, fy) in [(1,1), (1,-1), (-1,-1), (-1,1), (1,1)]]

#### tool function
####################
def ortho_prj(x1, y1, x2, y2, xn, yn):
    xA, yA = (x2-x1, y2-y1)
    xB, yB = (xn-x1, yn-y1)
    lA = numpy.sqrt(xA**2+yA**2)
    lB = numpy.sqrt(xB**2+yB**2)
    cosA = (xA*xB+yA*yB)/(lA*lB)
    return (x1 + cosA*lB*xA/lA, y1 + cosA*lB*yA/lA)
        
def flatten_poly(poly):
    ### turn bunch of edges into polygon as ordered sequence of edges
    gpoly = {}
    map_pis = {}
    for pi, (p1, p2) in enumerate(poly):
        map_pis[(p1, p2)] = pi+1
        map_pis[(p2, p1)] = -(pi+1)
        if p1 not in gpoly:
            gpoly[p1] = [p2]
        else:
            gpoly[p1].append(p2)
        if p2 not in gpoly:
            gpoly[p2] = [p1]
        else:
            gpoly[p2].append(p1)

    ks = gpoly.keys()
    for k in ks:
        gpoly[k].sort()
            
    fps = []
    fpis = []
    prev_prev = None
    prev_reuse = False
    while len(gpoly) > 0:
        if prev_prev is not None and len(gpoly.get(prev_prev, [])) > 0:
            prev_reuse = True
            prev_node = prev_prev
            fps[-1].reverse()
            fpis[-1].reverse()
        else:
            prev_node = sorted(gpoly.keys(), key=lambda x: (-len(gpoly[x]), x))[0]
            prev_reuse = False
            prev_prev = prev_node
            fps.append([prev_node])
            fpis.append([])

        while len(gpoly[prev_node]) > 0:
            next_node = gpoly[prev_node].pop(0)
            gpoly[next_node].remove(prev_node)
            fps[-1].append(next_node)
            fpis[-1].append(map_pis[(prev_node, next_node)])
            prev_node = next_node
        ks = gpoly.keys()
        for k in ks:
            if len(gpoly[k]) == 0:
                del gpoly[k]
        # if len(gpoly) > 0:
        #     print "More than one polygon"
        #     pdb.set_trace()
        #     print gpoly
        if (len(fps[-1]) == 1) or (len(fps[-1]) == 2 and fps[-1][0] == fps[-1][1]):
            fps.pop()
            fpis.pop()
    return fps, fpis

def round_poly(poly, nb_dec=None):
    ### drop successive equal dots in polygons
    if nb_dec is None:
        return poly
    return [(numpy.around(p[0], nb_dec), numpy.around(p[1], nb_dec)) for p in poly]
def dedup_poly(poly):
    ### drop successive equal dots in polygons
    i = 1
    while i < len(poly):
        if poly[i] == poly[i-1]:
            poly.pop(i)
        else:
            i += 1
    return poly
def decomplex_poly(poly):
    ### break up loops in polygon to separate polygons
    copy_poly = list(poly)
    i = 1
    subpolys = []
    while i < len(poly):
        if poly[i] in poly[:i]:
            j = poly[:i].index(poly[i])
            tmp_poly = []
            for k in range(i, j, -1):
                tmp_poly.append(poly.pop(k))
            subpolys.append([poly[j]]+tmp_poly[::-1])
            i = j
        else:
            i += 1
    if len(poly) > 1:
        subpolys.append(poly)
    return subpolys
def clean_poly(poly):
    return decomplex_poly(dedup_poly(poly))
def smoothen_polys(polys, fact=1):
    if fact <= 1:
        return polys
    return [smoothen_poly(poly, fact) for poly in polys]
def smoothen_poly(poly, fact=1):
    if fact <= 1 or len(poly) / fact < 10:
        return poly
    return poly[:-(fact-1):fact]+[poly[-1]]



###########################################################################
def get_ordered_edge_flatten(seid, list_edges, sign=None, kedge="edge"):
    if seid == 0:
        return [0, 1, 1, 0]
    if (sign is None and seid > 0) or (sign > 0):
        return [list_edges[abs(seid)][kedge][0][0], list_edges[abs(seid)][kedge][0][1], list_edges[abs(seid)][kedge][1][0], list_edges[abs(seid)][kedge][1][1]]
    else:
        return [list_edges[abs(seid)][kedge][1][0], list_edges[abs(seid)][kedge][1][1], list_edges[abs(seid)][kedge][0][0], list_edges[abs(seid)][kedge][0][1]]
def get_ordered_edge(seid, list_edges, sign=None, kedge="edge"):
    if (sign is None and seid > 0) or (sign > 0):
        return (list_edges[abs(seid)][kedge][0], list_edges[abs(seid)][kedge][1])
    else:
        return (list_edges[abs(seid)][kedge][1], list_edges[abs(seid)][kedge][0])
def get_cut_edge(list_edges, seid, node=None, kedge="edge"):
    if "cut_eid" in list_edges[abs(seid)]:        
        ceid = list_edges[abs(seid)]["cut_eid"]
        # if ceid < 0 or seid < 0: pdb.set_trace()
        edge = get_ordered_edge(ceid, list_edges, kedge=kedge)
        if seid < 0:
            ceid *= -1
            edge = [edge[1], edge[0]]
    else:
        ceid = seid
        edge = get_ordered_edge(seid, list_edges, kedge=kedge)

    if node is not None and node not in list_edges[abs(ceid)]["nodes"]:
        list_edges[abs(ceid)]["nodes"].append(node)       
    return ceid, edge

def order_edge(prev_point, next_point=None):
    if next_point is None:
        prev_point, next_point = prev_point
    if prev_point < next_point:
        sign = 1
        new_edge = (prev_point, next_point)
    else:
        sign = -1
        new_edge = (next_point, prev_point)        
    return new_edge, sign
def update_types(list_edges, neid, type_edge=None, from_edge=False):
    if type_edge is not None:
        tte = type_edge 
        if not type(type_edge) in [list, set]:
            tte = [type_edge]
        if not from_edge:
            list_edges[neid]["types"].update(tte)
        if list_edges[0] is not None and TIK in list_edges[0]:
            for te in tte:
                assert(te in TYPES_MAP)
                if te not in list_edges[0][TIK]:
                    list_edges[0][TIK][te] = set()
                list_edges[0][TIK][te].add(neid)
def create_new_edge(prev_point,  next_point, node, map_edges, list_edges, type_edge=None, add_data={}):
    new_edge, sign = order_edge(prev_point, next_point)
    if new_edge in map_edges:
        ## if not add_force: pdb.set_trace() ### something strange
        neid = map_edges[new_edge]
    else:
        neid = len(list_edges)
        map_edges[new_edge] = neid
        list_edges.append({"edge": new_edge, "nodes": [], "pos": [], "types": set()})
    if node is not None and node not in list_edges[neid]["nodes"]:
        list_edges[neid]["nodes"].append(node)
    list_edges[neid].update(add_data)    
    update_types(list_edges, neid, type_edge)
    return sign*neid


def compute_voronoi(PointsMap, bbox_ext=None):
    ### MAIN FUNCTION for computing polygons from coordinates
    ### Compute the voronoi diagram
    #################################
    ### coordinates of the points
    sx, sy = zip(*PointsMap.values())
    bbox = (numpy.min(sx), numpy.min(sy), numpy.max(sx), numpy.max(sy))
    dbx, dby = (bbox[2] - bbox[0])/100., (bbox[3] - bbox[1])/100.
    ebbox = [bbox[0]-dbx, bbox[1]-dby, bbox[2]+dbx, bbox[3]+dby]
    if bbox_ext is not None:
        assert(bbox[0] >= bbox_ext[0])
        assert(bbox[1] >= bbox_ext[1])
        assert(bbox[2] <= bbox_ext[2])
        assert(bbox[3] <= bbox_ext[3])
        ebbox = [numpy.maximum(ebbox[0], bbox_ext[0]), numpy.maximum(ebbox[1], bbox_ext[1]),
                 numpy.minimum(ebbox[2], bbox_ext[2]), numpy.minimum(ebbox[3], bbox_ext[3])]

    #1. Stations, Lines and edges
    vl=voronoi_poly.VoronoiPolygonsMod(PointsMap, BoundingBox=[ebbox[-1]]+ebbox[:-1])

    ### Collect nodes on either side of each edge in the voronoi diagram
    map_edges = {}
    list_edges = [{"edge": None, TIK: {}, "nb_nodes": len(PointsMap)}] ## so no real edge is indexed with 0, which has no sign and does not allow marking direction 
    polys = {}
    for so, details in vl.items():
        poly_tmp = []
        pids = []
        for edge in details['obj_polygon']:
            neid = create_new_edge(edge[0], edge[1], details["info"], map_edges, list_edges, type_edge="org")
            poly_tmp.append(edge)
            pids.append(neid)
        poly, polis = flatten_poly(poly_tmp)
        assert(len(polis) == 1 and len(polis[0]) == len(poly_tmp))
        ord_pids = [pids[abs(p)-1]*numpy.sign(p) for p in polis[0]]
        polys[details["info"]] = ord_pids
        for pi, eid in enumerate(ord_pids):
            list_edges[abs(eid)]["pos"].append((pi+1)*numpy.sign(eid))                        

    ### exactly two adjacent nodes, except for border edges that have only one
    ## assert all([(len(x["nodes"])==2 or len(x["nodes"])==1) for (k,x) in map_edges.items()])
    return map_edges, list_edges, polys, ebbox

ANGLE_TOL = 0.05
def compute_edges_distances(PointsMap, list_edges):
    horz_edges = []
    vert_edges = []
    for eid in range(1, len(list_edges)):
        dt = list_edges[eid]
        if len(dt["nodes"]) == 1: ## border edge
            update_types(list_edges, eid, "frame")
            dt["far"] = -1
        else: ## other edge
            edge = dt["edge"]
            midx = numpy.abs(PointsMap[dt["nodes"][0]][0] + PointsMap[dt["nodes"][1]][0])/2.
            midy = numpy.abs(PointsMap[dt["nodes"][0]][1] + PointsMap[dt["nodes"][1]][1])/2.
            dx = numpy.abs(PointsMap[dt["nodes"][0]][0] - PointsMap[dt["nodes"][1]][0])
            dy = numpy.abs(PointsMap[dt["nodes"][0]][1] - PointsMap[dt["nodes"][1]][1])
            closer = 0
            if (midx-edge[1][0])**2+(midy-edge[1][1])**2 < (midx-edge[0][0])**2+(midy-edge[0][1])**2:
                closer = 1
            dt.update({"dx": dx, "dy": dy, "far": 0, "n_closer": closer})
            horz_edges.append(dx)
            vert_edges.append(dy)
                        
    vert_edges = numpy.array(vert_edges)
    horz_edges = numpy.array(horz_edges)
    return vert_edges, horz_edges, list_edges


def compute_grid_size(vert_edges, horz_edges, gridh_percentile=-1, gridw_percentile=-1):
    return {'H': 0.007839320868257893, 'W': 0.0078403303939800773}
    if gridh_percentile <= 0:
        gridh_percentile = 50
    if gridw_percentile <= 0:
        gridw_percentile = gridh_percentile
        
    # gridH = numpy.mean(vert_edges)
    # gridW = numpy.mean(horz_edges)
    gridH = numpy.percentile(vert_edges, gridh_percentile)
    gridW = numpy.percentile(horz_edges, gridw_percentile)
    
    gridHW = {"H": gridH, "W": gridW}
    print "GRID", gridHW
    return gridHW

def update_far(PointsMap, list_edges, gridHW):
    for eid in range(1, len(list_edges)):
        if list_edges[eid]["far"] == 0:
            dt = list_edges[eid]
            if dt["dx"] > 1.5*gridHW["W"] or dt["dy"] > 1.2*gridHW["H"]:
                dt["far"] = 1
    return list_edges

def gather_require_cut(PointsMap, map_edges, list_edges, polys):
    require_cut = {}
    polys_cut_info = {}
    isolated_nodes = []
    ## go over each node in the voronoi diagram, prepare polygon 
    for node, poly in polys.items():
        cut_info = [-int(list_edges[abs(seid)]["far"] != 0) for seid in poly]
        if numpy.sum(cut_info) == 0:  ## contains at least one edge far==0
            continue
        elif numpy.prod(cut_info) == 0:  ## contains at least one edge far==0
            ### collect edges that are not far but adjacent to far, which will need to be cut 
            for pi, seid in enumerate(poly):
                if list_edges[abs(seid)]["far"] != 0:
                    if list_edges[abs(poly[pi-1])]["far"] == 0:
                        oei = abs(poly[pi-1])
                        wend = int(numpy.sign(poly[pi-1]) > 0)
                        if oei not in require_cut:
                            require_cut[oei] = []
                        require_cut[oei].append((node, pi, wend))
                        cut_info[pi-1] = 1
    
                    aft = pi+1
                    if aft == len(poly): aft = 0
                    if list_edges[abs(poly[aft])]["far"] == 0:
                        oei = abs(poly[aft])
                        wend = int(numpy.sign(poly[aft]) < 0)
                        if oei not in require_cut:
                            require_cut[oei] = []
                        require_cut[oei].append((node, pi, wend))
                        cut_info[aft] = 1
            polys_cut_info[node] = cut_info
        else:
            isolated_nodes.append(node)
    return require_cut, polys_cut_info, isolated_nodes

def cut_edges(PointsMap, map_edges, list_edges, require_cut, gridHW):
    ## cutting edges
    recut_nodes = {}
    for ei, dt in require_cut.items():
        edge = [list_edges[ei]["edge"][0], list_edges[ei]["edge"][1]]
        end_points = set([d[-1] for d in dt])
        end_cut = []
        for end_point in end_points:
            cut_point = getCutPoint(PointsMap, list_edges[ei], end_point, gridHW)
            if cut_point is not None:
                end_cut.append(end_point)
                edge[end_point] = cut_point
        if len(end_cut) > 0:
            neid = create_new_edge(edge[0], edge[1], None, map_edges, list_edges, type_edge = ["cut", OUTER_MAP[False]])
            nodes = set([d[0] for d in dt])
            recut_n = set(list_edges[ei]["nodes"]).difference(nodes)
            for rn in recut_n:
                if rn not in recut_nodes:
                    recut_nodes[rn] = {}
                recut_nodes[rn][ei] = end_cut
        else:
            neid = ei            
        list_edges[ei]["cut_eid"] = neid            
        list_edges[abs(neid)]["uncut_eid"] = ei
    return recut_nodes

        
FACT_ALONE = 0.5
def assemble_isolated(PointsMap, map_edges, list_edges, polys, isolated_nodes, gridHW, assembled={}):
    for node in isolated_nodes:
        epoly = getPolyRect(PointsMap[node][0], PointsMap[node][1], gridHW, FACT_ALONE)
        map_to = []
        ### does it connects to the outer border?
        outer = any([list_edges[abs(k)]["far"] == -1 for k in polys[node]])
        for pi in range(len(epoly)-1):
            neid = create_new_edge(epoly[pi], epoly[pi+1], node, map_edges, list_edges, type_edge = ["isolated", OUTER_MAP[outer]])
            map_to.append(neid)
        assembled[node] = map_to
    return assembled

def clip_edge(edge, bbox):
    marg = 10**-6
    new_edge = [[edge[0][0], edge[0][1]], [edge[1][0], edge[1][1]]]
    for end_point in [0,1]:
        # if new_edge[end_point][0] < bbox[0] or new_edge[end_point][1] < bbox[1] or new_edge[end_point][0] > bbox[2] or new_edge[end_point][1] > bbox[3]:
        #     pdb.set_trace()
        if new_edge[end_point][0] < bbox[0]:
            new_edge[end_point][1] = getInterYV(new_edge[0][0], new_edge[0][1], new_edge[1][0], new_edge[1][1], bbox[0]+marg)
            new_edge[end_point][0] = bbox[0]+marg
        if new_edge[end_point][1] < bbox[1]:
            new_edge[end_point][0] = getInterXH(new_edge[0][0], new_edge[0][1], new_edge[1][0], new_edge[1][1], bbox[1]+marg)
            new_edge[end_point][1] = bbox[1]+marg
        if new_edge[end_point][0] > bbox[2]:
            new_edge[end_point][1] = getInterYV(new_edge[0][0], new_edge[0][1], new_edge[1][0], new_edge[1][1], bbox[2]-marg)
            new_edge[end_point][0] = bbox[2]-marg            
        if new_edge[end_point][1] > bbox[3]:
            new_edge[end_point][0] = getInterXH(new_edge[0][0], new_edge[0][1], new_edge[1][0], new_edge[1][1], bbox[3]-marg)
            new_edge[end_point][1] = bbox[3]-marg            
    return ((new_edge[0][0], new_edge[0][1]), (new_edge[1][0], new_edge[1][1]))

def getInterYV(x1, y1, x2, y2, xv):
    ### get intersection of vertical line x=xv, with line going through (x1, y1) and (x2, y2)
    return y1+(xv-x1)*(y2-y1)/(x2-x1)
def getInterXH(x1, y1, x2, y2, yh):
    ### get intersection of horizontal line y=yh, with line going through (x1, y1) and (x2, y2)
    return x1+(yh-y1)*(x2-x1)/(y2-y1)

            
    return edge

def assemble_cut(PointsMap, map_edges, list_edges, polys, polys_cut_info, recut_nodes, assembled={}):
    global LOG_ON
    # LOG_ON = False
    # ND = 279 # 3274
    # if ND in polys_cut_info:
    #     LOG_ON = True
    #     polys_cut_info = {ND: polys_cut_info[ND]}

    for node, info in polys_cut_info.items():
        poly = polys[node]
        modified = False
        dropped = 0
        if node in recut_nodes:
            recuts = recut_nodes.pop(node)
            for ii, p in enumerate(poly):
                if abs(p) in recuts:
                    info[ii] = 2
                    
        outer = False
        pids = []
        process_order = []

        if numpy.prod(info) != 0:
            modified = True
            ones_pos = [zid for zid, i in enumerate(info) if i > 0]
            first_zid = ones_pos.pop(0)
            process_order = range(first_zid, len(info))+range(first_zid)
            if len(ones_pos) == 0:
                outer = any([list_edges[abs(k)]["far"] == -1 for k in poly])
                seid = poly[first_zid]
                ceid, edge = get_cut_edge(list_edges, seid, node)

                xp, yp = ortho_prj(edge[0][0], edge[0][1], edge[1][0], edge[1][1], PointsMap[node][0], PointsMap[node][1])
                tx, ty = (2.*(PointsMap[node][0]-xp), 2.*(PointsMap[node][1]-yp))
                new_edge = (edge[1][0]+tx, edge[1][1]+ty), (edge[0][0]+tx, edge[0][1]+ty)
                new_edge = clip_edge(new_edge, list_edges[0]["ebbox"])
                neid = create_new_edge(new_edge[0], new_edge[1], node, map_edges, list_edges, type_edge = ["projected", OUTER_MAP[outer]])
                pids = [neid]
            elif len(ones_pos) == 1:
                first_seid = poly[first_zid]
                corner = None
                if ones_pos[0] == first_zid + 1:
                    corner = get_ordered_edge(first_seid, list_edges)[1]
                    if "cut_eid" in list_edges[abs(first_seid)]:        
                        ccc = get_cut_edge(list_edges, first_seid)
                        if ccc[1][1] != corner:
                            corner = None
                elif first_zid == 0  and ones_pos[0] == len(info)-1:
                    corner = get_ordered_edge(first_seid, list_edges)[0]
                    if "cut_eid" in list_edges[abs(first_seid)]:        
                        ccc = get_cut_edge(list_edges, first_seid)
                        if ccc[1][0] != corner:
                            corner = None
                    process_order = [len(info)-1] + range(len(info)-1)

                if corner is not None:
                    outer = any([list_edges[abs(k)]["far"] == -1 for k in poly])
                    new_corner = (corner[0]+ 2*(PointsMap[node][0]-corner[0]), corner[1]+ 2*(PointsMap[node][1]-corner[1]))
                    new_edge = clip_edge((new_corner, corner), list_edges[0]["ebbox"])
                    pids = [new_edge[0], None]
        
        else:
            first_zid = 0
            while first_zid < len(info) and info[first_zid] != 0:
                first_zid += 1
            process_order = range(first_zid, len(info))+range(first_zid)
                
        for i in process_order:
            if info[i] > 0:
                seid = poly[i]
                ceid, ord_edge = get_cut_edge(list_edges, seid, node)
                if seid != ceid:
                    modified = True
                elif dropped == 1:
                    dropped = 0
                prev_point = ord_edge[0]                    
                if len(pids) > 0:
                    if pids[-1] is None:
                        prev_point = pids[0]
                        pids = []
                    else:
                        prev_point = get_ordered_edge(pids[-1], list_edges)[1]
                        # prev_point = list_edges[abs(pids[-1])]["edge"][int(pids[-1] > 0)]                        
                if prev_point !=  ord_edge[0]:
                    neid = create_new_edge(prev_point, ord_edge[0], node, map_edges, list_edges, type_edge = ["fill", OUTER_MAP[outer]])
                    pids.append(neid)
                    outer = False

                if len(pids) > 0 and ceid == -pids[-1]:
                    pids.pop()                    
                else:
                    pids.append(ceid)
                
            elif info[i] == 0:
                if len(pids) > 0:
                    prev_point = get_ordered_edge(pids[-1], list_edges)[1]
                    curr_point = get_ordered_edge(poly[i], list_edges)[0]
                    if prev_point != curr_point:
                        neid = create_new_edge(prev_point, curr_point, node, map_edges, list_edges, type_edge = ["fill", OUTER_MAP[False]])
                        pids.append(neid)
                pids.append(poly[i])
            else: ## info[i] == -1:
                dropped += 1
                if list_edges[abs(poly[i])]["far"] == -1:
                    outer = True

        #### make sure it's closed
        prev_point = get_ordered_edge(pids[-1], list_edges)[1]
        first_point = get_ordered_edge(pids[0], list_edges)[0]
        if prev_point != first_point:            
            # print "Doesn't close"
            neid = create_new_edge(prev_point, first_point, node, map_edges, list_edges, type_edge = ["fill", OUTER_MAP[outer]])
            if neid == -pids[-1]:
                pids.pop()
            else:
                pids.append(neid)
            outer = False

        if dropped > 1:
            modified = True            
        if not modified and sorted(pids) != sorted(poly):
            print "MODIFIED?", node, modified, "actually:", sorted(pids) != sorted(poly)
            print pids
            print poly
            raise ValueError("Cutting modification error")
        if modified:
            assembled[node] = pids

        if LOG_ON:
            plot_edges(poly, list_edges, lbl="IDS", color="b", linestyle="-", marker="x")
            plot_edges(assembled.get(node, []), list_edges, lbl="IDS", color="r", linestyle=":", marker="+")
            plot_show(True)
    LOG_ON = False
    return assembled

def make_list_cutdets(poly, eids):
    list_recut = []
    for p, v in enumerate(poly):
        ext = [(p, 0, 0)]
        if abs(v) in eids:                
            if 0 in eids[abs(v)]:
                if v > 0:
                    ext.insert(0, (p, -1))
                else:
                    ext.append((p, 1))
            if 1 in eids[abs(v)]:
                if v < 0:
                    ext.insert(0, (p, -1))
                else:
                    ext.append((p, 1))
        list_recut.extend(ext)
    list_recut.insert(0, list_recut.pop())
    return list_recut

    
def assemble_recut(PointsMap, map_edges, list_edges, polys, recut_nodes, assembled={}):
    global LOG_ON
    ND = 169 #1735 # 3274
    if ND in recut_nodes:
        LOG_ON = True
        recut_nodes = {ND: recut_nodes[ND]}
        pdb.set_trace()
        
    for node, eids in recut_nodes.items():
        poly = polys[node]
        map_poly = [[pi] for pi in poly]
        modified = False
        list_recut = make_list_cutdets(poly, eids)
        
        i = 0
        if LOG_ON:
            print "NODE", node, list_recut
            print "INIT MAP_POLY", map_poly
        while i < len(list_recut):
            if list_recut[i][-1] != 0:
                if LOG_ON:
                    print "Check", list_recut[i]                
                pos, where_insert = list_recut[i]
                cut_end = (where_insert+1)/2
                seid = poly[pos]
                ceid = list_edges[abs(seid)]["cut_eid"]
                if seid < 0:
                    ceid *= -1
                edge = get_ordered_edge(seid, list_edges)
                cedge = get_ordered_edge(ceid, list_edges)
                
                if cedge[cut_end] != edge[cut_end]:
                    jump = False

                    if i+1 < len(list_recut) and list_recut[i][-1]*list_recut[i+1][-1] != 0:
                        jump = True
                        if LOG_ON:
                            print "Check other", list_recut[i+1]                

                        pos_other, where_insert_other = list_recut[i+1]
                        cut_end_other = (where_insert_other+1)/2
                        seid_other = poly[pos_other]
                        ceid_other = list_edges[abs(seid_other)]["cut_eid"]
                        if seid_other < 0:
                            ceid_other *= -1
                        edge_other = get_ordered_edge(seid_other, list_edges)
                        cedge_other = get_ordered_edge(ceid_other, list_edges)
                        if cedge_other[cut_end_other] != edge_other[cut_end_other]:
                            ### corner recut
                            if LOG_ON:
                                print "corner cut", edge, edge_other, "->", cedge, cedge_other                

                            if cut_end == 0 or cut_end_other == 1: raise("Something unexpected during recut!")
                                
                            neid = create_new_edge(cedge[cut_end], cedge_other[cut_end_other], node, map_edges, list_edges, type_edge = ["residue", OUTER_MAP[False]])

                            map_poly[pos][-1] = ceid
                            map_poly[pos_other][-1] = ceid_other
                            map_poly[pos_other].insert(0, neid)
                            if LOG_ON:
                                print pos, pos_other, ceid, neid, ceid_other
                                print "MAP_POLY", map_poly
                            modified = True
                            i += 1
                        else:
                            jump = False
                            
                    if not jump:
                        ### single recut
                        if LOG_ON:
                            print "single cut", edge, "->", cedge                
                    
                        neid = create_new_edge(edge[cut_end], cedge[cut_end], node, map_edges, list_edges, type_edge = ["residue", OUTER_MAP[False]])
                        if cut_end == 0:
                            map_poly[pos][0] = ceid
                            map_poly[pos].insert(0, neid)
                        else:
                            map_poly[pos][-1] = ceid
                            map_poly[pos].append(-1*neid)
                        modified = True
                else:                                      
                    print "cut redacted"
            i += 1
            ####################
                
        if modified:
            assembled[node] = []
            for pp in map_poly:
                assembled[node].extend(pp)
        if LOG_ON:
            print "MAP_POLY", map_poly
            plot_edges(poly, list_edges, lbl="IDS", color="b", linestyle="-", marker="x")
            plot_edges(assembled.get(node, []), list_edges, lbl="IDS", color="r", linestyle=":", marker="+")
            plot_show(True)

    LOG_ON = False
    return assembled

def prepare_edges(PointsMap, gridh_percentile=-1, gridw_percentile=-1, after_cut=True, bbox=None):
    map_edges, list_edges, polys, ebbox = compute_voronoi(PointsMap, bbox)
    list_edges[0]["last_org"] = len(list_edges)
    list_edges[0]["last_cut"] = len(list_edges)
    list_edges[0]["last_isolated"] = len(list_edges)
    list_edges[0]["globe"] = False
    list_edges[0]["ebbox"] = ebbox
    if bbox is not None:
        list_edges[0]["bbox"] = bbox    
    
    polys_cut = {}
    if gridh_percentile > 0 and after_cut:
        vert_edges, horz_edges, _ = compute_edges_distances(PointsMap, list_edges)
        gridHW = compute_grid_size(vert_edges, horz_edges, gridh_percentile, gridw_percentile)    
        update_far(PointsMap, list_edges, gridHW)
        require_cut, polys_cut_info, isolated_nodes = gather_require_cut(PointsMap, map_edges, list_edges, polys)
                
        recut_nodes = cut_edges(PointsMap, map_edges, list_edges, require_cut, gridHW)
        list_edges[0]["last_cut"] = len(list_edges)
    
        assemble_isolated(PointsMap, map_edges, list_edges, polys, isolated_nodes, gridHW, polys_cut)
        list_edges[0]["last_isolated"] = len(list_edges)
        
        assemble_cut(PointsMap, map_edges, list_edges, polys, polys_cut_info, recut_nodes, polys_cut)
        assemble_recut(PointsMap, map_edges, list_edges, polys, recut_nodes, polys_cut)
        
    for node, poly in polys.items():
        if node in polys_cut:
            pp = polys_cut[node]
        else:
            pp = poly    
        for pi, eid in enumerate(pp):
            if "nodes_cut" not in list_edges[abs(eid)]:
                list_edges[abs(eid)]["nodes_cut"] = []
                list_edges[abs(eid)]["pos_cut"] = []
            list_edges[abs(eid)]["nodes_cut"].append(node)
            list_edges[abs(eid)]["pos_cut"].append((pi+1)*numpy.sign(eid))                        
            
    return map_edges, list_edges, polys, polys_cut, ebbox

def prepare_edges_dst(PointsMap, gridh_percentile=-1, gridw_percentile=-1, after_cut=True, dst_type="globe"):
    if dst_type == "globe":
        PointsRad = coordsPointsToGlobe(PointsMap)
        deg_bbox = [-180, -90, 180, 90]
        bbox = numpy.radians(deg_bbox)
    else:
        PointsRad = PointsMap
        deg_bbox = None
        bbox = None

    map_edges, list_edges, polys, polys_cut, ebbox = prepare_edges(PointsRad, gridh_percentile=gridh_percentile, gridw_percentile=gridw_percentile, after_cut=after_cut, bbox=bbox)
    if dst_type == "globe":
        coordsEdgesFromGlobe(list_edges, clip=deg_bbox)
        list_edges[0]["globe"] = True
        
    return map_edges, list_edges, polys, polys_cut, ebbox

def get_edges_coords_flatten(list_edges, seids=None, after_cut=True):
    kedge = "edge"
    if list_edges[0].get("globe"):
        kedge = "flat_edge"
    coords = []
    if seids is None:
        if after_cut:
            up_to = len(list_edges)
        else:
            up_to = list_edges[0]["last_org"]
        return [get_ordered_edge_flatten(eid, list_edges, kedge=kedge) for eid in range(0, up_to)]
    else:
        return [get_ordered_edge_flatten(seid, list_edges, kedge=kedge) for seid in seids]
        

def get_all_grps(list_edges):
    return [None] + range(-2, 2)
def get_edge_grp(list_edges, eid=None):
    if eid is None:
        return None
    grp = 0
    if "nodes_cut" in list_edges[eid]:
        grp += 1
    if "far" in list_edges[eid]:
        grp -= 1
        if not "cut_eid" in list_edges[eid]:
            grp -= 1
    return grp

def make_edges_graph_grps(map_edges, list_edges):
    edges_graph = {}
    all_grps = get_all_grps(list_edges)
    grp_to_edges = dict([(s,[]) for s in all_grps])
    for edge, eid in map_edges.items():
        grp = get_edge_grp(list_edges, eid)
        grp_to_edges[grp].append(eid)
        for ni, n in enumerate(edge):
            if n not in edges_graph:
                edges_graph[n] = dict([(s,[]) for s in all_grps])
            edges_graph[n][grp].append(edge[1-ni])
        if "cut_eid" in list_edges[eid]:
            ceid = list_edges[eid]["cut_eid"]
            cedge = get_ordered_edge(ceid, list_edges)
            grp_sp = get_edge_grp(list_edges, None)
            added = False
            for ni, n in enumerate(edge):
                if cedge[ni] != n:
                    added = True
                    edges_graph[n][grp_sp].append(cedge[ni])
                    if cedge[ni] not in edges_graph:
                        edges_graph[cedge[ni]] = dict([(s,[]) for s in all_grps])
                    edges_graph[cedge[ni]][grp_sp].append(n)
            if added:
                grp_to_edges[grp_sp].extend([eid, abs(ceid)])
    return edges_graph, grp_to_edges

def get_ordered_pairs(v, vs):
    return [order_edge(v, vv)[0] for vv in vs]

def filter_splength(source, graph, trav=[], collect=None):
    seen={}                  # level (number of hops) when seen in BFS
    level=0                  # the current level
    nextlevel=set([source])  # dict of nodes to check at next level
    while nextlevel:
        thislevel=nextlevel  # advance to next level
        nextlevel=set()         # and start a new list (fringe)
        for v in thislevel:
            if v not in seen:
                seen[v]=level # set the level of vertex v
                for t in trav:
                    if collect is not None:
                        collect.update(get_ordered_pairs(v, graph[v][t]))
                    nextlevel.update(graph[v][t]) # add neighbors of v
        level=level+1
    return seen  # return all path lengths as dictionary

def filter_cc(edges_graph, src_pool, trav=[]):
    seen={}
    for v in src_pool:
        if v not in seen:
            collect = set()
            c = filter_splength(v, edges_graph, trav, collect)
            yield list(c), collect
            seen.update(c)

def frame_cc(map_edges, list_edges):
    edges_graph, grp_to_edges = make_edges_graph_grps(map_edges, list_edges)
    src_points = set().union(*[list_edges[eid]["edge"] for eid in list_edges[0][TIK].get("frame", [])])
    blocks = []
    for cc, collect in filter_cc(edges_graph, src_points, trav=[-2]):
        reached = [map_edges[e] for e in collect]
        # next_layer = [map_edges[x] for x in set().union(*[get_ordered_pairs(c, edges_graph[c][-1]) for c in cc])]
        more_edges = set().union(*[[map_edges[x]
                                   for x in set().union(*[get_ordered_pairs(d, edges_graph[d][1])
                                                              for d in edges_graph[c][None]])
                                   if map_edges[x] >= list_edges[0]["last_cut"]] for c in cc])
        blocks.append({"bckbone": cc, "reached": reached, "more_edges": more_edges})        
    return blocks

def prepare_border_data(list_edges, connect_frame=None, after_cut=True):
    if after_cut:
        key_nodes = "nodes_cut"
        up_to = len(list_edges)
    else:
        key_nodes = "nodes"
        up_to = list_edges[0]["last_org"]

    beids =[eid for eid in range(1, up_to) if len(list_edges[eid].get(key_nodes, [])) == 1]    
    out = [list_edges[eids]["edge"] for eids in beids]
    fps, fpis = flatten_poly(out)
    out_data = {}
    for ppi, pp in enumerate(fps):
        org_len = len(pp)
        tt = clean_poly(pp)
        if len(tt) != 1 or len(tt[0]) != org_len:
            pdb.set_trace()
            # raise ValueError("Dirty polygon")
        peids = [numpy.sign(x)*beids[abs(x)-1] for x in fpis[ppi]]
        ci = -(len(out_data)+1)
        interior = (connect_frame is not None and len(connect_frame.intersection(peids)) == 0)
        out_data[ci] = {"ci": ci, "cells": [], "polys": [peids], "color": -1, "level": -int(interior)}
    return out_data

def make_out_data(map_edges, list_edges, after_cut=True):
    if after_cut:
        blocks = frame_cc(map_edges, list_edges)
        connect_frame = set().union(*[b["more_edges"] for b in blocks])
        connect_frame.update(list_edges[0][TIK].get("isolated", []))
        connect_frame.update(list_edges[0][TIK].get("projected",[]))        
    else:
        connect_frame = None
    return prepare_border_data(list_edges, connect_frame, after_cut)

def make_nodes_graph(list_edges, after_cut=True):
    nodes_graph = {}
    if after_cut:
        key_nodes = "nodes_cut"
        up_to = len(list_edges)
    else:
        key_nodes = "nodes"
        up_to = list_edges[0]["last_org"]

    for eid in range(1, up_to):
        if key_nodes not in list_edges[eid]:
            continue
        nodes = list_edges[eid][key_nodes]
        for node in nodes:
            if node not in nodes_graph:
                nodes_graph[node] = {}
            for nodex in nodes:
                if node != nodex:
                    nodes_graph[node][nodex] = eid
    return nodes_graph               

def compute_node_pairs(list_edges, max_nid=None, after_cut=True):
    node_pairs = []
    if after_cut:
        key_nodes = "nodes_cut"
        up_to = len(list_edges)
    else:
        key_nodes = "nodes"
        up_to = list_edges[0]["last_org"]

    for eid in range(1, up_to):
        if key_nodes not in list_edges[eid]:
            continue
        nodes = list_edges[eid][key_nodes]
        if len(nodes) == 1:
            if max_nid is None or nodes[0] < max_nid:
                node_pairs.append([eid, nodes[0], -1])
        elif len(nodes) == 2:
            if max_nid is None or (nodes[0] < max_nid and nodes[1] < max_nid):
                node_pairs.append([eid, nodes[0], nodes[1]])
            elif nodes[0] < max_nid:
                node_pairs.append([eid, nodes[0], -2])
            elif nodes[1] < max_nid:
                node_pairs.append([eid, nodes[1], -2])
    return numpy.array(node_pairs, dtype=int)

def prepare_cc_polys(list_edges, nodes_sel, polys):
    edge_counts = {}
    for node in nodes_sel:
        for eid in polys.get(node, []):         
            edge_counts[abs(eid)] = edge_counts.get(abs(eid), 0) + 1
    borders_eids = [eid for eid,c in edge_counts.items() if c == 1]
    borders_edges = [list_edges[eid]["edge"] for eid in borders_eids]
    fps, fpis = flatten_poly(borders_edges)
    pps = [[numpy.sign(ee)*borders_eids[abs(ee)-1] for ee in pp] for pp in fpis]
    return pps

def ss_splength(source, nodes_graph, nodes_colors=None):
    seen={}                  # level (number of hops) when seen in BFS
    level=0                  # the current level
    nextlevel=set([source])  # dict of nodes to check at next level
    while nextlevel:
        thislevel=nextlevel  # advance to next level
        nextlevel=set()         # and start a new list (fringe)
        for v in thislevel:
            if v not in seen:
                seen[v]=level # set the level of vertex v
                nextlevel.update([c for c in nodes_graph[v].keys() if nodes_colors is None or (c >= 0 and nodes_colors[v] == nodes_colors[c])]) # add neighbors of v
        level=level+1
    return seen  # return all path lengths as dictionary


def connected_components(nodes_graph, nodes_colors, color):
    seen={}
    pool = numpy.where(nodes_colors == color)[0]
    for v in pool:
        if v not in seen:
            c = ss_splength(v, nodes_graph, nodes_colors)
            yield list(c)
            seen.update(c)

def prepare_areas_helpers(map_edges, list_edges, after_cut=True):
    nodes_graph = make_nodes_graph(list_edges, after_cut)
    out_data = make_out_data(map_edges, list_edges, after_cut)
    return out_data, nodes_graph

def prepare_areas_polys(polys, polys_cut, after_cut=True):
    if after_cut:
        pp = dict([(p, polys_cut.get(p) or polys[p]) for p in polys])
    else:
        pp = polys
    return pp
            
def prepare_areas_data(nodes_colors, list_edges, polys, out_data, nodes_graph):
    #### nodes_colors_bckg: contains ids of parts all nodes belong to, i.e. support part, variable value, -2 means outside support, bckg cell
    nodes_colors_bckg = -2*numpy.ones(len(polys), dtype=int)
    if type(nodes_colors) is list:
        nodes_colors_bckg[nodes_colors] = 0
    elif type(nodes_colors) is dict:
        for i, v in nodes_colors.items():
            nodes_colors_bckg[i] = v
    else:
        nodes_colors_bckg[:nodes_colors.shape[0]] = nodes_colors

    #### compute color connected components
    ccs_data = {}
    for si in set(nodes_colors_bckg):
        for cc in connected_components(nodes_graph, nodes_colors_bckg, si):
            ci = len(ccs_data)
            cc_polys = prepare_cc_polys(list_edges, cc, polys)
            ccs_data[ci] = {"ci": ci, "nodes": cc, "polys": cc_polys, "color": si, "level": -1}
    ccs_data.update(out_data)

    cis = ccs_data.keys()
    eids_to_ccs = {} 
    adjacent = dict([(ci, set()) for ci in cis])
    for ci in cis:
        ccs_data[ci]["poly_sets"] = []
        for p in ccs_data[ci]["polys"]:
            ccs_data[ci]["poly_sets"].append(set([abs(eid) for eid in p]))
            for eid in ccs_data[ci]["poly_sets"][-1]:
                if eid not in eids_to_ccs:
                    eids_to_ccs[eid] = []
                else:
                    adjacent[eids_to_ccs[eid][0]].add(ci)
                    adjacent[ci].add(eids_to_ccs[eid][0])
                eids_to_ccs[eid].append(ci)

    #### compute reachability level starting from outside level=0
    queue = [k for (k, vs) in ccs_data.items() if vs["level"] == 0]
    nextlevel = set()
    level = 1
    while len(queue) > 0:                        
        for ci in queue:
            for cj in adjacent[ci]:
                if ccs_data[cj]["level"] < 0:
                    ccs_data[cj]["level"] = level
                    nextlevel.add(cj)
        queue = nextlevel
        nextlevel = set()
        level += 1

    #### From outside to inner most components find exterior border of component
    cks = sorted(ccs_data.keys(), key=lambda x: ccs_data[x]["level"])
    for ck, data in ccs_data.items():
        data["exterior_polys"] = [i for i in range(len(data["polys"]))]
        if data["level"] == 0:
            data["exterior_polys"] = []
            continue
        if len(data["polys"]) < 2:
            continue
        interior_dots = set()
        for k in adjacent[ck]:
            if data["level"] < ccs_data[k]["level"]:
                interior_dots.update(*ccs_data[k]["poly_sets"])
            
        if len(interior_dots) > 0:                            
            data["exterior_polys"] = [pi for pi, poly in enumerate(data["poly_sets"]) if len(set(poly).difference(interior_dots)) > 0]
    return ccs_data, cks, adjacent


# EDGES_FIELDS_LIST = []
EDGES_FIELDS_LIST = [('eid', "%d"), ('edge', "(%s,%s)"), ('flat_edge', "(%s,%s)"), ("types", "%s"),
                     ('nodes', "(%s,%s)"), ('pos', "(%s,%s)"),
                     ('nodes_cut', "(%s,%s)"), ('pos_cut', "(%s,%s)"),
                     ('uncut_eid', "%d"), ('cut_eid', "%d"), ('far', "%d"), ('n_closer', "%d")]
EDGES_FIELDS_MAP = dict(EDGES_FIELDS_LIST)

def preamble_for_edges(list_edges):
    entries = [(k,v) for (k,v) in list_edges[0].items() if re.match("last_", k) or (k == "nb_nodes")]
    entries_more = []
    entries_more.append(("globe", str(list_edges[0].get("globe"))))
    for k in ["bbox", "ebbox"]:
        if k in list_edges[0]:
            entries_more.append((k, "(%s,%s,%s,%s)" % tuple(list_edges[0][k])))
    entries.sort(key=lambda x: x[1])
    return "# LIST OF EDGES\t%s" % " ".join(["%s=%d" % (k,v) for (k,v) in entries]+["%s=%s" % (k,v) for (k,v) in entries_more])
def header_for_edges(list_edges):
    return "\t".join([k for k,f in EDGES_FIELDS_LIST])

def parse_preamble(line):
    list_edges = [{"edge": None, TIK: {}, "nb_nodes": 0}]
    if re.match("# LIST OF EDGES\t", line):
        parts = line.strip().split("\t")[1].split(" ")
        for part in parts:
            pp = part.strip().split("=")
            if pp[0] in ["bbox", "ebbox"]:
                list_edges[0][pp[0]] = numpy.array(eval(pp[1]))
            elif pp[0] in ["globe"]:
                list_edges[0][pp[0]] = bool(pp[1])
            else:
                list_edges[0][pp[0]] = int(pp[1])
    return list_edges
def parse_header(line):
    parts = line.strip().split("\t")
    return [(p, i) for i,p in enumerate(parts)]

def str_for_edge(list_edges, eid):
    edge = {"eid": eid}
    edge.update(list_edges[eid])
    for field in ['types']:
        if field in edge:
            edge[field] = "(%s)" % ",".join(edge[field])
    for field in ['nodes', 'pos', 'nodes_cut', 'pos_cut']:
        if field in edge:
            if len(edge[field]) == 1:
                edge[field] = (edge[field][0], "-")
            elif len(edge[field]) == 2:
                edge[field] = (edge[field][0], edge[field][1])
            elif len(edge[field]) > 2:
                print "EDGE", eid, edge
                raise ValueError("More than two nodes to an edge!")
            else:
                edge[field] = None
    return "\t".join([f % edge[k] if edge.get(k) is not None else "" for k,f in EDGES_FIELDS_LIST])
def parse_edge(line, head):
    parts = line.strip().split("\t")
    eid = None
    edge = {"edge": None, "nodes": [], "types": set()}
    for p,i in head:
        if i < len(parts) and len(parts[i]) > 0:
            if p in ["edge", "flat_edge"]:
                v = eval(parts[i])
            elif p in ["types"]:
                v = set(parts[i].strip("()").split(","))
            elif EDGES_FIELDS_MAP[p] == "(%s,%s)":                
                v = [int(vx) for vx in parts[i].strip("()").split(",") if vx != "-"]
            elif re.match("%[0-9.]*f$", EDGES_FIELDS_MAP[p]):
                v = float(parts[i])
            elif re.match("%[0-9.]*d$", EDGES_FIELDS_MAP[p]):
                v = int(parts[i])
            else:
                v = parts[i]
                
            if p == "eid":
                eid = v
            else:
                edge[p] = v
    return eid, edge

def write_edges(fp, list_edges):
    close = False
    if not isinstance(fp, file):
        fp = open(fp, "w")
        close = True
    fp.write(preamble_for_edges(list_edges)+"\n")
    fp.write(header_for_edges(list_edges)+"\n")
    for eid in range(1, len(list_edges)):
        fp.write(str_for_edge(list_edges, eid)+"\n")    
    if close:
        fp.close()
    
def read_edges(filename):
    list_edges = None
    close = False
    f, fcl = getFp(filename)
    if f is not None:
        head = None
        for line in f:
            if list_edges is None:
                list_edges = parse_preamble(line)
            elif head is None:
                head = parse_header(line)
            else:
                eid, edge = parse_edge(line, head)
                if eid is not None and eid == len(list_edges):
                    list_edges.append(edge)                
    if fcl:
        f.close()
    return list_edges

def build_from_edges(list_edges):
    map_edges, polys, polys_cut = ({}, {}, {})
    tmp_polys, tmp_polys_cut = ({}, {})
    for eid in range(1, len(list_edges)):
        edge = list_edges[eid]
        map_edges[edge["edge"]] = eid
        if len(edge["types"]) > 0:
            update_types(list_edges, eid, edge["types"], from_edge=True)
        for nkey, pkey, trg in [("nodes_cut", "pos_cut", tmp_polys_cut), ("nodes", "pos", tmp_polys)]:
            if edge.get(nkey) is not None and edge.get(pkey) is not None and len(edge.get(nkey)) > 0 and len(edge.get(nkey)) == len(edge.get(pkey)):
                for ni, n in enumerate(edge[nkey]):
                    p = edge[pkey][ni]
                    if n not in trg:
                        trg[n] = []
                    trg[n].append((abs(p), numpy.sign(p)*eid))
    nodes_polys = set().union(tmp_polys.keys(), tmp_polys_cut.keys())
    for node in nodes_polys:
        if node in tmp_polys:
            tmp_polys[node].sort()
        if node in tmp_polys_cut:
            tmp_polys_cut[node].sort()
        if tmp_polys.get(node) == tmp_polys_cut.get(node):
            polys[node] = [p[1] for p in tmp_polys[node]]
        else:
            if node in tmp_polys:
                polys[node] = [p[1] for p in tmp_polys[node]]
            if node in tmp_polys_cut:
                polys_cut[node] = [p[1] for p in tmp_polys_cut[node]]
    return map_edges, list_edges, polys, polys_cut

def read_edges_and_co(filename):
    list_edges = read_edges(filename)
    return build_from_edges(list_edges)


def flatToGlobe(coord):
    rx, ry = numpy.radians(coord)
    return (numpy.cos(ry) * rx, ry)
def globeToFlat(coord, clip=False):
    x, y = (numpy.degrees(coord[0]/numpy.cos(coord[1])), numpy.degrees(coord[1]))
    if clip is not None:
        if x < clip[0]: x = clip[0]
        elif x > clip[2]: x = clip[2]
        if y < clip[1]: y = clip[1]
        elif y > clip[3]: y = clip[3]
    return x, y

def coordsPointsToGlobe(PointsMap):
    return dict([(i,flatToGlobe(coord)) for i, coord in PointsMap.items()])

def coordsEdgesFromGlobe(list_edges, clip=None):
    for i in range(1, len(list_edges)):
        globe_edge = list_edges[i]["edge"]
        flat_edge = (globeToFlat(globe_edge[0], clip=clip), globeToFlat(globe_edge[1], clip=clip))        
        list_edges[i]["flat_edge"] = flat_edge
    return list_edges

# #Run this for instance as "python prepare_polygons.py ~/coords.csv ~/poly_coords.csv - map"
if __name__=="__main__":
    
    coords_bckg, rnames_bckg = read_coords_csv("coords_bckg.csv")
    PointsMap={}
    PointsIds={}
    for i, coord in enumerate(rnames_bckg):
        PointsIds[i] = rnames_bckg[i]
        PointsMap[i] = coords_bckg[i]

    dst_type = "globe"
    # dst_type = "flat"
    gridh_percentile=95
    map_edges, list_edges, polys, polys_cut, ebbox = prepare_edges_dst(PointsMap, gridh_percentile=gridh_percentile, dst_type=dst_type)
    
    # ## FULL MAP BY TYPES
    # bounds = [1, list_edges[0]["last_org"], list_edges[0]["last_cut"], list_edges[0]["last_isolated"], len(list_edges)]
    # elements = [(bounds[0], bounds[1], "-", "k"), (bounds[1], bounds[2], "-", "g"), (bounds[2], bounds[3], "-", "m"), (bounds[3], bounds[4], "-", "r")]
    # for (bdw, bup, linestyle, color) in elements:
    #     plot_edges(range(bdw, bup), list_edges, linestyle=linestyle, color=color, kedge="flat_edge")
    # # xs, ys = zip(*PointsMap.values())
    # # plt.plot(xs, ys, "bo")
    # # for pi, cc in PointsMap.items():
    # #     plt.text(cc[0], cc[1], pi)
    # plot_show(True)
    
    # fname = "/home/egalbrun/short/test_edges.txt"
    # write_edges(fname, list_edges)
    # rmap_edges, rlist_edges, rpolys, rpolys_cut = read_edges_and_co(fname)

    # npairs = compute_node_pairs(list_edges, max_nid=200)

    after_cut=True
    pp = prepare_areas_polys(polys, polys_cut, after_cut)
    # pds, pps = zip(*pp.items())
    # for p in pds:
    #     plt.text(PointsMap[p][0], PointsMap[p][1], p)
    #     plt.plot(PointsMap[p][0], PointsMap[p][1], "ro")        
    # plot_esets_colordered(pps, list_edges, simple=False, kedge="flat_edge")
    # plot_show(True)
    
    out_data, nodes_graph = prepare_areas_helpers(map_edges, list_edges, after_cut)
    # Xs = [o["polys"][0] for o in out_data.values()]
    # plot_esets_colordered(Xs, list_edges, simple=True, kedge="flat_edge")
    # plot_show()
    
    ccs_data, cks, adjacent = prepare_areas_data([40, 86], list_edges, pp, out_data, nodes_graph)

    colors = {-2: "#AAAAAA", -1: "white", 0: "r"}
    pp_data = {"ccs_data": ccs_data, "cks": cks, "adjacent": adjacent}
    if pp_data is not None and "cks" in pp_data:
        for cii, ck in enumerate(pp_data["cks"]):
            pp_polys = pp_data["ccs_data"][ck]["polys"]
                    
            for pi in pp_data["ccs_data"][ck]["exterior_polys"]:
                plot_filled(pp_polys[pi], list_edges, color=colors.get(pp_data["ccs_data"][ck]["color"], "k"))
    plot_show(True)


    if dst_type == "globe":
        colors = {-2: "#AAAAAA", -1: "white", 0: "r"}
        pp_data = {"ccs_data": ccs_data, "cks": cks, "adjacent": adjacent}
        if pp_data is not None and "cks" in pp_data:
            for cii, ck in enumerate(pp_data["cks"]):
                pp_polys = pp_data["ccs_data"][ck]["polys"]
                    
                for pi in pp_data["ccs_data"][ck]["exterior_polys"]:
                    plot_filled(pp_polys[pi], list_edges, color=colors.get(pp_data["ccs_data"][ck]["color"], "k"), kedge="flat_edge")

                
    # for ci, dt in out_data.items():
    #     if dt["level"] == 0:
    #         linewidth = 2
    #     else:
    #         linewidth = 1
    #     plot_edges(dt["polys"][0], list_edges, linewidth=linewidth)
            
    # # eids_sel =  get_border_eids(list_edges)
    # eids_sel = list_edges[0][TIK][OUTER_MAP[True]]
    # for eid in range(1, len(list_edges)):
    #     linewidth = 1
    #     if eid in eids_sel:
    #         linewidth = 2
    #     nbN = len(list_edges[eid].get("nodes_cut", []))
    #     if nbN > 0:
    #         if nbN == 2:
    #             color = "b"
    #         elif nbN == 1:
    #             color = "g"
    #         else:
    #             color = "r"
    #         plot_edges([eid], list_edges, color=color, linewidth=linewidth)
            
    # plot_edges_colordered(list_edges[0][TIK][OUTER_MAP[True]], list_edges, "outer")
    # plot_edges(get_border_eids(list_edges), list_edges, linestyle=":", color="k")
        
    plot_show(True)
        