import math, random, re, utilsIO
from classLog import Log
from classQuery import Op, Item, BoolItem, CatItem, NumItem, Term, Query 
from classRedescription import Redescription
from classBestsDraft import BestsDraft
import pdb

class DataM:
    type_id = 0
    
    def __init__(self, ncolSupps=[], nmaxRowId=-1):
        self.colSupps = ncolSupps
        self.nbRows = nmaxRowId+1

    def __len__(self):
        return self.nbRows

    def nbCols(self):
        return len(self.colSupps)
        
    def supp(self, term): ## the term should be the same type as the data on the considered side
        if term.isNeg():
            return set(range(self.nbRows)) - self.suppItem(term.item)
        else:
            return self.suppItem(term.item)

    def nonFull(self, minIn, minOut):
        return [col for col in range(self.nbCols())]

class BoolDataM(DataM):
    type_id = 1

    def suppItem(self, item):
        return set(self.colSupps[item.colId()])

    def __str__(self):
        return "%i x %i boolean" % ( len(self), self.nbCols())

    def vect(self, col): ## the term should be the same type as the data on the considered side
        return self.colSupps[col]

    def nonFull(self, minIn, minOut):
        it = []
        for col in range(len(self.colSupps)):
            if len(self.colSupps[col]) >= minIn and self.nbRows -len(self.colSupps[col]) >= minOut :
                it.append(col)
        return it 

    def anyAdvanceCol(self, toImprov, side, col):
        toColors = {True:[0,0], False:[0,0]}
        res = []
        if side == 1:
            (lparts) = (len(toImprov.parts[1]), len(toImprov.parts[0]), len(toImprov.parts[2]), len(toImprov.parts[3]))
            (toColors[False][0], toColors[True][1], toColors[False][1], toColors[True][0]) = \
                                 (len(toImprov.parts[1] & self.colSupps[col]), len(toImprov.parts[0] & self.colSupps[col]), len(toImprov.parts[2] & self.colSupps[col]), len(toImprov.parts[3] & self.colSupps[col]))
        
        else:
            (lparts) = (len(toImprov.parts[0]), len(toImprov.parts[1]), len(toImprov.parts[2]), len(toImprov.parts[3]))
            (toColors[False][0], toColors[True][1], toColors[False][1], toColors[True][0]) = \
                                 (len(toImprov.parts[0] & self.colSupps[col]), len(toImprov.parts[1] & self.colSupps[col]), len(toImprov.parts[2] & self.colSupps[col]), len(toImprov.parts[3] & self.colSupps[col]))

        for op in toImprov.queryTypesOp():
            for neg in toImprov.queryTypesNP(op):
                b = toImprov.compAdv(Term(neg, BoolItem(col)), op, neg, toColors[op], lparts)
                if b != None:
                    b.update({'side': side, 'op': Op(op)})
                    res.append(b)
        return res
    
class CatDataM(DataM):
    type_id = 2

    def __init__(self, ncolSupps=[], nmaxRowId=-1):
        self.colSupps = ncolSupps
        self.nbRows = nmaxRowId+1
        self.cards = []
        for i in range(len(self.colSupps)):
            tmp = {}
            for cat in self.colSupps[i].keys():
                c = len(self.colSupps[i][cat])
                if tmp.has_key(c):
                    tmp[c].add(cat)
                else:
                    tmp[c] = set([cat])
            self.cards.append(tmp)
            
            
    def suppItem(self, item):
        if item.cat in self.colSupps[item.col].keys():
            return self.colSupps[item.col][item.cat]
        else:
            return set()

    def __str__(self):
        return "%i x %i categorical" % ( len(self), self.nbCols())

#    def vect(self, col): ## the term should be the same type as the data on the considered side
#        return self.colSupps[col]

    def nonFull(self, minIn, minOut):
        it = []
        for col in range(len(self.colSupps)):
            if max(self.cards[col].keys()) >= minIn and self.nbRows - min(self.cards[col].keys()) >= minOut :
                it.append(col)
        return it 

    def fit(self, itemX, suppX, suppXb, col, toImprov, side):
        (scores, termsA, termsB) = ([], [], [])    
        #if side == 0:
        parts = (set(), suppX, set(), suppXb)
        #else:
        #    parts = (suppX, set(), set(), suppXb)
        (cand_A, cand_Ab) = CatDataM.findCover(self.colSupps[col], parts, side, col, toImprov, True )

        for cand in cand_A:
            cand.update({'supp': len(suppX)})
            scores.append(toImprov.score(cand))
            termsA.append(Term(False, itemX))
            termsB.append(cand['term'])

        for cand in cand_Ab:
            cand.update({'supp': len(suppXb)})
            scores.append(toImprov.score(cand))
            termsA.append(Term(True, itemX))
            termsB.append(cand['term'])
        return (scores, termsA, termsB)

    def anyAdvanceCol(self, toImprov, side, col):
        return CatDataM.findCover(self.colSupps[col], (toImprov.parts[side], toImprov.parts[1-side], toImprov.parts[2], toImprov.parts[3]), side, col, toImprov, False )

    def findCover(catsSupp, parts, side, col, toImprov, negB):
        res = []
        doNegB = negB  and toImprov.queryTypesHasNeg()
        resNegB = []
        lparts = (len(parts[0]), len(parts[1]), len(parts[2]), len(parts[3]))
        colop_ids = ((0,2),(3,1))
        for op in toImprov.queryTypesOp():
            if lparts[colop_ids[op][0]] + lparts[colop_ids[op][1]] >= toImprov.minItmC():
                bests = {False: None, True: None}
                if doNegB :
                    bestsNegB = {False: None, True: None}
                
                for cat in catsSupp.keys(): ### TODO: check cardinalities
                    toColors = (len(catsSupp[cat] & parts[colop_ids[op][0]]),\
                                len(catsSupp[cat] & parts[colop_ids[op][1]])) 

                    for neg in toImprov.queryTypesNP(op):
                        tmp_comp = toImprov.compAdv(cat, op, neg, toColors, lparts)
                        if BestsDraft.comparePair(tmp_comp, bests[neg]) > 0:
                            bests[neg] = tmp_comp
                        if doNegB :
                            tmp_comp = toImprov.compAdv(cat, op, neg, [toColors[1],toColors[0]] , (lparts[2], lparts[3], lparts[0], lparts[1]))
                            if BestsDraft.comparePair(tmp_comp, bestsNegB[neg]) > 0:
                                bestsNegB[neg] = tmp_comp
                        
        
                for neg in toImprov.queryTypesNP(op):
                    if bests[neg] != None  :
                        t = bests[neg]['term']
                        bests[neg].update({'side': side, 'op': Op(op), 'term': Term(neg, CatItem(col, t))})
                        res.append(bests[neg])
                    if doNegB and bestsNegB[neg] != None  :
                        t = bestsNegB[neg]['term']
                        bestsNegB[neg].update({'side': side, 'op': Op(op), 'term': Term(neg, CatItem(col, t))})
                        resNegB.append(bestsNegB[neg])
        if negB:
            return (res, resNegB)
        else:
            return res
    findCover = staticmethod(findCover)
    
