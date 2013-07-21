import pdb
import numpy as np
import voronoi_poly
import matplotlib.pyplot as plt
import scipy.spatial.distance
from shapely import geometry
from shapely.ops import polygonize
from shapely.geos import TopologicalError

def makePolys(pdp, boundaries):
    PointsMap=dict([(p, (c1,c2)) for (p, c1, c2) in pdp])
    sx, sy = zip(*PointsMap.values())
    D=scipy.spatial.distance.squareform(scipy.spatial.distance.pdist(np.array([sx,sy]).T, metric="euclidean"))
    nnvs = []
    nds = []
    for i in range(D.shape[0]):
        nnvs.append(np.argsort(D[:,i])[1:3])
    for i in range(D.shape[0]):
        nds.append(min([D[i,j] for j in nnvs[i]]+[D[nnvs[j][0],j] for j in nnvs[i]]+[D[nnvs[j][1],j] for j in nnvs[i]]))


    vl=voronoi_poly.VoronoiPolygonsMod(PointsMap, BoundingBox=boundaries)
    # margin = 1
    # vl=voronoi_poly.VoronoiPolygonsMod(PointsMap, BoundingBox=[max(sy)+margin, min(sx)-margin, min(sy)-margin, max(sx)+margin])

    ready = {}
    for s, obj in vl.items():
        pos = obj["info"]
        dst = nds[pos]
        fact = 1.41
        ready[pos] = []

        tmc = getContours(obj['obj_polygon'])
        for data_ct in tmc:
            data_poly = geometry.Polygon(data_ct)
            rst = [(obj["coordinate"][0]+x*dst*fact/2, obj["coordinate"][1]+y*dst*fact/2)
                   for (x,y) in [(-1,-1), (-1,1), (1,1), (1,-1), (-1,-1)]]
            restrict_poly = geometry.Polygon(rst)
            try:
                inter_p = restrict_poly.intersection(data_poly)
                ready[pos].append(list(inter_p.exterior.coords))
            except TopologicalError:
                mdi = np.max(scipy.spatial.distance.cdist(np.array([obj["coordinate"]]), data_ct, metric="euclidean"))
                if mdi > fact*dst:
                    ready[pos].append(rst)
                else:
                    ready[pos].append(data_ct)
    return ready



def getContours(obj_polygon):
    ends_map = {}
    for edge in obj_polygon:
        for end in [0,1]:
            if not ends_map.has_key(edge[end]):
                ends_map[edge[end]] = set([edge[1-end]])
            else:
                ends_map[edge[end]].add(edge[1-end])

    vertices = ends_map.keys()
    ### remove hanging nodes
    for v in vertices:
        if len(ends_map[v]) == 0:
            del ends_map[v]
        elif len(ends_map[v]) == 1:
            ends_map[ends_map[v].pop()].remove(v)
            del ends_map[v]

    contours = []
    loop = False
    contour = []
    while len(ends_map) > 0:
        if len(contour) == 0:
            contour = [ends_map.keys()[0]]
        while not loop and len(ends_map) > 0:
            if len(ends_map[contour[-1]].intersection(contour)) == 1:
                nv = ends_map[contour[-1]].intersection(contour).pop()
                ends_map[contour[-1]].remove(nv)
                loop = True
            else:
                nv = ends_map[contour[-1]].pop()
            if len(ends_map[contour[-1]]) == 0:
                del ends_map[contour[-1]]
            ends_map[nv].remove(contour[-1])
            contour.append(nv)

        if len(ends_map[nv]) == 0:
            del ends_map[nv]
        prev_p = contour.index(nv)
        contours.append(contour[prev_p:]+[nv])
        del contour[prev_p:]
        loop = False
    return contours

