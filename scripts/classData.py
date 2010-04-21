import math, random, re, utilsIO
from classRule import Op, Item, BoolItem, CatItem, NumItem, Term, Rule 
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

        for op in toImprov.ruleTypesOp():
            for neg in toImprov.ruleTypesNP(op):
                b = toImprov.compAdv(Term(neg, BoolItem(col)), op, neg, toColors[op], lparts)
                if b != None:
                    b.update({'side': side, 'op': Op(op)})
                    res.append(b)
        return res
    
class CatDataM(DataM):
    type_id = 2

    def suppItem(self, item):
        colX = self.colSupps[item.colId()]
        supp = set()
        for idRow in range(len(colX)):
            if colX[idRow] == item.cat:
                supp.add(idRow)
        return supp

    def vect(self, col): ## the term should be the same type as the data on the considered side
        return set()
    
    def __str__(self):
        return "%i x %i categorical" % ( len(self), self.nbCols())
    
class NumDataM(DataM):
    type_id = 3

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

        lparts = (0, len(suppX), 0, len(self) - len(suppX))
        lenIntX = len(self.interMode(col, suppX))
        linPartsMode = (0, lenIntX, 0, self.lenMode(col) - lenIntX)
        segments = None
            
        if lparts[3] >= toImprov.minNbItmOut() and (lparts[1] - linPartsMode[1]) >= toImprov.minNbItmIn() :
            segments = NumDataM.makeSegments(vector_abcd, side, self.colSupps[col], linPartsMode)
            cand_A = NumDataM.findCover(segments, lparts, side, col, toImprov)

            for cand in cand_A:
                cand.update({'supp': len(suppX)})
                scores.append(toImprov.score(cand))
                termsA.append(Term(False, itemX))
                termsB.append(cand['term'])

        if toImprov.ruleTypesHasNeg() and lparts[1] >= toImprov.minNbItmOut() and (lparts[3] - linPartsMode[3]) >= toImprov.minNbItmIn():
            if segments == None:
                segments = NumDataM.makeSegments(vector_abcd, side, self.colSupps[col], linPartsMode)
            segments = NumDataM.negateSegments(segments, False, True)
            lpartsN = (lparts[0], lparts[3], lparts[2], lparts[1])
            cand_Ab = NumDataM.findCover(segments, lpartsN, side, col, toImprov)

            for cand in cand_Ab:            
                cand.update({'supp': len(self) - len(suppX)})
                scores.append(toImprov.score(cand))
                termsA.append(Term(True, itemX))
                termsB.append(cand['term'])

        return (scores, termsA, termsB)

    def anyAdvanceCol(self, toImprov, side, col):
        res = []
#         if ( len(self.interNonMode(col,toImprov.parts[2])) >= toImprov.minNbItmIn() \
#              or len(self.interNonMode(col,toImprov.parts[1-side])) >= toImprov.minNbC() ):

