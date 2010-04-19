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
    -i, --rules-in=FILE
      Input file for rules. Optional, if not given, stdin is used.
    -I, --support-in=FILE
      Input file for support.
    -o, --rules-out=FILE
      Output file for rules. Optional, if not given, stdin is used.
    -O, --support-out=FILE
      Output file for support.
    -n, --rows-labels=FILENAME
       Filename row names
    -l, --left-labels=FILENAME
       Filename column names left
    -r, --right-labels=FILENAME
       Filename column names right
    --check-sanity
       Perform sanity check of the rules
    --disp-names
       Display rules with names
    --dense-support
       Write dense support
    -v, --verbosity=INT
      Verbosity level, use either many v's or verbosity.
    -h, --help
      This text.

    """%sys.argv[0]
 
def getOpts(argv):
    try:
        opts, args = getopt.getopt(argv, "L:R:o:O:i:I:n:l:r:vh", \
                                   ["dataL=", "dataR=", "rules-in=", "support-in=", "rules-out=", "support-out=", \
                                    "rows-labels=", "left-labels=", "right-labels=" , \
                                    "check-sanity", "disp-names", "dense-support", "exp", \
                                    "help","verbosity="])
    except getopt.GetoptError:
        usage()
        sys.exit(2)
    global setts
    setts['verb'] = 0
    setts['dataFiles'] = ["dataL.dat", "dataR.dat"]
    setts['rulesInFile'] = "-"
    setts['supportInFile'] = None
    setts['rulesOutFile'] = "-"
    setts['supportOutFile'] = None
    setts['labelsFiles'] = ["","",""]
    setts['checkSanity'] = False
    setts['dispNames'] = False
    setts['denseSupport'] = False
    setts['exp'] = False
    if len(opts) == 0:
        usage()
        sys.exit()
    for o, a in opts:
        if o in ("-L", "--dataL"): setts['dataFiles'][0] = a
        if o in ("-R", "--dataR"): setts['dataFiles'][1] = a
        if o in ("-i", "--rules-in"): setts['rulesInFile'] = a
        if o in ("-I", "--support-in"): setts['supportInFile'] = a
        if o in ("-o", "--rules-out"): setts['rulesOutFile'] = a
        if o in ("-O", "--support-out"): setts['supportOutFile'] = a
        if o in ("-n", "--rows-labels"): setts['labelsFiles'][2] = a
        if o in ("-l", "--left-labels"): setts['labelsFiles'][0] = a
        if o in ("-r", "--right-labels"): setts['labelsFiles'][1] = a
        if o in ("--check-sanity"): setts['checkSanity'] = True
        if o in ("--disp-names"): setts['dispNames'] = True
        if o in ("--dense-support"): setts['denseSupport'] = True
        if o in ("--exp"): setts['exp'] = True
        if o in ("-h", "--help"):
            usage()
            sys.exit()
        if o == "-v":
            setts['verb'] += 1
        if o == "--verbosity":
            setts['verb'] = int(a)  

def verbPrint(level, message):
    utilsIO.verbPrint(level, message, setts)

def main():
    getOpts(sys.argv[1:])
    data = Data(setts['dataFiles'])
    names = [None, None]
    if ( len(setts['labelsFiles'][0] + setts['labelsFiles'][1]) >0):
        names[0] = utilsIO.getNames(setts['labelsFiles'][0], data.nbCols(0), data.nbCols(0)==0)
        names[1] = utilsIO.getNames(setts['labelsFiles'][1], data.nbCols(1), data.nbCols(1)==0)

    if setts['rulesInFile'] != "-" and len(setts['rulesInFile']) > 0 :
        rulesInFp = open(setts['rulesInFile'], 'r')
    else: rulesInFp = sys.stdin
 
    supportInFp = None
    if setts['supportInFile'] != None  and len(setts['supportInFile']) > 0: supportInFp = open(setts['supportInFile'], 'r')

    if setts['dispNames'] :
        if setts['rulesOutFile'] != "-"  or len(setts['rulesOutFile']) == 0 :
            rulesOutFp = open(setts['rulesOutFile'], 'w')
        else: rulesOutFp = sys.stdout

    if setts['denseSupport'] :
        supports = []
        
    ruleNro = 1
    while True:
        currentR = Redescription.load(rulesInFp, supportInFp, data)
        if len(currentR) == 0 :
            break
        verbPrint(5,'Reading rule # %i'%ruleNro)
        
        if setts['checkSanity'] :
            res = currentR.check(data)

            if res == None:
                print 'Rule has toy supports !'
            elif type(res) == tuple and len(res)==3:
                if res[0] *res[1] *res[2] == 1:
                    print "Rule %i OK !" % ruleNro
                else:
                    print "Rule %i WRONG ! (%s)" % (ruleNro, res)
            else:
                print "Something happend while analysing rule %i !" % ruleNro

        if setts['dispNames'] :
            #if currentR.acc() >= 0.25 and currentR.lenI() > 30:
            rulesOutFp.write(currentR.disp(0, names)+'\n')
 
        if setts['exp'] :
            print currentR.surp(data)
 

        if setts['denseSupport'] :
            supports.extend([currentR.suppL(), currentR.suppR()])
            
        ruleNro += 1
    verbPrint(1,'Read all %i rules.'%(ruleNro-1))
    if setts['denseSupport'] :
        utilsIO.writeDense(setts['supportOutFile'], supports, data.N-1)    

    if setts['dispNames'] :
        rulesOutFp.close()     
    verbPrint(1,'Done')
        
## END of main()

if __name__ == "__main__":
    main()
