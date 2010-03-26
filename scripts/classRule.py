import re, pdb

class Op:
    
    ops = {0: 'X', 1: '|', -1: '&'}
    
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
    
    def same(self):
        return Op(self.val)
    
    def other(self):
        return Op(-self.val)
    
    def __int__(self):
        return self.val
    
    def isOr(self):
        return self.val == 1
    
    def __str__(self):
        return Op.ops[self.val]+' '

    def __cmp__(self, other):
        if other == None:
            return 1
        else:
            return cmp(2*self.val*self.val+self.val, 2*other.val*other.val+other.val)

    def __hash__(self):
        return self.val
    
    def parse(parts, pos):
        for (k, v) in Op.ops.iteritems():
            if v == parts[pos]:
                return (Op(k), pos+1)
        return (None, pos)
    parse = staticmethod(parse)
       
class Neg:
    symb = ['', '! ']

    def __init__(self, nNeg=False):
        if nNeg == True or nNeg < 0:
            self.neg = -1
        else:
            self.neg = 1

    def boolVal(self):
        return self.neg < 0
    
    def __str__(self):
        return Neg.symb[self.boolVal()]
    
    def __int__(self):
        return self.neg
    
    def __cmp__(self, other):
        if other == None:
            return 1
        else:
            return cmp(self.neg, other.neg)

    def __hash__(self):
        return self.neg

    def parse(parts, pos):
        if Neg.symb[1].startswith(parts[pos]):
            return (Neg(True), pos+1)
        else:
            return (Neg(False), pos)
    parse = staticmethod(parse)

class Item:
    type_id = 0
    
    def __init__(self, ncol):
        self.col = ncol
           
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
    
    def __cmp__(self, other):
        if self.cmpCol(other) == 0:
            return self.cmpType(other)
        else:
            return self.cmpCol(other)
        
    def __hash__(self):
        return self.col
    
    def disp(self, lenIndex=0, names = None):
        if lenIndex > 0 :
            lenIndex = str(lenIndex)
        else:
            lenIndex = ''
        if type(names) == list :
            return ('%'+lenIndex+'s ') % names[self.col]
        else:
            return ('%'+lenIndex+'i ') % self.col

    def __str__(self):
        return self.disp()
            
    def parse(parts, pos):
        ok = True
        try:
            ncol = int(parts[pos])
        except ValueError, detail:
            raise Warning('In boolean item %s, column is not convertible to int (%s)\n'%(parts[pos], detail))
            ok = False
        if ok :
            return (BoolItem(ncol), pos+1)
        return (None, pos)
    parse = staticmethod(parse)
    
class CatItem(Item):
    type_id = 2
    
    def __init__(self, ncol, ncat):
        self.col = ncol
        self.cat = ncat
            
    def __cmp__(self, other):
        if self.cmpCol(other) == 0:
            if self.cmpType(other) == 0:
                return cmp(self.cat, other.cat)
            else:
                return self.cmpType(other)
        else:
            return self.cmpCol(other)
    
    def __hash__(self):
        return self.col*self.cat+(self.col-1)*(self.cat+1)
    
    def disp(self, lenIndex=0, names = None):
        if lenIndex > 0 :
            lenIndex = str(lenIndex)
        else:
            lenIndex = ''
        if type(names) == list :
            return ('%'+lenIndex+'s=%i ') % (names[self.col], self.cat)
        else:
            return ('%'+lenIndex+'i=%i ') % (self.col, self.cat)

    def __str__(self):
        return self.disp()
    
    def parse(parts, pos):
        partsU = parts[pos].split('=')
        if len(partsU) == 2:
            ok = True
            try:
                ncat = int(partsU[1])
            except ValueError, detail:
                raise Warning('In categorical item %s, category is not convertible to int (%s)\n'%(parts[pos], detail))
                ok = False
            try:
                ncol = int(partsU[0])
            except ValueError, detail:
                raise Warning('In categorical item %s, column is not convertible to int (%s)\n'%(parts[pos], detail))
                ok = False
            if ok:
                return (CatItem(ncol, ncat), pos+1)
        return (None, pos)
    parse = staticmethod(parse)

