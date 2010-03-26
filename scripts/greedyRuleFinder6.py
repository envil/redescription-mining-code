#!/usr/bin/python

import sys, getopt, math, random, utilsIO
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
    setts['rule_types'] = {}
    setts['rule_types']['and_nots'] = True
    setts['rule_types']['or_nots'] = True
    setts['rule_types']['nots'] = True
    setts['rule_types']['ands'] = True
    setts['rule_types']['ors'] = True
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
        
        if o == "--witout-and-nots": setts['rule_types']['and_nots'] = False
        if o == "--without-or-nots": setts['rule_types']['or_nots'] = False
        if o == "--without-nots":
            setts['rule_types']['nots'] = False
            setts['rule_types']['and_nots'] = False
            setts['rule_types']['or_nots'] = False
        if o == "--without-ands":
            setts['rule_types']['ands'] = False
            setts['rule_types']['and_nots'] = False
        if o == "--without-ors":
            setts['rule_types']['ors'] = False
            setts['rule_types']['or_nots'] = False
            
        if o in ("-h", "--help"):
            usage()
            sys.exit()
        if o == "-v": setts['verb'] += 1
        if o == "--verbosity": setts['verb'] = int(a)
        

def verbPrint(level, message):
    utilsIO.verbPrint(level, message, setts)

def addInitialPair(N, suppA, suppB, idA, idB, initialPairs, ruleTypes, scoreFormula='suppI[i]/suppU[i]'):

    c = float(len(suppA & suppB))
    a = float(len(suppA - suppB))
    b = float(len(suppB - suppA))

## Evaluate score for AB AbB ABb AbBb
    if ruleTypes['and_nots'] or ruleTypes['or_nots'] :
        suppI = [ c, b, a, N-a-b-c]
        suppU = [ a+b+c, N-a, N-b, N-c]
        suppA = [ a+c, N-a-c, a+c, N-a-c]
        suppB = [ b+c, b+c, N-b-c, N-b-c]
        rand = [random.random()  for i in range(4)]
## Evaluate score for AB only
    else:
        suppI = [ c]
        suppU = [ a+b+c]
        suppA = [ a+c]
        suppB = [ b+c]
        rand = [random.random()]

    ## compute score according to given formula
    for i in range(len(suppI)):
        initialPairs.append((eval(scoreFormula), Term(i in [1, 3], idA), Term(i in [2, 3], idB), suppI[i] ))
    # for i in range(len(suppI)):
#         s = eval(scoreFormula)
#         if s > minScore and s < maxScore and suppI[i] >= minC and suppI[i] <= N - minC :
#             Ab = i in [1, 3]
#             Bb = i in [2, 3]
#             initialPairs.append((s, idA, idB, Ab, Bb, suppI[i] ))

def initializePairs(data, availableCols, nbPairs, ruleTypes, scoreFormula='suppI[i]/suppU[i]'):
    initialPairs = []
    for idL in availableCols[0]:
        verbPrint(10, 'Searching for intial pairs (idL:%i, *)' %idL)
        for idR in  availableCols[1]:
            addInitialPair(data.N, data.vect(0,idL), data.vect(1,idR), idL, idR, initialPairs, ruleTypes, scoreFormula)
    initialPairs.sort(key=lambda x: x[0], reverse=True) 
    if len(initialPairs) > nbPairs:
        initialPairs = initialPairs[:nbPairs]
    return initialPairs

def updateBestsBool(bests, palpha, pbeta, pgamma, pdelta, side, x, suppX, minSupp, maxSupp, ruleTypes):
    ingamma = float(len(pgamma & suppX))
    inalpha = float(len(palpha & suppX))
    inbeta = float(len(pbeta & suppX))
    indelta = float(len(pdelta & suppX))
    gamma = len(pgamma)
    alpha = len(palpha)
    beta = len(pbeta)
    delta = len(pdelta)
    
    verbPrint(9, 'Col %i: (%i / %i, %i / %i, %i / %i, %i / %i)' % \
              (x, inalpha, alpha, inbeta, beta, ingamma, gamma, indelta, delta))

    if ruleTypes['ands'] and ingamma >= minSupp:
        bests.upBest(side, Op(False), Term(False,x), ingamma / (beta + gamma + inalpha), inalpha, ingamma)

    if ruleTypes['and_nots'] and gamma - ingamma >= minSupp :
        bests.upBest(side, Op(False), Term(True,x), (gamma - ingamma) / (beta + gamma + alpha - inalpha), alpha - inalpha, gamma - ingamma)

    if ruleTypes['ors'] and alpha + gamma + inbeta + indelta <= maxSupp :
        bests.upBest(side, Op(True), Term(False,x), (inbeta + gamma)/ (alpha + beta + gamma + indelta), indelta, inbeta)

    if ruleTypes['or_nots'] and alpha + gamma + beta - inbeta + delta - indelta <= maxSupp :
        bests.upBest(side, Op(True), Term(True,x), (beta - inbeta + gamma)/ (alpha + beta + gamma + delta - indelta),  delta - indelta,  delta - inbeta)

