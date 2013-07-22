### TODO check which imports are needed 
import re, random
import wx
import numpy as np
from sklearn import (manifold, datasets, decomposition, ensemble, random_projection)
import inspect
import tsne
from reremi.classQuery import Query
from reremi.classRedescription import Redescription
from reremi.classData import BoolColM, CatColM, NumColM
import toolMath

import pdb

def all_subclasses(cls):
    return cls.__subclasses__() + [g for s in cls.__subclasses__()
                                   for g in all_subclasses(s)]
def argsF(f):
    if inspect.isclass(f):
        args, varargs, keywords, defaults = inspect.getargspec(f.__init__)
        args.pop(0)
    elif inspect.ismethod(f) or inspect.isfunction(f):
        args, varargs, keywords, defaults = inspect.getargspec(f)
    else:
        return
    defaults = [None for i in range(len(args)-len(defaults))] + list(defaults)
    return dict(zip(args, defaults))

def applyF(f, parameters):
    mtd_def = argsF(f)
    args = dict([(a, parameters.get(a, v)) for a,v in mtd_def.items()])
    return f(**args)


class Proj(object):

    PID = "---"
    whats = ["variables", "entities"]
    title_str = "Projection"
    gen_parameters = {"types":[NumColM.type_id], "only_able":True}
    fix_parameters = {}
    options_parameters = {"types": [("Boolean", BoolColM.type_id), ("Categorical", CatColM.type_id), ("Numerical", NumColM.type_id)]}
    dyn_f = []
    
    def __init__(self, data, params=None, what="entities", transpose=True):
        self.transpose = transpose
        self.what = what
        self.data = data
        self.coords_proj = None
        self.code = ""
        self.mcols = None
        self.initParameters(params)

    def getAxisLabel(self, axis=0):
        return None
    def getTitle(self):
        return "%s %s" % (self.what.title(), self.title_str)

    def getMCols(self):
        return self.mcols

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
        self.comp()


    def getCode(self):
        tt = "%s:" % self.PID
        if self.getParameter("types") is None:
            tt += "A,"
        if not self.getParameter("only_able"):
            tt += "a,"
        for k in self.getTunableParamsK():
            if k not in ["only_able", "types", "code"]:
                v = self.getParameter(k)
                if type(v) != bool:
                    tt += "%s=%s," % (k,v)
                else:
                    tt += "%s," % k
        return tt.strip(":, ")

    def parseCode(self, code):
        params = {}
        tmp = re.match("^(?P<alg>[A-Za-z]*)(?P<par>:.*)?$", code)
        if tmp is not None and tmp.group("par") is not None:
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
        if params.has_key("A"):
            params["types"] = None
        if params.has_key("a"):
            params["only_able"] = False
        return params

    def makeBoxes(self, frame):
        boxes = []
        for kp in self.getTunableParamsK():
            label = wx.StaticText(frame, wx.ID_ANY, kp+":")
            ctrls = []
            value = self.getParameter(kp)
            if type(value) in [int, float]:
                type_ctrl = "text"
                ctrls.append(wx.TextCtrl(frame, wx.NewId(), str(value)))
            elif type(value) is bool:
                type_ctrl = "checkbox" 
                ctrls.append(wx.CheckBox(frame, wx.NewId(), "", style=wx.ALIGN_RIGHT))
                ctrls[-1].SetValue(value)
            elif type(value) is list and self.options_parameters.has_key(kp):
                type_ctrl = "checkbox"
                for k,v in self.options_parameters[kp]:
                    ctrls.append(wx.CheckBox(frame, wx.NewId(), k, style=wx.ALIGN_RIGHT))
                    ctrls[-1].SetValue(v in value)
            elif self.options_parameters.has_key(kp):
                type_ctrl = "choice" 
                ctrls.append(wx.Choice(frame, wx.NewId()))
                strs = [k for k,v in self.options_parameters[kp]]
                ctrls[-1].AppendItems(strings=strs)
                try:
                    ind = strs.index(value)
                    ctrls[-1].SetSelection(ind)
                except ValueError:
                    pass
            boxes.append({"key": kp, "label": label, "type_ctrl": type_ctrl, "ctrls":ctrls, "value":value})
        return boxes

    def readBoxes(self, boxes):
        params = {}
        for box in boxes:
            if box["type_ctrl"] == "text":
                try:
                    params[box["key"]] = type(box["value"])(box["ctrls"][0].GetValue())
                except ValueError:
                    params[box["key"]] = box["value"]
            elif box["type_ctrl"] == "checkbox":
                if type(box["value"]) is bool:
                    params[box["key"]] = box["ctrls"][0].GetValue()
                else:
                    dd = dict(self.options_parameters[box["key"]])
                    params[box["key"]] = [dd[t.GetLabelText()] for t in box["ctrls"] if t.GetValue()]
            elif box["type_ctrl"] == "choice":
                params[box["key"]] = self.options_parameters[box["key"]][box["ctrls"][0].GetSelection()][1]
        return params

    def initParameters(self, params={}):
        if not type(params) is dict:
            if type(params) is list:
                params = self.readBoxes(params)
            else:
                self.code = params
                params = self.parseCode(params)
        self.params = {}
        self.params.update(self.gen_parameters)
        self.params.update(self.fix_parameters)
        self.params.update(params)

    def getParameters(self, params={}):
        loc_params = {}
        loc_params.update(self.params)
        loc_params.update(params)
        return loc_params

    def getTunableParamsK(self):
        return self.gen_parameters.keys()

    def getParameter(self, param):
        return self.params.get(param, None)

    def setParameter(self, param, v):
        self.params[param] = v

    def applyF(self, f, parameters={}):
        return applyF(f, self.getParameters(parameters))

