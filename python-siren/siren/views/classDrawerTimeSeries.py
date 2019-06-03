import wx
### from wx import ALIGN_BOTTOM, ALIGN_CENTER, ALIGN_LEFT, ALIGN_RIGHT, ALL, HORIZONTAL, VERTICAL, ID_ANY, EXPAND, RAISED_BORDER, SL_HORIZONTAL
### from wx import EVT_BUTTON, EVT_SCROLL_THUMBRELEASE, FONTFAMILY_DEFAULT, FONTSTYLE_NORMAL, FONTWEIGHT_NORMAL
### from wx import BoxSizer, Button, CallLater, CheckBox, Choice, DefaultPosition, Font, NewId, Panel,  Slider, StaticText, TextCtrl

import numpy
# The recommended way to use wx with mpl is with the WXAgg backend. 
# import matplotlib
# matplotlib.use('WXAgg')

from ..reremi.classRedescription import Redescription
from ..reremi.classSParts import SSetts
from classDrawerBasis import DrawerEntitiesTD
from classInterObjects import ResizeableRectangle, DraggableRectangle

import pdb

class DrawerRedTimeSeries(DrawerEntitiesTD):

    def getCoordsY(self):
        return self.getPltDtH().getCoordsY()

    def getCoordsXYA(self, idp):
        return self.getPltDtH().getCoordsXYA(idp)
    def getCoordsXY(self, idp):
        return self.getPltDtH().getCoordsXY(idp)
    def getCoords(self, axi=None, ids=None):
        return self.getPltDtH().getCoords(axi, ids)
    
    def getAxisLims(self):
        return self.getPltDtH().getCoordsExtrema()[:-1]+(1.2,)

    rect_alpha = 0.7
    rect_color = "0.7"
    rect_ecolor = "0.3"

    margins_sides = 0.05
    margins_tb = 0.05
    margin_hov = 0.01
    missing_yy = -0.1
    missing_w = -0.05

    ann_to_right = True
    ann_xy = (-15, -15)

    def __init__(self, view):
        self.view = view
        self.prepared_data = {}
        self.ri = None
        self.elements = {"active_info": False, "act_butt": [1],
                         "reps": set(), "ticks_ann": []}
        self.initPlot()
        self.plot_void()


    def isReadyPlot(self):
        return self.getPltDtH().getRed() is not None
        
    def getCanvasConnections(self):
        return [ ('draw_event', self.on_draw),
                ('key_press_event', self.key_press_callback),
                ('button_press_event', self.on_press),
                ('button_release_event', self.on_release),
                ('motion_notify_event', self.on_motion_all),
                ('axes_leave_event', self.on_axes_out),
                ('pick_event', self.onpick)]

    def prepareData(self, lits):

        pos_axis = len(lits[0])
        ranges = self.updateRanges(lits)
        
        side_cols = []
        lit_str = []
        for side in [0,1]:
            for l, dets in lits[side]:
                side_cols.append((side, l.colId()))
                lit_str.append(self.getParentData().getNames(side)[l.colId()])
        
        suppABCD = self.getPltDtH().getSuppABCD()

        precisions = numpy.array([10**numpy.floor(numpy.log10(self.getParentData().col(sc[0], sc[1]).minGap())) for sc in side_cols if sc is not None])


        mat, details, mcols = self.getParentData().getMatrix(nans=numpy.nan)
        cids = [mcols[sc] for sc in side_cols]
        data_m = mat[cids]

        limits = numpy.vstack([numpy.nanmin(data_m, axis=1),
                               numpy.nanmax(data_m, axis=1), precisions, numpy.zeros(precisions.shape)])
        denoms = limits[1,:]-limits[0,:]
        denoms[denoms==0] = 1.
        scaled_m = numpy.vstack([(data_m[i,:]-limits[0,i])/denoms[i] for i in range(data_m.shape[0])])
        
        qcols = [l[0] for l in lits[0]]+[l[0] for l in lits[1]]

        #### ORDERING LINES FOR DETAILS SUBSAMPLING BY GETTING CLUSTERS
        return {"pos_axis": pos_axis, "N": data_m.shape[1],
                "side_cols": side_cols, "qcols": qcols, "lits": lits, "labels": lit_str,
                "limits": limits, "ranges": ranges,
                "data_m": data_m, "scaled_m": scaled_m}


    def updateRanges(self, lits):
        ranges = []
        data = self.getParentData()
        for side in [0,1]:
            for l, dets in lits[side]:
                if l.isAnon():
                    #### ANONYMOUS
                    if self.isTypeId(l.typeId(), "Boolean"):
                        ranges.append([data.col(side, l.colId()).numEquiv(r)
                                       for r in [dets[0][-1], dets[0][-1]]])
                    elif self.isTypeId(l.typeId(), "Categorical"):
                        ranges.append([0, 0])
                    elif self.isTypeId(l.typeId(), "Numerical"):
                        ranges.append(data.col(side, l.colId()).getRange())
                    else:
                        ranges.append([None, None])
                    # ranges.append([None, None])

                elif self.isTypeId(l.typeId(), "Boolean"):
                    ranges.append([data.col(side, l.colId()).numEquiv(r)
                                   for r in [dets[0][-1], dets[0][-1]]])                        
                else:
                    ranges.append([data.col(side, l.colId()).numEquiv(r)
                                   for r in l.valRange()])
        return ranges

    def getVecAndDets(self, inter_params=None):
        vec = self.getPltDtH().getSuppABCD()
        vec_dets = self.getPltDtH().getVecDets(inter_params)
        return vec, vec_dets
    
    def update(self, more=None):
        if self.view.wasKilled():
            return

        if self.isReadyPlot():

            self.clearPlot()
            self.makeBackground()

            inter_params = self.getParamsInter()
            vec, vec_dets = self.getVecAndDets(inter_params)
            red = self.getPltDtH().getRed()
            suppABCD = self.getPltDtH().getSuppABCD()
            draw_settings = self.getDrawSettings()
            selected = self.getPltDtH().getUnvizRows()
            
            x0, x1, y0, y1 = self.getAxisLims()
            bx, by = (x1-x0)/100.0, (y1-y0)/100.0
            corners = (x0, x1, y0, y1, bx, by)
            
            self.dots_draw, mapper = self.prepareDotsDraw(vec, vec_dets, draw_settings)
            self.dots_draw["sz_dots"] /= 10. 
            if len(selected) > 0 and "fc_dots" in self.dots_draw:
                selp = inter_params.get("slide_opac", 50)/100.
                self.dots_draw["fc_dots"][numpy.array(list(selected)), -1] *= selp
                self.dots_draw["ec_dots"][numpy.array(list(selected)), -1] *= selp

            if "draw_dots" in self.dots_draw:
                draw_indices = numpy.where(self.dots_draw["draw_dots"])[0]
            else:
                draw_indices = []
            if self.plotSimple(): ##  #### NO PICKER, FASTER PLOTTING.
                self.plotDotsSimple(self.getAxe(), self.dots_draw, draw_indices, draw_settings)
            
            lits = [sorted(red.queries[side].listLiteralsDetails().items(), key=lambda x:x[1]) for side in [0,1]]

            self.prepared_data.update(self.prepareData(lits))
            coord = self.getPltDtH().getCoords()
            self.prepared_data["coord"] = coord
            self.prepared_data["ord_ids"] = numpy.argsort(coord)

            ### PLOTTING
            ### Lines
            nbv = len(self.prepared_data["labels"])
            yticks = []
            for vi, vs in enumerate(self.prepared_data["labels"]):
                self.axe.plot(coord[self.prepared_data["ord_ids"]], (self.prepared_data["scaled_m"][vi, self.prepared_data["ord_ids"]]+vi)/nbv, color="#444444", linewidth=1, zorder=1)
                yticks.append((.5+vi)/nbv)
            ### Labels
            self.axe.set_yticks(yticks)
            self.axe.set_yticklabels(self.prepared_data["labels"])

            if red.hasCondition():
                qC = red.getQueryC()
                if len(qC) == 1:
                    rC = [lC.valRange() for lC  in qC.invLiterals()][0]
                    bot, top = numpy.maximum(x0, rC[0]), numpy.minimum(x1, rC[1])
                    rects = self.axe.bar(bot, y1-y0, top-bot, y0,
                                         edgecolor=self.rect_ecolor, linewidth=0, color=self.rect_color, alpha=self.rect_alpha, zorder=-1)
                    
            
            ### Bars slidable/draggable rectangles
            rects_drag = {}
            rects_rez = {}
            for i, rg in enumerate(self.prepared_data["ranges"]):
                if rg[0] is not None:
                    bds = self.getYsforRange(i, rg)
                    rects = self.axe.bar(x1-x0, bds[1]-bds[0], x0, bds[0],
                                         edgecolor=self.rect_ecolor, linewidth=0, color=self.rect_color, alpha=self.rect_alpha, zorder=-1)

                    if self.prepared_data["qcols"][i] is not None:
                        if self.isTypeId(self.prepared_data["qcols"][i].typeId(), "Numerical"):
                            rects_rez[i] = rects[0]
                        elif self.isTypeId(self.prepared_data["qcols"][i].typeId(), ["Boolean", "Categorical"]):
                            rects_drag[i] = rects[0]

            self.drs = []
            self.ri = None
            for rid, rect in rects_rez.items():
                dr = ResizeableRectangle(rect, rid=rid, callback=self.receive_release, \
                                                  pinf=self.getPinvalue, annotation=None) #self.annotation)
                self.drs.append(dr)

            for rid, rect in rects_drag.items():
                dr = DraggableRectangle(rect, rid=rid, callback=self.receive_release, \
                                                  pinf=self.getPinvalue, annotation=None) #self.annotation)
                self.drs.append(dr)

            #########
            # if self.getParentData().hasMissing():
            #     bot = self.missing_yy-self.margins_tb
            # else:
            #     bot = 0-self.margins_tb

            # height = 1.

            # ### Labels
            # self.axe.set_xticks(self.prepared_data["xticks"])
            # self.axe.set_xticklabels(["" for i in self.prepared_data["xlabels"]])
            # self.axe.tick_params(labelsize=self.view.getFontSizeProp())

            # side = 0
            # ticks_ann = []
            # for lbi, lbl in enumerate(self.prepared_data["xlabels"]):
            #     if lbl is None:
            #         side = 1
            #     else:
            #         tt = self.axe.annotate(lbl,
            #                                xy =(self.prepared_data["xticks"][lbi], bot),
            #                                xytext =(self.prepared_data["xticks"][lbi]+0.2, bot-0.5*self.margins_tb), rotation=25,
            #                                horizontalalignment='right', verticalalignment='top', color=draw_settings[side]["color_e"],
            #                                bbox=dict(boxstyle="round", fc="w", ec="none", alpha=0.7), zorder=15, **self.view.getFontProps()
            #                                )
            #         ticks_ann.append(tt)
                    
            #         self.axe.annotate(lbl,
            #                           xy =(self.prepared_data["xticks"][lbi], bot),
            #                           xytext =(self.prepared_data["xticks"][lbi]+0.2, bot-0.5*self.margins_tb), rotation=25,
            #                           horizontalalignment='right', verticalalignment='top', color=draw_settings[side]["color_e"],
            #                           bbox=dict(boxstyle="round", fc=draw_settings[side]["color_e"], ec="none", alpha=0.3), zorder=15, **self.view.getFontProps()
            #                           )
            # self.setElement("ticks_ann", ticks_ann)
            # # borders_draw = [numpy.min(self.prepared_data["xticks"])-1-self.margins_sides, bot,
            # #                 numpy.max(self.prepared_data["xticks"])+1+self.margins_sides, 1+self.margins_tb]

            # self.axe.set_xlim([numpy.min(self.prepared_data["xticks"])-1-self.margins_sides,
            #                    numpy.max(self.prepared_data["xticks"])+1+self.margins_sides])
            # self.axe.set_ylim([bot,height+self.margins_tb])            

            self.makeFinish(corners[:4], corners[4:])   
            self.updateEmphasize(review=False)
            self.draw()
            self.setFocus()
            # ### SPECIAL PLOTTING
            # self.sendEmphasize(foc_points)
                        
    def on_press(self, event):
        if self.inCapture(event):
            i = 0
            while self.ri is None and i < len(self.drs):
                contains, attrd = self.drs[i].contains(event)
                if contains:
                    self.ri = i
                i+=1
            if self.ri is not None:
                self.delInfoText()
                self.drs[self.ri].do_press(event)

    def on_release(self, event):
        if self.inCapture(event):
            if self.ri is not None:
                self.drs[self.ri].do_release(event)
            else:
                self.on_click(event)
            self.ri = None
        
    def on_axes_out(self, event):
        if self.ri is not None:
            self.drs[self.ri].do_release(event)
        self.ri = None

    def on_motion_all(self, event):
        if self.inCapture(event) and self.ri is not None:
            self.drs[self.ri].do_motion(event)
        else:
            self.on_motion(event)
            
    def getVforY(self, rid, y):
        return (y*len(self.prepared_data["labels"])-rid)*(self.prepared_data["limits"][1,rid]-self.prepared_data["limits"][0,rid])+self.prepared_data["limits"][0,rid] #-direc*0.5*self.prepared_data["limits"][-1,rid]
    def getYforV(self, rid, v, direc=0):
        return (rid+(v-self.prepared_data["limits"][0,rid]+direc*0.5*self.prepared_data["limits"][-1,rid])/(self.prepared_data["limits"][1,rid]-self.prepared_data["limits"][0,rid]))/len(self.prepared_data["labels"])
    def getYsforRange(self, rid, range):
        ### HERE fix CAT
        return [self.getYforV(rid, range[0], direc=-1), self.getYforV(rid, range[-1], direc=1)]
     
    def getPinvalue(self, rid, b, direc=0):
        if "qcols" not in self.prepared_data or self.prepared_data["qcols"][rid] is None:
            return 0
        elif self.isTypeId(self.prepared_data["qcols"][rid].typeId(), "Numerical"):
            v = self.getVforY(rid, b)
            prec = int(-numpy.log10(self.prepared_data["limits"][2, rid]))
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
        elif self.isTypeId(self.prepared_data["qcols"][rid].typeId(), ["Boolean", "Categorical"]):
            v = int(round(b*(self.prepared_data["limits"][1, rid]-self.prepared_data["limits"][0,rid])+self.prepared_data["limits"][0, rid]))
            if v > self.prepared_data["limits"][1, rid]:
                v = self.prepared_data["limits"][1, rid]
            elif v < self.prepared_data["limits"][0, rid]:
                v = self.prepared_data["limits"][0, rid]
            side = 0
            if self.prepared_data["pos_axis"] < rid:
                side = 1
            c = self.getParentData().col(side, self.prepared_data["qcols"][rid].colId())
            if c is not None:
                return c.getValFromNum(v)

    def getPosInfo(self, x, y):
        rid = int(numpy.rint(x))
        if "qcols" in self.prepared_data and rid >= 0 and rid < len(self.prepared_data["qcols"]) and self.prepared_data["qcols"][rid] is not None:
            return self.prepared_data["xlabels"][rid], self.getPinvalue(rid, y)
        return rid, None
    def getPosInfoTxt(self, x, y):
        k,v = self.getPosInfo(x, y)
        if v is not None:
            return "%s=%s" % (k,v)

            
    def receive_release(self, rid, rect):
        if self.isReadyPlot() and "pos_axis" in self.prepared_data:
            pos_axis = self.prepared_data["pos_axis"]
            side = 0
            pos = rid
            if rid >= pos_axis:
                side = 1
                pos -= pos_axis
            copied = self.getPltDtH().getRed().queries[side].copy()
            ### HERE RELEASE
            l, dets = self.prepared_data["lits"][side][pos]
            alright = False
            upAll = False

            if l.isAnon():
                bounds = None 
                if self.isTypeId(l.typeId(), "Numerical"):
                    ys = [(rect.get_y(), -1), (rect.get_y() + rect.get_height(), 1)]
                    bounds = [self.getPinvalue(rid, b, direc) for (b, direc) in ys]
                else:
                    cat = self.getPinvalue(rid, rect.get_y() + rect.get_height()/2.0, 1)
                    if cat is not None:
                        bounds = set([cat])
                if bounds is not None:
                    upAll = True
                    for path, comp, neg in dets:
                        ll = copied.getBukElemAt(path)
                        newE = ll.getAdjusted(bounds)
                        if newE is not None:
                            copied.setBukElemAt(newE, path)
                        self.prepared_data["lits"][side][pos] = (newE, self.prepared_data["lits"][side][pos][1])
                alright = True

                
            elif self.isTypeId(l.typeId(), "Numerical"):
                ys = [(rect.get_y(), -1), (rect.get_y() + rect.get_height(), 1)]
                bounds = [self.getPinvalue(rid, b, direc) for (b, direc) in ys]
                upAll = (l.valRange() != bounds)
                if upAll:
                    for path, comp, neg in dets:
                        ll = copied.getBukElemAt(path)
                        ll.getTerm().setRange(bounds)
                        if comp:
                            ll.flip()
                alright = True
            elif self.isTypeId(l.typeId(), "Categorical"):
                cat = self.getPinvalue(rid, rect.get_y() + rect.get_height()/2.0, 1)
                if cat is not None:
                    upAll = (l.getTerm().getCat() != cat)
                    if upAll:
                        for path, comp, neg in dets:
                            ### HERE CAT FIX
                            copied.getBukElemAt(path).getTerm().setRange(set([cat]))
                alright = True
            elif self.isTypeId(l.typeId(), "Boolean"):
                bl = self.getPinvalue(rid, rect.get_y() + rect.get_height()/2.0, 1)
                if bl is not None:
                    upAll = bl != dets[0][-1]
                    if upAll:
                        for path, comp, neg in dets:
                            copied.getBukElemAt(path).flip()
                    alright = True                    
                    
            if alright:
                self.prepared_data["ranges"][rid] = [self.getParentData().col(side, l.colId()).numEquiv(r) for r in l.valRange()]
                if upAll:
                    self.getPltDtH().updateQuery(side, copied, force=True, upAll=upAll)
                else:
                    self.update()       
    def makeAdditionalElements(self, panel=None):
        if panel is None:
            panel = self.getLayH().getPanel()
        flags = wx.ALIGN_CENTER | wx.ALL # | wx.EXPAND
        
        buttons = []
        buttons.append({"element": wx.Button(panel, size=(self.getLayH().butt_w,-1), label="Expand"),
                        "function": self.view.OnExpandSimp})
        buttons[-1]["element"].SetFont(wx.Font(8, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))

        inter_elems = {}

        ##############################################
        add_boxB = wx.BoxSizer(wx.HORIZONTAL)
        add_boxB.AddSpacer((self.getLayH().getSpacerWn()/2.,-1))

        #add_boxB.AddSpacer((self.getLayH().getSpacerWn(),-1))
        add_boxB.Add(buttons[-1]["element"], 0, border=1, flag=flags)

        add_boxB.AddSpacer((self.getLayH().getSpacerWn()/2.,-1))

        self.setElement("buttons", buttons)
        self.setElement("inter_elems", inter_elems)        
        return [add_boxB]

    def getLidAt(self, x, y):
        if "coord" in self.prepared_data and abs(self.getCoordsY()-y) < self.margin_hov:
            return numpy.argmin((self.prepared_data["coord"]-x)**2)
        return None

    ###event when we click on label
    def onpick(self, event):
        artist = event.artist
        pos = round(artist.xy[0])
        updown = artist.xy[1] < 1.2
        if "pos_hids" in self.prepared_data and (pos, updown) in self.prepared_data["pos_hids"]:
            self.sendEmphasize(self.prepared_data["pos_hids"][(pos, updown)])
             
    def on_draw(self, event):
        pass
    
