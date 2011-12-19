import math, random, re, scipy.stats
from classLog import Log
from classQuery import Op, Item, BoolItem, CatItem, NumItem, Term, Query 
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

        for op in constraints.queryTypesOp(side):
            for neg in constraints.queryTypesNP(op, side):
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

        for op in constraints.queryTypesOp(side):
            if constraints.inSuppBounds(side, op, lparts): ### DOABLE 
                res.extend(CatColM.findCoverFullSearch(op, constraints, lparts, lmiss, self.sCats, supports, side, col))
        return res

    def findCoverFullSearch(op, constraints, lparts, lmiss, scats, supports, side, col, negB=False):
        res = []
        doNegB = negB  and (True in constraints.queryTypesNP(op, 1-side))
        resNegB = [] 
        bests = [None, None]
        bestsNegB = [None, None]
        
        for (cat, supp) in scats.iteritems():
            lin = supports.lpartsInterX(supp)
            for neg in constraints.queryTypesNP(op, side):
                tmp_comp = constraints.compAdv(cat, side, op, neg, lparts, lmiss, lin)
                if BestsDraft.comparePair(tmp_comp, bests[neg]) > 0:
                    bests[neg] = tmp_comp

                if doNegB :
                    tmp_comp = constraints.compAdv(cat, side, op, neg, SParts.negateParts(1-side, lparts), SParts.negateParts(1-side, lmiss), SParts.negateParts(1-side, lin))
                    if BestsDraft.comparePair(tmp_comp, bestsNegB[neg]) > 0:
                        bestsNegB[neg] = tmp_comp

        for neg in constraints.queryTypesNP(op, side):
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
        if len(self.sVals) > 0:
            self.min = self.sVals[0][0]
            self.max = self.sVals[-1][0]
        else:
            self.min = float('-Inf')
            self.max = float('Inf')
        self.missing = nmiss
        self.mode = {}
        self.buk = None
        self.colbuk = None
        self.vals = None
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


    def collapsedBuckets(self):
        if self.colbuk == None:
            self.colbuk = self.collapseBuckets()
        return self.colbuk
    
    def collapseBuckets(self):
        tmp = self.buckets()

        agg_max= 100;
        tmp_supp=set([])
        bucket_min=tmp[1][0]
        colB_supp = []
        colB_max= []
        colB_min= []
        for i in range(len(tmp[1])):
            if len(tmp_supp) > agg_max:
                colB_supp.append(tmp_supp)
                colB_min.append(bucket_min)
                colB_max.append(tmp[1][i-1])
                bucket_min=tmp[1][i]
                tmp_supp=set([])
            tmp_supp.update(tmp[0][i])
        colB_supp.append(tmp_supp)
        colB_min.append(bucket_min)
        colB_max.append(tmp[1][-1])
#        print len(colB_min)
        return (colB_supp, colB_min, 0, colB_max)

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

    def rowsVals(self):
        if self.vals == None:
            self.vals = [x[0] for x in sorted(self.sVals, key=lambda x: x[1])]
        return self.vals


    def fit(self, constraints, supports, side, col, itemX):
        (scores, termsFix, termsExt) = ([], [], [])    
        lparts = supports.lparts()
        lmiss = supports.lpartsInterX(self.miss())
        #### BREAK
        if constraints.inSuppBounds(side, True, lparts): ### DOABLE
            segments = self.makeSegments(side, supports, constraints.queryTypesOp(side))
            res = NumColM.findCover(segments, lparts, lmiss, side, col, constraints)
 
            for cand in res:
                scores.append(BestsDraft.score(cand, self.nbRows()))
                termsFix.append(Term(False, itemX))
                termsExt.append(cand['term'])

        nlparts = SParts.negateParts(1-side, lparts)
        nlmiss = SParts.negateParts(1-side, lmiss)
 
        if (True in constraints.queryTypesNP(True, 1-side) or True in constraints.queryTypesNP(False, 1-side)) \
               and constraints.inSuppBounds(side, True, lparts): ### DOABLE
            nsegments = self.makeSegments(side, supports.negate(1-side), constraints.queryTypesOp(side))
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
            segments = self.makeSegments(side, supports, constraints.queryTypesOp(side))
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
        #pdb.set_trace()
        for op in constraints.queryTypesOp(side):
            if len(segments[op]) < NumColM.maxSeg:
                Data.logger.printL(100,'---Doing the full search---')
#                pdb.set_trace()
                res.extend(NumColM.findCoverFullSearch(op, segments, lparts, lmiss, side, col, constraints))
            else:
                Data.logger.printL(100,'---Doing the fast search---')
