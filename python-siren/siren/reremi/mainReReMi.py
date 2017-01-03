#!/usr/bin/python

import sys, re, os.path, datetime
import numpy
import tempfile
from toolLog import Log
from classPackage import Package, saveAsPackage
from classData import Data
from classRedescription import Redescription, parseRedList, printRedList
from classBatch import Batch
from classConstraints import Constraints
from classPreferencesManager import PreferencesReader, getPM
from classMiner import instMiner, StatsMiner
from classQuery import Query
import pdb

## from codeRRM import RedModel

def loadAll(arguments=[]):
    pm = getPM()

    pack_filename = None
    config_filename = None
    tmp_dir = None
    params = None
    reds = None
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
        reds = elements_read.get("reds", None)
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
    return {"params": params, "data": data, "logger": logger,
            "filenames": filenames, "reds": reds, "pm": pm}

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
    filenames["basis"] = basis

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

    for (ffi, ffp) in filesfp.items():
        if ffp is not None and filenames.get(ffi, "") != "-":
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

def run(args):
    
    loaded = loadAll(args)
    params, data, logger, filenames = (loaded["params"], loaded["data"], loaded["logger"], loaded["filenames"]) 

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

###############################
 # def run_filterRM(args):
    
 #    loaded = loadAll(args)
 #    params, data, logger, filenames, reds = (loaded["params"], loaded["data"], loaded["logger"],
 #                                             loaded["filenames"], loaded["reds"]) 

 #    constraints = Constraints(data, params)

 #    candidate_ids = range(len(reds))
 #    scores = numpy.zeros((len(reds)+2, len(reds)))
 #    keep_ids = []
 #    rm = RedModel(data)
 #    best = (0, -1)
 #    while best[-1] is not None:
 #        best = (0, None)
 #        tic = datetime.datetime.now()
 #        for rr, ri in enumerate(candidate_ids):
 #            top = rm.getTopDeltaRed(reds[ri], data)
 #            scores[ri, len(keep_ids)] = top[0]
 #            if top[0] < best[0]:
 #                best = (top[0], top[1], rr)
 #                # print top, reds[ri].disp()

 #        if best[-1] is not None:
 #            ri = candidate_ids.pop(best[-1])
 #            scores[-2, len(keep_ids)] = (datetime.datetime.now()-tic).total_seconds()
 #            scores[-1, len(keep_ids)] = ri
 #            keep_ids.append(ri)
 #            rm.addRed(reds[ri], data, best[1])
 #            print "%f\t%d\t%s" % (best[0], ri, reds[ri].disp())

 #    numpy.savetxt('scores.txt', scores, fmt="%f")
###############################

def run_filter(args):
    #### USED FOR TESTS
    #### on 100
    # [84, 1, 43, 85, 6, 5, 7, 66, 11, 44, 90, 14, 31, 86, 75, 39, 58, 52, 55, 33, 89, 93, 18, 77, 53, 91, 34, 68, 65, 92, 76, 74, 80, 20, 56, 22, 78, 82, 25]
    # [(8, False), (0, False), (2, False), (9, False), (27, False), (42, False), (61, False), (84, True), (19, False), (17, False), (3, False), (10, False), (4, False), (1, True), (62, False), (46, False), (28, False), (32, False), (43, True), (63, False), (13, False), (85, True), (6, True), (5, True), (7, True), (66, True), (11, True), (29, False), (15, False), (44, True), (90, True), (70, False), (87, False), (12, False), (14, True), (16, False), (23, False), (31, True), (38, False), (36, False), (37, False), (86, True), (88, False), (73, False), (83, False), (51, False), (75, True), (39, True), (57, False), (58, True), (97, False), (67, False), (52, True), (30, False), (95, False), (47, False), (55, True), (50, False), (35, False), (33, True), (89, True), (69, False), (45, False), (93, True), (18, True), (54, False), (77, True), (53, True), (91, True), (34, True), (64, False), (68, True), (96, False), (65, True), (98, False), (92, True), (48, False), (49, False), (26, False), (40, False), (76, True), (74, True), (72, False), (94, False), (71, False), (99, False), (80, True), (21, False), (20, True), (56, True), (22, True), (81, False), (78, True), (79, False), (82, True), (59, False), (41, False), (60, False), (25, True), (24, False)]
