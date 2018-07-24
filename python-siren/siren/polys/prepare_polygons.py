#! /usr/local/bin/python

import sys
import voronoi_poly
import pdb
import numpy
import matplotlib.pyplot as plt
import matplotlib.cm

PLOT = True
PLOT_SPLIT = False
PLOT_EVERY = False
VERBOSE = False

GRT_CIR = 6370.997

ANGLE_TOL = 0.05
FACT_CUT = 0.8
FACT_ALONE = 0.5

GRIDH_PERCENTILE = 50
GRIDW_FACT = 1.

def computeHPoly(horz_edges):
    xy = numpy.array(horz_edges)
    ps = numpy.polyfit(xy[:,0], xy[:,1], 2)
    xps = numpy.polyval(ps, xy[:,0])
    errF = (xps - xy[:,1])/xps
    ids = numpy.abs(errF) < 2
    ps = numpy.polyfit(xy[ids,0], GRIDW_FACT*xy[ids,1], 2)

    # xps = numpy.polyval(ps, xy[:,0])
    # plt.scatter(xy[:,0], xy[:,1], color="b")
    # plt.plot(xy[:,0], xps, "r+")
    # plt.show()
    return ps

def getInterYV(x1, y1, x2, y2, xv):
    return y1+(xv-x1)*(y2-y1)/(x2-x1)
def getInterXH(x1, y1, x2, y2, yh):
    return x1+(yh-y1)*(x2-x1)/(y2-y1)

def getCutPoint(edge, end_cut, nodes, sx, sy, gridH, gridWps, f, edata, plot_dot=True):
    if end_cut is None:
        return None, False
    nA, nB = nodes
    midX = (sx[nA] + sx[nB])/2.
    midY = (sy[nA] + sy[nB])/2.

    cancel = {"V": False, "H": False}
    (xv, yv) = (edge[end_cut][0], edge[end_cut][1])
    (xh, yh) = (edge[end_cut][0], edge[end_cut][1])
    if edge[end_cut][0] < edge[1-end_cut][0]: ### end to cut is to the left
        xv = midX - f*getRectW(midX, midY, gridH, gridWps)
        yv = getInterYV(edge[0][0], edge[0][1], edge[1][0], edge[1][1], xv)
    elif edge[end_cut][0] > edge[1-end_cut][0]: ### end to cut is to the right
        xv = midX + f*getRectW(midX, midY, gridH, gridWps)
        yv = getInterYV(edge[0][0], edge[0][1], edge[1][0], edge[1][1], xv)
    else: # vertical edge
        cancel["V"] = True
        # print "No horizontal intersection"
    if edge[end_cut][1] < edge[1-end_cut][1]: ### end to cut is at the bottom
        yh = midY - f*getRectH(midX, midY, gridH, gridWps)
        xh = getInterXH(edge[0][0], edge[0][1], edge[1][0], edge[1][1], yh)
    elif edge[end_cut][1] > edge[1-end_cut][1]: ### end to cut is at the top
        yh = midY + f*getRectH(midX, midY, gridH, gridWps)
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
    if cancel["H"] and cancel["V"] and (edata["n_distTE"] > edata["n_dist"]):
        (xh, yh) = (edge[edata["n_closer"]][0], edge[edata["n_closer"]][1])
    plotted_dot = (plot_dot and cancel["H"] and cancel["V"] and (edata["n_distTE"] > edata["n_dist"]))
        
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

    if VERBOSE:
        print "-----------------"
        print "cutting", (edge[end_cut][0], edge[end_cut][1])
        print "TO", select_cut
    if plotted_dot:
        plt.plot([sx[nA], midX, sx[nB]], [sy[nA], midY, sy[nB]], ":ko")
        x, y = zip(*edge)
        plt.plot(x, y, "y", linewidth=3)
        plt.plot(edge[end_cut][0], edge[end_cut][1], "yo")
        if select_cut is not None:
            plt.plot(select_cut[0], select_cut[1], "rx")

        box = getPolyRect(midX, midY, gridH, gridWps, f)
        ex, ey = zip(*box)
        plt.plot(ex, ey, 'k:')
    return select_cut, plotted_dot

def getDistance(x1, y1, x2, y2):
    return greatCircleDistance(x1, y1, x2, y2)

