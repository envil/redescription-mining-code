import numpy as np
# The recommended way to use wx with mpl is with the WXAgg
# backend. 
import random
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


def getDistances(mat, details, side_cols=None, parameters=None, only_enabled=False, parts=None, pivots=None):
    if parameters is None:
        parameters = [{"type": "all", "metric": "seuclidean", "weight": 1}]

        # parameters = [{"type": BoolColM.type_id, "metric": "hamming", "weight": 1},
        #               {"type": CatColM.type_id, "metric": "hamming", "weight": 1},
        #               {"type": NumColM.type_id, "metric": "seuclidean", "weight": 1}]
        
    types_ids = pickVars(mat, details, side_cols, only_enabled)

    if pivots is None: 
        d = np.zeros((mat.shape[1]*(mat.shape[1]-1)/2.0))
    else:
        d = np.zeros((mat.shape[1], len(pivots)))
    for typ in parameters:
        if len(types_ids.get(typ["type"], [])) > 0:
            if typ["weight"] == "p":
                weight = 1/len(types_ids[typ["type"]])
            else:
                weight = typ["weight"]
            if pivots is None: 
                d += weight*scipy.spatial.distance.pdist(mat[types_ids[typ["type"]],:].T, metric=typ["metric"])
            else:
                tmp = mat[types_ids[typ["type"]],:]
                d += weight*scipy.spatial.distance.cdist(tmp.T, tmp[:,pivots].T, metric=typ["metric"])
    if parts is not None:
        if pivots is None: 
            d += 10*np.max(d)*scipy.spatial.distance.pdist(np.array([parts]).T, "hamming")
        else:
            d += 10*np.max(d)*scipy.spatial.distance.cdist(np.array([parts]).T, np.array([[parts[p] for p in pivots]]).T, "hamming")
    return d


def withen(mat):
    tt = np.std(mat, 0)
    tt[np.where(tt == 0)] = 1
    return (mat - np.tile(np.mean(mat, 0), (mat.shape[0], 1)))/np.tile(tt, (mat.shape[0], 1))

def withenR(mat):
    tt = np.std(mat, 1)
    tt[np.where(tt == 0)] = 1
    return (mat - np.tile(np.mean(mat, 1), (mat.shape[1], 1)).T)/np.tile(tt, (mat.shape[1], 1)).T


def linkageZds(mat, details, side_cols=None, osupp=None, step=500):    
    spids = set()
    if osupp is not None:
        spids = set(np.unique(osupp, return_index=True)[1])
        vsupp = np.array(osupp)
    pivots = list(spids.union(range(0,mat.shape[1], step)))     
    d = getDistances(mat, details, side_cols, parts=osupp, pivots=pivots)
    aff = np.argmin(d, 1)
    
    counts = {}
    used = []
    for i in range(aff.shape[0]):
        if counts.get(aff[i], {"count": 2*step})["count"] > 1.25*step:
            counts[aff[i]] = {"to": len(used), "count": 0}
            used.append(aff[i])
        counts[aff[i]]["count"]+=1
        aff[i] = counts[aff[i]]["to"]
    
    ids_cls = [np.where(aff == cl)[0] for cl in np.unique(aff)]

    zds = []
    for ids in ids_cls:
        if len(ids) == 1:
            d = np.array([0])
        else:
            d = getDistances(mat[:,ids], details, side_cols, parts=vsupp[ids])
        if sum(d**2) == 0:
            ids = ids.tolist()
            random.shuffle(ids)
            zds.append({"Z":None, "d":None, "ids": ids})
        else:
            Z = scipy.cluster.hierarchy.linkage(d)
            zds.append({"Z":Z, "d":d, "ids": ids.tolist()})
    return zds


def linkage(mat, details, side_cols=None, osupp=None):    
    d = getDistances(mat, details, side_cols, parts=osupp)
    if sum(d**2) == 0:
        return None, None
    Z = scipy.cluster.hierarchy.linkage(d)
    return Z, d

    ### OTHER PACK
    # d = toolMath.getDistances(mat, details, side_cols, parts=osupp)
    # types_ids = toolMath.pickVars(mat, details, side_cols)
    # Z = scipy.cluster.hierarchy.centroid(mat[types_ids["all"],:].T)


def sampleZds(zds, t):
    all_reps = []
    all_clusts = []
    for zd in zds:
        if t == 1:
            all_reps.extend(zd["ids"])
        elif round(t*len(zd["ids"])) > 0:
            nb = round(t*len(zd["ids"]))
            if zd["Z"] is None:
                all_reps.extend(zd["ids"][:int(nb)+1])
                all_clusts.extend([None for r in range(int(nb)+1)])                
            else:
                treps, tclusts = sample(zd["Z"], nb, zd["d"])
                all_reps.extend([zd["ids"][r] for r in treps])
                all_clusts.extend(tclusts)
    return all_reps, all_clusts

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



####
#### SHARE AMONG GROUPS
    # tfrom = len(ids_cls)-1
    # tto = 0
    # max_c = 
    # while tfrom > 0 and len(ids_cls[tfrom]) > max_c:
    #     tmp = ids_cls[tfrom][max_c:]
    #     ids_cls[tfrom] = ids_cls[tfrom][:max_c]
    #     while len(tmp) > 0 and tto < len(ids_cls):
    #         sto = max_c-len(ids_cls[tto])
    #         if sto > 0:
    #             ids_cls[tto].extend(tmp[:sto])
    #             tmp = tmp[sto:]
    #         else:
    #             tto +=1
