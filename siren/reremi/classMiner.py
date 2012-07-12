import datetime
from toolLog import Log
from classData import Data
from classRedescription import Redescription
from classExtension import Extension
from classBatch import Batch
from classExtensionsBatch import ExtensionsBatch
from classSouvenirs import Souvenirs
from classConstraints import Constraints
from classInitialPairs import *
from classSParts import SParts
from classQuery import  *
import pdb

class Miner:

### INITIALIZATION
##################
    def __init__(self, data, setts, logger, mid=None, souvenirs=None):
        if mid != None:
            self.id = mid
        else:
            self.id = 1
        self.data = data
        self.logger = logger
        self.constraints = Constraints(self.data.nbRows(), setts)
        if souvenirs == None:
            self.souvenirs = Souvenirs(self.data.usableIds(self.constraints.min_itm_c(), self.constraints.min_itm_c()), self.constraints.amnesic())
        else:
            self.souvenirs = souvenirs
        self.want_to_live = True

        try:
            self.initial_pairs = eval('IP%s()' % (self.constraints.pair_sel()))
        except AttributeError:
            raise Exception('Oups this selection method does not exist !')

        self.partial = {"results":[], "batch": Batch()}
        self.final = {"results":[], "batch": Batch()}


    def kill(self):
        self.want_to_live = False

### RUN FUNCTIONS
################################
### TODO improve progress tracking
    def part_run(self, redesc):
        self.count = "C"
        
        ticE = datetime.datetime.now()
        self.logger.printL(1,"Start part run %s" % ticE, "time", self.id)
        self.logger.printL(1, (100, 0), 'progress', self.id)
        self.logger.printL(1, "Expanding...", 'status', self.id) ### todo ID

        self.expandRedescriptions([redesc])

        tacE = datetime.datetime.now()
        self.logger.printL(1,"End part run %s, elapsed %s (%s)" % (tacE, tacE-ticE, self.want_to_live), "time", self.id)
        if not self.want_to_live:
            self.logger.printL(1, 'Interrupted...', 'status', self.id)
        else:
            self.logger.printL(1, 'Done...', 'status', self.id)


        self.logger.printL(1, None, 'progress', self.id)
        return self.partial

    def full_run(self):
        self.final["results"] = []
        self.final["batch"].reset()
        self.count = 0
        
        self.logger.printL(1, (100, 0), 'progress', self.id)
        self.logger.printL(1, "Starting mining", 'status', self.id) ### todo ID
        ticP = datetime.datetime.now()
        self.logger.printL(1,"Start Pairs %s" % ticP, "time", self.id)

        self.initializeRedescriptions()
        
        tacP = datetime.datetime.now()
        self.logger.printL(1,"End Pairs %s, elapsed %s (%s)" % (tacP, tacP-ticP, self.want_to_live), "time", self.id)

        ticF = datetime.datetime.now()
        self.logger.printL(1,"Start full run %s" % ticF, "time", self.id)

        initial_red = self.initial_pairs.get(self.data)
        # while initial_red != None and self.want_to_live:
        #     initial_red = self.initial_pairs.get(self.data)
        # exit()


        while initial_red != None and self.want_to_live:
            self.count += 1
            ticE = datetime.datetime.now()
            self.logger.printL(1,"Start expansion %s" % ticE, "time", self.id)
            self.logger.printL(1,"Expansion %d" % self.count, "log", self.id)

            self.expandRedescriptions([initial_red])
            
            self.final["batch"].extend([self.partial["batch"][i] for i in self.partial["results"]])
            self.final["results"] = self.final["batch"].selected(self.constraints.actions_final())

            tacE = datetime.datetime.now()
            self.logger.printL(1,"End expansion %s, elapsed %s (%s)" % (tacE, tacE-ticE, self.want_to_live), "time", self.id)
            self.logger.printL(1, "final", 'result', self.id)

            initial_red = self.initial_pairs.get(self.data)

        tacF = datetime.datetime.now()
        self.logger.printL(1,"End full run %s, elapsed %s (%s)" % (tacF, tacF-ticF, self.want_to_live), "time", self.id)
        if not self.want_to_live:
            self.logger.printL(1, 'Interrupted...', 'status', self.id)
        else:
            self.logger.printL(1, 'Done...', 'status', self.id)

        self.logger.printL(1, None, 'progress', self.id)
        return self.final


