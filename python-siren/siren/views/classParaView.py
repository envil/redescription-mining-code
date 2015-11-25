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
from matplotlib.patches import Ellipse
import itertools

from ..reremi.classQuery import Query, BoolTerm, CatTerm, NumTerm
from ..reremi.classRedescription import Redescription
from ..reremi.classData import BoolColM, CatColM, NumColM
from classGView import GView
from classInterObjects import ResizeableRectangle, DraggableRectangle

import pdb

def shuffle_ids(inl, i, cc):
    ii = (7*cc+8*i+1) % len(inl)
    if cc % 2:
        dt = numpy.hstack([inl,inl])[ii:(len(inl)+ii)]
    else:
        dt = numpy.hstack([inl,inl])[(len(inl)+ii):ii:-1]
    tmp = shuffle_order(dt)

    iii = (11*cc+3*i+1) % len(inl)
    ddt = numpy.array(range(len(inl)), dtype=numpy.int)
    if i % 2:
        ddt = numpy.hstack([ddt,ddt])[iii:(len(inl)+iii)]
    else:
        ddt = numpy.hstack([ddt,ddt])[(len(inl)+iii):iii:-1]

    dtmp = shuffle_order(ddt)
    ttt = tmp[dtmp]
    # print "ORD:", ii, i, cc, len(tmp), ttt[:10]
    # pdb.set_trace()
    return ttt

def shuffle_order(ids):
    scores = [max([ii-1 for ii,vv in enumerate(bin(v)) if vv!='1']) for v in range(len(ids))]
    vs = numpy.unique(scores)
    if vs.shape[0] == len(ids):
        return ids[numpy.argsort(scores)]

    ovs = shuffle_order(vs)
    return numpy.hstack([shuffle_order(ids[numpy.where(scores==v)[0]]) for v in ovs])
            
