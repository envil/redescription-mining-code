import re, pdb
from classSParts import  SParts

class Op:
    
    ops = {0: 'X', 1: '|', -1: '&'}
    opsTex = {0: 'X', 1: '\lor', -1: '\land'}
    opsU = {0: 'X', 1: ur'\u2228', -1: ur'\u2227'}
    
    def __init__(self, nval=0):
        if type(nval) == bool :
            if nval:
                self.val = 1
            else:
                self.val = -1
        elif Op.ops.has_key(nval):
            self.val = nval
        else:
            raise Exception('Uninterpretable operator: %s !' % nval)
                
    def isSet(self):
        return self.val != 0


    def copy(self):
        return Op(self.val)
    
    def other(self):
        return Op(-self.val)
    
    def __int__(self):
        return self.val
    
    def isOr(self):
        return self.val == 1

    def isAnd(self):
        return self.val == -1

    def __str__(self):
        return self.disp()

    def disp(self):
        return Op.ops[self.val]

    def dispTex(self):
        return Op.opsTex[self.val]

    def dispU(self):
        return Op.opsU[self.val]

    def __cmp__(self, other):
        if other == None:
            return 1
        else:
            return cmp(2*self.val*self.val+self.val, 2*other.val*other.val+other.val)

    def __hash__(self):
        return self.val
    
    def parse(string):
        for (k, v) in Op.ops.iteritems():
            if v == string:
                return Op(k)
        return None
    parse = staticmethod(parse)

    # def parseTex(parts, pos):
    #     return self.parse(parts, pos, Op.opsTex)
    # parseTex = staticmethod(parseTex)

    # def parseU(parts, pos):
    #     return self.parse(parts, pos, Op.opsU)
    # parseU = staticmethod(parseU)
       
class Neg:
    symb = ['', '! ']
    symbTex = ['', '\\neg ']
    symbU = ['', u'\u00ac ']

    def __init__(self, nNeg=False):
        if nNeg == True or nNeg < 0:
            self.neg = -1
        else:
            self.neg = 1

    def boolVal(self):
        return self.neg < 0
    
    def __int__(self):
        return self.neg
    
    def __cmp__(self, other):
        if other == None:
            return 1
        else:
            return cmp(self.neg, other.neg)

    def __hash__(self):
        return self.neg

    def __str__(self):
        return self.disp()

    def disp(self):
        return Neg.symb[self.boolVal()]

    def dispTex(self):
        return Neg.symbTex[self.boolVal()]

    def dispU(self):
        return Neg.symbU[self.boolVal()]

    # def parse(parts, pos, style= None):
    #     if style == None: style = Neg.symb 
    #     if style[1].startswith(parts[pos]):
    #         return (Neg(True), pos+1)
    #     else:
    #         return (Neg(False), pos)
    # parse = staticmethod(parse)

    # # def parseTex(parts, pos):
    # #     return self.parse(parts, pos, Neg.symbTex)
    # # parseTex = staticmethod(parseTex)

    # # def parseU(parts, pos):
    # #     return self.parse(parts, pos, Neg.symbU)
    # # parseU = staticmethod(parseU)


class Item:
    type_id = 0
    
    def __init__(self, ncol):
        self.col = ncol

#     def simple(self, neg):
#         return neg

    def copy(self):
        return Item(self.col)

    def cmpType(self, other):
        if other == None:
            return 1
        else:
            return cmp(self.type_id, other.type_id)
    
    def colId(self):
        return self.col
    
    def cmpCol(self, other):
        if other == None:
            return 1
        else:
            return cmp(self.col, other.col)
    
    def __str__(self):
        return '%i ' % self.col
    
