from classExtension import Extension
from classInitialPairs import *
from classSParts import SParts
from classQuery import  *
import pdb

class Charbon:

    def __init__(self, constraints):
        self.constraints = constraints

    def getCandidates(self, side, col, supports, init=0):
        method_string = 'self.getCandidates%i' % col.type_id
        try:
            method_compute =  eval(method_string)
        except AttributeError:
              raise Exception('Oups No candidates method for this type of data (%i)!'  % col.type_id)
        return method_compute(side, col, supports, init)

    def getCandidates1(self, side, col, supports, init=0):
        cands = []
        lparts = supports.lparts()
        lmiss = supports.lpartsInterX(col.missing)
        lin = supports.lpartsInterX(col.hold)

        for op in self.constraints.ops_query(side, init):
            for neg in self.constraints.neg_query(side):
                adv, clp = self.getAC(side, op, neg, lparts, lmiss, lin)
                if adv is not None :
                    cands.append(Extension(adv, clp, (side, op, Literal(neg, BoolTerm(col.getId())))))
        return cands

    def getCandidates2(self, side, col, supports, init=0):
        return self.getCandidatesNonBool(side, col, supports, init)

    def getCandidates3(self, side, col, supports, init=0):
        return self.getCandidatesNonBool(side, col, supports, init)

    def getCandidatesNonBool(self, side, col, supports, init=0):
        cands = []
        lparts = supports.lparts()
        lmiss = supports.lpartsInterX(col.miss())

        for cand in self.findCover(side, col, lparts, lmiss, supports, init):
            cands.append(cand[1])
        return cands

