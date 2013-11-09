
import os.path
import numpy as np
import scipy.sparse
import codecs, re
from itertools import chain

from classQuery import Op, Term, BoolTerm, CatTerm, NumTerm, Literal, Query 
from classRedescription import Redescription
from classSParts import SParts
from toolICList import ICList
import toolRead, csv_reader
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

    def isDense(self):
        return True

    def getName(self, details=None):
        if self.name is not None:
            return self.name
        else:
            return "%d" % self.getId()

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
        return np.nan 

    def getVector(self):
        if self.vect is None:
            v = self.numEquiv(False)
            self.vect = [v for i in range(self.N)]
            for n in self.missing:
                self.vect[n] = self.numEquiv("-")
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

    def fromXML(self, node):
        self.name = toolRead.getTagData(node, "name")
        self.N = toolRead.getTagData(node, "nb_entities", int)
        tmp_en = toolRead.getTagData(node, "status_enabled", int)
        if tmp_en is not None:
            self.enabled = tmp_en
        tmpm = toolRead.getTagData(node, "missing")
        if tmpm is not None:
            self.missing = set(map(int, re.split(Data.separator_str, tmpm.strip())))

    def toXML(self):
        strd = "<variable>\n"
        strd += "\t<name><![CDATA[\"%s\"]]></name>\n" % self.getName()
        strd += "\t<type_id>%d</type_id>\n" % self.type_id
        strd += "\t<nb_entities>%d</nb_entities>\n" % self.N
        strd += "\t<status_enabled>%d</status_enabled>\n" % self.enabled
        strd += self.typespec_placeholder + "\n"

        if self.missing is not None and len(self.missing) > 0:
            strd += "\t<missing>" + ",".join(map(str,self.missing)) +"</missing>\n"
        strd += "</variable>\n"
        return strd

class BoolColM(ColM):
    type_id = BoolTerm.type_id
    width = -1

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
        for i,j in indices.items():
            vt = listV[i]
            if vt is None:
                miss.add(j)
            else:
                v = vt.lower()
                if v not in BoolColM.values:
                    return None
                elif BoolColM.values[v]:
                    trues.add(j)
        return BoolColM(trues, max(indices.values())+1, miss)
    parseList = staticmethod(parseList)

    def getTerm(self):
        return BoolTerm(self.id)

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
            return np.nan

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
            return "%1.4f" % (float(self.lTrue())/self.N)
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


    def fromXML(self, node):
        ColM.fromXML(self, node)
        tmp_txt = toolRead.getTagData(node, "rows")
        if tmp_txt is not None and len(tmp_txt.strip()) > 0:
            self.hold = set(map(int, re.split(Data.separator_str, tmp_txt.strip())))
        self.missing -= self.hold

    def toXML(self):
        tmpl = ColM.toXML(self)
        strd = "\t<rows>" + ",".join(map(str, self.hold)) +"</rows>\n"
        return tmpl.replace(self.typespec_placeholder, strd)
    
    def getValue(self, rid):
        # self.getVector()
        if self.vect is None:
            if rid in self.missing:
                return "-"
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
        for i,j in indices.items():
            v = listV[i]
            if v is None:
                miss.add(j)
            # elif re.match(CatColM.n_patt, v):
            #     return None
            else:
                if cats.has_key(v):
                    cats[v].add(j)
                else:
                    cats[v] = set([j])
        if len(cats) > 1:
            return CatColM(cats, max(indices.values())+1, miss)
        else:
            return None
    parseList = staticmethod(parseList)

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
                if not sums_rows[i].has_key(cat):
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
            return "-"

    def getNumValue(self, rid):
        if self.vect is None:
            self.getVector()
        if rid < len(self.vect):
            return self.vect[rid]
        else:
            return "-"


    def numEquiv(self, v):
        try:
            return sorted(self.sCats.keys()).index(v)
        except:
            return np.nan

    def getVector(self):
        if self.vect is None:
            self.vect = super(CatColM, self).getVector()
            self.vvals = ["-" for i in range(self.N)]
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

    def toXML(self):
        tmpl = ColM.toXML(self)
        rows = []
        for cat, cat_supp in self.sCats.items():
            rows.extend([(row, "%s" % cat) for row in cat_supp])
        rows.sort(key=lambda x:x[0])
        strd = "\t\t<values>" + ",".join([row[1] for row in rows]) +"</values>\n"
        return tmpl.replace(self.typespec_placeholder, strd)

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
    
