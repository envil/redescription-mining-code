import numpy

try:
    from classCharbon import CharbonTree
    from classDTreeTools import DTree
    from classDTreeTools import DTreeToolsSKL as DTT
    # from classDTreeToolsDP import DTreeToolsDP as DTT
    from classQuery import  *
    from classRedescription import  *
except ModuleNotFoundError:
    from .classCharbon import CharbonTree
    from .classDTreeTools import DTree
    from .classDTreeTools import DTreeToolsSKL as DTT
    # from .classDTreeToolsDP import DTreeToolsDP as DTT
    from .classQuery import  *
    from .classRedescription import  *

import pdb

def init_tree(data, side, more={}, cols_info=None, tid=None):
    parent_tree = {"id": tid,
                   "candidates": list(range(data[side].shape[1])),
                   "involv": []}
    if cols_info is not None:
        vid = None
        invol_narrow = more.get("involved", [])
        if len(invol_narrow) == 1:
            vid = invol_narrow[0]
        ttm = [cols_info[side][c][1] for c in invol_narrow]
        invol = [kk for (kk,vv) in cols_info[side].items() if vv[1] in ttm]

        parent_tree["involv"] = invol
        parent_tree["tree"] = DTree({"supp_pos": more["target"], "feat": more.get("src")})
        parent_tree["support"] = more["target"]
    else:
        parent_tree["tree"] = DTree({"n": data[side].shape[0]})
        parent_tree["support"] = parent_tree["tree"].getSuppVect()
    return parent_tree

def initialize_treepile(data, side_ini, more={}, cols_info=None):
    trees_pile = [[[]],[[]]]
    trees_store = {}

    PID = 0
    trees_pile[1-side_ini][-1].append(PID)
    trees_store[PID] = init_tree(data, 1-side_ini, tid=PID)
    
    PID += 1
    trees_pile[side_ini][-1].append(PID)
    trees_store[PID] = init_tree(data, side_ini, more, cols_info, tid=PID)
    
    PID += 1
    return trees_pile, trees_store, PID
    
def get_trees_pair(data, trees_pile, trees_store, side_ini, max_level, min_bucket, split_criterion="gini", PID=0, singleD=False, cols_info=None):
    current_side = side_ini
    #### account for dummy tree on other side when counting levels
    while min(len(trees_pile[side_ini]), len(trees_pile[1-side_ini])-1) < max_level and len(trees_pile[current_side][-1]) > 0:
        # print(side_ini, len(trees_pile[side_ini]), len(trees_pile[1-side_ini]), len(trees_pile[current_side][-1]))
        target = numpy.sum([trees_store[tid]["support"] for tid in trees_pile[current_side][-1]], axis=0)
        # print("TARGET", current_side, sum(target))
        current_side = 1-current_side
        trees_pile[current_side].append([])

        for gpid in trees_pile[current_side][-2]:
            gp_tree = trees_store[gpid]
            candidates = [v for v in gp_tree["candidates"] if v not in gp_tree.get("involv", [])]
            if singleD:
                for ggid in trees_pile[1-current_side][-1]:
                    for vv in trees_store[ggid]["involv"]:
                        try:
                            candidates.remove(vv)
                        except ValueError:
                            pass

            leaves, dt = [], None
            if len(candidates) > 0:
                leaves = gp_tree["tree"].collectLeaves()
                dt = data[current_side][:, candidates]
            for leaf in leaves:
                mask = list(gp_tree["tree"].getSuppSet(leaf))                    
                if sum(target[mask]) > min_bucket and (len(mask)-sum(target[mask])) > min_bucket:
                    tree_rpart = DTT.fitTree(dt[mask,:], target[mask], in_depth=1, 
                                             in_min_bucket=min_bucket, split_criterion=split_criterion, random_state=0, logger=self.logger)
                    if not tree_rpart.isEmpty():
                        ### CHECK SUPPORT
                        # if numpy.sum(split_tree["over_supp"][mask] != tree_rpart.getSupportVect(dt[mask,:])) > 0:
                        vrs = tree_rpart.getFeatures()
                        support = tree_rpart.computeSupp(dt, ids=mask)
                        if cols_info is None:
                            # ncandidates = [vvi for vvi in candidates if vvi not in vrs]
                            ninvolved = list(vrs)
                        else:
                            ttm = [cols_info[current_side][c][1] for c in vrs]
                            # ncandidates = [vvi for vvi in candidates if cols_info[current_side][vvi][1] not in ttm]
                            ninvolved = [vvi for (vvi, vv) in cols_info[current_side].items() if vv[1] in ttm]

                        split_tree = {"id": PID, "tree": tree_rpart, "candidates": candidates,
                                  "branch": (gp_tree["id"], leaf),
                                  "support": support,
                                  "involv": ninvolved}
                        trees_pile[current_side][-1].append(PID)
                        trees_store[PID] = split_tree
                        PID += 1
    return trees_pile, trees_store, PID

