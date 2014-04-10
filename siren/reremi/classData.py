
import os.path
import numpy as np
import scipy.sparse
import codecs, re
from itertools import chain

from classQuery import Op, Term, BoolTerm, CatTerm, NumTerm, Literal, Query 
from classRedescription import Redescription
from classSParts import SSetts
from toolICList import ICList
################# START FOR BACKWARD COMPATIBILITY WITH XML
import toolRead
################# END FOR BACKWARD COMPATIBILITY WITH XML
import csv_reader
import pdb


class DataError(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)

class RowE(object):

    def __init__(self, rid, data):
        self.rid = rid
        self.data = data

    def getValue(self, side, col=None):
        if col is None:
            return self.data.getValue(side["side"], side["col"], self.rid)
        else:
            return self.data.getValue(side, col, self.rid)


    def getEnabled(self, details=None):
        if self.rid not in self.data.selectedRows():
            return 1
        else:
            return 0
        
    def flipEnabled(self):
        if self.rid in self.data.selectedRows():
            self.data.removeSelectedRow(self.rid)
        else:
            self.data.addSelectedRow(self.rid)

    def setEnabled(self):
        self.data.removeSelectedRow(self.rid)
    def setDisabled(self):
        self.data.addSelectedRow(self.rid)

    def getId(self, details=None):
        return self.rid

    def getRName(self, details=None):
        return self.data.getRName(self.rid)



class ColM(object):

    width = 0
    typespec_placeholder = "<!-- TYPE_SPECIFIC -->"

    def initSums(N):
        return [0 for i in range(N)]
    initSums = staticmethod(initSums)

    def parseList(list):
        return None
    parseList = staticmethod(parseList)
    
    def __init__(self, N=-1, nmiss= set()):
        if nmiss is None:
            nmiss = set()
        self.N = N
        self.missing = nmiss
        self.id = -1
        self.side = -1
        self.name = None
        self.enabled = 1
        self.infofull = {"in": (-1, True), "out": (-1, True)}
        self.vect = None

    def simpleBool(self):
        return False
                
    def nbRows(self):
        return self.N

    def rows(self):
        return set(range(self.N))

    def setId(self, nid):
        self.id = nid

    def hasMissing(self):
        return self.missing is not None and len(self.missing) > 0

    def getPrec(self, details=None):
        return 0

    def density(self):
        return 1.0

    def isDense(self, thres=None):
        if thres is None:
            thres = 0.5
        return self.density() > thres

    def getName(self, details=None):
        if self.name is not None:
            return self.name
        else:
            return Term.pattVName % self.getId()

    def hasName(self):
        return self.name is not None
        
    def getSide(self, details=None):
        return self.side

    def getId(self, details=None):
        return self.id

    def upSumsRows(self, sums_rows):
        pass
    def sumCol(self):
        return 0

    def numEquiv(self, v):
        try:
            return float(v)
        except:
            pass
        return Data.NA_num 

    def getVector(self):
        if self.vect is None:
            v = self.numEquiv(False)
            self.vect = [v for i in range(self.N)]
            for n in self.missing:
                self.vect[n] = self.numEquiv(Data.NA_num)
        return self.vect
    
    def getType(self, details=None):
        return "-"
    def getDensity(self, details=None):
        return "-"
    def getCategories(self, details=None):
        return "-"
    def getMin(self, details=None):
        return "-"
    def getMax(self, details=None):
        return "-"
    def getRange(self):
        return []


    def miss(self):
        return self.missing

    def suppLiteral(self, literal):
        if literal.isNeg():
            return self.rows() - self.suppTerm(literal.term) - self.miss()
        else:
            return self.suppTerm(literal.term)

    def lMiss(self):
        return len(self.miss())

    def lSuppLiteral(self, literal):
        if literal.isNeg():
            return self.nbRows() - len(self.suppTerm(literal.term)) - self.lMiss()
        else:
            return len(self.suppTerm(literal.term))

    def getEnabled(self, details=None):
        return self.enabled

    def flipEnabled(self):
        self.enabled = 1-self.enabled

    def setEnabled(self):
        self.enabled = 1
    def setDisabled(self):
        self.enabled = 0

    def __str__(self):
        return "%s variable %i %s, %d missing values" %(self.getType(), self.getId(), self.getName(), self.lMiss())

    def suppInBounds(self, min_in=-1, min_out=-1):
        return (self.infofull["in"][1] and self.infofull["out"][1]) 

    def usable(self, min_in=-1, min_out=-1, checkable=True):
        return self.suppInBounds(min_in, min_out) and (not checkable or self.getEnabled())

    ################# START FOR BACKWARD COMPATIBILITY WITH XML
    def fromXML(self, node):
        self.name = toolRead.getTagData(node, "name")
        self.N = toolRead.getTagData(node, "nb_entities", int)
        tmp_en = toolRead.getTagData(node, "status_enabled", int)
        if tmp_en is not None:
            self.enabled = tmp_en
        tmpm = toolRead.getTagData(node, "missing")
        if tmpm is not None:
            self.missing = set(map(int, re.split(Data.separator_str, tmpm.strip())))
    ################# END FOR BACKWARD COMPATIBILITY WITH XML

class BoolColM(ColM):
    type_id = BoolTerm.type_id
    width = -1
    values_eq = {True:1, False:0}

    values = {'true': True, 'false': False, 't': True, 'f': False, '0': False, '1': True}
    def parseList(listV, indices=None):
        if type(listV) is set:
            if type(indices) is int:
                trues = set(indices)
                N = indices
            elif type(indices) is dict:
                trues = set([indices.get(i,None) for i in listV])
                trues.discard(None)
                N = max(indices.values())+1
            else:
                raise ValueError('Sparse requires indices')
            return BoolColM(trues, N, set())
        if indices is None:
            indices = dict([(v,v) for v in range(len(listV))])
        trues = set()
        miss = set()
        if type(listV) is dict:
            ttt = set(listV.keys()).intersection(indices.keys())
        else:
            ttt = [i for i in indices.keys() if i < len(listV)]
        for i in ttt:
            j = indices[i]
            vt = listV[i]
            if vt is None or vt == str(Data.NA_num):
                miss.add(j)
            else:
                v = vt.lower()
                if v not in BoolColM.values:
                    return None
                elif BoolColM.values[v]:
                    trues.add(j)
        return BoolColM(trues, max(indices.values())+1, miss)
    parseList = staticmethod(parseList)

    def toList(self, sparse=False, fill=False):
        if sparse:
            t = int(True)
            m = Data.NA_num
            tmp = [(n, t) for n in self.hold]+[(n, m) for n in self.missing]
            if fill and self.N-1 not in self.hold and self.N-1 not in self.missing:
                tmp.append((self.N-1, int(False)))
            return tmp
        else:
            return map(str, self.getVector())

    def density(self):
        return (len(self.hold)+len(self.missing))/float(self.N)

    def getTerm(self):
        return BoolTerm(self.id)

    def simpleBool(self):
        return not self.hasMissing() and self.density() > 0

    def __str__(self):
        return ColM.__str__(self)+ ( ", %i Trues" %( self.lTrue() ))

    def upSumsRows(self, sums_rows):
        for i in self.hold:
            sums_rows[i] +=1
    def sumCol(self):
        return len(self.hold)

    def getRange(self):
        return dict([(k,v) for (v,k) in enumerate([True, False])])

    def numEquiv(self, v):
        try:
            return int(v)
        except:
            return Data.NA_num

    def getVector(self):
        if self.vect is None:
            self.vect = super(BoolColM, self).getVector()
            for i in self.hold:
                self.vect[i] = self.numEquiv(True)
        return self.vect

    def getType(self, details=None):
        return "Boolean"

    def getDensity(self, details=None):
        if self.N > 0:
            return "%1.4f" % self.density()
        return 0

    def __init__(self, ncolSupp=set(), N=-1, nmiss=set()):
        ColM.__init__(self, N, nmiss)
        self.hold = ncolSupp
        self.missing -= self.hold

    def subsetCol(self, row_ids=None):
        if row_ids is None:
            hold = set(self.hold)
            miss = set(self.missing)
            N = self.nbRows()
        else:
            miss = set()
            hold = set()
            N = sum([len(news) for news in row_ids.values()])
            for old in self.missing.intersection(row_ids.keys()):
                miss.update(row_ids[old])
            for old in self.hold.intersection(row_ids.keys()):
                hold.update(row_ids[old])
        tmp = BoolColM(hold, N, miss)
        tmp.name = self.name
        tmp.enabled = self.enabled
        tmp.infofull = {"in": tuple(self.infofull["in"]), "out": tuple(self.infofull["out"])}
        return tmp
    
    def getValue(self, rid):
        # self.getVector()
        if self.vect is None:
            if rid in self.missing:
                return Data.NA_num
            return rid in self.hold
        else:
            return self.vect[rid]

    def getNumValue(self, rid):
        return self.getValue(rid)

    def supp(self):
        return self.hold
    
    def suppTerm(self, term):
        return set(self.hold)

    def lTrue(self):
        return len(self.hold)

    def lFalse(self):
        return self.nbRows() - self.lTrue() - len(self.miss())

    def suppInBounds(self, min_in=-1, min_out=-1):
        if self.infofull["in"][0] != min_in:
            self.infofull["in"]= (min_in, self.lTrue() >= min_in)
        if self.infofull["out"][0] != min_out:
            self.infofull["out"]= (min_out, self.lFalse() >= min_out)
        return (self.infofull["in"][1] and self.infofull["out"][1]) 

    ################# START FOR BACKWARD COMPATIBILITY WITH XML
    def fromXML(self, node):
        ColM.fromXML(self, node)
        tmp_txt = toolRead.getTagData(node, "rows")
        if tmp_txt is not None and len(tmp_txt.strip()) > 0:
            self.hold = set(map(int, re.split(Data.separator_str, tmp_txt.strip())))
        self.missing -= self.hold
    ################# END FOR BACKWARD COMPATIBILITY WITH XML
    
