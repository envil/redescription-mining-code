#!/usr/bin/python

import sys, getopt, utilsIO
from classRule import *
from classRedescription import *
from classData import *
from classRedescriptionDraft import *
from classBestsDraft import *
from classSouvenirs import *
import pdb, time

## Global variables
setts={}

def usage():
    print """
    Usage: %s [options]

    Input files:
    ------------
        Input filenames must have an extension indicating the data format (sparse|dense|dat|num).
    -L / --dataL=FILENAME
    Left-hand side data
    -R / --dataR=FILENAME
    Right-hand side data
    -o / --rules-out=FILENAME
    Rules output file (default stdout)
    -O / --support-out=FILENAME
    Support output file

    -k / --nb-variables=INT
    Max number of variables on each side
    -K / --min-len=INT
    Min overall lenght

    Contribution and support limits:
    --------------------------------
        can be specified either
        * as a number of rows (INT >= 1)
        * or as a ratio of the number of the rows (0 <= FLOAT < 1).
    -c / --contribution=INT/FLOAT
    Min column contribution (default 1)
    -p / --itm-in=INT/FLOAT
    Min running intersection (default min contribution)
    -q / --itm-out=INT/FLOAT
    Min running left uncovered (default N - min running intersection)
    -P / --fin-in=INT/FLOAT
    Min final intersection (default min running intersection)
    -Q / --fin-out=INT/FLOAT
    Min final left uncovered (default N - min final intersection)

    Initial pairs:
    --------------
    -n / --nb-rules=INT
    Max number of rules (default 0=unlimited)
    -N / --meth-sel=(alternate|overall)
    Method for generating the next pair (default overall)
    * overall: next best scoring pair
    * alternate: next best scoring pair for column A,
    taking all columns i turns alternating between right and left hand side
    -f / --div-L=INT
    Sample columns left hand side to generate pairs (default 1, all columns)
    -F / --div-R=INT
    Sample columns right hand side to generate pairs (default 1, all columns)
    -s / --min-score=FLOAT
    Min score for a pair to be considered (default 0)

    Greedy redescription generation:
    --------------------------------
    -d / --draft-capacity=INT
    Max number of non-equivalent alternative redescriptions to keep in the draft for one pair (default 1)
    -D / --draft-output=INT
    Max number of non-equivalent alternative redescriptions to output for one pair (default 1)
    -b / --min-improvement=FLOAT
    Min improvement score for an alternative to be kept in the draft (default 0)
    -u / --coeff-impacc=FLOAT
    Coefficient of improvement in accuracy in the improvement score (default 1)
    -U / --coeff-relimpacc=FLOAT
    Coefficient of the relative inprovement in accuracy in the improvement score (default 0)
    -w / --coeff-pvrule=FLOAT
    Coefficient of the p-value of the rule overlap in the improvement score (default 1)
    -W / --coeff-pvred=FLOAT
    Coefficient of the p-value of the redescription overlap in the improvement score (default 1)
    -A / --amnesic
    Amnesic, do not remember previously seen rules (default False)
    -a / --max-side-identical=INT
    Maximum number of non-equivalent redescriptions for a same rule to be kept (default 2)
    if unlimited all rules are printed at the end, else they are printed on the fly

    Rule types:
    -----------
    Options that select the type of the rules used.
    Default is with all enabled.
    --without-and-nots
      Do not search rules with negated conjunctions.
    --without-or-nots
      Do not search rules with negated disjunctions.
    --without-nots
      Disable all negations, i.e., search only monotone rules.
    --without-ands
      Disable all conjunctions.
    --without-ors
      Disable all disjunctions.
      
    -v, --verbosity=INT
      Verbosity level, use either many v's or verbosity.
    -h, --help
      This text.
    """%sys.argv[0]




