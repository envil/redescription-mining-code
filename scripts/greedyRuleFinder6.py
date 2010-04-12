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

    -L, --dataL=FILE
      Input data file left.
    -R, --dataR=FILE
      Input data file right.
      File names must have an extension indicating their format (sparse|dense|dat).
    -o, --output=FILE
      Output file.
    -O, --support-output=FILE
      Output file for rule supports.
    -k INT, --nb-variables=INT
      Maximum number of variables in a query.
    -n INT, --nb-rules=INT
      Maximum number of rules to make. Default = Inf.
    -c INT/FLOAT, --min-contribution=INT/FLOAT
      Minimum contribution per column. 
             as a number of rows (INT >= 1)
             or as a ratio of the number of the rows (0 <= FLOAT < 1).
    -f STRING, --score-formula=STRING
      Score formula used to rank initial pairs.
    -r FLOAT, --min-score=FLOAT
      Min score for initial pair to be considered.
    -R FLOAT, --max-score=FLOAT
      Max score for initial pair to be considered.
    -d INT, --draft-capacity=INT
      Max number of alternatives extensions explored a one step for a pair. (default 1)
    -D INT, --draft-output=INT
      Max number of alternatives extensions outputed for a pair. ( INT <= draft-capacity, default 1)
    -m FLOAT, --min-improvement=FLOAT
      Min improvement for a redescription to be added to the draft. ( default 0.00001)
    -A, --amnesic
      Amnesic mining, does not remember previously seen rules (default disabled)
    -i, --max-side-identical
      Max number times the same rule is allowed to appear on one side,
      when equal to zero, not constrained, rules are printed on the fly,
      else rules are printed at the end by order of decreasing accuracy  (default 0)

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
        opts, args = getopt.getopt(argv, "L:R:o:O:xp:k:n:s:c:f:r:R:d:D:m:Ai:vh", \
                                   ["help", "dataL=", "dataR=",  \
                                    "output=", "support-output=", \
                                    "nb-variables=", "nb-rules=", \
                                    "limit-support=", "min-contribution=", \
                                    "score-formula=", "draft-capacity=", "draft-output=", \
                                    "min-improvement=","amnesic", "max-side-identical=", \
                                    "without-and-nots", "without-or-nots",\
                                    "without-nots","without-ands","without-ors", \
                                    "verbosity=", "help"])
    except getopt.GetoptError, err:
        print str(err)
        usage()
        sys.exit(2)
    global setts
    setts['verb'] = 0
    
    setts['datafiles'] = ["inputL.txt", "inputR.txt"]
    setts['outputfile'] = "output.txt"
    setts['supportOutputfile'] = "support-output.txt"
    setts['nbVariables'] = 1
    setts['nbRules'] = sys.maxint
    setts['s'] = 1
    setts['c'] = 1
    setts['scoreFormula'] = 'suppI[i]/suppU[i]'
    setts['draft_cap'] = 1
    setts['draft_out'] = 1
    setts['minImpr'] = 0
    setts['amnesic'] = False
    setts['maxSideIden'] = 0
    ## rule types
    setts['rule_types'] = {False: set([False, True]), True: set([False, True])}
    for o, a in opts:
            
        if o in ("-L", "--dataL"): setts['datafiles'][0] = a
        if o in ("-R", "--dataR"): setts['datafiles'][1] = a
        if o in ("-o", "--output"): setts['outputfile'] = a
        if o in ("-O", "--support-output"): setts['supportOutputfile'] = a
        if o in ("-k", "--nb-variables"): setts['nbVariables'] = int(a)
        if o in ("-n", "--nb-rules"): setts['nbRules'] = int(a)
        if o in ("-s", "--limit-support"): setts['s'] = float(a)
        if o in ("-c", "--min-contribution"): setts['c'] = float(a)
        if o in ("-f", "--score-formula"): setts['scoreFormula'] = a
        if o in ("-d", "--draft-capacity"): setts['draft_cap'] = int(a)
        if o in ("-D", "--draft-output"): setts['draft_out'] = int(a)
        if o in ("-m", "--min-improvement"): setts['minImpr'] = float(a)
        if o in ("-A", "--amnesic"): setts['amnesic'] = True
        if o in ("-i", "--max-side-identical"): setts['maxSideIden'] = int(a)
        
        if o == "--witout-and-nots": setts['rule_types'][False].remove(True)
        if o == "--without-or-nots": setts['rule_types'][True].remove(True)
        if o == "--without-nots": setts['rule_types'][False].remove(True); setts['rule_types'][True].remove(True)
        if o == "--without-ands": del setts['rule_types'][False]
        if o == "--without-ors": del setts['rule_types'][True]
            
        if o in ("-h", "--help"):
            usage()
            sys.exit()
        if o == "-v": setts['verb'] += 1
        if o == "--verbosity": setts['verb'] = int(a)
        

