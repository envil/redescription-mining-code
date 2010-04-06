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

    def nonFull(self):
        return [col for col in range(self.nbCols())]


    def compAcc(op, neg, toColors, lparts):
        acc = 0
        if op:
            if neg:
                acc = float(lparts[2] + lparts[1] - toColors[1])/(lparts[0] + lparts[1] + lparts[2] + lparts[3] - toColors[0])
            else:
                acc = float(lparts[2] + toColors[1])/(lparts[0] + lparts[1] + lparts[2] + toColors[0])
        else:
            if neg:
                acc = float(lparts[2] - toColors[1])/(lparts[0] - toColors[0] + lparts[1] + lparts[2])
            else:
                acc = float(toColors[1])/(toColors[0] + lparts[1] + lparts[2])
        return acc
    compAcc = staticmethod(compAcc)

    def makeBest(t, op, neg, toColors, lparts, noMin=False):
        b = None
        if op:
            if neg:
                if noMin or ((lparts[1] - toColors[1] >= Data.minC) and ( toColors[0] >= Data.minS )):
                    b= {'acc': float(lparts[2] + lparts[1] - toColors[1])/(lparts[0] + lparts[1] + lparts[2] + lparts[3] - toColors[0]),\
                        'toRed': lparts[3] - toColors[0], 'toBlue': lparts[1] - toColors[1], 'term': t}

            else:
                if noMin or ((toColors[1] >= Data.minC) and (lparts[3] + toColors[0] >= Data.minS )):
                    b= {'acc': float(lparts[2] + toColors[1])/(lparts[0] + lparts[1] + lparts[2] + toColors[0]),\
                        'toRed': toColors[0], 'toBlue': toColors[1], 'term': t}
        else:
            if neg:
                if noMin or ((lparts[2] - toColors[1] >= Data.minC) and (lparts[2] - toColors[0] >= Data.minS )):
                    b= {'acc': float(lparts[2] - toColors[1])/(lparts[0] - toColors[0] + lparts[1] + lparts[2]),\
                        'toRed': lparts[0] - toColors[0], 'toBlue': lparts[2] - toColors[1], 'term': t}
            else:
                if noMin or ((toColors[1] >= Data.minC) and (toColors[0] >= Data.minS )):
                    b= {'acc': float(toColors[1])/(toColors[0] + lparts[1] + lparts[2]),\
                        'toRed': toColors[0], 'toBlue': toColors[1], 'term': t}
        return b
    makeBest = staticmethod(makeBest)

class BoolDataM(DataM):
    type_id = 1

    def suppItem(self, item):
        return set(self.colSupps[item.colId()])

    def __str__(self):
        return "%i x %i boolean" % ( len(self), self.nbCols())

    def vect(self, col): ## the term should be the same type as the data on the considered side
        return self.colSupps[col]

    def nonFull(self):
        it = []
        for col in range(len(self.colSupps)):
            if len(self.colSupps[col]) >= Data.minC and len(self.colSupps[col]) <= self.nbRows - Data.minC :
                it.append(col)
        return it 

    def computeCol(self, parts, side, col, ruleTypes):
        toColors = {True:[0,0], False:[0,0]}
        res = []
        if side == 1:
            (lparts) = (len(parts[1]), len(parts[0]), len(parts[2]), len(parts[3]))
            (toColors[False][0], toColors[True][1], toColors[False][1], toColors[True][0]) = \
                                 (len(parts[1] & self.colSupps[col]), len(parts[0] & self.colSupps[col]), len(parts[2] & self.colSupps[col]), len(parts[3] & self.colSupps[col]))
        
        else:
            (lparts) = (len(parts[0]), len(parts[1]), len(parts[2]), len(parts[3]))
            (toColors[False][0], toColors[True][1], toColors[False][1], toColors[True][0]) = \
                                 (len(parts[0] & self.colSupps[col]), len(parts[1] & self.colSupps[col]), len(parts[2] & self.colSupps[col]), len(parts[3] & self.colSupps[col]))

        for op in ruleTypes.keys():
            for neg in ruleTypes[op]:
                b = DataM.makeBest(Term(neg, BoolItem(col)), op, neg, toColors[op], lparts)
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

    
    def __init__(self, ncolSupps=[], nmaxRowId=-1):
        ## self.colSupps[col] = [[list of values], [list of ids]] ordered by value
        self.colSupps = [ sorted( [(ncolSupps[col][i],i) for i in range(len(ncolSupps[col]))], key=lambda x: x[0])  for col in range(len(ncolSupps))]
        #self.colSupps = [ zip(*sorted( [(ncolSupps[col][i],i) for i in range(len(ncolSupps[col]))], key=lambda x: x[0]) for col in range(len(ncolSupps)))]
        self.nbRows = nmaxRowId+1

    def suppItem(self, item):
        ## DO NOT USE INDEX IF THE BOUND ARE NOT ONE OF THE VALUES
        supp = set()
        for (val , row) in self.colSupps[item.colId()]:
            if val > item.upb :
                return supp
            elif val >= item.lowb:
                supp.add(row)
        return supp

    def vect(self, col): ## the term should be the same type as the data on the considered side
        return set()
    
    def __str__(self):
        return "%i x %i numerical" % ( len(self), self.nbCols())

    def fit(self, itemX, suppX, vector_abcd, col, has_neg, side):
        if has_neg:
            ruleTypes = {True: [False, True]}
        else:
            ruleTypes = {True: [False]}
        
        if side==1:
            lparts = (len(suppX), 0, 0, len(self) - len(suppX))
        else:
            lparts = (0, len(suppX), 0, len(self) - len(suppX))

        segments = NumDataM.makeSegments(vector_abcd, side, self.colSupps[col])
        #Data.log_fid.write('## Pair (%i,%i), %i + %i segments\n%s' \
        # % (itemX.colId(), col, len(segments[0]), len(segments[1]), NumDataM.dispSegments(segments)))
        #Data.log_fid.flush()
        cand_A = NumDataM.findCover(segments, lparts, side, col, ruleTypes)
