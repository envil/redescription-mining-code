## needs Redescription
import utilsStats
import pdb
        
class BestsDraft:
    diff_item = 1
    diff_supp = 2
    diff_toRed = 3
    diff_toBlue = 4
    diff_acc = 5
    diff_none = 6

    minItmIn = None
    minItmOut = None
    minLen = None
    minC = None
    minFinIn = None
    minFinOut = None
    coeffPVRule = 1
    coeffPVRed =1
    coeffImpacc = 1
    coeffRelImpacc = 0

    def dispParams():

        return "minC:%i, minItmIn:%i, minItmOut:%i, minFinIn:%i, minFinOut:%i, minLen:%i, coeffImpacc:%f, coeffRelImpacc:%f, coeffPVRule:%f, coeffPVRed:%f"\
               % (BestsDraft.minC, BestsDraft.minItmIn, BestsDraft.minItmOut, BestsDraft.minFinIn, BestsDraft.minFinOut, BestsDraft.minLen, \
                  BestsDraft.coeffImpacc, BestsDraft.coeffRelImpacc, BestsDraft.coeffPVRule, BestsDraft.coeffPVRed)
    dispParams = staticmethod(dispParams)    
#     def compSurp(self, pos):
#         if self.bests[pos] != None:
#             if self.bests[pos]['side'] == 0:
#                 if self.bests[pos]['op'].isOr():
#                     return [self.red.prs[0], +self.red.prs[0]]

    def minNbItmIn(self):
        return BestsDraft.minItmIn
    def minNbItmOut(self):
        return BestsDraft.minItmOut
    def minNbFinIn(self):
        return BestsDraft.minFinIn
    def minNbFinOut(self):
        return BestsDraft.minFinOut
    def minNbC(self):
        return BestsDraft.minC

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
                if (lparts[1] - toColors[1] >= self.minNbC() ) and ( toColors[0] >= self.minNbItmOut() ):
                    b= {'acc': float(lparts[2] + lparts[1] - toColors[1])/(lparts[0] + lparts[1] + lparts[2] + lparts[3] - toColors[0]),\
                        'toRed': lparts[3] - toColors[0], 'toBlue': lparts[1] - toColors[1], 'term': t}

            else:
                if (toColors[1] >= self.minNbC() ) and (lparts[3] - toColors[0] >= self.minNbItmOut() ):
                    b= {'acc': float(lparts[2] + toColors[1])/(lparts[0] + lparts[1] + lparts[2] + toColors[0]),\
                        'toRed': toColors[0], 'toBlue': toColors[1], 'term': t}
        else:
            if neg:
                if (toColors[0] >= self.minNbC() ) and (lparts[2] - toColors[1] >= self.minNbItmIn() ):
                    b= {'acc': float(lparts[2] - toColors[1])/(lparts[0] - toColors[0] + lparts[1] + lparts[2]),\
                        'toRed': lparts[0] - toColors[0], 'toBlue': lparts[2] - toColors[1], 'term': t}
            else:
                if (lparts[0] - toColors[0] >= self.minNbC() ) and (toColors[1] >= self.minNbItmIn() ):
                    b= {'acc': float(toColors[1])/(toColors[0] + lparts[1] + lparts[2]),\
                        'toRed': toColors[0], 'toBlue': toColors[1], 'term': t}
        return b
    
    def pos(side, op):
        if side == -1:
            return -1
        else:
            return side*2 + op.isOr()*1
    pos = staticmethod(pos)    

    def __init__(self, ruleTypes, N,  currRed=None):
        currBest = {'side': -1, 'acc':0, 'op': None, 'term': None, 'toBlue': 0, 'toRed': 0, 'supp': set()}
        self.parts = None
        if currRed != None:
            self.parts = currRed.parts()
            currBest['acc'] = currRed.acc()
        self.bests = [None, None, None, None, currBest] ## last contains current rule
        self.red = currRed
        self.ruleTypes = ruleTypes
        self.N = N

    def ruleTypesOp(self):
        return self.ruleTypes.keys()

    def ruleTypesNP(self, opOR):
        return self.ruleTypes[opOR]

    def ruleTypesHasPos(self, opOR):
        return False in self.ruleTypes[opOR]
    
    def ruleTypesHasNeg(self, opOR=None):
        if opOR == None:
            return (True in self.ruleTypes[False]) or (True in self.ruleTypes[True])
        else:
            return True in self.ruleTypes[opOR]
        
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


    def pValRule(self, cand):
        return self.pValSupp2Rule(cand)
        
    def pValRed(self, cand):
        return self.pValSupp2Red(cand)

    def pValRuleScore(self, cand):
        if BestsDraft.coeffPVRule != 0:
            return BestsDraft.coeffPVRule*self.pValRule(cand)
        else:
            return 0

    def pValRedScore(self, cand):
        if BestsDraft.coeffPVRed != 0:
            return BestsDraft.coeffPVRed*self.pValRed(cand)
        else:
            return 0
    
    def score(self, cand):
        if cand == None:
            return None
        elif cand.has_key('side') and cand['side'] == -1:
            return 0
        else:
            return BestsDraft.coeffImpacc*self.impacc(cand) \
                   + BestsDraft.coeffRelImpacc*self.relImpacc(cand) \
                   - self.pValRuleScore(cand) - self.pValRedScore(cand)
        
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
        
    def finalOK(red):
        return red.length(0) + red.length(1) >= BestsDraft.minLen \
                   and red.N - red.lenU() >= BestsDraft.minFinOut \
                   and red.lenI() >= BestsDraft.minFinIn  
    finalOK = staticmethod(finalOK) 
        
    def improving(self, minScore = 0, excludeCurr = False):
        if excludeCurr or self.score(self.bests[-1]) < minScore:
            r = []
        else:
            r = [-1]
        for pos in range(len(self.bests)-1):
            if self.score(self.bests[pos]) >= minScore:
               r.append(pos)
        return r
    
    def dispCand(self, cand):
        if cand == None:
            dsp = '* %20s <==> * %20s' % ('','')
        elif cand['side'] == 0:
            dsp = '* %20s <==> * %20s\t\t%1.7f \t%+1.7f \t\t% 5i \t% 5i\t' \
                  % ((str(cand['op']) + str(cand['term'])), '', cand['acc'], self.score(cand), cand['toBlue'], cand['toRed'])
        elif cand['side'] == 1:
            dsp = '* %20s <==> * %20s\t\t%1.7f \t%+1.7f \t\t% 5i \t% 5i\t' \
                  % ('', (str(cand['op']) + str(cand['term'])), cand['acc'], self.score(cand), cand['toBlue'], cand['toRed'])
        return dsp

    def pValSuppRule(self, cand):
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

    def pValSupp2Rule(self, cand):
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

    def pValOverRule(self, cand):
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

    def pValSupp2Red(self, cand):
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

    def expOver(self, cand):
        if cand == None:
            return (-1,-1)
        elif self.red == None: # in the case of an initial pair WARNING  in that case supp is the support of the other side !
            return ( float(cand['supp'] * (cand['toBlue'] + cand['toRed']))/(self.N), cand['toBlue'])
        elif cand['side'] == -1:
            return (0,0)
        else:
            if cand['op'].isOr():
                return ( float(len(cand['supp']) * self.red.lenX(cand['side']))/(self.N), len(cand['supp']) - cand['toBlue'] - cand['toRed'])
                
            else: 
                return ( float(len(cand['supp']) * self.red.lenX(cand['side']))/(self.N), cand['toBlue'] + cand['toRed'])
                

    def dispCandSurp(self, cand):
        if cand == None:
            ext = ''
            dsp = '* %20s <==> * %20s' % ('','')
        else:
#            pdb.set_trace()
            #ext = '\n\t\t\tpValSuppS1: %f pValSuppS2: %f pValOverS: %f\n\t\t\tpValSuppN1: %f pValSuppN2: %f pValOverN: %f' \
            ext = '\n\t\t\t%f %f %f --- %f %f %f --- %s' \
                  %( self.pValSuppRule(cand), self.pValSupp2Rule(cand), self.pValOverRule(cand), self.pValSuppRed(cand), self.pValSupp2Red(cand), self.pValOverRed(cand), self.expOver(cand))
            dsp = ''
            if cand['side'] == 0:
                dsp = '* %20s <==> * %20s\t\t%1.7f \t%+1.7f \t\t% 5i \t% 5i\t% 5i' \
                      % ((str(cand['op']) + str(cand['term'])), '', cand['acc'], self.score(cand), cand['toBlue'], cand['toRed'], len(cand['supp']))
            elif cand['side'] == 1:
                dsp = '* %20s <==> * %20s\t\t%1.7f \t%+1.7f \t\t% 5i \t% 5i\t% 5i' \
                      % ('', (str(cand['op']) + str(cand['term'])), cand['acc'], self.score(cand), cand['toBlue'], cand['toRed'], len(cand['supp']))
        return '\n'+dsp+ext

        
    def __str__(self):
        dsp  = 'Bests Draft:  improving:%s\n' % (self.improving())
        if self.red != None:
            dsp += str(self.red)
        else:
            dsp += 'empty redescription'
        for cand in self.bests[:-1]: ## Do not print the last: current redescription
            dsp += '\n\t'+self.dispCandSurp(cand)
        return dsp
    