####################### COVER METHODS
    def findCover(self, side, col, lparts, lmiss, supports, init=0):
        method_string = 'self.findCover%i' % col.type_id
        try:
            method_compute =  eval(method_string)
        except AttributeError:
              raise Exception('Oups No covering method for this type of data (%i)!'  % col.type_id)
        return method_compute(side, col, lparts, lmiss, supports, init)

    def findCover1(self, side, col, lparts, lmiss, supports, init=0):
        cands = []
        best = (None, None, None)
        bestNeg = (None, None, None)

        lin = supports.lpartsInterX(col.supp())
        for op in self.constraints.ops_query(side, init):            
            for neg in self.constraints.neg_query(side):        
                best = self.updateACT(best, Literal(neg, BoolTerm(col.getId())), side, op, neg, lparts, lmiss, lin)

                ### to negate the other side when looking for initial pairs
                if init == 1 and True in self.constraints.neg_query(side):
                    bestNeg = self.updateACT(bestNeg, Literal(neg, BoolTerm(col.getId())), side, op, neg, \
                                          SParts.negateParts(1-side, lparts), SParts.negateParts(1-side, lmiss), SParts.negateParts(1-side, lin))

                if best[0] is not None:
                    cands.append((False, Extension(best)))
                if bestNeg[0] is not None:
                    cands.append((True, Extension(bestNeg)))
        return cands

    def findCover2(self, side, col, lparts, lmiss, supports, init=0):
        cands = []
        best = (None, None, None)
        bestNeg = (None, None, None)

        for op in self.constraints.ops_query(side, init):            
            for neg in self.constraints.neg_query(side):        
                best = Extension(); bestNeg = Extension()
                for (cat, supp) in col.sCats.iteritems():
                    lin = supports.lpartsInterX(supp)
                    best = self.updateACT(best, Literal(neg, CatTerm(col.getId(), cat)), side, op, neg, lparts, lmiss, lin)

                    ### to negate the other side when looking for initial pairs
                    if init ==1 and True in self.constraints.neg_query(side):
                        bestNeg = self.updateACT(bestNeg, Literal(neg, CatTerm(col.getId(), cat)), side, op, neg, \
                                              SParts.negateParts(1-side, lparts), SParts.negateParts(1-side, lmiss), SParts.negateParts(1-side, lin))

                if best[0] is not None:
                    cands.append((False, Extension(best)))
                if bestNeg[0] is not None:
                    cands.append((True, Extension(bestNeg)))
        return cands

    def findCover3(self, side, col, lparts, lmiss, supports, init=0):
        cands = []
        
        if self.inSuppBounds(side, True, lparts) or self.inSuppBounds(side, False, lparts):  ### DOABLE
            segments = col.makeSegments(side, supports, self.constraints.ops_query(side, init))
            for cand in self.findCoverSegments(side, col, segments, lparts, lmiss, init):
                cands.append((False, cand))

            ### to negate the other side when looking for initial pairs
            if init == 1 and True in self.constraints.neg_query(side):
                nlparts = SParts.negateParts(1-side, lparts)
                nlmiss = SParts.negateParts(1-side, lmiss)

                if self.inSuppBounds(side, True, nlparts): ### DOABLE
                    nsegments = col.makeSegments(side, supports.negate(1-side), self.constraints.ops_query(side, init))
                    ##H pdb.set_trace()
                    for cand in self.findCoverSegments(side, col, nsegments, nlparts, nlmiss, init):
                        cands.append((True, cand))
        return cands
        
    def findCoverSegments(self, side, col, segments, lparts, lmiss, init=0):
        cands = []
        for op in self.constraints.ops_query(side, init):
            if len(segments[op]) < self.constraints.max_seg():
                cands.extend(self.findCoverFullSearch(side, op, col, segments, lparts, lmiss))
            else:
                if (False in self.constraints.neg_query(side)):
                    cands.extend(self.findPositiveCover(side, op, col, segments, lparts, lmiss))
                if (True in self.constraints.neg_query(side)):
                    cands.extend(self.findNegativeCover(side, op, col, segments, lparts, lmiss))
        return cands

    def findCoverFullSearch(self, side, op, col, segments, lparts, lmiss):
        cands = []
        bests = {False: (None, None, None), True: (None, None, None)}

        for seg_s in range(len(segments[op])):
            lin = SParts.makeLParts()
            for seg_e in range(seg_s,len(segments[op])):
                lin = SParts.addition(lin, segments[op][seg_e][2])
                for neg in self.constraints.neg_query(side):
                    bests[neg] = self.updateACT(bests[neg], (seg_s, seg_e), side, op, neg, lparts, lmiss, lin)

        for neg in self.constraints.neg_query(side):
            if bests[neg][0]:
                bests[neg][-1][-1] = col.getLiteralSeg(neg, segments[op], bests[neg][-1][-1])
                if bests[neg][-1][-1] is not None:
                    cands.append(Extension(bests[neg]))
        return cands

    def findNegativeCover(self, side, op, col, segments, lparts, lmiss):
        cands = []
        lin_f = SParts.makeLParts()
        bests_f = [(SParts.advAcc(side, op, False, lparts, lmiss, lin_f), 0, lin_f)] 
        best_track_f = [0]
        lin_b = SParts.makeLParts()
        bests_b = [(SParts.advAcc(side, op, False, lparts, lmiss, lin_b), 0, lin_f)]
        best_track_b = [0]

        for  i in range(len(segments[op])):
            # FORWARD
            lin_f = SParts.addition(lin_f, segments[op][i][2])
            if  SParts.advRatioVar(side, op, lin_f) > bests_f[-1][0]:
                lin_f = SParts.addition(lin_f, bests_f[-1][2])
                bests_f.append((SParts.advAcc(side, op, False, lparts, lmiss, lin_f), i+1, lin_f))
                lin_f = SParts.makeLParts()
            best_track_f.append(len(bests_f)-1)

            # BACKWARD
            lin_b = SParts.addition(lin_b, segments[op][-(i+1)][2])
            if  SParts.advRatioVar(side, op, lin_b) > bests_b[-1][0]:
                lin_b = SParts.addition(lin_b, bests_b[-1][2])
                bests_b.append((SParts.advAcc(side, op, False, lparts, lmiss, lin_b), i+1, lin_b))
                lin_b = SParts.makeLParts()
            best_track_b.append(len(bests_b)-1)

        best_t = (None, None, None)
        for b in bests_b:
            if b[1] == len(segments[op]):
                f = bests_f[0]
            else:
                f = bests_f[best_track_f[len(segments[op])-(b[1]+1)]]
            if SParts.advRatioVar(side, op, f[2]) > b[0]:
                best_t = self.updateACT(best_t, (f[1], len(segments[op]) - (b[1]+1)), side, op, False, lparts, lmiss, SParts.addition(f[2], b[2]))
            else:
                best_t = self.updateACT(best_t, (0, len(segments[op]) - (b[1]+1)), side, op, False, lparts, lmiss, b[2])

        for f in bests_f:
            if f[1] == len(segments[op]):
                b = bests_b[0]
            else:
                b = bests_b[best_track_b[len(segments[op])-(f[1]+1)]]
            if SParts.advRatioVar(side, op, b[2]) > f[0]: 
                best_t = self.updateACT(best_t, (f[1], len(segments[op]) - (b[1]+1)), side, op, False, lparts, lmiss, SParts.addition(f[2], b[2]))
            else:
                best_t = self.updateACT(best_t, (f[1], len(segments)-1), side, op, False, lparts, lmiss, f[2])

        if best_t[0] is not None:
            best_t[-1][-1] = col.getLiteralSeg(True, segments[op], best_t[-1][-1])
            if best_t[-1][-1] is not None:
                cands.append(Extension(best_t))
        return cands

    def findPositiveCover(self, side, op, col, segments, lparts, lmiss):
        cands = []
        lin_f = SParts.makeLParts()
        nb_seg_f = 0
        best_f = (None, None, None)
        lin_b = SParts.makeLParts()
        nb_seg_b = 0
        best_b = (None, None, None)

        for  i in range(len(segments[op])-1):
            # FORWARD
            if i > 0 and \
                   SParts.advAcc(side, op, False, lparts, lmiss, segments[op][i][2]) < SParts.advRatioVar(side, op, lin_f):
                lin_f = SParts.addition(lin_f, segments[op][i][2])
                nb_seg_f += 1
            else: 
                lin_f = segments[op][i][2]
                nb_seg_f = 0
            best_f = self.updateACT(best_f, (i - nb_seg_f, i), side, op, False, lparts, lmiss, lin_f)

            # BACKWARD
            if i > 0 and \
               SParts.advAcc(side, op, False, lparts, lmiss, segments[op][-(i+1)][2]) < SParts.advRatioVar(side, op, lin_b):
                lin_b = SParts.addition(lin_b, segments[op][-(i+1)][2])
                nb_seg_b += 1
            else:
                lin_b = segments[op][-(i+1)][2]
                nb_seg_b = 0
                best_f = self.updateACT(best_f, (i - nb_seg_f, i), side, op, False, lparts, lmiss, lin_f)
            best_b = self.updateACT(best_b, (len(segments[op])-(1+i), len(segments[op])-(1+i) + nb_seg_b), \
                                    side, op, False, lparts, lmiss, lin_b)

        if best_b[0] is not None and best_f[0] is not None:
            bests = [best_b, best_f]

            if best_b[-1][-1][0] > best_f[-1][-1][0] and best_b[-1][-1][1] > best_f[-1][-1][1] and best_b[-1][-1][0] <= best_f[-1][-1][1]:
                lin_m = SParts.makeLParts()
                for seg in segments[op][best_b[-1][-1][0]:best_f[-1][-1][1]+1]:
                    lin_m = SParts.addition(lin_m, seg[2])
                tmp_adv_m, tmp_clp_m  = self.getAC(side, op, False, lparts, lmiss, lin_m)
                if tmp_adv_m is not None:
                    bests.append((tmp_adv_m, tmp_clp_m, [side, op, (best_b[-1][-1][0], best_f[-1][-1][1])]))

            bests.sort()
            best = bests[-1]
            
        elif not best_f[0] is not None:
            best = best_f
        else:
            best = best_b

        if best[0] is not None:
            best[-1][-1] = col.getLiteralSeg(False, segments[op], best[-1][-1])
            if best[-1][-1] is not None:
                cands.append(Extension(best))
        return cands

