import re, random, sys
import numpy
import inspect
from ..clired.classData import Data
import os

try:
    from sklearn import (manifold, decomposition, ensemble, random_projection)
    #sys.platform != 'win32'
    WITHSKLEARN = True
except ModuleNotFoundError as e:
    print(e)
    print("Some projection-based views will not be available!")
    WITHSKLEARN = False

WITH_VARS = True
    
import pdb

# def my_SIGTERM_handler(sign, frame):
#     ### DIRTY BUSINESS TO KILL THE WHOLE FAMILY SPAWNED BY SCIKIT
#     print("KILLED!", sign)
#     kill_children(os.getpid())
#     exit()

# def kill_children(pid):
#     for childp in get_children(pid):
#         kill_children(childp)
#         print("Killing %d..." % childp)
#         try:
#             os.kill(childp, signal.SIGTERM)
#         except OSError as e:
#             pass

def withen(mat):
    tt = numpy.std(mat, 0)
    tt[numpy.where(tt == 0)] = 1
    return (mat - numpy.tile(numpy.mean(mat, 0), (mat.shape[0], 1)))/numpy.tile(tt, (mat.shape[0], 1)), tt

def withenR(mat):
    tt = numpy.std(mat, 1)
    tt[numpy.where(tt == 0)] = 1
    return (mat - numpy.tile(numpy.mean(mat, 1), (mat.shape[1], 1)).T)/numpy.tile(tt, (mat.shape[1], 1)).T

def get_children(pid):
    if sys.platform == 'linux2':
        return map(int, os.popen("ps -o pid --ppid %d --noheaders" % pid).read().strip().split())
    if sys.platform == 'darwin':
        #### FILL IN HERE CORRECT OS X LS TO GET THE LIST OF PIDS FOR A GIVEN PARENT ID
        return [] #map(int, os.popen("ps -o pid --ppid %d --noheaders" % pid).read().strip().split())
    return []

def list_children(pid, l, level=0):
    for childp in get_children(pid):
        l.append((level+1, childp))
        list_children(childp, l, level+1)

def all_subclasses(cls):
    return cls.__subclasses__() + [g for s in cls.__subclasses__() for g in all_subclasses(s)]

def argsF(f):
    if inspect.isclass(f):
        args, varargs, keywords, defaults = inspect.getargspec(f.__init__)
        if len(args) > 0:
            args.pop(0)
        else: return {}
    elif inspect.ismethod(f) or inspect.isfunction(f):
        args, varargs, keywords, defaults = inspect.getargspec(f)
        if len(args) == 0: return {}
    else:
        return {}
    if defaults is None: defaults = []
    defaults = [None for i in range(len(args)-len(defaults))] + list(defaults)
    return dict(zip(args, defaults))

def applyF(f, parameters):
    mtd_def = argsF(f)
    args = dict([(a, parameters.get(a, v)) for a,v in mtd_def.items()])
    return f(**args)