class NumItem(Item):
    type_id = 3
    
    def __init__(self, ncol, nlowb, nupb):
        self.col = ncol
        self.lowb = nlowb
        self.upb = nupb
            
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
        return int(self.col*self.lowb*self.upb-(self.col)*(self.lowb+1)*(self.upb-1))
    
    def disp(self, lenIndex=0, names = None):
        if lenIndex > 0 :
            lenIndex = str(lenIndex)
        else:
            lenIndex = ''
        if type(names) == list :
            return ('%'+lenIndex+'s>%f<%f ') % (names[self.col], self.lowb, self.upb)
        else:
            return ('%'+lenIndex+'i>%f<%f ') % (self.col, self.lowb, self.upb)

    def __str__(self):
        return self.disp()
    
    def parse(parts, pos):
        partsU = parts[pos].split('<')
        if len(partsU) == 2:
            partsV = partsU[0].split('>')
            if len(partsV) == 2:
                ok = True
                try:
                    nupb = float(partsU[1])
                except ValueError, detail:
                    raise Warning('In numerical item %s, upper bound is not convertible to float (%s)\n'%(parts[pos], detail))
                    ok = False
                try:
                    nlowb = float(partsV[1])
                except ValueError, detail:
                    raise Warning('In numerical item %s, lower bound is not convertible to float (%s)\n'%(parts[pos], detail))
                    ok = False
                try:
                    ncol = int(partsV[0])
                except ValueError, detail:
                    raise Warning('In numerical item %s, column is not convertible to int (%s)\n'%(parts[pos], detail))
                    ok = False
                if ok:
                    return (NumItem(ncol, nlowb, nupb), pos+1)
        return (None, pos+1)
    parse = staticmethod(parse)     
                   
class Term:

    itemTypes = [{'class': NumItem,  'match':'\d+\>\d+(\.\d+)?\<\d+(\.\d+)?$'}, \
                 {'class': CatItem,  'match':'\d+\=\d+?$'}, \
                 {'class': BoolItem, 'match':'\d+$'}]
    
    def __init__(self, nneg, ncol, v1=None, v2=None):
        if type(ncol) == int:
            self.neg = Neg(nneg)
            if v1 == None and v2 == None:
                self.item = BoolItem(ncol)
            elif v2 == None:
                self.item = CatItem(ncol, v1)
            else:
                self.item = NumItem(ncol, v1, v2)
        else:
            self.neg = nneg  ## Already a Neg instance
            self.item = ncol ## Already an Item instance

    def disp(self, lenIndex=0, names = None):
        return '%s%s' % (self.neg, self.item.disp(lenIndex, names))

    def __str__(self):
        return self.disp()

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
    
    def parse(parts, pos):
        tmp_pos = pos
        (neg, pos) = Neg.parse(parts, pos)
        i = 0
        item = None
        while i < len(Term.itemTypes) and item == None:
            if (re.match(Term.itemTypes[i]['match'], parts[pos])):
                (item, pos) = Term.itemTypes[i]['class'].parse(parts, pos)
            i+=1
        if pos - tmp_pos in [1, 2]:
            return (Term(neg, item), pos)
        else:
            return (None, tmp_pos)
    parse = staticmethod(parse)
            