class NumColM(ColM):
    type_id = NumTerm.type_id
    width = 0

    p_patt = "^-?\d+(?P<dec>(\.\d+)?)$"
    def parseVal(v, j, vals, miss=set(), prec=None, exclude=False, matchMiss=False):
        if matchMiss is not False and v == matchMiss:
            miss.add(j)
            return v, prec
        else:
            tmatch = re.match(NumColM.p_patt, v)
            if not tmatch:
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
        for i,j in indices.items():
            val, prec = NumColM.parseVal(listV[i], j, vals, miss, prec, matchMiss=None)
        if len(vals) > 0 and len(vals) + len(miss) == N:
            return NumColM(vals, N, miss, prec)
        else:
            return None
    parseList = staticmethod(parseList)
    
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
        return np.nan 

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
                    self.vect[-1] = self.numEquiv("-")
                ### Make sure can recover the length
                for n in self.missing:
                    self.vect[n] = self.numEquiv("-")
                ## make sure we recover full length
                if not self.vect.has_key(self.nbRows()-1): 
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
        if len(self.sVals)+len(self.missing) > 0 and len(self.sVals)+len(self.missing) != self.N :
            ## gather row ids for which
            if len(self.sVals) > 0:
                rids = set(zip(*self.sVals)[1])
            else:
                rids = set()
            if len(rids) != len(self.sVals):
                raise DataError("Error reading real values, multiple values for a row!")
            rids.discard(-1)
            if 2*len(rids) > self.N:
                self.mode = (-1, set(range(self.N)) - rids - self.missing)
            else:
                self.mode = (1, rids)
        else:
            self.mode = (0, None)

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

    def isDense(self):
        return self.mode[0] == 0

    def toXML(self):
        tmpl = ColM.toXML(self)
        strd = ""
        if self.isDense():
            val_f = "%."+ ("%d" % self.getPrec()) +"f"
            strd += "\t<store_type>dense</store_type>\n"
            strd += "\t\t<values>" + ",".join([val_f % val for val, row_id in sorted(self.sVals, key = lambda x: x[1])]) +"</values>\n"
        else:
            val_f = "%d:%."+ ("%d" % self.getPrec()) +"f"
            strd += "\t<store_type>sparse</store_type>\n"
            strd += "\t\t<values>" + ",".join([val_f % (row_id, val) for val, row_id in sorted(self.sVals, key = lambda x: x[1])]) +"</values>\n"
            # for val, row_id in self.sVals:
            #     strd += "\t\t<entity><row>%d</row><value>%s</value></entity>\n" % (row_id, val)
        return tmpl.replace(self.typespec_placeholder, strd)

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

    def makeSegments(self, side, supports, ops =[False, True]):
        supports.makeVectorABCD()
        segments = [[[self.sVals[0][0], None, SParts.makeLParts()]], [[self.sVals[0][0], None, SParts.makeLParts()]]]
        current_valseg = [[self.sVals[0][0], self.sVals[0][0], SParts.makeLParts()], [self.sVals[0][0], self.sVals[0][0], SParts.makeLParts()]]
        for (val, row) in self.sVals+[(None, None)]:
            tmp_lparts = supports.lpartsRow(row, self)

            for op in ops:
                if val is not None and SParts.sumPartsId(side, SParts.IDS_varnum[op], tmp_lparts) + SParts.sumPartsId(side, SParts.IDS_varden[op], tmp_lparts) == 0:
                    continue
                if val is not None and val == current_valseg[op][0]: 
                    current_valseg[op][2] = SParts.addition(current_valseg[op][2], tmp_lparts)
                else:
                    tmp_pushadd = SParts.addition(segments[op][-1][2], current_valseg[op][2]) 
                    if segments[op][-1][1]==None or SParts.sumPartsId(side, SParts.IDS_varnum[op], tmp_pushadd)*SParts.sumPartsId(side, SParts.IDS_varden[op], tmp_pushadd) == 0:
                        segments[op][-1][2] = tmp_pushadd
                        segments[op][-1][1] = current_valseg[op][1]
                    else:
                        segments[op].append(current_valseg[op])
                    current_valseg[op] = [val, val, SParts.addition(SParts.makeLParts(),tmp_lparts)]
        return segments


    def makeSegmentsColors(self, side, supports, ops =[False, True]):
        supports.makeVectorABCD()

        partids = [[SParts.partId(SParts.gamma, side), SParts.partId(SParts.alpha, side)], \
                   [SParts.partId(SParts.beta, side), SParts.partId(SParts.delta, side)]]
        
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

