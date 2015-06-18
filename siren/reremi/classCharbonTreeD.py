import classCharbonStd
from classSParts import SParts
from classQuery import  *
from classRedescription import  *
import pdb
import numpy as np

import trees_m2 

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
        llt = red.queries[side].listLiterals()[0]
        ss = data.supp(side, llt)
        data_tt = [in_data_l.T, in_data_r.T]

        supp = np.zeros(data.nbRows(), dtype=bool)
        supp[list(ss)] = True
        if side == 0:
            mmap = tcols_l
        else:
            mmap = tcols_r
        if llt.term.type_id == 2:
            off = data.cols[side][llt.col()].numEquiv(llt.term.getCat())
        else:
            off = 0
        vid = mmap[(side, llt.col(), off)]
        more = {"involved": [vid], "supp": supp}
        trees_pile, trees_store, PID = trees_m2.initialize_treepile(data_tt, side, llt, more)
        trees_pile, trees_store, PID = trees_m2.get_trees_pair(data_tt, trees_pile, trees_store, side,
                                                               max_level=self.constraints.max_depth(),
                                                               min_bucket=self.constraints.min_node_size(), PID=PID)

        redt = trees_m2.extract_reds(trees_pile, trees_store, data, cols_info)
        if redt is not None:
            red = Redescription.fromQueriesPair(redt[0], data)
            # print red
            # if np.sum(redt[1][0]*redt[1][1]) != red.sParts.lenI():
            #     print np.sum(redt[1][0]*redt[1][1])
            #     pdb.set_trace()
            return red
        return None

