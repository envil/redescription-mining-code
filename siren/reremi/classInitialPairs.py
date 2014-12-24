import re, string, pdb
from classRedescription import  Redescription
from classQuery import  Literal, Query

class InitialPairs:

    def __init__(self):
        self.countdown = -1 
        self.pairs = []
        self.pstore = None

    def setStore(self, pstore):
        if len(pstore) > 0:
            self.pstore = pstore 

    def getStore(self):
        return self.pstore

    def store(self, filename):
        with open(filename, "w") as f:
            for p in self.pairs:
                f.write("%s\t%s\t%f\n" % (p[0], p[1], p[2]))

    def load(self, filename):
        with open(filename) as f:
            for line in f:
                parts = line.strip().split("\t")
                if len(parts) == 3:
                    try:
                        self.add(Literal.parse(parts[0]), Literal.parse(parts[1]), float(parts[2]))
                    except:
                        pass

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
        self.pairs.append((literalL, literalR, scoP))
                
    def pop(self, cond=None):
        if len(self.pairs) > 0 and self.countdown != 0:
            tt = self.pairs.pop(0)
            if cond is not None:
                while not cond(tt) and len(self.pairs) > 0:
                    tt = self.pairs.pop(0)
                if len(self.pairs) == 0:
                    return
            self.countdown -= 1
            return tt

    def get(self, data, cond=None):
        pair = self.pop(cond)
        if pair is not None:
            return Redescription.fromInitialPair(pair, data)

class IPoverall(InitialPairs):
    def __init__(self):
        InitialPairs.__init__(self)
        self.pairs = []

    def __str__(self):
        return "Initial Pairs overall %d" % len(self.pairs)

    def add(self, literalL, literalR, scoP): 
        self.pairs.append((literalL, literalR, scoP))
        self.sorted = False
                
    def pop(self, cond=None):
        if len(self.pairs) > 0 and self.countdown != 0:
            if not self.sorted:
                self._sort()
            tt = self.pairs.pop()
            if cond is not None:
                while not cond(tt) and len(self.pairs) > 0:
                    tt = self.pairs.pop(0)
                if len(self.pairs) == 0:
                    return
            self.countdown -= 1
            return tt

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

    def pop(self, cond=None):
        if self.countdown != 0:
            tt = self.popD()
            if cond is not None:
                while tt is not None and not cond(tt):
                    tt = self.popD()
                if tt is None:
                    return
            self.countdown -= 1
            return tt
        
    def popD(self):
        if self.nb_pairs > 0:
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
            self.nb_pairs -= 1
            return pair

    def _sort(self):
        for side in [0,1]:
            for col in self.pairs_side[side].keys():
                self.pairs_side[side][col].sort(key=lambda x: self.pairs[x][2])
        self.sorted = True


class IPsingle(InitialPairs):
    def __init__(self):
        InitialPairs.__init__(self)
        self.pairs = []
        self.psst = {}
        self.nb_pairs = 0

    def __str__(self):
        return "Initial Pairs single %d" % len(self.pairs)

    def add(self, literalL, literalR, scoP): 
        if (literalL.col(), 0) in self.psst:
            self.psst[(literalL.col(), 0)].add(literalL)
        else:
            self.psst[(literalL.col(), 0)] = set([literalL])
        if (literalR.col(), 1) in self.psst:
            self.psst[(literalR.col(), 1)].add(literalR)
        else:
            self.psst[(literalR.col(), 1)] = set([literalR])
        self.sorted = False
                
    def pop(self, cond=None):
        if not self.sorted:
            self._sort()
        if len(self.pairs) > 0 and self.countdown != 0:
            tt = self.pairs.pop(0)
            if cond is not None:
                while not cond(tt) and len(self.pairs) > 0:
                    tt = self.pairs.pop(0)
                if len(self.pairs) == 0:
                    return
            return tt

    def _sort(self):
        tt = sorted(self.psst.keys())
        first_turn = True
        count = self.countdown
        self.sorted = True
        while len(tt) > 0:
            i = 0
            while i < len(tt):
                if not first_turn:
                    count -= 1
                    if count == 0:
                        return
                self.pairs.append((tt[i][1], self.psst[tt[i]].pop()))
                if len(self.psst[tt[i]]) == 0:
                    tt.pop(i)
                else:
                    i+=1
            first_turn = False

    def get(self, data, cond=None):
        pair = self.pop() #cond)
        if pair is not None:
            queries = [Query(), Query()]
            queries[pair[0]].extend(True, pair[1])
            return Redescription.fromQueriesPair(queries, data)
