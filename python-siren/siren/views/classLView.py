import wx
import numpy
# The recommended way to use wx with mpl is with the WXAgg backend. 
# import matplotlib
# matplotlib.use('WXAgg')
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.lines import Line2D
from matplotlib.patches import Polygon
from matplotlib.path import Path

from classBasisView import BasisView, CustToolbar

from ..reremi.classSParts import SSetts
from ..reremi.classRedescription import Redescription

### updateHist moved to CtrlTable

import pdb


class LView(BasisView):

    
    TID = "L"
    SDESC = "LViz"
    ordN = 0
    title_str = "List View"
    geo = False
    typesI = "r"

    
    @classmethod
    def suitableView(tcl, geo=False, what=None, tabT=None):
        return tabT is None or tabT in tcl.typesI

    def __init__(self, parent, vid, more=None):
        self.initVars(parent, vid, more)
        self.reds = {}
        self.srids = []
        self.initView()
        
    def getReds(self):
        ### the actual queries, not copies, to test, etc. not for modifications
        return self.reds

    def refresh(self):
        self.autoShowSplitsBoxes()
        self.updateMap()
        if self.isIntab():
            self._SetSize()

    def setCurrent(self, reds_map):
        self.reds = dict(reds_map)
        self.srids = [rid for (rid, red) in reds_map]
        pass
     
