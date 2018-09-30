import os.path, time, copy
import numpy
import codecs, re

from toolRead import BOOL_MAP
from classContent import Item
from classQuery import Op, Term, AnonTerm, BoolTerm, CatTerm, NumTerm, Literal
import pdb

NA_num  = numpy.nan
NA_bool  = -1
NA_cat  = -1

NA_str_c = "nan"

MODE_VALUE = 0

def associate_term_class(col_class, term_class=None):
    col_class.assoc_term = term_class
    if term_class is not None:
        col_class.type_id = term_class.type_id
        col_class.type_letter = term_class.type_letter
        col_class.type_name = term_class.type_name        

def valToTimeStr(val):
    try:
        return time.ctime(val)
    except:
        return NA_str_c

def getValSpec(param, i):
    out = param
    if type(param) is list:
       out = param[i]
    elif type(param) is dict:
        if i in param:
            out = param[i]
        elif None in param:
            out = param[None]
    return out
    
class DataError(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)

class ColM(Item):

    width = 0
    typespec_placeholder = "<!-- TYPE_SPECIFIC -->"
    NA = NA_bool
    NA_specimen_str = ["na", "nan", "-", "-1"]
    anon_term = AnonTerm
    
    @classmethod
    def getAnonTermClass(tcl):
        return tcl.anon_term
    
    @classmethod
    def getAssocTermClass(tcl):
        return tcl.assoc_term
    
    @classmethod
    def initSums(tcl, N):
        return [0 for i in range(N)]

    @classmethod
    def parseList(tcl, list):
        return None

    @classmethod
    def fromVect(tcl, vect_data, prec=None, enabled=True):
        return None
    
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
        self.gid = -1
        self.extras = {}
        
    def getUid(self):
        return (self.side, self.id)
    def setUid(self, iid=None):
        raise Warning("Col UID is ready-only!")
    def setSideIdName(self, side, cid, name=None):
        self.setId(cid)
        self.side = side
        if name is None:
            self.name = Term.pattVName % cid
        else:
            self.name = name

    #### TODO IMPLEMENT
    # def getFieldV(self, field="uid", details={}):
    #     if field == "uid":
    #         return self.getUid()
    #     return None

        
    def setExtra(self, key, val):
        self.extras[key] = val
    def getExtra(self, key=None):
        if key is None:
            return self.extras
        return self.extras.get(key)
    def copyExtras(self):
        return copy.deepcopy(self.extras)
    def computeExtras(self, data, extras=None, details=None):
        self.extras.update(data.computeExtras(self, extras, details))
    
    def simpleBool(self):
        return False
                
    def nbRows(self):
        return self.N

    def rows(self):
        return set(range(self.N))

    def setGroupId(self, gid=-1):
        self.gid = gid
    def getGroupId(self):
        return self.gid
    def hasGroup(self):
        return self.gid > -1
    
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
            return NA_str_c 
        return val
    
    def areDataEquiv(self, vA, vB):
        return vA == vB
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

    def getAnonTerm(self):
        return self.getAnonTermClass()(self.getId(), self.typeId())
    
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
        self.vect = numpy.ones(self.N, dtype=numpy.int)*self.NA
        
    def getVector(self, bincats=False, nans=None):
        if self.vect is None:
            self.mkVector()
        if self.hasMissing() and nans is not None and \
               not ( (numpy.isnan(nans) and numpy.isnan(self.NA)) or nans == self.NA): ## Not the same nan...
            tmp = numpy.array(self.vect, dtype=numpy.float, copy=True)
            tmp[tmp==self.NA] = nans
            return tmp
        return self.vect

    def getSortAble(self, details=None):
        if details.get("aim") == "sort":
            return (self.enabled, self.getId())
        return ""
    def getType(self, details=None):
        return self.type_name
    def getDensity(self, details=None):
        return "-"
    def getCategories(self, details=None):
        return "-"
    def getMin(self, details=None):
        return "-"
    def getMax(self, details=None):
        return "-"
    def getMissInfo(self, details=None):
        return "%1.2f%%: %d"% (self.nbMissing()/float(self.N), self.nbMissing())
    def getRange(self):
        return []
    # def getCohesion(self, details=None):
    #     return "%1.4f" % self.cohesion
 

    def typeId(self):
        return self.type_id
    def miss(self):
        return self.missing
    def negSuppTerm(self, term):
        return self.rows() - self.suppTerm(term) - self.miss()
       
    def suppLiteral(self, literal): #TODO:literal has a time constraint added!
        if isinstance(literal, Term): ### It's a term, not a literal
            return self.suppTerm(literal)
        elif isinstance(literal, Literal):
            if literal.isNeg():
                return self.negSuppTerm(literal.getTerm())
            else:
                return self.suppTerm(literal.getTerm())

    def lMiss(self):
        return len(self.miss())
    
    def lNegSuppTerm(self, term):
        return self.nbRows() - len(self.suppTerm(term)) - self.lMiss()

    def lSuppLiteral(self, literal):
        if isinstance(literal, Term): ### It's a literal, not a term
            return len(self.suppTerm(literal))
        elif isinstance(literal, Literal):
            if literal.isNeg():
                return self.lNegSuppTerm(literal.getTerm())
            else:
                return len(self.suppTerm(literal.getTerm()))

    def getEnabled(self, details=None):
        return self.enabled
    def isEnabled(self, details=None):
        return self.getEnabled() > 0

    def flipEnabled(self):
        self.enabled = 1-self.enabled

    def setEnabled(self):
        self.enabled = 1
    def setDisabled(self):
        self.enabled = 0

    def __str__(self):
        act = ""
        if not self.isEnabled():
            act = " (OFF)"
        if self.hasGroup():
            act += " [gid=%d]" % self.getGroupId()
        return "%s variable %i %s%s, %d missing values" %(self.getType(), self.getId(), self.getName().encode('ascii', 'replace'), act, self.lMiss())

    def suppInBounds(self, min_in=-1, min_out=-1):
        return (self.infofull["in"][1] and self.infofull["out"][1]) 

    def usable(self, min_in=-1, min_out=-1, checkable=True):
        return self.suppInBounds(min_in, min_out) and (not checkable or self.isEnabled())
