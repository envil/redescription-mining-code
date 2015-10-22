#!/usr/bin/env python
import getopt, sys

from siren.work.classWorkServer import WorkServer

if __name__ == '__main__':
    args = {}
    if len(sys.argv) > 1:
        args = dict([(k.strip("-"), v) for (k,v) in getopt.getopt(sys.argv[1:], "", ["portnum=", "authkey=", "max_k=", "chroot=","setuid="])[0]])
    for k in ["portnum", "max_k", "setuid"]:
        if k in args:
            try:
                args[k] = int(args[k])
            except ValueError:
                del args[k]
    if "setuid" in args:
        os.setuid(args.pop("setuid"))
    if "chroot" in args:
        os.chroot(args.pop("chroot"))
    WorkServer(**args)