### HIGH LEVEL CALLING FUNCTIONS
################################
    def initializeRedescriptions(self):
        self.initial_pairs.reset()
        self.logger.printL(1, 'Searching for initial pairs...', 'status', self.id)
        self.logger.printL(1, (0, 100), 'progress', self.id)

        ### TODO check disabled
        ids = self.data.usableIds(self.constraints.min_itm_c(), self.constraints.min_itm_c())
        ## IDSPAIRS
        ## ids = [[101, 162, 192], [12, 24, 26]]
        total_pairs = (float(len(ids[0])))*(float(len(ids[1])))
        pairs = 0
        for cL in range(0, len(ids[0]), self.constraints.divL()):
            idL = ids[0][cL]
            self.logger.printL(4, 'Searching pairs %i <=> *...' %(idL), "status", self.id)
            for cR in range(0, len(ids[1]), self.constraints.divR()):
                idR = ids[1][cR]
                if not self.want_to_live:
                    return
                
                pairs += 1
                self.logger.printL(10, 'Searching pairs %i <=> %i ...' %(idL, idR), 'status', self.id)
                self.logger.printL(1, (total_pairs, pairs), 'progress', self.id)

                (scores, literalsL, literalsR) = self.computePair(self.data.col(0, idL), self.data.col(1, idR))
                for i in range(len(scores)):
                    if scores[i] >= self.constraints.min_pairscore():
                        self.logger.printL(4, 'Score:%f %s <=> %s' % (scores[i], literalsL[i], literalsR[i]), "log", self.id)
                        tmp = Redescription.fromInitialPair((literalsL[i], literalsR[i]), self.data)
                        if tmp.acc() != scores[i]:
                            ## pdb.set_trace()
                            print 'Ouille! Score:%f %s <=> %s\t\t%s' % (scores[i], literalsL[i], literalsR[i], tmp)

                        self.initial_pairs.add(literalsL[i], literalsR[i], scores[i])

        self.logger.printL(2, 'Found %i pairs, keeping at most %i' % (len(self.initial_pairs), self.constraints.max_red()), "log", self.id)
        self.initial_pairs.setCountdown(self.constraints.max_red())
        return self.initial_pairs

    def expandRedescriptions(self, nextge):
        self.partial["results"] = []
        self.partial["batch"].reset()
        step = 0
        total_steps = float(self.constraints.max_var()*2*len(nextge)) #### TODO

        while len(nextge) > 0  and self.want_to_live:
            kids = set()

            total_steps_int = 1 ## TODO sum([red.nbAvailableCols() for red in nextge])+len(nextge)
            step_int = 0.0
            step += 1
            
            for redi, red in enumerate(nextge):
                ### To know whether some of its extensions were found already
                nb_extensions = red.updateAvailable(self.souvenirs)
                if red.nbAvailableCols() > 0:
                    bests = ExtensionsBatch(self.constraints.score_coeffs(), red)
                    for side in [0,1]:
                        for v in red.availableColsSide(side):
                            if not self.want_to_live: return

                            step_int += 1
                            self.logger.printL(4, (100, 100*(step + step_int/total_steps_int)/total_steps), 'progress', self.id)

                            bests.update(self.getCandidates(side, self.data.col(side, v), red.supports()))

                            # tmp = self.getCandidates(side, self.data.col(side, v), red.supports())
                            # for cand in tmp: ### TODO remove, only for debugging
                            #     kid = cand.kid(red, self.data)
                            #     if kid.acc() != cand.acc:
                            #         pdb.set_trace()
                            #         print 'Something went badly wrong during expansion\nof %s\n\t%s ~> %s' % (red, cand, kid)
                            # bests.update(tmp)
                                                        
                    if self.logger.verbosity >= 4:
                        self.logger.printL(4, bests, "log", self.id)

                    kids = bests.improvingKids(self.data, self.constraints.min_impr(), self.constraints.max_var())
                    self.partial["batch"].extend(kids)
                    self.souvenirs.update(kids)

                    ### parent has been used remove availables
                    red.removeAvailables()

                step_int += 1
                self.logger.printL(4, (100, 100*(step + step_int/total_steps_int)/total_steps), 'progress', self.id)
                self.logger.printL(4, "Generation %s.%d expanded" % (self.count, step), 'status', self.id)

            nextge_keys = self.partial["batch"].selected(self.constraints.actions_nextge())
            nextge = [self.partial["batch"][i] for i in nextge_keys]
            self.partial["batch"].applyFunctTo(".removeAvailables()", nextge_keys, complement=True)
            self.logger.printL(1, "partial", 'result', self.id)

        ### Do before selecting next gen to allow tuning the beam
        ### ask to update results
        self.partial["results"] = self.partial["batch"].selected(self.constraints.actions_partial())
        self.logger.printL(1, "partial", 'result', self.id)
        self.logger.printL(1, "%d redescriptions selected" % len(self.partial["results"]), 'status', self.id)
        return self.partial

