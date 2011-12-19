import re, pdb
from classSParts import  SParts

class Op:
    
    ops = {0: 'X', 1: '|', -1: '&'}
    printops = {0: 'X', 1: '\lor', -1: '\land'}
    
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

    def ind(self):
        if self.val == -1:
            return 0
        else:
            return 1

    def copy(self):
        return Op(self.val)
    
    def other(self):
        return Op(-self.val)
    
    def __int__(self):
        return self.val
    
    def isOr(self):
        return self.val == 1
    
    def __str__(self):
        return Op.ops[self.val]+' '

    def opStr(self):
        return Op.ops[self.val]

    def dispPrint(self):
        return Op.printops[self.val]

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
    patt = '(?P<col>\d+)$'

    def copy(self):
        return BoolItem(self.col)
    
    def __cmp__(self, other):
        if self.cmpCol(other) == 0:
            return self.cmpType(other)
        else:
            return self.cmpCol(other)
        
    def __hash__(self):
        return self.col
    
    def disp(self, lenIndex=0, names = None):
        if lenIndex > 0 :
            lenIndex = max(lenIndex-1,3)
            slenIndex = str(lenIndex)
        else:
            slenIndex = ''
        if type(names) == list  and len(names) > 0:
            lab = ('%'+slenIndex+'s') % names[self.col]
            if len(lab) > lenIndex & lenIndex > 0:
                lab = lab[:lenIndex]
            return lab + ' '
        else:
            return ('%'+slenIndex+'i ') % self.col

    def __str__(self):
        return self.disp()

    def dispPrint(self, neg, names = None):
        if type(names) == list  and len(names) > 0:
            if neg:
                return '\\neg %s' % names[self.col]
            else:
                return '%s' % names[self.col]
        
        else:
            if neg:
                return '\\neg %i' % self.col
            else:
                return '%i' % self.col

    def parse(part):
        partsU = re.match(BoolItem.patt, part)
        if partsU != None:
            ok = True
            try:
                ncol = int(partsU.group('col'))
            except ValueError, detail:
                raise Warning('In boolean item %s, column is not convertible to int (%s)\n'%(part, detail))
                ok = False
            if ok :
                return BoolItem(ncol)
    parse = staticmethod(parse)
    
class CatItem(Item):
    type_id = 2
    patt = '(?P<col>\d+)\=(?P<cat>\d+?)$'
    
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
    
    def disp(self, lenIndex=0, names = None):
        strcat = '=%i ' % self.cat
        if lenIndex > 0 :
            lenIndex = max(lenIndex-len(strcat),3)
            slenIndex = str(lenIndex)
        else:
            slenIndex = ''
        if type(names) == list  and len(names) > 0:
            lab = ('%'+slenIndex+'s') % names[self.col]
            if len(lab) > lenIndex & lenIndex > 0:
                lab = lab[:lenIndex]
            return lab + strcat
        else:
            return (('%'+slenIndex+'i') % self.col) + strcat

    def __str__(self):
        return self.disp()


    def dispPrint(self, neg, names = None):
        if neg:
            instr = '\\not\\in'
        else:
            instr= '\\in'
        if type(names) == list  and len(names) > 0:
            idcol = '%s ' % names[self.col]
        else:
            idcol = '%i' % self.col
        catstr = '%i' % self.cat
        return ' '+idcol+' '+instr+catstr+' '

    
    def parse(part):
        partsU = re.match(CatItem.patt, part)
        if partsU != None :
            ok = True
            try:
                ncat = int(partsU.group('cat'))
            except ValueError, detail:
                raise Warning('In categorical item %s, category is not convertible to int (%s)\n'%(part, detail))
                ok = False
            try:
                ncol = int(partsU.group('col'))
            except ValueError, detail:
                raise Warning('In categorical item %s, column is not convertible to int (%s)\n'%(part, detail))
                ok = False
            if ok:
                return CatItem(ncol, ncat)
    parse = staticmethod(parse)

class NumItem(Item):
    type_id = 3
    patt = '(?P<col>\d+)((\>(?P<lowbs>-?\d+(\.\d+)?))|(\<(?P<upbs>-?\d+(\.\d+)?))|(\>(?P<lowb>-?\d+(\.\d+)?)\<(?P<upb>-?\d+(\.\d+)?)))$'
    
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
    
    def disp(self, lenIndex=0, names = None):
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
            return (('%'+slenIndex+'i') % self.col) + strbounds

