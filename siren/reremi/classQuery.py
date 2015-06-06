import re, random, operator, itertools, codecs
from classSParts import  SParts
from redquery_parser import RedQueryParser
from grako.exceptions import * # @UnusedWildImport
import pdb

def recurse_numeric(b, function, args={}):
    if type(b) is list:
        out = 0
        for bi, bb in enumerate(b):
            nargs = dict(args)
            if "trace" in args:
                nargs["trace"] = [bi]+args["trace"]
            out += recurse_numeric(bb, function, nargs)
        return out
    else:
        return function(b, **args)

### WARNING THIS DOES NOT RECURSE ON NEGATIONS
def recurse_list(b, function, args={}):
    if type(b) is list:
        out = []
        for bi, bb in enumerate(b):
            nargs = dict(args)
            if "trace" in args:
                nargs["trace"] = [bi]+args["trace"]
            tou = recurse_list(bb, function, nargs)
            if type(tou) is list:
                out.extend(tou)
            elif tou is not None:
                out.append(tou)
        return out
    elif isinstance(b, Literal):
        return function(b, **args)

def recurse_deep(b, function, args={}):
    if type(b) is list:
        out = []
        for bi, bb in enumerate(b):
            nargs = dict(args)
            if "trace" in args:
                nargs["trace"] = [bi]+args["trace"]
            tmp = recurse_deep(bb, function, nargs)
            if tmp is not None:
                out.append(tmp)
        return out
    else:
        return function(b, **args)



class SYM:

    SYMU_OR = ur'\u2228'
    SYMU_AND = ur'\u2227'
    SYMU_NOT = ur'\u00ac '
    SYMU_LEQ = ur'\u2264'
    SYMU_EIN = ur'\u2208'
    SYMU_NIN = ur'\u2209'
    SYMU_NEQ = ur'\u2260'

    SYMU_ALPHA=u"\u2081\u2080"
    SYMU_BETA=u"\u2080\u2081"
    SYMU_GAMMA=u"\u2081\u2081"
    SYMU_DELTA=u"\u2080\u2080"
    SYMU_SETMIN=u"\u2216"

    SYMU_ARRTOP=u"\u2191"
    SYMU_ARRBOT=u"\u2193"
    
    SYMO_OR = 'OR'
    SYMO_AND = 'AND'
    SYMO_NOT = 'NOT '
    SYMO_LEQ = '<'
    SYMO_EIN = 'IN'
    SYMO_NIN = 'NOT IN'
    SYMO_NEQ = '~'

    SYMO_ALPHA="_10"
    SYMO_BETA="_01"
    SYMO_GAMMA="_11"
    SYMO_DELTA="_00"
    SYMO_SETMIN="\\"

    SYMO_ARRTOP="^"
    SYMO_ARRBOT="v"

    ## WITH UNICODE
    SYM_OR = SYMU_OR
    SYM_AND = SYMU_AND
    SYM_NOT = SYMU_NOT
    SYM_LEQ = SYMU_LEQ
    SYM_EIN = SYMU_EIN
    SYM_NIN = SYMU_NIN
    SYM_NEQ = SYMU_NEQ

    SYM_ALPHA=SYMU_ALPHA
    SYM_BETA=SYMU_BETA
    SYM_GAMMA=SYMU_GAMMA
    SYM_DELTA=SYMU_DELTA
    SYM_SETMIN=SYMU_SETMIN

    SYM_ARRTOP=SYMU_ARRTOP
    SYM_ARRBOT=SYMU_ARRBOT

    ## WITHOUT UNICODE
    # SYM_OR = SYMO_OR
    # SYM_AND = SYMO_AND
    # SYM_NOT = SYMO_NOT
    # SYM_LEQ = SYMO_LEQ
    # SYM_EIN = SYMO_EIN
    # SYM_NIN = SYMO_NIN
    # SYM_NEQ = SYMO_NEQ

    # SYM_ALPHA=SYMO_ALPHA
    # SYM_BETA=SYMO_BETA
    # SYM_GAMMA=SYMO_GAMMA
    # SYM_DELTA=SYMO_DELTA
    # SYM_SETMIN=SYMO_SETMIN

    # SYM_ARRTOP=SYMO_ARRTOP
    # SYM_ARRBOT=SYMO_ARRBOT

