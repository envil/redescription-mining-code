#! /usr/local/bin/python

import sys
import voronoi_poly
import pdb
import numpy
import matplotlib.pyplot as plt

PLOT = False
VERBOSE = False

GRT_CIR = 6370.997

ANGLE_TOL = 0.05
FACT_CUT = 0.8
FACT_ALONE = 0.5

def getInterYV(x1, y1, x2, y2, xv):
    return y1+(xv-x1)*(y2-y1)/(x2-x1)
def getInterXH(x1, y1, x2, y2, yh):
    return x1+(yh-y1)*(x2-x1)/(y2-y1)

def getCutPoint(edge, end_cut, nodes, sx, sy, minH, minWs, f):
    if end_cut is None:
        return None
    nA, nB = nodes
    midX = (sx[nA] + sx[nB])/2.
    midY = (sy[nA] + sy[nB])/2.

    (xv, yv) = (edge[end_cut][0], edge[end_cut][1])
    (xh, yh) = (edge[end_cut][0], edge[end_cut][1])
    if edge[end_cut][0] < edge[1-end_cut][0]: ### end to cut is to the left
        xv = midX - f*getRectW(midX, midY, minH, minWs)
        yv = getInterYV(edge[0][0], edge[0][1], edge[1][0], edge[1][1], xv)
    elif edge[end_cut][0] > edge[1-end_cut][0]: ### end to cut is to the right
        xv = midX + f*getRectW(midX, midY, minH, minWs)
        yv = getInterYV(edge[0][0], edge[0][1], edge[1][0], edge[1][1], xv)
    if edge[end_cut][1] < edge[1-end_cut][1]: ### end to cut is at the bottom
        yh = midY - f*getRectH(midX, midY, minH, minWs)
        xh = getInterXH(edge[0][0], edge[0][1], edge[1][0], edge[1][1], yh)
    elif edge[end_cut][1] > edge[1-end_cut][1]: ### end to cut is at the top
        yh = midY + f*getRectH(midX, midY, minH, minWs)
        xh = getInterXH(edge[0][0], edge[0][1], edge[1][0], edge[1][1], yh)

    if xv < numpy.minimum(edge[0][0], edge[1][0]) or xv > numpy.maximum(edge[0][0], edge[1][0]) or yv < numpy.minimum(edge[0][1], edge[1][1]) or yv > numpy.maximum(edge[0][1], edge[1][1]):
        (xv, yv) = (edge[end_cut][0], edge[end_cut][1])
    if xh < numpy.minimum(edge[0][0], edge[1][0]) or xh > numpy.maximum(edge[0][0], edge[1][0]) or yh < numpy.minimum(edge[0][1], edge[1][1]) or yh > numpy.maximum(edge[0][1], edge[1][1]):
        (xh, yh) = (edge[end_cut][0], edge[end_cut][1])

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
    if PLOT:        
        plt.plot([sx[nA], midX, sx[nB]], [sy[nA], midY, sy[nB]], ":ko")
        x, y = zip(*edge)
        plt.plot(x, y, "y", linewidth=3)
        plt.plot(edge[end_cut][0], edge[end_cut][1], "yo")
        if select_cut is not None:
            plt.plot(select_cut[0], select_cut[1], "rx")

        box = getPolyRect(midX, midY, minH, minWs, f)
        ex, ey = zip(*box)
        plt.plot(ex, ey, 'k:')
    return select_cut

def getDistance(x1, y1, x2, y2):
    return greatCircleDistance(x1, y1, x2, y2)

def greatCircleDistance(x1, y1, x2, y2):
    x1 = numpy.radians(x1)
    y1 = numpy.radians(y1)
    x2 = numpy.radians(x2)
    y2 = numpy.radians(y2)
    angle1 = numpy.arccos(numpy.sin(x1) * numpy.sin(x2) + numpy.cos(x1) * numpy.cos(x2) * numpy.cos(y1 - y2))
    return  angle1*GRT_CIR

def getRectW(x, y, minH, minWs):
    return getW(y, minWs)*360./(2*numpy.pi*GRT_CIR)
