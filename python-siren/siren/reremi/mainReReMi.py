#!/usr/bin/python

import sys, re, os.path
import numpy
import tempfile
from toolLog import Log
from classPackage import Package
from classData import Data
from classRedescription import Redescription, parseRedList
from classBatch import Batch
from classPreferencesManager import PreferencesManager, PreferencesReader
from classMiner import instMiner, StatsMiner
from classQuery import Query
import pdb


def loadAll(arguments=[]):
    pref_dir = os.path.dirname(os.path.abspath(__file__))
    conf_defs = [pref_dir + "/miner_confdef.xml", pref_dir + "/inout_confdef.xml"]
    pm = PreferencesManager(conf_defs)

    pack_filename = None
    config_filename = None
    tmp_dir = None
    params = None
    options_args = arguments[1:]

    if len(arguments) > 1:
        if arguments[1] == "--config":
            print PreferencesReader(pm).dispParameters(None, True, True, True)
            sys.exit(2)
        if os.path.isfile(arguments[1]):
            if os.path.splitext(arguments[1])[1] == Package.DEFAULT_EXT:
                pack_filename = arguments[1]
                if len(arguments) > 2 and os.path.isfile(arguments[2]):
                    config_filename = arguments[2]
                    options_args = arguments[3:]
                else:
                    options_args = arguments[2:]
            else:
                config_filename = arguments[1]
                options_args = arguments[2:]

    if pack_filename is not None:
        package = Package(pack_filename)
        elements_read = package.read(pm)        
        data = elements_read.get("data", None)
        params = elements_read.get("preferences", None)
        tmp_dir = package.getTmpDir()

    params = PreferencesReader(pm).getParameters(config_filename, options_args, params)
    if params is None:
        print 'ReReMi redescription mining\nusage: "%s [package] [config_file]"' % arguments[0]
        print '(Type "%s --config" to generate a default configuration file' % arguments[0]
        sys.exit(2)

    params_l = trunToDict(params)
    filenames = prepareFilenames(params_l, tmp_dir) 
    logger = Log(params_l['verbosity'], filenames["logfile"])

    if pack_filename is None:
        data = Data([filenames["LHS_data"], filenames["RHS_data"]]+filenames["add_info"], filenames["style_data"])
    logger.printL(2, data, "log")

    if pack_filename is not None:
        filenames["package"] = os.path.abspath(pack_filename)
    print filenames
    return params, data, logger, filenames

def trunToDict(params):
    params_l = {}
    for k, v in  params.items():
        params_l[k] = v["data"]
    return params_l

def prepareFilenames(params_l, tmp_dir=None):
    filenames = {"queries": "-",
                 "style_data": "csv",
                 "add_info": [{}, params_l['NA_str']]
                 }
    
    for p in ['result_rep', 'data_rep']:
        if params_l[p] == "__TMP_DIR__":
            if tmp_dir is None:
                tmp_dir = tempfile.mkdtemp(prefix='ReReMi')
            params_l[p] = tmp_dir + "/"
        elif sys.platform != 'darwin':
            params_l[p] = re.sub("~", os.path.expanduser("~"), params_l[p])

    ### Make data file names
    if len(params_l["LHS_data"]) != 0 :
        filenames["LHS_data"] = params_l['LHS_data']
    else:
        filenames["LHS_data"] = params_l['data_rep']+params_l['data_l']+params_l['ext_l']
    if len(params_l["RHS_data"]) != 0 :
        filenames["RHS_data"] = params_l['RHS_data']
    else:
        filenames["RHS_data"] = params_l['data_rep']+params_l['data_r']+params_l['ext_r']

    if os.path.splitext(filenames["LHS_data"])[1] != ".csv" or os.path.splitext(filenames["RHS_data"])[1] != ".csv":
        filenames["style_data"] = "multiple"
        filenames["add_info"] = []

    ### Make queries file names
    if len(params_l["queries_file"]) != 0 :
        filenames["queries"] = params_l["queries_file"]
    elif params_l['out_base'] != "-"  and len(params_l['out_base']) > 0 and len(params_l['ext_queries']) > 0:
        filenames["queries"] = params_l['result_rep']+params_l['out_base']+params_l['ext_queries']

    if filenames["queries"] != "-":
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
    if params_l["support_file"] == "+" and filenames["queries"] != "-" and len(params_l['ext_support']) > 0:
        filenames["support"] = basis+params_l['ext_support']
    elif len(params_l["support_file"]) > 0:
        filenames["support"] = params_l["support_file"]

    ### Make log file name
    if params_l['logfile'] == "+" and filenames["queries"] != "-" and len(params_l['ext_log']) > 0:
        filenames["logfile"] = basis+params_l['ext_log']
    elif len(params_l['logfile']) > 0:
        filenames["logfile"] = params_l['logfile']

    return filenames

