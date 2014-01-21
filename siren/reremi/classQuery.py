import re, random
from classSParts import  SParts
import pdb

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

class Op:
    
    ops = {0: 'X', 1: '|', -1: '&'}
    opsTex = {0: 'X', 1: '$\lor$', -1: '$\land$'}
    opsU = {0: 'X', 1: SYM.SYM_OR, -1: SYM.SYM_AND}

    ### WITH UNICODE
    # patt = {-1: '(?P<op>[&]|'+opsU[-1]+'|(\$\\\\land\$))',
    #         1: '(?P<op>[|]|'+opsU[1]+'|(\$\\\\lor\$))'}
    # pattAny = '(?P<op>[&]|'+opsU[-1]+'|(\$\\\\land\$)|[|]|'+opsU[1]+'|(\$\\\\lor\$))'
    # bannchar = ops[-1]+opsU[-1]+ops[1]+opsU[1]

    ### WITHOUT UNICODE
    patt = {-1: '(?P<op>[&]|('+opsU[-1]+')|(\$\\\\land\$))',
            1: '(?P<op>[|]|('+opsU[1]+')|(\$\\\\lor\$))'}
    pattAny = '(?P<op>[&]|('+opsU[-1]+')|(\$\\\\land\$)|[|]|('+opsU[1]+')|(\$\\\\lor\$))'
    bannchar = ops[-1]+ops[1]

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
    
    def parse(string):
        for i in [-1,1]:
            if re.match("^\s*"+Op.patt[i]+"\s*$", string):
                return Op(i)
        return None
    parse = staticmethod(parse)
       
class Neg:
    symb = ['', '! ']
    symbTex = ['', '$\\neg$ ']

    symbU = ['', SYM.SYM_NOT]

    patt = '(?P<neg>'+symb[1].strip()+'|(\$\\\\neg\$)|'+symbU[1].strip()+')'

    def __init__(self, nNeg=False):
        if nNeg == True or nNeg < 0:
            self.neg = -1
        else:
            self.neg = 1

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

class Term:
    type_id = 0

    patt = '(?P<col>[^\\=<>'+ SYM.SYMU_LEQ + SYM.SYMU_EIN + SYM.SYMU_NIN +']+)'
    
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
        return '%i ' % self.col
    
class BoolTerm(Term):
    type_id = 1

    patt = ['^\s*'+Neg.patt+'?\s*'+Term.patt+'\s*$']

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
            return ('%s%'+slenIndex+'i ') % (strneg, self.col)

    def dispTex(self, neg, names = None):
        if type(neg) == bool:
            neg = Neg(neg)

        if type(names) == list  and len(names) > 0:
            if Query.side == 1:
                return '%s%s' % ( neg.dispTex(), names[self.col])
            else:
                return '\\textsc{%s%s}' % ( neg.dispTex(), names[self.col])

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

                    
    def parse(partsU, names=None):
        ncol = None
        if partsU is not None:
            neg = (partsU.group('neg') is not None)
            tmpcol = partsU.group('col').strip()
            if tmpcol.isdigit():
                try:
                    ncol = int(tmpcol)
                except ValueError, detail:
                    ncol = None
                    raise Warning('In boolean term %s, column is not convertible to int (%s)\n'%(tmpcol, detail))
            else: 
                if names is not None and tmpcol in names:
                    ncol = names.index(tmpcol)
        if ncol is not None :
            return (neg, BoolTerm(ncol))
        return (None, None)
    parse = staticmethod(parse)
    
