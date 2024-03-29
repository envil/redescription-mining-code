import pickle
from collections import defaultdict


try:

    from classData import Data
    from classCharbon import CharbonXaust
    from classQuery import *
    from classRedescription import Redescription
except ModuleNotFoundError:
    from .classData import Data
    from .classCharbon import CharbonXaust
    from .classQuery import *
    from .classRedescription import Redescription

import pdb


# -----------------------------------------------------------------------
# File    : pyfim.py
# Contents: frequent item set mining in Python
#           (in the current version only with the eclat algorithm)
# Author  : Christian Borgelt
# History : 2013.01.23 file created
#           2013.01.24 closed and maximal item set filtering improved
#           2013.01.25 recursion/output data combined in a list
#           2013.02.09 made compatible with Python 3 (print, range)
#           2017.06.02 bugs in perfect extension processing fixed
# -----------------------------------------------------------------------

def report(iset, pexs, supp, setts, store_handle):
    """Recursively report item sets with the same support.
iset    base item set to report (list of items)
pexs    perfect extensions of the base item set (list of items)
supp    (absolute) support of the item set to report
setts    static recursion/output setts as a list
        [ target, supp, zmin, zmax, maxx, count [, out] ]"""
    if not pexs:  # if no perfect extensions (left)
        n = len(iset)  # check the item set size
        if (n < setts[2]) or (n > setts[3]):
            return
        store_handle((tuple(iset), supp))
    else:  # if perfect extensions to process
        report(iset + [pexs[0]], pexs[1:], supp, setts, store_handle)
        report(iset, pexs[1:], supp, setts, store_handle)


def my_report(iset, pexs, supp, setts, store_handle):
    """Recursively report item sets with the same support.
iset    base item set to report (list of items)
pexs    perfect extensions of the base item set (list of items)
supp    (absolute) support of the item set to report
setts    static recursion/output setts as a list
        [ target, supp, zmin, zmax, maxx, count [, out] ]"""
    def check_item_size(n, zmin, zmax):
        return n < zmin or n > zmax

    def is_invalid_item_set_size(item_set, settings):
        [zmin, zmax] = settings[2:4]
        if len(zmax) == 1:
            n = len(item_set)  # check the item set size
            return check_item_size(n, settings[2][0], settings[3][0])
        elif len(zmax) == 2:
            result = True
            for side, (sided_zmin, sided_zmax) in enumerate(zip(zmin, zmax)):
                sided_iset = [item for item in item_set if item[0] == side]
                result = result & check_item_size(len(sided_iset), sided_zmin, sided_zmax)
            return result
        else:
            return False

    if not pexs:  # if no perfect extensions (left)
        if is_invalid_item_set_size(iset, setts):
            return
        store_handle((tuple(iset), supp))
    else:  # if perfect extensions to process
        my_report(iset + [pexs[0]], pexs[1:], supp, setts, store_handle)
        my_report(iset, pexs[1:], supp, setts, store_handle)


# -----------------------------------------------------------------------

def closed(tracts, elim):
    """Check for a closed item set.
tracts  list of transactions containing the item set
elim    list of lists of transactions for eliminated items
returns whether the item set is closed"""
    for t in reversed(elim):  # try to find a perfect extension
        if tracts <= t: return False
    return True  # return whether the item set is closed


# -----------------------------------------------------------------------

def maximal(tracts, elim, supp):
    """Check for a maximal item set.
tracts  list of transactions containing the item set
elim    list of lists of transactions for eliminated items
supp    minimum support of an item set
returns whether the item set is maximal"""
    for t in reversed(elim):  # try to find a frequent extension
        if sum([w for x, w in tracts & t]) >= supp: return False
    return True  # return whether the item set is maximal


# -----------------------------------------------------------------------

