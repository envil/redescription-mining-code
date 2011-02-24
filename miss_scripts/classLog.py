import sys
class Log:
    
    def __init__(self,  verbosity=1, output = '-'):
        
        self.out = None
        if output == '-':
            self.out = sys.stdout
        elif output != None  and len(output) > 0:
            self.out = open(output, 'w')
        self.verbosity = verbosity

    def printL(self, level, message):
        if self.out != None and self.verbosity >= level:
            self.out.write("%s\n" % message)