class Op(object):
    
    ops = {0: 'X', 1: '|', -1: '&'}
    opsTex = {0: 'X', 1: '$\lor$', -1: '$\land$'}
    opsU = {0: 'X', 1: SYM.SYM_OR, -1: SYM.SYM_AND}

    def __init__(self, nval=0):
        if type(nval) == bool :
            if nval:
                self.val = 1
            else:
                self.val = -1
        elif nval in Op.ops:
            self.val = nval
        else:
            raise Exception('Uninterpretable operator: %s !' % nval)
                
    def isSet(self):
        return self.val != 0

    def flip(self):
        self.val *= -1

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
        if other is None:
            return 1
        else:
            return cmp(self.val, other.val)

    def __hash__(self):
        return self.val
       
class Neg(object):
    symb = ['', '! ']
    symbTex = ['', '$\\neg$ ']
    symbU = ['', SYM.SYM_NOT]

    ################# START FOR BACKWARD COMPATIBILITY WITH XML
    patt = '(?P<neg>'+symb[1].strip()+')'
    ################# END FOR BACKWARD COMPATIBILITY WITH XML

    def __init__(self, nNeg=False):
        if nNeg == True or nNeg < 0:
            self.neg = -1
        else:
            self.neg = 1

    def copy(self):
        return Neg(self.neg)

    def boolVal(self):
        return self.neg < 0

    def flip(self):
        self.neg *= -1
    
    def __int__(self):
        return self.neg
    
    def __cmp__(self, other):
        if other is None:
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

class Term(object):
    
    pattVName = "v%d"
    type_id = 0

    ################# START FOR BACKWARD COMPATIBILITY WITH XML
    patt = '(?P<col>[^\\=<>'+ SYM.SYMU_LEQ + SYM.SYMU_EIN + SYM.SYMU_NIN +']+)'
    ################# END FOR BACKWARD COMPATIBILITY WITH XML
    
    def __init__(self, ncol):
        self.col = ncol

    def valRange(self):
        return [None, None]

    def setRange(self, newR):
        pass

#     def simple(self, neg):
#         return neg

    def copy(self):
        return Term(self.col)

    def cmpType(self, other):
        if other is None:
            return 1
        else:
            return cmp(self.type_id, other.type_id)
    
    def colId(self):
        return self.col
    
    def cmpCol(self, other):
        if other is None:
            return 1
        else:
            return cmp(self.col, other.col)
    
    def __str__(self):
        return (Term.pattVName + ' ') % self.col
    
class BoolTerm(Term):
    type_id = 1

    def valRange(self):
        return [True, True]
        
    def copy(self):
        return BoolTerm(self.col)
    
    def __cmp__(self, other):
        if self.cmpCol(other) == 0:
            return self.cmpType(other)
        else:
            return self.cmpCol(other)
        
    def __hash__(self):
        return self.col
    
    def __str__(self):
        return self.disp()

    def truthEval(self, variableV):
        return variableV

    def disp(self, neg=None, names = None, lenIndex=0):
        if type(neg) == bool:
            neg = Neg(neg)

        if neg is None:
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
            return ('%s'+Term.pattVName) % (strneg, self.col)

    def dispTex(self, neg, names = None):
        if type(neg) == bool:
            neg = Neg(neg)

        if type(names) == list  and len(names) > 0:
            return '%s%s' % ( neg.dispTex(), names[self.col])
        else:
            return ('%s$'+Term.pattVName+'$') % ( neg.dispTex(), self.col)

    def dispU(self, neg, names = None):
        if type(neg) == bool:
            neg = Neg(neg)

        if type(names) == list  and len(names) > 0:
            return u'%s%s' % ( neg.dispU(), names[self.col])
        else:
            return (u'%s'+Term.pattVName) % ( neg.dispU(), self.col)

    ################# START FOR BACKWARD COMPATIBILITY WITH XML
    patt = ['^\s*'+Neg.patt+'?\s*'+Term.patt+'\s*$']
    def parse(partsU):
        ncol = None
        if partsU is not None:
            neg = (partsU.group('neg') is not None)
            tmpcol = partsU.group('col').strip()
            try:
                ncol = int(tmpcol)
            except ValueError, detail:
                ncol = None
                raise Warning('In boolean term %s, column is not convertible to int (%s)\n'%(tmpcol, detail))
        if ncol is not None :
            return (neg, BoolTerm(ncol))
        return (None, None)
    parse = staticmethod(parse)
    ################# END FOR BACKWARD COMPATIBILITY WITH XML
    
