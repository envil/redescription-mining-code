### TODO check which imports are needed 
import wx
import numpy
import re
# The recommended way to use wx with mpl is with the WXAgg
# backend. 
import matplotlib
#matplotlib.use('WXAgg')
import matplotlib.pyplot as plt
import scipy.spatial.distance

from ..reremi.classQuery import Query
from ..reremi.classSParts import SSetts
from ..reremi.classRedescription import Redescription
from classGView import GView

import pdb

class TDView(GView):

    TID = None
    NBBINS = 20

    def plot_void(self):
        if self.wasKilled():
            return
        self.axe.cla()
        self.axe.plot([r/10.0+0.3 for r in [0,2,4]], [0.5 for r in [0,2,4]], 's', markersize=10, mfc="#DDDDDD", mec="#DDDDDD")
        self.axe.axis([0,1,0,1])
        self.MapcanvasMap.draw()

    def updateMap(self):
        """ Redraws the map
        """
        if self.wasKilled():
            return

        if self.isReadyPlot():
            self.highl = {}
            self.hight = {}
            self.hover_access = [i for (i, v) in enumerate(self.suppABCD) if (v != SSetts.delta or self.getDeltaOn())] 
            
            axxs = self.MapfigMap.get_axes()
            for ax in axxs:
                ax.cla()
                if ax != self.axe:
                    self.MapfigMap.delaxes(ax)
                self.axe.set_position([0.,0.,1.,1.])
            self.makeBackground()   
            draw_settings = self.getDrawSettings()

            ### SELECTED DATA
            selected = self.getUnvizRows()
            # selected = self.parent.dw.getData().selectedRows()
            selp = 0.5
            if self.sld_sel is not None:
                selp = self.sld_sel.GetValue()/100.0

            x0, x1, y0, y1 = self.getAxisLims()
            bx, by = (x1-x0)/100.0, (y1-y0)/100.0
            pick = self.getPickerOn()

            dsetts = draw_settings["default"]
            sz_dots = numpy.ones(len(self.suppABCD))*dsetts["size"]
            draw_indices = range(len(self.suppABCD))

            if self.isSingleVar():
                ccs = self.getQCols()
                ltid = self.getLitTypeId(ccs[0][0], ccs[0][1])
                vec = self.getValVector(ccs[0][0], ccs[0][1])
                cmap, vmin, vmax = (self.getCMap(ltid), numpy.min(vec), numpy.max(vec))
                
                norm = matplotlib.colors.Normalize(vmin=vmin, vmax=vmax, clip=True)
                mapper = matplotlib.cm.ScalarMappable(norm=norm, cmap=cmap)
                ec_dots = numpy.array([mapper.to_rgba(v) for v in vec])
                fc_dots = ec_dots.copy()
                fc_dots[:,-1] = dsetts["alpha"]
                mapper.set_array(vec)

            else:
                mapper = None
                vec = numpy.array(self.suppABCD)
                u, indices = numpy.unique(vec, return_inverse=True)
                ec_clusts = numpy.array([draw_settings[i]["color_e"]+[1.] for i in u])
                ec_dots = ec_clusts[indices]
                fc_clusts = numpy.array([draw_settings[i]["color_f"]+[ draw_settings[i]["alpha"] ] for i in u])
                fc_dots = fc_clusts[indices]

                if self.getDeltaOn():
                    sz_dots[numpy.where(vec==SSetts.delta)[0]] *= 0.5
                else:
                    draw_indices = numpy.where(vec!=SSetts.delta)[0]

            if len(selected) > 0:
                fc_dots[numpy.array(list(selected)), -1] *= selp

            self.dots_draws = {"fc_dots": fc_dots, "ec_dots": ec_dots, "sz_dots": sz_dots}
            if self.plotSimple(): ##  #### NO PICKER, FASTER PLOTTING.
                self.axe.scatter(self.getCoords(0,draw_indices),
                                 self.getCoords(1,draw_indices),
                                 c=fc_dots[draw_indices,:], edgecolors=ec_dots[draw_indices,:],
                                 s=5*sz_dots[draw_indices], marker=dsetts["shape"], zorder=10)
            else:
                for idp in draw_indices:
                        self.drawEntity(idp, self.getPlotColor(idp, "fc"), self.getPlotColor(idp, "ec"),
                                                self.getPlotProp(idp, "sz"), dsetts, picker=pick)
            if mapper is not None:
                ax2 = self.axe #.twinx()
                nb = self.NBBINS
                if ltid == 2:
                    nb = [b-0.5 for b in numpy.unique(vec)]
                    nb.append(nb[-1]+1)
                n, bins, patches = plt.hist(vec, bins=nb)
                sum_h = numpy.max(n)
                norm_h = [ni*0.1*float(x1-x0)/sum_h+0.03*float(x1-x0) for ni in n]
                norm_bins = [(bi-bins[0])/float(bins[-1]-bins[0]) * 0.95*float(y1-y0) + y0 + 0.025*float(y1-y0) for bi in bins]
                left = [norm_bins[i] for i in range(len(n))]
                width = [norm_bins[i+1]-norm_bins[i] for i in range(len(n))]
                colors = [mapper.to_rgba(numpy.mean(bins[i:i+2])) for i in range(len(n))]
                bckc = "white" # dsetts["color_l"]
                ax2.barh(y0, -(0.13*(x1-x0)+bx), y1-y0, x1+0.13*(x1-x0)+2*bx, color=bckc, edgecolor=bckc)
                ax2.barh(left, -numpy.array(norm_h), width, x1+0.13*(x1-x0)+2*bx, color=colors, edgecolor=bckc, linewidth=2)
                ax2.plot([x1+2*bx+0.1*(x1-x0), x1+2*bx+0.1*(x1-x0)], [norm_bins[0], norm_bins[-1]], color=bckc, linewidth=2)
                x1 += 0.13*(x1-x0)+2*bx
                self.axe.set_yticks(norm_bins)
                self.axe.set_yticklabels(bins)
                self.axe.yaxis.tick_right()
                self.axe.tick_params(direction="inout")

                ylbls_ext = self.axe.yaxis.get_ticklabel_extents(self.MapcanvasMap.get_renderer())[1].get_points()
                ratio = ylbls_ext[0,0]/ ylbls_ext[1,0]
                pos1 = self.axe.get_position() # get the original position
                self.axe.set_position([pos1.x0, pos1.y0,  ratio*pos1.width, pos1.height]) # set a new position 
                
            self.makeFinish((x0, x1, y0, y1), (bx, by))   
            self.updateEmphasize(review=False)
            self.MapcanvasMap.draw()
            self.MapfigMap.canvas.SetFocus()
        else:
            self.plot_void()
            
    def makeBackground(self):   
        pass
    def makeFinish(self, xylims, xybs):
	pass

    def plotSimple(self):
        return not self.getPickerOn()
    def isReadyPlot(self):
	return False    
    def getAxisLims(self):
        return (0,1,0,1)

    def getCoordsXY(self, id):
        return (0,0)
    def getCoords(self, axi=None, ids=None):
        return None

    def hoverActive(self):
        return GView.hoverActive(self) and not self.mc.isActive()

    def on_motion(self, event):
        if self.hoverActive() and self.getCoords() is not None:
            lid = None
            if event.inaxes == self.axe:
                lid = self.getLidAt(event.xdata, event.ydata)
                if lid is not None and lid != self.current_hover:
                    if self.current_hover is not None:
                        emph_off = set([self.current_hover])
                    else:
                        emph_off = set()
                    self.emphasizeOnOff(turn_on=set([lid]), turn_off=emph_off, review=True)
                    self.current_hover = lid
            if lid is None and lid != self.current_hover:
                self.emphasizeOnOff(turn_on=set(), turn_off=set([self.current_hover]), review=True)
                self.current_hover = None
            # if self.ri is not None:
            #     self.drs[self.ri].do_motion(event)
