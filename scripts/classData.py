import math, utilsIO
from classRule import *

class Data:
    
    dataTypes = [{'mSuff': 'Num',  'ext':'num$'}, \
                 {'mSuff': 'Cat',  'ext':'cat$'}, \
                 {'mSuff': 'Bool', 'ext':'(dense)|(dat)|(sparse)$'}]
    
    def __init__(self, datafiles):
        
        self.colSupps = [[],[]]
        self.dataTypeSuffs = ['', '']
        maxRowId = [-1, -1]
        for fileId in (0,1):
                (colSuppsTmp, maxRowIdTmp, dataType) = Data.readInput(datafiles[fileId])
                maxRowId[fileId] = maxRowIdTmp
                self.colSupps[fileId] = colSuppsTmp
                self.dataTypeSuffs[fileId] = dataType

        if maxRowId[0] != maxRowId[1]:
            sys.stderr.write("\n\nDatafiles do not have same number of rows,\
            first has %i, but second has %i!\nAborting.\n\n"%(maxRowId[0], maxRowId[1]))
            sys.exit(3)

        ## Variable Numbers:
        self.dataCols = [len(self.colSupps[0]), len(self.colSupps[1])]
        self.N = maxRowId[0]+1
        
    def nbCols(self,side):
        return self.dataCols[side]


    def vect(self, side, col):
        return self.colSupps[side][col]

    def suppBool(self, side, term):
        return set(self.colSupps[side][term.col()])

    def suppCat(self, side, term):
        colX = self.colSupps[side][term.col()]
        supp = set()
        for idRow in range(len(colX)):
            if colX[idRow] == term.cat:
                supp.add(idRow)
        return supp

    def suppNum(self, side, term):
        colX = self.colSupps[side][term.col()]
        supp = set()
        for idRow in range(len(colX)):
            if colX[idRow] > term.lowb and colX[idRow] < term.upb:
                supp.add(idRow)
        return supp
            
    def supp(self,side, term): ## the term should be the same type as the data on the considered side
        if term.isNeg():
            return set(range(self.N)) - eval('self.supp' + self.dataTypeSuffs[side])(side, term)
        else:
            return eval('self.supp' + self.dataTypeSuffs[side])(side, term)
        
    def __str__(self):
        return "Data size is %i x %i (%s) and %i x %i (%s)" % ( self.N, self.dataCols[0], self.dataTypeSuffs[0],  self.N, self.dataCols[1], self.dataTypeSuffs[1])
   
    def updateS(self, s):
        if s>= 0 and s < 0.5 :
            minSupp = int(math.floor(s*self.N))
            maxSupp = int(math.ceil((1-s)*self.N))
        elif s <1:
            maxSupp = int(math.ceil(s*self.N))
            minSupp = int(math.floor((1-s)*self.N))
        elif s < float(self.N)/2:
            maxSupp = int(self.N - math.ceil(s))
            minSupp = int(math.floor(s))
        elif s < self.N:
            minSupp = int(self.N - math.floor(s))
            maxSupp = int(math.ceil(s))
        else:
            minSupp = 0
            maxSupp = self.N

        return (minSupp, maxSupp)

    def updateC(self, c):
        if c >= 1:
            minC = int(c)
        elif c >= 0 and c < 1 :
            minC = int(math.floor(c*self.N))

        return (minC)


    def nonFullCols(self, minC, side):
        if self.dataTypeSuffs[side] == 'Bool':
            it = set()
            for id in range(self.nbCols(side)):
                if len(self.vect(side,id)) < minC or len(self.vect(side,id)) > self.N - minC :
                    self.colSupps[side][id] = frozenset()
                else:
                    it.add(id)
        
        else:
            it = set([i for i in range(self.nbCols(side))]) 
            
        return it


    def readInput(datafile):
        ## Read input

        format_f = datafile.split('.').pop()
        if format_f == 'dense':
            (colSuppsTmp, rowIdTmp) = utilsIO.readDense(datafile)
        elif format_f == 'dat':
            (colSuppsTmp, rowIdTmp) = utilsIO.readMatlab(datafile)
        elif format_f == 'sparse':
            (colSuppsTmp, rowIdTmp) = utilsIO.readSparse(datafile)
        elif format_f == 'num':
            (colSuppsTmp, rowIdTmp) = utilsIO.readNonBoolean(datafile)
        elif format_f == 'cat' :
            (colSuppsTmp, rowIdTmp) = utilsIO.readNonBoolean(datafile)
            
        dataType = None
        for i in range(len(Data.dataTypes)):
            if re.match(Data.dataTypes[i]['ext'],format_f):
                dataType = Data.dataTypes[i]['mSuff']

        return (colSuppsTmp, rowIdTmp, dataType)
    readInput = staticmethod(readInput)
