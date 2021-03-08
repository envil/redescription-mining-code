import re
import os.path

try:
    from classProps import WithProps
    from classQuery import Op, Literal, Query
    from classRedescription import Redescription
except ModuleNotFoundError:
    from .classProps import WithProps
    from .classQuery import Op, Literal, Query
    from .classRedescription import Redescription

import pdb

LIT_SEP = " AND "


class ExtensionWarning(Warning):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)


def clpToStr(clp, preff="", suff=""):  # return empty string to skip
    if clp is not None:
        return preff+str([list(clp[i]) for i in [0, -1]])+suff
        # return preff+str([list(c) for c in clp])+suff
    # return ""


def clpToRepr(clp):
    if clp is not None:
        return str([list(c) for c in clp])


#######################################
# SORTING METHODS FOR INITIAL PAIRS
DEF_SCORE = float("-inf")
# drop_set is assumed to be a subset of all_keys,
# so "drop_set.symmetric_difference(all_keys)" is in effect the same as set(all_keys).difference(drop_set)


def fifo_sort(all_keys, store, drop_set=set(), sort_criterion="score", default=DEF_SCORE):
    return sorted(drop_set.symmetric_difference(all_keys), reverse=True)


def filo_sort(all_keys, store, drop_set=set(), sort_criterion="score", default=DEF_SCORE):
    return sorted(drop_set.symmetric_difference(all_keys))


def overall_sort(all_keys, store, drop_set=set(), sort_criterion="score", default=DEF_SCORE):
    return sorted(drop_set.symmetric_difference(all_keys), key=lambda x: store[x].getPropD(sort_criterion, default))


def alternate_sort(all_keys, store, drop_set=set(), sort_criterion="score", default=DEF_SCORE):
    best_sides = [{}, {}]
    loc_data = {}
    for k in all_keys:
        loc_data[k] = {"tail_brk": store[k].getPropD(sort_criterion, default=default)}
        for side in [0, 1]:
            col = store[k].getCid(side)
            if col is not None and col >= 0:
                if col in best_sides[side]:
                    best_sides[side][col].append(k)
                else:
                    best_sides[side][col] = [k]

    for side in [0, 1]:
        for col in best_sides[side]:
            best_sides[side][col].sort(key=lambda x: store[x].getPropD(sort_criterion, default=default), reverse=True)
        for c, vs in best_sides[side].items():
            for pp, v in enumerate(vs):
                loc_data[v]["rank_%d" % side] = pp
    sort_dt = sorted([(loc_data[k].get("tail_brk", -1) - max(loc_data[k].get("rank_0", -1), loc_data[k].get("rank_1", -1)), k)
                      for k in drop_set.symmetric_difference(all_keys)])
    return [k[-1] for k in sort_dt]


SORT_METHODS = {"overall": overall_sort,
                "alternate": alternate_sort,
                "fifo": fifo_sort,
                "filo": filo_sort}
DEFAULT_METHOD = overall_sort


###############################################
# Generic Candidate class and Stores where to keep them

class Candidate(WithProps):

    def getLits(self):
        if self.getSide() == 1:
            return (None, self.lit)
        return (self.lit, None)

    def getLit(self, side=None):
        if side is None or side == self.getSide():
            return self.lit

    def dispLit(self, side=None):
        lit = self.getLit(side)
        if lit is None:
            return "-"
        elif type(lit) is list:
            return LIT_SEP.join(["%s" % ll for ll in lit])
        return "%s" % lit

    def getCid(self, side=None):
        lit = self.getLit(side)
        if isinstance(lit, Literal):
            return lit.colId()

    def getAcc(self):
        return -1

    def isNeg(self, side=None):
        lit = self.getLit(side)
        if isinstance(lit, Literal):
            return self.getLit().isNeg()
        return False

    # condition

    def getCondition(self):
        return None

    def hasCondition(self):
        return self.getCondition() is not None

    def getCidC(self):
        if self.hasCondition():
            return self.getCondition().getCid()

    def getLitC(self):
        if self.hasCondition():
            return self.getCondition().getLit()

    def dispLitC(self):
        if self.hasCondition():
            return self.getCondition().dispLit()

    def getAccC(self):
        if self.hasCondition():
            return self.getCondition().getAcc()
        return self.getAcc()

    def mkRed(self, data, red=None):
        return Redescription.fromInitialPair(self.getLits(), data, self.getLitC())

    def checkRed(self, red, thres=0.0001):
        acc_KO = (red.getAcc() - self.getAcc())**2 > thres
        accC_KO = red.hasCondition() and (red.getAcc("cond") - self.getAccC())**2 > thres
        if acc_KO or accC_KO:
            msg = "acc     %s %s %s" % (red.getAcc(), self.getAcc(), acc_KO*"!!!")
            if red.hasCondition():
                msg += "acc cond %s %s %s" % (red.getAcc("cond"), self.getAccC(), accC_KO*"!!!")
            return msg

    # comparisons
    def toKey(self):
        return None

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.toKey() == other.toKey()

    def __ne__(self, other):
        return not isinstance(other, self.__class__) or self.toKey() != other.toKey()

    def __lt__(self, other):
        return isinstance(other, self.__class__) and self.toKey() < other.toKey()

    def __le__(self, other):
        return isinstance(other, self.__class__) and self.toKey() <= other.toKey()

    def __gt__(self, other):
        return not isinstance(other, self.__class__) or self.toKey() > other.toKey()

    def __ge__(self, other):
        return not isinstance(other, self.__class__) or self.toKey() >= other.toKey()

    def getScore(self, prop=None, default=None):
        return self.getPropD(prop, default)