class Data:

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
                if N == "multiple":
                    self.cols, self.N, self.coords, self.rnames, self.single_dataset = readDNCFromMulFiles(cols)
                elif N == "csv":
                    self.cols, self.N, self.coords, self.rnames, self.single_dataset = readDNCFromCSVFiles(cols)
                elif N == "xml":
                    self.cols, self.N, self.coords, self.rnames, self.single_dataset = readDNCFromXMLFile(cols)

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
        if self.hasMissing():
            SParts.resetPartsIds("grounded")
        else:
            SParts.resetPartsIds("none")

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

    def toXML(self):
        ########## XML DATA
        strd = "<data>\n"
        strd += "\t<nb_entities>%d</nb_entities>\n" % self.N
        sides = [0,1]
        if self.single_dataset:
            strd += "\t<single_dataset>1</single_dataset>\n"
            sides = [0]
        for side in sides:
            strd += "\t<side>\n"
            strd += "\t<name>%d</name>\n" % side
            strd += "\t<nb_variables>%d</nb_variables>\n" % len(self.cols[side])
            for col in self.cols[side]:
                strd += col.toXML().replace("\n", "\n\t")
            strd += "\t</side>\n"
        if self.isGeospatial():
            strd += "\t<coordinates>\n"
            for coord in self.coords:
                strd += "\t\t<coordinate>\n"
                strd += "\t\t\t<values>" + ",".join(map(str, coord)) +"</values>\n"
                strd += "\t\t</coordinate>\n"
            strd += "\t</coordinates>\n"
        strd += "</data>"
        return strd

    def writeXML(self, output):
        output.write("<root>\n")
        output.write("<data>\n")
        output.write("\t<nb_entities>%d</nb_entities>\n" % self.N)
        sides = [0,1]
        if self.single_dataset:
            output.write("\t<single_dataset>1</single_dataset>\n")
            sides = [0]
        for side in sides:
            output.write("\t<side>\n")
            output.write("\t<name>%d</name>\n" % side)
            output.write("\t<nb_variables>%d</nb_variables>\n"% len(self.cols[side]) ) 
            for col in self.cols[side]:
                output.write(col.toXML().replace("\n", "\n\t"))
            output.write("\t</side>\n")
        if self.isGeospatial():
            output.write("\t<coordinates>\n")
            for coord in self.coords:
                output.write("\t\t<coordinate>\n")
                output.write("\t\t\t<values>" + ",".join([":".join(map(str, cs)) for cs in coord]) +"</values>\n")
                output.write("\t\t</coordinate>\n")
            output.write("\t</coordinates>\n")
        if self.rnames is not None:
            output.write("\t<rnames>\n")
            for rname in self.rnames:
                output.write("\t\t\t<rname>%s</rname>\n" % rname)
            output.write("\t</rnames>\n")
        output.write("</data>\n")
        output.write("</root>")
        
    def write(self, output):
        self.writeXML(output)
        
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
            raise DataError('Data error reading csv %s' % arg)
        cols, N, coords, rnames = parseDNCFromCSVData(tmp_data)
    return cols, N, coords, rnames, single_dataset