class CatTerm(Term):
    type_id = 2
    
    def __init__(self, ncol, ncat):
        self.col = ncol
        self.cat = ncat

    def getCat(self):
        return self.cat
    
    def valRange(self):
        return [self.getCat(), self.getCat()]

    def setRange(self, cat):
        self.cat = cat #codecs.encode(cat, 'utf-8','replace')
            
    def copy(self):
        return CatTerm(self.col, self.cat)
            
    def __cmp__(self, other):
        if self.cmpCol(other) == 0:
            if self.cmpType(other) == 0:
                return cmp(self.cat, other.cat)
            else:
                return self.cmpType(other)
        else:
            return self.cmpCol(other)

    def truthEval(self, variableV):
        return variableV == self.cat
    
    def __hash__(self):
        return self.col*hash(self.cat)+(self.col-1)*(hash(self.cat)+1)

    def __str__(self):
        return self.disp()
    
    def disp(self, neg=None, names = None, lenIndex=0):
        if type(neg) == bool:
            neg = Neg(neg)

        if neg is None:
            strneg = ''
        else:
            strneg = neg.disp()
        strcat = '=%s' % self.cat
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
            return (('%s'+Term.pattVName) % (strneg, self.col)) + strcat

    def dispTex(self, neg, names = None):
        if type(neg) == bool:
            neg = Neg(neg)
        if neg.boolVal():
            symbIn = '\\in'
        else:
            symbIn = '\\not\\in'
        
        if type(names) == list  and len(names) > 0:
            return '%s %s %s' % (names[self.col], symbIn, self.cat)
        else:
            return ('$'+Term.pattVName+'$ %s %s') % (self.col, symbIn, self.cat)

    def dispU(self, neg, names = None):
        if type(neg) == bool:
            neg = Neg(neg)

        if neg.boolVal():
            symbIn = SYM.SYM_NEQ
        else:
            symbIn = '='
        if type(names) == list  and len(names) > 0:
            try:
                return ('[%s '+symbIn+' %s]') % (names[self.col], self.getCat())
            except UnicodeDecodeError:
                pdb.set_trace()
                self.getCat()
        else:
            return ('['+Term.pattVName+' '+symbIn+' %s]') % (self.col, self.getCat())

    ################# START FOR BACKWARD COMPATIBILITY WITH XML
    patt = ['^\s*'+Neg.patt+'?\s*'+Term.patt+'\s*\=\s*(?P<cat>\S*)\s*$']
    def parse(partsU):
        ncol = None
        if partsU is not None:
            neg = (partsU.group('neg') is not None)
            tmpcol = partsU.group('col').strip()
            try:
                ncol = int(tmpcol)
            except ValueError, detail:
                ncol = None
                raise Warning('In categorical term %s, column is not convertible to int (%s)\n'%(tmpcol, detail))
            try:
                cat = partsU.group('cat')
            except ValueError, detail:
                ncol = None
                raise Warning('In categorical term %s, category is not convertible to int (%s)\n'%(partsU.group('cat'), detail))
        if ncol is not None :
            return (neg, CatTerm(ncol, cat))
        return (None, None)
    parse = staticmethod(parse)
    ################# END FOR BACKWARD COMPATIBILITY WITH XML
    
