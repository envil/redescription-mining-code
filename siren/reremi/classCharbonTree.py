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

    def getTreeCandidates(self, side, data, red):
        if len(red.queries[side]) != 1:
            return None

        in_data_l, tmp, tcols_l = data.getMatrix([(0, None)], bincats=True)
        in_data_r, tmp, tcols_r = data.getMatrix([(1, None)], bincats=True)

        cols_info = [dict([(i,d) for (d,i) in tcols_l.items() if len(d) == 3]),
                     dict([(i,d) for (d,i) in tcols_r.items() if len(d) == 3])]

        tmp = data.supp(side, red.queries[side].listLiterals()[0])
        target = np.zeros(data.N)
        target[list(tmp)] = 1

        # if str(red) == '0 + 0 terms:\t (1): v1=PS\t[]\t0.000000 0 0.000000\t0:1;1:':
        #     pdb.set_trace()

        current_split_result = self.getSplit(in_data_l.T, in_data_r.T, target, 2, self.constraints.min_node_size())
        if current_split_result['data_rpart_l'] is not None and current_split_result['data_rpart_r'] is not None:
            return self.get_redescription(current_split_result, data, cols_info)
        return None

    def get_redescription(self, in_animals_rpart, data, cols_info):
        left_query = self.get_pathway(0, in_animals_rpart['data_rpart_l'], data, cols_info)
        right_query = self.get_pathway(1, in_animals_rpart['data_rpart_r'], data, cols_info)
        red = Redescription.fromQueriesPair((left_query, right_query), data)
        # if True: ## check
        #     sL = set(np.where(np.array(in_animals_rpart['split_vector_l']))[0])
        #     sR = set(np.where(np.array(in_animals_rpart['split_vector_r']))[0])
        #     if sL != red.supp(0) or sR != red.supp(1):
        #         print "OUPS!"
        #         pdb.set_trace()
        return red

    
    def get_pathway(self, side, tree, data, cols_info):
        left      = list(tree.tree_.children_left)
        right     = list(tree.tree_.children_right)
        threshold = tree.tree_.threshold
        features  = [i for i in tree.tree_.feature]
        mclass  = [i[0][0]<i[0][1] for i in tree.tree_.value]

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

        todo = [i for i in range(len(left)) if left[i] == -1 and mclass[i]]
        buks = []
        for child in todo:
            tmp = get_branch(side, left, right, child, features, threshold, data, cols_info[side])
            if tmp is not None:
                buks.append(tmp)
        qu = Query(True, buks)
        return qu

    def getSplit(self, in_data_l, in_data_r, target, depth, in_min_bucket):
        current_split_result = None
        if np.count_nonzero(target) > in_min_bucket:
            flag = True
            
            while flag:
                if depth <= self.constraints.max_depth():
                    current_split_result = splitting_with_depth(in_data_l, in_data_r, target, depth, in_min_bucket)
                    #Check if we have both vectors (split was successful on the left and right matrix) 
                    if current_split_result['data_rpart_l'] is None or current_split_result['data_rpart_r'] is None:
                        if depth != 2:
                            #Check if left tree was able to split
                            if current_split_result['split_vector_l'] is None:
                                current_split_result['split_vector_l'] = copy.deepcopy(previous_split_result['split_vector_l'])
                                current_split_result['data_rpart_l'] = copy.deepcopy(previous_split_result['data_rpart_l'])
                                #print("split_vector_l didn't split")
                            #Check if right tree was able to split 
                            if current_split_result['split_vector_r'] is None:
                                current_split_result['split_vector_r'] = copy.deepcopy(previous_split_result['split_vector_r'])
                                current_split_result['data_rpart_r'] = copy.deepcopy(previous_split_result['data_rpart_r'])
                                #print("split_vector_r didn't split")
                            previous_split_result = None
                        flag = False
                    else:
                        if depth==2: #depth = 2 means the first iteration, no previous results exist here. Thus, no additional checks are available
                            previous_split_result = copy.deepcopy(current_split_result)
                            depth = depth + 1
                        else:
                            #Here we have successful splits and have to check wethere trees has changed          
                            if (set(previous_split_result['split_vector_l']) == set(current_split_result['split_vector_l'])) or (set(previous_split_result['split_vector_r']) == set(current_split_result['split_vector_r'])):
                                #print("one of trees doesn't change anymore")
                                previous_split_result = None
                                flag = False
                            else:
                                previous_split_result = copy.deepcopy(current_split_result)
                                depth = depth + 1
                else:
                    flag = False
        return current_split_result



def splitting_with_depth(in_data_l, in_data_r, in_target, in_depth, in_min_bucket):
    data_rpart_l = tree.DecisionTreeClassifier(max_depth = in_depth, min_samples_leaf = in_min_bucket)
    data_rpart_l = data_rpart_l.fit(in_data_l, in_target)
    
    #Form Vectors for computing Jaccard. The same vectors are used to form new targets
    split_vector_l = data_rpart_l.predict(in_data_l) #Binary vector of the left tree for Jaccard
    
    if (len(set(split_vector_l)) <= 1):
        split_vector_l = None
        split_vector_r = None
        data_rpart_l = None
        data_rpart_r = None
    else:
        target = split_vector_l
    
        data_rpart_r = tree.DecisionTreeClassifier(max_depth = in_depth, min_samples_leaf = in_min_bucket)
        data_rpart_r = data_rpart_r.fit(in_data_r, target)
    
        #Form Vectors for computing Jaccard. The same vectors are used to form new targets
        split_vector_r = data_rpart_r.predict(in_data_r) #Binary vector of the left tree for Jaccard
    
        if (len(set(split_vector_r)) <= 1):
            split_vector_r = None
            data_rpart_r = None
    result = {'split_vector_l': split_vector_l, 'split_vector_r' : split_vector_r, 'data_rpart_l' : data_rpart_l, 'data_rpart_r' : data_rpart_r}
    return result 