class CatTerm(Term):
    type_id = 2
    
    patt = ['^\s*\[\s*'+Term.patt+'\s*(?P<neg>'+ SYM.SYMU_NEQ +')?(?(neg)|\=)\s*(?P<cat>\S*)\s*\]\s*$',
            '^\s*'+Term.patt+'\s*((?P<neg>\\\\not)\s*)?\\\\in\s*(?P<cat>\S*)\s*$',
            '^\s*'+Neg.patt+'?\s*'+Term.patt+'\s*\=\s*(?P<cat>\S*)\s*$']

    def __init__(self, ncol, ncat):
        self.col = ncol
        self.cat = ncat

    def valRange(self):
        return [self.cat, self.cat]

    def setRange(self, cat):
        self.cat = cat

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
        strcat = '=%s ' % self.cat
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
            return (('%s%'+slenIndex+'i') % (strneg, self.col)) + strcat

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
            return '%i %s %s' % (self.col, symbIn, self.cat)

    def dispU(self, neg, names = None):
        if type(neg) == bool:
            neg = Neg(neg)

        if neg.boolVal():
            symbIn = SYM.SYM_NEQ
        else:
            symbIn = '='
        if type(names) == list  and len(names) > 0:
            return ('[%s '+symbIn+' %s]') % (names[self.col], self.cat)
        else:
            return ('[%s '+symbIn+' %s]') % (self.col, self.cat)

    def parse(partsU, names=None):
        ncol = None
        if partsU is not None:
            neg = (partsU.group('neg') is not None)
            tmpcol = partsU.group('col').strip()
            if tmpcol.isdigit():
                try:
                    ncol = int(tmpcol)
                except ValueError, detail:
                    ncol = None
                    raise Warning('In categorical term %s, column is not convertible to int (%s)\n'%(tmpcol, detail))
            else: 
                if names is not None and tmpcol in names:
                    ncol = names.index(tmpcol)
            try:
                cat = partsU.group('cat')
            except ValueError, detail:
                ncol = None
                raise Warning('In categorical term %s, category is not convertible to int (%s)\n'%(partsU.group('cat'), detail))
        if ncol is not None :
            return (neg, CatTerm(ncol, cat))
        return (None, None)
    parse = staticmethod(parse)

    
class NumTerm(Term):
    type_id = 3

    num_patt = '-?\d+\.\d+'
    
    patt = ['^\s*'+Neg.patt+'?\s*\$\s*\[\s*(?P<lowb>'+num_patt+')\s*\\\\leq\{\}\s*'+Term.patt+'\s*\\\\leq\{\}\s*(?P<upb>'+num_patt+')\s*\]\s*\$\s*$',
            '^\s*'+Neg.patt+'?\s*\$\s*\[\s*(?P<lowb>'+num_patt+')\s*\\\\leq\{\}\s*'+Term.patt+'\s*\]\s*\$\s*$',
            '^\s*'+Neg.patt+'?\s*\$\s*\[\s*'+Term.patt+'\s*\\\\leq\{\}\s*(?P<upb>'+num_patt+')\s*\]\s*\$\s*$',
            '^\s*'+Neg.patt+'?\s*\[\s*(?P<lowb>'+num_patt+')\s*[' + SYM.SYMU_LEQ +'|<]\s*'+Term.patt+'\s*[' + SYM.SYMU_LEQ +'<]\s*(?P<upb>'+num_patt+')\s*\]\s*$',
            '^\s*'+Neg.patt+'?\s*\[\s*(?P<lowb>'+num_patt+')\s*[' + SYM.SYMU_LEQ +'|<]\s*'+Term.patt+'\s*\]\s*$',
            '^\s*'+Neg.patt+'?\s*\[\s*'+Term.patt+'\s*[' + SYM.SYMU_LEQ +'<]\s*(?P<upb>'+num_patt+')\s*\]\s*$',
            '^\s*'+Neg.patt+'?\s*'+Term.patt+'\s*\>\s*(?P<lowb>'+num_patt+')\s*\<\s*(?P<upb>'+num_patt+')\s*$',
            '^\s*'+Neg.patt+'?\s*'+Term.patt+'\s*\>\s*(?P<lowb>'+num_patt+')\s*$',
            '^\s*'+Neg.patt+'?\s*'+Term.patt+'\s*\<\s*(?P<upb>'+num_patt+')\s*$']
    
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
            lb = '>%s' % float(self.lowb)
        else:
            lb = ''
        if self.upb < float('Inf'):
            ub = '<%s' % float(self.upb)
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
            if Query.side == 1:
                idcol = '$ %s $' % names[self.col]
            else:
                idcol = '$ \\textsc{%s} $' % names[self.col]
        else:
            idcol = '%i' % self.col
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
            ub = (u' '+ SYM.SYM_LEQ +' %s]') % float(self.upb)
        else:
            ub = ']'
        negstr = u'%s' % neg.dispU()
        if type(names) == list  and len(names) > 0:
            idcol = '%s' % names[self.col]
        else:
            idcol = '%i' % self.col
        return ''+negstr+lb+idcol+ub+''

    def parse(partsU, names=None):
        ncol=None
        if partsU is not None :
            neg = (partsU.group('neg') is not None)
            lowb = float('-inf')
            upb = float('inf')
            
            tmpcol = partsU.group('col').strip()
            if tmpcol.isdigit():
                try:
                    ncol = int(tmpcol)
                except ValueError, detail:
                    ncol = None
                    raise Warning('In numerical term %s, column is not convertible to int (%s)\n'%(tmpcol, detail))
            else: 
                if names is not None and tmpcol in names:
                    ncol = names.index(tmpcol)

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

               
class Literal:

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
        if other is None:
            return 1
        elif cmp(self.term, other.term) == 0:
            return cmp(self.neg, other.neg)
        else:
            return cmp(self.term, other.term)
     
    def __hash__(self):
        return hash(self.term)+hash(self.neg)
    
    def isNeg(self):
        return self.neg.boolVal()

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
    
    def parse(string, names=None):
        i = 0
        term = None
        while i < len(Literal.termTypes) and term is None:
            patts = Literal.termTypes[i]['class'].patt
            j = 0
            while j < len(patts) and term is None:
                parts = re.match(patts[j], string)
                if parts is not None:
                    (neg, term) = Literal.termTypes[i]['class'].parse(parts, names)
                j+=1
            i+=1
        if term is not None:
            return Literal(neg, term)
        else:
            return None
    parse = staticmethod(parse)
            
