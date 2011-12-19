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
from classQuery import Term, NumItem
import pdb
import pickle


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

    
    constraints = Constraints(data, setts)
    queriesInFp = open(setts.param['result_rep']+'queries.sav', 'r')
    supportInFp = open(setts.param['result_rep']+'support.sav', 'r')
       
    pic = open(setts.param['result_rep']+'pickles.sav', 'r')
    tmpIdsSets = pickle.load(pic)
    pic.close()

    tmpCurrGen = []
    terms = {}
    while True:
        (currentR, comment, commentSupp)= Redescription.load(queriesInFp, supportInFp, data)
        if len(currentR) == 0 and comment == '':
                break
        else:
            tmp = currentR.invTerms()
            termL = tmp[0].pop()
            termR = tmp[1].pop()

            if not terms.has_key((0, termL.col())): 
                terms[(0, termL.col())] = []
            terms[(0, termL.col())].append((termR.col(), termR.item.lowb, termR.item.upb, currentR.acc()))

            if not terms.has_key((0, termR.col())): 
                terms[(0, termR.col())] = []
            terms[(0, termR.col())].append((termL.col(), termR.item.lowb, termR.item.upb, currentR.acc()))

            tmpCurrGen.append(currentR)

    for (side, col) in [(0,35)]: # terms.keys():
        print "##### %d %d (%d)" % (side, col, len(terms[(side, col)]))
        terms[(side, col)].sort(key= lambda x: x[3], reverse=True)
        for (col, lowb, upb, acc) in terms[(side, col)]:
            print "%d %f %f %f" % (col,  lowb, upb, acc)
        
    queriesInFp.close()
    supportInFp.close()


    tac = datetime.datetime.now()
    logger.printL(1,"TAC... Ended: %s" % tac)
    logger.printL(1,"TIC-TAC Elapsed: %s" % (tac-tic))

    logger.printL(1, 'THE END')
## END of main()

if __name__ == "__main__":
    main()


    
