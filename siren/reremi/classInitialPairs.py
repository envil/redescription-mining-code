import re, string, pdb
from classRedescription import  Redescription

class InitialPairs:

    def __init__(self):
        self.countdown = -1 
        self.pairs = []

    def reset(self):
        self.countdown = -1 
        del self.pairs[:]

    def __len__(self):
        return len(self.pairs)

    def setCountdown(self, n):
        self.countdown = n

    def getCountdown(self):
        return self.countdown

    def __str__(self):
        return "Initial Pairs %d" % len(self.pairs)

    def add(self, literalL, literalR, scoP): 
        self.pairs((literalL, literalR, scoP))
                
    def pop(self):
        if len(self.pairs) > 0 and self.countdown != 0:
            self.countdown -= 1
            return self.pairs.pop(0)

    def get(self, data):
        pair = self.pop()
        if pair is not None:
            return Redescription.fromInitialPair(pair, data)

class IPoverall(InitialPairs):
    def __init__(self):
        InitialPairs.__init__(self)
        self.pairs = []

    def __str__(self):
        return "Initial Pairs overall %d" % len(self.pairs)

    def add(self, literalL, literalR, scoP): 
        self.pairs((literalL, literalR, scoP))
        self.sorted = False
                
    def pop(self):
        if len(self.pairs) > 0 and self.countdown != 0:
            self.countdown -= 1
            if not self.sorted:
                self._sort()
            return self.pairs.pop()

    def _sort(self):
        self.pairs.sort(key=lambda x: x[2])
        self.sorted = True

class IPalternate(InitialPairs):
    def __init__(self):
        InitialPairs.__init__(self)
        self.pairs_side = [{}, {}]
        self.sorted = False
        self.seen_sides = [set(), set()]
        self.side = 0
        self.nb_pairs = 0

    def reset(self):
        self.countdown = -1 
        del self.pairs[:]
        self.pairs_side = [{}, {}]
        self.sorted = False
        self.seen_sides = [set(), set()]
        self.side = 0
        self.nb_pairs = 0
        
    def __str__(self):
        return "Initial Pairs alternate %d" % len(self.pairs)

    def add(self, literalL, literalR, scoP): 
        self.pairs_side[0].setdefault(literalL.col(), []).append(len(self.pairs))
        self.pairs_side[1].setdefault(literalR.col(), []).append(len(self.pairs))
        self.pairs.append((literalL, literalR, scoP))
        self.sorted = False
        self.nb_pairs += 1
        
    def pop(self):
        if self.nb_pairs > 0 and self.countdown != 0:
            if not self.sorted:
                self._sort()
            potential_cols = set(self.pairs_side[self.side].keys()) - self.seen_sides[self.side]
            if len(potential_cols) == 0:
                self.seen_sides[self.side] = set()
                potential_cols = set(self.pairs_side[self.side].keys())

            col = sorted(potential_cols, key=lambda x: self.pairs[self.pairs_side[self.side][x][-1]][2]).pop()
            pair_id = self.pairs_side[self.side][col].pop()
            if len(self.pairs_side[self.side][col]) == 0:
                del self.pairs_side[self.side][col]
            pair = self.pairs[pair_id]
            assert pair[self.side].col() == col
            self.pairs_side[1-self.side][pair[1-self.side].col()].remove(pair_id)
            if len(self.pairs_side[1-self.side][pair[1-self.side].col()]) == 0:
                del self.pairs_side[1-self.side][pair[1-self.side].col()]
            self.seen_sides[self.side].add(col)
            self.seen_sides[1-self.side].add(pair[1-self.side].col())
            self.side = 1-self.side
            self.countdown -= 1
            self.nb_pairs -= 1
            return pair

    def _sort(self):
        for side in [0,1]:
            for col in self.pairs_side[side].keys():
                self.pairs_side[side][col].sort(key=lambda x: self.pairs[x][2])
        self.sorted = True
