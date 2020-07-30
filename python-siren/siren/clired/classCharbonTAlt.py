try:
    from classCharbon import CharbonTree
    from classDTreeTools import DTreeToolsSKL as DTT
    # from classDTreeToolsDP import DTreeToolsDP as DTT
    from classQuery import *
    from classRedescription import Redescription
except ModuleNotFoundError:
    from .classCharbon import CharbonTree
    from .classDTreeTools import DTreeToolsSKL as DTT
    # from .classDTreeToolsDP import DTreeToolsDP as DTT
    from .classQuery import *
    from .classRedescription import Redescription

import pdb


class CharbonTCW(CharbonTree):
    name = "TreeCartWheel"
    
    def getTreeCandidates(self, side, data, more, in_data, cols_info):
        if side is None:
            jj0, results0 = self.getSplit(0, in_data, more["target"], singleD=data.isSingleD(), cols_info=cols_info)
            jj1, results1 = self.getSplit(1, in_data, more["target"], singleD=data.isSingleD(), cols_info=cols_info)
            if jj0 > jj1:
                jj, results = (jj0, results0)
            else:
                jj, results = (jj1, results1)
        else:
            jj, results = self.getSplit(side, in_data, more["target"], singleD=data.isSingleD(), cols_info=cols_info)

        if results is not None and results[0].get("tree") is not None and results[1].get("tree") is not None:
            redex = self.get_redescription(results, data, cols_info)
            return redex
        return None


    def getJacc(self, suppL=None, suppR=None):
        if suppL is None or suppR is None:
            return -1
        lL = sum(suppL)
        lR = sum(suppR)
        lI = sum(suppL * suppR)
        return lI/(lL+lR-lI)

    def splitting_with_depth(self, in_data, in_target, in_depth, in_min_bucket,  split_criterion="gini"):
        dtc = DTT.fitTree(in_data, in_target, in_depth, in_min_bucket, split_criterion, random_state=0, logger=self.logger)
        suppv = dtc.getSupportVect(in_data)
        if sum(suppv) < in_min_bucket or len(suppv)-sum(suppv) < in_min_bucket:
            return None, None
        return dtc, suppv

    def getSplit(self, side, in_data, target, singleD=False, cols_info=None):
        best = (0, None)
        results = {0: {}, 1: {}}
        current_tids = [0, 1]
        current_side = 1-side
        if sum(target) >= self.constraints.getCstr("min_itm_c") and len(target)-sum(target) >= self.constraints.getCstr("min_itm_c"):
            results[current_tids[side]]["support"] = target
            rounds = 0
        else:
            rounds = -1

        while rounds < self.constraints.getCstr("max_rounds") and rounds >= 0:            
            rounds += 1
            if results[current_tids[1-current_side]].get("tree") is not None and singleD:
                vrs = results[current_tids[1-current_side]]["tree"].getFeatures()
                if cols_info is None:
                    ncandidates = [vvi for vvi in range(in_data[current_side].shape[1]) if vvi not in vrs]
                else:
                    ttm = [cols_info[current_side][c][1] for c in vrs]
                    ncandidates = [vvi for vvi in range(in_data[current_side].shape[1]) if cols_info[current_side][vvi][1] not in ttm]
                feed_data = in_data[current_side][:, ncandidates]
            else:
                ncandidates = None
                feed_data = in_data[current_side]
                
            dtc, suppv = self.splitting_with_depth(feed_data, results[current_tids[1-current_side]].get("support"),
                                                   self.constraints.getCstr("max_var", side=current_side), self.constraints.getCstr("min_itm_c"),
                                                   split_criterion=self.constraints.getCstr("split_criterion"))

            if dtc is None or (results[current_tids[current_side]].get("tree") is not None and results[current_tids[1-current_side]].get("tree") is not None \
                               and results[current_tids[current_side]].get("support") is not None and all(results[current_tids[current_side]].get("support") == suppv)):
                ### nothing found or no change
                rounds = -1
            else:
                current_dt = {"support": suppv, "tree": dtc, "candidates": ncandidates}
                current_tids[current_side] = len(results)                
                results[current_tids[current_side]] = current_dt
                current_side = 1-current_side
                jj = self.getJacc(results[current_tids[0]].get("support"), results[current_tids[1]].get("support"))
                if jj > best[0] and results[current_tids[current_side]].get("tree") is not None:
                    best = (jj, (current_tids[0], current_tids[1]))
        if best[1] is not None:
            return (best[0], {0: results[best[1][0]], 1: results[best[1][1]]})
        return best