class CatColM(ColM):
    type_id = CatTerm.type_id
    width = 1

    def initSums(N):
        return [{} for i in range(N)]
    initSums = staticmethod(initSums)

    n_patt = "^-?\d+(\.\d+)?$"
    def parseList(listV, indices=None):
        if indices is None:
            indices = dict([(v,v) for v in range(len(listV))])
        cats = {}
        miss = set()
        if type(listV) is dict:
            ttt = set(listV.keys()).intersection(indices.keys())
        else:
            ttt = [i for i in indices.keys() if i < len(listV)]
        for i in ttt:
            j = indices[i]
            v = listV[i]
            if v is None or v == str(Data.NA_num):
                miss.add(j)
            # elif re.match(CatColM.n_patt, v):
            #     return None
            else:
                if v in cats:
                    cats[v].add(j)
                else:
                    cats[v] = set([j])
        if len(cats) > 1:
            return CatColM(cats, max(indices.values())+1, miss)
        else:
            return None
    parseList = staticmethod(parseList)

    def toList(self, sparse=False, fill=False):
        cat_dict = dict([(Data.NA_num, Data.NA_num)]+enumerate(self.cats()))
        if sparse:
            return [(i,cat_dict[v]) for (i,v) in enumerate(self.getVector())]
        else:
            return [cat_dict[v] for (i,v) in enumerate(self.getVector())]


    def getTerm(self):
        return CatTerm(self.id, self.modeCat())

    def __str__(self):
        return ColM.__str__(self)+ ( ", %i categories" % len(self.cats()))

    def getRange(self):
        return dict([(k,v) for (v,k) in enumerate(self.cats())])

    def getCategories(self, details=None):
        if len(self.sCats) < 5:
            return ("%d [" % len(self.sCats)) + ', '.join(["%s:%d" % (catL, len(self.sCats[catL])) for catL in self.cats()]) + "]"
        else:
            return ("%d [" % len(self.sCats)) + ', '.join(["%s:%d" % (catL, len(self.sCats[catL])) for catL in self.cats()[:3]]) + "...]"

    def upSumsRows(self, sums_rows):
        for cat, rows in self.sCats.items():
            for i in rows:
                if not cat in sums_rows[i]:
                    sums_rows[i][cat]= 0
                sums_rows[i][cat]+=1
    def sumCol(self):
        return dict([(cat, len(rows)) for cat, rows in self.sCats.items()])
    
    def getValue(self, rid):
        if self.vvals is None:
            self.getVector()
        if rid < len(self.vvals):
            return self.vvals[rid]
        else:
            return Data.NA_num

    def getNumValue(self, rid):
        if self.vect is None:
            self.getVector()
        if rid < len(self.vect):
            return self.vect[rid]
        else:
            return Data.NA_num

    def numEquiv(self, v):
        try:
            return sorted(self.sCats.keys()).index(v)
        except:
            return Data.NA_num

    def getVector(self):
        if self.vect is None:
            self.vect = super(CatColM, self).getVector()
            self.vvals = [Data.NA_num for i in range(self.N)]
            for v, cat in enumerate(self.cats()):
                for i in self.sCats[cat]:
                    self.vect[i] = v
                    self.vvals[i] = cat
        return self.vect

    def getType(self, details=None):
        return "categorical"

    def __init__(self, ncolSupp={}, N=-1, nmiss= set()):
        ColM.__init__(self, N, nmiss)
        self.vvals = None
        self.sCats = ncolSupp
        self.cards = sorted([(cat, len(self.suppCat(cat))) for cat in self.cats()], key=lambda x: x[1]) 

    def subsetCol(self, row_ids=None):
        if row_ids is None:
            scats = dict(self.sCats)
            miss = set(self.missing)
            N = self.nbRows()
        else:
            miss = set()
            scats[cat] = {}
            N = sum([len(news) for news in row_ids.values()])
            for old in self.missing.intersection(row_ids.keys()):
                miss.update(row_ids[old])
            for cat in self.cats():
                scats[cat] = set()
                for old in self.hold.intersection(row_ids.keys()):
                    scats[cat].update(row_ids[old])
        tmp = CatColM(scats, N, miss)
        tmp.name = self.name
        tmp.enabled = self.enabled
        tmp.infofull = {"in": tuple(self.infofull["in"]), "out": tuple(self.infofull["out"])}
        return tmp

    def modeCat(self):
        return sorted(self.sCats.keys(),key=lambda x: len(self.sCats[x]))[-1]

    def getCatFromNum(self, n):
        if n < len(self.sCats):
            return self.cats()[n]
        return 0

    def cats(self):
        return sorted(self.sCats.keys())

    def suppCat(self, cat):
        return self.sCats.get(cat, set())
            
    def suppTerm(self, term):
        return self.suppCat(term.cat)

    def suppInBounds(self, min_in=-1, min_out=-1):
        if self.infofull["in"][0] != min_in:
            self.infofull["in"]= (min_in, self.cards[-1][1] >= min_in)
        if self.infofull["out"][0] != min_out:
            self.infofull["out"]= (min_out, self.nbRows() - self.cards[0][1] >= min_out)
        return (self.infofull["in"][1] and self.infofull["out"][1]) 

    ################# START FOR BACKWARD COMPATIBILITY WITH XML
    def fromXML(self, node):
        ColM.fromXML(self, node)
        self.sCats = {}
        count_miss = self.N
        tmp_txt = toolRead.getTagData(node, "values")
        if tmp_txt is not None:
            rows = set()
            row_id = 0
            for cat in re.split(Data.separator_str, tmp_txt.strip()):
                while row_id in self.missing:
                    row_id+=1
                self.sCats.setdefault(cat, set()).add(row_id)
                count_miss -= 1
                row_id += 1
            if count_miss != len(self.missing):
                raise DataError("Error reading real values, not the expected number of values!")
        self.cards = sorted([(cat, len(self.suppCat(cat))) for cat in self.cats()], key=lambda x: x[1]) 
    ################# END FOR BACKWARD COMPATIBILITY WITH XML
    
