### TODO check which imports are needed 
import wx
import numpy as np
# The recommended way to use wx with mpl is with the WXAgg
# backend. 
import matplotlib
#matplotlib.use('WXAgg')
import matplotlib.pyplot as plt
import scipy.spatial.distance
import scipy.cluster
from matplotlib.backends.backend_wxagg import \
    FigureCanvasWxAgg as FigCanvas, \
    NavigationToolbar2WxAgg as NavigationToolbar
from matplotlib.lines import Line2D
from matplotlib.patches import Ellipse
import itertools

from reremi.classQuery import Query
from reremi.classRedescription import Redescription
from reremi.classData import BoolColM, CatColM, NumColM
from classGView import GView
import toolsMath

import pdb

class DraggableResizeableRectangle:
    # draggable rectangle with the animation blit techniques; see
    # http://www.scipy.org/Cookbook/Matplotlib/Animations

    """
    Draggable and resizeable rectangle with the animation blit techniques.
    Based on example code at
http://matplotlib.sourceforge.net/users/event_handling.html
    If *allow_resize* is *True* the recatngle can be resized by dragging its
    lines. *border_tol* specifies how close the pointer has to be to a line for
    the drag to be considered a resize operation. Dragging is still possible by
    clicking the interior of the rectangle. *fixed_aspect_ratio* determines if
    the recatngle keeps its aspect ratio during resize operations.
    """
    lock = None  # only one can be animated at a time
    def __init__(self, rect, border_tol=.15, rid=None, callback=None):
        self.callback = callback
        self.rid = rid
        self.rect = rect
        self.border_tol = border_tol
        self.press = None
        self.background = None

    def do_press(self, event):
        """on button press we will see if the mouse is over us and store some 
data"""
        #print 'event contains', self.rect.xy
        x0, y0 = self.rect.xy
        w0, h0 = self.rect.get_width(), self.rect.get_height()
        aspect_ratio = np.true_divide(w0, h0)
        self.press = x0, y0, w0, h0, aspect_ratio, event.xdata, event.ydata

        # draw everything but the selected rectangle and store the pixel buffer
        canvas = self.rect.figure.canvas
        axes = self.rect.axes
        self.rect.set_animated(True)
        canvas.draw()
        self.background = canvas.copy_from_bbox(self.rect.axes.bbox)

        # now redraw just the rectangle
        axes.draw_artist(self.rect)

        # and blit just the redrawn area
        canvas.blit(axes.bbox)

    def do_motion(self, event):
        """on motion we will move the rect if the mouse is over us"""
        x0, y0, w0, h0, aspect_ratio, xpress, ypress = self.press
        self.dx = event.xdata - xpress
        self.dy = event.ydata - ypress
        #self.rect.set_x(x0+dx)
        #self.rect.set_y(y0+dy)

        self.update_rect()

        canvas = self.rect.figure.canvas
        axes = self.rect.axes
        # restore the background region
        canvas.restore_region(self.background)

        # redraw just the current rectangle
        axes.draw_artist(self.rect)

        # blit just the redrawn area
        canvas.blit(axes.bbox)

    def contains(self, event):
        return self.rect.contains(event)
    
    def do_release(self, event):
        """on release we reset the press data"""
        self.press = None
        if self.callback is not None:
            self.callback(self.rid, self.rect)

        # turn off the rect animation property and reset the background
        self.rect.set_animated(False)
        self.background = None

        # redraw the full figure
        self.rect.figure.canvas.draw()

    def update_rect(self):
        x0, y0, w0, h0, aspect_ratio, xpress, ypress = self.press
        dx, dy = self.dx, self.dy
        bt = self.border_tol
        if abs(y0-ypress)<bt*h0:
            if h0-dy > 0:
                self.rect.set_y(y0+dy)
                self.rect.set_height(h0-dy)
        elif abs(y0+h0-ypress)<bt*h0:
            if h0+dy > 0:
                self.rect.set_height(h0+dy)

