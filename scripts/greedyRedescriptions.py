#!/usr/bin/python

import ConfigParser
import sys
from classLog import Log
from classData import Data
from classRedescription import Redescription
from classRedescriptionsDraft import RedescriptionsDraft
from classBestsDraft import BestsDraft
from classSouvenirs import Souvenirs
from classSParts import SParts
from classConstraints import Constraints
import pdb

def getOpts(conf_filename):
    
    # Default settings
    setts = { 'verbosity': 1, 'logfile': '-',
              'data_rep': './',
              'data_l': 'left', 'ext_l':'.datbool',
              'data_r': 'right', 'ext_r':'.datbool',
              'result_rep': './', 'out_base': 'out' , 'ext_rules': '.rul', 'ext_support': '.supp',
              'nb_variables': 4, 'min_length': 2, 'contribution': 3,	                
              'min_suppin': 0.1, 'min_suppout': 0.7, 'min_acc': 0.0, 'max_pval': 0.05, 'method_pval' : 'marg',
              'nb_pairs': 0, 'method_pairs': 'overall', 'div_l': 1, 'div_r': 1, 'min_score': 0.01,
              'draft_capacity': 4, 'draft_output': 1, 'min_improvement': 0.0,
              'coeff_impacc': 1.0, 'coeff_relimpacc': 0.0, 'coeff_pvrule': 0.05, 'coeff_pvred': 0.05,
              'amnesic': False, 'max_side_identical': 2, 'forbid_rules': ''
              }

    # Sections to read in the config file
    sections_read = ['log', 'files', 'mine']

    config = ConfigParser.ConfigParser() 
    config.read(conf_filename)
    for sect in sections_read: 
        if config.has_section(sect):
            for (opti,val) in config.items(sect):
                if setts.has_key(opti):
                    try:
                        setts[opti] = type(setts[opti])(val)
                    except ValueError:
                        raise Exception('Unexpected value for %s %s, default is %s.' %(opti, val, setts[opti]))
    return setts

def processDraft(initialRed, data, draftCap, draftOut, minImpr, constraints, souvenirs, logger):    

    currentDraft = RedescriptionsDraft(draftCap)
    nextGen = [initialRed]
    logger.printL(1, "Expanding initial pair %i:  %s" % (data.count, initialRed))
    step = 0
    
    while len(nextGen) > 0 :
        step += 1
        logger.printL(2, "Expanding pair %i, step %i" % (data.count, step))
        kids = set()
        for red in nextGen :
            nb_extensions = red.updateAvailable(souvenirs)
            if red.nbAvailableCols() > 0:
                constraints.setRedLength(len(red))
                bests = BestsDraft(data.nbRows(), red.acc(), red.probas())
                for x in red.availableColsSide(0):
                    data.updateBests(bests, constraints, red.supports(), 0, x)

                for y in red.availableColsSide(1):
                    data.updateBests(bests, constraints, red.supports(), 1, y)

                if logger.verbosity >= 4:
                    logger.printL(4, "Redescription %s" % (red))
                    logger.printL(4, bests)
        
                for pos in bests.improving(minImpr):
                    t = red.kid(data, bests.side(pos), bests.op(pos), bests.term(pos), data.supp(bests.side(pos), bests.term(pos)), data.miss(bests.side(pos), bests.term(pos)) )
                    if t.acc() != bests.acc(pos):
                        print 'OUPS'
                        print '%s <~> %s %f ' % (t, bests.term(pos), bests.acc(pos))
                        pdb.set_trace()
                    kids.add(t)
                if nb_extensions == 0:
                    red.removeAvailables()
                    kids.add(red)

        souvenirs.update(kids)
        currentDraft.update(kids)
        nextGen = currentDraft.nextGeneration(constraints.checkFinalConstraints)
        
    currentDraft.cut(draftOut)
    return currentDraft.redescriptions()

def main():
    if len(sys.argv) > 1:
        conf_filename = sys.argv[1]
    else:
        conf_filename = ''
    setts = getOpts(conf_filename)
    logger = Log(setts['verbosity'], setts['logfile'])
    logger.printL(2,"Settings:\n %s" % (setts))
    Data.logger = logger; Redescription.logger = logger; RedescriptionsDraft.logger = logger; BestsDraft.logger = logger; Souvenirs.logger = logger; Constraints.logger = logger

    data = Data([setts['data_rep']+setts['data_l']+setts['ext_l'], setts['data_rep']+setts['data_r']+setts['ext_r']])
    logger.printL(2, data)

    if setts['out_base'] != "-"  and len(setts['out_base']) > 0  and len(setts['ext_rules']) > 0:
        rulesOutFp = open(setts['result_rep']+setts['out_base']+setts['ext_rules'], 'w')
    else: rulesOutFp = sys.stdout

    if setts['out_base'] != "-"  and len(setts['out_base']) > 0  and len(setts['ext_support']) > 0:
        supportOutFp = open(setts['result_rep']+setts['out_base']+setts['ext_support'], 'w')
    else:
        supportOutFp = None

    constraints = Constraints(data, setts)
    (BestsDraft.coeffImpacc, BestsDraft.coeffRelImpacc, BestsDraft.coeffPVRule, BestsDraft.coeffPVRed) = (setts['coeff_impacc'], setts['coeff_relimpacc'], setts['coeff_pvrule'], setts['coeff_pvred'])
    SParts.setMethodPVal(setts['method_pval'].capitalize())
    Redescription.nbVariables = setts['nb_variables']
    readyDraft = RedescriptionsDraft()
    souvenirs = Souvenirs(data.nonFull(), setts['amnesic'])
        
    data.setInitialMSelection(setts['method_pairs'], setts['div_l'], setts['div_r'])
#    pdb.set_trace()
    data.initializeRedescriptions(setts['nb_pairs'], constraints )
    initialRed = data.getNextInitialRed()

    while initialRed != None :
        try:
            reds = processDraft(initialRed, data, setts['draft_capacity'], setts['draft_output'], setts['min_improvement'], constraints, souvenirs, logger)
            if setts['max_side_identical'] == 0 and len(reds) > 0 :
                logger.printL(2, 'Appending reds...')
                for currentRedescription in reds: 
                    currentRedescription.write(rulesOutFp, supportOutFp)
            else:
                insertedIds = readyDraft.updateCheckOneSideIdentical(reds, setts['max_side_identical'])
                if len(insertedIds) > 0 :
                    logger.printL(2, 'Printing reds...')
                    rulesOutFp.flush(); rulesOutFp.seek(0); rulesOutFp.truncate()
                    if supportOutFp != None:
                        supportOutFp.flush(); supportOutFp.seek(0); supportOutFp.truncate()
                    for currentRedescription in readyDraft.redescriptions():
                        currentRedescription.write(rulesOutFp, supportOutFp)
                    
            initialRed = data.getNextInitialRed()

        except KeyboardInterrupt:
            logger.printL(1, 'Stopped...')
            break
                    
    if setts['max_side_identical'] > 0:
        logger.printL(2, 'Printing reds...')
        rulesOutFp.flush(); rulesOutFp.seek(0); rulesOutFp.truncate()
        if supportOutFp != None:
            supportOutFp.flush(); supportOutFp.seek(0); supportOutFp.truncate()
        for currentRedescription in readyDraft.redescriptions():
            currentRedescription.write(rulesOutFp, supportOutFp)
            
    rulesOutFp.close()
    supportOutFp.close()
    logger.printL(1, 'THE END')
## END of main()

if __name__ == "__main__":
    main()


    
