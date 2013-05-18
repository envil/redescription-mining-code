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
from matplotlib.lines import Line2D
from matplotlib.patches import Ellipse

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
        self.hight = {}
        self.map_lines = {}
        self.MapfigMap = plt.figure()

        self.Mapcurr_mapi = 0
        self.MapcanvasMap = FigCanvas(self.mapFrame, -1, self.MapfigMap)
        
        self.MaptoolbarMap = NavigationToolbar(self.MapcanvasMap)

        self.MapfigMap.clear()
        self.axe = self.MapfigMap.add_subplot(111)
        self.gca = plt.gca()

        self.el = Ellipse((2, -1), 0.5, 0.5)
        self.axe.add_patch(self.el)

        self.MapcanvasMap.draw()
            
    def updateMap(self, red = None):
        """ Redraws the map
        """
        if red is not None: # and self.coords_proj is not None:

            draw_settings = self.getDrawSettings()
            scale_p = 0.1

            self.map_lines = {}
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
                    colorse = [draw_settings[osupp[i]]["color_e"] for i in self.selectids]
                    data = [draw_settings[osupp[i]]["pos"] + scale_p*(float(j)/len(self.selectids)-0.5) for j,i in enumerate(self.selectids)]

                    d[colsU[-1]] = data
                    bounds.append([0, 0])

            ttz = []
            cis = range(len(colsU))
            for co in colsU:
                ttz.append(d[co])
            ttx = zip(*ttz)
            for i, ent in enumerate(ttx):
                for e in ent:
                    if e < 0 or e > 1:
                        print i, ent
                tt = plt.plot(cis, ent, color=colorse[i], picker=2)
                self.map_lines[tt[0]] = self.selectids[i]
            for i,bound in enumerate(bounds):
                plt.bar(i-.05, bound[1]-bound[0], 0.1, bound[0], edgecolor='0.3', color='0.7', alpha=0.7, zorder=10)
            m.set_xticks(range(len(colsU)))
            m.set_xticklabels(colsU)
            m.axis([0,len(colsU)-1, 0,1])
            self.updateEmphasize(ParaView.COLHIGH)
            self.MapfigMap.canvas.mpl_connect('pick_event', self.OnPick)
            self.MapcanvasMap.draw()
        return red


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
        self.highl[lid].extend(plt.plot(xs, ys, colhigh, linewidth=1))
        #self.highl[lid].extend(plt.plot(xs, ys, color=draw_settings[osupp[lid]]["color_e"], linewidth=1))


        self.hight[lid] = []
        self.hight[lid].append(plt.annotate('%d' % lid, xy=(xs[-1], ys[-1]),  xycoords='data',
                          xytext=(10, 0), textcoords='offset points', color= draw_settings[osupp[lid]]["color_e"],
                          size=10, va="center", backgroundcolor="#FFFFFF",
                          bbox=dict(boxstyle="round", facecolor="#FFFFFF", ec="none"),
                          arrowprops=dict(arrowstyle="wedge,tail_width=1.",
                                          fc="#FFFFFF", ec="none",
                                          patchA=None,
                                          patchB=self.el,
                                          relpos=(0.2, 0.5),
                                          )
                                      ))
        self.MapcanvasMap.draw()

    def additionalElements(self):
        tmp = []
        tmp.append(self.MaptoolbarMap)
        self.buttons = []
        self.buttons.append({"element": wx.Button(self.mapFrame, size=(80,-1), label="Expand"),
                             "function": self.OnExpand})
        tmp.append(self.buttons[-1]["element"])
        return tmp

    def OnPick(self, event):
        if isinstance(event.artist, Line2D):
            if event.artist in self.map_lines: 
                si = self.map_lines[event.artist]
                self.sendHighlight(si)
                
                # if si in self.high:
                #     self.high.remove(si)
                #     self.clearEmphasize([si])

                # else:
                #     self.high.append(si)
                #     self.emphasizeLine(si)
                #     self.sendHighlight(si, True)

    def sendHighlight(self, lid):
        if self.source_list is not None and self.parent.tabs.has_key(self.source_list):
            self.parent.tabs[self.source_list]["tab"].sendHighlight(self.getId(), lid)
