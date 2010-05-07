from classRedescription import *

class RedescriptionsDraft:
    
    def __init__(self, ncapacity=float('Inf')):
        self.capacity = ncapacity
        self.draft = []

    def count(self):
        return len(self.draft)
    
    def __len__(self):
        return len(self.draft)
    
    def isFull(self):
        return len(self) >= self.capacity

    def redescriptions(self):
        return self.draft
    
    def get(self, id):
        if id <  self.count():
            return self.draft[id]
        
    def cut(self, maxNb=-1, direction=0):
        if maxNb != -1 and maxNb < self.count():
            self.draft = self.draft[:self.cutIndex(maxNb, direction)]

    def cutIndex(self, index=1, direction=1):
        if index >= self.count():
            index = self.count()
        elif index <= 0:
            index = 0
        elif direction > 0 :
            while index+1 <= self.count() and self.draft[index].equivalent(self.draft[index-1]):
                index+=1
        elif direction < 0 :
            while index > 0  and self.draft[index].equivalent(self.draft[index-1]):
                index-=1
        return index

    def insert(self, redescription):
        i = 0
        while i < self.count() and self.draft[i].score() > redescription.score():
            i += 1
        if i < self.capacity :
            self.draft.insert(i,redescription)
            self.draft= self.draft[:self.cutIndex(self.capacity)]

    def update(self, redescriptionSet):
        if len(redescriptionSet) > 0:
            redescriptionList = list(redescriptionSet)
            redescriptionList.sort(reverse=True)
            if self.count() == 0:
                self.draft = redescriptionList
            else:
                to_insert = 0
                place = 0
                while to_insert < len(redescriptionList) and place < self.count() and place < self.capacity:
                    if redescriptionList[to_insert] > self.draft[place] :
                        self.draft.insert(place, redescriptionList[to_insert])
                        to_insert += 1
                    place += 1
                if self.capacity > self.count() and to_insert < len(redescriptionList):
                    self.draft.extend(redescriptionList[to_insert:])
            self.draft = self.draft[:self.cutIndex(self.capacity)]

    def updateCheckOneSideIdentical(self, redescriptionList, max_iden=0):
        insertedIds = {}
        if len(redescriptionList) > 0 and self.capacity > 0:
            redescriptionList.sort(reverse=True)
            
            to_insert = 0
            place = -1
            compare = 0
            count_iden = [0, 0]
            while to_insert < len(redescriptionList) and ( place < self.capacity or redescriptionList[to_insert].equivalent(self.draft[place])):
       
                if compare == self.count(): ## if the end has been reached, simply append and go to next one
                    if place == -1:
                        self.draft.append(redescriptionList[to_insert])
                        insertedIds[to_insert] = len(self.draft)
                        
                    compare = -1
                    to_insert += 1
                    count_iden = [0, 0]
                    place = -1
                elif redescriptionList[to_insert] == self.draft[compare]: # FOUND IDENTICAL, SHOULD ONLY HAPPEN WITH AMNESIC
                    compare = -1
                    to_insert += 1
                elif place== -1 and redescriptionList[to_insert] >= self.draft[compare] : ## place has been found, insert
                    place = compare
                    self.draft.insert(place, redescriptionList[to_insert])
                    insertedIds[to_insert] = place
                elif redescriptionList[to_insert].oneSideIdentical(self.draft[compare], count_iden, max_iden) :
                    #pdb.set_trace()
                    if not redescriptionList[to_insert].equivalent(self.draft[compare]) : ## if one side identical is found,
                        if place >= 0 and place < compare : ## if it is further than the current insert,
                            ## remove compared, go to next one continue, might find other side identical ...
                            self.draft.pop(compare)
                            compare -= 1
                        else: ## else don't insert current, go to next one
                            compare = -1
                            to_insert += 1
                            count_iden = [0, 0]
                            place = -1
                compare += 1
                    
            if self.capacity < self.count():
                self.draft = self.draft[:self.cutIndex(self.capacity)]
        return insertedIds

#     def updateCheckSubsum(self, redescriptionList):          
#         if self.count() >= 2:
#             current = self.count()-1
#             comp_to = current - 1
#             while current >= 1:
#                 while comp_to >= 0:
#                     den0 = Rule.denominator(self.draft[-1].rules[0], self.draft[comp_to].rules[0])
#                     den1 = Rule.denominator(self.draft[-1].rules[0], self.draft[comp_to].rules[0])
#                     if abs(Redescription.compare(self.draft[-1], self.draft[comp_to])) != Redescription.diff_indexes \
#                            and (den0.length() == self.draft[-1].length(0) or  den1.length() == self.draft[-1].length(1) ):
#                         self.draft.pop(current)
#                         current -=1 
#                         comp_to = current -1
#                     else:
#                         comp_to -= 1
#                 current -=1 
#                 comp_to = current - 1

    def nextGeneration(self, functFinalOK):
        nextGen = []
        i = 0
        while i < len(self.draft):
            if self.draft[i].nbAvailableCols() > 0:
                nextGen.append(self.draft.pop(i))
            elif not functFinalOK(self.draft[i]):
                self.draft.pop(i)
            else:
                i += 1
        return nextGen 

    def __str__(self):
        dsp = 'Redescription draft (%i/%s):\n' % (self.count(), self.capacity)
        for i in self.draft :
            dsp += '%s\n' %i
        return dsp

    def disp(self):
        dsp = 'Redescription draft (%i/%s):\n' % (self.count(), self.capacity)
        for i in self.draft :
            dsp += '%s\n' %i.disp()
        return dsp
