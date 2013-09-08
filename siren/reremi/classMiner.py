import datetime, random, os.path
import classCharbonStd
import classCharbonAlt
from classRedescription import Redescription
from classBatch import Batch
from classExtension import ExtensionError, ExtensionsBatch
from classSouvenirs import Souvenirs
from classConstraints import Constraints
from classInitialPairs import *
from codeRRM import RedModel

import pdb

class Miner:

### INITIALIZATION
##################
    def __init__(self, data, params, logger, mid=None, souvenirs=None, qin=None, cust_params={}):
        self.qin = qin
        self.deps = []
        self.org_data = None
        self.want_to_live = True
        if mid is not None:
            self.id = mid
        else:
            self.id = 1
        self.double_check = False #True
        self.data = data

        row_ids = None
        if cust_params.has_key("area"):
            inw, outw = cust_params.get("in_weight", 1), cust_params.get("out_weight", 1)
            if params.has_key("in_weight"):
                inw = params["in_weight"]["data"]
            if params.has_key("out_weight"):
                outw = params["out_weight"]["data"]
            weights = dict([(r,outw) for r in range(self.data.nbRows())])
            for old in cust_params["area"]:
                weights[old] = inw
            cust_params["weights"] = weights

        if cust_params.has_key("weights"):
            row_ids = {}
            off = 0
            for (old, mul) in cust_params["weights"].items():
                row_ids[old] = [off+r for r in range(mul)]
                off += mul
                
        if row_ids is not None:
            self.org_data = self.data
            self.data = self.data.subset(row_ids)


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

        try:
            self.initial_pairs = eval('IP%s()' % (self.constraints.pair_sel()))
            if params.has_key("pairs_store"):
                self.initial_pairs.setStore(params["pairs_store"]["data"])
        except AttributeError:
            raise Exception('Oups this selection method does not exist !')

        self.partial = {"results":[], "batch": Batch()}
        self.final = {"results":[], "batch": Batch()}

        self.progress_ss = {"total":0, "current":0}
        self.rm = None
        if self.constraints.dl_score():
            self.logger.printL(1,"Using DL for scoring...")
            self.rm = RedModel(data)


        ### Dependencies between variables 
        self.deps = []
        if self.data.hasNames():
            names = self.data.getNames()
            if len(names[0]) == len(names[1]) and re.search("^.* \[\[(?P<deps>[0-9,]*)\]\]$", names[0][0]) is not None:
                for name in names[0]:
                    self.deps.append(set(map(int, re.search("^.* \[\[(?P<deps>[0-9,]*)\]\]$", name).group("deps").split(","))))
                            
    def kill(self):
        self.want_to_live = False

    def questionLive(self):
        if self.want_to_live and self.qin is not None:
            try:
                piece_result = self.qin.get_nowait()
                if piece_result["type_message"] == "progress" and piece_result["message"] == "stop":
                    self.want_to_live = False
            except:
                pass
        return self.want_to_live

