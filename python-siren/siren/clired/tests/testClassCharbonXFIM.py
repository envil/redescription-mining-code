import pickle
from unittest import TestCase, skip
from ..classCharbonXFIM import CandStoreMineAndPair
from ..classConstraints import Constraints
import sys
from ..classData import *
from ..toolICDict import *
from ..classCol import *
from ..classContent import *
from ..classSParts import *
from ..classCharbonXFIM import *
from .. import toolICDict, classData, classCol, classContent, classSParts, classCharbonXFIM
sys.modules['classData'] = classData
sys.modules['toolICDict'] = toolICDict
sys.modules['classCol'] = classCol
sys.modules['classContent'] = classContent
sys.modules['classSParts'] = classSParts
sys.modules['classCharbonXFIM'] = classCharbonXFIM

class CandStoreV2TestCase(TestCase):
    def setUp(self) -> None:
        with open('siren/clired/tests/data/params.pickle', 'rb') as f:
            params = pickle.load(f)
            self.constraints = Constraints(params)
        candidate_store_setts = dict([(k, self.constraints.getCstr(k)) for k in ["max_var_s0", "max_var_s1",
                                                                                 "min_fin_in", "min_fin_out",
                                                                                 "min_fin_acc"]])
        self.candidate_store = CandStoreMineAndPair(candidate_store_setts)
        with open('siren/clired/tests/data/tid_lists.pickle', 'rb') as f:
            self.tid_lists = pickle.load(f)
        with open('siren/clired/tests/data/supps.pickle', 'rb') as f:
            self.candidate_store.store = pickle.load(f)
        with open('siren/clired/tests/data/data.pickle', 'rb') as f:
            # self.data = pickle.Unpickler(f).find_class('classData', 'Data').load()
            self.data = pickle.load(f)
        with open('siren/clired/tests/data/queries_v2.pickle', 'rb') as f:
            # self.data = pickle.Unpickler(f).find_class('classData', 'Data').load()
            self.queries_v2 = pickle.load(f)
        with open('siren/clired/tests/data/queries.pickle', 'rb') as f:
            # self.data = pickle.Unpickler(f).find_class('classData', 'Data').load()
            self.queries_v3 = pickle.load(f)

    @skip()
    def testCompareTuple(self):
        tuple1 = ((0, 6, 0), (0, 8, 0))
        tuple2 = ((0, 6, 0), (0, 8, 0))
        assert tuple1 == tuple2

    @skip()
    def testGetQueries(self):
        queries_v2 = self.candidate_store.getQueries(self.tid_lists)
        assert queries_v2 is not None
        for query_v3 in self.queries_v3:
            for query_v2 in queries_v2:
                if query_v2[0] == query_v3[0] and query_v2[1] == query_v3[1]:
                    print(query_v2 == query_v3)

    # def testGenerateCand(self):
    #     for qs in self.queries_v2:
    #         literals_s0 = [initial_candidates[initial_candidates_map[0][q[1]][q[2]]][0] for q in qs[0]]
    #         literals_s1 = [initial_candidates[initial_candidates_map[1][q[1]][q[2]]][1] for q in qs[1]]

@skip('not needed')
class CandStoreV3TestCase(TestCase):
    def setUp(self) -> None:
        with open('siren/clired/tests/data/params.pickle', 'rb') as f:
            params = pickle.load(f)
            self.constraints = Constraints(params)
        candidate_store_setts = dict([(k, self.constraints.getCstr(k)) for k in ["max_var_s0", "max_var_s1",
                                                                                 "min_fin_in", "min_fin_out",
                                                                                 "min_fin_acc"]])
        self.candidate_store = CandStoreMineAndSplit(candidate_store_setts)
        # with open('siren/clired/tests/data/tid_lists.pickle', 'rb') as f:
        #     self.tid_lists = pickle.load(f)
        # with open('siren/clired/tests/data/supps.pickle', 'rb') as f:
        #     self.candidate_store.store = pickle.load(f)
        # with open('siren/clired/tests/data/data.pickle', 'rb') as f:
            # self.data = pickle.Unpickler(f).find_class('classData', 'Data').load()
            # self.data = pickle.load(f)

    def testGetQueries(self):
        result = self.candidate_store.getQueries(self.tid_lists)
        assert result is not None
