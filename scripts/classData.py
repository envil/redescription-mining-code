import math, random, re
from classLog import Log
from classRule import Op, Item, BoolItem, CatItem, NumItem, Term, Rule 
from classRedescription import Redescription
from classSParts import SParts
from classBestsDraft import BestsDraft
import pdb

class ColM:

    def miss(self):
        return self.missing

    def suppTerm(self, term):
        if term.isNeg():
            return set(range(self.N)) - self.suppItem(term.item) - self.miss()
        else:
            return self.suppItem(term.item)

    def lMiss(self):
        return len(self.missing)

    def lSuppTerm(self, term):
        if term.isNeg():
            return self.N - len(self.suppItem(term.item)) - len(self.miss())
        else:
            return len(self.suppItem(term.item))

    def nbRows(self):
        return self.N

class BoolColM(ColM):
    type_id = 1

    def __str__(self):
        return "boolean variable (density=%i/%i, %i missing values)" %(self.lTrue(), self.N, len(self.miss()))

    def __init__(self, ncolSupp=[], N=-1, nmiss=set()):
        self.hold = ncolSupp
        self.N = N
        self.missing = nmiss

    def supp(self):
        return self.hold
    
    def suppItem(self, item):
        return set(self.hold)

    def lTrue(self):
        return len(self.hold)

    def lFalse(self):
        return self.nbRows() - self.lTrue() - len(self.miss())

    def nonFull(self, minIn, minOut):
        if self.lTrue() >= minIn and self.lFalse() >= minOut :
            return True
        return False

    def anyAdvance(self, constraints, supports, side, col):
        res = []
        lparts = supports.lparts()
        lmiss = supports.lpartsInterX(self.missing)
        lin = supports.lpartsInterX(self.hold)

        for op in constraints.ruleTypesOp():
            for neg in constraints.ruleTypesNP(op):
                b = constraints.compAdv(Term(neg, BoolItem(col)), side, op, neg, lparts, lmiss, lin)
                if b != None:
                    res.append(b)
        return res
    
class CatColM(ColM):
    type_id = 2

    def __str__(self):
        return "categorical variable (%i categories, %i rows, %i missing values)" %(len(self.cats()), self.nbRows(), len(self.miss()))

    def __init__(self, ncolSupp=[], N=-1, nmiss= set()):
        self.sCats = ncolSupp
        self.N = N
        self.missing = nmiss
        self.cards = sorted([(cat, len(self.suppCat(cat))) for cat in self.cats()], key=lambda x: x[1]) 
            
    def cats(self):
        return self.sCats.keys()

    def suppCat(self, cat):
        if cat in self.sCats.keys():
            return self.sCats[cat]
        else:
            return set()
            
    def suppItem(self, item):
        return self.suppCat(item.cat)

    def nonFull(self, minIn, minOut):
        if self.cards[-1][1] >= minIn and self.nbRows() - self.cards[0][1] >= minOut :
            return True
        return False

    def fit(self, constraints, supports, side, col, itemX):
        (scores, termsFix, termsExt) = ([], [], [])   
        lparts = supports.lparts()
        lmiss = supports.lpartsInterX(self.miss())
        
        (cand_Fix, cand_FixB) = CatColM.findCoverFullSearch(True, constraints, lparts, lmiss, self.sCats, supports, side, col, True )

        for cand in cand_Fix:
            scores.append(BestsDraft.score(cand, self.nbRows()))
            termsFix.append(Term(False, itemX))
            termsExt.append(cand['term'])

        for cand in cand_FixB:
            scores.append(BestsDraft.score(cand, self.nbRows()))
            termsFix.append(Term(True, itemX))
            termsExt.append(cand['term'])
        return (scores, termsFix, termsExt)

    
    def anyAdvance(self, constraints, supports, side, col):
        res = []
        lparts = supports.lparts()
        lmiss = supports.lpartsInterX(self.miss())

        for op in constraints.ruleTypesOp():
            if constraints.inSuppBounds(side, op, lparts): ### DOABLE 
                res.extend(CatColM.findCoverFullSearch(op, constraints, lparts, lmiss, self.sCats, supports, side, col))
        return res

    def findCoverFullSearch(op, constraints, lparts, lmiss, scats, supports, side, col, negB=False):
        res = []
        doNegB = negB  and (True in constraints.ruleTypesNP(op))
        resNegB = [] 
        bests = [None, None]
        bestsNegB = [None, None]
        
        for (cat, supp) in scats.iteritems():
            lin = supports.lpartsInterX(supp)
            for neg in constraints.ruleTypesNP(op):
                tmp_comp = constraints.compAdv(cat, side, op, neg, lparts, lmiss, lin)
                if BestsDraft.comparePair(tmp_comp, bests[neg]) > 0:
                    bests[neg] = tmp_comp

                if doNegB :
                    tmp_comp = constraints.compAdv(cat, side, op, neg, SParts.negateParts(1-side, lparts), SParts.negateParts(1-side, lmiss), SParts.negateParts(1-side, lin))
                    if BestsDraft.comparePair(tmp_comp, bestsNegB[neg]) > 0:
                        bestsNegB[neg] = tmp_comp

        for neg in constraints.ruleTypesNP(op):
            if bests[neg] != None  :
                t = bests[neg]['term']
                bests[neg].update({'term': Term(neg, CatItem(col, t))})
                res.append(bests[neg])
            if doNegB and bestsNegB[neg] != None  :
                t = bestsNegB[neg]['term']
                bestsNegB[neg].update({'term': Term(neg, CatItem(col, t))})
                resNegB.append(bestsNegB[neg])
        if negB:
            return (res, resNegB)
        else:
            return res
    findCoverFullSearch = staticmethod(findCoverFullSearch)
    