def getRectH(x, y, minH, minWs):
    return minH*360./(2*numpy.pi*GRT_CIR)
def getPolyRect(x, y, minH, minWs, f):
    w = getRectW(x, y, minH, minWs)
    h = getRectH(x, y, minH, minWs)
    return [(x+fx*f*w, y+fy*f*h) for (fx, fy) in [(1,1), (1,-1), (-1,-1), (-1,1), (1,1)]]


def angleCosSin(x1, y1, x2, y2):
    ac = (x2-x1)
    bc = (y2-y1)
    return ac/numpy.sqrt(ac**2+bc**2), bc/numpy.sqrt(ac**2+bc**2)


def getW(y, minWs):
    i = 0
    while i < len(minWs)-1 and y < minWs[i][0]:
        i += 1
    return minWs[i][1]

def getDistanceThres(y, minH, minWs):
    return 1.5*numpy.sqrt(getW(y, minWs)**2+minH**2)

def ortho_prj(x1, y1, x2, y2, xn, yn):
    xA, yA = (x2-x1, y2-y1)
    xB, yB = (xn-x1, yn-y1)
    lA = numpy.sqrt(xA**2+yA**2)
    lB = numpy.sqrt(xB**2+yB**2)
    cosA = (xA*xB+yA*yB)/(lA*lB)
    return (x1 + cosA*lB*xA/lA, y1 + cosA*lB*yA/lA)

def fill_gaps(poly, node, sx, sy):
    if len(poly) == 1:
        xp, yp = ortho_prj(poly[0][0][0], poly[0][0][1], poly[0][1][0], poly[0][1][1], sx[node], sy[node])
        tx, ty = (2.*(sx[node]-xp), 2.*(sy[node]-yp))
        filled = [poly[0][0], poly[0][1], (poly[0][1][0]+tx, poly[0][1][1]+ty), (poly[0][0][0]+tx, poly[0][0][1]+ty), poly[0][0]]
    elif len(poly) == 2:
        if poly[0][1] == poly[1][0]: ### fill in second to last?
            corner = poly[0][1]
            new_corner = (corner[0]+ 2*(sx[node]-corner[0]), corner[1]+ 2*(sy[node]-corner[1]))
            filled = [poly[0][0], poly[0][1], poly[1][1], new_corner, poly[0][0]]
        elif poly[0][0] == poly[1][1]:
            corner = poly[1][1]
            new_corner = (corner[0]+ 2*(sx[node]-corner[0]), corner[1]+ 2*(sy[node]-corner[1]))
            filled = [poly[1][0], poly[1][1], poly[0][1], new_corner, poly[1][0]]
        else:
            filled = [poly[0][0], poly[0][1], poly[1][0], poly[1][1], poly[0][0]]
    else:
        filled = list(poly[0])
        for i in range(1, len(poly)):
            if poly[i][0] != filled[-1]:
                filled.append(poly[i][0])
            filled.append(poly[i][1])
        if filled[-1] != filled[0]:
            filled.append(filled[0])
    return filled
        
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

    fps = []
    fpis = []
    while len(gpoly) > 0:     
        prev_node = sorted(gpoly.keys())[0]
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
        if len(gpoly) > 0:
            pdb.set_trace()
            print gpoly
    return fps, fpis

