import random, numpy, os.path, re

try:
    from toolLog import Log
    from classContent import BatchCollection
    from classRedescription import Redescription
    from classExtension import ExtensionError, newExtensionsBatch
    from classSouvenirs import Souvenirs
    from classConstraints import Constraints
    from classInitialCands import initCands

    from classCharbonXFIM import CharbonXFIM
    from classCharbonGMiss import CharbonGMiss
    from classCharbonGStd import CharbonGStd
    from classCharbonTAlt import CharbonTCW, CharbonTSprit, CharbonTSplit
    from classCharbonTLayer import CharbonTLayer
except ModuleNotFoundError:
    from .toolLog import Log
    from .classContent import BatchCollection
    from .classRedescription import Redescription
    from .classExtension import ExtensionError, newExtensionsBatch
    from .classSouvenirs import Souvenirs
    from .classConstraints import Constraints
    from .classInitialCands import initCands

    from .classCharbonXFIM import CharbonXFIM
    from .classCharbonGMiss import CharbonGMiss
    from .classCharbonGStd import CharbonGStd
    from .classCharbonTAlt import CharbonTCW, CharbonTSprit, CharbonTSplit
    from .classCharbonTLayer import CharbonTLayer

import pdb

XAUST_CLASSES = {"fim": CharbonXFIM}
XAUST_DEF = CharbonXFIM
TREE_CLASSES = { "layeredtrees": CharbonTLayer,
                 "cartwheel": CharbonTCW,
                 "splittrees": CharbonTSplit,
                 "sprit": CharbonTSprit}
TREE_DEF = CharbonTLayer

CHARBON_MISS_FORCE = False

# PAIR_LOADS = [[1,2,3],
#               [2,4,6],
#               [3,6,10]]

class DummyLog(object):
    verbosity = 0
    def printL(self, level, message, type_message="*", source=None):
        pass
    def updateProgress(self, details, level=-1, id=None):
        pass
    def logResults(self, rcollect, lid, pid):
        pass
    
class RCollection(BatchCollection, Souvenirs):
    name_class = "R"
    def __init__(self, nAvailableMo=None, nAmnesic=False):
        Souvenirs.__init__(self, nAvailableMo, nAmnesic)
        BatchCollection.__init__(self)
        ### prepare buffer list
        self.newList(iid="F")
        self.newList(iid="P")
        self.newList(iid="W")

    def toShare(self):
        return RCollection(self.copyAvailableCols(), self.isAmnesic())
        
    def __str__(self):
        svrs = ""
        if self.isActive():
            svrs = ", " + Souvenirs.__str__(self)
        return "RCollection: %d items in W=%d/P=%d/F=%d, %d tracks%s" % (self.nbItems(), self.getLen("W"), self.getLen("P"), self.getLen("F"), self.nbTracks(), svrs)
        
    def resetWorking(self, reds=[]):
        self.clearList("W")
        for red in reds:
            self.addItem(red, "W")                
        
    def resetPartial(self, reds=[]):
        self.clearList("P")
        self.resetWorking(reds)
                
    def resetFinal(self, reds=[]):
        self.clearList("F")
        self.resetPartial(reds)

def dispTracksEnd(logger, rcollect, pid):
    logger.printL(1, "=========================================", "log", pid)
    logger.printL(1, rcollect.tracksToStr(), "log", pid)
    logger.printL(1, "----- REDS:", "log", pid)
    fids = rcollect.getIidsList("F")
    for i in rcollect.getItems():
        prefix = "+" if i.getUid() in fids else "-"
        logger.printL(1, "%s %s" % (prefix, i), "log", pid)

        
        
