#!/usr/bin/python

import sys, getopt, os, re, random
import pdb

setts = {}

def usage():
    print """
    Usage: %s [options]
    File names:
    ------------
        Filenames must have an extension indicating the data format (sparse|dense|bdat|ndat|num ...)
    -i/ --input=FILENAME
    input data
    -o / --output=FILENAME
    output data
    -l /--letter=CHAR
      Name for the variable, Cart format
    -c / --classes
      Generate classes file, for Cart
    -w / --overwrite
      Force overwrite
    -h, --help
      This text.

    """%sys.argv[0]

def getOpts():
    try:
        opts, args = getopt.getopt(sys.argv[1:], "i:o:l:wch", \
                                   ["help","input", "output", "letter","classes", "overwrite"])
    except getopt.GetoptError:
        usage()
        sys.exit(2)
    global setts
    setts['inFile'] = "-"
    setts['outFile'] = "-"
    setts['letter'] = "A"
    setts['classes'] = False
    setts['overwrite'] = False
    if len(opts) == 0:
        usage()
        sys.exit()
    for o, a in opts:
        if o in ("-h", "--help"):
            usage()
            sys.exit()
	if o in ("-i", "--input"): setts['inFile'] = a
	if o in ("-o", "--output"): setts['outFile'] = a
	if o in ("-l", "--letter"): setts['letter'] = a
	if o in ("-c", "--classes"): setts['classes'] = True
	if o in ("-w", "--overwrite"): setts['overwrite'] = True

def verbPrint(level, message, setts={'verb':0}, where=sys.stdout):
    if where != None and setts['verb'] >= level:
        where.write("%s\n" % message)
##         sys.stderr.write("\r                                                 \
##                                                                         \r%s"\
##                          %message)

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
            sys.stderr.write('\nWARNING ! First column empty ! Adding offset to names ...\n')
    if (len(names) !=  lenColSupps):
        names = None
    return names


def readMatlabNum(filename):
    ## Read input
    ##pdb.set_trace()
    f = open(filename, 'r')
    rowId = 0
    tmpcolSupps = []
    verbPrint(1,"\nReading matlab input %s\n"%filename)
    #cols = -1
    for row in f:
        a = row.split('\t')
        id_row = int(a[0])
        id_col = int(a[1])
        val = int(a[2])
        ## For Python 2.4, convert a to INT
        if tmpcolSupps == []:
            tmpcolSupps = [[(0, -1)] for i in range(id_col)]
            rowId = id_row -1
        elif id_col > len(tmpcolSupps) or id_row-1 > rowId:
        ## Sanity check
            sys.stderr.write('\n\nSomething wrong when reading data\n')
            sys.exit(3)
        else :
            tmpcolSupps[id_col-1].append((val, id_row-1))
    f.close()
    if len(tmpcolSupps[0]) == 1:
        sys.stderr.write('\nWARNING ! First column empty !\n')
    for i in range(len(tmpcolSupps)):
        tmpcolSupps[i].sort(key=lambda x: x[0])
    return (tmpcolSupps, rowId)

def readNumerical(filename):
    ## Read input
    ## WARNING: non boolean data stored transposed

    rowId = -1
    f = open(filename, 'r')
    tmpcolSupps = []
    verbPrint(1,"\nReading dense input %s\n"%filename)
    for row in f:
        a = (row.strip()).split(' ')
        if rowId == -1:
            rowId = len(a)
        elif rowId != len(a):
            raise Exception('Inconsistent number of rows !\n')
        #tmpcolSupps.append([float(i) for i in a])
        tmpcolSupps.append( sorted( [(float(a[i]),i) for i in range(len(a))], key=lambda x: x[0]) )
    f.close()
    return (tmpcolSupps, rowId-1)

def readCategorical(filename):
    ## Read input
    ## WARNING: non boolean data stored transposed

    rowId = -1
    f = open(filename, 'r')
    tmpcolSupps = []
    verbPrint(1,"\nReading dense input %s\n"%filename)
    for row in f:
        a = (row.strip()).split(' ')
        if rowId == -1:
            rowId = len(a)
        elif rowId != len(a):
            raise Exception('Inconsistent number of rows !\n')
        tmpcolSupps.append(a)
    f.close()
    return (tmpcolSupps, rowId-1)

def readDense(filename):
    ## Read input

    rowId = -1
    f = open(filename, 'r')
    tmpcolSupps = []
    verbPrint(1,"\nReading dense input %s\n"%filename)
    for row in f:
        a = (row.strip()).split(' ')
        if rowId == -1:
            tmpcolSupps = [set() for i in range(len(a))]
        rowId += 1
        for i in range(len(a)):
            if int(a[i]) == 1: tmpcolSupps[i].add(rowId) 
    f.close()
    return (tmpcolSupps, rowId)