def getDistanceTroughEdge(x1, y1, x2, y2, edge):
    midX = (x1 + x2)/2.
    midY = (y1 + y2)/2.
    dst = getDistance(x1, y1, x2, y2)
    closer = 0
    if (midX-edge[1][0])**2+(midY-edge[1][1])**2 < (midX-edge[0][0])**2+(midY-edge[0][1])**2:
        closer = 1
        
    if midX >= numpy.minimum(edge[0][0], edge[1][0]) and midX <= numpy.maximum(edge[0][0], edge[1][0]) and midY >= numpy.minimum(edge[0][1], edge[1][1]) and midY <= numpy.maximum(edge[0][1], edge[1][1]):
        return dst, dst, closer

    return dst, getDistance(x1, y1, edge[closer][0], edge[closer][1])+getDistance(edge[closer][0], edge[closer][1], x2, y2), closer

def greatCircleDistance(x1, y1, x2, y2):
    x1 = numpy.radians(x1)
    y1 = numpy.radians(y1)
    x2 = numpy.radians(x2)
    y2 = numpy.radians(y2)
    angle1 = numpy.arccos(numpy.sin(x1) * numpy.sin(x2) + numpy.cos(x1) * numpy.cos(x2) * numpy.cos(y1 - y2))
    return  angle1*GRT_CIR

def getRectW(x, y, gridH, gridWps):
    return getW(y, gridWps)*360./(2*numpy.pi*GRT_CIR)
def getRectH(x, y, gridH, gridWps):
    return gridH*360./(2*numpy.pi*GRT_CIR)
def getPolyRect(x, y, gridH, gridWps, f):
    w = getRectW(x, y, gridH, gridWps)
    h = getRectH(x, y, gridH, gridWps)
    return [(x+fx*f*w, y+fy*f*h) for (fx, fy) in [(1,1), (1,-1), (-1,-1), (-1,1), (1,1)]]


def angleCosSin(x1, y1, x2, y2):
    ac = (x2-x1)
    bc = (y2-y1)
    return ac/numpy.sqrt(ac**2+bc**2), bc/numpy.sqrt(ac**2+bc**2)

def getW(y, gridWps):
    return numpy.polyval(gridWps, numpy.abs(y))

def getDistanceThres(y, gridH, gridWps, fact=1.):
    return fact*numpy.sqrt(getW(y, gridWps)**2+gridH**2)

def ortho_prj(x1, y1, x2, y2, xn, yn):
    xA, yA = (x2-x1, y2-y1)
    xB, yB = (xn-x1, yn-y1)
    lA = numpy.sqrt(xA**2+yA**2)
    lB = numpy.sqrt(xB**2+yB**2)
    cosA = (xA*xB+yA*yB)/(lA*lB)
    return (x1 + cosA*lB*xA/lA, y1 + cosA*lB*yA/lA)

