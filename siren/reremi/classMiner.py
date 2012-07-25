import datetime
import classCharbonStd
import classCharbonAlt
from classRedescription import Redescription
from classBatch import Batch
from classExtension import ExtensionError, ExtensionsBatch
from classSouvenirs import Souvenirs
from classConstraints import Constraints
from classInitialPairs import *
import pdb

class Miner:

### INITIALIZATION
##################
    def __init__(self, data, params, logger, mid=None, souvenirs=None):
        if mid is not None:
            self.id = mid
        else:
            self.id = 1
        self.double_check = True
        self.data = data
        self.logger = logger
        self.constraints = Constraints(self.data.nbRows(), params)
        if self.data.hasMissing():
            self.charbon = classCharbonAlt.Charbon(self.constraints)
        else:
            self.charbon = classCharbonStd.Charbon(self.constraints)
        if souvenirs is None:
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
        self.progress_ss = {"total":0, "current":0}

    def kill(self):
        self.want_to_live = False


### RUN FUNCTIONS
################################
### TODO improve progress tracking

    def filter_run(self, redescs):
        batch = Batch(redescs)
        tmp_ids = batch.selected(self.constraints.actions_final())
        return [batch[i] for i in tmp_ids]

    def part_run(self, redesc):
        self.count = "C"

        self.progress_ss["cand_var"] = 1
        self.progress_ss["cand_side"] = [self.souvenirs.nbCols(0)*self.progress_ss["cand_var"],
                                         self.souvenirs.nbCols(1)*self.progress_ss["cand_var"]]
        self.progress_ss["generation"] = self.constraints.batch_cap()*sum(self.progress_ss["cand_side"])
        self.progress_ss["expansion"] = (self.constraints.max_var()*2-len(redesc))*self.progress_ss["generation"]
        self.progress_ss["total"] = self.progress_ss["expansion"]
        self.progress_ss["current"] = 0
        
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

        ids = self.data.usableIds(self.constraints.min_itm_c(), self.constraints.min_itm_c())
        self.progress_ss["pair_gen"] = 10
        self.progress_ss["pairs_gen"] = (len(ids[0])/self.constraints.divL())*(len(ids[1])/self.constraints.divR())*self.progress_ss["pair_gen"]
        self.progress_ss["cand_var"] = 1
        self.progress_ss["cand_side"] = [self.souvenirs.nbCols(0)*self.progress_ss["cand_var"],
                                         self.souvenirs.nbCols(1)*self.progress_ss["cand_var"]]
        self.progress_ss["generation"] = self.constraints.batch_cap()*sum(self.progress_ss["cand_side"])
        self.progress_ss["expansion"] = (self.constraints.max_var()-1)*2*self.progress_ss["generation"]
        self.progress_ss["total"] = self.progress_ss["pairs_gen"] + self.constraints.max_red()*self.progress_ss["expansion"]
        self.progress_ss["current"] = 0
        
        self.logger.printL(1, (self.progress_ss["total"], self.progress_ss["current"]), 'progress', self.id)
        self.logger.printL(1, "Starting mining", 'status', self.id) ### todo ID
        ticP = datetime.datetime.now()
        self.logger.printL(1,"Start Pairs %s" % ticP, "time", self.id)

        self.initializeRedescriptions(ids)
        
        tacP = datetime.datetime.now()
        self.logger.printL(1,"End Pairs %s, elapsed %s (%s)" % (tacP, tacP-ticP, self.want_to_live), "time", self.id)

        ticF = datetime.datetime.now()
        self.logger.printL(1,"Start full run %s" % ticF, "time", self.id)

        initial_red = self.initial_pairs.get(self.data)
        # while initial_red is not None and self.want_to_live:
        #     initial_red = self.initial_pairs.get(self.data)
        # exit()


        while initial_red is not None and self.want_to_live:
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
    def initializeRedescriptions(self, ids=None):
        self.initial_pairs.reset()
        self.logger.printL(1, 'Searching for initial pairs...', 'status', self.id)
        self.logger.printL(1, (self.progress_ss["total"], self.progress_ss["current"]), 'progress', self.id)

        ### TODO check disabled
        if ids is None:
            ids = self.data.usableIds(self.constraints.min_itm_c(), self.constraints.min_itm_c())
        ## IDSPAIRS
        ## ids = [[101, 162, 192], [12, 24, 26]]
        total_pairs = (float(len(ids[0])))*(float(len(ids[1])))
        pairs = 0
        for cL in range(0, len(ids[0]), self.constraints.divL()):
            idL = ids[0][cL]
            self.logger.printL(3, 'Searching pairs %i <=> *...' %(idL), "status", self.id)
            for cR in range(0, len(ids[1]), self.constraints.divR()):
                idR = ids[1][cR]
                if not self.want_to_live:
                    return
                
                pairs += 1
                self.progress_ss["current"] += self.progress_ss["pair_gen"]
                self.logger.printL(10, 'Searching pairs %i <=> %i ...' %(idL, idR), 'status', self.id)
                self.logger.printL(1, (self.progress_ss["total"], self.progress_ss["current"]), 'progress', self.id)
                seen = []
                (scores, literalsL, literalsR) = self.charbon.computePair(self.data.col(0, idL), self.data.col(1, idR))
                for i in range(len(scores)):
                    if scores[i] >= self.constraints.min_pairscore() and (literalsL[i], literalsR[i]) not in seen:
                        seen.append((literalsL[i], literalsR[i]))
                        self.logger.printL(6, 'Score:%f %s <=> %s' % (scores[i], literalsL[i], literalsR[i]), "log", self.id)
                        if self.double_check:
                            tmp = Redescription.fromInitialPair((literalsL[i], literalsR[i]), self.data)
                            if tmp.acc() != scores[i]:
                                ### H pdb.set_trace()
                                self.logger.printL(1,'OUILLE! Score:%f %s <=> %s\t\t%s' % (scores[i], literalsL[i], literalsR[i], tmp), "log", self.id)
                        
                        self.initial_pairs.add(literalsL[i], literalsR[i], scores[i])
        self.logger.printL(2, 'Found %i pairs, keeping at most %i' % (len(self.initial_pairs), self.constraints.max_red()), "log", self.id)
        self.initial_pairs.setCountdown(self.constraints.max_red())
        return self.initial_pairs

    def expandRedescriptions(self, nextge):
        self.partial["results"] = []
        self.partial["batch"].reset()

        while len(nextge) > 0  and self.want_to_live:
            kids = set()

            tmp_gen = self.progress_ss["current"]
            
            for redi, red in enumerate(nextge):
                ### To know whether some of its extensions were found already
                nb_extensions = red.updateAvailable(self.souvenirs)
                if red.nbAvailableCols() > 0:
                    bests = ExtensionsBatch(self.data.nbRows(), self.constraints.score_coeffs(), red)
                    for side in [0,1]:
                    ##for side in [1]:
                        ### check whether we are extending a redescription with this side empty
                        if red.length(side) == 0:
                            init = -1
                        else:
                            init = 0 
                            
                        for v in red.availableColsSide(side):
                            if not self.want_to_live: return

                            if self.double_check:
                                tmp = self.charbon.getCandidates(side, self.data.col(side, v), red.supports())                         
                                for cand in tmp: ### TODO remove, only for debugging
                                    kid = cand.kid(red, self.data)
                                    if kid.acc() != cand.getAcc():
                                        self.logger.printL(1,'OUILLE! Something went badly wrong during expansion of %s.%d.%d\n\t%s\n\t%s\n\t~> %s' % (self.count, len(red), redi, red, cand, kid), "log", self.id)
                                bests.update(tmp)

                            else:
                                bests.update(self.charbon.getCandidates(side, self.data.col(side, v), red.supports(), init))

                        self.progress_ss["current"] += self.progress_ss["cand_side"][side]
                        self.logger.printL(1, (self.progress_ss["total"], self.progress_ss["current"]), 'progress', self.id)
                                                        
                    if self.logger.verbosity >= 4:
                        self.logger.printL(4, bests, "log", self.id)

                    try:
                        kids = bests.improvingKids(self.data, self.constraints.min_impr(), self.constraints.max_var())
                    except ExtensionError as details:
                        self.logger.printL(1,'OUILLE! Something went badly wrong during expansion of %s.%d.%d\n%s' % (self.count, len(red), redi, details), "log", self.id)
                        kids = []
                        
                    self.partial["batch"].extend(kids)
                    self.souvenirs.update(kids)
                    ### parent has been used remove availables
                    red.removeAvailables()
                self.progress_ss["current"] = tmp_gen + self.progress_ss["generation"]
                self.logger.printL(1, (self.progress_ss["total"], self.progress_ss["current"]), 'progress', self.id)
                self.logger.printL(4, "Candidate %s.%d.%d expanded" % (self.count, len(red), redi), 'status', self.id)

            self.logger.printL(4, "Generation %s.%d expanded" % (self.count, len(red)), 'status', self.id)
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