#        cand_A = NumDataM.findCover(segments, ids_seg_blue, ids_seg_bluemix, max_blue, max_bluemix, lparts, side, col, ruleTypes)
        (suppI, suppU, rand, termsA, termsB) = ([], [], [], [], [])

        for cand in cand_A:
            suppI.append(float(cand['toBlue']))
            suppU.append(float(cand['toRed'] + len(suppX)))
            rand.append(random.random())
            termsA.append(Term(False, itemX))
            termsB.append(cand['term'])

        # if has_neg and len(cand_A) > 0:
#             NumDataM.negateSegments(segments, side == 1, side == 0)
#             cand_A = NumDataM.findCover(segments, ids_seg_clean[1], ids_seg_mix[1], max_clean[1], max_mix[1], lparts, side, col, ruleTypes)
#             cand_Ab = NumDataM.findCover(segments, lparts, ruleTypes)

#             for cand in cand_Ab:
#                 suppI.append(float(cand['toBlue']))
#                 suppU.append(float(cand['toRed'] + len(suppX)))
#                 rand.append(random.random())
#                 termsA.append(Term(True, itemX))
#                 termsB.append(cand['term'])
        return (suppI, suppU, rand, termsA, termsB)
            
    def makeSegments(vector_abcd, side, vectCol):
        ## vector_abcd alpha->0 gamma->1 delta->2 beta->3
        segments = [[],[]]
        if side==0:
            OR = [Redescription.sym_delta, Redescription.sym_beta]
            BLUE = [Redescription.sym_gamma, Redescription.sym_beta]
        else:
            OR = [Redescription.sym_delta, Redescription.sym_alpha]
            BLUE = [Redescription.sym_gamma, Redescription.sym_alpha]

        ## segment: [count_red, count_blue, start_val, end_val]
        current_segments = [[0,0, None, None],[0,0, None, None]] # [AND [RED, BLUE] , OR [RED, BLUE]]
        
        ## buff: [count_red_current_val, count_blue_current_val, highest_val]
        buff_count = [[0,0, None],[0,0, None]]
        for (val, row) in vectCol:
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
            
#     def makeSegments(vector_abcd, side, vectCol):
#         ## vector_abcd alpha->0 gamma->1 delta->2 beta->3
#         segments = [[],[]]
#         if side==0:
#             OR = [Redescription.sym_delta, Redescription.sym_beta]
#             BLUE = [Redescription.sym_gamma, Redescription.sym_beta]
#         else:
#             OR = [Redescription.sym_delta, Redescription.sym_alpha]
#             BLUE = [Redescription.sym_gamma, Redescription.sym_alpha]

