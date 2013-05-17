### TODO check which imports are needed 
import wx
import numpy as np
# The recommended way to use wx with mpl is with the WXAgg
# backend. 
import matplotlib
#matplotlib.use('WXAgg')
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
        self.highl = {}
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
            self.selectids, self.opids = red.supports().sampleRows(0.1, 100)
#            self.selectids, opids = red.supports().sampleRows(2, 2)
#            self.selectids, opids = red.supports().sampleRows(1, 100)
            d = {}
            topP = red.supports().topPart()+1
            osupp = red.supports().getVectorABCD()
            d['class'] = [osupp[i] for i in self.selectids]
            colorsl =  [draw_settings[i]["color_e"] for i in sorted(self.opids.keys())]
            bounds = []
            colsU = []
            # for side,pref in [(0,"RHS:"), (1,"LHS:")]:
            for side,pref in [(0,""), (1,"")]:
                for lit in red.queries[side].listLiterals():
                    ti = lit.sampleBounds(self.parent.dw.getDataCols(side), self.parent.details['names'][side], self.selectids, scale_p)
                    colsU.append(pref+ti["text"])
                    d[colsU[-1]] = ti["data"]
                    bounds.append(ti["bounds"])
                if side == 0:
                    colsU.append('--')
                    data = [draw_settings[osupp[i]]["pos"] + scale_p*(float(j)/len(self.selectids)-0.5) for j,i in enumerate(self.selectids)]

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

    def clearEmphasize(self, lids = None):
        if lids is None:
            lids = self.highl.keys()
        for lid in lids:
            if self.highl.has_key(lid):
                while len(self.highl[lid]) > 0:
                    self.gca.axes.lines.remove(self.highl[lid].pop())
                del self.highl[lid]
        self.MapcanvasMap.draw()

    def emphasizeLine(self, lid, colhigh='#FFFF00'):
        if self.highl.has_key(lid):
        #     self.clearEmphasize([lid])
            return

        draw_settings = self.getDrawSettings()
        scale_p = 0.1
        m = self.axe
        red = Redescription.fromQueriesPair(self.queries, self.parent.dw.data)
        osupp = red.supports().getVectorABCD()

        pp = (self.opids[osupp[lid]][0] + (self.opids[osupp[lid]][1] - self.opids[osupp[lid]][0])/2.0)/len(self.selectids) 
        xs, ys = [], []
        for side,pref in [(0,""), (1,"")]:
            for lit in red.queries[side].listLiterals():
                ti = lit.sampleBounds(self.parent.dw.getDataCols(side), self.parent.details['names'][side], [lid],  scale_p, pos=pp)
                xs.append(len(ys))
                ys.append(ti["data"][0])
            if side == 0:
                xs.append(len(ys))
                ys.append(draw_settings[osupp[lid]]["pos"]  + scale_p*(pp-0.5) )

        self.highl[lid] = []
        self.highl[lid].extend(plt.plot(xs, ys, colhigh, linewidth=2))
        self.highl[lid].extend(plt.plot(xs, ys, color=draw_settings[osupp[lid]]["color_e"], linewidth=1))
        self.MapcanvasMap.draw()

    def additionalElements(self):
        tmp = []
        tmp.append(self.MaptoolbarMap)
        self.buttons = []
        self.buttons.append({"element": wx.Button(self.mapFrame, size=(80,-1), label="Expand"),
                             "function": self.OnExpand})
        tmp.append(self.buttons[-1]["element"])
        return tmp