# for dot in [(0., 0., 0., 1.), (0., 0., 1., 0.), (70., 0., 70., 1.), (70., 0., 71., 0.)]:
#     print dot, greatCircleDistance(dot[0], dot[1], dot[2], dot[3]), angleCosSin(dot[0], dot[1], dot[2], dot[3])
# pdb.set_trace()


    
def loadCoords(coords_fn):    
    #Creating the PointsMap from the input data
    PointsMap={}
    PointsIds={}
    fp=open(coords_fn, "r")
    for line in fp:
        data=line.strip().split(",")
        if True:
        # if float(data[1]) > 70: # and float(data[2]) < 15:
            try:
                PointsIds[len(PointsMap)]=data[0] 
                PointsMap[len(PointsMap)]=(float(data[2]),float(data[1]))               
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
    minH = float("Inf")
    edges = [{"edge": (None, -1)}]
    horz_edges = []
    # graph = {}
    for edg, sts in map_edges.items():
        if len(sts) == 1: ## border edge
            nodes = (sts[0], -1)
            dst = EXT_D+1
            cos, sin = (0,0)
            far = -1
        else: ## other edge
            nodes = (sts[0], sts[1])
            dst = getDistance(sx[sts[0]], sy[sts[0]], sx[sts[1]], sy[sts[1]])
            if dst > MAX_D:
                MAX_D = dst
            cos, sin = angleCosSin(sx[sts[0]], sy[sts[0]], sx[sts[1]], sy[sts[1]])
            far = 0
            if numpy.abs(cos) > (1-ANGLE_TOL): ## if near-horizontal
                horz_edges.append((-numpy.abs(sy[sts[0]]), dst))
            elif numpy.abs(cos) < ANGLE_TOL and dst < minH: ## if near-vertical
                minH = dst

        # for ni in [0,1]:            
        #     if nodes[ni] not in graph:
        #         graph[nodes[ni]] = []
        #     graph[nodes[ni]].append((nodes[1-ni], len(edges)))                
        edges.append({"n_dist": dst, "angle": numpy.abs(cos), "nodes": nodes, "edge": edg, "far": far})

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
    horz_edges.sort(reverse=True)
    lat, w = horz_edges.pop()
    minWs = [(-lat, w)]
    while len(horz_edges) > 0:
        lat, w = horz_edges.pop()
        if w < minWs[-1][1]:
            minWs.append((-lat, w))
    # print minH, minWs

    # minH = 42.9790700991
    # minWs = [(80.359999999999999, 333.59850268452698), (79.939999999999998, 271.0695203722704), (79.489999999999995, 260.78274638299251), (79.040000000000006, 250.54621716951834), (78.590000000000003, 242.44403844367775), (78.549999999999997, 207.95823843747908), (78.099999999999994, 182.35959382689566), (70.980000000000004, 153.44892651288208), (70.530000000000001, 149.00113154145825), (70.079999999999998, 146.77723405579687)]

    
    ### from the detected grid sizes, go through edges and mark far-apart neighbors
    for ei in range(1, len(edges)):
        dt = edges[ei]
        lw = 1
        if dt["nodes"][1] >= 0:
            y = (sy[dt["nodes"][0]]+sy[dt["nodes"][1]])/2.
            th = getDistanceThres(y, minH, minWs) ### max distance to be considered neighbors at this latitude
            if dt["n_dist"] > th:
                dt["far"] = 1
                lw = 2
            else:
                ### HERE
                x = (sx[dt["nodes"][0]]+sx[dt["nodes"][1]])/2.
                dstA = numpy.sqrt((dt["edge"][0][0]-x)**2+(dt["edge"][0][1]-y)**2)
                dstB = numpy.sqrt((dt["edge"][1][0]-x)**2+(dt["edge"][1][1]-y)**2)
                dstE = numpy.sqrt((dt["edge"][0][0]-dt["edge"][1][0])**2+(dt["edge"][0][1]-dt["edge"][1][1])**2)
                if dstA+dstB > 2.*dstE:
                    dt["far"] = 2
                    # pdb.set_trace()
                    lw = 6
        else:
            lw = 4
        if PLOT:
            ex,ey = zip(*dt["edge"])
            ci = dt["n_dist"]/MAX_D
            plt.plot(ex, ey, color=cmap(ci), linewidth=lw)
    if PLOT:
        plt.plot(sx, sy, "go")
        plt.show()
    
    require_cut = {}
    polys = {}
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
            ### collect edges that are not far but adjacent to far, which will need to be cut 
            for pi in range(len(poly)):
                for ppi in range(len(poly[pi])-1):
                    if edges[abs(pis[pi][ppi])]["far"] != 0:
                        oei = None
                        if edges[abs(pis[pi][ppi-1])]["far"] == 0:
                            oei = abs(pis[pi][ppi-1])
                            which = poly[pi][ppi]
                            ww = sorted(set(edges[abs(pis[pi][ppi-1])]["edge"]).intersection(edges[abs(pis[pi][ppi])]["edge"]))
                            if len(ww) != 1 or ww[0] != which:
                                pdb.set_trace()
                            if oei not in require_cut:
                                require_cut[oei] = []
                            require_cut[oei].append((which, node, pi, ppi))

                        aft = ppi+1
                        if aft == len(pis[pi]): aft = 0
                        if edges[abs(pis[pi][aft])]["far"] == 0:
                            oei = abs(pis[pi][aft])
                            which = poly[pi][ppi+1]
                            ww = sorted(set(edges[abs(pis[pi][aft])]["edge"]).intersection(edges[abs(pis[pi][ppi])]["edge"]))
                            if len(ww) != 1 or ww[0] != which:
                                pdb.set_trace()
                            if oei not in require_cut:
                                require_cut[oei] = []
                            require_cut[oei].append((which, node, pi, ppi))

        else:
            polys[node] = None #getPolyRect(sx[node], sy[node], minH, minWs, .5)

    ## cutting edges 
    cut_edges = {}
    for ei, dt in require_cut.items():
        if VERBOSE:
            print "====== EDGE CUT"
            print ei, edges[ei]["nodes"], dt
        if PLOT:
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

        for end_cut in set([d[0] for d in dt]):
            if end_cut == edges[ei]["edge"][0]:
                end_point = 0
            elif end_cut == edges[ei]["edge"][1]:
                end_point = 1
            else:
                end_point = None
                raise Warning("Wrong end point!") 
            cut_point = getCutPoint(edges[ei]["edge"], end_point, edges[ei]["nodes"], sx, sy, minH, minWs, FACT_CUT)
            if cut_point is not None:
                cut_edges[(ei, end_point)] = cut_point
        if PLOT:
            plt.show()


    final_polys = {}
    ## constructing the polygons
    for node, pols in polys.items():
        if pols is None:
            final_polys[node] = [getPolyRect(sx[node], sy[node], minH, minWs, FACT_ALONE)]
        else:
            current = []
            # org = []
            for pis in pols:
                tmp = []
                # current.append([])
                # org.append([])                
                for pi in pis:
                    # org_edge = (edges[abs(pi)]["edge"][0], edges[abs(pi)]["edge"][1])
                    # if pi < 0:
                    #     org_edge = (org_edge[1], org_edge[0])
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
                
                filled = fill_gaps(tmp, node, sx, sy)
                current.append(filled)
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
    edges.pop(0)
    return final_polys, edges



