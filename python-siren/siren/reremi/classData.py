
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

NA_str = "NA"
NA_num  = np.nan
NA_bool  = -1
NA_cat  = -1

class DataError(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)

class ColM(object):

    type_id = None
    width = 0
    typespec_placeholder = "<!-- TYPE_SPECIFIC -->"
    NA = NA_bool

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

    def nbMissing(self):
        if self.missing is not None:
            return len(self.missing)
        return 0

    def valToStr(self, val):
        if val == self.NA:
            return Data.NA_str 
        return val

    def getPrec(self, details=None):
        return 0

    def density(self):
        return 1.0

    def minGap(self):
        return 0

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
            return int(v)
        except:
            pass
        return self.NA


    def mkVector(self):
        self.vect = np.ones(self.N, dtype=np.int)*self.NA
        
    def getVector(self, bincats=False, nans=None):
        if self.vect is None:
            self.mkVector()
        if self.hasMissing() and nans is not None and \
               not ( (np.isnan(nans) and np.isnan(self.NA)) or nans == self.NA): ## Not the same nan...
            tmp = np.array(self.vect, dtype=np.float, copy=True)
            tmp[tmp==self.NA] = nans
            return tmp
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
    def getMissInfo(self, details=None):
        return "%1.2f%%: %d"% (len(self.missing)/float(self.N), len(self.missing))
    def getRange(self):
        return []


    def typeId(self):
        return self.type_id

    def miss(self):
        return self.missing

    def suppLiteral(self, literal):
        if isinstance(literal, Term): ### It's a literal, not a term
            return self.suppTerm(literal)
        elif isinstance(literal, Literal):
            if literal.isNeg():
                return self.rows() - self.suppTerm(literal.getTerm()) - self.miss()
            else:
                return self.suppTerm(literal.getTerm())

    def lMiss(self):
        return len(self.miss())

    def lSuppLiteral(self, literal):
        if isinstance(literal, Term): ### It's a literal, not a term
            return len(self.suppTerm(literal))
        elif isinstance(literal, Literal):
            if literal.isNeg():
                return self.nbRows() - len(self.suppTerm(literal.getTerm())) - self.lMiss()
            else:
                return len(self.suppTerm(literal.getTerm()))

    def getEnabled(self, details=None):
        return self.enabled

    def flipEnabled(self):
        self.enabled = 1-self.enabled

    def setEnabled(self):
        self.enabled = 1
    def setDisabled(self):
        self.enabled = 0

    def __str__(self):
        return "%s variable %i %s, %d missing values" %(self.getType(), self.getId(), self.getName().encode('ascii', 'replace'), self.lMiss())

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
    letter = 'B'
    width = -1
    values_eq = {True:1, False:0}
    NA = NA_bool

    values = {'true': True, 'false': False, 't': True, 'f': False, '0': False, '1': True, 0:False, 1:True}
    def parseList(listV, indices=None, force=False):
        if  force:
            if type(listV) is list:
                listV = set([i for (i, v) in enumerate(listV) if BoolColM.values.get(v, True)])
            elif type(listV) is not set:
                tt = set()
                ok = True
                for idx, v in listV.items():
                    try:
                        if int(v) != 0:
                            tt.add(idx)
                    except ValueError:
                        ok = False
                if ok:
                    listV = tt
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
            if vt is None or vt == str(BoolColM.NA):
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
            tmp = [(n, t) for n in self.hold]+[(n, self.NA) for n in self.missing]
            if fill and self.N-1 not in self.hold and self.N-1 not in self.missing:
                tmp.append((self.N-1, int(False)))
            return tmp
        else:
            # return map(self.valToStr, self.getVector())
            return self.getVector()

    def density(self):
        if self.N == len(self.missing):
            return 0.0
        else:
            return len(self.hold)/float(self.N-len(self.missing))

    def minGap(self):
        return 1.

    def getTerm(self):
        return BoolTerm(self.id)

    def getInitTerms(self, minIn=0, minOut=0):
        if len(self.hold) >= minIn and self.N-(len(self.hold)+self.nbMissing()) >= minOut:
            return [(BoolTerm(self.id), len(self.hold))]
        else:
            return []
        
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

    def getNbValues(self):
        return 2
    
    def numEquiv(self, v):
        try:
            return int(v)
        except:
            return self.NA

    def mkVector(self):
        self.vect = np.ones(self.N, dtype=np.int)*self.numEquiv(False)
        self.vect[list(self.missing)] = self.NA
        self.vect[list(self.hold)] = self.numEquiv(True)

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
        if self.vect is None:
            if rid in self.missing:
                return self.NA
            return rid in self.hold
        else:
            return self.vect[rid]

    def getNumValue(self, rid):
        return int(self.getValue(rid))

    def getCatFromNum(self, n):
        return n == 1

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
    letter = 'C'
    width = 1
    NA =  NA_cat

    def getType(self, details=None):
        return "categorical"

    def __init__(self, ncolSupp={}, N=-1, nmiss= set()):
        ColM.__init__(self, N, nmiss)
        self.sCats = ncolSupp
        self.ord_cats = sorted(self.sCats.keys())
        self.cards = sorted([(cat, len(self.suppCat(cat))) for cat in self.cats()], key=lambda x: x[1])

    def initSums(N):
        return [{} for i in range(N)]
    initSums = staticmethod(initSums)

    n_patt = "^-?\d+(\.\d+)?$"
    def parseList(listV, indices=None, force=False):
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
            if v is None or v == str(CatColM.NA):
                miss.add(j)
            # elif re.match(CatColM.n_patt, v):
            #     return None
            else:
                if v in cats:
                    cats[v].add(j)
                else:
                    cats[v] = set([j])
        if len(cats) > 0:
            if len(cats) == 1:
                print "Only one category %s, this is suspect!.." % (cats.keys())
            return CatColM(cats, max(indices.values())+1, miss)
        else:
            return None
    parseList = staticmethod(parseList)

    def toList(self, sparse=False, fill=False):
        if sparse:
            dt = [(i, NA_str) for i in self.missing]
            for cat, iis in self.sCats.items():
                dt.extend([(i, cat) for i in iis])
            return dt
        else:
            cat_dict = self.ord_cats + [NA_str]
            return [cat_dict[v] for v in self.getVector()]

    def mkVector(self):
        self.vect = np.ones(self.N, dtype=np.int)*self.numEquiv(self.NA)
        for v, cat in enumerate(self.ord_cats):
            self.vect[list(self.sCats[cat])] = v

    def getVector(self, bincats=False, nans=None):
        if bincats:
            vect = np.zeros((self.N, self.nbCats()), dtype=np.int)
            for v, cat in enumerate(self.ord_cats):
                vect[list(self.sCats[cat]), v] = 1
            return vect
        
        if self.vect is None:
            self.mkVector()
        if self.hasMissing() and nans is not None and \
               not ( (np.isnan(nans) and np.isnan(self.NA)) or nans == self.NA): ## Not the same nan...
            tmp = np.array(self.vect, dtype=np.float, copy=True)
            tmp[tmp==self.NA] = nans
            return tmp
        return self.vect

    def minGap(self):
        return 1

    def getTerm(self):
        return CatTerm(self.id, self.modeCat())

    def getInitTerms(self, minIn=0, minOut=0):
        terms = []
        for cat in self.cats():
            if len(self.sCats[cat]) >= minIn and self.N-(len(self.sCats[cat])+self.nbMissing()) >= minOut:
                terms.append((CatTerm(self.id, cat), len(self.sCats[cat])))
        return terms

    def __str__(self):
        return ColM.__str__(self)+ ( ", %i categories" % self.nbCats())

    def getRange(self):
        return dict([(k,v) for (v,k) in enumerate(self.ord_cats)])

    def getNbValues(self):
        return self.nbCats()

    def getCategories(self, details=None):
        if self.nbCats() < 5:
            return ("%d [" %  self.nbCats()) + ', '.join(["%s:%d" % (catL, len(self.sCats[catL])) for catL in self.cats()]) + "]"
        else:
            return ("%d [" % self.nbCats()) + ', '.join(["%s:%d" % (catL, len(self.sCats[catL])) for catL in self.cats()[:3]]) + "...]"

    def upSumsRows(self, sums_rows):
        for cat, rows in self.sCats.items():
            for i in rows:
                sums_rows[i][cat] = sums_rows[i].get(cat, 0)+1
    def sumCol(self):
        return dict(self.cards)
    
    def getValue(self, rid):
        if self.vect is None:
            self.getVector()
        if rid < len(self.vect) and self.vect[rid] != self.NA:
            return self.ord_cats[self.vect[rid]]
        else:
            return self.NA

    def getNumValue(self, rid):
        if self.vect is None:
            self.getVector()
        if rid < len(self.vect):
            return self.vect[rid]
        else:
            return self.NA

    def numEquiv(self, v):
        try:
            if type(v) is str and type(self.ord_cats[0]) is unicode:
                v = codecs.decode(v, 'utf-8','replace')
            return self.ord_cats.index(v)
        except:
            return self.NA

    def subsetCol(self, row_ids=None):
        if row_ids is None:
            scats = dict(self.sCats)
            miss = set(self.missing)
            N = self.nbRows()
        else:
            miss = set()
            scats = {}
            N = sum([len(news) for news in row_ids.values()])
            for old in self.missing.intersection(row_ids.keys()):
                miss.update(row_ids[old])
            for cat, rs in self.sCats.items():
                scats[cat] = set()
                for old in rs.intersection(row_ids.keys()):
                    scats[cat].update(row_ids[old])
        tmp = CatColM(scats, N, miss)
        tmp.name = self.name
        tmp.enabled = self.enabled
        tmp.infofull = {"in": tuple(self.infofull["in"]), "out": tuple(self.infofull["out"])}
        return tmp

    def modeCat(self):
        return self.cards[-1][0]

    def getCatFromNum(self, n):
        if n>= 0 and n < self.nbCats():
            return self.cats()[int(n)]
        return self.NA

    def cats(self):
        return self.ord_cats
    def nbCats(self):
        return len(self.ord_cats)
    
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
            self.ord_cats = sorted(self.sCats.keys())
            self.cards = sorted([(cat, len(self.suppCat(cat))) for cat in self.cats()], key=lambda x: x[1])
    ################# END FOR BACKWARD COMPATIBILITY WITH XML
    