class NumColM(ColM):
    type_id = NumTerm.type_id
    width = 0

    p_patt = "^-?\d+(?P<dec>(\.\d+)?)$"
    alt_patt = "^[+-]?\d+.?\d*(?:[Ee][-+]\d+)?$"
    def parseVal(v, j, vals, miss=set(), prec=None, exclude=False, matchMiss=False):
        if (matchMiss is not False and v == matchMiss) or v == str(Data.NA_num):
            miss.add(j)
            return v, prec
        else:
            tmatch = re.match(NumColM.p_patt, v)
            if not tmatch:
                atmatch = re.match(NumColM.alt_patt, v)
                if not atmatch:
                    if matchMiss is False:
                        miss.add(j)
                    return v, prec
            else:
                if len(tmatch.group("dec")) > prec:
                    prec = len(tmatch.group("dec"))

            val = float(v)
            if exclude is False or val != exclude:
                vals.append((val, j))
        return val, prec
    parseVal = staticmethod(parseVal)
                
    def parseList(listV, indices=None):
        prec = None
        if indices is None:
            indices = dict([(v,v) for v in range(len(listV))])
        miss = set()
        vals = []
        N = max(indices.values())+1
        if type(listV) is dict:
            ttt = set(listV.keys()).intersection(indices.keys())
        else:
            ttt = [i for i in indices.keys() if i < len(listV)]
        for i in ttt:
            j = indices[i]
            val, prec = NumColM.parseVal(listV[i], j, vals, miss, prec, matchMiss=None)
        if len(vals) > 0 and (len(vals) + len(miss) == N or type(listV) is dict):
            return NumColM(vals, N, miss, prec)
        else:
            return None
    parseList = staticmethod(parseList)

    def toList(self, sparse=False, fill=False):
        if self.isDense() and not self.hasMissing():
            tmp = self.getVector()
            if sparse:
                return list(enumerate(tmp))
            else:
                return tmp
        else:
            tmp = dict([(i,v) for (v,i) in self.sVals])
            if self.nbRows()-1 not in tmp and fill: 
                tmp[self.nbRows()-1] = tmp[-1]
            if sparse:
                if -1 in tmp:
                    tmp.pop(-1)
                return tmp.items()
            else:
                return [tmp.get(i, tmp[-1]) for i in range(self.nbRows())]

    
    def getTerm(self):
        return NumTerm(self.id, self.sVals[int(len(self.sVals)*0.25)][0], self.sVals[int(len(self.sVals)*0.75)][0])

    def __str__(self):
        return ColM.__str__(self)+ ( ", %i values not in mode" % self.lenNonMode())

    def upSumsRows(self, sums_rows):
        for (v,i) in self.sVals:
            sums_rows[i] +=v
        if self.mode[0] == 1:
            for i in set(range(self.N)) - self.mode[1]:
                sums_rows[i] +=self.sVals[-1]
        if self.mode[0] == -1:
            for i in self.mode[1]:
                sums_rows[i] +=self.sVals[-1]

    def sumCol(self):
        tt = 0
        if len(self.sVals) > 0:
            tt = sum(zip(*self.sVals)[0])
        ### Add mode values, one has already been counted
        if self.mode[0] == 1:
            tt += (self.N - len(self.mode[1]) - 1)*self.sVals[-1]
        if self.mode[0] == -1:
            tt += (len(self.mode[1]) -1)*self.sVals[-1]
        return tt

    def getValue(self, rid):
        if self.vect is None:
            self.getVector()
        if type(self.vect) is dict:
            return self.vect.get(rid, self.vect[-1])
        else:
            return self.vect[rid]

    def numEquiv(self, v):
        try:
            tmp = float(v)
            if tmp < self.getMin():
                tmp = self.getMin()
            elif tmp > self.getMax():
                tmp = self.getMax()
            return tmp
        except:
            pass
        return Data.NA_num 

    def getVector(self):
        if self.vect is None:
            if self.isDense() and not self.hasMissing():
                if len(self.sVals) > 0:
                    self.vect = zip(*sorted(self.sVals,key=lambda x:x[1]))[0]
                else:
                    self.vect = []
            else:
                self.vect = dict([(i,v) for (v,i) in self.sVals])
                if self.isDense():
                    self.vect[-1] = self.numEquiv(Data.NA_num)
                ### Make sure can recover the length
                for n in self.missing:
                    self.vect[n] = self.numEquiv(Data.NA_num)
                ## make sure we recover full length
                if self.nbRows()-1 not in self.vect: 
                    self.vect[self.nbRows()-1] = self.vect[-1]
        return self.vect

    def getType(self, details=None):
        return "numerical"

    def getRange(self, details=None):
        return (self.getMin(details), self.getMax(details))
    def getMin(self, details=None):
        return self.sVals[0][0]
    def getMax(self, details=None):
        return self.sVals[-1][0]

    def compPrec(self, details=None):
        for (v,i) in self.sVals:
            if len(str(v % 1))-2 > self.prec:
                self.prec = len(str(v % 1))-2
        
    def getPrec(self, details=None):
        if self.prec is None:
            self.compPrec()
        return self.prec

    def __init__(self, ncolSupp=[], N=-1, nmiss=set(), prec=None):
        ColM.__init__(self, N, nmiss)
        self.prec = prec
        self.sVals = ncolSupp
        self.sVals.sort()
        self.mode = {}
        self.buk = None
        self.colbuk = None
        self.max_agg = None
        self.setMode()

    def subsetCol(self, row_ids=None):
        if row_ids is None:
            svals = [(v,i) for (v,i) in self.sVals]
            miss = set(self.missing)
            N = self.nbRows()
        else:
            miss = set()
            svals = []
            N = sum([len(news) for news in row_ids.values()])
            for old in self.missing.intersection(row_ids.keys()):
                miss.update(row_ids[old])
            for v, old in self.sVals:
                svals.extend([(v,new) for new in row_ids.get(old, [])])

        tmp = NumColM(svals, N, miss, self.prec)
        tmp.name = self.name
        tmp.enabled = self.enabled
        tmp.infofull = {"in": tuple(self.infofull["in"]), "out": tuple(self.infofull["out"])}
        return tmp

    def setMode(self):
        ### The mode is indicated by a special entry in sVals with row id -1,
        ### all rows which are not listed in either sVals or missing take that value
        if len([i for v,i in self.sVals if v == 0]) > 0.1*self.N:
            self.sVals = [(v,i) for (v,i) in self.sVals if v != 0]
        if len(self.sVals)+len(self.missing) > 0 and len(self.sVals)+len(self.missing) != self.N :
            ## gather row ids for which
            if len(self.sVals) > 0:
                rids = set(zip(*self.sVals)[1])
            else:
                rids = set()
            if len(rids) != len(self.sVals):
                raise DataError("Error reading real values, multiple values for a row!")
            has_mv = -1 in rids
            if has_mv:
                rids.discard(-1)
            if 2*len(rids) > self.N:
                self.mode = (-1, set(range(self.N)) - rids - self.missing)
            else:
                self.mode = (1, rids)
            if not has_mv:
                i = 0
                while i < len(self.sVals) and self.sVals[i][0] < 0:
                    i+=1
                self.sVals.insert(i, (0, -1))
        else:
            self.mode = (0, None)

    def density(self):
        if self.mode[0] != 0:
            if self.mode[0] == 1:
                return len(self.mode[1])/float(self.N)
            else:
                return 1-len(self.mode[1])/float(self.N)
        return 1.0

    def isDense(self, thres=None):
        if self.mode[0] != 0:
            if thres is None:
                return False
            else:
                return self.density() > thres
        return True

    def interNonMode(self, suppX):
        if self.mode[0] == -1:
            return suppX - self.mode[1] - self.miss()
        elif self.mode[0] == 1:
            return suppX & self.mode[1]
        else:
            return suppX - self.miss()  
    
    def interMode(self, suppX):
        if self.mode[0] == 1:
            return suppX - self.mode[1] - self.miss()
        elif self.mode[0] == -1:
            return suppX & self.mode[1]
        else:
            return set()    
        
    def lenNonMode(self):
        if self.mode[0] == -1:
            return self.nbRows() - len(self.mode[1]) - len(self.miss())
        elif self.mode[0] == 1:
            return len(self.mode[1])
        else:
            return self.nbRows() - len(self.miss())
        
    def lenMode(self):
        if self.mode[0] == 1:
            return self.nbRows() - len(self.mode[1]) - len(self.miss())
        elif self.mode[0] == -1:
            return len(self.mode[1])
        else:
            return 0
        
    def nonModeSupp(self):
        if self.mode[0] == -1:
            return set(range(self.nbRows())) - self.mode[1] - self.miss()
        elif self.mode[0] == 1:
            return self.mode[1]
        else:
            return set(range(self.nbRows()))-self.miss()

    def modeSupp(self):
        if self.mode[0] == 1:
            return set(range(self.nbRows())) - self.mode[1] -self.miss()
        elif self.mode[0] == -1:
            return self.mode[1]
        else:
            return set()

    def suppInBounds(self, min_in=-1, min_out=-1):
        if self.infofull["in"][0] != min_in:
            self.infofull["in"]= (min_in, self.lenNonMode() >= min_in)
        if self.infofull["out"][0] != min_out:
            self.infofull["out"]= (min_out, self.lenNonMode() >= min_out)
        return (self.infofull["in"][1] or self.infofull["out"][1]) 


    def collapsedBuckets(self, max_agg):
        if self.colbuk is None or (max_agg is not None and self.max_agg != max_agg):
            self.max_agg = max_agg
            self.colbuk = self.collapseBuckets(self.max_agg)
        return self.colbuk
    
    def collapseBuckets(self, max_agg):
        tmp = self.buckets()

        tmp_supp=set([])
        bucket_min=tmp[1][0]
        colB_supp = []
        colB_min= []
        colB_max= []
        # colB_max= [None]
        for i in range(len(tmp[1])):
            if len(tmp_supp) > max_agg:
                colB_supp.append(tmp_supp)
                colB_min.append(bucket_min)
                colB_max.append(tmp[1][i-1])
                bucket_min=tmp[1][i]
                tmp_supp=set([])
            tmp_supp.update(tmp[0][i])
        colB_supp.append(tmp_supp)
        colB_min.append(bucket_min)
        colB_max.append(tmp[1][-1])
        # colB_max[0] = colB_max[1]
        return (colB_supp, colB_min, 0, colB_max)

    def buckets(self):
        if self.buk is None:
            self.buk = self.makeBuckets()
        return self.buk

    def makeBuckets(self):
        if self.sVals[0][1] != -1 :
            bucketsSupp = [set([self.sVals[0][1]])]
        else:
            bucketsSupp = [set()]
        bucketsVal = [self.sVals[0][0]]
        bukMode = None
        for (val , row) in self.sVals:
            if row == -1: 
                if val != bucketsVal[-1]: # should be ...
                    bucketsVal.append(val)
                    bucketsSupp.append(set())
                bukMode = len(bucketsVal)-1
            else:
                if val == bucketsVal[-1]:
                    bucketsSupp[-1].add(row)
                else:
                    bucketsVal.append(val)
                    bucketsSupp.append(set([row]))
        return (bucketsSupp, bucketsVal, bukMode)

    def suppTerm(self, term):
        suppIt = set()
        for (val , row) in self.sVals:
            if val > term.upb :
                return suppIt
            elif val >= term.lowb:
                if row == -1:
                    suppIt.update(self.modeSupp())
                else:
                    suppIt.add(row)
        return suppIt

    def makeSegments(self, ssetts, side, supports, ops =[False, True]):
        supports.makeVectorABCD()
        segments = [[[self.sVals[0][0], None, ssetts.makeLParts()]], [[self.sVals[0][0], None, ssetts.makeLParts()]]]
        current_valseg = [[self.sVals[0][0], self.sVals[0][0], ssetts.makeLParts()], [self.sVals[0][0], self.sVals[0][0], ssetts.makeLParts()]]
        for (val, row) in self.sVals+[(None, None)]:
            tmp_lparts = supports.lpartsRow(row, self)

            for op in ops:
                if val is not None and ssetts.sumPartsId(side, ssetts.IDS_varnum[op], tmp_lparts) + ssetts.sumPartsId(side, ssetts.IDS_varden[op], tmp_lparts) == 0:
                    continue
                if val is not None and val == current_valseg[op][0]: 
                    current_valseg[op][2] = ssetts.addition(current_valseg[op][2], tmp_lparts)
                else:
                    tmp_pushadd = ssetts.addition(segments[op][-1][2], current_valseg[op][2]) 
                    if segments[op][-1][1]==None or ssetts.sumPartsId(side, ssetts.IDS_varnum[op], tmp_pushadd)*ssetts.sumPartsId(side, ssetts.IDS_varden[op], tmp_pushadd) == 0:
                        segments[op][-1][2] = tmp_pushadd
                        segments[op][-1][1] = current_valseg[op][1]
                    else:
                        segments[op].append(current_valseg[op])
                    current_valseg[op] = [val, val, ssetts.addition(ssetts.makeLParts(),tmp_lparts)]
        return segments


    def makeSegmentsColors(self, ssetts, side, supports, ops =[False, True]):
        supports.makeVectorABCD()

        partids = [[ssetts.partId(ssetts.gamma, side), ssetts.partId(ssetts.alpha, side)], \
                   [ssetts.partId(ssetts.beta, side), ssetts.partId(ssetts.delta, side)]]
        
        segments = [[[self.sVals[0][0], None, [0, 0]]], [[self.sVals[0][0], None, [0, 0]]]]
        current_valseg = [[self.sVals[0][0], self.sVals[0][0], [0, 0]], [self.sVals[0][0], self.sVals[0][0], [0, 0]]]
        for (val, row) in self.sVals+[(None, None)]:
            tmp_lparts = supports.lpartsRow(row, self)
            if tmp_lparts is None:
                procs = [(partids[0][0], 0), (partids[1][0], 0)]
            elif type(tmp_lparts) == int:
                procs = [(tmp_lparts, 1)]
            else:
                procs = enumerate(tmp_lparts)

            for (partid, incre) in procs:
                for op in ops:
                    if partid in partids[op]:
                        pos = partids[op].index(partid)
                        if val is not None and val == current_valseg[op][0]: 
                            current_valseg[op][2][pos] += incre
                        else:
                            tmp_pushadd = [segments[op][-1][2][0] + current_valseg[op][2][0], segments[op][-1][2][1] + current_valseg[op][2][1]] 
                            if segments[op][-1][1] == None or tmp_pushadd[0]*tmp_pushadd[1] == 0:
                                segments[op][-1][2] = tmp_pushadd
                                segments[op][-1][1] = current_valseg[op][1]
                            else:
                                segments[op].append(current_valseg[op])
                            tmp_init = [0, 0]
                            tmp_init[pos] = incre 
                            current_valseg[op] = [val, val, tmp_init]
        return segments

    def getLiteralBuk(self, neg, buk_op, bound_ids, buk_op_top=None):
        if buk_op_top is None:
            buk_op_top = buk_op
        if bound_ids[0] == 0 and bound_ids[1] == len(buk_op)-1:
            return (neg, None)
        elif bound_ids[0] == 0 :
            if neg:
                lowb = buk_op[bound_ids[1]+1]
                upb = float('Inf')
                n = False
            else:
                lowb = float('-Inf')
                upb = buk_op_top[bound_ids[1]]
                n = False
        elif bound_ids[1] == len(buk_op)-1 :
            if neg:
                lowb = float('-Inf') 
                upb = buk_op_top[bound_ids[0]-1]
                n = False
            else:
                lowb = buk_op[bound_ids[0]]
                upb = float('Inf') 
                n = False
        else:
            lowb = buk_op[bound_ids[0]]
            upb = buk_op_top[bound_ids[1]]
            n = neg
        return Literal(n, NumTerm(self.getId(), lowb, upb))

    def getLiteralSeg(self, neg, segments_op, bound_ids):
        if (bound_ids[0] == 0 and bound_ids[1] == len(segments_op)-1) or bound_ids[0] > bound_ids[1]:
            return None
        elif bound_ids[0] == 0 :
            if neg:
                lowb = segments_op[bound_ids[1]+1][0]
                upb = float('Inf')
                n = False
            else:
                lowb = float('-Inf')
                upb = segments_op[bound_ids[1]][1]
                n = False
        elif bound_ids[1] == len(segments_op)-1 :
            if neg:
                lowb = float('-Inf') 
                upb = segments_op[bound_ids[0]-1][1]
                n = False
            else:
                lowb = segments_op[bound_ids[0]][0]
                upb = float('Inf') 
                n = False
        else:
            lowb = segments_op[bound_ids[0]][0]
            upb = segments_op[bound_ids[1]][1]
            n = neg
        return Literal(n, NumTerm(self.getId(), lowb, upb))

    ################# START FOR BACKWARD COMPATIBILITY WITH XML
    def fromXML(self, node):
        ColM.fromXML(self, node)
        self.buk = None
        self.colbuk = None
        self.max_agg = None
        self.prec = None
        miss = set()
        self.sVals = []
        store_type = toolRead.getTagData(node, "store_type")
        if store_type == 'dense':
            i = 0
            for v in re.split(Data.separator_str, toolRead.getTagData(node, "values")):
                while i in self.missing:
                    i+=1
                val, self.prec = NumColM.parseVal(v, i, self.sVals, miss, self.prec)
                i+=1
        elif store_type == 'sparse':
            tmp_txt = toolRead.getTagData(node, "values").strip()
            if len(tmp_txt) > 0:
                for strev in  re.split(Data.separator_str, tmp_txt):
                    parts = strev.split(":")
                    val, self.prec = NumColM.parseVal(parts[1], int(parts[0]), self.sVals, miss, self.prec)
        if len(self.sVals) > 0:
            tmp_hold = set(zip(*self.sVals)[1])
        else:
            tmp_hold = set()
        if len(tmp_hold) != len(self.sVals):
            self.sVals = []
            tmp_hold = set()
            raise DataError("Error reading real values, multiple values for a row!")

        if len(miss) > 0:
            raise DataError("Error reading real values, some values could not be parsed!")

        self.sVals.sort()
        self.setMode()
    ################# END FOR BACKWARD COMPATIBILITY WITH XML
        
