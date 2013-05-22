#!/usr/bin/python

import sys, re, datetime, os.path
from toolLog import Log
from classData import Data
from classRedescription import Redescription
from classBatch import Batch
from classPreferencesManager import PreferencesManager, PreferencesReader
from classMiner import Miner
from classQuery import Query
from codeRRM import RedModel
import pdb

def loadRedescriptions(filename, data):
    fp = open(filename, "r")
    tmp = []
    red = Redescription.load(fp, None, data)
    while red[0] != None and red[1] != -1:
        if len(red[0]) > 0:
            tmp.append(red[0])
        red = Redescription.load(fp, None, data)
    return tmp

def run_filter(params):
    # ta = do_filter(params)
    miner = Miner(data, params, logger)

    tf = miner.filter_run(ta)
    for ti, t in enumerate(tf):
        print t.disp()
    # names = [None, None]
    # if data.hasNames():
    #     names = data.getNames()

    #     print t.dispTexLine(ti, names)

def do_filter(params):

    params_l = {}
    for k, v in  params.items():
        params_l[k] = v["data"]

    fn_queries = params_l['result_rep']+params_l['out_base']+params_l['ext_queries']
    if fn_queries != "-" and params_l['logfile'] == "+":
        fn_log = params_l['result_rep']+params_l['out_base']+".fillog"
    else:
        fn_log = params_l['logfile']
    logger = Log(params_l['verbosity'], fn_log)
    
    data = Data([params_l['data_rep']+params_l['data_l']+params_l['ext_l'], params_l['data_rep']+params_l['data_r']+params_l['ext_r']], "multiple")
    logger.printL(2, data, "log")

    ta = loadRedescriptions(fn_queries, data)
    return ta
        
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

    return params, pm, pr


def run_dl(params):

    ticO = datetime.datetime.now()

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

    fn_queries = params_l['result_rep']+params_l['out_base']+params_l['ext_queries']
    if fn_queries != "-" and params_l['logfile'] == "+":
        fn_log = params_l['result_rep']+params_l['out_base']+".dllog"
    else:
        fn_log = params_l['logfile']

    logger = Log(params_l['verbosity'], fn_log)
    data = Data([fn_l, fn_r]+add_info, style_data)
    logger.printL(2, data, "log")
    names = data.getNames()

    logger.printL(2, "DL Model...", "log")
    rm = RedModel(data)

    logger.printL(2, "Loading reds...", "log")
    reds = loadRedescriptions(fn_queries, data)

    logger.printL(2, "Computing initial DL...", "log")
    ocs = rm.getEncodedLength(data)
    oc = sum(ocs)
    logger.printL(2, "Initial DL >> LHS=%f RHS=%f Qs=%f..." % tuple(ocs), "log")

    dirs = {None:"<>", 0:">>", 1:"<<"}
    try:
        rm.filterReds(reds, data, True, logger)
        logger.printL(2, "Done...", "log")
    except KeyboardInterrupt:
        logger.printL(1, 'Stopped...', "log")

    logger.printL(2, "Computing final DL...", "log")
    ncs = rm.getEncodedLength(data)
    nc = sum(ncs)
    logger.printL(2, "Final DL >> LHS=%f RHS=%f Qs=%f Gain=%f..." % (ncs[0], ncs[1], ncs[2], (oc-nc)/oc), "log")

    for ri, (sideAdd, red) in enumerate(rm.getReds()):
        logger.printL(1, "* (%d) %s\t%s" % (ri, dirs[sideAdd], red.dispQueries(names)), "log")
        logger.printL(1, "RED\t%s" % red.disp(), "log")
    tacO = datetime.datetime.now()
    logger.printL(1, 'THE END (at %s, elapsed %s)' % (tacO, tacO - ticO), "log")


def run(params):

    ticO = datetime.datetime.now()

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
            fn_names = fn_queries+"_names" 
            try:
                tfs = open(fn_queries, "a")
                tfs.close()
            except IOError:
                print "Queries output file not writable, use stdout instead..."
                fn_queries = "-"
                fn_names = None
                
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
    namesOutFp = None

    if queriesOutFp is not None:
        names = None
        if data.hasNames() and fn_names is not None:
            names = data.getNames()
            namesOutFp = open(fn_names, "w")
        for pos in miner.final["results"]:
            miner.final["batch"][pos].write(queriesOutFp, supportOutFp, namesOutFp, names)

    queriesOutFp.close()
    if supportOutFp is not None:
        supportOutFp.close()

    tacO = datetime.datetime.now()
    logger.printL(1, 'THE END (at %s, elapsed %s)' % (tacO, tacO - ticO), "log")
## END of main()


if __name__ == "__main__":
    params, pr, pm = getParams(sys.argv)
    if len(sys.argv) > 2 and sys.argv[2] == "filter":
        run_filter(params)
    if len(sys.argv) > 2 and sys.argv[2] == "dl":
        run_dl(params)
    else:
        run(params)