class DictStore(dict):

    def __init__(self, d={}, track_changes=True):
        dict.__init__(self, d)
        self.change_keys = set(self.keys())
        self.track_changes = track_changes

    def clear(self):
        dict.clear(self)
        self.change_keys = set()

    def setTracking(self, track_changes=False):
        self.track_changes = track_changes

    def ready_items(self):
        if self.track_changes:
            return [(k, v) for (k, v) in self.items() if k not in self.change_keys]
        return self.items()

    def ready_keys(self):
        if self.track_changes:
            return [k for k in self.keys() if k not in self.change_keys]
        return self.keys()

    def __setitem__(self, key, value):
        try:
            dict.__setitem__(self, key, value)
        except:
            raise
        else:
            self.change_keys.add(key)

    def __delitem__(self, key):
        try:
            dict.__delitem__(self, key)
        except:
            raise
        else:
            self.change_keys.discard(key)

    def toNextRound(self):
        self.change_keys = set()

    def currentRoundKeys(self):
        return self.change_keys

    def currentRoundIter(self):
        for k in self.change_keys:
            yield self[k]

    def nextPos(self, cand):
        return None

    def betterCand(self, pos, cand):
        return True

    def add(self, cand):
        pos = self.nextPos(cand)
        if pos is not None and self.betterCand(pos, cand):
            self[pos] = cand
            return pos


class ListStore(DictStore):
    # this is actually a dictionary with incremental keys

    def __init__(self, d=[]):
        DictStore.__init__(self, enumerate(d))
        self.next_pos = len(self)

    def nextPos(self, cand):
        return self.next_pos

    def add(self, cand):
        pos = self.nextPos(cand)
        if pos is not None:
            self[pos] = cand
            self.next_pos += 1
            return pos


class XStore(object):

    # operates on a candidate store that provides items method
    # only store the necessary constraints
    def __init__(self, N=0, ssetts=None, constraints=None, current=None):
        self.N = N
        self.ssetts = ssetts
        self.constraints = {}
        self.c_vals = {}

    def emptyCopy(self):
        return self.__class__(self.N, self.ssetts, self.constraints, self.c_vals)

    # def __repr__(self):
    #     return f"{self.__class__.__name__}({self.N}, {self.ssetts}, {self.constraints}, {self.c_vals})"

    # def nextPos(self, cand):
    # def betterCand(self, pos, cand):
    # def addPair(self, score, litL, litR, negL=False, negR=False):
    # def addExt(self, nego, adv_parts, clp, lit_parts):


###############################################
# Storage of extensions candidates