class NumTerm(Term):
    type_id = 3
    
    def __init__(self, ncol, nlowb, nupb):
        if nlowb == float('-Inf') and nupb == float('Inf') or nlowb > nupb:
            raise Warning('Unbounded numerical term !')
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

    def valRange(self):
        return [self.lowb, self.upb]

    def setRange(self, bounds):
        if bounds[0] == float('-Inf') and bounds[1] == float('Inf') or bounds[0] > bounds[1]:
            raise Warning('Unbounded numerical term !')
        self.lowb = bounds[0]
        self.upb = bounds[1]
            
    def copy(self):
        return NumTerm(self.col, self.lowb, self.upb)

    def truthEval(self, variableV):
        return self.lowb <= variableV and variableV <= self.upb
                        
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
        
        if other is None:
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

        if neg is None:
            strneg = ''
        else:
            strneg = neg.disp()
            ### force float to make sure we have dots in the output
        if self.lowb > float('-Inf'):
            lb = '%s<' % float(self.lowb)
        else:
            lb = ''
        if self.upb < float('Inf'):
            ub = '<%s' % float(self.upb)
        else:
            ub = ''
        if lenIndex > 0 :
            lenIndex = max(lenIndex-len(lb)-len(ub),3)
            slenIndex = str(lenIndex)
        else:
            slenIndex = ''
        if type(names) == list  and len(names) > 0:
            lab = ('%'+slenIndex+'s') % names[self.col]
            if len(lab) > lenIndex & lenIndex > 0:
                lab = lab[:lenIndex]
            return lb + lab + ub
        else:
            return strneg+lb+(Term.pattVName % self.col) + ub

    def dispTex(self, neg, names = None):            
        prec = "0.4"
        if type(neg) == bool:
            neg = Neg(neg)
            ### force float to make sure we have dots in the output
        if self.lowb > float('-Inf'):
            lb = ('$[%'+prec+'f\\leq{}') % float(self.lowb)
        else:
            lb = '$['
        if self.upb < float('Inf'):
            ub = ('\\leq{}%'+prec+'f]$') % float(self.upb)
        else:
            ub = ']$'
        negstr = ' %s' % neg.dispTex()
        if type(names) == list  and len(names) > 0:
            idcol = '$ %s $' % names[self.col]
        else:
            idcol = Term.pattVName % self.col
        return ''+negstr+lb+idcol+ub+''

    def dispU(self, neg, names = None):
        if type(neg) == bool:
            neg = Neg(neg)
            ### force float to make sure we have dots in the output
        if self.lowb > float('-Inf'):
            lb = ('[%s '+ SYM.SYM_LEQ +' ') % float(self.lowb)
        else:
            lb = '['
        if self.upb < float('Inf'):
            ub = (' '+ SYM.SYM_LEQ +' %s]') % float(self.upb)
        else:
            ub = ']'
        negstr = '%s' % neg.dispU()
        if type(names) == list  and len(names) > 0:
            idcol = '%s' % names[self.col]
        else:
            idcol = Term.pattVName % self.col
        try:
            return negstr+lb+idcol+ub
        except UnicodeDecodeError:
            return negstr+lb+"v"+str(self.col)+ub

    ################# START FOR BACKWARD COMPATIBILITY WITH XML
    num_patt = '-?\d+\.\d+'
    patt = ['^\s*'+Neg.patt+'?\s*'+Term.patt+'\s*\>\s*(?P<lowb>'+num_patt+')\s*\<\s*(?P<upb>'+num_patt+')\s*$',
            '^\s*'+Neg.patt+'?\s*'+Term.patt+'\s*\>\s*(?P<lowb>'+num_patt+')\s*$',
            '^\s*'+Neg.patt+'?\s*'+Term.patt+'\s*\<\s*(?P<upb>'+num_patt+')\s*$']
    def parse(partsU):
        ncol=None
        if partsU is not None :
            neg = (partsU.group('neg') is not None)
            lowb = float('-inf')
            upb = float('inf')
            
            tmpcol = partsU.group('col').strip()
            try:
                ncol = int(tmpcol)
            except ValueError, detail:
                ncol = None
                raise Warning('In numerical term %s, column is not convertible to int (%s)\n'%(tmpcol, detail))

            if 'lowb' in partsU.groupdict() and partsU.group('lowb') is not None:
                tmplowbs = partsU.group('lowb')
                try:
                    lowb = float(tmplowbs)
                except ValueError, detail:
                    ncol = None
                    raise Warning('In numerical term %s, lower bound is not convertible to float (%s)\n'%(tmplowbs, detail))

            if 'upb' in partsU.groupdict() and partsU.group('upb') is not None:
                tmpupbs = partsU.group('upb')
                try:
                    upb = float(tmpupbs)
                except ValueError, detail:
                    ncol = None
                    raise Warning('In numerical term %s, upper bound is not convertible to float (%s)\n'%(tmpupbs, detail))
            
        if ncol is not None and (lowb != float('-inf') or upb != float('inf')) and lowb <= upb:
            return (neg, NumTerm(ncol, lowb, upb))
        return (None, None)
    parse = staticmethod(parse)
    ################# END FOR BACKWARD COMPATIBILITY WITH XML

               
class Literal(object):

    ### types ordered for parsing
    termTypes = [{'class': NumTerm }, \
                 {'class': CatTerm }, \
                 {'class': BoolTerm }]

    
    def __init__(self, nneg, nterm):
        self.term = nterm ## Already an Term instance
        self.neg = Neg(nneg)
