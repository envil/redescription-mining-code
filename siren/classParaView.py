### TODO check which imports are needed 
from __future__ import unicode_literals
import wx
import numpy
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

from reremi.classQuery import Query, BoolTerm, CatTerm, NumTerm
from reremi.classRedescription import Redescription
from reremi.classData import BoolColM, CatColM, NumColM
from classGView import GView, CustToolbar
from classInterObjects import ResizeableRectangle, DraggableRectangle


import pdb
            
class ParaView(GView):

    TID = "PC"
    SDESC = "Pa.Co."
    ordN = 1
    title_str = "Parallel Coordinates"

    rect_halfwidth = 0.05
    rect_alpha = 0.7
    rect_color = "0.7"
    rect_ecolor = "0.3"

    org_spreadL = 0.49 #(2/3.-0.5)
    org_spreadR = 0.49
    flat_space = 0.03
    maj_space = 0.1
    max_group_clustering = 100
    nb_clusters = 10
    margins_sides = 0.05
    margins_tb = 0.05
    margin_hov = 0.01
        
    def __init__(self, parent, vid, more=None):
        self.reps = set()
        self.current_r = None
        self.prepared_data = None
        self.lits = None
        self.sld = None
        self.ri = None
        GView.__init__(self, parent, vid)
    
    def getId(self):
        return (self.TID, self.vid)

    def setCurrent(self, qr=None, source_list=None):
        if qr is not None:
            if type(qr) in [list, tuple]:
                queries = qr
                red = Redescription.fromQueriesPair(qr, self.parent.dw.getData())
            else:
                red = qr
                queries = [red.query(0), red.query(1)]
            self.queries = queries
            red.setRestrictedSupp(self.parent.dw.getData())
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
                red = Redescription.fromQueriesPair(self.queries, self.parent.dw.getData())
            except Exception:
                ### Query could be parse but not recomputed
                red = None
                self.queries = old
        if red is not None:
            red.setRestrictedSupp(self.parent.dw.getData())
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
        self.MapfigMap.canvas.mpl_connect('motion_notify_event', self.on_motion_all)
        self.MapfigMap.canvas.mpl_connect('axes_leave_event', self.on_axes_out)
        self.MapcanvasMap.draw()

    def prepareData(self, draw_pord=None):
        pos_axis = len(self.litsort[0])

        side_cols = []
        lit_str = []
        for side in [0,1]:
            for l in self.litsort[side]:
                side_cols.append((side, l.colId()))
                lit_str.append(self.parent.dw.getData().getNames(side)[l.colId()])

        precisions = [self.parent.dw.getData().col(side, col).getPrec() for side,col in side_cols]

        side_cols.insert(pos_axis, None)
        precisions.insert(pos_axis, 0)
        qcols = [l for l in self.litsort[0]]+[None]+[l for l in self.litsort[1]]

        ranges = self.updateRanges()
        
        mat, details, mcols = self.parent.dw.getData().getMatrix()
        mcols[None] = -1
        cids = [mcols[sc] for sc in side_cols]
        #reps.sort(key=lambda x: draw_settings["draw_pord"][osupp[x]])
        if draw_pord is not None:
            tmp = sorted(numpy.unique(self.suppABCD), key=lambda x: draw_pord[x])
            dd = -numpy.ones(numpy.max(tmp)+1)
            for (p,v) in enumerate(tmp):
                dd[v] = p
            data_m = numpy.vstack([mat, dd[self.suppABCD]])[cids]
        else:
            data_m = numpy.vstack([mat, self.suppABCD])[cids]
        limits = numpy.vstack([numpy.nanmin(data_m, axis=1), numpy.nanmax(data_m, axis=1), precisions])

        denoms = limits[1,:]-limits[0,:]
        denoms[denoms==0] = 1.
        scaled_m = numpy.vstack([(data_m[i,:]-limits[0,i])/denoms[i] for i in range(data_m.shape[0])])

        ### spreading lines over range
        N = float(data_m.shape[1])
        avgs = numpy.mean(scaled_m, axis=0)
        pos_lids = []
        for i in range(data_m.shape[0]):
            if ranges[i][-1] == 0:
                pos_lids.append(scaled_m[i])
            else:
                ww = numpy.array([50, 10, 100])
                if i == 0:
                    cc = [i+1, i+1, pos_axis]
                elif i == data_m.shape[0]-1:
                    cc = [i-1, i-1, pos_axis]
                else:
                    cc = [i-1, i+1, pos_axis]
                w = abs(ranges[i][-1])
                center = 0.5*w
                av_space = center - 0.5*self.maj_space * (denoms[i] + w)  
                pos_help = numpy.dot(ww, scaled_m[cc,:])+avgs
                spreadv = numpy.zeros(data_m[i,:].shape)
                vs = numpy.unique(data_m[i,:])
                for v in vs:
                    vids = list(numpy.where(data_m[i,:]==v)[0])
                    vids.sort(key=lambda x: pos_help[x])
                    top, bot = center-len(vids)*av_space/N, center+len(vids)*av_space/N
                    spreadv[vids] += numpy.linspace(top, bot, len(vids))
                pos_lids.append((data_m[i,:]-limits[0,i] + spreadv)/(denoms[i] + w))

        spreadL = numpy.zeros(data_m[i,:].shape)
        spreadL[numpy.argsort(pos_lids[0])] = numpy.linspace(0.5-self.org_spreadL, 0.5+self.org_spreadL, N)
        spreadR = numpy.zeros(data_m[i,:].shape)
        spreadR[numpy.argsort(pos_lids[-1])] = numpy.linspace(0.5-self.org_spreadR, 0.5+self.org_spreadR, N)

        pos_lids.extend([spreadR,spreadL])
        pos_lids = numpy.vstack(pos_lids)
        
        xlabels = lit_str
        xticks = [x for x,v in enumerate(side_cols) if v is not None]
        ycols = [-1]
        xs = [-1]
        for i in range(len(side_cols)):
            ycols.extend([i,i])
            xs.extend([i-self.flat_space, i+self.flat_space])
        ycols.append(-2)
        xs.append(len(side_cols))
                
        #### ORDERING LINES FOR DETAILS SUBSAMPLING BY GETTING CLUSTERS
        sorting_samples = numpy.zeros(scaled_m[i,:].shape)
        left_over = []
        for v in numpy.unique(scaled_m[pos_axis,:]):
            ids = numpy.where(scaled_m[pos_axis,:]==v)[0]
            # numpy.random.shuffle(ids)
            rg = ids.shape[0]/self.max_group_clustering+1
            for i in range(rg):
                if i > 0 and ((i+1)*self.max_group_clustering - ids.shape[0]) > 2*self.max_group_clustering/3.:
                    left_over.extend(ids[i*self.max_group_clustering:])
                    break
                else:
                    subids = ids[i*self.max_group_clustering:(i+1)*self.max_group_clustering]
                    d = scipy.spatial.distance.pdist(scaled_m[:,subids].T)
                    Z = scipy.cluster.hierarchy.linkage(d)
                    T = scipy.cluster.hierarchy.fcluster(Z, self.nb_clusters, criterion="maxclust")        
                    for cc in numpy.unique(T):
                        ci = numpy.where(T==cc)[0]
                        #numpy.random.shuffle(ci)
                        sorting_samples[subids[ci]] = -0.1*v+float(i)/rg+10*numpy.arange(1., ci.shape[0]+1)
        if len(left_over) > 0:
            subids = numpy.array(left_over)
            d = scipy.spatial.distance.pdist(scaled_m[:,subids].T)
            Z = scipy.cluster.hierarchy.linkage(d)
            T = scipy.cluster.hierarchy.fcluster(Z, self.nb_clusters, criterion="maxclust")
            for cc in numpy.unique(T):
                ci = numpy.where(T==cc)[0]
                #numpy.random.shuffle(ci)
                sorting_samples[subids[ci]] = v+10*numpy.arange(1., ci.shape[0]+1)
        sampling_ord = numpy.argsort(sorting_samples)

        ### TODO: Handle missing values
        # idsNAN = numpy.where(~numpy.isfinite(mat))
        # mat[idsNAN] = numpy.random.random(idsNAN[0].shape[0])

        prepared_data = {"pos_axis": pos_axis,
                         "N": N,
                         "xlabels": xlabels,
                         "xticks": xticks,
                         "ycols": ycols,
                         "xs": xs,
                         "precisions": precisions,
                         "limits": limits,
                         "ranges": ranges,
                         "sampling_ord": sampling_ord,
                         "side_cols": side_cols,
                         "qcols": qcols,
                         "data_m": data_m,
                         "scaled_m": scaled_m,
                         "pos_lids": pos_lids}
        return prepared_data

    def updateRanges(self):
        ranges = []
        for side in [0,1]:
            for l in self.litsort[side]:
                if l.typeId() == BoolColM.type_id:
                    ranges.append([self.parent.dw.getData().col(side, l.colId()).numEquiv(r)
                                   for r in [self.lits[side][l][0][-1], self.lits[side][l][0][-1]]] 
                                  + [self.parent.dw.getData().col(side, l.colId()).width])
                else:
                    ranges.append([self.parent.dw.getData().col(side, l.colId()).numEquiv(r) for r in l.valRange()] \
                                  + [self.parent.dw.getData().col(side, l.colId()).width])
        ranges.insert(len(self.litsort[0]), [None, None, 1])
        return ranges


    def updateMap(self):
        """ Redraws the map
        """

        if self.current_r is not None:
            self.highl = {}
            self.hight = {}

            red = self.current_r

            draw_settings = self.getDrawSettings()

            lits = [red.queries[side].listLiteralsDetails()  for side in [0,1]]
            if self.prepared_data is None or lits != self.lits:
                self.lits = lits
                self.litsort = [sorted(self.lits[side].keys(), key=lambda x: self.lits[side][x])   for side in [0,1]]
                pos_axis = len(self.litsort[0])
                self.prepared_data = self.prepareData(draw_pord = draw_settings["draw_pord"])
            else:
                self.prepared_data["ranges"] = self.updateRanges()

            ### SAMPLING ENTITIES
            t = 0.1
            if self.sld is not None:
                td = self.sld.GetValue()
                t = (5*(td/100.0)**8+1*(td/100.0)**2)/6
            self.reps = list(self.prepared_data["sampling_ord"][:int(t*self.prepared_data["N"])])
            self.reps.sort(key=lambda x: draw_settings["draw_pord"][self.suppABCD[x]])
            #self.reps = set(self.prepared_data["sampling_ord"])

            ### SELECTED DATA
            selv = numpy.ones(self.prepared_data["N"])
            # selected = self.parent.dw.getData().selectedRows()
            # selp = 0.1
            # # if self.sld_sel is not None:
            # #     selp = self.sld_sel.GetValue()/100.0
            # selv = numpy.ones((self.parent.dw.getData().nbRows(), 1))
            # if len(selected) > 0:
            #     selv[numpy.array(list(selected))] = selp

            ### PLOTTING
            ### Lines
            self.axe.cla()
            ycols = self.prepared_data["ycols"]
            for r in self.reps:
                if True: #selv[i] > 0:
                    self.axe.plot(self.prepared_data["xs"], self.prepared_data["pos_lids"][self.prepared_data["ycols"],r],
                                  color=draw_settings[self.suppABCD[r]]["color_e"],
                                  alpha=draw_settings[self.suppABCD[r]]["alpha"]*selv[r], picker=2, gid="%d.%d" % (r, 1))

            ### Labels
            self.axe.set_xticks(self.prepared_data["xticks"])
            self.axe.set_xticklabels(self.prepared_data["xlabels"], rotation=20, ha="right")

            ### Bars slidable/draggable rectangles
            rects_drag = {}
            rects_rez = {}
            for i, rg in enumerate(self.prepared_data["ranges"]):
                if rg[0] is not None:
                    bds = [(rg[k]-self.prepared_data["limits"][0,i]+
                            k*numpy.abs(rg[2]))/(self.prepared_data["limits"][1,i]+numpy.abs(rg[2]) -
                                              self.prepared_data["limits"][0,i]) for k in [0,1]]
                    rects = self.axe.bar(i-self.rect_halfwidth, bds[1]-bds[0], 2*self.rect_halfwidth, bds[0],
                                         edgecolor=self.rect_ecolor, color=self.rect_color, alpha=self.rect_alpha, zorder=10)

                    if self.prepared_data["qcols"][i] is not None:
                        if self.prepared_data["qcols"][i].typeId() == NumColM.type_id:
                            rects_rez[i] = rects[0]
                        elif self.prepared_data["qcols"][i].typeId() == CatColM.type_id or \
                                 self.prepared_data["qcols"][i].typeId() == BoolColM.type_id:   
                            rects_drag[i] = rects[0]

            self.annotation = self.axe.annotate("", xy=(0.5, 0.5), xytext=(0.5,0.5), backgroundcolor="w")
            self.drs = []
            self.ri = None
            for rid, rect in rects_rez.items():
                dr = ResizeableRectangle(rect, rid=rid, callback=self.receive_release, \
                                                  pinf=self.getPinvalue, annotation=self.annotation)
                self.drs.append(dr)

            for rid, rect in rects_drag.items():
                dr = DraggableRectangle(rect, rid=rid, callback=self.receive_release, \
                                                  pinf=self.getPinvalue, annotation=self.annotation)
                self.drs.append(dr)

            #### fit window size
            self.axe.set_xlim([numpy.min(self.prepared_data["xticks"])-1-self.margins_sides,
                               numpy.max(self.prepared_data["xticks"])+1+self.margins_sides])
            self.axe.set_ylim([0-self.margins_tb,1+self.margins_tb])

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
        
    def on_axes_out(self, event):
        if self.ri is not None:
            self.drs[self.ri].do_release(event)
        self.ri = None

    def on_motion_all(self, event):
        if event.inaxes == self.axe and self.ri is not None:
            self.drs[self.ri].do_motion(event)
        else:
            self.on_motion(event)

    def getPinvalue(self, rid, b, direc=0):
        if self.prepared_data is None or self.prepared_data["qcols"][rid] is None:
            return 0
        elif self.prepared_data["qcols"][rid].typeId() == NumColM.type_id:
            v = b*(self.prepared_data["limits"][1,rid]-self.prepared_data["limits"][0, rid])+self.prepared_data["limits"][0, rid]
            prec = int(self.prepared_data["limits"][2, rid])
            if direc < 0:
                tmp = 10**-prec*numpy.ceil(v*10**prec)
            elif direc > 0:
                tmp = 10**-prec*numpy.floor(v*10**prec)
            else:
                tmp = numpy.around(v, prec)            

            if tmp >= self.prepared_data["limits"][1, rid]:
                tmp = float("Inf")
            elif tmp <= self.prepared_data["limits"][0, rid]:
                tmp = float("-Inf")
            return tmp
        elif self.prepared_data["qcols"][rid].typeId() == CatColM.type_id or \
                 self.prepared_data["qcols"][rid].typeId() == BoolColM.type_id:
            v = int(round(b*(self.prepared_data["limits"][1, rid]-self.prepared_data["limits"][0,rid])+self.prepared_data["limits"][0, rid]))
            if v > self.prepared_data["limits"][1, rid]:
                v = self.prepared_data["limits"][1, rid]
            elif v < self.prepared_data["limits"][0, rid]:
                v = self.prepared_data["limits"][0, rid]
            side = 0
            if self.prepared_data["pos_axis"] < rid:
                side = 1
            c = self.parent.dw.getData().col(side, self.prepared_data["qcols"][rid].colId())
            if c is not None:
                return c.getCatFromNum(v)
            
    def receive_release(self, rid, rect):
        if self.current_r is not None and self.litsort is not None:
            pos_axis = self.prepared_data["pos_axis"]
            side = 0
            pos = rid
            if rid > pos_axis:
                side = 1
                pos -= (pos_axis+1)
            copied = self.current_r.queries[side].copy()
            ### HERE RELEASE
            l = self.litsort[side][pos]
            alright = False
            upAll = False
            if l.typeId() == NumColM.type_id:
                ys = [(rect.get_y(), -1), (rect.get_y() + rect.get_height(), 1)]
                bounds = [self.getPinvalue(rid, b, direc) for (b,direc) in ys]
                upAll = (l.valRange() != bounds)
                if upAll:
                    for path, comp, neg in self.lits[side][l]:
                        ll = copied.getBukElemAt(path)
                        ll.getTerm().setRange(bounds)
                        if comp:
                            ll.flip()
                alright = True
            elif l.typeId() == CatColM.type_id:
                cat = self.getPinvalue(rid, rect.get_y() + rect.get_height()/2.0, 1)
                if cat is not None:
                    upAll = (l.getCat() != cat)
                    if upAll:
                        for path, comp, neg in self.lits[side][l]:
                            copied.getBukElemAt(path).getTerm().setRange(cat)
                    alright = True
            elif l.typeId() == BoolColM.type_id:
                bl = self.getPinvalue(rid, rect.get_y() + rect.get_height()/2.0, 1)
                if bl is not None:
                    upAll = bl != self.lits[side][l][0][-1]
                    if upAll:
                        for path, comp, neg in self.lits[side][l]:
                            copied.getBukElemAt(path).flip()
                    alright = True
            if alright and upAll:
                self.prepared_data["ranges"][rid] = [self.parent.dw.getData().col(side, l.colId()).numEquiv(r) for r in l.valRange()] \
                                   + [self.parent.dw.getData().col(side, l.colId()).width]
                
                self.current_r = self.updateQuery(side, copied, force=True, upAll=upAll)

                
    def emphasizeOn(self, lids, colhigh='#FFFF00'):
        draw_settings = self.getDrawSettings()
        for lid in lids:
            if lid in self.highl:
                continue

            self.highl[lid] = []
            if lid in self.reps:
                self.highl[lid].extend(self.axe.plot(self.prepared_data["xs"],
                                                     self.prepared_data["pos_lids"][self.prepared_data["ycols"],lid],
                                                     color=colhigh, linewidth=1))
            else:
                self.highl[lid].extend(self.axe.plot(self.prepared_data["xs"],
                                                     self.prepared_data["pos_lids"][self.prepared_data["ycols"],lid],
                                                     color=colhigh, linewidth=1, picker=2, gid="%d.%d" % (lid, 1)))

            if len(lids) <= self.max_emphlbl and not lid in self.hight:
                pi = self.suppABCD[lid]
                tag = self.parent.dw.getData().getRName(lid)
                self.hight[lid] = []
                x = self.prepared_data["xs"][-1]+self.margins_sides
                y = self.prepared_data["pos_lids"][self.prepared_data["ycols"][-1],lid]
                self.hight[lid].append(self.axe.annotate(tag, xy=(x,y),
                                                         xycoords='data', xytext=(10, 0), textcoords='offset points',
                                                         color= draw_settings[pi]["color_e"], size=10,
                                                         va="center", backgroundcolor="#FFFFFF",
                                                         bbox=dict(boxstyle="round", facecolor="#FFFFFF",
                                                                   ec=draw_settings[pi]["color_e"]),
                                                         arrowprops=dict(arrowstyle="wedge,tail_width=1.",
                                                                         fc="#FFFFFF", ec=draw_settings[pi]["color_e"],
                                                                         patchA=None, patchB=self.el, relpos=(0.2, 0.5))
                                                         ))


    def additionalElements(self):
        t = self.parent.dw.getPreferences()
        add_box = wx.BoxSizer(wx.HORIZONTAL)
        flags = wx.ALIGN_CENTER | wx.ALL | wx.EXPAND

        add_box.Add(self.MaptoolbarMap, 0, border=3, flag=flags)
        add_box.AddSpacer((20,-1))
        self.buttons = []
        self.buttons.append({"element": wx.Button(self.mapFrame, size=(80,-1), label="Expand"),
                             "function": self.OnExpandSimp})
        self.sld = wx.Slider(self.mapFrame, -1, t["details_level"]["data"], 0, 100, wx.DefaultPosition, (150, -1), wx.SL_HORIZONTAL)
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

    def on_motion(self, event):
        lid = None
        if event.inaxes == self.axe and numpy.abs(numpy.around(event.xdata) - event.xdata) < self.flat_space and event.ydata >= 0 and event.ydata <= 1:
            lid = self.getLidAt(event.ydata, int(numpy.around(event.xdata)))
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

    def getLidAt(self, y, axid):
        if self.prepared_data is not None:
            rlid = numpy.argmin((self.prepared_data["pos_lids"][axid,self.reps]-y)**2)
            lid = self.reps[rlid]
            if abs(self.prepared_data["pos_lids"][axid,lid]-y) < self.margin_hov:
                return lid
        return None

