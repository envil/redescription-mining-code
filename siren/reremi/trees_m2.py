from sklearn import tree
import numpy as np
from classQuery import  *
import sys

import pdb

NID = 0
def next_nid():
    global NID
    NID += 1
    return NID


# mammals_data_file_name = '/home/r/r_rpart/python_version/mammals.csv'
# climate_data_file_name = '/home/r/r_rpart/python_version/worldclim_tp.csv'

mammals_data_file_name = './mammals.csv'
climate_data_file_name = './worldclim_tp.csv'

prep_mammals_data_file_name = './mammals_prep.csv'
prep_climate_data_file_name = './worldclim_tp_prep.csv'

legend_file_name = "legend.txt"

# #### LOAD, FILTER AND SAVE THE DATA
# data = [{"head": None, "rows": {}, "data": None}, {"head": None, "rows": {}, "data": None}]
# side = 0
# for (filename, side, SEP) in [(mammals_data_file_name, 0, ';'), (climate_data_file_name, 1, ',')]:
#     for line in open(filename):
#         if data[side]["head"] is None:
#             data[side]["head"] = line.rstrip().split(SEP)
#             data[side]["data"] = np.ones((0,len(data[side]["head"])-3))
#         else:
#             data[side]["rows"][line.rstrip().split(SEP)[2]] = data[side]["data"].shape[0]
#             data[side]["data"] = np.vstack([data[side]["data"], np.array(map(float, line.rstrip().split(SEP)[3:]))])

# keep_rows = sorted(set(data[0]["rows"].keys()).intersection(data[1]["rows"].keys()))
# rowsids = [data[0]["rows"][r] for r in keep_rows]
# cols = list(np.where(np.sum(data[0]["data"][rowsids,:], axis=0))[0])
# dt = data[0]["data"][rowsids,:]
# dt = dt[:,cols]
# with open(legend_file_name, "w") as fo:
#     fo.write(";".join([data[0]["head"][c+3] for c in cols])+"\n")
#     fo.write(";".join(data[1]["head"][3:])+"\n")
#     fo.write(";".join(keep_rows)+"\n")

# np.savetxt(prep_mammals_data_file_name, dt, fmt="%d")
# rowsids = [data[1]["rows"][r] for r in keep_rows]
# np.savetxt(prep_climate_data_file_name, data[1]["data"][rowsids,:], fmt="%.1f")

def gather_supp(tree_exp):
    def recurse_gather(tree_exp, node_id, support_vs, which=None):
        if "split" in tree_exp[node_id]:
            recurse_gather(tree_exp, tree_exp[node_id]["children"][0], support_vs, 0)
            recurse_gather(tree_exp, tree_exp[node_id]["children"][1], support_vs, 1)
        else:
            if which == 0:
                support_vs.append(tree_exp[node_id]["support"])
    support_vs = []
    recurse_gather(tree_exp["nodes"], tree_exp["root"], support_vs)
    return np.sum(support_vs,axis=0)

def set_supp(tree_exp, data_in, mask=None):
    def recurse_supp(tree_exp, data_in, node_id, support_v, over_supp, which=0):
        if "split" in tree_exp[node_id]:
            if tree_exp[node_id]["split"][-1] > 0:
                Ev = data_in[:,tree_exp[node_id]["split"][0]] <= tree_exp[node_id]["split"][-2]
            else:
                Ev = data_in[:,tree_exp[node_id]["split"][0]] > tree_exp[node_id]["split"][-2]
            recurse_supp(tree_exp, data_in, tree_exp[node_id]["children"][0], support_v*Ev, over_supp, 0)
            recurse_supp(tree_exp, data_in, tree_exp[node_id]["children"][1], support_v*np.logical_not(Ev), over_supp, 1)
        else:
            tree_exp[node_id]["support"] = np.zeros(mask.shape[0], dtype=bool)
            tree_exp[node_id]["support"][mask] = support_v
            if which == 0:
                over_supp += tree_exp[node_id]["support"]
    if mask is None:
        mask = np.ones(data_in.shape[0], dtype=bool)
    over_supp = np.zeros(mask.shape[0], dtype=bool)
    recurse_supp(tree_exp["nodes"], data_in, tree_exp["root"], np.ones(data_in.shape[0], dtype=bool), over_supp)
    tree_exp["over_supp"] = over_supp
    return over_supp    

