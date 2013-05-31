### TODO check which imports are needed 
import re, random
import numpy as np
from reremi.classQuery import Query
from reremi.classRedescription import Redescription
from reremi.classData import BoolColM, CatColM, NumColM

import pdb

class ProjFactory:

    @classmethod
    def getProj(self, data, code = None):

        if code is not None:
            tmp = re.match("^(?P<alg>[A-Z]*):(?P<par>.*)$", code)
            if tmp is not None:
                k = tmp.group("alg")
                subcode = tmp.group("par")
                
                for cls in Proj.__subclasses__():
                    if cls.PID == k:
                        return cls(data, subcode)

        #m = SVDProj
        m = random.choice(Proj.__subclasses__())
        return m(data)

class Proj(object):

    def __init__(self, data, code = None):
        self.data = data

class AxesProj(Proj):

    PID = "A"

    def __init__(self, data, code=None):
        mat, details, mcols = data.getMatrix()
        self.axis_ids = random.sample(range(len(mat)), 2)

        if code is not None:
            sidestr = {"0":0, "1":1, "L":0, "R":1, "l":0, "r":1}
            tmpr = re.match("^(?P<side0>[01LRlr])(?P<axis0>[0-9]*)-(?P<side1>[01LRlr])(?P<axis1>[0-9]*)$", code)
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

    PID = "S"

    def __init__(self, data, code=None):
        self.stypes=[NumColM.type_id]
        if code is not None and "a" in code:
            self.stypes = None

        mat, details, mcol = data.getMatrix(types=self.stypes)
        tt = np.std(mat, 1)
        tt[np.where(tt == 0)] = 1
        matn = (mat - np.tile(np.mean(mat, 1), (mat.shape[1], 1)).T)/np.tile(tt, (mat.shape[1], 1)).T
        U, s, V = np.linalg.svd(matn, full_matrices=False)
        tmp = np.dot(U[:2],matn)
        self.coords_proj = (tmp[0], tmp[1])

    def getAxisLabel(self, axi):
        return "dimension %d" % (axi+1)
    
    def getCode(self):
        l = {True: "a", False: "n"}
        return "%s:%s" % (self.PID, l[self.stypes is None])

    def getAxisLims(self):
        return (min(self.coords_proj[0]), max(self.coords_proj[0]), min(self.coords_proj[1]), max(self.coords_proj[1]))

    def getCoords(self, axi=None, ids=None):
        if axi is None:
            return self.coords_proj
        elif ids is None:
            return self.coords_proj[axi]
        return self.coords_proj[axi][ids]