#         ## segment: [count_red, count_blue, start_val, end_val]
#         current_segments = [[0,0, None, None],[0,0, None, None]] # [AND [RED, BLUE] , OR [RED, BLUE]]
#         max_clean = [[[0,-1],[0, -1]],[[0,-1], [0,-1]]] # [RED [AND, OR], BLUE [AND, OR]]
#         max_mix = [[[0,-1],[0, -1]],[[0,-1], [0,-1]]]  # [RED [AND, OR], BLUE [AND, OR]]
#         nb_seg = [[0,0],[0,0]]  # [RED [AND, OR], BLUE [AND, OR]]
#         ids_seg_clean = [[[],[]],[[],[]]]  # [RED [AND, OR], BLUE [AND, OR]]
#         ids_seg_mix = [[[],[]], [[],[]], [[],[]]]  # [NEUT [AND, OR], RED [AND, OR], BLUE [AND, OR]]

#         ## buff: [count_red_current_val, count_blue_current_val, highest_val]
#         buff_count = [[0,0, None],[0,0, None]]
#         for (val, row) in vectCol:
#             op = vector_abcd[row] in OR
#             color = vector_abcd[row] in BLUE

#             if val == buff_count[op][-1]:
#                 buff_count[op][color] += 1

#             ## first loop will go throught this conditional and append the initial segment to the list, removed at the end
#             elif buff_count[op][color] == 0:  ## AND val > current_segments[op][-1]
#                 ## Other color encontered, no mixing: push counts, save and start new 
#                 #print 'NO MIXING\nSegments: %s\n\nCurrent:%s\nBuffer:%s' % (segments, current_segments, buff_count)
# #                pdb.set_trace()
#                 col_new_seg = buff_count[op][1]>0 # what's the color of the segment to add
#                 current_segments[op][col_new_seg] += buff_count[op][col_new_seg] # push counts from buffer
#                 current_segments[op][-1] = buff_count[op][-1] # push upper bound from buffer
#                 ids_seg_clean[col_new_seg][op].append(len(segments[op])) # record the id of the segment
#                 if current_segments[op][col_new_seg] > max_clean[col_new_seg][op][0] : # is it the best so far ?
#                     max_clean[col_new_seg][op] = [current_segments[op][col_new_seg], len(segments[op])]
#                 nb_seg[col_new_seg][op] += 1 # count segments (temporary double check)
#                 segments[op].append(current_segments[op]) # append to segments
#                 buff_count[op] = [1*(not color), 1*color, val] # create new segment
#                 current_segments[op] = [0, 0, val, val] # re-initialize buffer

#             elif buff_count[op][not color] == 0 : ## AND val > current_segments[op][-1]
#                 ## Same color, push counts
#                 current_segments[op][color] += buff_count[op][color]
#                 current_segments[op][-1] = buff_count[op][-1]
#                 buff_count[op][color] = 1
#                 buff_count[op][-1] = val

#             else: ## buff_count[op][0]*buff_count[op][1] > 0:  ## AND val > current_segments[op][-1]
#                 ## Mixing in the previous value: save current segment and previous value separately and start new
#                 #print 'MIXING\nSegments: %s\n\nCurrent:%s\nBuffer:%s' % (segments, current_segments, buff_count)
# #                pdb.set_trace()
#                 if current_segments[op][0]+current_segments[op][1] > 0: ## if current segment is non empty (not two successive mixing), save
#                     col_new_seg = current_segments[op][1]>0
#                     ids_seg_clean[col_new_seg][op].append(len(segments[op]))
#                     if current_segments[op][col_new_seg] > max_clean[col_new_seg][op][0] :
#                         max_clean[col_new_seg][op] = [current_segments[op][col_new_seg], len(segments[op])]
#                     nb_seg[col_new_seg][op] += 1
#                     segments[op].append(current_segments[op])