################################################################### PAIRS METHODS
###################################################################

    def computePair(self, colL, colR):
        min_type = min(colL.type_id, colR.type_id)
        max_type = max(colL.type_id, colR.type_id)
        method_string = 'self.do%i%i' % (min_type, max_type)
        try:
            method_compute =  eval(method_string)
        except AttributeError:
              raise Exception('Oups this combination does not exist (%i %i)!'  % (min_type, max_type))
        if colL.type_id == min_type:
            (scores, literalsL, literalsR) = method_compute(colL, colR, 1)
        else:
            (scores, literalsR, literalsL) =  method_compute(colL, colR, 0)
        return (scores, literalsL, literalsR)

    def doBoolStar(self, colL, colR, side):
        if side == 1:
            (supports, fixTerm, extCol) = (SParts(colL.nbRows(), [colL.supp(), set(), colL.miss(), set()]), BoolTerm(colL.getId()), colR)
        else:
            (supports, fixTerm, extCol) = (SParts(colL.nbRows(), [set(), colR.supp(), set(), colR.miss()]), BoolTerm(colR.getId()), colL)

        return self.fit(extCol, supports, side, fixTerm)

    def fit(self, col, supports, side, termX):
        (scores, literalsFix, literalsExt) = ([], [], [])   
        lparts = supports.lparts()
        lmiss = supports.lpartsInterX(col.miss())
        cands = self.findCover(side, col, lparts, lmiss, supports, init=1)
        for cand in cands:
            scores.append(cand[1].getAcc())
            literalsFix.append(Literal(cand[0], termX))
            literalsExt.append(cand[1].getLiteral())
        return (scores, literalsFix, literalsExt)

    def do11(self, colL, colR, side):
        return self.doBoolStar(colL, colR, side)

    def do12(self, colL, colR, side):
        return self.doBoolStar(colL, colR, side)
        
    def do13(self, colL, colR, side):
        return self.doBoolStar(colL, colR, side)
        
    def do22(self, colL, colR, side):
        return self.subdo22Full(colL, colR, side)

    def do23(self, colL, colR, side):
        return self.subdo23Full(colL, colR, side)
    
    def do33(self, colL, colR, side):