class BoolItem(Item):
    type_id = 1
    patt = '^\s*((?P<neg>'+Neg.symb[1]+')?\s*)(?P<col>\d+)\s*$'
    pattTex = '^\s*((?P<neg>'+Neg.symbTex[1]+')?\s*)(?P<col>\d+)\s*$'
    pattU = '^\s*((?P<neg>'+Neg.symbU[1]+')?\s*)(?P<col>.+)\s*$'

    def copy(self):
        return BoolItem(self.col)
    
    def __cmp__(self, other):
        if self.cmpCol(other) == 0:
            return self.cmpType(other)
        else:
            return self.cmpCol(other)
        
    def __hash__(self):
        return self.col
    
    def __str__(self):
        return self.disp()

    def disp(self, neg=None, names = None, lenIndex=0):
        if type(neg) == bool:
            neg = Neg(neg)

        if neg == None:
            strneg = ''
        else:
            strneg = neg.disp()
        if lenIndex > 0 :
            lenIndex = max(lenIndex-1,3)
            slenIndex = str(lenIndex)
        else:
            slenIndex = ''
        if type(names) == list  and len(names) > 0:
            lab = ('%s%'+slenIndex+'s') % (strneg, names[self.col])
            if len(lab) > lenIndex & lenIndex > 0:
                lab = lab[:lenIndex]
            return lab + ' '
        else:
            return ('%s%'+slenIndex+'i ') % (strneg, self.col)

    def dispTex(self, neg, names = None):
        if type(neg) == bool:
            neg = Neg(neg)

        if type(names) == list  and len(names) > 0:
            return '%s%s' % ( neg.dispTex(), names[self.col])
        else:
            return '%s%i' % ( neg.dispTex(), self.col)

    def dispU(self, neg, names = None):
        if type(neg) == bool:
            neg = Neg(neg)

        if type(names) == list  and len(names) > 0:
            return '%s%s' % ( neg.dispU(), names[self.col])
        else:
            return '%s%i' % ( neg.dispU(), self.col)
                    
    def parse(string, pattern, names=None):
        partsU = re.match(pattern, string)
        ncol = None
        if partsU != None:
            neg = (partsU.group('neg') != None)
            tmpcol = partsU.group('col').strip()
            if tmpcol.isdigit():
                try:
                    ncol = int(tmpcol)
                except ValueError, detail:
                    ncol = None
                    raise Warning('In boolean item %s, column is not convertible to int (%s)\n'%(string, detail))
            else: 
                if names != None and tmpcol in names:
                    ncol = names.index(tmpcol)
        if ncol != None :
            return (neg, BoolItem(ncol))
        return (None, None)
    parse = staticmethod(parse)
    