#                 buff_count[op].append(buff_count[op][-1]) ## transform the buff in segment by setting end_val == start_val <- highest_val
#                 ratio = float(buff_count[op][1])/buff_count[op][0]
#                 ids_seg_mix[1*(ratio>1)+1*(ratio!=1)][op].append(len(segments[op]))
#                 if ratio > max_mix[1][op][0]:
#                     max_mix[1][op] = [ratio, len(segments[op])]
#                 if float(buff_count[op][0])/ buff_count[op][1] > max_mix[0][op][0]:
#                     max_mix[0][op] = [float(buff_count[op][0])/ buff_count[op][1], len(segments[op])]
#                 segments[op].append(buff_count[op])
#                 buff_count[op] = [1*(not color), 1*color, val]
#                 current_segments[op] = [0, 0, val, val]

#         for op in [False, True]:
#             if buff_count[op][0]*buff_count[op][1] > 0:
#                 ## Mixing in the last value: save current segment and last value separately
#                 if current_segments[op][0]+current_segments[op][1] > 0: ## if current segment is non empty (not two successive mixing), save
#                     col_new_seg = current_segments[op][1]>0
#                     ids_seg_clean[col_new_seg][op].append(len(segments[op]))
#                     if current_segments[op][col_new_seg] > max_clean[col_new_seg][op][0] :
#                         max_clean[col_new_seg][op] = [current_segments[op][col_new_seg], len(segments[op])]
#                     nb_seg[col_new_seg][op] += 1

#                 buff_count[op].append(buff_count[op][-1]) ## transform the buff in segment by setting end_val == start_val <- highest_val
#                 ratio = float(buff_count[op][1])/buff_count[op][0]
#                 ids_seg_mix[1*(ratio>1)+1*(ratio!=1)][op].append(len(segments[op]))
#                 if ratio > max_mix[1][op][0]:
#                     max_mix[1][op] = [ratio, len(segments[op])]
#                 if float(buff_count[op][0])/ buff_count[op][1] > max_mix[0][op][0]:
#                     max_mix[0][op] = [float(buff_count[op][0])/ buff_count[op][1], len(segments[op])]
#                 segments[op].append(buff_count[op])                
#             else:
#                 ## no mixing: push counts and save
#                 col_new_seg = buff_count[op][1]>0 # what's the color of the segment to add
#                 current_segments[op][col_new_seg] += buff_count[op][col_new_seg] # push counts from buffer
#                 current_segments[op][-1] = buff_count[op][-1] # push upper bound from buffer
#                 ids_seg_clean[col_new_seg][op].append(len(segments[op])) # record the id of the segment
#                 if current_segments[op][col_new_seg] > max_clean[col_new_seg][op] : # is it the best so far ?
#                     max_clean[col_new_seg][op] = [current_segments[op][col_new_seg], len(segments[op])]
#                 nb_seg[col_new_seg][op] += 1 # count segments (temporary double check)
#                 segments[op].append(current_segments[op]) # append to segments
                
#             ## pop the first segment: it is empty
#             nb_seg[segments[op][0][1]>0][op] -= 1
#             if 0 != ids_seg_clean[segments[op][0][1]>0][op].pop(0):
#                 pdb.set_trace()
#             segments[op].pop(0)
#             for color in [0,1]:
#                 j= -1
#                 for i in ids_seg_clean[0][op] :
#                     if i-j == 1:
#                         pdb.set_trace()
#                     j = i