#         if len(init_info[1-side]) == 3: # fit FULL
#             if len(init_info[1-side][0]) > len(init_info[side][0]): 
#                 (scores, literalsB, literalsA)= self.subdo33Full(colL, colR, side)
#                 return (scores, literalsA, literalsB)
#             else:
#                 return self.subdo33Full(colL, colR, side)
#         else:
#             return self.subdo33Heur(colL, colR, side)
        if len(colL.interNonMode(colR.nonModeSupp())) >= self.constraints.min_itm_in() :
            return self.subdo33Full(colL, colR, side)
        else:
            return ([], [], [])
    
    def subdo33Heur(self, colL, colR, side):
        ### Suitable for sparse data
        bestScore = None
        if True: ### DOABLE
            ## FIT LHS then RHS
            supports = SParts(colL.nbRows(), [set(), colR.nonModeSupp(), set(), colR.miss()])
            (scoresL, literalsFixL, literalsExtL) = self.fit(colL, supports, 0, idR)
            for tL in literalsExtL:
                suppL = colL.suppLiteral(tL)
                supports = SParts(colL.nbRows(), [suppL, set(), colL.miss(), set()])
                (scoresR, literalsFixR, literalsExtR) = self.fit(colR, supports, 1, tL)
                for i in range(len(scoresR)):
                    if scoresR[i] > bestScore:
                        (scores, literalsL, literalsR) = ([scoresR[i]], [literalsFixR[i]], [literalsExtR[i]])
                        bestScore = scoresR[i]
                        
            ## FIT RHS then LHS
            supports = SParts(colL.nbRows(), [colL.nonModeSupp(), set(), colL.miss(), set()])
            (scoresR, literalsFixR, literalsExtR) = self.fit(colR, supports, 1, idL)
            for tR in literalsExtR:
                suppR = colR.suppLiteral(tR)
                supports = SParts(colL.nbRows(), [set(), suppR, set(), colR.miss()])
                (scoresL, literalsFixL, literalsExtL) = self.fit(colL, supports, 0, tR)
                for i in range(len(scoresL)):
                    if scoresL[i] > bestScore:
                        (scores, literalsL, literalsR) = ([scoresR[i]], [literalsExtL[i]], [literalsFixL[i]])
                        bestScore = scoresL[i]
                        