class CatItem(Item):
    type_id = 2
    patt = '^\s*((?P<neg>'+Neg.symb[1]+')?\s*)?(?P<col>\d+)\s*\=(?P<cat>\d+?)\s*$'
    pattTex = '^\s*((?P<neg>'+Neg.symb[1]+')?\s*)?(?P<col>\d+)\s*\\in(?P<cat>\d+?)\s*$'
    pattU = '^\s*(?P<col>.+)\s*(?P<neg>['+ur'\u2208'+'])?(?(neg)|['+ur'\u2209'+'\=])\s*(?P<cat>\d+?)\s*$'

    
    def __init__(self, ncol, ncat):
        self.col = ncol
        self.cat = ncat

    def copy(self):
        return CatItem(self.col, self.cat)
            
    def __cmp__(self, other):
        if self.cmpCol(other) == 0:
            if self.cmpType(other) == 0:
                return cmp(self.cat, other.cat)
            else:
                return self.cmpType(other)
        else:
            return self.cmpCol(other)
    
    def __hash__(self):
        return self.col*hash(self.cat)+(self.col-1)*(hash(self.cat)+1)

    def __str__(self):
        return self.disp()
    
    def disp(self, neg=None, names = None, lenIndex=0):
        if type(neg) == bool:
            neg = Neg(neg)

        if neg == None:
            strneg = ''
        else:
            strneg = neg.disp()
        strcat = '=%i ' % self.cat
        if lenIndex > 0 :
            lenIndex = max(lenIndex-len(strcat),3)
            slenIndex = str(lenIndex)
        else:
            slenIndex = ''
        if type(names) == list  and len(names) > 0:
            lab = ('%s%'+slenIndex+'s') % (strneg, names[self.col])
            if len(lab) > lenIndex & lenIndex > 0:
                lab = lab[:lenIndex]
            return lab + strcat
        else:
            return strneg+(('%s%'+slenIndex+'i') % (strneg, self.col)) + strcat

    def dispTex(self, neg, names = None):
        if type(neg) == bool:
            neg = Neg(neg)

        if type(names) == list  and len(names) > 0:
            return '%s %s\\in %i' % (names[self.col], neg.dispTex(), self.cat)
        else:
            return '%i %s\\in %i' % (self.col, neg.dispTex(), self.cat)

    def dispU(self, neg, names = None):
        if type(neg) == bool:
            neg = Neg(neg)

        if neg.boolVal():
            symbIn = u'\u2209'
        else:
            symbIn = u'\u2208'
        if type(names) == list  and len(names) > 0:
            return ('%s '+symbIn+' %i') % (names[self.col], self.cat)
        else:
            return ('%s '+symbIn+' %i') % (self.col, self.cat)

    def parse(string, pattern, names=None):
        partsU = re.match(pattern, string)
        ncol = None
        if partsU != None:
            neg = (partsU.group('neg') != None)
            tmpcol = partsU.group('col').strip()
            if tmpcol.isdigit():
                try:
                    ncol = int(tmpcol)
                except ValueError, detail:
                    ncol = None
                    raise Warning('In categorical item %s, column is not convertible to int (%s)\n'%(string, detail))
            else: 
                if names != None and tmpcol in names:
                    ncol = names.index(tmpcol)
            try:
                cat = int(partsU.group('cat'))
            except ValueError, detail:
                ncol = None
                raise Warning('In categorical item %s, category is not convertible to int (%s)\n'%(string, detail))
        if ncol != None :
            return (neg, CatItem(ncol, cat))
        return (None, None)
    parse = staticmethod(parse)

    
    # def parse(parts, pos):
    #     partsU = re.match(CatItem.patt, string)
    #     if partsU != None :
    #         ok = True
    #         try:
    #             ncat = int(partsU.group('cat'))
    #         except ValueError, detail:
    #             raise Warning('In categorical item %s, category is not convertible to int (%s)\n'%(string, detail))
    #             ok = False
    #         try:
    #             ncol = int(partsU.group('col'))
    #         except ValueError, detail:
    #             raise Warning('In categorical item %s, column is not convertible to int (%s)\n'%(string, detail))
    #             ok = False
    #         if ok:
    #             return (CatItem(ncol, ncat), pos+1)
    #     return (None, pos)
    # parse = staticmethod(parse)

class NumItem(Item):
    type_id = 3

    patt = '^\s*((?P<neg>'+Neg.symb[1]+')?\s*)(?P<col>\d+)((\>(?P<lowbs>-?\d+(\.\d+)?))|(\<(?P<upbs>-?\d+(\.\d+)?))|(\>(?P<lowb>-?\d+(\.\d+)?)\<(?P<upb>-?\d+(\.\d+)?)))\s*$'
    pattTex = '^\s*((?P<neg>'+Neg.symbTex[1]+')?\s*)\[\s*((?P<lowbs>-?\d+(\.\d+)?)\s*\\\\leq{}\s*)(?P<col>.+)?(\s*\\\\leq{}\s*(?P<upbs>-?\d+(\.\d+)?))\s*\]\s*$'
    pattU = '^\s*((?P<neg>'+Neg.symbU[1]+')?\s*)\[\s*((?P<lowbs>-?\d+(\.\d+)?)\s*(' + ur'\u2a7d' +'|<<)\s*)?(?P<col>[^'+ ur'\u2a7d'+'<]+)(\s*[' + ur'\u2a7d' +'<]\s*(?P<upbs>-?\d+(\.\d+)?))?\s*\]\s*$'
    
    def __init__(self, ncol, nlowb, nupb):
        if nlowb == float('-Inf') and nupb == float('Inf'):
            #pdb.set_trace()
            raise Warning('Unbounded numerical item !')
        else:
            self.col = ncol
            self.lowb = nlowb
            self.upb = nupb