class Data:

    NA_str = "NA"
    NA_num  = np.nan
    separator_str = "[;, \t]"
    var_types = [None, BoolColM, CatColM, NumColM]

    def __init__(self, cols=[[],[]], N=0, coords=None, rnames=None, single_dataset=False):
        self.single_dataset = single_dataset
        self.as_array = [None, None, None]
        self.selected_rows = set()
        if type(N) == int:
            self.cols = cols
            self.N = N
            self.setCoords(coords)
            self.rnames = rnames

        elif type(N) == str:
            try:
                self.cols, self.N, self.coords, self.rnames, self.selected_rows, self.single_dataset = readDNCFromCSVFiles(cols)
                
            except DataError:
                self.cols, self.N, self.coords, self.rnames = [[],[]], 0, None, None
                raise

        else:
            print "Input non recognized!"
            self.cols, self.N, self.coords, self.rnames = [[],[]], 0, None, None
            raise
            
        if type(self.cols) == list and len(self.cols) == 2:
            self.cols = [ICList(self.cols[0]), ICList(self.cols[1])]
        else:
            self.cols = [ICList(),ICList()]
        self.ssetts = SSetts(self.hasMissing())

    def getSSetts(self):
        return self.ssetts

    def getValue(self, side, col, rid):
        return self.cols[side][col].getValue(rid)

    def getRName(self, rid):
        if self.rnames is not None and rid < len(self.rnames):
            return self.rnames[rid]
        return "#%d" % rid

    def getStats(self, group=None):
        if group is None:
            ### Group all columns from both side together
            group = []
            for side in [0,1]:
                group.extend([(side, i) for i in range(data.nbCols(side))])
        elif type(group) == int and group in [0,1]:
            ### Group all columns from that side together
            side = group
            group = [(side, i) for i in range(data.nbCols(side))]

        sums_rows = [None for t in Data.var_types]
        sums_cols = []
        details = []
        for side, col in group:
            tid = self.cols[side][col].type_id
            if sums_rows[tid] is None:
                sums_rows[tid] = self.cols[side][col].initSums(self.N)
            self.cols[side][col].upSumsRows(sums_rows[tid])
            sums_cols.append(self.cols[side][col].sumCol())
            details.append((side, col, tid))
        return sums_rows, sums_cols, details
        
    def getMatrix(self, side_cols=None, store=True, types=None, only_able=False):
        if store and self.as_array[0] == (side_cols, types, only_able):
            return self.as_array[1]

        if store:
            self.as_array[0] = (side_cols, types, only_able)
        
        if types is None:
            types = [BoolColM.type_id, CatColM.type_id, NumColM.type_id]

        if side_cols is None:
            side_cols = [(side, None) for side in [0,1]]
                    
        mcols = {}
        details = []
        for side, col in side_cols:
            if col is None:
                tcols = [c for c in range(len(self.cols[side]))]
            else:
                tcols = [col] 
            tcols = [c for c in tcols if self.cols[side][c].type_id in types and (not only_able or self.cols[side][c].getEnabled())]
            if len(tcols) > 0:
                for col in tcols:
                    mcols[(side, col)] = len(details)
                    details.append({"side": side, "col": col, "type": self.cols[side][col].type_id, "name":self.cols[side][col].getName(), "enabled":self.cols[side][c].getEnabled()})

        mat = np.vstack([getDenseArray(self.cols[d["side"]][d["col"]].getVector()) for d in details])
        if store:
            self.as_array[1] = (mat, details, mcols)
        return mat, details, mcols

    def subset(self, row_ids=None):
        coords = None
        rnames = None
        if row_ids is None:
            N = self.nbRows()
        else:
            N = sum([len(news) for news in row_ids.values()])
        if self.rnames is not None:
            if row_ids is None:
                rnames = list(self.rnames)
            else:
                rnames = ["-" for i in range(N)]
                for old, news in row_ids.items():
                    for new in news:
                        rnames[new]=self.rnames[old]
        if self.coords is not None:
            coords = []
            for coord in self.coords:
                if row_ids is None:
                    coords.append(list(coord))
                else:
                    coords.append([0 for i in range(N)])
                    for old, news in row_ids.items():
                        for new in news:
                            coords[-1][new]=coord[old]
        cols = [[],[]]
        for side in [0,1]:
            for col in self.cols[side]:
                tmp = col.subsetCol(row_ids)
                tmp.side = side
                tmp.id = len(cols[side])
                cols[side].append(tmp)
        return Data(cols, N, coords, rnames, self.single_dataset)

    def selectedRows(self):
        return self.selected_rows

    def nonselectedRows(self):
        return set(range(self.nbRows())) - self.selected_rows

    def addSelectedRow(self, rid):
        self.selected_rows.add(rid)

    def removeSelectedRow(self, rid):
        self.selected_rows.discard(rid)
                    
    def hasMissing(self):
        for side in [0,1]:
            for c in self.cols[side]:
                if c.hasMissing():
                    return True
        return False

    def getRows(self):
        return [RowE(i, self) for i in range(self.nbRows())]

    def __str__(self):
        return "%i x %i+%i data" % ( self.nbRows(), self.nbCols(0), self.nbCols(1))
        
    ### TODO REPLACE THE WRITE METHOD
    def writeCSV(self, outputs, thres=0.1, full_details=False, inline=False):
        #### FIGURE OUT HOW TO WRITE, WHERE TO PUT COORDS, WHAT METHOD TO USE
        #### check whether some row name is worth storing
        rids = {}
        if self.rnames is not None:
            rids = dict(enumerate([prepareRowName(rname, i, self) for i, rname in enumerate(self.rnames)]))
        elif len(self.selectedRows()) == 0:
            rids = dict(enumerate([prepareRowName(i+1, i, self) for i in range(self.N)]))

        mean_denses = [np.mean([col.density() for col in self.cols[0]]),
                       np.mean([col.density() for col in self.cols[1]])]
        argmaxd = 0
        if mean_denses[0] < mean_denses[1]:
            argmaxd = 1

        if mean_denses[1-argmaxd] > thres: ## BOTH SIDES ARE DENSE
            styles = {argmaxd: {"meth": "dense", "details": True},
                      1-argmaxd: {"meth": "dense", "details": full_details}}
        elif mean_denses[argmaxd] > thres:  ## ONE SIDE IS DENSE
            methot = "triples"
            if sum([col.simpleBool() for col in self.cols[1-argmaxd]])==0:
                methot = "pairs"
            styles = {argmaxd: {"meth": "dense", "details": True},
                      1-argmaxd: {"meth": methot, "details": full_details, "inline": inline}}
        else:  ## BOTH SIDES ARE SPARSE
            simpleBool = [sum([col.simpleBool() for col in self.cols[0]]) == 0,
                          sum([col.simpleBool() for col in self.cols[1]]) == 0]
            if self.isGeospatial() or len(rids) > 0:
                if not simpleBool[1-argmax]: ### is not only boolean so can have names and coords
                    styles = {argmaxd: {"meth": "pairs", "details": full_details},
                              1-argmaxd: {"meth": "triples", "details": True, "inline": inline}}
                else: ### otherwise argmax has it
                    styles = {argmaxd: {"meth": "triples", "details": True, "inline": inline},
                              1-argmaxd: {"meth": "pairs", "details": full_details}}
            else:
                styles = {argmaxd: {"meth": "pairs", "details": full_details},
                          1-argmaxd: {"meth": "pairs", "details": full_details}}
                for side in [0,1]:
                    if not simpleBool[side] or len(cids[side]) > 0:
                        styles[side]["meth"] = "triples"
                        styles[side]["inline"] = inline

        
        meths = {"pairs": self.writeCSVSparsePairs, "triples": self.writeCSVSparseTriples, "dense": self.writeCSVDense}
        for side in [0,1]:
    #### check whether some column name is worth storing
            cids = {}
            if sum([not (col.getName() == cid and col.getEnabled()) for cid, col in enumerate(self.cols[side])]) > 0:
                type_smap = None
                if full_details and styles[side]["meth"] == "dense":
                    type_smap = {}
                cids = dict(enumerate([prepareColumnName(col, type_smap) for col in self.cols[side]]))
                meth = meths[styles[side].pop("meth")]
            with open(outputs[side], "wb") as fp:
                csvf = csv_reader.start_out(fp)
                meth(side, csvf, rids=rids, cids=cids, **styles[side])

    def writeCSVDense(self, side, csvf, rids={}, cids={}, details=True):
        header = []
        if details and len(rids) > 0:
            header.append(csv_reader.IDENTIFIERS[0])
        if details and self.isGeospatial():
            header.append(csv_reader.LATITUDE[0])
            header.append(csv_reader.LONGITUDE[0])
        for cid, col in enumerate(self.cols[side]):
            col.getVector()
            if len(header) > 0 or len(cids) > 0:
                header.append(cids.get(cid, cid))
                
        if len(header) > 0:
            csv_reader.write_row(csvf, header)

        for n in range(self.N):
            row = []
            if details and len(rids) > 0:
                row.append(rids.get(n,n))
            if details and self.isGeospatial():
                row.append(":".join(map(str, self.coords[0][n])))
                row.append(":".join(map(str, self.coords[1][n])))
            for col in self.cols[side]:
                row.append(col.getValue(n))
            csv_reader.write_row(csvf, row)


    def writeCSVSparseTriples(self, side, csvf, rids={}, cids={}, details=True, inline=False):
        csv_reader.write_row(csvf, [csv_reader.IDENTIFIERS[0], csv_reader.COLVAR[0], csv_reader.COLVAL[0]])
        if not inline:
            trids, tcids = {}, {}
        else:
            trids, tcids = rids, cids
            
        if details and self.isGeospatial():
            for n in range(self.N):
                csv_reader.write_row(csvf, [trids.get(n,n), csv_reader.LATITUDE[0], ":".join(map(str,  self.coords[0][n]))])
                csv_reader.write_row(csvf, [trids.get(n,n), csv_reader.LONGITUDE[0], ":".join(map(str,  self.coords[1][n]))])

        fill = False
        if details and len(rids) > 0 and not inline:
            for n in range(self.N):
                csv_reader.write_row(csvf, [n, -1, rids.get(n,n)])
        else:
            fill = True

        for ci, col in enumerate(self.cols[side]):
            if not inline and len(cids) > 0:
                csv_reader.write_row(csvf, [-1, ci, cids.get(ci,ci)])
            else:
                fill = True

            if ci == 0 and fill:
                tmp = col.toList(sparse=True, fill=False)
                non_app = col.rows().difference(zip(*tmp)[0])
                for (n,v) in tmp:
                    csv_reader.write_row(csvf, [trids.get(n,n), tcids.get(ci,ci), v])
                for n in non_app:
                    csv_reader.write_row(csvf, [trids.get(n,n), tcids.get(ci,ci), 0])

            else:
                for (n,v) in col.toList(sparse=True, fill=fill):
                    csv_reader.write_row(csvf, [trids.get(n,n), tcids.get(ci,ci), v])

    ### THIS FORMAT ONLY ALLOWS BOOLEAN WITHOUT COORS, IF NAMES THEY HAVE TO BE INLINE
    def writeCSVSparsePairs(self, side, csvf, rids={}, cids={}, details=True):
        csv_reader.write_row(csvf, [csv_reader.IDENTIFIERS[0], csv_reader.COLVAR[0]])
        if not details:
            rids = {}
        for ci, col in enumerate(self.cols[side]):
            for (n,v) in col.toList(sparse=True, fill=False):
                csv_reader.write_row(csvf, [rids.get(n,n), cids.get(ci,ci)])

    def disp(self):
        strd = str(self) +":\n"
        strd += 'Left Hand side columns:\n'
        for col in self.cols[0]:
            strd += "\t%s\n" % col
        strd += 'Right Hand side columns:\n'
        for col in self.cols[1]:
            strd += "\t%s\n" % col
        return strd

    def rows(self):
        return set(range(self.N))

    def nbRows(self):
        return self.N

    def nbCols(self, side):
        return len(self.cols[side])

    def colsSide(self, side): 
        return self.cols[side]

    def col(self, side, literal):
        colid = None
        if type(literal) == int and literal < len(self.cols[side]):
            colid = literal
        elif literal.term.colId() < len(self.cols[side]):
            colid = literal.term.colId()
            if literal.term.type_id != self.cols[side][colid].type_id:
                raise DataError("The type of literal does not match the type of the corresponding variable (%s~%s)!" % (literal.term.type_id, self.cols[side][colid].type_id))
                colid = None
        if colid is not None:
            return self.cols[side][colid]

    def name(self, side, literal):
        return self.col(side, literal).getName()
        
    def supp(self, side, literal): 
        return self.col(side, literal).suppLiteral(literal)

    def miss(self, side, literal):
        return self.col(side, literal).miss()

    def literalSuppMiss(self, side, literal):
        return (self.supp(side, literal), self.miss(side,literal))
            
    def usableIds(self, min_in=-1, min_out=-1):
        return [[i for i,col in enumerate(self.cols[0]) if col.usable(min_in, min_out)], \
                [i for i,col in enumerate(self.cols[1]) if col.usable(min_in, min_out)]]

    def isGeospatial(self):
        return self.coords is not None
            
    def getCoords(self):
        return self.coords

    def getCoordsExtrema(self):
        if self.isGeospatial():
            return [min(chain.from_iterable(self.coords[0])), max(chain.from_iterable(self.coords[0])), min(chain.from_iterable(self.coords[1])), max(chain.from_iterable(self.coords[1]))]
        return None

        return self.coords

    def hasRNames(self):
        return self.rnames is not None

    def hasNames(self):
        for side in [0,1]:
            for col in self.cols[side]:
                if col.hasName():
                    return True
        return False

    def getNames(self, side=None):
        if side is None:
            return [[col.getName() for col in self.cols[side]] for side in [0,1]]
        else:
            return [col.getName() for col in self.cols[side]]

    def setNames(self, names):
        if len(names) == 2:
            for side in [0,1]:
                if names[side] is not None:
                    if len(names) == self.nbCols(side):
                        for i, col in enumerate(self.colsSide(side)):
                            col.name = names[i]
                    else:
                        raise DataError('Number of names does not match number of variables!')

    def setCoords(self, coords):
        if coords is None or (len(coords)==2 and len(coords[0]) == self.nbRows()):
            self.coords = coords
        else:
            self.coords = None
            raise DataError('Number of coordinates does not match number of entities!')

    ################# START FOR BACKWARD COMPATIBILITY WITH XML
    def readDataFromXMLFile(filename):
        (cols, N, coord, rnames) = ([[],[]], 0, None, None)
        single_dataset = False
        try:
            try:
                doc = toolRead.parseXML(filename)
                dtmp = doc.getElementsByTagName("data")
            except AttributeError as inst:
                raise DataError("%s is not a valid data file! (%s)" % (filename, inst))
            else:
                if len(dtmp) != 1:
                    raise DataError("%s is not a valid data file! (%s)" % (filename, inst))
                N = toolRead.getTagData(dtmp[0], "nb_entities", int)
                tsd = toolRead.getTagData(dtmp[0], "single_dataset", int)
                if tsd == 1:
                    single_dataset = True
                for side_data in doc.getElementsByTagName("side"):
                    side = toolRead.getTagData(side_data, "name", int)
                    if side not in [0,1]:
                        print "Unknown side (%s)!" % side
                    else:
                        nb_vars = toolRead.getTagData(side_data, "nb_variables", int)
                        for var_tmp in side_data.getElementsByTagName("variable"):
                            type_id = toolRead.getTagData(var_tmp, "type_id", int)
                            if type_id >= len(Data.var_types):
                                print "Unknown variable type (%d)!" % type_id
                            else:
                                col = Data.var_types[type_id]()
                                col.fromXML(var_tmp)
                                if col is not None and col.N == N:
                                    col.setId(len(cols[side]))
                                    col.side = side
                                    cols[side].append(col)
                                    if single_dataset:
                                        ocol = col.subsetCol()
                                        ocol.setId(len(cols[1-side]))
                                        ocol.side = 1-side
                                        cols[1-side].append(ocol)


                    if nb_vars != len(cols[side]):
                        print "Number of variables found don't match expectations (%d ~ %d)!" % (nb_vars, len(cols[side]))
                ctmp = doc.getElementsByTagName("coordinates")
                if len(ctmp) == 1:
                    coord = []
                    for cotmp in ctmp[0].getElementsByTagName("coordinate"):
                        tmp_txt = toolRead.getTagData(cotmp, "values")
                        if tmp_txt is not None:
                            coord.append([map(float, p.strip(":").split(":")) for p in re.split(Data.separator_str, tmp_txt.strip())])
                    if len(coord) != 2 or len(coord[0]) != len(coord[1]) or len(coord[0]) != N:
                        coord = None
                    else:
                        coord = np.array(coord)
                ctmp = doc.getElementsByTagName("rnames")
                if len(ctmp) == 1:
                    rnames = [v.strip() for v in toolRead.getValues(ctmp[0], str, "rname")]
                    if len(rnames) != N:
                        rnames = None
        except DataError:
            cols, N, coords, rnames = [[],[]], 0, None, None
            raise
        return Data(cols, N, coord, rnames, single_dataset)
    readDataFromXMLFile = staticmethod(readDataFromXMLFile)
    ################# END FOR BACKWARD COMPATIBILITY WITH XML
    