#                pdb.set_trace()
                if (False in constraints.queryTypesNP(op, side)):
                    res.extend(NumColM.findPositiveCover(op, segments, lparts, lmiss, side, col, constraints))
                if (True in constraints.queryTypesNP(op, side)):
                    res.extend(NumColM.findNegativeCover(op, segments, lparts, lmiss, side, col, constraints))
        return res
    findCover = staticmethod(findCover)

    def findCoverFullSearch(op, segments, lparts, lmiss, side, col, constraints):
        res = []
        map_acc = {}
        for neg in constraints.queryTypesNP(op, side):
            map_acc[neg] = []
        bests = {False: None, True: None}

        for seg_s in range(len(segments[op])):
            lin = SParts.makeLParts()

            for seg_e in range(seg_s,len(segments[op])):
                lin = SParts.addition(lin, segments[op][seg_e][2])
                for neg in constraints.queryTypesNP(op, side):
                    tmp_comp = constraints.compAdv((seg_s, seg_e), side, op, neg, lparts, lmiss, lin)
                    # if tmp_comp != None:
                    #     print (seg_s, seg_e, tmp_comp['acc'])
                    if tmp_comp != None:
                        map_acc[neg].append(tmp_comp) #['term'][0], tmp_comp['term'][1], tmp_comp['acc']))
                    if BestsDraft.comparePair(tmp_comp, bests[neg]) > 0:
                        bests[neg] = tmp_comp

        for neg in constraints.queryTypesNP(op, side):
            top_acc = {}
            seen = []
            boundsT = (segments[op][0][0], segments[op][-1][1])

            map_acc[neg].sort(key=lambda x: x['acc'])
            if len(map_acc[neg])>0:
                best_acc = map_acc[neg][-1]['acc']
            while (len(map_acc[neg])>0 ) and map_acc[neg][-1]['acc'] >= best_acc*constraints.maxBestAccRP():
                current = map_acc[neg].pop()
                # add_acc = True
                # for offset in [(0,1), (0,-1), (1,0), (-1,0), (1,1), (1,-1), (-1,-1), (-1,1), (0,2), (0,-2), (2,0), (-2,0)]:
                #     if (current['term'][0]+offset[0], current['term'][1]+offset[1]) in seen:
                #         add_acc = False
                # seen.append((current['term'][0], current['term'][1]))
                # if add_acc :

                add_acc = True
                compi = 0
                while compi < len(seen) and add_acc:
                    (black, grey, white) = Data.computeOverlap(boundsT, \
                                                          (segments[op][seen[compi][0]][0], segments[op][seen[compi][1]][1]), \
                                                          (segments[op][current['term'][0]][0], segments[op][current['term'][1]][1]))
                    if (black+grey) == 0:
                        add_acc = False
                    else:
                        add_acc = ((black/( black + grey)) <= constraints.maxOvP() )
                    # if (black/( black + grey)) <= constraints.maxOvP():
                    #     print "%f %f <> %f %f : %f" % ( segments[op][seen[compi][0]][0], segments[op][seen[compi][1]][1], \
                    #                                     segments[op][current['term'][0]][0], segments[op][current['term'][1]][1], (black/( black + grey)))
                        
                    compi+=1
                seen.append((current['term'][0], current['term'][1]))
                if add_acc :
                    (n, t) = NumColM.makeTermSeg(neg, segments[op], col, current['term'])
                    if t != None:
#                        print "%s: %f" % ( t, current['acc'])
#                        pdb.set_trace()
                        current.update({'term': t, 'neg':n })
                        res.append(current)        
            
        # for neg in constraints.queryTypesNP(op, side):
        #     if bests[neg] != None:
        #         (n, t) = NumColM.makeTermSeg(neg, segments[op], col, bests[neg]['term'])
        #         if t != None:
        #             bests[neg].update({'term': t, 'neg':n })
        #             res.append(bests[neg])
        # print res
        # exit()
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
        map_acc = []
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
                bests_b.append((constraints.compAcc(side, op, False, lparts, lmiss, lin_b), i+1, lin_b))
                lin_b = SParts.makeLParts()
            best_track_b.append(len(bests_b)-1)

        best_t = None
#        best_tb_l = []
        for b in bests_b:
            if b[1] == len(segments[op]):
                f = bests_f[0]
            else:
                f = bests_f[best_track_f[len(segments[op])-(b[1]+1)]]
            if SParts.compRatioVar(side, op, f[2]) > b[0]:
                tmp_comp_tb = constraints.compAdv((f[1], len(segments[op]) - (b[1]+1)), side, op, False, lparts, lmiss, SParts.addition(f[2], b[2]))
            else:
                tmp_comp_tb = constraints.compAdv((0, len(segments[op]) - (b[1]+1)), side, op, False, lparts, lmiss, b[2])