class ParaView(GView):

    TID = "PC"
    SDESC = "Pa.Co."
    ordN = 2
    title_str = "Parallel Coordinates"
    typesI = ["Var", "Reds"]

    rect_halfwidth = 0.05
    rect_alpha = 0.7
    rect_color = "0.7"
    rect_ecolor = "0.3"

    org_spreadL = 0.49 #(2/3.-0.5)
    org_spreadR = 0.49
    flat_space = 0.06
    maj_space = 0.05
    max_group_clustering = 2**8
    nb_clusters = 5
    margins_sides = 0.05
    margins_tb = 0.05
    margin_hov = 0.01
    missing_yy = -0.1
    missing_w = -0.05
        
    def __init__(self, parent, vid, more=None):
        self.reps = set()
        self.current_r = None
        self.prepared_data = {}
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

        if not hasattr( self, 'axe' ):
            self.axe = self.MapfigMap.add_subplot( 111 )

        # self.MapfigMap = plt.figure()
        # self.MapcanvasMap = FigCanvas(self.mapFrame, -1, self.MapfigMap)
        #self.MapfigMap.clear()

        self.el = Ellipse((2, -1), 0.5, 0.5)
        self.axe.add_patch(self.el)

        self.MapfigMap.canvas.mpl_connect('pick_event', self.OnPick)
        self.MapfigMap.canvas.mpl_connect('key_press_event', self.key_press_callback)
        self.MapfigMap.canvas.mpl_connect('button_press_event', self.on_press)
        self.MapfigMap.canvas.mpl_connect('button_release_event', self.on_release)
        self.MapfigMap.canvas.mpl_connect('motion_notify_event', self.on_motion_all)
        self.MapfigMap.canvas.mpl_connect('axes_leave_event', self.on_axes_out)
        self.MapcanvasMap.draw()

    def prepareData(self, red, draw_ppos=None):
        
        lits = [red.queries[side].listLiteralsDetails()  for side in [0,1]]
        litsort = [sorted(lits[side].keys(), key=lambda x: lits[side][x])   for side in [0,1]]
        pos_axis = len(litsort[0])
        
        ranges = self.updateRanges(litsort, lits)
        
        side_cols = []
        lit_str = []
        for side in [0,1]:
            for l in litsort[side]:
                side_cols.append((side, l.colId()))
                lit_str.append(self.parent.dw.getData().getNames(side)[l.colId()])
                # lit_str.append("v%d" % l.colId())
        side_cols.insert(pos_axis, None)

        if self.prepared_data.get("side_cols", None) != side_cols:
            precisions = [10**numpy.floor(numpy.log10(self.parent.dw.getData().col(sc[0], sc[1]).minGap())) for sc in side_cols if sc is not None]

            precisions.insert(pos_axis, 1)
            precisions = numpy.array(precisions)
        
            mat, details, mcols = self.parent.dw.getData().getMatrix(nans=numpy.nan)
            mcols[None] = -1
            cids = [mcols[sc] for sc in side_cols]
            if draw_ppos is not None:
                data_m = numpy.vstack([mat, draw_ppos[self.suppABCD]])[cids]
            else:
                data_m = numpy.vstack([mat, self.suppABCD])[cids]

            limits = numpy.vstack([numpy.nanmin(data_m, axis=1),
                                   numpy.nanmax(data_m, axis=1), precisions, numpy.zeros(precisions.shape)])
            denoms = limits[1,:]-limits[0,:]
            denoms[denoms==0] = 1.
            scaled_m = numpy.vstack([(data_m[i,:]-limits[0,i])/denoms[i] for i in range(data_m.shape[0])])

            ### spreading lines over range
            pos_lids = self.getPos(scaled_m, data_m, limits, denoms, pos_axis)

            qcols = [l for l in litsort[0]]+[None]+[l for l in litsort[1]]
            xlabels = lit_str
            xticks = [x for x,v in enumerate(side_cols)]# if v is not None]
            lit_str.insert(pos_axis, None)
            ycols = [-1]
            xs = [-1]
            for i in range(len(side_cols)):
                ycols.extend([i,i])
                xs.extend([i-self.flat_space, i+self.flat_space])
            ycols.append(-2)
            xs.append(len(side_cols))

            #### ORDERING LINES FOR DETAILS SUBSAMPLING BY GETTING CLUSTERS
            sampling_ord = self.getSamplingOrd(scaled_m, pos_axis)

            return {"pos_axis": pos_axis, "N": data_m.shape[1],
                    "side_cols": side_cols, "qcols": qcols, "lits": lits, "litsort": litsort,
                    "xlabels": xlabels, "xticks": xticks, "ycols": ycols, "xs": xs,
                    "limits": limits, "ranges": ranges, "sampling_ord": sampling_ord,
                    "data_m": data_m, "scaled_m": scaled_m, "pos_lids": pos_lids}

        else:
            limits = self.prepared_data["limits"].copy()
            data_m = self.prepared_data["data_m"].copy()
            scaled_m = self.prepared_data["scaled_m"].copy()

            if draw_ppos is not None:
                data_m[pos_axis,:] = numpy.array([draw_ppos[self.suppABCD]])
            else:
                data_m[pos_axis,:] = numpy.array(self.suppABCD)

            ### test whether support changed
            if numpy.sum(data_m[pos_axis,:] != self.prepared_data["data_m"][pos_axis,:]) > 0:
                limits[:, pos_axis] = numpy.array([numpy.nanmin(data_m[pos_axis,:]), numpy.nanmax(data_m[pos_axis,:]), 1, 0])
                denoms = numpy.ones(limits[1,:].shape)
                denoms[pos_axis] = limits[1,pos_axis]-limits[0,pos_axis]
                scaled_m[pos_axis,:] = (data_m[pos_axis,:]-limits[0,pos_axis])/denoms[pos_axis]

                update_pos = [pos_axis]
                pos_lids = self.prepared_data["pos_lids"].copy()
                tmp_pos_lids = self.getPos(scaled_m, data_m,
                                           limits, denoms, pos_axis, update_pos)
                for i, j in enumerate(update_pos):
                    pos_lids[j,:] = tmp_pos_lids[i,:]
                return {"lits": lits, "litsort": litsort,
                        "limits": limits, "ranges": ranges,
                        "data_m": data_m, "scaled_m": scaled_m, "pos_lids": pos_lids}
            else:
                return {"lits": lits, "litsort": litsort, "ranges": ranges}



    def updateRanges(self, litsort, lits):
        ranges = []
        for side in [0,1]:
            for l in litsort[side]:
                if l.typeId() == BoolColM.type_id:
                    ranges.append([self.parent.dw.getData().col(side, l.colId()).numEquiv(r)
                                   for r in [lits[side][l][0][-1], lits[side][l][0][-1]]])
                else:
                    ranges.append([self.parent.dw.getData().col(side, l.colId()).numEquiv(r)
                                   for r in l.valRange()])
        ranges.insert(len(litsort[0]), [None, None])
        return ranges


    def updateMap(self):
        """ Redraws the map
        """
        if self.current_r is not None:
            self.highl = {}
            self.hight = {}

            red = self.current_r
            draw_settings = self.getDrawSettings()

            self.prepared_data.update(self.prepareData(red, draw_ppos = draw_settings["draw_ppos"]))

            ### SAMPLING ENTITIES
            t = 0.1
            if self.sld is not None:
                td = self.sld.GetValue()
                t = (5*(td/100.0)**8+1*(td/100.0)**2)/6
            self.reps = list(self.prepared_data["sampling_ord"][:int(t*self.prepared_data["N"])])
            self.reps.sort(key=lambda x: draw_settings["draw_pord"][self.suppABCD[x]])
            #self.reps = set(self.prepared_data["sampling_ord"])

            ### SELECTED DATA
            selv = 1*numpy.ones(self.prepared_data["N"])
            selected = self.getUnvizRows()
            # selected = self.parent.dw.getData().selectedRows()
            if self.sld_sel is not None and len(selected) > 0:
                selp = self.sld_sel.GetValue()/100.0
                selv[list(selected)] = selp

            ### PLOTTING
            ### Lines
            self.axe.cla()
            ycols = self.prepared_data["ycols"]
            for r in self.reps:
                # if numpy.sum(~numpy.isfinite(self.prepared_data["data_m"][:,r])) == 0:
                if selv[r] > 0:
                    self.axe.plot(self.prepared_data["xs"], self.prepared_data["pos_lids"][self.prepared_data["ycols"],r],
                                  color=draw_settings[self.suppABCD[r]]["color_l"],
                                  alpha=draw_settings[self.suppABCD[r]]["alpha"]*selv[r], picker=2, gid="%d.%d" % (r, 1))

            ### Bars slidable/draggable rectangles
            rects_drag = {}
            rects_rez = {}
            for i, rg in enumerate(self.prepared_data["ranges"]):
                if rg[0] is not None:
                    bds = self.getYsforRange(i, rg)
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
            extent = [numpy.min(self.prepared_data["xticks"])-1, numpy.max(self.prepared_data["xticks"])+1,
                      self.missing_yy-self.margins_tb, 0]
            self.axe.fill([extent[0], extent[1], extent[1], extent[0]],
                          [extent[2], extent[2], extent[3], extent[3]],
                          color='1', alpha=0.66, zorder=5, ec="1" )
            self.axe.set_xlim([numpy.min(self.prepared_data["xticks"])-1-self.margins_sides,
                               numpy.max(self.prepared_data["xticks"])+1+self.margins_sides])
            if self.parent.dw.getData().hasMissing():
                bot = self.missing_yy-self.margins_tb
            else:
                bot = 0-self.margins_tb
            self.axe.set_ylim([bot,1+self.margins_tb])

            ### Labels
            self.axe.set_xticks(self.prepared_data["xticks"])
            self.axe.set_xticklabels(["" for i in self.prepared_data["xlabels"]]) #, rotation=20, ha="right")
            side = 0
            for lbi, lbl in enumerate(self.prepared_data["xlabels"]):
                if lbl is None:
                    side = 1
                else:
                    tt = self.axe.annotate(lbl,
                                           xy =(self.prepared_data["xticks"][lbi], bot),
                                           xytext =(self.prepared_data["xticks"][lbi]+0.2, bot-0.5*self.margins_tb), rotation=25,
                                           horizontalalignment='right', verticalalignment='top', color=draw_settings[side]["color_l"],
                                           bbox=dict(boxstyle="round", fc="w", ec="none", alpha=0.7), zorder=15
                                           )
                    self.axe.annotate(lbl,
                                      xy =(self.prepared_data["xticks"][lbi], bot),
                                      xytext =(self.prepared_data["xticks"][lbi]+0.2, bot-0.5*self.margins_tb), rotation=25,
                                      horizontalalignment='right', verticalalignment='top', color=draw_settings[side]["color_l"],
                                      bbox=dict(boxstyle="round", fc=draw_settings[side]["color_l"], ec="none", alpha=0.3), zorder=15
                                      )



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

    def getVforY(self, rid, y):
        return self.prepared_data["limits"][0,rid] + y*(self.prepared_data["limits"][1,rid]-self.prepared_data["limits"][0,rid])
    def getYforV(self, rid, v, direc=0):
        return (v-self.prepared_data["limits"][0,rid]+direc*0.5*self.prepared_data["limits"][-1,rid])/(self.prepared_data["limits"][1,rid]-self.prepared_data["limits"][0,rid])
    def getYsforRange(self, rid, range):
        return [self.getYforV(rid, range[0], direc=-1), self.getYforV(rid, range[1], direc=1)]

    def getPinvalue(self, rid, b, direc=0):
        if "qcols" not in self.prepared_data or self.prepared_data["qcols"][rid] is None:
            return 0
        elif self.prepared_data["qcols"][rid].typeId() == NumColM.type_id:
            v = self.getVforY(rid, b)
            prec = -numpy.log10(self.prepared_data["limits"][2, rid])
            #tmp = 10**-prec*numpy.around(v*10**prec)
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
        if self.current_r is not None and "pos_axis" in self.prepared_data:
            pos_axis = self.prepared_data["pos_axis"]
            side = 0
            pos = rid
            if rid > pos_axis:
                side = 1
                pos -= (pos_axis+1)
            copied = self.current_r.queries[side].copy()
            ### HERE RELEASE
            l = self.prepared_data["litsort"][side][pos]
            alright = False
            upAll = False
            if l.typeId() == NumColM.type_id:
                ys = [(rect.get_y(), -1), (rect.get_y() + rect.get_height(), 1)]
                bounds = [self.getPinvalue(rid, b, direc) for (b,direc) in ys]
                upAll = (l.valRange() != bounds)
                if upAll:
                    for path, comp, neg in self.prepared_data["lits"][side][l]:
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
                        for path, comp, neg in self.prepared_data["lits"][side][l]:
                            copied.getBukElemAt(path).getTerm().setRange(cat)
                    alright = True
            elif l.typeId() == BoolColM.type_id:
                bl = self.getPinvalue(rid, rect.get_y() + rect.get_height()/2.0, 1)
                if bl is not None:
                    upAll = bl != self.prepared_data["lits"][side][l][0][-1]
                    if upAll:
                        for path, comp, neg in self.prepared_data["lits"][side][l]:
                            copied.getBukElemAt(path).flip()
                    alright = True
            if alright:
                self.prepared_data["ranges"][rid] = [self.parent.dw.getData().col(side, l.colId()).numEquiv(r) for r in l.valRange()]
                if upAll:
                    self.current_r = self.updateQuery(side, copied, force=True, upAll=upAll)
                else:
                    self.updateMap()
                
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
                                                         color= draw_settings[pi]["color_l"], size=10,
                                                         va="center", backgroundcolor="#FFFFFF",
                                                         bbox=dict(boxstyle="round", facecolor="#FFFFFF",
                                                                   ec=draw_settings[pi]["color_l"]),
                                                         arrowprops=dict(arrowstyle="wedge,tail_width=1.",
                                                                         fc="#FFFFFF", ec=draw_settings[pi]["color_l"],
                                                                         patchA=None, patchB=self.el, relpos=(0.2, 0.5))
                                                         ))


    def additionalElements(self):
        t = self.parent.dw.getPreferences()
        add_box = wx.BoxSizer(wx.HORIZONTAL)
        add_boxA = wx.BoxSizer(wx.VERTICAL)
        add_boxB = wx.BoxSizer(wx.HORIZONTAL)
        flags = wx.ALIGN_CENTER | wx.ALL # | wx.EXPAND

        self.buttons = []
        self.buttons.append({"element": wx.Button(self.panel, size=(self.butt_w,-1), label="Expand"),
                             "function": self.OnExpandSimp})
        self.buttons[-1]["element"].SetFont(wx.Font(8, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
        
        self.sld = wx.Slider(self.panel, -1, t["details_level"]["data"], 0, 100, wx.DefaultPosition, (115, -1), wx.SL_HORIZONTAL)
        self.sld_sel = wx.Slider(self.panel, -1, 10, 0, 100, wx.DefaultPosition, (115, -1), wx.SL_HORIZONTAL)
        
        add_boxB.AddSpacer((self.getSpacerWn()/2.,-1), userData={"where": "*"})
        v_box = wx.BoxSizer(wx.HORIZONTAL)
        v_box.Add(self.boxL, 0, border=0, flag=flags, userData={"where": "*"})
        v_box.Add(self.boxT, 0, border=0, flag=flags, userData={"where": "*"})
        add_boxB.Add(v_box, 0, border=1, flag=flags)
        add_boxB.AddSpacer((self.getSpacerWn(),-1), userData={"where": "*"})

        add_boxA.Add(self.info_title, 0, border=1, flag=flags, userData={"where": "ts"})
        # add_boxB.AddSpacer((self.getSpacerWn(),-1), userData={"where": "ts"})

        v_box = wx.BoxSizer(wx.VERTICAL)
        label = wx.StaticText(self.panel, wx.ID_ANY,u"- opac. disabled +")
        label.SetFont(wx.Font(8, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
        v_box.Add(label, 0, border=1, flag=flags) #, userData={"where": "*"})
        v_box.Add(self.sld_sel, 0, border=1, flag=flags) #, userData={"where": "*"})
        add_boxB.Add(v_box, 0, border=1, flag=flags)
        add_boxB.AddSpacer((self.getSpacerWn(),-1)) #, userData={"where": "*"})
        
        v_box = wx.BoxSizer(wx.VERTICAL)
        label = wx.StaticText(self.panel, wx.ID_ANY, "-        details       +")
        label.SetFont(wx.Font(8, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
        v_box.Add(label, 0, border=1, flag=flags) #, userData={"where": "*"})
        v_box.Add(self.sld, 0, border=1, flag=flags) #, userData={"where": "*"})
        add_boxB.Add(v_box, 0, border=1, flag=flags)
        add_boxB.AddSpacer((self.getSpacerWn()/2.,-1), userData={"where": "*"})
        
        add_boxA.Add(add_boxB, 0, border=1, flag=flags)
        add_boxA.Add(self.MaptoolbarMap, 0, border=1, flag=flags)

        ##############################################

        add_box.Add(add_boxA, 0, border=1, flag=flags)
        add_box.AddSpacer((self.getSpacerWn()/2.,-1))
        
        add_boxB = wx.BoxSizer(wx.VERTICAL)
        add_boxB.Add(self.buttons[-1]["element"], 0, border=1, flag=flags)

        hh_box = wx.BoxSizer(wx.HORIZONTAL)
        hh_box.Add(self.boxPop, 0, border=0, flag=flags, userData={"where":"*"})
        hh_box.Add(self.boxKil, 0, border=0, flag=flags, userData={"where":"*"})
        add_boxB.Add(hh_box, 0, border=1, flag=flags)

        add_box.Add(add_boxB, 0, border=1, flag=flags)
        add_box.AddSpacer((self.getSpacerWn(),-1))

        #return [add_boxbis, add_box]
        return [add_box]

    def additionalBinds(self):
        for button in self.buttons:
            button["element"].Bind(wx.EVT_BUTTON, button["function"])
        self.sld.Bind(wx.EVT_SCROLL_THUMBRELEASE, self.OnSlide)
        self.sld_sel.Bind(wx.EVT_SCROLL_THUMBRELEASE, self.OnSlide)


    def OnSlide(self, event):
        self.updateMap()

    def on_motion(self, event):
        lid = None
        if self.hoverActive() and event.inaxes == self.axe and numpy.abs(numpy.around(event.xdata) - event.xdata) < self.flat_space and event.ydata >= self.missing_yy-.1 and event.ydata <= 1:
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
        if "pos_lids" in self.prepared_data:
            rlid = numpy.argmin((self.prepared_data["pos_lids"][axid,self.reps]-y)**2)
            lid = self.reps[rlid]
            if abs(self.prepared_data["pos_lids"][axid,lid]-y) < self.margin_hov:
                return lid
        return None


    def getPos(self, scaled_m, data_m, limits, denoms, pos_axis, update_pos=None):
        N = data_m.shape[1]
        avgs = numpy.nanmean(numpy.vstack([scaled_m, numpy.zeros_like(scaled_m[0,:])]), axis=0)
        pos_lids = []
        do_all = False
        if update_pos is None:
            do_all = True
            update_pos = range(data_m.shape[0])
        for i in update_pos:
            idsNAN = list(numpy.where(~numpy.isfinite(scaled_m[i,:]))[0])
            nanvs = None
            if len(idsNAN) > 0:
                scaled_m[i,idsNAN] = self.missing_yy
                top, bot = self.missing_yy-len(idsNAN)*self.missing_w/N, \
                           self.missing_yy+len(idsNAN)*self.missing_w/N
                nanvs = numpy.linspace(top, bot, len(idsNAN))

            spreadv = numpy.zeros(data_m[i,:].shape)
            w = abs(limits[2,i])
            limits[0,i]-=0.5*w
            limits[1,i]+=0.5*w
            av_space = w - self.maj_space * denoms[i]
            if av_space > 0:
                limits[-1,i] = av_space
                ww = numpy.array([50, 10, 100])
                if scaled_m.shape[0] == 1:
                    pos_help = numpy.ones(scaled_m[i,:].shape)
                    single = True
                else:
                    if i == 0:
                        cc = [i+1, i+1, pos_axis]
                    elif i == data_m.shape[0]-1:
                        cc = [i-1, i-1, pos_axis]
                    else:
                        cc = [i-1, i+1, pos_axis]
                    pos_help = numpy.dot(ww, scaled_m[cc,:])+avgs
                
                vs = numpy.unique(scaled_m[i,:])
                for v in vs:
                    if v != self.missing_yy:
                        vids = list(numpy.where(scaled_m[i,:]==v)[0])
                        vids.sort(key=lambda x: pos_help[x])
                        top, bot = -len(vids)*av_space*0.5/N, len(vids)*av_space*0.5/N
                        spreadv[vids] += numpy.linspace(top, bot, len(vids))

            pos_lids.append((data_m[i,:]-limits[0,i] + spreadv)/(limits[1,i]-limits[0,i]))
            if nanvs is not None:
                pos_lids[-1][idsNAN] = nanvs

        if do_all:
            spreadL = numpy.zeros(data_m[i,:].shape)
            spreadL[numpy.argsort(pos_lids[0])] = numpy.linspace(0.5-self.org_spreadL, 0.5+self.org_spreadL, N)
            spreadR = numpy.zeros(data_m[i,:].shape)
            spreadR[numpy.argsort(pos_lids[-1])] = numpy.linspace(0.5-self.org_spreadR, 0.5+self.org_spreadR, N)

            pos_lids.extend([spreadR,spreadL])
        pos_lids = numpy.vstack(pos_lids)
        return pos_lids

    def getSamplingOrd(self, scaled_m, pos_axis):
        sorting_samples = numpy.zeros(scaled_m[0,:].shape)
        left_over = []
        for v in numpy.unique(scaled_m[pos_axis,:]):
            ids = numpy.where(scaled_m[pos_axis,:]==v)[0]
            # numpy.random.shuffle(ids)
            rg = ids.shape[0]/self.max_group_clustering+1
            for i in range(rg):
                if i == 0 and ids.shape[0] < self.nb_clusters:
                    sorting_samples[ids] = -0.1*v+float(i)/rg
                    break
                elif i > 0 and ((i+1)*self.max_group_clustering - ids.shape[0]) > 2*self.max_group_clustering/3.:
                    left_over.extend(ids[i*self.max_group_clustering:])
                    break
                else:
                    subids = ids[i*self.max_group_clustering:(i+1)*self.max_group_clustering]
                    d = scipy.spatial.distance.pdist(scaled_m[:,subids].T)
                    Z = scipy.cluster.hierarchy.linkage(d)
                    T = scipy.cluster.hierarchy.fcluster(Z, self.nb_clusters, criterion="maxclust")        
                    for cc in numpy.unique(T):
                        ci = shuffle_ids(numpy.where(T==cc)[0], i, cc)
                        #numpy.random.shuffle(ci)
                        sorting_samples[subids[ci]] = -0.1*v+float(i)/rg+10*numpy.arange(1., ci.shape[0]+1)
        if len(left_over) > 0:
            subids = numpy.array(left_over)
            d = scipy.spatial.distance.pdist(scaled_m[:,subids].T)
            Z = scipy.cluster.hierarchy.linkage(d)
            T = scipy.cluster.hierarchy.fcluster(Z, self.nb_clusters, criterion="maxclust")
            for cc in numpy.unique(T):
                ci = shuffle_ids(numpy.where(T==cc)[0], 0, cc)
                #numpy.random.shuffle(ci)
                sorting_samples[subids[ci]] = v+10*numpy.arange(1., ci.shape[0]+1)
        sampling_ord = numpy.argsort(sorting_samples)
        return sampling_ord


