import random, os.path, re
from toolLog import Log
from classRedescription import Redescription
from classBatch import Batch
from classExtension import ExtensionError, ExtensionsBatch
from classSouvenirs import Souvenirs
from classConstraints import Constraints
from classInitialPairs import InitialPairs
from classData import BoolColM, CatColM, NumColM

import pdb

from classCharbonGMiss import CharbonGMiss
from classCharbonGStd import CharbonGStd
from classCharbonTAlt import CharbonTCW, CharbonTRelay, CharbonTLayer
from classCharbonTSplit import CharbonTSplit



TREE_CLASSES = { "layeredtrees": CharbonTLayer,
                 "cartwheel": CharbonTCW,
                 "splittrees": CharbonTSplit,
                 "relayer": CharbonTRelay}
TREE_DEF = CharbonTRelay

# PAIR_LOADS = [[1,2,3],
#               [2,4,6],
#               [3,6,10]]

class DummyLog:
    verbosity = 0
    def printL(self, level, message, type_message="*", source=None):
        pass
    def updateProgress(self, details, level=-1, id=None):
        pass


class ExpMiner:
    def __init__(self, ppid, count, data, charbon, constraints, souvenirs, logger=None, question_live=None):
        self.charbon = charbon
        self.data = data
        self.count = count
        self.ppid = ppid
        self.constraints = constraints
        self.souvenirs = souvenirs
        self.upSouvenirs = False
        self.question_live = question_live
        if logger is None:
            self.logger = DummyLog()
        else:
            self.logger = logger

    def questionLive(self):
        if self.question_live is None:
            return True
        return self.question_live()

    def expandRedescriptions(self, nextge, partial=None, final=None):
        if len(nextge) > 0 and self.questionLive():
            if partial is not None:
                partial["results"] = []
                partial["batch"].reset()
            else:
                partial = {"results":[], "batch": Batch()}
            partial["batch"].extend(nextge)
            if self.charbon.isTreeBased():
                return self.expandRedescriptionsTree(nextge, partial, final)
            else:
                return self.expandRedescriptionsGreedy(nextge, partial, final)

    def expandRedescriptionsTree(self, nextge, partial, final=None):
        for redi, red in enumerate(nextge):
            new_red = self.charbon.getTreeCandidates(-1, self.data, red)
            if new_red is not None:
                partial["batch"].append(new_red)

            # self.logger.updateProgress({"rcount": self.count, "redi": redi}, 4, self.ppid)
            self.logger.printL(4, "Candidate %s.%d.%d grown" % (self.count, len(red), redi), 'status', self.ppid)

        self.logger.printL(4, "Generation %s.%d expanded" % (self.count, len(red)), 'status', self.ppid)
        self.logger.printL(1, {"partial":partial["batch"]}, 'result', self.ppid)

        ### Do before selecting next gen to allow tuning the beam
        ### ask to update results
        if 1 in partial["batch"].selected(self.constraints.actions_partial()):
            addR = True
            ii = 0
            if final is not None:
                while addR and ii < len(final["batch"]):
                ### check identity
                    addR = (partial["batch"][1].supp(0) != final["batch"][ii].supp(0) or
                            partial["batch"][1].supp(1) != final["batch"][ii].supp(1) or
                            partial["batch"][1].invColsSide(0) != final["batch"][ii].invColsSide(0) or
                            partial["batch"][1].invColsSide(1) != final["batch"][ii].invColsSide(1))
                    ii += 1
            if addR:
                partial["results"].append(1)
        self.logger.printL(1, {"partial":partial["batch"]}, 'result', self.ppid)
        self.logger.printL(1, "%d redescriptions selected" % len(partial["results"]), 'status', self.ppid)
        for red in partial["results"]:
            self.logger.printL(2, "--- %s" % partial["batch"][red])
        return partial
        

    def expandRedescriptionsGreedy(self, nextge, partial, final=None):
        while len(nextge) > 0:
            kids = set()
            redi = 0

            while redi < len(nextge):
                red = nextge[redi]
                ### To know whether some of its extensions were found already
                nb_extensions = red.updateAvailable(self.souvenirs)

                if red.nbAvailableCols() > 0:
                    bests = ExtensionsBatch(self.data.nbRows(), self.constraints.score_coeffs(), red)
                    for side in [0,1]:
                    ##for side in [1]:
                        ### check whether we are extending a redescription with this side empty
                        if red.length(side) == 0:
                            init = 1
                        else:
                            init = red.usesOr(1-side)*-1 
                        for v in red.availableColsSide(side, self.constraints.getDeps(), self.data.single_dataset):
                            if not self.questionLive():
                                nextge = []
                        
                            else:
                                bests.update(self.charbon.getCandidates(side, self.data.col(side, v), red.supports(), init))

                    if self.logger.verbosity >= 4:
                        self.logger.printL(4, bests, "log", self.ppid)

                    try:
                        kids = bests.improvingKids(self.data, self.constraints.min_impr(), self.constraints.max_var())

                    except ExtensionError as details:
                        self.logger.printL(1,"OUILLE! Something went badly wrong during expansion of %s.%d.%d\n--------------\n%s\n--------------" % (self.count, len(red), redi, details.value), "log", self.ppid)
                        kids = []

                    partial["batch"].extend(kids)
                    ## SOUVENIRS
                    if self.upSouvenirs:
                        self.souvenirs.update(kids)

                    ### parent has been used remove availables
                    red.removeAvailables()
                # self.logger.updateProgress({"rcount": self.count, "generation": len(red), "cand": redi}, 4, self.ppid)
                self.logger.printL(4, "Candidate %s.%d.%d expanded" % (self.count, len(red), redi), 'status', self.ppid)
                redi += 1

            self.logger.printL(4, "Generation %s.%d expanded" % (self.count, len(red)), 'status', self.ppid)
            nextge_keys = partial["batch"].selected(self.constraints.actions_nextge())
            nextge = [partial["batch"][i] for i in nextge_keys]

            partial["batch"].applyFunctTo(".removeAvailables()", nextge_keys, complement=True)
            self.logger.printL(1, {"partial":partial["batch"]}, 'result', self.ppid)

        ### Do before selecting next gen to allow tuning the beam
        ### ask to update results
        partial["results"] = partial["batch"].selected(self.constraints.actions_partial())
        self.logger.printL(1, {"partial":partial["batch"]}, 'result', self.ppid)
        self.logger.printL(1, "%d redescriptions selected" % len(partial["results"]), 'status', self.ppid)
        for red in partial["results"]:
            self.logger.printL(2, "--- %s" % partial["batch"][red])
        return partial