class ExtCand(Candidate):

    what = "Extension"

    def __init__(self, adv_parts, clp, lit_parts, condition=None):
        # adv_parts is a tuple: acc, var_num, var_den, contri, fix_num, fix_den
        # clp is a triple [lparts,[ lmiss,] lout, lin], where each is a list of counts in support sets
        self.condition = condition
        self.adv = adv_parts
        self.clp = clp
        # self.setClp(clp)
        # side, op, tmp_neg, lit = lit_parts
        self.setLit(lit_parts[-1], lit_parts[0])
        if len(lit_parts) == 4:
            self.op = lit_parts[1]
            self.through_neg = lit_parts[2]
        else:
            self.op = False
            self.through_neg = False

    def toKey(self):
        return tuple(self.adv)+(self.side, self.op)+self.lit.toKey()

    def setLit(self, lit, side=0):
        self.lit = lit
        self.side = side

    def getOp(self):
        return self.op

    def getSide(self):
        return self.side

    def getAcc(self):
        return self.adv[0]

    def getVarBlue(self):
        return self.adv[1]

    def getVarRed(self):
        return self.adv[2]

    def getClp(self):
        return self.clp

    def setCondition(self, condition):
        self.condition = condition

    def getCondition(self):
        return self.condition

    def __repr__(self):
        lit = repr(self.getLit())
        clp = clpToRepr(self.clp)
        condition = ""
        if self.hasCondition():
            condition = ", condition=" + repr(self.getCondition())
        return f"{self.__class__.__name__}({self.adv}, {clp}, ({self.side}, {self.op}, {self.through_neg}, {lit}){condition})"

    def __str__(self):
        if self.getSide() == -1:
            lit = self.dispLit()
        else:
            lit = "(%d, %s, %s)" % (self.getSide(), Op(self.getOp()), self.dispLit())
        if any([c != -1 for c in self.adv[1:]]):
            adv = str(self.adv)
        else:
            adv = "%f" % self.adv[0]
        clp = clpToStr(self.clp, preff="\t")
        tmp = ("%s: %s -> %s%s" %
               (self.what, lit, adv, clp))
        if self.hasCondition():
            tmp += "\n\t"+str(self.getCondition())
        return tmp

    def disp(self, ssetts=None, N=0, base_acc=None, prs=None, coeffs=None):
        strPieces = ["", "", "", ""]
        score_of = self
        strPieces[self.getSide()] = "%s %s" % (Op(self.getOp()), self.dispLit())
        if self.hasCondition():
            # score_of = self.getCondition()
            strPieces[2] = self.getCondition().dispLit()

        if base_acc is None or ssetts is None:
            strPieces[-1] = "----\t%1.7f\t----\t----\t% 5i\t% 5i" \
                % (score_of.getAcc(), score_of.getVarBlue(), score_of.getVarRed())
        else:
            strPieces[-1] = "\t\t%+1.7f \t%1.7f \t%1.7f \t%1.7f\t% 5i\t% 5i" \
                % (score_of.getScore(ssetts, N, base_acc, prs, coeffs), score_of.getAcc(),
                   score_of.pValQuery(ssetts, N, prs), score_of.pValRed(ssetts, N, prs), score_of.getVarBlue(), score_of.getVarRed())
        return "* %20s <==> * %20s %20s %s" % tuple(strPieces)

    def getScore(self, ssetts, N, base_acc, prs, coeffs):
        # HERE: HOW TO SCORE WITH CONDITION?
        sc = coeffs["impacc"]*self.impacc(base_acc) \
            + coeffs["rel_impacc"]*self.relImpacc(base_acc) \
            + self.pValRedScore(ssetts, N, prs, coeffs) \
            + self.pValQueryScore(ssetts, N, prs, coeffs)
        if False:  # self.hasCondition():
            sc += self.getCondition().getScore(ssetts, N, base_acc, prs, coeffs)
        return sc

    def relImpacc(self, base_acc=0):
        if base_acc != 0:
            return (self.adv[0] - base_acc)/base_acc
        else:
            return self.adv[0]

    def impacc(self, base_acc=0):
        return (self.adv[0] - base_acc)

    def mkRed(self, data, red=None):
        if red is not None:
            supp = data.supp(self.getSide(), self.getLit())
            miss = data.miss(self.getSide(), self.getLit())
            red_ext = red.mkRed(data, self.getSide(), self.getOp(), self.getLit(), supp, miss)
            if self.hasCondition():
                litC = self.getLitC()
                if type(litC) is list:
                    # if len(litC) > 1: pdb.set_trace()
                    qC = Query(OR=False, buk=litC)
                else:
                    qC = Query(buk=[litC])
                supp_cond, miss_cond = qC.recompute(-1, data)
                red_ext.setCondition(qC, supp_cond)
            return red_ext

    def pValQueryScore(self, ssetts, N, prs, coeffs=None):
        if coeffs is None or coeffs["pval_query"] < 0:
            return coeffs["pval_query"] * self.pValQuery(ssetts, N, prs)
        elif coeffs["pval_query"] > 0:
            return -coeffs["pval_fact"]*(coeffs["pval_query"] < self.pValQuery(ssetts, N, prs))
        else:
            return 0

    def pValRedScore(self, ssetts, N, prs, coeffs=None):
        if coeffs is None or coeffs["pval_red"] < 0:
            return coeffs["pval_red"] * self.pValRed(ssetts, N, prs)
        elif coeffs["pval_red"] > 0:
            return -coeffs["pval_fact"]*(coeffs["pval_red"] < self.pValRed(ssetts, N, prs))
        else:
            return 0

    def pValQuery(self, ssetts, N=0, prs=None):
        return ssetts.pValQueryCand(self.side, self.op, self.isNeg(), self.clp, N, prs)

    def pValRed(self, ssetts, N=0, prs=None):
        return ssetts.pValRedCand(self.side, self.op, self.isNeg(), self.clp, N, prs)


class CondCand(ExtCand):
    what = "Condition"

    def setLit(self, lit, side=-1):
        self.lit = lit
        self.side = -1