associate_term_class(ColM, Term)
    
class BoolColM(ColM):
    width = -1
    values_eq = {True:1, False:0}
    NA = NA_bool

    values = BOOL_MAP
    
    @classmethod
    def parseList(tcl, listV, indices=None, force=False):
        miss = set()
        if force:
            if type(listV) is list:
                miss = set([i for (i, v) in enumerate(listV) if v is None])
                listV = set([i for (i, v) in enumerate(listV) if v is not None and BoolColM.values.get(v.lower(), True)])
            elif type(listV) is not set:
                tt = set()
                ok = True
                for idx, v in listV.items():
                    try:
                        if float(v) != 0:
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
                miss = set([indices.get(i,None) for i in miss])
                miss.discard(None)
                N = max(indices.values())+1
            else:
                raise ValueError('Sparse requires indices')
            return BoolColM(trues, N, miss)
        if indices is None:
            indices = dict([(v,v) for v in range(len(listV))])
        trues = set()
        miss = set()
        if type(listV) is dict:
            ttt = set(listV.keys()).intersection(indices.keys())
        else:
            ttt = [i for i in indices.keys() if i < len(listV)]

        val_nonbool = set([listV[i].lower() for i in ttt if listV[i] is not None]).difference(BoolColM.values.keys())
        val_na = val_nonbool.intersection(BoolColM.NA_specimen_str)
        na_v = BoolColM.NA
        if len(val_na) == 1:
            na_v = val_na.pop()
        elif len(val_nonbool) > 0:
            return None
            
        for i in ttt:
            j = indices[i]
            if listV[i] is None or listV[i].lower() == na_v:
                miss.add(j)
            else:
                v = listV[i].lower()
                if v not in BoolColM.values:
                    return None
                elif BoolColM.values[v]:
                    trues.add(j)
        return BoolColM(trues, max(indices.values())+1, miss)

    @classmethod
    def fromVect(tcl, vect_data, prec=None, enabled=True):
        tmp = vect_data
        if prec is not None:
            tmp = numpy.around(tmp, prec)

        col = tcl(set([i for (i,v) in enumerate(tmp) if v != 0]), len(tmp))
        if not enabled:
            col.flipEnabled()
        return col
    
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
        if self.N == self.nbMissing():
            return 0.0
        else:
            return self.sumCol()/float(self.N-self.nbMissing())

    def minGap(self):
        return 1.
    
    def getInitTerms(self, minIn=0, minOut=0):
        if self.sumCol() >= minIn and self.N-(self.sumCol()+self.nbMissing()) >= minOut:
            return [(self.getAssocTermClass()(self.getId()), self.sumCol())]
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
        self.vect = numpy.ones(self.N, dtype=numpy.int)*self.numEquiv(False)
        self.vect[list(self.missing)] = self.NA
        self.vect[list(self.hold)] = self.numEquiv(True)

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
    
    def getValue(self, rid, pref=None):
        if self.vect is None:
            if rid in self.missing:
                return self.NA

            if pref == "bnum":
                return int(rid in self.hold)
            return rid in self.hold
        else:
            if pref == "bnum":
                return self.vect[rid]
            return BoolColM.values.get(self.vect[rid], self.NA)

    def getNumValue(self, rid):
        return int(self.getValue(rid))

    def getCatFromNum(self, n):
        return n == 1

    def supp(self):
        return self.hold
    
    def suppTerm(self, term):
        if term.isAnon():
            return set()
        return set(self.hold)

    def lTrue(self):
        return self.sumCol()

    def lFalse(self):
        return self.nbRows() - self.lTrue() - self.lMiss()

    def suppInBounds(self, min_in=-1, min_out=-1):
        if self.infofull["in"][0] != min_in:
            self.infofull["in"]= (min_in, self.lTrue() >= min_in)
        if self.infofull["out"][0] != min_out:
            self.infofull["out"]= (min_out, self.lFalse() >= min_out)
        return (self.infofull["in"][1] and self.infofull["out"][1]) 