#            best_tb_l.append(tmp_comp_tb)
            if BestsDraft.comparePair(tmp_comp_tb, best_t) > 0:
                best_t = tmp_comp_tb
            if tmp_comp_tb != None:
                map_acc.append(tmp_comp_tb)

#        best_tf_l = []
        for f in bests_f:
            if f[1] == len(segments[op]):
                b = bests_b[0]
            else:
                b = bests_b[best_track_b[len(segments[op])-(f[1]+1)]]
            if SParts.compRatioVar(side, op, b[2]) > f[0]: 
                tmp_comp_tf = constraints.compAdv((f[1], len(segments[op]) - (b[1]+1)), side,  op, False, lparts, lmiss, SParts.addition(f[2], b[2]))
            else:
                tmp_comp_tf = constraints.compAdv((f[1], len(segments)-1), side, op, False, lparts, lmiss, f[2])
#            best_tf_l.append(tmp_comp_tf)
            if BestsDraft.comparePair(tmp_comp_tf, best_t) > 0:
                best_t = tmp_comp_tf
            if tmp_comp_tf != None:
                map_acc.append(tmp_comp_tf)

        # if best_t != None:
        #     (n, t) = NumColM.makeTermSeg(True, segments[op], col, best_t['term'])
        #     if t != None:
        #         best_t.update({'term': t, 'neg':n })
        #         res.append(best_t)

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

        boundsT = (segments[op][0][0], segments[op][-1][1])
        top_acc = {}
        seen = []
        map_acc.sort(key=lambda x: x['acc'])
        if len(map_acc)>0:
            best_acc = map_acc[-1]['acc']
        while len(map_acc)>0 and map_acc[-1]['acc'] >= best_acc*constraints.maxBestAccRP():
            current = map_acc.pop()
            # add_acc = True
            # for offset in [(0,0), (0,1), (0,-1), (1,0), (-1,0), (1,1), (1,-1), (-1,-1), (-1,1), (0,2), (0,-2), (2,0), (-2,0)]:
            #     if (current['term'][0]+offset[0], current['term'][1]+offset[1]) in seen:
            #         add_acc = False

            add_acc = True
            compi = 0
            while compi < len(seen) and add_acc:
                (black, grey, white) = Data.computeOverlap(boundsT, \
                                                      (segments[op][seen[compi][0]][0], segments[op][seen[compi][1]][1]), \
                                                      (segments[op][current['term'][0]][0], segments[op][current['term'][1]][1]))
                add_acc = ((black/( black + grey)) <= constraints.maxOvP() )
                # if (black/( black + grey)) <= constraints.maxOvP():
                #     print "%f %f <> %f %f : %f" % ( segments[op][seen[compi][0]][0], segments[op][seen[compi][1]][1], \
                #                                     segments[op][current['term'][0]][0], segments[op][current['term'][1]][1], (black/( black + grey)))
                compi+=1

            seen.append((current['term'][0], current['term'][1]))
            if add_acc :
                (n, t) = NumColM.makeTermSeg(True, segments[op], col, current['term'])
                if t != None:
#                    print "%s: %f" % ( t, current['acc'])
                    current.update({'term': t, 'neg':n })
                    res.append(current)
        return res
    findNegativeCover = staticmethod(findNegativeCover)

    def findPositiveCover(op, segments, lparts, lmiss, side, col, constraints):
        res = []
        map_acc = []

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
            if tmp_comp_f != None:
                map_acc.append(tmp_comp_f) #['term'][0], tmp_comp['term'][1], tmp_comp['acc']))


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
            if tmp_comp_b != None:
                map_acc.append(tmp_comp_b) #['term'][0], tmp_comp['term'][1], tmp_comp['acc']))

        if best_b != None and best_f != None :
            bests = [best_b, best_f]
            if best_b['term'][0] > best_f['term'][0] and best_b['term'][1] > best_f['term'][1] and best_b['term'][0] <= best_f['term'][1]:
                lin_m = SParts.makeLParts()
                for seg in segments[op][best_b['term'][0]:best_f['term'][1]+1]:
                    lin_m = SParts.addition(lin_m, seg[2])
                tmp_comp_m = constraints.compAdv((best_b['term'][0], best_f['term'][1]), side, op, False, lparts, lmiss, lin_m)
                if tmp_comp_m != None:
                    map_acc.append(tmp_comp_m)

        boundsT = (segments[op][0][0], segments[op][-1][1])
        top_acc = {}
        seen = []
        map_acc.sort(key=lambda x: x['acc'])
        if len(map_acc)>0:
            best_acc = map_acc[-1]['acc']
        while len(map_acc)>0 and map_acc[-1]['acc'] >= best_acc*constraints.maxBestAccRP():
            current = map_acc.pop()
            # add_acc = True
            # for offset in [(0,0), (0,1), (0,-1), (1,0), (-1,0), (1,1), (1,-1), (-1,-1), (-1,1), (0,2), (0,-2), (2,0), (-2,0)]:
            #     if (current['term'][0]+offset[0], current['term'][1]+offset[1]) in seen:
            #         add_acc = False

            add_acc = True
            compi = 0
            while compi < len(seen) and add_acc:
                (black, grey, white) = Data.computeOverlap(boundsT, \
                                                      (segments[op][seen[compi][0]][0], segments[op][seen[compi][1]][1]), \
                                                      (segments[op][current['term'][0]][0], segments[op][current['term'][1]][1]))
                add_acc = ((black/( black + grey)) <= constraints.maxOvP() )
                # if (black/( black + grey)) <= constraints.maxOvP():
                #     print "%f %f <> %f %f : %f" % ( segments[op][seen[compi][0]][0], segments[op][seen[compi][1]][1], \
                #                                     segments[op][current['term'][0]][0], segments[op][current['term'][1]][1], (black/( black + grey)))
                        
                compi+=1

            seen.append((current['term'][0], current['term'][1]))
            if add_acc :
                (n, t) = NumColM.makeTermSeg(False, segments[op], col, current['term'])
                if t != None:
