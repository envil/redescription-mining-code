import numpy as np
# The recommended way to use wx with mpl is with the WXAgg
# backend. 
import matplotlib
import scipy.spatial.distance
import scipy.cluster
import itertools

from reremi.classData import BoolColM, CatColM, NumColM

import pdb

def pickVars(mat, details, side_cols=None, only_enabled=False, only_nzstd=True):
    types_ids = {BoolColM.type_id: [], CatColM.type_id:[], NumColM.type_id:[]}
    for i, dt in enumerate(details):
        if ( dt["enabled"] or not only_enabled ) and ( (side_cols is None) or ((dt["side"], None) in side_cols) or ( (dt["side"], dt["col"]) in side_cols)):
            if only_nzstd and np.std(mat[i,:]) != 0:
                types_ids[dt["type"]].append(i)
    types_ids["all"] = list(itertools.chain(*types_ids.values()))
    return types_ids


def getDistances(mat, details, side_cols=None, parameters=None, only_enabled=False, parts=None):
    if parameters is None:
        parameters = [{"type": "all", "metric": "seuclidean", "weight": 1}]

        # parameters = [{"type": BoolColM.type_id, "metric": "hamming", "weight": 1},
        #               {"type": CatColM.type_id, "metric": "hamming", "weight": 1},
        #               {"type": NumColM.type_id, "metric": "seuclidean", "weight": 1}]
        
    types_ids = pickVars(mat, details, side_cols, only_enabled)

    d = np.zeros((mat.shape[1]*(mat.shape[1]-1)/2.0))
    for typ in parameters:
        if len(types_ids.get(typ["type"], [])) > 0:
            if typ["weight"] == "p":
                weight = 1/len(types_ids[typ["type"]])
            else:
                weight = typ["weight"]
            d += weight*scipy.spatial.distance.pdist(mat[types_ids[typ["type"]],:].T, metric=typ["metric"])
    if parts is not None:
        d += 10*max(d)*scipy.spatial.distance.pdist(np.array([parts]).T, "hamming")
    return d

def withen(mat):
    tt = np.std(mat, 1)
    tt[np.where(tt == 0)] = 1
    return (mat - np.tile(np.mean(mat, 1), (mat.shape[1], 1)).T)/np.tile(tt, (mat.shape[1], 1)).T


def linkage(mat, details, side_cols=None, osupp=None):
    mat = mat[:,:300]
    osupp = osupp[:300]
    
    d = getDistances(mat, details, side_cols, parts=osupp)
    Z = scipy.cluster.hierarchy.linkage(d)
    return Z, d

    ### OTHER PACK
    # d = toolsMath.getDistances(mat, details, side_cols, parts=osupp)
    # types_ids = toolsMath.pickVars(mat, details, side_cols)
    # Z = scipy.cluster.hierarchy.centroid(mat[types_ids["all"],:].T)


def sample(Z, t, d):
    T = scipy.cluster.hierarchy.fcluster(Z, t, criterion="maxclust")
    clusters = [[] for i in range(max(T))]
    for i,c in enumerate(T):
        clusters[c-1].append(i)
    D = scipy.spatial.distance.squareform(d)
    reps = []
    for cluster in clusters:
        if len(cluster) > 1:
            reps.append(cluster[np.argmin(np.mean(D[cluster,:], 0)[cluster])])
        else:
            reps.extend(cluster)
    return reps, clusters