associate_term_class(BoolColM, BoolTerm)
    
class CatColM(ColM):
    width = 1
    NA =  NA_cat
    
    def makeCatLit(self, best_cat, neg, allw_neg=True):
        if type(best_cat) in [list, set]:
            dc = set(self.cats()).difference(best_cat)                
            if allw_neg and (len(dc) < len(best_cat)):
                return Literal(not neg, self.getAssocTermClass()(self.getId(), dc))
            else:
                return Literal(neg, self.getAssocTermClass()(self.getId(), set(best_cat)))
        return Literal(neg, self.getAssocTermClass()(self.getId(), best_cat))
            
    def __init__(self, ncolSupp={}, N=-1, nmiss= set()):
        ColM.__init__(self, N, nmiss)
        self.sCats = ncolSupp
        self.ord_cats = sorted(self.sCats.keys())
        self.cards = sorted([(cat, len(self.suppCat(cat))) for cat in self.cats()], key=lambda x: x[1])

    @classmethod
    def initSums(tcl, N):
        return [{} for i in range(N)]

    @classmethod
    def parseList(tcl, listV, indices=None, force=False):
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
            if v is None or v == str(tcl.NA):
                miss.add(j)
            else:
                if v in cats:
                    cats[v].add(j)
                else:
                    cats[v] = set([j])
        if len(cats) > 0:
            if len(cats) == 1:
                print "Only one category %s, this is suspect!.." % (cats.keys())
            return tcl(cats, max(indices.values())+1, miss)
        else:
            return None

    @classmethod
    def fromVect(tcl, vect_data, prec=0, enabled=True):
        tmp = vect_data
        if prec is not None:
            tmp = numpy.around(tmp, prec)
        cats = {}
        for (j,v) in enumerate(tmp):
            if v in cats:
                cats[v].add(j)
            else:
                cats[v] = set([j])
            
        col = tcl(cats, N=len(tmp))
        if not enabled:
            col.flipEnabled()
        return col
    
    def toList(self, sparse=False, fill=False):
        if sparse:
            dt = [(i, NA_str_c) for i in self.missing]
            for cat, iis in self.sCats.items():
                dt.extend([(i, cat) for i in iis])
            return dt
        else:
            cat_dict = self.ord_cats + [NA_str_c]
            return [cat_dict[v] for v in self.getVector()]

    def mkVector(self):
        self.vect = numpy.ones(self.N, dtype=numpy.int)*self.numEquiv(self.NA)
        for v, cat in enumerate(self.ord_cats):
            self.vect[list(self.sCats[cat])] = v

    def getVector(self, bincats=False, nans=None):
        if bincats: ### binarize the categories, i.e return a matrix rather than vector
            vect = numpy.zeros((self.N, self.nbCats()), dtype=numpy.int)
            for v, cat in enumerate(self.ord_cats):
                vect[list(self.sCats[cat]), v] = 1
            return vect
        
        if self.vect is None:
            self.mkVector()
        if self.hasMissing() and nans is not None and \
               not ( (numpy.isnan(nans) and numpy.isnan(self.NA)) or nans == self.NA): ## Not the same nan...
            tmp = numpy.array(self.vect, dtype=numpy.float, copy=True)
            tmp[tmp==self.NA] = nans
            return tmp
        return self.vect

    def minGap(self):
        return 1
        
    def getInitTerms(self, minIn=0, minOut=0):
        terms = []
        for cat in self.cats():
            if len(self.sCats[cat]) >= minIn and self.N-(len(self.sCats[cat])+self.nbMissing()) >= minOut:
                terms.append((self.getAssocTermClass()(self.getId(), cat), len(self.sCats[cat])))
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
    
    def getCatForVal(self, v, missing_str=None):
        if v != self.NA:
            try:
                vint = int(v)
                return self.ord_cats[vint]
            except:
                pass
        if missing_str is not None:
            return missing_str
        return self.NA
        
    def getValue(self, rid, pref=None):
        if pref == "cnum":
            return self.getNumValue(rid)
        return self.getCatForVal(self.getNumValue(rid))

    def getNumValue(self, rid):
        if self.vect is None:
            self.getVector()
        if rid < len(self.vect):
            return self.vect[rid]
        else:
            return self.NA

    def numEquiv(self, v):
        if v == "#LOW#":
            return -0.5 # 0
        if v == "#HIGH#":
            return -0.5 # len(self.ord_cats)-1

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

    def iter_cats(self):
        return self.sCats.iteritems()
    def cats(self):
        return self.ord_cats
    def nbCats(self):
        return len(self.ord_cats)
    
    def suppCat(self, cat):
        supp = set()
        if type(cat) in [list, set]:
            cc = cat
        else:
            cc = [cat]
        for c in cc:
            supp.update(self.sCats.get(c, set()))
        return supp
            
    def suppTerm(self, term):
        if term.isAnon():
            return set()
        return self.suppCat(term.cat)

    def suppInBounds(self, min_in=-1, min_out=-1):
        if self.infofull["in"][0] != min_in:
            self.infofull["in"]= (min_in, (self.cards[-1][1] >= min_in or (self.nbRows() - self.cards[0][1]) >= min_in))
        if self.infofull["out"][0] != min_out:
            self.infofull["out"]= (min_out, (self.cards[-1][1] >= min_out or (self.nbRows() - self.cards[0][1]) >= min_out))
        return (self.infofull["in"][1] and self.infofull["out"][1]) 