class AxesProj(Proj):

    PID = "AXE"
    whats = ["entities"]
    title_str = "Axis Projection"
    gen_parameters = {"Xaxis": -1.0, "Yaxis": -1.0}
    fix_parameters = {"types":[BoolColM.type_id, CatColM.type_id, NumColM.type_id], "only_able":False}
    dyn_f = []

    def comp(self):
        mat, details, mcols = self.data.getMatrix(types=self.getParameter("types"), only_able=self.getParameter("only_able"))
        if len(mcols) == 0:
            return
        scs = random.sample(mcols.keys(), 2)
        side_lstr = {0:"LHS", 1:"RHS"}
        self.labels = ["", ""]
        for ai, axis in enumerate(["Xaxis", "Yaxis"]):
            tmp = self.getParameter(axis)
            if tmp > 0:
                sc = tuple(map(int, str(tmp).split(".")[:2]))
                if mcols.has_key(sc):
                    scs[ai] = sc
            self.setParameter(axis, float("%d.%d" % scs[ai]))
            self.labels[ai] = "%s %s" % (side_lstr[scs[ai][0]], details[mcols[scs[ai]]]["name"])
        self.coords_proj = [mat[mcols[scs[0]]], mat[mcols[scs[1]]]]
        self.mcols = mcols
        for side in [0,1]:
            if details[mcols[scs[side]]]["type"] != NumColM.type_id:
                self.coords_proj[side] += 0.33*np.random.rand(len(self.coords_proj[side])) 

    def getAxisLabel(self, axi):
        return "%s" % self.labels[axi]

class VrsProj(Proj):

    PID = "VRS"
    whats = ["variables"]
    title_str = "Axis Projection"
    gen_parameters = dict(Proj.gen_parameters)
    gen_parameters.update({"Xaxis": -1, "Yaxis": -1})
    dyn_f = []

    def comp(self):
        mat, details, mcols = self.data.getMatrix(types=self.getParameter("types"), only_able=False)
        if len(mcols) == 0:
            return

        rids = range(self.data.nbRows())
        if self.getParameter("only_able") and len(self.data.selectedRows()) > 0:
            rids = list(self.data.nonselectedRows())
            selected = np.array(rids)
            mat = mat[:,selected]
            
        scs = random.sample(rids, 2)
        self.labels = ["", ""]
        for ai, axis in enumerate(["Xaxis", "Yaxis"]):
            tmp = self.getParameter(axis)
            if tmp > 0 and tmp in rids:
                scs[ai] = tmp
            self.setParameter(axis, scs[ai])
            self.labels[ai] = "%s" % scs[ai]
        self.coords_proj = [mat[:,rids.index(scs[0])], mat[:,rids.index(scs[1])]]
        self.mcols = mcols

    def getAxisLabel(self, axi):
        return "%s" % self.labels[axi]

    