#                    print "%s: %f" % ( t, current['acc'])
                    current.update({'term': t, 'neg':n })
                    res.append(current)
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


    def makeTermBuk(neg, buk_op, col, bound_ids, flag=0):
        if bound_ids[0] == 0 and bound_ids[1] == len(buk_op)-1:
            return (neg, None)
        elif bound_ids[0] == 0 :
            if neg:
                lowb = buk_op[bound_ids[1]+1]
                upb = float('Inf')
                n = False
            else:
                lowb = float('-Inf')
                upb = buk_op[bound_ids[1]+flag]-flag
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
            upb = buk_op[bound_ids[1]+flag]-flag
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
        self.main_ids = [None, None]
        Data.logger.printL(7, 'Left Hand side columns')
        for col in self.cols[0]:
            Data.logger.printL(7, col)
        Data.logger.printL(7, 'Right Hand side columns')
        for col in self.cols[1]:
            Data.logger.printL(7, col)

    def selectUncorr(self, side):
        ids= self.nf[side]
        max_coor = 0.9
        max_pval = 0.05
        tmp_coor = {}
        Data.logger.printL(5, 'Selecting uncorrelated %d' % side)
        for idA in range(len(ids)):
            tmp_coor[ids[idA]] = set()
            if self.cols[side][ids[idA]].type_id == 3:
                for idB in range(idA):
                    if self.cols[side][ids[idB]].type_id == 3:
                        [coor, pval] = scipy.stats.spearmanr(self.cols[side][ids[idA]].rowsVals(),self.cols[side][ids[idB]].rowsVals())
                        if coor > max_coor and pval < max_pval:
                            tmp_coor[ids[idB]].add(ids[idA])
                            tmp_coor[ids[idA]].add(ids[idB])
        lens = sorted([i for i in tmp_coor.keys()], key=lambda x: tmp_coor[x])
        main_ids = {}
        all_ids = set()
        while len(lens) > 0:
            tmp = lens.pop()
            if tmp not in all_ids:
                all_ids.add(tmp)
                main_ids[tmp] = tmp_coor[tmp] - all_ids
                all_ids.update(tmp_coor[tmp])
        Data.logger.printL(6, 'Uncorrelated variables %d: %s' % (side, main_ids))
        self.main_ids[side] = main_ids
        return main_ids

                                
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
        return [self.nonFullSide(0), self.nonFullSide(1)]

    def nonFullSide(self, side):
        if self.main_ids[side] == None:
            return set(self.nf[side])
        else:
            return set(self.main_ids[side].keys()) 

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
        flag=0
        interMat = []
        bucketsL = colL.buckets()
        bucketsR = colR.buckets()

        if len(bucketsL[0]) > len(bucketsR[0]):
            bucketsF = bucketsR; colF = colR; idF = idR; bucketsE = bucketsL; colE = colL; idE = idL; side = 1-side; flip_side = True
        else:
            bucketsF = bucketsL; colF = colL; idF = idL; bucketsE = bucketsR; colE = colR; idE = idR; flip_side = False
            
        (scores, termsF, termsE) = ([], [], [])
        ## DOABLE

        Data.logger.printL(6,"Nb buckets: %i x %i"% (len(bucketsF[1]), len(bucketsE[1])))
        if ( len(bucketsF[1]) * len(bucketsE[1]) > 5000 ): 
            if len(bucketsE[1])> 20:
                bucketsE = colE.collapsedBuckets()
                bucketsF = colF.collapsedBuckets()
                #pdb.set_trace()
                flag=1 ## in case of collapsed bucket the threshold is different
        Data.logger.printL(6,"Nb buckets: %i x %i"% (len(bucketsF[1]), len(bucketsE[1])))
        if ( len(bucketsF[1]) * len(bucketsE[1]) <= 5000 ): 

        #if (True): ## Test
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

