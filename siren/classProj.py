### TODO check which imports are needed 
import re, random
import numpy as np
import inspect
from sklearn import (manifold, datasets, decomposition, ensemble, random_projection)
import tsne
from reremi.classQuery import Query
from reremi.classRedescription import Redescription
from reremi.classData import BoolColM, CatColM, NumColM
import toolsMath

import pdb

def all_subclasses(cls):
    return cls.__subclasses__() + [g for s in cls.__subclasses__()
                                   for g in all_subclasses(s)]

class ProjFactory:

    @classmethod
    def getProj(self, data, code = None, logger=None):

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
                        
                for cls in all_subclasses(Proj):
                    if re.match("^"+cls.PID+"$", k):
                        return cls(data, params, logger)

        #m = SVDProj
        cls = random.choice([p for p in all_subclasses(Proj)
                           if re.match("^(?P<alg>[^-S][A-Za-z*.]*)$", p.PID) is not None])
        return cls(data, {}, logger)

class Proj(object):

    PID = "---"
    title_str = "Projection"
    
    def __init__(self, data, params={}, logger=None):
        self.want_to_live = True
        self.data = data
        self.params = params
        self.logger = logger
        self.coords_proj = None
        self.stypes=[NumColM.type_id]
        self.ables=True
        if self.params.has_key("A"):
            self.stypes = None
        if self.params.has_key("a"):
            self.ables = False

    def getAxisLabel(self, axis=0):
        return None
    def getTitle(self):
        return self.title_str

    def getCoords(self, axi=None, ids=None):
        if self.coords_proj is None:
            return self.coords_proj
        if axi is None:
            return self.coords_proj
        elif ids is None:
            return self.coords_proj[axi]
        return self.coords_proj[axi][ids]

    def getAxisLims(self):
        if self.coords_proj is None:
            return (0,1,0,1)
        return (min(self.coords_proj[0]), max(self.coords_proj[0]), min(self.coords_proj[1]), max(self.coords_proj[1]))

    def do(self):
        pass

    def notifyDone(self):
        if self.logger is not None:
            self.logger.printL(1,"Projection ready...", "result")

    def kill(self):
        self.want_to_live = False

    def getCode(self):
        tt = "%s:" % self.PID
        if self.stypes is None:
            tt += "A,"
        if not self.ables:
            tt += "a,"
        for k,v in self.params.items():
            if k not in ["A", "a", "code"]:
                if type(v) != bool:
                    tt += "%s=%s," % (k,v)
                else:
                    tt += "%s," % k
        return tt.strip(":, ")

class AxesProj(Proj):

    PID = "A"
    title_str = "Projection"
        
    def do(self):
        if not self.want_to_live:
            return
        mat, details, mcols = self.data.getMatrix()
        self.axis_ids = random.sample(range(len(mat)), 2)

        if self.params.has_key("code"):
            sidestr = {"0":0, "1":1, "L":0, "R":1, "l":0, "r":1}
            tmpr = re.match("^(?P<side0>[01LRlr])(?P<axis0>[0-9]*)-(?P<side1>[01LRlr])(?P<axis1>[0-9]*)$", self.params["code"])
            if tmpr is not None:
                axis0 = (sidestr[tmpr.group("side0")], int(tmpr.group("axis0")))
                axis1 = (sidestr[tmpr.group("side1")], int(tmpr.group("axis1")))
                if mcols.has_key(axis0):
                    self.axis_ids[0] = mcols[axis0]
                if mcols.has_key(axis1):
                    self.axis_ids[1] = mcols[axis1]
        sidestr = {0: "L", 1:"R"}
        self.codes = ["%s%d" % (sidestr[details[self.axis_ids[0]]["side"]], details[self.axis_ids[0]]["col"]),
                      "%s%d" % (sidestr[details[self.axis_ids[1]]["side"]], details[self.axis_ids[1]]["col"])]
        if self.data.hasNames():
            sidestr = {0: "LHS", 1:"RHS"}
            names = self.data.getNames()
            self.labels = ["%s %s" % (sidestr[details[self.axis_ids[0]]["side"]], names[details[self.axis_ids[0]]["side"]][details[self.axis_ids[0]]["col"]]),
                           "%s %s" % (sidestr[details[self.axis_ids[1]]["side"]], names[details[self.axis_ids[1]]["side"]][details[self.axis_ids[1]]["col"]])]
        else:
            self.labels = self.codes

        self.coords_proj = [mat[self.axis_ids[0]], mat[self.axis_ids[1]]]
        for side in [0,1]:
            if details[self.axis_ids[side]]["type"] != NumColM.type_id:
                self.coords_proj[side] += 0.33*np.random.rand(len(self.coords_proj[side])) 
        self.notifyDone()

    def getAxisLabel(self, axi):
        return "%s" % self.labels[axi]
    
    def getCode(self):
        return "%s:%s-%s" % (self.PID, self.codes[0], self.codes[1])