class NumDataM(DataM):
    type_id = 3
    maxSeg = 100

    ## Using suitable reading method returns suitable colSupps :)
#     def __init__(self, ncolSupps=[], nmaxRowId=-1):
#         ## self.colSupps[col] = [list of (value, ids] ordered by value
#         self.colSupps = [ sorted( [(ncolSupps[col][i],i) for i in range(len(ncolSupps[col]))], key=lambda x: x[0])  for col in range(len(ncolSupps))]
#         #self.colSupps = [ zip(*sorted( [(ncolSupps[col][i],i) for i in range(len(ncolSupps[col]))], key=lambda x: x[0]) for col in range(len(ncolSupps)))]
#         self.nbRows = nmaxRowId+1

    def __init__(self, ncolSupps=[], nmaxRowId=-1):
        self.colSupps = ncolSupps
        self.nbRows = nmaxRowId+1
        self.modeSupps = {}
        for i in range(len(self.colSupps)):
            if len(self.colSupps[i]) != self.nbRows:
                tmp = set([r[1] for r in self.colSupps[i] ])
                if -1 in tmp:
                    tmp.remove(-1)
                if 2*len(tmp) > self.nbRows:
                    self.modeSupps[i] = (-1, set(range(self.nbRows)) - tmp)
                else:
                    self.modeSupps[i] = (1, tmp)
            else:
                self.modeSupps[i] = (0, None)

    
    def interNonMode(self, col, suppX):
        if self.modeSupps[col][0] == -1:
            return suppX - self.modeSupps[col][1]
        elif self.modeSupps[col][0] == 1:
            return suppX & self.modeSupps[col][1]
        else:
            return suppX   
    
    def interMode(self, col, suppX):
        if self.modeSupps[col][0] == 1:
            return suppX - self.modeSupps[col][1]
        elif self.modeSupps[col][0] == -1:
            return suppX & self.modeSupps[col][1]
        else:
            return set()    
        
    def lenNonMode(self, col):
        if self.modeSupps[col][0] == -1:
            return self.nbRows - len(self.modeSupps[col][1])
        elif self.modeSupps[col][0] == 1:
            return len(self.modeSupps[col][1])
        else:
            return self.nbRows
        
    def lenMode(self, col):
        if self.modeSupps[col][0] == 1:
            return self.nbRows - len(self.modeSupps[col][1])
        elif self.modeSupps[col][0] == -1:
            return len(self.modeSupps[col][1])
        else:
            return 0
        
    def nonModeSupp(self, col):
        if self.modeSupps[col][0] == -1:
            return set(range(self.nbRows)) - self.modeSupps[col][1]
        elif self.modeSupps[col][0] == 1:
            return self.modeSupps[col][1]
        else:
            return set(range(self.nbRows))

    def modeSupp(self, col):
        if self.modeSupps[col][0] == 1:
            return set(range(self.nbRows)) - self.modeSupps[col][1]
        elif self.modeSupps[col][0] == -1:
            return self.modeSupps[col][1]
        else:
            return set()

    def nonFull(self, minIn, minOut):
        it = []
        for col in range(len(self.colSupps)):
            if self.lenNonMode(col) >= minOut or self.lenNonMode(col) >= minIn :
                it.append(col)
        return it


    def makeBuckets(self, col):
        if self.colSupps[col][0][1] != -1 :
            bucketsSupp = [set(self.colSupps[col][0][1])]
        else:
            bucketsSupp = [set()]
        bucketsVal = [self.colSupps[col][0][0]]
        bukMode = None
        for (val , row) in self.colSupps[col]:
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
        ## DO NOT USE INDEX IF THE BOUND ARE NOT ONE OF THE VALUES
        supp = set()
        for (val , row) in self.colSupps[item.colId()]:
            if val > item.upb :
                return supp
            elif val >= item.lowb:
                if row == -1:
                    supp.update(self.modeSupp(item.colId()))
                else:
                    supp.add(row)
        return supp

    def vect(self, col): ## the term should be the same type as the data on the considered side
        return self.nonModeSupp(col)
    
    def __str__(self):
        return "%i x %i numerical" % ( len(self), self.nbCols())

    def fit(self, itemX, suppX, vector_abcd, col, toImprov, side):
        (scores, termsA, termsB) = ([], [], [])    

        if side == 0:
            lparts = (0, len(suppX), 0, len(self) - len(suppX))
            lpartsN = (lparts[2], lparts[3], lparts[0], lparts[1])
            lenIntX = len(self.interMode(col, suppX))
            linPartsMode = (0, lenIntX, 0, self.lenMode(col) - lenIntX)
        else:
            lparts = (len(suppX), 0, 0, len(self) - len(suppX))
            lpartsN = (lparts[3], lparts[2], lparts[1], lparts[0])
            lenIntX = len(self.interMode(col, suppX))
            linPartsMode = (lenIntX, 0, 0, self.lenMode(col) - lenIntX)
        segments = None

        #### BREAK
        if lparts[3] >= toImprov.minItmSuppOut() and (lparts[1-side] - linPartsMode[1-side]) >= toImprov.minItmSuppIn() :
            segments = NumDataM.makeSegments(vector_abcd, side, self.colSupps[col], linPartsMode)
            cand_A = NumDataM.findCover(segments, lparts, side, col, toImprov)

            for cand in cand_A:
                cand.update({'supp': len(suppX)})
                scores.append(toImprov.score(cand))
                termsA.append(Term(False, itemX))
                termsB.append(cand['term'])

        if toImprov.queryTypesHasNeg() and lparts[1-side] >= toImprov.minItmSuppOut() and (lparts[3] - linPartsMode[3]) >= toImprov.minItmSuppIn() :
            if segments == None:
                segments = NumDataM.makeSegments(vector_abcd, side, self.colSupps[col], linPartsMode)
            segments = NumDataM.negateSegments(segments, False, True)
            cand_Ab = NumDataM.findCover(segments, lpartsN, side, col, toImprov)

            for cand in cand_Ab:            
                cand.update({'supp': len(self) - len(suppX)})
                scores.append(toImprov.score(cand))
                termsA.append(Term(True, itemX))
                termsB.append(cand['term'])

        return (scores, termsA, termsB)

    def anyAdvanceCol(self, toImprov, side, col):
        res = []
#         if ( len(self.interNonMode(col,toImprov.parts[2])) >= toImprov.minItmSuppIn() \
#              or len(self.interNonMode(col,toImprov.parts[1-side])) >= toImprov.minItmC() ):