#        pdb.set_trace()
        if best != None:
            (nF, tF) = NumColM.makeTermBuk(False, bucketsF[1], idF, best['term'][0:2])
            (nE, tE) = NumColM.makeTermBuk(False, bucketsE[1], idE, best['term'][2:],flag)
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
                (nE, tE) = NumColM.makeTermBuk(False, buckets[1], idE, best[i]['term'][1:],flag)
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
        tmpCurrGen = []
        tmpIdsSets = {}

#        (scores, termsL, termsR) = self.computePair(7, 0, constraints)                        

        ids= self.nonFull()
        for idL in ids[0]:
            Data.logger.printL(4, 'Searching pairs %i <=> *...' %(idL))
            for idR in ids[1]:
                Data.logger.printL(10, 'Searching pairs %i <=> %i ...' %(idL, idR))
                print 'Searching pairs %i <=> %i ...' %(idL, idR)
                (scores, termsL, termsR) = self.computePair(idL, idR, constraints)                        
                
                for i in range(len(scores)):
                    ind_c = len(tmpCurrGen)
                    redE = Redescription.fromInitialPair([termsL[i], termsR[i]], self)
                    if redE.pVal() < constraints.maxPVal():
                        tmpCurrGen.append((redE.queries,redE.acc())))
                        tmp = red.invStr().split(':')
                        for sList in Data.subLists(tmp):
                            i = ':'.join(sList)
                            if not tmpIdsSets.has_key(i):
                                tmpIdsSets[i] = []
                            tmpIdsSets[i].append(ind_c)
        return (tmpCurrGen, tmpIdsSets)


    def computeOverlaps(self, side):
        overlaps = []

        for (idS, neg) in self.terms[side].keys():
            if self.cols[side][idS].type_id == 3:
                intervals = []
                min_col = self.cols[side][idS].min
                max_col = self.cols[side][idS].max
                for idPair in self.terms[side][(idS, neg)]:
                    if self.pairs[idPair][side].item.lowb == float('-Inf'):
                        lowb = min_col
                    else:
                        lowb = self.pairs[idPair][side].item.lowb
                    if self.pairs[idPair][side].item.upb == float('Inf'):
                        upb = max_col
                    else:
                        upb = self.pairs[idPair][side].item.upb
                    intervals.append((lowb, upb, self.pairs[idPair][1-side].col(), idPair))
                intervals.sort(cmp=compareIntervals)
                
                len_tot = float(max_col - min_col)
                for i in range(len(intervals)):
                    for j in range(i):
                        if intervals[i][2] != intervals[j][2]:
                            ov = intervals[j][1]-intervals[i][0]
                            if ov >= 0:
                                lenj = abs(intervals[j][0]-intervals[i][0])
                                leni = abs(intervals[j][1]-intervals[i][1]) 
                                overlaps.append((1-(lenj+leni)/len_tot, idS, intervals[i], intervals[j]))
                                
        overlaps.sort(key=lambda x: x[0], reverse=True)
        return overlaps

    def computeCommons(self, side):
        commons = []
        for (idS, neg) in self.terms[side].keys():
            if self.cols[side][idS].type_id == 1:
                pairs = self.terms[side][(idS, neg)]
                for i in range(len(pairs)):
                    for j in range(i):
                        if self.pairs[pairs[i]][1-side].col() != self.pairs[pairs[j]][1-side].col():
                            commons.append((pairs[i], pairs[j]))
        return commons


    def nextGen(self, currGen, extKeys, constraints):
        constraints.incRedLength()
        tmpCurrGen = []
        tmpExtKeys = {}

        idsKeys = extKeys.keys()
        idsKeys.sort()
        cands = []
        # tot_counts = [0,0]
        for idsKey in idsKeys:
