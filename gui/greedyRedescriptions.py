#!/usr/bin/python

import ConfigParser
import sys, re, datetime
from classLog import Log
from classSettings import Settings
from classData import Data
from classRedescription import Redescription
from classRedescriptionsDraft import RedescriptionsDraft
from classBestsDraft import BestsDraft
from classSouvenirs import Souvenirs
from classConstraints import Constraints
import utilsTools as ut
import pdb

def processDraft(initialRed, data, draftCap, draftOut, minImpr, constraints, souvenirs, logger, keep=False, notify=None):    
    keepDraft = None
    if keep:
        keepDraft = RedescriptionsDraft()
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
        if keepDraft != None:
#            keepDraft.updateCheckOneSideIdentical(kids)
            insertedIds = keepDraft.update(kids)
            if notify != None:
                tmpE = []
                for (i,k) in insertedIds.items():
                    tmpE.append(keepDraft.redescriptions()[i])
                ut.sendResult(tmpE, notify)
        nextGen = currentDraft.nextGeneration(constraints.checkFinalConstraints)
        
    currentDraft.cut(draftOut)
    if keepDraft != None:
        return keepDraft.redescriptions()
    return currentDraft.redescriptions()

def run(arguments):

    setts = Settings('mine', arguments)
    if setts.getParams() == 0:
        print setts.dispHelp()
        sys.exit(2)
    logger = Log(setts.param['verbosity'], setts.param['logfile'])
    logger.printL(5,'Settings:\n' + setts.dispParams())

    tic = datetime.datetime.now()
    logger.printL(1,"TIC... Started: %s" % tic)

    Data.logger = logger; Redescription.logger = logger; RedescriptionsDraft.logger = logger; BestsDraft.logger = logger; Souvenirs.logger = logger
    
    data = Data([setts.param['data_rep']+setts.param['data_l']+setts.param['ext_l'], setts.param['data_rep']+setts.param['data_r']+setts.param['ext_r']])
    logger.printL(2, data)

    if setts.param['out_base'] != "-"  and len(setts.param['out_base']) > 0  and len(setts.param['ext_queries']) > 0:
        queriesOutFp = open(setts.param['result_rep']+setts.param['out_base']+setts.param['ext_queries'], 'w')
    else: queriesOutFp = sys.stdout

    if setts.param['out_base'] != "-"  and len(setts.param['out_base']) > 0  and len(setts.param['ext_support']) > 0:
        supportOutFp = open(setts.param['result_rep']+setts.param['out_base']+setts.param['ext_support'], 'w')
    else:
        supportOutFp = None

    constraints = Constraints(data, setts)
    Redescription.settings(setts)
    BestsDraft.settings(setts)

    readyDraft = RedescriptionsDraft()
    souvenirs = Souvenirs(data.nonFull(), setts.param['amnesic'])
        
    data.setInitialMSelection(setts.param['method_pairs'], setts.param['div_l'], setts.param['div_r'])
#    pdb.set_trace()
    tuc = datetime.datetime.now()
    logger.printL(1,"TUC... Start Pairs %s" % tuc)

    data.initializeRedescriptions(setts.param['nb_pairs'], constraints )
    
    tuc = datetime.datetime.now()
    logger.printL(1,"TUC... End Pairs %s" % tuc)
    
    initialRed = data.getNextInitialRed()

    while initialRed != None :
        tuc = datetime.datetime.now()
        logger.printL(1,"TUC... Start Expand %s" % tuc)
        try:
            reds = processDraft(initialRed, data, setts.param['draft_capacity'], setts.param['draft_output'], setts.param['min_improvement'], constraints, souvenirs, logger)
            if len(reds) > 0:
                if setts.param['max_side_identical'] == 0 :
                    logger.printL(2, 'Appending reds...')
                    for currentRedescription in reds: 
                        currentRedescription.write(queriesOutFp, supportOutFp)
                else :
                    insertedIds = readyDraft.updateCheckOneSideIdentical(reds, setts.param['max_side_identical'])
                    if len(insertedIds) > 0 :
                        logger.printL(2, 'Printing reds...')
                        queriesOutFp.flush(); queriesOutFp.seek(0); queriesOutFp.truncate()
                        if supportOutFp != None:
                            supportOutFp.flush(); supportOutFp.seek(0); supportOutFp.truncate()
                        for currentRedescription in readyDraft.redescriptions():
                            currentRedescription.write(queriesOutFp, supportOutFp)
                    
            initialRed = data.getNextInitialRed()

        except KeyboardInterrupt:
            logger.printL(1, 'Stopped...')
            break
                    
    if setts.param['max_side_identical'] > 0:
        logger.printL(2, 'Printing reds...')
        queriesOutFp.flush(); queriesOutFp.seek(0); queriesOutFp.truncate()
        if supportOutFp != None:
            supportOutFp.flush(); supportOutFp.seek(0); supportOutFp.truncate()
        for currentRedescription in readyDraft.redescriptions():
            currentRedescription.write(queriesOutFp, supportOutFp)

    queriesOutFp.close()
    supportOutFp.close()

    tac = datetime.datetime.now()
    logger.printL(1,"TAC... Ended: %s" % tac)
    logger.printL(1,"TIC-TAC Elapsed: %s" % (tac-tic))

    logger.printL(1, 'THE END')
