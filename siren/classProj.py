### TODO check which imports are needed 
import re, random
import numpy as np
import inspect
from sklearn import (manifold, datasets, decomposition, ensemble, random_projection)
from reremi.classQuery import Query
from reremi.classRedescription import Redescription
from reremi.classData import BoolColM, CatColM, NumColM

import pdb

class ProjFactory:

    @classmethod
    def getProj(self, data, code = None):

        if code is not None:
            tmp = re.match("^(?P<alg>[A-Za-z]*)(?P<par>:.*)?$", code)
            if tmp is not None:
                k = tmp.group("alg")
                params = {"alg": k}
                if tmp.group("par") is not None:
                    params["code"] = tmp.group("par")[1:].strip()
                    for part in tmp.group("par")[1:].split(","):
                        if len(part) > 0:
                            sp = part.split("=")
                            if len(sp) == 1:
                                params[sp[0].strip()] = True
                            elif len(sp) > 1:
                                try:
                                    params[sp[0]] = int(sp[1])
                                except ValueError:
                                    try:
                                        params[sp[0]] = float(sp[1])
                                    except ValueError:
                                        params[sp[0]] = sp[1]
                        
                for cls in Proj.__subclasses__():
                    if re.match("^"+cls.PID+"$",k):
                        return cls(data, params)

        #m = SVDProj
        m = random.choice([p for p in Proj.__subclasses__()
                           if re.match("^(?P<alg>[A-Za-z*.]*)$", p.PID) is not None])
        return m(data, {})

class Proj(object):

    PID = "---"
    def __init__(self, data, params={}):
        self.data = data
        self.params = params

    def getAxisLabel(self, axis=0):
        return None
    def getTitle(self):
        return None


class AxesProj(Proj):

    PID = "-A"
    def __init__(self, data, params={}):
        mat, details, mcols = data.getMatrix()
        self.axis_ids = random.sample(range(len(mat)), 2)

        if params.has_key("code"):
            sidestr = {"0":0, "1":1, "L":0, "R":1, "l":0, "r":1}
            tmpr = re.match("^(?P<side0>[01LRlr])(?P<axis0>[0-9]*)-(?P<side1>[01LRlr])(?P<axis1>[0-9]*)$", params["code"])
            if tmpr is not None:
                axis0 = (sidestr[tmpr.group("side0")], int(tmpr.group("axis0")))
                axis1 = (sidestr[tmpr.group("side1")], int(tmpr.group("axis1")))
                if mcols.has_key(axis0):
                    self.axis_ids[0] = mcols[axis0]
                if mcols.has_key(axis1):
                    self.axis_ids[1] = mcols[axis1]
        sidestr = {0: "L", 1:"R"}
        self.codes = ["%s%d" % (sidestr[details[self.axis_ids[0]][0]], details[self.axis_ids[0]][1]),
                       "%s%d" % (sidestr[details[self.axis_ids[1]][0]], details[self.axis_ids[1]][1])]
        if data.hasNames():
            sidestr = {0: "LHS", 1:"RHS"}
            names = data.getNames()
            self.labels = ["%s %s" % (sidestr[details[self.axis_ids[0]][0]], names[details[self.axis_ids[0]][0]][details[self.axis_ids[0]][1]]),
                           "%s %s" % (sidestr[details[self.axis_ids[1]][0]], names[details[self.axis_ids[1]][0]][details[self.axis_ids[1]][1]])]
        else:
            self.labels = self.codes

        self.coords_proj = [mat[self.axis_ids[0]], mat[self.axis_ids[1]]]
        for side in [0,1]:
            if details[self.axis_ids[side]][2] != NumColM.type_id:
                self.coords_proj[side] += 0.33*np.random.rand(len(self.coords_proj[side])) 

    def getAxisLabel(self, axi):
        return "%s" % self.labels[axi]
    
    def getCode(self):
        return "%s:%s-%s" % (self.PID, self.codes[0], self.codes[1])

    def getAxisLims(self):
        return (min(self.coords_proj[0]), max(self.coords_proj[0]), min(self.coords_proj[1]), max(self.coords_proj[1]))

    def getCoords(self, axi=None, ids=None):
        if axi is None:
            return self.coords_proj
        elif ids is None:
            return self.coords_proj[axi]
        return self.coords_proj[axi][ids]


class SVDProj(Proj):

    PID = "-S"

    def __init__(self, data, params={}):
        self.params = params
        self.params["alg"] = "S"
        self.stypes=[NumColM.type_id]
        self.ables=True
        if params.has_key("A"):
            self.stypes = None
        if params.has_key("a"):
            self.ables = False

        mat, details, mcol = data.getMatrix(types=self.stypes, only_able=self.ables)
        tt = np.std(mat, 1)
        tt[np.where(tt == 0)] = 1
        matn = (mat - np.tile(np.mean(mat, 1), (mat.shape[1], 1)).T)/np.tile(tt, (mat.shape[1], 1)).T
        U, s, V = np.linalg.svd(matn, full_matrices=False)
        tmp = np.dot(U[:2],matn)
        self.coords_proj = (tmp[0], tmp[1])

    def getAxisLabel(self, axi):
        return "dimension %d" % (axi+1)
    
    def getCode(self):
        tt = "%s:" % self.params["alg"]
        if self.stypes is None:
            tt += "A,"
        if not self.ables:
            tt += "a,"
        return tt.strip(":, ")

    def getAxisLims(self):
        return (min(self.coords_proj[0]), max(self.coords_proj[0]), min(self.coords_proj[1]), max(self.coords_proj[1]))

    def getCoords(self, axi=None, ids=None):
        if axi is None:
            return self.coords_proj
        elif ids is None:
            return self.coords_proj[axi]
        return self.coords_proj[axi][ids]