#        for idsKey in ['0-120-0:0-124-0:1-32-0']:
            print "############ %s" % idsKey
            # drop = 0
            # counts = [0,0]
            rootParts = [[],[]]
            for keyPart in idsKey.split(':'):
                if keyPart.startswith('0-'):
                    rootParts[0].append(keyPart)
                else:
                    rootParts[1].append(keyPart)
                
            ext_list = []
            for keyi in extKeys[idsKey].keys():
                sidei = int(keyi[0])
                if (keyi > rootParts[sidei][-1]):
                    # if not map_red.has_key(keyi):
                    #     raise Error('Something went wrong in the ordering of part keys (%s not in %s)!' % (keyi, map_red.keys()))
                    ext_list.append((sidei, keyi))
                # else:
                #     drop+=1

            ### This identifies part keys such that all their parents part keys are present in the previous generation
            ### Part keys encode only the variables present, not how they are combined, so the parents might end up not compatible...
            (s, k) = ([None, None], [None, None])
            for i in range(len(ext_list)):
                (s[0], k[0]) = ext_list[i]
                for j in range(i+1, len(ext_list)):
                    (s[1], k[1]) = ext_list[j]
                    pairOk = True
                    parents = set()
                    for subId in [0,1]:
                        subPos = 0
                        while subPos < len(rootParts[s[subId]]):
                            kSub = rootParts[s[subId]].pop(subPos)
                            rootParts[s[subId]].append(k[subId])
                            altRoot = ':'.join(rootParts[0]) + ':' + ':'.join(rootParts[1])
                            if not extKeys.has_key(altRoot) \
                                   or not extKeys[altRoot].has_key(k[1-subId]) \
                                   or not extKeys[altRoot].has_key(kSub):
                                pairOk = False
                            else:
                                parents.add((altRoot, k[1-subId], kSub))
                                parents.add((altRoot, kSub, k[1-subId]))
                            # kidOE=False
                            # kidSE=False
                            # rootE=False
                            # if extKeys.has_key(altRoot):
                            #     rootE=True
                            #     kidOE = k[1-subId] in extKeys[altRoot]
                            #     kidSE = kSub in extKeys[altRoot]
                            # print "## %s (%s)::\t%s (%s)\t%s (%s)" % (altRoot, rootE, k[1-subId], kidOE, kSub, kidSE)

                            rootParts[s[subId]].pop()
                            rootParts[s[subId]].insert(subPos, kSub)
                            subPos+=1
                    # counts[int(pairOk)] +=1
                    # print "\t%s %s %s\n--------------" % (k[0], k[1], pairOk)

                    if pairOk:
                        parents.add((idsKey, k[0], k[1]))
                        parents.add((idsKey, k[1], k[0]))
                        parts_list = idsKey.split(':')
                        parts_list.extend(k)
                        parts_list.sort()
                        self.kidsPair(currGen, extKeys, idsKey, parents, parts_list, constraints, tmpCurrGen, tmpExtKeys)
                        #cands.append((idsKey, k[0], k[1], map_red[k[0]], map_red[k[1]]))
            # print "\t%s %d %d/%d\n--------------" % (idsKey, drop, counts[1], counts[0])
            # for i in [0,1]:
            #     tot_counts[i] += counts[i]
            # pdb.set_trace()
        return (tmpCurrGen, tmpExtKeys)


    def kidsPair(self, currGen, extKeys, idsKey, parents, parts_list, constraints, tmpCurrGen, tmpExtKeys):
        ### Here we get a bunch of parent redescriptions to combine together or not in case they are not compatible...
        # ### Easy cases first...

        exts = {}
        for parent in parents:
            if exts.has_key(parent[2]):
                ### this is not needed
                exts[parent[2]] &= set(extKeys[parent[0]][parent[1]])
            else:
                exts[parent[2]] = set(extKeys[parent[0]][parent[1]])

        exts_list = exts.items()
        alternatives = [ [(exts_list[0][0], i)] for i in exts_list[0][1]]
        for (keyp, idst) in exts_list[1:]:                    
            ids = list(idst)
            if len(ids) == 0:
                alternatives = []
                break
            main = ids.pop()
            for i in range(len(alternatives)):
                alternatives[i].append((keyp, main))
            if len(ids) > 0:
                add_alter = []
                for second in ids:
                    for alternative in alternatives:
                        add_alter.append(list(alternative))
                        add_alter[-1][-1] = (keyp, second)
                alternatives.extend(add_alter)

        for alternative in alternatives:

            highOp = [[],[]]
            lowOp = [[],[]]
            sideExt = []
            for (ext, redI) in alternative:
                sideExt.append(int(ext.startswith('1-')))
                for side in [0,1]:
                    highOp[side].append(currGen[redI].queries[side].highOp())
                    lowOp[side].append(currGen[redI].queries[side].lowOp())

            if (1 in highOp[0] and -1 in highOp[0]) or (1 in highOp[1] and -1 in highOp[1]):
                print "### Incompatibles"
            redE = None
            sExt = set(sideExt)
            if len(sExt) == 2:
                queries = [[],[]]
                for i in range(len(sideExt)):
                    queries[1-sideExt[i]].append(currGen[alternative[i][1]].queries[1-sideExt[i]])
                redE = Redescription.fromQueriesPair([queries[0][0], queries[1][0]], self)

            else:
                side = sExt.pop()
                shOps = set(highOp[side])
                if len(shOps) == 1 and 0 in shOps:
                    slOps = set(lowOp[side])
                    if len(slOps) == 1:
                        tmp = currGen[alternative[1][1]].searchTerm(alternative[0][0])
                        if tmp != None:
                            redE = currGen[alternative[0][1]].cousin(self, tmp['side'], tmp['buk'], tmp['term'])
                    else: ### "triangle case" find the double edge type
                        if len(alternative) != 3:
                            print "OUPS the triangle does not have three sides..."
                        opNum = sum(lowOp[side])
                        i=0; j=0
                        while i < len(lowOp[side]) and lowOp[side][i] == opNum:
                            i+= 1
                        if i == 0: j=1
                        tmp = currGen[alternative[j][1]].searchTerm(alternative[i][0])
                        if tmp != None:
                            redE = currGen[alternative[i][1]].cousin(self, tmp['side'], -1, tmp['term'])
                        ### more complex combination, has to find the right fold...
                else:
                    ### There is some redescription with highOp, use as basis and find where the extension fits
                    compQ = [None]
                    compat = True
                    for i in range(len(alternative)):
                        if highOp[side][i] != 0:
                            if compQ[0] == None:
                                compQ[0] = alternative[i]
                            else:
                                compat &= (currGen[compQ[0][1]].queries[side].highOp() == currGen[alternative[i][1]].queries[side].highOp())
                                compQ.append(alternative[i])
                        else:
                            compQ.append(alternative[i])
                    compi = 1
                    compOp = currGen[compQ[0][1]].queries[side].lowOp()
                    basBuk = currGen[compQ[0][1]].queries[side].bukCols()
                    missBas = int(compQ[0][0].split('-')[1])
                    basBuk.append((-1, missBas))
                    basBuk.sort(key=lambda x: x[1])
                    while compat and compi < len(compQ):
                        compBuk = currGen[compQ[compi][1]].queries[side].bukCols(compOp)
                        compBuk.sort(key= lambda x: x[1])
                        compi+=1; ib = 0; ic = 0; cbMiss = None
                        map_buk = {}
                        while compat and ib < len(basBuk):
