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
import pdb

def processDraft(initialRed, data, draftCap, draftOut, minImpr, queryTypes, souvenirs, logger):    

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
                bests = BestsDraft(queryTypes, data.N, red)
                for x in red.availableColsSide(0):
                    data.updateBests(bests, 0, x)

                for y in red.availableColsSide(1):
                    data.updateBests(bests, 1, y)

                for pos in bests.improving(minImpr, nb_extensions > 0):
                    kids.add(red.kid(data, bests.side(pos), bests.op(pos), bests.term(pos), bests.supp(pos) ))

        souvenirs.update(kids)
        currentDraft.update(kids)
        nextGen = currentDraft.nextGeneration(BestsDraft.checkFinalConstraints)
        
    currentDraft.cut(draftOut)
    return currentDraft.redescriptions()

def main():

    setts = Settings('mine', sys.argv)
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

    (Redescription.methodpVal, Redescription.nbVariables, Redescription.trackHisto) = (setts.param['method_pval'].capitalize(), setts.param['nb_variables'], setts.param['track_histo'])
    (BestsDraft.minC, BestsDraft.minSuppIn, BestsDraft.minSuppOut) = data.scaleSuppParams(setts.param['contribution'], setts.param['min_suppin'], setts.param['min_suppout'])
    (BestsDraft.coeffImpacc, BestsDraft.coeffRelImpacc, BestsDraft.coeffPVQuery, BestsDraft.coeffPVRed) = (setts.param['coeff_impacc'], setts.param['coeff_relimpacc'], setts.param['coeff_pvquery'], setts.param['coeff_pvred'])
    (BestsDraft.minLen, BestsDraft.minAcc, BestsDraft.maxPVal) = (setts.param['min_length'], setts.param['min_acc'], setts.param['max_pval'])

    readyDraft = RedescriptionsDraft()
    souvenirs = Souvenirs(data.nonFull(), setts.param['amnesic'])
        
    data.setInitialMSelection(setts.param['method_pairs'], setts.param['div_l'], setts.param['div_r'])
    data.initializeRedescriptions(setts.param['nb_pairs'], setts.param['query_types'], setts.param['min_score'])
    initialRed = data.getNextInitialRed()

    while initialRed != None :
        try:
            reds = processDraft(initialRed, data, setts.param['draft_capacity'], setts.param['draft_output'], setts.param['min_improvement'], setts.param['query_types'], souvenirs, logger)
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

if __name__ == "__main__":
    main()


    
