from classLog import Log
from classQuery import Op
from classRedescription import  Redescription
from classSParts import SParts
import pdb
        
class BestsDraft:
    diff_item = 1
    diff_in = 2
    diff_toRed = 3
    diff_toBlue = 4
    diff_acc = 5
    diff_none = 6

    logger = Log(0)

    coeffPVQuery = 1
    coeffPVRed =1
    coeffImpacc = 1
    coeffRelImpacc = 0
    thresfact = 1    

    def settings(setts):
        (BestsDraft.coeffImpacc, BestsDraft.coeffRelImpacc, BestsDraft.coeffPVQuery, BestsDraft.coeffPVRed) = (setts.param['coeff_impacc'], setts.param['coeff_relimpacc'], setts.param['coeff_pvquery'], setts.param['coeff_pvred'])
    settings = staticmethod(settings)


    def pos(side, op):
        if side == -1:
            return -1
        else:
            return side*2 + op*1
    pos = staticmethod(pos)    

    def score(cand, N, baseAcc=0, prs=None):
        if cand == None:
            return None
        else:

            return BestsDraft.coeffImpacc*BestsDraft.impacc(cand, baseAcc) \
                   + BestsDraft.coeffRelImpacc*BestsDraft.relImpacc(cand, baseAcc) \
                   + BestsDraft.pValRedScore(cand, N, prs) + BestsDraft.pValQueryScore(cand, N, prs)
    score = staticmethod(score)
        
    def relImpacc(cand, baseAcc=0):
        if cand == None:
            return None
        else:
            if baseAcc != 0:
                return (cand['acc']- baseAcc)/baseAcc
            else:
                return cand['acc']
    relImpacc = staticmethod(relImpacc)
    
    def impacc(cand, baseAcc=0):
        if cand == None:
            return None
        else:
            if baseAcc != 0:
                return (cand['acc']- baseAcc)
            else:
                return cand['acc']
    impacc = staticmethod(impacc)

    def pValQueryScore(cand, N, prs):
        if BestsDraft.coeffPVQuery < 0:
            return BestsDraft.coeffPVQuery * SParts.pValQueryCand(cand['side'], cand['op'], cand['neg'], cand['lparts'], N, prs)
        elif BestsDraft.coeffPVQuery > 0:
            return -BestsDraft.thresfact*(BestsDraft.coeffPVQuery < SParts.pValQueryCand(cand['side'], cand['op'], cand['neg'], cand['lparts'], N, prs))
        else:
            return 0
    pValQueryScore = staticmethod(pValQueryScore)

    def pValRedScore(cand, N, prs):
        if BestsDraft.coeffPVRed < 0:
            return BestsDraft.coeffPVRed * SParts.pValRedCand(cand['side'], cand['op'], cand['neg'], cand['lparts'], N, prs)
        elif BestsDraft.coeffPVRed > 0:
            return -BestsDraft.thresfact*(BestsDraft.coeffPVRed < SParts.pValRedCand(cand['side'], cand['op'], cand['neg'], cand['lparts'], N, prs))
        else:
            return 0
    pValRedScore = staticmethod(pValRedScore)

    def __init__(self, N,  baseAcc=0, prs = None):
        self.baseAcc = baseAcc
        self.bests = [None, None, None, None]
        self.N = N
        self.prs = prs 
        
    def acc(self, pos):
        return self.bests[pos]['acc']
    
    def term(self, pos):
        return self.bests[pos]['term']
    
    def side(self, pos):
        if self.bests[pos] != None:
            return self.bests[pos]['side']
        else:
            return None
    def op(self, pos):
        return self.bests[pos]['op']
    
    def supp(self, pos):
        return self.bests[pos]['supp']

    def comparePair(x, y):
        if x == None:
            return -BestsDraft.diff_none
        elif y == None:
            return BestsDraft.diff_none
        else:
            if x['acc'] > y['acc']:
                return BestsDraft.diff_acc
            elif x['acc'] == y['acc']:
                if x['toBlue'] > y['toBlue']:
                    return BestsDraft.diff_toBlue
                elif x['toBlue'] == y['toBlue']:
                    if x['toRed'] > y['toRed']:
                        return BestsDraft.diff_toRed
                    elif x['toRed'] == y['toRed']:
                        if x['cont'] < y['cont']:
                            return BestsDraft.diff_in
                        elif x['cont'] == y['cont']:
                            if x['term'] > y['term']:
                                return BestsDraft.diff_item
                            elif x['term'] == y['term']:
                                return 0
                            else:
                                return -BestsDraft.diff_item
                        else:
                            return -BestsDraft.diff_in
                    else:
                        return -BestsDraft.diff_toRed
                else:
                    return -BestsDraft.diff_toBlue
            else:
                return -BestsDraft.diff_acc
    comparePair = staticmethod(comparePair) 

    def upBests(self, candis):
        for candi in candis:
            pos = BestsDraft.pos(candi['side'], candi['op'])
            if BestsDraft.score(candi, self.N, self.baseAcc, self.prs) > BestsDraft.score(self.bests[pos], self.N, self.baseAcc, self.prs) :
            #if BestsDraft.comparePair(candi, self.bests[pos]) > 0 :
                self.bests[pos] = candi

    def improving(self, minScore = 0):
        r = []
        for pos in range(len(self.bests)):
            if BestsDraft.score(self.bests[pos], self.N, self.baseAcc, self.prs) >= minScore:
               r.append(pos)
        return r

    def dispCand(self, cand):
        if cand == None:
            dsp = '* %20s <==> * %20s' % ('','')
            scoring = ''

        elif cand['side'] == 0:
            dsp = '* %20s <==> * %20s' \
                  % ((str(Op(cand['op'])) + str(cand['term'])), '')
            
            scoring = '\t\t%+1.7f \t%1.7f \t%1.7f \t%1.7f\t% 5i\t% 5i' \
                      % (BestsDraft.score(cand, self.N, self.baseAcc, self.prs), cand['acc'], \
                         SParts.pValQueryCand(cand['side'], cand['op'], cand['neg'], cand['lparts'], self.N, self.prs), \
                         SParts.pValRedCand(cand['side'], cand['op'], cand['neg'], cand['lparts'], self.N, self.prs) , cand['toBlue'], cand['toRed'])
            
        elif cand['side'] == 1:
            dsp = '* %20s <==> * %20s' \
                  % ('', (str(Op(cand['op'])) + str(cand['term'])))
            
            scoring = '\t\t%+1.7f \t%1.7f \t%1.7f \t%1.7f\t% 5i\t% 5i' \
                     % (BestsDraft.score(cand, self.N, self.baseAcc, self.prs), cand['acc'], \
                         SParts.pValQueryCand(cand['side'], cand['op'], cand['neg'], cand['lparts'], self.N, self.prs), \
                         SParts.pValRedCand(cand['side'], cand['op'], cand['neg'], cand['lparts'], self.N, self.prs) , cand['toBlue'], cand['toRed'])
            
        return dsp+scoring
        
    def __str__(self):
        dsp  = 'Bests Draft:\n' 
        dsp += '\n\t  %20s        %20s' \
                  % ('LHS extension', 'RHS extension')
            
        dsp += '\t\t%10s \t%9s \t%9s \t%9s\t% 5s\t% 5s' \
                      % ('score', 'Accuracy',  'Query pV','Red pV', 'toBlue', 'toRed')
            
        for cand in self.bests: ## Do not print the last: current redescription
            dsp += '\n\t'+self.dispCand(cand)
        return dsp
    
