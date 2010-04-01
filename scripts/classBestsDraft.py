## needs Redescription
import pdb

## return list of index for sorted values between given bounds
def  sortIndexList(L, minVal = float('-Inf'), maxVal = float('Inf')):
    if min(L) == max(L):
        if  minVal < L[0] and maxVal > L[0]:
            return range(len(L))
        else:
            return []
    else:
        S = [(i, L[i]) for i in range(len(L))]
        S.sort(key = lambda x: x[1])
        if minVal < S[0][1] and maxVal > S[-1][1]:
            return [S[i][0] for i in range(len(S))]
        else :
            sortedIndList = []
            for i in range(len(S)):
                if S[i][1] >= minVal and S[i][1] <= maxVal:
                    sortedIndList.append(S[i][0])
            return sortedIndList
        
class BestsDraft:
    diff_item = 1
    diff_toRed = 2
    diff_toBlue = 3
    diff_acc = 4
    diff_none = 5
    
    def make(acc=-1, side=-1, op=-1, term=-1, toRed=0, toBlue=0):
        return {'acc': acc, 'term': term, 'side': side, 'op': op, 'toRed' : toRed, 'toBlue': toBlue }
    make = staticmethod(make)
    
    def pos(side, op):
        if side == -1:
            return -1
        else:
            return side*2 + op.isOr()*1
    pos = staticmethod(pos)    

    def __init__(self, ncurrAcc):
        self.bests = [BestsDraft.make(),
                      BestsDraft.make(),
                      BestsDraft.make(),
                      BestsDraft.make(),
                      BestsDraft.make(ncurrAcc)] ## last contains current rule
        
    def term(self, pos):
        return self.bests[pos]['term']
    def acc(self, pos):
        return self.bests[pos]['acc']
    def toRed(self, pos):
        return self.bests[pos]['toRed']
    def toBlue(self, pos):
        return self.bests[pos]['toBlue']
    def side(self, pos):
        return self.bests[pos]['side']
    def op(self, pos):
        return self.bests[pos]['op']    

#     def compare(self, x, pos):
#         if x['acc'] > self.bests[pos]['acc']:
#             return BestsDraft.diff_acc
#         elif x['acc'] == self.bests[pos]['acc']:
#             if x['toBlue'] > self.bests[pos]['toBlue']:
#                 return BestsDraft.diff_toBlue
#             elif x['toBlue'] == self.bests[pos]['toBlue']:
#                 if x['toRed'] > self.bests[pos]['toRed']:
#                     return BestsDraft.diff_toRed
#                 elif x['toRed'] == self.bests[pos]['toRed']:
#                     if x['term'] > self.bests[pos]['term']:
#                         return BestsDraft.diff_item
#                     elif x['term'] == self.bests[pos]['term']:
#                         return 0
#                     else:
#                         return -BestsDraft.diff_item
#                 else:
#                     return -BestsDraft.diff_toRed
#             else:
#                 return -BestsDraft.diff_toBlue
#         else:
#             return -BestsDraft.diff_acc

    def comparePair(x, y):
        if y == None:
            return BestsDraft.diff_none
        elif x == None:
            return -BestsDraft.diff_none
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
                        if x['term'] > y['term']:
                            return BestsDraft.diff_item
                        elif x['term'] == y['term']:
                            return 0
                        else:
                            return -BestsDraft.diff_item
                    else:
                        return -BestsDraft.diff_toRed
                else:
                    return -BestsDraft.diff_toBlue
            else:
                return -BestsDraft.diff_acc
    comparePair = staticmethod(comparePair) 

    def upBest(self, candis):
        for candi in candis:
            pos = BestsDraft.pos(candi['side'], candi['op'])
        ##cand = BestsDraft.make(acc, side, op, term, toRed, toBlue)
            if BestsDraft.comparePair(candi, self.bests[pos]) > 0 :
                self.bests[pos] = candi

#     def newABc(self, pos, redescription):
#         if self.bests[pos]['side'] == 0 :
#             if self.bests[pos]['OR'] :
#                 return (redescription.lenL() + self.bests[pos]['toBlue'] + self.bests[pos]['toRed'], redescription.lenR(), redescription.lenI() + self.bests[pos]['toBlue'])
#             else:
#                 return (self.bests[pos]['toBlue'] + self.bests[pos]['toRed'], redescription.lenR(), self.bests[pos]['toBlue'])
#         if self.bests[pos]['side'] == 1 :
#             if self.bests[pos]['OR'] :
#                 return (redescription.lenL(), redescription.lenR() + self.bests[pos]['toBlue'] + self.bests[pos]['toRed'],  redescription.lenI() + self.bests[pos]['toBlue'])
#             else:
#                 return (redescription.lenL(), self.bests[pos]['toBlue'] + self.bests[pos]['toRed'], self.bests[pos]['toBlue'])

#     def surp(self, pos, redescription):
#         (A, B, c) = self.newABc(pos, redescription)
#         (min_acc, max_acc, exp_acc) = (max(0,(A+B)-redescription.N)/min(redescription.N, (A+B)), min(A,B)/max(A,B), A*B/(redescription.N*(A+B)-A*B))
#         return 'exp_acc: %f, min_acc: %f, max_acc: %f, d: %f, ratio: %f' %(exp_acc, min_acc, max_acc, self.bests[pos]['acc'] -exp_acc, (self.bests[pos]['acc']- min_acc)/max(0.001,(max_acc - min_acc)))
             
    def score(self, pos): 
        return (self.bests[pos]['acc']- self.bests[-1]['acc'])/self.bests[-1]['acc']

    def rank(self, min = 0 , max= float('Inf') , excludeCurr = False):
        return sortIndexList([ self.score(i) for i in range(len(self.bests)-1*excludeCurr)], min, max)
    
    def dispCand(self, pos):
        if self.side(pos) == 0:
            dsp = '* %8s <==> * %8s\t\t%1.7f \t%+1.7f \t\t% 5i \t% 5i\t' % ((str(self.op(pos)) + str(self.term(pos))), '', self.acc(pos), self.score(pos), self.toBlue(pos), self.toRed(pos))
        else:
            dsp = '* %8s <==> * %8s\t\t%1.7f \t%+1.7f \t\t% 5i \t% 5i\t' % ('', (str(self.op(pos)) + str(self.term(pos))), self.acc(pos), self.score(pos), self.toBlue(pos), self.toRed(pos))
        return dsp

#     def dispCandLong(self, pos, red):
#         return self.dispCand( pos) + self.surp(pos, red)
        
    def __str__(self):    
        dsp  = 'Bests Draft:   %1.7f  ranking:%s' % (self.bests[-1]['acc'], str(self.rank()))
        for i in range(len(self.bests)-1): ## Do not print the last: current redescription
            dsp += '\n\t'+self.dispCand(i)
        return dsp
    
 #    def dispLong(self, red):    
#         dsp  = 'Bests Draft:   %1.7f  ranking:%s' % (self.bests[-1]['acc'], str(self.rank()))
#         for i in range(len(self.bests)-1): ## Do not print the last: current redescription
#             dsp += '\n\t'+self.dispCandLong(i, red)
#         return dsp
    
