import pdb

class Charbon:
    name = "-"
    def getAlgoName(self):
        return self.name

    def __init__(self, constraints):
        ### For use with no missing values
        self.constraints = constraints


class CharbonTree(Charbon):

    name = "T"
    def isTreeBased(self):
        return True
    def handlesMiss(self):
        return False

    ### def getTreeCandidates(self, side, data, red)

class CharbonGreedy(Charbon):

    name = "G"

    def isTreeBased(self):
        return False
    def handlesMiss(self):
        return False
