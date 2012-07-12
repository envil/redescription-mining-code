import os.path
from classQuery import Op, Item, BoolItem, CatItem, NumItem, Term, Query 
from classRedescription import Redescription
from classSParts import SParts
import pdb

class ColM:
    def __init__(self, N=-1, nmiss= set()):
        self.N = N
        self.missing = nmiss
        self.id = None
        self.side = None
        self.name = ""
        self.enabled = 1

    def setId(self, nid):
        self.id = nid

    def getName(self, details):
        return self.name
        
    def getSide(self, details=None):
        return self.side

    def getId(self, details=None):
        return self.id

    def getType(self, details=None):
        return "-"

    def miss(self):
        return self.missing

    def suppTerm(self, term):
        if term.isNeg():
            return set(range(self.N)) - self.suppItem(term.item) - self.miss()
        else:
            return self.suppItem(term.item)

    def lMiss(self):
        return len(self.missing)

    def lSuppTerm(self, term):
        if term.isNeg():
            return self.N - len(self.suppItem(term.item)) - len(self.miss())
        else:
            return len(self.suppItem(term.item))

    def nbRows(self):
        return self.N

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


class BoolColM(ColM):
    type_id = 1

    def getItem(self):
        return BoolItem(self.id)

    def __str__(self):
        return ColM.__str__(self)+ ( ", %i Trues" %( self.lTrue() ))

    def getType(self, details):
        return "Boolean"

    def getDensity(self, details):
        return self.lTrue()

    def __init__(self, ncolSupp=[], N=-1, nmiss=set()):
        ColM.__init__(self, N, nmiss)
        self.hold = ncolSupp

    def supp(self):
        return self.hold
    
    def suppItem(self, item):
        return set(self.hold)

    def lTrue(self):
        return len(self.hold)

    def lFalse(self):
        return self.nbRows() - self.lTrue() - len(self.miss())

    def nonFull(self, minIn, minOut):
        if self.lTrue() >= minIn and self.lFalse() >= minOut :
            return True
        return False

    
class CatColM(ColM):
    type_id = 2

    def getItem(self):
        return CatItem(self.id, self.cats()[0])

    def __str__(self):
        return ColM.__str__(self)+ ( ", %i categories" % len(self.cats()))

    def getCategories(self, details):
        return ', '.join(["%s:%d" % (catL, len(catR)) for catL,catR in self.sCats.items()])

    def getType(self, details):
        return "categorical"


    def __init__(self, ncolSupp=[], N=-1, nmiss= set()):
        ColM.__init__(self, N, nmiss)
        self.sCats = ncolSupp
        self.cards = sorted([(cat, len(self.suppCat(cat))) for cat in self.cats()], key=lambda x: x[1]) 

    def cats(self):
        return self.sCats.keys()

    def suppCat(self, cat):
        if cat in self.sCats.keys():
            return self.sCats[cat]
        else:
            return set()
            
    def suppItem(self, item):
        return self.suppCat(item.cat)

    def nonFull(self, minIn, minOut):
        if self.cards[-1][1] >= minIn and self.nbRows() - self.cards[0][1] >= minOut :
            return True
        return False
    