class NumColM(ColM):
    type_id = 3
    maxSeg = 100

    def __str__(self):
        return "numerical variable (%i values not in mode, %i rows, %i missing values)" %(self.lenNonMode(), self.nbRows(), len(self.miss()))

    def __init__(self, ncolSupp=[], N=-1, nmiss=set()):
        self.sVals = ncolSupp
        self.N = N
        self.missing = nmiss
        self.mode = {}
        self.buk = None
        
        if len(self.sVals)+len(self.missing) != self.N :
            tmp = set([r[1] for r in self.sVals])
            if -1 in tmp:
                tmp.remove(-1)
            if 2*len(tmp) > self.N:
                self.mode = (-1, set(range(self.N)) - tmp - self.missing)
            else:
                self.mode = (1, tmp)
        else:
            self.mode = (0, None)
    
    def interNonMode(self, suppX):
        if self.mode[0] == -1:
            return suppX - self.mode[1] - self.miss()
        elif self.mode[0] == 1:
            return suppX & self.mode[1]
        else:
            return suppX - self.miss()  

    
    def interMode(self, suppX):
        if self.mode[0] == 1:
            return suppX - self.mode[1] - self.miss()
        elif self.mode[0] == -1:
            return suppX & self.mode[1]
        else:
            return set()    
        
    def lenNonMode(self):
        if self.mode[0] == -1:
            return self.nbRows() - len(self.mode[1]) - len(self.miss())
        elif self.mode[0] == 1:
            return len(self.mode[1])
        else:
            return self.nbRows() - len(self.miss())
        
    def lenMode(self):
        if self.mode[0] == 1:
            return self.nbRows() - len(self.mode[1]) - len(self.miss())
        elif self.mode[0] == -1:
            return len(self.mode[1])
        else:
            return 0
        
    def nonModeSupp(self):
        if self.mode[0] == -1:
            return set(range(self.nbRows())) - self.mode[1] - self.miss()
        elif self.mode[0] == 1:
            return self.mode[1]
        else:
            return set(range(self.nbRows()))-self.miss()

    def modeSupp(self):
        if self.mode[0] == 1:
            return set(range(self.nbRows())) - self.mode[1] -self.miss()
        elif self.mode[0] == -1:
            return self.mode[1]
        else:
            return set()

    def nonFull(self, minIn, minOut):
        if self.lenNonMode() >= minOut or self.lenNonMode() >= minIn :
            return True
        return False

    def buckets(self):
        if self.buk == None:
            self.buk = self.makeBuckets()
        return self.buk

    def makeBuckets(self):
        if self.sVals[0][1] != -1 :
            bucketsSupp = [set([self.sVals[0][1]])]
        else:
            bucketsSupp = [set()]
        bucketsVal = [self.sVals[0][0]]
        bukMode = None
        for (val , row) in self.sVals:
            if row == -1: 
                if val != bucketsVal[-1]: # should be ...
                    bucketsVal.append(val)
                    bucketsSupp.append(set())
                bukMode = len(bucketsVal)-1
            else:
                if val == bucketsVal[-1]:
                    bucketsSupp[-1].add(row)
                else:
                    bucketsVal.append(val)
                    bucketsSupp.append(set([row]))
        return (bucketsSupp, bucketsVal, bukMode)

    def suppItem(self, item):
        suppIt = set()
        for (val , row) in self.sVals:
            if val > item.upb :
                return suppIt
            elif val >= item.lowb:
                if row == -1:
                    suppIt.update(self.modeSupp())
                else:
                    suppIt.add(row)
        return suppIt

    def fit(self, constraints, supports, side, col, itemX):
        (scores, termsFix, termsExt) = ([], [], [])    
        lparts = supports.lparts()
        lmiss = supports.lpartsInterX(self.miss())

        if constraints.inSuppBounds(side, True, lparts): ### DOABLE
            segments = self.makeSegments(side, supports, constraints.ruleTypesOp())
            res = NumColM.findCover(segments, lparts, lmiss, side, col, constraints)
 
            for cand in res:
                scores.append(BestsDraft.score(cand, self.nbRows()))
                termsFix.append(Term(False, itemX))
                termsExt.append(cand['term'])

        nlparts = SParts.negateParts(1-side, lparts)
        nlmiss = SParts.negateParts(1-side, lmiss)

        if len(constraints.negTypesInit()) == 4 and constraints.inSuppBounds(side, True, lparts): ### DOABLE
            nsegments = self.makeSegments(side, supports.negate(1-side), constraints.ruleTypesOp())
            res = NumColM.findCover(nsegments, nlparts, nlmiss, side, col, constraints)
            
            for cand in res:            
                scores.append(BestsDraft.score(cand, self.nbRows()))
                termsFix.append(Term(True, itemX))
                termsExt.append(cand['term'])

        return (scores, termsFix, termsExt)

    def anyAdvance(self, constraints, supports, side, col):
        res = []
        lparts = supports.lparts()
        lmiss = supports.lpartsInterX(self.miss())

        if constraints.inSuppBounds(side, True, lparts) or constraints.inSuppBounds(side, False, lparts):  ### DOABLE
            segments = self.makeSegments(side, supports, constraints.ruleTypesOp())
            res = NumColM.findCover(segments, lparts, lmiss, side, col, constraints)
        return res
    
    def makeSegments(self, side, supports, ops =[ False, True]):
        supports.makeVectorABCD()
        segments = [[[self.sVals[0][0], None, SParts.makeLParts()]], [[self.sVals[0][0], None, SParts.makeLParts()]]]
        current_valseg = [[self.sVals[0][0], self.sVals[0][0], SParts.makeLParts()], [self.sVals[0][0], self.sVals[0][0], SParts.makeLParts()]]
        for (val, row) in self.sVals+[(None, None)]:
            tmp_lparts = supports.lpartsRow(row, self)

            for op in ops:
                if val != None and val == current_valseg[op][0]: 
                    current_valseg[op][2] = SParts.addition(current_valseg[op][2], tmp_lparts)
                else:
                    tmp_pushadd = SParts.addition(segments[op][-1][2], current_valseg[op][2]) 
                    if segments[op][-1][1]==None or SParts.sumPartsId(side, SParts.IDS_varnum[op], tmp_pushadd)*SParts.sumPartsId(side, SParts.IDS_varden[op], tmp_pushadd) == 0:
                        segments[op][-1][2] = tmp_pushadd
                        segments[op][-1][1] = current_valseg[op][1]
                    else:
                        segments[op].append(current_valseg[op])
                    current_valseg[op] = [val, val, SParts.addition(SParts.makeLParts(),tmp_lparts)]
        return segments
            
    def findCover(segments, lparts, lmiss, side, col, constraints):
        res = []
        for op in constraints.ruleTypesOp():
            if len(segments[op]) < NumColM.maxSeg:
                Data.logger.printL(100,'---Doing the full search---')
                res.extend(NumColM.findCoverFullSearch(op, segments, lparts, lmiss, side, col, constraints))
            else:
                Data.logger.printL(100,'---Doing the fast search---')
                if (False in constraints.ruleTypesNP(op)):
                    res.extend(NumColM.findPositiveCover(op, segments, lparts, lmiss, side, col, constraints))
                if (True in constraints.ruleTypesNP(op)):
                    res.extend(NumColM.findNegativeCover(op, segments, lparts, lmiss, side, col, constraints))
        return res
    findCover = staticmethod(findCover)

    def findCoverFullSearch(op, segments, lparts, lmiss, side, col, constraints):
        res = []
        bests = {False: None, True: None}

        for seg_s in range(len(segments[op])):
            lin = SParts.makeLParts()

            for seg_e in range(seg_s,len(segments[op])):
                lin = SParts.addition(lin, segments[op][seg_e][2])
                for neg in constraints.ruleTypesNP(op):
                    tmp_comp = constraints.compAdv((seg_s, seg_e), side, op, neg, lparts, lmiss, lin)
                    if BestsDraft.comparePair(tmp_comp, bests[neg]) > 0:
                        bests[neg] = tmp_comp
        for neg in constraints.ruleTypesNP(op):
            
            if bests[neg] != None:
                (n, t) = NumColM.makeTermSeg(neg, segments[op], col, bests[neg]['term'])
                if t != None:
                    bests[neg].update({'term': t, 'neg':n })
                    res.append(bests[neg])

