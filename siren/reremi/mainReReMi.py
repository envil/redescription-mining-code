#!/usr/bin/python

import sys, re, datetime, os.path
from toolLog import Log
from classData import Data
from classRedescription import Redescription, parseRedList
from classBatch import Batch
from classPreferencesManager import PreferencesManager, PreferencesReader
from classMiner import Miner
from classQuery import Query
from codeRRM import RedModel
import pdb

def getParams(arguments=[]):
    pref_dir = os.path.dirname(os.path.abspath(__file__))
    conf_defs = [pref_dir + "/miner_confdef.xml", pref_dir + "/inout_confdef.xml"]

    pm = PreferencesManager(conf_defs)
    pr = PreferencesReader(pm)
    config_filename = None
    options_args = arguments[1:]

    if len(arguments) > 1:
        if arguments[1] == "--config":
            print pr.dispParameters(None, True, True, True)
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

def trunToDict(params):
    params_l = {}
    for k, v in  params.items():
        params_l[k] = v["data"]
    return params_l

def prepareFilenames(params):
    filenames = {"queries": "-",
                 "style_data": "multiple",
                 "add_info": [],
                 }
    
    if sys.platform != 'darwin':
        for p in ['result_rep', 'data_rep']:
            params_l[p] = re.sub("~", os.path.expanduser("~"), params_l[p])

    ### Make data file names
    if params_l['ext_l'] == ".csv" and params_l['ext_r'] == ".csv":
        filenames["style_data"] = "csv"
        filenames["add_info"] = [{}, params_l['str_NA']]

    if len(params_l["LHS_data"]) == 0 :
        filenames["LHS_data"] = params_l['LHS_data']
    else:
        filenames["LHS_data"] = params_l['data_rep']+params_l['data_l']+params_l['ext_l']
    if len(params_l["RHS_data"]) == 0 :
        filenames["RHS_data"] = params_l['RHS_data']
    else:
        filenames["RHS_data"] = params_l['data_rep']+params_l['data_r']+params_l['ext_r']

    ### Make queries file name
    if params_l['out_base'] != "-"  and len(params_l['out_base']) > 0:
        if len(params_l["queries_file"]) == 0 :
            filenames["queries"] = params_l["queries_file"]
        elif len(params_l['ext_queries']) > 0:
            filenames["queries"] = params_l['result_rep']+params_l['out_base']+params_l['ext_queries']
            try:
                tfs = open(filenames["queries"], "a")
                tfs.close()
            except IOError:
                print "Queries output file not writable, using stdout instead..."
                filenames["queries"] = "-"
    parts = filenames["queries"].split(".")
    basis = ".".join(parts[:-1])

    ### Make named queries file name
    if params_l["queries_named_file"] == "+" and filenames["queries"] != "-":
        filenames["queries_named"] = basis+"_named."+parts[-1]
    elif len(params_l["queries_named_file"]) > 0:
        filenames["queries_named"] = params_l["queries_named_file"]

    ### Make support file name
    if params_l["support_file"] == "+" and filenames["queries"] != "-"  and len(params_l['ext_support']) > 0::
        filenames["support"] = basis+params_l['ext_support']
    elif len(params_l["support_file"]) > 0:
        filenames["support"] = params_l["support_file"]

    ### Make log file name
    if params_l['logfile'] == "+" filenames["queries"] != "-" and len(params_l['ext_log']) > 0:
        filenames["logfile"] = basis+params_l['ext_log']
    elif len(params_l['logfile']) > 0:
        filenames["logfile"] = params_l['logfile']

    return filenames

def outputResults(filenames, results_batch, header=None, header_named=None, mode="w", data_recompute=None):
    header = Redescription.dispHeader()
    header_named = Redescription.dispHeader(named=True)
    
    filesfp = {"queries": None, "queries_named": None, "support": None}
    if filenames["queries"] == "-":
        filesfp["queries"] = sys.stdout
    else:
        filesfp["queries"] = open(filenames["queries"], mode)

    if "support" in filenames:
        filesfp["support"] = open(filenames["support"], mode)

    filesfp["queries"].write(header+"\n")
    if data.hasNames() and "queries_named" in filenames:
        names = data.getNames()
        filesfp["queries_named"] = open(filenames["queries_named"], mode)
        filesfp["queries_named"].write(header_named+"\n")

    for pos in results_batch["results"]:
        if data_recompute is not None:
            org = results_batch["batch"][pos]
            red = org.copy()
            red.recompute(data_recompute)
            acc_diff = (red.getAcc()-org.getAcc())/org.getAcc()
            miner.final["batch"][pos].write(queriesOutFp, supportOutFp, namesOutFp, names, "\t"+red.dispStats()+"\t%f" % acc_diff)
        else:
            results_batch["batch"][pos].write(queriesOutFp, supportOutFp, namesOutFp, names)

    for ffp in filesfp.values():
        if ffp is not None:
            ffp.close()



