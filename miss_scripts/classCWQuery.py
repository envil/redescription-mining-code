import re, pdb
from classQuery import Op, Neg, Term, Item, BoolItem
            
class CWQuery:
    
    def __init__(self):
        self.vars = [[None, None], [None, None]]

    def __len__(self):
        if self.vars[0][0] == None: return 0
        elif self.vars[0][1] == None and self.vars[1][1] == None: return 1
        elif self.vars[0][1] != None and self.vars[1][1] != None: return 4
        else: return 3

    def parse(string):
        r = CWQuery()
        parts = string.split(') | (')
        for ptid in range(len(parts)):
            vrs = parts[ptid].split('&')
            for vrid in range(len(vrs)):
                if vrs[vrid].find('!') != -1:
                    neg = True
                else:
                    neg = False
#                 print vrs[vrid]
#                 print vrs[vrid].strip('()! ')
#                 pdb.set_trace()
                r.vars[ptid][vrid] = Term(neg, BoolItem(int(vrs[vrid].strip('() !\n'))))
                
        # if r.vars[0][0] == None or (r.vars[1][0] != None and (
#             (r.vars[0][0].col() != r.vars[1][0].col()) or (r.vars[0][0].isNeg() == r.vars[1][0].isNeg()) )):
#             pdb.set_trace()
#             raise Exception('Problem with CW query parsing !')
        return r
    parse = staticmethod(parse)


    def disp(self, lenIndex=0, names = None):
        string = '('
        for ptid in range(len(self.vars)):
            for vrid in range(len(self.vars[ptid])):
                if self.vars[ptid][vrid] != None :
                    if vrid == 0 :
                        if ptid == 1:
                            string += ') | ('
                        string += ' %s ' % (self.vars[ptid][vrid].disp(lenIndex, names))
                    else:
                        string += ' & %s ' % (self.vars[ptid][vrid].disp(lenIndex, names))
        string += ')'        
        return string

    def dispPrint(self, names = None):
        string = '$('
        for ptid in range(len(self.vars)):
            for vrid in range(len(self.vars[ptid])):
                if self.vars[ptid][vrid] != None :
                    if vrid == 0 :
                        if ptid == 1:
                            string += ')\\lor('
                        string += '%s' % (self.vars[ptid][vrid].dispPrint(names))
                    else:
                        string += '\\land%s' % (self.vars[ptid][vrid].dispPrint(names))
        string += ')$'        
        return string

    
    def __str__(self):
        return self.disp()    

    def dispPlus(self, data, side, lenIndex=0, names = None):
        return self.disp()    
    
    ## return the support associated to a query
    def recompute(self, side, data= None):

        supp = set()
        if data!=None:
            for ptid in range(len(self.vars)):
                suppTmp = set()
                for vrid in range(len(self.vars[ptid])):
                    if self.vars[ptid][vrid] != None :
                        if vrid == 0 :
                            suppTmp = data.supp(side, self.vars[ptid][vrid])
                        else:
                            suppTmp &= data.supp(side, self.vars[ptid][vrid])
                supp |= suppTmp
            
        return supp
          
    ## return the support associated to a query
    def proba(self, side, data= None):
        pr = -1
        
        if data!=None:
            pr = 0
            for ptid in range(len(self.vars)):
                prTmp = 0
                for vrid in range(len(self.vars[ptid])):
                    if self.vars[ptid][vrid] != None :
                        if vrid == 0 :
                            prTmp = len(data.supp(side, self.vars[ptid][vrid]))/float(data.N)
                        else:
                            prTmp *= len(data.supp(side, self.vars[ptid][vrid]))/float(data.N)
                pr += prTmp
            
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
 
    def updateProba(prA, prB, op):
        raise Exception('CWNotImplemented', 'Not implemented')
 
    
    def invCols(self):
        raise Exception('CWNotImplemented', 'Not implemented')
    
    def invTerms(self):
        raise Exception('CWNotImplemented', 'Not implemented')
    
    def makeIndexes(self, format_str):
        raise Exception('CWNotImplemented', 'Not implemented')
    

    def __hash__(self):
        return hash(self.negs+self.vars)
        
    def opBuk(self, nb): 
        raise Exception('CWNotImplemented', 'Not implemented')
    
    def copy(self):
        raise Exception('CWNotImplemented', 'Not implemented')
            
    def compare(x, y): 
        raise Exception('CWNotImplemented', 'Not implemented')
    compare = staticmethod(compare)
    
    def __cmp__(self, other):
        raise Exception('CWNotImplemented', 'Not implemented')
    
    def comparePair(x0, x1, y0, y1):
        raise Exception('CWNotImplemented', 'Not implemented')
    comparePair = staticmethod(comparePair)
    
    def extend(self, op, term):
        raise Exception('CWNotImplemented', 'Not implemented')