def recurse(tadb, iset, pexs, elim, setts, store_handle):
    """Recursive part of the eclat algorithm.
tadb    (conditional) transaction settsbase, in vertical representation,
        as a list of item/transaction information, one per (last) item
        (triples of support, item and transaction set)
iset    item set (prefix of conditional transaction settsbase)
pexs    set of perfect extensions (parent equivalent items)
elim    set of eliminated items (for closed/maximal check)
setts    static recursion/output setts as a list
        [ target, supp, zmin, zmax, maxx, count [, out] ]"""
    # TODO reverse the sort here? what will be the impact?
    tadb.sort()  # sort items by (conditional) support
    xelm = []
    m = 0  # init. elim. items and max. support
    for k, (sum_transactions, item, transactions) in enumerate(tadb):  # traverse the items/item sets
        if sum_transactions > m:
            m = sum_transactions  # find maximum extension support
        if setts[0] in 'cm' and not closed(transactions, elim + xelm):
            continue  # check for a perfect extension
        proj = []
        xpxs = []  # construct the projection of the
        for r, j, u in tadb[k + 1:]:  # trans. settsbase to the current item:
            u = u & transactions  # intersect with subsequent lists
            r = sum([w for x, w in u])
            if r >= sum_transactions:
                xpxs.append(j)
            elif r >= setts[1]:
                proj.append([r, j, u])
        xpxs = pexs + xpxs  # combine perfect extensions and
        xset = iset + [item]  # add the current item to the set and
        n = len(xpxs) if setts[0] in 'cm' else 0
        r = recurse(proj, xset, xpxs, elim + xelm, setts, store_handle) \
            if proj and (len(xset) + n < setts[4]) else 0
        xelm += [transactions]  # collect the eliminated items
        if setts[0] == 'm':  # if to report only maximal item sets
            if r < setts[1] and maximal(transactions, elim + xelm[:-1], setts[1]):
                report(xset + xpxs, [], sum_transactions, setts, store_handle)
        elif setts[0] == 'c':  # if to report only closed  item sets
            if r < sum_transactions: report(xset + xpxs, [], sum_transactions, setts, store_handle)
        else:  # if to report all frequent item sets
            report(xset, xpxs, sum_transactions, setts, store_handle)
    return m  # return the maximum extension support


def my_recurse(tadb, iset, pexs, setts, store_handle):
    """Recursive part of the eclat algorithm.
tadb    (conditional) transaction settsbase, in vertical representation,
        as a list of item/transaction information, one per (last) item
        (triples of support, item and transaction set)
iset    item set (prefix of conditional transaction settsbase)
pexs    set of perfect extensions (parent equivalent items)
elim    set of eliminated items (for closed/maximal check)
setts    static recursion/output setts as a list
        [ target, supp, zmin, zmax, maxx, count [, out] ]"""
    tadb.sort()  # sort items by (conditional) support
    for k, (sum_transactions, item, transactions) in enumerate(tadb):  # traverse the items/item sets
        proj = []
        xpxs = []  # construct the projection of the
        for r, j, u in tadb[k + 1:]:  # trans. settsbase to the current item:
            u = u & transactions  # intersect with subsequent lists
            r = sum([w for x, w in u])
            if r >= sum_transactions:
                xpxs.append(j)
            elif r >= setts[1]:
                proj.append([r, j, u])
        xpxs = pexs + xpxs  # combine perfect extensions and
        xset = iset + [item]  # add the current item to the set and
        if proj and (len(xset) < setts[4]):
            my_recurse(proj, xset, xpxs, setts, store_handle)
        my_report(xset, xpxs, sum_transactions, setts, store_handle)

# -----------------------------------------------------------------------

def mod_eclat(tracts, setts, store_handle):
    ### prepare transaction data
    tadb = dict()  # reduce by combining equal transactions
    for t in [frozenset(t) for t in tracts]:
        if t in tadb:
            tadb[t] += 1
        else:
            tadb[t] = 1
    tracts = tadb.items()  # get reduced trans. and collect items
    items = set().union(*[t for t, w in tracts])
    tadb = dict([(i, []) for i in items])
    for t in tracts:  # collect transactions per item
        for i in t[0]: tadb[i].append(t)
    tadb = [[sum([w for t, w in tadb[i]]), i, set(tadb[i])]
            for i in tadb]  # build and filter transaction sets
    sall = sum([w for t, w in tracts])
    pexs = [i for s, i, t in tadb if s >= sall]
    tadb = [t for t in tadb if t[0] >= setts[1] and t[0] < sall]

    r = recurse(tadb, [], [], [], setts, store_handle)
    # r = my_recurse(tadb, [], [], setts, store_handle)
    return r


# -----------------------------------------------------------------------