###############################################################################
###############################################################################
####################### CANDIDATES METHODS
    def getCandidates(self, side, col, supports):
        method_string = 'self.getCandidates%i' % col.type_id
        try:
            method_compute =  eval(method_string)
        except AttributeError:
              raise Exception('Oups No candidates method for this type of data (%i)!'  % col.type_id)
        return method_compute(side, col, supports)

    def getCandidates1(self, side, col, supports):
        cands = []
        lparts = supports.lparts()
        lmiss = supports.lpartsInterX(col.missing)
        lin = supports.lpartsInterX(col.hold)

        for op in self.constraints.ops_query():
            for neg in self.constraints.neg_query():
                adv = self.getAdv(side, op, neg, lparts, lmiss, lin)
                if adv != None :
                    cands.append(Extension(side, op, Literal(neg, BoolTerm(col.getId())), adv, col.nbRows()))
        return cands

    def getCandidates2(self, side, col, supports):
        return self.getCandidatesNonBool(side, col, supports)

    def getCandidates3(self, side, col, supports):
        return self.getCandidatesNonBool(side, col, supports)

    def getCandidatesNonBool(self, side, col, supports):
        cands = []
        lparts = supports.lparts()
        lmiss = supports.lpartsInterX(col.miss())

        for cand in self.findCover(side, col, lparts, lmiss, supports):
            cands.append(cand[1])
        return cands

