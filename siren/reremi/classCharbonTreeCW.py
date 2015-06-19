from classExtension import Extension
import classCharbonStd
from classInitialPairs import *
from classSParts import SParts
from classQuery import  *
from classRedescription import  *
from sklearn import tree
import copy
import pdb
import numpy as np

class Charbon(classCharbonStd.Charbon):

    def withTree(self):
        return True

    def initializeData(self, side, data):
        in_data_l, tmp, tcols_l = data.getMatrix([(0, None)], bincats=True)
        in_data_r, tmp, tcols_r = data.getMatrix([(1, None)], bincats=True)

        in_data = [in_data_l.T, in_data_r.T]
        cols_info = [dict([(i,d) for (d,i) in tcols_l.items() if len(d) == 3]),
                     dict([(i,d) for (d,i) in tcols_r.items() if len(d) == 3])]
        return in_data, cols_info

    def initializeTrg(self, side, data, red):
        if red is None or len(red.queries[0]) + len(red.queries[1]) == 0:
            nsupp = np.random.randint(self.constraints.min_node_size(), data.nbRows()-self.constraints.min_node_size())
            tmp = np.random.choice(range(data.nbRows()), nsupp, replace=False)
        elif side == -1: # and len(red.queries[0]) * len(red.queries[1]) != 0:
            side = 1
            if len(red.queries[side]) == 0:
                side = 1-side
            tmp = red.supp(side)
        else:
            tmp = red.getSuppI()
        target = np.zeros(data.nbRows())
        target[list(tmp)] = 1
        return target, side

    def getTreeCandidates(self, side, data, red):
        in_data, cols_info = self.initializeData(side, data)
        target, side = self.initializeTrg(side, data, red)

        if side is None:
            jj0, suppvs0, dtcs0 = self.getSplit(0, in_data, target)
            jj1, suppvs1, dtcs1 = self.getSplit(1, in_data, target)
            if jj0 > jj1:
                jj, suppvs, dtcs = (jj0, suppvs0, dtcs0)
            else:
                jj, suppvs, dtcs = (jj1, suppvs1, dtcs1)
        else:
            jj, suppvs, dtcs = self.getSplit(side, in_data, target)

        if dtcs[0] is not None and dtcs[1] is not None:
            red = self.get_redescription(dtcs, suppvs, data, cols_info)
            # if True: ## check
            #     sL = set(np.where(np.array(suppvs[0]))[0])
            #     sR = set(np.where(np.array(suppvs[1]))[0])
            #     if sL != red.supp(0) or sR != red.supp(1):
            #         print "OUPS!"
            #         pdb.set_trace()
            return red
        return None

    def get_redescription(self, dtcs, suppvs, data, cols_info):
        left_query = self.get_pathway(0, dtcs[0], data, cols_info)
        right_query = self.get_pathway(1, dtcs[1], data, cols_info)
        return Redescription.fromQueriesPair((left_query, right_query), data)

    def get_pathway(self, side, tree, data, cols_info):
        def get_branch(side, left, right, child, features, threshold, data, cols_info):
            branch = []
            while child is not None:
                parent = None
                if child in left:
                    neg = True
                    parent = left.index(child)
                elif child in right:
                    neg = False
                    parent = right.index(child)
                if parent is not None:
                    if features[parent] in cols_info:
                        side, cid, cbin = cols_info[features[parent]]
                    else:
                        raise Warning("Literal cannot be parsed !")
                        cid = features[parent]
                    if data.cols[side][cid].type_id == BoolTerm.type_id:
                        lit = Literal(neg, BoolTerm(cid))
                    elif data.cols[side][cid].type_id == CatTerm.type_id:
                        lit = Literal(neg, CatTerm(cid, data.col(side, cid).getCatFromNum(cbin)))
                    elif data.cols[side][cid].type_id == NumTerm.type_id:
                        if neg:
                            rng = (float("-inf"), threshold[parent])
                        else:
                            rng = (threshold[parent], float("inf")) 
                        lit = Literal(False, NumTerm(cid, rng[0], rng[1]))
                    else:
                        raise Warning('This type of variable (%d) is not yet handled with tree mining...' % data.cols[side][cid].type_id)
                    branch.append(lit)
                child = parent
            return branch

        left      = list(tree.tree_.children_left)
        right     = list(tree.tree_.children_right)
        to_parent = {}
        for tside, dt in enumerate([left, right]):
            for ii, ni in enumerate(dt):
                if ni > 0:
                    to_parent[ni] = (tside, ii)
        to_parent[0] = (None, None)
        threshold = tree.tree_.threshold
        features  = [i for i in tree.tree_.feature]
        mclass  = [i[0][0]<i[0][1] for i in tree.tree_.value]
        todo = [i for i in range(len(left)) if left[i] == -1 and mclass[i]]
        count_c = {}
        ii = 0
        while ii < len(todo):
            if to_parent[todo[ii]][1] in count_c:
                todo.append(to_parent[todo[ii]][1])
                tn = todo.pop(ii)
                todo.pop(count_c[to_parent[tn][1]])
                ii -= 1
            else:
                count_c[to_parent[todo[ii]][1]] = ii
                ii += 1

        buks = []
        for child in todo:
            tmp = get_branch(side, left, right, child, features, threshold, data, cols_info[side])
            if tmp is not None:
                buks.append(tmp)
        qu = Query(True, buks)
        return qu

    def getSplit(self, side, in_data, target):
        suppvs = [None, None]
        dtcs = [None, None]
        best = (0, suppvs, dtcs)
        current_side = 1-side
        if sum(target) >= self.constraints.min_node_size() and len(target)-sum(target) >= self.constraints.min_node_size():
            suppvs[side] = target
            rounds = 0
        else:
            rounds = -1

        while rounds < self.constraints.max_rounds() and rounds >= 0:            
            rounds += 1
            try:
                dtc, suppv = self.splitting_with_depth(in_data[current_side], suppvs[1-current_side], self.constraints.max_depth(), self.constraints.min_node_size())
            except IndexError:
                pdb.set_trace()
                print current_side
            if dtc is None or (suppvs[current_side] is not None and np.sum((suppvs[current_side] - suppv)**2) == 0):
            ### nothing found or no change
                rounds = -1
            else:
                suppvs[current_side] = suppv
                dtcs[current_side] = dtc
                current_side = 1-current_side
                if suppvs[0] is not None and suppvs[1] is not None:
                    jj = self.getJacc(suppvs)
                    if jj > best[0]:
                        best = (jj, list(suppvs), list(dtcs))
        return best

    def getJacc(self, supps):
        lL = np.sum(supps[0])
        lR = np.sum(supps[1])
        lI = np.sum(supps[0] * supps[1])
        return lI/(lL+lR-lI)

    def splitting_with_depth(self, in_data, in_target, in_depth, in_min_bucket):
        dtc = tree.DecisionTreeClassifier(max_depth = in_depth, min_samples_leaf = in_min_bucket)
        dtc = dtc.fit(in_data, in_target)
        
        #Form Vectors for computing Jaccard. The same vectors are used to form new targets
        suppv = dtc.predict(in_data) #Binary vector of the left tree for Jaccard
    
        if sum(suppv) < in_min_bucket or len(suppv)-sum(suppv) < in_min_bucket:
            return None, None
        return dtc, suppv