##### SOME ACTIONS
def run_filter(params, data, logger):
    # ta = do_filter(params)    
    miner = Miner(data, params, logger)

    tf = miner.filter_run(ta)
    for ti, t in enumerate(tf):
        print t.disp()

def do_filter(params):

    params_l = trunToDict(params)
    filenames = prepareFilenames(params_l)

    logger = Log(params_l['verbosity'], filenames["logfile"])
    data = Data([filenames["LHS_data"], filenames["RHS_data"]]+filenames["add_info"], filenames["style_data"])
    logger.printL(2, data, "log")

    ta = parseRedList(open(filenames["queries"], "r"), data)
    for ti, t in enumerate(ta):
        print t.disp(names)
        

def run_dl(params):

    ticO = datetime.datetime.now()
    params_l = trunToDict(params)
    filenames = prepareFilenames(params_l)

    logger = Log(params_l['verbosity'], filenames["logfile"])
    data = Data([filenames["LHS_data"], filenames["RHS_data"]]+filenames["add_info"], filenames["style_data"])
    logger.printL(2, data, "log")
    names = data.getNames()

    logger.printL(2, "DL Model...", "log")
    rm = RedModel(data)

    logger.printL(2, "Loading reds...", "log")
    reds = parseRedList(open(filenames["queries"], "r"), data)

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
    params_l = trunToDict(params)
    filenames = prepareFilenames(params_l)
 
    logger = Log(params_l['verbosity'], filenames["logfile"])
    data = Data([filenames["LHS_data"], filenames["RHS_data"]]+filenames["add_info"], filenames["style_data"])
    logger.printL(2, data, "log")

    miner = Miner(data, params, logger)

    try:
        miner.full_run()
    except KeyboardInterrupt:
        logger.printL(1, 'Stopped...', "log")

    outputResults(filenames, miner.final)

    tacO = datetime.datetime.now()
    logger.printL(1, 'THE END (at %s, elapsed %s)' % (tacO, tacO - ticO), "log")


def run_splits(params):

    ticO = datetime.datetime.now()
    params_l = trunToDict(params)
    filenames = prepareFilenames(params_l)
 
    logger = Log(params_l['verbosity'], filenames["logfile"])
    data = Data([filenames["LHS_data"], filenames["RHS_data"]]+filenames["add_info"], filenames["style_data"])
    logger.printL(2, data, "log")

    header = Redescription.dispHeader()+"\t"+Redescription.dispHeader(list_fields=Redescription.print_default_fields_stats)+"\tacc_diff\n"
    header_named = Redescription.dispHeader(named=True)+"\t"+Redescription.dispHeader(list_fields=Redescription.print_default_fields_stats, named=True)+"\tacc_diff\n"

    runid = 0
    while runid < params_l['splits_runs']:
        subsets_rids = data.getSplit(params_l['splits_nb'], params_l['splits_dim'], params_l['splits_grain'])
        # data.addSplitCol(subsets_rids)
        si = 0
        while si < len(subsets_rids):
            subset = subsets_rids[si]
            header_split = "### ---------- RUN %d SPLIT s%d ---------------" % (runid, si)
            header_splitlist = "### %s\n" % subset

            logger.printL(1, header_split, "log")

            sL, sT = data.get_LTsplit(subset)
            miner = Miner(sL, params, logger)
            try:
                miner.full_run()
            except KeyboardInterrupt:
                logger.printL(1, 'Stopped...', "log")
                si = len(subsets_rids)
                runid = params_l['splits_runs']

            if si*runid == 0:
                outputResults(filenames, miner.final,
                              header="\n".join([header, header_split, header_splitlist]),
                              header_named="\n".join([header_named, header_split, header_splitlist]),
                              mode="w", data_recompute=sT)
            else:
                outputResults(filenames, miner.final,
                              header="\n".join([header_split, header_splitlist]),
                              header_named="\n".join([header_split, header_splitlist]),
                              mode="a+", data_recompute=sT)

            si += 1
        runid += 1

    tacO = datetime.datetime.now()
    logger.printL(1, 'THE END (at %s, elapsed %s)' % (tacO, tacO - ticO), "log")


##### MAIN
###########
    
if __name__ == "__main__":
    params, pr, pm = getParams(sys.argv)
    if len(sys.argv) > 2 and sys.argv[2] == "filter":
        do_filter(params)
    elif len(sys.argv) > 2 and sys.argv[2] == "dl":
        run_dl(params)
    elif len(sys.argv) > 2 and sys.argv[2] == "splits":
        run_splits(params)
    else:
        run(params)