#             if (( len(toImprov.parts[2])- len(self.interMode(col, toImprov.parts[2]))) + \
#                 (len(toImprov.parts[1-side]) - len(self.interMode(col, toImprov.parts[1-side])))) < toImprov.minItmSuppIn() :
#                 pdb.set_trace()

#             linPartsMode = (len(self.interMode(col, toImprov.parts[0])), \
#                             len(self.interMode(col, toImprov.parts[1])), \
#                             len(self.interMode(col, toImprov.parts[2])), \
#                             len(self.interMode(col, toImprov.parts[3])))
            
#             if side==1:
#                 lparts = (len(toImprov.parts[1]), len(toImprov.parts[0]), len(toImprov.parts[2]), len(toImprov.parts[3]))
#             else:
#                 lparts = (len(toImprov.parts[0]), len(toImprov.parts[1]), len(toImprov.parts[2]), len(toImprov.parts[3]))

        linPartsMode = (len(self.interMode(col, toImprov.parts[0])), \
                        len(self.interMode(col, toImprov.parts[1])), \
                        len(self.interMode(col, toImprov.parts[2])), \
                        len(self.interMode(col, toImprov.parts[3])))
        lparts = (len(toImprov.parts[0]), len(toImprov.parts[1]), len(toImprov.parts[2]), len(toImprov.parts[3]))


        if lparts[2] - linPartsMode[2] >= toImprov.minItmSuppIn() or lparts[1-side] - linPartsMode[1-side] >= toImprov.minItmC(): 
            segments = NumDataM.makeSegments(toImprov.parts[4], side, self.colSupps[col], linPartsMode)
            res = NumDataM.findCover(segments, (lparts[side], lparts[1-side], lparts[2], lparts[3]), side, col, toImprov)
        return res
    
    def makeSegments(vector_abcd, side, vectCol, linPartsMode):
        ## vector_abcd alpha->0 gamma->1 delta->2 beta->3
        segments = [[],[]]
        if side==0:
            toColorsMode = [[linPartsMode[0], linPartsMode[2]], [linPartsMode[3], linPartsMode[1]]]
            OR = [Data.sym_delta, Data.sym_beta]
            BLUE = [Data.sym_gamma, Data.sym_beta]
        else:
            toColorsMode = [[linPartsMode[1], linPartsMode[2]], [linPartsMode[3], linPartsMode[0]]]
            OR = [Data.sym_delta, Data.sym_alpha]
            BLUE = [Data.sym_gamma, Data.sym_alpha]

        ## segment: [count_red, count_blue, start_val, end_val]
        current_segments = [[0,0, None, None],[0,0, None, None]] # [AND [RED, BLUE] , OR [RED, BLUE]]
        
        ## buff: [count_red_current_val, count_blue_current_val, highest_val]
        buff_count = [[0,0, None],[0,0, None]]
        for (val, row) in vectCol:
            if row == -1:
                
                for op in [False, True]:
                    if toColorsMode[op][0]+toColorsMode[op][1] > 0:
                        if current_segments[op][0]*current_segments[op][1] > 0: ## if current segment is non empty (not two successive mixing), save
                            segments[op].append(current_segments[op])

                        buff_count[op].append(buff_count[op][-1]) ## transform the buff in segment by setting end_val == start_val <- highest_val
                        segments[op].append(buff_count[op])
                        buff_count[op] = [toColorsMode[op][0], toColorsMode[op][1], val]
                        current_segments[op] = [0, 0, val, val]
                        
            else :
                op = vector_abcd[row] in OR
                color = vector_abcd[row] in BLUE

                if val == buff_count[op][-1]:
                    buff_count[op][color] += 1

                ## first loop will go throught this conditional and append the initial segment to the list, removed at the end
                elif buff_count[op][color] == 0:  ## AND val > current_segments[op][-1]
                    ## Other color encontered, no mixing: push counts, save and start new 
                    current_segments[op][buff_count[op][1]>0] += buff_count[op][buff_count[op][1]>0]  # push counts from buffer
                    current_segments[op][-1] = buff_count[op][-1]                                     # push upper bound from buffer 
                    segments[op].append(current_segments[op])                                         # append to segments
                    buff_count[op] = [1*(not color), 1*color, val]                                    # create new segment
                    current_segments[op] = [0, 0, val, val]                                           # re-initialize buffer

                elif buff_count[op][not color] == 0 : ## AND val > current_segments[op][-1]
                    ## Same color, push counts
                    current_segments[op][color] += buff_count[op][color]
                    current_segments[op][-1] = buff_count[op][-1]
                    buff_count[op][color] = 1
                    buff_count[op][-1] = val

                else: ## buff_count[op][0]*buff_count[op][1] > 0:  ## AND val > current_segments[op][-1]
                    ## Mixing in the previous value: save current segment and previous value separately and start new
                    if current_segments[op][0]+current_segments[op][1] > 0: ## if current segment is non empty (not two successive mixing), save
                        segments[op].append(current_segments[op])

                    buff_count[op].append(buff_count[op][-1]) ## transform the buff in segment by setting end_val == start_val <- highest_val
                    segments[op].append(buff_count[op])
                    buff_count[op] = [1*(not color), 1*color, val]
                    current_segments[op] = [0, 0, val, val]

        for op in [False, True]:
            if buff_count[op][0]*buff_count[op][1] > 0:
                ## Mixing in the last value: save current segment and last value separately
                if current_segments[op][0]+current_segments[op][1] > 0: ## if current segment is non empty (not two successive mixing), save
                    segments[op].append(current_segments[op])
                    
                buff_count[op].append(buff_count[op][-1]) ## transform the buff in segment by setting end_val == start_val <- highest_val
                segments[op].append(buff_count[op])                
            else:
                ## no mixing: push counts and save
                current_segments[op][buff_count[op][1]>0] += buff_count[op][buff_count[op][1]>0] # push counts from buffer
                current_segments[op][-1] = buff_count[op][-1]                                    # push upper bound from buffer
                segments[op].append(current_segments[op])                                        # append to segments
                
            ## pop the first segment: it is empty
            segments[op].pop(0)

        #print 'nb_seg: %ix%i' % (len(segments[0]), len(segments[1]))
        return segments
    makeSegments = staticmethod(makeSegments)
            
    def negateSegments(segments, negateL, negateR):
        if negateL:
            segments = [segments[1], segments[0]]
        if negateR:
            for op in [0,1]:
                for seg in range(len(segments[op])):
                    segments[op][seg]=(segments[op][seg][1], segments[op][seg][0], segments[op][seg][2], segments[op][seg][3])
        return segments

    negateSegments = staticmethod(negateSegments)

    def findCover(segments, lparts, side, col, toImprov):
        res = []
        for op in toImprov.queryTypesOp():
            if len(segments[op]) < NumDataM.maxSeg:
                Data.logger.printL(100,'---Doing the full search---')