####################### COVER METHODS
    def findCover(self, side, col, lparts, lmiss, supports, init=False):
        method_string = 'self.findCover%i' % col.type_id
        try:
            method_compute =  eval(method_string)
        except AttributeError:
              raise Exception('Oups No covering method for this type of data (%i)!'  % col.type_id)
        return method_compute(side, col, lparts, lmiss, supports, init)

    def findCover1(self, side, col, lparts, lmiss, supports, init=False):
        cands = []

        lin = supports.lpartsInterX(col.supp())
        for op in self.constraints.ops_query():            
            for neg in self.constraints.neg_query():        
                best = self.updateExt(best, Literal(neg, BoolTerm(col.getId())), side, op, neg, lparts, lmiss, lin, col.nbRows())

                ### to negate the other side when looking for initial pairs
                if init and True in self.constraints.neg_query():
                    bestNeg = self.updateExt(bestNeg, Literal(neg, BoolTerm(col.getId())), side, op, neg, \
                                          SParts.negateParts(1-side, lparts), SParts.negateParts(1-side, lmiss), SParts.negateParts(1-side, lin), col.nbRows())

                if best.isValid():
                    cands.append((False, best))
                if bestNeg.isValid():
                    cands.append((True, bestNeg))
        return cands

    def findCover2(self, side, col, lparts, lmiss, supports, init=False):
        cands = []

        for op in self.constraints.ops_query():            
            for neg in self.constraints.neg_query():        
                best = Extension(); bestNeg = Extension()
                for (cat, supp) in col.sCats.iteritems():
                    lin = supports.lpartsInterX(supp)
                    best = self.updateExt(best, Literal(neg, CatTerm(col.getId(), cat)), side, op, neg, lparts, lmiss, lin, col.nbRows())

                    ### to negate the other side when looking for initial pairs
                    if init and True in self.constraints.neg_query():
                        bestNeg = self.updateExt(bestNeg, Literal(neg, CatTerm(col.getId(), cat)), side, op, neg, \
                                              SParts.negateParts(1-side, lparts), SParts.negateParts(1-side, lmiss), SParts.negateParts(1-side, lin), col.nbRows())

                if best.isValid():
                    cands.append((False, best))
                if bestNeg.isValid():
                    cands.append((True, bestNeg))
        return cands

    def findCover3(self, side, col, lparts, lmiss, supports, init=False):
        cands = []
        
        if self.inSuppBounds(side, True, lparts) or self.inSuppBounds(side, False, lparts):  ### DOABLE
            segments = col.makeSegments(side, supports, self.constraints.ops_query(init))
            for cand in self.findCoverSegments(side, col, segments, lparts, lmiss, init):
                cands.append((False, cand))

            ### to negate the other side when looking for initial pairs
            if init and True in self.constraints.neg_query():
                nlparts = SParts.negateParts(1-side, lparts)
                nlmiss = SParts.negateParts(1-side, lmiss)

                if self.inSuppBounds(side, True, nlparts): ### DOABLE
                    nsegments = self.makeSegments(side, supports.negate(1-side), self.constraints.ops_query(init))
                    for cand in self.findCoverSegments(side, col, nsegments, nlparts, nlmiss, init):
                        cands.append((True, cand))
        return cands
        
    def findCoverSegments(self, side, col, segments, lparts, lmiss, init=False):
        cands = []
        for op in self.constraints.ops_query(init):
            if len(segments[op]) < self.constraints.max_seg():
                # print '---Doing the full search---'
                # pdb.set_trace()
                cands.extend(self.findCoverFullSearch(side, op, col, segments, lparts, lmiss))
            else:
                # print '---Doing the fast search---'
                # pdb.set_trace()
                if (False in self.constraints.neg_query()):
                    cands.extend(self.findPositiveCover(side, op, col, segments, lparts, lmiss))
                if (True in self.constraints.neg_query()):
                    cands.extend(self.findNegativeCover(side, op, col, segments, lparts, lmiss))
        return cands

    def findCoverFullSearch(self, side, op, col, segments, lparts, lmiss):
        cands = []
        bests = {False: Extension(), True: Extension()}

        for seg_s in range(len(segments[op])):
            lin = SParts.makeLParts()
            for seg_e in range(seg_s,len(segments[op])):
                lin = SParts.addition(lin, segments[op][seg_e][2])
                for neg in self.constraints.neg_query():
                    bests[neg] = self.updateExt(bests[neg], (seg_s, seg_e), side, op, neg, lparts, lmiss, lin, col.nbRows())

        for neg in self.constraints.neg_query():
            if bests[neg].isValid():
                bests[neg].literal = col.getLiteralSeg(neg, segments[op], bests[neg].literal)
                if bests[neg].literal != None:
                    cands.append(bests[neg])
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

        best_t = Extension()
        for b in bests_b:
            if b[1] == len(segments[op]):
                f = bests_f[0]
            else:
                f = bests_f[best_track_f[len(segments[op])-(b[1]+1)]]
            if SParts.advRatioVar(side, op, f[2]) > b[0]:
                best_t = self.updateExt(best_t, (f[1], len(segments[op]) - (b[1]+1)), side, op, False, lparts, lmiss, SParts.addition(f[2], b[2]), col.nbRows())
            else:
                best_t = self.updateExt(best_t, (0, len(segments[op]) - (b[1]+1)), side, op, False, lparts, lmiss, b[2], col.nbRows())

        for f in bests_f:
            if f[1] == len(segments[op]):
                b = bests_b[0]
            else:
                b = bests_b[best_track_b[len(segments[op])-(f[1]+1)]]
            if SParts.advRatioVar(side, op, b[2]) > f[0]: 
                best_t = self.updateExt(best_t, (f[1], len(segments[op]) - (b[1]+1)), side, op, False, lparts, lmiss, SParts.addition(f[2], b[2]), col.nbRows())
            else:
                best_t = self.updateExt(best_t, (f[1], len(segments)-1), side, op, False, lparts, lmiss, f[2], col.nbRows())

        if best_t.isValid():
            best_t.literal = col.getLiteralSeg(True, segments[op], best_t.literal)
            if best_t.literal != None:
                cands.append(best_t)
        return cands

    def findPositiveCover(self, side, op, col, segments, lparts, lmiss):
        cands = []
        lin_f = SParts.makeLParts()
        nb_seg_f = 0
        best_f = Extension()
        lin_b = SParts.makeLParts()
        nb_seg_b = 0
        best_b = Extension()

        for  i in range(len(segments[op])-1):
            # FORWARD
            if i > 0 and \
                   SParts.advAcc(side, op, False, lparts, lmiss, segments[op][i][2]) < SParts.advRatioVar(side, op, lin_f):
                lin_f = SParts.addition(lin_f, segments[op][i][2])
                nb_seg_f += 1
            else: 
                lin_f = segments[op][i][2]
                nb_seg_f = 0
            best_f = self.updateExt(best_f, (i - nb_seg_f, i), side, op, False, lparts, lmiss, lin_f, col.nbRows())

            # BACKWARD
            if i > 0 and \
               SParts.advAcc(side, op, False, lparts, lmiss, segments[op][-(i+1)][2]) < SParts.advRatioVar(side, op, lin_b):
                lin_b = SParts.addition(lin_b, segments[op][-(i+1)][2])
                nb_seg_b += 1
            else:
                lin_b = segments[op][-(i+1)][2]
                nb_seg_b = 0
                best_f = self.updateExt(best_f, (i - nb_seg_f, i), side, op, False, lparts, lmiss, lin_f, col.nbRows())
            best_b = self.updateExt(best_b, (len(segments[op])-(1+i), len(segments[op])-(1+i) + nb_seg_b), \
                                    side, op, False, lparts, lmiss, lin_b, col.nbRows())

        if best_b.isValid() and best_f.isValid():
            bests = [best_b, best_f]

            if best_b.literal[0] > best_f.literal[0] and best_b.literal[1] > best_f.literal[1] and best_b.literal[0] <= best_f.literal[1]:
                lin_m = SParts.makeLParts()
                for seg in segments[op][best_b.literal[0]:best_f.literal[1]+1]:
                    lin_m = SParts.addition(lin_m, seg[2])
                tmp_adv_m = self.getAdv(side, op, False, lparts, lmiss, lin_m)
                if tmp_adv_m != None:
                    bests.append(Extension(side, op, (best_b.literal[0], best_f.literal[1]), tmp_adv_m, col.nbRows()))

            bests.sort()
            best = bests[-1]
            
        elif not best_f.isValid():
            best = best_f
        else:
            best = best_b

        if best.isValid():
            best.literal = col.getLiteralSeg(False, segments[op], best.literal)
            if best.literal != None:
                cands.append(best)
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

        ### TODO deliteraline the right pair miner
        for cand in self.findCover(side, col, lparts, lmiss, supports, True):
            scores.append(cand[1].acc)
            literalsFix.append(Literal(cand[0], termX))
            literalsExt.append(cand[1].literal)
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
        best = Extension()
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

                                best = self.updateExt(best, (lowF, upF, lowE, upE), side, True, False, lparts, lmiss, lin, colE.nbRows())
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

        if best.isValid():
            tF = colF.getLiteralBuk(False, bucketsF[1], best.literal[0:2])
            tE = colE.getLiteralBuk(False, bucketsE[1], best.literal[2:],flag)
            if tF != None and tE != None:
                literalsF.append(tF)
                literalsE.append(tE)
                scores.append(best.acc)

        if flip_side:
            return (scores, literalsE, literalsF)
        else:
            return (scores, literalsF, literalsE)

    def subdo22Full(self, colL, colR, side):
        configs = [(0, False, False), (1, False, True), (2, True, False), (3, True, True)]
        if neg in self.constraints.neg_query():
            configs = configs[:1]
        best = [Extension() for c in configs]
        
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

                    best[i] = self.updateExt(best[i], (catL, catR), side, True, nR, tmp_lparts, tmp_lmiss, tmp_lin, colL.nbRows())
                    
        (scores, literalsFix, literalsExt) = ([], [], [])
        for (i, nL, nR) in configs:
            if best[i].isValid():
                scores.append(best[i].acc)
                literalsFix.append(Literal(nL, CatTerm(colL.getId(), best[i].literal[0])))
                literalsExt.append(Literal(nR, CatTerm(colR.getId(), best[i].literal[1])))
        return (scores, literalsFix, literalsExt)


    def subdo23Full(self, colL, colR, side):
        if side == 0:
            (colF, colE) = (colR, colL)
        else:
            (colF, colE) = (colL, colR)

        configs = [(0, False, False), (1, False, True), (2, True, False), (3, True, True)]
        if neg in self.constraints.neg_query():
            configs = configs[:1]
        best = [Extension() for c in configs]

        buckets = colE.buckets()
        ### TODO DOABLE
        if True : # (colF.lenMode() >= self.constraints.min_itm_out() and colE.lenNonMode() >= self.constraints.min_itm_in()) or ( len(buckets) <= 100 ):
            partsMubB = len(colF.miss())
            missMubB = len(colF.miss() & colE.miss())
            
            missMat = [len(colF.miss() & buk) for buk in buckets[0]]
            totMiss = sum(missMat)

            marg = [len(buk) for buk in buckets[0]]
            if buckets[2] != None :
                marg[buckets[2]] += colE.lenMode()

            for cat in colF.cats():
                lparts = SParts.makeLParts([(SParts.alpha, len(colF.suppCat(cat)) ), (SParts.mubB, partsMubB ), (SParts.delta, - colF.nbRows())], 1-side)
                lmiss  = SParts.makeLParts([(SParts.alpha, len(colF.suppCat(cat) & colE.miss()) ), (SParts.mubB, missMubB ), (SParts.delta, -len(colE.miss()) )], 1-side)
                
                interMat = [len(colF.suppCat(cat) & buk) for buk in buckets[0]]
                if buckets[2] != None :
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

                            best[i] = self.updateExt(best[i], (cat, low, up), side, True, nE, tmp_lparts, tmp_lmiss, tmp_lin, colE.nbRows())

                        above+=interMat[up]
                        missAbove+=missMat[up]
                        up-=1
                    below+=interMat[low]
                    missBelow+=missMat[low]
                    low+=1

        
        (scores, literalsFix, literalsExt) = ([], [], [])
        for (i, nF, nE) in configs:

            if best[i].isValid():
                tE = colE.getLiteralBuk(nE, buckets[1], idE, best[i].literal[1:],flag)
                if tE != None:
                    literalsExt.append(tE)
                    literalsFix.append(Literal(nF, CatTerm(idF, best[i].literal[0])))
                    scores.append(best[i].acc)
        return (scores, literalsFix, literalsExt)