class SKProj(Proj):

    PID = "SK.*"

    def __init__(self, data, params={}):
        self.title_str = None
        self.params = params
        self.stypes=[NumColM.type_id]
        self.ables=True
        if params.has_key("A"):
            self.stypes = None
        if params.has_key("a"):
            self.ables = False

        mat, details, mcol = data.getMatrix(types=self.stypes, only_able=self.ables)
        tt = np.std(mat, 1)
        tt[np.where(tt == 0)] = 1
        matn = (mat - np.tile(np.mean(mat, 1), (mat.shape[1], 1)).T)/np.tile(tt, (mat.shape[1], 1)).T

        alg = None
        if params.has_key("alg"):
            for name, val in inspect.getmembers(self):
                if re.match("get"+params["alg"]+"Proj", name) is not None and alg is None:
                    alg = val
        if alg is None:
            name, val = random.choice([(n, v) for n, v in inspect.getmembers(self)
                               if re.match("get(?P<alg>.*)Proj", n) is not None])
            self.params["alg"] = re.match("get(?P<alg>.*)Proj", name).group("alg")
            alg = val

        X_pro, err = alg(matn.T, params)
        self.coords_proj = (X_pro[:,0], X_pro[:,1])

    def getTitle(self):
        return self.title_str
    
    def getCode(self):
        tt = "%s:" % self.params["alg"]
        if self.stypes is None:
            tt += "A,"
        if not self.ables:
            tt += "a,"
        for k,v in self.params.items():
            if k not in ["A", "a", "code", "alg"]:
                if type(v) != bool:
                    tt += "%s=%s," % (k,v)
                else:
                    tt += "%s," % k
        return tt.strip(":, ")

    def getAxisLims(self):
        return (min(self.coords_proj[0]), max(self.coords_proj[0]), min(self.coords_proj[1]), max(self.coords_proj[1]))

    def getCoords(self, axi=None, ids=None):
        if axi is None:
            return self.coords_proj
        elif ids is None:
            return self.coords_proj[axi]
        return self.coords_proj[axi][ids]

    ### The various projections with sklearn
    #----------------------------------------------------------------------
    # Random 2D projection using a random unitary matrix
    def getSKrandProj(self, X, params={}):
        self.title_str = "Random projection"
        rp = random_projection.SparseRandomProjection(n_components=2, random_state=params.get("rand", random.randint(1, 100)))
        X_projected = rp.fit_transform(X)
        return X_projected, 0

    #----------------------------------------------------------------------
    # Projection on to the first 2 principal components
    def getSKpcaProj(self, X, params={}):
        self.title_str = "PCA projection"
        X_pca = decomposition.RandomizedPCA(n_components=2, random_state=params.get("rand", random.randint(1, 100))).fit_transform(X)
        return X_pca, 0

    #----------------------------------------------------------------------
    # Isomap projection of the digits dataset
    def getSKisomapProj(self, X, params={}):
        self.title_str = "Isomap projection"
        X_iso = manifold.Isomap(n_neighbors=params.get("#k",4), n_components=2).fit_transform(X)
        return X_iso, 0

    #----------------------------------------------------------------------
    # Locally linear embedding of the digits dataset
    def getSKlleProj(self, X, params={}):
        ### methods: standard, modified, hessian, ltsa
        self.title_str = "%s LLE embedding" % params.get("method", 'standard')
        clf = manifold.LocallyLinearEmbedding(n_components=2, n_neighbors=params.get("#k",4),
                                              method=params.get("method", 'standard'), random_state=params.get("rand", random.randint(1, 100)))
        X_lle = clf.fit_transform(X)
        return X_lle, clf.reconstruction_error_

    #----------------------------------------------------------------------
    # MDS  embedding of the digits dataset
    #### SLOW!!!
    # def getSKmdsProj(self, X, params={}):
    #     self.title_str = "MDS embedding"
    #     print("Computing MDS embedding")
    #     clf = manifold.MDS(n_components=2, n_init=params.get("#R",1), max_iter=params.get("#I",100))
    #     X_mds = clf.fit_transform(X)
    #     return X_mds, clf.stress_

    #----------------------------------------------------------------------
    # Random Trees embedding of the digits dataset
    def getSKrtreeProj(self, X, params={}):
        self.title_str = "Totally Random Trees embedding"
        hasher = ensemble.RandomTreesEmbedding(n_estimators=params.get("#E",200),
                                               random_state=params.get("rand", random.randint(1, 100)),
                                               max_depth=params.get("dep",5))
        X_transformed = hasher.fit_transform(X)
        pca = decomposition.RandomizedPCA(n_components=2)
        X_reduced = pca.fit_transform(X_transformed)
        return X_reduced, 0

    #----------------------------------------------------------------------
    # Spectral embedding of the digits dataset
    def getSKspectralProj(self, X, params={}):
        ### eigen solvers: arpack, lobpcg
        self.title_str = "Spectral embedding"
        embedder = manifold.SpectralEmbedding(n_components=2, random_state=params.get("rand", random.randint(1, 100)))
        X_se = embedder.fit_transform(X)
        return X_se, 0

