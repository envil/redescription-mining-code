import pickle
from unittest import TestCase
from ..classCharbonXFIM import CandStoreV2
from ..classConstraints import Constraints


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
            self.candidate_store.supps = pickle.load(f)

    def testGetQueries(self):
        result = self.candidate_store.getQueries(self.tid_lists)
        assert result is not None