class NumColM(ColM):
    type_id = 3

    def getItem(self):
        return NumItem(self.id, self.sVals[0][0], self.sVals[-1][0])

    def __str__(self):
        return ColM.__str__(self)+ ( ", %i values not in mode" % self.lenNonMode())

    def getType(self, details):
        return "numerical"

    def getMin(self, details):
        return self.sVals[0][0]
    def getMax(self, details):
        return self.sVals[-1][0]

    def __init__(self, ncolSupp=[], N=-1, nmiss=set()):
        ColM.__init__(self, N, nmiss)
        self.sVals = ncolSupp
        self.mode = {}
        self.buk = None
        self.colbuk = None
        self.max_agg = None
        
        ### The mode is indicated by a special entry in sVals with row id -1,
        ### all rows which are not listed in either sVals or missing take that value
        if len(self.sVals)+len(self.missing) != self.N :
            tmp = set([r[1] for r in self.sVals])
            if -1 in tmp:
                tmp.remove(-1)
            if 2*len(tmp) > self.N:
                self.mode = (-1, set(range(self.N)) - tmp - self.missing)
            else:
                self.mode = (1, tmp)
        else:
            self.mode = (0, None)
    
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

    def nonFull(self, minIn, minOut):
        if self.lenNonMode() >= minOut or self.lenNonMode() >= minIn :
            return True
        return False

    def collapsedBuckets(self, max_agg):
        if self.colbuk == None or (max_agg != None and self.max_agg != max_agg):
            self.max_agg = max_agg
            self.colbuk = self.collapseBuckets(self.max_agg)
        return self.colbuk
    
    def collapseBuckets(self, max_agg):
        tmp = self.buckets()

        tmp_supp=set([])
        bucket_min=tmp[1][0]
        colB_supp = []
        colB_max= []
        colB_min= []
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
        return (colB_supp, colB_min, 0, colB_max)

    def buckets(self):
        if self.buk == None:
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

    def suppItem(self, item):
        suppIt = set()
        for (val , row) in self.sVals:
            if val > item.upb :
                return suppIt
            elif val >= item.lowb:
                if row == -1:
                    suppIt.update(self.modeSupp())
                else:
                    suppIt.add(row)
        return suppIt

    def getTermBuk(self, neg, buk_op, bound_ids, flag=0):
        if bound_ids[0] == 0 and bound_ids[1] == len(buk_op)-1:
            return (neg, None)
        elif bound_ids[0] == 0 :
            if neg:
                lowb = buk_op[bound_ids[1]+1]
                upb = float('Inf')
                n = False
            else:
                lowb = float('-Inf')
                upb = buk_op[bound_ids[1]+flag]-flag
                n = False
        elif bound_ids[1] == len(buk_op)-1 :
            if neg:
                lowb = float('-Inf') 
                upb = buk_op[bound_ids[0]-1]
                n = False
            else:
                lowb = buk_op[bound_ids[0]]
                upb = float('Inf') 
                n = False
        else:
            lowb = buk_op[bound_ids[0]]
            upb = buk_op[bound_ids[1]+flag]-flag
            n = neg
        return Term(n, NumItem(self.getId(), lowb, upb))

    def getTermSeg(self, neg, segments_op, bound_ids):
        if bound_ids[0] == 0 and bound_ids[1] == len(segments_op)-1:
            return (neg, None)
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
        return Term(n, NumItem(self.getId(), lowb, upb))


class Data:
    
    def __init__(self, datafiles):
        (self.cols, self.type_ids, self.N) = readData(datafiles)
        self.redunRows = set()
        self.nf = [[i for i in range(self.nbCols(0))], [i for i in range(self.nbCols(1))]]
            
    def __str__(self):
        return "%i x %i+%i data" % ( self.nbRows(), self.nbCols(0), self.nbCols(1))

    def disp(self):
        strd = str(self) +":\n"
        strd += 'Left Hand side columns:\n'
        for col in self.cols[0]:
            strd += "\t%s\n" col
        strd += 'Right Hand side columns:\n'
        for col in self.cols[1]:
            strd += "\t%s\n" col
        return strd

    def nbRows(self):
        return self.N

    def nbCols(self, side):
        return len(self.cols[side])
        
    def supp(self, side, term): 
        if term.item.colId() < len(self.cols[side]):
            return self.cols[side][term.item.colId()].suppTerm(term)- self.redunRows
        else:
            return set()

    def miss(self, side, term):
        if term.item.colId() < len(self.cols[side]):
            return self.cols[side][term.item.colId()].miss()- self.redunRows
        else:
            return set()

    def termSuppMiss(self, side, term):
        return (self.supp(side, term), self.miss(side,term))
        
    def addRedunRows(self, redunRows):
	self.redunRows.update(redunRows)
    
    ###TODO compute non full
    def nonFull(self):
        return [set(self.nf[0]), set(self.nf[1])]
    def nbNonFull(self, side):
        return len(self.nf[side])

    def usableCols(self):
        return [set([col for col in self.nf[0] if self.cols[0][col].getEnabled() == 1]), \
                set([col for col in self.nf[1] if self.cols[1][col].getEnabled() == 1])]