def get_variables(tree_exp, node_id):
    variables = set()
    if "split" in tree_exp[node_id]:
        variables.add(tree_exp[node_id]["split"][1])
        variables |= get_variables(tree_exp, tree_exp[node_id]["children"][0])
        variables |= get_variables(tree_exp, tree_exp[node_id]["children"][1])
    return variables

def get_tree(decision_tree, candidates):
    def recurse(decision_tree, node_id, tree_exp, candidates=None, parent=None, depth=0, new_nid=None):
        if node_id == tree._tree.TREE_LEAF:
            raise ValueError("Invalid node_id %s" % tree._tree.TREE_LEAF)

        if new_nid is None:
            new_nid = next_nid()
        new_node = {"id": new_nid, "parent": parent} #,
        children = []
        if decision_tree.children_left[node_id] != tree._tree.TREE_LEAF:
            nvar = decision_tree.feature[node_id]
            if candidates is not None:
                nvar = candidates[nvar]
            lcid, rcid = (decision_tree.children_left[node_id], decision_tree.children_right[node_id])
            dl = decision_tree.value[lcid][0]
            dr = decision_tree.value[rcid][0]
            if dl[0] < dl[1] and dr[1] < dr[0]:
                new_node["split"] = (decision_tree.feature[node_id], nvar, decision_tree.threshold[node_id], 1)
                children = [lcid, rcid]
                new_node["children"] = [next_nid(), next_nid()]
            elif dl[1] < dl[0] and dr[0] < dr[1]:
                new_node["split"] = (decision_tree.feature[node_id], nvar, decision_tree.threshold[node_id], -1)
                children = [rcid, lcid]
                new_node["children"] = [next_nid(), next_nid()]
            else:
                tree_exp["root"] = None
                return
            for cci, cid in enumerate(children):
                recurse(decision_tree, cid, tree_exp, candidates, parent=new_nid, depth=depth + 1, new_nid = new_node["children"][cci])    

        if len(children) == 0:
            tree_exp["leaves"].append(new_nid)

        tree_exp["nodes"][new_nid] = new_node

    tree_exp = {"nodes": {}, "root": None, "leaves": []}
    if decision_tree.node_count > 2:
        tree_exp["root"] = next_nid()
        recurse(decision_tree, 0, tree_exp, candidates, new_nid=tree_exp["root"])
    return tree_exp

#Function which does split of left and right trees
def splitting(in_target, in_data, candidates, max_depth= 1,  min_bucket=3):
    if sum(in_target) <= min_bucket:
        return {"root": None}

    data_rpart = tree.DecisionTreeClassifier(max_depth = 1, min_samples_leaf = min_bucket).fit(in_data, in_target)
    # split_vector = data_rpart.predict(in_data) #Binary vectoFile "/home/r/NetBeansProjects/RedescriptionTrees/src/redescriptiontrees_method2.py", line 201, in <module>r of the tree for Jaccard
    split_tree = get_tree(data_rpart.tree_, candidates)
    # ttt = set_supp(split_tree, in_data)
    # if sum(ttt-split_vector) > 0:
    #     print "Something smells bad around here splitting..."
    #     pdb.set_trace()
    #     ttt = set_supp(split_tree, in_data)
    # print sum(ttt-split_vector), sum(ttt), "vs", sum(split_vector) 
    return split_tree

def init_tree(data, side, vid=None, more={}):
    #### TEST INIT
    parent_tree = {"id": None,
                   "branch": None,
                   "candidates": range(data[side].shape[1])}
    if vid is not None:
        for vv in more.get("involved", [vid]):
            parent_tree["candidates"].remove(vv)
        if "supp" in more:
            supp_pos = more["supp"]
            split = vid
        else:
            supp_pos = data[side][:,vid] > 0.5
            split = (vid, vid, 0.5, -1)
        parent_tree["over_supp"] = supp_pos
        
        nidt = next_nid()
        nidl = next_nid()
        nidr = next_nid()
        parent_tree["root"] = nidt
        parent_tree["leaves"] = [nidl, nidr]
        parent_tree["nodes"] = {nidt: {"id": nidt, "split": split, "parent": None, "children": [nidl,nidr]},
                                nidl: {"id": nidl, "support": supp_pos, "parent": nidt},
                                nidr: {"id": nidr, "support": np.logical_not(supp_pos), "parent": nidt}}
    else:
        nidt = next_nid()
        parent_tree["root"] = nidt
        parent_tree["init"] = True
        parent_tree["leaves"] = [nidt]
        parent_tree["nodes"] = {nidt: {"id": nidt, "support": np.ones(data[side].shape[0], dtype=bool)}}
                                    
    return parent_tree