class Proj(object):
    
    WHAT_MAP = {"entities": "", "cluster": "CL"}
    
    xaxis_lbl = "x-axis var (side.id)"
    yaxis_lbl = "y-axis var (side.id)"

    rint_max = 10000
    PID = "---"
    SDESC = "---"
    whats = ["entities", "cluster"]
    title_str = "Projection"
    gen_parameters = {"types": Data.getTidForName(["Numerical"]), "only_able":True}
    fix_parameters = {}
    options_parameters = {"types": Data.getNamesTids()}
    dyn_f = []
    
    def __init__(self, data, params=None, what="entities", transpose=True):
        # signal.signal(signal.SIGTERM, my_SIGTERM_handler)
        self.transpose = transpose
        self.what = what
        self.data = data
        self.coords_proj = None
        self.vars_proj = None
        self.vars_details = None
        self.code = ""
        self.initParameters(params)
        self.pids_ex = set()

    @classmethod
    def getTPIDw(tcl, what="entities"):
        return "%s%s" % (tcl.WHAT_MAP.get(what, "??"), tcl.PID)
        
    def getTPID(self):
        return self.getTPIDw(self.what)
        
    def getPid(self):
        return os.getpid()

    def stop(self):
        self.clearCoords()
        
    def clearCoords(self):
        self.coords_proj = None
        self.vars_proj = None

    def getAxisLabel(self, axis=0):
        return None
    def getTitle(self):
        return self.title_str
        # return "%s %s" % (self.what.title(), self.title_str)
    def readyCoords(self):
       return self.coords_proj is not None
        
    def getCoords(self, axi=None, ids=None):
        if not self.readyCoords():
            return None
        if axi is None:
            return self.coords_proj
        elif ids is None:
            return self.coords_proj[axi]
        return self.coords_proj[axi][ids]
    def getVarsP(self, axi=None, ids=None):
        if not self.readyCoords() or self.vars_proj is None:       
            return None
        if axi is None:
            return self.vars_proj
        elif ids is None:
            return self.vars_proj[axi]
        return self.vars_proj[axi][ids]

    
    def getAxisLims(self):
        if not self.readyCoords():
            return (0,1,0,1)
        hspan = .95
        corners = (min(self.coords_proj[0]), max(self.coords_proj[0]), min(self.coords_proj[1]), max(self.coords_proj[1]))
        xm, ym = (corners[1]+corners[0])/2., (corners[3]+corners[2])/2.
        nc = ((xm-(xm-corners[0])/hspan), (xm+(corners[1]-xm)/hspan), (ym-(ym-corners[2])/hspan), (ym+(corners[3]-ym)/hspan))
        return nc

    def do(self):
        self.pids_ex = set(get_children(os.getpid()))
        self.comp()
        
    def getCode(self):
        tt = "%s:" % self.getTPID()
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
        if "A" in params:
            params["types"] = None
        if "a" in params:
            params["only_able"] = False
        return params

    # def makeBoxes(self, frame):
    #     boxes = []
    #     for kp in self.getTunableParamsK():
    #         label = wx.StaticText(frame, wx.ID_ANY, kp.replace("_", " ").capitalize()+":")
    #         ctrls = []
    #         value = self.getParameter(kp)
    #         if type(value) in [int, float]:
    #             type_ctrl = "text"
    #             ctrls.append(wx.TextCtrl(frame, wx.NewId(), str(value)))
    #         elif type(value) is bool:
    #             type_ctrl = "checkbox" 
    #             ctrls.append(wx.CheckBox(frame, wx.NewId(), "", style=wx.ALIGN_RIGHT))
    #             ctrls[-1].SetValue(value)
    #         elif type(value) is list and kp in self.options_parameters:
    #             type_ctrl = "checkbox"
    #             for k,v in self.options_parameters[kp]:
    #                 ctrls.append(wx.CheckBox(frame, wx.NewId(), k, style=wx.ALIGN_RIGHT))
    #                 ctrls[-1].SetValue(v in value)
    #         elif kp in self.options_parameters:
    #             type_ctrl = "choice"
    #             strs = [k for k,v in self.options_parameters[kp]]
    #             ctrls.append(wx.Choice(frame, wx.NewId(), choices=strs))
    #             try:
    #                 ind = strs.index(value)
    #                 ctrls[-1].SetSelection(ind)
    #             except ValueError:
    #                 pass
    #         boxes.append({"key": kp, "label": label, "type_ctrl": type_ctrl, "ctrls":ctrls, "value":value})
    #     return boxes

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

    def addParamsRandrep(self, more={}):
        pass
        
    def getParameters(self, params={}):
        loc_params = {}
        loc_params.update(self.params)
        loc_params.update(params)
        if self.params.get(Proj.yaxis_lbl, "-1.0") == "-1.0" or self.params.get(Proj.xaxis_lbl, "-1.0") == "-1.0" and not "random_state" in self.params:
            self.params["random_state"] = random.randint(0, self.rint_max)
        return loc_params

    def getParamsHash(self):
        prms = self.getParameters()
        # if prms.get(self.xaxis_lbl) == "-1.0" or prms.get(self.yaxis_lbl) == "-1.0":            
        #     return "RND"
        return ";".join(["%s=%s" % (k, prms[k]) for k in sorted(prms.keys())])


    def getTunableParamsK(self):
        return list(self.gen_parameters.keys())

    def getParameter(self, param):
        return self.params.get(param)

    def setParameter(self, param, v):
        self.params[param] = v

    def applyF(self, f, parameters={}):
        return applyF(f, self.getParameters(parameters))

