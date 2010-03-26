#!/usr/bin/python

import sys, getopt, utilsIO
from classRedescription import *
from classData import *
import pdb

## Global variables
setts={}
def usage():
    print """
    Usage: %s [options]

    -L, --dataL=FILE
      Input data file left.
    -R, --dataR=FILE
      Input data file right.
      File names must have an extension indicating their format (sparse|dense|dat).
    -o, --output=FILE
      Output file.
    -O, --support-output=FILE
      Output file for rule supports.
      
    -v, --verbosity=INT
      Verbosity level, use either many v's or verbosity.
    -h, --help
      This text.
    """%sys.argv[0]



def getOpts(argv):
    try:
        opts, args = getopt.getopt(argv, "L:R:o:O:xvh", \
                                   ["help", "dataL=", "dataR=",  \
                                    "output=", "support-output=", \
                                    "verbosity=", "help"])
    except getopt.GetoptError, err:
        print str(err)
        usage()
        sys.exit(2)
    global setts
    setts['verb'] = 0
    
    setts['datafiles'] = ["inputL.txt", "inputR.txt"]
    setts['outputfile'] = "output.txt"
    setts['supportOutputfile'] = None
    for o, a in opts:
            
        if o in ("-L", "--dataL"): setts['datafiles'][0] = a
        if o in ("-R", "--dataR"): setts['datafiles'][1] = a
        if o in ("-o", "--output"): setts['outputfile'] = a
        if o in ("-O", "--support-output"): setts['supportOutputfile'] = a
            
        if o in ("-h", "--help"):
            usage()
            sys.exit()
        if o == "-v": setts['verb'] += 1
        if o == "--verbosity": setts['verb'] = int(a)

def verbPrint(level, message):
    utilsIO.verbPrint(level, message, setts)

def main():
    #pdb.set_trace()
    getOpts(sys.argv[1:])
    data = Data(setts['datafiles'])

    rulesFp = open(setts['outputfile'], 'r')
    supportsFp = None
    if setts['supportOutputfile'] != None: supportsFp = open(setts['supportOutputfile'], 'r')
    
    ## And to the work!
    ruleNro = 1
    while True:
        verbPrint(10,'Reading rule # %i'%ruleNro)
        currentR = Redescription.load(rulesFp, supportsFp)
        if len(currentR) == 0:
            break
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
        

        ruleNro = ruleNro + 1
    verbPrint(1,'Analyzed all %i rules\n'%(ruleNro-1))
    rulesFp.close()
    if supportsFp != None: supportsFp.close()
## END OF main()

if __name__ == "__main__": main()
        