def readSparse(filename):
    ## Read input

    rowId = -1
    f = open(filename, 'r')
    tmpcolSupps = []
    verbPrint(1,"\nReading sparse input %s\n"%filename)
    #cols = -1
    for row in f:
        a = row.split()
        rowId += 1
        if len(a) == 0: continue
        ## For Python 2.4, convert a to INT
        for i in range(len(a)): a[i] = int(a[i])
        if max(a)+1 > len(tmpcolSupps):
            tmpcolSupps = tmpcolSupps + \
                          [set() for i in range(max(a)+1-len(tmpcolSupps))]
        ## Sanity check
        if max(a)+1 > len(tmpcolSupps):
            sys.stderr.write('\n\nSomething wrong when reading data\n')
            sys.exit(3)
        for i in a:
            tmpcolSupps[i].add(rowId)
    f.close()
    if len(tmpcolSupps[0]) == 0:
        sys.stderr.write('\nWARNING ! First column empty !\n')
    return (tmpcolSupps, rowId)

def readMatlab(filename):
    ## Read input
    ##pdb.set_trace()
    f = open(filename, 'r')
    rowId = 0
    tmpcolSupps = []
    verbPrint(1,"\nReading matlab input %s\n"%filename)
    #cols = -1
    for row in f:
        a = row.split('\t')
        id_row = int(a[0])
        id_col = int(a[1])
        val = int(a[2])
        ## For Python 2.4, convert a to INT
        if tmpcolSupps == []:
            tmpcolSupps = [set() for i in range(id_col)]
            rowId = id_row-1
        elif id_col > len(tmpcolSupps) or id_row-1 > rowId:
        ## Sanity check
#            pdb.set_trace()
            sys.stderr.write('\n\nSomething wrong when reading data\n')
            sys.exit(3)
        elif val != 0 :
            tmpcolSupps[id_col-1].add(id_row-1)
    f.close()
    if len(tmpcolSupps[0]) == 0:
        sys.stderr.write('\nWARNING ! First column empty !\n')
    return (tmpcolSupps, rowId)

def writeSparse(filename, tmpcolSupps, rowId):
    verbPrint(1,"\nWriting sparse output %s\n"%filename)
    e = ['' for i in range(rowId+1)]
    f = open(filename, 'w')
    for i in range(len(tmpcolSupps)):
        for j in tmpcolSupps[i]:
            e[j] += '%i ' % i
    to_write = '\n'.join(e)+"\n"
    to_write = to_write.replace(' \n','\n')
    f.write(to_write)
    f.close()
    
def writeCompact(filename, tmpcolSupps, rowId):
    ## DELETE EMPTY COLUMNS
    verbPrint(1,"\nWriting compact output %s\n"%filename)
    e = ['' for i in range(rowId+1)]
    f = open(filename, 'w')
    k = 0
    for i in range(len(tmpcolSupps)):
        for j in tmpcolSupps[i]:
            e[j] += '%i ' % k
        if len(tmpcolSupps[i]) > 0 :
            k +=1
    to_write = '\n'.join(e)+"\n"
    to_write = to_write.replace(' \n','\n')
    f.write(to_write)
    f.close()

def writeIbm(filename, tmpcolSupps, rowId):
    ## WARNING COLIDS WILL START FROM 1
    verbPrint(1,"\nWriting ibm output %s\n"%filename)
    #pdb.set_trace()
    e = ['' for i in range(rowId+1)]
    f = open(filename, 'w')
    for i in range(len(tmpcolSupps)):
        for j in tmpcolSupps[i]:
            e[j] += '%i ' % (i+1)
    d = []
    for j in range(len(e)):
        d.append('%i %i %i ' %(j+1,j+1, len(e[j].split()))+e[j].strip())
    to_write = '\n'.join(d)
    f.write(to_write.strip(' ')+'\n')
    f.close()

def writeDense(filename, tmpcolSupps, rowId):
    verbPrint(1,"\nWriting dense output %s\n"%filename)

    e = ['' for i in range(rowId+1)]
    f = open(filename, 'w')
    for i in range(len(tmpcolSupps)):
        for j in range(rowId+1):
            e[j] += '%i ' % (j in tmpcolSupps[i])
    to_write = '\n'.join(e).replace(' \n','\n')
    f.write(to_write.strip(' ')+'\n')
    f.close()

