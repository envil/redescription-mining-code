from classCol import ColM
from classQuery import Literal
from classRedescription import  Redescription
from classSParts import tool_ratio

import numpy
import pdb

class Charbon(object):
    name = "-"
    def getAlgoName(self):
        return self.name

    def __init__(self, constraints):
        ### For use with no missing values
        self.constraints = constraints



class CharbonGreedy(Charbon):

    name = "G"

    def isTreeBased(self):
        return False
    def handlesMiss(self):
        return False

    def computeExpand(self, side, col, red, colsC=None):
        if isinstance(red, ColM):
            (colL, colR) = (col, red)
            if side == 1:
                (colL, colR) = (col, red)
            return self.computePair(colL, colR, colsC)
        elif isinstance(red, Redescription):
            return self.getCandidates(side, col, red, colsC)
        return []

    def __init__(self, constraints):
        Charbon.__init__(self, constraints)
        self.setOffsets()
    def getOffsets(self):
        return self.offsets
    def setOffsets(self, offsets=(0,0)):
        self.offsets = offsets
    def offsetsNonZero(self):
        return (self.offsets[0]+self.offsets[1]) != 0
    
    def unconstrained(self, no_const):
        return no_const or self.offsetsNonZero()

    def ratio(self, num, den):
        return tool_ratio(num, den)

    def offset_ratio(self, num, den):
        return tool_ratio(num+self.offsets[0], den+self.offsets[1])

    
class CharbonTree(Charbon):

    name = "T"
    def isTreeBased(self):
        return True
    def handlesMiss(self):
        return False

    def computeExpandTree(self, side, data, red):
        targets, in_data, cols_info, basis_red = self.prepareTreeDataTrg(side, data, red)
        xps = []
        if len(basis_red) > 0:
            xps.append(basis_red)
        for target_dt in targets:
            tmp = self.getTreeCandidates(target_dt["side"], data, target_dt, in_data, cols_info)
            if tmp is not None:
                xps.append(tmp)
        return xps
    def computeInitTerm(self, colL):
        # pdb.set_trace()
        tmp = [(Literal(False,t), v) for (t,v) in colL.getInitTerms(self.constraints.getCstr("min_itm_in"), self.constraints.getCstr("min_itm_out"))]
        ## tmp = [(Literal(False,t),v) for (t,v) in colL.getInitTerms(self.constraints.getCstr("min_itm_in")/4., self.constraints.getCstr("min_itm_out")/4.)]
        # if len(tmp) > 0:
        #     print "--", colL.getId(), colL
        return tmp
    
    def prepareTreeDataTrg(self, side, data, red):
        min_entities = min(self.constraints.getCstr("min_node_size"), self.constraints.getCstr("min_itm_in"), self.constraints.getCstr("min_itm_out"))
        av_cols = data.usableIds(min_entities, min_entities)
        basis_red, lsAnon, modr = red.minusAnonRed(data)

        if len(lsAnon[0]) > 0 or len(lsAnon[1]) > 0:
            cols = [sorted(basis_red.invColsSide(s).union([l[1].colId() for l in lsAnon[s]])) for s in [0,1]]
            for s in [0,1]:
                if len(cols[s]) == 0:
                    cols[s] = av_cols[s]
        else:
            cols = av_cols

        in_data_l, tmp, tcols_l = data.getMatrix([(0, v) for v in cols[0]], bincats=True)
        in_data_r, tmp, tcols_r = data.getMatrix([(1, v) for v in cols[1]], bincats=True)

        in_data = [in_data_l.T, in_data_r.T]
        cols_info = [dict([(i,d) for (d,i) in tcols_l.items() if len(d) == 3]),
                     dict([(i,d) for (d,i) in tcols_r.items() if len(d) == 3])]
        tcols = [tcols_l, tcols_r]
            
        if side == -1:
            sides = [0,1]
        else:
            sides = [side]
        targets = []       
        for side in sides:
            if basis_red.length(side) > 0:
                supp = numpy.zeros(data.nbRows(), dtype=bool) 
                supp[list(basis_red.supp(side))] = 1
                involved = [tcols[side].get(data.getMatLitK(side, t, bincats=True)) for t in basis_red.query(side).invTerms()]
                targets.append({"side": side, "target": supp, "involved": involved, "src": basis_red.query(side)})
                
            elif len(basis_red) == 0:
                cids = []
                if len(lsAnon[side]) > 0:
                    cids = [l[1].colId() for l in lsAnon[side]]
                elif len(lsAnon[1-side]) == 0:
                    cids = av_cols[side]
                for cid in cids:
                    dcol = data.col(side, cid)
                    for lit, ss in self.computeInitTerm(dcol):
                        supp = numpy.zeros(data.nbRows(), dtype=bool) 
                        supp[list(dcol.suppLiteral(lit))] = 1
                        involved = [tcols[side].get(data.getMatLitK(side, lit, bincats=True))]
                        targets.append({"side": side, "target": supp, "involved": involved, "src": lit})
        return targets, in_data, cols_info, basis_red

    # def initializeTrg(self, side, data, red):
    #     if red is None or len(red.queries[0]) + len(red.queries[1]) == 0:
    #         nsupp = np.random.randint(self.constraints.getCstr("min_node_size"), data.nbRows()-self.constraints.getCstr("min_node_size"))
    #         tmp = np.random.choice(range(data.nbRows()), nsupp, replace=False)
    #     elif side == -1: # and len(red.queries[0]) * len(red.queries[1]) != 0:
    #         side = 1
    #         if len(red.queries[side]) == 0:
    #             side = 1-side
    #         tmp = red.supp(side)
    #     else:
    #         tmp = red.getSuppI()
    #     target = np.zeros(data.nbRows())
    #     target[list(tmp)] = 1
    #     return target, side