class ExpMiner(object):
    def __init__(self, pid, count, data, charbon, constraints, logger=None, question_live=None):
        self.charbon = charbon
        self.data = data
        self.count = count
        self.pid = pid
        self.constraints = constraints
        self.upSouvenirs = False
        self.question_live = question_live
        if logger is None:
            self.logger = DummyLog()
        else:
            self.logger = logger

    def getId(self):
        return self.pid
    def getLogId(self):
        return "%s" % self.getId()

    def questionLive(self):
        if self.question_live is None:
            return True
        return self.question_live()

    def initGreedyCharbon(self):
        if self.constraints.getCstr("add_condition"):
            if not self.data.isConditional() and self.data.isGeospatial():
                self.data.prepareGeoCond()
            ## self.charbon_alt = CharbonGMiss(self.constraints)
            ### CHARBON
        if CHARBON_MISS_FORCE or self.data.hasMissing():
            return CharbonGMiss(self.constraints, logger=self.shareLogger())
        else:
            return CharbonGStd(self.constraints, logger=self.shareLogger())
    
    def expandRedescriptions(self, nextge, rcollect=None):
        if len(nextge) > 0 and self.questionLive():
            if rcollect is None:                
                rcollect = RCollection()
            rcollect.resetPartial(nextge)
            if self.charbon.isTreeBased():
                return self.expandRedescriptionsTree(nextge, rcollect)
            else:
                return self.expandRedescriptionsGreedy(nextge, rcollect)
        return rcollect
            
    def expandRedescriptionsTree(self, nextge, rcollect):
        for redi, red in enumerate(nextge):
            self.logger.printL(2, "Expansion %s.%s\t%s" % (self.count, redi, red), 'status', self.getLogId())
            kids = self.charbon.computeExpandTree(-1, self.data, red)
            self.logger.printL(2, "Expansion returned %s redescriptions" % len(kids), 'status', self.getLogId())
            kid_ids = []
            for kid in kids:
                self.logger.printL(2, kid, 'status', self.getLogId())
                rcollect.addItem(kid, "W")
                kid_ids.append(kid.getUid())
            if len(kid_ids) > 0:
                track = {"do": "expand-tree", "trg": kid_ids, "src": [red.getUid()], "out": "W"}
                rcollect.addTrack(track)

            # self.logger.updateProgress({"rcount": self.count, "redi": redi}, 4, self.getLogId())
            self.logger.printL(4, "Candidate %s.%d.%d grown" % (self.count, len(red), redi), 'status', self.getLogId())
        self.logger.printL(4, "Generation %s.%d expanded" % (self.count, len(red)), 'status', self.getLogId())

        ### extra selection step for tree-based to check not repeating itself
        sel = rcollect.selected(self.constraints.getActionsList("partial"), ids="W")
        Xsel = rcollect.selected(self.constraints.getActionsList("tree_rectangles"), ids="F", new_ids=sel, new_only=True, trg_lid="P")
        self.logger.logResults(rcollect, "P", self.getLogId())
        return rcollect

    
    def expandRedescriptionsGreedy(self, nextge, rcollect):
        first_round = True
        max_var = [self.constraints.getCstr("max_var", side=0), self.constraints.getCstr("max_var", side=1)]
        for r in nextge:
            r.initAvailable(rcollect, self.data, max_var)
        
        while len(nextge) > 0:
            kids = set()
            redi = 0

            while redi < len(nextge):
                red = nextge[redi]
                if first_round:
                    self.logger.printL(2, "Expansion %s.%s\t%s" % (self.count, redi, red), 'status', self.getLogId())
                ### To know whether some of its extensions were found already
                red.updateAvailable(rcollect)

                if red.hasAvailableCols():
                    exts, basis_red, modr = red.prepareExtElems(self.data, self.data.isSingleD(), souvenirs=rcollect)
                    if modr != 0:
                        if modr == 1:
                            rcollect.addItem(basis_red, "W")
                            track = {"do": "prepare-greedy", "trg": [basis_red.getUid()], "src": [red.getUid()], "out": "W"}
                            rcollect.addTrack(track)
                        red.cutOffAvailables()
                    bests = newExtensionsBatch(self.data.nbRows(), self.constraints, basis_red)
                        
                    ### WARNING DANGEROUS few extensions for DEBUG!
                    for (side, v, r) in exts:
                        if not self.questionLive():
                            nextge = []                        
                        else:
                            tmp_cands = self.charbon.computeExpand(side, self.data.col(side,v), r, self.data.getColsC())
                            bests.update(tmp_cands)

                    if self.logger.verbosity >= 4:
                        self.logger.printL(4, bests, "log", self.getLogId())

                    try:
                        kids = bests.improvingKids(self.data)

                    except ExtensionError as details:
                        self.logger.printL(1,"OUILLE! Something went badly wrong during expansion of %s.%d.%d\n--------------\n%s\n--------------" % (self.count, len(red), redi, details.value), "log", self.getLogId())
                        kids = []

                    kid_ids = []
                    for kid in kids:
                        rcollect.addItem(kid, "W")
                        kid_ids.append(kid.getUid())
                    if len(kid_ids) > 0:
                        track = {"do": "expand-greedy", "trg": kid_ids, "src": [basis_red.getUid()], "out": "W"}
                        rcollect.addTrack(track)
                        
                    ## SOUVENIRS
                    if self.upSouvenirs:
                        rcollect.updateSeen(kids)

                    ### parent has been used remove availables
                    basis_red.cutOffAvailables()
                # self.logger.updateProgress({"rcount": self.count, "generation": len(red), "cand": redi}, 4, self.getLogId())
                self.logger.printL(4, "Candidate %s.%d.%d expanded" % (self.count, len(red), redi), 'status', self.getLogId())
                redi += 1

            first_round = False
            self.logger.printL(4, "Generation %s.%d expanded" % (self.count, len(red)), 'status', self.getLogId())
            rcollect.turnTrackOff()
            nextge_keys = rcollect.selected(self.constraints.getActionsList("nextge"), ids="W", verbosity=8)
            rcollect.turnTrackOn()

            nextge = [rcollect.getItem(i) for i in nextge_keys]
            for iid in rcollect.getIids():
                if iid not in nextge_keys:
                    rcollect.getItem(iid).cutOffAvailables()
            

        ### Do before selecting next gen to allow tuning the beam
        ### ask to update results
        rcollect.selected(self.constraints.getActionsList("partial"), ids="W", trg_lid="P")
        self.logger.logResults(rcollect, "P", self.getLogId())
        return rcollect
                    
    def improveRedescriptions(self, nextge, rcollect=None):
        if len(nextge) == 0 or not self.questionLive():
            return rcollect

        charbon = self.initGreedyCharbon()
        if rcollect is None:                
            rcollect = RCollection()
        rcollect.resetPartial()

        nbS = 0
        for red in nextge:
            if self.questionLive():
                rcollect.resetWorking()
                non_anons = [red]
                if red.containsAnon():
                    pids = self.setAnonRedescription(red, rcollect, charbon, trg_lid="W")
                    non_anons = [rcollect.getItem(iid) for iid in pids]
                    
                for r in non_anons:
                    self.improveRedescription(r, rcollect, charbon, trg_lid="W")

                rcollect.addItem(red, "P")
                if rcollect.getLen("W") > 0:
                    rcollect.selected(self.constraints.getActionsList("partial"), ids="W", trg_lid="P")

                self.logger.logResults(rcollect, "P", self.getLogId())
                # rcollect.logResults( "W", self.getId())
        return rcollect
                    
    def improveRedescription(self, red, rcollect, charbon, skip={}, round_id=0, trg_lid=None, track_rounds=[], try_shorten=True):
        # print("-----------------", round_id, track_rounds)
        # print("IMPRV -(0:0)-\t%s" % red)
        bests = []
        best_score = red.score()
        got_better = False
        for side in [0, 1]:
            queries = [red.query(0), red.query(1)]
            org_q = red.query(side)
            for (ls, q) in org_q.minusOneLiteral():
                if (side, ls, round_id) in skip:
                    ### no need to try improving the same element as previous round
                    continue

                xps = self.improveRedescriptionElement(charbon, queries, side, org_q, ls)
                for cand in xps:
                    if cand["red"].score() > best_score:
                        got_better = True
                        bests = [cand]
                        best_score = cand["red"].score()
                    elif got_better and cand["red"].score() == best_score:
                        bests.append(cand)
                        
                if len(q) > 0 and try_shorten:
                    queries[side] = q
                    cand_red = Redescription.fromQueriesPair(queries, self.data)
                    if cand_red.score() > red.score():
                        bests.append({"red": cand_red, "side": side, "ls": ls, "lit": None})
                        
        kid_ids = []
        desc_ids = []
        for ci, best in enumerate(bests):
            # if round_id < 50:
            #     print("%s|_ (%d:%d:%d)%s\t%s" % (" "*round_id, ci, best["lit"] is None, best["red"].getUid(), " "*(50-round_id), best["red"]))
            # else:
            #     print("[...]")
            kid_ids.append(best["red"].getUid())
        if len(kid_ids) > 0:
            track = {"do": "improve", "trg": kid_ids, "src": [red.getUid()], "out": trg_lid}
            rcollect.addTrack(track)

        for ci, best in enumerate(bests):
            rcollect.addItem(best["red"], trg_lid)

            skip_next ={(best["side"], best["ls"], round_id+1): best["red"].score()}
            desc_ids.extend(self.improveRedescription(best["red"], rcollect, charbon, skip_next, round_id+1, trg_lid=trg_lid, track_rounds=[ci]+track_rounds, try_shorten=try_shorten))
            
        return kid_ids+desc_ids


    def setAnonRedescription(self, red, rcollect, charbon, first_round=True, trg_lid=None):
        kid_ids = []
        desc_ids = []

        bests = []
        best_score = 0.
        qs, ls = red.minusAnon()
        if (len(qs[0]) * len(qs[1]) > 0) and (len(ls[0]) + len(ls[1]) > 0):
            noan_red = Redescription.fromQueriesPair(qs, self.data)
            best_score = noan_red.score()

            if first_round:
                kid_ids.append(noan_red.getUid())
                rcollect.addItem(noan_red, trg_lid)

        for side in [0, 1]:
            queries = [red.query(0), red.query(1)]
            org_q = red.query(side)
            for (q, org_ls, lit, ls) in org_q.minusAnonButOne():

                xps = self.improveRedescriptionElement(charbon, queries, side, q, ls)
                for cand in xps:
                    cand["org_ls"] = org_ls
                    if cand["red"].score() > best_score:
                        bests = [cand]
                        best_score = cand["red"].score()
                    elif len(bests) > 0 and cand["red"].score() == best_score:
                        bests.append(cand)


        for ci, best in enumerate(bests):
            kid_ids.append(best["red"].getUid())
        if len(kid_ids) > 0:
            track = {"do": "set-anonymous", "trg": kid_ids, "src": [red.getUid()], "out": trg_lid}
            rcollect.addTrack(track)

        for ci, best in enumerate(bests):            
            rcollect.addItem(best["red"], trg_lid)
            
            queries = [red.query(0), red.query(1)]
            cand_q = queries[best["side"]].copy()
            cand_q.setBukElemAt(best["lit"], best["org_ls"])
            queries[best["side"]] = cand_q
            cand_red = Redescription.fromQueriesPair(queries, self.data)                
            desc_ids.extend(self.setAnonRedescription(cand_red, rcollect, charbon, first_round=False, trg_lid=trg_lid))
        return kid_ids+desc_ids

    def improveRedescriptionElement(self, charbon, queries, side, org_q, ls):
        xps = []
                            
        lit = org_q.getBukElemAt(ls)
        op, qc, qd = org_q.partsOCD(ls)

        ext_op = False ### default use conjunction
        offsets = (0,0)
        if len(qc) == 0:
            ext_op = True ### use disjunction
            queries[side] = qd
            red_basis = Redescription.fromQueriesPair(queries, self.data)
            supports = red_basis.supports().copy() 
        else:
            queries[side] = qc
            red_basis = Redescription.fromQueriesPair(queries, self.data)
            supports = red_basis.supports().copy() 
            if len(qd) > 0:
                supp_mask, miss_mask = qd.recompute(side, self.data)
                mlparts = supports.moveInterAllOut(side, supp_mask)
                num = supports.getSSetts().sumPartsId(side, supports.getSSetts().IDS_num[True], mlparts)
                den = supports.getSSetts().sumPartsId(side, supports.getSSetts().IDS_den[True], mlparts)
                offsets = (num, den)
                    
        # #### SEARCH FOR IMPROVEMENT
        col = self.data.col(side, lit.colId())
        tmp_cands = charbon.getCandidatesImprov(side, col, red_basis, ext_op, supports, offsets)
        if len(tmp_cands) > 1:
            print("Multi")
            pdb.set_trace()

        for cand in tmp_cands:
            cand_q = org_q.copy()
            cand_q.setBukElemAt(cand.getLiteral(), ls)
            queries[side] = cand_q
            cand_red = Redescription.fromQueriesPair(queries, self.data)
            xps.append({"red": cand_red, "side": side, "ls": ls, "lit": cand.getLiteral()})                
        return xps
            
