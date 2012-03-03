import sys
import pdb
import wx
class Log:
    
    def __init__(self,  verbosity=1, output = '-'):
        
        self.out = None
        if type(output) == wx.TextCtrl:
            self.out = output
        elif output == '-':
            self.out = sys.stdout
        elif output != None  and len(output) > 0:
#            pdb.set_trace()
            self.out = open(output, 'w')
        self.verbosity = verbosity

    def printL(self, level, message):
        if self.out != None and self.verbosity >= level:
            if type(self.out) == wx.TextCtrl:
                self.out.AppendText("%s\n" % message)
            else:
                self.out.write("%s\n" % message)
        
        