def writeMatlab(filename, tmpcolSupps, rowId): 
    verbPrint(1,"\nWriting matlab output %s\n"%filename)

    f = open(filename, 'w')
    f.write('%i\t%i\t0\n'% (rowId+1, len(tmpcolSupps))) ## To ensure that the sparse matrix will have the right size
    for column in range(len(tmpcolSupps)):
        for row in tmpcolSupps[column]:
            f.write('%i\t%i\t1\n'% (row+1, column+1))
    f.close()
    
def writeCart(filename, tmpcolSupps, rowId, classes, letterColumn = 'C', letterRow='G'): 
    verbPrint(1,"\nWriting cart output %s\n"%filename)

    f = open(filename, 'w')
    d = []
    for column in range(len(tmpcolSupps)):
        for row in tmpcolSupps[column]:
            d.append("%s%08i\t%s%08i"% (letterRow, row, letterColumn, column))
    d.sort()
    to_write = '\n'.join(d).strip()
    f.write(re.sub("([A-Z])0*([0-9])","\g<1>\g<2>",to_write))
    f.close()

    if (classes):
        verbPrint(1,"\nWriting cart classes %s\n"%filename)
        f = open(filename+".classes", 'w')
        col = random.randint(1,len(tmpcolSupps))
        pos = tmpcolSupps[col-1]
        neg = list(set(range(rowId+1))-pos)
        pos = list(pos)
        
        d = ["%s%08i\t%s%i"% (letterRow, pos[i], letterColumn, col) for i in range(len(pos))]
        d.extend(["%s%08i\texc-%s%i"% (letterRow, neg[i], letterColumn, col) for i in range(len(neg))])
        d.sort()
        to_write = '\n'.join(d).strip()
        f.write(re.sub("([A-Z])0*([0-9])","\g<1>\g<2>",to_write))
        f.close()

# IBM to sparse :
# cut -f4- -d ' ' filename

# sparse to IBM :
# nl ./data/houseVotes/house-votes-84_sparse | nl | expand | sed 's/  */ /g' | sed 's/^ //g' > ./data/houseVotes/house-votes-84_ibm

def convertFormat(inFile, outFile, overwrite=False, letter='A', classes=False):
    format_in = inFile.split('.').pop()
    format_out = outFile.split('.').pop()
    if format_in == format_out:
        sys.stderr.write("\nError, input and output format are the same (%s %s)!" % (format_in, format_out))
        sys.exit(1)

    if ( not overwrite and os.path.isfile(outFile) ):
        sys.stderr.write("\nOutput file %s already exists, not overwriting (add --overwrite to force)\n"% ( outFile))
        sys.exit(1)

        ## FROM IBM FORMAT -> shell commands
    if format_in == "ibm" and  format_out == "sparse" :
       verbPrint(1,"\nIbm to sparse  %s -> %s\n"% ( inFile, outFile))
       os.system("cut -f4- -d ' ' "+inFile+" > "+outFile)
       (colSupps, rowId) = readSparse(outFile)
       #pdb.set_trace()
       del colSupps[0]
       writeSparse(outFile, colSupps, rowId)
       inFormat = "done"
       outFormat = "done"

    elif format_in == 'dense':
        (colSupps, rowId) = readDense(inFile)
    elif format_in == 'bdat':
        (colSupps, rowId) = readMatlab(inFile)
    elif format_in == 'sparse':
        (colSupps, rowId) = readSparse(inFile)
    elif format_in == 'num':
        (colSupps, rowId) = readNumerical(inFile)
    elif format_in == 'ndat':
        (colSupps, rowId) = readMatlabNum(inFile)
    elif format_in == 'cat' :
        (colSupps, rowId) = readCategorical(inFile)
    else:
        (colSupps, rowId) =  (None, None)
        raise Warning('Unknown format !')

    ## WRITING OTHER FORMATS
    if format_out == "sparse" :
        writeSparse(outFile, colSupps, rowId)
    elif format_out == "bdat":
        writeMatlab(outFile, colSupps, rowId)
    elif format_out == "dense" :
        writeDense(outFile, colSupps, rowId)
    elif format_out == "compact":
        writeCompact(outFile, colSupps, rowId)
    elif format_out == "ibm":
        writeIbm(outFile, colSupps, rowId)
    elif format_out == "cart":
        writeCart(outFile, colSupps, rowId, classes, letter)

def main():

    getOpts()
    convertFormat(setts['inFile'], setts['outFile'], setts['overwrite'], setts['letter'], setts['classes'])
   
        
## END of main()

if __name__ == "__main__":
    main()