def initialize_treepile(data, side_ini, vid, more={}):
    trees_pile = [[[]],[[]]]
    trees_store = {}

    PID = 0
    anc_tree = init_tree(data, 1-side_ini)
    anc_tree["id"] = PID

    trees_pile[1-side_ini][-1].append(PID)
    trees_store[PID] = anc_tree
    PID += 1

    parent_tree = init_tree(data, side_ini, vid, more)
    parent_tree["id"] = PID
    trees_pile[side_ini][-1].append(PID)
    trees_store[PID] = parent_tree
    PID += 1
    return trees_pile, trees_store, PID
    

def piece_together(trees_store, trees_pile_side):
    out = None
    for ii in range(len(trees_pile_side[0])-1, -1, -1):
        if trees_store[trees_pile_side[0][ii]].get("init", False):
            del trees_store[trees_pile_side[0][ii]]
            trees_pile_side[0].pop(ii)
        if len(trees_pile_side[0]) == 0:
            trees_pile_side.pop(0)

    while len(trees_pile_side) > 1:
        current_layer = trees_pile_side.pop()
        for tree in current_layer:
            toplug = trees_store[tree]["branch"]
            # print "PLUG: ", toplug
            pnid = trees_store[toplug[0]]["nodes"][toplug[1]]["parent"]
            rp = trees_store[toplug[0]]["nodes"][pnid]["children"].index(toplug[1])
            trees_store[toplug[0]]["nodes"][pnid]["children"][rp] = trees_store[tree]["root"] 
            # trees_store[tree]["nodes"][trees_store[tree]["root"]]["replace"] = toplug[1]
            del trees_store[toplug[0]]["nodes"][toplug[1]]
            trees_store[toplug[0]]["nodes"].update(trees_store[tree]["nodes"])
            trees_store[toplug[0]]["leaves"].remove(toplug[1])
            trees_store[toplug[0]]["leaves"].extend(trees_store[tree]["leaves"])
            del trees_store[tree]
    if len(trees_pile_side[0]) > 1:
        print "Many trees left..."
    for treeid in trees_pile_side.pop():
        for field in ["candidates", "over_supp", "branch", "id"]:
            del trees_store[treeid][field]
        out = treeid
    return out

def get_trees_pair(data, trees_pile, trees_store, side_ini, max_level, min_bucket, PID=0):
    current_side = side_ini
    #### account for dummy tree on other side when counting levels
    while min(len(trees_pile[side_ini]),len(trees_pile[1-side_ini])-1) <= max_level and len(trees_pile[current_side][-1]) > 0:
        target = np.sum([trees_store[tree]["over_supp"] for tree in trees_pile[current_side][-1]], axis=0)

        current_side = 1-current_side
        trees_pile[current_side].append([])
        
        for gpid in trees_pile[current_side][-2]:
            gp_tree = trees_store[gpid]
            
            dt = data[current_side][:, gp_tree["candidates"]]
            for leaf in gp_tree["leaves"]:            
                mask = gp_tree["nodes"][leaf]["support"]
                # print "BRANCH\t(%d,%d)\t%d %d\t%d:%d/%d"  % (current_side, len(trees_pile[current_side]),
                #                                              gp_tree["id"], leaf, sum(mask),
                #                                              sum(target[mask]), sum(mask)-sum(target[mask]))
                split_tree = splitting(target[mask], dt[mask,:], gp_tree["candidates"], max_depth=1, min_bucket=min_bucket)
                if split_tree["root"] is not None:
                    set_supp(split_tree, dt[mask,:], mask)
                    # print "\tX", split_tree["nodes"][split_tree["root"]]["split"], [sum(split_tree["nodes"][lf]["support"]) for lf in split_tree["leaves"]], sum(split_tree["over_supp"])
                    
                    split_tree["branch"] = (gp_tree["id"], leaf)
                    
                    vrs = get_variables(split_tree["nodes"], split_tree["root"])
                    cand_vrs = [vvi for vvi in gp_tree["candidates"] if vvi not in vrs]
                    split_tree["candidates"] = cand_vrs
                        
                    split_tree["id"] = PID
                    trees_pile[current_side][-1].append(PID)
                    trees_store[PID] = split_tree
                    PID += 1
    return trees_pile, trees_store, PID