#         self.neg = Neg(self.term.simple(nneg))

    def copy(self):
        return Literal(self.neg.boolVal(), self.term.copy())

    def valRange(self):
        if self.term.type_id == 1:
            return [not self.neg.boolVal(), not self.neg.boolVal()]
        else:
            return self.term.valRange()

    def __str__(self):
        return self.disp()

    def disp(self, names = None, lenIndex=0):
        return self.term.disp(self.neg, names, lenIndex)

    def dispTex(self, names = None):
        return self.term.dispTex(self.neg, names)
    
    def dispU(self, names = None):
        return self.term.dispU(self.neg, names)

    def tInfo(self, names = None):
        return self.term.tInfo(names)

    def __cmp__(self, other):
        if other is None or not isinstance(other, Literal):
            return 1
        elif cmp(self.term, other.term) == 0:
            return cmp(self.neg, other.neg)
        else:
            return cmp(self.term, other.term)
     
    def __hash__(self):
        return hash(self.term)+hash(self.neg)
    
    def isNeg(self):
        return self.neg.boolVal()

    def setNeg(self, neg):
        self.neg = Neg(neg)

    def flip(self):
        self.neg.flip()

    def truthEval(self, variableV):
        if self.isNeg():
            return not self.term.truthEval(variableV)
        else:
            return self.term.truthEval(variableV)

    def typeId(self):
        return self.term.type_id
            
    def col(self):
        return self.term.colId()

    ################# START FOR BACKWARD COMPATIBILITY WITH XML
    def parse(string):
        i = 0
        term = None
        while i < len(Literal.termTypes) and term is None:
            patts = Literal.termTypes[i]['class'].patt
            j = 0
            while j < len(patts) and term is None:
                parts = re.match(patts[j], string)
                if parts is not None:
                    (neg, term) = Literal.termTypes[i]['class'].parse(parts)
                j+=1
            i+=1
        if term is not None:
            return Literal(neg, term)
        else:
            return None
    parse = staticmethod(parse)
    ################# END FOR BACKWARD COMPATIBILITY WITH XML
            