### RUN FUNCTIONS
################################

    def filter_run(self, redescs):
        batch = Batch(redescs)
        tmp_ids = batch.selected(self.constraints.actions_redundant())
        #tmp_ids = batch.selected(self.constraints.actions_final())
        return [batch[i] for i in tmp_ids]

    def part_run(self, cust_params):
        if cust_params.has_key("reds"):
            reds = cust_params["reds"]
        elif cust_params.has_key("red"):
            reds = [cust_params["red"]]
        else:
            reds = []
        if self.org_data is not None:
            for red in reds:
                red.recompute(self.data)

        if cust_params.has_key("side"):
            self.souvenirs.cutOffSide(1-cust_params["side"])

        self.count = "C"

        self.progress_ss["cand_var"] = 1
        self.progress_ss["cand_side"] = [self.souvenirs.nbCols(0)*self.progress_ss["cand_var"],
                                         self.souvenirs.nbCols(1)*self.progress_ss["cand_var"]]
        self.progress_ss["generation"] = self.constraints.batch_cap()*sum(self.progress_ss["cand_side"])
        self.progress_ss["expansion"] = (self.constraints.max_var()[0]-min([self.constraints.max_var()[0]]+[len(r.queries[0]) for r in reds])+
                                         self.constraints.max_var()[1]-min([self.constraints.max_var()[1]]+[len(r.queries[1]) for r in reds]))*self.progress_ss["generation"]
        self.progress_ss["total"] = self.progress_ss["expansion"]
        self.progress_ss["current"] = 0
        
        ticE = datetime.datetime.now()
        self.logger.printL(1,"Start part run %s" % ticE, "time", self.id)
        self.logger.printL(1, (100, 0), 'progress', self.id)
        self.logger.printL(1, "Expanding...", 'status', self.id) ### todo ID

        self.expandRedescriptions(reds)

        tacE = datetime.datetime.now()
        self.logger.printL(1,"End part run %s, elapsed %s (%s)" % (tacE, tacE-ticE, self.questionLive()), "time", self.id)
        if not self.questionLive():
            self.logger.printL(1, 'Interrupted...', 'status', self.id)
        else:
            self.logger.printL(1, 'Done...', 'status', self.id)


        self.logger.printL(1, None, 'progress', self.id)
        return self.partial

    def full_run(self, cust_params={}):
        self.final["results"] = []
        self.final["batch"].reset()
        self.count = 0

        ids = self.data.usableIds(self.constraints.min_itm_c(), self.constraints.min_itm_c())
        self.progress_ss["pair_gen"] = 10
        self.progress_ss["pairs_gen"] = (len(ids[0])/self.constraints.mod_lhs())*(len(ids[1])/self.constraints.mod_rhs())*self.progress_ss["pair_gen"]
        self.progress_ss["cand_var"] = 1
        self.progress_ss["cand_side"] = [self.souvenirs.nbCols(0)*self.progress_ss["cand_var"],
                                         self.souvenirs.nbCols(1)*self.progress_ss["cand_var"]]
        self.progress_ss["generation"] = self.constraints.batch_cap()*sum(self.progress_ss["cand_side"])
        self.progress_ss["expansion"] = (self.constraints.max_var()[0]+self.constraints.max_var()[0]-2)*2*self.progress_ss["generation"]
        self.progress_ss["total"] = self.progress_ss["pairs_gen"] + self.constraints.max_red()*self.progress_ss["expansion"]
        self.progress_ss["current"] = 0
        
        self.logger.printL(1, (self.progress_ss["total"], self.progress_ss["current"]), 'progress', self.id)
        self.logger.printL(1, "Starting mining", 'status', self.id) ### todo ID
        ticP = datetime.datetime.now()
        self.logger.printL(1,"Start Pairs %s" % ticP, "time", self.id)
 
        self.initializeRedescriptions(ids)
        
        tacP = datetime.datetime.now()
        self.logger.printL(1,"End Pairs %s, elapsed %s (%s)" % (tacP, tacP-ticP, self.questionLive()), "time", self.id)

        ticF = datetime.datetime.now()
        self.logger.printL(1,"Start full run %s" % ticF, "time", self.id)

        initial_red = self.initial_pairs.get(self.data, self.testIni)
        # while initial_red is not None and self.questionLive():
        #     initial_red = self.initial_pairs.get(self.data)
        # exit()


        while initial_red is not None and self.questionLive():
            self.count += 1
            ticE = datetime.datetime.now()
            self.logger.printL(1,"Start expansion %s" % ticE, "time", self.id)
            self.logger.printL(1,"Expansion %d" % self.count, "log", self.id)
            self.expandRedescriptions([initial_red])
            
            self.final["batch"].extend([self.partial["batch"][i] for i in self.partial["results"]])
            self.final["results"] = self.final["batch"].selected(self.constraints.actions_final())
            if self.rm is not None:
                treds = [self.final["batch"][pos] for pos in self.final["results"]]
                self.rm = self.rm.fillCopy(self.data, treds)

            tacE = datetime.datetime.now()
            self.logger.printL(1,"End expansion %s, elapsed %s (%s)" % (tacE, tacE-ticE, self.questionLive()), "time", self.id)
            self.logger.printL(1, {"final":self.final["batch"], "partial":self.partial["batch"]}, 'result', self.id)

            initial_red = self.initial_pairs.get(self.data, self.testIni)

        tacF = datetime.datetime.now()
        self.logger.printL(1,"End full run %s, elapsed %s (%s)" % (tacF, tacF-ticF, self.questionLive()), "time", self.id)
        if not self.questionLive():
            self.logger.printL(1, 'Interrupted...', 'status', self.id)
        else:
            self.logger.printL(1, 'Done...', 'status', self.id)

        self.logger.printL(1, None, 'progress', self.id)
        return self.final


