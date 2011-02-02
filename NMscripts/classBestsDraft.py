from classLog import Log
from classRedescription import  Redescription
import utilsStats
import pdb
        
class BestsDraft:
    diff_item = 1
    diff_supp = 2
    diff_toRed = 3
    diff_toBlue = 4
    diff_acc = 5
    diff_none = 6

    logger = Log(0)

    minSuppIn = None
    minSuppOut = None

    minLen = 0
    minAcc = 0
    maxPVal = 1

    minC = 0
    
    coeffPVQuery = 1
    coeffPVRed =1
    coeffImpacc = 1
    coeffRelImpacc = 0

    def minItmSuppIn(self):
        return BestsDraft.minSuppIn
    def minItmSuppOut(self):
        return BestsDraft.minSuppOut
    def minItmC(self):
        return BestsDraft.minC
    def minFinSuppIn():
        return BestsDraft.minSuppIn
    minFinSuppIn = staticmethod(minFinSuppIn)
    def minFinSuppOut():
        return BestsDraft.minSuppOut
    minFinSuppOut = staticmethod(minFinSuppOut)
    def minFinLength():
        return BestsDraft.minLen
    minFinLength = staticmethod(minFinLength)
    def maxFinPVal():
        return BestsDraft.maxPVal    
    maxFinPVal = staticmethod(maxFinPVal)
    def minFinAcc():
        return BestsDraft.minAcc
    minFinAcc = staticmethod(minFinAcc)

    def checkFinalConstraints(red):
        if red.length(0) + red.length(1) >= BestsDraft.minFinLength() \
                   and red.N - red.lenU() >= BestsDraft.minFinSuppOut() \
                   and red.lenI() >= BestsDraft.minFinSuppIn() \
                   and red.acc()  >= BestsDraft.minFinAcc() \
                   and red.pVal() <= BestsDraft.maxFinPVal():
            BestsDraft.logger.printL(3, 'Redescription complies with final constraints ... (%s)' %(red))
            return True
        else:
            BestsDraft.logger.printL(3, 'Redescription non compliant with final constraints ...(%s)' % (red))
            return False
    checkFinalConstraints = staticmethod(checkFinalConstraints) 


    def lenRed(self):
        if self.red == None:
            return 2
        else:
            return len(self.red)

    def compAcc(self, op, neg, toColors, lparts):
        acc = 0
        if op:
            if neg:
                acc = float(lparts[2] + lparts[1] - toColors[1])/(lparts[0] + lparts[1] + lparts[2] + lparts[3] - toColors[0])
            else:
                acc = float(lparts[2] + toColors[1])/(lparts[0] + lparts[1] + lparts[2] + toColors[0])
        else:
            if neg:
                acc = float(lparts[2] - toColors[1])/(lparts[0] - toColors[0] + lparts[1] + lparts[2])
            else:
                acc = float(toColors[1])/(toColors[0] + lparts[1] + lparts[2])
        return acc
    
    def compAdv(self, t, op, neg, toColors, lparts):
        b = None
        if op:
            if neg:
#                pdb.set_trace()
                if (lparts[1] - toColors[1] >= self.minItmC() ) and ( toColors[0] >= self.minItmSuppOut() ):
                    if ((lparts[0] + lparts[1] + lparts[2] + lparts[3] - toColors[0]) > 0):
                        b= {'acc': float(lparts[2] + lparts[1] - toColors[1])/(lparts[0] + lparts[1] + lparts[2] + lparts[3] - toColors[0]),\
                            'toRed': lparts[3] - toColors[0], 'toBlue': lparts[1] - toColors[1], 'term': t}

            else:
#                pdb.set_trace()
                if (toColors[1] >= self.minItmC() ) and (lparts[3] - toColors[0] >= self.minItmSuppOut() ):
                    if ((lparts[0] + lparts[1] + lparts[2] + toColors[0]) > 0):
                        b= {'acc': float(lparts[2] + toColors[1])/(lparts[0] + lparts[1] + lparts[2] + toColors[0]),\
                            'toRed': toColors[0], 'toBlue': toColors[1], 'term': t}
        else:
            if neg:
                if (toColors[0] >= self.minItmC() ) and (lparts[2] - toColors[1] >= self.minItmSuppIn() ):
                    if ( (lparts[0] - toColors[0] + lparts[1] + lparts[2]) > 0 ):
                        b= {'acc': float(lparts[2] - toColors[1])/(lparts[0] - toColors[0] + lparts[1] + lparts[2]),\
                            'toRed': lparts[0] - toColors[0], 'toBlue': lparts[2] - toColors[1], 'term': t}
            else:
                if (lparts[0] - toColors[0] >= self.minItmC() ) and (toColors[1] >= self.minItmSuppIn() ):
                    if ((toColors[0] + lparts[1] + lparts[2]) > 0 ):
                        b= {'acc': float(toColors[1])/(toColors[0] + lparts[1] + lparts[2]),\
                            'toRed': toColors[0], 'toBlue': toColors[1], 'term': t}
        return b
    
    def pos(side, op):
        if side == -1:
            return -1
        else:
            return side*2 + op.isOr()*1
    pos = staticmethod(pos)    

    def __init__(self, queryTypes, N,  currRed=None):