class Rule:
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
        if nb % 2 == 0: # even bucket: rule operator, else other
            return self.op.same()
        else: 
            return self.op.other()

    def copy(self):
        c = Rule()
        c.op = self.op
        c.buk = []
        for buk in self.buk:
            c.buk.append(set(buk))
        return c
            
    def compare(x, y): ## same as compare pair with empty right
        if x.op == y.op and x.buk == y.buk:
            return 0
        
        if len(x) < len(y): ## nb of terms in the rule, shorter better
            return Rule.diff_length
        elif len(x) == len(y):
            if len(x.buk)  < len(y.buk) : ## nb of buckets in the rule, shorter better
                return Rule.diff_balance
            elif len(x.buk) == len(y.buk) :
                if x.op > y.op : ## operator
                    return Rule.diff_op
                elif x.op == y.op :
                    if x.invCols() > y.invCols(): ## terms in the rule
                        return Rule.diff_cols
                    elif x.invCols() == y.invCols():
                        return Rule.diff_terms
                    else:
                        return -Rule.diff_cols
                else:
                    return -Rule.diff_op
            else:
                return -Rule.diff_balance
        else:
            return -Rule.diff_length
    compare = staticmethod(compare)
    
    def __cmp__(self, other):
        if other == None:
            return 1
        else:
            return Rule.compare(self, other)
    
    def comparePair(x0, x1, y0, y1):
        if ( x0.op == y0.op and x0.buk == y0.buk and x1.op == y1.op and x1.buk == y1.buk ):
            return 0

        if len(x0) + len(x1) < len(y0) + len(y1): ## nb of items in the rule, shorter better
            return Rule.diff_length
        
        elif len(x0) + len(x1) == len(y0) + len(y1):
            if len(x0.buk) + len(x1.buk) < len(y0.buk) + len(y1.buk): ## nb of sets of items in the rule, shorter better
                return Rule.diff_balance
            elif len(x0.buk) + len(x1.buk) == len(y0.buk) + len(y1.buk):
                if max(len(x0), len(x1)) < max(len(y0), len(y1)): ## balance of the nb of items in the rule, more balanced is better
                    return Rule.diff_balance
                elif max(len(x0), len(x1)) == max(len(y0), len(y1)):
                    if max(len(x0.buk), len(x1.buk) ) < max(len(y0.buk), len(y1.buk)): ## balance of the nb of sets of items in the rule, more balanced is better
                        return Rule.diff_balance
                    
                    elif max(len(x0.buk), len(x1.buk) ) == max(len(y0.buk), len(y1.buk)):
                        if x0.op > y0.op : ## operator on the left
                            return Rule.diff_op
                        elif x0.op == y0.op:
                            if x1.op > y1.op : ## operator on the right
                                return Rule.diff_op
                            elif x1.op == y1.op:
                                if x0.invCols() > y0.invCols() :
                                    return Rule.diff_cols
                                elif x0.invCols() == y0.invCols() :
                                    if x1.invCols() > y1.invCols() :
                                        return Rule.diff_cols
                                    elif x1.invCols() == y1.invCols() :
                                        return Rule.diff_terms
                                return -Rule.diff_cols
                        return -Rule.diff_op
            return -Rule.diff_balance
        return -Rule.diff_length
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

    def parse(string):
        parts = string.split()
        if len(parts) > 0:
            r = Rule()
            (op, pos) = (Op(0), 0)
            (t, pos) = Term.parse(parts, pos)
            while pos < len(parts) and (op != None) and (t != None):
                r.extend(op,t)
                (op, pos) = Op.parse(parts, pos)
                (t, pos) = Term.parse(parts, pos)
            if (op != None) and (t != None):
                r.extend(op,t)
                return r
        return None
    parse = staticmethod(parse)

    def disp(self, lenIndex=0, names = None):
        if len(self) == 0 :
            string = '[]'
        else:
            string = ''
            op = self.op
            for cbuk in self.buk:
                cterms = list(cbuk)
                cterms.sort()
                for term in cterms:
                    string += '%s%s' % (op, term.disp(lenIndex, names))
                op = op.other()
            string = string[2:]
        return string
    
    def __str__(self):
        return self.disp()    
         
    ## return the support associated to a rule
    def recompute(self, side, data= None):

        if len(self) == 0 or data==None:
            supp = set()
        else:
            ## initialize support
            sterms = list(self.buk[0])
            sterms.sort()
            supp = data.supp(side, sterms[0])

            if len(self) > 1:
                op = self.op
                for buk in self.buk:
                    for term in buk:
                        if op.isOr() :
                            supp |= data.supp(side, term)
                        else :
                            supp &= data.supp(side, term)
                    op = op.other()
        return supp
    
#     def invTerms(self):
#         invTerms = []
#         OR = self.opBukIsOR(1)
#         for part in self.rule[1:] :
#             spart = list(part)
#             spart.sort()
#             for item in spart :
#                 invItems.append((rule_itemId(item), rule_itemNot(item), OR))    
#             OR = not OR
#         return invItems
    
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
    
