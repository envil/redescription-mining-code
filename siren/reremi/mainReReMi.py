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
    
    data = Data([params_l['data_rep']+params_l['data_l']+params_l['ext_l'], params_l['data_rep']+params_l['data_r']+params_l['ext_r']], "multiple")
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
    options_args = arguments[1:]
    if len(arguments) > 1:
        if arguments[1] == "--config":
            print pr.dispParameters(None,True, True, True)
            sys.exit(2)
        if os.path.isfile(arguments[1]):
            config_filename = arguments[1]
            options_args = arguments[2:]
        
    params = pr.getParameters(config_filename, options_args)
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

    ### construct filenames
    if params_l['ext_l'] == ".csv" and params_l['ext_r'] == ".csv":
        style_data = "csv"
        add_info = [{}, "NA"]
    else:
        style_data = "multiple"
        add_info = []
        
    fn_l = params_l['data_rep']+params_l['data_l']+params_l['ext_l']
    fn_r = params_l['data_rep']+params_l['data_r']+params_l['ext_r']

    fn_log = params_l['logfile']
    fn_queries = "-"
    fn_support = None
    if params_l['out_base'] != "-"  and len(params_l['out_base']) > 0:
        if len(params_l['ext_queries']) > 0:
            fn_queries = params_l['result_rep']+params_l['out_base']+params_l['ext_queries']
            try:
                tfs = open(fn_queries, "a")
                tfs.close()
            except IOError:
                print "Queries output file not writable, use stdout instead..."
                fn_queries = "-"
                
            if fn_queries != "-" and params_l['logfile'] == "+":
                fn_log = params_l['result_rep']+params_l['out_base']+".log"

        if fn_queries != "-" and len(params_l['ext_support']) > 0:
            fn_support = params_l['result_rep']+params_l['out_base']+params_l['ext_support']

    logger = Log(params_l['verbosity'], fn_log)
    data = Data([fn_l, fn_r]+add_info, style_data)
    logger.printL(2, data, "log")

    miner = Miner(data, params, logger)

    # tmpL = Query.parse("66 & ! 114 | 54")
    # tmpR = Query.parse("20>15.5<29.6 | 33>5.3357<8.3583")
    # r = Redescription.fromQueriesPair([tmpL, tmpR], data)
    # miner.part_run(r)

    try:
        miner.full_run()
    except KeyboardInterrupt:
        logger.printL(1, 'Stopped...', "log")

    if fn_queries == "-":
        queriesOutFp = sys.stdout
    else:
        queriesOutFp = open(fn_queries, "w")

    if fn_support is None:
        supportOutFp = None
    else:
        supportOutFp = open(fn_support, "w")

    if queriesOutFp is not None:
        for pos in miner.final["results"]:
            miner.final["batch"][pos].write(queriesOutFp, supportOutFp)

    queriesOutFp.close()
    if supportOutFp is not None:
        supportOutFp.close()

    tacO = datetime.datetime.now()
    logger.printL(1, 'THE END (at %s, elapsed %s)' % (tacO, tacO - ticO), "log")
## END of main()


if __name__ == "__main__":
    run(sys.argv)