class ExtsStore(object):

    def __init__(self, N=0, ssetts=None, constraints=None, current=None):
        XStore.__init__(self, N, ssetts, constraints, current)

        self.setCurrent(current)

        if type(constraints) is dict:
            self.constraints["score_coeffs"] = constraints.get("score_coeffs")
            self.constraints["min_impr"] = constraints.get("min_impr")
            self.constraints["max_var"] = tuple(constraints.get("max_var"))
        elif constraints is not None:
            self.constraints["score_coeffs"] = constraints.getCstr("score_coeffs")
            self.constraints["min_impr"] = constraints.getCstr("min_impr")
            self.constraints["max_var"] = (constraints.getCstr("max_var", side=0), constraints.getCstr("max_var", side=1))
        else:
            self.constraints["score_coeffs"] = None
            self.constraints["min_impr"] = 0
            self.constraints["max_var"] = (-1, -1)

    def setCurrent(self, current=None):
        if type(current) is dict:
            self.current = None
            self.c_vals = dict(current)
        elif current is not None:
            self.current = current
            self.c_vals = {"base_acc": self.current.getAcc(),
                           "prs": self.current.probas()}
        else:
            self.current = None
            self.c_vals = {"base_acc": 0, "prs": None}

    def emptyCopy(self):
        return self.__class__(self.N, self.ssetts, self.constraints, self.current)

    def __str__(self):
        # (min_impr=%f, max_var=%d:%d)\n" % (self.constraints["min_impr"], self.constraints["max_var"][0], self.constraints["max_var"][1])
        dsp = "ExtsStore:\n"
        dsp += "Redescription: %s" % self.current
        dsp += "\n\t  %20s        %20s        %20s" \
            % ("LHS extension", "RHS extension", "Condition")

        dsp += "\t\t%10s \t%9s \t%9s \t%9s\t% 5s\t% 5s" \
            % ("score", "Accuracy", "Query pV", "Red pV", "toBlue", "toRed")

        for k, cand in self.items():  # Do not print the last: current redescription
            dsp += "\n\t%s" % self.dispCand(cand)
        return dsp

    def dispCand(self, cand):
        if isinstance(cand, ExtCand):
            return cand.disp(self.ssetts, self.N,
                             self.c_vals["base_acc"], self.c_vals["prs"], self.constraints["score_coeffs"])

    def scoreCand(self, cand):
        if isinstance(cand, ExtCand):
            return cand.getScore(self.ssetts, self.N, self.c_vals["base_acc"], self.c_vals["prs"], self.constraints["score_coeffs"])

    def improving(self):
        return dict([(pos, cand) for (pos, cand) in self.items() if self.scoreCand(cand) >= self.constraints["min_impr"]])

    def mkRedFromCand(self, cand, data):
        red = cand.mkRed(data, self.current)
        red.setFull(self.constraints["max_var"])
        return red

    def improvingReds(self, data):
        reds = []
        for (pos, cand) in self.items():
            if self.scoreCand(cand) >= self.constraints["min_impr"]:
                reds.append(self.mkRedFromCand(cand, data))
        return reds


class ExtsBatch(DictStore, ExtsStore):

    def __init__(self, N=0, ssetts=None, constraints=None, current=None):
        ExtsStore.__init__(self, N, ssetts, constraints, current)
        DictStore.__init__(self)

    def nextPos(self, cand):
        if isinstance(cand, ExtCand):
            return (cand.getSide(), cand.getOp())

    def betterCand(self, pos, cand):
        return isinstance(cand, ExtCand) and (pos not in self or cand > self[pos])
        # self.scoreCand(cand) > self.scoreCand(self[pos]))

    def addPair(self, score, litL, litR, negL=False, negR=False):
        # print("--- ExtsBatch addPair", score, litL, litR)
        # does not store pairs
        pass

    def addExt(self, nego, adv_parts, clp, lit_parts):
        cand = ExtCand(adv_parts, clp, lit_parts)
        return self.add(cand)

    def clear(self, current=None):
        DictStore.clear(self)
        ExtsStore.setCurrent(self, current)

###############################################
# Storage of initial candidates


