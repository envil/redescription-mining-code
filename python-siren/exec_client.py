#!/usr/bin/env python
import sys
import os.path
import time
import re

from blocks.mine.classPackage import IOTools
from blocks.mine.classContent import BatchCollection
from blocks.mine.classConstraints import Constraints
from blocks.mine.classProps import findFile
from blocks.mine.exec_clired import TASKS, METHS, do_task, get_reds_etc
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


def client_forward(kw, loaded, *task_args):
    params = loaded["params"]
    ip = params["workserver_ip"]["data"]
    client_id = params["workserver_clientid"]["data"]
    suff = task_args[0] if len(task_args) > 0 else ""
    if ip is not None and not re.match("[lL]ocal$", ip):
        wp = WorkClient(ip, params["workserver_port"]["data"], params["workserver_authkey"]["data"])
        # wp = WorkLocal()

        status, info, client_ids = wp.getDetailedInfos()
        cl_ids = ("\tclient ids: " + ", ".join(["%s" % c for c in client_ids])) if len(client_ids) > 0 else ""
        print("Server %s\t%s%s" % (status, info.strip(), cl_ids))

        # nothing more to do for ping...
        if kw == "ping":
            sys.exit(0)
        if status == "KO":
            print("No server, stopping...")
            sys.exit(2)
        if kw == "reconnect" and client_id not in client_ids:
            print("Nothing to reconnect to...")
            sys.exit(0)

        data, logger, filenames = (loaded["data"], loaded["logger"], loaded["filenames"])
        trg_reds = filenames["queries"]
        bc = BatchCollection()
        boss = CLIBoss(wp, data, params, logger, bc, params["results_delay"]["data"])
        # if results delay is not strictly postive, this means simply issue the command and exit, wil come back to collect results later on
        collectLater = (params["results_delay"]["data"] <= 0) and wp.isDistributed()

        if kw == "reconnect":
            wp.resetClientId(client_id)
            wp.reconnection(boss)
        else:
            task_params = {"task": "mine"}
            if kw != "mine":
                reds, srcs_reds, trg_reds = get_reds_etc(loaded, suff=suff, alt_suff="_X")
                if kw == "expand":
                    task_params = {"task": "expand", "reds": reds}
                elif kw == "improve":
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
        constraints = Constraints(params, data, filenames=filenames)
        ids = boss.getRedsBC().selected(constraints.getActionsList("final"))
        IOTools.writeRedescriptionsFmt(boss.getRedsBC().getItems(ids), trg_reds, data)
        # IOTools.writeRedescriptionsFmt(boss.getReds(), trg_reds, data)
        logger.clockTac(0, None)

    else:
        # no server specified, falling back on standard clired, or ending
        if kw in METHS:
            METHS[kw](kw, loaded, *task_args)


CMETHS = {"mine": client_forward, "expand": client_forward, "improve": client_forward,
          "ping": client_forward, "reconnect": client_forward}


def do_client(sargs):

    srcdir = os.path.dirname(os.path.abspath(__file__))
    work_conf_defs = []
    for cdef in ["network_confdef.xml"]:
        fn = findFile(cdef, [srcdir+"/blocks/work"])
        if fn is not None:
            work_conf_defs.append(fn)

    client_meths = dict(CMETHS)

    def_task = {"kw": "ping", "load_extra": {"conf_defs": list(work_conf_defs), "params_only": True}}  # False}
    client_tasks = [def_task,
                    {"kw": "reconnect", "load_extra": {"conf_defs": [0]+work_conf_defs}}]
    for task in TASKS:
        ntask = dict(task)
        if ntask["kw"] not in client_meths:  # shortcut tasks that should be sent to server
            client_meths[ntask["kw"]] = METHS[ntask["kw"]]
        if "load_extra" in ntask:
            if ntask["load_extra"] != False:
                ntask["load_extra"]["conf_defs"] = ntask["load_extra"].get("conf_defs", [0])+work_conf_defs
        else:
            ntask["load_extra"] = {"conf_defs": [0]+work_conf_defs}
        client_tasks.append(ntask)

    do_task(sargs, client_meths, client_tasks, def_task)


def main():
    do_client(sys.argv)


if __name__ == '__main__':
    main()