def fill_gaps(poly, eis, node, sx, sy, edges):
    filled_pis = []

    #### REORDERING EIS
    eis_sub, eis_org = ([], [])
    eis_sbA, eis_sbZ = ([], [])
    for eiss in eis:
        if eiss[0] is None:
            eis_sub.extend(eiss[1:])
            if len(eis_org) == 0:                
                eis_sbZ.append(eiss[1:])
            else:
                eis_sbA.append(eiss[1:])
        else:
            eis_org.extend(eiss)
    if eis[-1][0] is None and len(eis_sbZ) > 0:        
        eis_sbA[-1].extend(eis_sbZ.pop(0))
    eis_sbA += eis_sbZ

    # print "EIS", eis
    if eis[0][0] is None:
        eis_reorder = eis[1:]            
        if eis[-1][0] is None:
            eis_reorder[-1].extend(eis[0][1:])
        else:
            eis_reorder.append(eis[0])
    else:
        eis_reorder = eis
    # print "REORDERED", eis_reorder

    
    which = "X"
    if len(poly) == 1:
        which = "X1"        
        xp, yp = ortho_prj(poly[0][0][0], poly[0][0][1], poly[0][1][0], poly[0][1][1], sx[node], sy[node])
        tx, ty = (2.*(sx[node]-xp), 2.*(sy[node]-yp))
        filled = [poly[0][0], poly[0][1], (poly[0][1][0]+tx, poly[0][1][1]+ty), (poly[0][0][0]+tx, poly[0][0][1]+ty), poly[0][0]]
        filled_pis = [{"range": (0, 1), "eis": eis_org}, {"range": (1, 4), "eis": eis_sub}]
    elif len(poly) == 2:
        which = "X2"        
        if poly[0][1] == poly[1][0]: ### fill in second to last?
            which = "X2a"        
            corner = poly[0][1]
            new_corner = (corner[0]+ 2*(sx[node]-corner[0]), corner[1]+ 2*(sy[node]-corner[1]))
            filled = [poly[0][0], poly[0][1], poly[1][1], new_corner, poly[0][0]]
            filled_pis = [{"range": (0, 1), "eis": [eis_org[0]]},
                          {"range": (1, 2), "eis": [eis_org[1]]},
                          {"range": (2, 4), "eis": eis_sub}]
        elif poly[0][0] == poly[1][1]:
            which = "X2b"        
            corner = poly[1][1]
            new_corner = (corner[0]+ 2*(sx[node]-corner[0]), corner[1]+ 2*(sy[node]-corner[1]))
            filled = [poly[1][0], poly[1][1], poly[0][1], new_corner, poly[1][0]]
            filled_pis = [{"range": (0, 1), "eis": [eis_org[1]]},
                          {"range": (1, 2), "eis": [eis_org[0]]},
                          {"range": (2, 4), "eis": eis_sub}]
        else:
            filled = [poly[0][0], poly[0][1], poly[1][0], poly[1][1], poly[0][0]]
            filled_pis = [{"range": (0, 1), "eis": [eis_org[0]]},
                          {"range": (1, 2), "eis": []},
                          {"range": (2, 3), "eis": [eis_org[1]]},
                          {"range": (3, 4), "eis": []}]
            if eis_reorder[1][0] is None:
                filled_pis[1]["eis"] = eis_reorder[1][1:]
            if eis_reorder[-1][0] is None:
                filled_pis[-1]["eis"] = eis_reorder[-1][1:]
                
    else:
        which = "Xm"
            
        filled = list(poly[0])
        filled_pis = [{"range": (0, 1), "eis": eis_reorder[0]}]
        j = 1
        for i in range(1, len(poly)):
            if poly[i][0] != filled[-1]:
                if eis_reorder[j][0] is None:
                    filled_pis.append({"range": (len(filled)-1, len(filled)), "eis": eis_reorder[j][1:]})
                    j += 1
                else:
                    filled_pis.append({"range": (len(filled)-1, len(filled)), "eis": []})
                filled.append(poly[i][0])

            if eis_reorder[j][0] is None:
                filled_pis.append({"range": (len(filled)-1, len(filled)), "eis": eis_reorder[j][1:]})
            else:
                filled_pis.append({"range": (len(filled)-1, len(filled)), "eis": eis_reorder[j]})
            j += 1
            filled.append(poly[i][1])
        if filled[-1] != filled[0]:
            if j < len(eis_reorder):
                if eis_reorder[j][0] is None:
                    filled_pis.append({"range": (len(filled)-1, len(filled)), "eis": eis_reorder[j][1:]})
                else:
                    filled_pis.append({"range": (len(filled)-1, len(filled)), "eis": eis_reorder[j]})
                j += 1
            filled.append(filled[0])

    # if which == "Xm":
    #     print which, node
    #     print "----\nPOLY", poly, "\nEIS", eis
    #     print "FILLED", filled, "\nPIS", filled_pis
    #     print len(eis_reorder), j
    #     if len(eis_reorder) != j:
    #         pdb.set_trace()


    #     cmap = matplotlib.cm.get_cmap('rainbow')
    #     plt.plot(filled[0][0], filled[0][1],"x", ms=10, color="red")
    #     plt.plot(filled[1][0], filled[1][1],"^", ms=10, color="red")
    #     for oi in range(1, len(filled)):
    #         color = cmap((oi-1.)/(len(filled)-1.))
    #         plt.plot((filled[oi-1][0], filled[oi][0]), (filled[oi-1][1], filled[oi][1]),"o-", color=color, linewidth=2)
    #     for dd in filled_pis:
    #         color = cmap(dd["range"][0]/(len(filled)-1.))
    #         f = 0.001
    #         for aei in dd["eis"]:
    #             ei = abs(aei)
    #             plt.plot((edges[ei]["edge"][0][0]+f, edges[ei]["edge"][1][0]+f), (edges[ei]["edge"][0][1]+f, edges[ei]["edge"][1][1]+f),"s--", color=color, linewidth=1)
    #     plt.show()
            
    return filled, filled_pis
        