#             if len(scores) > 0:
#                print "%f: %s <-> %s" % (scores[0], literalsA[0], literalsB[0])
        return (scores, literalsL, literalsR)

    def subdo33Full(self, colL, colR, side):
        best = (None, None, None)
        flag=0
        interMat = []
        bucketsL = colL.buckets()
        bucketsR = colR.buckets()

        if len(bucketsL[0]) > len(bucketsR[0]):
            bucketsF = bucketsR; colF = colR; bucketsE = bucketsL; colE = colL; side = 1-side; flip_side = True
        else:
            bucketsF = bucketsL; colF = colL; bucketsE = bucketsR; colE = colR; flip_side = False
            
        (scores, literalsF, literalsE) = ([], [], [])
        ## DOABLE

        # print "Nb buckets: %i x %i"% (len(bucketsF[1]), len(bucketsE[1]))
        if ( len(bucketsF[1]) * len(bucketsE[1]) > self.constraints.max_prodbuckets() ): 
            if len(bucketsE[1])> self.constraints.max_sidebuckets():
                bucketsE = colE.collapsedBuckets(self.constraints.max_agg())
                #pdb.set_trace()
                flag=1 ## in case of collapsed bucket the threshold is different
        if ( len(bucketsF[1]) * len(bucketsE[1]) <= self.constraints.max_prodbuckets() ): 
        #if (True): ## Test
            partsMubB = len(colF.miss())
            missMubB = len(colF.miss() & colE.miss())
            totInt = colE.nbRows() - len(colF.miss()) - len(colE.miss()) + missMubB
            #margE = [len(intE) for intE in bucketsE[0]]
            
            lmissFinE = [len(colF.miss() & bukE) for bukE in bucketsE[0]]
            lmissEinF = [len(colE.miss() & bukF) for bukF in bucketsF[0]]
            margF = [len(bucketsF[0][i]) - lmissEinF[i] for i in range(len(bucketsF[0]))]
            totMissE = len(colE.miss())
            totMissEinF = sum(lmissEinF)
            
            for bukF in bucketsF[0]: 
                interMat.append([len(bukF & bukE) for bukE in bucketsE[0]])
            
            if bucketsF[2] is not None :
                margF[bucketsF[2]] += colF.lenMode()
                for bukEId in range(len(bucketsE[0])):
                    interMat[bucketsF[2]][bukEId] += len(colF.interMode(bucketsE[0][bukEId])) 

            if bucketsE[2] is not None :
                #margE[bucketsE[2]] += colE.lenMode()
                for bukFId in range(len(bucketsF[0])):
                    interMat[bukFId][bucketsE[2]] += len(colE.interMode(bucketsF[0][bukFId]))        

            if bucketsF[2] is not None and bucketsE[2] is not None:
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