#             if bests[neg] != None and (bests[neg]['term'][0] != 0 or  bests[neg]['term'][1] != len(segments[op])-1)  :
#                 if bests[neg]['term'][0] == 0:
#                     lowb = float('-Inf')
#                 else:
#                     lowb = segments[op][bests[neg]['term'][0]][0]
#                 if bests[neg]['term'][1] == len(segments[op])-1 :
#                     upb = float('Inf')
#                 else:
#                     upb = segments[op][bests[neg]['term'][1]][1]
#                 bests[neg].update({'term': Term(neg, NumItem(col, lowb, upb))})
#                 res.append(bests[neg])
        return res
    findCoverFullSearch = staticmethod(findCoverFullSearch)

    def findNegativeCover(op, segments, lparts, lmiss, side, col, constraints):
        res = []
        lin_f = SParts.makeLParts()
        bests_f = [(constraints.compAcc(side, op, False, lparts, lmiss, lin_f), 0, lin_f)] 
        best_track_f = [0]
        lin_b = SParts.makeLParts()
        bests_b = [(constraints.compAcc(side, op, False, lparts, lmiss, lin_b), 0, lin_f)]
        best_track_b = [0]

        for  i in range(len(segments[op])):
            # FORWARD
            lin_f = SParts.addition(lin_f, segments[op][i][2])
            if  SParts.compRatioVar(side, op, lin_f) > bests_f[-1][0]:
                lin_f = SParts.addition(lin_f, bests_f[-1][2])
                bests_f.append((constraints.compAcc(side, op, False, lparts, lmiss, lin_f), i+1, lin_f))
                lin_f = SParts.makeLParts()
            best_track_f.append(len(bests_f)-1)

            # BACKWARD
            lin_b = SParts.addition(lin_b, segments[op][-(i+1)][2])
            if  SParts.compRatioVar(side, op, lin_b) > bests_b[-1][0]:
                lin_b = SParts.addition(lin_b, bests_b[-1][2])
                bests_b.append((SParts.compAcc(side, op, False, lparts, lmiss, lin_b), i+1, lin_b))
                lin_b = SParts.makeLParts()
            best_track_b.append(len(bests_b)-1)

        best_t = None
        best_tb_l = []
        for b in bests_b:
            if b[1] == len(segments[op]):
                f = bests_f[0]
            else:
                f = bests_f[best_track_f[len(segments[op])-(b[1]+1)]]
            if SParts.compRatioVar(side, op, f[2]) > b[0]:
                tmp_comp_tb = constraints.compAdv((f[1], len(segments[op]) - (b[1]+1)), side, op, False, lparts, lmiss, SParts.addition(f[2], b[2]))
            else:
                tmp_comp_tb = constraints.compAdv((0, len(segments[op]) - (b[1]+1)), side, op, False, lparts, lmiss, b[2])
            best_tb_l.append(tmp_comp_tb)
            if BestsDraft.comparePair(tmp_comp_tb, best_t) > 0:
                best_t = tmp_comp_tb

        best_tf_l = []
        for f in bests_f:
            if f[1] == len(segments[op]):
                b = bests_b[0]
            else:
                b = bests_b[best_track_b[len(segments[op])-(f[1]+1)]]
            if SParts.compRatioVar(side, op, b[2]) > f[0]: 
                tmp_comp_tf = constraints.compAdv((f[1], len(segments[op]) - (b[1]+1)), side,  op, False, lparts, lmiss, SParts.addition(f[2], b[2]))
            else:
                tmp_comp_tf = constraints.compAdv((f[1], len(segments)-1), side, op, False, lparts, lmiss, f[2])
            best_tf_l.append(tmp_comp_tf)
            if BestsDraft.comparePair(tmp_comp_tf, best_t) > 0:
                best_t = tmp_comp_tf


        if best_t != None:
            (n, t) = NumColM.makeTermSeg(True, segments[op], col, best_t['term'])
            if t != None:
                best_t.update({'term': t, 'neg':n })
                res.append(best_t)

#         if best_t != None and best_t['term'][0] <= best_t['term'][1] and ((best_t['term'][0] != 0) or (best_t['term'][1] != len(segments[op])-1)) :
#             if best_t['term'][0] == 0:
#                 lowb = float('-Inf')
#             else:
#                 lowb = segments[op][best_t['term'][0]][0]
#             if best_t['term'][1] == len(segments[op])-1 :
#                 upb = float('Inf')
#             else:
#                 upb = segments[op][best_t['term'][1]][1]
#             best_t.update({'term': Term(True, NumItem(col, lowb, upb))})
#             res.append(best_t)
        return res
    findNegativeCover = staticmethod(findNegativeCover)

    def findPositiveCover(op, segments, lparts, lmiss, side, col, constraints):
        res = []
        lin_f = SParts.makeLParts()
        nb_seg_f = 0
        best_f = None
        lin_b = SParts.makeLParts()
        nb_seg_b = 0
        best_b = None 

        for  i in range(len(segments[op])-1):
            # FORWARD
            if i > 0 and \
               constraints.compAcc(side, op, False, lparts, lmiss, segments[op][i][2]) < SParts.compRatioVar(side, op, lin_f):
                lin_f = SParts.addition(lin_f, segments[op][i][2])
                nb_seg_f += 1
            else: 
                lin_f = segments[op][i][2]
                nb_seg_f = 0
            tmp_comp_f = constraints.compAdv((i - nb_seg_f, i), side, op, False, lparts, lmiss, lin_f)
            if BestsDraft.comparePair(tmp_comp_f, best_f) > 0 :
                best_f = tmp_comp_f

            # BACKWARD
            if i > 0 and \
               constraints.compAcc(side, op, False, lparts, lmiss, segments[op][-(i+1)][2]) < SParts.compRatioVar(side, op, lin_b):
                lin_b = SParts.addition(lin_b, segments[op][-(i+1)][2])
                nb_seg_b += 1
            else:
                lin_b = segments[op][-(i+1)][2]
                nb_seg_b = 0
            tmp_comp_b = constraints.compAdv((len(segments[op])-(1+i), len(segments[op])-(1+i) + nb_seg_b), side, op, False, lparts, lmiss, lin_b)
            if BestsDraft.comparePair(tmp_comp_b, best_b) > 0 :
                best_b = tmp_comp_b


        if best_b != None and best_f != None :
            bests = [best_b, best_f]

            if best_b['term'][0] > best_f['term'][0] and best_b['term'][1] > best_f['term'][1] and best_b['term'][0] <= best_f['term'][1]:
                lin_m = SParts.makeLParts()
                for seg in segments[op][best_b['term'][0]:best_f['term'][1]+1]:
                    lin_m = SParts.addition(lin_m, seg[2])


                tmp_comp_m = constraints.compAdv((best_b['term'][0], best_f['term'][1]), side, op, False, lparts, lmiss, lin_m)
                if tmp_comp_m != None:
                    bests.append(tmp_comp_m)
                        
            best = sorted(bests, cmp=BestsDraft.comparePair)[-1]

        elif best_f == None:
            best = best_f
        else:
            best = best_b

        if best != None:
            (n, t) = NumColM.makeTermSeg(False, segments[op], col, best['term'])
            if t != None:
                best.update({'term': t, 'neg':n })
                res.append(best)
        return res
    findPositiveCover = staticmethod(findPositiveCover)

    def makeTermSeg(neg, segments_op, col, bound_ids):
        if bound_ids[0] == 0 and bound_ids[1] == len(segments_op)-1:
            return (neg, None)
        elif bound_ids[0] == 0 :
            if neg:
                lowb = segments_op[bound_ids[1]+1][0]
                upb = float('Inf')
                n = False
            else:
                lowb = float('-Inf')
                upb = segments_op[bound_ids[1]][1]
                n = False
        elif bound_ids[1] == len(segments_op)-1 :
            if neg:
                lowb = float('-Inf') 
                upb = segments_op[bound_ids[0]-1][1]
                n = False
            else:
                lowb = segments_op[bound_ids[0]][0]
                upb = float('Inf') 
                n = False
        else:
            lowb = segments_op[bound_ids[0]][0]
            upb = segments_op[bound_ids[1]][1]
            n = neg
        return (n, Term(n, NumItem(col, lowb, upb)))
    makeTermSeg = staticmethod(makeTermSeg)


    def makeTermBuk(neg, buk_op, col, bound_ids):
        if bound_ids[0] == 0 and bound_ids[1] == len(buk_op)-1:
            return (neg, None)
        elif bound_ids[0] == 0 :
            if neg:
                lowb = buk_op[bound_ids[1]+1]
                upb = float('Inf')
                n = False
            else:
                lowb = float('-Inf')
                upb = buk_op[bound_ids[1]]
                n = False
        elif bound_ids[1] == len(buk_op)-1 :
            if neg:
                lowb = float('-Inf') 
                upb = buk_op[bound_ids[0]-1]
                n = False
            else:
                lowb = buk_op[bound_ids[0]]
                upb = float('Inf') 
                n = False
        else:
            lowb = buk_op[bound_ids[0]]
            upb = buk_op[bound_ids[1]]
            n = neg
        return (n, Term(n, NumItem(col, lowb, upb)))
    makeTermBuk = staticmethod(makeTermBuk)