class CharbonTSprit(CharbonTCW):
    name = "TreeSprit"

    def getSplit(self, side, in_data, target, singleD=False, cols_info=None):
        best = (0, None)
        results = {0: {}, 1: {}}
        current_tids = [0, 1]
        current_side = 1-side
        if sum(target) >= self.constraints.getCstr("min_itm_c") and len(target)-sum(target) >= self.constraints.getCstr("min_itm_c"):
            results[current_tids[side]]["support"] = target
            rounds = 0
        else:
            rounds = -1

        depth = [2,2]
        while rounds >=0 and (depth[0] <= self.constraints.getCstr("max_var", side=0) or depth[1] <= self.constraints.getCstr("max_var", side=1)):
            rounds += 1
            if results[current_tids[1-current_side]].get("tree") is not None and singleD:
                vrs = results[current_tids[1-current_side]]["tree"].getFeatures()
                if cols_info is None:
                    ncandidates = [vvi for vvi in range(in_data[current_side].shape[1]) if vvi not in vrs]
                else:
                    ttm = [cols_info[current_side][c][1] for c in vrs]
                    ncandidates = [vvi for vvi in range(in_data[current_side].shape[1]) if cols_info[current_side][vvi][1] not in ttm]
                feed_data = in_data[current_side][:, ncandidates]
            else:
                ncandidates = None
                feed_data = in_data[current_side]

            dtc, suppv = self.splitting_with_depth(feed_data, results[current_tids[1-current_side]].get("support"),
                                                   depth[current_side], self.constraints.getCstr("min_itm_c"),
                                                   split_criterion=self.constraints.getCstr("split_criterion"))

            if dtc is None or (results[current_tids[current_side]].get("tree") is not None and results[current_tids[1-current_side]].get("tree") is not None \
                               and results[current_tids[current_side]].get("support") is not None and all(results[current_tids[current_side]].get("support") == suppv)):
                ### nothing found or no change
                rounds = -1
            else:
                depth[current_side] += 1
                current_dt = {"support": suppv, "tree": dtc, "candidates": ncandidates}
                current_tids[current_side] = len(results)                
                results[current_tids[current_side]] = current_dt
                current_side = 1-current_side
                jj = self.getJacc(results[current_tids[0]].get("support"), results[current_tids[1]].get("support"))
                if jj > best[0] and results[current_tids[current_side]].get("tree") is not None:
                    best = (jj, (current_tids[0], current_tids[1]))
        if best[1] is not None:
            return (best[0], {0: results[best[1][0]], 1: results[best[1][1]]})
        return best
    

class CharbonTSplit(CharbonTCW):

    name = "TreeSplit"
    def getTreeCandidates(self, side, data, more, in_data, cols_info):        
        results = self.getSplit(side, in_data, more["target"], data.isSingleD(), cols_info)
        if results is not None and results[0].get("tree") is not None and results[1].get("tree") is not None:
            return self.get_redescription(results, data, cols_info)
        return None

    def getSplit(self, side, in_data, target, singleD=False, cols_info=None):        
        depth = 1
        prev_results = None
        trg = target
        if sum(target) >= self.constraints.getCstr("min_itm_c") and len(target)-sum(target) >= self.constraints.getCstr("min_itm_c"):
            
            while depth > 0 and depth <= max(self.constraints.getCstr("max_var", side=0), self.constraints.getCstr("max_var", side=1)):
                change, results = self.splitting_with_depth_both(side, in_data, trg, singleD, cols_info,
                                                    in_depth=depth, in_min_bucket=self.constraints.getCstr("min_itm_c"),
                                                    split_criterion=self.constraints.getCstr("split_criterion"),
                                                    prev_results=prev_results)
                if -1 not in change and 1 in change:
                    trg = results[side].get("support")
                    prev_results = results
                    depth += 1
                elif depth == 1: 
                    depth = 2 ## try depth 2 anyway, keeping target
                else:
                    depth = 0

                # # Check if we have both vectors (split was successful on the left and right matrix)
                # if results[0].get("tree") is None or results[1].get("tree") is None:                    
                #     if prev_results is not None:
                #         # Check if left tree was able to split
                #         if results[0].get("tree") is None:
                #             results[0] = prev_results[0]
                #         if results[1].get("tree") is None:
                #             results[1] = prev_results[1]
                #     depth = 0
                # else:
                #     # Either have no previous results or have successful splits and have to check whether trees changed
                #     if prev_results is None or \
                #         ((prev_results[0].get("support") is None or any(prev_results[0].get("support") != results[0].get("support"))) and \
                #          (prev_results[1].get("support") is None or any(prev_results[1].get("support") != results[1].get("support")))):
                #         prev_results = results
                #         depth += 1
                #     else:
                #         depth = 0
        return results


    def splitting_with_depth_both(self, side, in_data, in_target, singleD=False, cols_info=None, in_depth=1, in_min_bucket=0, split_criterion="gini", prev_results=None):
        trg = in_target
        results = {0: {}, 1: {}}
        change = [-1,-1]
        for current_side in [1-side, side]:
            dtc, suppv = (None, None)            
            side_depth = min(self.constraints.getCstr("max_var", side=current_side), in_depth)
            if results[1-current_side].get("tree") is not None and singleD:
                vrs = results[1-current_side]["tree"].getFeatures()
                if cols_info is None:
                    ncandidates = [vvi for vvi in range(in_data[current_side].shape[1]) if vvi not in vrs]
                else:
                    ttm = [cols_info[current_side][c][1] for c in vrs]
                    ncandidates = [vvi for vvi in range(in_data[current_side].shape[1]) if cols_info[current_side][vvi][1] not in ttm]
                feed_data = in_data[current_side][:, ncandidates]
            else:
                ncandidates = None
                feed_data = in_data[current_side]

            dtc, suppv = self.splitting_with_depth(feed_data, trg, side_depth, in_min_bucket, split_criterion)
            if dtc is None: ## split failed, fall back
                return change, prev_results
            else:
                change[current_side] = 1*(prev_results is None or prev_results[current_side].get("support") is None or any(prev_results[current_side].get("support") != suppv))
            results[current_side] = {"support": suppv, "tree": dtc, "candidates": ncandidates}
            trg = suppv
        return change, results
    