class Query:
    diff_literals, diff_cols, diff_op, diff_balance, diff_length = range(1,6)
    side = 0
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

    def usesOr(self): # Does the query involve some disjunction?
        if len(self.buk) == 0:
            return False
        elif len(self.buk) == 1:
            if len(self.buk[0]) == 1:
                return False
            else:
                return self.op.isOr()
        else:
            return True
    
    def opBuk(self, nb): # get operator for bucket nb (need not exist yet).
        if nb % 2 == 0: # even bucket: query operator, else other
            return self.op.copy()
        else: 
            return self.op.other()
        
    def nbBuk(self): 
        return len(self.buk)

    def copy(self):
        c = Query()
        c.op = self.op.copy()
        c.buk = []
        for buk in self.buk:
            c.buk.append(set([t.copy() for t in buk if t is not None]))
        return c

    def negate(self):
        self.op.flip()
        for buk in self.buk:
            for t in buk:
                t.flip()

    def dependencies(self, pos=True):
        dQs = []
        ### IF ONLY ONE ELEMENT OR DISJUNCTION, JUST COPY
        if len(self) == 1 \
           or (pos and self.opBuk(len(self.buk)-1).isOr()) \
           or (not pos and not self.opBuk(len(self.buk)-1).isOr()):
            dQs.append(self.copy())
        ### ELSE IF THE OUT MOST IS CONJUNCTION, SPLIT
        else:
            if len(self.buk) > 1:
                c = Query()
                c.op = self.op.copy()
                c.buk = []
                for buk in self.buk[:-1]:
                    c.buk.append(set([t.copy() for t in buk if t is not None]))
                dQs.append(c)
            for t in self.buk[-1]:
                if t is not None:
                    c = Query()
                    c.buk.append(set([t.copy()]))
                    dQs.append(c)
        if not pos:
            for q in dQs:
                q.negate()
        return dQs
            
    def __cmp__(self, y):
        return self.compare(y)
            
    def compare(self, y): 
        if y is None:
            return 1
        if self.op == y.op and self.buk == y.buk:
            return 0
        
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
    
    def extend(self, op, literal):
        if len(self) == 0:
            self.buk.append(set([literal]))
        elif len(self) == 1:
            self.buk[-1].add(literal)
            self.op = op
        elif op == self.opBuk(len(self.buk)-1):
            self.buk[-1].add(literal)
        else:
            self.buk.append(set([literal]))

    def invCols(self):
        invCols = set()
        for buk in self.buk :
            for literal in buk:
                invCols.add(literal.col())
        return invCols
    
    def invLiterals(self):
        invLiterals = set()
        for buk in self.buk :
            for literal in buk:
                invLiterals.add(literal)
        return invLiterals
    
    def makeIndexes(self, format_str):
        indexes = []
        for buk_nb in range(len(self.buk)) :
            for literal in list(self.buk[buk_nb]) :
                indexes.append(format_str % {'col': literal.col(), 'buk': buk_nb}) 
        return indexes

    ## return the truth value associated to a configuration
    def truthEval(self, config = {}):
        tv = True
        if len(self) > 0:
            op = self.op
            for buk in self.buk:
                for literal in buk:
                    tmp = literal.col() in config and literal.truthEval(config[literal.col()])
                    if op.isOr():
                        tv = tv or tmp
                    else:
                        tv = tv and tmp
                op = op.other()
        return tv
    
    ## return the support associated to a query
    def recompute(self, side, data=None, restrict=None):

        if len(self) == 0 or data==None:
            sm = (set(), set())
        else:
            sm = None
            
            if len(self) > 0:
                op = self.op
                for buk in self.buk:
                    for literal in buk:
                        sm  = SParts.partsSuppMiss(op.isOr(), sm, data.literalSuppMiss(side, literal))
                    op = op.other()
        if restrict is None:
            return sm
        else:
            return sm[0] & restrict, sm[1] & restrict
          
    def proba(self, side, data= None, restrict=None):
        if data==None:
            pr = -1
        elif len(self) == 0 :
            pr = 1
        else:
            pr = -1
            if len(self) > 0:
                op = self.op
                for buk in self.buk:
                    for literal in buk:
                        if restrict is None:
                            pr = SParts.updateProba(pr, len(data.supp(side, literal))/float(data.nbRows()), op.isOr())
                        else:
                            pr = SParts.updateProba(pr, len(data.supp(side, literal) & restrict)/float(len(restrict)), op.isOr())
                        ##print '%s : pr=%f (%s %f)' % (literal, pr, op, len(data.supp(side, literal))/float(data.nbRows()) )
                    op = op.other()
        return pr

    def probaME(self, dbPr=None, side=None, epsilon=0):
        if dbPr==None:
            pr = -1
        elif len(self) == 0 :
            pr = 1
        else:
            pr = -1
            if len(self) > 0:
                op = self.op
                for buk in self.buk:
                    for literal in buk:
                        pr = SParts.updateProba(pr, dbPr.pointPrLiteral(side, literal, epsilon), op.isOr())
                    op = op.other()
        return pr
    