class Miner:

### INITIALIZATION
##################
    def __init__(self, data, params, logger=None, mid=None, souvenirs=None, qin=None, cust_params={}):
        self.qin = qin
        self.org_data = None
        self.want_to_live = True
        if mid is not None:
            self.id = mid
        else:
            self.id = 1
        self.data = data

        self.max_processes = params["nb_processes"]["data"]
        row_ids = None
        if "area" in cust_params:
            inw, outw = cust_params.get("in_weight", 1), cust_params.get("out_weight", 1)
            if "in_weight" in params:
                inw = params["in_weight"]["data"]
            if "out_weight" in params:
                outw = params["out_weight"]["data"]
            weights = dict([(r,outw) for r in range(self.data.nbRows())])
            for old in cust_params["area"]:
                weights[old] = inw
            cust_params["weights"] = weights

        if "weights" in cust_params:
            row_ids = {}
            off = 0
            for (old, mul) in cust_params["weights"].items():
                row_ids[old] = [off+r for r in range(mul)]
                off += mul
                
        if row_ids is not None:
            self.org_data = self.data
            self.data = self.data.subset(row_ids)


        if logger is not None:
            self.logger = logger
        else:
             self.logger = Log()       
        self.constraints = Constraints(self.data, params)

        self.charbon = self.initCharbon()
        if souvenirs is None:
            self.souvenirs = Souvenirs(self.data.usableIds(self.constraints.min_itm_c(), self.constraints.min_itm_c()), self.constraints.amnesic())
        else:
            self.souvenirs = souvenirs

        self.initial_pairs = InitialPairs(self.constraints.pair_sel(), self.constraints.max_red(), params.get("pairs_store"))
        
        self.partial = {"results":[], "batch": Batch()}
        self.final = {"results":[], "batch": Batch()}

        ### Dependencies between variables 
        deps = []
        if self.data.hasNames():
            names = self.data.getNames()
            if len(names[0]) == len(names[1]) and re.search("^.* \[\[(?P<deps>[0-9,]*)\]\]$", names[0][0]) is not None:
                for name in names[0]:
                    deps.append(set(map(int, re.search("^.* \[\[(?P<deps>[0-9,]*)\]\]$", name).group("deps").split(","))))
        self.constraints.setDeps(deps)

    def initCharbon(self):
        if self.constraints.algo_family() == "trees":
            if self.data.hasMissing():
                self.logger.printL(1, "THE DATA CONTAINS MISSING VALUES, FALLING BACK TO GREEDY...", 'log', self.id)
                return CharbonGStd(self.constraints)
            else:
                return TREE_CLASSES.get(self.constraints.tree_mine_algo(), TREE_DEF)(self.constraints)

        else:
            if self.data.hasMissing():
                return CharbonGMiss(self.constraints)
            else:
                return CharbonGStd(self.constraints)

                            
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
        if "reds" in cust_params:
            reds = cust_params["reds"]
        elif "red" in cust_params:
            reds = [cust_params["red"]]
        else:
            reds = []
        if self.org_data is not None:
            for red in reds:
                red.recompute(self.data)

        if "side" in cust_params:
            self.souvenirs.cutOffSide(1-cust_params["side"])

        self.count = "C"

        self.logger.initProgressPart(self.constraints, self.souvenirs, reds, 1, self.id)
        self.logger.clockTic(self.id, "part run")        
        self.logger.printL(1, "Expanding...", 'status', self.id) ### todo ID

        partial = self.expandRedescriptions(reds)

        self.logger.clockTac(self.id, "part run", "%s" % self.questionLive())        
        if not self.questionLive():
            self.logger.printL(1, 'Interrupted...', 'status', self.id)
        else:
            self.logger.printL(1, 'Done...', 'status', self.id)
        self.logger.sendCompleted(self.id)
        return partial

    def full_run(self, cust_params={}):
        self.final["results"] = []
        self.final["batch"].reset()
        self.count = 0
        
        self.logger.printL(1, "Starting mining", 'status', self.id) ### todo ID

        #### progress initialized after listing pairs
        self.logger.clockTic(self.id, "pairs")
        self.initializeRedescriptions()
        self.logger.clockTac(self.id, "pairs")
        
        self.logger.clockTic(self.id, "full run")
        initial_red = self.initial_pairs.get(self.data, self.testIni)

        while initial_red is not None and self.questionLive():
            self.count += 1
            self.logger.clockTic(self.id, "expansion")
            self.logger.printL(1,"Expansion %d" % self.count, "log", self.id)
            partial = self.expandRedescriptions([initial_red])
            self.logger.updateProgress({"rcount": self.count}, 1, self.id)
            ## SOUVENIRS self.souvenirs.update(partial["batch"])

            if partial is not None:
                self.final["batch"].extend([partial["batch"][i] for i in partial["results"]])
            else:
                print "Partial NONE"
                
            self.final["results"] = self.final["batch"].selected(self.constraints.actions_final())

            self.logger.clockTac(self.id, "expansion", "%s" % self.questionLive())
            self.logger.printL(1, {"final":self.final["batch"]}, 'result', self.id)

            initial_red = self.initial_pairs.get(self.data, self.testIni)

        self.logger.clockTac(self.id, "full run", "%s" % self.questionLive())        
        if not self.questionLive():
            self.logger.printL(1, 'Interrupted...', 'status', self.id)
        else:
            self.logger.printL(1, 'Done...', 'status', self.id)
        self.logger.sendCompleted(self.id)
        return self.final


