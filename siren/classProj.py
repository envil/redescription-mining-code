### TODO check which imports are needed 
import re, random
import numpy as np
from reremi.classQuery import Query
from reremi.classRedescription import Redescription

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

        m = random.choice(Proj.__subclasses__())
        return m(data)

class Proj(object):

    def __init__(self, data, code = None):
        self.data = data

class AxesProj(Proj):

    PID = "A"

    def __init__(self, data, code=None):
        totcols = data.nbCols(0)+data.nbCols(1)
        self.axis_ids = [[],[]]
        for axi in [0,1]:
            self.axis_ids[axi] = np.random.randint(data.nbCols(0)+1, totcols)

        if code is not None:
            tmpr = re.match("^(?P<axis0>[0-9]*)-(?P<axis1>[0-9]*)$", code)
            if tmpr is not None:
                axis0 = int(tmpr.group("axis0"))
                axis1 = int(tmpr.group("axis1"))
                if axis0 < totcols:
                    self.axis_ids[0] = axis0
                if axis1 < totcols:
                    self.axis_ids[1] = axis1

        mat, details = data.getMatrix()
        self.coords_proj = (mat[self.axis_ids[0]], mat[self.axis_ids[1]])

    def getAxisLabel(self, axi):
        return "axis %d" % self.axis_ids[axi]
    
    def getCode(self):
        return "%s:%d-%d" % (self.PID, self.axis_ids[0], self.axis_ids[1])

    def getAxisLims(self):
        return (min(self.coords_proj[0]), max(self.coords_proj[0]), min(self.coords_proj[1]), max(self.coords_proj[1]))

    def getCoords(self, axi=None, ids=None):
        if axi is None:
            return self.coords_proj
        elif ids is None:
            return self.coords_proj[axi]
        return self.coords_proj[axi][ids]