class ParaView(GView):

    TID = "PC"

    def __init__(self, parent, vid):
        GView.__init__(self, parent, vid)
        self.Z = None
        self.sc = None
    
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

        connections = []
        # connections.append(self.MapfigMap.canvas.mpl_connect('pick_event', self.OnPick))
        connections.append(self.MapfigMap.canvas.mpl_connect('button_press_event', self.on_press))
        connections.append(self.MapfigMap.canvas.mpl_connect('button_release_event', self.on_release))
        connections.append(self.MapfigMap.canvas.mpl_connect('motion_notify_event', self.on_motion))

        # self.el = Ellipse((2, -1), 0.5, 0.5)
        # self.axe.add_patch(self.el)

        self.MapcanvasMap.draw()

            
    def prepareData(self, osupp=None, top_part=None):
            
        side_cols = []
        ranges = []
        lit_str = []
        for side in [0,1]:
            for l in self.sc[side]:
                side_cols.append((side, l.col()))
                ranges.append([self.parent.dw.data.col(side, l.col()).numEquiv(r) for r in l.term.valRange()] \
                              + [self.parent.dw.data.col(side, l.col()).width])
                #lit_str.append(l.term.dispU(False, self.parent.dw.data.getNames(side)))
                lit_str.append(self.parent.dw.data.getNames(side)[l.col()])

        pos_axis = len(self.sc[0])
        ranges.insert(pos_axis, [None, None, 1])
        lit_str.insert(pos_axis, "---")

        mat, details, mcols = self.parent.dw.data.getMatrix()
        Z, d = toolsMath.linkage(mat, details, side_cols, osupp)

        mcols[None] = 0
        side_cols.insert(pos_axis, None)
        data_m = np.vstack([mat[mcols[sc],:] for sc in side_cols])
        limits = np.vstack([np.array([min(mat[mcols[sc],:]), max(mat[mcols[sc],:])]) for sc in side_cols])

        return data_m, lit_str, limits, ranges, Z, d


    def updateMap(self, red = None):
        """ Redraws the map
        """

        if red is not None:

            self.current_r = red
            t = 20 # TODO get t

            osupp = red.supports().getVectorABCD()
            pos_axis = len(red.queries[0])

            new = [[l.col() for l in red.queries[side].listLiterals()] for side in [0,1]]
            current = None
            if self.sc is not None:
                current = [[l.col() for l in self.sc[side]] for side in [0,1]]
            if self.Z is None or current != new:
                self.sc =  [[l for l in red.queries[side].listLiterals()] for side in [0,1]]
                self.data_m, self.lit_str, self.limits, self.ranges, self.Z, self.d = self.prepareData(osupp)
                
            ## TEST whether t is different?
            m = self.axe
            self.map_lines = {}
            m.cla()

            ### GATHERING DATA
            draw_settings = self.getDrawSettings()
            self.data_m[pos_axis, :] = [draw_settings["draw_pord"][o] for o in osupp]
            tt = [draw_settings["draw_pord"][o] for o in red.suppPartRange()]
            self.limits[pos_axis, :] = [min(tt), max(tt)]
            colorsl =  [draw_settings[i]["color_e"] for i in osupp]

            ### SAMPLING ENTITIES
            reps, clusters = toolsMath.sample(self.Z, t, self.d)

            ### ADDING NOISE AND RESCALING
            N = float(self.parent.dw.data.nbRows())
            tt = np.array([abs(r[2]) for r in self.ranges])
            mask_noise = - np.tile(self.limits[:,0], (len(reps),1)) \
                         + np.outer([(N-i)/N for i in reps], tt/2.0)+ tt/4.0
                         
            mask_div = np.tile((self.limits[:,1]+tt) - self.limits[:,0], (len(reps),1))  
            tt = [i/(2*N)+0.25 for i in reps]
            final = np.vstack((tt, (self.data_m[:,reps] + mask_noise.T)/mask_div.T, tt))

            ### PLOTTING
            ### Lines
            for i, r in enumerate(reps):
                tt = plt.plot(final[:,i], color=colorsl[r], picker=1)
                self.map_lines[tt[0]] = r

            ### Labels
            m.set_xticks(range(len(self.lit_str)+2))
            # tmp = [""]+["\n\n"*(i%2)+s for (i,s) in enumerate(self.lit_str)]+[""]
            tmp = [""]+self.lit_str+[""]
            m.set_xticklabels(tmp) #, rotation=20)

            ### Bars
            rects_map = {}
            for i, rg in enumerate(self.ranges):
                if rg[0] is not None:
                    bds = [(rg[k]-self.limits[i,0]+k*abs(rg[2]))/(self.limits[i,1]+abs(rg[2]) - self.limits[i,0]) for k in [0,1]]
                    rects = plt.bar(i+.95, bds[1]-bds[0], 0.1, bds[0], edgecolor='0.3', color='0.7', alpha=0.7, zorder=10)
                    if rg[2] == 0:
                        rects_map[i] = rects[0]
                        
            self.drs = []
            self.ri = None
            for rid, rect in rects_map.items():
                dr = DraggableResizeableRectangle(rect, rid=rid, callback=self.receive_release)
                self.drs.append(dr)


            #self.updateEmphasize(ParaView.COLHIGH)
            self.MapcanvasMap.draw()
            return red


    def on_press(self, event):
        if event.inaxes != self.axe: return
        i = 0
        while self.ri is None and i < len(self.drs):
            contains, attrd = self.drs[i].contains(event)
            if contains:
                self.ri = i
            i+=1
        if self.ri is not None:
            self.drs[self.ri].do_press(event)
        
    def on_release(self, event):
        if event.inaxes != self.axe: return
        if self.ri is not None:
            self.drs[self.ri].do_release(event)
        self.ri = None

    def on_motion(self, event):
        if event.inaxes != self.axe: return
        if self.ri is not None:
            self.drs[self.ri].do_motion(event)

    def receive_release(self, rid, rect):
        pos_axis = len(self.current_r.queries[0])
        side = 0
        pos = rid
        if rid > pos_axis:
            side = 1
            pos -= (pos_axis+1)
        ys = [rect.get_y(), rect.get_y() + rect.get_height()]
        bounds = []
        for b in ys:
            if b == 1:
                tmp = float("Inf")
            elif b == 0:
                tmp = float("-Inf")
            else:
                tmp = b*(self.limits[rid, 1]-self.limits[rid, 0])+self.limits[rid, 0]
            bounds.append(tmp)
        copied = self.current_r.queries[side].copy()
        l = copied.listLiterals()[pos]
        l.term.setRange(bounds)
        self.ranges[rid] = [self.parent.dw.data.col(side, l.col()).numEquiv(r) for r in l.term.valRange()] \
                              + [self.parent.dw.data.col(side, l.col()).width]

        self.updateQuery(side, copied)

                
    def emphasizeLine(self, lid, colhigh='#FFFF00'):
        pass
        ### TODO rewrite...
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
                #### this method does not exist any longer
                ### ti = lit.sampleBounds(self.parent.dw.getDataCols(side), self.parent.dw.data.getNames(side), [lid],  scale_p, pos=pp)
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