### HIGH LEVEL CALLING FUNCTIONS
################################

####################################################
#####      INITIAL PAIRS
####################################################

    def initializeRedescriptions(self, ids=None):
        self.initial_pairs.reset()
        if self.charbon.isTreeBased():
            self.initializeRedescriptionsTree(ids)
        else:
            self.initializeRedescriptionsGreedy(ids)

    def initializeRedescriptionsTree(self, ids=None):
        self.logger.printL(1, 'Searching for initial literals...', 'status', self.id)
        self.logger.initProgressFull(self.constraints, self.souvenirs, None, 1, self.id)
        
        if ids is None:
            ids = self.data.usableIds(self.constraints.min_itm_c(), self.constraints.min_itm_c())

        sides = [0,1]
        if self.data.isSingleD(): sides = [0]
        for side in sides:
            for idl in ids[side]:
                for (l,v) in self.charbon.computeInitTerm(self.data.col(side, idl)):
                    if side == 0:
                        self.initial_pairs.add(l, None, {"score":0, side: idl, 1-side: -1})
                    else:
                        self.initial_pairs.add(None, l, {"score":0, side: idl, 1-side: -1})
        self.initial_pairs.setMaxOut(-1)
        self.logger.printL(1, 'Found %i literals' % (len(self.initial_pairs)), "log", self.id)
        self.logger.sendCompleted(self.id)

        
    def initializeRedescriptionsGreedy(self, ids=None):
        self.initial_pairs.reset()

        ### Loading pairs from file if filename provided
        if not self.initial_pairs.loadFromFile():

            self.logger.printL(1, 'Searching for initial pairs...', 'status', self.id)
            explore_list = self.getInitExploreList(ids)
            self.logger.initProgressFull(self.constraints, self.souvenirs, explore_list, 1, self.id)

            total_pairs = len(explore_list)
            for pairs, (idL, idR, pload) in enumerate(explore_list):
                if not self.questionLive():
                    return

                self.logger.updateProgress({"rcount": self.count, "pair": pairs, "pload": pload})
                if pairs % 100 == 0:
                    self.logger.printL(3, 'Searching pair %d/%d (%i <=> %i) ...' %(pairs, total_pairs, idL, idR), 'status', self.id)
                    self.logger.updateProgress(level=3, id=self.id)
                if pairs % 10 == 5:

                    self.logger.printL(7, 'Searching pair %d/%d (%i <=> %i) ...' %(pairs, total_pairs, idL, idR), 'status', self.id)
                    self.logger.updateProgress(level=7, id=self.id)

                seen = []
                (scores, literalsL, literalsR) = self.charbon.computePair(self.data.col(0, idL), self.data.col(1, idR))
                for i in range(len(scores)):
                    if scores[i] >= self.constraints.min_pairscore() and (literalsL[i], literalsR[i]) not in seen:
                        seen.append((literalsL[i], literalsR[i]))
                        self.logger.printL(6, 'Score:%f %s <=> %s' % (scores[i], literalsL[i], literalsR[i]), "log", self.id)
                        self.initial_pairs.add(literalsL[i], literalsR[i], {"score": scores[i], 0: idL, 1: idR})
            self.logger.printL(1, 'Found %i pairs, will try at most %i' % (len(self.initial_pairs), self.constraints.max_red()), "log", self.id)
            self.logger.updateProgress(level=1, id=self.id)

            ### Saving pairs to file if filename provided
            self.initial_pairs.saveToFile()

        return self.initial_pairs

    def testIni(self, pair):
        if pair is None:
            return False
        return True
    
    def getInitExploreList(self, ids):
        explore_list = []
        if ids is None:
            ids = self.data.usableIds(self.constraints.min_itm_c(), self.constraints.min_itm_c())

        ### WARNING DANGEROUS few pairs for DEBUG!
        for idL in ids[0]:
            for idR in ids[1]:
                if ( not self.constraints.hasDeps() or \
                       len(self.constraints.getDeps(idR) & self.constraints.getDeps(idL)) == 0) and \
                       ( not self.data.isSingleD() or idR > idL or idR not in ids[0] or idL not in ids[1]): 
                    explore_list.append((idL, idR, self.getPairLoad(idL, idR)))
        return explore_list

    def getPairLoad(self, idL, idR):
        return max(1, self.data.col(0, idL).getNbValues()* self.data.col(1, idR).getNbValues()/50)
        # return PAIR_LOADS[self.data.col(0, idL).type_id-1][self.data.col(1, idR).type_id-1]