class Miner(object):

### INITIALIZATION
##################
    def __init__(self, data, params, logger=None, mid=None, qin=None, cust_params={}):
        self.count = "-"
        self.qin = qin
        self.org_data = None
        self.want_to_live = True
        if mid is not None:
            self.id = mid
        else:
            self.id = 1
        self.data = data

        self.max_processes = params["nb_processes"]["data"]
        self.pe_balance = params["pe_balance"]["data"]

        #### SETTING UP DATA
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

        keep_rows = None
        if self.data.hasSelectedRows() or self.data.hasLT():
            keep_rows = self.data.getVizRows({"rset_id": "learn"})
            if "weights" not in cust_params:
                row_ids = dict([(v,[k]) for (k,v) in enumerate(keep_rows)])
            
        if "weights" in cust_params:
            row_ids = {}
            off = 0
            for (old, mul) in cust_params["weights"].items():
                if keep_rows is None or old in keep_rows:
                    row_ids[old] = [off+r for r in range(mul)]
                    off += mul

        if row_ids is not None:
            self.org_data = self.data
            self.data = self.data.subset(row_ids)

        if logger is not None:
            self.logger = logger
        else:
             self.logger = Log()
        self.constraints = Constraints(params, self.data)

        self.charbon = self.initCharbon()
        pairs_store = None
        if "pairs_store" in params and len(params["pairs_store"]["data"]) > 0:
            pairs_store = params["pairs_store"]["data"]
        self.initial_candidates = initCands(self.constraints.getCstr("pair_sel"), self.constraints.getCstr("max_inits"), save_filename=pairs_store,
                                           data=self.data)
        self.rcollect = RCollection(self.data.usableIds(self.constraints.getCstr("min_itm_c"), self.constraints.getCstr("min_itm_c")), self.constraints.getCstr("amnesic"))
        self.logger.printL(1, "Miner set up...\n\t%s\n\t%s" % (self.data, self.rcollect), 'log', self.getLogId())
        

    def getId(self):
        return self.id
    def getLogId(self):
        return "%s" % self.getId()
    
    def shareRCollect(self):
        return self.rcollect.toShare()

    def shareLogger(self):
        return self.logger
        # if not self.logger.usesOutMethods():
        #     return self.logger
        # return None
    
    def initGreedyCharbon(self):
        if self.constraints.getCstr("add_condition"):
            if not self.data.isConditional() and self.data.isGeospatial():
                self.data.prepareGeoCond()
            ## self.charbon_alt = CharbonGMiss(self.constraints)
            ### CHARBON
        if CHARBON_MISS_FORCE or self.data.hasMissing():
            return CharbonGMiss(self.constraints)
        else:
            return CharbonGStd(self.constraints)
       
    def initCharbon(self):
        if self.constraints.getCstr("mining_algo") in TREE_CLASSES:
            if self.data.hasMissing():
                self.logger.printL(1, "THE DATA CONTAINS MISSING VALUES, FALLING BACK ON GREEDY REREMI...", 'log', self.getLogId())
                return CharbonGMiss(self.constraints, logger=self.shareLogger())
            else:
                return TREE_CLASSES.get(self.constraints.getCstr("mining_algo"), TREE_DEF)(self.constraints, logger=self.shareLogger())
        elif self.constraints.getCstr("mining_algo") in XAUST_CLASSES:
            return XAUST_CLASSES.get(self.constraints.getCstr("mining_algo"), XAUST_DEF)(self.constraints, logger=self.shareLogger())
        return self.initGreedyCharbon()                            
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
        return BatchCollection(redescs).selectedItems(self.constraints.getActionsList("redundant"))

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

        rcollect = self.shareRCollect()
        if "side" in cust_params:
            rcollect.cutOffSide(1-cust_params["side"])

        self.count = "C"

        self.logger.initProgressPart(self.constraints, reds, rcollect.getNbAvailableCols(), 1, self.getLogId())
        self.logger.clockTic(self.getLogId(), "part run")        

        if cust_params.get("task") == "improve":
            self.logger.printL(1, "Improving...", 'status', self.getLogId()) ### todo ID
            rcollect = self.improveRedescriptions(reds, rcollect)
        else:
            self.logger.printL(1, "Expanding...", 'status', self.getLogId()) ### todo ID
            rcollect = self.expandRedescriptions(reds, rcollect)

        self.logger.clockTac(self.getLogId(), "part run", "%s" % self.questionLive())        
        if not self.questionLive():
            self.logger.printL(1, 'Interrupted...', 'status', self.getLogId())
        else:
            self.logger.printL(1, 'Done...', 'status', self.getLogId())
        self.logger.sendCompleted(self.getLogId())
        # print(rcollect)
        return rcollect

    def full_run(self, cust_params={}):
        self.rcollect.resetFinal()
        self.count = 0
        self.logger.printL(1, "Starting mining", 'status', self.getLogId()) ### todo ID
        #### progress initialized after listing pairs
        self.logger.clockTic(self.getLogId(), "pairs")
        self.initializeRedescriptions()
        self.logger.clockTac(self.getLogId(), "pairs")
        self.logger.clockTic(self.getLogId(), "full run")
        
        self.doExpansions(cust_params)
        self.logger.clockTac(self.getLogId(), "full run", "%s" % self.questionLive())        
        if not self.questionLive():
            self.logger.printL(1, 'Interrupted...', 'status', self.getLogId())
        else:
            self.logger.printL(1, 'Done...', 'status', self.getLogId())
        self.logger.sendCompleted(self.getLogId())
        dispTracksEnd(self.logger, self.rcollect, self.getLogId())
        return self.rcollect

    def doExpansions(self, cust_params={}):
        if self.charbon.isIterative():
            self.doExpansionsIterative(cust_params)
        else:
            self.doExpansionsGlobal(cust_params)

    def doExpansionsGlobal(self, cust_params={}):
        initial_candidates, scs = self.initial_candidates.getAllTerms(self.data, self.testIni)
        if len(initial_candidates) > 0 and self.questionLive():
        
            self.logger.clockTic(self.getLogId(), "fim_exp")
            self.logger.printL(1,"FIM expansion starting", "log", self.getLogId())

            kids = self.charbon.computeExpansions(self.data, initial_candidates) ###
            self.logger.printL(2, "FIM expansion returned %s redescriptions" % len(kids), 'status', self.getLogId())
            kid_ids = []
            for kid in kids:
                self.logger.printL(2, kid, 'status', self.getLogId())
                self.rcollect.addItem(kid, "W")
                kid_ids.append(kid.getUid())
            if len(kid_ids) > 0:
                track = {"do": "fim-expand", "trg": kid_ids, "src": [], "out": "W"}
                self.rcollect.addTrack(track)
            self.logger.printL(4, "FIM expansion done", 'status', self.getLogId())

            self.rcollect.selected(self.constraints.getActionsList("partial", action_substitute=("cut", None)), ids="W", trg_lid="P")
            self.logger.logResults(self.rcollect, "P", self.getLogId())
        
            # self.logger.clockTic(self.getLogId(), "select")
            if self.rcollect.getLen("P") > 0:
                self.rcollect.selected(self.constraints.getActionsList("final"), ids="F", new_ids="P", trg_lid="F")

            self.logger.clockTac(self.getLogId(), "fim_exp", "%s" % self.questionLive())
            self.logger.logResults(self.rcollect, "F", self.getLogId())
                
           
    def doExpansionsIterative(self, cust_params={}):
        check_score = not self.charbon.isTreeBased()
        nb_round = 0
        initial_red = None
        try:
            initial_red = self.initial_candidates.get(self.data, self.testIni, check_score=check_score)
        except ExtensionError as details:
            self.logger.printL(1,"OUILLE! Something went badly wrong with initial candidate %s\n--------------\n%s\n--------------" % (self.count, details.value), "log", self.getLogId())
        # print("THRESHOLDS [%s, %s]" % (self.constraints.getCstr("min_itm_in"), self.constraints.getCstr("min_itm_out")))
        while initial_red is not None and self.questionLive():
            self.count += 1
        
            self.logger.clockTic(self.getLogId(), "expansion_%d-%d" % (self.count,0))
            self.logger.printL(1,"Expansion %d" % self.count, "log", self.getLogId())
            self.expandRedescriptions([initial_red], self.rcollect)
            self.logger.updateProgress({"rcount": self.count}, 1, self.getLogId())
        
            # self.logger.clockTic(self.getLogId(), "select")
            if self.rcollect.getLen("P") > 0:
                self.rcollect.selected(self.constraints.getActionsList("final"), ids="F", new_ids="P", trg_lid="F")

            # self.final["results"] = self.final["batch"].selected(self.constraints.getActionsList("final"))
            # if (self.final["results"] != ttt):
            #     pdb.set_trace()
            #     print("Not same")

            ### DEBUG self.final["results"] = range(len(self.final["batch"]))
            # self.logger.clockTac(self.getLogId(), "select")

            self.logger.clockTac(self.getLogId(), "expansion_%d-%d" % (self.count,0), "%s" % self.questionLive())
            self.logger.logResults(self.rcollect, "F", self.getLogId())
            check_score = not self.charbon.isTreeBased()
            try:
                initial_red = self.initial_candidates.get(self.data, self.testIni, check_score=check_score)
            except ExtensionError as details:
                self.logger.printL(1,"OUILLE! Something went badly wrong with initial candidate %s\n--------------\n%s\n--------------" % (self.count, details.value), "log", self.getLogId())

                