class Query:
    diff_literals, diff_cols, diff_op, diff_balance, diff_length = range(1,6)
    side = 0
    def __init__(self, OR=True, buk=None):
        self.op = Op(OR)
        if buk is not None:
            self.buk = buk
        else:
            self.buk = []

    def __len__(self):
        if len(self.buk) == 0:
            return 0
        return recurse_numeric(self.buk, function =lambda x: int(isinstance(x, Literal)))

    def __hash__(self):
        if len(self) == 0:
            return 0
        return hash(self.op) + recurse_numeric(self.buk, function =lambda x, trace: hash(t)+sum(trace), args = {"trace": []})

    def max_depth(self): # Does the query involve some disjunction?
        if len(self) == 0:
            return 0
        return max(recurse_list(self.buk, function =lambda x, trace: len(trace), args = {"trace":[]}))

    def usesOr(self): # Does the query involve some disjunction?
        max_d = self.max_depth()
        return max_d > 1 or ( len(self) > 1  and self.op.isOr() )
    
    def opBuk(self, nb): # get operator for bucket nb (need not exist yet).
        if nb % 2 == 0: # even bucket: query operator, else other
            return self.op.copy()
        else: 
            return self.op.other()
        
    def copy(self):
        c = Query()
        c.op = self.op.copy()
        c.buk = recurse_deep(self.buk, function =lambda x: x.copy())
        return c

    def push_negation(self):
        def evl(b, flip=False):
            if isinstance(b, Literal):
                if flip:
                    b.flip()
                return (False, b) 
            else:
                now_flip = False
                neg = [bb for bb in b if isinstance(bb, Neg)]
                if len(neg) == 1:
                    b.remove(neg[0])
                    now_flip = True
                vs = []
                for bb in b:
                    sfliped, res = evl(bb, now_flip ^ flip)
                    if sfliped:
                        vs.extend(res)
                    else:
                        vs.append(res)
                return (now_flip, vs)
        if len(self) == 0:
            return
        sfliped, res =  evl(self.buk, False)
        self.buk = res
        if sfliped:
            self.op.flip()
        # print self
        # pdb.set_trace()
        # print "-------"

    def negate(self):
        if len(self) == 0:
            return
        neg = [bb for bb in self.buk if isinstance(bb, Neg)]
        if len(neg) == 1:
            self.buk.remove(neg[0])
        else:
            self.buk.insert(0, Neg(True))
        self.push_negation()
        # self.op.flip()
        # recurse_list(self.buk, function =lambda x: x.flip())
            
    def __cmp__(self, y):
        return self.compare(y)
            
    def compare(self, y): 
        if y is None:
            return 1
        try:
            if self.op == y.op and self.buk == y.buk:
                return 0
        except AttributeError:
            ### Such error means the buckets are not identical...
            pass
        
        if len(self) < len(y): ## nb of literals in the query, shorter better
            return Query.diff_length
        elif len(self) == len(y):
            if len(self.buk)  < len(y.buk) : ## nb of buckets in the query, shorter better
                return Query.diff_balance
            elif len(self.buk) == len(y.buk) :
                if self.op > y.op : ## operator
                    return Query.diff_op
                elif self.op == y.op :
                    if self.invCols() > y.invCols(): ## literals in the query
                        return Query.diff_cols
                    elif self.invCols() == y.invCols():
                        return Query.diff_literals
                    else:
                        return -Query.diff_cols
                else:
                    return -Query.diff_op
            else:
                return -Query.diff_balance
        else:
            return -Query.diff_length
    
    def comparePair(x0, x1, y0, y1): ## combined compare for pair
        if ( x0.op == y0.op and x0.buk == y0.buk and x1.op == y1.op and x1.buk == y1.buk ):
            return 0

        if len(x0) + len(x1) < len(y0) + len(y1): ## nb of terms in the query, shorter better
            return Query.diff_length
        
        elif len(x0) + len(x1) == len(y0) + len(y1):
            if len(x0.buk) + len(x1.buk) < len(y0.buk) + len(y1.buk): ## nb of sets of terms in the query, shorter better
                return Query.diff_balance
            elif len(x0.buk) + len(x1.buk) == len(y0.buk) + len(y1.buk):
                if max(len(x0), len(x1)) < max(len(y0), len(y1)): ## balance of the nb of terms in the query, more balanced is better
                    return Query.diff_balance
                elif max(len(x0), len(x1)) == max(len(y0), len(y1)):
                    if max(len(x0.buk), len(x1.buk) ) < max(len(y0.buk), len(y1.buk)): ## balance of the nb of sets of terms in the query, more balanced is better
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
                                        return Query.diff_literals
                                return -Query.diff_cols
                        return -Query.diff_op
            return -Query.diff_balance
        return -Query.diff_length
    comparePair = staticmethod(comparePair)
    
    def invCols(self):
        return set(recurse_list(self.buk, function =lambda term: term.col()))
    
    def invLiterals(self):
        return set(recurse_list(self.buk, function =lambda term: term))
    
    def makeIndexesNew(self, format_str):
        if len(self) == 0:
            return ""
        return recurse_list(self.reorderedLits()[1], function =lambda term, trace: format_str % {'col': term.col(), 'buk': ".".join(map(str,trace))}, args = {"trace":[]})
    
    def makeIndexes(self, format_str):
        if len(self) == 0:
            return ""
        return recurse_list(self.reorderedLits()[1], function =lambda term, trace: format_str % {'col': term.col(), 'buk': len(trace)}, args = {"trace":[]})
    
    ## return the truth value associated to a configuration
    def truthEval(self, config = {}):
        def evl(b, op, config = {}):
            if isinstance(b, Literal):
                return b.col() in config and b.truthEval(config[b.col()])                
            else:
                vs = [evl(bb, op.other(), config) for bb in b]
                if op.isOr():
                    return  sum(vs) > 0
                else:
                    return reduce(operator.mul, vs) > 0
        if len(self) == 0:
            return True
        cp = self.copy()
        cp.push_negation()
        return evl(cp.buk, cp.op, config)
    
    ## return the support associated to a query
    def recompute(self, side, data=None, restrict=None):
        def evl(b, op, side, data):
            if isinstance(b, Literal):
                return data.literalSuppMiss(side, b)
            else:
                vs = [evl(bb, op.other(), side, data) for bb in b]
                return SParts.partsSuppMissMass(op.isOr(), vs) 

        if len(self) == 0 or data==None:
            return (set(), set())
        else:
            cp = self.copy()
            cp.push_negation()
            sm = evl(cp.buk, cp.op, side, data) 
            if restrict is None:
                return sm
            else:
                return sm[0] & restrict, sm[1] & restrict

    def proba(self, side, data= None, restrict=None):
        def evl(b, op, side, data, restrict=None):
            if isinstance(b, Literal):
                if restrict is None:
                    return len(data.supp(side, b))/float(data.nbRows())
                else:
                    return len(data.supp(side, b) & restrict)/float(len(restrict))
            else:
                vs = [evl(bb, op.other(), side, data, restrict) for bb in b]
                return SParts.updateProbaMass(vs, op.isOr()) 

        if data is None:
            pr = -1
        elif len(self) == 0 :
            pr = 1
        else:
            cp = self.copy()
            cp.push_negation()
            pr = evl(cp.buk, cp.op, side, data, restrict)
        return pr

    def probaME(self, dbPr=None, side=None, epsilon=0):
        def evl(b, op, dbPr, side, epsilon):
            if isinstance(b, Literal):
                return dbPr.pointPrLiteral(side, literal, epsilon)                
            else:
                vs = [evl(bb, op.other(), dbPr, side, epsilon) for bb in b]
                return SParts.updateProbaMass(vs, op.isOr()) 

        if dbPr is None:
            pr = -1
        elif len(self) == 0 :
            pr = 1
        else:
            cp = self.copy()
            cp.push_negation()
            pr = evl(cp.buk, cp.op, dbPr, side, epsilon)
        return pr

    #### RESORT TODO FOR DEBUGGING
    def extend(self, op, literal, resort = True):
        if len(self) == 0:
            self.buk.append(literal)
        elif len(self) == 1:
            self.buk.append(literal)
            self.op = op
        elif op == self.op:
            self.buk.append(literal)
        else:
            self.op = self.op.other()
            self.buk = [self.buk, literal]
        if resort:
            def soK(x):
                if type(x) is list:
                    return -1
                else:
                    return x.col()
            self.buk.sort(key=lambda x: soK(x))

    def listLiterals(self):
        def evl(b, lits):
            for bb in b:
                if isinstance(bb, Literal):
                    lits.append(bb)
                elif not isinstance(bb, Neg):
                    evl(bb, lits)
        lits = []
        if len(self) > 0:
            evl(self.buk, lits)
        return lits
        
    def __str__(self):
        return self.disp()    

    def reorderedLits(self, b=None):
        if b is None:
            b = self.buk
        if isinstance(b, Literal):
            return (b.col(), b)
        elif isinstance(b, Neg):
            return (-1, b)
        else:
            if len(b) == 0:
                return ()
            vs = [self.reorderedLits(bb) for bb in b]
            vs.sort(key=lambda x: x[0])
            return (vs[0][0], [v[1] for v in vs])

    def reorderLits(self):
        if len(self) > 0:
            self.buk = self.reorderedLits()[1]

    def disp(self, names = None, lenIndex=0, style=""):
        def evl(b, op, names, lenIndex, style):
            if isinstance(b, Literal):
                return b.__getattribute__("disp"+style)(names)
            if isinstance(b, Neg):
                return "!NEG!"
            else:
                vs = [evl(bb, op.other(), names, lenIndex, style) for bb in b]
                if len(vs) == 1:
                    return vs[0]
                else:
                    jstr = " %s " % op.__getattribute__("disp"+style)()
                    pref = "( "
                    suff = " )"
                    if "!NEG!" in vs:
                        vs.remove("!NEG!")
                        pref = Neg(True).__getattribute__("disp"+style)() + "( "
                    return pref + jstr.join(vs) + suff

        if len(self) == 0 :
            if style == "":
                return '[]'
            else:
                return ""
        else:
            vs = [evl(bb, self.op.other(), names, lenIndex, style) for bb in self.buk]
            if len(vs) == 1:
                return vs[0]
            else:
                jstr = " %s " % self.op.__getattribute__("disp"+style)()
                pref = ""
                suff = ""
                if "!NEG!" in vs:
                    vs.remove("!NEG!")
                    pref = Neg(True).__getattribute__("disp"+style)() + "( "
                    suff = " )"
                return pref + jstr.join(vs) + suff
            #### old code to write the query justified in length lenField
            #### string.ljust(qstr, lenField)[:lenField]

            
    ################# START FOR BACKWARD COMPATIBILITY WITH XML
    def parseApd(string):
        bannchar = Op.ops[-1]+Op.ops[1]
        pattAny = '(?P<op>['+Op.ops[-1]+']|['+Op.ops[1]+'])'
        pattrn = '^(?P<pattIn>[^\\'+bannchar+']*)'+pattAny+'?(?P<pattOut>(?(op).*))$'
        op = None; r = None
        parts = re.match(pattrn, string)
        if parts is not None:
            r = Query()
        while parts is not None:
            t = Literal.parse(parts.group('pattIn'))
            if t is not None:
                r.extend(op, t, resort=False)
                if parts.group('op') is not None:
                    op = Op(parts.group('op')==Op.ops[1])
                    parts = re.match(pattrn, parts.group('pattOut'))
                else:
                    parts = None
            else:
                ## stop
                parts = None
                r = None
        if r is not None and len(r) == 0:
            r = Query()
        return r 
    parseApd = staticmethod(parseApd)
    ################# END FOR BACKWARD COMPATIBILITY WITH XML

    def parse(part, names = None):
        if len(part.strip()) == 0:
            return Query()
        qs = QuerySemantics(names)
        parser = RedQueryParser(parseinfo=False)
        try:
            tmp = parser.parse(part, "query", semantics=qs)
        except FailedParse as e:
            tmp = Query()
            raise Exception("Failed parsing query %s!\n\t%s" % (part, e))
        return tmp
    parse = staticmethod(parse)