associate_term_class(CatColM, CatTerm)
    
class NumColM(ColM):
    width = 0
    NA = NA_num

    p_patt = "^-?\d+(?P<dec>(\.\d+)?)$"
    # alt_patt = "^[+-]?\d+.?\d*(?:[Ee][-+]\d+)?$"
    alt_patt = "^[+-]?\d+\.?\d*(?:[Ee][-+]\d+)?$"
    prec_patt = "^-?\d+((?P<dec>\.\d+)|(e-(?P<epw>\d+)))?$"
    @classmethod
    def parseVal(tcl, v, j, vals, miss=set(), prec=None, exclude=False, matchMiss=False):
        if (matchMiss is not False and v == matchMiss) or v == str(tcl.NA):
            miss.add(j)
            return v, prec
        else:
            tmatch = re.match(tcl.p_patt, v)
            if not tmatch:
                atmatch = re.match(tcl.alt_patt, v)
                if not atmatch:
                    if matchMiss is False:
                        miss.add(j)
                    return v, prec
            else:
                pprec = 0
                mtch = re.match(tcl.prec_patt, str(float(v)))
                if mtch is not None:
                    if mtch.group("dec") is not None:
                        pprec = len(mtch.group("dec"))
                    elif mtch.group("epw") is not None:
                        pprec = int(mtch.group("epw"))
                if pprec > prec:
                    prec = pprec
                    
            val = float(v)
            if exclude is False or val != exclude:
                vals.append((val, j))
        return val, prec

    @classmethod
    def parseList(tcl, listV, indices=None, force=False):
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
            val, prec = tcl.parseVal(listV[i], j, vals, miss, prec, matchMiss=None)
        if len(vals) > 0 and (len(vals) + len(miss) == N or type(listV) is dict):
            return tcl(vals, N, miss, prec)
        elif force:
            # pdb.set_trace()
            return tcl(vals, N, miss, prec, force=True)
        else:
            return None

    @classmethod
    def fromVect(tcl, vect_data, prec=None, enabled=True):
        tmp = vect_data
        if prec is not None:
            tmp = numpy.around(tmp, prec)

        col = tcl([(v,i) for (i,v) in enumerate(tmp)], N=len(tmp), prec=prec)
        if not enabled:
            col.flipEnabled()
        return col
    
    def toList(self, sparse=False, fill=False):
        if self.isDense(): # and not self.hasMissing():
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
    
    def getInitTerms(self, minIn=0, minOut=0):
        terms = []
        # if self.lenMode() >= minIn and self.lenNonMode() >= minOut:
        if self.lenNonMode() >= minIn and self.lenMode() >= minOut: 
            idx = self.sVals.index((0,-1))
            low_idx, hi_idx = (idx-1, idx+1)
            while low_idx > 0 and self.sVals[low_idx][0] == self.sVals[idx][0]:
                low_idx -= 1
            while hi_idx < len(self.sVals) and self.sVals[hi_idx][0] == self.sVals[idx][0]:
                hi_idx += 1
            if low_idx >= 0 and low_idx+1 >= minIn and ( self.nbRows() - (low_idx+1) ) >= minOut :
                terms.append((self.getAssocTermClass()(self.getId(), float("-Inf"), self.sVals[low_idx][0]), low_idx+1))
            if hi_idx < len(self.sVals) and (len(self.sVals)-hi_idx) >= minIn \
                   and ( self.nbRows() - (len(self.sVals)-hi_idx) ) >= minOut :
                terms.append((self.getAssocTermClass()(self.getId(), self.sVals[hi_idx][0], float("Inf")), len(self.sVals)-hi_idx))
        else:            
            max_agg = 2*minIn #max(2*min(minIn, minOut), max(minIn, minOut)/2)
            tt = self.collapseBuckets(max_agg)
            for i in range(len(tt[0])):
                count, lowb, upb =  (len(tt[0][i]), tt[1][i], tt[-1][i])
                if count >= minIn and ( self.nbRows() - count ) >= minOut :
                    if i == 0:
                        lowb = float("-Inf")
                    elif i == len(tt[0])-1:
                        upb = float("Inf")
                    terms.append((self.getAssocTermClass()(self.getId(), lowb, upb), i))
                    # print "Found term\t", terms[-1][0], terms[-1][1], count 

        # if len(terms) == 0:
        #     print "Nothing found %s" % self
        return terms

    def getRoundThres(self, thres, which):
        ## return thres ### NO ROUNDING, many digits...
        i = 0
        while i < len(self.sVals) -1 and self.sVals[i][0] < thres:
            i+= 1
        if which == "high":
            ## print thres, which, self.sVals[i-1][0] 
            return self.sVals[i-1][0]
        else:
            ## print thres, which, self.sVals[i][0] 
            return self.sVals[i][0]

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

    def getValue(self, rid, pref=None):
        if self.vect is None:
            self.getVector()
        if type(self.vect) is dict:
            return self.vect.get(rid, self.vect[-1])
        else:
            self.getVector()
            return self.vect[rid]

    def valToStr(self, val):
        if (numpy.isnan(val) and numpy.isnan(self.NA)) or \
               val == self.NA:
            return NA_str_c
        return val


    def getNumValue(self, rid):
        return self.getValue(rid)

    def areDataEquiv(self, vA, vB):
        if self.uniqvs is None:
            self.uniqvs = sorted(set([self.sVals[x][0] for x in range(len(self.sVals))]))
        # print "DataEquiv? %s vs. %s [%s]" % (vA, vB, list(enumerate(self.uniqvs[:10])))
        if vA == vB:
            return True
        icurrent, iAe, iBe, iAg, iBg = (0, None, None, None, None)
        while icurrent < len(self.uniqvs) and ( iAg is None or iBg is None):
            if iAg is None and self.uniqvs[icurrent] > vA:
                iAg = icurrent
            if iBg is None and self.uniqvs[icurrent] > vB:
                iBg = icurrent
            if iAe is None and self.uniqvs[icurrent] >= vA:
                iAe = icurrent
            if iBe is None and self.uniqvs[icurrent] >= vB:
                iBe = icurrent
            icurrent += 1
        # print "iAe=%s iBe=%s iAg=%s iBg=%s" % (iAe, iBe, iAg, iBg)
        ans = (False, False)
        if iAe!=iAg and iBe!=iBg: # if both values are in the data
            if iAe == iBe and iAg == iBg: # if they are equal
                # This should not happen, as we tested for equality of values at the start
                ans = (True, True)
        elif iAe==iAg and iBe==iBg: # if neither value is in the data
            if iAe == iBe: ## and iAg == iBg: # if they are in the same bin
                ans = (True, True)
        elif iAe==iAg: # and iBe!=iBg: # if B is in the data but not A
            ans = ((iAe == iBg), (iAe == iBe))
        elif iBe==iBg: # and iAe!=iAg: # if A is in the data but not B
            ans = ((iBe == iAg), (iBe == iAe))
        # print "A in data %s\tB in data %s\tA ~ B %s" % (iAe!=iAg, iBe!=iBg, ans)
        return ans[0], ans[1], iAe!=iAg, iBe!=iBg
    
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
        return numpy.min(numpy.diff(numpy.unique(self.vect[numpy.isfinite(self.vect)])))

    def mkVector(self):
        if self.isDense():
            self.vect = numpy.ones(self.N)*self.NA
        else:
            self.vect = numpy.zeros(self.N)
            self.vect[list(self.missing)] = self.NA

        if len(self.sVals) > 0:
            vals, ids = zip(*self.sVals)
            self.vect[list(ids)] = vals
        ### mode rows HERE
                   
    def getRange(self, details=None):
        return (self.getMin(details), self.getMax(details))
    def getMin(self, details=None):
        if len(self.sVals) > 0:
            return self.sVals[0][0]
        return MODE_VALUE ### DEBUG
    def getMax(self, details=None):
        if len(self.sVals) > 0:
            return self.sVals[-1][0]
        return MODE_VALUE
    def getNbValues(self):
        if self.nbUniq is None:
            self.nbUniq = numpy.unique([v[0] for v in self.sVals]).shape[0]
        return self.nbUniq

    def compPrec(self, details=None):
        for (v,i) in self.sVals:
            if len(str(v % 1))-2 > self.prec:
                self.prec = len(str(v % 1))-2
        
    def getPrec(self, details=None):
        if self.prec is None:
            self.compPrec()
        return self.prec

    def __init__(self, ncolSupp=[], N=-1, nmiss=set(), prec=None, force=False, mode=None):
        ColM.__init__(self, N, nmiss)
        self.nbUniq = None
        self.uniqvs = None
        self.prec = prec
        self.sVals = ncolSupp
        self.buk = None
        self.colbuk = None
        self.max_agg = None
        if mode is None:
            self.sVals.sort()
            self.mode = {}
            self.setMode(force)
        else: ### especially for subsetCol
            self.mode = mode

    def subsetCol(self, row_ids=None):
        mode_rids = None
        hasMode = False
        if row_ids is None:
            svals = [(v,i) for (v,i) in self.sVals]
            miss = set(self.missing)
            N = self.nbRows()
            if self.mode[1] is not None:
                hasMode = True
                mode_rids = set(self.mode[1]) 
        else:
            miss = set()
            svals = []
            N = sum([len(news) for news in row_ids.values()])
            for old in self.missing.intersection(row_ids.keys()):
                miss.update(row_ids[old])
                
            if self.mode[1] is not None:
                mode_rids = set()
                hasMode = True
                for old in self.mode[1].intersection(row_ids.keys()):
                    mode_rids.update(row_ids[old])
                    
            for v, old in self.sVals:
                if hasMode and old == -1:
                    svals.append((MODE_VALUE, -1))
                else:
                    svals.extend([(v,new) for new in row_ids.get(old, [])])

        mode = (MODE_VALUE, None)
        if hasMode:
            mode = (self.mode[0], mode_rids)

        tmp = NumColM(svals, N, miss, self.prec, mode=mode)
        tmp.name = self.name
        tmp.enabled = self.enabled
        tmp.infofull = {"in": tuple(self.infofull["in"]), "out": tuple(self.infofull["out"])}
        return tmp

    def setMode(self, force=False):
        ### The mode is indicated by a special entry in sVals with row id -1,
        ### all rows which are not listed in either sVals or missing take that value
        ## if len([i for v,i in self.sVals if v == 0]) > 0.1*self.N:
        ##     self.sVals = [(v,i) for (v,i) in self.sVals if v != 0]
        ## if force or (len(self.sVals)+self.nbMissing() > 0 and len(self.sVals)+self.nbMissing() != self.N ):
        tmpV = [(v,i) for (v,i) in self.sVals if v != MODE_VALUE]
        # if len([i for v,i in self.sVals if v == MODE_VALUE]) > 0.1*self.N compute vector
        #     self.sVals = [(v,i) for (v,i) in self.sVals if v != MODE_VALUE]
        if force or ( len(self.sVals)+self.nbMissing() > 0 and len(tmpV)+self.nbMissing() != self.N \
           and ( len(self.sVals)+self.nbMissing() < self.N  or len(self.sVals) - len(tmpV)  > 0.1*self.N)):
           ### THIS CONDITION LAST CONDITION: either is already sparse or turning to sparse would bring gain
            self.sVals = tmpV    ## gather row ids for which
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
                self.sVals.insert(i, (MODE_VALUE, -1))
        else: ### MODE unused
            self.mode = (MODE_VALUE, None)
        
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


    def collapsedBuckets(self, max_agg, nbb=None):
        if nbb is not None:
            max_agg = self.nbRows()/float(nbb)
        if self.colbuk is None or (max_agg is not None and self.max_agg != max_agg):
            self.max_agg = max_agg
            self.colbuk = self.collapseBuckets(self.max_agg, checknext=True)
        return self.colbuk
    
    def collapseBuckets(self, max_agg, checknext=False):
        #### collapsing from low to up, could do reverse...
        tmp = self.buckets()
        tmp_supp=set([])
        bucket_min=tmp[1][0]
        colB_supp = []
        colB_min= []
        colB_max= []
        # colB_max= [None]
        for i in range(len(tmp[1])):
            # if len(tmp[0][i]) > max_agg:
            #     print "POTENTIAL DIFF", self
            if len(tmp_supp) > max_agg or (checknext and i > 0 and len(tmp[0][i]) > max_agg):
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
        if term.isAnon():
            return set()
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

        partids = [[ssetts.partId(ssetts.Exx, side), ssetts.partId(ssetts.Exo, side)], \
                   [ssetts.partId(ssetts.Eox, side), ssetts.partId(ssetts.Eoo, side)]]
        
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
        return Literal(n, self.getAssocTermClass()(self.getId(), lowb, upb))

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
        return Literal(n, self.getAssocTermClass()(self.getId(), lowb, upb))
associate_term_class(NumColM, NumTerm)