class NumColM(ColM):
    type_id = NumTerm.type_id
    letter = 'N'
    width = 0
    NA = NA_num

    p_patt = "^-?\d+(?P<dec>(\.\d+)?)$"
    alt_patt = "^[+-]?\d+.?\d*(?:[Ee][-+]\d+)?$"
    def parseVal(v, j, vals, miss=set(), prec=None, exclude=False, matchMiss=False):
        if (matchMiss is not False and v == matchMiss) or v == str(NumColM.NA):
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
                
    def parseList(listV, indices=None, force=False):
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
        elif force:
            # pdb.set_trace()
            return NumColM(vals, N, miss, prec, force=True)
        else:
            return None
    parseList = staticmethod(parseList)

    def toList(self, sparse=False, fill=False):
        if self.isDense() and not self.hasMissing():
            if sparse:
                return list(enumerate(self.getVector()))
            else:
                return self.getVector()
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

    def getInitTerms(self, minIn=0, minOut=0):
        return []

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

    def valToStr(self, val):
        if (np.isnan(val) and np.isnan(self.NA)) or \
               val == self.NA:
            return Data.NA_str
        return val


    def getNumValue(self, rid):
        return self.getValue(rid)
        
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
        return self.NA 

    def minGap(self):
        if self.vect is None:
            self.mkVector()
        return np.min(np.diff(np.unique(self.vect[np.isfinite(self.vect)])))

    def mkVector(self):
        if self.isDense():
            self.vect = np.ones(self.N)*self.NA
        else:
            self.vect = np.zeros(self.N)
            self.vect[list(self.missing)] = self.NA

        if len(self.sVals) > 0:
            vals, ids = zip(*self.sVals)
            self.vect[list(ids)] = vals

    def getType(self, details=None):
        return "numerical"

    def getRange(self, details=None):
        return (self.getMin(details), self.getMax(details))
    def getMin(self, details=None):
        return self.sVals[0][0]
    def getMax(self, details=None):
        return self.sVals[-1][0]

    def getNbValues(self):
        return self.nbUniq

    def compPrec(self, details=None):
        for (v,i) in self.sVals:
            if len(str(v % 1))-2 > self.prec:
                self.prec = len(str(v % 1))-2
        
    def getPrec(self, details=None):
        if self.prec is None:
            self.compPrec()
        return self.prec

    def __init__(self, ncolSupp=[], N=-1, nmiss=set(), prec=None, force=False):
        ColM.__init__(self, N, nmiss)
        self.prec = prec
        self.sVals = ncolSupp
        self.sVals.sort()
        self.mode = {}
        self.buk = None
        self.colbuk = None
        self.max_agg = None
        self.setMode(force)

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

    def setMode(self, force=False):
        ### The mode is indicated by a special entry in sVals with row id -1,
        ### all rows which are not listed in either sVals or missing take that value
        if len([i for v,i in self.sVals if v == 0]) > 0.1*self.N:
            self.sVals = [(v,i) for (v,i) in self.sVals if v != 0]
        if force or (len(self.sVals)+len(self.missing) > 0 and len(self.sVals)+len(self.missing) != self.N ):
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
        self.nbUniq = np.unique([v[0] for v in self.sVals]).shape[0]
        
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
            return None
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

