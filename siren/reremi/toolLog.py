import sys
import pdb
import random
import datetime
        
class Log:
    def __init__(self, verbosity=1, output = '-', method_comm = None):
        self.out = []
        self.oqu = []
        self.verbosity = -1
        self.addOut(verbosity, output, method_comm)
        self.tics = {None: datetime.datetime.now()}

    def getTic(self, id, name=None):
        if name is None:
            return self.tics[None]
        elif (id, name) in self.tics:
            return self.tics[(id, name)]
        else:
            return None
        
    def setTic(self, id, name):
        self.tics[(id, name)] = datetime.datetime.now()
        return self.tics[(id, name)]

    def setTac(self, id, name=None):
        if name is None:
            return (self.tics[None], datetime.datetime.now())
        elif (id, name) in self.tics:
            return (self.tics.pop((id,name)), datetime.datetime.now())

    def getTac(self, id, name):
        if name is None:
            return (self.tics[None], datetime.datetime.now())
        elif (id, name) in self.tics:
            return (self.tics[(id,name)], datetime.datetime.now())

    def clockTic(self, id, name=None, details=None):
        tic = self.setTic(id,name)
        if name is None: name = "\t"
        mess = "Start %s\t((at %s))" % (name, tic)
        if details is not None:
            mess += ("\t%s" % details)
        self.printL(1, mess, "time", id)

    def clockTac(self, id, name=None, details=""):
        tic, tac = self.getTac(id,name)
        if name is None: name = "\t"
        mess = "End %s\t((at %s, elapsed %s))" % (name, tac, tac-tic)
        if details is not None:
            mess += ("\t%s" % details)
        self.printL(1, mess, "time", id)
    
    def disp(self):
        tmp = "LOGGER"
        for out in self.out:
            tmp += "\n\t* %s -> %s" % (out["verbosity"],  out["destination"])
        for out in self.oqu:
            tmp += "\n\t* %s -> %s" % (out["verbosity"],  out["destination"])
        return tmp
        
    def resetOut(self):
        self.out = []
        self.oqu = []
        self.verbosity = -1

    def __getstate__(self):
        return { 'verbosity': self.verbosity, 'oqu': self.oqu, 'out': []}
        
    def addOut(self,  verbosity=1, output = '-', method_comm = None):
        # print "Adding output:\t", output, type(output), method_comm
        ### CHECK OUTPUT
        if type(output) == str:
            if output in ['-', "stdout"]:
                tmp_dest = sys.stdout
            elif output == 'stderr':
                tmp_dest = sys.stderr
            else:
                try:
                    tmp_dest = open(output, 'w')
                except IOError:
                    return
        else:
            tmp_dest = output
            

        ### CHECK VERBOSITY
        if type(verbosity) == int:
            verbosity = {"*": verbosity, "progress":0, "result":0, "error":0} 
        
        if type(verbosity) == dict:
            if max(verbosity.values()) > self.verbosity:
                self.verbosity = max(verbosity.values())
        else:
            return

        ### OK ADD OUTPUT
        if output is not None and type(output) is not str:
             self.oqu.append({"verbosity": verbosity, "destination": tmp_dest, "method": method_comm})
        else:
            self.out.append({"verbosity": verbosity, "destination": tmp_dest, "method": method_comm})
        return len(self.out)+len(self.oqu)-1

    def printL(self, level, message, type_message="*", source=None):
        for out in self.out+self.oqu:
            if ( type_message in out["verbosity"].keys() and level <= out["verbosity"][type_message]) \
                   or  ( type_message not in out["verbosity"].keys() and "*" in out["verbosity"].keys() and level <= out["verbosity"]["*"]):
                
                if type(out["destination"]) == file:
                    if type_message == "*":
                        header = ""
                    else:
                        header = type_message
                    if source is None:
                        header += ""
                    else:
                        header += "@%s" % source
                    if len(header) > 0:
                        header = "[[%-10s]]\t" % header
                    out["destination"].write("%s%s\n" % (header, message))
                    out["destination"].flush()
                else:
                    # print "Log printing:\t", type_message, message, "\n\tFrom", source ," to ", out["destination"]
                    out["method"](out["destination"], message, type_message, source)
        
        
