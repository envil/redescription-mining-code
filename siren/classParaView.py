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
    FigureCanvasWxAgg as FigCanvas
from matplotlib.patches import Ellipse
import itertools

from reremi.classQuery import Query
from reremi.classRedescription import Redescription
from reremi.classData import BoolColM, CatColM, NumColM
from classGView import GView, CustToolbar
from classInterObjects import DraggableResizeableRectangle
import toolMath

import pdb

class ParaView(GView):

    TID = "PC"
    SDESC = "Pa.Co."
    ordN = 1
    title_str = "Parallel Coordinates"

    def __init__(self, parent, vid, more=None):
        self.reps = set()
        self.current_r = None
        self.zds = None
        self.sc = None
        self.sld = None
        self.ri = None
        GView.__init__(self, parent, vid)
    
    def getId(self):
        return (ParaView.TID, self.vid)

    def setCurrent(self, qr=None, source_list=None):
        if qr is not None:
            if type(qr) in [list, tuple]:
                queries = qr
                red = Redescription.fromQueriesPair(qr, self.parent.dw.data)
            else:
                red = qr
                queries = [red.query(0), red.query(1)]
            self.queries = queries
            self.suppABCD = red.supports().getVectorABCD()
            self.current_r = red
            self.source_list=source_list
            self.updateText(red)
            self.updateMap()
            self.updateHist(red)
            return red

    def updateQuery(self, sd=None, query=None, force=False, upAll=True):
        if sd is None:
            queries = [self.parseQuery(0),self.parseQuery(1)]
        else:
            queries = [None, None]
            if query is None:
                queries[sd] = self.parseQuery(sd)
            else:
                queries[sd] = query

        changed = False
        old = [None, None]
        for side in [0,1]:
            old[side] = self.queries[side]
            if queries[side] != None and queries[side] != self.queries[side]:
                self.queries[side] = queries[side]
                changed = True

        red = None
        if changed or force:
            try:
                red = Redescription.fromQueriesPair(self.queries, self.parent.dw.data)
            except Exception:
                ### Query could be parse but not recomputed
                red = None
                self.queries = old
        if red is not None:
            self.suppABCD = red.supports().getVectorABCD()
            self.current_r = red
            if upAll:
                self.updateText(red)
                self.makeMenu()
                self.updateOriginal(red)
                self.updateHist(red)
            self.updateMap()
            return red
        else: ### wrongly formatted query, revert
            for side in [0,1]:
                self.updateQueryText(self.queries[side], side)
        return None
        
    def drawMap(self):
        """ Draws the map
        """
        self.highl = {}
        self.hight = {}
        self.MapfigMap = plt.figure()
        self.MapcanvasMap = FigCanvas(self.mapFrame, -1, self.MapfigMap)
        self.MaptoolbarMap = CustToolbar(self.MapcanvasMap, self)
        self.MapfigMap.clear()
        self.axe = self.MapfigMap.add_subplot(111)

        self.el = Ellipse((2, -1), 0.5, 0.5)
        self.axe.add_patch(self.el)

        self.MapfigMap.canvas.mpl_connect('pick_event', self.OnPick)
        self.MapfigMap.canvas.mpl_connect('key_press_event', self.key_press_callback)
        self.MapfigMap.canvas.mpl_connect('button_press_event', self.on_press)
        self.MapfigMap.canvas.mpl_connect('button_release_event', self.on_release)
        self.MapfigMap.canvas.mpl_connect('motion_notify_event', self.on_motion)
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
            zds = toolMath.linkageZds(mat, details, side_cols, osupp)
        else:
            Z, d = toolMath.linkage(mat, details, side_cols, osupp)
            zds = [{"Z":Z, "d":d, "ids": range(mat.shape[1])}]

        mcols[None] = 0
        precisions = [self.parent.dw.data.col(side, col).getPrec() for side,col in side_cols]
        side_cols.insert(pos_axis, None)
        precisions.insert(pos_axis, 0)
        data_m = np.vstack([mat[mcols[sc],:] for sc in side_cols])
        limits = np.vstack([np.array([float(np.min(mat[mcols[sc],:])), np.max(mat[mcols[sc],:]), precisions[si]]) for si, sc in enumerate(side_cols)])
        
        return data_m, lit_str, limits, ranges, zds


    def updateRanges(self):
            
        ranges = []
        for side in [0,1]:
            for l in self.sc[side]:
                ranges.append([self.parent.dw.data.col(side, l.col()).numEquiv(r) for r in l.term.valRange()] \
                              + [self.parent.dw.data.col(side, l.col()).width])

        pos_axis = len(self.sc[0])
        ranges.insert(pos_axis, [None, None, 1])
        return ranges


    def updateMap(self):
        """ Redraws the map
        """

        if self.current_r is not None:

            self.highl = {}
            self.hight = {}

            red = self.current_r
            draw_settings = self.getDrawSettings()
            self.axe.cla()

            osupp = self.suppABCD
            pos_axis = len(red.queries[0])

            new = [[l.col() for l in red.queries[side].listLiterals()] for side in [0,1]]
            current = None
            if self.sc is not None:
                current = [[l.col() for l in self.sc[side]] for side in [0,1]]
            self.sc =  [[l for l in red.queries[side].listLiterals()] for side in [0,1]]
            if self.zds is None or current != new:
                self.sc =  [[l for l in red.queries[side].listLiterals()] for side in [0,1]]
                self.data_m, self.lit_str, self.limits, self.ranges, self.zds = self.prepareData(osupp)
            else:
                self.ranges = self.updateRanges()

            N = float(self.parent.dw.data.nbRows())

            t = 0.1
            if self.sld is not None:
                td = self.sld.GetValue()
                t = (5*(td/100.0)**8+1*(td/100.0)**2)/6
                
                
            ### GATHERING DATA
            self.data_m[pos_axis, :] = [draw_settings["draw_pord"][o] for o in osupp]
            tt = [draw_settings["draw_pord"][o] for o in red.suppPartRange()]
            self.limits[pos_axis, :] = [np.min(tt), np.max(tt), 0]

            ### SAMPLING ENTITIES
            reps, clusters = toolMath.sampleZds(self.zds, t)
            reps.sort(key=lambda x: draw_settings["draw_pord"][osupp[x]])
            self.reps = set(reps)
            
            ### ADDING NOISE AND RESCALING
            tt = np.array([abs(r[2]) for r in self.ranges])
            mask_noise = - np.tile(self.limits[:,0], (len(reps),1)) \
                         + np.outer([(N-i)/N for i in reps], tt/2.0)+ tt/4.0
                         
            mask_div = np.tile((self.limits[:,1]+tt) - self.limits[:,0], (len(reps),1))  
            tt = [(N-i)/(2.0*N)+0.25 for i in reps]
            final = np.vstack((tt, (self.data_m[:,reps] + mask_noise.T)/mask_div.T, tt))

            ### SELECTED DATA
            selected = self.parent.dw.data.selectedRows()
            selp = 0.1
            # if self.sld_sel is not None:
            #     selp = self.sld_sel.GetValue()/100.0
            selv = np.ones((self.parent.dw.data.nbRows(), 1))
            if len(selected) > 0:
                selv[np.array(list(selected))] = selp
            
            ### PLOTTING
            ### Lines
            for i, r in enumerate(reps):
                if selv[i] > 0:
                    self.axe.plot(final[:,i], color=draw_settings[osupp[r]]["color_e"], alpha=draw_settings[osupp[r]]["alpha"]*selv[r], picker=2, gid="%d.%d" % (r, 1))

            ### Labels
            self.axe.set_xticks(range(len(self.lit_str)+2))
            # tmp = [""]+["\n\n"*(i%2)+s for (i,s) in enumerate(self.lit_str)]+[""]
            tmp = [""]+self.lit_str+[""]
            self.axe.set_xticklabels(tmp) #, rotation=20)

            ### Bars
            rects_map = {}
            for i, rg in enumerate(self.ranges):
                if rg[0] is not None:
                    bds = [(rg[k]-self.limits[i,0]+k*np.abs(rg[2]))/(self.limits[i,1]+np.abs(rg[2]) - self.limits[i,0]) for k in [0,1]]
                    rects = self.axe.bar(i+.95, bds[1]-bds[0], 0.1, bds[0], edgecolor='0.3', color='0.7', alpha=0.7, zorder=10)
                    if rg[2] == 0:
                        rects_map[i] = rects[0]
                        
            self.annotation = self.axe.annotate("", xy=(0.5, 0.5), xytext=(0.5,0.5), backgroundcolor="w")
            self.drs = []
            self.ri = None
            for rid, rect in rects_map.items():
                dr = DraggableResizeableRectangle(rect, rid=rid, callback=self.receive_release, \
                                                  pinf=self.getPinvalue, annotation=self.annotation)
                self.drs.append(dr)

            self.axe.axis((0,len(self.lit_str)+1, 0, 1))
            self.updateEmphasize(self.COLHIGH, review=False)
            self.MapcanvasMap.draw()
            self.MapfigMap.canvas.SetFocus()

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

    def getPinvalue(self, rid, b, direc=0):
        v = b*(self.limits[rid, 1]-self.limits[rid, 0])+self.limits[rid, 0]
        prec = int(self.limits[rid, 2])
        if direc < 0:
            tmp = 10**-prec*np.ceil(v*10**prec)
        elif direc > 0:
            tmp = 10**-prec*np.floor(v*10**prec)
        else:
            tmp = np.around(v, prec)            

        if tmp == self.limits[rid, 1]:
            tmp = float("Inf")
        elif tmp == self.limits[rid, 0]:
            tmp = float("-Inf")
        return tmp

    def receive_release(self, rid, rect):
        if self.current_r is not None:
            pos_axis = len(self.current_r.queries[0])
            side = 0
            pos = rid
            if rid > pos_axis:
                side = 1
                pos -= (pos_axis+1)
            ys = [(rect.get_y(), -1), (rect.get_y() + rect.get_height(), 1)]
            bounds = [self.getPinvalue(rid, b, direc) for (b,direc) in ys]
            copied = self.current_r.queries[side].copy()
            l = copied.listLiterals()[pos]
            l.term.setRange(bounds)
            self.ranges[rid] = [self.parent.dw.data.col(side, l.col()).numEquiv(r) for r in l.term.valRange()] \
                                  + [self.parent.dw.data.col(side, l.col()).width]

            upAll = self.current_r.queries[side].listLiterals()[pos] != l
            self.current_r = self.updateQuery(side, copied, force=True, upAll=upAll)

                
    def emphasizeOn(self, lids, colhigh='#FFFF00'):
        draw_settings = self.getDrawSettings()
        N = float(self.parent.dw.data.nbRows())
        for lid in lids:
            if self.highl.has_key(lid):
                continue

            ### ADDING NOISE AND RESCALING
            mask_noise = - self.limits[:,0] \
                         + np.array([np.abs(r[2])*(N-lid)/(2.0*N)+np.abs(r[2])/4.0 for r in self.ranges])

            mask_div = self.limits[:,1]+np.array([np.abs(r[2]) for r in self.ranges]) - self.limits[:,0]
            tt = (N-lid)/(2.0*N)+0.25

            #pdb.set_trace()
            tmm= (self.data_m[:,lid] + mask_noise)/mask_div
            
            final = np.concatenate(([tt], (self.data_m[:,lid] + mask_noise)/mask_div, [tt]))

            self.highl[lid] = []
            if lid in self.reps:
                self.highl[lid].extend(self.axe.plot(final, color=colhigh, linewidth=1))
            else:
                self.highl[lid].extend(self.axe.plot(final, color=colhigh, linewidth=1, picker=2, gid="%d.%d" % (lid, 1)))

        if len(lids) == 1 and not self.hight.has_key(lid):
            pi = self.suppABCD[lid]
            self.hight[lid] = []
            self.hight[lid].append(self.axe.annotate('%d' % lid, xy=(len(self.ranges)+1, tt),  xycoords='data',
                                                     xytext=(10, 0), textcoords='offset points', color= draw_settings[pi]["color_e"],
                                                     size=10, va="center", backgroundcolor="#FFFFFF",
                                                     bbox=dict(boxstyle="round", facecolor="#FFFFFF", ec=draw_settings[pi]["color_e"]),
                                                     arrowprops=dict(arrowstyle="wedge,tail_width=1.", fc="#FFFFFF", ec=draw_settings[pi]["color_e"],
                                                                     patchA=None, patchB=self.el, relpos=(0.2, 0.5))
                                            ))


    def additionalElements(self):
        add_box = wx.BoxSizer(wx.HORIZONTAL)
        flags = wx.ALIGN_CENTER | wx.ALL | wx.EXPAND

        add_box.Add(self.MaptoolbarMap, 0, border=3, flag=flags)
        add_box.AddSpacer((20,-1))
        self.buttons = []
        self.buttons.append({"element": wx.Button(self.mapFrame, size=(80,-1), label="Expand"),
                             "function": self.OnExpandSimp})
        self.sld = wx.Slider(self.mapFrame, -1, 30, 0, 100, wx.DefaultPosition, (150, -1), wx.SL_HORIZONTAL)
        self.sld_sel = wx.Slider(self.mapFrame, -1, 10, 0, 100, wx.DefaultPosition, (150, -1), wx.SL_HORIZONTAL)
        add_box.Add(self.buttons[-1]["element"], 0, border=3, flag=flags)
        add_box.AddSpacer((20,-1))
        
        v_box = wx.BoxSizer(wx.VERTICAL)
        label = wx.StaticText(self.mapFrame, wx.ID_ANY,u"- opac. disabled  +")
        v_box.Add(label, 0, border=3, flag=wx.ALIGN_CENTER | wx.ALL)
        v_box.Add(self.sld_sel, 0, border=3, flag=flags)
        add_box.Add(v_box, 0, border=3, flag=flags)
        add_box.AddSpacer((20,-1))
        
        v_box = wx.BoxSizer(wx.VERTICAL)
        label = wx.StaticText(self.mapFrame, wx.ID_ANY, "-      details      +")
        v_box.Add(label, 0, border=3, flag=wx.ALIGN_CENTER | wx.ALL )
        v_box.Add(self.sld, 0, border=3, flag=flags)
        add_box.Add(v_box, 0, border=3, flag=flags)
        return [add_box]

    def additionalBinds(self):
        for button in self.buttons:
            button["element"].Bind(wx.EVT_BUTTON, button["function"])
        ##self.sld.Bind(wx.EVT_SLIDER, self.OnSlide)
        self.sld.Bind(wx.EVT_SCROLL_THUMBRELEASE, self.OnSlide)
        self.sld_sel.Bind(wx.EVT_SCROLL_THUMBRELEASE, self.OnSlide)
        ##self.sld.Bind(wx.EVT_SCROLL_CHANGED, self.OnSlide)
        ##self.sld_sel.Bind(wx.EVT_SCROLL_CHANGED, self.OnSlide)

    def OnSlide(self, event):
        self.updateMap()


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