#                            print "(%d) %s (%d) %s, %s" % (ib, basBuk[ib], ic, compBuk[ic], map_buk)
                            if compBuk[ic][1] > basBuk[ib][1]:
                                ib+=1
                            else:
                                if basBuk[ib][0] == -1:
                                    cbMiss = compBuk[ic][0] 
                                elif not map_buk.has_key(basBuk[ib][0]):
                                    map_buk[basBuk[ib][0]] = compBuk[ic][0]
                                elif map_buk[basBuk[ib][0]] != compBuk[ic][0]:
                                    compat = False
                                ic+=1
                                ib+=1
                    if compat and cbMiss != None:
                        bbMiss = -1
                        for (b,c) in map_buk.items():
                            if c == cbMiss:
                                bbMiss = b
                        tmp = currGen[compQ[-1][1]].searchTerm(compQ[0][0])
                        if tmp != None:
                            redE = currGen[compQ[0][1]].cousin(self, tmp['side'], bbMiss, tmp['term'])
                        
            ## check for adjustments TODO
            ##############################
            # print '-----------'
            # for (keyi, i) in alternative:
            #     print '%s' % currGen[i]
            # print '==> %s' % redE
            
            if redE != None and constraints.isGoodKid(redE, [currGen[i] for (keyi, i) in alternative], None):
