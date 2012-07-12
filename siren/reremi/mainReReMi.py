#!/usr/bin/python

import sys, re, datetime
from toolLog import Log
from toolSettings import Settings
from classData import Data
from classRedescription import Redescription
from classBatch import Batch
from classMiner import Miner
import pdb
 
def run(arguments):

    ticO = datetime.datetime.now()
    setts = Settings('mine', arguments)
    if setts.getParams() == 0:
        print setts.dispHelp()
        sys.exit(2)
    logger = Log(setts.param['verbosity'], setts.param['logfile'])
    logger.printL(5,'Settings:\n' + setts.dispParams())
    
    data = Data([setts.param['data_rep']+setts.param['data_l']+setts.param['ext_l'], setts.param['data_rep']+setts.param['data_r']+setts.param['ext_r']])
    logger.printL(2, data, "log")

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
        logger.printL(1, 'Stopped...', "log")
        
    if supportOutFp != None:
        for pos in miner.final["results"]:
            miner.final["batch"][pos].write(queriesOutFp, supportOutFp)

    queriesOutFp.close()
    supportOutFp.close()

    tacO = datetime.datetime.now()
    logger.printL(1, 'THE END (at %s, elapsed %s)' % (tacO, tacO - ticO), "log")
## END of main()


if __name__ == "__main__":
    run(sys.argv)