### HIGH LEVEL CALLING FUNCTIONS
################################
    def testIni(self, pair):
        if pair is None:
            return False
        if self.rm is not None:
            tmp = Redescription.fromInitialPair(pair, self.data)
            top = self.rm.getTopDeltaRed(tmp, self.data)
            return top[0] < 0
        return True
    
    def initializeRedescriptions(self, ids=None):
        self.initial_pairs.reset()

        if self.initial_pairs.getStore() is not None and os.path.isfile(self.initial_pairs.getStore()):
            self.initial_pairs.load(self.initial_pairs.getStore())
            self.initial_pairs.setCountdown(self.constraints.max_red())
            return self.initial_pairs 

        self.logger.printL(1, 'Searching for initial pairs...', 'status', self.id)
        self.logger.printL(1, (self.progress_ss["total"], self.progress_ss["current"]), 'progress', self.id)

        if ids is None:
            ids = self.data.usableIds(self.constraints.min_itm_c(), self.constraints.min_itm_c())
        ## IDSPAIRS
        if len(ids[0]) > 5000:
           ids[0] = sorted(random.sample(ids[0], 100))
        total_pairs = (float(len(ids[0])))*(float(len(ids[1])))
        pairs = 0
        for cL in range(0, len(ids[0]), self.constraints.mod_lhs()):
            idL = ids[0][cL]
            self.logger.printL(3, 'Searching pairs %i <=> *...' %(idL), "status", self.id)
            self.logger.printL(3, (self.progress_ss["total"], self.progress_ss["current"]), 'progress', self.id)
            if len(self.deps) > 0:
                idsR = [ids[1][cR] for cR in range(cL+1, len(ids[1]), self.constraints.mod_rhs()) if len(self.deps[ids[1][cR]] & self.deps[idL]) == 0]                
            else:
                idsR = [ids[1][cR] for cR in range(0, len(ids[1]), self.constraints.mod_rhs())]
            if len(idsR) > 5000:
                idsR = sorted(random.sample(idsR, 1000))

            for idR in idsR:
                if not self.questionLive():
                    return
                
                pairs += 1
                self.progress_ss["current"] += self.progress_ss["pair_gen"]
                self.logger.printL(7, 'Searching pairs %i <=> %i ...' %(idL, idR), 'status', self.id)
                self.logger.printL(7, (self.progress_ss["total"], self.progress_ss["current"]), 'progress', self.id)
                seen = []
                (scores, literalsL, literalsR) = self.charbon.computePair(self.data.col(0, idL), self.data.col(1, idR))
                for i in range(len(scores)):
                    nsc = None
                    if scores[i] >= self.constraints.min_pairscore() and (literalsL[i], literalsR[i]) not in seen:
                        if self.rm is not None:
                        #### HERE DL
                            tmp = Redescription.fromInitialPair((literalsL[i], literalsR[i]), self.data)
                            top = self.rm.getTopDeltaRed(tmp, self.data)
                            if top[0] < 0:
                                nsc = -top[0]
                        else:
                            nsc = scores[i]
                    if nsc is not None:
                        seen.append((literalsL[i], literalsR[i]))
                        self.logger.printL(6, 'Score:%f %s <=> %s' % (nsc, literalsL[i], literalsR[i]), "log", self.id)
                        if self.double_check:
                            tmp = Redescription.fromInitialPair((literalsL[i], literalsR[i]), self.data)
                            if tmp.getAcc() != scores[i]:
                                self.logger.printL(1,'OUILLE! Score:%f %s <=> %s\t\t%s' % (scores[i], literalsL[i], literalsR[i], tmp), "log", self.id)

                        self.initial_pairs.add(literalsL[i], literalsR[i], nsc)
        self.logger.printL(1, 'Found %i pairs, keeping at most %i' % (len(self.initial_pairs), self.constraints.max_red()), "log", self.id)
        self.logger.printL(1, (self.progress_ss["total"], self.progress_ss["current"]), 'progress', self.id)
        if self.initial_pairs.getStore() is not None:
            self.initial_pairs.store(self.initial_pairs.getStore())
        self.initial_pairs.setCountdown(self.constraints.max_red())
        return self.initial_pairs

    def expandRedescriptions(self, nextge):
        self.partial["results"] = []
        self.partial["batch"].reset()
        self.partial["batch"].extend(nextge)


        while len(nextge) > 0  and self.questionLive():

            kids = set()

            tmp_gen = self.progress_ss["current"]
            
            for redi, red in enumerate(nextge):
                ### To know whether some of its extensions were found already
                nb_extensions = red.updateAvailable(self.souvenirs)
                # print "Adding ", len(self.partial["batch"]), red.queries[0], "\t", red.queries[1] 
                # self.partial["batch"].append(red)
                if red.nbAvailableCols() > 0:
                    bests = ExtensionsBatch(self.data.nbRows(), self.constraints.score_coeffs(), red)
                    for side in [0,1]:
                    ##for side in [1]:
                        ### check whether we are extending a redescription with this side empty
                        if red.length(side) == 0:
                            init = 1
                        else:
                            init = red.usesOr(1-side)*-1 
                        for v in red.availableColsSide(side, self.deps, self.data.single_dataset):
                            if not self.questionLive(): return

                            if self.double_check:
                                tmp = self.charbon.getCandidates(side, self.data.col(side, v), red.supports(), init)                  
                                for cand in tmp: ### TODO remove, only for debugging
                                    kid = cand.kid(red, self.data)
                                    if kid.getAcc() != cand.getAcc():
                                        pdb.set_trace()
                                        self.logger.printL(1,"OUILLE! Something went badly wrong during expansion of %s.%d.%d\n\t%s\n\t%s\n\t~> %s" % (self.count, len(red), redi, red, cand, kid), "log", self.id)

                                if self.rm is not None:
                                    bests.updateDL(tmp, self.rm, self.data)
                                else:
                                    bests.update(tmp)
                            else:
                                #### HERE DL
                                if self.rm is not None:
                                    bests.updateDL(self.charbon.getCandidates(side, self.data.col(side, v), red.supports(), init), self.rm, self.data)
                                else:
                                    bests.update(self.charbon.getCandidates(side, self.data.col(side, v), red.supports(), init))


                        self.progress_ss["current"] += self.progress_ss["cand_side"][side]
                        self.logger.printL(1, (self.progress_ss["total"], self.progress_ss["current"]), 'progress', self.id)
                                                        
                    if self.logger.verbosity >= 4:
                        self.logger.printL(4, bests, "log", self.id)

                    try:
                        ### DL HERE
                        if self.rm is not None:
                            kids = bests.improvingKidsDL(self.data, self.constraints.min_impr(), self.constraints.max_var(), self.rm)
                        else:
                            kids = bests.improvingKids(self.data, self.constraints.min_impr(), self.constraints.max_var())

                    except ExtensionError as details:
                        self.logger.printL(1,"OUILLE! Something went badly wrong during expansion of %s.%d.%d\n--------------\n%s\n--------------" % (self.count, len(red), redi, details.value), "log", self.id)
                        kids = []
                        
                    
                    self.partial["batch"].extend(kids)
                    self.souvenirs.update(kids)
                    ### parent has been used remove availables
                    red.removeAvailables()
                self.progress_ss["current"] = tmp_gen + self.progress_ss["generation"]
                self.logger.printL(2, (self.progress_ss["total"], self.progress_ss["current"]), 'progress', self.id)
                self.logger.printL(4, "Candidate %s.%d.%d expanded" % (self.count, len(red), redi), 'status', self.id)

            self.logger.printL(4, "Generation %s.%d expanded" % (self.count, len(red)), 'status', self.id)
            nextge_keys = self.partial["batch"].selected(self.constraints.actions_nextge())
            nextge = [self.partial["batch"][i] for i in nextge_keys]
            self.partial["batch"].applyFunctTo(".removeAvailables()", nextge_keys, complement=True)
            self.logger.printL(1, {"final":self.final["batch"], "partial":self.partial["batch"]}, 'result', self.id)

        ### Do before selecting next gen to allow tuning the beam
        ### ask to update results
        self.partial["results"] = self.partial["batch"].selected(self.constraints.actions_partial())
        self.logger.printL(1, {"final":self.final["batch"], "partial":self.partial["batch"]}, 'result', self.id)
        self.logger.printL(1, "%d redescriptions selected" % len(self.partial["results"]), 'status', self.id)

        return self.partial