#                pdb.set_trace()
                res.extend(NumDataM.findCoverFullSearch(op, segments, lparts, side, col, toImprov))
            else:
                Data.logger.printL(100,'---Doing the fast search---')
#                pdb.set_trace()
                if toImprov.queryTypesHasPos(op):
                    res.extend(NumDataM.findPositiveCover(op, segments, lparts, side, col, toImprov))
                if toImprov.queryTypesHasNeg(op):
                    res.extend(NumDataM.findNegativeCover(op, segments, lparts, side, col, toImprov))
        return res
    findCover = staticmethod(findCover)


    def findCoverFullSearch(op, segments, lparts, side, col, toImprov):
        res = []
        bests = {False: None, True: None}

        for seg_s in range(len(segments[op])):
            toColors = [0,0]
            for seg_e in range(seg_s,len(segments[op])):
                toColors[0] += segments[op][seg_e][0]
                toColors[1] += segments[op][seg_e][1]
                for neg in toImprov.queryTypesNP(op):
                    if (seg_s, seg_e) == (0,16):
                        pdb.set_trace()
                    tmp_comp = toImprov.compAdv((seg_s, seg_e), op, neg, toColors, lparts)
                    if tmp_comp != None:
                        print (seg_s, seg_e, tmp_comp['acc'])
                    if BestsDraft.comparePair(tmp_comp, bests[neg]) > 0:
                        bests[neg] = tmp_comp

        for neg in toImprov.queryTypesNP(op):
            if bests[neg] != None and (bests[neg]['term'][0] != 0 or  bests[neg]['term'][1] != len(segments[op])-1)  :
                if bests[neg]['term'][0] == 0:
                    lowb = float('-Inf')
                else:
                    lowb = segments[op][bests[neg]['term'][0]][-2]
                if bests[neg]['term'][1] == len(segments[op])-1 :
                    upb = float('Inf')
                else:
                    upb = segments[op][bests[neg]['term'][1]][-1]
                bests[neg].update({'side': side, 'op': Op(op), 'term': Term(neg, NumItem(col, lowb, upb))})
                res.append(bests[neg])
        print res
        exit()
        return res
    findCoverFullSearch = staticmethod(findCoverFullSearch)

    def findNegativeCover(op, segments, lparts, side, col, toImprov):
        res = []
        #print 'INCR SEARCH:'
        toColors_buff_f = [0,0]
        bests_f = [(toImprov.compAcc(op, False, [0,0], lparts), 0, (0,0))] 
        best_track_f = [0]
        toColors_buff_b = [0,0]
        bests_b = [(toImprov.compAcc(op, False, [0,0], lparts), 0, (0,0))] 
        best_track_b = [0]

        for  i in range(len(segments[op])):
            # FORWARD
            toColors_buff_f = [toColors_buff_f[0] + segments[op][i][0], toColors_buff_f[1] + segments[op][i][1]]
            if  toColors_buff_f[0] == 0 or toColors_buff_f[1]/toColors_buff_f[0] > bests_f[-1][0]:
                toColors_buff_f[0] += bests_f[-1][-1][0]
                toColors_buff_f[1] += bests_f[-1][-1][1]
                bests_f.append((toImprov.compAcc(op, False, toColors_buff_f, lparts), i+1, toColors_buff_f))
                toColors_buff_f = [0,0]
            best_track_f.append(len(bests_f)-1)

            # FORWARD
            toColors_buff_b = [toColors_buff_b[0] + segments[op][-(i+1)][0], toColors_buff_b[1] + segments[op][-(i+1)][1]]
            if  toColors_buff_b[0] == 0 or toColors_buff_b[1]/toColors_buff_b[0] > bests_b[-1][0]:
                toColors_buff_b[0] += bests_b[-1][-1][0]
                toColors_buff_b[1] += bests_b[-1][-1][1]
                bests_b.append((toImprov.compAcc(op, False, toColors_buff_b, lparts), i+1, toColors_buff_b))
                toColors_buff_b = [0,0]
            best_track_b.append(len(bests_b)-1)

        best_t = None
        best_tb_l = []
        for b in bests_b:
            if b[1] == len(segments[op]):
                f = bests_f[0]
            else:
                f = bests_f[best_track_f[len(segments[op])-(b[1]+1)]]
            if f[-1][0] == 0 or float(f[-1][1])/f[-1][0] > b[0]:
                tmp_comp_tb = toImprov.compAdv((f[1], len(segments[op]) - (b[1]+1)), op, False, [f[-1][0]+b[-1][0],f[-1][1]+b[-1][1]], lparts)
            else:
                tmp_comp_tb = toImprov.compAdv((0, len(segments[op]) - (b[1]+1)), op, False, b[-1], lparts)
            best_tb_l.append(tmp_comp_tb)
            if BestsDraft.comparePair(tmp_comp_tb, best_t) > 0:
                best_t = tmp_comp_tb

        best_tf_l = []
        for f in bests_f:
            if f[1] == len(segments[op]):
                b = bests_b[0]
            else:
                b = bests_b[best_track_b[len(segments[op])-(f[1]+1)]]
            if b[-1][0] == 0 or float(b[-1][1])/b[-1][0] > f[0]:
                tmp_comp_tf = toImprov.compAdv((f[1], len(segments[op]) - (b[1]+1)), op, False, [f[-1][0]+b[-1][0],f[-1][1]+b[-1][1]], lparts)
            else:
                tmp_comp_tf = toImprov.compAdv((f[1], len(segments)-1), op, False, f[-1], lparts)
            best_tf_l.append(tmp_comp_tf)
            if BestsDraft.comparePair(tmp_comp_tf, best_t) > 0:
                best_t = tmp_comp_tf

        if best_t != None and best_t['term'][0] <= best_t['term'][1] and ((best_t['term'][0] != 0) or (best_t['term'][1] != len(segments[op])-1)) :
            #print '%i <-> %i: %i/%i=%f %s' \
            #        % (best_t['term'][0], best_t['term'][1], best_t['toBlue'], best_t['toRed'], best_t['acc'], lparts)
            if best_t['term'][0] == 0:
                lowb = float('-Inf')
            else:
                lowb = segments[op][best_t['term'][0]][-2]
            if best_t['term'][1] == len(segments[op])-1 :
                upb = float('Inf')
            else:
                upb = segments[op][best_t['term'][1]][-1]
            best_t.update({'side': side, 'op': Op(op), 'term': Term(True, NumItem(col, lowb, upb))})
            res.append(best_t)

        return res
    findNegativeCover = staticmethod(findNegativeCover)

    def findPositiveCover(op, segments, lparts, side, col, toImprov):
        res = []
        #print 'INCR SEARCH:'
        toColors_f = [0,0]
        nb_seg_f = 0
        best_f = None
        toColors_b = [0,0]
        nb_seg_b = 0
        best_b = None 

        for  i in range(len(segments[op])-1):
            # FORWARD
            if i > 0 and (toColors_f[0] == 0 \
                          or toImprov.compAcc(op, False, segments[op][i][:2], lparts) <  float(toColors_f[1])/float(toColors_f[0])):
                toColors_f = [toColors_f[0] + segments[op][i][0], toColors_f[1] + segments[op][i][1]]
                nb_seg_f += 1
            else: 
                toColors_f = segments[op][i][:2]
                nb_seg_f = 0
            tmp_comp_f = toImprov.compAdv((i - nb_seg_f, i), op, False, toColors_f, lparts)
            if BestsDraft.comparePair(tmp_comp_f, best_f) > 0 :
                best_f = tmp_comp_f

            # BACKWARD
            if i > 0 and (toColors_b[0] == 0 \
                          or toImprov.compAcc(op, False, segments[op][-(i+1)][:2], lparts) <  float(toColors_b[1])/float(toColors_b[0]) ):
                toColors_b = [toColors_b[0] + segments[op][-(i+1)][0], toColors_b[1] + segments[op][-(i+1)][1]]
                nb_seg_b += 1
            else:
                toColors_b = segments[op][-(i+1)][:2]
                nb_seg_b = 0
            tmp_comp_b = toImprov.compAdv((len(segments[op])-(1+i), len(segments[op])-(1+i) + nb_seg_b), op, False, toColors_b, lparts)
            if BestsDraft.comparePair(tmp_comp_b, best_b) > 0 :
                best_b = tmp_comp_b


        if best_b != None and best_f != None :
            bests = [best_b, best_f]

            if best_b['term'][0] > best_f['term'][0] and best_b['term'][1] > best_f['term'][1] and best_b['term'][0] <= best_f['term'][1]:
                toColors_m = [0,0]
                for seg in segments[op][best_b['term'][0]:best_f['term'][1]+1]:
                    toColors_m = [toColors_m[0] + seg[0], toColors_m[1] + seg[1]]

                tmp_comp_m = toImprov.compAdv((best_b['term'][0], best_f['term'][1]), op, False, toColors_m, lparts)
                if tmp_comp_m != None:
                    bests.append(tmp_comp_m)

            best = sorted(bests, cmp=BestsDraft.comparePair)[-1]

        elif best_f == None:
            best = best_f
        else:
            best = best_b

        if best != None and (best['term'][0] != 0 or  best['term'][1] != len(segments[op])-1)  :
            #print '%i <-> %i: %i/%i=%f' \
            #        % (best['term'][0], best['term'][1], best['toBlue'], best['toRed'], best['acc'])
            if best['term'][0] == 0:
                lowb = float('-Inf')
            else:
                lowb = segments[op][best['term'][0]][-2]
            if best['term'][1] == len(segments[op])-1 :
                upb = float('Inf')
            else:
                upb = segments[op][best['term'][1]][-1]
            best.update({'side': side, 'op': Op(op), 'term': Term(False, NumItem(col, lowb, upb))})
            res.append(best)
            
        return res
    findPositiveCover = staticmethod(findPositiveCover)

