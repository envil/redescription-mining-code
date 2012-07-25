#!/usr/bin/python

import sys, re, datetime, os.path
from toolLog import Log
from classData import Data
from classRedescription import Redescription
from classBatch import Batch
from classPreferencesManager import PreferencesManager, PreferencesReader
from classMiner import Miner
from classQuery import Query
import pdb

def loadRedescriptions(filename, data):
    fp = open(filename, "r")
    tmp = []
    red = Redescription.load(fp, None, data)
    while red[0] != None and len(red[0]) > 0:
        tmp.append(red[0])
        red = Redescription.load(fp, None, data)
    return tmp

def run_filter(arguments):
    params = getParams(sys.argv)
    params_l = {}
    for k, v in  params.items():
        params_l[k] = v["data"]

    logger = Log(params_l['verbosity'], params_l['logfile'])
    
    data = Data([params_l['data_rep']+params_l['data_l']+params_l['ext_l'], params_l['data_rep']+params_l['data_r']+params_l['ext_r']])
    logger.printL(2, data, "log")


    fileq = params_l['result_rep']+params_l['out_base']+params_l['ext_queries']
    t = loadRedescriptions(fileq, data)
    miner = Miner(data, params, logger)

    tr = miner.filter_run(t)
    for t in tr:
        print t.disp()

        
def getParams(arguments=[]):
    pref_dir = os.path.dirname(os.path.abspath(__file__))
    conf_defs = [pref_dir + "/miner_confdef.xml", pref_dir + "/inout_confdef.xml"]

    pm = PreferencesManager(conf_defs)
    pr = PreferencesReader(pm)
    config_filename = None
    if len(arguments) > 1:
        if arguments[1] == "--config":
            print pr.dispParameters(None,True, True, True)
            sys.exit(2)
        else:
            config_filename = arguments[1]

    params = pr.getParameters(config_filename)
    if params is None:
        print 'ReReMi redescription mining\nusage: "%s [config_file]"' % arguments[0]
        print '(Type "%s --config" to generate a default configuration file' % arguments[0]
        sys.exit(2)

    return params


 
def run(arguments):

    ticO = datetime.datetime.now()

    params = getParams(arguments)

    params_l = {}
    for k, v in  params.items():
        params_l[k] = v["data"]

    logger = Log(params_l['verbosity'], params_l['logfile'])
    
    data = Data([params_l['data_rep']+params_l['data_l']+params_l['ext_l'], params_l['data_rep']+params_l['data_r']+params_l['ext_r']])
    logger.printL(2, data, "log")

    if params_l['out_base'] != "-"  and len(params_l['out_base']) > 0  and len(params_l['ext_queries']) > 0:
        queriesOutFp = open(params_l['result_rep']+params_l['out_base']+params_l['ext_queries'], 'w')
    else: queriesOutFp = sys.stdout

    if params_l['out_base'] != "-"  and len(params_l['out_base']) > 0  and len(params_l['ext_support']) > 0:
        supportOutFp = open(params_l['result_rep']+params_l['out_base']+params_l['ext_support'], 'w')
    else:
        supportOutFp = None

    miner = Miner(data, params, logger)

    # tmpL = Query.parse("66 & ! 114 | 54")
    # tmpR = Query.parse("20>15.5<29.6 | 33>5.3357<8.3583")
    # r = Redescription.fromQueriesPair([tmpL, tmpR], data)
    # miner.part_run(r)

    try:
        miner.full_run()
    except KeyboardInterrupt:
        logger.printL(1, 'Stopped...', "log")
        
    if supportOutFp is not None:
        for pos in miner.final["results"]:
            miner.final["batch"][pos].write(queriesOutFp, supportOutFp)

    queriesOutFp.close()
    supportOutFp.close()

    tacO = datetime.datetime.now()
    logger.printL(1, 'THE END (at %s, elapsed %s)' % (tacO, tacO - ticO), "log")
## END of main()


if __name__ == "__main__":
    run(sys.argv)