############################################################################
############## READING METHODS
############################################################################
def loadColumnNames(filename):
    if isinstance(filename, file):
        f = filename
    else:
        f = open(filename, 'r')
    a = []
    for line in f.readlines():
        a.append(parseUnicodes(line.strip()))
    return a

def setNames(data, filenames, extension='.names'):
        names = [None, None]
        for side in [0,1]:
            filename = filenames[side]
            if not isinstance(filename, file):
                filename_parts = filename.split('.')
                filename_parts.pop()
                filename_names = '.'.join(filename_parts) + extension
                assert os.path.exists(filename_names)
            names[side] = loadColumnNames(filename)
            if (len(names[side]) ==  lenColSupps):
                names[side] = None
                raise Warning('Number of names does not match number of variables ! Not returning names')
            else:
                for i, col in enumerate(data.cols[side]):
                    col.name = names[side][i]
        return names

def parseUnicodes(text):
    for (i, p) in enumerate(text.split('\\u')):
        if i == 0:
            str_tmp = p
        else:
            str_tmp += unichr(int(p[:4], 16)) + p[4:]
    return str_tmp

def readData(filenames):
    data = []; nbRowsT = None;
    for side, filename in enumerate(filenames):
        (cols, type_ids_tmp, nbRows, nbCols) = readMatrix(filename, side)
        if len(cols) != nbCols:
            raise Exception('Matrix in %s does not have the expected number of variables !' % filename)

        else:
            if nbRowsT == None:
                nbRowsT = nbRows
                type_ids = type_ids_tmp
                data.append(cols)
            elif nbRowsT == nbRows:
                data.append(cols)
                type_ids.update(type_ids_tmp)
            else:
                raise Exception('All matrices do not have the same number of entities (%i ~ %i)!' % (nbRowsT, nbRows))
    return (data, type_ids, nbRows)

def readMatrix(filename, side = None):
    ## Read input
    nbRows = None
    names = []
    type_ids = set()
    if isinstance(filename, file):
        f = filename
        filename = f.name
    else:
        f = open(filename, 'r')

    filename_parts = filename.split('.')
    type_all = filename_parts.pop()
    nbRows = None
    nbCols = None

    if len(type_all) >= 3 and (type_all[0:3] == 'mix' or type_all[0:3] == 'dat' or type_all[0:3] == 'spa'):  
        row = f.next()
        a = row.split()
        nbRows = int(a[0])
        nbCols = int(a[1])
    try:
        if len(type_all) >= 3 and type_all[0:3] == 'dat':
            method_parse =  eval('parseCell%s' % (type_all.capitalize()))
            method_prepare = eval('prepare%s' % (type_all.capitalize()))
            method_finish = eval('finish%s' % (type_all.capitalize()))
        else:
            method_parse =  eval('parseVar%s' % (type_all.capitalize()))
            method_prepare = eval('prepareNonDat')
            method_finish = eval('finishNonDat')
    except NameError:
        return
    try:
        tmpCols = method_prepare(nbRows, nbCols)

        Data.logger.printL(2,"Reading input data %s (%s)"% (filename, type_all))
        for row in f:
            if  len(type_all) >= 3 and type_all[0:3] == 'den' and nbRows == None:
                nbRows = len(row.split())
            method_parse(tmpCols, row.split(), nbRows, nbCols)

        if  len(type_all) >= 3 and type_all[0:3] == 'den' and nbCols == None:
            nbCols = len(tmpCols)

        Data.logger.printL(4,"Done with reading input data %s (%i x %i %s)"% (filename, nbRows, len(tmpCols), type_all))
        (cols, type_ids) = method_finish(tmpCols, nbRows, nbCols)
        for (cid, col) in enumerate(cols):
            col.setId(cid)
            col.side = side
    except (AttributeError, ValueError, StopIteration):
        raise Exception('Size and type header is not right')

    return (cols, type_ids, nbRows, nbCols)
    
