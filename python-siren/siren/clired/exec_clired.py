#!/usr/bin/python

import sys, re, datetime
import numpy
import tempfile

try:
    from classData import Data
    from classQuery import Query
    from classRedescription import Redescription
    from classConstraints import Constraints
    from classPackage import Package, IOTools
    from classContent import BatchCollection
    from classMiner import instMiner, StatsMiner
    from classRndFactory import RndFactory
except ModuleNotFoundError:
    from .classData import Data
    from .classQuery import Query
    from .classRedescription import Redescription
    from .classConstraints import Constraints
    from .classPackage import Package, IOTools
    from .classContent import BatchCollection
    from .classMiner import instMiner, StatsMiner
    from .classRndFactory import RndFactory

import pdb



def run(args):

    loaded = IOTools.loadAll(args)
    params, data, logger, filenames = (loaded["params"], loaded["data"], loaded["logger"], loaded["filenames"])
    miner = instMiner(data, params, logger)
    try:
        miner.full_run()
    except KeyboardInterrupt:
        ## miner.initial_pairs.saveToFile()
        logger.printL(1, 'Stopped...', "log")

    IOTools.outputResults(filenames, miner.rcollect.getItems("F"), data)
    logger.clockTac(0, None)

def run_filter(args):

    loaded = IOTools.loadAll(args)
    params, data, logger, filenames, reds = (loaded["params"], loaded["data"], loaded["logger"], loaded["filenames"], loaded["reds"])
    constraints = Constraints(params, data)
    all_reds = []
    for r in reds:
        all_reds.extend(r["items"])
    bc = BatchCollection(all_reds)
    iids = bc.getIids()
    ids = bc.selected(constraints.getActionsList("final"), ids=iids[:10], new_ids=iids[:4])


def run_folds(args, flds=""):
    nb_folds = 5
    tmp = re.match("folds(?P<nbs>[0-9]+)\s*", flds)
    if tmp is not None:
        nb_folds = int(tmp.group("nbs"))
        
    loaded = IOTools.loadAll(args)
    params, data, logger, filenames = (loaded["params"], loaded["data"], loaded["logger"], loaded["filenames"]) 
    if "package" in filenames:
        parts = filenames["package"].split("/")[-1].split(".")
        pp = filenames["basis"].split("/")
        pp[-1] = ".".join(parts[:-1])
        filenames["basis"] = "/".join(pp)
    fold_cols = data.findCandsFolds(strict=True)

    if len(fold_cols) == 0:
        fold_cols = [None]
    else:
        for fci in fold_cols:
            data.col(fci[0], fci[1]).setDisabled()

    for fci in fold_cols:
        if fci is None:
            logger.printL(2, "Data has no folds, generating...", "log")
            sss = data.getFold(nbsubs=nb_folds)
            data.addFoldsCol()
            suff = "rand"
            flds_pckgf = filenames["basis"]+ ("_fold-%d:%s_empty.siren" % (nb_folds, suff))
            IOTools.saveAsPackage(flds_pckgf, data, preferences=params, pm=loaded["pm"])        
        else:
            logger.printL(2, "Using existing fold: side %s col %s" % fci, "log")
            sss = data.extractFolds(fci[0], fci[1])
            nb_folds = len(sss)
            suff = data.col(fci[0],fci[1]).getName()
        print("SIDS", suff, sorted(data.getFoldsInfo()["fold_ids"].items(), key=lambda x: x[1]))
        print(data)
        flds_pckgf = filenames["basis"]+ ("_fold-%d:%s.siren" % (nb_folds, suff))
        flds_statf = filenames["basis"]+ ("_fold-%d:%s.txt" % (nb_folds, suff))            

        stM = StatsMiner(data, params, logger)
        reds_list, all_stats, summaries, list_fields, stats_fields = stM.run_stats()
        
        rp = Redescription.getRP()
        flds_fk = filenames["basis"]+ ("_fold-%d:%s-kall.txt" % (nb_folds, suff))            
        with open(flds_fk, "w") as f:
            f.write(rp.printRedList(reds_list, fields=list_fields+["track"]))

        for fk, dt in summaries.items():
            flds_fk = filenames["basis"]+ ("_fold-%d:%s-k%d.txt" % (nb_folds, suff, fk))            
            with open(flds_fk, "w") as f:
                f.write(rp.printRedList(dt["reds"], fields=list_fields+["track"]))
                
        nbreds = numpy.array([len(ll) for (li, ll) in all_stats.items() if li > -1])
        tot = numpy.array(all_stats[-1])
        if nbreds.sum() > 0:
            summary_mat = numpy.hstack([numpy.vstack([tot.min(axis=0), tot.max(axis=0), tot.mean(axis=0), tot.std(axis=0)]), numpy.array([[nbreds.min()], [nbreds.max()], [nbreds.mean()], [nbreds.std()]])])

            info_plus = "\nrows:min\tmax\tmean\tstd\tnb_folds:%d" % (len(all_stats)-1)
            numpy.savetxt(flds_statf, summary_mat, fmt="%f", delimiter="\t", header="\t".join(stats_fields+["nb reds"])+info_plus)
            # IOTools.saveAsPackage(flds_pckgf, data, preferences=params, pm=loaded["pm"], reds=reds_list)
        else:
            with open(flds_statf, "w") as fo:
                fo.write("No redescriptions found")
        # for red in reds_list:
        #     print(red.disp())