#     def simple(self, neg):
#         if neg:
#             if self.lowb == float('-Inf'):
#                 self.lowb = self.upb
#                 self.upb = float('-Inf')
#                 neg = False
#             elif self.upb == float('-Inf'):
#                 self.upb = self.lowb
#                 self.lowb = float('-Inf')
#                 neg = False
#         return neg
            
    def copy(self):
        return NumItem(self.col, self.lowb, self.upb)
                        
    def __cmp__(self, other):
        if self.cmpCol(other) == 0:
            if self.cmpType(other) == 0:
                if cmp(self.lowb, other.lowb) == 0:
                    return cmp(self.upb, other.upb)
                else:
                    return cmp(self.lowb, other.lowb)
            else:
                return self.cmpType(other)
        else:
            return self.cmpCol(other)
        
        if other == None:
            return 1
        elif cmp(self.col, other.col) == 0:
            if cmp(self.lowb, other.lowb) == 0:
                return cmp(self.upb, other.upb)
            else:
                return cmp(self.lowb, other.lowb)
        else:
            return cmp(self.col, other.col)
        
    def __hash__(self):
        return int(self.col+hash(self.lowb)+hash(self.upb))
    
    def __str__(self):
        return self.disp()

    def disp(self, neg=None, names = None, lenIndex=0):
        if type(neg) == bool:
            neg = Neg(neg)

        if neg == None:
            strneg = ''
        else:
            strneg = neg.disp()
        if self.lowb > float('-Inf'):
            lb = '>%s' % self.lowb
        else:
            lb = ''
        if self.upb < float('Inf'):
            ub = '<%s' % self.upb
        else:
            ub = ''
        strbounds = '%s%s ' % (lb, ub)
        if lenIndex > 0 :
            lenIndex = max(lenIndex-len(strbounds),3)
            slenIndex = str(lenIndex)
        else:
            slenIndex = ''
        if type(names) == list  and len(names) > 0:
            lab = ('%'+slenIndex+'s') % names[self.col]
            if len(lab) > lenIndex & lenIndex > 0:
                lab = lab[:lenIndex]
            return lab + strbounds
        else:
            return strneg+(('%'+slenIndex+'i') % self.col) + strbounds

    def dispTex(self, neg, names = None):
        if type(neg) == bool:
            neg = Neg(neg)
        if self.lowb > float('-Inf'):
            lb = '[%s\\leq{}' % self.lowb
        else:
            lb = '['
        if self.upb < float('Inf'):
            ub = '\\leq{}%s]' % self.upb
        else:
            ub = ']'
        negstr = ' %s' % neg.dispTex()
        if type(names) == list  and len(names) > 0:
            idcol = '%s' % names[self.col]
        else:
            idcol = '%i' % self.col
        return ''+negstr+lb+idcol+ub+''

    def dispU(self, neg, names = None):
        if type(neg) == bool:
            neg = Neg(neg)
        if self.lowb > float('-Inf'):
            lb = u'[%s \u2a7d ' % self.lowb
        else:
            lb = '['
        if self.upb < float('Inf'):
            ub = u' \u2a7d %s]' % self.upb
        else:
            ub = ']'
        negstr = u' %s' % neg.dispU()
        if type(names) == list  and len(names) > 0:
            idcol = '%s' % names[self.col]
        else:
            idcol = '%i' % self.col
        return ''+negstr+lb+idcol+ub+''

    def parse(string, pattern, names=None):
        partsU = re.match(pattern, string)
        ncol=None
        if partsU != None :
            neg = (partsU.group('neg') != None)
            lowb = float('-inf')
            upb = float('inf')
            tmpcol = partsU.group('col').strip()
            tmpupbs = partsU.group('upbs')
            if partsU.groupdict().has_key('upb') and partsU.group('upb') != None:
                tmpupbs = partsU.group('upb')
            tmplowbs = partsU.group('lowbs')
            if partsU.groupdict().has_key('lowb') and partsU.group('lowb') != None:
                tmplowbs = partsU.group('lowb')
            if tmpcol.isdigit():
                try:
                    ncol = int(tmpcol)
                except ValueError, detail:
                    ncol = None
                    raise Warning('In numerical item %s, column is not convertible to int (%s)\n'%(string, detail))
            else: 
                if names != None and tmpcol in names:
                    ncol = names.index(tmpcol)
            if tmpupbs != None:                
                try:
                    upb = float(tmpupbs)
                except ValueError, detail:
                    ncol = None
                    raise Warning('In numerical item %s, upper bound is not convertible to float (%s)\n'%(string, detail))
            
            if tmplowbs != None:                
                try:
                    lowb = float(tmplowbs)
                except ValueError, detail:
                    ncol = None
                    raise Warning('In numerical item %s, lower bound is not convertible to float (%s)\n'%(string, detail))
        if ncol != None and (lowb != float('-inf') or upb != float('inf')):
            return (neg, NumItem(ncol, lowb, upb))
        return (None, None)
    parse = staticmethod(parse)

               