class Data:
    sym_alpha = 0
    sym_beta = 1
    sym_gamma = 2
    sym_delta = 3
    
    dataTypes = [{'class': NumDataM,  'match':'(datnum$)|(densenum$)'}, \
                 {'class': CatDataM,  'match':'densecat$'}, \
                 {'class': BoolDataM, 'match':'(densebool$)|(datbool$)|(sparsebool$)'}]

    defaultMinC = 1
    logger = Log(0)
    
    def __init__(self, datafiles):
        self.m = [None, None]
	self.redunRows = set()
        
        for fileId in (0,1):
            (colSuppsTmp, maxRowIdTmp, dataType) = Data.readInput(datafiles[fileId])
            if dataType == None:
                raise Exception("\nUnknown data type for file %s!" % datafiles[fileId])
            else:
                self.m[fileId] = Data.dataTypes[dataType]['class'](colSuppsTmp, maxRowIdTmp)
                
        if len(self.m[0]) != len(self.m[1]):
            raise Exception("\n\nData matrices do not have same number of rows,\
            first has %i, but second has %i!"%(len(self.m[0]), len(self.m[1])))

        ## Variable Numbers:
        self.N = len(self.m[0])    
        self.nf = [[i for i in range(self.nbCols(0))], [i for i in range(self.nbCols(1))]]


    def makeVectorABCD(self, alpha, beta, gamma):
        if max(self.m[0].type_id, self.m[1].type_id) == 3 :
            vect = [Data.sym_delta for i in range(self.N)]
            sets = [(Data.sym_gamma, gamma), (Data.sym_beta, beta), (Data.sym_alpha, alpha)]
            for (val, s) in sets:
                for i in s:
                    vect[i] = val
        else:
            vect = None
        return vect

    def makeInitInfo(self, ids, side, fitFull):
        types_id = (self.m[side].type_id, self.m[1-side].type_id)
        if (types_id  == (3,3) and fitFull)  or types_id  == (3,2):
            return self.m[side].makeBuckets(ids[side])
        elif (types_id  == (3,3) and not fitFull) or types_id == (1,3):
            if side == 1:
                return self.makeVectorABCD( set(), self.m[side].vect(ids[side]), set())        
            else:
                return self.makeVectorABCD( self.m[side].vect(ids[side]), set(), set())        
        elif types_id  == (1,2):
            return self.m[side].supp(Term(True, BoolItem(ids[side])))
        else:
            return None
        
    def nbCols(self,side):
        return self.m[side].nbCols()

    def addRedunRows(self, redunRows):
	self.redunRows.update(redunRows)

    def supp(self,side, term): ## the term should be the same type as the data on the considered side
        return self.m[side].supp(term)-self.redunRows
        
    def __str__(self):
        return "Data %s and %s" % ( self.m[0], self.m[1])        
    
    def scaleF(self, f):
        if f >= 1:
            return int(f)
        elif f >= 0 and f < 1 :
            return  int(round(f*self.N))
    
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
        self.nf = [self.m[0].nonFull(rMinC, rMinC), self.m[1].nonFull(rMinC, rMinC)]
        return (rMinC, rMinIn, rMinOut)
            
    def nonFull(self):
        return [set(self.nf[0]), set(self.nf[1])]
    def nbNonFull(self, side):
        return len(self.nf[side])

    def updateBests(self, bests, side, col):
        bs = self.m[side].anyAdvanceCol(bests, side, col)
        for b in range(len(bs)):
            bs[b].update({'supp': self.supp(bs[b]['side'], bs[b]['term'])})
        bests.upBests(bs)

       
    def computeBooleanPairParts(self, a, b, c, itemA, itemB, toImprov):
        ## Evaluate score for AB AbB ABb AbBb
        toColors = [[a, c], [c, a]]
        lparts = [[0, b+c, 0, self.N-b-c], [0, self.N-b-c, 0, b+c]]
        nA = [False, True, False, True]
        nB = [False, False, True, True]

        up_to = 1+ toImprov.queryTypesHasNeg()*3
        (scores, termsA, termsB) = ([], [], [])        
        for i in range(up_to):
            cand = toImprov.compAdv(itemA, True, nA[i], toColors[nB[i]], lparts[nB[i]])
            if cand != None:
                cand.update({'supp':  lparts[nB[i]][1]})
                scores.append(toImprov.score(cand))
                termsA.append(Term(nA[i], itemA))
                termsB.append(Term(nB[i], itemB))
        return (scores, termsA, termsB)

    def computePairParts11(self, mA, idA, mB, idB, toImprov, init_info=[[],[]], side=1):
        c = len(mA.vect(idA) & mB.vect(idB))
        a = len(mA.vect(idA) - mB.vect(idB))
        b = len(mB.vect(idB) - mA.vect(idA))
        return self.computeBooleanPairParts(a, b, c, BoolItem(idA), BoolItem(idB), toImprov)
    
    def computePairParts12(self, mA, idA, mB, idB, toImprov, init_info, side=1):
        return mB.fit(BoolItem(idA), mA.vect(idA), init_info[1-side][idA], idB, toImprov, side)
    
    def computePairParts13(self, mA, idA, mB, idB, toImprov, init_info, side=1):
        return mB.fit(BoolItem(idA), mA.vect(idA), init_info[1-side][idA], idB, toImprov, side)
        
    def computePairParts21(self, mA, idA, mB, idB, toImprov, init_info, side=0):
        (scores, termsB, termsA)= self.computePairParts12(mB, idB, mA, idA, toImprov, init_info, side )
        return (scores, termsA, termsB)

    def computePairParts22(self, mA, idA, mB, idB, toImprov, init_info, side=1):
        return self.computePairParts22Full(mA, idA, mB, idB, toImprov, init_info, side)

    def computePairParts23(self, mA, idA, mB, idB, toImprov, init_info, side=1):
        return self.computePairParts23Full(mA, idA, mB, idB, toImprov, init_info, side)
        
    def computePairParts32(self, mA, idA, mB, idB, toImprov, init_info, side=0):
        (scores, termsB, termsA)= self.computePairParts23(mB, idB, mA, idA, toImprov, init_info, side )
        return (scores, termsA, termsB)

    def computePairParts31(self, mA, idA, mB, idB, toImprov, init_info, side=0):
        (scores, termsB, termsA)= self.computePairParts13(mB, idB, mA, idA, toImprov, init_info, side )
        return (scores, termsA, termsB)

    
    def computePairParts33(self, mA, idA, mB, idB, toImprov, init_info, side=1):
        if len(init_info[1-side][idA]) == 3: # fit FULL
            if len(init_info[1-side][idA][0]) > len(init_info[side][idB][0]): 
                (scores, termsB, termsA)= self.computePairParts33Full(mB, idB, mA, idA, toImprov, init_info, 1-side )
                return (scores, termsA, termsB)
            else:
                return self.computePairParts33Full(mA, idA, mB, idB, toImprov, init_info, side)
        else:
            return self.computePairParts33Heur(mA, idA, mB, idB, toImprov, init_info, side)
    
    def computePairParts33Heur(self, mA, idA, mB, idB, toImprov, vectors_abcd, side=1):
        bestScore = float('-Inf')
        (scores, termsA, termsB) = ([], [], [])
        if mA.lenMode(idA) >= toImprov.minItmSuppOut() and mB.lenMode(idB) >= toImprov.minItmSuppOut() :
        #and mA.lenNonMode(idA) >= toImprov.minItmSuppIn() and mB.lenNonMode(idB) >= toImprov.minItmSuppIn() :
            ## FIT LHS then RHS
            (scoresL, termsBL, termsAL) = mA.fit(idB, mB.vect(idB), vectors_abcd[side][idB], idA, toImprov, 1-side)
            for tA in termsAL:
                suppA = mA.supp(tA)
                vector_abcd = Redescription.makeVectorABCD(True, self.N, suppA, set(), set())
                (scoresLR, termsALR, termsBLR) = mB.fit(tA.item, suppA, vector_abcd, idB, toImprov, side)
                for i in range(len(scoresLR)):
                    if scoresLR[i] > bestScore:
                        (scores, termsA, termsB) = ([scoresLR[i]], [termsALR[i]], [termsBLR[i]])
                        bestScore = scoresLR[i]
                        
            ## FIT RHS then LHS
            (scoresR, termsAR, termsBR) = mB.fit(idA, mA.vect(idA), vectors_abcd[1-side][idA], idB, toImprov, side)
            for tB in termsBR:
                suppB = mB.supp(tB)
                vector_abcd = Redescription.makeVectorABCD(True, self.N, set(), suppB, set())
                (scoresRL, termsBRL, termsARL) = mA.fit(tB.item, suppB, vector_abcd, idA, toImprov, 1-side)
                for i in range(len(scoresRL)):
                    if scoresRL[i] > bestScore:
                        (scores, termsA, termsB) = ([scoresRL[i]], [termsARL[i]], [termsBRL[i]])
                        bestScore = scoresRL[i]
                        
