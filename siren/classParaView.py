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
from matplotlib.patches import Ellipse
import itertools

from reremi.classQuery import Query
from reremi.classRedescription import Redescription
from reremi.classData import BoolColM, CatColM, NumColM
from classGView import GView
from classInterObjects import DraggableResizeableRectangle
import toolsMath

import pdb


class ParaView(GView):

    TID = "PC"

    def __init__(self, parent, vid):
        self.current_r = None
        self.zds = None
        self.sc = None
        self.sld = None
        GView.__init__(self, parent, vid)
    
    def getId(self):
        return (ParaView.TID, self.vid)
        
    def drawMap(self):
        """ Draws the map
        """
        self.highl = {}
        self.hight = {}
        self.MapfigMap = plt.figure()

        self.Mapcurr_mapi = 0
        self.MapcanvasMap = FigCanvas(self.mapFrame, -1, self.MapfigMap)
        
        self.MaptoolbarMap = NavigationToolbar(self.MapcanvasMap)

        self.MapfigMap.clear()
        self.axe = self.MapfigMap.add_subplot(111)
        self.gca = plt.gca()

        connections = []
        connections.append(self.MapfigMap.canvas.mpl_connect('pick_event', self.OnPick))
        connections.append(self.MapfigMap.canvas.mpl_connect('button_press_event', self.on_press))
        connections.append(self.MapfigMap.canvas.mpl_connect('button_release_event', self.on_release))
        connections.append(self.MapfigMap.canvas.mpl_connect('motion_notify_event', self.on_motion))

        self.el = Ellipse((2, -1), 0.5, 0.5)
        self.axe.add_patch(self.el)

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
        if len(osupp) > 500:
            zds = toolsMath.linkageZds(mat, details, side_cols, osupp)
        else:
            Z, d = toolsMath.linkage(mat[:,:500], details, side_cols, osupp)
            zds = [{"Z":Z, "d":d, "ids": range(mat.shape[1])}]

        mcols[None] = 0
        precisions = [self.parent.dw.data.col(side, col).getPrec() for side,col in side_cols]
        side_cols.insert(pos_axis, None)
        precisions.insert(pos_axis, 0)
        data_m = np.vstack([mat[mcols[sc],:] for sc in side_cols])
        limits = np.vstack([np.array([min(mat[mcols[sc],:]), max(mat[mcols[sc],:]), precisions[si]]) for si, sc in enumerate(side_cols)])

        return data_m, lit_str, limits, ranges, zds


    def updateMap(self, red = None):
        """ Redraws the map
        """

        if red is not None:
            
            self.current_r = red

            osupp = red.supports().getVectorABCD()
            pos_axis = len(red.queries[0])

            new = [[l.col() for l in red.queries[side].listLiterals()] for side in [0,1]]
            current = None
            if self.sc is not None:
                current = [[l.col() for l in self.sc[side]] for side in [0,1]]
            if self.zds is None or current != new:
                self.sc =  [[l for l in red.queries[side].listLiterals()] for side in [0,1]]
                self.data_m, self.lit_str, self.limits, self.ranges, self.zds = self.prepareData(osupp)
                
            N = float(self.parent.dw.data.nbRows())
            td = 10
            if self.sld is not None:
                td = self.sld.GetValue()
            t = (5*(td/100.0)**10+1*(td/100.0)**2)/6
                
            ## TEST whether t is different?
            m = self.axe
            m.cla()

            ### GATHERING DATA
            draw_settings = self.getDrawSettings()
            self.data_m[pos_axis, :] = [draw_settings["draw_pord"][o] for o in osupp]
            tt = [draw_settings["draw_pord"][o] for o in self.current_r.suppPartRange()]
            self.limits[pos_axis, :] = [min(tt), max(tt), 0]
            colorsl =  [draw_settings[i]["color_e"] for i in osupp]


            ### SAMPLING ENTITIES
            reps, clusters = toolsMath.sampleZds(self.zds, t)
            reps.sort(key=lambda x: draw_settings["draw_pord"][osupp[x]])

            ### ADDING NOISE AND RESCALING
            tt = np.array([abs(r[2]) for r in self.ranges])
            mask_noise = - np.tile(self.limits[:,0], (len(reps),1)) \
                         + np.outer([(N-i)/N for i in reps], tt/2.0)+ tt/4.0
                         
            mask_div = np.tile((self.limits[:,1]+tt) - self.limits[:,0], (len(reps),1))  
            tt = [(N-i)/(2.0*N)+0.25 for i in reps]
            final = np.vstack((tt, (self.data_m[:,reps] + mask_noise.T)/mask_div.T, tt))

            ### PLOTTING
            ### Lines
            for i, r in enumerate(reps):
                plt.plot(final[:,i], color=colorsl[r], picker=True, gid="%d.%d" % (r, 0))

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
                        
            self.annotation = self.axe.annotate("", xy=(0.5, 0.5), xytext=(0.5,0.5), backgroundcolor="w")
            self.drs = []
            self.ri = None
            for rid, rect in rects_map.items():
                dr = DraggableResizeableRectangle(rect, rid=rid, callback=self.receive_release, \
                                                  pinf=self.getPinvalue, annotation=self.annotation)
                self.drs.append(dr)


            m.axis((0,len(self.lit_str)+1, 0, 1))
            #self.updateEmphasize(ParaView.COLHIGH)
            self.MapcanvasMap.draw()
            return self.current_r


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

    def getPinvalue(self, rid, b):
        if b == 1:
            tmp = float("Inf")
        elif b == 0:
            tmp = float("-Inf")
        else:
            tmp = np.around(b*(self.limits[rid, 1]-self.limits[rid, 0])+self.limits[rid, 0], int(self.limits[rid, 2]))
        return tmp

    def receive_release(self, rid, rect):
        pos_axis = len(self.current_r.queries[0])
        side = 0
        pos = rid
        if rid > pos_axis:
            side = 1
            pos -= (pos_axis+1)
        ys = [rect.get_y(), rect.get_y() + rect.get_height()]
        bounds = [self.getPinvalue(rid, b) for b in ys]
        copied = self.current_r.queries[side].copy()
        l = copied.listLiterals()[pos]
        l.term.setRange(bounds)
        self.ranges[rid] = [self.parent.dw.data.col(side, l.col()).numEquiv(r) for r in l.term.valRange()] \
                              + [self.parent.dw.data.col(side, l.col()).width]

        self.updateQuery(side, copied)
                
    def emphasizeLine(self, lid, colhigh='#FFFF00'):
        if self.highl.has_key(lid):
        #     self.clearEmphasize([lid])
            return

        draw_settings = self.getDrawSettings()
        N = float(self.parent.dw.data.nbRows())
        m = self.axe

        ### ADDING NOISE AND RESCALING
        mask_noise = - self.limits[:,0] \
                     + np.array([abs(r[2])*(N-lid)/(2.0*N)+abs(r[2])/4.0 for r in self.ranges])
                         
        mask_div = self.limits[:,1]+np.array([abs(r[2]) for r in self.ranges]) - self.limits[:,0]
        tt = (N-lid)/(2.0*N)+0.25
        final = np.concatenate(([tt], (self.data_m[:,lid] + mask_noise)/mask_div, [tt]))

        self.highl[lid] = []
        self.highl[lid].extend(plt.plot(final, color=colhigh, linewidth=1))

        self.hight[lid] = []
        self.hight[lid].append(m.annotate('%d' % lid, xy=(len(self.ranges)+1, tt),  xycoords='data',
                          xytext=(-10, 15), textcoords='offset points', color= draw_settings[self.suppABCD[lid]]["color_e"],
                          size=10, va="center", backgroundcolor="#FFFFFF",
                          bbox=dict(boxstyle="round", facecolor="#FFFFFF", ec="gray"),
                          arrowprops=dict(arrowstyle="wedge,tail_width=1.", fc="#FFFFFF", ec="gray",
                                          patchA=None, patchB=self.el, relpos=(0.2, 0.5))
                                            ))
        self.MapcanvasMap.draw()

    def additionalElements(self):
        tmp = []
        tmp.append(self.MaptoolbarMap)
        self.buttons = []
        self.buttons.append({"element": wx.Button(self.mapFrame, size=(80,-1), label="Expand"),
                             "function": self.OnExpand})
        self.sld = wx.Slider(self.mapFrame, -1, 10, 0, 100, wx.DefaultPosition, (100, -1),
                            wx.SL_AUTOTICKS | wx.SL_HORIZONTAL | wx.SL_LABELS)
        tmp.append(self.buttons[-1]["element"])
        tmp.append(self.sld)
        return tmp

    def additionalBinds(self):
        for button in self.buttons:
            button["element"].Bind(wx.EVT_BUTTON, button["function"])
        ##self.sld.Bind(wx.EVT_SLIDER, self.OnSlide)
        ##self.sld.Bind(wx.EVT_SCROLL_THUMBRELEASE, self.OnSlide)
        self.sld.Bind(wx.EVT_SCROLL_CHANGED, self.OnSlide)

    def OnSlide(self, event):
        if self.current_r is not None:
            ##print "SLIDER", self.sld.GetValue()
            self.updateMap(self.current_r)


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