#Run this for instance as "python prepare_polygons.py ~/coords.csv ~/poly_coords.csv - map"
if __name__=="__main__":

    COORDS_FN = "coords.csv"
    POLY_FN = "poly_coords.csv"
    EDGES_FN = "poly_edges.csv"
    MK_MAP = True

    POLY_FN = None
    EDGES_FN = None
    MK_MAP = False
    
    if len(sys.argv) > 1:
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
    

    print COORDS_FN, POLY_FN, EDGES_FN, MK_MAP


    PointsMap, PointsIds = loadCoords(COORDS_FN)
    final_polys, edges = compute_polys(PointsMap)

    if POLY_FN is not None:
        with open(POLY_FN, "w") as fp:
            nodes = sorted(final_polys.keys())
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
        with open(EDGES_FN, "w") as fp:
            for dt in edges:
                nA = PointsIds[dt["nodes"][0]] if dt["nodes"][0] > -1 else "None"
                nB = PointsIds[dt["nodes"][1]] if dt["nodes"][1] > -1 else "None"
                fp.write("\"%s\",\"%s\",%s\n" % (nA, nB, dt["far"]))

    if MK_MAP:
        for node, pls in final_polys.items():                
            for pl in pls:
                ex,ey = zip(*pl)
                plt.plot(ex, ey, "b")
            plt.plot(PointsMap[node][0], PointsMap[node][1], "go")
        plt.show()