#             if len(scores) > 0:
#                print "%f: %s <-> %s" % (scores[0], termsA[0], termsB[0])
        return (scores, termsA, termsB)

    def computePairParts33Full(self, mA, idA, mB, idB, toImprov, buckets, side=1):
        interMat = []
        (scores, termsA, termsB) = ([], [], [])
        if mA.lenMode(idA) >= toImprov.minItmSuppOut() and mB.lenMode(idB) >= toImprov.minItmSuppOut() \
           and (mA.lenNonMode(idA) >= toImprov.minItmSuppIn() and mB.lenNonMode(idB) >= toImprov.minItmSuppIn()): 

            margA = [len(intA) for intA in buckets[1-side][idA][0]]
            margB = [len(intB) for intB in buckets[side][idB][0]]

            for bukA in buckets[1-side][idA][0]:
                interMat.append([len(bukA & bukB) for bukB in buckets[side][idB][0]])

            if buckets[1-side][idA][2] != None :
                margA[buckets[1-side][idA][2]] += mA.lenMode(idA)
                for bukBId in range(len(buckets[side][idB][0])):
                    interMat[buckets[1-side][idA][2]][bukBId] += len(mA.interMode(idA, buckets[side][idB][0][bukBId])) 

            if buckets[side][idB][2] != None :
                margB[buckets[side][idB][2]] += mB.lenMode(idB)
                for bukAId in range(len(buckets[1-side][idA][0])):
                    interMat[bukAId][buckets[side][idB][2]] += len(mB.interMode(idB, buckets[1-side][idA][0][bukAId]))        

            if buckets[1-side][idA][2] != None and buckets[side][idB][2] != None:
                interMat[buckets[1-side][idA][2]][buckets[side][idB][2]] += len(mB.interMode(idB, mA.modeSupp(idA)))

