#!/usr/bin/python

import sys, getopt, numpy, utilsIO
from classRedescription import *
from classData import *
import pdb
## Ignore future warning for the hist function
import warnings
warnings.filterwarnings('ignore', category=FutureWarning)

setts = {}

def usage():
    print """
    Usage: %s [options]
    -L, --dataL=FILE
      Input data file left.
    -R, --dataR=FILE
      Input data file right.
      File names must have an extension indicating their format (sparse|dense|dat).
    -o, --rules-in=FILE
      Input file for rules. Optional, if not given, stdin is used.
    -O, --rules-out=FILE
      Output file for rules. Optional, if not given, stdout is used. 
    -n, --rows-labels=FILENAME
       Filename row names
    -l, --left-labels=FILENAME
       Filename column names left
    -r, --right-labels=FILENAME
       Filename column names right
    -v, --verbosity=INT
      Verbosity level, use either many v's or verbosity.
    -h, --help
      This text.

    """%sys.argv[0]

def getOpts(argv):
    try:
        opts, args = getopt.getopt(argv, "L:R:o:pO:n:l:r:vh", \
                                   ["dataL=", "dataR=", "rules-in=", "rules-out=", \
                                    "rows-labels=", "left-labels=", "right-labels=" , \
                                       "help","verbosity="])
    except getopt.GetoptError:
        usage()
        sys.exit(2)
    global setts
    setts['verb'] = 0
    setts['datafiles'] = ["inputL.txt", "inputR.txt"]
    setts['rulesfile'] = "-"
    setts['outputfile'] = "-"
    setts['labelsfiles'] = ["","",""]
    if len(opts) == 0:
        usage()
        sys.exit()
    for o, a in opts:
        if o in ("-L", "--dataL"): setts['datafiles'][0] = a
        if o in ("-R", "--dataR"): setts['datafiles'][1] = a
        if o in ("-o", "--rules-in"): setts['rulesfile'] = a
        if o in ("-O", "--output"): setts['outputfile'] = a
        if o in ("-n", "--rows-labels"): setts['labelsfiles'][2] = a
        if o in ("-l", "--left-labels"): setts['labelsfiles'][0] = a
        if o in ("-r", "--right-labels"): setts['labelsfiles'][1] = a
        if o in ("-h", "--help"):
            usage()
            sys.exit()
        if o == "-v":
            setts['verb'] += 1
        if o == "--verbosity":
            setts['verb'] = int(a)  

def verbPrint(level, message):
    utilsIO.verbPrint(level, message, setts)

def linesCompare(x, y):
    if x[0] > y[0]:
        return -1
    elif x[0] == y[0]:
        if x[1] > y[1]:
            return -1
        elif x[1] == y[1]:
            return 0
    return 1
    