class CandStore:
    def __init__(self, setts):
        self.setts = setts
        self.supps = {}

    def add(self, cand):
        if ("max_var_s0" not in self.setts or len([c for c in cand[0] if c[0] == 0]) <= self.setts["max_var_s0"]) and \
            ("max_var_s1" not in self.setts or len([c for c in cand[0] if c[0] == 1]) <= self.setts["max_var_s1"]):
            self.supps[cand[0]] = cand[1]

    def getQueries(self):
        qs = []
        for cand, s01 in self.supps.items():
            q0 = tuple([c for c in cand if c[0] == 0])
            q1 = tuple([c for c in cand if c[0] == 1])
            if len(q0) > 0 and len(q1) > 0:
                s0 = self.supps.get(q0, -1)
                s1 = self.supps.get(q1, -1)
                if s0 > 0 and s1 > 0 and \
                    ("min_itm_in" not in self.setts or s01 >= self.setts["min_itm_in"]) and \
                    ("min_fin_acc" not in self.setts or s01 / (s0 + s1 - s01) >= self.setts["min_fin_acc"]):
                    qs.append((q0, q1, s0, s1, s01))
        return qs


class TIDList:
    def __init__(self):
        # self.setts = setts
        self.lists = [{}, {}]

    def set_data(self, side, item, data):
        if self.lists[side] is not None:
            self.lists[side][item] = data

    def get_supports(self, candidate: tuple):
        side, _, _ = candidate[0] if isinstance(candidate[0], tuple) else candidate
        if self.lists[side].get(candidate) is None:
            self.lists[side][candidate] = self.create_tid(candidate)
        return self.lists[side].get(candidate, set())

    def create_tid(self, candidate):
        supps = self.get_supports(candidate[0])
        for item in candidate:
            supps = supps & self.get_supports(item)
        return supps


class CandStoreMineAndPair:
    def __init__(self, setts):
        self.setts = setts
        self.store = [{}, {}]

    def add(self, cand):
        side = cand[0][0][0]
        if side == 0 and (
            "max_var_s0" not in self.setts or len([c for c in cand[0] if c[0] == 0]) <= self.setts["max_var_s0"]):
            self.store[0][cand[0]] = cand[1]
        elif side == 1 and (
            "max_var_s1" not in self.setts or len([c for c in cand[0] if c[0] == 1]) <= self.setts["max_var_s1"]):
            self.store[1][cand[0]] = cand[1]

    def getQueries(self, tid_lists: TIDList) -> list:
        query_store = []
        for lhs_cand, s0 in self.store[0].items():
            for rhs_cand, s1 in self.store[1].items():
                s0 = tid_lists.get_supports(lhs_cand)
                s1 = tid_lists.get_supports(rhs_cand)

                union_supports = s0 | s1
                intersection_supports = s0 & s1
                accuracy = len(intersection_supports)/len(union_supports)

                if accuracy >= self.setts.get("min_fin_acc", 0) and len(intersection_supports) >= self.setts.get('min_itm_in', 0):
                    query_store.append((lhs_cand, rhs_cand, s0, s1, accuracy))
        return query_store


class CandStoreMineAndSplit:
    def __init__(self, setts):
        self.setts = setts
        self.store = {}

    def add(self, cand):
        sides = set([item[0] for item in cand[0]])
        if len(sides) < 2:
            return
        if ("max_var_s0" not in self.setts or len([c for c in cand[0] if c[0] == 0]) <= self.setts["max_var_s0"]) and \
            ("max_var_s1" not in self.setts or len([c for c in cand[0] if c[0] == 1]) <= self.setts["max_var_s1"]):
            self.store[cand[0]] = cand[1]

    def getQueries(self, tid_lists: TIDList) -> list:
        query_store = []
        for cand, _ in self.store.items():
            q0 = tuple([c for c in cand if c[0] == 0])
            q1 = tuple([c for c in cand if c[0] == 1])
            s0 = tid_lists.get_supports(q0)
            s1 = tid_lists.get_supports(q1)
            union_supports = s0 | s1
            intersection_supports = s0 & s1
            accuracy = len(intersection_supports)/len(union_supports)

            if ("min_fin_acc" not in self.setts or accuracy >= self.setts["min_fin_acc"]):
                query_store.append((q0, q1, s0, s1, accuracy))
        return query_store