############################################################################
############## READING METHODS
############################################################################
def readDNCFromCSVFiles(filenames):
    cols, N, coords, rnames = [[],[]], 0, None, None
    csv_params={}; unknown_string=None
    single_dataset = False
    if len(filenames) >= 2:
        left_filename = filenames[0]
        right_filename = filenames[1]
        single_dataset = (filenames[0] == filenames[1])
        if len(filenames) >= 3:
            csv_params = filenames[2]
            if len(filenames) >= 4:
                unknown_string = filenames[3]
        try:
            tmp_data = csv_reader.importCSV(left_filename, right_filename, csv_params, unknown_string)
        except ValueError as arg:
            raise DataError('Data error reading csv: %s' % arg)
        except csv_reader.CSVRError as arg:
            raise DataError(str(arg).strip("'"))
        cols, N, coords, rnames, disabled_rows = parseDNCFromCSVData(tmp_data)

    return cols, N, coords, rnames, disabled_rows, single_dataset


def prepareRowName(rname, rid=None, data=None):
    en = ""
    if rid is not None and data is not None and rid in data.selectedRows():
        en = "_"
    return "%s%s" % (en, rname) 

def parseRowsNames(rnames):
    disabled = set()
    names = []
    for i, rname in enumerate(rnames):
        if rname is None:
            names.append("%d" % (i+1))
        else:
            tmatch = re.match("^(?P<disabled>__*)?(?P<name>.*)$", rname)
            if tmatch.group("disabled") is not None:
                disabled.add(i)
            names.append(tmatch.group("name"))
    return names, disabled