## [0, 2, 9, 27, 42, 61, 19, 17, 3, 10, 4, 62, 46, 28, 32, 63, 13, 29, 15, 70, 87, 12, 16, 23, 38, 36, 37, 88, 73, 83, 51, 57, 97, 67, 30, 95, 47, 50, 35, 69, 45, 54, 64, 96, 98, 48, 49, 26, 40, 72, 94, 71, 99, 21, 81, 79, 59, 41, 60, 24, 8]

    loaded = loadAll(args)
    params, data, logger, filenames, reds = (loaded["params"], loaded["data"], loaded["logger"],
                                             loaded["filenames"], loaded["reds"]) 

    constraints = Constraints(data, params)
    reds = []
    with open("/home/galbrun/current/redescriptions.csv") as fd:
        parseRedList(fd, data, reds)

    # bbatch = Batch(reds)
    # # org_ids = bbatch.selected(constraints.getActions("final"))
    # # pdb.set_trace()
    
    # cc = constraints.getActions("final")
    # ttt = [0, 2, 9, 27, 42, 61, 84, 19, 17, 3, 10, 4, 1, 62, 46, 28, 32, 43, 63, 13, 85, 6, 5, 7, 66, 11, 29, 15, 44, 90, 70, 87, 12, 14, 16, 23, 31, 38, 36, 37, 86, 88, 73, 83, 51, 75, 39, 57, 58, 97, 67, 52, 30, 95, 47, 55, 50, 35, 33, 89, 69, 45, 93, 18, 54, 77, 53, 91, 34, 64, 68, 96, 65, 98, 92, 48, 49, 26, 40, 76, 74, 72, 94, 71, 99, 80, 21, 20, 56, 22, 81, 78, 79, 82, 59, 41, 60, 25, 24, 8]
    # for i in range(len(ttt)):
    #     for j in range(i):
    #         if bbatch.filterLast([ttt[j],ttt[i]], cc[-1][1]):
    #             print j, i, ttt[j], ttt[i]
    # pdb.set_trace()

    rr_tests = [[1, 32, 6, 5, 29, 94], [23, 12], [7, 66, 11, 29]]
    rr_tests = [[73]] ## [2]
    for ri, add_redids in enumerate(rr_tests):

        include_redids = [84, 77, 53, 29, 94]

        bbatch = Batch([reds[i] for i in include_redids]+[reds[i] for i in add_redids])
        org_ids = bbatch.selected(constraints.getActions("final"))
        
        batch = Batch([reds[i] for i in include_redids])
        pids = batch.selected(constraints.getActions("final"))
        batch.extend([reds[i] for i in add_redids])
        # tmp_ids = batch.selected(self.constraints.getActions("redundant"))
        ticc = datetime.datetime.now()
        new_ids = range(len(include_redids), len(include_redids)+len(add_redids))
        tmp_ids = batch.selected(constraints.getActions("final"), ids= pids+new_ids, new_ids=new_ids)
        tacc = datetime.datetime.now()
        print "Elapsed ", ri, tacc-ticc
        if tmp_ids != org_ids:
            print "Not identical"
        pdb.set_trace()
        print len(tmp_ids), len(org_ids)
        
    return [batch[i] for i in tmp_ids]


    ## miner = instMiner(data, params, logger)
    ## try:
    ##     miner.full_run()
    ## except KeyboardInterrupt:
    ##     logger.printL(1, 'Stopped...', "log")
    ## 
    ## outputResults(filenames, miner.final, data)
    ## logger.clockTac(0, None)


def run_splits(args, splt=""):

    nb_splits = 5
    tmp = re.match("splits(?P<nbs>[0-9]+)\s*", splt)
    if tmp is not None:
        nb_splits = int(tmp.group("nbs"))
        
    loaded = loadAll(args)
    params, data, logger, filenames = (loaded["params"], loaded["data"], loaded["logger"], loaded["filenames"]) 
    if "package" in filenames:
        parts = filenames["package"].split("/")[-1].split(".")
        pp = filenames["basis"].split("/")
        pp[-1] = ".".join(parts[:-1])
        filenames["basis"] = "/".join(pp)
    splt_pckgf = filenames["basis"]+ ("_split-%d.siren" % nb_splits)
    splt_statf = filenames["basis"]+ ("_split-%d.txt" % nb_splits)
    fold_cols = data.findCandsFolds()

    if len(fold_cols) == 0:
        logger.printL(2, "Data has no folds, generating...", "log")
        sss = data.getSplit(nbsubs=nb_splits)
        data.addFoldsCol()        
        saveAsPackage(splt_pckgf, data, preferences=params, pm=loaded["pm"])        
    else:
        logger.printL(2, "Using existing fold: side %s col %s" % fold_cols[0], "log")
        sss = data.extractFolds(fold_cols[0][0], fold_cols[0][1])
    stM = StatsMiner(data, params, logger)
    reds_list, all_stats, header = stM.run_stats()

    nbreds = numpy.array([len(ll) for (li, ll) in all_stats.items() if li > -1])
    tot = numpy.array(all_stats[-1])
    summary_mat = numpy.hstack([numpy.vstack([tot.min(axis=0), tot.max(axis=0), tot.mean(axis=0), tot.std(axis=0)]), numpy.array([[nbreds.min()], [nbreds.max()], [nbreds.mean()], [nbreds.std()]])])

    info_plus = "\nrows:min\tmax\tmean\tstd\tnb_folds:%d" % (len(all_stats)-1)
    numpy.savetxt(splt_statf, summary_mat, fmt="%f", delimiter="\t", header="\t".join(header+["nb reds"])+info_plus)
    saveAsPackage(splt_pckgf, data, preferences=params, pm=loaded["pm"], reds=reds_list)        

    for red in reds_list:
        print red.disp()

##### MAIN
###########
    
if __name__ == "__main__":
    
    if re.match("splits", sys.argv[-1]):
        run_splits(sys.argv[:-1], sys.argv[-1])
    elif sys.argv[-1] == "filter":
        run_filter(sys.argv[:-1])
    elif sys.argv[-1] == "filterRM":
        run_filterRM(sys.argv[:-1])
    else:
        run(sys.argv)


    # pm = getPM()
    # package = Package(sys.argv[-1])
    # elements_read = package.read(pm)        

    # if elements_read.get("reds") is not None:
    #     reds = elements_read.get("reds")
    #     data = elements_read.get("data")
    #     with open("test.txt", "w") as fp:
    #         fp.write(printRedList(reds, [None, None], None, full_supp=True))
    #     rrr = []
    #     with open("test.txt") as fp:
    #         parseRedList(fp, data, rrr)
    #     print [r.disp() for r in rrr]