class RowE(object):

    def __init__(self, rid, data):
        self.rid = rid
        self.data = data

    def getValue(self, side, col=None):
        if col is None:
            if side.get("aim", None) == "sort":
                t = self.data.getNumValue(side["side"], side["col"], self.rid)
                return {BoolColM.NA: None, CatColM.NA: None, NumColM.NA: None}.get(t,t)
            elif side.get("aim", None) == "row":
                return self.data.getNumValue(side["side"], side["col"], self.rid)
            else:
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
        
class Data(object):

    enabled_codes = {(0,0): "F", (1,1): "T", 0: "F", 1: "T", (0,1): "L", (1,0): "R"}
    enabled_codes_rev_simple = {"F": 0, "T": 1}
    enabled_codes_rev_double = {"F": (0,0), "T": (1,1), "L": (0,1), "R": (1,0)}
    separator_str = "[;, \t]"
    var_types = [None, BoolColM, CatColM, NumColM]
    all_types_map = dict([(None, None)]+[(v.letter, v) for v in var_types[1:]])
    NA_str = "NA"

    def __init__(self, cols=[[],[]], N=0, coords=None, rnames=None, single_dataset=False):
        self.single_dataset = single_dataset
        self.split = None 
        self.as_array = [None, None, None]
        self.selected_rows = set()
        if type(N) == int:
            self.cols = cols
            self.N = N
            self.rnames = rnames

        elif type(N) == str:
            try:
                self.cols, self.N, coords, self.rnames, self.selected_rows, self.single_dataset, Data.NA_str = readDNCFromCSVFiles(cols, Data.NA_str)
                
            except DataError:
                self.cols, self.N, coords, self.rnames = [[],[]], 0, None, None
                raise

        else:
            print "Input non recognized!"
            self.cols, self.N, coords, self.rnames = [[],[]], 0, None, None
            raise
        self.setCoords(coords)
        
        if type(self.cols) == list and len(self.cols) == 2:
            self.cols = [ICList(self.cols[0]), ICList(self.cols[1])]
        else:
            self.cols = [ICList(),ICList()]
        self.ssetts = SSetts(self.hasMissing())

    def addCol(self, col, sito=0, name=None):
        addCol(self.cols, col, sito, name)

    def getCommonType(self, side):
        s = set([col.letter for col in self.cols[side]])
        if len(s) == 1:
            return s.pop()
        return None
        
    def isSingleD(self):
        return self.single_dataset

    def getSSetts(self):
        return self.ssetts

    def getValue(self, side, col, rid):
        return self.cols[side][col].getValue(rid)

    def getNumValue(self, side, col, rid):
        return self.cols[side][col].getNumValue(rid)


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
        
    def getMatrix(self, side_cols=None, store=True, types=None, only_able=False, bincats=False, nans=None):
        if store and self.as_array[0] == (side_cols, types, only_able, bincats):
            return self.as_array[1]

        if store:
            self.as_array[0] = (side_cols, types, only_able, bincats)
        
        if types is None:
            types = [BoolColM.type_id, CatColM.type_id, NumColM.type_id]

        if side_cols is None:
            side_cols = [(side, None) for side in [0,1]]
                    
        mcols = {}
        details = []
        off = 0
        for side, col in side_cols:
            if col is None:
                tcols = [c for c in range(len(self.cols[side]))]
            else:
                tcols = [col] 
            tcols = [c for c in tcols if self.cols[side][c].typeId() in types and (not only_able or self.cols[side][c].getEnabled())]
            if len(tcols) > 0:
                for col in tcols:
                    bids = [0]
                    if bincats and self.cols[side][col].typeId() == 2:
                        bids = range(self.cols[side][col].nbCats()) 
                    mcols[(side, col)] = len(details)
                    for bid in bids:
                        mcols[(side, col, bid)] = off
                        off += 1
                    details.append({"side": side, "col": col, "type": self.cols[side][col].typeId(), "name":self.cols[side][col].getName(), "enabled":self.cols[side][c].getEnabled(), "bincats": bids})
        mat = np.hstack([self.cols[d["side"]][d["col"]].getVector(bincats, nans).reshape((self.nbRows(),-1)) for d in details]).T
        if store:
            self.as_array[1] = (mat, details, mcols)
        return mat, details, mcols

    def getSplit(self, nbsubs=10, coo_dim=None, grain=10., force=False):
        if coo_dim is not None and \
               not (( self.isGeospatial() and coo_dim < 0 and abs(coo_dim)-1 < len(self.getCoords())) or \
                    ( coo_dim >= 0 and coo_dim < len(self.cols[0])+len(self.cols[1]) )):
            coo_dim = None

        if ( self.split is None ) or ( self.split["source"] != "auto" ) \
                 or self.split["parameters"].get("nbsubs", None) != nbsubs \
                 or self.split["parameters"].get("coo_dim", None) != coo_dim \
                 or self.split["parameters"].get("grain", None) != grain :
            if coo_dim is None:
                vals = None
                grain = None
            elif self.isGeospatial() and coo_dim < 0 and abs(coo_dim)-1 < len(self.getCoords()):
                vals = self.getCoordPoints()[:,abs(coo_dim)-1]
            else: ## is in the variables
                if coo_dim >= len(self.cols[0]):
                    col = self.cols[1][coo_dim-len(self.cols[0])]
                else:
                    col = self.cols[0][coo_dim]
                vals = col.getVector()

            self.split = {"source": "auto",
                          "parameters": {"coo_dim": coo_dim, "grain": grain, "nbsubs": nbsubs},
                          "splits": self.rsubsets_split(nbsubs, vals, grain)}
            skeys = ["%d" % i for (i,v) in enumerate(self.split['splits'])]
            self.split["split_ids"] = dict([(v,k) for (k,v) in enumerate(skeys)])
        return self.split['splits']            

    def dropLT(self):
        if self.split is not None:
            if "lt_ids" in self.split:
                del self.split["lt_ids"]
                del self.split["lt_sids"]


    def assignLT(self, learn_sids, test_sids):
        if self.split is None:
            return
        rids = {"learn": set(), "test": set()}
        for (which, sids) in [("learn", learn_sids), ("test", test_sids)]:
            for sid in sids:
                if sid in self.split["split_ids"]:
                    rids[which].update(self.split["splits"][self.split["split_ids"][sid]])
        self.split["lt_ids"] = rids
        self.split["lt_sids"] = {"learn": learn_sids, "test": test_sids}

    def hasSplits(self):
        return self.split is not None
    def hasAutoSplits(self):
        return self.split is not None and self.split["source"] == "auto"
    def hasLT(self):
        return self.split is not None and "lt_ids" in self.split
    def getLT(self):
        if self.hasLT():
            return self.split["lt_ids"]
        else:
            return {}
    def getLTsids(self):
        if self.hasLT():
            return self.split["lt_sids"]
        else:
            return {}


    def getFoldsInfo(self):
        return self.split

    def addFoldsCol(self, subsets=None, sito=1):
        suff = "cust"
        if subsets is None and self.split is not None:
            if self.split["source"] != "auto":
                subsets = dict([(k, self.split["splits"][kk]) for (k,kk) in self.split["split_ids"].items()])
                suff = "%s-g%s" % ((self.split["parameters"]["coo_dim"] or "N"), (self.split["parameters"]["grain"] or "N"))
        if type(subsets) is list:
            subsets = dict(enumerate(subsets))
        if subsets is not None and type(subsets) is dict:
            col = CatColM(dict([("F:%s" % i, s) for (i,s) in subsets.items()]), self.nbRows())
            self.addCol(col, sito, "folds_split_"+suff)

    def extractFolds(self, side, colid):
        splits = None
        if type(self.cols[side][colid]) is CatColM:
            self.cols[side][colid].setDisabled()
            splits = dict([(re.sub("^F:", "", f), set(fsupp)) for (f, fsupp) in self.cols[side][colid].sCats.items()])
            skeys = sorted(splits.keys())
            self.split = {"source": "data",
                          "parameters": {"side": side, "colid": colid, "colname": self.cols[side][colid].getName()},
                          "split_ids": dict([(v,k) for (k,v) in enumerate(skeys)]),
                          "splits": [splits[k] for k in skeys]}
        return splits

    def findCandsFolds(self):
        return self.getColsByName("^folds_split_")

    def getColsByName(self, pattern):
        results = []
        for (sito, cols) in enumerate(self.cols):
            for (ci, col) in enumerate(cols):
                if re.search(pattern, col.getName()):
                    results.append((sito, ci))
        return results
        
    def rsubsets_split(self, nbsubs=10, split_vals=None, grain=10.):
        # uv, uids = np.unique(np.mod(np.floor(self.getCoords()[0]*grain),nbsubs), return_inverse=True)
        # return [set(np.where(uids==uv[i])[0]) for i in range(len(uv))]
        if split_vals is not None:
            uv, uids = np.unique(split_vals, return_inverse=True)
            if len(uv) > nbsubs:
                nv = np.floor(split_vals*grain)
                uv, uids = np.unique(nv, return_inverse=True)
                sizes = [(len(uv)/nbsubs, nbsubs - len(uv)%nbsubs), (len(uv)/nbsubs+1, len(uv)%nbsubs)]
                maps_to = np.hstack([[i]*sizes[0][0] for i in range(sizes[0][1])]+[[i+sizes[0][1]]*sizes[1][0] for i in range(sizes[1][1])])
                np.random.shuffle(maps_to)
                subsets_ids = [set() for i in range(nbsubs)]
                for i in range(len(uv)):
                    subsets_ids[maps_to[i]].update(np.where(uids==i)[0])
            else:
                subsets_ids = [set(np.where(uids==i)[0]) for i in range(len(uv))]
        else:
            sizes = [(self.nbRows()/nbsubs, nbsubs - self.nbRows()%nbsubs), (self.nbRows()/nbsubs+1, self.nbRows()%nbsubs)]
            maps_to = np.hstack([[i]*sizes[0][0] for i in range(sizes[0][1])]+[[i+sizes[0][1]]*sizes[1][0] for i in range(sizes[1][1])])
            np.random.shuffle(maps_to)
            subsets_ids = [set() for i in range(nbsubs)]
            for i in range(nbsubs):
                subsets_ids[i].update(np.where(maps_to==i)[0])
        return subsets_ids
        

    #### old version for reremi run subsplits
    def get_LTsplit(self, row_idsT):
        row_idsL = set(range(self.nbRows()))
        row_idsT = row_idsL.intersection(row_idsT)
        row_idsL.difference_update(row_idsT)
        return self.subset(row_idsL), self.subset(row_idsT)

    def subset(self, row_ids=None):
        coords = None
        rnames = None
        if row_ids is None:
            N = self.nbRows()
        else:
            if type(row_ids) is set:
                row_ids = sorted(row_ids)
            if type(row_ids) is list:
                row_ids = dict([(r,[ri]) for (ri, r) in enumerate(row_ids)])
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
            if row_ids is None:
                coords = self.coords.copy()
            else:
                maps_to = np.array([0 for i in range(N)])
                for old, news in row_ids.items():
                    maps_to[news] = old
                coords = self.coords[:,maps_to]

        cols = [[],[]]
        for side in [0,1]:
            for col in self.cols[side]:
                tmp = col.subsetCol(row_ids)
                tmp.side = side
                tmp.id = len(cols[side])
                cols[side].append(tmp)
        return Data(cols, N, coords, rnames, self.isSingleD())

    def hasSelectedRows(self):
        return len(self.selected_rows) > 0

    def selectedRows(self):
        return self.selected_rows

    def getVizRows(self, details=None):
        if details is not None and details.get("rset_id", None) in self.getLT():
            if len(self.selected_rows) == 0:
                return set(self.getLT()[details["rset_id"]])
            return set(self.getLT()[details["rset_id"]])  - self.selected_rows
        return self.nonselectedRows()

    def getUnvizRows(self, details=None):
        if details is not None and details.get("rset_id", None) in self.getLT():
            return self.selected_rows.union(*[s for (k,s) in self.getLT().items() if k != details["rset_id"]])
        return self.selected_rows

    def nonselectedRows(self):
        return self.rows() - self.selected_rows

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
        
    def writeCSV(self, outputs, thres=0.1, full_details=False, inline=False):
        #### FIGURE OUT HOW TO WRITE, WHERE TO PUT COORDS, WHAT METHOD TO USE
        #### check whether some row name is worth storing
        rids = {}
        if self.rnames is not None:
            rids = dict(enumerate([prepareRowName(rname, i, self) for i, rname in enumerate(self.rnames)]))
        elif len(self.selectedRows()) > 0:
            rids = dict(enumerate([prepareRowName(i+1, i, self) for i in range(self.N)]))
        mean_denses = [np.mean([col.density() for col in self.cols[0]]),
                       np.mean([col.density() for col in self.cols[1]])]
        argmaxd = 0
        if mean_denses[0] < mean_denses[1]:
            argmaxd = 1
        #### FOR DEBUGING OF DENSE FORMAT, REMOVE!!!!
        # if mean_denses[1-argmaxd] > 0 : #thres: ## BOTH SIDES ARE DENSE
        if mean_denses[1-argmaxd] > thres: ## BOTH SIDES ARE DENSE
            styles = {argmaxd: {"meth": "dense", "details": True},
                      1-argmaxd: {"meth": "dense", "details": full_details}}
        elif mean_denses[argmaxd] > thres:  ## ONE SIDE IS DENSE
            methot = "triples"
            if not self.hasDisabledCols(1-argmaxd) and sum([col.simpleBool() for col in self.cols[1-argmaxd]])==0:
                methot = "pairs"
            styles = {argmaxd: {"meth": "dense", "details": True},
                      1-argmaxd: {"meth": methot, "details": full_details, "inline": inline}}
        else:  ## BOTH SIDES ARE SPARSE
            simpleBool = [sum([not col.simpleBool() for col in self.cols[0]]) == 0,
                          sum([not col.simpleBool() for col in self.cols[1]]) == 0]

            if self.isGeospatial() or len(rids) > 0:
                if not simpleBool[1-argmaxd]: ### is not only boolean so can have names and coords
                    methot = "pairs"
                    if self.hasDisabledCols(argmaxd) or not simpleBool[argmaxd]:
                        methot = "triples"
                    styles = {argmaxd: {"meth": methot, "details": full_details},
                              1-argmaxd: {"meth": "triples", "details": True, "inline": inline}}
                else: ### otherwise argmax has it
                    methot = "pairs"
                    if self.hasDisabledCols(1-argmaxd):
                        methot = "triples"
                    styles = {argmaxd: {"meth": "triples", "details": True, "inline": inline},
                              1-argmaxd: {"meth": methot, "details": full_details}}
            else:
                styles = {argmaxd: {"meth": "pairs", "details": full_details},
                          1-argmaxd: {"meth": "pairs", "details": full_details}}
                for side in [0,1]:
                    if not simpleBool[side] or len(cids[side]) > 0:
                        styles[side]["meth"] = "triples"
                        styles[side]["inline"] = inline

        meths = {"pairs": self.writeCSVSparsePairs, "triples": self.writeCSVSparseTriples, "dense": self.writeCSVDense}
        sides = [0,1]
        if self.isSingleD() and (len(outputs) == 1 or outputs[0] == outputs[1] or outputs[1] is None):
            sides = [0]
            styles[0]["details"] = True
            styles[0]["single_dataset"] = True
        for side in sides:
    #### check whether some column name is worth storing
            cids = {}
            if sum([col.getName() != cid or not col.getEnabled() for cid, col in enumerate(self.cols[side])]) > 0:
                type_smap = None
                if full_details and styles[side]["meth"] == "dense":
                    type_smap = {}
                cids = dict(enumerate([prepareColumnName(col, type_smap) for col in self.cols[side]]))
                meth = meths[styles[side].pop("meth")]
            with open(outputs[side], "wb") as fp:
                csvf = csv_reader.start_out(fp)
                meth(side, csvf, rids=rids, cids=cids, **styles[side])

    def writeCSVDense(self, side, csvf, rids={}, cids={}, details=True, single_dataset=False):
        discol = []
        if self.hasDisabledCols(side) or (single_dataset and self.hasDisabledCols()):
            discol.append(csv_reader.ENABLED_COLS[0])
            if details and self.hasSelectedRows():
                discol.append(0)
            if details and self.isGeospatial():
                discol.append(0)
                discol.append(0)
            for cid, col in enumerate(self.cols[side]):
                if single_dataset:
                    discol.append(Data.enabled_codes[(self.cols[0][cid].getEnabled(), self.cols[1][cid].getEnabled())])
                else:
                    discol.append(Data.enabled_codes[col.getEnabled()])

        header = []
        if (details and len(rids) > 0) or len(discol) > 0:
            header.append(csv_reader.IDENTIFIERS[0])
        if details and self.hasSelectedRows():
            header.append(csv_reader.ENABLED_ROWS[0])
        if details and self.isGeospatial():
            header.append(csv_reader.LONGITUDE[0])
            header.append(csv_reader.LATITUDE[0])
        for cid, col in enumerate(self.cols[side]):
            col.getVector()
            if len(header) > 0 or len(cids) > 0:
                header.append(cids.get(cid, cid))

        letter = self.getCommonType(side)
        if letter is not None:
            header.append("type=%s" % letter)

        if len(header) > 0:
            csv_reader.write_row(csvf, header)
        if len(discol) > 0:
            csv_reader.write_row(csvf, discol)

        for n in range(self.N):
            row = []
            if (details and len(rids) > 0) or len(discol) > 0:
                row.append(rids.get(n,n))
            if details and self.hasSelectedRows():
                row.append(Data.enabled_codes[n not in self.selectedRows()])
            if details and self.isGeospatial():
                row.append(":".join(map(str, self.coords[0][n])))
                row.append(":".join(map(str, self.coords[1][n])))
            for col in self.cols[side]:
                row.append(col.valToStr(col.getValue(n)))
            csv_reader.write_row(csvf, row)


    def writeCSVSparseTriples(self, side, csvf, rids={}, cids={}, details=True, inline=False, single_dataset=False):
        header = [csv_reader.IDENTIFIERS[0], csv_reader.COLVAR[0], csv_reader.COLVAL[0]]
        letter = self.getCommonType(side)
        if letter is not None:
            header.append("type=%s" % letter)
        csv_reader.write_row(csvf, header)
        if not inline:
            trids, tcids = {}, {}
        else:
            trids, tcids = rids, cids
            
        if details and self.isGeospatial():
            for n in range(self.N):
                csv_reader.write_row(csvf, [trids.get(n,n), csv_reader.LONGITUDE[0], ":".join(map(str,  self.coords[0][n]))])
                csv_reader.write_row(csvf, [trids.get(n,n), csv_reader.LATITUDE[0], ":".join(map(str,  self.coords[1][n]))])

        for n in self.selectedRows():
                csv_reader.write_row(csvf, [trids.get(n,n), csv_reader.ENABLED_ROWS[0], "F"])

        if self.hasDisabledCols(side) or (single_dataset and self.hasDisabledCols()):
            for cid, col in enumerate(self.cols[side]):
                if single_dataset:
                    tmp = Data.enabled_codes[(self.cols[0][cid].getEnabled(), self.cols[1][cid].getEnabled())]
                else:
                    tmp = Data.enabled_codes[col.getEnabled()]
                if tmp != Data.enabled_codes[1]:
                    if inline:
                        csv_reader.write_row(csvf, [csv_reader.ENABLED_COLS[0], cids.get(cid,cid), tmp])
                    else:
                        csv_reader.write_row(csvf, [csv_reader.ENABLED_COLS[0], cid, tmp])

        fillR = False
        ### if names are not written inline, add the entities names now, that serves to recovers the correct number of lines
        if details and len(rids) > 0 and not inline:
            for n in range(self.N):
                csv_reader.write_row(csvf, [n, -1, rids.get(n,n)])
        else:
            ### otherwise it will need fill to recover the number of lines
            fillR = True

        for ci, col in enumerate(self.cols[side]):
            fillC = False
            if not inline and len(cids) > 0:
                ### if names are not written inline, add the variable's name now
                csv_reader.write_row(csvf, [-1, ci, cids.get(ci,ci)])
            else:
                fillC = True

            if ci == 0 and fillR:
                tmp = col.toList(sparse=True, fill=False)
                non_app = col.rows().difference(zip(*tmp)[0])
                for (n,v) in tmp:
                    csv_reader.write_row(csvf, [trids.get(n,n), tcids.get(ci,ci), v])
                for n in non_app:
                    csv_reader.write_row(csvf, [trids.get(n,n), tcids.get(ci,ci), 0])
            else:
                for (n,v) in col.toList(sparse=True, fill=fillR):
                    fillC = False
                    csv_reader.write_row(csvf, [trids.get(n,n), tcids.get(ci,ci), v])
                if fillC:
                    ### Filling for column if it does not have any entry
                    csv_reader.write_row(csvf, [trids.get(0,0), tcids.get(ci,ci), 0])
                    

    ### THIS FORMAT ONLY ALLOWS BOOLEAN WITHOUT COORS, IF NAMES THEY HAVE TO BE INLINE
    def writeCSVSparsePairs(self, side, csvf, rids={}, cids={}, details=True, inline=False, single_dataset=False):
        header = [csv_reader.IDENTIFIERS[0], csv_reader.COLVAR[0]]
        letter = self.getCommonType(side)
        if letter is not None:
            header.append("type=%s" % letter)
        csv_reader.write_row(csvf, header)
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
        if type(literal) in [int, np.int64] and literal < len(self.cols[side]):
            colid = literal
        elif (isinstance(literal, Term) or isinstance(literal, Literal)) and literal.colId() < len(self.cols[side]):
            colid = literal.colId()
            if literal.typeId() != self.cols[side][colid].typeId():
                raise DataError("The type of literal does not match the type of the corresponding variable (on side %s col %d type %s ~ lit %s type %s)!" % (side, colid, literal, literal.typeId(), self.cols[side][colid].typeId()))
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

    def getDisabledCols(self, side=None):
        dis = []
        if side is None:
            sides = [0,1]
        else:
            sides = [side]
        for s in sides:
            for col in self.cols[s]:
                if not col.getEnabled():
                    dis.append((s,col.id))
        return dis

    def hasDisabledCols(self, side=None):
        if side is None:
            sides = [0,1]
        else:
            sides = [side]
        for s in sides:
            for col in self.cols[s]:
                if not col.getEnabled():
                    return True
        return False

    def isGeospatial(self):
        return self.coords is not None
            
    def getCoords(self):
        return self.coords

    def getCoordPoints(self):
        return self.coords_points

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
        ### coords are NOT turned to a numpy array because polygons might have different numbers of points
        if coords is None or (len(coords)==2 and len(coords[0]) == self.nbRows()):
            self.coords = coords
            self.coords_points = np.array([[coords[0][i][0], coords[1][i][0]] for i in range(len(coords[0]))])
        else:
            self.coords = None
            self.coords_points = None
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
def readDNCFromCSVFiles(filenames, unknown_string = None):
    cols, N, coords, rnames = [[],[]], 0, None, None
    csv_params={}; 
    single_dataset = False
    if len(filenames) >= 2:
        left_filename = filenames[0]
        right_filename = filenames[1]
        if len(filenames) >= 3:
            csv_params = filenames[2]
            if len(filenames) >= 4 and filenames[3] is not None:
                unknown_string = filenames[3]
        try:
            tmp_data, single_dataset = csv_reader.importCSV(left_filename, right_filename, csv_params, unknown_string)
        except ValueError as arg:
            raise DataError('Data error reading csv: %s' % arg)
        # except csv_reader.CSVRError as arg:
        #     raise DataError(str(arg).strip("'"))
        cols, N, coords, rnames, disabled_rows = parseDNCFromCSVData(tmp_data, single_dataset)

    return cols, N, coords, rnames, disabled_rows, single_dataset, unknown_string

