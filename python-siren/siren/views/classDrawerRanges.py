from __future__ import unicode_literals
import wx
### from wx import ALIGN_CENTER, ALL, EXPAND, HORIZONTAL
### from wx import FONTFAMILY_DEFAULT, FONTSTYLE_NORMAL, FONTWEIGHT_NORMAL
### from wx import BoxSizer, Button, Font, NewId
### from wx import EVT_BUTTON, EVT_LEFT_DCLICK

import numpy
# The recommended way to use wx with mpl is with the WXAgg
# backend. 
# import matplotlib
# matplotlib.use('WXAgg')
import matplotlib
matplotlib.use('WXAgg')

import matplotlib.pyplot as plt

from ..reremi.classSParts import SSetts
from ..reremi.classRedescription import Redescription
from classDrawerBasis import DrawerBasis

import pdb

LOG_VALS = [3,4,5]

class DrawerRanges(DrawerBasis):

    BOXH = .8 #66
    RH = .45
    ALPHA_BARS = .25
    WSERIES = 1.1
    HSERIES = 1.
    
    def update(self, update_trees=True):        
        if self.view.wasKilled():
            return

        if self.isReadyPlot():

            self.clearPlot()
            inter_params = self.getParamsInter()
            vec, vec_dets = self.getVecAndDets(inter_params)
            draw_settings = self.getDrawSettings()

            ranges = vec_dets["ranges"]
            def_ticks = [0, .5, 1]
            reds_map = dict(self.getPltDtH().getReds())

            # subsets = [("", None)]
            subsets = [("Baode-30", set([4416, 4417])), ("Baode-49", set([4418, 4419])),
                       ("Lantian-42", set([4420, 4421, 4422, 4423])), ("Lantian-6", set([4424, 4425]))]
            vs = sorted(ranges.keys())
            vs = [(1, 2), (1, 7), (1, 9), (1, 12), (1, 17), (1,18)]
            # vs = [(1, 7), (1, 8), (1, 9), (1, 10), (1, 11)]
            # vs = [(1, 12), (1, 13), (1, 15), (1, 17), (1, 20)]
            # vs = [(1,0), (1,9), (1,4), (1,17)]
            
            xticks, xlbls = [], []
            for si, (slbl, subset) in enumerate(subsets):
                if subset is not None: ## 
                    # self.axe.text(-.2, si*self.HSERIES, '%s (%d)' % (slbl, len(subset)), color="#333333", va="center",ha="center", rotation=90, **self.view.getFontProps())
                    self.axe.text(-.1, si*self.HSERIES, slbl, color="#333333", va="center",ha="center", rotation=90, **self.view.getFontProps())
                if self.ALPHA_BARS > 0:
                    self.draw_bars_subset(ranges, subset, vs, reds_map, si)
                self.draw_ranges_subset(ranges, subset, vs, reds_map, si)

            self.draw_reds_lbls(ranges, subset, vs, reds_map, si+1)
                
            for vi, v in enumerate(vs):
                if v in ranges:
                    self.axe.text(vi*self.WSERIES+.5, (len(subsets)+.5)*self.HSERIES, '%s' % (ranges[v]["vname"]), color="#333333", ha="center", va="bottom", **self.view.getFontProps())
                    ## self.axe.text(-.66, vi-.01, '%s' % ranges[v]["vrng"], color="#333333", ha="center", va="top", **self.view.getFontProps())

        # if rid is not None: #offset_h == 0 and           
        #     acc = ""
        #     if rid in reds_map:
        #         acc = " (%.2f)" % reds_map[rid].getAcc()
        #     self.axe.text(offset_h+high, cx, ' r%s%s' % (rid, acc), color="#333333", ha="left", va="center", alpha=self.ALPHA_BARS, **self.view.getFontProps())

                    
            # corners = (-1.2, wseries*(len(subsets)-1)+1.1, -0.5, len(vs)-.2, .05, .05)
            corners = (-.3, self.WSERIES*len(vs), -0.8, self.HSERIES*(len(subsets)+1), .05, .05)
                      
            # self.axe.set_xticks(xticks)        
            # self.axe.set_xticklabels(xlbls, **self.view.getFontProps())
            self.axe.set_xticks([])        
            self.axe.set_yticks([])        
            
            self.makeFinish(corners[:4], corners[4:])   
            self.updateEmphasize(review=False)
            self.draw()
            self.setFocus()
        else:
            self.plot_void()      


    def draw_reds_lbls(self, ranges, subset_rows=None, vs=None, reds_map={}, si=0):
        offset_v = si*self.HSERIES
        if vs is None:
            vs = sorted(ranges.keys())
        if subset_rows is None:            
            Nr =  self.getParentData().nbRows()
        else:
            Nr = len(subset_rows)
        if Nr < 1:
            Nr = 1

        max_rng_nb = numpy.max([len(rngs["rids"]) for k,rngs in ranges.items()])
        box_h = self.BOXH
        wunit = box_h/max_rng_nb
        wh = self.RH*wunit

        for vi, v in enumerate(vs):
            offset_h = vi*self.WSERIES
            if v not in ranges:
                continue
            rngs = ranges[v]
            
            c0 = offset_v - ((len(rngs["rids"])-1)*wunit)/2.                    
            for rni, rng in enumerate(rngs["ranges"]):
                cx = c0+rni*wunit
                rid = rng[1]
                if rid is not None: #offset_h == 0 and           
                    acc = ""
                    if rid in reds_map:
                        acc = " J=%.2f" % reds_map[rid].getAcc()
                    self.axe.text(offset_h+0.5, cx, 'r%s%s' % (rid, acc), color="#333333", ha="center", va="center", alpha=self.ALPHA_BARS, **self.view.getFontProps())
                
            
    def draw_bars_subset(self, ranges, subset_rows=None, vs=None, reds_map={}, si=0):
        offset_v = si*self.HSERIES
        if vs is None:
            vs = sorted(ranges.keys())
        if subset_rows is None:            
            Nr =  self.getParentData().nbRows()
        else:
            Nr = len(subset_rows)
        if Nr < 1:
            Nr = 1

        max_rng_nb = numpy.max([len(rngs["rids"]) for k,rngs in ranges.items()])
        box_h = self.BOXH
        wunit = .5*box_h/max_rng_nb
        wh = self.RH*wunit

        for vi, v in enumerate(vs):
            offset_h = vi*self.WSERIES
            if v not in ranges:
                continue
            rngs = ranges[v]
            self.axe.plot([offset_h+0, offset_h+0, offset_h+1, offset_h+1, offset_h+0],
                          [offset_v-.5*box_h, offset_v+.5*box_h, offset_v+.5*box_h, offset_v-.5*box_h, offset_v-.5*box_h], '-', color="#aaaaaa")
            
            c0 = offset_v - .25*box_h - ((len(rngs["rids"])-1)*wunit)/2.                    
            if rngs.get("values") is not None: ### Boolean or categorical
                tck_lbls = rngs["values"]
                nb_vals = len(rngs["values"])
                w = 1./nb_vals

                for rni, rng in enumerate(rngs["ranges"]):
                    for point in rng[0]:
                        pi = rngs["map_values"][point]                    
                        # rni = rng[1]
                        cx = c0+rni*wunit
                        low, high = pi*w, (pi+1)*w
                        self.plot_rng(high, low, cx, wh, offset_h, Nr, rng[1], rng[-1], subset_rows, reds_map)
                        
            else: ### numerical
                tck_lbls = [rr["v"] for rr in rngs["splits"]]

                for rni, rng in enumerate(rngs["ranges"]):
                    cx = c0+rni*wunit
                    ttk = "ticks"
                    if vi in LOG_VALS and "log_ticks" in rngs:
                        ttk = "log_ticks"
                    low = rngs[ttk][rngs["map_values"][rng[0][0]]]
                    high = rngs[ttk][rngs["map_values"][rng[0][1]]]
                    self.plot_rng(high, low, cx, wh, offset_h, Nr, rng[1], rng[-1], subset_rows, reds_map)

            # for ti, t in enumerate(rngs["ticks"]):
            #     self.axe.text(offset_h+t, offset_v-.5*box_h, '%s' % tck_lbls[ti], color="#333333", ha="center", va="top", **self.view.getFontProps())


    def plot_rng(self, high, low, cx, wh, offset_h, Nr, rid, rows_in, subset_rows=None, reds_map={}):
        if subset_rows is not None:
            rows_in = subset_rows.intersection(rows_in)
        nb_rows_in =  len(rows_in)

        if rid is not None and rid in reds_map:
            wh *= reds_map[rid].getAcc()
        
        bottom, top = (cx-wh, cx+wh)                       
        if nb_rows_in == 0:
            self.axe.fill([offset_h+low, offset_h+low, offset_h+high, offset_h+high],
                          [bottom, top, top, bottom], "#aaaaaa", linewidth=.8, edgecolor="#aaaaaa", alpha=self.ALPHA_BARS)
        elif nb_rows_in == Nr:
            self.axe.fill([offset_h+low, offset_h+low, offset_h+high, offset_h+high],
                          [bottom, top, top, bottom], "#222222", linewidth=.8, edgecolor="#222222", alpha=self.ALPHA_BARS)
        else:
        #     mid = cx+((2.*nb_rows_in)/Nr-1)*wh
        #     self.axe.fill([offset_h+low, offset_h+low, offset_h+high, offset_h+high],
        #                   [mid, top, top, mid], "#aaaaaa", linewidth=0, alpha=self.ALPHA_BARS)
        #     self.axe.fill([offset_h+low, offset_h+low, offset_h+high, offset_h+high],
        #                   [bottom, mid, mid, bottom], "#222222", linewidth=0, alpha=self.ALPHA_BARS)
            self.axe.fill([offset_h+low, offset_h+low, offset_h+high, offset_h+high],
                          [bottom, top, top, bottom], "#FFFFFF", linewidth=.8, edgecolor="#333333", alpha=self.ALPHA_BARS)

            
        # if rid is not None: #offset_h == 0 and           
        #     acc = ""
        #     if rid in reds_map:
        #         acc = " (%.2f)" % reds_map[rid].getAcc()
        #     self.axe.text(offset_h+high, cx, ' r%s%s' % (rid, acc), color="#333333", ha="left", va="center", alpha=self.ALPHA_BARS, **self.view.getFontProps())

        
    def draw_ranges_subset(self, ranges, subset_rows=None, vs=None, reds_map={}, si=0):
        offset_v = si*self.HSERIES
        if vs is None:
            vs = sorted(ranges.keys())
        if subset_rows is None:            
            Nr =  self.getParentData().nbRows()
        else:
            Nr = len(subset_rows)
        if Nr < 1:
            Nr = 1

        max_rng_nb = numpy.max([len(rngs["rids"]) for k,rngs in ranges.items()])
        box_h = self.BOXH
        wunit = box_h/max_rng_nb
        wh = self.RH*wunit

        for vi, v in enumerate(vs):
            offset_h = vi*self.WSERIES
            if v not in ranges:
                continue
            rngs = ranges[v]
            self.axe.plot([offset_h+0, offset_h+0, offset_h+1, offset_h+1, offset_h+0],
                          [offset_v-.5*box_h, offset_v+.5*box_h, offset_v+.5*box_h, offset_v-.5*box_h, offset_v-.5*box_h], '-', color="#aaaaaa")
            # self.axe.plot([offset_h+0, offset_h+1], [offset_v, offset_v], ':', color="#aaaaaa")
            
            if rngs.get("values") is not None: ### Boolean or categorical
                tck_lbls = rngs["values"]
                last = 0
            else:
                tck_lbls = [rr["v"] for rr in rngs["splits"]]
                last = 1

            xs, ys = [], []
            for si in range(len(rngs["splits"])-last):
                h = 0.
                for rri in rngs["splits"][si]["ids"]:
                    red = reds_map[rngs["ranges"][rri][1]]
                    acc = red.getAcc()
                    rows_in = rngs["ranges"][rri][-1]
                    if subset_rows is not None:
                        rows_in = subset_rows.intersection(rows_in)
                    if len(rows_in) == Nr:
                        fsupp = .5
                    elif len(rows_in) == 0:
                        fsupp = -.5
                    else:
                        fsupp = 0.
                    # fsupp = float(len(rows_in))/Nr-.5
                    h += fsupp*acc

                if rngs.get("values") is not None: ### Boolean or categorical
                    xs.extend([rngs["splits"][si]["v"]-.5, rngs["splits"][si]["v"]+.5])
                else:
                    xs.extend([rngs["splits"][si]["v"], rngs["splits"][si+1]["v"]])
                ys.extend([h, h])

            xs = numpy.array(xs)
            ys = numpy.array(ys)
            if vi in LOG_VALS and "log_ticks" in rngs:
                xs = numpy.log10(xs-numpy.min(xs)+1)
            minv, maxv = numpy.min(xs), numpy.max(xs)
            xs = (xs-minv)/float(maxv-minv)
            ys = ys/float(len(rngs["ranges"]))
            # if numpy.max(numpy.abs(ys)) > 0:
            #     ys = ys/(numpy.max(numpy.abs(ys)))

            xxs = offset_h+xs
            y1s = offset_v+.25*box_h+.5*box_h*ys
            y2s = offset_v*numpy.ones(ys.shape)+.25*box_h
            self.axe.fill_between(xxs, y1s, y2s, where=y2s >= y1s, facecolor='#aaaaaa', linewidth=0, alpha=self.ALPHA_BARS)
            self.axe.fill_between(xxs, y1s, y2s, where=y2s <= y1s, facecolor='#222222', linewidth=0, alpha=self.ALPHA_BARS)
            self.axe.plot(xxs, y1s, "#000000") 

            if offset_v == 0:
                ttk = "ticks"
                if vi in LOG_VALS and "log_ticks" in rngs:
                    ttk = "log_ticks"
                for ti, t in enumerate(ranges[v][ttk]):
                    self.axe.plot([offset_h+t, offset_h+t], [offset_v-.5*box_h-.01, offset_v-.5*box_h+.01], '-', color='#333333')
                    self.axe.text(offset_h+t, offset_v-.5*box_h-.02, '%s' % tck_lbls[ti], color="#333333", ha="center", va="top", rotation=90, **self.view.getFontProps())