# GENERATE PARSER:
#     python -m grako -m RedQuery -o redquery_parser.py redquery.ebnf (!!! REMOVE ABSOLUTE_IMPORT FROM GENERATED FILE)
# RUN:
#     python redquery_parser.py queries.txt QUERIES
class QuerySemantics(object):

    def __init__(self, names=None):
        self.names = names

    def query(self, ast):
        buk = []
        OR = 0
        if "conjunction" in ast:
            buk = ast["conjunction"]
            OR = False
        elif "disjunction" in ast:
            buk = ast["disjunction"]
            OR = True
        elif "literal" in ast:
            buk = ast["literal"].values()[0]
        if "mass_neg" in ast:
            buk.insert(0,Neg(True))
        return Query(OR, buk)

    def conjunction(self, ast):
        tmp = []
        for e in ast:
            if len(e) == 1:
                tmp.extend(e)
            else:
                tmp.append(e)
        return tmp

    def disjunction(self, ast):
        tmp = []
        for e in ast:
            if len(e) == 1:
                tmp.extend(e)
            else:
                tmp.append(e)
        return tmp

    def conj_item(self, ast):
        if "mass_neg" in ast.keys():
            del ast["mass_neg"]
            return [Neg(True)]+ast.values()[0]
        return ast.values()[0]

    def disj_item(self, ast):
        if "mass_neg" in ast.keys():
            del ast["mass_neg"]
            return [Neg(True)]+ast.values()[0]
        return ast.values()[0]

    def categorical_literal(self, ast):
        return [Literal(("neg" in ast) ^ ("cat_false" in ast.get("cat_test", {})),
                        CatTerm(self.parse_vname(ast.get("variable_name")), ast.get("category")))]

    def realvalued_literal(self, ast):
        return [Literal("neg" in ast, NumTerm(self.parse_vname(ast.get("variable_name")),
                                              float(ast.get("lower_bound", "-inf")),
                                              float(ast.get("upper_bound", "inf"))))]

    def boolean_literal(self, ast):
        return [Literal("neg" in ast, BoolTerm(self.parse_vname(ast.get("variable_name"))))]

    def variable_name(self, ast):
        return ast

    def category(self, ast):
        return ast

    def parse_vname(self, vname):
        tmp = re.match("v(?P<id>\d+)$", vname)
        if tmp is not None:
            return int(tmp.group("id"))
        elif self.names is not None:
            if type(vname) is str and type(self.names[0]) is unicode:
                vname = codecs.decode(v, 'utf-8','replace')
            if vname in self.names:
                return self.names.index(vname)
        else:
            print vname
            # pdb.set_trace()
            raise Exception("No variables names provided when needed!")