### HIGH LEVEL CALLING FUNCTIONS
################################

####################################################
#####      INITIAL PAIRS
####################################################

    def initializeRedescriptions(self, ids=None):
        self.initial_candidates.reset()
        if self.charbon.withInitTerms():
            self.initializeTerms(ids)
        else:
            self.initializePairs(ids)

    def initializeTerms(self, ids=None):
        self.logger.printL(1, 'Searching for initial terms...', 'status', self.getLogId())
        self.logger.initProgressFull(self.constraints, None, self.rcollect.getNbAvailableCols(), 1, self.getLogId())
        
        if ids is None:
            ids = self.data.usableIds(self.constraints.getCstr("min_itm_c"), self.constraints.getCstr("min_itm_c"))

        sides = [0,1]
        if self.data.isSingleD(): sides = [0]
        for side in sides:
            for idl in ids[side]:
                iTerms = self.charbon.computeInitTerms(self.data.col(side, idl))
                self.logger.printL(10, 'Generated %d initial terms from variable %d %d' % (len(iTerms), side, idl), 'status', self.getLogId())
                for (l,v) in iTerms:
                    if side == 0:
                        self.initial_candidates.add(l, None, {"score":v, side: idl, 1-side: -1})
                    else:
                        self.initial_candidates.add(None, l, {"score":v, side: idl, 1-side: -1})
        self.initial_candidates.setMaxOut(self.constraints.getCstr("max_inits"))
        # self.initial_candidates.setMaxOut(-1) ### DEBUG
        self.logger.printL(1, 'Found %i initial terms, will try at most %i (ordered by decreasing support)' % (len(self.initial_candidates), self.constraints.getCstr("max_inits")), "log", self.getLogId())
        # self.logger.sendCompleted(self.getLogId())

        
    def initializePairs(self, ids=None):
        self.initial_candidates.reset()

        ##### SELECTION USING FOLDS
        # folds = numpy.array(self.data.col(0,-1).getVector())
        # counts_folds = 1.*numpy.bincount(folds) 
        # nb_folds = len(counts_folds)
        
        ### Loading pairs from file if filename provided
        loaded, done = self.initial_candidates.loadFromLogFile(self.data)
        if not loaded or done is not None:

            self.logger.printL(1, 'Searching for initial pairs...', 'status', self.getLogId())
            explore_list = self.getInitExploreList(ids, done)
            self.logger.initProgressFull(self.constraints, explore_list, self.rcollect.getNbAvailableCols(), 1, self.getLogId())

            self.initial_candidates.setExploreList(explore_list, done=done)
            total_pairs = len(explore_list)
            for pairs, (idL, idR, pload) in enumerate(explore_list):
                if not self.questionLive():
                    ## self.initial_candidates.saveToFile()
                    return
                self.logger.updateProgress({"rcount": self.count, "pair": pairs, "pload": pload})
                if pairs % 100 == 0:
                    self.logger.printL(3, 'Searching pair %d/%d (%i <=> %i) ...' %(pairs, total_pairs, idL, idR), 'status', self.getLogId())
                    self.logger.updateProgress(level=3, id=self.getLogId())
                if pairs % 10 == 5:
                    self.logger.printL(7, 'Searching pair %d/%d (%i <=> %i) ...' %(pairs, total_pairs, idL, idR), 'status', self.getLogId())
                    self.logger.updateProgress(level=7, id=self.getLogId())
                else:
                    self.logger.printL(10, 'Searching pair %d/%d (%i <=> %i) ...' %(pairs, total_pairs, idL, idR), 'status', self.getLogId())
                    
                seen = []
                pairs = self.charbon.computePair(self.data.col(0, idL), self.data.col(1, idR), self.data.getColsC())
                for i, pair in enumerate(pairs):
                    if pair["score"] >= self.constraints.getCstr("min_pairscore") and (pair["litL"], pair["litR"]) not in seen:
                        seen.append((pair["litL"], pair["litR"]))
                        self.logger.printL(6, 'Score:%f %s <=> %s %s' % (pair["score"], pair["litL"], pair["litR"], " & ".join(["%s" % l for l in pair.get("litC", ["-"])])), "log", self.getLogId())
                        pair.update({0: idL, 1: idR})
                        self.initial_candidates.add(pair["litL"], pair["litR"], pair)
                        # ########
                        # ######## Filter pair candidates on folds distribution
                        # rr = Redescription.fromInitialPair((literalsL[i], literalsR[i]), self.data)
                        # bcount = numpy.bincount(folds[list(rr.getSuppI())], minlength=nb_folds)
                        # if len(numpy.where(bcount > 0)[0]) > 1:
                        #     bb = bcount/counts_folds
                        #     # bpr = bcount/float(numpy.sum(bcount))
                        #     # entropS = -numpy.sum(numpy.log(bpr)*bpr)
                        #     bpr = bb/numpy.max(bb)
                        #     score = numpy.sum(bpr)
                        #     # entropM = -numpy.sum(numpy.log(bpr)*bpr)
                        #     if score > 1.5:
                        #         self.logger.printL(6, '\tfolds count: %f, %d, %s' % (score, numpy.sum(bcount), bcount), "log", self.getLogId())
                        #         ####
                        #         # self.initial_candidates.add(literalsL[i], literalsR[i], {"score": scores[i], 0: idL, 1: idR})
                        #         self.initial_candidates.add(literalsL[i], literalsR[i], {"score": score, 0: idL, 1: idR})
                        # # if pairs % 50 == 0 and pairs > 0:
                        # #     exit()
                    elif (idL, idR) == (0,3):
                        self.logger.printL(6, '---- Score:%f %s <=> %s %s' % (pair["score"], pair["litL"], pair["litR"], " & ".join(["%s" % l for l in pair.get("litC", ["-"])])), "log", self.getLogId())
                self.initial_candidates.addExploredPair((idL, idR))

            self.logger.printL(1, 'Found %i pairs, will try at most %i' % (len(self.initial_candidates), self.constraints.getCstr("max_inits")), "log", self.getLogId())
            self.logger.updateProgress(level=1, id=self.getLogId())

            ### Saving pairs to file if filename provided
            self.initial_candidates.setExploredDone()
            ## self.initial_candidates.saveToFile()
        else:
            self.logger.initProgressFull(self.constraints, None, self.rcollect.getNbAvailableCols(), 1, self.getLogId())
            self.logger.printL(1, 'Loaded %i pairs from file, will try at most %i' % (len(self.initial_candidates), self.constraints.getCstr("max_inits")), "log", self.getLogId())
        return self.initial_candidates
    
    def testIni(self, pair):
        if pair is None:
            return False
        return True
    
    def getInitExploreList(self, ids, done=set()):
        explore_list = []
        if ids is None:
            ids = self.data.usableIds(self.constraints.getCstr("min_itm_c"), self.constraints.getCstr("min_itm_c"))

        # ### WARNING DANGEROUS few pairs for DEBUG!
        # if self.data.nbCols(0) > 100:
        #     ids = [[4], [15]]
        for idL in ids[0]:
            for idR in ids[1]:
                if not self.data.arePairTypesIn(idL, idR, tset=self.constraints.getCstr("inits_types_exclude")) and self.data.areGroupCompat(idL, idR) and \
                       ( not self.data.isSingleD() or idR > idL or idR not in ids[0] or idL not in ids[1]):
                    if done is None or (idL, idR) not in done:
                        explore_list.append((idL, idR, self.getPairLoad(idL, idR)))
                    else:
                        self.logger.printL(3, 'Loaded pair (%i <=> %i) ...' %(idL, idR), 'log', self.getLogId())
        return explore_list

    def getPairLoad(self, idL, idR):
        # pdb.set_trace()
        # print(idL, idR, eval("0b"+"".join(["%d" %(((idL+idR)%10)%i ==0) for i in [8,4,2]])))
        ## + ((idL + idR)%10)/1000.0
        return max(1, self.data.col(0, idL).getNbValues()* self.data.col(1, idR).getNbValues()/50) + 1./(1+((idL + idR)%10))
        ## return max(1, self.data.col(0, idL).getNbValues()* self.data.col(1, idR).getNbValues()/50)
        # return PAIR_LOADS[self.data.col(0, idL).type_id-1][self.data.col(1, idR).type_id-1]


