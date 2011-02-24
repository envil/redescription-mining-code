#!/usr/bin/python
from classData import BoolColM, CatColM, NumColM
import pdb

from classLog import Log
logger = Log()

def loadColumnNames(filename):
    f = open(filename, 'r')
    a = []
    for line in f.readlines():
        a.append(line.strip())
    return a

def getNames(filename, lenColSupps, empty):
    names = loadColumnNames(filename)
    if (len(names) ==  lenColSupps):
        if(empty):
            names.insert(0,'')
            raise Warning('First column empty ! Adding offset to names ...')
    if (len(names) !=  lenColSupps):
        names = None
        raise Warning('Number of names does not match number of variables ! Not returning names')
    return names

def readData(filenames):
    data = []; nbRowsT = None;
    for filename in filenames:
        (cols, nbRows, nbCols) = readMatrix(filename)
        if len(cols) != nbCols:
            raise Exception('Matrix in %s does not have the expected number of variables !' % filename)

        else:
            if nbRowsT == None:
                nbRowsT = nbRows
            elif nbRowsT == nbRows:
                data.append(cols)
            else:
                raise Exception('All matrices do not have the same number of entities (%i ~ %i)!' % (nbRowsT, nbRows))
    return (data, nbRows)

def readMatrix(filename):
    ## Read input
    nbRows = None
    f = open(filename, 'r')
    try:
        row = f.next()
        a = row.split()
        nbCols = int(a[0])
        nbRows = int(a[1])
        type_all = a[2]
        
        if len(type_all) >= 3 and type_all[0:3] == 'dat':
            method_parse =  eval('parseCell%s' % (type_all.capitalize()))
            method_prepare = eval('prepare%s' % (type_all.capitalize()))
            method_finish = eval('finish%s' % (type_all.capitalize()))
        else:
            method_parse =  eval('parseRow%s' % (type_all.capitalize()))
            method_prepare = eval('prepareNonDat')
            method_finish = eval('finishNonDat')
    except (AttributeError, ValueError, StopIteration):
        raise Exception('Size and type header is not right')

    tmpCols = method_prepare(nbRows, nbCols)

    logger.printL(2,"\nReading input data %s (%i x %i %s)\n"% (filename, nbRows, nbCols, type_all))
                
    for row in f:
        method_parse(tmpCols, row.split(), nbRows, nbCols)

    logger.printL(4,"\nDone with reading input data %s (%i x %i %s)\n"% (filename, nbRows, nbCols, type_all))
    cols = method_finish(tmpCols, nbRows, nbCols)
    return (cols, nbRows, nbCols)
    
def prepareNonDat(nbRows, nbCols):
    return []

def parseRowMix(tmpCols, a, nbRows, nbCols):
    type_row = a.pop(0)
    if type_row[0:3] == 'dat':
        raise Exception('Oups this row format is not allowed for mixed datat (%s)!' % (type_row))
    try:
        method_parse =  eval('parseRow%s' % (type_row))
    except AttributeError:
        raise Exception('Oups this row format does not exist (%s)!' % (type_row))
    method_parse(tmpCols, a, nbRows, nbCols)

def finishNonDat(tmpCols, nbRows, nbCols):
    return tmpCols

def prepareDatnum(nbRows, nbCols):
    return [[(0, -1)] for i in range(nbCols)]

def parseCellDatnum(tmpCols, a, nbRows, nbCols):
    id_col = int(a[0])-1
    id_row = int(a[1])-1
    val = float(a[2])
    if id_col >= nbCols or id_row >= nbRows:
        raise Exception('Outside expected columns and rows (%i,%i)' % (id_col, id_row))
    else :
        tmpCols[id_col].append((val, id_row))

def finishDatnum(tmpCols, nbRows, nbCols):
    return [NumColM(tmpCols[col].sort(key=lambda x: x[0]), nbRows) for col in range(len(tmpCols))]
        
def prepareDatbool(nbRows, nbCols):
    return [set() for i in range(nbCols)]

def parseCellDatbool(tmpCols, a, nbRows, nbCols):
    id_col = int(a[0])-1
    id_row = int(a[1])-1
    val = float(a[2])
    if id_col >= nbCols or id_row >= nbRows:
        raise Exception('Outside expected columns and rows (%i,%i)' % (id_col, id_row))
    else :
        if val != 0:
            tmpCols[id_col].append(id_row)

def finishDatbool(tmpCols, nbRows, nbCols):
    return [BoolColM(tmpCols[col], nbRows) for col in range(len(tmpCols))]

def parseVarDensenum(tmpCols, a, nbRows, nbCols):
    if len(a) == nbRows:
        tmpCols.append(NumColM( sorted( [(float(a[i]),i) for i in range(len(a))], key=lambda x: x[0]), nbRows ))
    else:
        raise Exception('Too many rows (%i)' % (len(a)))
                        
def parseVarDensecat(tmpCols, a, nbRows, nbCols):
    if len(a) == nbRows:
        tmp = {}
        for row in range(len(a)):
            cat = int(a[row])
            if tmp.has_key(cat):
                tmp[cat].add(row)
            else:
                tmp[cat] = set([row])
        tmpCols.append(CatColM(tmp, nbRows))
    else:
        raise Exception('Too many rows (%i)' % (len(a)))

def parseVarDensebool(tmpCols, a, nbRows, nbCols):
    if len(a) == nbRows:
        tmp = set()
        for i in range(len(a)):
            if int(a[i]) != 0: tmp.add(i) 
        tmpCols.append(BoolColM( tmp, nbRows ))
    else:
        raise Exception('Too many rows (%i)' % (len(a)))
                        
def parseVarSparsebool(tmpCols, a, nbRows, nbCols):
    tmp = set()
    for i in range(len(a)):
        tmp.add(int(a[i]))
    if max(tmp) >= nbRows:
        raise Exception('Too many rows (%i)' % (len(a)))
    else:
        tmpCols.append(BoolColM( tmp, nbRows ))