class Term:

    itemTypes = [{'class': NumItem }, \
                 {'class': CatItem }, \
                 {'class': BoolItem }]

#     itemTypes = [{'class': NumItem,  'match':'\d+\>-?\d+(\.\d+)?\<-?\d+(\.\d+)?$'}, \
#                  {'class': CatItem,  'match':'\d+\=\d+?$'}, \
#                  {'class': BoolItem, 'match':'\d+$'}]
    
    def __init__(self, nneg, nitem):
        self.item = nitem ## Already an Item instance
        self.neg = Neg(nneg)
#         self.neg = Neg(self.item.simple(nneg))

    def copy(self):
        return Term(self.neg.boolVal(), self.item.copy())

    def __str__(self):
        return self.disp()

    def disp(self, names = None, lenIndex=0):
        return self.item.disp(self.neg, names, lenIndex)

    def dispTex(self, names = None):
        return self.item.dispTex(self.neg, names)
    
    def dispU(self, names = None):
        return self.item.dispU(self.neg, names)

    def __cmp__(self, other):
        if other == None:
            return 1
        elif cmp(self.item, other.item) == 0:
            return cmp(self.neg, other.neg)
        else:
            return cmp(self.item, other.item)
     
    def __hash__(self):
        return hash(self.item)+hash(self.neg)
    
    def isNeg(self):
        return self.neg.boolVal()

    def col(self):
        return self.item.colId()
    
    def parse(string):
        i = 0
        item = None
        while i < len(Term.itemTypes) and item == None:
            if (re.match(Term.itemTypes[i]['class'].patt, string)):
                (neg, item) = Term.itemTypes[i]['class'].parse(string, Term.itemTypes[i]['class'].patt)
            i+=1
        if item != None:
            return Term(neg, item)
        else:
            return None
    parse = staticmethod(parse)

    def parseTex(string, names=None):
        i = 0
        item = None
        while i < len(Term.itemTypes) and item == None:
            if (re.match(Term.itemTypes[i]['class'].pattTex, string)):
                (neg, item) = Term.itemTypes[i]['class'].parse(string, Term.itemTypes[i]['class'].pattTex)
            i+=1
        if item != None:
            return Term(neg, item)
        else:
            return None
    parseTex = staticmethod(parseTex)

    def parseU(string, names=None):
        i = 0
        item = None
        while i < len(Term.itemTypes) and item == None:
            if (re.match(Term.itemTypes[i]['class'].pattU, string)):
                (neg, item) = Term.itemTypes[i]['class'].parse(string, Term.itemTypes[i]['class'].pattU, names)
            i+=1
        if item != None:
            return Term(neg, item)
        else:
            return None
    parseU = staticmethod(parseU)

            