#                print "GOOD"
                ind_c = len(tmpCurrGen)
                tmpCurrGen.append(redE)
                for (keyi, i) in alternative:
                    keyRoot = currGen[i].invStr()
                    if not tmpExtKeys.has_key(keyRoot):
                        tmpExtKeys[keyRoot] = {}
                    if not tmpExtKeys[keyRoot].has_key(keyi):
                        tmpExtKeys[keyRoot][keyi] = []
                    tmpExtKeys[keyRoot][keyi].append(ind_c)

    def firstGen(self, currGen, idsSets, constraints):
        constraints.incRedLength()
        tmpCurrGen = []
        tmpExtKeys = {}

        if constraints.redLength() == 1:
            for (idS, idsRed) in idsSets.items():

                (side, col, neg) = Redescription.decoInvStr(idS)
                print "%s (%d)" % (idS, len(idsRed))
                idsRed.sort(key=lambda x: currGen[x].getTerm(side, 0, 0).item)
        
                for idRedA in range(min(20,len(idsRed))):
                    redA = currGen[idsRed[idRedA]]
                    idRedB = idRedA+1
                    tA = currGen[idsRed[idRedA]].getTerm(side, 0, 0)
                    dA = currGen[idsRed[idRedA]].getTerm(1-side, 0, 0)

                    while idRedB < len(idsRed) and \
                              ( tA.item.type_id == 1 or tA.item.upb > currGen[idsRed[idRedB]].getTerm(side, 0, 0).item.lowb ):
                        if dA.col() == currGen[idsRed[idRedB]].getTerm(1-side, 0, 0).col() :
                            idRedB+=1
                            continue

                        tB = currGen[idsRed[idRedB]].getTerm(side, 0, 0)
                        dB = currGen[idsRed[idRedB]].getTerm(1-side, 0, 0)
                
                        match = True
                        adjust = []

                ## In case join on real-valued, check interval compatible
                        if tA.item.type_id == 3 and tA!= tB:
                            boundsT = [self.cols[side][tA.col()].min, self.cols[side][tA.col()].max]
                            boundsA = [tA.item.lowb, tA.item.upb]
                            boundsB = [tB.item.lowb, tB.item.upb]
                            (black, grey, white) = Data.computeOverlap(boundsT, boundsA, boundsB)
                            match = ( (black + grey) > 0  and black / (black + grey) > 0.5 )
                            if match:
                                adjust.append({'side': side, 'buk': 0, 'pos': 0, 'terms': [tA, tB]})

                        if match:
                            redB = currGen[idsRed[idRedB]]
                            for op in constraints.queryTypesOp(1-side):
                                for i in range(len(adjust)):
                                    adjust[i]['op'] = op
                                redE = redA.cousin(self, 1-side, op, dB, adjust)

                                if constraints.isGoodKid(redE, [redA, redB], op):
                                    ind_c = len(tmpCurrGen)
                                    tmpCurrGen.append((redE.queries,redE.acc()))
                                    for (keyRoot, t) in [(redA.invStr(), dB), (redB.invStr(), dA)]:
                                        keyExt = Redescription.encoInvStr(1-side, t.col(), t.isNeg()==1)
                                        if not tmpExtKeys.has_key(keyRoot):
                                            tmpExtKeys[keyRoot] = {}
                                        if not tmpExtKeys[keyRoot].has_key(keyExt):
                                            tmpExtKeys[keyRoot][keyExt] = []
                                        tmpExtKeys[keyRoot][keyExt].append(ind_c)
                        idRedB+=1
            return (tmpCurrGen, tmpExtKeys)
            
    def computeOverlap(boundsT, boundsA, boundsB):
        if boundsA[0] == float('-Inf'):
            boundsA[0] = boundsT[0]
        if boundsB[0] == float('-Inf'):
            boundsB[0] = boundsT[0]
        if boundsA[1] == float('Inf'):
            boundsA[1] = boundsT[1]
        if boundsB[1] == float('Inf'):
            boundsB[1] = boundsT[1]

        if boundsA[0] < boundsB[0]:
            boundsF = boundsA
            boundsS = boundsB
        else:
            boundsF = boundsB
            boundsS = boundsA

        if boundsF[1] > boundsS[0]:
            black = (min(boundsF[1], boundsS[1]) - boundsS[0])
            white = (boundsF[0] - boundsT[0]) \
                  + (boundsT[1] - max(boundsF[1], boundsS[1]))
            grey = boundsT[1] - boundsT[0] - white - black
        else:
            black = 0
            grey = boundsF[1] - boundsF[0] + boundsS[1] - boundsS[0]
            white = boundsT[1] - boundsT[0] - grey
        return (black, grey, white)
    computeOverlap = staticmethod(computeOverlap)

    def subLists(listO):
        subL = []
        for i in range(len(listO)):
            tmp = list(listO)
            tmp.pop(i)
            subL.append(tmp)
        return subL
    subLists = staticmethod(subLists)
                
def compareIntervals(x,y):
    if (x[0] < y[0]):
        return -1
    elif (x[0] > y[0]):
        return 1
    else:
        if (x[1] < y[1]):
            return -1
        elif (x[1] > y[1]):
            return 1
        else:
            return 0

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
	
     	if len(type_all) >= 3 and (type_all[0:3] == 'mix' or type_all[0:3] == 'dat' or type_all[0:3] == 'spa'):  
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