def graft_trees(trees_store, pile, in_data=None):
    list_nodes = {}
    tids = []
    ids_init = None
    for ti, t in enumerate(pile):
        if ti == 0 and len(t) == 1:
            if trees_store[t[0]]["tree"].isEmpty() or trees_store[t[0]]["tree"].isEmptyFeat(trees_store[t[0]]["tree"].getFeature(0)):
                continue ### Empty tree to bootstrap, drop
            elif trees_store[t[0]]["tree"].isSpecialFeat(trees_store[t[0]]["tree"].getFeature(0)):
                ids_init = list(numpy.where(trees_store[t[0]]["support"])[0])
            tids.extend(t)
        else:
            tids.extend(t)
    graft_points = {}
    for tid in tids:
        list_nodes[tid] = list(trees_store[tid]["tree"].getNodeIds())
        if trees_store[tid].get("branch", [None])[0] in tids:
            list_nodes[trees_store[tid]["branch"][0]][trees_store[tid]["branch"][1]] = None
            graft_points[trees_store[tid]["branch"]] = (tid, 0)
    map_nodes = {}
    for tid in tids:
        for node_id, v in enumerate(list_nodes[tid]):
            if v is not None:
                map_nodes[(tid, node_id)] = len(map_nodes)
    feats, thres, clss, chls, chrs = ([], [], [], [], [])    
    for tid in tids:
        ct = trees_store[tid]["tree"]
        # print("%d\t%s" % (tid, ct))
        for (i, v) in enumerate(list_nodes[tid]):
            if v is not None:
                if trees_store[tid].get("candidates") is None or ct.isEmptyFeat(ct.getFeature(i)) or ct.isSpecialFeat(ct.getFeature(i)):
                    feats.append(ct.getFeature(i))
                else:
                    feats.append(trees_store[tid]["candidates"][ct.getFeature(i)])
                thres.append(ct.getThreshold(i))
                clss.append(ct.getClass(i))
                for cid, chs in [(ct.getChildrenLeft(i), chls), (ct.getChildrenRight(i), chrs)]:
                    if (tid, cid) in graft_points:
                        chs.append(map_nodes.get(graft_points[(tid, cid)], -1))
                    else:
                        chs.append(map_nodes.get((tid, cid), -1))
        # print("\tFeat: %s\n * Thres: %s\n * Clss: %s\n * ChL: %s\n * ChR: %s" % (feats, thres, clss, chls, chrs))
    dtc = DTree((feats, thres, clss, chls, chrs))
    if dtc.isEmpty():
       return (None, None)
    suppv = dtc.getSupportVect(in_data, ids=ids_init)
    return dtc, suppv

    
class CharbonTLayer(CharbonTree):
    
    name = "TreeLayer"
    def getTreeCandidates(self, side, data, more, in_data, cols_info):
        trees_pile, trees_store, PID = initialize_treepile(in_data, side, more, cols_info=cols_info)
        trees_pile, trees_store, PID = get_trees_pair(in_data, trees_pile, trees_store, side,
                                                      max_level=self.constraints.getCstr("max_var", side=side),
                                                      min_bucket=self.constraints.getCstr("min_node_size"),
                                                      split_criterion=self.constraints.getCstr("split_criterion"),
                                                      PID=PID, singleD=data.isSingleD(), cols_info=cols_info)

        # print("PILE", trees_pile)
        # for ti, tree in trees_store.items():
        #     print("------ %s %s" % (ti, tree["tree"]))
        dtc0, suppv0 = graft_trees(trees_store, trees_pile[0], in_data[0])
        dtc1, suppv1 = graft_trees(trees_store, trees_pile[1], in_data[1])
        if dtc0 is not None and dtc1 is not None:
            results = {0: {"tree": dtc0, "support": suppv0}, 1: {"tree": dtc1, "support": suppv1}}
            redex = self.get_redescription(results, data, cols_info)
            return redex
        return None
