import wx, numpy, re
# The recommended way to use wx with mpl is with the WXAgg backend. 
import matplotlib
matplotlib.use('WXAgg')

import matplotlib.pyplot as plt
import matplotlib.colors

from .classDrawerBasis import DrawerBasis, DrawerEntitiesTD
import pdb

    
class DrawerClustTD(DrawerEntitiesTD):

    redistrib_colors = True

    norm = matplotlib.colors.Normalize(vmin=0, vmax=1, clip=True)
    mapper_occ = matplotlib.cm.ScalarMappable(norm=norm, cmap="binary")
    
    frac_top = .1
    frac_lbls = .05
    cmap_name = "rainbow"
    def drawPoly(self):
        return False

    def prepareDotsDraw(self, vec, vec_dets, draw_settings):
        return self.prepareDotsDrawOther(vec, vec_dets, draw_settings)
    
    def getVecAndDets(self, inter_params=None):
        vec_org, vec_dets_org = self.getPltDtH().getVecAndDets(inter_params)
        vec, vec_dets = vec_org, vec_dets_org
        uu = numpy.unique(vec_org)
        if self.redistrib_colors and len(uu) < numpy.max(vec_org)+1:
            map_v = -numpy.ones(numpy.max(vec_org)+2, dtype=int)
            i = -1
            for v in uu:
                if v > -1:
                    i += 1  
                    map_v[v] = i
            vec, vec_dets = map_v[vec_org], dict(vec_dets_org)
            vec_dets['min_max'] = (0, numpy.max(map_v))
            vec_dets['binVals'] = numpy.arange(0, vec_dets['min_max'][1]+1, dtype=int)
            vec_dets['binHist'] = numpy.arange(-1, vec_dets['min_max'][1]+1) + .5
            
        self.setElement("vec", vec)
        self.setElement("vec_dets", vec_dets)
        return vec, vec_dets

    def getAxisLims(self):
        return self.getPltDtH().getCoordsExtrema()

    def makeFinish(self, xylims=(0,1,0,1), xybs=(.1,.1)):
        self.axe.axis([xylims[0], xylims[1], xylims[2], xylims[3]])

    
    #### SEC: ACTIONS
    ######################################
    def makeAdditionalElements(self, panel=None):
        if panel is None:
            panel = self.getLayH().getPanel()
        flags = wx.ALIGN_CENTER | wx.ALL # | wx.EXPAND

        buttons = []

        inter_elems = {}
        inter_elems["slide_opac"] = wx.Slider(panel, -1, 10, 0, 100, wx.DefaultPosition, (self.getLayH().sld_w, -1), wx.SL_HORIZONTAL)

        ##############################################
        add_boxB = wx.BoxSizer(wx.HORIZONTAL)
        add_boxB.AddSpacer(self.getLayH().getSpacerWn()/2)

        v_box = wx.BoxSizer(wx.VERTICAL)
        label = wx.StaticText(panel, wx.ID_ANY,u"- opac. disabled +")
        label.SetFont(wx.Font(8, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
        v_box.Add(label, 0, border=1, flag=flags) #, userData={"where": "*"})
        v_box.Add(inter_elems["slide_opac"], 0, border=1, flag=flags) #, userData={"where":"*"})
        add_boxB.Add(v_box, 0, border=1, flag=flags)

        for k, dets in self.getPltDtH().getIParamsChoices():
            inter_elems[k] = wx.Choice(panel, -1)
            inter_elems[k].SetItems(dets["options"])
            if len(dets["options"]) > 0:
                inter_elems[k].SetSelection(0)
        
            add_boxB.AddSpacer(self.getLayH().getSpacerWn())
            label = wx.StaticText(panel, wx.ID_ANY, dets["label"])
            label.SetFont(wx.Font(8, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
            add_boxB.Add(label, 0, border=1, flag=flags)
            add_boxB.Add(inter_elems[k], 0, border=1, flag=flags)   

        add_boxB.AddSpacer(self.getLayH().getSpacerWn()/2)

        self.setElement("buttons", buttons)
        self.setElement("inter_elems", inter_elems)        
        return [add_boxB]


    def plot_block(self, axe, pi, block_data, ord_rids, sizes):
        bckcocc = "#999999"
        # mapper = matplotlib.cm.ScalarMappable(norm=norm, cmap="Purples")

        nbr = len(ord_rids)
        clrs = [self.mapper_occ.to_rgba(block_data["occ_avg"][j]) for j, rid in ord_rids]
        
        e_drawn = []
        e_drawn.append(axe.barh(numpy.ones(nbr)*sizes["left"][pi], numpy.ones(nbr)*sizes["h_occ"], numpy.ones(nbr)*sizes["width"][pi], sizes["btms"], color=clrs, edgecolor=bckcocc, linewidth=.5, linestyle=":", align="edge", zorder=self.zorder_sideplot))
        ## y, width, height, left
        if self.getSettV("blocks_show_values", False):
            for jj, (j, rid) in enumerate(ord_rids):
                c = self.mapper_occ.to_rgba(numpy.around(1-block_data["occ_avg"][j]))
                e_drawn.append(axe.text(sizes["btms"][jj]+.5*sizes["h_occ"], sizes["left"][pi]+.5*sizes["width"][pi], block_data["occ_str"][j], ha="center", va="center", rotation=90, color=c, zorder=self.zorder_sideplot, **self.view.getFontProps()))
        return e_drawn

    def plotMapperHist(self, axe, vec, vec_dets, mapper, nb_bins, corners, draw_settings):                
        with_rlbls = self.getSettV("blocks_show_rids", True)
        x0, x1, y0, y1, bx, by = corners
        nbc = len(vec_dets["binLbls"])
        
        if nbc == 0:
            hci = {"left_edge_map": x0, "right_edge_map": x1, "right_edge_occ": x1, "right_edge_hist": x1,
                   "hedges_hist": [], "vedges_occ": [], "h_occ": 0, "y1_top": y1, "y1_lbls": y1, "y1_blocks": y1, "axe": axe}
            self.setElement("hist_click_info", hci)
            return (x0, x1, y0, y1, bx, by)
            
        
        y1_top, y1_lbls = y1, y1
        f_top = 0
        if with_rlbls:
            f_top += self.frac_lbls
            y1_lbls = y0+(y1_top-y0)*(1-f_top)
        if self.getSettV("blocks_show_emph", True):
            f_top += self.frac_top
        y1 = y0+(y1_top-y0)*(1-f_top)
            
        fracts = [.25, .05] ## ratio bars occ/fixed
        bins_ticks = numpy.arange(nbc)
        tmpb = [b-0.5 for b in bins_ticks]
        tmpb.append(tmpb[-1]+1)

        # norm_bins_ticks = [(bi-tmpb[0])/float(tmpb[-1]-tmpb[0]) * 0.95*float(y1-y0) + y0 + 0.025*float(y1-y0) for bi in bins_ticks]
        # norm_bins = [(bi-tmpb[0])/float(tmpb[-1]-tmpb[0]) * 0.95*float(y1-y0) + y0 + 0.025*float(y1-y0) for bi in tmpb]
        norm_bins_ticks = [(bi-tmpb[0])/float(tmpb[-1]-tmpb[0]) *float(y1-y0) + y0 for bi in bins_ticks]
        norm_bins = [(bi-tmpb[0])/float(tmpb[-1]-tmpb[0]) *float(y1-y0) + y0 for bi in tmpb]
        left = [norm_bins[i] for i in range(nbc)]
        width = [norm_bins[i+1]-norm_bins[i] for i in range(nbc)]

        if vec_dets.get("blocks", False):
            nbr = len(vec_dets["cols"])
            h_occ = (fracts[0]*(x1-x0))/nbr
        else:
            nbr = 0
            h_occ = 0
        h_hist = fracts[1]*(x1-x0)+2*bx
        bottom_occ = x1
        bottom_hist = bottom_occ+nbr*h_occ
        top_hist = bottom_hist+h_hist
        btms = [bottom_occ+i*h_occ for i in range(nbr)]

        bckc = "white"
        bins_lbl = vec_dets["binLbls"]
        #vvmax = int(numpy.max(vec))
        colors = [mapper.to_rgba(i) for i in vec_dets["binVals"]]        
        # colors[-1] = draw_settings["default"]["color_f"]
        
        axe.barh(y0, nbr*h_occ+h_hist, y1-y0, x1, color=bckc, edgecolor=bckc, align="edge", zorder=self.zorder_sideplot)
        # axe.plot([bottom_occ, bottom_occ], [y0, y1-y0], color="blue")
        # axe.plot([bottom_hist, bottom_hist], [y0, y1-y0], color="red")
        # axe.plot([bottom+nbr*h, bottom+nbr*h], [y0, y1-y0], color="red")
        axe.barh(left, numpy.ones(nbc)*h_hist, width, numpy.ones(nbc)*bottom_hist, color=colors, edgecolor=bckc, linewidth=2, align="edge", zorder=self.zorder_sideplot)
        axe.plot([bottom_hist, bottom_hist], [norm_bins[0], norm_bins[-1]], color="black", linewidth=.2, zorder=self.zorder_sideplot)
        axe.plot([bottom_occ, bottom_occ], [norm_bins[0], norm_bins[-1]], color="black", linewidth=.2, zorder=self.zorder_sideplot)

        sizes = {"left": left, "h_occ": h_occ, "width": width, "btms": btms}
        if nbr > 0:
            for pi, i in enumerate(vec_dets["more"]["ord_cids"]):
                self.plot_block(axe, pi, vec_dets["more"][i], vec_dets["more"]["ord_rids"], sizes)

            if with_rlbls:
                for jj, (j, rid) in enumerate(vec_dets["more"]["ord_rids"]):
                    axe.text(bottom_occ+(jj+.5)*h_occ, y1_top-.01*(y1_top-y0), "%s" % rid, va="top", ha="center", rotation=90, bbox=dict(facecolor='white', linewidth=0, alpha=0.85, boxstyle='square,pad=0.1'), zorder=self.zorder_sideplot, **self.view.getFontProps())
                    # axe.text(bottom_occ+(jj+.5)*h_occ, y0 + .05*(y1-y0) + (.9*(y1-y0)*jj)/max(1, nbr-1), "%s" % rid, bbox=dict(facecolor='white', edgecolor='white', alpha=0.75), ha="center", rotation=90)
                
        
        x1 += nbr*h_occ+h_hist #(fracts[0]+fracts[1])*(x1-x0)+2*bx
        hci = {"left_edge_map": x0, "right_edge_map": bottom_occ, "right_edge_occ": bottom_hist, "right_edge_hist": x1,
               "hedges_hist": norm_bins, "vedges_occ": btms, "h_occ": h_occ, "y1_top": y1_top, "y1_lbls": y1_lbls, "y1_blocks": y1, "axe": axe}
        self.setElement("hist_click_info", hci)

        
        axe.set_yticks(norm_bins_ticks)
        axe.set_yticklabels(bins_lbl, **self.view.getFontProps())
        # self.axe.yaxis.tick_right()
        axe.tick_params(direction="inout", left="off", right="on",
                            labelleft="off", labelright="on")
        return (x0, x1, y0, y1_top, bx, by)
        

    def on_click(self, event):
        # print "Event location:", event.xdata, event.ydata
        if self.clickActive() and self.inCapture(event) and self.hasElement("hist_click_info"):
            hci = self.getElement("hist_click_info")
            if event.xdata > hci['right_edge_occ'] and event.xdata < hci['right_edge_hist'] and \
              event.ydata > hci['hedges_hist'][0] and event.ydata < hci['hedges_hist'][-1]:
                self.on_click_hist(event)
            elif event.xdata > hci['right_edge_map'] and event.xdata < hci['right_edge_occ'] and \
              event.ydata > hci['hedges_hist'][0] and event.ydata < hci['hedges_hist'][-1]:
                self.on_click_occ(event)
            elif event.xdata > hci['left_edge_map'] and event.xdata < hci['right_edge_map'] and \
              event.ydata > hci['hedges_hist'][0] and event.ydata < hci['hedges_hist'][-1]:
                lid = self.getLidAt(event.xdata, event.ydata)
                if lid is not None:
                    self.sendEmphasize([lid])

    def on_click_hist(self, event):
        if self.hasElement("hist_click_info"):
            hci = self.getElement("hist_click_info")
            bini = 0
            while event.ydata > hci['hedges_hist'][bini]:
                bini += 1
            bval = self.getElement("vec_dets")["binVals"][bini-1]
            lids = numpy.where(self.getElement("vec") == bval)[0]
            if len(lids) > 0:
                self.sendEmphasize(lids)

    def on_click_occ(self, event):
        if self.hasElement("hist_click_info"):
            hci = self.getElement("hist_click_info")
            bini = 0
            while bini < len(hci['hedges_hist']) and event.ydata > hci['hedges_hist'][bini]:
                bini += 1
            ri = 0
            while ri < len(hci['vedges_occ']) and event.xdata > hci['vedges_occ'][ri]:
                ri += 1
            # status = 1
            # if event.ydata < (hci['hedges_hist'][bini]+hci['hedges_hist'][bini-1])/2.:
            #     status = 0
            bval = self.getElement("vec_dets")["binVals"][bini-1]
            etor = self.getPltDtH().getEtoR()
            lids = numpy.where(etor[:,ri-1] & (self.getElement("vec") == bval))[0]
            if len(lids) > 0:
                self.sendEmphasize(lids)
            
    def makeEmphTag(self, lid):
        tag = "%s" % self.getParentData().getRName(lid)
        if self.getElement("vec") is not None:
            c = self.getElement("vec")[lid]
            if "ddER" in self.getElement("vec_dets"):
                ddE = self.getElement("vec_dets")["ddER"]["E"]
                erep = ddE["rprt"][ddE["to_rep"][lid]]
                tag += "[%d:%d]" % (lid, erep)
            if c >= 0:
                x = self.getElement("vec_dets")["binLbls"][c]
                tag += ": %s" % x.split()[0] 
        return tag


    def emphasizeSpecial(self, turn_on=set(), turn_off=set(), hover=False):
        lids = self.getParentViewsm().getEmphasizedR(vkey=self.getId())
        if self.hasElement("emph_blocks"):
            while len(self.getElement("emph_blocks")) > 0:
                e = self.getElement("emph_blocks").pop()
                try:
                    e.remove()
                except ValueError:
                    pass ## was already removed by a redraw or such

        if len(lids) > 0 and self.hasElement("hist_click_info"):
            hci = self.getElement("hist_click_info")
            if "axe" in hci and (hci["y1_lbls"] > hci["y1_blocks"]):
                nodes = sorted(lids)
                cols = self.getElement("vec_dets")["cols"]
                ord_rids = self.getElement("vec_dets")["more"]["ord_rids"]
                etor = self.getPltDtH().getEtoR()
                block_emph = self.getPltDtH().getClustDetails(nodes, etor, cols)
                sizes = {"left": [hci["y1_blocks"]], "h_occ": hci["h_occ"], "width": [hci["y1_lbls"]-hci["y1_blocks"]], "btms": hci["vedges_occ"]}
                emph_blocks = self.plot_block(hci["axe"], -1, block_emph, ord_rids, sizes)
                self.setElement("emph_blocks", emph_blocks)


    # def update(self, more=None):
    #     if self.view.wasKilled():
    #         return

    #     if self.readyPlot():

    #         inter_params = self.getParamsInter()
    #         if inter_params.get("choice_agg", 0) > 2:
    #             DrawerEntitiesTD.update(self, more)
    #             return
            
    #         self.clearPlot()
    #         inter_params = self.getParamsInter()
    #         vec, vec_dets = self.getVecAndDets(inter_params)
    #         draw_settings = self.getDrawSettings()
    #         selected = self.getPltDtH().getUnvizRows()

    #         cpos = vec_dets["clusters"]["clust_pos"]
    #         pairs = vec_dets["clusters"]["pairs"]
    #         ddER = vec_dets["ddER"]
    #         etor = vec_dets["etor"]
           
    #         na, nb, ds = pairs[0]
    #         ncounts = {na: 1, nb:1}
    #         mid = (cpos[na]+cpos[nb])/2.
    #         self.axe.plot([mid, cpos[na]], [0, ncounts[na]], "b-", linewidth=.1)
    #         self.axe.plot([mid, cpos[nb]], [0, ncounts[nb]], "b-", linewidth=.1)
    #         self.axe.text(mid, 0, "%s" % ds[1], fontsize=2, ha="left", va="bottom", rotation=30)
    #         # self.axe.text(mid, 0, "[0 %s %s]" % (ds[1], ds[2]), fontsize=2, ha="left", va="bottom", rotation=30)            
    #         # self.axe.text(mid, 0, "%d" % ds[3], fontsize=2, ha="right", va="top", rotation=90)
    #         self.axe.text(cpos[na], ncounts[na], "c:%d" % na, fontsize=2, ha="right", va="top", rotation=90)
    #         self.axe.text(cpos[nb], ncounts[nb], "c:%d" % nb, fontsize=2, ha="right", va="top", rotation=90)

    #         for pi, pair in enumerate(pairs[1:]):
    #             na, nb, ds = pair

    #             self.axe.plot([cpos[na], cpos[na]], [ncounts[na], ncounts[na]+1], "b-", linewidth=.1)
    #             self.axe.plot([cpos[na], cpos[nb]], [ncounts[na], ncounts[na]+1], "b-", linewidth=.1)
    #             # self.axe.text(cpos[na], ncounts[na], "[%d %s %s]" % (pi+1, ds[1], ds[2]), fontsize=2, ha="left", va="bottom", rotation=30)
    #             # self.axe.text(cpos[na], ncounts[na], "%d" % ds[3], fontsize=2, ha="right", va="top", rotation=90)

    #             self.axe.text(cpos[na], ncounts[na], "%s" % ds[1], fontsize=2, ha="left", va="bottom", rotation=30)
    #             self.axe.text(cpos[nb], ncounts[na]+1, "c:%d" % nb, fontsize=2, ha="right", va="top", rotation=90)
                
    #             ncounts[na] += 1
    #             ncounts[nb] = ncounts[na]

    #         mx = numpy.max(ncounts.values())            
    #         for na, ncount in ncounts.items():
    #             self.axe.plot([cpos[na], cpos[na]], [ncounts[na], mx], "k-", linewidth=.05)
    #             self.axe.text(cpos[na], mx, " %04d %s %s" % (ddER["E"]["rprt"][na], "".join(["%d" % xx for xx in etor[ddER["E"]["rprt"][na], :]]), ddER["E"]["counts"][na]), fontsize=2, ha="center", va="bottom", rotation=90)

    #         corners = (-3, len(cpos)+2, -1, mx+4, 1, 1)
            
    #         self.makeFinish(corners[:4], corners[4:])   
    #         self.updateEmphasize(review=False)
    #         self.draw()
    #         self.setFocus()
    #     else:
    #         self.plot_void()      