### The various projections with sklearn
#----------------------------------------------------------------------
class DynProj(Proj):

    PID =  "---"
    title_str = "Projection"

    def getData(self):
        if self.data is np.array:
            if self.transpose:
                mat = self.data.T
            else:
                mat = self.data
        else:
            if self.transpose:
                mat, details, self.mcols = self.data.getMatrix(types=self.getParameter("types"), only_able=self.getParameter("only_able"))
                if len(mcols) == 0:
                    return

                matn = toolMath.withen(mat.T)
            else:
                mat, details, self.mcols = self.data.getMatrix(types=self.getParameter("types"), only_able=False)
                if len(mcols) == 0:
                    return

                if self.getParameter("only_able") and len(self.data.selectedRows()) > 0:
                    selected = np.array(list(self.data.nonselectedRows()))
                    matn = toolMath.withen(mat[:,selected])
                else:
                    matn = toolMath.withen(mat)
        return matn

    def comp(self):
        matn = self.getData()
        if matn is not None:
            X_pro, err = self.getX(matn)
            self.coords_proj = (X_pro[:,0], X_pro[:,1])

    def getX(self, X):
        pass

class SVDProj(DynProj):

    PID = "-SVD"
    title_str = "SVD Projection"
    fix_parameters = dict(DynProj.fix_parameters)
    fix_parameters.update({"compute_uv": True, "full_matrices":False })
    dyn_f = [np.linalg.svd]
    
    def comp(self):
        matn = self.getData()
        U, s, V = self.applyF(np.linalg.svd, {"a": matn.T})
        tmp = np.dot(U[:2], matn.T)
        self.coords_proj = (tmp[0], tmp[1])

    def getAxisLabel(self, axi):
        return "dimension %d" % (axi+1)

class SKrandProj(DynProj):

    PID =  "SKrand"
    title_str = "Random projection"
    fix_parameters = dict(DynProj.fix_parameters)
    fix_parameters.update({"n_components": 2 })
    dyn_f = [random_projection.SparseRandomProjection]
    
    # Random 2D projection using a random unitary matrix
    def getX(self, X):
        rp = self.applyF(random_projection.SparseRandomProjection)
        X_projected = rp.fit_transform(X)
        return X_projected, 0

class SKpcaProj(DynProj):
    #----------------------------------------------------------------------
    # Projection on to the first 2 principal components

    PID =  "SKpca"
    title_str = "PCA projection"
    gen_parameters = dict(Proj.gen_parameters)
    gen_parameters.update({"iterated_power": 3 })
    dyn_f = [decomposition.RandomizedPCA]

    def getX(self, X):
        self.title_str = "PCA projection"
        X_pca = self.applyF(decomposition.RandomizedPCA).fit_transform(X)
        return X_pca, 0

class SKisoProj(DynProj):
    #----------------------------------------------------------------------
    # Isomap projection

    PID =  "SKiso"
    title_str = "Isomap projection"
    gen_parameters = dict(DynProj.gen_parameters)
    gen_parameters.update({"n_neighbors": 5, "max_iter":100})
    dyn_f = [manifold.Isomap]

    def getX(self, X):
        X_iso = self.applyF(manifold.Isomap).fit_transform(X)
        return X_iso, 0

class SKlleProj(DynProj):
    #----------------------------------------------------------------------
    # Locally linear embedding

    PID =  "SKlle"
    title_str = "LLE projection"
    gen_parameters = dict(DynProj.gen_parameters)
    gen_parameters.update({"n_neighbors": 5, "max_iter":100, "method": "standard"})
    options_parameters = dict(DynProj.options_parameters)
    options_parameters["method"] = [("standard", "standard"), ("hessian", "hessian"), ("modified", "modified"), ("ltsa", "ltsa")]
    dyn_f = [manifold.LocallyLinearEmbedding]

    def getX(self, X):
        ### methods: standard, modified, hessian, ltsa
        clf = self.applyF(manifold.LocallyLinearEmbedding)
        X_lle = clf.fit_transform(X)
        return X_lle, clf.reconstruction_error_