def addCol(cols, col, sito=0, name=None):
    col.setId(len(cols[sito]))
    col.side = sito
    if name is None:
        col.name = Term.pattVName % len(cols[sito])
    else:
        col.name = name
    cols[sito].append(col)

def prepareRowName(rname, rid=None, data=None):
    return "%s" % rname 
    en = ""
    if rid is not None and data is not None and rid in data.selectedRows():
        en = "_"
    return "%s%s" % (en, rname) 

def parseRowsNames(rnames):
    names = []
    for i, rname in enumerate(rnames):
        if rname is None:
            names.append("%d" % (i+1))
        else:
            names.append(rname)
    return names

def prepareColumnName(col, types_smap={}):
    return "%s" % col.getName() 
    en = ""
    if not col.getEnabled():
        en = "_"
    if types_smap is None:
        return "%s%s" % (en, col.getName()) 
    else:
        return "%s[%s]%s" % (en, types_smap.get(col.typeId(), col.typeId()), col.getName()) 
    
def parseColumnName(name, types_smap={}):
    tmatch = re.match("^(\[(?P<type>[0-9])\])?(?P<name>.*)$", name)
    det = {"name": tmatch.group("name")}
    if tmatch.group("type") is not None and tmatch.group("type") in types_smap:
        det["type"] = types_smap[tmatch.group("type")]
    return name, det