class InitsStore(XStore):

    @classmethod
    def getStoredClass(tcl):
        return Candidate

    @classmethod
    def getStoredClassName(tcl):
        return tcl.getStoredClass().__name__

    @classmethod
    def getCmpCriterion(tcl):
        return "score"

    @classmethod
    def getCmpDefault(tcl):
        return DEF_SCORE

    def __init__(self, N=0, ssetts=None, constraints=None, current=None):
        XStore.__init__(self, N, ssetts, constraints, current)

        if type(current) is dict:
            if current.get("avC") is not None:
                self.c_vals = {"avC": [list(current["avC"][side]) if current["avC"][side] is not None else None for side in [0, 1]]}
            else:
                self.c_vals = None
        elif current is not None:
            self.c_vals = {"avC": [current.lAvailableCols[side] for side in [0, 1]]}
        else:
            self.c_vals = None

        if type(constraints) is dict:
            self.constraints["init_minscore"] = constraints.get("init_minscore")
        elif constraints is not None:
            self.constraints["init_minscore"] = constraints.getCstr("init_minscore")
        else:
            self.constraints["init_minscore"] = 0

    def __str__(self):
        dsp = "%s: (%f)\n" % (self.__class__.__name__, self.constraints["init_minscore"])
        return "\n".join([dsp, self.getStoredClass().dispHeader()]+[self.dispCand(cand) for k, cand in self.items()])

    def dispCand(self, cand):
        return cand.disp(prop=self.getCmpCriterion(), default=self.getCmpDefault())

    def scoreCand(self, cand):
        if isinstance(cand, self.getStoredClass()):
            return cand.getScore(self.getCmpCriterion(), default=self.getCmpDefault())

    def mkRedFromCand(self, cand, data):
        return cand.mkRed(data)

    def improving(self):
        return dict([(pos, cand) for (pos, cand) in self.items() if self.scoreCand(cand) >= self.constraints["init_minscore"]])

    def improvingReds(self, data):
        reds = []
        for (pos, cand) in self.items():
            if self.scoreCand(cand) >= self.constraints["init_minscore"]:
                red = self.mkRedFromCand(cand, data)
                if self.c_vals is not None:
                    for side in [0, 1]:
                        red.restrictAvailable(side, self.c_vals["avC"][side])
                reds.append(red)
        return reds


class TermCand(Candidate):

    what = "Term"
    info_what = {"side": "self.getSide()", "lit": "self.getLit()", "cid": "self.getCid()",
                 "supp_len": "self.getSuppLen()", "supp_ratio": "self.getSuppRatio()"}

    def __init__(self, side, lit, supp_len=-1, N=0):
        self.setLit(lit, side)
        self.supp_len = supp_len
        self.N = N

    def setLit(self, lit, side=0):
        self.lit = lit
        self.side = side
        # if isinstance(self.lit, Lit) and self.cid != self.lit.colId():
        #     self.cid = self.lit.colId()

    def getSide(self):
        return self.side

    def getAcc(self):
        return 0

    def getSuppLen(self):
        return self.supp_len

    def getSuppRatio(self):
        if self.N == 0:
            return self.supp_len
        else:
            return self.supp_len/self.N

    def makeTrg(self, data, tcols=None):
        supp = numpy.zeros(data.nbRows(), dtype=bool)
        supp[list(data.col(self.getSide(), self.getCid()).suppLiteral(self.getLit()))] = 1
        if tcols is not None:
            involved = [tcols[self.getSide()].get(data.getMatLitK(self.getSide(), self.getLit(), bincats=True))]
        else:
            involved = []
        return {"side": self.getSide(), "target": supp, "involved": involved, "src": self.getLit()}

    @classmethod
    def dispHeader(tcl, sep="\t"):
        return (sep.join(["%10s", "%s", "%s"])) % ("score", "side",  "lit")

    def disp(self, sep="\t", prop="score", default=None):
        return sep.join(["%10s", "%s", "%s"]) % (self.getScore(prop, default), self.getSide(), self.getLit())

    def __repr__(self):
        lit = repr(self.getLit())
        return f"{self.__class__.__name__}({self.side}, {lit}, {self.supp_len}, {self.N})"

    def __str__(self):
        if self.getSide() == 1:
            return "%s: (---, %s) -> %s" % (self.what, self.getLit(), self.getSuppLen())
        else:
            return "%s: (%s, ---) -> %s" % (self.what, self.getLit(), self.getSuppLen())