def verbPrint(level, message):
    utilsIO.verbPrint(level, message, setts)

def getKids(currentRedescription, data, minImpr, maxImpr, ruleTypes, excludeCurr):    
    bests = BestsDraft(currentRedescription.acc())
    parts = currentRedescription.parts()
    for x in currentRedescription.availableColsSide(0):
        data.updateBests(bests, parts, 0, x, ruleTypes)

    for y in currentRedescription.availableColsSide(1):
        data.updateBests(bests, parts, 1, y, ruleTypes)
 
    verbPrint(8, currentRedescription)
    verbPrint(8, bests)
    kids = set()
    for i in bests.rank(minImpr, maxImpr, excludeCurr):
        kids.add(currentRedescription.kid(data, bests.side(i), bests.op(i), bests.term(i) ))
    return kids

def processDraft(currentDraft, data, minImpr, maxImpr, ruleTypes, souvenirs):    
    step = 0
    verbPrint(4, "Expanding pair, step %i" % (step))
    verbPrint(5, currentDraft)
    notBarren = currentDraft.notBarren()

    while len(notBarren) > 0 :
        step += 1
        kids = set()
        for red in notBarren : ## code getKids
            nb_extensions = red.updateAvailable(souvenirs)
            if red.nbAvailableCols() > 0:
                tmp_kids = getKids(red, data, minImpr, maxImpr, ruleTypes, nb_extensions > 0)
                if nb_extensions == 0 or len(tmp_kids) > 0:
                    kids.update(tmp_kids)
                    souvenirs.update(tmp_kids)
                else: ##if nb_extensions > 0 and len(tmp_kids) == 0:
                    verbPrint(8, 'HERE IS SOME ANCESTOR !')
                    ##pdb.set_trace()

        currentDraft.update(kids)
        verbPrint(4, "Expanding pair, step %i" % (step))
        verbPrint(5, currentDraft)
        verbPrint(5, souvenirs)
        ## sort kids and add to the draft
        notBarren = currentDraft.notBarren()


def main():
    getOpts(sys.argv[1:])
    utilsIO.setts = setts
    data = Data(setts['datafiles'])
    data.setMinSC(setts['s'], setts['c'])
    verbPrint(3, "Settings:\n %s" % (setts))
    verbPrint(3, data)
    Redescription.nbVariables = setts['nbVariables']
    readyDraft = RedescriptionsDraft()
    souvenirs = Souvenirs(data.nonFull(), setts['amnesic'])
    criterionsReady = [':red:length(1) + :red:length(0) > %i' % 3 ]

    output = open(setts['outputfile'], 'w')
    supportOutput = open(setts['supportOutputfile'], 'w', 1)
    
    ## Initialization phase, try all pairs:
    verbPrint(3, 'Searching for initial pairs')
    initialReds = data.initializeRedescriptions(setts['nbRules'], setts['rule_types'],  setts['scoreFormula'])
    verbPrint(3, "%i initial pairs" % len(initialReds))
    verbPrint(20, "Initial Pairs: %s" % str(initialReds))

    while len(initialReds) > 0 :
         currentDraft = RedescriptionsDraft(setts['draft_cap'])
         currentDraft.insert(initialReds.pop(0))

         processDraft(currentDraft, data, setts['minImpr'], float('Inf'), setts['rule_types'], souvenirs)
         ready = currentDraft.getReady(setts['draft_out'], criterionsReady) #setts['draft_out']

         if setts['maxSideIden'] > 0 :
             inserted = readyDraft.updateCheckOneSideIdentical(ready, setts['maxSideIden'])
             if inserted > 0:
                 verbPrint(7, "Ready draft")
                 verbPrint(7, readyDraft)
         else:
             for currentRedescription in ready:
                 verbPrint(6,"Redescription:\n"+currentRedescription.disp()+'\n\n')
                 currentRedescription.write(output, supportOutput)
    ## END for i in range(len(initialPairs))
                 
    if  setts['maxSideIden'] > 0 :           
## WRITE ALL REDESCRIPTIONS
        for currentRedescription in readyDraft.getSlice():
            verbPrint(6,"Redescription:\n"+currentRedescription.disp()+'\n\n')
            currentRedescription.write(output, supportOutput)

    output.close()
    supportOutput.close()
    verbPrint(1, 'END\n')
## END of main()

if __name__ == "__main__":
    main()


    
