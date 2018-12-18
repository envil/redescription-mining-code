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

class DrawerRanges(DrawerBasis):
    
    def update(self, update_trees=True):        
        if self.view.wasKilled():
            return

        if self.isReadyPlot():

            self.clearPlot()
            inter_params = self.getParamsInter()
            vec, vec_dets = self.getVecAndDets(inter_params)
            draw_settings = self.getDrawSettings()

            hunit = 1.
            ranges = vec_dets["ranges"]
            univ_supp = ranges[None]
            Nr = numpy.maximum(len(univ_supp), 1)
            vs = sorted([k for k in ranges.keys() if k is not None])
            for vi, v in enumerate(vs):
                rngs = ranges[v]
                if "values" in rngs: ### Boolean or categorical
                    pass
                else: ### numerical
                    w = float(rngs["maxv"]-rngs["minv"])
                    self.axe.plot([0, 1], [vi, vi], '--', color="#aaaaaa")
                    self.axe.text(0, vi, '%s' % rngs["minv"], color="#333333", ha="left")
                    self.axe.text(1, vi, '%s' % rngs["maxv"], color="#333333", ha="right")
                    self.axe.text(1, vi+.5, 'v%d.%d %s' % (v[0], v[1], rngs["name"]), color="#333333", va="center", ha="left")
                    for rng in rngs["ranges"]:
                        low, high = rng[0]
                        if numpy.isinf(low): low = rngs["minv"]
                        if numpy.isinf(high): high = rngs["maxv"]
                        low, high = (low-rngs["minv"])/w, (high-rngs["minv"])/w
                        h = (hunit*len(rng[-1]))/Nr
                        self.axe.fill([low, low, high, high], [vi, vi+h, vi+h, vi], 'b-', alpha=.6)
                        self.axe.fill([low, low, high, high], [vi+h, vi+hunit, vi+hunit, vi+h], 'r-', alpha=.6)
            corners = (0., 1., 0., 1.+vi, .05, .05)

            self.makeFinish(corners[:4], corners[4:])   
            self.updateEmphasize(review=False)
            self.draw()
            self.setFocus()
        else:
            self.plot_void()      