def parseDNCFromCSVData(csv_data):
    cols = [[],[]]
    coords = None
    single_dataset = False
    if csv_data.get("coord", None) is not None:
        try:
            tmp = zip(*csv_data["coord"])
            coords = np.array([tmp[1], tmp[0]])
        except Exception:
            coords = None
        
    for side in [0,1]:
        indices = dict([(v,k) for (k,v) in enumerate(csv_data['data'][side]["order"])])
        N = len(indices)
        for name in csv_data['data'][side]["headers"]:
            if len(name) == 0:
                continue
            values = csv_data['data'][side]["data"][name]
            col = None
            type_ids = [CatColM, NumColM, BoolColM]
            while col is None and len(type_ids) >= 1:
                col = type_ids.pop().parseList(values, indices)

            if col is not None and col.N == N:
                col.setId(len(cols[side]))
                col.side = side
                col.name = name
                cols[side].append(col)
            else:
                raise DataError('Unrecognized variable type!')
    if csv_data.get("ids", None) is not None and len(csv_data["ids"]) == N:
        rnames = csv_data["ids"]
    else:
        rnames = range(N)
    return (cols, N, coords, rnames)

def readDNCFromXMLFile(filename):
    (cols, N, coord, rnames) = ([[],[]], 0, None, None)
    single_dataset = False
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
    return (cols, N, coord, rnames, single_dataset)

def readDNCFromMulFiles(filenames):
    cols, N, coords, rnames = [[],[]], 0, None, None
    single_dataset = False
    if len(filenames) >= 2:
        (cols, N) = readVariables(filenames[:2])
        single_dataset = (filenames[0] == filenames[0])
        if len(filenames) >=5  and filenames[4] is not None:
            coords = readCoords(filenames[4])
            if coords is not None and coords.shape[1] != N:
                coords = None
        if len(filenames) >=6  and filenames[5] is not None:
            rnames = readRNames(filenames[5])
            if rnames is not None and len(rnames) != N:
                rnames = None

        names_filenames = [None, None]
        extension = ".names"
        if len(filenames) == 3:
            extension = filenames[2]
        elif len(filenames) >= 4:
            if filenames[3] is None and filenames[2] is not None:
                extension = filenames[2]

            else:
                for side in [0,1]:
                    if filenames[2+side] is not None and os.path.exists(filenames[2+side]):
                        names_filenames[side] = filenames[2+side]

        for side in [0,1]:
            if names_filenames[side] is None:
                filename = filenames[side]
                filename_parts = filename.split('.')
                filename_parts.pop()
                names_filename = '.'.join(filename_parts) + extension
                if os.path.exists(names_filename):
                    names_filenames[side] = names_filename

            if names_filenames[side] is not None:
                tmp_names = readNamesSide(names_filenames[side])
                if len(tmp_names) == len(cols[side]):
                    for i in range(len(cols[side])):
                        cols[side][i].name = tmp_names[i]
                else:
                    print "Number of names does not match number of variables on side %d." % side
    return (cols, N, coords, rnames, single_dataset)
        
def readCoords(filename):
    coord = [[], []]
    with open(filename) as f:
        for line in f:
            parts = line.strip().split(" ")
            if len(parts)==2:
                for c in [0,1]:
                    coord[c].append(map(float, parts[c].strip(" :").split(":")))
            else:
                tmp = zip(*[map(float, p.split(",")) for p in parts])
                for c in [0,1]:
                    coord[c].append(tmp[c])
            if len(coord[0][-1]) != len(coord[1][-1]):
                return None
    return np.array(coord) 

def readRNames(filename):
    rnames = None
    with open(filename) as f:
        rnames = [line.strip() for line in f]
    return rnames

def readNamesSide(filename):
    a = []
    if type(filename) in [unicode, str]:
        f = codecs.open(filename, encoding='utf-8', mode='r')
    else: ## Assume it's a file
        f = filename
    for line in f:
        a.append(line.strip())
    return a

