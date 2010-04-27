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
    --recompute
       Recompute redescription
    -v, --verbosity=INT
      Verbosity level, use either many v's or verbosity.
    -h, --help
      This text.

    """%sys.argv[0]
 
def getOpts(argv):
    try:
        opts, args = getopt.getopt(argv, "L:R:o:O:i:I:n:l:r:a:s:S:p:vh", \
                                   ["dataL=", "dataR=", "rules-in=", "support-in=", "base-out=", \
                                    "rows-labels=", "left-labels=", "right-labels=" , \
                                    "redundancy", "check-sanity", "disp-names", "recompute", "filter", \
                                    "min-acc=", "min-supp=", "max-supp=", "max-pval=", \
                                    "help","verbosity="])
    except getopt.GetoptError, err:
        print err
        usage()
        sys.exit(2)
    global setts
    setts['verb'] = 0
    setts['dataFiles'] = ["dataL.dat", "dataR.dat"]
    setts['rulesInFile'] = "-"
    setts['supportInFile'] = None
    setts['baseOut'] = None
    setts['labelsFiles'] = ["","",""]
    setts['recompute'] = False
    setts['checkSanity'] = False
    setts['dispNames'] = False
    setts['filter'] = False
    setts['redundancy'] = False
    setts['minAcc'] = 0
    setts['minSupp'] = 0
    setts['maxSupp'] = float('Inf')
    setts['maxPVal'] = 1
    if len(opts) == 0:
        usage()
        sys.exit()
    for o, a in opts:
        if o in ("-L", "--dataL"): setts['dataFiles'][0] = a
        if o in ("-R", "--dataR"): setts['dataFiles'][1] = a
        if o in ("-i", "--rules-in"): setts['rulesInFile'] = a
        if o in ("-I", "--support-in"): setts['supportInFile'] = a
        if o in ("-o", "--base-out"): setts['baseOut'] = a
        if o in ("-n", "--rows-labels"): setts['labelsFiles'][2] = a
        if o in ("-l", "--left-labels"): setts['labelsFiles'][0] = a
        if o in ("-r", "--right-labels"): setts['labelsFiles'][1] = a
        if o == "--check-sanity" : setts['checkSanity'] = True
        if o == "--recompute" : setts['recompute'] = True
        if o == "--redundancy": setts['redundancy'] = True
        if o == "--disp-names": setts['dispNames'] = True
        if o == "--filter": setts['filter'] = True
        if o in ("-s","--min-supp"): setts['minSupp'] = int(a)
        if o in ("-S","--max-supp"): setts['maxSupp'] = int(a)
        if o in ("-a","--min-acc"): setts['minAcc'] = float(a)
        if o in ("-p","--max-pval"): setts['maxPVal'] = float(a)
        if o in ("-h", "--help"):
            usage()
            sys.exit()
        if o == "-v":
            setts['verb'] += 1
        if o == "--verbosity":
            setts['verb'] = int(a)  

def verbPrint(level, message):
    utilsIO.verbPrint(level, message, setts, sys.stderr)

def main():
#    pdb.set_trace()
    getOpts(sys.argv[1:])
    verbPrint(2, "setts:%s" % setts)
    data = Data(setts['dataFiles'])
    names = [None, None]
    if ( setts['dispNames'] and len(setts['labelsFiles'][0] + setts['labelsFiles'][1]) >0):
        names[0] = utilsIO.getNames(setts['labelsFiles'][0], data.nbCols(0), data.nbCols(0)==0)
        names[1] = utilsIO.getNames(setts['labelsFiles'][1], data.nbCols(1), data.nbCols(1)==0)

    if setts['rulesInFile'] != "-" and len(setts['rulesInFile']) > 0 :
        rulesInFp = open(setts['rulesInFile'], 'r')
    else: rulesInFp = sys.stdin
 
    supportInFp = None
    if setts['supportInFile'] != None  and len(setts['supportInFile']) > 0: supportInFp = open(setts['supportInFile'], 'r')

    rulesOutFp = None
    rulesNamedOutFp = None

    if setts['filter'] or setts['redundancy']:
        if setts['baseOut'] != "-" and len(setts['baseOut']) > 0 : 
            rulesOutFp = open(setts['baseOut']+'_fil.rul', 'w')
            if names[0] != None and names[1] != None :  
                rulesNamedOutFp = open(setts['baseOut']+'_fil.names', 'w')
        elif setts['baseOut'] == "-" :
            rulesOutFp = sys.stdout 
            if names[0] != None and names[1] != None :  
                rulesNamedOutFp = sys.stdout
    elif names[0] != None and names[1] != None :
        if len(setts['baseOut']) > 0 : 
            rulesNamedOutFp = open(setts['baseOut']+'.names', 'w')  
        elif setts['baseOut'] == "-" :
            rulesNamedOutFp = sys.stdout
        
    ruleNro = 1
    while True:
        (currentR, comment)= Redescription.load(rulesInFp, supportInFp, data)
        if len(currentR) == 0:
            if comment == '':
                break
            else:
               if rulesOutFp != None:
                   rulesOutFp.write(comment+'\n')
               if rulesNamedOutFp != None:
                   rulesNamedOutFp.write(comment+'\n')
        else:
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



	    if setts['redundancy'] and data != None :
                
                currentRedun = currentR.copy()
                currentRedun.recompute(data)
                if currentRedun.lenU() == 0 :
                    comment = '# REDUNDANT RULE NO SUPPORT LEFT ' + comment
                elif currentRedun.acc() >= setts['minAcc'] and currentRedun.lenI() >= setts['minSupp'] \
                       and currentRedun.lenU() <= setts['maxSupp'] and currentRedun.pVal() <= setts['maxPVal']:
                    comment = '# ' + currentRedun.dispCaracteristiquesSimple() + comment
                    data.addRedunRows(currentRedun.suppI())
                else:
                    comment = '# REDUNDANT RULE ' + currentRedun.dispCaracteristiquesSimple() + comment
                        
                        
	    if (setts['filter'] or setts['recompute']) and data != None :
		currentR.recompute(data)
            if not setts['filter'] or \
                   ( currentR.acc() >= setts['minAcc'] and currentR.lenI() >= setts['minSupp'] and currentR.lenU() <= setts['maxSupp']):
                #pdb.set_trace()
                if rulesOutFp != None:
                    rulesOutFp.write(currentR.dispSimple()+' '+comment+'\n')
                if rulesNamedOutFp != None:
                    rulesNamedOutFp.write(currentR.dispSimple(0, names)+' '+comment+'\n')

            ruleNro += 1
    verbPrint(1,'Read all %i rules.'%(ruleNro-1))
 
    if rulesOutFp != None :
        rulesOutFp.close()     
 
    if rulesNamedOutFp != None :
        rulesNamedOutFp.close()     
    verbPrint(1,'Done')
        
## END of main()

if __name__ == "__main__":
    main()
