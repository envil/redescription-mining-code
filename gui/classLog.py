import sys
import pdb
        
class Log:
    def __init__(self,  verbosity=1, output = '-', method_comm = None):
        self.out = []
        self.addOut(verbosity, output, method_comm)
        
    def addOut(self,  verbosity=1, output = '-', method_comm = None):
        tmp_dest = None
        if type(output) == str: 
            if output == '-':
                tmp_dest = sys.stdout
            else:
                try:
                    tmp_dest = open(output, 'w')
                except IOError:
                    tmp_dest = None
        else:
            tmp_dest = output
        if tmp_dest != None:
            self.out.append([verbosity, tmp_dest, method_comm])
        self.verbosity = max([t[0] for t in self.out])
        return len(self.out)-1

    def printL(self, level, message, type_message=None):
        for (verbosity, output, method_comm) in self.out:
            if type(output) == file:
                if level >= 0 and level <= verbosity:
                    if type_message == None:
                        str_type = ""
                    else:
                        str_type = "%s:\t" % type_message
                    output.write("%s%s\n" % (str_type, message))
                    output.flush()
            else:
                if level <= verbosity:
                    method_comm(output, message, type_message)
        
        
