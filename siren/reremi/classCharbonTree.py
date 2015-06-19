from classExtension import Extension
import classCharbonTreeCW
from classInitialPairs import *
from classSParts import SParts
from classQuery import  *
from classRedescription import  *
from sklearn import tree
import copy
import pdb
import numpy as np

class Charbon(classCharbonTreeCW.Charbon):

    def getTreeCandidates(self, side, data, red):
        in_data, cols_info = self.initializeData(side, data)
        target, side = self.initializeTrg(side, data, red)

        current_split_result = self.getSplit(in_data[0], in_data[1], target, 2, self.constraints.min_node_size())
        if current_split_result['data_rpart_l'] is not None and current_split_result['data_rpart_r'] is not None:
            return self.get_redescription([current_split_result['data_rpart_l'], current_split_result['data_rpart_r']],
                                          [current_split_result['split_vector_l'], current_split_result['split_vector_l']],
                                          data, cols_info)
        return None


    def getSplit(self, in_data_l, in_data_r, target, depth, in_min_bucket):
        current_split_result = {'data_rpart_l': None, 'data_rpart_r': None}
        if np.count_nonzero(target) > in_min_bucket:
            flag = True
            
            while flag:
                if depth <= self.constraints.max_depth():
                    current_split_result = splitting_with_depth_both(in_data_l, in_data_r, target, depth, in_min_bucket)
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



def splitting_with_depth_both(in_data_l, in_data_r, in_target, in_depth, in_min_bucket):
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