class PairCand(Candidate):

    what = "Pair"
    info_what = {"litL": "self.getLit(0)", "litR": "self.getLit(1)", "cidL": "self.getCid(0)", "cidR": "self.getCid(1)",
                 "acc": "self.getAcc()"}

    def __init__(self, adv, clp, litL, litR, negL=False, negR=False, swap=False, condition=None):
        self.swapped = swap
        if swap:
            self.lits = [litR, litL]
            self.thrg_neg = [negR, negL]
        else:
            self.lits = [litL, litR]
            self.thrg_neg = [negL, negR]
        if type(adv) is float:
            self.acc = adv
        else:
            self.acc = adv[0]
        self.clp = clp
        self.condition = condition

    def getAcc(self):
        return self.acc

    def setLit(self, lit, side=0):
        self.lits[side] = lit

    def getLits(self):
        return self.lits

    def getLit(self, side=0):
        return self.lits[side]

    def setCondition(self, condition):
        self.condition = condition

    def getCondition(self):
        return self.condition

    # def swapSides(self):
    #     self.lits = [self.lits[1], self.lits[0]]
    #     self.thrg_neg = [self.thrg_neg[1], self.thrg_neg[0]]

    def setLitTerm(self, term, side=0):
        if type(self.lits[side]) is bool:
            self.setLit(Literal(self.lits[side], term), side)
        else:
            self.setLit(Literal(False, term), side)

    def doublyNegatedLit(self, side):
        return isinstance(self.lits[side], Literal) and self.lits[side].isNeg() != self.thrg_neg[side]

    @classmethod
    def dispHeader(tcl, sep="\t"):
        return (sep.join(["%10s", "%s", "%s"])) % ("score", "litLHS",  "litRHS")

    def disp(self, sep="\t", prop=None, default=None):
        return sep.join(["%10s", "%s", "%s"]) % (self.getScore(prop, default), self.getLit(0), self.getLit(1))

    def __repr__(self):
        litL = repr(self.getLit(0))
        litR = repr(self.getLit(1))
        clp = clpToRepr(self.clp)
        condition = ""
        if self.hasCondition():
            condition = ", condition="+repr(self.getCondition())
        return f"{self.__class__.__name__}({self.acc}, {clp}, {litL}, {litR}, {self.thrg_neg[0]}, {self.thrg_neg[1]}{condition})"

    def __str__(self):
        condition = ""
        if self.hasCondition():
            condition = "\t+ " + str(self.getCondition())
        clp = clpToStr(self.clp, preff="\t")
        return "%s: (%s, %s) -> %s%s%s" % (self.what, self.getLit(0), self.getLit(1), self.getAcc(), clp, condition)

    @classmethod
    def pattCand(tcl):
        ip_patt = tcl.what+":\s+\((?P<litL>.*), (?P<litR>.*)\)\s+->\s+(?P<acc>\d\.\d+)"
        cond_patt = "\t\+ Condition:\s+(?P<litC>.*)\s+->\s+(?P<accC>[\(\)0-9\., ]+)"
        return ip_patt+"(\t(?P<clp>[\[\]0-9, ]*))?"+"(?P<cond>"+cond_patt+"(\t(?P<clpC>[\[\]0-9, ]*))?)?"


class PairsBatch(ListStore, InitsStore):

    @classmethod
    def getStoredClass(tcl):
        return PairCand

    @classmethod
    def getCmpCriterion(tcl):
        return "acc"

    @classmethod
    def getCmpDefault(tcl):
        return -1

    def __init__(self, N=0, ssetts=None, constraints=None, current=None):
        InitsStore.__init__(self, N, ssetts, constraints, current)
        ListStore.__init__(self)

    def addPair(self, adv, clp, litL, litR, negL=False, negR=False, side=1):
        # print("--- PairssBatch addPair", score, litL, litR)
        cand = PairCand(adv, clp, litL, litR, negL, negR, swap=(side == 0))
        self.add(cand)

    def addExt(self, nego, adv_parts, clp, lit_parts):
        # only one literal provided, and indication whether the other is negated (nego), will be filled in later, and flipped around if needed
        # print("--- PairsBatch addExt", nego, adv_parts, clp, lit_parts)
        cand = PairCand(adv_parts, clp, nego, lit_parts[-1], nego, lit_parts[2], swap=(lit_parts[0] == 0))
        self.add(cand)
        # self.addPair(adv_parts[0], nego, lit_parts[-1])

    def removeNegDuplicates(self):
        dneg, oth, drop = ([], [], [])
        for ck in self.currentRoundKeys():
            if self[ck].doublyNegatedLit(0) or self[ck].doublyNegatedLit(1):
                dneg.append(ck)
            else:
                oth.append(ck)
        for ck in dneg:
            i = 0
            while i < len(oth):
                if self[oth[i]].getLit(0) == self[ck].getLit(0) and \
                   self[oth[i]].getLit(1) == self[ck].getLit(1):
                    drop.append(self[ck])
                    del self[ck]
                    i = len(oth)
                i += 1
        # if len(drop) > 0:
        #     print("DROP", drop)
        return drop