class AxesProj(Proj):

    PID = "AXE"
    SDESC = "Scatter"
    whats = ["entities", "cluster"]
    title_str = "Scatter Plot"
    gen_parameters = {Proj.xaxis_lbl: "-1.0", Proj.yaxis_lbl: "-1.0"}
    fix_parameters = {"types": Data.real_types_name_to_id.values(), "only_able":False}
    dyn_f = []

    def __init__(self, data, params=None, what="entities", transpose=True):
        self.ax_vars = None
        Proj.__init__(self, data, params, what, transpose)
    
    def addParamsRandrep(self, more={}):
        self.params.update(more)

    def comp(self):
        mat, details, mcols = self.data.getMatrix(side_cols=[(0, None),(1, None)], types=self.getParameter("types"), only_able=self.getParameter("only_able"))
        mm = [m for m in mcols.keys() if len(m)==2]
        if len(mm) == 0:
            return
        scs = random.sample(mm, 2)
        if "vids" in self.params:
            if len(self.params["vids"]) == 1:
                scs[1] = self.params["vids"][0]
                # #### DEBUG
                # map_vars = {(0, 12): (1, 0), (0, 13): (1, 4), (0, 14): (1, 11), (0, 15): (1, 20)}
                # if scs[1] in map_vars:
                #     scs[0] = map_vars[scs[1]]
                #     print("VARS", scs)
                # scs[0] = (1, 32) ## debug

            elif len(self.params["vids"]) > 1:
                scs = random.sample(self.params["vids"], 2)
                nn = [m for m in mm if m in self.params["vids"]]
         
        side_lstr = {0:"LHS", 1:"RHS"}
        self.labels = ["", ""]
        for ai, axis in enumerate([Proj.xaxis_lbl, Proj.yaxis_lbl]):
            tmp = self.getParameter(axis)
            try:
                sc = tuple(map(int, str(tmp).split(".")[:2]))
                if sc[0] > -1 and sc in mm:
                    scs[ai] = sc
            except ValueError:
                pass
            
            self.setParameter(axis, float("%d.%d" % scs[ai]))
            self.labels[ai] = "%s %s" % (side_lstr[scs[ai][0]], details[mcols[scs[ai]]]["name"])
        self.coords_proj = [mat[mcols[scs[0]]], mat[mcols[scs[1]]]]
        for side in [0,1]:
            self.coords_proj[side][numpy.where(~numpy.isfinite(self.coords_proj[side]))] = numpy.nanmin(self.coords_proj[side]) -1
        for side in [0,1]:
            if not Data.isTypeId(details[mcols[scs[side]]]["type"], "Numerical"):
                self.coords_proj[side] = 1.*self.coords_proj[side] + 0.33*numpy.random.rand(len(self.coords_proj[side]))
        self.ax_vars = scs
    def getAxisLabel(self, axi):
        return "%s" % self.labels[axi]
    def getAxVars(self):
        return self.ax_vars