def getOpts(argv):
    try:


        opts, args = getopt.getopt(argv, \
                                   "L:R:o:O:k:K:c:p:q:P:Q:n:N:f:F:s:d:D:b:u:U:w:W:Aa:hv" , \
                                   [ "dataL=", "dataR=", "rules-out=", "support-out=", \
                                     "nb-variables=", "min-len=", \
                                     "contribution=", "itm-in=", "itm-out=", "fin-in=", "fin-out=", \
                                     "nb-rules=", "meth-sel=", "div-L=", "div-R=", "min-score=", \
                                     "draft-capacity=", "draft-output=", \
                                     "min-improvement=", "coeff-impacc=", "coeff-relimpacc=", "coeff-pvrule=", "coeff-pvred=", \
                                     "amnesic", "max-side-identical=", \
                                     "witout-and-nots", "without-or-nots", \
                                     "without-nots", "without-ands", "without-ors", \
                                     "help", "verbosity=" ])
    except getopt.GetoptError, err:
        print str(err)
        usage()
        sys.exit(2)
    global setts
    setts['verb'] = 0

    setts['dataFiles'] = ["dataL.dat", "dataR.dat"]
    setts['rulesOutFile'] = "-"
    setts['supportOutFile'] = None

    setts['nbVariables'] = 1
    setts['minLen'] = 2
    setts['minC'] = None
    setts['minItmIn'] = None
    setts['minItmOut'] = None
    setts['minFinIn'] = None
    setts['minFinOut'] = None

    setts['nbRules'] = 0
    setts['methodSel'] = 'overall'
    setts['divL'] = 1
    setts['divR'] = 1
    setts['minScore'] = None

    setts['draftCap'] = 1
    setts['draftOut'] = 1
    setts['minImpr'] = 0
    setts['coeffImpacc'] = 1
    setts['coeffRelImpacc'] = 0
    setts['coeffPVRule'] = 1
    setts['coeffPVRed'] = 1
    setts['amnesic'] = False
    setts['maxSideIden'] = 0
    ## rule types
    setts['ruleTypes'] = {False: set([False, True]), True: set([False, True])}
    for o, a in opts:
            
        if o in ("-L", "--dataL"): setts['dataFiles'][0] = a
        if o in ("-R", "--dataR"): setts['dataFiles'][1] = a
        if o in ("-o", "--rules-out"): setts['rulesOutFile'] = a
        if o in ("-O", "--support-out"): setts['supportOutFile'] = a

        if o in ("-k", "--nb-variables"): setts['nbVariables'] = int(a)
        if o in ("-K", "--min-len"): setts['minLen'] = int(a)
        if o in ("-c", "--contribution"): setts['minC'] = float(a)
        if o in ("-p", "--itm-in"): setts['minItmIn'] = float(a)
        if o in ("-q", "--itm-out"): setts['minItmOut'] = float(a)
        if o in ("-P", "--fin-in"): setts['minFinIn'] = float(a)
        if o in ("-Q", "--fin-out"): setts['minFinOut'] = float(a)
        
        if o in ("-n", "--nb-rules"): setts['nbRules'] = int(a)
        if o in ("-N", "--meth-sel"): setts['methodSel'] = a
        if o in ("-f", "--div-L"): setts['divL'] = int(a)
        if o in ("-F", "--div-R"): setts['divR'] = int(a)
        if o in ("-s", "--min-score"): setts['minScore'] = float(a)

        if o in ("-d", "--draft-capacity"): setts['draftCap'] = int(a)
        if o in ("-D", "--draft-output"): setts['draftOut'] = int(a)
        if o in ("-b", "--min-improvement"): setts['minImpr'] = float(a)
        if o in ("-w", "--coeff-impacc"): setts['coeffImpacc'] = float(a)
        if o in ("-w", "--coeff-relimpacc"): setts['coeffRelImpacc'] = float(a)
        if o in ("-w", "--coeff-pvrule"): setts['coeffPVRule'] = float(a)
        if o in ("-w", "--coeff-pvred"): setts['coeffPVRed'] = float(a)
        if o in ("-A", "--amnesic"): setts['amnesic'] = True
        if o in ("-a", "--max-side-identical"): setts['maxSideIden'] = int(a)
        
        if o == "--witout-and-nots": setts['ruleTypes'][False].remove(True)
        if o == "--without-or-nots": setts['ruleTypes'][True].remove(True)
        if o == "--without-nots": setts['ruleTypes'][False].remove(True); setts['ruleTypes'][True].remove(True)
        if o == "--without-ands": del setts['ruleTypes'][False]
        if o == "--without-ors": del setts['ruleTypes'][True]
            
        if o in ("-h", "--help"):
            usage()
            sys.exit()
        if o == "-v": setts['verb'] += 1 
        if o == "--verbosity": setts['verb'] = int(a)
        
def verbPrint(level, message):
    utilsIO.verbPrint(level, message, setts)