def flatten_poly(poly):
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
    while len(gpoly) > 0:     
        prev_node = sorted(gpoly.keys(), key=lambda x: (-len(gpoly[x]), x))[0]
        next_node = gpoly[prev_node].pop(0)
        gpoly[next_node].remove(prev_node)
        fps.append([prev_node, next_node])
        fpis.append([map_pis[(prev_node, next_node)]])
        prev_node = next_node
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

def dedup_poly(poly):
    i = 1
    while i < len(poly):
        if poly[i] == poly[i-1]:
            poly.pop(i)
        else:
            i += 1
    return poly
def decomplex_poly(poly):
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
# for dot in [(0., 0., 0., 1.), (0., 0., 1., 0.), (70., 0., 70., 1.), (70., 0., 71., 0.)]:
#     print dot, greatCircleDistance(dot[0], dot[1], dot[2], dot[3]), angleCosSin(dot[0], dot[1], dot[2], dot[3])
# pdb.set_trace()


def loadCoords(coords_fn, sep=",", lat_cid=0, lng_cid=1, names_cid=None):    
    #Creating the PointsMap from the input data
    PointsMap={}
    PointsIds={}
    fp=open(coords_fn, "r")
    for line in fp:
        data=line.strip().split(sep)

        try:
            if True:
            # if float(data[1]) < 0 and float(data[1]) > -30 and float(data[2]) < -20:
                if names_cid is not None:
                    PointsIds[len(PointsMap)]=data[names_cid].strip()                    
                else:
                    PointsIds[len(PointsMap)]=len(PointsMap)
                PointsMap[len(PointsMap)]=(float(data[lat_cid].strip()),float(data[lng_cid].strip()))               
        except:
            sys.stderr.write( "(warning) Invalid Input Line: "+line)
    fp.close()
    return PointsMap, PointsIds