#             if totE != totF or totE != colE.nbRows():
#                 raise Error('Error in computing the marginals (3)')


            belowF = 0
            lowF = 0
            while lowF < len(interMat) and totInt - belowF >= self.constraints.min_itm_in():

                aboveF = 0
                upF = len(interMat)-1
                while upF >= lowF and totInt - belowF - aboveF >= self.constraints.min_itm_in():
                    if belowF + aboveF  >= self.constraints.min_itm_out():
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
                        while lowE < len(interMat[lowF]) and totInt - belowF - aboveF - belowEF >= self.constraints.min_itm_in():
                            aboveEF = 0
                            outAboveEF = 0
                            upE = len(interMat[lowF])-1
                            while upE >= lowE and totInt - belowF - aboveF - belowEF - aboveEF >= self.constraints.min_itm_in():
                                
                                lmissF = sum(lmissFinE[lowE:upE+1])
                                lin = SParts.makeLParts([(SParts.partId(SParts.alpha, 1-side), totInt - belowF - aboveF - belowEF - aboveEF), \
                                                         (SParts.partId(SParts.mubB, 1-side), lmissF ), \
                                                         (SParts.partId(SParts.delta, 1-side), belowF + aboveF - outAboveEF - outBelowEF)], 0)

                                best = self.updateACT(best, (lowF, upF, lowE, upE), side, True, False, lparts, lmiss, lin)
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

        if best[0]:
            tF = colF.getLiteralBuk(False, bucketsF[1], best[-1][-1][0:2])
            tE = colE.getLiteralBuk(False, bucketsE[1], best[-1][-1][2:],flag)
            if tF is not None and tE is not None:
                literalsF.append(tF)
                literalsE.append(tE)
                scores.append(best[0][0])

        if flip_side:
            return (scores, literalsE, literalsF)
        else:
            return (scores, literalsF, literalsE)

    def subdo22Full(self, colL, colR, side):
        configs = [(0, False, False), (1, False, True), (2, True, False), (3, True, True)]
        if neg in self.constraints.neg_query(side):
            configs = configs[:1]
        best = [(None, None, None) for c in configs]
        
        for catL in colL.cats():
            ### TODO DOABLE
            supports = SParts(colL.nbRows(), [colL.suppCat(catL), set(), colL.miss(), set()])
            lparts = supports.lparts()
            lmiss = supports.lpartsInterX(colR.miss())
            
            for catR in colR.cats():
                lin = supports.lpartsInterX(colR.suppCat(catR))

                for (i, nL, nR) in configs:
                    if nL:
                        tmp_lparts = SParts.negateParts(0, lparts)
                        tmp_lmiss = SParts.negateParts(0, lmiss)
                        tmp_lin = SParts.negateParts(0, lin)
                    else:
                        tmp_lparts = lparts
                        tmp_lmiss = lmiss
                        tmp_lin = lin

                    best[i] = self.updateACT(best[i], (catL, catR), side, True, nR, tmp_lparts, tmp_lmiss, tmp_lin)
                    
        (scores, literalsFix, literalsExt) = ([], [], [])
        for (i, nL, nR) in configs:
            if best[i][0] is not None:
                scores.append(best[i][0][0])
                literalsFix.append(Literal(nL, CatTerm(colL.getId(), best[i][-1][-1][0])))
                literalsExt.append(Literal(nR, CatTerm(colR.getId(), best[i][-1][-1][1])))
        return (scores, literalsFix, literalsExt)


    def subdo23Full(self, colL, colR, side):
        if side == 0:
            (colF, colE) = (colR, colL)
        else:
            (colF, colE) = (colL, colR)

        configs = [(0, False, False), (1, False, True), (2, True, False), (3, True, True)]
        if neg in self.constraints.neg_query(side):
            configs = configs[:1]
        best = [(None, None, None) for c in configs]

        buckets = colE.buckets()
        ### TODO DOABLE
        if True : # (colF.lenMode() >= self.constraints.min_itm_out() and colE.lenNonMode() >= self.constraints.min_itm_in()) or ( len(buckets) <= 100 ):
            partsMubB = len(colF.miss())
            missMubB = len(colF.miss() & colE.miss())
            
            missMat = [len(colF.miss() & buk) for buk in buckets[0]]
            totMiss = sum(missMat)

            marg = [len(buk) for buk in buckets[0]]
            if buckets[2] is not None :
                marg[buckets[2]] += colE.lenMode()

            for cat in colF.cats():
                lparts = SParts.makeLParts([(SParts.alpha, len(colF.suppCat(cat)) ), (SParts.mubB, partsMubB ), (SParts.delta, - colF.nbRows())], 1-side)
                lmiss  = SParts.makeLParts([(SParts.alpha, len(colF.suppCat(cat) & colE.miss()) ), (SParts.mubB, missMubB ), (SParts.delta, -len(colE.miss()) )], 1-side)
                
                interMat = [len(colF.suppCat(cat) & buk) for buk in buckets[0]]
                if buckets[2] is not None :
                    interMat[buckets[2]] += len(colE.interMode(colF.suppCat(cat)))        

                totIn = sum(interMat) 
                below = 0
                missBelow = 0
                low = 0
                while low < len(interMat) and \
                          (totIn - below >= self.constraints.min_itm_in() or totIn - below >= self.constraints.min_itm_out()):
                    above = 0
                    missAbove = 0
                    up = len(interMat)-1
                    while up >= low and \
                          (totIn - below - above >= self.constraints.min_itm_in() or totIn - below - above >= self.constraints.min_itm_out()):
                        lin = SParts.makeLParts([(SParts.alpha, totIn - below - above), (SParts.mubB, totMiss - missBelow - missAbove ), (SParts.delta, -sum(marg[low:up+1]))], 1-side)
                        for (i, nF, nE) in configs:
                            if nF:
                                tmp_lparts = SParts.negateParts(1-side, lparts)
                                tmp_lmiss = SParts.negateParts(1-side, lmiss)
                                tmp_lin = SParts.negateParts(1-side, lin)
                            else:
                                tmp_lparts = lparts
                                tmp_lmiss = lmiss
                                tmp_lin = lin

                            best[i] = self.updateACT(best[i], (cat, low, up), side, True, nE, tmp_lparts, tmp_lmiss, tmp_lin)

                        above+=interMat[up]
                        missAbove+=missMat[up]
                        up-=1
                    below+=interMat[low]
                    missBelow+=missMat[low]
                    low+=1

        
        (scores, literalsFix, literalsExt) = ([], [], [])
        for (i, nF, nE) in configs:

            if best[i][0] is not None:
                tE = colE.getLiteralBuk(nE, buckets[1], idE, best[i][-1][-1][1:],flag)
                if tE is not None:
                    literalsExt.append(tE)
                    literalsFix.append(Literal(nF, CatTerm(idF, best[i][-1][-1][0])))
                    scores.append(best[i][0][0])
        return (scores, literalsFix, literalsExt)