## END of main()

def full_run(data, setts):
    data.count = 0
    logger = Log(setts.param['verbosity'], setts.param['logfile'])
    logger.printL(5,'Settings:\n' + setts.dispParams())

    tic = datetime.datetime.now()
    logger.printL(1,"TIC... Started: %s" % tic)

    Data.logger = logger; Redescription.logger = logger; RedescriptionsDraft.logger = logger; BestsDraft.logger = logger; Souvenirs.logger = logger
    
    data = Data([setts.param['data_rep']+setts.param['data_l']+setts.param['ext_l'], setts.param['data_rep']+setts.param['data_r']+setts.param['ext_r']])
    logger.printL(2, data)

    constraints = Constraints(data, setts)
    Redescription.settings(setts)
    BestsDraft.settings(setts)

    readyDraft = RedescriptionsDraft()
    souvenirs = Souvenirs(data.nonFull(), setts.param['amnesic'])
        
    data.setInitialMSelection(setts.param['method_pairs'], setts.param['div_l'], setts.param['div_r'])
#    pdb.set_trace()
    tuc = datetime.datetime.now()
    logger.printL(1,"TUC... Start Pairs %s" % tuc)

    data.initializeRedescriptions(setts.param['nb_pairs'], constraints )
    
    tuc = datetime.datetime.now()
    logger.printL(1,"TUC... End Pairs %s" % tuc)
    
    initialRed = data.getNextInitialRed()

    while initialRed != None :
        tuc = datetime.datetime.now()
        logger.printL(1,"TUC... Start Expand %s" % tuc)
    
        reds = processDraft(initialRed, data, setts.param['draft_capacity'], setts.param['draft_output'], setts.param['min_improvement'], constraints, souvenirs, logger)
        if len(reds) > 0:
            if setts.param['max_side_identical'] != 0 :
                insertedIds = readyDraft.updateCheckOneSideIdentical(reds, setts.param['max_side_identical'])
                    
        initialRed = data.getNextInitialRed()

    tac = datetime.datetime.now()
    logger.printL(1,"TAC... Ended: %s" % tac)
    logger.printL(1,"TIC-TAC Elapsed: %s" % (tac-tic))

    logger.printL(1, 'THE END')
    return readyDraft.redescriptions()
## END of main()


def part_run(data, setts, redesc, log=None, notify=None):
    data.count = 0
    if log == None:
        logger = Log(setts.param['verbosity'], setts.param['logfile'])
    else:
        logger = log
    logger.printL(5,'Settings:\n' + setts.dispParams())
    tic = datetime.datetime.now()
    Data.logger = logger; Redescription.logger = logger; RedescriptionsDraft.logger = logger; BestsDraft.logger = logger; Souvenirs.logger = logger
    logger.printL(1,"TIC... Started: %s" % tic)

    constraints = Constraints(data, setts)
    Redescription.settings(setts)
    BestsDraft.settings(setts)

    readyDraft = RedescriptionsDraft()
    souvenirs = Souvenirs(data.nonFull(), setts.param['amnesic'])

    redesc.initAvailable(souvenirs)
    tmpRed = processDraft(redesc, data, setts.param['draft_capacity'], -1, setts.param['min_improvement'], constraints, souvenirs, logger, True, notify)
    tac = datetime.datetime.now()
    logger.printL(1,"TAC... Finished: %s" % tac)
    return tmpRed

if __name__ == "__main__":
    run(sys.argv)


    