def compute_polys(PointsMap):

    ### Compute the voronoi diagram
    #################################
    ### coordinates of the points
    sx, sy = zip(*PointsMap.values())
    #1. Stations, Lines and edges   
    vl=voronoi_poly.VoronoiPolygonsMod(PointsMap, BoundingBox=[max(sy)+1, min(sx)-1, min(sy)-1, max(sx)+1])

    ### Collect nodes on either side of each edge in the voronoi diagram
    map_edges = {}
    for so, details in vl.items():
        for edge in details['obj_polygon']:
            if edge[0] < edge[1]:
                norm_edge = (edge[0], edge[1])
            else:
                norm_edge = (edge[1], edge[0])
          
            if norm_edge in map_edges:
                map_edges[norm_edge].append(details["info"])
            else:
                map_edges[norm_edge] = [details["info"]]
    ### exactly two adjacent nodes, except for border edges that have only one
    assert all([(len(x)==2 or len(x)==1) for (k,x) in map_edges.items()])

    # define the colormap
    cmap = plt.get_cmap('cool')
    EXT_D = getDistance(numpy.min(sx), numpy.min(sy), numpy.max(sx), numpy.max(sy))
    MAX_D = 1.


    ### compute distances between neighbors,
    ### collect near-vertical and near-horizontal neighbors to detect the side of the grid
    gridH = float("Inf")
    edges = [{"edge": (None, -1)}]
    horz_edges = []
    vert_edges = []
    # graph = {}
    for edg, sts in map_edges.items():
        if len(sts) == 1: ## border edge
            nodes = (sts[0], -1)
            dst, dstTE, clsr = EXT_D+1, EXT_D+1, 0           
            cos, sin = (0,0)
            far = -1
        else: ## other edge
            nodes = (sts[0], sts[1])
            dst, dstTE, clsr = getDistanceTroughEdge(sx[sts[0]], sy[sts[0]], sx[sts[1]], sy[sts[1]], edg)
            if dst > MAX_D:
                MAX_D = dst
            cos, sin = angleCosSin(sx[sts[0]], sy[sts[0]], sx[sts[1]], sy[sts[1]])
            far = 0
            if numpy.abs(cos) > (1-ANGLE_TOL): ## if near-horizontal
                horz_edges.append((numpy.abs(sy[sts[0]]), dst))
            elif numpy.abs(cos) < ANGLE_TOL: ## if near-vertical
                if dst < gridH: 
                    gridH = dst
                vert_edges.append(dst)

        # for ni in [0,1]:            
        #     if nodes[ni] not in graph:
        #         graph[nodes[ni]] = []
        #     graph[nodes[ni]].append((nodes[1-ni], len(edges)))                
        edges.append({"n_dist": dst, "n_distTE": dstTE, "n_closer": clsr, "angle": numpy.abs(cos), "nodes": nodes, "edge": edg, "far": far})

    ### build index of edge ids in data
    map_norm_edges = dict([(ed["edge"], ei) for (ei, ed) in enumerate(edges)])
    for (ei, ed) in enumerate(edges):
        redge = (ed["edge"][1], ed["edge"][0])
        if redge in map_norm_edges:
            pdb.set_trace()
        else:
            map_norm_edges[redge] = -ei
    ### build index of nodes ids in voronoi data
    nodes_vli = dict([(details["info"], so) for so, details in vl.items()])


    ### detect adaptive vertical grid size from collected near-vertical neighbors distances 
    gridH = numpy.percentile(vert_edges, GRIDH_PERCENTILE)
    gridWps = computeHPoly(horz_edges)
    
    ### from the detected grid sizes, go through edges and mark far-apart neighbors
    for ei in range(1, len(edges)):
        dt = edges[ei]
        lw = 1
        if dt["nodes"][1] >= 0:
            y = (sy[dt["nodes"][0]]+sy[dt["nodes"][1]])/2.
            th = getDistanceThres(y, gridH, gridWps, 1.) ### max distance to be considered neighbors at this latitude
            if dt["n_dist"] > 1.2*th:
                dt["far"] = 1
                lw = 6
            elif dt["n_distTE"] > 1.2*th:
                dt["far"] = 2
                lw = 4
        else:
            lw = 8
        if PLOT_SPLIT and lw > 1:
            ex,ey = zip(*dt["edge"])
            ci = dt["n_dist"]/MAX_D
            plt.plot(ex, ey, color=cmap(ci), linewidth=lw)
    if PLOT_SPLIT:
        plt.plot(sx, sy, "g+")
        plt.show()
    
    require_cut = {}
    polys = {}
    edges_ids = {}
    ## go over each node in the voronoi diagram, prepare polygon 
    for node, nvi in nodes_vli.items():
        has_far = False
        has_near = False
        eis = []
        for edge in vl[nvi]['obj_polygon']:
            eis.append(map_norm_edges[edge])
            if edges[abs(eis[-1])]["far"] == 0:
                has_near = True
            else:
                has_far = True
        if has_near:        
            poly, polis = flatten_poly(vl[nvi]['obj_polygon'])
            pis = []
            for poli in polis:
                pis.append([numpy.sign(pi)*numpy.sign(eis[abs(pi)-1])*abs(eis[abs(pi)-1]) for pi in poli])
                # rep_poly = []
                # for pi in pis[-1]:
                #     if pi > 0:
                #         rep_poly.append(edges[pi]["edge"][0])
                #     elif pi < 0:
                #         rep_poly.append(edges[-pi]["edge"][1])
            polys[node] = pis
            edges_ids[node] = pis
            
            ### collect edges that are not far but adjacent to far, which will need to be cut 
            for pi in range(len(poly)):
                for ppi in range(len(poly[pi])-1):
                    if edges[abs(pis[pi][ppi])]["far"] != 0:
                        oei = None
                        if edges[abs(pis[pi][ppi-1])]["far"] == 0:
                            oei = abs(pis[pi][ppi-1])
                            which = poly[pi][ppi]
                            # ww = sorted(set(edges[abs(pis[pi][ppi-1])]["edge"]).intersection(edges[abs(pis[pi][ppi])]["edge"]))
                            # if len(ww) != 1 or ww[0] != which:
                            #     pdb.set_trace()
                            if oei not in require_cut:
                                require_cut[oei] = []
                            require_cut[oei].append((which, node, pi, ppi))

                        aft = ppi+1
                        if aft == len(pis[pi]): aft = 0
                        if edges[abs(pis[pi][aft])]["far"] == 0:
                            oei = abs(pis[pi][aft])
                            which = poly[pi][ppi+1]
                            # ww = sorted(set(edges[abs(pis[pi][aft])]["edge"]).intersection(edges[abs(pis[pi][ppi])]["edge"]))
                            # if len(ww) != 1 or ww[0] != which:
                            #     pdb.set_trace()
                            if oei not in require_cut:
                                require_cut[oei] = []
                            require_cut[oei].append((which, node, pi, ppi))

        else:
            polys[node] = None #getPolyRect(sx[node], sy[node], gridH, gridWps, .5)
            edges_ids[node] = eis
            
    ## cutting edges 
    cut_edges = {}
    for ei, dt in require_cut.items():
        plot_dot = PLOT_EVERY
        if VERBOSE:
            print "====== EDGE CUT"
            print ei, edges[ei]["nodes"], dt

        for end_cut in set([d[0] for d in dt]):
            if end_cut == edges[ei]["edge"][0]:
                end_point = 0
            elif end_cut == edges[ei]["edge"][1]:
                end_point = 1
            else:
                end_point = None
                raise Warning("Wrong end point!") 
            cut_point, plotted_dot = getCutPoint(edges[ei]["edge"], end_point, edges[ei]["nodes"], sx, sy, gridH, gridWps, FACT_CUT, edges[ei], plot_dot=plot_dot)
            if cut_point is not None:
                cut_edges[(ei, end_point)] = cut_point

        if plotted_dot: 
            for n in edges[ei]["nodes"]:           
                pis = polys[n]
                for pi in pis[0]:
                    if edges[abs(pi)]["far"] == -1:
                        c = "b"
                        # print edges[abs(pi)]
                    elif edges[abs(pi)]["far"] == 1:
                        c = "c"
                        # print edges[abs(pi)]
                    elif edges[abs(pi)]["far"] == 2:
                        c = "m"
                        # print edges[abs(pi)]
                    else:
                        c = "r"
                    x, y = zip(*edges[abs(pi)]["edge"])
                    plt.plot(x, y, c)
            plt.show()


    final_polys = {}
    final_details = {}
    ## constructing the polygons
    for node, pols in polys.items():
        if pols is None:
            final_polys[node] = [getPolyRect(sx[node], sy[node], gridH, gridWps, FACT_ALONE)]                
            final_details[node] = [[{"range": (0, 4), "eis": edges_ids[node]}]]
        else:
            current = []
            current_pis = []
            # org = []
            for pis in pols:
                tmp = []
                tmpis = []
                last = [None]
                # current.append([])
                # org.append([])                
                for pi in pis:
                    # org_edge = (edges[abs(pi)]["edge"][0], edges[abs(pi)]["edge"][1])
                    # if pi < 0:
                    #     org_edge = (org_ed ge[1], org_edge[0])
                    # org[-1].append(org_edge)
                    
                    if edges[abs(pi)]["far"] == 0:
                        edge = [edges[abs(pi)]["edge"][0], edges[abs(pi)]["edge"][1]]
                        if (abs(pi), 0) in cut_edges:
                            edge[0] = cut_edges[(abs(pi), 0)]
                        if (abs(pi), 1) in cut_edges:
                            edge[1] = cut_edges[(abs(pi), 1)]
                        if pi < 0:
                            edge = [edge[1], edge[0]]
                            
                        tmp.append(tuple(edge))
                        if len(last) > 1:
                            tmpis.append(last)
                            last = [None]
                        tmpis.append([pi])
                    else:
                        last.append(pi)
                if len(last) > 1:
                    tmpis.append(last)

                ### HERE
                filled, filled_pis = fill_gaps(tmp, tmpis, node, sx, sy, edges)
                current.append(filled)
                current_pis.append(filled_pis)
                # if len(current[-1]) == 1:
                #     for oe in org[-1]:
                #         x,y = zip(*oe)
                #         plt.plot(x,y,"b:")
                #     for oe in current[-1]:
                #         x,y = zip(*oe)
                #         plt.plot(x,y,"g--")

                #     x,y = zip(*filled)
                #     plt.plot(x,y,"r")
                #     plt.plot(sx[node],sy[node],"ko")
                #     plt.show()

            final_polys[node] = current
            final_details[node] = current_pis
    edges.pop(0)
    return final_polys, final_details, edges



