import sys
import pdb
        
class Log:
    def __init__(self, verbosity=1, output = '-', method_comm = None):
        self.out = []
        self.verbosity = -1
        self.addOut(verbosity, output, method_comm)

    def resetOut(self):
        self.out = []
        self.verbosity = -1
        
    def addOut(self,  verbosity=1, output = '-', method_comm = None):
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
        self.out.append({"verbosity": verbosity, "destination": tmp_dest, "method": method_comm})
        return len(self.out)-1

    def printL(self, level, message, type_message="*", source=None):
        for out in self.out:
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
                    out["method"](out["destination"], message, type_message, source)
        
        