class Data:

    defaultMinC = 1
    logger = Log(0)
    
    def __init__(self, datafiles):
        (self.cols, self.type_ids, self.N) = readData(datafiles)
        self.redunRows = set()
        self.nf = [[i for i in range(self.nbCols(0))], [i for i in range(self.nbCols(1))]]
        Data.logger.printL(7, 'Left Hand side columns')
        for col in self.cols[0]:
            Data.logger.printL(7, col)
        Data.logger.printL(7, 'Right Hand side columns')
        for col in self.cols[1]:
            Data.logger.printL(7, col)
            
    def __str__(self):
        return "%i x %i+%i data" % ( self.nbRows(), self.nbCols(0), self.nbCols(1))

    def nbRows(self):
        return self.N

    def nbCols(self, side):
        return len(self.cols[side])
        
    def supp(self, side, term): 
        return self.cols[side][term.item.colId()].suppTerm(term)- self.redunRows

    def miss(self, side, term): 
        return self.cols[side][term.item.colId()].miss()- self.redunRows

    def termSuppMiss(self, side, term):
        return (self.supp(side, term), self.miss(side,term))
        
    def addRedunRows(self, redunRows):
	self.redunRows.update(redunRows)
    
    def scaleF(self, f):
        if f >= 1:
            return int(f)
        elif f >= 0 and f < 1 :
            return  int(round(f*self.nbRows()))
    
    def scaleSuppParams(self, minC=None, minIn=None, minOut=None):
        if minC == None:
            rMinC = Data.defaultMinC
        else:
            rMinC = self.scaleF(minC)
        if minIn == None:
            rMinIn = rMinC
        else:
            rMinIn = self.scaleF(minIn)
        if minOut == None:
            rMinOut = self.N - rMinIn
        else:
            rMinOut = self.scaleF(minOut)
        self.nf = [[col for col in range(len(self.cols[0])) if self.cols[0][col].nonFull(rMinC, rMinC)], \
             [col for col in range(len(self.cols[1])) if self.cols[1][col].nonFull(rMinC, rMinC)] ]
        return (rMinC, rMinIn, rMinOut)
            
    def nonFull(self):
        return [set(self.nf[0]), set(self.nf[1])]
    def nbNonFull(self, side):
        return len(self.nf[side])

    def updateBests(self, bests, constraints, supports, side, col):
        bests.upBests(self.cols[side][col].anyAdvance(constraints, supports, side, col))

    def computePairParts11(self, colL, idL, colR, idR, constraints, side):
        supports = SParts(self.nbRows(), [colL.supp(), set(), colL.miss(), set()])
        lparts = supports.lparts()
        lmiss = supports.lpartsInterX(colR.miss())
        lin = supports.lpartsInterX(colR.supp())
        (scores, termsFix, termsExt) = ([], [], [])        

        for (i, nL, nR) in constraints.negTypesInit():
            if nL:
                tmp_lparts = SParts.negateParts(0, lparts)
                tmp_lmiss = SParts.negateParts(0, lmiss)
                tmp_lin = SParts.negateParts(0, lin)
            else:
                tmp_lparts = lparts
                tmp_lmiss = lmiss
                tmp_lin = lin

            if constraints.inSuppBounds(side, True, tmp_lparts): ### DOABLE
                cand = constraints.compAdv(idR, 1, True, nR, tmp_lparts, tmp_lmiss, tmp_lin)
                if cand != None:
                    scores.append(BestsDraft.score(cand, self.nbRows()))
                    termsFix.append(Term(nL, BoolItem(idL)))
                    termsExt.append(Term(nR, BoolItem(idR)))
        return (scores, termsFix, termsExt)

    def computePairPartsBoolNonBool(self, colL, idL, colR, idR, constraints, side):
        if side == 1:
            (supports, fixCol, fixItem, extCol, extId) = (SParts(self.nbRows(), [colL.supp(), set(), colL.miss(), set()]), colL, BoolItem(idL), colR, idR)
        else:
            (supports, fixCol, fixItem, extCol, extId) = (SParts(self.nbRows(), [set(), colR.supp(), set(), colR.miss()]), colR, BoolItem(idR), colL, idL)

        return extCol.fit(constraints, supports, side, extId, fixItem)
    
    def computePairParts12(self, colL, idL, colR, idR, constraints, side):
        return self.computePairPartsBoolNonBool(colL, idL, colR, idR, constraints, side)
        
    def computePairParts13(self, colL, idL, colR, idR, constraints, side):
        return self.computePairPartsBoolNonBool(colL, idL, colR, idR, constraints, side)
        
    def computePairParts22(self, colL, idL, colR, idR, constraints, side):
        return self.computePairParts22Full(colL, idL, colR, idR, constraints, side)

    def computePairParts23(self, colL, idL, colR, idR, constraints, side):
        return self.computePairParts23Full(colL, idL, colR, idR, constraints, side)
    
    def computePairParts33(self, colL, idL, colR, idR, constraints, side):
