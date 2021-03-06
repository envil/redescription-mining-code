#!/usr/bin/python

import sys, re, datetime, os, os.path, random, itertools
from siren.clired.toolLog import Log
from siren.clired.classData import Data
from siren.clired.classMiner import Miner
from siren.clired.classRedescription import Redescription
import siren.clired.mainclired as clired
import pdb
 
def run(arguments):
    multiprocessus = True
    nb_parts = 10

    params = clired.getParams(arguments)

    params_l = {}
    for k, v in  params.items():
        params_l[k] = v["data"]

    ### construct filenames
    fn_l = params_l['data_rep']+params_l['data_l']+params_l['ext_l']
    fn_r = params_l['data_rep']+params_l['data_r']+params_l['ext_r']
                
    dataAll = Data([fn_l, fn_r])

    ### partition data
    rows = range(dataAll.nbRows())
    random.shuffle(rows)
    step = len(rows)/nb_parts
    parts = []
    for i in range(0, len(rows)-step, step):
        parts.append(rows[i:i+step])
    parts.append(rows[i+step:])

    parts_ids = range(len(parts))
    datasets = []
    for i in range(nb_parts):
        out_ids = parts[i]
        in_ids = [i for i in itertools.chain(*[p for j, p in enumerate(parts) if j != i])]
        print len(out_ids), len(in_ids)
        datasets.append({"in_ids": in_ids,
               "out_ids": out_ids,
               "in": dataAll.subset(in_ids),
               "out": dataAll.subset(out_ids)
               })

    for di, dataset in enumerate(datasets):
        pid = False
        if multiprocessus:
            pid = os.fork()
            
        if pid:
            print "Parent ", di
        else:
            print "START child ", di
            logger = Log(params_l['verbosity'], params_l['result_rep']+params_l['out_base']+("_%d" % di)+".log")
            ticO = datetime.datetime.now()
            data = dataset["in"]
            logger.printL(2, data, "log")
            miner = Miner(data, params, logger)

            try:
                miner.full_run()
            except KeyboardInterrupt:
                logger.printL(1, 'Stopped...', "log")

            queriesInFp = open(params_l['result_rep']+params_l['out_base']+("_%dIN" % di)+params_l['ext_queries'], "w")
            supportInFp = None
            if len(params_l['ext_support']) > 0:
                supportInFp = open(params_l['result_rep']+params_l['out_base']+("_%dIN" % di)+params_l['ext_support'], "w")

            queriesOutFp = open(params_l['result_rep']+params_l['out_base']+("_%dOUT" % di)+params_l['ext_queries'], "w")
            supportOutFp = None
            if len(params_l['ext_support']) > 0:
                supportOutFp = open(params_l['result_rep']+params_l['out_base']+("_%dOUT" % di)+params_l['ext_support'], "w")

            resultsFp = open(params_l['result_rep']+params_l['out_base']+("_%d" % di)+".statistics", "w")

            coverage = [0 for n in range(dataAll.nbRows())]
            for pos in miner.final["results"]:
                in_red = miner.final["batch"][pos] 
                in_red.write(queriesInFp, supportInFp)
                
                out_red = Redescription.fromQueriesPair(in_red.queries, dataset["out"])
                out_red.write(queriesOutFp, supportOutFp)
                
                resultsFp.write(" ".join(map(str, in_red.supports().lparts()))+"\t"+
                                " ".join(map(str, out_red.supports().lparts()))+"\n")

                for row in in_red.suppI():
                    coverage[dataset["in_ids"][row]] += 1

                for row in out_red.suppI():
                    coverage[dataset["out_ids"][row]] += 1

            resultsFp.close()
            queriesInFp.close()
            if supportInFp is not None:
                supportInFp.close()
            queriesOutFp.close()
            if supportOutFp is not None:
                supportOutFp.close()
            
            coverFp = open(params_l['result_rep']+params_l['out_base']+("_%d" % di)+".cover", "w")
            coverFp.write("\n".join(["0 %d %d %d" % (sr, ar, coverage[ar]) for (sr, ar) in enumerate(dataset["in_ids"])]))
            coverFp.write("\n"+"\n".join(["1 %d %d %d" % (sr, ar, coverage[ar]) for (sr, ar) in enumerate(dataset["out_ids"])]))
            coverFp.close()

            tacO = datetime.datetime.now()

            logger.printL(1, 'THE END (at %s, elapsed %s)' % (tacO, tacO - ticO), "log")
            print "END child ", di
            exit()

if __name__ == "__main__":
    run(sys.argv)