def prepareColumnName(col, types_smap={}):
    en = ""
    if not col.getEnabled():
        en = "_"
    if types_smap is None:
        return "%s%s" % (en, col.getName()) 
    else:
        return "%s[%s]%s" % (en, types_smap.get(col.type_id, col.type_id), col.getName()) 
    
def parseColumnName(name, types_smap={}):
    tmatch = re.match("^(?P<disabled>__*)?(\[(?P<type>[0-9])\])?(?P<name>.*)$", name)
    det = {"name": tmatch.group("name")}
    if tmatch.group("disabled") is not None:
        det["enabled"] = False
    if tmatch.group("type") is not None and tmatch.group("type") in types_smap:
        det["type"] = types_smap[tmatch.group("type")]
    return name, det

def parseDNCFromCSVData(csv_data):
    type_ids_org = [CatColM, NumColM, BoolColM]
    types_smap = dict([(str(c.type_id), c) for c in type_ids_org])
    cols = [[],[]]
    coords = None
    single_dataset = False
    if csv_data.get("coord", None) is not None:
        try:
            tmp = zip(*csv_data["coord"])
            coords = np.array([tmp[1], tmp[0]])
        except Exception:
            coords = None

    N = len(csv_data['data'][0]["order"]) ### THE READER CHECKS THAT BOTH SIDES HAVE SAME SIZE
    if csv_data.get("ids", None) is not None and len(csv_data["ids"]) == N:
        rnames, disabled_rows = parseRowsNames(csv_data["ids"])
    else:
        rnames, disabled_rows = [Term.pattVName % n for n in range(N)], set()
        
    for side in [0,1]:
        indices = dict([(v,k) for (k,v) in enumerate(csv_data['data'][side]["order"])])
        for name, det in [parseColumnName(header, types_smap) for header in csv_data['data'][side]["headers"]]:
            if len(name) == 0:
                continue
            values = csv_data['data'][side]["data"][name]
            col = None
            
            if "type" in det:
                col = det["type"].parseList(values, indices)
            else:
                type_ids = list(type_ids_org)
                while col is None and len(type_ids) >= 1:
                    col = type_ids.pop().parseList(values, indices)

            if col is not None and col.N == N:
                col.setId(len(cols[side]))
                col.side = side
                col.name = det.get("name", name)
                if not det.get("enabled", True):
                    col.flipEnabled()
                cols[side].append(col)
            else:
                raise DataError('Unrecognized variable type!')
    return (cols, N, coords, rnames, disabled_rows)