##### TOOLS METHODS
    # compute the advance resulting of appending X on given side with given operator and negation
    # from intersections of X with parts (clp)            
    def getAdv(self, side, op, neg, lparts, lmiss, lin):
        lout = [lparts[i] - lmiss[i] - lin[i] for i in range(len(lparts))]
        clp = (lin, lout, lmiss, lparts)
        contri = SParts.sumPartsIdInOut(side, neg, SParts.IDS_cont[op], clp)
        if contri >= self.constraints.min_itm_c():
            varBlue = SParts.sumPartsIdInOut(side, neg, SParts.IDS_varnum[op], clp)
            fixBlue = SParts.sumPartsIdInOut(side, neg, SParts.IDS_fixnum[op], clp)
            if varBlue+fixBlue >= self.constraints.min_itm_in():
                sout = SParts.sumPartsIdInOut(side, neg, SParts.IDS_out[op], clp)
                if sout >= self.constraints.min_itm_out():
                    varRed = SParts.sumPartsIdInOut(side, neg, SParts.IDS_varden[op], clp)
                    fixRed = SParts.sumPartsIdInOut(side, neg, SParts.IDS_fixden[op], clp)
                    return (contri, varBlue, fixBlue, varRed, fixRed, clp)
        return None

    def updateExt(self, best, t, side, op, neg, lparts, lmiss, lin, N):
        tmp_adv = self.getAdv(side, op, neg, lparts, lmiss, lin)
        if best.compareAdv(tmp_adv) < 0:
            return Extension(side, op, t, tmp_adv, N)
        else:
            return best
        ### EX: best = self.updateExt(best, Literal(neg, BoolTerm(col.getId())), side, op, neg, lparts, lmiss, lin, col.nbRows())


    def inSuppBounds(self, side, op, lparts):
        return SParts.sumPartsId(side, SParts.IDS_varnum[op] + SParts.IDS_fixnum[op], lparts) >= self.constraints.min_itm_in() \
               and SParts.sumPartsId(side, SParts.IDS_cont[op], lparts) >= self.constraints.min_itm_c()