def parseDNCFromCSVData(csv_data, single_dataset=False):
    if single_dataset:
        sides = (0,0)
    else:
        sides = (0,1)
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
        rnames = parseRowsNames(csv_data["ids"])
    else:
        rnames = [Term.pattVName % n for n in range(N)]

    indices = [dict([(v,k) for (k,v) in enumerate(csv_data['data'][sides[0]]["order"])]),
               dict([(v,k) for (k,v) in enumerate(csv_data['data'][sides[1]]["order"])])]
    disabled_rows = set()

    for er in csv_reader.ENABLED_ROWS:
        for side in set(sides):
            if er in csv_data['data'][side]["headers"]:
                csv_data['data'][side]["headers"].remove(er)
                tmp = csv_data['data'][side]["data"].pop(er)
                if type(tmp) is dict:
                    tmp = tmp.items()
                else:
                    tmp = enumerate(tmp)
                for i,v in tmp:
                    if not Data.enabled_codes_rev_simple[v]:
                        disabled_rows.add(indices[side][i])
    for sito, side in enumerate(sides):
        for name, det in [parseColumnName(header, types_smap) for header in csv_data['data'][side]["headers"]]:
            if len(name) == 0:
                continue
            values = csv_data['data'][side]["data"][name]
            col = None

            if Data.all_types_map.get(csv_data['data'][side]['type_all']) is not None:
                col = Data.all_types_map[csv_data['data'][side]['type_all']].parseList(values, indices[side], force=True)
                if col is None:
                    print "DID NOT MANAGE FORCE PARSING..."
            if col is None:
                if "type" in det:
                    col = det["type"].parseList(values, indices[side])
                else:
                    type_ids = list(type_ids_org)
                    # if sito == 1 and len(cols[sito]) == 2:
                    #      pdb.set_trace()
                    while col is None and len(type_ids) >= 1:
                        col = type_ids.pop().parseList(values, indices[side])

            if col is not None and col.N == N:
                if not det.get("enabled", True) or \
                       (csv_data["data"][side][csv_reader.ENABLED_COLS[0]] is not None \
                        and not Data.enabled_codes_rev_double.get(csv_data["data"][side][csv_reader.ENABLED_COLS[0]].get(name, None), (1,1))[sito] ):
                    col.flipEnabled()
                addCol(cols, col, sito, det.get("name", name))
            else:
                pdb.set_trace()
                raise DataError('Unrecognized variable type!')            
    return (cols, N, coords, rnames, disabled_rows)