class ProjFactory(object):
    defaultView = AxesProj
    
    @classmethod
    def getViewsDetails(tcl, bc, what="entities"):
        preff_title = "%s " % what.title()
        details = {}
        for cls in all_subclasses(Proj):
            PIDw = cls.getTPIDw(what)
            if (re.match("^(?P<alg>[A-Za-z*.]*)$", PIDw) is not None) and (what in cls.whats):
                short_title = re.sub("Multidimensional", "Mul.Dim.", re.sub("Projection", "Proj.", re.sub("Embedding", "Embd.", cls.title_str)))
                details[PIDw]= {"title": preff_title + cls.title_str, "class": bc, "more": PIDw, "ord": bc.ordN}
                # details[cls.PID]= {"title": preff_title + cls.title_str, "short_title": short_title, "class": bc, "more": cls.PID, "ord": bc.ordN}
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

#### COMMENT OUT FROM  HERE TO GET RID OF SKLEARN
if WITHSKLEARN:

    ### The various projections with sklearn
    #----------------------------------------------------------------------
    class DynProj(Proj):

        PID =  "---"
        SDESC = "---"
        title_str = "Projection"
        gen_parameters = dict(Proj.gen_parameters)
        gen_parameters.update({"with_vars":False})
        
        def getData(self):
            details, mcols = (None, None)
            if type(self.data) is numpy.array or type(self.data) is numpy.ndarray:
                if self.transpose:
                    mat = self.data.T
                else:
                    mat = self.data
                idsNAN = numpy.where(~numpy.isfinite(mat))
                mat[idsNAN] = numpy.nanmin(mat) -1
                matn, tt = withen(mat)
            else:
                if self.transpose:
                    mat, details, mcols = self.data.getMatrix(types=self.getParameter("types"), only_able=self.getParameter("only_able"))
                    if len(mcols) == 0:
                        return None, None, None
                    idsNAN = numpy.where(~numpy.isfinite(mat))
                    mat[idsNAN] = numpy.nanmin(mat) -1
                    matn,tt = withen(mat.T)
                else:
                    mat, details, mcols = self.data.getMatrix(types=self.getParameter("types"), only_able=False)
                    if len(mcols) == 0:
                        return None, None, None

                    idsNAN = numpy.where(~numpy.isfinite(mat))
                    mat[idsNAN] = numpy.nanmin(mat) -1

                    if self.getParameter("only_able") and len(self.data.selectedRows()) > 0:
                        selected = numpy.array(list(self.data.nonselectedRows()))
                        matn,tt = withen(mat[:,selected])
                    else:
                        matn, tt = withen(mat)
            return matn, tt, details, mcols

        def comp(self):
            matn, tt, data_details, mcols = self.getData()
            org_matn = None
            # pdb.set_trace()
            if matn is not None:

                if self.getParameter("with_vars"):
                    if len(data_details) == len(tt): # matn.shape[1]:
                        # unit_vecs = numpy.eye(matn.shape[1])
                        unit_vecs = numpy.diag(tt)
                        org_matn = matn
                        matn = numpy.vstack([matn, unit_vecs])
                
                X_pro, err = self.getX(matn)
                if org_matn is None:
                    self.coords_proj = (X_pro[:,0], X_pro[:,1])
                    self.vars_proj = None
                else:
                    self.coords_proj = (X_pro[:org_matn.shape[0],0], X_pro[:org_matn.shape[0],1])
                    self.vars_proj = (X_pro[org_matn.shape[0]:,0], X_pro[org_matn.shape[0]:,1], [ddt["name"] for ddt in data_details])

        def getX(self, X):
            pass


    class KillerProj(DynProj):
        ## ----------------------------------------------------------------------
        # For projections with subprocesses


        PID =  "---"
        SDESC = "---"
        title_str = "Projection"

        def updatePL(self):
            l = []
            list_children(os.getpid(), l)
            self.pids_ex.update(l) 

        def stop(self):
            l = []
            list_children(os.getpid(), l)
            l.sort()
            l = [childp for (lev, childp) in l if childp not in self.pids_ex] # and lev > 1]
            while len(l) > 0:
                childp =  l.pop()
                try:
                    os.kill(childp, signal.SIGTERM)
                except OSError:
                    pass
            self.clearCoords()

    class SVDProj(DynProj):

        PID = "-SVD"
        SDESC = "SVD"
        title_str = "SVD Projection"
        fix_parameters = dict(DynProj.fix_parameters)
        fix_parameters.update({"compute_uv": True, "full_matrices":False })
        dyn_f = [numpy.linalg.svd]
        #### http://docs.scipy.org/doc/numpy/reference/generated/numpy.linalg.svd.html

        def comp(self):
            matn, tt, data_details, mcols = self.getData()
            U, s, V = self.applyF(numpy.linalg.svd, {"a": matn.T})
            tmp = numpy.dot(U[:2], matn.T)
            self.coords_proj = (tmp[0], tmp[1])

        def getAxisLabel(self, axi):
            return "dimension %d" % (axi+1)

    class SKrandProj(DynProj):

        PID =  "SKrand"
        SDESC = "Random"
        title_str = "Sparse Random Projection"
        fix_parameters = dict(DynProj.fix_parameters)
        fix_parameters.update({"n_components": 2 })
        dyn_f = [random_projection.SparseRandomProjection]
        #### http://scikit-learn.org/stable/modules/random_projection.html

        def addParamsRandrep(self, more={}):
            self.params["random_state"] = random.randint(0, self.rint_max)
            self.params.update(more)

        # Random 2D projection using a random unitary matrix
        def getX(self, X):
            rp = self.applyF(random_projection.SparseRandomProjection)
            X_projected = rp.fit_transform(X)
            return X_projected, 0

    class SKpcaProj(DynProj):
       #----------------------------------------------------------------------
       # Projection on to the first 2 principal components

       PID =  "SKpca"
       if sys.platform == 'darwin': PID =  "-"+ PID
       SDESC = "PCA"
       title_str = "PCA Projection"
       gen_parameters = dict(DynProj.gen_parameters)
       gen_parameters.update({"iterated_power": 3, "svd_solver": "randomized"})
       dyn_f = [decomposition.PCA]
       #### http://scikit-learn.org/stable/modules/generated/sklearn.decomposition.PCA.html

       def addParamsRandrep(self, more={}):
           self.params["random_state"] = random.randint(0, self.rint_max)
           self.params.update(more)
           
       def getX(self, X):
           X_pca = self.applyF(decomposition.PCA).fit_transform(X)
           return X_pca, 0

    class SKisoProj(DynProj):
        #----------------------------------------------------------------------
        # Isomap projection

        PID =  "SKiso"
        if sys.platform == 'darwin': PID =  "-"+ PID
        SDESC = "Isomap"
        title_str = "Isomap Embedding"
        gen_parameters = dict(DynProj.gen_parameters)
        gen_parameters.update({"n_neighbors": 5, "max_iter":100})
        dyn_f = [manifold.Isomap]
        ### http://scikit-learn.org/stable/modules/generated/sklearn.manifold.Isomap.html

        # def addParamsRandrep(self):
        #     self.params["random_state"] = random.randint(0, self.rint_max)

        def getX(self, X):
            X_iso = self.applyF(manifold.Isomap).fit_transform(X)
            return X_iso, 0

    class SKlleProj(DynProj):
        #----------------------------------------------------------------------
        # Locally linear embedding

        PID =  "SKlle"
        SDESC = "LLE"
        title_str = "Locally Linear Embedding"
        gen_parameters = dict(DynProj.gen_parameters)
        gen_parameters.update({"n_neighbors": 5, "max_iter":100, "method": "standard"})
        options_parameters = dict(DynProj.options_parameters)
        options_parameters["method"] = [("standard", "standard"), ("hessian", "hessian"), ("modified", "modified"), ("ltsa", "ltsa")]
        dyn_f = [manifold.LocallyLinearEmbedding]
        ### http://scikit-learn.org/stable/modules/generated/sklearn.manifold.LocallyLinearEmbedding.html

        def getX(self, X):
            ### methods: standard, modified, hessian, ltsa
            clf = self.applyF(manifold.LocallyLinearEmbedding)
            X_lle = clf.fit_transform(X)
            return X_lle, clf.reconstruction_error_

    class SKmdsProj(KillerProj):
        #----------------------------------------------------------------------
        # MDS  embedding

        PID =  "SKmds"
        if sys.platform == 'darwin': PID =  "-SKpca"
        SDESC = "MDS"
        title_str = "Multidimensional Scaling"
        gen_parameters = dict(DynProj.gen_parameters)
        gen_parameters.update({"n_init": 4, "max_iter":100})
        fix_parameters = dict(DynProj.fix_parameters)
        fix_parameters.update({"n_jobs": -2})
        dyn_f = [manifold.MDS]
        ### http://scikit-learn.org/stable/modules/generated/sklearn.manifold.MDS.html

        def getX(self, X):
            self.updatePL() 
            clf = self.applyF(manifold.MDS)
            X_mds = clf.fit_transform(X)
            return X_mds, clf.stress_

    class SKtreeProj(DynProj):
        #----------------------------------------------------------------------
        # Random Trees embedding

        PID =  "SKtree"
        if sys.platform == 'darwin': PID =  "-SKpca"
        SDESC = "Rand.Trees"
        title_str = "Totally Random Trees Rep."
        gen_parameters = dict(DynProj.gen_parameters)
        gen_parameters.update({"max_depth":5, "n_estimators":10})
        fix_parameters = dict(DynProj.fix_parameters)
        dyn_f = [ensemble.RandomTreesEmbedding, decomposition.PCA]
        ### http://scikit-learn.org/stable/modules/generated/sklearn.ensemble.RandomTreesEmbedding.html
        ### http://scikit-learn.org/stable/modules/generated/sklearn.decomposition.PCA.html

        def addParamsRandrep(self, more={}):
            self.params["random_state"] = random.randint(0, self.rint_max)
            self.params.update(more)

        def getX(self, X):
            X_transformed = self.applyF(ensemble.RandomTreesEmbedding).fit_transform(X)
            X_reduced = self.applyF(decomposition.PCA).fit_transform(X_transformed.toarray())
            return X_reduced, 0

    class SKspecProj(DynProj):
        #----------------------------------------------------------------------
        # Spectral embedding

        PID =  "SKspec"
        SDESC = "Spectral"
        title_str = "Spectral Embedding"
        dyn_f = [manifold.SpectralEmbedding]
        ### http://scikit-learn.org/stable/modules/generated/sklearn.manifold.SpectralEmbedding.html
        
        def getX(self, X):
            ### eigen solvers: arpack, lobpcg
            X_se = self.applyF(manifold.SpectralEmbedding).fit_transform(X)
            return X_se, 0

    class SKtsneProj(DynProj):
        #----------------------------------------------------------------------
        # Stochastic Neighbors embedding

        # ### THIS IS DISABLED "starting with minus"
        # PID =  "-SKtsne"
        PID =  "SKtsne"
        SDESC = "t-SNE"
        title_str = "t-SNE Embedding"
        gen_parameters = dict(DynProj.gen_parameters)
        gen_parameters.update({"perplexity":20.0})
        # fix_parameters = dict(DynProj.fix_parameters)
        # fix_parameters.update({"no_dims":2})
        dyn_f = [manifold.TSNE]
        ## https://scikit-learn.org/stable/modules/generated/sklearn.manifold.TSNE.html

        def getX(self, X):
            X_sne = self.applyF(manifold.TSNE).fit_transform(X)
            return X_sne, 0
            # X_sne, c = self.applyF(tsne.tsne, {"X":X})
            # return X_sne, c