def prepareNonDat(nbRows, nbCols):
    return []

def parseVarMix(tmpCols, a, nbRows, nbCols):
    name = a.pop(0)
    type_row = a.pop(0)
    if type_row[0:3] == 'dat':
        raise Exception('Oups this row format is not allowed for mixed datat (%s)!' % (type_row))
    try:
        method_parse =  eval('parseVar%s' % (type_row.capitalize()))
    except AttributeError:
        raise Exception('Oups this row format does not exist (%s)!' % (type_row))
    method_parse(tmpCols, a, nbRows, nbCols)

def finishNonDat(tmpCols, nbRows, nbCols):
    type_ids = set()
    for col in tmpCols:
        type_ids.add(col.type_id)
    return (tmpCols, type_ids)

def prepareDatnum(nbRows, nbCols):
    return [[[(0, -1)], set()] for i in range(nbCols)]

def parseCellDatnum(tmpCols, a, nbRows, nbCols):
    id_row = int(a[0])-1
    id_col = int(a[1])-1
    if id_col >= nbCols or id_row >= nbRows:
        raise Exception('Outside expected columns and rows (%i,%i)' % (id_col, id_row))
    else :
        try:
            val = float(a[2])
            if val != 0:
                tmpCols[id_col][0].append((val, id_row))
        except ValueError:
            tmpCols[id_col][1].add(id_row)
            
def finishDatnum(tmpCols, nbRows, nbCols):
    return ([NumColM(sorted(tmpCols[col][0], key=lambda x: x[0]), nbRows, tmpCols[col][1]) for col in range(len(tmpCols))], set([NumColM.type_id]))
        
def prepareDatbool(nbRows, nbCols):
    return [[set(), set()] for i in range(nbCols)]

def parseCellDatbool(tmpCols, a, nbRows, nbCols):
    id_row = int(a[0])-1
    id_col = int(a[1])-1
    if id_col >= nbCols or id_row >= nbRows:
        raise Exception('Outside expected columns and rows (%i,%i)' % (id_col, id_row))
    else :
        try:
            val = float(a[2])
            if val != 0:
                tmpCols[id_col][0].add(id_row)
        except ValueError:
            tmpCols[id_col][1].add(id_row)
        
def finishDatbool(tmpCols, nbRows, nbCols):
    return ([BoolColM(tmpCols[col][0], nbRows, tmpCols[col][1]) for col in range(len(tmpCols))], set([BoolColM.type_id]))


def parseVarDensenum(tmpCols, a, nbRows, nbCols):
    if len(a) == nbRows:
        tmp = []
        miss = set()
        for i in range(len(a)):
            try:
                val = float(a[i])
                tmp.append((val,i))
            except ValueError:
                miss.add(i)
        tmp.sort(key=lambda x: x[0])
        tmpCols.append(NumColM( tmp, nbRows, miss ))
    else:
        raise Exception('Number of rows does not match (%i ~ %i)' % (nbRows,len(a)))

                        
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
        raise Exception('Number of rows does not match (%i ~ %i)' % (nbRows,len(a)))

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
        tmpCols.append(BoolColM( tmp, nbRows , miss))
    else:
        raise Exception('Number of rows does not match (%i ~ %i)' % (nbRows,len(a)))
    
                        
def parseVarSparsebool(tmpCols, a, nbRows, nbCols):
    tmp = set()
    for i in range(len(a)):
        tmp.add(int(a[i]))
    if max(tmp) >= nbRows:
        raise Exception('Too many rows (%i ~ %i)' % (nbRows, max(tmp)))
    else:
        tmpCols.append(BoolColM( tmp, nbRows ))