class InitialCands(object):
    # to use, must implement getStoredClass and getCmpCriterion class methods

    def __init__(self, sort_meth="overall", max_out=-1):
        self.max_out = max_out
        if sort_meth in SORT_METHODS:
            self.sort_meth_name = sort_meth
            self.sort_meth = SORT_METHODS[sort_meth]
        else:
            self.sort_meth_name = "default"
            self.sort_meth = DEFAULT_METHOD
        self.list_out = []
        self.drop_set = set()
        self.sorted_ids = None

    def msgLoaded(self):
        return "Loaded %d %s, will try at most %d (ordered by %s, %s)" % \
            (len(self), self.getStoredClassName(), self.getMaxOut(), self.getCmpCriterion(), self.sort_meth_name)

    def msgFound(self):
        already = ""
        if self.getNbOut() > 0:
            already = " tried %d before testing all," % self.getNbOut()
        return "Found %d %s,%s will try at most %d (ordered by %s, %s)" % \
            (len(self), self.getStoredClassName(), already, self.getMaxOut(), self.getCmpCriterion(), self.sort_meth_name)

    @classmethod
    def pattFound(tcl):
        return "Found \d+ %s," % tcl.getStoredClassName()

    def clear(self):
        self.list_out = []
        self.drop_set = set()
        self.sorted_ids = None

    def setMaxOut(self, n):
        self.max_out = n

    def getNbOut(self):
        return len(self.list_out)

    def getMaxOut(self):
        return self.max_out

    def getRemainOut(self):
        if self.max_out == -1:
            return self.max_out
        else:
            return self.max_out - self.getNbOut()

    def exhausted(self):
        return (self.max_out > -1) and (self.getNbOut() >= self.max_out)

    # Adding and retrieving candidates
    def _sort(self):
        if self.sorted_ids is None:
            self.sorted_ids = self.sort_meth(self.ready_keys(), self, self.drop_set, self.getCmpCriterion(), default=self.getCmpDefault())

    # cond allows to provide a method that must evaluate to True on the candidate, else it is skipped
    def getNext(self, cond=None):
        if len(self) > 0 and not self.exhausted():
            self._sort()
            if len(self.sorted_ids) > 0:
                nid = self.sorted_ids.pop()
                self.drop_set.add(nid)
                if cond is not None:
                    while not cond(self[nid]) and len(self.sorted_ids) > 0:
                        nid = self.sorted_ids.pop()
                        self.drop_set.add(nid)
                    # exhausted candidates, no good one
                    if not cond(self[nid]) and len(self.sorted_ids) == 0:
                        return None
                self.list_out.append(nid)
                return self[nid]
        return None

    # cond allows to provide a method that must evaluate to True on the candidate, else it is skipped
    def getNextRed(self, data, cond=None):
        cand = self.getNext(cond)
        if cand is not None:
            return self.mkRedFromCand(cand, data)

    def getAll(self, data, thres_what=None, thres_min=None, cond=None):
        if thres_what is None:
            thres_what = self.getCmpCriterion()
        reds = []
        scs = []
        for nid, cand in self.ready_items():
            if (thres_min is None or cand.getPropD(thres_what) >= thres_min) and (cond is None or cond(cand)):
                reds.append(self.mkRedFromCand(cand, data))
                scs.append(cand.getPropD(thres_what))
        return reds, scs

    def getAllCands(self, data, thres_what=None, thres_min=None, cond=None):
        if thres_what is None:
            thres_what = self.getCmpCriterion()
        cands = []
        scs = []
        for nid, cand in self.ready_items():
            if (thres_min is None or cand.getPropD(thres_what) >= thres_min) and (cond is None or cond(cand)):
                cands.append(cand)
                scs.append(cand.getPropD(thres_what))
        return cands, scs

    def getLatestCand(self):
        return self[self.list_out[-1]]


class InitialTerms(ListStore, InitsStore, InitialCands):
    @classmethod
    def getStoredClass(tcl):
        return TermCand

    @classmethod
    def getCmpCriterion(tcl):
        return "supp_ratio"

    @classmethod
    def getCmpDefault(tcl):
        return -1

    def __init__(self, N=0, ssetts=None, constraints=None, current=None, sort_meth="overall", max_out=-1):
        InitsStore.__init__(self, N, ssetts, constraints, current)
        ListStore.__init__(self)
        InitialCands.__init__(self, sort_meth, max_out)

    def clear(self, current=None):  # current parameter for same function interface
        ListStore.clear(self)
        InitialCands.clear(self)

    def add(self, cand):
        if isinstance(cand, self.getStoredClass()):
            nid = ListStore.add(self, cand)
            if nid is not None:
                self.sorted_ids = None
                return nid

    def setExploredDone(self):
        self.setTracking(False)