#        pdb.set_trace()
        try:
            self.pValQuery = eval('self.pVal%sQuery' % (Redescription.methodpVal))
            self.pValRed = eval('self.pVal%sRed' % (Redescription.methodpVal))
        except AttributeError:
              raise Exception('Oups method to compute the p-value does not exist !')

        
        currBest = {'side': -1, 'acc':0, 'op': None, 'term': None, 'toBlue': 0, 'toRed': 0, 'supp': set()}
        self.parts = None
        if currRed != None:
            self.parts = currRed.parts()
            currBest['acc'] = currRed.acc()
        self.bests = [None, None, None, None, currBest] ## last contains current query
        self.red = currRed
        self.queryTypes = queryTypes
        self.N = N

    def queryTypesOp(self):
        return [i for i in self.queryTypes.keys() if len(self.queryTypes[i])> 0]

    def queryTypesNP(self, opOR):
        return self.queryTypes[opOR]

    def queryTypesHasPos(self, opOR):
        return False in self.queryTypes[opOR]
    
    def queryTypesHasNeg(self, opOR=None):
        if opOR == None:
            return (True in self.queryTypes[False]) or (True in self.queryTypes[True])
        else:
            return True in self.queryTypes[opOR]
        
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
                        if not x.has_key('supp') or not y.has_key('supp') or len(x['supp']) == len(y['supp']):
                            if x['term'] > y['term']:
                                return BestsDraft.diff_item
                            elif x['term'] == y['term']:
                                return 0
                            else:
                                return -BestsDraft.diff_item
                        elif len(x['supp']) > len(y['supp']):
                            return BestsDraft.diff_supp
                        else:
                            return -BestsDraft.diff_supp
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
            if self.score(candi) > self.score(self.bests[pos]) :
            #if BestsDraft.comparePair(candi, self.bests[pos]) > 0 :
                self.bests[pos] = candi

    def improving(self, minScore = 0, excludeCurr = False):
        
        if BestsDraft.logger.verbosity >= 4:
            BestsDraft.logger.printL(4, self)

        if excludeCurr or self.score(self.bests[-1]) < minScore:
            r = []
        else:
            r = [-1]
        for pos in range(len(self.bests)-1):
            if self.score(self.bests[pos]) >= minScore:
               r.append(pos)
        return r
    
    def score(self, cand):
        #pdb.set_trace()
        if cand == None:
            return None
        elif cand.has_key('side') and cand['side'] == -1:
            return 0
        else:
            return BestsDraft.coeffImpacc*self.impacc(cand) \
                   + BestsDraft.coeffRelImpacc*self.relImpacc(cand) \
                   + self.pValQueryScore(cand) + self.pValRedScore(cand)
        
    def relImpacc(self, cand):
        if cand == None:
            return None
        else:
            if self.bests[-1]['acc'] != 0:
                return (cand['acc']- self.bests[-1]['acc'])/self.bests[-1]['acc']
            else:
                return cand['acc']
        
    def impacc(self, cand):
        if cand == None:
            return None
        else:
            if self.bests[-1]['acc'] != 0:
                return (cand['acc']- self.bests[-1]['acc'])
            else:
                return cand['acc']

    def pValQueryScore(self, cand):
        if BestsDraft.coeffPVQuery < 0:
            return BestsDraft.coeffPVQuery * self.pValQuery(cand)
        elif BestsDraft.coeffPVQuery > 0:
            return -10*(BestsDraft.coeffPVQuery < self.pValQuery(cand))
        else:
            return 0

    def pValRedScore(self, cand):
        if BestsDraft.coeffPVRed < 0:
            return BestsDraft.coeffPVRed * self.pValRed(cand)
        elif BestsDraft.coeffPVRed > 0:
            return -10*(BestsDraft.coeffPVRed < self.pValRed(cand))
        else:
            return 0
    
    def pValSuppQuery(self, cand):
        if cand == None:
            return -1
        elif self.red == None or cand['side'] == -1:
            return 0
        else:
            if cand['op'].isOr():
                return 1-utilsStats.pValSupp(self.N, len(cand['supp']) - cand['toBlue'] - cand['toRed'], \
                                          self.red.prs[cand['side']] + float(len(cand['supp']))/(self.N) - self.red.prs[cand['side']]*float(len(cand['supp']))/(self.N))
            else: 
                return utilsStats.pValSupp(self.N, cand['toBlue'] + cand['toRed'], \
                                           self.red.prs[cand['side']]*float(len(cand['supp']))/(self.N))

    def pValMargQuery(self, cand):
        if cand == None:
            return -1
        elif  self.red == None or cand['side'] == -1:
            return 0
        else:
            if cand['op'].isOr():
                return 1-utilsStats.pValSupp(self.N, len(cand['supp']) - cand['toBlue'] - cand['toRed'], \
                                           float(len(cand['supp']) * self.red.lenX(cand['side']))/(self.N*self.N))
            else: 
                return utilsStats.pValSupp(self.N, cand['toBlue'] + cand['toRed'], \
                                           float(len(cand['supp']) * self.red.lenX(cand['side']))/(self.N*self.N))

    def pValOverQuery(self, cand):
        if cand == None:
            return -1
        elif  self.red == None or cand['side'] == -1 : 
            return 0
        else:
            if cand['op'].isOr():
                return 1-utilsStats.pValOver(len(cand['supp']) - cand['toBlue'] - cand['toRed'],\
                                    self.N, self.red.lenX(cand['side']) , len(cand['supp']))
            else: 
                return utilsStats.pValOver(cand['toBlue'] + cand['toRed'],\
                                    self.N, self.red.lenX(cand['side']) , len(cand['supp']))

    
    def pValSuppRed(self, cand):
        if cand == None:
            return -1
        elif self.red == None : # in the case of an initial pair WARNING  in that case supp is the len of the support of the other side !
            return utilsStats.pValSupp(self.N, cand['toBlue'], float(cand['supp']*(cand['toBlue'] + cand['toRed']))/(self.N*self.N))
        elif cand['side'] == -1:
            return 0
        else:
            if cand['op'].isOr():
                return utilsStats.pValSupp(self.N, self.red.lenI()+ cand['toBlue'], \
                                          self.red.prs[1-cand['side']]* \
                                           (self.red.prs[cand['side']] + float(len(cand['supp']))/(self.N) - self.red.prs[cand['side']]*float(len(cand['supp']))/(self.N)))
            else: 
                return utilsStats.pValSupp(self.N, cand['toBlue'], \
                                          self.red.prs[1-cand['side']]*self.red.prs[cand['side']] *float(len(cand['supp']))/(self.N))

    def pValMargRed(self, cand):
        if cand == None:
            return -1
        elif self.red == None: # in the case of an initial pair WARNING   in that case supp is the len of the support of the other side !
            return utilsStats.pValSupp(self.N, cand['toBlue'], float(cand['supp']*(cand['toBlue'] + cand['toRed']))/(self.N*self.N))
        elif cand['side'] == -1:
            return 0
        else:
            if cand['op'].isOr():
                return utilsStats.pValSupp(self.N, self.red.lenI()+ cand['toBlue'], \
                                          self.red.prs[1-cand['side']]* \
                                           float(self.red.lenX(cand['side']) + cand['toBlue'] + cand['toRed'])/(self.N))
            else: 
                return utilsStats.pValSupp(self.N, cand['toBlue'], \
                                          self.red.prs[1-cand['side']]* \
                                           float(cand['toBlue'] + cand['toRed'])/(self.N))

    def pValOverRed(self,  cand):
        if cand == None:
            return -1
        elif self.red == None: # in the case of an initial pair WARNING   in that case supp is the len of the support of the other side !
            return utilsStats.pValOver(cand['toBlue'], self.N, cand['toBlue'] + cand['toRed'], cand['supp'])
        elif cand['side'] == -1:
            return 0
        else:
            if cand['op'].isOr():
                return utilsStats.pValOver(self.red.lenI()+ cand['toBlue'], 
                                    self.N, self.red.lenX(1-cand['side']), self.red.lenX(cand['side']) + cand['toBlue'] + cand['toRed'])
            else: 
                return utilsStats.pValOver(cand['toBlue'],\
                                    self.N, self.red.lenX(1-cand['side']), cand['toBlue'] + cand['toRed'])


    def dispCand(self, cand):
        if cand == None:
            dsp = '* %20s <==> * %20s' % ('','')
            scoring = ''

        elif cand['side'] == 0:
            dsp = '* %20s <==> * %20s' \
                  % ((str(cand['op']) + str(cand['term'])), '')
            
            scoring = '\t\t%+1.7f \t%1.7f \t%1.7f \t%1.7f\t% 5i\t% 5i' \
                      % (self.score(cand), cand['acc'],  self.pValQuery(cand), self.pValRed(cand), cand['toBlue'], cand['toRed'])
            
        elif cand['side'] == 1:
            dsp = '* %20s <==> * %20s' \
                  % ('', (str(cand['op']) + str(cand['term'])))
            
            scoring = '\t\t%+1.7f \t%1.7f \t%1.7f \t%1.7f\t% 5i\t% 5i' \
                      % (self.score(cand), cand['acc'],  self.pValQuery(cand), self.pValRed(cand), cand['toBlue'], cand['toRed'])
            
        return dsp+scoring
        
    def __str__(self):
        dsp  = 'Bests Draft:\n'
        if self.red != None:
            dsp += str(self.red)
        else:
            dsp += 'empty redescription'
        dsp += '\n\t  %20s        %20s' \
                  % ('LHS extension', 'RHS extension')
            
        dsp += '\t\t%10s \t%9s \t%9s \t%9s\t% 5s\t% 5s' \
                      % ('score', 'Accuracy',  'Query pV','Red pV', 'toBlue', 'toRed')
            
        for cand in self.bests[:-1]: ## Do not print the last: current redescription
            dsp += '\n\t'+self.dispCand(cand)
        return dsp
    
