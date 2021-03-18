import pickle
from unittest import TestCase
from ..classCharbonXFIM import CandStoreV2
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
        self.candidate_store = CandStoreV2(candidate_store_setts)
        with open('siren/clired/tests/data/tid_lists.pickle', 'rb') as f:
            self.tid_lists = pickle.load(f)
        with open('siren/clired/tests/data/supps.pickle', 'rb') as f:
            self.candidate_store.store = pickle.load(f)
        with open('siren/clired/tests/data/data.pickle', 'rb') as f:
            # self.data = pickle.Unpickler(f).find_class('classData', 'Data').load()
            self.data = pickle.load(f)

    def testGetQueries(self):
        result = self.candidate_store.getQueries(self.tid_lists)
        assert result is not None