#             if (( len(toImprov.parts[2])- len(self.interMode(col, toImprov.parts[2]))) + \
#                 (len(toImprov.parts[1-side]) - len(self.interMode(col, toImprov.parts[1-side])))) < toImprov.minNbItmIn() :
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


        if lparts[2] - linPartsMode[2] >= toImprov.minNbItmIn() or lparts[1-side] - linPartsMode[1-side] >= toImprov.minNbC(): 
            segments = NumDataM.makeSegments(toImprov.parts[4], side, self.colSupps[col], linPartsMode)
            res = NumDataM.findCover(segments, (lparts[side], lparts[1-side], lparts[2], lparts[3]), side, col, toImprov)
        return res
    
    def makeSegments(vector_abcd, side, vectCol, linPartsMode):
        ## vector_abcd alpha->0 gamma->1 delta->2 beta->3
        segments = [[],[]]
        if side==0:
            toColorsMode = [[linPartsMode[0], linPartsMode[2]], [linPartsMode[3], linPartsMode[1]]]
            OR = [Redescription.sym_delta, Redescription.sym_beta]
            BLUE = [Redescription.sym_gamma, Redescription.sym_beta]
        else:
            toColorsMode = [[linPartsMode[1], linPartsMode[2]], [linPartsMode[3], linPartsMode[0]]]
            OR = [Redescription.sym_delta, Redescription.sym_alpha]
            BLUE = [Redescription.sym_gamma, Redescription.sym_alpha]

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
        
        res = NumDataM.findPositiveCover(segments, lparts, side, col, toImprov)
        res.extend(NumDataM.findNegativeCover(segments, lparts, side, col, toImprov))
        return res
        
    findCover = staticmethod(findCover)


    def findCoverFullSearch(segments, lparts, side, col, toImprov):
        res = []
        maxSeg = 250
        for op in toImprov.ruleTypesOp():
            bests = {False: { 'term': (None, None), 'acc': float('-Inf'), 'toRed': 0, 'toBlue': 0},\
                     True: { 'term': (None, None), 'acc': float('-Inf'), 'toRed': 0, 'toBlue': 0}}

            nb_seg = len(segments[op])
            if nb_seg > maxSeg:
                nb_seg = 0
            for seg_s in range(nb_seg):
                toColors = [0,0]
                for seg_e in range(seg_s,len(segments[op])):
                    toColors[0] += segments[op][seg_e][0]
                    toColors[1] += segments[op][seg_e][1]
                    for neg in ruleTypes[op]:
                        tmp_comp = toImprov.compAdv((seg_s, seg_e), op, neg, toColors, lparts)
                        if BestsDraft.comparePair(tmp_comp, bests[neg]) > 0:
                            bests[neg] = tmp_comp
                                
            for neg in toImprov.ruleTypesNP(op):
                if bests[neg]['term'][0] != None:
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
        return res
    findCoverFullSearch = staticmethod(findCoverFullSearch)

    def findNegativeCover(segments, lparts, side, col, toImprov):
        res = []
        for op in toImprov.ruleTypesOp():
            if toImprov.ruleTypesHasNeg(op):
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
                    #print '%i <-> %i: %i/%i=%f' \
                    #        % (best['term'][0], best['term'][1], best['toBlue'], best['toRed'], best['acc'])
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

    def findPositiveCover(segments, lparts, side, col, toImprov):
        res = []
        for op in toImprov.ruleTypesOp():
            if toImprov.ruleTypesHasPos(op):
                #print 'INCR SEARCH:'
                toColors_f = [0,0]
                nb_seg_f = 0
                best_f = None
                toColors_b = [0,0]
                nb_seg_b = 0
                best_b = None 

                for  i in range(len(segments[op])-1):
                    # FORWARD
                    if i > 0 and (toColors_f[0] == 0 or toImprov.compAcc(op, False, segments[op][i][:2], lparts) <  float(toColors_f[1])/float(toColors_f[0])):
                        toColors_f = [toColors_f[0] + segments[op][i][0], toColors_f[1] + segments[op][i][1]]
                        nb_seg_f += 1
                    else: 
                        toColors_f = segments[op][i][:2]
                        nb_seg_f = 0
                    tmp_comp_f = toImprov.compAdv((i - nb_seg_f, i), op, False, toColors_f, lparts)
                    if BestsDraft.comparePair(tmp_comp_f, best_f) > 0 :
                        best_f = tmp_comp_f

                    # BACKWARD
                    if i > 0 and (toColors_b[0] == 0 or  toImprov.compAcc(op, False, segments[op][-(i+1)][:2], lparts) <  float(toColors_b[1])/float(toColors_b[0]) ):
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
    #                 for best in bests:
    #                     print '%i <-> %i: %i/%i=%f' \
    #                         % (best['term'][0], best['term'][1], best['toBlue'], best['toRed'], best['acc'])

                    best = sorted(bests, cmp=BestsDraft.comparePair)[-1]

                elif best_f == None:
                    best = best_f
                else:
                    best = best_b

                if best != None :
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

                # else:
    #                 print 'No candidate !'
    #             print 'FULL SEARCH:'
    #             best_full = (0, '')
    #             for seg_s in range(len(segments[op])):
    #                 toColors = [0,0]
    #                 for seg_e in range(seg_s,len(segments[op])):
    #                     toColors[0] += segments[op][seg_e][0]
    #                     toColors[1] += segments[op][seg_e][1]
    #                     if  toImprov.compAcc(op, False, toColors, lparts) > best_full[0]:
    #                         best_full = ( toImprov.compAcc(op, False, toColors, lparts),\
    #                                  '%i <-> %i: %i/%i, %f' % (seg_s, seg_e, toColors[1], toColors[0], toImprov.compAcc(op, False, toColors, lparts)))
    #             print best_full[1]
    #             if best == None or best_full[0] != best['acc']:
    #                 print 'FULL SEARCH GIVES DIFFERENT RESULT !'
            
        return res
    findPositiveCover = staticmethod(findPositiveCover)

