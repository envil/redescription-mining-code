from classExtension import Extension
import classCharbonTreeCW
from classInitialPairs import *
from classSParts import SParts
from classQuery import  *
from classRedescription import  *
from sklearn import tree
import copy
import pdb
import numpy as np

class Charbon(classCharbonTreeCW.Charbon):

    def getSplit(self, side, in_data, target):
        suppvs = [None, None]
        dtcs = [None, None]
        best = (0, suppvs, dtcs)
        current_side = 1-side
        if sum(target) >= self.constraints.min_node_size() and len(target)-sum(target) >= self.constraints.min_node_size():
            suppvs[side] = target
            rounds = 0
        else:
            rounds = -1

        depth = [2,2]
        while depth[0] <= self.constraints.max_depth() or depth[1] <= self.constraints.max_depth():
        # while rounds < 30 and rounds >= 0:            
            rounds += 1
            dtc, suppv = self.splitting_with_depth(in_data[current_side], suppvs[1-current_side], depth[current_side], self.constraints.min_node_size())
            if dtc is None or (suppvs[current_side] is not None and np.sum((suppvs[current_side] - suppv)**2) == 0):
            ### nothing found or no change
                rounds = -1
                depth[current_side] = self.constraints.max_depth()+1
                depth[1-current_side] = self.constraints.max_depth()+1
            else:
                depth[current_side] += 1
                suppvs[current_side] = suppv
                dtcs[current_side] = dtc
                current_side = 1-current_side
                if suppvs[0] is not None and suppvs[1] is not None:
                    jj = self.getJacc(suppvs)
                    if jj > best[0]:
                        best = (jj, list(suppvs), list(dtcs))
        return best