def processDraft(initialRed, data, draftCap, draftOut, minImpr, ruleTypes, souvenirs):    

    currentDraft = RedescriptionsDraft(draftCap)
    nextGen = [initialRed]
    verbPrint(3, "Expanding initial pair %i:  %s" % (data.count, initialRed))
    step = 0
    
    while len(nextGen) > 0 :
        step += 1
        verbPrint(4, "Expanding pair %i, step %i" % (data.count, step))
        kids = set()
        for red in nextGen :
            nb_extensions = red.updateAvailable(souvenirs)
            if red.nbAvailableCols() > 0:
                bests = BestsDraft(ruleTypes, data.N, red)
                for x in red.availableColsSide(0):
                    data.updateBests(bests, 0, x)

                for y in red.availableColsSide(1):
                    data.updateBests(bests, 1, y)
                verbPrint(7, bests)
                for pos in bests.improving(minImpr, nb_extensions > 0):
                    kids.add(red.kid(data, bests.side(pos), bests.op(pos), bests.term(pos), bests.supp(pos) ))

        souvenirs.update(kids)
        currentDraft.update(kids)
        verbPrint(5, currentDraft)
        verbPrint(5, souvenirs)
        nextGen = currentDraft.nextGeneration(BestsDraft.finalOK)
        
    currentDraft.cut(draftOut)
    return currentDraft.redescriptions()

def main():
    getOpts(sys.argv[1:])
    utilsIO.setts = setts

    verbPrint(3, "Settings:\n %s" % (setts))
    data = Data(setts['dataFiles'])
    verbPrint(3, data)
    (BestsDraft.minC, BestsDraft.minItmIn, BestsDraft.minItmOut, BestsDraft.minFinIn, BestsDraft.minFinOut) = data.scaleSuppParams(setts['minC'], setts['minItmIn'], setts['minItmOut'], setts['minFinIn'], setts['minFinOut'])
    (BestsDraft.minLen, BestsDraft.coeffImpacc, BestsDraft.coeffRelImpacc, BestsDraft.coeffPVRule, BestsDraft.coeffPVRed) = \
                        (setts['minLen'], setts['coeffImpacc'], setts['coeffRelImpacc'], setts['coeffPVRule'], setts['coeffPVRed'])
    verbPrint(3, BestsDraft.dispParams())
    Redescription.nbVariables = setts['nbVariables']
    readyDraft = RedescriptionsDraft()
    souvenirs = Souvenirs(data.nonFull(), setts['amnesic'])
    if setts['rulesOutFile'] != "-"  and len(setts['rulesOutFile']) > 0 :
        rulesOutFp = open(setts['rulesOutFile'], 'w')
    else: rulesOutFp = sys.stdout

    if setts['supportOutFile'] != None  and len(setts['supportOutFile']) > 0:
        supportOutFp = open(setts['supportOutFile'], 'w')
    else:
        supportOutFp = None
    (rulesOutFpTmp, supportOutFpTmp) = (rulesOutFp, supportOutFp) 
        
    verbPrint(3, 'Searching for initial pairs (%s, %i/%ix%i/%i) ' % (setts['methodSel'], data.nbNonFull(0), setts['divL'], data.nbNonFull(1), setts['divR']))
    data.setInitialMSelection(setts['methodSel'], setts['divL'], setts['divR'])
    data.initializeRedescriptions(setts['nbRules'], setts['ruleTypes'], setts['minScore'])
    verbPrint(2, '%i initial pairs' % data.nbRed)
    initialRed = data.getNextInitialRed()
    
    while initialRed != None :
        reds = processDraft(initialRed, data, setts['draftCap'], setts['draftOut'], setts['minImpr'], setts['ruleTypes'], souvenirs)
        
        verbPrint(2,"Redescriptions output (%i):" % (data.count))
        if setts['maxSideIden'] > 0 :

            insertedIds = readyDraft.updateCheckOneSideIdentical(reds, setts['maxSideIden'])
            for i in range(len(reds)):
                if i in insertedIds.keys():
                    verbPrint(3,"Redescription (YES):\t"+reds[i].dispSimple())
                else:
                    verbPrint(3,"Redescription (NO):\t"+reds[i].dispSimple())
            if len(insertedIds) > 0:
                #pdb.set_trace()
                reds = readyDraft.redescriptions()
                rulesOutFp.flush()
                rulesOutFp.seek(0)
                rulesOutFp.truncate()
                if supportOutFp != None:
                    supportOutFp.seek(0)
            else:
                reds = []

        verbPrint(2,"---------------------------------------")
        for currentRedescription in reds:
            verbPrint(2,currentRedescription.disp())
            currentRedescription.write(rulesOutFp, supportOutFp)
        
        initialRed = data.getNextInitialRed()

    rulesOutFp.close()
    supportOutFp.close()
    verbPrint(1, 'END\n')
## END of main()

if __name__ == "__main__":
    main()


    