class SKmdsProj(DynProj):
    #----------------------------------------------------------------------
    # MDS  embedding

    PID =  "SKmds"
    title_str = "MDS embedding"
    gen_parameters = dict(DynProj.gen_parameters)
    gen_parameters.update({"n_init": 4, "max_iter":100})
    fix_parameters = dict(DynProj.fix_parameters)
    fix_parameters.update({"n_jobs": 4})
    dyn_f = [manifold.MDS]

    def getX(self, X):
        clf = self.applyF(manifold.MDS)
        X_mds = clf.fit_transform(X)
        return X_mds, clf.stress_

class SKtreeProj(DynProj):
    #----------------------------------------------------------------------
    # Random Trees embedding

    PID =  "SKtree"
    title_str = "Totally Random Trees embedding"
    gen_parameters = dict(DynProj.gen_parameters)
    gen_parameters.update({"max_depth":5, "n_estimators":10})
    fix_parameters = dict(DynProj.fix_parameters)
    fix_parameters.update({"n_jobs": 4})
    dyn_f = [ensemble.RandomTreesEmbedding, decomposition.RandomizedPCA]

    def getX(self, X):
        X_transformed = self.applyF(ensemble.RandomTreesEmbedding).fit_transform(X) 
        X_reduced = self.applyF(decomposition.RandomizedPCA).fit_transform(X_transformed)
        return X_reduced, 0

class SKspecProj(DynProj):
    #----------------------------------------------------------------------
    # Spectral embedding

    PID =  "SKspec"
    title_str = "Spectral embedding"
    dyn_f = [manifold.SpectralEmbedding]

    def getX(self, X):
        ### eigen solvers: arpack, lobpcg
        X_se = self.applyF(manifold.SpectralEmbedding).fit_transform(X)
        return X_se, 0

class SKtsneProj(DynProj):
    #----------------------------------------------------------------------
    # Stochastic Neighbors embedding

    PID =  "-SKtsne"
    title_str = "t-SNE embedding"
    gen_parameters = dict(DynProj.gen_parameters)
    gen_parameters.update({"initial_dims":50, "perplexity":20.0})
    fix_parameters = dict(DynProj.fix_parameters)
    fix_parameters.update({"no_dims":2})
    dyn_f = [tsne.tsne]

    def getX(self, X):
        X_sne, c = self.applyF(tsne.tsne, {"X":X})
        return X_sne, c


class ProjFactory:
    defaultView = AxesProj

    @classmethod
    def getViewsDetails(tcl, bc, what="entities"):
        preff_title = "%s " % what.title()
        details = {}
        for cls in all_subclasses(Proj):
            if (re.match("^(?P<alg>[A-Za-z*.]*)$", cls.PID) is not None) and (what in cls.whats):
                details[cls.PID+"_"+what]= {"title": preff_title + cls.title_str, "class": bc, "more": cls.PID, "ord": bc.ordN}
        return details

    @classmethod
    def getProj(tcl, data, code = None, boxes=[], what="entities", transpose=True):
            
        if code is not None:
            tmp = re.match("^(?P<alg>[A-Za-z]*)(?P<par>:.*)?$", code)
            if tmp is not None:
                for cls in all_subclasses(Proj):
                    if re.match("^"+cls.PID+"(_.*)?$", tmp.group("alg")):
                        return cls(data, code, what, transpose)

        cls = tcl.defaultView
        # cls = random.choice([p for p in all_subclasses(Proj)
        #                      if re.match("^(?P<alg>[^-S][A-Za-z*.]*)$", p.PID) is not None])
        return cls(data, {}, what, transpose)


    @classmethod
    def dispProjsInfo(tcl):

        str_info = ""
        for cls in all_subclasses(Proj):
            str_info += "--- %s [%s] ---" % (cls.title_str, cls.PID)
            str_info += "".join(["\n\t+%s:\t%s" %c for c in cls.gen_parameters.items()])
            # str_info +=  "".join(["\n\t-%s:\t%s" %c for c in cls.fix_parameters.items()])
            str_info +=  "\nCalls:"
            for f in cls.dyn_f:
                 str_info +=  "\n\t*%s" % f
            #     str_info +=  "".join(["\n\t\t-%s:\t%s" %c for c in argsF(f).items()])
            str_info +=  "\n\n"
        return str_info