#         if len(init_info[1-side]) == 3: # fit FULL
#             if len(init_info[1-side][0]) > len(init_info[side][0]): 
#                 (scores, termsB, termsA)= self.computePairParts33Full(colL, idL, colR, idR, constraints, side)
#                 return (scores, termsA, termsB)
#             else:
#                 return self.computePairParts33Full(colL, idL, colR, idR, constraints, side)
#         else:
#             return self.computePairParts33Heur(colL, idL, colR, idR, constraints, side)
        if len(colL.interNonMode(colR.nonModeSupp())) >= constraints.minItmSuppIn() :
            return self.computePairParts33Full(colL, idL, colR, idR, constraints, side)
        else:
            return ([], [], [])
    
    def computePairParts33Heur(self, colL, idL, colR, idR, constraints, side):
        bestScore = None
        if constraints.inSuppBoundsMode(colL.lenMode(), colR.lenMode(), self.nbRows()): ### DOABLE
            ## FIT LHS then RHS
            supports = SParts(self.N, [set(), colR.nonModeSupp(), set(), colR.miss()])
            (scoresL, termsFixL, termsExtL) = colL.fit(constraints, supports, 0, idL, idR)
            for tL in termsExtL:
                suppL = self.supp(0,tL)
                supports = SParts(self.nbRows(), [suppL, set(), colL.miss(), set()])
                (scoresR, termsFixR, termsExtR) = colR.fit(constraints, supports, 1, idR, idL)
                for i in range(len(scoresR)):
                    if scoresR[i] > bestScore:
                        (scores, termsL, termsR) = ([scoresR[i]], [termsFixR[i]], [termsExtR[i]])
                        bestScore = scoresR[i]
                        
            ## FIT RHS then LHS
            supports = SParts(self.nbRows(), [colL.nonModeSupp(), set(), colL.miss(), set()])
            (scoresR, termsFixR, termsExtR) = colR.fit(constraints, supports, 1, idR, idL)
            for tR in termsExtR:
                suppR = self.supp(1,tR)
                supports = SParts(self.N, [set(), suppR, set(), colR.miss()])
                (scoresL, termsFixL, termsExtL) = colL.fit(constraints, supports, 0, idL, idR)
                for i in range(len(scoresL)):
                    if scoresL[i] > bestScore:
                        (scores, termsL, termsR) = ([scoresR[i]], [termsExtL[i]], [termsFixL[i]])
                        bestScore = scoresL[i]
                        
#             if len(scores) > 0:
#                print "%f: %s <-> %s" % (scores[0], termsA[0], termsB[0])
        return (scores, termsL, termsR)

    def computePairParts33Full(self, colL, idL, colR, idR, constraints, side):
        best =  None
        
        interMat = []
        bucketsL = colL.buckets()
        bucketsR = colR.buckets()

        if len(bucketsL[0]) > len(bucketsR[0]):
            bucketsF = bucketsR; colF = colR; idF = idR; bucketsE = bucketsL; colE = colL; idE = idL; side = 1-side; flip_side = True
        else:
            bucketsF = bucketsL; colF = colL; idF = idL; bucketsE = bucketsR; colE = colR; idE = idR; flip_side = False
            
        (scores, termsF, termsE) = ([], [], [])
        ## DOABLE
        if ( len(bucketsF) * len(bucketsE) <= 1000 ): 

            partsMubB = len(colF.miss())
            missMubB = len(colF.miss() & colE.miss())
            totInt = self.nbRows() - len(colF.miss()) - len(colE.miss()) + missMubB
            #margE = [len(intE) for intE in bucketsE[0]]
            
            lmissFinE = [len(colF.miss() & bukE) for bukE in bucketsE[0]]
            lmissEinF = [len(colE.miss() & bukF) for bukF in bucketsF[0]]
            margF = [len(bucketsF[0][i]) - lmissEinF[i] for i in range(len(bucketsF[0]))]
            totMissE = len(colE.miss())
            totMissEinF = sum(lmissEinF)
            
            for bukF in bucketsF[0]: 
                interMat.append([len(bukF & bukE) for bukE in bucketsE[0]])
            
            if bucketsF[2] != None :
                margF[bucketsF[2]] += colF.lenMode()
                for bukEId in range(len(bucketsE[0])):
                    interMat[bucketsF[2]][bukEId] += len(colF.interMode(bucketsE[0][bukEId])) 

            if bucketsE[2] != None :
                #margE[bucketsE[2]] += colE.lenMode()
                for bukFId in range(len(bucketsF[0])):
                    interMat[bukFId][bucketsE[2]] += len(colE.interMode(bucketsF[0][bukFId]))        

            if bucketsF[2] != None and bucketsE[2] != None:
                interMat[bucketsF[2]][bucketsE[2]] += len(colE.interMode(colF.modeSupp()))

#             ### check marginals
#             totF = 0
#             for iF in range(len(bucketsF[0])):
#                 sF = sum(interMat[iF])
#                 if sF != margF[iF]:
#                     raise Error('Error in computing the marginals (1)')
#                 totF += sF

#             totE = 0
#             for iE in range(len(bucketsE[0])):
#                 sE = sum([intF[iE] for intF in interMat])
#                 if sE != margE[iE]:
#                     raise Error('Error in computing the marginals (2)')
#                 totE += sE

#             if totE != totF or totE != self.nbRows():
#                 raise Error('Error in computing the marginals (3)')


            belowF = 0
            lowF = 0
            while lowF < len(interMat) and totInt - belowF >= constraints.minItmSuppIn():
                aboveF = 0
                upF = len(interMat)-1
                while upF >= lowF and totInt - belowF - aboveF >= constraints.minItmSuppIn():
                    if belowF + aboveF  >= constraints.minItmSuppOut():
                        EinF = [sum([interMat[iF][iE] for iF in range(lowF,upF+1)]) for iE in range(len(interMat[lowF]))]
                        EoutF = [sum([interMat[iF][iE] for iF in range(0,lowF)+range(upF+1,len(interMat))]) for iE in range(len(interMat[lowF]))]
                        lmissE = sum(lmissEinF[lowF:upF+1])
                        #totEinF = sum(EinF)
                        
                        lparts = SParts.makeLParts([(SParts.partId(SParts.alpha, 1-side), totInt - aboveF - belowF + lmissE), \
                                                    (SParts.partId(SParts.mubB, 1-side), partsMubB ), \
                                                    (SParts.partId(SParts.delta, 1-side), aboveF + belowF + totMissEinF - lmissE)], 0)
                        lmiss  = SParts.makeLParts([(SParts.partId(SParts.alpha, 1-side), lmissE ), \
                                                    (SParts.partId(SParts.mubB, 1-side), missMubB ), \
                                                    (SParts.partId(SParts.delta, 1-side), totMissEinF - lmissE )], 0)

                        belowEF = 0
                        outBelowEF = 0
                        lowE = 0
                        while lowE < len(interMat[lowF]) and totInt - belowF - aboveF - belowEF >= constraints.minItmSuppIn():
                            aboveEF = 0
                            outAboveEF = 0
                            upE = len(interMat[lowF])-1
                            while upE >= lowE and totInt - belowF - aboveF - belowEF - aboveEF >= constraints.minItmSuppIn():
                                
                                lmissF = sum(lmissFinE[lowE:upE+1])
                                lin = SParts.makeLParts([(SParts.partId(SParts.alpha, 1-side), totInt - belowF - aboveF - belowEF - aboveEF), \
                                                         (SParts.partId(SParts.mubB, 1-side), lmissF ), \
                                                         (SParts.partId(SParts.delta, 1-side), belowF + aboveF - outAboveEF - outBelowEF)], 0)
                                tmp_comp = constraints.compAdv((lowF, upF, lowE, upE), side, True, False, lparts, lmiss, lin) 
                                if tmp_comp != None and BestsDraft.comparePair(tmp_comp, best) > 0:
                                    best = tmp_comp
                                aboveEF+=EinF[upE]
                                outAboveEF+=EoutF[upE]
                                upE-=1
                            belowEF+=EinF[lowE]
                            outBelowEF+=EoutF[lowE]
                            lowE+=1
                    aboveF+=margF[upF]
                    upF-=1
                belowF+=margF[lowF]
                lowF+=1

        if best != None:
            (nF, tF) = NumColM.makeTermBuk(False, bucketsF[1], idF, best['term'][0:2])
            (nE, tE) = NumColM.makeTermBuk(False, bucketsE[1], idE, best['term'][2:])
            if tF != None and tE != None:
                termsF.append(tF)
                termsE.append(tE)
                scores.append(BestsDraft.score(best, self.nbRows()))


