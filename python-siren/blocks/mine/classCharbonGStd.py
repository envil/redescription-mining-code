import numpy
try:
    from classCol import NumColM
    from classData import Data
    from classConstraints import Constraints
    from classCharbon import CharbonGreedy
    from classCandidates import CondCand, ExtensionWarning
    from classSParts import SParts, cmp_lower, cmp_greater, cmp_leq, cmp_geq
    from classQuery import *
except ModuleNotFoundError:
    from .classCol import NumColM
    from .classData import Data
    from .classConstraints import Constraints
    from .classCharbon import CharbonGreedy
    from .classCandidates import CondCand, ExtensionWarning
    from .classSParts import SParts, cmp_lower, cmp_greater, cmp_leq, cmp_geq
    from .classQuery import *

import pdb


class CharbonGStd(CharbonGreedy):

    name = "GreedyStd"

    def getCandidates(self, side, col, red, colsC=None, data=None):
        self.store.toNextRound()
        supports = red.supports()
        currentRStatus = Constraints.getStatusRed(red, side)
        method_string = 'self.getCandidates%i' % col.typeId()
        try:
            method_compute = eval(method_string)
        except AttributeError:
            raise Exception('Oups No candidates method for this type of data (%i)!' % col.typeId())
        method_compute(side, col, supports, currentRStatus)

        if self.constraints.getCstr("debug_checks"):  # DEBUG
            # print("======STD ===========")
            for c in self.store.currentRoundIter():
                self.checkCountsExt(supports, col, c)
                self.checkRedExt(data, c)

        # compute additional condition
        if colsC is not None and self.constraints.getCstr("add_condition"):
            for c in self.store.currentRoundIter():
                ss = supports.copy()
                supp = col.suppLiteral(c.getLit())
                ss.update(side, c.getOp(), supp)
                cond_sparts = SParts(self.constraints.getSSetts(), ss.nbRows(), [ss.suppI(), ss.suppU()])
                lparts = cond_sparts.lparts()
                cond_cand = self.getConditionCand(colsC, cond_sparts, lparts)
                if cond_cand is not None:
                    c.setCondition(cond_cand)
                    if self.constraints.getCstr("debug_checks"):  # DEBUG
                        csp = SParts(self.constraints.getSSetts(), ss.nbRows(), [sI, sD.union(sI)])  # modified when getting the condition
                        self.checkCountsCond(colsC, csp, cond_cand)
                        self.checkRedExt(data, c)

        return self.store.currentRoundIter()

    def getCandidatesImprov(self, side, col, red, op, supports, offsets):
        self.store.toNextRound()
        self.setOffsets(offsets)
        currentRStatus = Constraints.getStatusRed(red, side, [op])
        method_string = 'self.getCandidates%i' % col.typeId()
        try:
            method_compute = eval(method_string)
        except AttributeError:
            raise Exception('Oups No candidates method for this type of data (%i)!' % col.typeId())
        method_compute(side, col, supports, currentRStatus)
        self.setOffsets()
        return self.store.currentRoundIter()

    def getCandidates1(self, side, col, supports, currentRStatus=0):
        lparts = supports.lparts()
        lin = supports.lpartsInterX(col.supp())

        for op in self.constraints.getCstr("allw_ops", side=side, currentRStatus=currentRStatus):
            for neg in self.constraints.getCstr("allw_negs", side=side, type_id=col.typeId(), currentRStatus=currentRStatus):
                adv, clp, stt = self.getAC(side, op, neg, [lparts, lin], self.isCond(currentRStatus))
                if adv is not None:
                    self.addExtToStore(False, adv, clp, (side, op, neg, Literal(neg, BoolTerm(col.getId()))))

    def getCandidates2(self, side, col, supports, currentRStatus=0):
        self.getCandidatesNonBool(side, col, supports, currentRStatus)

    def getCandidates3(self, side, col, supports, currentRStatus=0):
        self.getCandidatesNonBool(side, col, supports, currentRStatus)

    def getCandidatesNonBool(self, side, col, supports, currentRStatus=0):
        lparts = supports.lparts()
        self.findCover(side, col, lparts, supports, currentRStatus)

    ##################################################
    # CONDITIONAL

    def isCond(self, currentRStatus=0):
        return self.constraints.isStatusCond(currentRStatus)

    def getConditionCand(self, colsC, cond_sparts, lparts):
        cis = range(len(colsC))
        prev = None
        best = ([], 0)
        while len(cis) > 0:  # if there are multiple condition attributes, iteratively and greedily try to find a combination
            current = []
            for ci in cis:
                # collect the best candidate for each condition attribute, if fit only returns one
                self.startStoreDivert()
                self.findCover(1, colsC[ci], lparts, cond_sparts, Constraints.getStatusCond())
                cands = self.stopStoreDivert()
                if len(cands) == 1:
                    cand = CondCand(*cands[0][1:])
                    if cmp_lower(best[1], cand.getAcc()):
                        best = ([len(current)], cand.getAcc())
                    elif best[1] == cand.getAcc():
                        best[0].append(len(current))
                    current.append(cand)
            if len(best[0]) == 0:
                cis = []
            else:
                basis = (None, None, cond_sparts.nbRows(), 0.)
                for cc in best[0]:  # among the best candidates, select top w.r.t. VarRed
                    cand = current[cc]
                    supp = colsC[cand.getCid()].suppLiteral(cand.getLit())
                    if cand.getVarRed() > basis[-1] or (cand.getVarRed() == basis[-1] and len(supp) < basis[-2]):
                        basis = (cc, supp, len(supp), cand.getVarRed())
                cis = [ci for cii, ci in enumerate(cis) if basis[0] != cii]
                keep_cand, keep_supp = current[basis[0]], basis[1]
                if prev is None:
                    keep_cand.setLit([keep_cand.getLit()])
                else:
                    keep_cand.setLit([keep_cand.getLit()]+prev.getLit())
                prev = keep_cand
                cond_sparts.update(1, False, keep_supp)
                lparts = cond_sparts.lparts()
                best = ([], prev.getAcc())
        return prev

    def getCCandSupp(self, colsC, cond_cand):
        lits = cond_cand.getLit()
        if type(lits) is Literal:
            lits = [lits]
        return set.intersection(*[colsC[lit.colId()].suppLiteral(lit) for lit in lits])

    ##################################################
    # COVER METHODS

    def findCover(self, side, col, lparts, supports, currentRStatus=0):
        method_string = 'self.findCover%i' % col.typeId()
        try:
            method_compute = eval(method_string)
        except AttributeError:
            raise Exception('Oups No covering method for this type of data (%i)!' % col.typeId())
        method_compute(side, col, lparts, supports, currentRStatus)

    def findCover1(self, side, col, lparts, supports, currentRStatus=0):
        lin = supports.lpartsInterX(col.supp())
        if self.constraints.getCstr("neg_query_init", side=side, currentRStatus=currentRStatus):
            nlparts = self.constraints.getSSetts().negateParts(1-side, lparts)
            nlin = self.constraints.getSSetts().negateParts(1-side, lin)

        for op in self.constraints.getCstr("allw_ops", side=side, currentRStatus=currentRStatus):
            for neg in self.constraints.getCstr("allw_negs", side=side, type_id=col.typeId(), currentRStatus=currentRStatus):
                adv, clp, stt = self.getAC(side, op, neg, [lparts, lin], self.isCond(currentRStatus))
                if adv is not None:
                    self.addExtToStore(False, adv, clp, (side, op, neg, Literal(neg, BoolTerm(col.getId()))))

                # to negate the other side when looking for initial pairs
                if self.constraints.getCstr("neg_query_init", side=side, currentRStatus=currentRStatus):
                    adv, clp, stt = self.getAC(side, op, neg, [nlparts, nlin], self.isCond(currentRStatus))
                    if adv is not None:
                        self.addExtToStore(True, adv, clp, (side, op, neg, Literal(neg, BoolTerm(col.getId()))))

    def findCover2(self, side, col, lparts, supports, currentRStatus=0):
        allw_neg = True in self.constraints.getCstr("allw_negs", side=side, type_id=col.typeId(), currentRStatus=currentRStatus)
        negs = self.constraints.getCstr("allw_negs", side=side, type_id=col.typeId(), currentRStatus=currentRStatus)
        if self.constraints.getCstr("multi_cats"):  # redundant negation
            negs = [False]

        if self.constraints.getCstr("neg_query_init", side=side, currentRStatus=currentRStatus):
            nlparts = self.constraints.getSSetts().negateParts(1-side, lparts)

        for op in self.constraints.getCstr("allw_ops", side=side, currentRStatus=currentRStatus):
            for neg in negs:
                best = (None, None, None)
                bestNeg = (None, None, None)
                collect_goods = []
                collect_goodsNeg = []
                for (cat, supp) in col.iter_cats():
                    lin = supports.lpartsInterX(supp)
                    tmp_adv, tmp_clp, stt = self.getAC(side, op, neg, [lparts, lin], self.isCond(currentRStatus))
                    if tmp_adv is not None:
                        if cmp_lower(best[0], tmp_adv):
                            best = (tmp_adv, tmp_clp, [side, op, neg, Literal(neg, CatTerm(col.getId(), cat))])
                        collect_goods.append((tmp_adv, tmp_clp, cat))

                    # to negate the other side when looking for initial pairs
                    if self.constraints.getCstr("neg_query_init", side=side, currentRStatus=currentRStatus):
                        nlin = self.constraints.getSSetts().negateParts(1-side, lin)
                        tmp_adv, tmp_clp, stt = self.getAC(side, op, neg, [nlparts, nlin], self.isCond(currentRStatus))
                        if tmp_adv is not None:
                            if cmp_lower(bestNeg[0], tmp_adv):
                                bestNeg = (tmp_adv, tmp_clp, [side, op, neg, Literal(neg, CatTerm(col.getId(), cat))])
                            collect_goodsNeg.append((tmp_adv, tmp_clp, cat))

                if best[0] is not None:
                    bb = self.combCats(best, allw_neg, side, op, neg, col, collect_goods, currentRStatus=currentRStatus)
                    self.addExtToStore(False, *bb)
                if bestNeg[0] is not None:
                    bb = self.combCats(bestNeg, allw_neg, side, op, neg, col, collect_goodsNeg, currentRStatus=currentRStatus)
                    self.addExtToStore(True, *bb)

    def findCover3(self, side, col, lparts, supports, currentRStatus=0):
        counts = None  # so counts can be reused for ops, rather than recomputed
        for op in self.constraints.getCstr("allw_ops", side=side, currentRStatus=currentRStatus):

            if self.constraints.isStatusCond(currentRStatus) or self.inSuppBounds(side, op, lparts):  # DOABLE
                segments, counts = col.makeSegments(self.constraints.getSSetts(), side, supports, op, counts)
                self.findCoverSegments(side, op, col, segments, counts, lparts, currentRStatus, nego=False)

            # to negate the other side when looking for initial pairs
            if self.constraints.getCstr("neg_query_init", side=side, currentRStatus=currentRStatus):
                nlparts = self.constraints.getSSetts().negateParts(1-side, lparts)

                if self.inSuppBounds(side, op, nlparts):  # DOABLE (op is True, OR, for initial pairs)
                    nsegments, ncounts = col.makeSegments(self.constraints.getSSetts(), side, supports.negate(1-side), op)
                    self.findCoverSegments(side, op, col, nsegments, ncounts, nlparts, currentRStatus, nego=True)

    def findCoverSegments(self, side, op, col, segments, counts, lparts, currentRStatus=0, nego=None):
        if len(segments) < self.constraints.getCstr("max_seg"):
            self.findCoverFullSearch(side, op, col, segments, counts, lparts, currentRStatus, nego)
        else:
            if (False in self.constraints.getCstr("allw_negs", side=side, type_id=col.typeId(), currentRStatus=currentRStatus)):
                self.findPositiveCover(side, op, col, segments, counts, lparts, currentRStatus, nego)
            if (True in self.constraints.getCstr("allw_negs", side=side, type_id=col.typeId(), currentRStatus=currentRStatus)):
                self.findNegativeCover(side, op, col, segments, counts, lparts, currentRStatus, nego)

    def findCoverFullSearch(self, side, op, col, segments, counts, lparts, currentRStatus=0, nego=None):
        bests = {False: (None, None, None), True: (None, None, None)}
        for seg_si, seg_s in enumerate(segments):
            for seg_e in segments[seg_si:]:
                lin = numpy.sum(counts[seg_s[0]:seg_e[1]+1], axis=0)
                for neg in self.constraints.getCstr("allw_negs", side=side, type_id=col.typeId(), currentRStatus=currentRStatus):
                    bests[neg], stt = self.updateACT(bests[neg], (seg_s[0], seg_e[1]), side, op, neg, [lparts, lin], self.isCond(currentRStatus))

        for neg in self.constraints.getCstr("allw_negs", side=side, type_id=col.typeId(), currentRStatus=currentRStatus):
            if bests[neg][0] is not None:
                seg = bests[neg][-1][-1]
                bests[neg][-1][-1] = col.getLiteralSeg(neg, bests[neg][-1][-1])
                if self.constraints.getCstr("debug_checks"):  # DEBUG
                    self.checkCountsSeg(counts, seg, col, bests[neg][-1][-1], bests[neg][1], comp=neg)
                if bests[neg][-1][-1] is not None:
                    self.addExtToStore(nego, *bests[neg])

    def findPositiveCover(self, side, op, col, segments, counts, lparts, currentRStatus=0, nego=None):
        is_cond = self.isCond(currentRStatus)

        lin_f = numpy.zeros(counts.shape[1], dtype=int)
        bound_ids_f = []
        best_f = (None, None, None)
        lin_b = numpy.zeros(counts.shape[1], dtype=int)
        bound_ids_b = []
        best_b = (None, None, None)
        for i, seg_f in enumerate(segments[:-1]):
            # FORWARD
            # seg_f = segments[i]
            lin_segf = numpy.sum(counts[seg_f[0]:seg_f[1]+1], axis=0)
            if i > 0 and cmp_lower(self.advAcc(side, op, False, [lparts, lin_segf], is_cond), self.advRatioVar(side, op, lin_f, is_cond)):
                lin_f += numpy.sum(counts[bound_ids_f[1]+1:seg_f[1]+1], axis=0)
                bound_ids_f[1] = seg_f[1]
            else:
                lin_f = lin_segf
                bound_ids_f = [seg_f[0], seg_f[1]]
            best_f, stt = self.updateACT(best_f, tuple(bound_ids_f), side, op,
                                         False, [lparts, list(lin_f)], is_cond)
            # print("FWD", i, best_f[0], best_f[1][0] if best_f[1] is not None else best_f[1], bound_ids_f, lin_f)

            # BACKWARD
            seg_b = segments[-(i+1)]
            lin_segb = numpy.sum(counts[seg_b[0]:seg_b[1]+1], axis=0)
            if i > 0 and cmp_lower(self.advAcc(side, op, False, [lparts, lin_segb], is_cond),
                                   self.advRatioVar(side, op, lin_b, is_cond)):
                lin_b += numpy.sum(counts[seg_b[0]:bound_ids_b[0]], axis=0)
                bound_ids_b[0] = seg_b[0]
            else:
                lin_b = lin_segb
                bound_ids_b = [seg_b[0], seg_b[1]]
            best_b, stt = self.updateACT(best_b, tuple(bound_ids_b), side, op,
                                         False, [lparts, list(lin_b)], is_cond)
            # print("BWD", i, best_b[0], best_b[1][0] if best_b[1] is not None else best_b[1], bound_ids_b, lin_b)

        # print("END", best_f, best_b)
        if best_b[0] is not None and best_f[0] is not None:
            # Attempt to intersect the two candidates if they overlap
            bests = [best_b, best_f]
            if cmp_greater(best_b[-1][-1][0], best_f[-1][-1][0]) and \
                    cmp_greater(best_b[-1][-1][1], best_f[-1][-1][1]) and cmp_leq(best_b[-1][-1][0], best_f[-1][-1][1]):
                bounds_m = (best_b[-1][-1][0], best_f[-1][-1][1])
                lin_m = list(numpy.sum(counts[bounds_m[0]:bounds_m[1]+1], axis=0))
                tmp_adv_m, tmp_clp_m, stt = self.getAC(side, op, False, [lparts, lin_m], is_cond)
                if tmp_adv_m is not None:
                    bests.append((tmp_adv_m, tmp_clp_m, [side, op, False, bounds_m]))

            bests.sort()
            best = bests[-1]

        elif best_f[0] is not None:
            best = best_f
        else:
            best = best_b

        if best[0] is not None:
            seg = best[-1][-1]
            best[-1][-1] = col.getLiteralSeg(False, best[-1][-1])
            if self.constraints.getCstr("debug_checks"):  # DEBUG
                self.checkCountsSeg(counts, seg, col, best[-1][-1], best[1])
            if best[-1][-1] is not None:
                self.addExtToStore(nego, *best)

    def findNegativeCover(self, side, op, col, segments, counts, lparts, currentRStatus=0, nego=None):
        # negation is accounted for in counts in, so setting neg to False
        # should be returned to True for the produced candidates, to indicate they were generated with negation,
        # regardless of whether it was flipped when creating the literal, so duplicates with positive cover can be detected
        is_cond = self.isCond(currentRStatus)

        lin_f = numpy.zeros(counts.shape[1], dtype=int)
        bests_f = [(self.advAcc(side, op, False, [lparts, lin_f], is_cond), -1, lin_f)]
        lin_b = numpy.zeros(counts.shape[1], dtype=int)
        bests_b = [(self.advAcc(side, op, False, [lparts, lin_b], is_cond), -1, lin_b)]

        for i, seg_f in enumerate(segments):
            # FORWARD
            # find best cut points for intervals from bottom
            # seg_f = segments[i]
            if i > 0:
                lin_f += numpy.sum(counts[segments[i-1][0]:seg_f[0]], axis=0)
            else:
                lin_f = numpy.sum(counts[:seg_f[0]], axis=0)
            if cmp_greater(self.advRatioVar(side, op, lin_f, is_cond), bests_f[-1][0]):
                lin_f += bests_f[-1][2]
                bests_f.append((self.advAcc(side, op, False, [lparts, lin_f], is_cond), seg_f[0], lin_f))
                lin_f = numpy.zeros(counts.shape[1], dtype=int)

            # BACKWARD
            # find best cut points for intervals from top
            seg_b = segments[-(i+1)]
            if i > 0:
                lin_b += numpy.sum(counts[seg_b[1]+1:segments[-i][1]+1], axis=0)
            else:
                lin_b = numpy.sum(counts[seg_b[1]+1:], axis=0)
            if cmp_greater(self.advRatioVar(side, op, lin_b, is_cond), bests_b[-1][0]):
                lin_b += bests_b[-1][2]
                bests_b.append((self.advAcc(side, op, False, [lparts, lin_b], is_cond), seg_b[1], lin_b))
                lin_b = numpy.zeros(counts.shape[1], dtype=int)

        bests_f.pop(0)
        bests_b.pop(0)
        bests_b.reverse()

        # pair,
        # a forward, i.e. lower bound, cut point should be paired
        # with any backward, i.e. upper bound, cut point that appears before the next forward cut point
        # ## Pairing too close bounds might not leave enough values out!
        ixf, ixb = (-1, 0)
        best_t = (None, None, None)
        stt_b, stt_f, stt_p = (None, None, None)
        while ixf < len(bests_f) and ixb < len(bests_b):
            if ixf+1 == len(bests_f) or bests_b[ixb][1] < bests_f[ixf+1][1]:
                best_t, stt_b = self.updateACT(best_t, (None, bests_b[ixb][1]), side, op,
                                               False, [lparts, bests_b[ixb][2]], is_cond)

                if ixf > -1 and not self.is_raised_flag(stt_b, self.FLG_OUT):
                    best_t, stt_p = self.updateACT(best_t, (bests_f[ixf][1], bests_b[ixb][1]), side, op,
                                                   False, [lparts, bests_b[ixb][2] + bests_f[ixf][2]], is_cond)
                    # print("<<< Pair %s %s\tf:%s b:%s p:%s\t%s %s" % (bests_f[ixf][1], bests_b[ixb][1],
                    #                                                  self.disp_status(stt_f), self.disp_status(stt_b), self.disp_status(stt_p),
                    #                                                  self.is_raised_flag(stt_b, self.FLG_OUT), self.is_raised_flag(stt_p, self.FLG_OUT)))

                    # if self.is_raised_flag(stt_b, self.FLG_OUT) and not self.is_raised_flag(stt_p, self.FLG_OUT):
                    #     pdb.set_trace()
                    # store_status, store_best = stt_p, best_t
                    # off_f = ixf
                    # while off_f > 0 and self.is_raised_flag(stt_p, self.FLG_OUT) and not self.is_raised_flag(stt_p, self.FLG_IN):
                    #     # if out is too small, but in is not
                    #     # try pairing with previous fwds to increase out
                    #     off_f -= 1
                    #     best_t, stt_p = self.updateACT(best_t, (bests_f[off_f][1], bests_b[ixb][1]), side, op,
                    #                                       False, [lparts, bests_b[ixb][2] + bests_f[off_f][2]], is_cond)
                    # print(">> Pair %s %s\tf:%s b:%s p:%s\t%s %s" % (bests_f[off_f][1], bests_b[ixb][1],
                    #                                                 self.disp_status(stt_f), self.disp_status(stt_b), self.disp_status(stt_p),
                    #                                                 self.is_raised_flag(stt_b, self.FLG_OUT), self.is_raised_flag(stt_p, self.FLG_OUT)))

                    # if stt_p == 0 and store_status > 0:
                    #     print("--------------------")
                    #     print(">>>", store_status, store_best)
                    #     print("<<<", best_t)
                ixb += 1
            else:
                ixf += 1
                best_t, stt_f = self.updateACT(best_t, (bests_f[ixf][1], None), side, op,
                                               False, [lparts, bests_f[ixf][2]], is_cond)

        if best_t[0] is not None:
            seg = best_t[-1][-1]
            best_t[-1][-1] = col.getLiteralSeg(True, best_t[-1][-1])
            if self.constraints.getCstr("debug_checks"):  # DEBUG
                self.checkCountsSeg(counts, seg, col, best_t[-1][-1], best_t[1], comp=True)
            if best_t[-1][-1] is not None:
                best_t[-1][2] = True
                self.addExtToStore(nego, *best_t)

    ##################################################
    # PAIRS METHODS

    def computePair(self, colL, colR, colsC=None, data=None):
        self.store.toNextRound()
        min_type = min(colL.typeId(), colR.typeId())
        max_type = max(colL.typeId(), colR.typeId())
        method_string = 'self.do%i%i' % (min_type, max_type)
        try:
            method_compute = eval(method_string)
        except AttributeError:
            raise Exception('Oups this combination does not exist (%i %i)!' % (min_type, max_type))
        if colL.typeId() == min_type:
            method_compute(colL, colR, 1)
        else:
            method_compute(colL, colR, 0)

        if self.constraints.getCstr("debug_checks"):  # DEBUG
            if data is not None:
                for c in self.store.currentRoundIter():
                    self.checkRedExt(data, c)

        self.store.removeNegDuplicates()
        if colsC is not None and self.constraints.getCstr("add_condition"):
            for c in self.store.currentRoundIter():
                # compute additional condition
                suppL = colL.suppLiteral(c.getLit(0))
                suppR = colR.suppLiteral(c.getLit(1))
                cond_sparts = SParts(self.constraints.getSSetts(), colL.nbRows(),
                                     [suppL.intersection(suppR), suppL.union(suppR)])
                lparts = cond_sparts.lparts()
                cond_cand = self.getConditionCand(colsC, cond_sparts, lparts)
                if cond_cand is not None:
                    c.setCondition(cond_cand)
                    if self.constraints.getCstr("debug_checks"):  # DEBUG
                        csp = SParts(self.constraints.getSSetts(), colL.nbRows(), [sI, sD.union(sI)])  # modified when getting the condition
                        self.checkCountsCond(colsC, csp, cond_cand)
                        self.checkRedExt(data, c)

        return self.store.currentRoundIter()

    def doBoolStar(self, colL, colR, side):
        if side == 1:
            (supports, fixTerm, extCol) = (SParts(self.constraints.getSSetts(), colL.nbRows(),
                                                  [colL.supp(), set()]), BoolTerm(colL.getId()), colR)
        else:
            (supports, fixTerm, extCol) = (SParts(self.constraints.getSSetts(), colL.nbRows(),
                                                  [set(), colR.supp()]), BoolTerm(colR.getId()), colL)
        self.fit(extCol, supports, side, fixTerm)

    def fit(self, col, supports, side, termX):
        lparts = supports.lparts()
        currentRStatus = Constraints.getStatusPair(col, side, termX)
        self.findCover(side, col, lparts, supports, currentRStatus=currentRStatus)
        for c in self.store.currentRoundIter():
            c.setLitTerm(termX, 1-side)

    def do11(self, colL, colR, side):
        self.doBoolStar(colL, colR, side)

    def do12(self, colL, colR, side):
        self.doBoolStar(colL, colR, side)

    def do13(self, colL, colR, side):
        self.doBoolStar(colL, colR, side)

    def do22(self, colL, colR, side):
        self.subdo22Full(colL, colR, side)

    def do23(self, colL, colR, side):
        self.subdo23Full(colL, colR, side)

    def do33(self, colL, colR, side):
        if len(colL.interNonMode(colR.nonModeSupp())) >= self.constraints.getCstr("min_itm_in"):
            self.subdo33Alts(colL, colR, side)

    def subdo33Alts(self, colL, colR, side):
        # print("###### subdo33Alts",  colL.getUid(), colR.getUid())
        org_side = side
        best = []
        interMat = []
        tails_params = {"lower_tail_agg": self.constraints.getCstr("lower_tail_agg"),
                        "upper_tail_agg": self.constraints.getCstr("upper_tail_agg")}
        if tails_params["lower_tail_agg"] != 0 or tails_params["upper_tail_agg"]:
            bucketsL = colL.buckets("tails", tails_params)
            bucketsR = colR.buckets("tails", tails_params)
        else:
            bucketsL = colL.buckets()
            bucketsR = colR.buckets()

        if len(bucketsL[0]) > len(bucketsR[0]):
            bucketsF = bucketsR
            colF = colR
            bucketsE = bucketsL
            colE = colL
            side = 1-side
        else:
            bucketsF = bucketsL
            colF = colL
            bucketsE = bucketsR
            colE = colR

        # DOABLE
        nbb = self.constraints.getCstr("max_prodbuckets") / float(len(bucketsF[1]))
        # print("--- Nb buckets: %i x %i, max buckets = %s, max agg = %s" %
        #       (len(bucketsF[1]), len(bucketsE[1]), self.constraints.getCstr("max_prodbuckets"), self.constraints.getCstr("max_agg")))
        # print("--- nbb=%s\tnb B E/nb=%s" % (nbb, len(bucketsE[1])/nbb))
        if len(bucketsE[1]) > nbb:

            if len(bucketsE[1])/nbb < self.constraints.getCstr("max_agg"):
                # collapsing buckets on the largest side is enough to get within the reasonable size
                # print("subdo33Alts A --- Collapsing just E")
                bucketsE = colE.buckets("collapsed", {"max_agg": self.constraints.getCstr("max_agg"), "nbb": nbb})

            else:
                # collapsing buckets on the largest side is NOT enough to get within the reasonable size
                # print("subdo33Alts B --- As categories?")
                bucketsE = None

                # try cats
                exclL = NumColM.buk_excl_bi(bucketsL)
                exclR = NumColM.buk_excl_bi(bucketsR)
                bbs = [dict([(bi, es) for (bi, es) in enumerate(bucketsL[0])
                             if (len(es) > self.constraints.getCstr("min_itm_in") and
                                 colL.nbRows() - len(es) > self.constraints.getCstr("min_itm_out") and (exclL is None or bi != exclL))]),
                       dict([(bi, es) for (bi, es) in enumerate(bucketsR[0])
                             if (len(es) > self.constraints.getCstr("min_itm_in") and
                                 colR.nbRows() - len(es) > self.constraints.getCstr("min_itm_out") and (exclR is None or bi != exclR))])]

                # if len(bbs[0]) > 0 and ( len(bbs[1]) == 0 or len(bbs[0])/float(len(bucketsL[0])) < len(bbs[1])/float(len(bucketsR[0]))):
                nbes = [max(sum([len(v) for (k, v) in bbs[s].items()]), .5) for s in [0, 1]]
                sideN = None
                # Decide which side to make categorical, based on the number and cardinalities of the categories that would result
                # will get through in subdo23? ((len(buckets[1]) * len(colF.cats()) <= self.constraints.getCstr("max_prodbuckets")))
                if len(bbs[0]) > 0 and (len(bbs[1]) == 0 or nbes[0]/len(bbs[0]) > nbes[1]/len(bbs[1])):
                    sideN, ccN, ccC, ccCN, bucksC = (1, colR, Data.getColClassForName("Categorical")(bbs[0], colL.nbRows(), colL.miss()), colL, bucketsL)
                elif len(bbs[1]) > 0:
                    sideN, ccN, ccC, ccCN, bucksC = (0, colL, Data.getColClassForName("Categorical")(bbs[1], colR.nbRows(), colR.miss()), colR, bucketsR)

                if sideN is not None:
                    # working with variable as categories is doable
                    # print("Trying cats...", len(bucketsL[0]), len(bucketsR[0]), len(bbs[0]), len(bbs[1]))
                    self.startStoreDivert()
                    self.subdo23Full(ccC, ccN, 1, try_comb=False)
                    cands = self.stopStoreDivert()
                    for cand in cands:
                        # the column that was turned categorical
                        ltc = cand[2]
                        c = ltc.getTerm().getCat()
                        if type(c) is set and len(c) > 0:
                            c = sorted(c)[0]
                        valLow = bucksC[1][c]
                        valUp = bucksC[NumColM.buk_ind_maxes(bucksC)][c]
                        cand = list(cand)
                        cand[2] = Literal(ltc.isNeg(), NumTerm(ccCN.getId(), valLow, valUp))
                        cand[-1] = sideN
                        if self.constraints.getCstr("debug_checks"):  # DEBUG
                            # the column that was kept numerical
                            self.checkCountsPair(1, False, ccCN, ccN, cand[2], cand[3], cand[1])
                        self.addPairToStore(*cand)
                    return
                else:
                    # working with variable as categories is NOT doable
                    # the only remaining solution is aggressive collapse of buckets on both sides
                    # print("subdo33Alts C --- Collapsing both")
                    nbb = numpy.sqrt(self.constraints.getCstr("max_prodbuckets"))
                    bucketsE = colE.buckets("collapsed", {"max_agg": self.constraints.getCstr("max_agg"), "nbb": nbb})
                    bucketsF = colF.buckets("collapsed", {"max_agg": self.constraints.getCstr("max_agg"), "nbb": nbb})
                    # print("Last resort solution... Collapsing both E and F", nbb, len(bucketsL[0]), len(bucketsR[0]))

        # print("buckets lengths\t(0,%d) %d\t(1,%d) %d\tcollapsed %d -- product %d" % (colL.getId(), len(bucketsL[1]), colR.getId(), len(bucketsR[1]), len(bucketsE[1]), len(bucketsF[1]) * len(bucketsE[1])))
        if bucketsE is not None and (len(bucketsF[1]) * len(bucketsE[1]) < self.constraints.getCstr("max_prodbuckets")):
            # print("subdo33Alts D --- Trying buckets...", len(bucketsF[0]), len(bucketsE[0]))
            totInt = colE.nbRows()
            # margE = [len(intE) for intE in bucketsE[0]]

            margF = [len(bucketsF[0][i]) for i in range(len(bucketsF[0]))]

            for bukF in bucketsF[0]:
                interMat.append([len(bukF & bukE) for bukE in bucketsE[0]])

            if bucketsF[2] is not None:
                margF[bucketsF[2]] += colF.lenMode()
                for bukEId in range(len(bucketsE[0])):
                    interMat[bucketsF[2]][bukEId] += len(colF.interMode(bucketsE[0][bukEId]))

            if bucketsE[2] is not None:
                # margE[bucketsE[2]] += colE.lenMode()
                for bukFId in range(len(bucketsF[0])):
                    interMat[bukFId][bucketsE[2]] += len(colE.interMode(bucketsF[0][bukFId]))

            if bucketsF[2] is not None and bucketsE[2] is not None:
                interMat[bucketsF[2]][bucketsE[2]] += len(colE.interMode(colF.modeSupp()))

            # ### check marginals
            # totF = 0
            # for iF in range(len(bucketsF[0])):
            #     sF = sum(interMat[iF])
            #     if sF != margF[iF]:
            #         raise Error('Error in computing the marginals (1)')
            #     totF += sF

            # totE = 0
            # for iE in range(len(bucketsE[0])):
            #     sE = sum([intF[iE] for intF in interMat])
            #     if sE != margE[iE]:
            #         raise Error('Error in computing the marginals (2)')
            #     totE += sE

            # if totE != totF or totE != colE.nbRows():
            #     raise Error('Error in computing the marginals (3)')

            exclF = NumColM.buk_excl_bi(bucketsF)
            exclE = NumColM.buk_excl_bi(bucketsE)
            belowF = 0
            lowF = 0
            while lowF < len(interMat) and totInt - belowF >= self.constraints.getCstr("min_itm_in"):
                aboveF = 0
                upF = len(interMat)-1

                if exclF is not None:
                    if lowF == exclF:  # basically, skip this value
                        upF = lowF-1
                    elif lowF < exclF:
                        upF = exclF-1
                        aboveF = numpy.sum(margF[upF+1:])

                while upF >= lowF and totInt - belowF - aboveF >= self.constraints.getCstr("min_itm_in"):
                    if belowF + aboveF >= self.constraints.getCstr("min_itm_out"):
                        EinF = [sum([interMat[iF][iE] for iF in range(lowF, upF+1)]) for iE in range(len(interMat[lowF]))]
                        EoutF = [sum([interMat[iF][iE] for iF in list(range(0, lowF))+list(range(upF+1, len(interMat)))]) for iE in range(len(interMat[lowF]))]
                        # totEinF = sum(EinF)
                        lparts = self.constraints.getSSetts().makeLParts([totInt - aboveF - belowF,
                                                                          aboveF + belowF], side=side)
                        belowEF = 0
                        outBelowEF = 0
                        lowE = 0
                        while lowE < len(interMat[lowF]) and totInt - belowF - aboveF - belowEF >= self.constraints.getCstr("min_itm_in"):
                            aboveEF = 0
                            outAboveEF = 0
                            upE = len(interMat[lowF])-1

                            if exclE is not None:
                                if lowE == exclE:  # basically, skip this value
                                    upE = lowE-1
                                elif lowE < exclE:
                                    upE = exclE-1
                                    aboveEF = numpy.sum(EinF[upE+1:])
                                    outAboveEF = numpy.sum(EoutF[upE+1:])

                            while upE >= lowE and totInt - belowF - aboveF - belowEF - aboveEF >= self.constraints.getCstr("min_itm_in"):
                                lin = self.constraints.getSSetts().makeLParts([totInt - belowF - aboveF - belowEF - aboveEF,
                                                                               belowF + aboveF - outAboveEF - outBelowEF], side=side)

                                stt = self.updateACTList(33, best, (lowF, upF, lowE, upE), side, True, False, [lparts, lin])
                                aboveEF += EinF[upE]
                                outAboveEF += EoutF[upE]
                                upE -= 1
                            belowEF += EinF[lowE]
                            outBelowEF += EoutF[lowE]
                            lowE += 1
                    aboveF += margF[upF]
                    upF -= 1
                belowF += margF[lowF]
                lowF += 1

        bUpE = NumColM.buk_ind_maxes(bucketsE)  # in case of collapsed bucket the threshold is different
        bUpF = NumColM.buk_ind_maxes(bucketsF)  # in case of collapsed bucket the threshold is different
        self.updateBests(33, best)
        for b in best:
            tF = colF.getLiteralBuk(False, bucketsF[1], b[-1][-1][0:2], bucketsF[bUpF])
            tE = colE.getLiteralBuk(False, bucketsE[1], b[-1][-1][2:], bucketsE[bUpE])
            if self.constraints.getCstr("debug_checks"):  # DEBUG
                self.checkCountsPair(side, False, colF, colE, tF, tE, b[1])
            if tF is not None and tE is not None:
                self.addPairToStore(b[0], b[1], tF, tE, False, False, side)

    def subdo22Full(self, colL, colR, side):
        configs = [(False, False), (False, True), (True, False), (True, True)]

        allw_neg = True
        if True not in self.constraints.getCstr("neg_query", side=side, type_id=2):
            configs = configs[:1]
            allw_neg = False
        best = [[] for c in configs]

        # print("--------------------------------------")
        # print("\t".join(["", ""]+[catR for catR in colR.cats()]))
        # print("\t".join(["", ""]+["%d" % colR.lsuppCat(catR) for catR in colR.cats()]))
        # for catL in colL.cats():
        #     print("\t".join([catL, "%d" % colL.lsuppCat(catL)]+["%d" % len(colL.suppCat(catL).intersection(colR.suppCat(catR))) for catR in colR.cats()]))
        # print("--------------------------------------")

        tot = colL.nbRows()
        for catL in colL.cats():
            totL = len(colL.suppCat(catL))
            lparts = [totL, 0, 0, colL.nbRows()-totL]

            for catR in colR.cats():
                totR = len(colR.suppCat(catR))
                interLR = len(colL.suppCat(catL) & colR.suppCat(catR))
                lin = [interLR, 0, 0, totR - interLR]
                for i, (nL, nR) in enumerate(configs):
                    if nL:
                        tmp_lparts = self.constraints.getSSetts().negateParts(0, lparts)
                        tmp_lin = self.constraints.getSSetts().negateParts(0, lin)
                    else:
                        tmp_lparts = lparts
                        tmp_lin = lin

                    stt = self.updateACTList(22, best[i], (catL, catR), side, True, nR, [tmp_lparts, tmp_lin], pre_multi=self.constraints.getCstr("multi_cats"))

        for i, (nL, nR) in enumerate(configs):
            if self.constraints.getCstr("multi_cats"):
                self.combCatsPair(best[i], colL, colR, nL, nR, allw_neg)
            self.updateBests(22, best[i])

            for b in best[i]:
                tL = Literal(nL, CatTerm(colL.getId(), b[-1][-1][0]))
                tR = Literal(nR, CatTerm(colR.getId(), b[-1][-1][1]))
                if self.constraints.getCstr("debug_checks"):  # DEBUG
                    self.checkCountsPair(side, False, colL, colR, tL, tR, b[1])
                self.addPairToStore(b[0], b[1], tL, tR, nL, nR, side)

    def subdo23Full(self, colL, colR, side, try_comb=True):
        multi_cats = try_comb and self.constraints.getCstr("multi_cats")
        if side == 0:
            (colF, colE) = (colR, colL)
        else:
            (colF, colE) = (colL, colR)

        configs = [(False, False), (False, True), (True, False), (True, True)]
        allw_neg = True
        if True not in self.constraints.getCstr("neg_query", side=side, type_id=3):
            configs = configs[:1]
            allw_neg = False
        best = [[] for c in configs]

        buckets = colE.buckets()
        nbb = self.constraints.getCstr("max_prodbuckets") / len(colF.cats())
        if len(buckets[1]) > nbb:  # self.constraints.getCstr("max_sidebuckets"):
            buckets = colE.buckets("collapsed", {"max_agg": self.constraints.getCstr("max_agg"), "nbb": nbb})

        # TODO DOABLE
        if buckets is not None and (len(buckets[1]) * len(colF.cats()) <= self.constraints.getCstr("max_prodbuckets")):

            marg = [len(buk) for buk in buckets[0]]
            if buckets[2] is not None:
                marg[buckets[2]] += colE.lenMode()

            for cat in colF.cats():
                lparts = self.constraints.getSSetts().makeLParts([colF.lsuppCat(cat),
                                                                  colF.nbRows() - colF.lsuppCat(cat)], side=side)

                interMat = [len(colF.suppCat(cat) & buk) for buk in buckets[0]]
                if buckets[2] is not None:
                    interMat[buckets[2]] += len(colE.interMode(colF.suppCat(cat)))

                totIn = sum(interMat)
                below = 0
                low = 0
                while low < len(interMat) and \
                        (totIn - below >= self.constraints.getCstr("min_itm_in") or
                         totIn - below >= self.constraints.getCstr("min_itm_out")):
                    above = 0
                    up = len(interMat)-1
                    while up >= low and \
                            (totIn - below - above >= self.constraints.getCstr("min_itm_in") or
                             totIn - below - above >= self.constraints.getCstr("min_itm_out")):
                        lin = self.constraints.getSSetts().makeLParts([totIn - below - above,
                                                                       sum(marg[low:up+1]) - totIn + below + above], side=side)

                        for i, (nF, nE) in enumerate(configs):
                            if nF:
                                tmp_lparts = self.constraints.getSSetts().negatePartsV(1-side, lparts)
                                tmp_lin = self.constraints.getSSetts().negatePartsV(1-side, lin)
                            else:
                                tmp_lparts = lparts
                                tmp_lin = lin

                            stt = self.updateACTList(23, best[i], (cat, low, up), side, True, nE, [tmp_lparts, tmp_lin], pre_multi=multi_cats)

                        above += interMat[up]
                        up -= 1
                    below += interMat[low]
                    low += 1

        bUp = NumColM.buk_ind_maxes(buckets)
        for i, (nF, nE) in enumerate(configs):
            if multi_cats:
                self.combCatsNum(best[i], colF, colE, nF, nE, allw_neg, side, buckets, bUp)
            self.updateBests(23, best[i])

            for b in best[i]:
                tE = colE.getLiteralBuk(nE, buckets[1], b[-1][-1][1:], buckets[bUp])
                tF = colF.getLiteralCat(nF, b[-1][-1][0])
                if self.constraints.getCstr("debug_checks"):  # DEBUG
                    self.checkCountsPair(side, False, colF, colE, tF, tE, b[1])
                if tE is not None and tF is not None:
                    self.addPairToStore(b[0], b[1], tF, tE, nF, nE, side)

    ##################################################
    # METHODS COMBINING CATEGORIES

    def additionsLParts(self, prevc, nextc, side=1, neg=False, other_side=False):
        # prevc and nextc are numpy array containing clp in rows lparts,[ lmiss,] lin
        c = numpy.array(nextc, dtype=int)
        if other_side:
            if side == 1:  # Exo(union) = Exo(A) + Exo(B); Eoo(union) = Eoo(A) - Exo(B); Emo(union) = Emo(A)
                p_from, p_to = (self.constraints.getSSetts().Eoo, self.constraints.getSSetts().Exo)
            else:
                p_from, p_to = (self.constraints.getSSetts().Eoo, self.constraints.getSSetts().Eox)
            if neg:
                p_from, p_to = (p_to, p_from)
            transv = prevc[:, p_to]
            c[:, p_from] -= transv
            c[:, p_to] += transv
        else:
            if neg:
                disj, comp = (-2, -1)  # adding disjoint lout, lparts[ and lmiss] are the same, adjusting lin
            else:
                disj, comp = (-1, -2)  # adding disjoint lin, lparts[ and lmiss] are the same, adjusting lout
            c[disj, :] += prevc[disj, :]
            c[comp, :] = c[0, :] - c[disj, :]
        return c

    def combCats(self, best, allw_neg, side, op, neg, col, collected, other_side=False, other_neg=False, currentRStatus=0):
        if not self.constraints.getCstr("multi_cats"):
            return best
        collected.sort(key=lambda x: (x[0], x[-1]))
        nextc = collected.pop()
        best_adv = nextc[0]
        cum_counts = numpy.array(nextc[1], dtype=int)
        best_cat = [nextc[-1]]
        # print("---", nextc[-1], "\t",  best_adv)
        while len(collected) > 0:
            nextc = collected.pop()
            # part counts have already been negated earlier where relevant,
            # this is accounted for in addition and neg is set to False in getAC,
            ccum_counts = self.additionsLParts(cum_counts, nextc[1], side, neg, other_side)
            tmp_adv, tmp_clp, stt = self.getAC(side, op, False, ccum_counts, self.isCond(currentRStatus), filled=True)
            # tmp_acc = self.advAcc(side, op, False, ccum_counts, self.isCond(currentRStatus), filled=True)
            # print(best_cat, nextc[-1], "\t",  tmp_adv, self.disp_status(stt))
            if tmp_adv is not None and cmp_lower(best_adv, tmp_adv):
                best_adv = tmp_adv
                cum_counts = ccum_counts
                best_cat.append(nextc[-1])
        if len(best_cat) > 1:  # otherwise best did not change
            # best_adv, best_clp, stt = self.getAC(side, op, False, cum_counts, self.isCond(currentRStatus), filled=True)
            if best_adv is not None:
                if col is None:
                    best = (best_adv, cum_counts, [side, op, neg, set(best_cat)])
                else:
                    lit = col.getLiteralCat(neg, best_cat, allw_neg)
                    if lit is not None:
                        best = (best_adv, cum_counts, [side, op, lit.isNeg(), lit])
        return best

    def combCatsPair(self, besti, colF, colE, nF, nE, allw_neg):
        map_cat_rs = [[{}, {}], [{}, {}]]
        # collect together all candidates that have the same category
        for b in besti:
            for ss in [0, 1]:
                cat = b[-1][-1][ss]
                if cat not in map_cat_rs[0][ss]:
                    map_cat_rs[0][ss][cat] = []
                map_cat_rs[0][ss][cat].append((b[0], b[1], b[-1][-1][1-ss]))
                # adv, clp, cat

        # ss is the common side
        for ri in range(len(map_cat_rs)):
            for ss, nS, nX in [(0, nF, nE), (1, nE, nF)]:
                cats_loc = [None, None]
                kk = map_cat_rs[ri][ss].keys()
                for k in kk:
                    if len(map_cat_rs[ri][ss][k]) > 1:
                        bb = self.combCats(None, allw_neg, 1, True, nX, None, map_cat_rs[ri][ss][k], other_side=(ss == 1), other_neg=nS)
                        if bb is not None:
                            cats_loc = {ss: set(k) if type(k) is tuple else k, 1-ss: bb[-1][-1]}
                            if self.constraints.getCstr("debug_checks"):  # DEBUG
                                tF = colF.getLiteralCat(nF, cats_loc[0], allw_neg)
                                tE = colE.getLiteralCat(nE, cats_loc[1], allw_neg)
                                self.checkCountsPair(1, False, colF, colE, tF, tE, bb[1])
                            stt = self.insertBest(22, besti, bb[0], bb[1], (cats_loc[0], cats_loc[1]), 1, True, False, pre_multi=False)

                            # ADD TO map_cat of other side for further combination
                            if ri+1 < len(map_cat_rs):  # and stt == 0?
                                cat = tuple(sorted(bb[-1][-1]))
                                if cat not in map_cat_rs[ri+1][1-ss]:
                                    map_cat_rs[ri+1][1-ss][cat] = []
                                map_cat_rs[ri+1][1-ss][cat].append((bb[0], bb[1], k))

    def combCatsNum(self, besti, colF, colE, nF, nE, allw_neg, side, buckets, bUp):
        map_cat = {}
        # collect together all candidates that have the same numerical interval
        for b in besti:
            buk = b[-1][-1][1:]
            if buk not in map_cat:
                map_cat[buk] = []
            map_cat[buk].append((b[0], b[1], b[-1][-1][0]))
            # adv, clp, cat

        kk = map_cat.keys()
        for k in kk:
            if len(map_cat[k]) > 1:
                bb = self.combCats(None, allw_neg, side, True, nF, None, map_cat[k], other_side=True, other_neg=nE)
                if bb is not None:
                    if self.constraints.getCstr("debug_checks"):  # DEBUG
                        tE = colE.getLiteralBuk(nE, buckets[1], k, buckets[bUp])
                        tF = colF.getLiteralCat(nF, bb[-1][-1], allw_neg)
                        self.checkCountsPair(side, False, colF, colE, tF, tE, bb[1])
                    stt = self.insertBest(23, besti, bb[0], bb[1], (bb[-1][-1], )+k, 1, True, False, pre_multi=False)

    ##################################################
    # TOOLS METHODS
    @classmethod
    def fillClp(tcl, clp_ti, neg=False):  # ads lout and flips with lin if negated
        lparts, lin = clp_ti
        lout = [lparts[i] - lin[i] for i in range(len(lparts))]
        if neg:
            return (lparts, lin, lout)
        else:
            return (lparts, lout, lin)

    def inSuppBounds(self, side, op, lparts):
        if side == 1:
            (Eox, Exo, Exx, Eoo) = range(4)
        else:
            (Exo, Eox, Exx, Eoo) = range(4)
        if op:  # OR disjunction
            return (lparts[Exx] + lparts[Eox] >= self.constraints.getCstr("min_itm_in")) and \
                   (lparts[Eox] >= self.constraints.getCstr("min_itm_c")) and \
                   (lparts[Eoo] >= self.constraints.getCstr("min_itm_out"))
        else:  # AND conjunction
            return (lparts[Exx] >= self.constraints.getCstr("min_itm_in")) and \
                   (lparts[Exo] >= self.constraints.getCstr("min_itm_c")) and \
                   (lparts[Eoo] + lparts[Exo] >= self.constraints.getCstr("min_itm_out"))

    def clpToPieces(self, side, op, neg, lparts, lin, is_cond=False):
        if side == 1:
            (Eox, Exo, Exx, Eoo) = range(4)
        else:
            (Exo, Eox, Exx, Eoo) = range(4)

        if is_cond:  # Condition
            if neg:
                fix_num = 0
                var_num = lparts[Exx] - lin[Exx]
                fix_den = 0
                var_den = lparts[Exo] - lin[Exo]
                sout = -1
                cont = lparts[Exx] - lin[Exx]
            else:
                fix_num = 0
                var_num = lin[Exx]
                fix_den = 0
                var_den = lin[Exo]
                sout = -1
                cont = lin[Exx]
        elif op:  # OR disjunction
            if neg:
                fix_num = lparts[Exx]
                var_num = lparts[Eox] - lin[Eox]
                fix_den = lparts[Exx] + lparts[Exo] + lparts[Eox]
                var_den = lparts[Eoo] - lin[Eoo]
                sout = lin[Eoo]
                cont = lparts[Eox] - lin[Eox]
            else:
                fix_num = lparts[Exx]
                var_num = lin[Eox]
                fix_den = lparts[Exx]+lparts[Exo]+lparts[Eox]
                var_den = lin[Eoo]
                sout = lparts[Eoo] - lin[Eoo]  # lout[Eoo]
                cont = lin[Eox]
        else:  # AND conjunction
            if neg:
                fix_num = 0
                var_num = lparts[Exx] - lin[Exx]
                fix_den = lparts[Eox] + lparts[Exx]
                var_den = lparts[Exo] - lin[Exo]
                sout = lin[Exo] + lparts[Eoo]
                cont = lin[Exo]
            else:
                fix_num = 0
                var_num = lin[Exx]
                fix_den = lparts[Eox] + lparts[Exx]
                var_den = lin[Exo]
                sout = lparts[Exo] - lin[Exo] + lparts[Eoo]  # lout[Exo]+lparts[Eoo]
                cont = lparts[Exo] - lin[Exo]  # lout[Exo]
        return fix_num, var_num, fix_den, var_den, sout, cont

    def advRatioVar(self, side, op, lin_f, is_cond=False):
        if side == 1:
            (Eox, Exo, Exx, Eoo) = range(4)
        else:
            (Exo, Eox, Exx, Eoo) = range(4)

        if is_cond:
            num = lin_f[Exx]
            den = lin_f[Exo]
            return self.ratio(num, den+num)
        if op:  # OR disjunction
            num = lin_f[Eox]
            den = lin_f[Eoo]
        else:  # AND conjunction
            num = lin_f[Exx]
            den = lin_f[Exo]
        return self.ratio(num, den)

    def advAcc(self, side, op, neg, clp_ti, is_cond=False, filled=False):
        (fix_num, var_num, fix_den, var_den, sout, cont) = self.clpToPieces(side, op, neg, clp_ti[0], clp_ti[-1], is_cond)
        return self.offset_ratio(fix_num + var_num, fix_den + var_den)

    def getAC(self, side, op, neg, clp_ti, is_cond=False, no_const=False, filled=False):
        (fix_num, var_num, fix_den, var_den, sout, cont) = self.clpToPieces(side, op, neg, clp_ti[0], clp_ti[-1], is_cond)

        if is_cond:
            if self.unconstrained(no_const) or cont >= self.constraints.getCstr("min_itm_in"):
                acc = self.offset_ratio(var_num, var_den)
                clp = clp_ti if filled else self.fillClp(clp_ti, neg)
                return (acc, var_num, var_den, cont, fix_num, fix_den), clp, 0
            return None, None, self.FLG_IN | self.FLG_CONT

        cstr_status = 0
        if var_num+fix_num < self.constraints.getCstr("min_itm_in"):
            cstr_status |= self.FLG_IN
        if sout < self.constraints.getCstr("min_itm_out"):
            cstr_status |= self.FLG_OUT
        if cont < self.constraints.getCstr("min_itm_c"):
            cstr_status |= self.FLG_CONT
        # print(cstr_status, var_num+fix_num, sout, cont, clp_ti[0], clp_ti[-1])
        if self.unconstrained(no_const) or cstr_status == 0:
            acc = self.offset_ratio(var_num + fix_num, var_den + fix_den)
            clp = clp_ti if filled else self.fillClp(clp_ti, neg)
            return (acc, var_num, var_den, cont, fix_num, fix_den), clp, cstr_status
        return None, None, cstr_status

    def updateACT(self, best, lit, side, op, neg, clp_ti, is_cond=False):
        tmp_adv, tmp_clp, stt = self.getAC(side, op, neg, clp_ti, is_cond)
        if tmp_adv is None:
            return best, stt
        elif cmp_lower(best[0], tmp_adv):
            return (tmp_adv, tmp_clp, [side, op, neg, lit]), self.STG_OK
        else:
            return best, self.STG_CMP

    def updateACTList(self, typs, best, lit, side, op, neg, clp_ti, pre_multi=True):
        tmp_adv, tmp_clp, stt = self.getAC(side, op, neg, clp_ti)
        if tmp_adv is None:
            return stt
        return self.insertBest(typs, best, tmp_adv, tmp_clp, lit, side, op, neg, pre_multi)

    ##################################################
    # DOUBLE CHECKS FUNCTIONS

    def resultCheck(self, rv, msg):
        if not rv:
            print(msg)
            raise ExtensionWarning(msg)
        return rv

    def checkCountsSeg(self, counts, seg, col, lit, clp, comp=False):
        if seg[0] is None:
            cc = numpy.sum(counts[:seg[1]+1], axis=0)
        elif seg[1] is None:
            cc = numpy.sum(counts[seg[0]:], axis=0)
        else:
            cc = numpy.sum(counts[seg[0]:seg[1]+1], axis=0)
        new_sums = str(list(cc))
        if comp:
            org_c = clp[-2]
        else:
            org_c = clp[-1]
        org_sums = str(list(org_c))
        org_in = sum(clp[-1])
        if lit is None:
            if org_in > 0:  # can't guess whether it's negated or not...
                new_in = col.nbRows() - col.lMiss()
            else:
                new_in = 0
        else:
            new_in = len(col.suppLiteral(lit))

        msg = "--- checkCountsSeg %s" % lit
        msg += "\nsums %s %s%s" % (org_sums, new_sums, (org_sums != new_sums)*" !!!")
        msg += "\nin %s %s%s" % (org_in, new_in, (org_in != new_in)*" !!!")
        rv = (org_sums == new_sums) and (org_in == new_in)
        return self.resultCheck(rv, msg)

    def checkCountsPair(self, side, neg, colF, colE, tF, tE, clp):
        part_ids = self.constraints.getSSetts().getInitPartIds(side)
        org_ltot = str([clp[0][pid] for pid in part_ids])
        if neg:
            org_lin = str([clp[-2][pid] for pid in part_ids])
        else:
            org_lin = str([clp[-1][pid] for pid in part_ids])

        if tE is None:
            if sum(clp[-1][:3]) > 0:  # can't guess whether it's negated or not...
                suppE = colE.rows() - colE.miss()
            else:
                suppE = set()
        else:
            suppE = colE.suppLiteral(tE)
        if tF is None:
            if sum(clp[-1][:3]) > 0:  # can't guess whether it's negated or not...
                suppF = colF.rows() - colF.miss()
            else:
                suppF = set()
        else:
            suppF = colF.suppLiteral(tF)
        new_ltot = str([len(suppF), colF.N - len(suppF)])
        new_lin = str([len(suppE & suppF), len(suppE) - len(suppE & suppF)])

        rv = (org_ltot == new_ltot) and (org_lin == new_lin)
        msg = "--- checkCountsPair %s %s %s" % (side, tF, tE)
        msg += "\nltot %s %s%s" % (org_ltot, new_ltot, (org_ltot != new_ltot)*" !!!")
        msg += "\nlin %s %s%s" % (org_lin, new_lin, (org_lin != new_lin)*" !!!")
        return self.resultCheck(rv, msg)

    def checkCountsCond(self, colsC, cond_sparts, c):
        supp = self.getCCandSupp(colsC, c)
        lparts = cond_sparts.lparts()
        lin = cond_sparts.lpartsInterX(supp)
        new_ltot = str(lparts)
        new_lin = str(lin)

        clp = c.getClp()
        org_ltot = str([cc for cc in clp[0]])
        org_lin = str([cc for cc in clp[-1]])

        rv = (org_ltot == new_ltot) and (org_lin == new_lin)
        msg = "--- checkCountsCond %s" % " and ".join([str(l) for l in c.getLit()])
        msg += "\nltot %s %s%s" % (org_ltot, new_ltot, (org_ltot != new_ltot)*" !!!")
        msg += "\nlin %s %s%s" % (org_lin, new_lin, (org_lin != new_lin)*" !!!")
        return self.resultCheck(rv, msg)

    def checkCountsExt(self, supports, col, c):
        supp = col.suppLiteral(c.getLit())
        lparts = supports.lparts()
        lin = supports.lpartsInterX(supp)
        lout = [lparts[i]-lin[i] for i in range(len(lparts))]

        org_clp = str([list(c.getClp()[0]), list(c.getClp()[-1])])
        new_clp = str([lparts, lin])

        rv = org_clp == new_clp
        msg = "--- checkCountsExt %s" % c.disp(self.store.ssetts, self.store.N,
                                               self.store.c_vals["base_acc"], self.store.c_vals["prs"], self.store.constraints["score_coeffs"])
        msg += "\n<<< clp: %s" % org_clp
        msg += "\n>>> clp: %s" % new_clp
        return self.resultCheck(rv, msg)

    def checkRedExt(self, data, c):
        if data is not None:
            red = self.store.mkRedFromCand(c, data)
            chk = c.checkRed(red)
            rv = chk is None
            msg = "--- checkRedExt %s" % self.store.dispCand(c)
            msg += "\n%s" % red
            msg += "\n%s" % chk
            return self.resultCheck(rv, msg)