def updateBestsCat(bests, palpha, pbeta, pgamma, pdelta, side, x, suppX, minSupp, maxSupp, ruleTypes):
    ## TODO
    print "To be defined"
    
def updateBestsNum(bests, palpha, pbeta, pgamma, pdelta, side, x, suppX, minSupp, maxSupp, ruleTypes):
    ## TODO
    print "To be defined"

def getKids(currentRedescription, data, minContribution, minImpr, maxImpr, ruleTypes, excludeCurr):    

    minSupp = minContribution*(1+max(currentRedescription.length(0), currentRedescription.length(1)))
    maxSupp = data.N - minContribution*(1+max(currentRedescription.length(0), currentRedescription.length(1)))
    
    bests = BestsDraft(currentRedescription.acc(), minContribution)
    (alpha, beta, gamma, delta) = currentRedescription.parts()
    for x in currentRedescription.availableColsSide(0):
        eval('updateBests' + data.dataTypeSuffs[0])(bests, alpha, beta, gamma, delta, 0, x, data.vect(0,x), minSupp, maxSupp, ruleTypes)
        
    for y in currentRedescription.availableColsSide(1):
        eval('updateBests' + data.dataTypeSuffs[1])(bests, beta, alpha, gamma, delta, 1, y, data.vect(1,y), minSupp, maxSupp, ruleTypes)

    verbPrint(8, currentRedescription)
    verbPrint(8, bests)
    kids = set()
    for i in bests.rank(minImpr, maxImpr, excludeCurr):
        kids.add(currentRedescription.kid(data, bests.side(i), bests.op(i), bests.term(i) ))
    return kids

def processDraft(currentDraft, data, minContribution, minImpr, maxImpr, ruleTypes, souvenirs):    
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
                tmp_kids = getKids(red, data, minContribution, minImpr, maxImpr, ruleTypes, nb_extensions > 0)
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
    setts['minC'] = data.updateC(setts['c'])
    (setts['minSupp'], setts['maxSupp']) = data.updateS(setts['s'])
    verbPrint(3, "Settings:\n %s" % (setts))
    verbPrint(3, data)
    Redescription.nbVariables = setts['nbVariables']
    readyDraft = RedescriptionsDraft()
    souvenirs = Souvenirs([data.nonFullCols(setts['minC'],0),data.nonFullCols(setts['minC'],1)], setts['amnesic'])
    criterionsReady = [':red:length(1) + :red:length(0) > %i' % 3, \
                      ':red:lenI() > %i' % setts['minSupp'], \
                      ':red:lenI() < %i' % setts['maxSupp'] ]

    output = open(setts['outputfile'], 'w')
    supportOutput = open(setts['supportOutputfile'], 'w', 1)
    
    ## Initialization phase, try all pairs:
    verbPrint(3, 'Searching for initial pairs')
    initialPairs = initializePairs(data, souvenirs.availableMo, setts['nbRules'], setts['rule_types'],  setts['scoreFormula'])
    verbPrint(3, "%i initial pairs" % len(initialPairs))
    verbPrint(20, "Initial Pairs: %s" % str(initialPairs))

    while len(initialPairs) > 0 :
         currentDraft = RedescriptionsDraft(setts['draft_cap'])
         currentDraft.insert(Redescription.fromInitialPair(initialPairs.pop(0), data, souvenirs))

         processDraft(currentDraft, data, setts['minC'], setts['minImpr'], float('Inf'), setts['rule_types'], souvenirs)
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


    
