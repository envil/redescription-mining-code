from classRule import *
import pdb
class Souvenirs:
    format_index_pref = ':%(lengthL)i:%(lengthR)i:%(side)i:%(op)i:'
    format_index_suff = '%(buk)i:%(col)i:'
    def __init__(self,  nAvailableMo, nAmnesic = False):
        self.rulesList = []
        self.indexes = {}
        self.availableMo = nAvailableMo
        self.amnesic = nAmnesic

    def __str__(self):
        if self.amnesic :
            return 'Amnesic, Availables :%i x %i' % (len(self.availableMo[0]), len(self.availableMo[1]))
        else :
            return '%i souvenirs, %i indexes, Availables :%i x %i' \
                   % (len(self.rulesList), len(self.indexes), len(self.availableMo[0]), len(self.availableMo[1]))
    
    def count(self):
        return len(self.rulesList)
    
    def nextId(self):
        return len(self.rulesList)
        
    def add(self, red):
        if ( red.nbAvailableCols() > 0 and len(red) > 2 ) or (red.fullLength(0) and red.fullLength(1)):
            #print 'ADDED SOUVENIR----' + red.rules[0].dispIds() + '<=>' + red.rules[1].dispIds()
    
            ix = self.nextId()
            for indx in self.makeOwnIndexes(red):
                if self.indexes.has_key(indx):
                    self.indexes[indx].add(ix)
                else:
                    self.indexes[indx] = set([ix])
            self.rulesList.append((red.rules[0], red.rules[1], red.score()))
        
    def makeIndexes(self, red, lengthL, lengthR, side, op):
        return red.rules[side].makeIndexes((self.format_index_pref % {'lengthL': lengthL, 'lengthR': lengthR, 'side': side, 'op': op}) + self.format_index_suff)
                        
    def makeOwnIndexes(self, red):
        indexes = []
        for side in [0,1]:
            indexes.extend(self.makeIndexes(red, red.length(0), red.length(1), side, red.rules[side].opBuk(0)))
        return indexes
    
    def extOneStep(self, red, side):
        cols_ext = red.invColsSide(side)
        if not self.amnesic:
            other_side = 1-side
            lengthL = red.length(0)+(1-side)
            lengthR = red.length(1)+side

            rules_ids_other_side = self.lookForRules(self.makeIndexes(red, lengthL, lengthR, other_side, red.rules[other_side].opBuk(0)))
            if len(rules_ids_other_side ) > 0:
#                pdb.set_trace()
                if red.length(side) == 1:
                    rules_ids = self.lookForRules(self.makeIndexes(red, lengthL, lengthR, side, Op(True))) 
                    rules_ids |= self.lookForRules(self.makeIndexes(red, lengthL, lengthR, side, Op(False)))
                else:
                    rules_ids = self.lookForRules(self.makeIndexes(red, lengthL, lengthR, side, red.rules[side].opBuk(0)))

                rules_ids &= rules_ids_other_side
                if len(rules_ids) > 0:
                    
                    # print 'EXTENSIONS-%i------%s <=> %s -------' % (side, red.rules[0].dispIds(),red.rules[1].dispIds())
#                     for i in rules_ids:
#                         print self.rulesList[i][0].dispIds() + '<=>' + self.rulesList[i][1].dispIds() 
#                     print '------------------------'
                    cols_ext = self.colsExtending(rules_ids, side) ## includes already used cols
#             if len(cols_ext) > red.rules[side].length() :
#                 print 'EXCLUDED-%i-------------' % side
#                 print cols_ext
#                 print '------------------------'
        
        return cols_ext   
                
#     def extOneStepFromInitial(self, initialPair, side):
#         cols_ext = set([initialPair[side+1]])
#         nb_cols_own = 1
#         if not self.amnesic:
#             other_side = 1-side
#             lengthL = 1+(1-side)
#             lengthR = 1+side
#             col_side = rule_colX(initialPair[side+1], initialPair[side+3])
#             col_other = rule_colX(initialPair[other_side+1], initialPair[other_side+3])

#             indexes_other_side = [(self.format_index_pref + self.format_index_suff) % {'lengthL': lengthL, 'lengthR': lengthR, 'side': other_side, 'op': -1, 'col': col_other, 'buk': 1} ]
#             indexes_OR = [(self.format_index_pref + self.format_index_suff) % {'lengthL': lengthL, 'lengthR': lengthR, 'side': side, 'op': 1, 'col': col_side, 'buk': 1} ]
#             indexes_AND = [(self.format_index_pref + self.format_index_suff) % {'lengthL': lengthL, 'lengthR': lengthR, 'side': side, 'op': 0, 'col': col_side, 'buk': 1} ]

#             rules_ids_other_side = self.lookForRules(indexes_other_side)
#             if len(rules_ids_other_side ) > 0:
#                 #pdb.set_trace()
#                 rules_ids = self.lookForRules(indexes_OR)
#                 rules_ids |= self.lookForRules(indexes_AND)
#                 rules_ids &= rules_ids_other_side
#                 if len(rules_ids) > 0:
                    
#                    #  print 'EXTENSIONS-%i-----%s--------' % (side, initialPair)
# #                     for i in rules_ids:
# #                         print self.rulesList[i][0].dispIds() + '<=>' + self.rulesList[i][1].dispIds()
# #                     print '------------------------'
                    
#                     cols_ext = self.colsExtending(rules_ids, side) ## includes already used cols
#             # if len(cols_ext) > 1 :
# #                 print 'EXCLUDED-%i-------------' % side
# #                 print cols_ext
# #             print '------------------------'
#         return cols_ext
    
    def initialAvailable(self, initialPairRed):
        return [self.availableMo[0] - self.extOneStep(initialPairRed, 0), \
                self.availableMo[1] - self.extOneStep(initialPairRed, 1)]

        
    def colsExtending(self, rules_ids, side):
        cols = set()
        for idr in rules_ids:
            cols |= self.rulesList[idr][side].invCols()
        return cols  

    def lookForRules(self, indexes_p):
        if len(indexes_p) > 0 and not self.amnesic:
            rule_ids = set([-1])
            id_inds = 0
            while id_inds < len(indexes_p) and self.indexes.has_key(indexes_p[id_inds]) and len(rule_ids) > 0:
                if id_inds ==0 :
                    rule_ids = set(self.indexes[indexes_p[id_inds]])
                else:
                    rule_ids &= self.indexes[indexes_p[id_inds]]
                id_inds +=1
            if id_inds != len(indexes_p):
                rule_ids = set()
            return rule_ids
        else:
            return set()
        
    def update(self, redList):
        for red in redList:
            if not self.amnesic:
                self.add(red)