#         if best != None \
#                and (best['term'][0] != 0 or best['term'][1] != len(bucketsF[1])-1) \
#                and (best['term'][2] != 0 or best['term'][3] != len(bucketsE[1])-1):            

#             if best['term'][0] == 0:
#                 lowa = float('-Inf')
#             else:
#                 lowa = bucketsF[1][best['term'][0]]
#             if best['term'][1] == len(bucketsF[1])-1 :
#                 upa = float('Inf')
#             else:
#                 upa = bucketsF[1][best['term'][1]]

#             if best['term'][2] == 0:
#                 lowb = float('-Inf')
#             else:
#                 lowb = bucketsE[1][best['term'][2]]
#             if best['term'][3] == len(bucketsE[1])-1 :
#                 upb = float('Inf')
#             else:
#                 upb = bucketsE[1][best['term'][3]]

#             termsF.append(Term(False, NumItem(idF, lowa, upa)))
#             termsE.append(Term(False, NumItem(idE, lowb, upb)))
# #            pdb.set_trace()
#             scores.append(BestsDraft.score(best, self.nbRows()))
        if flip_side:
            return (scores, termsE, termsF)
        else:
            return (scores, termsF, termsE)

    def computePairParts22Full(self, colL, idL, colR, idR, constraints, side):
        best = [ None for i in constraints.negTypesInit()]
        
        for catL in colL.cats():
            ### TODO DOABLE
            supports = SParts(self.nbRows(), [colL.suppCat(catL), set(), colL.miss(), set()])
            lparts = supports.lparts()
            lmiss = supports.lpartsInterX(colR.miss())
            
            for catR in colR.cats():
                lin = supports.lpartsInterX(colR.suppCat(catR))

                for (i, nL, nR) in constraints.negTypesInit():
                    if nL:
                        tmp_lparts = SParts.negateParts(0, lparts)
                        tmp_lmiss = SParts.negateParts(0, lmiss)
                        tmp_lin = SParts.negateParts(0, lin)
                    else:
                        tmp_lparts = lparts
                        tmp_lmiss = lmiss
                        tmp_lin = lin

                    tmp_comp = constraints.compAdv((catL, catR), 1, True, nR, tmp_lparts, tmp_lmiss, tmp_lin)
                    if tmp_comp != None and BestsDraft.comparePair(tmp_comp, best[i]) > 0:
                        best[i] = tmp_comp

        (scores, termsFix, termsExt) = ([], [], [])

        for (i, nL, nR) in constraints.negTypesInit():
            if best[i] != None:
                scores.append(BestsDraft.score(best[i], self.nbRows()))
                termsFix.append(Term(nL, CatItem(idL, best[i]['term'][0])))
                termsExt.append(Term(nR, CatItem(idR, best[i]['term'][1])))
        return (scores, termsFix, termsExt)


    def computePairParts23Full(self, colL, idL, colR, idR, constraints, side):

        if side == 0:
            (colF, idF, colE, idE) = (colR, idR, colL, idL)
        else:
            (colF, idF, colE, idE) = (colL, idL, colR, idR)
            
        best = [ None for i in constraints.negTypesInit()]
        buckets = colE.buckets()
        ### TODO DOABLE
        if True : # (colF.lenMode() >= constraints.minItmSuppOut() and colE.lenNonMode() >= constraints.minItmSuppIn()) or ( len(buckets) <= 100 ):
            partsMubB = len(colF.miss())
            missMubB = len(colF.miss() & colE.miss())
            
            missMat = [len(colF.miss() & buk) for buk in buckets[0]]
            totMiss = sum(missMat)

            marg = [len(buk) for buk in buckets[0]]
            if buckets[2] != None :
                marg[buckets[2]] += colE.lenMode()

            for cat in colF.cats():
                lparts = SParts.makeLParts([(SParts.alpha, len(colF.suppCat(cat)) ), (SParts.mubB, partsMubB ), (SParts.delta, - self.nbRows())], 1-side)
                lmiss  = SParts.makeLParts([(SParts.alpha, len(colF.suppCat(cat) & colE.miss()) ), (SParts.mubB, missMubB ), (SParts.delta, -len(colE.miss()) )], 1-side)
                
                interMat = [len(colF.suppCat(cat) & buk) for buk in buckets[0]]
                if buckets[2] != None :
                    interMat[buckets[2]] += len(colE.interMode(colF.suppCat(cat)))        

                totIn = sum(interMat) 
                below = 0
                missBelow = 0
                low = 0
                while low < len(interMat) and \
                          (totIn - below >= constraints.minItmSuppIn() or totIn - below >= constraints.minItmSuppOut()):
                    above = 0
                    missAbove = 0
                    up = len(interMat)-1
                    while up >= low and \
                          (totIn - below - above >= constraints.minItmSuppIn() or totIn - below - above >= constraints.minItmSuppOut()):
                        lin = SParts.makeLParts([(SParts.alpha, totIn - below - above), (SParts.mubB, totMiss - missBelow - missAbove ), (SParts.delta, -sum(marg[low:up+1]))], 1-side)
                        for (i, nF, nE) in constraints.negTypesInit():
                            if nF:
                                tmp_lparts = SParts.negateParts(1-side, lparts)
                                tmp_lmiss = SParts.negateParts(1-side, lmiss)
                                tmp_lin = SParts.negateParts(1-side, lin)
                            else:
                                tmp_lparts = lparts
                                tmp_lmiss = lmiss
                                tmp_lin = lin
 
                            tmp_comp = constraints.compAdv((cat, low, up), side, True, nE, tmp_lparts, tmp_lmiss, tmp_lin)
                            if tmp_comp != None and BestsDraft.comparePair(tmp_comp, best[i]) > 0:
                                best[i] = tmp_comp

                        above+=interMat[up]
                        missAbove+=missMat[up]
                        up-=1
                    below+=interMat[low]
                    missBelow+=missMat[low]
                    low+=1

        
        (scores, termsFix, termsExt) = ([], [], [])
        for (i, nF, nE) in constraints.negTypesInit():

            if best[i] != None:
                (nE, tE) = NumColM.makeTermBuk(False, buckets[1], idE, best[i]['term'][1:])
                if tE != None:
                    termsExt.append(tE)
                    termsFix.append(Term(nF, CatItem(idF, best[i]['term'][0])))
                    scores.append(BestsDraft.score(best[i], self.nbRows()))

            # if best[i] != None and ( best[i]['term'][1] != 0 or best[i]['term'][2] != len(buckets[1])-1 ):
            