#         print '--------------------------------'
#         print 'nb_seg: %ix%i, %s' % (len(segments[0]), len(segments[1]), nb_seg)
#         print 'ids_seg_clean(%ix%i + %ix%i)' % (len(ids_seg_clean[0][0]), len(ids_seg_clean[1][0]), len(ids_seg_clean[0][1]), len(ids_seg_clean[1][1]) ) 
#         print 'ids_seg_mix(%ix%ix%i + %ix%ix%i)' % (len(ids_seg_mix[0][0]), len(ids_seg_mix[1][0]), len(ids_seg_mix[2][0]),\
#                                                     len(ids_seg_mix[0][1]), len(ids_seg_mix[1][1]), len(ids_seg_mix[2][1]) ) 
#         print 'max_clean: %s, max_mix:%s' % (max_clean, max_mix)
# #        pdb.set_trace()        
#         return (segments, ids_seg_clean, ids_seg_mix, max_clean, max_mix)
#     makeSegments = staticmethod(makeSegments)
    
    def negateSegments(segments, negateL, negateR):
        ## vector_abcd alpha->0 gamma->1 delta->2 beta->3
        if negateL:
            segments = [segments[1], segments[0]]

        if negateR:
            for op in [0,1]:
                for seg in range(len(segments[op])):
                    segments[op][seg]=(segments[op][seg][1], segments[op][seg][0], segments[op][seg][2], segments[op][seg][3])
    negateSegments = staticmethod(negateSegments)

    def findCover(segments, lparts, side, col, ruleTypes):
        return NumDataM.newFindCover(segments, lparts, side, col, ruleTypes)
    findCover = staticmethod(findCover)
        

    def oldFindCover(segments, lparts, side, col, ruleTypes):
        res = []
        maxSeg = 250
        for op in ruleTypes.keys():
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
                        tmp_comp = DataM.makeBest((seg_s, seg_e), op, neg, toColors, lparts)
                        if BestsDraft.comparePair(tmp_comp, bests[neg]) > 0:
                            bests[neg] = tmp_comp
                                
            for neg in ruleTypes[op]:
                if bests[neg]['term'][0] != None:
                    lowb = segments[op][bests[neg]['term'][0]][-2]
                    upb = segments[op][bests[neg]['term'][1]][-1]
                    bests[neg].update({'side': side, 'op': Op(op), 'term': Term(neg, NumItem(col, lowb, upb))})
                    res.append(bests[neg])
        return res
    oldFindCover = staticmethod(oldFindCover)

    def newFindCover(segments, lparts, side, col, ruleTypes):

        res = []
        for op in ruleTypes.keys():
                
            #print 'INCR SEARCH:'
            toColors_f = [0,0]
            nb_seg_f = 0
            best_f = None
            toColors_b = [0,0]
            nb_seg_b = 0
            best_b = None 

            for  i in range(len(segments[op])):
                # FORWARD
                if i > 0 and (toColors_f[0] == 0 or DataM.compAcc(op, False, segments[op][i][:2], lparts) <  float(toColors_f[1])/float(toColors_f[0])):
                    toColors_f = [toColors_f[0] + segments[op][i][0], toColors_f[1] + segments[op][i][1]]
                    nb_seg_f += 1
                else: 
                    toColors_f = segments[op][i][:2]
                    nb_seg_f = 0
                tmp_comp_f = DataM.makeBest((i - nb_seg_f, i), op, False, toColors_f, lparts)
#                if tmp_comp_f != None and (best_f == None or tmp_comp_f['acc']> best_f['acc']):
                if BestsDraft.comparePair(tmp_comp_f, best_f) > 0:
                    best_f = tmp_comp_f

                # BACKWARD
                if i > 0 and (toColors_b[0] == 0 or  DataM.compAcc(op, False, segments[op][-(i+1)][:2], lparts) <  float(toColors_b[1])/float(toColors_b[0]) ):
                    toColors_b = [toColors_b[0] + segments[op][-(i+1)][0], toColors_b[1] + segments[op][-(i+1)][1]]
                    nb_seg_b += 1
                else:
                    toColors_b = segments[op][-(i+1)][:2]
                    nb_seg_b = 0
                tmp_comp_b = DataM.makeBest((len(segments[op])-(1+i), len(segments[op])-(1+i) + nb_seg_b), op, False, toColors_b, lparts)
                if BestsDraft.comparePair(tmp_comp_b, best_b) > 0:
#                if tmp_comp_b != None and (best_b == None or tmp_comp_b['acc']> best_b['acc']):
                    best_b = tmp_comp_b

            if best_b != None and best_f != None:
                bests = [best_b, best_f]

                if best_b['term'][0] > best_f['term'][0] and best_b['term'][1] > best_f['term'][1] and best_b['term'][0] <= best_f['term'][1]:
                    toColors_m = [0,0]
                    for seg in segments[op][best_b['term'][0]:best_f['term'][1]+1]:
                        toColors_m = [toColors_m[0] + seg[0], toColors_m[1] + seg[1]]

                    tmp_comp_m = DataM.makeBest((best_b['term'][0], best_f['term'][1]), op, False, toColors_m, lparts)
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

                lowb = segments[op][best['term'][0]][-2]
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
#                     if  DataM.compAcc(op, False, toColors, lparts) > best_full[0]:
#                         best_full = ( DataM.compAcc(op, False, toColors, lparts),\
#                                  '%i <-> %i: %i/%i, %f' % (seg_s, seg_e, toColors[1], toColors[0], DataM.compAcc(op, False, toColors, lparts)))
#             print best_full[1]
#             if best == None or best_full[0] != best['acc']:
#                 print 'FULL SEARCH GIVES DIFFERENT RESULT !'
            
        return res
    newFindCover = staticmethod(newFindCover)

    def computeCol(self, parts, side, col, ruleTypes):