#######################################
# PairsBatch with tracking of what goes in and out, saving and explore list for parallel computation
class InitialPairs(InitialCands, PairsBatch):

    def __init__(self, N=0, ssetts=None, constraints=None, current=None, sort_meth="overall", max_out=-1, save_filename=None):
        PairsBatch.__init__(self, N, ssetts, constraints, current)
        InitialCands.__init__(self, sort_meth, max_out)
        self.setExploreList()
        self.setSaveFilename(save_filename)

    # Adding and retrieving candidates
    def clear(self, current=None):  # current parameter for same function interface
        PairsBatch.clear(self)
        InitialCands.clear(self)
        self.setExploreList()
        self.saved = False

    def add(self, cand):
        if isinstance(cand, self.getStoredClass()):
            nid = PairsBatch.add(self, cand)
            if nid is not None:
                self.sorted_ids = None
                self.saved = False
                return nid

    # For saving to/loading from file
    ########################################################
    def setSaveFilename(self, save_filename):
        self.save_filename = None
        self.saved = True
        if type(save_filename) is str and len(save_filename) > 0:
            self.save_filename = save_filename
            self.saved = False

    def getSaveFilename(self):
        return self.save_filename

    def saveToFile(self):  # TODO: also save condition
        if self.save_filename is not None and not self.saved:
            try:
                with open(self.save_filename, "w") as f:
                    f.write("\n".join([repr(k) + "\t" + repr(v) for k, v in self.items()])+"\n")
                    done = self.getExploredDone()
                    if done is None:
                        self.saved = True
                    else:
                        f.write("DONE: "+" ".join(["%d-%d" % d for d in done])+"\n")
                return True
            except IOError:
                pass
        return False

    def loadFromFile(self, data=None):
        loaded = False
        done = set()
        if self.save_filename is not None and os.path.isfile(self.save_filename):
            with open(self.save_filename) as f:
                loaded, done = self.loadFromLogFile(f, data)
            if not loaded:
                with open(self.save_filename) as f:
                    loaded, done = self.loadFromStoreFile(f, data)
            if done is None:
                self.setTracking(False)
        return loaded, done

    def loadFromStoreFile(self, f, data=None):
        done = None
        for line in f:
            if re.match("DONE:", line):
                done = set([tuple(map(int, d.split("-"))) for d in line.strip().split(" ")[1:]])
            else:
                parts = line.strip().split("\t")
                if len(parts) == 2:
                    cand = eval(parts[1])
                    if data is None or (data.col(0, cand.getCid(0)).isEnabled() and data.col(1, cand.getCid(1)).isEnabled()):
                        self.add(cand)
        return True, done

    def loadFromLogFile(self, f, data=None):
        log_patt = "\[\[log@[0-9]+\s+\]\]\s+"
        cand_patt = log_patt+self.getStoredClass().pattCand()
        end_patt = log_patt+self.pattFound()

        done = set()
        for line in f:
            if re.match(end_patt, line):
                return len(done) > 0, None
            tmp = re.match(cand_patt, line)
            if tmp is not None:
                condition = None
                if tmp.group("cond") is not None:
                    if tmp.group("clpC") is not None:
                        clpC = eval(tmp.group("clpC"))
                    else:
                        clpC = None
                    condition = CondCand(eval(tmp.group("accC")), clpC, [Literal(l) for l in tmp.group("litC").split(LIT_SEP)])
                if tmp.group("clp") is not None:
                    clp = eval(tmp.group("clp"))
                else:
                    clp = None
                cand = PairCand(eval(tmp.group("acc")), clp, Literal(tmp.group("litL")), Literal(tmp.group("litR")), condition=condition)
                done.add((cand.getCid(0), cand.getCid(1)))
                if data is None or (data.col(0, cand.getCid(0)).isEnabled() and data.col(1, cand.getCid(1)).isEnabled()):
                    self.add(cand)
        return len(done) > 0, done

    # For parallel computation of initial candidates
    ########################################################

    def setExploreList(self, explore_list=[], pointer=-1, batch_size=0, done=set()):
        if done is None:
            done = set()
        self.explore_initc = {"list": explore_list, "pointer": pointer, "batch_size": batch_size, "done": done}

    def addExploredPair(self, pair):
        if self.explore_initc["done"] is not None:
            self.explore_initc["done"].add(pair)

    def getExploreList(self):
        return self.explore_initc["list"]

    def getExploredDone(self):
        return self.explore_initc["done"]

    def setExploredDone(self):
        self.setTracking(False)
        self.explore_initc["done"] = None
        self.explore_initc["pointer"] = -1

    def getExplorePointer(self):
        return self.explore_initc["pointer"]

    def setExplorePointer(self, pointer=-1):
        self.explore_initc["pointer"] = pointer

    def incrementExplorePointer(self):
        self.explore_initc["pointer"] += 1

    def getExploreNextBatch(self, pointer=None, bsize=None):
        if pointer is None:
            pointer = self.explore_initc["pointer"]
        if bsize is None:
            bsize = self.explore_initc["batch_size"]
        return self.explore_initc["list"][pointer*bsize:(pointer+1)*bsize]


def initCands(pt, data, constraints, save_filename=None):
    if pt == "T":
        return InitialTerms(data.nbRows(), constraints.getSSetts(), constraints, None,
                            constraints.getCstr("pair_sel"), constraints.getCstr("max_inits"))
    else:
        return InitialPairs(data.nbRows(), constraints.getSSetts(), constraints, None,
                            constraints.getCstr("pair_sel"), constraints.getCstr("max_inits"), save_filename=save_filename)


# if __name__ == "__main__":
#     import pickle

#     # from classPreferencesManager import getParams
#     # import glob
#     # import os.path
#     # import sys
#     # pref_dir = os.path.dirname(os.path.abspath(__file__))
#     # conf_defs = glob.glob(pref_dir + "/*_confdef.xml")
#     # params = getParams(sys.argv, conf_defs)

#     eb = ExtsBatch(20)
#     # pdb.set_trace()

#     with open('datafile.txt', 'wb') as fh:
#         pickle.dump(eb, fh)

#     pickle_off = open("datafile.txt", "rb")
#     ebx = pickle.load(pickle_off)
#     pickle_off.close()

#     pdb.set_trace()