####################################################
#####      REDS EXPANSIONS
####################################################
    def expandRedescriptions(self, nextge):
        return ExpMiner(self.id, self.count, self.data, self.charbon, self.constraints, self.souvenirs, self.logger, self.questionLive).expandRedescriptions(nextge, self.partial, self.final)

#######################################################################
########### MULTIPROCESSING MINER
#######################################################################

import multiprocessing

class MinerDistrib(Miner):

    def full_run(self, cust_params={}):
        self.final["results"] = []
        self.final["batch"].reset()
        self.count = 0
        self.workers = {}
        self.rqueue = multiprocessing.Queue()
        
        self.logger.printL(1, "Starting mining", 'status', self.id) ### todo ID

        #### progress initialized after listing pairs
        self.logger.clockTic(self.id, "pairs")
        self.initializeRedescriptions()

        self.logger.clockTic(self.id, "full run")
        if self.charbon.isTreeBased():
            self.initializeExpansions()
        self.keepWatchDispatch()
        self.logger.clockTac(self.id, "full run", "%s" % self.questionLive())        
        if not self.questionLive():
            self.logger.printL(1, 'Interrupted...', 'status', self.id)
        else:
            self.logger.printL(1, 'Done...', 'status', self.id)
        self.logger.sendCompleted(self.id)
        return self.final

    def shareLogger(self):
        if not self.logger.usesOutMethods():
            return self.logger
        return None
        
    def initializeRedescriptionsGreedy(self, ids=None):
        self.initial_pairs.reset()
        self.pairs = 0
        ### Loading pairs from file if filename provided
        if not self.initial_pairs.loadFromFile():

            self.logger.printL(1, 'Searching for initial pairs...', 'status', self.id)
            explore_list = self.getInitExploreList(ids)
            self.logger.initProgressFull(self.constraints, self.souvenirs, explore_list, 1, self.id)
            
            self.total_pairs = len(explore_list)
            explore_list.sort(key=lambda x:x[-1], reverse =True)
            batch_size = (self.total_pairs-10) / (self.max_processes-1) 
            pairs = 0
            K = self.max_processes
            for k in range(K-1):
                # print k, len(explore_list[k*batch_size:(k+1)*batch_size])
                self.workers[k] = PairsProcess(k, explore_list[k*batch_size:(k+1)*batch_size], self.charbon, self.data, self.rqueue)
            # print K-1, len(explore_list[(K-1)*batch_size:])
            self.workers[K-1] = PairsProcess(K-1, explore_list[(K-1)*batch_size:], self.charbon, self.data, self.rqueue)

            self.pairWorkers = len(self.workers)
        return self.initial_pairs


    def initializeExpansions(self):
        for k in set(range(self.max_processes)).difference(self.workers.keys()):
            initial_red = self.initial_pairs.get(self.data, self.testIni)
            if initial_red is not None and self.questionLive():
                self.count += 1
                self.logger.printL(1,"Expansion %d" % self.count, "log", self.id)
                self.logger.clockTic(self.id, "expansion_%d-%d" % (self.count,k))
                self.workers[k] = ExpandProcess(k, self.id, self.count, self.data,
                                                self.charbon, self.constraints,
                                                self.souvenirs, self.rqueue, [initial_red],
                                                final=self.final, logger=self.shareLogger())

       
    def handlePairResult(self, m):
        scores, literalsL, literalsR, idL, idR, pload = m["scores"], m["lLs"], m["lRs"], m["idL"], m["idR"], m["pload"]
        self.pairs += 1
        self.logger.updateProgress({"rcount": 0, "pair": self.pairs, "pload": pload})
        if self.pairs % 100 == 0:
            self.logger.printL(3, 'Searching pair %d/%d (%i <=> %i) ...' %(self.pairs, self.total_pairs, idL, idR), 'status', self.id)
            self.logger.updateProgress(level=1, id=self.id)

        if self.pairs % 10 == 5:
                            
            self.logger.printL(7, 'Searching pair %d/%d (%i <=> %i) ...' %(self.pairs, self.total_pairs, idL, idR), 'status', self.id)
            self.logger.updateProgress(level=7, id=self.id)

        for i in range(len(scores)):
            if scores[i] >= self.constraints.min_pairscore():
                self.logger.printL(6, 'Score:%f %s <=> %s' % (scores[i], literalsL[i], literalsR[i]), "log", self.id)
                self.initial_pairs.add(literalsL[i], literalsR[i], {"score": scores[i], 0: idL, 1: idR})

    def handleExpandResult(self, m):
        self.final["batch"].extend([m["out"]["batch"][i] for i in m["out"]["results"]])
        self.final["results"] = self.final["batch"].selected(self.constraints.actions_final())
        self.souvenirs.update(m["out"]["batch"])
        
        self.logger.clockTac(self.id, "expansion_%d-%d" % (m["count"], m["id"]), "%s" % self.questionLive())
        self.logger.printL(1, {"final":self.final["batch"]}, 'result', self.id)
        self.logger.updateProgress({"rcount": m["count"]}, 1, self.id)
        
    def keepWatchDispatch(self):
        while len(self.workers) > 0 and self.questionLive():
            m = self.rqueue.get()
            if m["what"] == "done":
                del self.workers[m["id"]]
                self.pairWorkers -= 1
                self.initializeExpansions()

                if self.pairWorkers == 0:
                    self.logger.updateProgress({"rcount": 0}, 1, self.id)
                    self.logger.clockTac(self.id, "pairs")
                    self.logger.printL(1, 'Found %i pairs, will try at most %i' % (len(self.initial_pairs), self.constraints.max_red()), "log", self.id)
                    self.logger.updateProgress(level=1, id=self.id)
                    self.initial_pairs.saveToFile()
                
            elif m["what"] == "pairs":
                self.handlePairResult(m)

            elif m["what"] == "expansion":
                self.handleExpandResult(m)
                del self.workers[m["id"]]
                self.initializeExpansions()

    