#                 if best[i]['term'][1] == 0:
#                     lowb = float('-Inf')
#                 else:
#                     lowb = buckets[1][best[i]['term'][1]]
#                 if best[i]['term'][2] == len(buckets[1])-1 :
#                     upb = float('Inf')
#                 else:
#                     upb = buckets[1][best[i]['term'][2]]
#                termsFix.append(Term(nF, CatItem(idF, best[i]['term'][0])))
#                 scores.append(BestsDraft.score(best[i], self.nbRows()))

#                 termsExt.append(Term(nE, NumItem(idE, lowb, upb)))
        return (scores, termsFix, termsExt)

    def computePair(self, idL, idR, constraints):
        min_type = min(self.cols[0][idL].type_id, self.cols[1][idR].type_id)
        max_type = max(self.cols[0][idL].type_id, self.cols[1][idR].type_id)
        method_string = 'self.computePairParts%i%i' % (min_type, max_type)
        try:
            method_compute =  eval(method_string)
        except AttributeError:
              raise Exception('Oups this combination does not exist (%i %i)!'  % (min_type, max_type))
        if self.cols[0][idL].type_id == min_type:
            (scores, termsL, termsR) = method_compute(self.cols[0][idL], idL, self.cols[1][idR], idR, constraints, 1)
        else:
            (scores, termsR, termsL) =  method_compute(self.cols[0][idL], idL, self.cols[1][idR], idR, constraints, 0)
        return (scores, termsL, termsR)
        
    def initializeRedescriptions(self, nbRed, constraints, minScore=0):
        Data.logger.printL(1, 'Starting the search for initial pairs...')
        self.pairs = []
        
        ids= self.nonFull()
        cL = 0
        cR = 0  
        for idL in ids[0]:
            if cL % self.divL == 0:
                Data.logger.printL(4, 'Searching pairs %i <=> *...' %(idL))
                for idR in ids[1]:
                    if cR % self.divR == 0:
                        Data.logger.printL(10, 'Searching pairs %i <=> %i ...' %(idL, idR))
                        (scores, termsL, termsR) = self.computePair(idL, idR, constraints)                        
                        for i in range(len(scores)):
                            if scores[i] >= constraints.minPairsScore():
                                Data.logger.printL(9, 'Score:%f %s <=> %s' % (scores[i], termsL[i], termsR[i]))
                                self.methodsP['add'](scores[i], idL, idR)
                                self.pairs.append((termsL[i], termsR[i]))
                    cR += 1
            cL += 1
        self.methodsP['sort']()
        self.count = 0
        Data.logger.printL(2, 'Found %i pairs, keeping at most %i' % (len(self.pairs), nbRed))
        if nbRed > 0:
            self.nbRed = min(nbRed, len(self.pairs))
        else:
            self.nbRed = len(self.pairs)

    def setInitialMSelection(self, methodSel='overall', divL=1, divR=1):
        self.divL = divL
        self.divR = divR
        try:
            self.methodsP = {'init': eval('self.%sInitPairs' % (methodSel)), \
                             'add': eval('self.%sAddPairs' % (methodSel)), \
                            'sort': eval('self.%sSortPairs' % (methodSel)), \
                            'next': eval('self.%sNextPair' % (methodSel)) }    
        except AttributeError:
              raise Exception('Oups this selection method does not exist !')
        self.methodsP['init']()

    def overallInitPairs(self):
        self.overall = []
        
    def overallAddPairs(self, scoP, idA, idB): 
        self.overall.append((scoP, len(self.pairs)))
        
    def overallSortPairs(self):
        self.overall.sort(key=lambda x: x[0])
        
    def overallNextPair(self, nb):
        (tmp, idP) = self.overall.pop()
        Data.logger.printL(5, 'Next initial pair score %f' %(tmp))
        return self.pairs[idP]
    
    def alternateInitPairs(self):
        self.pairsSide = [{}, {}]
    
    def alternateAddPairs(self, scoP, idA, idB):
        if not self.pairsSide[0].has_key(idA):
            self.pairsSide[0][idA] = []
        if not self.pairsSide[1].has_key(idB):
            self.pairsSide[1][idB] = []
        self.pairsSide[0][idA].append((scoP, len(self.pairs)))
        self.pairsSide[1][idB].append((scoP, len(self.pairs)))
        
    def alternateSortPairs(self):
        self.colsIds = [[],[]]
        self.alternateSortPairsSide(0)
        self.alternateSortPairsSide(1)
        self.countsCols = [0,0]
    
    def alternateSortPairsSide(self, side):
        tmp = []
        for i in self.pairsSide[side].keys():
            if len(self.pairsSide[side][i]) > 0:
                self.pairsSide[side][i].sort(key=lambda x: x[0])
                tmp.append((self.pairsSide[side][i][-1], i))
        self.colsIds[side] = [i[1] for i in sorted(tmp, key=lambda x: x[0], reverse=True)]
        
    def alternateNextPair(self, nb):
        idP = self.alternateNextPairIdSide(nb%2)
        while idP != None and self.pairs[idP] == None:
            idP = self.alternateNextPairIdSide(nb%2)
        if idP == None:
            idP = self.alternateNextPairIdSide(1-(nb%2))
            while idP != None and self.pairs[idP] == None:
                idP = self.alternateNextPairIdSide(1-(nb%2))
        if idP != None :
            pair = self.pairs[idP]
            self.pairs[idP] = None
        return pair
        
    def alternateNextPairIdSide(self, side):
        if len(self.colsIds[side]) > 0:
            try:
                (tmp, idP) = self.pairsSide[side][self.colsIds[side][self.countsCols[side]]].pop()
                Data.logger.printL(5, 'Next initial pair score %f' %(tmp))
            except IndexError:
                raise Warning('Error in returning the next initial pair!')
                return None
            if len(self.pairsSide[side][self.colsIds[side][self.countsCols[side]]]) == 0:
                self.colsIds[side].pop(self.countsCols[side])
            else:
                self.countsCols[side] += 1
            if self.countsCols[side] >= len(self.colsIds[side]):
                self.countsCols[side] = 0
            return idP
        else:
            return None
    
    def getNextInitialRed(self):
        if self.count < self.nbRed :
            pair = self.methodsP['next'](self.count)
            self.count += 1
            return Redescription.fromInitialPair(pair, self)
        else:
            return None


def loadColumnNames(filename):
    f = open(filename, 'r')
    a = []
    for line in f.readlines():
        a.append(line.strip())
    return a