if __name__ == '__main__':
    import codecs
    from classData import Data
    import sys
    rep = "/home/galbrun/TKTL/redescriptors/data/vaalikone/"
    data = Data([rep+"vaalikone_profiles_all.csv", rep+"vaalikone_questions_all.csv", {}, "Na"], "csv")
    qsLHS = QuerySemantics(data.getNames(0))
    qsRHS = QuerySemantics(data.getNames(1))
    parser = RedQueryParser(parseinfo=False)

    with open("../../runs/vaalikone_new/vaali_named.csv") as f:
        header = None
        for line in f:
            if header is None:
                header = line.strip().split("\t")
            elif len(line.strip().split("\t")) >= 2:
                resLHS = parser.parse(line.strip().split("\t")[0], "query", semantics=qsLHS)
                resRHS = parser.parse(line.strip().split("\t")[1], "query", semantics=qsRHS)
                pdb.set_trace()
                print "----------"
                print line.strip()
                print "ORG   :", resLHS, "---", resRHS
                print len(resLHS.recompute(0, data)[0])
                print len(resRHS.recompute(1, data)[0])

                # cp = resLHS.copy()
                # resLHS.push_negation()
                # print "COPY  :", cp
                # print "PUSHED:", resLHS
                # cp.negate()
                # print "NEG   :", cp
                # print resLHS.recompute(0, data)
                # print resRHS.recompute(1, data)
                # pdb.set_trace()
                # print len(resLHS)
                # print resLHS.listLiterals()
                # tmp = resLHS.copy()
                # print tmp
                # tmp.negate()
                # print tmp
                # print resLHS.disp(style="U", names=data.getNames(0)), "\t", resRHS.disp(style="U")
                # print resLHS.makeIndexesNew('%(buk)s:%(col)i:')
                # resLHS.reorderLits()
                # print resLHS.disp(style="U", names=data.getNames(0)), "\t", resRHS.disp(style="U")