#        pdb.set_trace()
        # if col == 19:
#             pdb.set_trace()
        if side==1:
            lparts = (len(parts[1]), len(parts[0]), len(parts[2]), len(parts[3]))
        else:
            lparts = (len(parts[0]), len(parts[1]), len(parts[2]), len(parts[3]))
        
        segments = NumDataM.makeSegments(parts[4], side, self.colSupps[col])
        #(segments, ids_seg_clean, ids_seg_mix, max_clean, max_mix) = NumDataM.makeSegments(parts[4], side, self.colSupps[col])
        #Data.log_fid.write('## Col (%i), %i + %i segments\n%s' % (col, len(segments[0]), len(segments[1]), NumDataM.dispSegments(segments)))
        #Data.log_fid.flush()
        ##print '## Col (%i), %i + %i segments' % (col, len(segments[0]), len(segments[1]))
        return NumDataM.findCover(segments, lparts, side, col, ruleTypes)

class Data:

    dataTypes = [{'class': NumDataM,  'match':'num$'}, \
                 {'class': CatDataM,  'match':'cat$'}, \
                 {'class': BoolDataM, 'match':'(dense)|(dat)|(sparse)$'}]
    minC = 1
    minS = 1
    log_fid = open('/tmp/workfile2', 'w')
    
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
                                
    def stats(self, side):
        return self.m[side].stats
        
    def __str__(self):
        return "Data %s and %s" % ( self.m[0], self.m[1])
   
    def setMinSC(self, s, c):
        if s>= 0 and s < 0.5 :
            minSupp = int(math.floor(s*self.N))
        elif s <1:
            minSupp = int(math.floor((1-s)*self.N))
        elif s < float(self.N)/2:
            minSupp = int(math.floor(s))
        elif s < self.N:
            minSupp = int(self.N - math.floor(s))
        else:
            minSupp = 0

        Data.minS = minSupp
                    
        if c >= 1:
            minC = int(c)
        elif c >= 0 and c < 1 :
            minC = int(math.floor(c*self.N))

        Data.minC = minC
        self.nf = [self.m[0].nonFull(), self.m[1].nonFull()]
                    
    def nonFull(self):
        return self.nf

    def updateBests(self, bests, parts, side, col, ruleTypes):
        bests.upBest(self.m[side].computeCol(parts, side, col,  ruleTypes))

    def computePairParts11(self, mA, idA, mB, idB, has_neg, vectors_abcd=[[],[]], side=1):
        c = float(len(mA.vect(idA) & mB.vect(idB)))
        a = float(len(mA.vect(idA) - mB.vect(idB)))
        b = float(len(mB.vect(idB) - mA.vect(idA)))
        ## Evaluate score for AB AbB ABb AbBb
        I = [ c, b, a, self.N-a-b-c]
        U = [ a+b+c, self.N-a, self.N-b, self.N-c]
        nA = [False, True, False, True]
        nB = [False, False, True, True]

        up_to = 1+ has_neg*3
        (suppI, suppU, rand, termsA, termsB) = ([], [], [], [], [])        
        for i in range(up_to):
            if I[i] >= Data.minC and (self.N - U[i]) >= Data.minS :
                suppI.append(I[i])
                suppU.append(U[i])
                rand.append(random.random())
                termsA.append(Term(nA[i], BoolItem(idA)))
                termsB.append(Term(nB[i], BoolItem(idB)))
            
        return (suppI, suppU, rand, termsA, termsB)

    def computePairParts12(self, mA, idA, mB, idB, has_neg, vectors_abcd, side=1):
        raise Exception('To be implemented !')
        return (suppI, suppU, rand, termsA, termsB)
    
    def computePairParts13(self, mA, idA, mB, idB, has_neg, vectors_abcd, side=1):
        return mB.fit(BoolItem(idA), mA.vect(idA), vectors_abcd[1-side][idA], idB, has_neg, side)
       
    def computePairParts21(self, mA, idA, mB, idB, has_neg, vectors_abcd, side=0):
        (suppI, suppU, rand, termsB, termsA)= self.computePairParts12(mB, idB, mA, idA, has_neg, vectors_abcd, side )
        return (suppI, suppU, rand, termsA, termsB)

    def computePairParts22(self, mA, idA, mB, idB, has_neg, vectors_abcd, side=1):
        raise Exception('To be implemented !')
        return (suppI, suppU, rand, termsA, termsB)

    def computePairParts23(self, mA, idA, mB, idB, has_neg, vectors_abcd, side=1):
        raise Exception('To be implemented !')
        return (suppI, suppU, rand, termsA, termsB)

    def computePairParts32(self, mA, idA, mB, idB, has_neg, vectors_abcd, side=0):
        (suppI, suppU, rand, termsB, termsA)= self.computePairParts23(mB, idB, mA, idA, has_neg, vectors_abcd, side )
        return (suppI, suppU, rand, termsA, termsB)

    def computePairParts31(self, mA, idA, mB, idB, has_neg, vectors_abcd, side=0):
        (suppI, suppU, rand, termsB, termsA)= self.computePairParts13(mB, idB, mA, idA, has_neg, vectors_abcd, side )
        return (suppI, suppU, rand, termsA, termsB)
    
    def computePairParts33(self, mA, idA, mB, idB, has_neg, vectors_abcd, side=1):
        raise Exception('To be implemented !')
        return (suppI, suppU, rand, termsA, termsB)
        
    def computePair(self, idA, idB, vectors_abcd=[[],[]], pairs=[], has_neg = True, scoreFormula='suppI[i]/suppU[i]'):
        method_string = 'self.computePairParts%i%i' % (self.m[0].type_id, self.m[1].type_id)
        try:
            method_compute =  eval(method_string)
        except AttributeError:
              raise Exception('Oups this combination does not exist (%i %i)!' % (self.m[0].type_id, self.m[1].type_id))

        (suppI, suppU, rand, termsA, termsB) = method_compute(self.m[0], idA, self.m[1], idB, has_neg, vectors_abcd)
        for i in range(len(suppI)):
            pairs.append((eval(scoreFormula), termsA[i], termsB[i]))
        return pairs
       

    def initializePairs(self, nbPairs, ruleTypes, scoreFormula='suppI[i]/suppU[i]'):
        pairs = []
        has_neg = False
        for i in ruleTypes.values():
            has_neg |= True in i

        ids_tmp= self.nonFull()
        ids = [ids_tmp[0][0::5], ids_tmp[1][0::5]]
        print 'generating %ix%i initials' % (len(ids[0]), len(ids[1]))

        vectors_abcd = [{},{}]
        for idA in ids[0]:
            vectors_abcd[0][idA] = Redescription.makeVectorABCD(self.m[1].type_id > 1, self.N, self.m[0].vect(idA), set(), set())
        for idB in ids[1]:
            vectors_abcd[1][idB] = Redescription.makeVectorABCD(self.m[0].type_id > 1, self.N, set(), self.m[1].vect(idB), set())

        for idA in ids[0]:
            for idB in ids[1]:
                self.computePair(idA, idB, vectors_abcd, pairs, has_neg, scoreFormula)

        pairs.sort(key=lambda x: x[0], reverse=True) 
        if len(pairs) > nbPairs:
            pairs = pairs[:nbPairs]
        return pairs

    def readInput(datafile):
        ## Read input

        format_f = datafile.split('.').pop()
        if format_f == 'dense':
            (colSuppsTmp, rowIdTmp) = utilsIO.readDense(datafile)
        elif format_f == 'dat':
            (colSuppsTmp, rowIdTmp) = utilsIO.readMatlab(datafile)
        elif format_f == 'sparse':
            (colSuppsTmp, rowIdTmp) = utilsIO.readSparse(datafile)
        elif format_f == 'num':
            (colSuppsTmp, rowIdTmp) = utilsIO.readNumerical(datafile)
        elif format_f == 'cat' :
            (colSuppsTmp, rowIdTmp) = utilsIO.readCategorical(datafile)
            
        dataType = None
        for i in range(len(Data.dataTypes)):
            if re.match(Data.dataTypes[i]['match'],format_f):
                dataType = i

        return (colSuppsTmp, rowIdTmp, dataType)
    readInput = staticmethod(readInput)