def getNames(filename, lenColSupps, empty):
    names = loadColumnNames(filename)
    if (len(names) ==  lenColSupps):
        if(empty):
            names.insert(0,'')
            raise Warning('First column empty ! Adding offset to names ...')
    if (len(names) !=  lenColSupps):
        names = None
        raise Warning('Number of names does not match number of variables ! Not returning names')
    return names

def readData(filenames):
    data = []; nbRowsT = None;
    for filename in filenames:
        (cols, type_ids_tmp, nbRows, nbCols) = readMatrix(filename)
        if len(cols) != nbCols:
            raise Exception('Matrix in %s does not have the expected number of variables !' % filename)

        else:
            if nbRowsT == None:
                nbRowsT = nbRows
                type_ids = type_ids_tmp
                data.append(cols)
            elif nbRowsT == nbRows:
                data.append(cols)
                type_ids.update(type_ids_tmp)
            else:
                raise Exception('All matrices do not have the same number of entities (%i ~ %i)!' % (nbRowsT, nbRows))
    return (data, type_ids, nbRows)

def readMatrix(filename):
    ## Read input
    nbRows = None
    type_ids = set()
    f = open(filename, 'r')
    try:
        type_all = filename.split('.').pop()
        nbRows = None
        nbCols = None
	
     	if len(type_all) >= 3 and (type_all[0:3] == 'dat' or type_all[0:3] == 'spa'):  
	    row = f.next()
            a = row.split()
            nbRows = int(a[0])
            nbCols = int(a[1])

	if len(type_all) >= 3 and type_all[0:3] == 'dat':
            method_parse =  eval('parseCell%s' % (type_all.capitalize()))
            method_prepare = eval('prepare%s' % (type_all.capitalize()))
            method_finish = eval('finish%s' % (type_all.capitalize()))
        else:
            method_parse =  eval('parseVar%s' % (type_all.capitalize()))
            method_prepare = eval('prepareNonDat')
            method_finish = eval('finishNonDat')
    except (AttributeError, ValueError, StopIteration):
        raise Exception('Size and type header is not right')

    tmpCols = method_prepare(nbRows, nbCols)

    Data.logger.printL(2,"Reading input data %s (%s)"% (filename, type_all))
    for row in f:
        if  len(type_all) >= 3 and type_all[0:3] == 'den' and nbRows == None:
            nbRows = len(row.split())
        method_parse(tmpCols, row.split(), nbRows, nbCols)

    if  len(type_all) >= 3 and type_all[0:3] == 'den' and nbCols == None:
        nbCols = len(tmpCols)


    Data.logger.printL(4,"Done with reading input data %s (%i x %i %s)"% (filename, nbRows, len(tmpCols), type_all))
    (cols, type_ids) = method_finish(tmpCols, nbRows, nbCols)
    return (cols, type_ids, nbRows, nbCols)
    
def prepareNonDat(nbRows, nbCols):
    return []

def parseVarMix(tmpCols, a, nbRows, nbCols):
    name = a.pop(0)
    type_row = a.pop(0)
    if type_row[0:3] == 'dat':
        raise Exception('Oups this row format is not allowed for mixed datat (%s)!' % (type_row))
    try:
        method_parse =  eval('parseVar%s' % (type_row.capitalize()))
    except AttributeError:
        raise Exception('Oups this row format does not exist (%s)!' % (type_row))
    method_parse(tmpCols, a, nbRows, nbCols)

def finishNonDat(tmpCols, nbRows, nbCols):
    type_ids = set()
    for col in tmpCols:
        type_ids.add(col.type_id)
    return (tmpCols, type_ids)

def prepareDatnum(nbRows, nbCols):
    return [[[(0, -1)], set()] for i in range(nbCols)]

def parseCellDatnum(tmpCols, a, nbRows, nbCols):
    id_row = int(a[0])-1
    id_col = int(a[1])-1
    if id_col >= nbCols or id_row >= nbRows:
        raise Exception('Outside expected columns and rows (%i,%i)' % (id_col, id_row))
    else :
        try:
            val = float(a[2])
            if val != 0:
                tmpCols[id_col][0].append((val, id_row))
        except ValueError:
            tmpCols[id_col][1].add(id_row)
            
def finishDatnum(tmpCols, nbRows, nbCols):
    return ([NumColM(sorted(tmpCols[col][0], key=lambda x: x[0]), nbRows, tmpCols[col][1]) for col in range(len(tmpCols))], set([NumColM.type_id]))
        
def prepareDatbool(nbRows, nbCols):
    return [[set(), set()] for i in range(nbCols)]

def parseCellDatbool(tmpCols, a, nbRows, nbCols):
    id_row = int(a[0])-1
    id_col = int(a[1])-1
    if id_col >= nbCols or id_row >= nbRows:
        raise Exception('Outside expected columns and rows (%i,%i)' % (id_col, id_row))
    else :
        try:
            val = float(a[2])
            if val != 0:
                tmpCols[id_col][0].add(id_row)
        except ValueError:
            tmpCols[id_col][1].add(id_row)
        
def finishDatbool(tmpCols, nbRows, nbCols):
    return ([BoolColM(tmpCols[col][0], nbRows, tmpCols[col][1]) for col in range(len(tmpCols))], set([BoolColM.type_id]))


def parseVarDensenum(tmpCols, a, nbRows, nbCols):
    if len(a) == nbRows:
        tmp = []
        miss = set()
        for i in range(len(a)):
            try:
                val = float(a[i])
                tmp.append((val,i))
            except ValueError:
                miss.add(i)
        tmp.sort(key=lambda x: x[0])
        tmpCols.append(NumColM( tmp, nbRows, miss ))
    else:
        raise Exception('Number of rows does not match (%i ~ %i)' % (nbRows,len(a)))

                        
def parseVarDensecat(tmpCols, a, nbRows, nbCols):
    if len(a) == nbRows:
        tmp = {}
        miss = set()
        for i in range(len(a)):
            try:
                cat = float(a[i])
                if tmp.has_key(cat):
                    tmp[cat].add(i)
                else:
                    tmp[cat] = set([i])
            except ValueError:
                miss.add(i) 
        tmpCols.append(CatColM(tmp, nbRows, miss))
    else:
        raise Exception('Number of rows does not match (%i ~ %i)' % (nbRows,len(a)))

def parseVarDensebool(tmpCols, a, nbRows, nbCols):
    if len(a) == nbRows:
        tmp = set()
        miss = set()
        for i in range(len(a)):
            try:
                val = float(a[i])
                if val != 0: tmp.add(i)
            except ValueError:
                miss.add(i) 
        tmpCols.append(BoolColM( tmp, nbRows , miss))
    else:
        raise Exception('Number of rows does not match (%i ~ %i)' % (nbRows,len(a)))
    
                        
def parseVarSparsebool(tmpCols, a, nbRows, nbCols):
    tmp = set()
    for i in range(len(a)):
        tmp.add(int(a[i]))
    if max(tmp) >= nbRows:
        raise Exception('Too many rows (%i ~ %i)' % (nbRows, max(tmp)))
    else:
        tmpCols.append(BoolColM( tmp, nbRows ))