def outputResults(filenames, results_batch, data=None, header=None, header_named=None, mode="w", data_recompute=None):
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
    names = None
    if data is not None and data.hasNames() and "queries_named" in filenames:
        names = data.getNames()
        filesfp["queries_named"] = open(filenames["queries_named"], mode)
        filesfp["queries_named"].write(header_named+"\n")

    #### TO DEBUG: output all shown in siren, i.e. no filtering
    ## for pos in range(len(results_batch["batch"])):

    for pos in results_batch["results"]:
        if data_recompute is not None:
            org = results_batch["batch"][pos]
            red = org.copy()
            red.recompute(data_recompute)
            acc_diff = (red.getAcc()-org.getAcc())/org.getAcc()
            miner.final["batch"][pos].write(filesfp["queries"], filesfp["support"], filesfp["queries_named"], names, "\t"+red.dispStats()+"\t%f" % acc_diff)
        else:
            results_batch["batch"][pos].write(filesfp["queries"], filesfp["support"], filesfp["queries_named"], names)

    for ffp in filesfp.values():
        if ffp is not None:
            ffp.close()

def loadPackage(filename, pm):

    package = Package(filename)
    elements_read = package.read(pm)        

    if elements_read.get("data") is not None:
        data = elements_read.get("data")
    else:
        data = None
    if elements_read.get("preferences"):
        params = elements_read.get("preferences")
    else:
        params = None

    return params, data


# def run_filter(params, data, logger):
#     # ta = do_filter(params)    
#     miner = Miner(data, params, logger)

#     tf = miner.filter_run(ta)
#     for ti, t in enumerate(tf):
#         print t.disp()

# def do_filter(params):

#     params_l = trunToDict(params)
#     filenames = prepareFilenames(params_l)

#     logger = Log(params_l['verbosity'], filenames["logfile"])
#     data = Data([filenames["LHS_data"], filenames["RHS_data"]]+filenames["add_info"], filenames["style_data"])
#     logger.printL(2, data, "log")

#     ta = parseRedList(open(filenames["queries"], "r"), data)
#     for ti, t in enumerate(ta):
#         print t.disp(names)
        


def run(args):
    
    params, data, logger, filenames = loadAll(args)

    ############################
    #### SPLITS
    # data.extractFolds(1, 12)
    # splits_info = data.getFoldsInfo()
    # stored_splits_ids = sorted(splits_info["split_ids"].keys(), key=lambda x: splits_info["split_ids"][x])
    # ids = {}
    # checked = [("learn", range(1,len(stored_splits_ids))), ("test", [0])]
    # for lt, bids in checked:
    #     ids[lt] = [stored_splits_ids[bid] for bid in bids]
    # data.assignLT(ids["learn"], ids["test"])
    ############################

    miner = instMiner(data, params, logger)
    try:
        miner.full_run()
    except KeyboardInterrupt:
        logger.printL(1, 'Stopped...', "log")

    outputResults(filenames, miner.final, data)
    logger.clockTac(0, None)

def run_splits(args):

    params, data, logger, filenames = loadAll(args)    
    #### TODO generic
    data.extractFolds(1, 12)
    stM = StatsMiner(data, params, logger)
    reds_list, all_stats, header = stM.run_stats()

    nbreds = numpy.array([len(ll) for (li, ll) in all_stats.items() if li > -1])
    tot = numpy.array(all_stats[-1])
    summary_mat = numpy.hstack([numpy.vstack([tot.min(axis=0), tot.max(axis=0), tot.mean(axis=0), tot.std(axis=0)]), numpy.array([[nbreds.min()], [nbreds.max()], [nbreds.mean()], [nbreds.std()]])])

    info_plus = "\nrows:min\tmax\tmean\tstd\tnb_folds:%d" % (len(all_stats)-1)
    numpy.savetxt("tmp_stats.txt", summary_mat, fmt="%f", delimiter="\t", header="\t".join(header+["nb reds"])+info_plus)
    # print header
    # print summary_mat
    for red in reds_list:
        print red

##### MAIN
###########
    
if __name__ == "__main__":
        
    if sys.argv[-1] == "splits":
        run_splits(sys.argv[:-1])
    else:
        run(sys.argv)