def run_printout(args):
    suff = args[-1].strip("printout")
    if len(suff) == 0:
        suff = "_reprint"

    conf_defs = ["miner", "inout", "dataext"]
    loaded = IOTools.loadAll(args[:-1], conf_defs)
    params, data, logger, filenames, reds = (loaded["params"], loaded["data"], loaded["logger"],
                                             loaded["filenames"], loaded["reds"])

    rp = Redescription.getRP()
    qfilename = None
    if reds is None and "queries" in filenames:
        qfilename = filenames["queries"]        
    if "queries_second" in filenames:
        qfilename = filenames["queries_second"]

    if qfilename is not None:
        reds = []
        try:
            with open(qfilename) as fd:
                rp.parseRedList(fd, data, reds)
        except IOError:
            reds = []
    
    #### OUT
    parts = filenames["queries"].split(".")
    if len(parts) > 1:
        if "." in suff:
            filename = ".".join(parts[:-2] + [parts[-2]+ suff])
        else:
            filename = ".".join(parts[:-2] + [parts[-2]+ suff, parts[-1]])
    else:
        filename = filenames["queries"] + suff
    print("FILENAME", filename)
    if type(reds) is list and len(reds) > 0 and type(reds[0]) is dict and "items" in reds[0]:
        red_contents = []
        for r in reds:
            red_contents.extend(r["items"])
    else:
        red_contents = reds

    # IOTools.saveAsPackage("/home/egalbrun/Desktop/Z.siren", data, preferences=params, pm=loaded["pm"])        
    # data.saveExtensions(details={"dir": "/home/egalbrun/Desktop/"})
    params = IOTools.getPrintParams(filename, data)
    params["modifiers"] = rp.getModifiersForData(data)
    IOTools.writeRedescriptions(red_contents, filename, **params)
                

def run_rnd(args):

    conf_defs = ["miner", "inout", "dataext", "rnd"]
    loaded = IOTools.loadAll(args, conf_defs)
    params, data, logger, filenames = (loaded["params"], loaded["data"], loaded["logger"], loaded["filenames"])

    params_l = PreferencesReader.paramsToDict(params)
    select_red = None 
    if len(params_l.get("select_red", "")) > 0:
        select_red = params_l["select_red"]
    prec_all = None
    if params_l.get("agg_prec", -1) >= 0:
        prec_all = params_l["agg_prec"]
    count_vname = params_l.get("count_vname", "COUNTS")
            
    rf = RndFactory(org_data=data)    
    with_traits=False
    if "traits_data" in filenames:
        traits_data = Data([filenames["traits_data"], None]+filenames["add_info"], filenames["style_data"])
        rf.setTraits(traits_data)
        with_traits=True
        
    if params_l.get("rnd_seed", -1) >= 0:
        rf.setSeed(params_l["rnd_seed"])

    stop = False
    for rnd_meth in params_l["rnd_meth"]:
        nb_copies = params_l["rnd_series_size"]
        if rnd_meth == "none":
            nb_copies = 1
        
        for i in range(nb_copies):
            sub_filenames = dict(filenames)
            suff = "_%s-%d" % (rnd_meth, i)
            sub_filenames["basis"] += suff
            for k in ["queries", "queries_named", "support"]:
                if k in sub_filenames:
                    parts = sub_filenames[k].split(".")
                    parts[-2] += suff
                    sub_filenames[k] = ".".join(parts)

            Dsub, sids, back, store = rf.makeupRndData(rnd_meth=rnd_meth, with_traits=with_traits, count_vname=count_vname, select_red=select_red, prec_all=prec_all)
            logger.printL(2, "STARTING Random series %s %d" % (rnd_meth, i), "log")
            logger.printL(2, Dsub, "log")
                        
            miner = instMiner(Dsub, params, logger)
            try:
                miner.full_run()
            except KeyboardInterrupt:
                ## miner.initial_pairs.saveToFile()
                logger.printL(1, 'Stopped...', "log")
                stop = True
                
            IOTools.outputResults(sub_filenames, miner.final, Dsub)
            logger.clockTac(0, None)
            if stop:
                exit()

def run_extend(args, qfilename):
    loaded = IOTools.loadAll(args)
    params, data, logger, filenames = (loaded["params"], loaded["data"], loaded["logger"], loaded["filenames"])

    rp = Redescription.getRP()
    reds = []
    try:
        with open(qfilename) as fd:
            rp.parseRedList(fd, data, reds)
    except IOError:
        reds = []
        
    miner = instMiner(data, params, logger)
    collect_reds = []
    try:
        for red in reds:
            rcollect = miner.part_run({"red": red, "side": 1})
            collect_reds.extend(rcollect.getItems("P"))
    except KeyboardInterrupt:
        ## miner.initial_pairs.saveToFile()
        logger.printL(1, 'Stopped...', "log")
    IOTools.outputResults(filenames, collect_reds, data)
    logger.clockTac(0, None)

                
##### MAIN
###########
def main():

    if re.match("printout", sys.argv[-1]):
        run_printout(sys.argv)
    elif re.match("rnd", sys.argv[-1]):
        run_rnd(sys.argv[:-1])
    elif re.match("folds", sys.argv[-1]):
        run_folds(sys.argv[:-1], sys.argv[-1])
    elif sys.argv[-1] == "filter":
        run_filter(sys.argv[:-1])
    elif re.match("extend", sys.argv[-1]) and len(sys.argv) > 3:
        run_extend(sys.argv[:-2], sys.argv[-2])
    else:
        run(sys.argv)

if __name__ == "__main__":
    main()
