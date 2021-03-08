#!/usr/bin/python

import os.path
import sys
import re
import datetime
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


def get_reds_etc(loaded, suff="", alt_suff="_alt"):
    filenames = loaded["filenames"]
    if len(loaded.get("leftover_args", [])) == 1:
        # if there is one left-over arguments, assume it's a filename for queries
        qfilename = loaded["leftover_args"][0]
    elif "queries" in filenames:
        qfilename = filenames["queries"]
    else:
        qfilename = None
    q_found = False
    reds = []
    srcs_reds = []
    if loaded["reds"] is not None:
        i = 0
        while i < len(loaded["reds"]):
            if qfilename is not None and loaded["reds"][i]["src"][1] == qfilename:
                q_found = True
                reds = loaded["reds"][i]["items"]
                srcs_reds = [(i, qfilename)]
                i = len(loaded["reds"])
            else:
                reds.extend(loaded["reds"][i]["items"])
                srcs_reds.append((i, loaded["reds"][i]["src"][1]))
            i += 1

    if (qfilename is not None) and os.path.exists(qfilename) and not q_found:
        # the file exists and redescriptions have not yet been loaded from it
        q_found = True
        rp = Redescription.getRP()
        try:
            with open(qfilename) as fd:
                reds, _ = rp.parseRedList(fd, loaded["data"])
        except IOError:
            reds = []
            srcs_reds = []
        else:
            srcs_reds = [(None, qfilename)]

    # done loading reds, now figure target
    if qfilename is not None:
        if not q_found:  # not used
            trg_reds = qfilename
        elif len(suff) == 0 and filenames.get("queries", qfilename) != qfilename:
            # different, unused specified query file
            trg_reds = filenames["queries"]
        else:  # makeup name
            if len(suff) == 0:
                suff = alt_suff
            parts = qfilename.split(".")
            if len(parts) > 1:
                if "." in suff:
                    trg_reds = ".".join(parts[:-2] + [parts[-2] + suff])
                else:
                    trg_reds = ".".join(parts[:-2] + [parts[-2] + suff, parts[-1]])
            else:
                trg_reds = qfilename + suff
    else:  # no base name, last resort
        trg_reds = suff if len(suff) > 0 else alt_suff
    return reds, srcs_reds, trg_reds


def run(kw, loaded):
    params, data, logger, filenames = (loaded["params"], loaded["data"], loaded["logger"], loaded["filenames"])
    miner = instMiner(data, params, logger, filenames=filenames)
    try:
        miner.full_run()
    except KeyboardInterrupt:
        # miner.initial_pairs.saveToFile()
        logger.printL(1, 'Stopped...', "log")

    IOTools.outputResults(filenames, miner.rcollect.getItems("F"), data)
    logger.clockTac(0, None)


def run_filter(kw, loaded, suff=""):  # TODO
    params, data, logger, filenames = (loaded["params"], loaded["data"], loaded["logger"], loaded["filenames"])
    reds, srcs_reds, trg_reds = get_reds_etc(loaded, suff=suff, alt_suff="_filtered")
    bc = BatchCollection(reds)
    constraints = Constraints(params, data, filenames=filenames)
    ids = bc.selected(constraints.getActionsList("final"))
    IOTools.writeRedescriptionsFmt(bc.getItems(ids), trg_reds, data)


def run_printout(kw, loaded, suff=""):
    params, data, logger, filenames = (loaded["params"], loaded["data"], loaded["logger"], loaded["filenames"])
    reds, srcs_reds, trg_reds = get_reds_etc(loaded, suff=suff, alt_suff="_reprint")
    # IOTools.saveAsPackage("/home/egalbrun/Desktop/Z.siren", data, preferences=params, pm=loaded["pm"])
    # data.saveExtensions(details={"dir": "/home/egalbrun/Desktop/"})
    IOTools.writeRedescriptionsFmt(reds, trg_reds, data)


def run_expand(kw, loaded, suff=""):
    params, data, logger, filenames = (loaded["params"], loaded["data"], loaded["logger"], loaded["filenames"])
    reds, srcs_reds, trg_reds = get_reds_etc(loaded, suff=suff, alt_suff="_expanded")
    filenames["queries"] = trg_reds

    miner = instMiner(data, params, logger, filenames=filenames)
    collect_reds = []
    try:
        rcollect = miner.part_run({"reds": reds, "task": kw})  # , "side": 1})
        collect_reds.extend(rcollect.getItems("P"))
    except KeyboardInterrupt:
        # miner.initial_pairs.saveToFile()
        logger.printL(1, 'Stopped...', "log")
    IOTools.writeRedescriptionsFmt(collect_reds, trg_reds, data)
    logger.clockTac(0, None)


