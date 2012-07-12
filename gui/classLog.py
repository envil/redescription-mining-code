import sys
import pdb
        
class Log:
    def __init__(self, verbosity=1, output = '-', method_comm = None):
        self.out = []
        self.verbosity = -1
        self.addOut(verbosity, output, method_comm)
        
    def addOut(self,  verbosity=1, output = '-', method_comm = None):
        ### CHECK OUTPUT
        if type(output) == str: 
            if output == '-':
                tmp_dest = sys.stdout
            else:
                try:
                    tmp_dest = open(output, 'w')
                except IOError:
                    return
        else:
            tmp_dest = output

        ### CHECK VERBOSITY
        if type(verbosity) == int:
            verbosity = {"*": verbosity} 
        
        if type(verbosity) == dict:
            if max(verbosity.values()) > self.verbosity:
                self.verbosity = max(verbosity.values())
        else:
            return

        ### OK ADD OUTPUT
        self.out.append({"verbosity": verbosity, "destination": tmp_dest, "method": method_comm})
        return len(self.out)-1

    def printL(self, level, message, type_message="*"):
        for out in self.out:
            if ( type_message in out["verbosity"].keys() and level <= out["verbosity"][type_message]) \
                   or  ( "*" in out["verbosity"].keys() and level <= out["verbosity"]["*"]):

                if type(out["destination"]) == file:
                    if type_message == "*":
                        str_type = ""
                    else:
                        str_type = "[%s]\t" % type_message
                    out["destination"].write("%s%s\n" % (str_type, message))
                    out["destination"].flush()
                else:
                    out["method"](out["destination"], message, type_message)
        
        