class Query:
    diff_terms = 1
    diff_cols = 2
    diff_op = 3
    diff_balance = 4
    diff_length = 5
    
    def __init__(self):
        self.op = Op()
        self.buk = []

    def __len__(self):
        l = 0
        for i in self.buk:
            l += len(i)
        return l

    def __hash__(self):
        h = hash(self.op)
        for i in range(len(self.buk)):
            for t in self.buk[i]:
                h += hash(t)+i
        return h
    
    def opBuk(self, nb): # get operator for bucket nb (need not exist yet).
        if nb % 2 == 0: # even bucket: query operator, else other
            return self.op.copy()
        else: 
            return self.op.other()

    def copy(self):
        c = Query()
        c.op = self.op.copy()
        c.buk = []
        for buk in self.buk:
            c.buk.append(set([t.copy() for t in buk if t != None]))
        return c
            
    def compare(x, y): ## same as compare pair with empty right
        if x.op == y.op and x.buk == y.buk:
            return 0
        
        if len(x) < len(y): ## nb of terms in the query, shorter better
            return Query.diff_length
        elif len(x) == len(y):
            if len(x.buk)  < len(y.buk) : ## nb of buckets in the query, shorter better
                return Query.diff_balance
            elif len(x.buk) == len(y.buk) :
                if x.op > y.op : ## operator
                    return Query.diff_op
                elif x.op == y.op :
                    if x.invCols() > y.invCols(): ## terms in the query
                        return Query.diff_cols
                    elif x.invCols() == y.invCols():
                        return Query.diff_terms
                    else:
                        return -Query.diff_cols
                else:
                    return -Query.diff_op
            else:
                return -Query.diff_balance
        else:
            return -Query.diff_length
    compare = staticmethod(compare)
    
    def __cmp__(self, other):
        if other == None:
            return 1
        else:
            return Query.compare(self, other)
    
    def comparePair(x0, x1, y0, y1):
        if ( x0.op == y0.op and x0.buk == y0.buk and x1.op == y1.op and x1.buk == y1.buk ):
            return 0

        if len(x0) + len(x1) < len(y0) + len(y1): ## nb of items in the query, shorter better
            return Query.diff_length
        
        elif len(x0) + len(x1) == len(y0) + len(y1):
            if len(x0.buk) + len(x1.buk) < len(y0.buk) + len(y1.buk): ## nb of sets of items in the query, shorter better
                return Query.diff_balance
            elif len(x0.buk) + len(x1.buk) == len(y0.buk) + len(y1.buk):
                if max(len(x0), len(x1)) < max(len(y0), len(y1)): ## balance of the nb of items in the query, more balanced is better
                    return Query.diff_balance
                elif max(len(x0), len(x1)) == max(len(y0), len(y1)):
                    if max(len(x0.buk), len(x1.buk) ) < max(len(y0.buk), len(y1.buk)): ## balance of the nb of sets of items in the query, more balanced is better
                        return Query.diff_balance
                    
                    elif max(len(x0.buk), len(x1.buk) ) == max(len(y0.buk), len(y1.buk)):
                        if x0.op > y0.op : ## operator on the left
                            return Query.diff_op
                        elif x0.op == y0.op:
                            if x1.op > y1.op : ## operator on the right
                                return Query.diff_op
                            elif x1.op == y1.op:
                                if x0.invCols() > y0.invCols() :
                                    return Query.diff_cols
                                elif x0.invCols() == y0.invCols() :
                                    if x1.invCols() > y1.invCols() :
                                        return Query.diff_cols
                                    elif x1.invCols() == y1.invCols() :
                                        return Query.diff_terms
                                return -Query.diff_cols
                        return -Query.diff_op
            return -Query.diff_balance
        return -Query.diff_length
    comparePair = staticmethod(comparePair)
    
    def extend(self, op, term):
        if len(self) == 0:
            self.buk.append(set([term]))
        elif len(self) == 1:
            self.buk[-1].add(term)
            self.op = op
        elif op == self.opBuk(len(self.buk)-1):
            self.buk[-1].add(term)
        else:
            self.buk.append(set([term]))

    def invCols(self):
        invCols = set()
        for buk in self.buk :
            for term in buk:
                invCols.add(term.col())
        return invCols
    
    def invTerms(self):
        invTerms = set()
        for buk in self.buk :
            for term in buk:
                invTerms.add(term)
        return invTerms
    
    def makeIndexes(self, format_str):
        indexes = []
        for buk_nb in range(len(self.buk)) :
            for term in list(self.buk[buk_nb]) :
                indexes.append(format_str % {'col': term.col(), 'buk': buk_nb}) 
        return indexes
    
    ## return the support associated to a query
    def recompute(self, side, data= None):

        if len(self) == 0 or data==None:
            sm = (set(), set())
        else:
            sm = None

            if len(self) > 0:
                op = self.op
                for buk in self.buk:
                    for term in buk:
                        sm  = SParts.partsSuppMiss(op.isOr(), sm, data.termSuppMiss(side, term))
                    op = op.other()
        return sm
          
    def proba(self, side, data= None):
        if data==None:
            pr = -1
        elif len(self) == 0 :
            pr = 1
        else:
            pr = -1
            if len(self) > 0:
                op = self.op
                for buk in self.buk:
                    for term in buk:
                        pr = SParts.updateProba(pr, len(data.supp(side, term))/float(data.nbRows()), op.isOr())
                        ##print '%s : pr=%f (%s %f)' % (term, pr, op, len(data.supp(side, term))/float(data.nbRows()) )
                    op = op.other()
        return pr
    