#             ### check marginals
#             totA = 0
#             for iA in range(len(buckets[1-side][idA][0])):
#                 sA = sum(interMat[iA])
#                 if sA != margA[iA]:
#                     raise Error('Error in computing the marginals (1)')
#                 totA += sA

#             totB = 0
#             for iB in range(len(buckets[side][idB][0])):
#                 sB = sum([intA[iB] for intA in interMat])
#                 if sB != margB[iB]:
#                     raise Error('Error in computing the marginals (2)')
#                 totB += sB

#             if totB != totA or totB != self.N:
#                 raise Error('Error in computing the marginals (3)')

            best = None
            belowA = 0
            lowA = 0
            while lowA < len(interMat) and self.N - belowA >= toImprov.minItmSuppIn():
                aboveA = 0
                upA = len(interMat)-1
                while upA >= lowA and self.N - belowA - aboveA >= toImprov.minItmSuppIn():
                    if belowA + aboveA  >= toImprov.minItmSuppOut():
                        Bina = [sum([interMat[iA][iB] for iA in range(lowA,upA+1)]) for iB in range(len(interMat[lowA]))]
                        totBina = sum(Bina)
                        belowBa = 0
                        lowB = 0
                        while lowB < len(interMat[lowA]) and totBina - belowBa >= toImprov.minItmSuppIn():
                            aboveBa = 0
                            upB = len(interMat[lowA])-1
                            while upB >= lowB and totBina - belowBa - aboveBa >= toImprov.minItmSuppIn():
                                suppI = totBina - belowBa - aboveBa
                                suppB = sum(margB[lowB:upB+1])
                                #print (self.N - belowA - aboveA, lowA, upA, lowB, upB), idA, idB, (suppB-suppI, suppI), (0, self.N - belowA - aboveA, 0, belowA + aboveA)
                                tmp_comp = toImprov.compAdv((self.N - belowA - aboveA, lowA, upA, lowB, upB), True, False, (suppB-suppI, suppI), (0, self.N - belowA - aboveA, 0, belowA + aboveA))
                                if BestsDraft.comparePair(tmp_comp, best) > 0:
                                    best = tmp_comp

                                aboveBa+=Bina[upB]
                                upB-=1
                            belowBa+=Bina[lowB]
                            lowB+=1
                    aboveA+=margA[upA]
                    upA-=1
                belowA+=margA[lowA]
                lowA+=1

            if best != None \
                   and (best['term'][1] == 0 or best['term'][2] == len(buckets[1-side][idA][1])-1) \
                   and (best['term'][3] == 0 or best['term'][4] == len(buckets[side][idB][1])-1):            
                best.update({'supp': best['term'][0]})
                scores.append(toImprov.score(best))

                if best['term'][1] == 0:
                    lowa = float('-Inf')
                else:
                    lowa = buckets[1-side][idA][1][best['term'][1]]
                if best['term'][2] == len(buckets[1-side][idA][1])-1 :
                    upa = float('Inf')
                else:
                    upa = buckets[1-side][idA][1][best['term'][2]]

                if best['term'][3] == 0:
                    lowb = float('-Inf')
                else:
                    lowb = buckets[side][idB][1][best['term'][3]]
                if best['term'][4] == len(buckets[side][idB][1])-1 :
                    upb = float('Inf')
                else:
                    upb = buckets[side][idB][1][best['term'][4]]

                termsA.append(Term(False, NumItem(idA, lowa, upa)))
                termsB.append(Term(False, NumItem(idB, lowb, upb)))
            
        return (scores, termsA, termsB)

    def computePairParts22Full(self, mA, idA, mB, idB, toImprov, init_info, side=1):
        
        nA = [False, True, False, True]
        nB = [False, False, True, True]

        up_to = 1+ toImprov.queryTypesHasNeg()*3
        best = [ None for i in range(up_to)]

        for catA in mA.colSupps[idA].keys():
            for catB in mB.colSupps[idB].keys():
                suppB = len(mB.colSupps[idB][catB])
                suppI = len(mA.colSupps[idA][catA] & mB.colSupps[idB][catB])
                suppsI = (suppI, len(mA.colSupps[idA][catA]) - suppI)
                suppsB = (suppB, self.N-suppB)
                for i in range(up_to):
                    tmp_comp = toImprov.compAdv((suppsB[nB[i]], catA, catB), True, nA[i], (suppsI[not nB[i]], suppsI[nB[i]]), (0, suppsB[nB[i]], 0, suppsB[not nB[i]] ))
                    if tmp_comp != None and BestsDraft.comparePair(tmp_comp, best[i]) > 0:
#                        print (suppsB[nB[i]], catA, catB), True, nA[i], (suppsI[not nB[i]], suppsI[nB[i]]), (0, suppsB[nB[i]], 0, suppsB[not nB[i]], tmp_comp )
                        best[i] = tmp_comp

        (scores, termsA, termsB) = ([], [], [])
        
        for i in range(up_to):
            if best[i] != None:
                best[i].update({'supp': best[i]['term'][0]})
                scores.append(toImprov.score(best[i]))
                termsA.append(Term(nA[i], CatItem(idA, best[i]['term'][1])))
                termsB.append(Term(nB[i], CatItem(idB, best[i]['term'][2])))
