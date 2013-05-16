### TODO check which imports are needed 
import wx
import numpy as np
# The recommended way to use wx with mpl is with the WXAgg
# backend. 
import matplotlib
matplotlib.use('WXAgg')
import matplotlib.pyplot as plt
from mpl_toolkits.basemap import Basemap
from matplotlib.backends.backend_wxagg import \
    FigureCanvasWxAgg as FigCanvas, \
    NavigationToolbar2WxAgg as NavigationToolbar

from pandas import read_csv
from pandas import DataFrame
from pandas.tools.plotting import parallel_coordinates

from reremi.classQuery import Query
from reremi.classSParts import SParts
from reremi.classRedescription import Redescription
from classGView import GView

import pdb

class ParaView(GView):

    TID = "PC"
    
    def getId(self):
        return (ParaView.TID, self.vid)
        
    def drawMap(self):
        """ Draws the map
        """
        self.MapfigMap = plt.figure()

        self.Mapcurr_mapi = 0
        self.MapcanvasMap = FigCanvas(self.mapFrame, -1, self.MapfigMap)
        
        self.MaptoolbarMap = NavigationToolbar(self.MapcanvasMap)

        self.MapfigMap.clear()
        self.axe = self.MapfigMap.add_subplot(111)
        self.gca = plt.gca()
        self.MapcanvasMap.draw()
            
    def updateMap(self, red = None):
        """ Redraws the map
        """
        if red is not None: # and self.coords_proj is not None:

            draw_settings = self.getDrawSettings()
            scale_p = 0.1

            m = self.axe
            m.cla()
            selectids, opids = red.supports().sampleRows(0.1, 100)
#            selectids, opids = red.supports().sampleRows(2, 2)
#            selectids, opids = red.supports().sampleRows(1, 100)
            d = {}
            topP = red.supports().topPart()+1
            osupp = red.supports().getVectorABCD()
            d['class'] = [osupp[i] for i in selectids]
            colorsl =  [draw_settings[i]["color_e"] for i in sorted(opids)]
            bounds = []
            colsU = []
            # for side,pref in [(0,"RHS:"), (1,"LHS:")]:
            for side,pref in [(0,""), (1,"")]:
                for lit in red.queries[side].listLiterals():
                    ti = lit.sampleBounds(self.parent.dw.getDataCols(side), self.parent.details['names'][side], selectids)
                    colsU.append(pref+ti["text"])
                    d[colsU[-1]] = ti["data"]
                    bounds.append(ti["bounds"])
                if side == 0:
                    colsU.append('--')
                    data = [draw_settings[osupp[i]]["pos"] + scale_p*(float(j)/len(selectids)-0.5) for j,i in enumerate(selectids)]

                    d[colsU[-1]] = data
                    bounds.append([0, 0])
            data = DataFrame(d)
            parallel_coordinates(data, 'class', ax=m, cols=colsU, colors=colorsl, alpha=0.6, zorder=1)
            for i,bound in enumerate(bounds):
                plt.axvspan(i-.05, i+.05, bound[0], bound[1], facecolor='0.5', alpha=0.5, zorder=10)
            m.set_yticklabels([], visible =False)
            m.legend().set_visible(False)
            self.MapcanvasMap.draw()

        return red