def extract_reds(trees_pile, trees_store, data):
    outids = (piece_together(trees_store, trees_pile[0]), piece_together(trees_store, trees_pile[1]))
    if outids[0] is not None and outids[1] is not None:
        qus = (make_lits(0, trees_store[outids[0]], data), make_lits(1, trees_store[outids[1]], data))
        supps = (gather_supp(trees_store[outids[0]]), gather_supp(trees_store[outids[1]]))
        trees = (trees_store[outids[0]], trees_store[outids[1]])
        return qus, supps, trees
    return None


def make_lits(side, tree_exp, data):
    def recurse_lits(side, tree_exp, node_id, data, which=0):
        lls = []
        if "split" in tree_exp[node_id]:
            lit = make_literal(side, tree_exp[node_id]["split"], data)
            for l in recurse_lits(side, tree_exp, tree_exp[node_id]["children"][0], data, which=0):
                try:
                    lls.append([lit.copy()]+l)
                except AttributeError:
                    pdb.set_trace()
            lit.flip()
            for l in recurse_lits(side, tree_exp, tree_exp[node_id]["children"][1], data, which=1):
                lls.append([lit.copy()]+l)
        elif which == 0:
            lls.append([])
        return lls
    tmp = recurse_lits(side, tree_exp["nodes"], tree_exp["root"], data)
    return Query(True, tmp)

def make_literal(side, node, data):
    lit=None
    ### HERE test for literal
    if isinstance(node, Literal):
        lit = node
    elif len(node) > 2:
        cid = node[-3]
        threshold = node[-2]
        direct = node[-1]

        if data.cols[side][cid].type_id == BoolTerm.type_id:
            lit = Literal(direct > 0, BoolTerm(cid))
        elif data.cols[side][cid].type_id == NumTerm.type_id:
            if direct > 0:
                rng = (float("-inf"), threshold)
            else:
                rng = (threshold, float("inf")) 
            lit = Literal(False, NumTerm(cid, rng[0], rng[1]))
        else:
            raise Warning('This type of variable (%d) is not yet handled with tree mining...' % data.cols[side][cid].type_id)
    return lit


#The following variable will contain trees and splitting lists for every animal
def run_main(args):
    animals_trees = {}

    data = [np.loadtxt(prep_mammals_data_file_name),
            np.loadtxt(prep_climate_data_file_name)]
    if data[0].shape[0] == data[1].shape[0]: 
        nb_rows = data[0].shape[0]
    else:
        raise ValueError("Number of rows doesn't match! %d ~ %d" % (data[0].shape[0], data[1].shape[0]))

    rownames = []
    with open(legend_file_name) as fp:
        colnames = [fp.readline().rstrip().split(";"),
                    fp.readline().rstrip().split(";")]
        rownames = fp.readline().rstrip().split(";")
    if nb_rows != len(rownames): 
        raise Warning("Nb of labels does not match number of rows! %d ~ %d" % (nb_rows, len(rownames)))
    if data[0].shape[1] != len(colnames[0]): 
        raise Warning("Nb of labels does not match number of columns on the left! %d ~ %d" % (data[0].shape[1], len(colnames[0])))
    if data[1].shape[1] != len(colnames[1]): 
        raise Warning("Nb of labels does not match number of columns on the right! %d ~ %d" % (data[1].shape[1], len(colnames[1])))

#####################################################################
    side_ini = 0
    max_level = 3
    min_bucket = 2 #max(1,int(np.round(np.sum(data_L[:,aid])/100.0)))

   
    for vid in [1, 2]: #range(4): #data[side_ini].shape[1]):
        trees_pile, trees_store, PID = initialize_treepile(data, side_ini, vid)
        reds = get_trees_pair(data, trees_pile, trees_store, side_ini, max_level, min_bucket, PID)
        # print "----", vid
        # print reds[0][0], reds[1][0]


if __name__ == "__main__":
    run_main(sys.argv)
