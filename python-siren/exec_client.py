#!/usr/bin/env python
import sys
import os.path
import time
import re

from blocks.mine.classPackage import IOTools
from blocks.mine.classProps import findFile
from blocks.mine.exec_clired import TASKS_METH, TASKS_DEFAULT, TASKS_LOAD, CONF_DEFS, CONF_FILTER, do_task
from blocks.work.classWorkInactive import CLIBoss
from blocks.work.classWorkLocal import WorkLocal
from blocks.work.classWorkClient import WorkClient

import pdb

# dynamic methods definition
# CMETHS = {}
# for kw in ["ping", "reconnect", "mine", "expand"]:
#     meth_tmpl = f"""
# def client_{kw}(loaded, *args):
#     client_forward("{kw}", loaded, *args)
#     # print("Client {kw}")
# CMETHS["{kw}"] = client_{kw}"""
#     exec(meth_tmpl)


def client_forward(task, loaded):
    params = loaded["params"]
    ip = params["workserver_ip"]
    client_id = params["workserver_clientid"]
    if ip is not None and not re.match("[lL]ocal$", ip):
        wp = WorkClient(ip, params["workserver_port"], params["workserver_authkey"])
        # wp = WorkLocal()

        status, info, client_ids = wp.getDetailedInfos()
        cl_ids = ("\tclient ids: " + ", ".join(["%s" % c for c in client_ids])) if len(client_ids) > 0 else ""
        print("Server %s\t%s%s" % (status, info.strip(), cl_ids))

        # nothing more to do for ping...
        if task == "ping":
            sys.exit(0)
        if status == "KO":
            print("No server, stopping...")
            sys.exit(2)
        if task == "reconnect" and client_id not in client_ids:
            print("Nothing to reconnect to...")
            sys.exit(0)

        data, logger, filenames = (loaded["data"], loaded["logger"], loaded["filenames"])
        trg_reds = filenames["queries"]
        boss = CLIBoss(wp, data, params, logger, params["results_delay"])
        # if results delay is not strictly postive, this means simply issue the command and exit, wil come back to collect results later on
        collectLater = (params["results_delay"] <= 0) and wp.isDistributed()
        out_lid = "F"

        if task == "reconnect":
            wp.resetClientId(client_id)
            wp.reconnection(boss)
        else:
            task_params = {"task": "mine"}
            if task != "mine":
                out_lid = "P"
                reds, srcs_reds, all_queries_src, trg_reds = IOTools.getRedsEtc(loaded, alt_suff="_X")
                if task == "expand":
                    task_params = {"task": "expand", "reds": reds}
                elif task == "improve":
                    task_params = {"task": "improve", "reds": reds}
            wp.addWorker(boss, task_params)
        try:
            if not collectLater:
                boss.checkResults()  # countdown=5)
        except KeyboardInterrupt:
            if wp.isDistributed():
                msg = WorkClient.questionReturnLater(wp.getHid())
                x = input(msg+"\n\ty(es)/n(o)\n")
                collectLater = (x.strip() == "y")
            logger.printL(1, "Stopped...", "log")

        wp.closeDown(boss, collectLater=collectLater)
        if boss.getNbchecks() > 0:
            IOTools.writeRedescriptionsFmt(boss.getReds(out_lid), trg_reds, data)
            logger.clockTac(0, None)

    else:
        # no server specified, falling back on standard clired, or ending
        if task in TASKS_METH:
            TASKS_METH[task](task, loaded)


CTASKS_METH = {"mine": client_forward, "expand": client_forward, "improve": client_forward,
               "ping": client_forward, "reconnect": client_forward}
CTASKS_DEFAULT = "ping"
CTASKS_LOAD = {"ping": {"params_only": True}}


def run_client(sargs):

    srcdir = os.path.dirname(os.path.abspath(__file__))
    work_conf_defs = list(CONF_DEFS)
    work_conf_filter = list(CONF_FILTER)
    for cdef in ["network_confdef.xml"]:
        fn = findFile(cdef, [srcdir+"/blocks/work"])
        if fn is not None:
            work_conf_defs.append(fn)
            work_conf_filter.append(fn)

    ctasks_meth = dict(TASKS_METH)
    ctasks_meth.update(CTASKS_METH)

    ctasks_load = dict(TASKS_LOAD)
    ctasks_load.update(CTASKS_LOAD)

    do_task(sargs, conf_defs=work_conf_defs, tasks_meths=ctasks_meth, tasks_default=CTASKS_DEFAULT, tasks_load=ctasks_load, conf_filter=work_conf_filter)


if __name__ == '__main__':
    run_client(sys.argv)