# def getDenseArray(vect):
#     if type(vect) is dict:
#         tmp = [0 for i in range(max(vect.keys())+1)]
#         for i, v in vect.items():
#             if i != -1:
#                 tmp[i] = v
#         return np.array([tmp])
#         # vs, ijs = zip(*[(v, (i,0)) for (i,v) in vect.items() if i != -1])
#         # return scipy.sparse.csc_matrix((np.array(vs),np.array(ijs).T)).todense().T
#     else:
#         return np.array([vect])




def main():

    # rep = "/home/galbrun/TKTL/redescriptors/generaliz/data/"
    # # data = Data([rep+"top_plstats_0.csv", rep+"top_btstats_0.csv", {}, "NA"], "csv")
    # data = Data([rep+"mammals_points.csv", rep+"worldclim_tp_points.csv", {}, ""], "csv")
    # data.writeCSV(["/home/galbrun/testoutL.csv", "/home/galbrun/testoutR.csv"])
    # data2 = Data(["/home/galbrun/testoutL.csv", "/home/galbrun/testoutR.csv", {}, ""], "csv")
    # print data, data2
    # exit()

    # subsets_rids = data.rsubsets_split(10, 0, 10.)
    # for si, subset in enumerate(subsets_rids):
    #     sL, sT = data.get_LTsplit(subset)
    #     print "Train:", sL, "Test:", sT
    # exit()


    rep = "/home/galbrun/TKTL/redescriptors/data/rajapaja/"
    # data = Data([rep+"mammals_poly.csv", rep+"worldclim_poly.csv"], "csv")
    data = Data([rep+"mammals.csv", rep+"worldclim.csv"], "csv")
    print data
    print data.getCoordPoints().shape
    # subsets =
    data.getSplit(nbsubs=5, coo_dim=19, grain=1.)
    data.addFoldsCol()
    data.getSplit(nbsubs=10, coo_dim=-1, grain=10.)
    data.addFoldsCol()
    data.getSplit(nbsubs=4, coo_dim=-2, grain=10.)
    data.addFoldsCol()
    print data.findCandsFolds()
    pdb.set_trace()
    splits = data.extractFolds(1, 69)    

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