class SVDProj(Proj):

    PID = "-SVD"
    title_str = "Projection"
    
    def do(self):
        if not self.want_to_live:
            return

        mat, details, mcol = self.data.getMatrix(types=self.stypes, only_able=self.ables)
        matn = toolsMath.withen(mat)
        U, s, V = np.linalg.svd(matn, full_matrices=False)
        tmp = np.dot(U[:2],matn)
        self.coords_proj = (tmp[0], tmp[1])
        self.notifyDone()

    def getAxisLabel(self, axi):
        return "dimension %d" % (axi+1)

### The various projections with sklearn
#----------------------------------------------------------------------
class SKrandProj(Proj):

    PID =  "SKrand"
    title_str = "Random projection"

    def do(self):
        if not self.want_to_live:
            return

        mat, details, mcol = self.data.getMatrix(types=self.stypes, only_able=self.ables)
        matn = toolsMath.withen(mat)

        X_pro, err = self.getX(matn.T)
        self.coords_proj = (X_pro[:,0], X_pro[:,1])
        self.notifyDone()
    
    # Random 2D projection using a random unitary matrix
    def getX(self, X, params={}):
        rp = random_projection.SparseRandomProjection(n_components=2, random_state=self.params.get("rand", random.randint(1, 100)))
        X_projected = rp.fit_transform(X)
        return X_projected, 0

class SKpcaProj(SKrandProj):
    #----------------------------------------------------------------------
    # Projection on to the first 2 principal components

    PID =  "SKpca"
    title_str = "PCA projection"

    def getX(self, X):
        self.title_str = "PCA projection"
        X_pca = decomposition.RandomizedPCA(n_components=2, random_state=self.params.get("rand", random.randint(1, 100))).fit_transform(X)
        return X_pca, 0

class SKisoProj(SKrandProj):
    #----------------------------------------------------------------------
    # Isomap projection

    PID =  "SKiso"
    title_str = "Isomap projection"

    def getX(self, X):
        X_iso = manifold.Isomap(n_neighbors=self.params.get("#k",4), n_components=2).fit_transform(X)
        return X_iso, 0

class SKlleProj(SKrandProj):
    #----------------------------------------------------------------------
    # Locally linear embedding

    PID =  "SKlle"
    title_str = "LLE projection"

    def getTitle(self):
        return "%s %s" % (self.params.get("method", 'standard'), self.title_str)

    def getX(self, X):
        ### methods: standard, modified, hessian, ltsa
        clf = manifold.LocallyLinearEmbedding(n_components=2, n_neighbors=self.params.get("#k",4),
                                              method=self.params.get("method", 'standard'), random_state=self.params.get("rand", random.randint(1, 100)))
        X_lle = clf.fit_transform(X)
        return X_lle, clf.reconstruction_error_

class SKmdsProj(SKrandProj):
    #----------------------------------------------------------------------
    # MDS  embedding

    PID =  "SKmds"
    title_str = "MDS embedding"

    def getX(self, X):
        clf = manifold.MDS(n_components=2, n_init=self.params.get("#R",1), max_iter=self.params.get("#I",100))
        X_mds = clf.fit_transform(X)
        return X_mds, clf.stress_

class SKtreeProj(SKrandProj):
    #----------------------------------------------------------------------
    # Random Trees embedding

    PID =  "SKtree"
    title_str = "Totally Random Trees embedding"

    def getX(self, X):
        hasher = ensemble.RandomTreesEmbedding(n_estimators=self.params.get("#E",200),
                                               random_state=self.params.get("rand", random.randint(1, 100)),
                                               max_depth=self.params.get("dep",5))
        X_transformed = hasher.fit_transform(X)
        pca = decomposition.RandomizedPCA(n_components=2)
        X_reduced = pca.fit_transform(X_transformed)
        return X_reduced, 0

class SKspecProj(SKrandProj):
    #----------------------------------------------------------------------
    # Spectral embedding

    PID =  "SKspec"
    title_str = "Spectral embedding"

    def getX(self, X):
        ### eigen solvers: arpack, lobpcg
        embedder = manifold.SpectralEmbedding(n_components=2, random_state=self.params.get("rand", random.randint(1, 100)))
        X_se = embedder.fit_transform(X)
        return X_se, 0

class SKtsneProj(SKrandProj):
    #----------------------------------------------------------------------
    # Stochastic Neighbors embedding

    PID =  "-SKtsne"
    title_str = "t-SNE embedding"

    def getX(self, X):
        X_sne, c = tsne.tsne(X, no_dims=2, initial_dims=self.params.get("dim",50), perplexity=self.params.get("perp",20.0))
        return X_sne, c