def readVariables(filenames):
    data = []; nbRowsT = None;
    for side, filename in enumerate(filenames):
        (cols, nbRows, nbCols) = readMatrix(filename, side)
        if len(cols) != nbCols:
            raise DataError('Matrix in %s does not have the expected number of variables !' % filename)

        else:
            if nbRowsT is None:
                nbRowsT = nbRows
            if nbRowsT == nbRows:
                for cid, col in enumerate(cols):
                    col.id = cid
                    col.side = side
                data.append(cols)
            else:
                raise DataError('All matrices do not have the same number of entities (%i ~ %i)!' % (nbRowsT, nbRows))            
    return (data, nbRows)

def readMatrix(filename, side = None):
    ## Read input
    nbRows = None
    if isinstance(filename, file):
        f = filename
        filename = f.name
    else:
        f = open(filename, 'r')

    filename_parts = filename.split('.')
    type_all = filename_parts.pop()
    nbRows = None
    nbCols = None
    
    if len(type_all) >= 3 and (type_all[0:3] == 'mix' or type_all[0:3] == 'spa'):  
        row = f.next()
        a = re.split(Data.separator_str, row)
        nbRows = int(a[0])
        nbCols = int(a[1])
    try:
        if len(type_all) >= 3 and type_all[0:3] == 'spa':
            method_parse =  eval('parseCell%s' % (type_all.capitalize()))
            method_prepare = eval('prepare%s' % (type_all.capitalize()))
            method_finish = eval('finish%s' % (type_all.capitalize()))
        elif len(type_all) >= 3 and type_all[0:3] == 'dat':
            method_parse =  eval('parseVarDatAll')
            method_prepare = eval('preparePerRow')
            method_finish = eval('finishVar%s' % (type_all.capitalize()))
        else:
            method_parse =  eval('parseVar%s' % (type_all.capitalize()))
            method_prepare = eval('preparePerRow')
            method_finish = eval('finishPerRow')

    except NameError as detail:
        raise DataError("Could not find correct data reader! (%s)" % detail)
    try:
        tmpCols = method_prepare(nbRows, nbCols)
        
        # print "Reading input data %s (%s)"% (filename, type_all)
        for row in f:
            if  len(type_all) >= 3 and type_all[0:3] == 'den' and nbRows is None:
                nbRows = len(re.split(Data.separator_str, row))
            method_parse(tmpCols, re.split(Data.separator_str, row.strip()), nbRows, nbCols)

        ## print "Done with reading input data %s (%i x %i %s)"% (filename, nbRows, len(tmpCols), type_all)
        cols, nbRows, nbCols = method_finish(tmpCols, nbRows, nbCols)
    except DataError:
        raise
    except (AttributeError, ValueError, StopIteration) as detail:
        raise DataError("Problem with the data format while reading (%s)" % detail)
    except:
        raise
    return (cols, nbRows, nbCols)
    
def preparePerRow(nbRows, nbCols):
    return []

def parseVarMix(tmpCols, a, nbRows, nbCols):
    name = a.pop(0)
    type_row = a.pop(0)
    if type_row[0:3] == 'dat':
        raise DataError('Oups this row format is not allowed for mixed datat (%s)!' % (type_row))
    try:
        method_parse =  eval('parseVar%s' % (type_row.capitalize()))
    except AttributeError:
        raise DataError('Oups this row format does not exist (%s)!' % (type_row))
    method_parse(tmpCols, a, nbRows, nbCols)

def finishPerRow(tmpCols, nbRows, nbCols):
    ## Todo: check number of rows and cols?
    return tmpCols, nbRows, len(tmpCols)

def prepareSparsenum(nbRows, nbCols):
    return [[[(0, -1)], set(), 0] for i in range(nbCols)]