#Run this for instance as "python prepare_polygons.py ~/coords.csv ~/poly_coords.csv - map"
if __name__=="__main__":
    
    NAMES_CID = 0
    LAT_CID = 2
    LNG_CID = 1
    SEP = ","
    
    REP = "./"

    #### EUROPE
    GRIDH_PERCENTILE = 20
    GRIDW_FACT = 1.3
    
    COORDS_FN = "coords_EU.csv"
    POLY_FN = "poly_coords_EU.csv"
    EDGES_FN = "poly_edges_EU.csv"

    # #### WORLD
    # GRIDH_PERCENTILE = 50
    # GRIDW_FACT = 1.

    # COORDS_FN = "coords.csv"
    # POLY_FN = "poly_coords.csv"
    # EDGES_FN = "poly_edges.csv"

    MK_MAP = True
    
    # POLY_FN = None
    # EDGES_FN = None
    # MK_MAP = False


    if len(sys.argv) == 2:
        REP = sys.argv[1]
    elif len(sys.argv) > 1:
        COORDS_FN = sys.argv[1]
        
    if len(sys.argv) > 2:
        if sys.argv[2] != "-":
            POLY_FN = sys.argv[2]
    if len(sys.argv) > 3:
        if sys.argv[3] != "-":
            EDGES_FN = sys.argv[3]
    if len(sys.argv) > 4:
        if sys.argv[4] == "map":
            MK_MAP = True
    

    print REP, COORDS_FN, POLY_FN, EDGES_FN, MK_MAP

    PointsMap, PointsIds = loadCoords(REP+COORDS_FN, SEP, LAT_CID, LNG_CID, NAMES_CID)
    reverseIds = dict([(v,k) for (k,v) in PointsIds.items()])
    final_polys, final_details, edges = compute_polys(PointsMap)
    
    nodes = sorted(final_polys.keys())    
    if POLY_FN is not None:
        with open(REP+POLY_FN, "w") as fp:
            for node in nodes:
                ex, ey = ([],[])
                for pl in final_polys[node]:
                    exi, eyi = zip(*pl)
                    ex.extend(exi)
                    ey.extend(eyi)

                fp.write("\"%s\",\"%s\",\"%s\"\n" % (PointsIds[node], 
                               ":".join(["%s" % x for x in ex]),
                               ":".join(["%s" % y for y in ey])))

    if EDGES_FN is not None:
        with open(REP+EDGES_FN, "w") as fp:
            for ei, dt in enumerate(edges):
                nA = PointsIds[dt["nodes"][0]] if dt["nodes"][0] > -1 else "None"
                nB = PointsIds[dt["nodes"][1]] if dt["nodes"][1] > -1 else "None"
                ex, ey = zip(*dt["edge"])
                fp.write("%s,\"%s\",\"%s\",%s,\"%s\",\"%s\"\n" % (ei+1, nA, nB, dt["far"],
                               ":".join(["%s" % x for x in ex]),
                               ":".join(["%s" % y for y in ey])))


        parts = EDGES_FN.split(".")
        parts[-2] += "_details"
        filename = ".".join(parts)
        with open(REP+filename, "w") as fp:            
            for node in nodes:
                for bi, blocks in enumerate(final_details[node]):
                    for bbi, block in enumerate(blocks):
                        fp.write("\"%s\",%s,%s,%s,%s,%s\n" % (PointsIds[node], bi, bbi, block["range"][0], block["range"][1], 
                                    ":".join(["%s" % x for x in block["eis"]])))


    if MK_MAP:
        for node, pls in final_polys.items():                
            for pl in pls:
                ex,ey = zip(*pl)
                plt.plot(ex, ey, "b")
            plt.plot(PointsMap[node][0], PointsMap[node][1], "go")
        plt.show()
