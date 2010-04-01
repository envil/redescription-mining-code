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

    def makeBest(t, op, neg, toColors, lparts):
        b = None
        if op:
            if neg:
                if (lparts[1] - toColors[1] >= Data.minC) and ( toColors[0] >= Data.minS ):
                    b= {'acc': float(lparts[2] + lparts[1] - toColors[1])/(lparts[0] + lparts[1] + lparts[2] + lparts[3] - toColors[0]),\
                        'toRed': lparts[3] - toColors[0], 'toBlue': lparts[1] - toColors[1], 'term': t}

            else:
                if (toColors[1] >= Data.minC) and (lparts[3] + toColors[0] >= Data.minS ):
                    b= {'acc': float(lparts[2] + toColors[1])/(lparts[0] + lparts[1] + lparts[2] + toColors[0]),\
                        'toRed': toColors[0], 'toBlue': toColors[1], 'term': t}
        else:
            if neg:
                if (lparts[2] - toColors[1] >= Data.minC) and (lparts[2] - toColors[0] >= Data.minS ):
                    b= {'acc': float(lparts[2] - toColors[1])/(lparts[0] - toColors[0] + lparts[1] + lparts[2]),\
                        'toRed': lparts[0] - toColors[0], 'toBlue': lparts[2] - toColors[1], 'term': t}
            else:
                if (toColors[1] >= Data.minC) and (toColors[0] >= Data.minS ):
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
            typeRules = {True: [False, True]}
        else:
            typeRules = {True: [False]}
        
        if side==1:
            lparts = (len(suppX), 0, 0, len(self) - len(suppX))
        else:
            lparts = (0, len(suppX), 0, len(self) - len(suppX))

        segments = NumDataM.makeSegments(vector_abcd, side, self.colSupps[col])
        #Data.log_fid.write('## Pair (%i,%i), %i + %i segments\n%s' % (itemX.colId(), col, len(segments[0]), len(segments[1]), NumDataM.dispSegments(segments)))
        #Data.log_fid.flush()
        cand_A = NumDataM.findCover(segments, lparts, side, col, typeRules)
        (suppI, suppU, rand, termsA, termsB) = ([], [], [], [], [])

        for cand in cand_A:
            suppI.append(float(cand['toBlue']))
            suppU.append(float(cand['toRed'] + len(suppX)))
            rand.append(random.random())
            termsA.append(Term(False, itemX))
            termsB.append(cand['term'])

        if has_neg and len(cand_A) > 0:
            NumDataM.negateSegments(segments, side == 1, side == 0)
            cand_Ab = NumDataM.findCover(segments, lparts, typeRules)

            for cand in cand_Ab:
                suppI.append(float(cand['toBlue']))
                suppU.append(float(cand['toRed'] + len(suppX)))
                rand.append(random.random())
                termsA.append(Term(True, itemX))
                termsB.append(cand['term'])
        return (suppI, suppU, rand, termsA, termsB)

    def dispSegments(segments):
        message = ''
#         for op in [True, False]:
#             message += '## operator: %s\n' % op
#             for segment in segments[op]:
#                 message += '%i\t%i\t%f\t%f\n' % (segment[0], segment[1], segment[2], segment[3])
        return message
    dispSegments = staticmethod(dispSegments)
            
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
        current_segments = [[0,0, None, None],[0,0, None, None]]
        ## buff: [count_red_current_val, count_blue_current_val, highest_val]
        buff_count = [[0,0, None],[0,0, None]]
        for (val, row) in vectCol:
            op = vector_abcd[row] in OR
            color = vector_abcd[row] in BLUE

            if val == buff_count[op][-1]:
                buff_count[op][color] += 1

            elif buff_count[op][color] == 0:  ## AND val > current_segments[op][-1]
                ## Other color encontered, no mixing: push counts, save and start new 
                #print 'NO MIXING\nSegments: %s\n\nCurrent:%s\nBuffer:%s' % (segments, current_segments, buff_count)
                current_segments[op][not color] += buff_count[op][not color]
                current_segments[op][-1] = buff_count[op][-1]
                segments[op].append(current_segments[op])
                buff_count[op] = [1*(not color), 1*color, val]
                current_segments[op] = [0, 0, val, val]

            elif buff_count[op][not color] == 0 : ## AND val > current_segments[op][-1]
                ## Same color, push counts
                current_segments[op][color] += buff_count[op][color]
                current_segments[op][-1] = buff_count[op][-1]
                buff_count[op][color] = 1
                buff_count[op][-1] = val

            else: ## buff_count[op][0]*buff_count[op][1] > 0:  ## AND val > current_segments[op][-1]
                ## Mixing in the previous value: save current segment and previous value separately and start new
                #print 'MIXING\nSegments: %s\n\nCurrent:%s\nBuffer:%s' % (segments, current_segments, buff_count)
                if current_segments[op][0]+current_segments[op][1] > 0: ## if current segment is non empty (not two successive mixing), save
                    segments[op].append(current_segments[op])
                buff_count[op].append(buff_count[op][-1]) ## transform the buff in segment by setting end_val == start_val <- highest_val
                segments[op].append(buff_count[op])
                buff_count[op] = [1*(not color), 1*color, val]
                current_segments[op] = [0, 0, val, val]

        for op in [False, True]:
            if buff_count[op][0]*buff_count[op][1] > 0:
                ## Mixing in the last value: save current segment and last value separately
                if current_segments[op][0]+current_segments[op][1] > 0:  ## if current segment is non empty (not two successive mixing), save 
                    segments[op].append(current_segments[op])
                buff_count[op].append(buff_count[op][-1]) ## transform the buff in segment by setting end_val == start_val <- highest_val
                segments[op].append(buff_count[op])
                
            else:
                ## no mixing: push counts and save
                current_segments[op][not color] += buff_count[op][not color]
                current_segments[op][-1] = buff_count[op][-1]
                segments[op].append(current_segments[op])

            ## pop the first segment: it is empty
            segments[op].pop(0)
        return segments
    makeSegments = staticmethod(makeSegments)
    
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
    findCover = staticmethod(findCover)

    def computeCol(self, parts, side, col, ruleTypes):
        # if col == 19:
#             pdb.set_trace()
        if side==1:
            lparts = (len(parts[1]), len(parts[0]), len(parts[2]), len(parts[3]))
        else:
            lparts = (len(parts[0]), len(parts[1]), len(parts[2]), len(parts[3]))
        
        segments = NumDataM.makeSegments(parts[4], side, self.colSupps[col])
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

#         vectors_abcd = [{},{}]
#         ids = [(161, 35), (129, 42), (176, 7), (15, 21)]
#         for (idA, idB) in ids:
#             vectors_abcd[0][idA] = Redescription.makeVectorABCD(self.m[1].type_id > 1, self.N, self.m[0].vect(idA), set(), set())
#             vectors_abcd[1][idB] = Redescription.makeVectorABCD(self.m[0].type_id > 1, self.N, set(), self.m[1].vect(idB), set())
#             self.computePair(idA, idB, vectors_abcd, pairs, has_neg, scoreFormula)

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