class CharbonXFIM(CharbonXaust):
    name = "XaustFIM"

    def isIterative(self):
        return False

    def computeExpansions(self, data, initial_candidates):
        fim_variant = self.constraints.getCstr("fim_variant")
        if fim_variant == "mas":
            return self.computeExpansionsMineAndSplit(data, initial_candidates)
        elif fim_variant == "map":
            return self.computeExpansionsMineAndPair(data, initial_candidates)
        else:
            raise Exception(f"Invalid fim_variant value: {fim_variant}")

    def computeExpansionsMineAndPair(self, data, initial_candidates_full):
        zmin = 1
        min_supp = self.constraints.getCstr("min_itm_in")

        candidate_store_setts = dict([(k, self.constraints.getCstr(k)) for k in ["max_var_s0", "max_var_s1",
                                                                                 "min_itm_in", "min_itm_out",
                                                                                 "min_fin_acc"]])
        candidate_store = CandStoreMineAndPair(candidate_store_setts)
        tid_lists = TIDList()
        initial_candidates = [None, None]
        initial_candidates_map = [None, None]
        for side in [0, 1]:
            zmax = self.constraints.getCstr(f"max_var_s{side}")
            initial_candidates[side] = [candidate.getLit() for candidate in initial_candidates_full
                                        if candidate.getSide() == side]
            tracts = [[] for _ in range(data.nbRows())]
            initial_candidates_map[side] = defaultdict(list)
            for i, candidate in enumerate(initial_candidates[side]):
                candidate_supp = data.supp(side, candidate)
                if len(candidate_supp) < min_supp:
                    continue
                column_id = candidate.colId()
                k = (side, column_id, len(initial_candidates_map[side][column_id]))
                initial_candidates_map[side][column_id].append(i)
                tid_lists.set_data(side, k, candidate_supp)
                for row_id in candidate_supp:
                    tracts[row_id].append(k)

            tracts = [frozenset(t) for t in tracts]
            r = mod_eclat(tracts, ['s', min_supp, zmin, zmax, zmax + 1], candidate_store.add)
        queries = candidate_store.getQueries(tid_lists)
        lits = []
        for qs in queries:
            lits_s0 = [initial_candidates[q[0]][initial_candidates_map[0][q[1]][q[2]]] for q in qs[0]]
            lits_s1 = [initial_candidates[q[0]][initial_candidates_map[1][q[1]][q[2]]] for q in qs[1]]
            query_s0 = Query(False, lits_s0)
            query_s1 = Query(False, lits_s1)
            r = Redescription.fromQueriesPair([query_s0, query_s1], data, copyQ=False)
            lits.append(r)
        return lits

    def computeExpansionsMineAndSplit(self, data, initial_candidates_full):
        tracts = [[] for _ in range(data.nbRows())]
        initial_candidates = []
        initial_candidates_map = [{}, {}]
        tid_lists = TIDList()
        for i, candidate in enumerate(initial_candidates_full):
            side = candidate.getSide()
            column_id = candidate.getCid()
            initial_candidates.append(candidate.getLit())
            if column_id not in initial_candidates_map[side]:
                initial_candidates_map[side][column_id] = []
            k = (side, column_id, len(initial_candidates_map[side][column_id]))
            initial_candidates_map[side][column_id].append(i)
            supps = data.supp(side, candidate.getLit())
            tid_lists.set_data(side, k, supps)
            for row_id in supps:
                tracts[row_id].append(k)
        tracts = [frozenset(t) for t in tracts]

        zmin = 1
        zmax = self.constraints.getCstr("max_var_s0") + self.constraints.getCstr("max_var_s1")
        maxx = zmax + 1
        min_supp = self.constraints.getCstr("min_itm_in")

        candidate_store_setts = dict([(k, self.constraints.getCstr(k)) for k in ["max_var_s0", "max_var_s1",
                                                                                 "min_itm_in", "min_itm_out",
                                                                                 "min_fin_acc"]])

        candidate_store = CandStoreMineAndSplit(candidate_store_setts)
        r = mod_eclat(tracts, ['s', min_supp, zmin, zmax, maxx], candidate_store.add)
        queries = candidate_store.getQueries(tid_lists)

        lits = []
        for qs in queries:
            #  could be to recover the original variables
            literals_s0 = [initial_candidates[initial_candidates_map[0][q[1]][q[2]]] for q in qs[0]]
            literals_s1 = [initial_candidates[initial_candidates_map[1][q[1]][q[2]]] for q in qs[1]]
            r = Redescription.fromQueriesPair([Query(False, literals_s0), Query(False, literals_s1)], data, copyQ=False)
            lits.append(r)
        return lits

