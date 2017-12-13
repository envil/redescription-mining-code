import numpy
import wx
### from wx import ALIGN_CENTER, ALL, EXPAND, HORIZONTAL
### from wx import FONTFAMILY_DEFAULT, FONTSTYLE_NORMAL, FONTWEIGHT_NORMAL
### from wx import BoxSizer, Button, Font, NewId
### from wx import EVT_BUTTON, EVT_LEFT_DCLICK

# The recommended way to use wx with mpl is with the WXAgg
# backend. 

from ..reremi.classSParts import SSetts
from classGView import GView

import matplotlib
# matplotlib.use('WXAgg')

import matplotlib.pyplot as plt
import matplotlib.colors

import pdb

class TDView(GView):

    TID = None
    NBBINS = 20
    
    def updateMap(self):
        """ Redraws the map
        """
        if self.wasKilled():
            return

        if self.isReadyPlot():

            self.clearPlot()

            self.makeBackground()   
            draw_settings = self.getDrawSettings()

            ### SELECTED DATA
            selected = self.getUnvizRows()
            # selected = self.getParentData().selectedRows()
            selp = 0.5
            if self.sld_sel is not None:
                selp = self.sld_sel.GetValue()/100.0

            x0, x1, y0, y1 = self.getAxisLims()
            bx, by = (x1-x0)/100.0, (y1-y0)/100.0
            corners = (x0, x1, y0, y1, bx, by)
            
            vec, vec_dets = self.getValVec()
            
            if self.isSingleVar():
                self.dots_draws, mapper = self.prepareSingleVarDots(vec, vec_dets, draw_settings, delta_on=self.getDeltaOn())

            else:
                self.dots_draws = self.prepareEntitiesDots(vec, vec_dets, draw_settings, delta_on=self.getDeltaOn())
                mapper = None
                
            if len(selected) > 0:
                self.dots_draws["fc_dots"][numpy.array(list(selected)), -1] *= selp
                self.dots_draws["ec_dots"][numpy.array(list(selected)), -1] *= selp


            draw_indices = numpy.where(self.dots_draws["draw_dots"])[0]
            # print draw_indices.shape[0], "to", draw_indices.shape[0]/4
            # draw_indices = numpy.random.choice(draw_indices, draw_indices.shape[0]/4)

            ###########################
            ###########################
            if self.plotSimple(): ##  #### NO PICKER, FASTER PLOTTING.
                self.plotDotsSimple(self.axe, self.dots_draws, draw_indices, draw_settings)
            else:
                self.plotDotsPoly(self.axe, self.dots_draws, draw_indices, draw_settings)

            if mapper is not None:
                corners = self.plotMapperHist(self.axe, vec, vec_dets, mapper, self.NBBINS, corners)
                
            ###########################
            ###########################
            self.makeFinish(corners[:4], corners[4:])   
            self.updateEmphasize(review=False)
            self.MapcanvasMap.draw()
            self.MapfigMap.canvas.SetFocus()
        else:
            self.plot_void()      

    def getCanvasConnections(self):
        return [("MASK", None),
                ("key_press_event", self.key_press_callback),
                ("button_release_event", self.on_click),
                ("motion_notify_event", self.on_motion)]
            
    def additionalBinds(self):
        self.MapredMapQ[0].Bind(wx.EVT_TEXT_ENTER, self.OnEditQuery)
        self.MapredMapQ[1].Bind(wx.EVT_TEXT_ENTER, self.OnEditQuery)
        for button in self.buttons:
            button["element"].Bind(wx.EVT_BUTTON, button["function"])
        self.sld_sel.Bind(wx.EVT_SCROLL_THUMBRELEASE, self.OnSlide)
        ##self.sld_sel.Bind(wx.EVT_SCROLL_CHANGED, self.OnSlide)

    def OnSlide(self, event):
        self.updateMap()
    
    def isReadyPlot(self):
        return False
    
    def hoverActive(self):
        return GView.hoverActive(self) and not self.mc.isActive()
    def inCapture(self, event):
        return self.getCoords() is not None and event.inaxes == self.axe
