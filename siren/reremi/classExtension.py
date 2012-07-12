from classQuery import Op
from classRedescription import Redescription
from classSParts import SParts
import pdb

class Extension:
    diff_literal, diff_in, diff_toRed, diff_toBlue, diff_acc, diff_none = range(1,7)

    def __init__(self, side=None, op=None, literal=None, adv=None, N=None):
        self.side = side
        self.op = op
        self.literal = literal
        if adv != None:
            self.contrib, self.varBlue, self.fixBlue, self.varRed, self.fixRed, self.lparts = adv
            if self.varRed + self.fixRed == 0:
                self.acc == 0
            else:
                self.acc = float( self.varBlue + self.fixBlue ) / ( self.varRed + self.fixRed )
            self.N = N
        else:
            self.acc = None

    def kid(self, red, data):
        supp = data.supp(self.side, self.literal)
        miss = data.miss(self.side, self.literal)
        return red.kid(data, self.side, self.op, self.literal, supp, miss)

    def isValid(self):
        return self.acc != None

    def isNeg(self):
        if self.isValid():
            return self.literal.isNeg()

    def adv(self):
        if self.isValid():
            return (self.contrib, self.varBlue, self.fixBlue, self.varRed, self.fixRed, self.lparts)

    def __str__(self):
        if self.isValid():
            return "Extension:\t (%d, %s, %s) -> %f" % (self.side, Op(self.op), self.literal, self.acc) 
        else:
            return "Empty extension"

    def disp(self, base_acc=None, prs=None, coeffs=None):
        strPieces = ["", "", ""]
        if self.isValid():
            strPieces[self.side] = str(Op(self.op)) + " " + str(self.literal) 
            if base_acc == None:
                strPieces[-1] = '----\t%1.7f\t----\t----\t% 5i\t% 5i' \
                                % (self.acc, self.varBlue, self.varRed)
            else:
                strPieces[-1] = '\t\t%+1.7f \t%1.7f \t%1.7f \t%1.7f\t% 5i\t% 5i' \
                                % (self.score(base_acc, prs, coeffs), self.acc, \
                                   self.pValQuery(prs), self.pValRed(prs) , self.varBlue, self.varRed)

        return '* %20s <==> * %20s %s' % tuple(strPieces)
            
    def score(self, base_acc, prs, coeffs):
        if self.isValid():
            return coeffs["impacc"]*self.impacc(base_acc) \
                   + coeffs["rel_impacc"]*self.relImpacc(base_acc) \
                   + self.pValRedScore(prs, coeffs) \
                   + self.pValQueryScore(prs, coeffs)

    def relImpacc(self, base_acc=0):
        if self.isValid():
            if base_acc != 0:
                return (self.acc - base_acc)/base_acc
            else:
                return self.acc
        
    def impacc(self, base_acc=0):
        if self.isValid():
            return (self.acc - base_acc)
        
    def pValQueryScore(self, prs, coeffs=None):
        if self.isValid():
            if coeffs == None or coeffs["pVal_query"] < 0:
                return coeffs["pVal_query"] * SParts.pValQuery(prs)
            elif coeffs["pVal_query"] > 0:
                return -coeffs["pVal_fact"]*(coeffs["pVal_query"] < self.pValQuery(prs))
            else:
                return 0

    def pValRedScore(self, prs, coeffs=None):
        if self.isValid():
            if coeffs == None or coeffs["pVal_red"] < 0:
                return coeffs["pVal_red"] * self.pValRed(prs)
            elif coeffs["pVal_red"] > 0:
                return -coeffs["pVal_fact"]*(coeffs["pVal_red"] < self.pValRed(prs))
            else:
                return 0

    def pValQuery(self, prs=None):
        if self.isValid():
            return SParts.pValQueryCand(self.side, self.op, self.isNeg(), self.lparts, self.N, prs)

    def pValRed(self, prs=None):
        if self.isValid():
            return SParts.pValRedCand(self.side, self.op, self.isNeg(), self.lparts, self.N, prs)

    def __cmp__(self, other):
        return self.compare(other)
    
    def compare(self, other):
        tmp = self.compareAdv(other)
        if tmp == 0:
            if self.literal > other.literal:
                return Extension.diff_literal
            elif self.literal == other.literal:
                return 0
            else:
                return -Extension.diff_literal
        else:
            return tmp

    def compareAdv(self, other):
        if other == None:
            return Extension.diff_none

        if self.acc == None:
            return -Extension.diff_none

        if type(other) in [tuple, list]:
            other_contrib, other_varBlue, other_fixBlue, other_varRed, other_fixRed, other_clp = other
            if other_varRed + other_fixRed == 0:
                other_acc = 0
            else:
                other_acc = float(other_varBlue + other_fixBlue)/ (other_varRed + other_fixRed)
        else:
            if other.acc == None:
                return Extension.diff_none
            other_contrib, other_varBlue, other_fixBlue, other_varRed, other_fixRed, other_clp = other.adv()
            other_acc = other.acc

        if self.acc > other_acc:
            return Extension.diff_acc
        elif self.acc == other_acc:
            if self.acc > other_acc:
                return Extension.diff_toBlue
            elif self.varBlue == other_varBlue:
                if self.varRed > self.varRed:
                    return Extension.diff_toRed
                elif self.varRed == other_varRed:
                    if self.contrib < other_contrib:
                        return Extension.diff_in
                    elif self.contrib == other_contrib:
                        return 0
                    else:
                        return -Extension.diff_in
                else:
                    return -Extension.diff_toRed
            else:
                return -Extension.diff_toBlue
        else:
            return -Extension.diff_acc
        
    