def run_folds(kw, loaded, flds=""):
    params, data, logger, filenames = (loaded["params"], loaded["data"], loaded["logger"], loaded["filenames"])

    nb_folds = 5
    tmp = re.match("(?P<nbs>[0-9]+)\s*", flds)
    if tmp is not None:
        nb_folds = int(tmp.group("nbs"))

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
            flds_pckgf = filenames["basis"] + ("_fold-%d:%s_empty.siren" % (nb_folds, "rnd"))
            IOTools.saveAsPackage(flds_pckgf, data, preferences=params, pm=loaded["pm"])
        else:
            logger.printL(2, "Using existing fold: side %s col %s" % fci, "log")
            sss = data.extractFolds(fci[0], fci[1])
            nb_folds = len(sss)
            suff = data.col(fci[0], fci[1]).getName()
        print("SIDS", suff, sorted(data.getFoldsInfo()["fold_ids"].items(), key=lambda x: x[1]))
        print(data)
        flds_pckgf = filenames["basis"] + ("_fold-%d:%s.siren" % (nb_folds, suff))
        flds_statf = filenames["basis"] + ("_fold-%d:%s.txt" % (nb_folds, suff))

        stM = StatsMiner(data, params, logger)
        reds_list, all_stats, summaries, list_fields, stats_fields = stM.run_stats()

        rp = Redescription.getRP()
        flds_fk = filenames["basis"] + ("_fold-%d:%s-kall.txt" % (nb_folds, suff))
        with open(flds_fk, "w") as f:
            f.write(rp.printRedList(reds_list, fields=list_fields+["track"]))

        for fk, dt in summaries.items():
            flds_fk = filenames["basis"] + ("_fold-%d:%s-k%d.txt" % (nb_folds, suff, fk))
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


def run_rnd(kw, loaded):
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
    with_traits = False
    if "traits_data" in filenames:
        traits_data = Data([filenames["traits_data"], None]+filenames["add_info"], filenames["style_data"])
        rf.setTraits(traits_data)
        with_traits = True

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

            miner = instMiner(Dsub, params, logger, filenames=sub_filenames)
            try:
                miner.full_run()
            except KeyboardInterrupt:
                # miner.initial_pairs.saveToFile()
                logger.printL(1, 'Stopped...', "log")
                stop = True

            IOTools.outputResults(sub_filenames, miner.final, Dsub)
            logger.clockTac(0, None)
            if stop:
                exit()


############################################
TASKS = [{"kw": "mine", "load_extra": {"log": False}},  # first is the default one
         {"kw": "filter", "patt": ".*", "load_extra": {"with_log": False}},
         {"kw": "printout", "patt": ".*", "load_extra": {"conf_defs": [0, "dataext"], "with_log": False}},
         {"kw": "improve", "patt": ".*"},
         {"kw": "expand", "patt": ".*"},
         {"kw": "folds", "patt": "([0-9]+\s*)?$"},
         {"kw": "rnd", "load_extra": {"conf_defs": [0, "dataext", "rnd"]}}]
DEF_TASK = TASKS[0]
METHS = {"mine": run, "filter": run_filter, "printout": run_printout,
         "expand": run_expand, "improve": run_expand, "folds": run_folds, "rnd": run_rnd}
# determine which task to run, load data etc. if not provided, and run


def do_task(sargs, meths=METHS, tasks=TASKS, def_task=DEF_TASK):
    task = None
    ti = 0
    while ti < len(tasks) and task is None:
        if re.match(tasks[ti]["kw"]+tasks[ti].get("patt", "$"), sys.argv[-1]):
            task = tasks[ti]
        ti += 1
    if task is None and def_task is not None:
        task = def_task
        sargs.append(task["kw"])  # compensate absence of patt keyword

    if task is not None:
        if len(task.get("patt", "")) > 0:
            # strip keyword from last argument
            task_args = [sargs[-1][len(task["kw"]):]]
        else:
            task_args = []
        load_args = sargs[:-1]

        if task.get("load_extra", {}) != False:
            success, loaded = IOTools.loadAll(load_args, **task.get("load_extra", {}))
            if not success:
                print(loaded)  # print help message
                sys.exit(2)
            if "filenames" in loaded:
                print(loaded["filenames"])
        else:
            loaded = load_args

        print("Running %s" % " ".join([task["kw"]]+task_args))
        meths[task["kw"]](task["kw"], loaded, *task_args)


def main():
    do_task(sys.argv)


if __name__ == "__main__":
    main()