#     def disp(self, lenIndex=0, names = None):
#         if self.lowb > float('-Inf'):
#             lb = '%i' % (round(self.lowb/10))
#         else:
#             lb = '-\infty'
#         if self.upb < float('Inf'):
#             ub = '%i' % (round(self.upb/10))
#         else:
#             ub = '+\infty'
#         if lenIndex > 0 :
#             lenIndex = str(lenIndex)
#         else:
#             lenIndex = ''
#         if type(names) == list  and len(names) > 0:
#             return ('%'+lenIndex+'s \in [%s,%s] ') % (names[self.col], lb, ub)
#         else:
#             return ('%'+lenIndex+'i%s%s ') % (self.col, lb, ub)

    def __str__(self):
        return self.disp()


    def dispPrint(self, neg, names = None):
        if self.lowb > float('-Inf'):
            lb = '[%s\\leq{}' % self.lowb
        else:
            lb = '['
        if self.upb < float('Inf'):
            ub = '\\leq{}%s]' % self.upb
        else:
            ub = ']'
        if neg:
            negstr = ' \\not '
        else:
            negstr= ''
        if type(names) == list  and len(names) > 0:
            idcol = '%s' % names[self.col]
        else:
            idcol = '%i' % self.col
        return ''+negstr+lb+idcol+ub+''



    def parse(part):
        partsU = re.match(NumItem.patt, part)
        if partsU != None :
            ok = True; ncol=None; lowb=None; upb=None
            if partsU.group('upbs') != None:                
                try:
                    upb = float(partsU.group('upbs'))
                except ValueError, detail:
                    raise Warning('In numerical item %s, upper bound is not convertible to float (%s)\n'%(part, detail))
                    ok = False
                lowb = float('-inf')
            
            elif partsU.group('lowbs') != None:                
                try:
                    lowb = float(partsU.group('lowbs'))
                except ValueError, detail:
                    raise Warning('In numerical item %s, lower bound is not convertible to float (%s)\n'%(part, detail))
                    ok = False
                upb = float('inf')

            else:
                try:
                    lowb = float(partsU.group('lowb'))
                    upb = float(partsU.group('upb'))
                except ValueError, detail:
                    raise Warning('In numerical item %s, some bound is not convertible to float (%s)\n'%(part, detail))
                    ok = False
            try:
                ncol = int(partsU.group('col'))
            except ValueError, detail:
                raise Warning('In numerical item %s, column is not convertible to int (%s)\n'%(part, detail))
                ok = False
            if ok:
                return NumItem(ncol, lowb, upb)
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
            
    def disp(self, lenIndex=0, names = None):
        strneg = '%s' % self.neg
        return strneg + self.item.disp(lenIndex-len(strneg), names)

    def __str__(self):
        return self.disp()

    def dispPrint(self, names = None):
        return self.item.dispPrint(self.neg.boolVal(), names)

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
    
    def parse(part):
        parts = part.split()
        (neg, pos) = Neg.parse(parts,0)
        i = 0
        item = None
        while i < len(Term.itemTypes) and item == None:
            if (re.match(Term.itemTypes[i]['class'].patt, parts[pos])):
                item = Term.itemTypes[i]['class'].parse(parts[pos])
            i+=1
        if item != None:
            return Term(neg.boolVal(), item)
    parse = staticmethod(parse)

    def squeeze(self, opBool, terms):
        ok = len(terms)>0
        for term in terms:
            ok &= term.col() == self.col()
            ok &= term.isNeg() == self.isNeg()
            ok &= term.item.type_id == self.item.type_id 

            if ok and self.item.type_id==3:
                if opBool : ## TODO: invert for negated terms?
                    lowb = min([term.item.lowb for term in terms])
                    upb = max([term.item.upb for term in terms])
                else:
                    lowb = max([term.item.lowb for term in terms])
                    upb = min([term.item.upb for term in terms])

                ok &= lowb <= upb
                if ok:
                    self.item.lowb = lowb
                    self.item.lowb = lowb
        return ok
             
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
    
    def lowOp(self): 
        return self.op.val

    def highOp(self):
        if len(self.buk) > 1:
            return self.op.val
        else:
            return 0

    def copy(self):
        c = Query()
        c.op = self.op.copy()
        c.buk = []
        for buk in self.buk:
            c.buk.append([t.copy() for t in buk])
        return c

    def searchTerm(self, col, neg):
        bukNb = 0
        t = None
        while bukNb < len(self.buk) and t== None:
            posNb = 0
            while posNb < len(self.buk[bukNb]) and t== None:
                if self.buk[bukNb][posNb].col() == col and self.buk[bukNb][posNb].isNeg() == neg:
                    t = self.buk[bukNb][posNb]
                posNb +=1
            bukNb +=1
        if t!= None:
            return {'term': t, 'buk': bukNb-1, 'pos': posNb-1}

    def getTerm(self, bukNb, posNb):
        if bukNb < len(self.buk):
            if posNb < len(self.buk[bukNb]):
                return self.buk[bukNb][posNb]
            
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
    
    def extend(self, bukNb, term):
        if len(self.buk) == 0 or bukNb==-1:
            self.buk.append([term])
        elif len(self.buk) == 1 and len(self.buk[0]) == 1 and not term in self.buk[0]:
            self.buk[0].append(term)
            ### In case of first append, bukNub is in fact the operator!! 
            self.op = Op(bukNb)
        elif bukNb < len(self.buk) and not term in self.buk[bukNb]:
            self.buk[bukNb].append(term)
        self.buk[-1].sort()
        self.buk.sort()

    def parse(string):
        orStr=Op(True).opStr()
        andStr=Op(False).opStr()
        r = Query()
        m = re.search(r"(?P<op>["+orStr+""+andStr+"]) *\(", string)
        if m != None:
            r.op = Op(m.group('op')==andStr) ## lower level op is opposite
        else:
            m = re.search(r"\) *(?P<op>["+orStr+""+andStr+"])", string)
            if m != None:
                r.op = Op(m.group('op')==andStr) ## lower level op is opposite
            else:
                indAnd = string.find(andStr)
                indOr = string.find(orStr)
                if indAnd == -1 and indOr > 0:
                    r.op = Op(True)
                if indOr == -1 and indAnd > 0:
                    r.op = Op(False)
                # else:
                #     ## Problem: mixed operators without parenthesis

        buksStr = string.split(r.op.other().opStr())
        bukTmp = []
        for bukStr in buksStr:
            bukTmp.append([])
            parts = bukStr.split(r.op.opStr())
            for part in parts:
                t= Term.parse(part.strip('() '))
                if (t != None) and not t in bukTmp[-1]:
                    bukTmp[-1].append(t)
            bukTmp[-1].sort()
        bukTmp.sort()
        r.buk = bukTmp
        return r
    parse = staticmethod(parse)