#     def invTerms(self):
#         invTerms = []
#         OR = self.opBukIsOR(1)
#         for part in self.query[1:] :
#             spart = list(part)
#             spart.sort()
#             for item in spart :
#                 invItems.append((query_itemId(item), query_itemNot(item), OR))    
#             OR = not OR
#         return invItems
    

    
    def __str__(self):
        return self.disp()    


#     def disPlus(self, data, side, lenIndex=0, names = None):
#         if len(self) == 0 :
#             string = '[]'
#         else:
# #             if len(self.buk) > 2:
# #                 pdb.set_trace()
#             string = ''
#             op = self.op
#             for cbuk in self.buk:
#                 cterms = list(cbuk)
#                 cterms.sort()
#                 for term in cterms:
#                     spp = len(data.supp(side, term));
#                     string += '%s%s (%i,%f)' % (op, term.disp(lenIndex, names), spp, spp/float(data.nbRows()) )
#                 op = op.other()
#         return string[1:]

    def disp(self, names = None, lenIndex=0):
        if len(self) == 0 :
            string = '[]'
        else:
            string = ''
            op = self.op
            for ci, cbuk in enumerate(self.buk):
                cterms = list(cbuk)
                cterms.sort()
                for ti, term in enumerate(cterms):
                    if ti != 0 or ci != 0:
                        string += '%s ' % op
                    string += term.disp(names, lenIndex)
                op = op.other()
        return string

    def dispTex(self, names = None):
        if len(self) == 0 :
            string = ''
        else:
            string = ''
            first = 0
            op = self.op
            for cbuk in self.buk:
                if first != 0:
                    string = '(' + string + ')'
                cterms = list(cbuk)
                cterms.sort()
                for term in cterms:
                    if first == 0:
                        first = 1
                        string += '%s' % (term.dispTex(names))
                    else:
                        string += ' %s %s' % (op.dispTex(), term.dispTex(names))
                op = op.other()
        return string

    def dispU(self, names = None):
        if len(self) == 0 :
            string = ''
        else:
            string = ''
            first = 0
            op = self.op
            for cbuk in self.buk:
                if first != 0:
                    string = '(' + string + ')'
                cterms = list(cbuk)
                cterms.sort()
                for term in cterms:
                    if first == 0:
                        first = 1
                        string += '%s' % (term.dispU(names))
                    else:
                        string += ' %s %s' % (op.dispU(), term.dispU(names))
                op = op.other()
        return string

    def parse(string):
        pattrn = '^(?P<pattIn>[^'+Op.ops[1]+Op.ops[-1]+']*)(?P<op>['+Op.ops[1]+Op.ops[-1]+'])?(?P<pattOut>(?(op).*))$'
        op = None; r = None
        parts = re.match(pattrn, string)
        if parts != None:
            r = Query()
        while parts != None:
            t = Term.parse(parts.group('pattIn'))
            r.extend(op,t)
            if parts.group('op') != None:
                op = Op.parse(parts.group('op'))
                parts = re.match(pattrn, parts.group('pattOut'))
            else:
                parts = None
        return r 
    parse = staticmethod(parse)

    def parseTex(string, names=None):
        r = None
        parts = re.match(r'^\s*(\(\s*(?P<pattIn>.*)\s*\))*\s*(?P<pattOut>[^()]*)\s*$', string)
        if parts != None:
            opExt = None
            ## parse inner query
            if parts.group('pattIn') != None:
                r = Query.parseTex(parts.group('pattIn'), names)
            else:
                r = Query()
            ## identify operator
            if r != None:
                indA = parts.group('pattOut').find(Op.opsTex[-1])
                indO = parts.group('pattOut').find(Op.opsTex[1])
                if indA == -1 and indO == -1:
                    if not r.opBuk(len(r)).isSet():
                        opExt = Op() 
                elif indA > -1 and indO == -1:
                    if not r.opBuk(len(r)).isAnd():
                        opExt = Op(False) 
                elif indA == -1 and indO > -1:
                    if not r.opBuk(len(r)).isOr():
                        opExt = Op(True) 
                # else:
                #     raise Exception('Something is wrong with the operators... %s' % string)
            ## if all went fine so far, split on operator and parse terms
            if opExt != None:
                partsOut = parts.group('pattOut').split(opExt.dispTex())
                pi = 0
                while pi < len(partsOut):
                    t = Term.parseTex(partsOut[pi], names)
                    if t != None:
                        r.extend(opExt,t)
                    else:
                        pi = len(partsOut)
                        r = None
                    pi+=1
        return r
    parseTex = staticmethod(parseTex)

    def parseU(string, names=None):
        r = None
        parts = re.match(ur'^\s*(\(\s*(?P<pattIn>.*)\s*\))*\s*(?P<pattOut>[^()]*)\s*$', string)
        if parts != None:
            opExt = None
            ## parse inner query
            if parts.group('pattIn') != None:
                r = Query.parseU(parts.group('pattIn'), names)
            else:
                r = Query()
            ## identify operator
            if r != None:
                indA = re.search('(?P<op>[' + Op.ops[-1]+ Op.opsU[-1] + '])', parts.group('pattOut'))
                indO = re.search('(?P<op>[' + Op.ops[1]+ Op.opsU[1] + '])', parts.group('pattOut'))
                if indA == None and indO == None:
                    if not r.opBuk(len(r)).isSet():
                        opExt = Op()
                        opStr = Op.ops[-1]
                elif indA != None and indO == None:
                    if not r.opBuk(len(r)).isAnd():
                        opExt = Op(False)
                        opStr = indA.group('op')
                elif indA == None and indO != None:
                    if not r.opBuk(len(r)).isOr():
                        opExt = Op(True)
                        opStr = indO.group('op')
                # else:
                #     raise Exception('Something is wrong with the operators... %s' % string)
            ## if all went fine so far, split on operator and parse terms
            if opExt != None:
                partsOut = parts.group('pattOut').split(opStr)
                pi = 0
                while pi < len(partsOut):
                    if len(partsOut[pi].strip()) > 0:
                        t = Term.parseU(partsOut[pi], names)
                        if t != None:
                            r.extend(opExt,t)
                        else:
                            pi = len(partsOut)
                            r = None
                    pi+=1
        return r
    parseU = staticmethod(parseU)

    def parseAny(string, names=None):
        r = Query.parseU(string, names)
        if r == None:
            r = Query.parseTex(string, names)
            if r == None:
                r = Query.parse(string)
        return r
    parseAny = staticmethod(parseAny)