##### TOOLS METHODS
    # compute the advance resulting of appending X on given side with given operator and negation
    # from intersections of X with parts (clp)            
    def getAC(self, side, op, neg, lparts, lmiss, lin):
        lout = [lparts[i] - lmiss[i] - lin[i] for i in range(len(lparts))]
        clp = (lin, lout, lparts, lmiss)
        contri = SParts.sumPartsIdInOut(side, neg, SParts.IDS_cont[op], clp)
        if contri >= self.constraints.min_itm_c():
            varBlue = SParts.sumPartsIdInOut(side, neg, SParts.IDS_varnum[op], clp)
            fixBlue = SParts.sumPartsIdInOut(side, neg, SParts.IDS_fixnum[op], clp)
            if varBlue+fixBlue >= self.constraints.min_itm_in():
                sout = SParts.sumPartsIdInOut(side, neg, SParts.IDS_out[op], clp)
                if sout >= self.constraints.min_itm_out():
                    varRed = SParts.sumPartsIdInOut(side, neg, SParts.IDS_varden[op], clp)
                    fixRed = SParts.sumPartsIdInOut(side, neg, SParts.IDS_fixden[op], clp)
                    if varRed + fixRed == 0:
                        if varBlue + fixBlue > 0:
                            acc = float("Inf")
                        else:
                            acc = 0
                    else:
                        acc = float(varBlue + fixBlue)/ (varRed + fixRed)
                    return (acc, varBlue, varRed, contri, fixBlue, fixRed), clp
        return None, clp

    def updateACT(self, best, lit, side, op, neg, lparts, lmiss, lin):
        tmp_adv = self.getAC(side, op, neg, lparts, lmiss, lin)
        if best[0] < tmp_adv[0]:
            return tmp_adv[0], tmp_adv[1], [side, op, lit]
        else:
            return best
        ### EX: best = self.updateACT(best, Literal(neg, BoolTerm(col.getId())), side, op, neg, lparts, lmiss, lin, col.nbRows())

    def inSuppBounds(self, side, op, lparts):
        return SParts.sumPartsId(side, SParts.IDS_varnum[op] + SParts.IDS_fixnum[op], lparts) >= self.constraints.min_itm_in() \
               and SParts.sumPartsId(side, SParts.IDS_cont[op], lparts) >= self.constraints.min_itm_c()