####################################################
#####      REDS EXPANSIONS
####################################################
    def expandRedescriptions(self, nextge, rcollect=None):
        return ExpMiner(self.getId(), self.count, self.data, self.charbon, self.constraints, self.logger, self.questionLive).expandRedescriptions(nextge, rcollect)
    def improveRedescriptions(self, nextge, rcollect=None):
        return ExpMiner(self.getId(), self.count, self.data, self.charbon, self.constraints, self.logger, self.questionLive).improveRedescriptions(nextge, rcollect)
        
#######################################################################
########### MULTIPROCESSING MINER
#######################################################################

import multiprocessing

class MinerDistrib(Miner):

    def full_run(self, cust_params={}):
        self.rcollect.resetFinal()
        self.count = 0
        self.reinitOnNew = False
        self.workers = {}
        self.rqueue = multiprocessing.Queue()
        self.pstopqueue = multiprocessing.Queue()
        
        self.logger.printL(1, "Starting mining", 'status', self.getLogId()) ### todo ID

        #### progress initialized after listing pairs
        self.logger.clockTic(self.getLogId(), "pairs")
        self.initializeRedescriptions()

        self.logger.clockTic(self.getLogId(), "full run")
        # if self.charbon.isTreeBased():
        self.initializeExpansions()

        self.keepWatchDispatch()
        self.logger.clockTac(self.getLogId(), "full run", "%s" % self.questionLive())        
        if not self.questionLive():
            self.logger.printL(1, 'Interrupted...', 'status', self.getLogId())
        else:
            self.logger.printL(1, 'Done...', 'status', self.getLogId())
        self.logger.sendCompleted(self.getLogId())
        dispTracksEnd(self.logger, self.rcollect, self.getLogId())
        return self.rcollect
        
    def initializePairs(self, ids=None):
        self.initial_candidates.reset()
        self.pairs = 0
        ### Loading pairs from file if filename provided
        loaded, done = self.initial_candidates.loadFromLogFile(self.data)
        if not loaded or done is not None:

            self.logger.printL(1, 'Searching for initial pairs...', 'status', self.getLogId())
            explore_list = self.getInitExploreList(ids, done)
            self.logger.initProgressFull(self.constraints, explore_list, self.rcollect.getNbAvailableCols(), 1, self.getLogId())
            self.total_pairs = len(explore_list)

            min_bsize = 25
            if self.pe_balance == 0:
                #### Finish all pairs before exhausting,
                #### split in fixed sized batches, not sorted by cost
                K = self.max_processes
                batch_size = max(self.total_pairs//(5*K), min_bsize) #self.total_pairs / (self.max_processes-1)
                ## print("Batch size=", batch_size)
                pointer = 0
            else:
                #### Sort from easiest to most expensive
                tot_cost = sum([c[-1] for c in explore_list])
                explore_list.sort(key=lambda x:x[-1], reverse =True)
                thres_cost = (tot_cost/self.max_processes)*(1-self.pe_balance/10.)

                cost = 0
                off = 0
                while off < len(explore_list)-1  and cost < thres_cost:
                    off += 1
                    cost += explore_list[-off][-1]
                if len(self.initial_candidates) > off:
                    off = 0
                ## print("OFF", off)
                K = self.max_processes-1
                batch_size = max((self.total_pairs-off) // K, min_bsize)

                ### Launch last worker
                if K*batch_size < len(explore_list):
                    self.logger.printL(3, 'Initial pairs process [%s] with %d batch...' % (K, len(explore_list[K*batch_size:])), 'status', self.getLogId())
                    ## print("Init PairsProcess ", K, self.getId(), len(explore_list[K*batch_size:]))
                    self.workers[K] = PairsProcess(K, self.getId(), explore_list[K*batch_size:], self.charbon, self.data, self.rqueue)
                pointer = -1
                
            self.initial_candidates.setExploreList(explore_list, pointer, batch_size, done)
            ### Launch other workers
            for k in range(K):
                ll = self.initial_candidates.getExploreNextBatch(pointer=k)
                if len(ll) > 0:
                    self.logger.printL(3, 'Initial pairs process [%s] with %d batch...' % (k, len(ll)), 'status', self.getLogId())
                    ## print("Init PairsProcess ", k, self.getId(), len(ll))
                    self.workers[k] = PairsProcess(k, self.getId(), ll, self.charbon, self.data, self.rqueue)
                else:
                    pointer = -1
                    
            self.pairWorkers = len(self.workers)
            if pointer == 0:
                pointer = self.pairWorkers
            self.initial_candidates.setExplorePointer(pointer)
        else:
            self.initial_candidates.setExploredDone()
            self.logger.initProgressFull(self.constraints, None, self.rcollect.getNbAvailableCols(), 1, self.getLogId())
            self.logger.printL(1, 'Loaded %i pairs from file, will try at most %i' % (len(self.initial_candidates), self.constraints.getCstr("max_inits")), "log", self.getLogId())
        return self.initial_candidates


    def initializeExpansions(self):
        self.reinitOnNew = False
        for k in set(range(self.max_processes)).difference(self.workers.keys()):
            initial_red = self.initial_candidates.get(self.data, self.testIni)
            if self.questionLive():
                if initial_red is None:
                    self.reinitOnNew = True
                else:
                    self.count += 1

                    ir_dets = self.initial_candidates.getLatestDetails()
                    if (initial_red.score() - ir_dets["score"])**2 > 0.0001:           
                        self.logger.printL(1,"OUILLE! Something went badly wrong with initial candidate %s (expected score=%s)\n--------------\n%s\n--------------" % (self.count, ir_dets["score"], initial_red), "log", self.getLogId())
                    
                    self.logger.printL(1,"Expansion %d" % self.count, "log", self.getLogId())
                    self.logger.printL(3, 'Expand process [%s]...' % k, 'status', self.getLogId())
                    self.logger.clockTic(self.getLogId(), "expansion_%d-%d" % (self.count,k))
                    ## print("Init ExpandProcess ", k, self.count)
                    self.workers[k] = ExpandProcess(k, self.getId(), self.count, self.data,
                                                    self.charbon, self.constraints,
                                                    self.rqueue, [initial_red],
                                                    rcollect=self.shareRCollect(), logger=self.shareLogger())
       
    def handlePairResult(self, m):
        pairs, idL, idR, pload = m["pairs"], m["idL"], m["idR"], m["pload"]
        self.pairs += 1
        self.logger.updateProgress({"rcount": 0, "pair": self.pairs, "pload": pload})
        if self.pairs % 100 == 0:
            self.logger.printL(3, 'Searching pair %d/%d (%i <=> %i) ...' %(self.pairs, self.total_pairs, idL, idR), 'status', self.getLogId())
            self.logger.updateProgress(level=1, id=self.getLogId())

        if self.pairs % 10 == 5:
                            
            self.logger.printL(7, 'Searching pair %d/%d (%i <=> %i) ...' %(self.pairs, self.total_pairs, idL, idR), 'status', self.getLogId())
            self.logger.updateProgress(level=7, id=self.getLogId())

        added = 0
        for i, pair in enumerate(pairs):
            if pair["score"] >= self.constraints.getCstr("min_pairscore"):
                added += 1
                self.logger.printL(6, 'Score:%f %s <=> %s %s' % (pair["score"], pair["litL"], pair["litR"], pair.get("litC", "-")), "log", self.getLogId())
                pair.update({0: idL, 1: idR})
                self.initial_candidates.add(pair["litL"], pair["litR"], pair)
        self.initial_candidates.addExploredPair((idL, idR))
        if added > 0 and self.reinitOnNew:
            self.initializeExpansions()

    def handleExpandResult(self, m):
        for red in m["out"].getItems():
            self.rcollect.addItem(red)

        if m["out"].getLen("P") > 0:
            self.rcollect.selected(self.constraints.getActionsList("final"), ids="F", new_ids=m["out"].getIidsList("P"), trg_lid="F")
        self.rcollect.importTracks(m["out"].getTracks(), m["id"])

        if not self.constraints.getCstr("amnesic"):
            self.rcollect.updateSeen(m["out"].getItems("P"))
        self.logger.clockTac(self.getLogId(), "expansion_%d-%d" % (m["count"], m["id"]), "%s" % self.questionLive())
        self.logger.logResults(self.rcollect, "F", self.getLogId())
        self.logger.updateProgress({"rcount": m["count"]}, 1, self.getLogId())

    def leftOverPairs(self):
        # print("LEFTOVER", self.workers)
        return self.initial_candidates.exhausted() and len(self.workers) > 0 and len([(wi, ww) for (wi, ww) in self.workers.items() if ww.isExpand()]) == 0
        
    def keepWatchDispatch(self):
        while len(self.workers) > 0 and self.questionLive():
            m = self.rqueue.get()
            if m["what"] == "done":
                ## print("Worker done", m["id"])
                del self.workers[m["id"]]

                if self.initial_candidates.getExplorePointer() >= 0:
                    ll = self.initial_candidates.getExploreNextBatch()
                    if len(ll) > 0:
                        ## print("Init Additional PairsProcess ", m["id"], self.getId(), self.explore_pairs["pointer"], len(ll))
                        self.workers[m["id"]] = PairsProcess(m["id"], self.getId(), ll, self.charbon, self.data, self.rqueue)
                        self.initial_candidates.incrementExplorePointer()
                    else:
                        self.initial_candidates.setExplorePointer(-1)

                if self.initial_candidates.getExplorePointer() == -1:
                    self.pairWorkers -= 1
                    if self.pe_balance > 0:
                        self.initializeExpansions()
                    # else:
                    #     print("Waiting for all pairs to complete...")

                if self.pairWorkers == 0:
                    self.logger.updateProgress({"rcount": 0}, 1, self.getLogId())
                    self.logger.clockTac(self.getLogId(), "pairs")
                    self.logger.printL(1, 'Found %i pairs, will try at most %i' % (len(self.initial_candidates), self.constraints.getCstr("max_inits")), "log", self.getLogId())
                    self.logger.updateProgress(level=1, id=self.getLogId())
                    self.initial_candidates.setExploredDone()
                    ## self.initial_candidates.saveToFile()
                    if self.pe_balance == 0:
                        self.initializeExpansions()
                        ## print("All pairs complete, launching expansion...")

                
            elif m["what"] == "pairs":
                self.handlePairResult(m)

            elif m["what"] == "expand":
                self.handleExpandResult(m)
                del self.workers[m["id"]]
                self.initializeExpansions()

            if self.leftOverPairs():
                self.logger.printL(1, 'Found %i pairs, tried %i before testing all' % (len(self.initial_candidates), self.constraints.getCstr("max_inits")), "log", self.getLogId())
                ## self.initial_candidates.saveToFile()
                break

    
class PairsProcess(multiprocessing.Process):
    task = "pairs"
    def __init__(self, sid, ppid, explore_list, charbon, data, rqueue):
        multiprocessing.Process.__init__(self)
        self.daemon = True
        self.id = sid
        self.ppid = ppid
        self.explore_list = explore_list
        self.charbon = charbon
        self.data = data
        self.queue = rqueue
        self.start()

    def getId(self):
        return self.id
    def getParentId(self):
        return self.ppid
    def getLogId(self):
        return "%s-%s" % (self.getParentId(), self.getId())

    def isExpand(self): ### expand or init?
        return False
    def getTask(self):
        return self.task
    
    def run(self):
        for pairs, (idL, idR, pload) in enumerate(self.explore_list):
            pairs = self.charbon.computePair(self.data.col(0, idL), self.data.col(1, idR), self.data.getColsC())
            self.queue.put({"id": self.getId(), "what": self.getTask(), "pairs": pairs, "idL": idL, "idR": idR, "pload": pload})
        self.queue.put({"id": self.getId(), "what": "done"})

class ExpandProcess(multiprocessing.Process, ExpMiner):

    def __init__(self, sid, ppid, count, data, charbon, constraints, rqueue,
                 nextge, rcollect=None, logger=None,
                 question_live=None, task = "expand"):
        multiprocessing.Process.__init__(self)
        self.task = task
        self.daemon = True
        self.id = sid
        self.ppid = ppid
        self.count = count
        
        self.charbon = charbon
        self.data = data
        self.queue = rqueue

        self.constraints = constraints
        self.upSouvenirs = False
        self.question_live = question_live
        if logger is None:
            self.logger = DummyLog()
        else:
            self.logger = logger

        self.nextge= nextge
        if rcollect is None:
            self.rcollect = RCollection()
        else:
            self.rcollect = rcollect
        self.start()

    def getId(self):
        return self.id
    def getParentId(self):
        return self.ppid
    def getLogId(self):
        return "%s-%s" % (self.getParentId(), self.getId())
    
    def getTask(self):
        return self.task
        
    def isExpand(self): ### expand or init?
        return True

    def run(self):
        if self.getTask() == "improve":
            rcollect = self.improveRedescriptions(self.nextge, rcollect=self.rcollect)
        else:
            rcollect = self.expandRedescriptions(self.nextge, rcollect=self.rcollect)
        self.queue.put({"id": self.getId(), "what": self.getTask(), "out": rcollect, "count": self.count})

#######################################################################
########### MINER INSTANCIATION
#######################################################################

def instMiner(data, params, logger=None, mid=None, qin=None, cust_params={}):
    if params["nb_processes"]["data"] > 1:
        Redescription.setUidGen(nv=None, step=None, mp_lock=True)
        return MinerDistrib(data, params, logger, mid, qin, cust_params)
    else:
        return Miner(data, params, logger, mid, qin, cust_params)

class StatsMiner:
    def __init__(self, data, params, logger=None, cust_params={}):
        self.data = data
        self.params = params
        self.logger = logger
        self.cust_params = cust_params
        
    def run_stats(self):
        rp = Redescription.getRP()
        modifiers = rp.getModifiersForData(self.data)
        modifiers["wfolds"] = True
        list_fields = rp.getListFields("basic", modifiers)
        exp_dict = rp.getExpDict(list_fields)
        stats_fields = [f for f in list_fields if not re.search("query", f) and not re.search("rid", f)]

        folds_info = self.data.getFoldsInfo()
        stored_folds_ids = sorted(folds_info["fold_ids"].keys(), key=lambda x: folds_info["fold_ids"][x])
        summaries = {}
        nbfolds = len(stored_folds_ids)
        for kfold in range(nbfolds):
            ids = {"learn": [], "test": []}
            for splt in range(nbfolds):
                if splt == kfold:
                    ids["test"].append(stored_folds_ids[splt])
                else:
                    ids["learn"].append(stored_folds_ids[splt])
            self.data.assignLT(ids["learn"], ids["test"])
            miner = instMiner(self.data, self.params, self.logger)
            try:
                miner.full_run()
            except KeyboardInterrupt:
                self.logger.printL(1, 'Stopped...', "log")
            
            stats = []
            reds = []
            for red in miner.rcollect.getItems("F"):
                red.recompute(self.data) ### to set the rsets
                evals_dict = rp.compEVals(red, exp_dict, details={})
                stats.append([evals_dict[f] for f in stats_fields])
                reds.append(red)
            summaries[kfold] = {"reds": reds, "stats": stats}

        reds_map = []
        stack_stats = []
        all_stats = {}
        for k,rr in summaries.items():
            all_stats[k] = rr["stats"]
            stack_stats.extend(rr["stats"])
            for ri, r in enumerate(rr["reds"]):
                found = None
                i = 0
                while i < len(reds_map) and found is None:
                    if reds_map[i]["red"].compare(r) == 0:
                        found = i
                    i += 1
                if found is None:
                    reds_map.append({"red": r, "pos": [(k, ri)]})
                else:
                    reds_map[found]["pos"].append((k,ri))
        reds_map.sort(key=lambda x: x["red"].getAcc(), reverse=True)
        reds_list = []
        for rr in reds_map:
            rr["red"].setTrack(rr["pos"])
            reds_list.append(rr["red"])
        all_stats[-1] =  stack_stats
        return reds_list, all_stats, summaries, list_fields, stats_fields
