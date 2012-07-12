from classRedescription import Redescription
from classExtension import Extension
import pdb

class ExtensionsBatch:
    def __init__(self, coeffs=None, current=None):
        self.current = current
        self.base_acc = self.current.acc()
        self.prs = self.current.probas()
        self.coeffs = coeffs
        self.bests = {}

    def scoreCand(self, cand):
        if cand != None:
            #if cand.literal.term.col == 1: pdb.set_trace()
            return cand.score(self.base_acc, self.prs, self.coeffs)
    def scoreRed(self, red):
        pass

    def pos(self, cand):
        if cand.isValid():
            return (cand.side, cand.op)

    def get(self, pos):
        if self.bests.has_key(pos):
            return self.bests[pos]
        else:
            return None
        
    def update(self, cands):
        for cand in cands:
            pos = self.pos(cand)
            self.scoreCand(cand)
            if pos != None and (not self.bests.has_key(pos) or self.scoreCand(cand) > self.scoreCand(self.bests[pos])):
                self.bests[pos] = cand

    def improving(self, min_impr=0):
        return dict([(pos, cand)  for (pos, cand) in self.bests.items() \
                     if self.scoreCand(cand, self.coeffs) >= min_impr])

    def improvingKids(self, data, min_impr=0, max_var=-1):
        kids = []
        for (pos, cand) in self.bests.items():
            if self.scoreCand(cand) >= min_impr:
                kid = cand.kid(self.current, data)
                kid.setFull(max_var)
                if kid.acc() != cand.acc: raise Error('Something went badly wrong during expansion\nof %s\n\t%s ~> %s' % (self.current, cand, kid))
                kids.append(kid)
        return kids
        
    def __str__(self):
        dsp  = 'Extensions Batch:\n' 
        dsp += 'Redescription: %s' % self.current
        dsp += '\n\t  %20s        %20s' \
                  % ('LHS extension', 'RHS extension')
            
        dsp += '\t\t%10s \t%9s \t%9s \t%9s\t% 5s\t% 5s' \
                      % ('score', 'Accuracy',  'Query pV','Red pV', 'toBlue', 'toRed')
            
        for k,cand in self.bests.items(): ## Do not print the last: current redescription
            dsp += '\n\t%s' % cand.disp(self.base_acc, self.prs, self.coeffs)
        return dsp