#     def dispPlus(self, data, side, lenIndex=0, names = None):
#         if len(self) == 0 :
#             string = '[]'
#         else:
# #             if len(self.buk) > 2:
# #                 pdb.set_trace()
#             string = ''
#             op = self.op
#             for cbuk in self.buk:
#                 for term in cbuk:
#                     spp = len(data.supp(side, term));
#                     string += '%s%s (%i,%f)' % (op, term.disp(lenIndex, names), spp, spp/float(data.nbRows()) )
#                 op = op.other()
#             string = string[2:]
#         return string
    
    def __str__(self):
        return self.disp()    

    def disp(self, lenIndex=0, names = None):
        if len(self) == 0 :
            string = '[]'
        else:
            nbBuks = len(self.buk)
                
#             if len(self.buk) > 2:
#                 pdb.set_trace()
            string = ''
            for ibuk in range(len(self.buk)):
                if len(self.buk[ibuk]) > 1 and nbBuks > 1: ## just a trick to get parenthesis and no operator for the first term in the bucket
                    op = '( '
                else:
                    op = ''
                for term in self.buk[ibuk]:
                    string += '%s%s' % (op, term.disp(lenIndex, names))
                    op = self.op
                    
                if len(self.buk[ibuk]) > 1 and nbBuks > 1:
                    string += ') '

                if ibuk+1 < len(self.buk): ## not last bucket
                    op = op.other()
                    string += '%s' % op
        return string

    def dispPrint(self, lenIndex=0, names = None):
        if len(self) == 0 :
            string = '[]'
        else:
            nbBuks = len(self.buk)
                
#             if len(self.buk) > 2:
#                 pdb.set_trace()
            string = ''
            for ibuk in range(len(self.buk)):
                if len(self.buk[ibuk]) > 1 and nbBuks > 1: ## just a trick to get parenthesis and no operator for the first term in the bucket
                    op = '( '
                else:
                    op = ''
                for term in self.buk[ibuk]:
                    string += '%s%s' % (op, term.dispPrint(names))
                    op = self.op
                    
                if len(self.buk[ibuk]) > 1 and nbBuks > 1:
                    string += ') '

                if ibuk+1 < len(self.buk): ## not last bucket
                    op = op.other()
                    string += '%s' % op
        return string
    
    def __str__(self):
        return self.disp()    

    def invSigned(self):
        invSigns = []
        for buk in self.buk :
            for term in buk:
                invSigns.append((term.col(), term.isNeg()))
        invSigns.sort()
        return invSigns

    def bukCols(self, op=None):
        bukCols = []
        if len(self.buk)==1 and op != None and self.lowOp() != op:
            incr = 1
        else:
            incr = 0
        buki = 0
        for buk in self.buk:
            for term in buk:
                bukCols.append((buki, term.col()))
                buki+=incr
            buki+=(1-incr)
        return bukCols
    
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
            for term in self.buk[buk_nb] :
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
                    tm = None
                    for term in buk:
                        tm  = SParts.partsSuppMiss(op.isOr(), tm, data.termSuppMiss(side, term))
                    sm  = SParts.partsSuppMiss(not op.isOr(), sm, tm)
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
                    tr = -1 
                    for term in buk:
                        tr = SParts.updateProba(tr, len(data.supp(side, term))/float(data.nbRows()), op.isOr())
                    pr = SParts.updateProba(pr, tr, not op.isOr())
                        ##print '%s : pr=%f (%s %f)' % (term, pr, op, len(data.supp(side, term))/float(data.nbRows()))
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
    