#     def invLiterals(self):
#         invLiterals = []
#         OR = self.opBukIsOR(1)
#         for part in self.query[1:] :
#             spart = list(part)
#             spart.sort()
#             for term in spart :
#                 invTerms.append((query_termId(term), query_termNot(term), OR))    
#             OR = not OR
#         return invTerms
    

    
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
#                 cliterals = list(cbuk)
#                 cliterals.sort()
#                 for literal in cliterals:
#                     spp = len(data.supp(side, literal));
#                     string += '%s%s (%i,%f)' % (op, literal.disp(lenIndex, names), spp, spp/float(data.nbRows()) )
#                 op = op.other()
#         return string[1:]

    def disp(self, names = None, lenIndex=0):
        if len(self) == 0 :
            string = '[]'
        else:
            string = ''
            op = self.op
            for ci, cbuk in enumerate(self.buk):
                cliterals = list(cbuk)
                cliterals.sort()
                for ti, literal in enumerate(cliterals):
                    if ti != 0 or ci != 0:
                        string += '%s ' % op
                    string += literal.disp(names, lenIndex)
                op = op.other()
        return string.strip()

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
                cliterals = list(cbuk)
                cliterals.sort()
                for literal in cliterals:
                    if first == 0:
                        first = 1
                        string += '%s' % (literal.dispTex(names))
                    else:
                        string += ' %s %s' % (op.dispTex(), literal.dispTex(names))
                op = op.other()
        return string.strip()

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
                cliterals = list(cbuk)
                cliterals.sort()
                for literal in cliterals:
                    if first == 0:
                        first = 1
                        string += '%s' % (literal.dispU(names))
                    else:
                        string += ' %s %s' % (op.dispU(), literal.dispU(names))
                op = op.other()
        return string.strip()

    def listLiterals(self):
        lti = []
        if len(self) > 0 :
            for cbuk in self.buk:
                cliterals = list(cbuk)
                cliterals.sort()
                for literal in cliterals:
                    lti.append(literal)
        return lti

    def parseApd(string, names=None):
        pattrn = '^(?P<pattIn>[^\\'+Op.bannchar+']*)'+Op.pattAny+'?(?P<pattOut>(?(op).*))$'
        op = None; r = None
        parts = re.match(pattrn, string)
        if parts is not None:
            r = Query()
        while parts is not None:
            t = Literal.parse(parts.group('pattIn'), names)
            if t is not None:
                r.extend(op,t)
                if parts.group('op') is not None:
                    op = Op.parse(parts.group('op'))
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
    
    def parsePar(string, names=None):
        r = None
        parts = re.match(ur'^\s*(\(\s*(?P<pattIn>.*)\s*\))*\s*(?P<pattOut>[^()]*)\s*$', string)
        if parts is not None:
            opExt = None
            ## parse inner query
            if parts.group('pattIn') is not None:
                r = Query.parsePar(parts.group('pattIn'), names)
            else:
                r = Query()
            ## identify operator
            if r is not None:
                indA = re.search(Op.patt[-1], parts.group('pattOut'))
                indO = re.search(Op.patt[1], parts.group('pattOut'))
                if indA is None and indO is None:
                    if not r.opBuk(len(r)).isSet():
                        opExt = Op()
                        opStr = Op.ops[-1]
                elif indA is not None and indO is None:
                    if not r.opBuk(r.nbBuk()-1).isAnd():
                        opExt = Op(False)
                        opStr = indA.group('op')
                elif indA is None and indO is not None:
                    if not r.opBuk(r.nbBuk()-1).isOr():
                        opExt = Op(True)
                        opStr = indO.group('op')
                # else:
                #     raise Exception('Something is wrong with the operators... %s' % string)
            ## if all went fine so far, split on operator and parse literals
            if opExt is not None:
                partsOut = parts.group('pattOut').split(opStr)
                pi = 0
                while pi < len(partsOut):
                    if len(partsOut[pi].strip()) > 0:
                        t = Literal.parse(partsOut[pi], names)
                        if t is not None:
                            r.extend(opExt,t)
                        else:
                            ### stop here
                            pi = len(partsOut)
                            r = None
                    pi+=1
        if r is not None and len(r) == 0:
            r = None
        return r
    parsePar = staticmethod(parsePar)

    def parse(string, names=None):
        #### TODO Check bug
        if not re.search("[a-zA-Z0-9]", string):
            print "AA", string
            return Query()
        r = Query.parsePar(string, names)
        if r is None:
            r = Query.parseApd(string, names)
        if r is None:
            print "BB", string
            r = Query()
        return r
    parse = staticmethod(parse)

