#!/usr/bin/python

import ConfigParser
import sys, re, datetime
from classLog import Log
from classSettings import Settings
from classData import Data
from classRedescription import Redescription
from classItemsDraft import ItemsDraft
from classBestsDraft import BestsDraft
from classSouvenirs import Souvenirs
from classConstraints import Constraints
import pdb

def run(arguments):
    pdb.set_trace()
    setts = Settings('mine', arguments)
    if setts.getParams() == 0:
        print setts.dispHelp()
        sys.exit(2)
    logger = Log(setts.param['verbosity'], setts.param['logfile'])
    logger.printL(5,'Settings:\n' + setts.dispParams())
    
    data = Data([setts.param['data_rep']+setts.param['data_l']+setts.param['ext_l'], setts.param['data_rep']+setts.param['data_r']+setts.param['ext_r']])
    logger.printL(2, data)

    if setts.param['out_base'] != "-"  and len(setts.param['out_base']) > 0  and len(setts.param['ext_queries']) > 0:
        queriesOutFp = open(setts.param['result_rep']+setts.param['out_base']+setts.param['ext_queries'], 'w')
    else: queriesOutFp = sys.stdout

    if setts.param['out_base'] != "-"  and len(setts.param['out_base']) > 0  and len(setts.param['ext_support']) > 0:
        supportOutFp = open(setts.param['result_rep']+setts.param['out_base']+setts.param['ext_support'], 'w')
    else:
        supportOutFp = None

    miner = Miner(data, setts, logger)
    try:
        miner.full_run()
    except KeyboardInterrupt:
        logger.printL(1, 'Stopped...')
        
    if supportOutFp != None:
        for currentRedescription in miner.final["results"]:
            currentRedescription.write(queriesOutFp, supportOutFp)

    queriesOutFp.close()
    supportOutFp.close()

    logger.printL(1, 'THE END (at %s)' % datetime.datetime.now())
## END of main()


if __name__ == "__main__":
    run(sys.argv)