def parseCellSparsenum(tmpCols, a, nbRows, nbCols):
    id_row = int(a[0])-1
    id_col = int(a[1])-1
    if id_col >= nbCols or id_row >= nbRows:
        raise DataError('Outside expected columns and rows (%i,%i)' % (id_col, id_row))
    else :
        val, tmpCols[id_col][2] = NumColM.parseVal(a[2], id_row, tmpCols[id_col][0], tmpCols[id_col][1], tmpCols[id_col][2], exclude=0)

            
def finishSparsenum(tmpCols, nbRows, nbCols):
    return [NumColM(tmpCols[col][0], nbRows, tmpCols[col][1], tmpCols[col][2]) for col in range(len(tmpCols))], nbRows, nbCols

def prepareSparsebool(nbRows, nbCols):
    return [[set(), set()] for i in range(nbCols)]

def parseCellSparsebool(tmpCols, a, nbRows, nbCols):
    id_row = int(a[0])-1
    id_col = int(a[1])-1
    if id_col >= nbCols or id_row >= nbRows:
        raise DataError('Outside expected columns and rows (%i,%i)' % (id_col, id_row))
    else :
        try:
            val = float(a[2])
            if val != 0:
                tmpCols[id_col][0].add(id_row)
        except ValueError:
            tmpCols[id_col][1].add(id_row)
        
def finishSparsebool(tmpCols, nbRows, nbCols):
    return [BoolColM(tmpCols[col][0], nbRows, tmpCols[col][1]) for col in range(len(tmpCols))], nbRows, nbCols

def parseVarDensenum(tmpCols, a, nbRows, nbCols):
    prec = None
    if len(a) == nbRows:
        tmp = []
        miss = set()
        for i in range(len(a)):
            val, prec = NumColM.parseVal(a[i], i, tmp, miss, prec)
                
        tmp.sort(key=lambda x: x[0])
        tmpCols.append(NumColM(tmp, nbRows, miss, prec))
    else:
        raise DataError('Number of rows does not match (%i ~ %i)' % (nbRows,len(a)))
                    
def parseVarDensecat(tmpCols, a, nbRows, nbCols):
    if len(a) == nbRows:
        tmp = {}
        miss = set()
        for i in range(len(a)):
            try:
                cat = float(a[i])
                if tmp.has_key(cat):
                    tmp[cat].add(i)
                else:
                    tmp[cat] = set([i])
            except ValueError:
                miss.add(i) 
        tmpCols.append(CatColM(tmp, nbRows, miss))
    else:
        raise DataError('Number of rows does not match (%i ~ %i)' % (nbRows,len(a)))

def parseVarDensebool(tmpCols, a, nbRows, nbCols):
    if len(a) == nbRows:
        tmp = set()
        miss = set()
        for i in range(len(a)):
            try:
                val = float(a[i])
                if val != 0: tmp.add(i)
            except ValueError:
                miss.add(i) 
        tmpCols.append(BoolColM(tmp, nbRows, miss))
    else:
        raise DataError('Number of rows does not match (%i ~ %i)' % (nbRows,len(a)))
             
def parseVarDatAll(tmpCols, a, nbRows, nbCols):
    tmpCols.append(set(map(int, a)))

def finishVarDatbool(tmpCols, nbRows, nbCols):
    nbRows = max([max(tmp) for tmp in tmpCols])+1    
    return [BoolColM(col, nbRows+1) for col in tmpCols], nbRows, len(tmpCols)  

def finishVarDat(tmpOCols, nbORows, nbOCols):
    ### Each line contains one transaction
    ## transpose
    nbRows = len(tmpOCols)
    nbCols = max([max(tmp) for tmp in tmpOCols])+1

    tmpCols = [set() for i in range(nbCols)]
    for ri, row in enumerate(tmpOCols):
        for i in row:
            tmpCols[i].add(ri)
    return [BoolColM(col, nbRows) for col in tmpCols], nbRows, len(tmpCols)  

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
    print "UNCOMMENT"
    # rep = "/home/galbrun/redescriptors/data/vaalikone/"
    # data = Data([rep+"vaalikone_profiles_miss.csv", rep+"vaalikone_questions_miss.csv", {}, "NA"], "csv")
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