#        pdb.set_trace()
        return (scores, termsA, termsB)

    def computePairParts23Full(self, mA, idA, mB, idB, toImprov, buckets, side=1):

        nA = [False, True, False, True]
        nB = [False, False, True, True]

        up_to = 1+ toImprov.queryTypesHasNeg()*3
        best = [ None for i in range(up_to)]

        interMat = []
        (scores, termsA, termsB) = ([], [], [])
        if mB.lenMode(idB) >= toImprov.minItmSuppOut() and mB.lenNonMode(idB) >= toImprov.minItmSuppIn():

            margB = [len(intB) for intB in buckets[side][idB][0]]
            if buckets[side][idB][2] != None :
                margB[buckets[side][idB][2]] += mB.lenMode(idB)

            for catA in mA.colSupps[idA].keys():
                interMat = [len(mA.colSupps[idA][catA] & bukB) for bukB in buckets[side][idB][0]]
                if buckets[side][idB][2] != None :
                    interMat[buckets[side][idB][2]] += len(mB.interMode(idB, mA.colSupps[idA][catA]))        

                totBina = len(mA.colSupps[idA][catA])
                        
                belowBa = 0
                lowB = 0
                while lowB < len(interMat) and \
                          (totBina - belowBa >= toImprov.minItmSuppIn() or totBina - belowBa >= toImprov.minItmSuppOut()):
                    aboveBa = 0
                    upB = len(interMat)-1
                    while upB >= lowB and \
                          (totBina - belowBa - aboveBa >= toImprov.minItmSuppIn() or totBina - belowBa - aboveBa >= toImprov.minItmSuppOut()):
                        suppsI = (totBina - belowBa - aboveBa, belowBa + aboveBa)
                        suppB = sum(margB[lowB:upB+1])
                        suppsB = (suppB, self.N-suppB)
                        for i in range(up_to):
                            tmp_comp = toImprov.compAdv((suppsB[nB[i]], catA, lowB, upB), True, nA[i], (suppsI[not nB[i]], suppsI[nB[i]]), (0, suppsB[nB[i]], 0, suppsB[not nB[i]]))
                            if BestsDraft.comparePair(tmp_comp, best[i]) > 0:
 #                               print (suppsB[nB[i]], catA, lowB, upB), True, nA[i], (suppsI[not nB[i]], suppsI[nB[i]]), (0, suppsB[nB[i]], 0, suppsB[not nB[i]], tmp_comp)
                                best[i] = tmp_comp

                        aboveBa+=interMat[upB]
                        upB-=1
                    belowBa+=interMat[lowB]
                    lowB+=1

        (scores, termsA, termsB) = ([], [], [])
        
        for i in range(up_to):
            if best[i] != None and ( best[i]['term'][2] != 0 or best[i]['term'][3] != len(buckets[side][idB][1])-1 ):
                
                if best[i]['term'][2] == 0:
                    lowb = float('-Inf')
                else:
                    lowb = buckets[side][idB][1][best[i]['term'][2]]
                if best[i]['term'][3] == len(buckets[side][idB][1])-1 :
                    upb = float('Inf')
                else:
                    upb = buckets[side][idB][1][best[i]['term'][3]]

                best[i].update({'supp': best[i]['term'][0]})
                scores.append(toImprov.score(best[i]))
                termsA.append(Term(nA[i], CatItem(idA, best[i]['term'][1])))
                termsB.append(Term(nB[i], NumItem(idB, lowb, upb)))

#        print scores
        return (scores, termsA, termsB)

    def computePair(self, idA, idB, init_info, toImprov):
        method_string = 'self.computePairParts%i%i' % (self.m[0].type_id, self.m[1].type_id)
        try:
            method_compute =  eval(method_string)
        except AttributeError:
              raise Exception('Oups this combination does not exist (%i %i)!' % (self.m[0].type_id, self.m[1].type_id))

        return method_compute(self.m[0], idA, self.m[1], idB, toImprov, init_info)
        

    def initializeRedescriptions(self, nbRed, queryTypes, minScore=0):
        Data.logger.printL(1, 'Starting the search for initial pairs...')
        self.pairs = []
        fitFull = True
        pairsRType = {True: set(), False: set()}
        if True in queryTypes[True] or True in queryTypes[False]:
            pairsRType[True].add(True)
        if False in queryTypes[True] or False in queryTypes[False]:
            pairsRType[True].add(False)
        toImprov = BestsDraft(pairsRType, self.N)

        ids= self.nonFull()
        init_info = [{},{}]
        
        init_info[0][7] = self.makeInitInfo((7, 0), 0, fitFull) 
        init_info[1][0] = self.makeInitInfo((7, 0), 1, fitFull)
        (scores, termsA, termsB) = self.computePair(7, 0, init_info, toImprov)

        cL = 0
        cR = 0  
        for idA in ids[0]:
            if cL % self.divL == 0:
                Data.logger.printL(4, 'Searching pairs %i <=> *...' %(idA))
                for idB in ids[1]:
                    if cR % self.divR == 0:
                        Data.logger.printL(10, 'Searching pairs %i <=> %i ...' %(idA, idB))
                        if not init_info[0].has_key(idA): # pairsA has just the same keys
                            init_info[0][idA] = self.makeInitInfo((idA, idB), 0, fitFull) 
                            
                        if not init_info[1].has_key(idB): # pairsB has just the same keys
                            init_info[1][idB] = self.makeInitInfo((idA, idB), 1, fitFull)
                        (scores, termsA, termsB) = self.computePair(idA, idB, init_info, toImprov)
                        for i in range(len(scores)):
                            if scores[i] >= minScore:
                                Data.logger.printL(9, 'Score:%f %s <=> %s' % (scores[i], termsA[i], termsB[i]))
                                self.methodsP['add'](scores[i], idA, idB)
                                self.pairs.append((termsA[i], termsB[i]))
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
        self.cols = [[],[]]
        self.alternateSortPairsSide(0)
        self.alternateSortPairsSide(1)
        self.countsCols = [0,0]
    
    def alternateSortPairsSide(self, side):
        tmp = []
        for i in self.pairsSide[side].keys():
            if len(self.pairsSide[side][i]) > 0:
                self.pairsSide[side][i].sort(key=lambda x: x[0])
                tmp.append((self.pairsSide[side][i][-1], i))
        self.cols[side] = [i[1] for i in sorted(tmp, key=lambda x: x[0], reverse=True)]
        
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
        if len(self.cols[side]) > 0:
            try:
                (tmp, idP) = self.pairsSide[side][self.cols[side][self.countsCols[side]]].pop()
            except IndexError:
                raise Warning('Error in returning the next initial pair!')
                return None
            if len(self.pairsSide[side][self.cols[side][self.countsCols[side]]]) == 0:
                self.cols[side].pop(self.countsCols[side])
            else:
                self.countsCols[side] += 1
            if self.countsCols[side] >= len(self.cols[side]):
                self.countsCols[side] = 0
            return idP
        else:
            return None
    
    def getNextInitialRed(self):
        if self.count < self.nbRed :
            pair = self.methodsP['next'](self.count)
            self.count += 1
            return Redescription.fromInitialPair(pair, self, self.count)
        else:
            return None

    def readInput(datafile):
        ## Read input

        utilsIO.logger = Data.logger
        format_f = datafile.split('.').pop()
        if format_f == 'densebool':
            (colSuppsTmp, rowIdTmp) = utilsIO.readDense(datafile)
        elif format_f == 'datbool':
            (colSuppsTmp, rowIdTmp) = utilsIO.readMatlab(datafile)
        elif format_f == 'sparsebool':
            (colSuppsTmp, rowIdTmp) = utilsIO.readSparse(datafile)
        elif format_f == 'densenum':
            (colSuppsTmp, rowIdTmp) = utilsIO.readNumerical(datafile)
        elif format_f == 'datnum':
            (colSuppsTmp, rowIdTmp) = utilsIO.readMatlabNum(datafile)
        elif format_f == 'densecat' :
            (colSuppsTmp, rowIdTmp) = utilsIO.readCategorical(datafile)
        else:
            (colSuppsTmp, rowIdTmp) =  (None, None)
            raise Warning('Unknown format !')
            
        dataType = None
        for i in range(len(Data.dataTypes)):
            if re.match(Data.dataTypes[i]['match'],format_f):
                dataType = i

        return (colSuppsTmp, rowIdTmp, dataType)
    readInput = staticmethod(readInput)