class Data:

    dataTypes = [{'class': NumDataM,  'match':'(ndat$)|(num$)'}, \
                 {'class': CatDataM,  'match':'cat$'}, \
                 {'class': BoolDataM, 'match':'(dense$)|(bdat$)|(sparse$)'}]

    defaultMinC = 1
    
    def __init__(self, datafiles):
        self.m = [None, None]
        
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

    def needsVectorABCD(self):
        return self.m[0].type_id +self.m[1].type_id > 2
        
    def nbCols(self,side):
        return self.m[side].nbCols()

    def supp(self,side, term): ## the term should be the same type as the data on the considered side
        return self.m[side].supp(term)
        
    def __str__(self):
        return "Data %s and %s" % ( self.m[0], self.m[1])        
    
    def scaleF(self, f):
        if f >= 1:
            return int(f)
        elif f >= 0 and f < 1 :
            return  int(math.round(f*self.N))
    
    def scaleSuppParams(self, minC=None, minIn=None, minOut=None, minSIn=None, minSOut=None):
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
        if minSIn == None:
            rMinSIn = rMinIn
        else:
            rMinSIn = self.scaleF(minSIn)
        if minSOut == None:
            rMinSOut = self.N - rMinSIn
        else:
            rMinSOut = self.scaleF(minSOut)
        self.nf = [self.m[0].nonFull(rMinIn, rMinOut), self.m[1].nonFull(rMinIn, rMinOut)]
        return (rMinC, rMinIn, rMinOut, rMinSIn, rMinSOut)
            
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

        up_to = 1+ toImprov.ruleTypesHasNeg()*3
        (scores, termsA, termsB) = ([], [], [])        
        for i in range(up_to):
            cand = toImprov.compAdv(itemA, True, nA[i], toColors[nB[i]], lparts[nB[i]])
            if cand != None:
                cand.update({'supp':  lparts[nB[i]][1]})
                scores.append(toImprov.score(cand))
                termsA.append(Term(nA[i], itemA))
                termsB.append(Term(nB[i], itemB))
        return (scores, termsA, termsB)

    def computePairParts11(self, mA, idA, mB, idB, toImprov, vectors_abcd=[[],[]], side=1):
        c = len(mA.vect(idA) & mB.vect(idB))
        a = len(mA.vect(idA) - mB.vect(idB))
        b = len(mB.vect(idB) - mA.vect(idA))
        return self.computeBooleanPairParts(a, b, c, BoolItem(idA), BoolItem(idB), toImprov)
    
    def computePairParts12(self, mA, idA, mB, idB, toImprov, vectors_abcd, side=1):
        raise Exception('To be implemented !')
        return (scores, termsA, termsB)
    
    def computePairParts13(self, mA, idA, mB, idB, toImprov, vectors_abcd, side=1):
        return mB.fit(BoolItem(idA), mA.vect(idA), vectors_abcd[1-side][idA], idB, toImprov, side)
        
    def computePairParts21(self, mA, idA, mB, idB, toImprov, vectors_abcd, side=0):
        (scores, termsB, termsA)= self.computePairParts12(mB, idB, mA, idA, toImprov, vectors_abcd, side )
        return (scores, termsA, termsB)

    def computePairParts22(self, mA, idA, mB, idB, toImprov, vectors_abcd, side=1):
        raise Exception('To be implemented !')
        return (scores, termsA, termsB)

    def computePairParts23(self, mA, idA, mB, idB, toImprov, vectors_abcd, side=1):
        raise Exception('To be implemented !')
        return (scores, termsA, termsB)

    def computePairParts32(self, mA, idA, mB, idB, toImprov, vectors_abcd, side=0):
        (scores, termsB, termsA)= self.computePairParts23(mB, idB, mA, idA, toImprov, vectors_abcd, side )
        return (scores, termsA, termsB)

    def computePairParts31(self, mA, idA, mB, idB, toImprov, vectors_abcd, side=0):
        (scores, termsB, termsA)= self.computePairParts13(mB, idB, mA, idA, toImprov, vectors_abcd, side )
        return (scores, termsA, termsB)
    
    def computePairParts33(self, mA, idA, mB, idB, toImprov, vectors_abcd, side=1):
        bestScore = float('-Inf')
        (scores, termsA, termsB) = ([], [], [])
        if mA.lenMode(idA) >= toImprov.minNbItmOut() and mB.lenMode(idB) >= toImprov.minNbItmOut() :
        #and mA.lenNonMode(idA) >= toImprov.minNbItmIn() and mB.lenNonMode(idB) >= toImprov.minNbItmIn() :
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
                
    def computePair(self, idA, idB, vectors_abcd, toImprov):
        method_string = 'self.computePairParts%i%i' % (self.m[0].type_id, self.m[1].type_id)
        try:
            method_compute =  eval(method_string)
        except AttributeError:
              raise Exception('Oups this combination does not exist (%i %i)!' % (self.m[0].type_id, self.m[1].type_id))

        return method_compute(self.m[0], idA, self.m[1], idB, toImprov, vectors_abcd)
        

    def initializeRedescriptions(self, nbRed, ruleTypes, minScore=0):
        self.pairs = []
        
        toImprov = BestsDraft(ruleTypes, self.N)

        ids= self.nonFull()
        vectors_abcd = [{},{}]
        cL = 0
        cR = 0  
        for idA in ids[0]:
            if cL % self.divL == 0:
                for idB in ids[1]:
                    if cR % self.divR == 0:
                        if not vectors_abcd[0].has_key(idA): # pairsA has just the same keys
                            vectors_abcd[0][idA] = Redescription.makeVectorABCD(self.m[1].type_id > 1, self.N, self.m[0].vect(idA), set(), set())
                        if not vectors_abcd[1].has_key(idB): # pairsB has just the same keys
                            vectors_abcd[1][idB] = Redescription.makeVectorABCD(self.m[0].type_id > 1, self.N, set(), self.m[1].vect(idB), set())
                        (scores, termsA, termsB) = self.computePair(idA, idB, vectors_abcd, toImprov)
                        for i in range(len(scores)):
                            if scores[i] >= minScore:
                                self.methodsP['add'](scores[i], idA, idB)
                                self.pairs.append((termsA[i], termsB[i]))
                    cR += 1
            cL += 1

        self.methodsP['sort']()
        self.count = 0
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
            return Redescription.fromInitialPair(pair, self)
        else:
            return None

    def readInput(datafile):
        ## Read input

        format_f = datafile.split('.').pop()
        if format_f == 'dense':
            (colSuppsTmp, rowIdTmp) = utilsIO.readDense(datafile)
        elif format_f == 'bdat':
            (colSuppsTmp, rowIdTmp) = utilsIO.readMatlab(datafile)
        elif format_f == 'sparse':
            (colSuppsTmp, rowIdTmp) = utilsIO.readSparse(datafile)
        elif format_f == 'num':
            (colSuppsTmp, rowIdTmp) = utilsIO.readNumerical(datafile)
        elif format_f == 'ndat':
            (colSuppsTmp, rowIdTmp) = utilsIO.readMatlabNum(datafile)
        elif format_f == 'cat' :
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