def pickVars(mat, details, side_cols=None, only_enabled=False):
    types_ids = {BoolColM.type_id: [], CatColM.type_id:[], NumColM.type_id:[]}
    for i, dt in enumerate(details):
        if ( dt["enabled"] or not only_enabled ) and ( (side_cols is None) or ((dt["side"], None) in side_cols) or ( (dt["side"], dt["col"]) in side_cols)):
            if np.std(mat[i,:]) != 0:
                types_ids[dt["type"]].append(i)
    types_ids["all"] = list(itertools.chain(*types_ids.values()))
    return types_ids


def getDistances(mat, details, side_cols=None, parameters=None, only_enabled=False, parts=None):
    if parameters is None:
        parameters = [{"type": "all", "metric": "seuclidean", "weight": 1}]

        # parameters = [{"type": BoolColM.type_id, "metric": "hamming", "weight": 1},
        #               {"type": CatColM.type_id, "metric": "hamming", "weight": 1},
        #               {"type": NumColM.type_id, "metric": "seuclidean", "weight": 1}]
        
    types_ids = pickVars(mat, details, side_cols, only_enabled)

    d = np.zeros((mat.shape[1]*(mat.shape[1]-1)/2.0))
    for typ in parameters:
        if len(types_ids.get(typ["type"], [])) > 0:
            if typ["weight"] == "p":
                weight = 1/len(types_ids[typ["type"]])
            else:
                weight = typ["weight"]
            d += weight*scipy.spatial.distance.pdist(mat[types_ids[typ["type"]],:].T, metric=typ["metric"])
    if parts is not None:
        d += 10*max(d)*scipy.spatial.distance.pdist(np.array([parts]).T, "hamming")
    return d