class PairsProcess(multiprocessing.Process):
    def __init__(self, sid, explore_list, charbon, data, rqueue):
        multiprocessing.Process.__init__(self)
        self.daemon = True
        self.id = sid
        self.explore_list = explore_list
        self.charbon = charbon
        self.data = data
        self.queue = rqueue
        self.start()

    def run(self):
        for pairs, (idL, idR, pload) in enumerate(self.explore_list):
            (scores, literalsL, literalsR) = self.charbon.computePair(self.data.col(0, idL), self.data.col(1, idR))
            self.queue.put({"id": self.id, "what": "pairs", "lLs": literalsL, "lRs": literalsR, "idL": idL, "idR": idR, "scores": scores, "pload": pload})
        self.queue.put({"id": self.id, "what": "done"})

class ExpandProcess(multiprocessing.Process, ExpMiner):
    
    def __init__(self, sid, ppid, count, data, charbon, constraints, souvenirs, rqueue,
                 nextge, partial=None, final=None, logger=None,
                 question_live=None):
        multiprocessing.Process.__init__(self)
        self.daemon = True
        self.id = sid
        self.ppid = ppid
        self.count = count
        
        self.charbon = charbon
        self.data = data
        self.queue = rqueue

        self.constraints = constraints
        self.souvenirs = souvenirs
        self.upSouvenirs = False
        self.question_live = question_live
        if logger is None:
            self.logger = DummyLog()
        else:
            self.logger = logger

        self.nextge= nextge
        self.partial= partial
        self.final= final
        self.start()

    def run(self):
        partial = self.expandRedescriptions(self.nextge, partial=self.partial, final=self.final)
        self.queue.put({"id": self.id, "what": "expansion", "out": partial, "count": self.count})



#######################################################################
########### MINER INSTANCIATION
#######################################################################

def instMiner(data, params, logger=None, mid=None, souvenirs=None, qin=None, cust_params={}):
    if params["nb_processes"]["data"] > 1:
        return MinerDistrib(data, params, logger, mid, souvenirs, qin, cust_params)
    else:
        return Miner(data, params, logger, mid, souvenirs, qin, cust_params)