def getDenseArray(vect):
    if type(vect) is dict:
        tmp = [0 for i in range(max(vect.keys())+1)]
        for i, v in vect.items():
            if i != -1:
                tmp[i] = v
        return np.array([tmp])
        # vs, ijs = zip(*[(v, (i,0)) for (i,v) in vect.items() if i != -1])
        # return scipy.sparse.csc_matrix((np.array(vs),np.array(ijs).T)).todense().T
    else:
        return np.array([vect])




def main():
    # print "UNCOMMENT"
    # rep = "/home/galbrun/redescriptors/data/world/"
    # data = Data([rep+"carnivora-3r.csv", rep+"navegcovermatthews-3r.csv", {}, "NA"], "csv")
    # data.writeXML(open("tmp.xml", "w"))

    # rep = "/home/galbrun/redescriptors/data/rajapaja/"
    # data = Data([rep+"mammals.sparsebool", rep+"worldclim_tp.densenum", {}, "NA"], "csv")
    # print data

    # rep = "/home/galbrun/"
    # data = Data([rep+"data1.csv", rep+"data2.csv", {}, "NA"], "csv")    
    # data2 = Data("tmp.xml", "xml")
    # data = Data([rep+"carnivora-3l.csv", rep+"navegcovermatthews-3l.csv", {}, "NA"], "csv")
    # pdb.set_trace()
    # data = Data([rep+"carnivora-3g.csv", rep+"navegcovermatthews-3.csv", {}, "NA"], "csv")
    # print data2
    # print data2.isGeospatial()
    #data = Data([rep+"carnivora-3.csv", rep+"navegcovermatthews-3.csv", {}, "NA"], "csv")
    # rep = "/home/galbrun/TKTL/redescriptors/data/vaalikone/"
    # data = Data([rep+"vaalikone_profiles_miss.csv", rep+"vaalikone_questions_miss.csv", {}, "NA"], "csv")
    # data = Data([rep+"vaalikone_profiles_test.csv", rep+"vaalikone_questions_test.csv", {}, "NA"], "csv")
    rep = "/home/galbrun/TKTL/redescriptors/data/dblp/"
    data = Data([rep+"coauthor_picked0_num.csv", rep+"conference_picked0_num.csv"], "csv")
    # print data
    # data.writeCSV([rep+"testoutL.csv", rep+"testoutR.csv"], full_details=True)
    # data.writeCSV([rep+"testoutL4.csv", rep+"testoutR4.csv"], inline=True)
    # data.writeCSV([rep+"testoutL3.csv", rep+"testoutR3.csv"])
    # data2 = Data([rep+"testoutL4.csv", rep+"testoutR4.csv", {}, "nan"], "csv")
    # print data2
    # data2.writeCSV([rep+"testoutL2.csv", rep+"testoutR2.csv"])

    # rep = "/home/galbrun/TKTL/redescriptors/data/rajapaja/"
    # data = Data([rep+"mammals_poly.csv", rep+"worldclim_poly.csv"], "csv")
    # data.selected_rows = set([0,2, data.N-1])
    # data.writeCSV([rep+"testoutL.csv", rep+"testoutR.csv"])
    # data2 = Data([rep+"testoutL.csv", rep+"testoutR.csv", {}, "nan"], "csv")
    # data2.writeCSV([rep+"testoutL2.csv", rep+"testoutR2.csv"])
    # rep = "/home/galbrun/redescriptors/data/de/"
    # rep = "/home/galbrun/redescriptors/data/de/de.siren_FILES/"
    # # print data.hasMissing()
    # # print len(data.cols[1][0].missing)
    # #data.writeXML(open("tmp.xml", "w"))
    # data2 = Data("data.xml", "xml")
    # print data2.hasRNames()
    # print data2
    # print data2.hasMissing()
    # print data2.cols[1][0].missing == data.cols[1][0].missing
    
    # data = Data(["/home/galbrun/redescriptors/data/rajapaja/mammals.csv",
    #               "/home/galbrun/redescriptors/data/rajapaja/worldclim_nomiss.csv"], "csv")
    # data = Data(["/home/galbrun/redescriptors/data/world/mammals.csv",
    #               "/home/galbrun/redescriptors/data/world/worldclim.csv"], "csv")
    # print data
    # print data.getCoordsExtrema()
    # data = Data("/home/galbrun/re.siren_FILES/data.xml", "xml")
    # data = Data("/home/galbrun/redescriptors/data/rajapaja/data_poly.xml", "xml")
    # print data.getCoordsExtrema()
    # data = Data(["/home/galbrun/redescriptors/data/rajapaja/mammals.sparsebool",
    #              "/home/galbrun/redescriptors/data/rajapaja/worldclim_tp.densenum", None, None,
    #              "/home/galbrun/redescriptors/data/rajapaja/coordinates_poly.names",
    #              "/home/galbrun/redescriptors/data/rajapaja/entities.names"], "multiple")
    # data = Data(["/home/galbrun/redescriptors/data/dblp/conference_picked.sparsenum",
    #              "/home/galbrun/redescriptors/data/dblp/coauthor_picked.sparsenum", None, None,
    #              None,
    #              "/home/galbrun/redescriptors/data/dblp/coauthor_picked.names"], "multiple")
    # print data.hasRNames()
    # data.writeXML(open("tmp.xml", "w"))

if __name__ == '__main__':
    main()

