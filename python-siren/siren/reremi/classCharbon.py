import numpy
try:
    from classData import Data
    from classCol import ColM
    from classQuery import  *
    from classRedescription import  Redescription
    from classSParts import tool_ratio
    from classExtension import ExtensionComb
    from classConstraints import Constraints
except ModuleNotFoundError:
    from .classData import Data
    from .classCol import ColM
    from .classQuery import  *
    from .classRedescription import  Redescription
    from .classSParts import tool_ratio
    from .classExtension import ExtensionComb
    from .classConstraints import Constraints

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

    def getCombinedCands(self, ext_lits, common, reds, cols):
        ### basic check that the queries are compatible,
        ### same side, same neg for all common literals
        compatible = len(common[0]) == len(common[1]) and all([(common[0][i][0] == common[1][i][0]) and (common[0][i][2].isNeg() == common[1][i][2].isNeg()) for i in range(len(common[0]))])

        ext_side = ext_lits[1][0]
        currentRStatus = Constraints.getStatusRed(reds[0], ext_side)
        cand_ops = self.constraints.getCstr("allw_ops", side=ext_side, currentRStatus=currentRStatus)

        ### in maps, True stands for "OR", "disjunction", "union"
        ###          False stands for "AND", "conjunction", "intersection"
        #### allowing "mixed-combinations" means trying conjunctive extension with union of literals' ranges and vice-versa (where relevant)
        ext_elems = {} ### conj-inter, disj-union, disj-inter, conj-union
        ext_op0 = reds[0].query(ext_side).getOuterOp()
        ext_op1 = reds[1].query(ext_side).getOuterOp()
        ext_ops_inds = []
        if ext_lits[0][0] != ext_side or ext_op1 == ext_op0:
            ### extension elements are not on the same side, or operators are equal (possibly not defined)
            if ext_op1.isSet():
                if ext_op1.isOr() in cand_ops:
                    ext_ops_inds = [(ext_op1.isOr(), (-1,))]
            else:
                ext_ops_inds = [(op, (-1,)) for op in cand_ops]                
        else:
            ### on same side, different operators
            if ext_op0.isSet():
                if ext_op1.isSet(): ### both ops are set, but different
                    if ext_op1.isOr() in cand_ops:
                        ext_ops_inds.append((ext_op1.isOr(), (None,)))
                else:
                    op = ext_op0.isOr()
                    if op in cand_ops:
                        ext_ops_inds.append((op, (-1,)))
                    op = not op
                    if op in cand_ops:
                        ext_ops_inds.append((op, (None,)))

            elif ext_op1.isOr() in cand_ops:
                ext_ops_inds.append((ext_op1.isOr(), (-1,)))

        for ext_op, ind in ext_ops_inds:
            ext_elems[(ext_op, ext_op)] = {"ind": ind, "lits": []}
            if self.constraints.getCstr("mixed_combinations"):
                ext_elems[(ext_op, not ext_op)] = {"ind": ind, "lits": []}
                
        if len(ext_elems) == 0:
            return []
                
        same_uandi = True
        for cci, col in enumerate(cols):
            cid, side, tid = col.getId(), col.getSide(), col.typeId()

            lA, lB = common[0][cci][-1], common[1][cci][-1]
            lARng = lA.valRange()
            lBRng = lB.valRange()

            lit = {True: None, False: None}
            if Data.isTypeId(tid, "Numerical"):
                if lARng[0] == lBRng[0] and lARng[1] == lBRng[1]:
                    lit[False] = NumTerm(cid, lARng[0], lARng[1])
                    lit[True] = NumTerm(cid, lARng[0], lARng[1])
                else:
                    same_uandi = False
                    interv = [numpy.maximum(lARng[0], lBRng[0]), numpy.minimum(lARng[1], lBRng[1])]
                    if interv[0] <= interv[1]:
                        lit[False] = NumTerm(cid, interv[0], interv[1])
                    univ = [numpy.minimum(lARng[0], lBRng[0]), numpy.maximum(lARng[1], lBRng[1])]
                    if univ[0] > col.getMin() or univ[1] < col.getMax():
                        lit[True] = NumTerm(cid, univ[0], univ[1])
            elif Data.isTypeId(tid, "Categorical"):
                if lARng == lBRng:
                    lit[False] = CatTerm(cid, set(lARng))
                    lit[True] = CatTerm(cid, set(lARng))
                else:
                    same_uandi = False
                    interv = set(lARng).intersection(lBRng)
                    if len(interv) > 0:
                        lit[False] = CatTerm(cid, interv)
                    univ = set(lARng).union(lBRng)
                    if len(univ) < col.nbCats():
                        lit[True] = CatTerm(cid, univ)
            else:
                lit[False] = BoolTerm(cid)
                lit[True] = BoolTerm(cid)

            for k in ext_elems.keys():
                if ext_elems[k]["lits"] is not None:                                        
                    if lit[k[1]] is not None:
                        ext_elems[k]["lits"].append((common[0][cci][0], common[0][cci][1], Literal(lA.isNeg(), lit[k[1]])))
                    else:
                        ext_elems[k]["lits"] = None
                        
            if all([v["lits"] is None for v in ext_elems.values()]):
                return []

        if same_uandi: ### unions and intersections of literals' ranges are all same, no need to try mixed           
            ext_elems.pop((True, False), None)
            ext_elems.pop((False, True), None)

        cands = []
        for k, ext_elem in ext_elems.items():
            if ext_elem["lits"] is not None:
                lits = ext_elem["lits"]+[(ext_lits[0][0], ext_lits[0][1], ext_lits[0][2].copy()),
                                        (ext_lits[1][0], ext_elem["ind"], ext_lits[1][2].copy())]               
                cands.append(ExtensionComb(self.constraints.getSSetts(), reds[0], lits, k[0], 2*(k[0]==k[1])+k[0]))
        return cands

    
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
        #     print("--", colL.getId(), colL)
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