def dispRuleCompact(currentR, data,  m=3, reversing = True):
    suppL = currentR.recompute(0, data)
    suppR = currentR.recompute(1, data)
    (invTermsL, invTermsR) = currentR.invTerms()
        
    memb = numpy.zeros(data.N+1,type(1))
    terms = list(invTermsL)
    terms.extend(invTermsR)
    border = len(invTermsL)
    side = 0
    if reversing:
        terms.reverse()
        border = len(invTermsR)
        side = 1
    #pdb.set_trace()    
    i = 0
    labels = ['']
    for term in terms :
        if i == border:
            border = 0
            side = abs(side - 1)
            for k in range(len(labels)):
                if reversing:
                    labels[k] = '\t<==>\t' + labels[k]
                else:
                    labels[k] += '\t<==>\t'
                
        labels.extend(labels)
        if reversing:
            for k in range(len(labels)/2):
                labels[k] = (m+1)*' '+2*' ' + labels[k]
            for k in range(len(labels)/2):
                labels[k+len(labels)/2] = (m+1)*'X'+2*' ' + labels[k+len(labels)/2]
        else:
            for k in range(len(labels)/2):
                labels[k] += (m+1)*' '+2*' '
            for k in range(len(labels)/2):
                labels[k+len(labels)/2] += (m+1)*'X'+2*' '
            
        memb[list(data.supp(side, term))] += int(2**i)
        i += 1

    suppNL = numpy.unique(memb[list(suppL - suppR)]).tolist()
    suppNR = numpy.unique(memb[list(suppR - suppL)]).tolist()
    suppNI = numpy.unique(memb[list(suppL & suppR)]).tolist()
    try:
        hist, edges = numpy.histogram(memb, bins=range(2**i))
    except FutureWarning:
        verbPrint(1,'Computing histogramm')
    
    suppReady = [(0, 0, hist[0], labels[0].replace('<==>','    '))]
    summing = [ hist[0],0,0,0]
    for i in suppNR:
        summing[1] += hist[i]
        suppReady.append((1, i, hist[i],labels[i].replace('<==>','>>  ')))
    suppReady.append((1, -1, -summing[1],labels[i].replace('<==>','>>  ').replace('X','-').replace(' ','-')))
    for i in suppNL:
        summing[2] += hist[i]
        suppReady.append((2, i, hist[i],labels[i].replace('<==>','  <<')))
    suppReady.append((2, -1, -summing[2],labels[i].replace('<==>','  <<').replace('X','-').replace(' ','-')))
    for i in suppNI:
        summing[3] += hist[i]
        suppReady.append((3, i, hist[i],labels[i].replace('<==>','>><<')))
    suppReady.append((3, -1, -summing[3],labels[i].replace('<==>','>><<').replace('X','-').replace(' ','-')))

    suppReady.sort(linesCompare)

    toPrint = ''
    for l in suppReady:
        try:
            toPrint += ('% 5i (%1.5f\t%1.6f):\t%s\n' % (l[2], abs(float(l[2]))/max(summing[l[0]],1), abs(float(l[2]))/data.N, l[3]) )
        except ZeroDivisionError:
            verbPrint(20,'Zero !')
            ##pdb.set_trace()
    toPrint += '\t\t\t\tSummary: %i %i %i/%i %f\n' %( summing[3]+summing[1], summing[3]+summing[2], summing[3], summing[3]+summing[2]+summing[1], float(summing[3])/(summing[3]+summing[2]+summing[1]))
    
    return toPrint

def main():
    #pdb.set_trace()
    getOpts(sys.argv[1:])
    data = Data(setts['datafiles'])
    names = [None, None]
    if ( len(setts['labelsfiles'][0] + setts['labelsfiles'][1]) >0):
        names[0] = utilsIO.getNames(setts['labelsfiles'][0], data.nbCols(0), data.nbCols(0)==0)
        names[1] = utilsIO.getNames(setts['labelsfiles'][1], data.nbCols(1), data.nbCols(1)==0)

    if type(names[0]) == list and len(names[0]) > 0 and type(names[1]) == list and len(names[1]) > 0:
        setts['names'] = True
        n = 20
    else:
        setts['names'] = False
        n = 4

    names_rows = []
    if ( len(setts['labelsfiles'][2]) >0):
        names_rows = utilsIO.getNames(setts['labelsfiles'][2], data.N+1, False)
        m = 30
    if len(names_rows) == 0:
        names_rows = [str(i) for i in range(data.N+1)]
        m = 4

    if setts['rulesfile'] != "-":
        rulesFp = open(setts['rulesfile'], 'r')
    else: rulesFp = sys.stdin
    
    if setts['outputfile'] != "-":
        rulesOutFp = open(setts['outputfile'], 'w')
    else: rulesOutFp = sys.stdout
    
    ruleNro = 1
    while True:
        currentR = Redescription.load(rulesFp)

        if len(currentR) == 0 :
            break
        
        verbPrint(5,'Reading rule # %i'%ruleNro)
        print 'RULE %i'%ruleNro
        rulesOutFp.write('\t\t\t\t'+currentR.disp(n, names)+'\n')
            
#        rulesOutFp.write(dispRuleCompact(currentR, data, n)+'\n')
        
        ruleNro += 1
    verbPrint(1,'Read all %i rules.'%(ruleNro-1))
    verbPrint(1,'Done')
        
## END of main()

if __name__ == "__main__":
    main()
