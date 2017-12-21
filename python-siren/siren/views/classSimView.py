import re
import wx
import numpy
import matplotlib
matplotlib.use('WXAgg')

import os.path, glob

from scipy.sparse.csgraph import shortest_path, minimum_spanning_tree, reconstruct_path
import scipy.spatial.distance
import scipy.misc
# The recommended way to use wx with mpl is with the WXAgg backend. 
# import matplotlib
# matplotlib.use('WXAgg')
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon

# import networkx as nx
# import sklearn.cluster
from classMapView import MapBase

from classLView import LView

import pdb

# def deduplicate_rows(M, ids_sets=None, i=0):
#     if ids_sets is None:
#         ids_sets = [numpy.ones(M.shape[0], dtype=bool)]

#     collect = []
#     for v in numpy.unique(M[:,i]):
#         for ids in ids_sets:
#             iiA = M[:,i]==v
#             if numpy.sum(ids & iiA) > 0:
#                 collect.append(ids & iiA)
#     if M.shape[1] == i+1:
#         return collect
#     else:
#         return deduplicate_rows(M, collect, i+1)
#         pdb.set_trace()
#         MM = numpy.packbits(etor, axis=1)
#         collect = deduplicate_rows(MM)
#         pdb.set_trace()

    
def get_cover_far(dists, nb):
    order = -numpy.ones(dists.shape[0])
    nodesc = numpy.zeros(dists.shape[0], dtype=int)
    dds = numpy.zeros(dists.shape[0], dtype=int)
    uniq_dds = []
    if dists.shape[0] == 1:
        nodesc[0] = 1
        order[0] = 0
        return nodesc, order, dds, uniq_dds
    x,y = numpy.unravel_index(numpy.argmax(dists), dists.shape)
    nodesc[x] = 1
    nodesc[y] = 2
    dds[x] = dists[x,y]
    dds[y] = dists[x,y]
    order[x] = 0.
    order[y] = 1.
    uniq_dds.append(dds[x])
    i = 2
    while numpy.sum(nodesc==0) > 0 and (len(uniq_dds) < nb or nb == 0):
        i+=1
        # z = numpy.argmax(numpy.sum(dists[nodesc>0,:], axis=0))
        z = numpy.argmax(numpy.min(dists[nodesc>0,:], axis=0))
        dds[z] = numpy.min(dists[nodesc>0,z])
        if dds[z] < uniq_dds[-1]:
            uniq_dds.append(dds[z])
        ## print "ASSIGNED", numpy.sum(nodesc==0), z, numpy.min(dists[nodesc>0,z])
        if nodesc[z] > 0:
            print "OUPS! Already picked", z, numpy.where(nodesc>0)
            pdb.set_trace()
        else:
            ww = numpy.max(dists[z, nodesc>0])+1 - dists[z, nodesc>0]
            order[z] = numpy.dot(order[nodesc>0], ww)/numpy.sum(ww)
            nodesc[z] = i
    o = numpy.zeros(numpy.sum(nodesc>0)+1)
    o[nodesc[nodesc>0][numpy.argsort(order[nodesc>0])]-1] = numpy.arange(numpy.sum(nodesc>0))
    return nodesc, o, dds, uniq_dds


class SimView(LView):

    cversion = 0
    TID = "SIM"
    SDESC = "SimLViz"
    ordN = 0
    title_str = "SimTree View"
    typesI = "r"

    
    color_list = [(0.4, 0.165, 0.553), (0.949, 0.482, 0.216), (0.47, 0.549, 0.306), \
                  (0.925, 0.165, 0.224), (0.141, 0.345, 0.643), (0.965, 0.633, 0.267), \
                  (0.627, 0.118, 0.165), (0.878, 0.475, 0.686)]
    color_palet = {'before': (0.2,0.2,0.2),
                   'before_light': (0.2,0.2,0.2),
                   'add': (1,1,0.25),
                   'add_light': (1,1,0.25)}
        
    max_emphlbl = 5
    distc = 1 #5
    NBC = 15
    
    def initVars(self, parent, vid, more=None):
        LView.initVars(self, parent, vid)
        self.clusters = None
        self.choice_dist = None
        self.hist_click_info = {}
        self.vals = None

    def getClusters(self):
        if self.clusters is None:
            self.clusters = self.computeClusters()
        return self.clusters
        
    def computeClusters(self):
        ddER = self.getDeduplicateER()
        nodesc, order, dds, uniq_dds = get_cover_far(ddER["dists"], self.getSettMaxClust())
        return {"nodesc": nodesc, "order": order, "dds": dds, "uniq_dds": uniq_dds, "nbc_max": numpy.sum(nodesc>0)}    

    def getCNb(self):
        if self.choice_dist is not None:
           return self.choice_dist.GetSelection()
        return self.distc
        
    def getValVec(self):
        vec = numpy.empty((0))
        details = {}
        etor = self.getEtoR()
        ddER = self.getDeduplicateER()
        clusters = self.getClusters()

        if clusters is not None:
            # v_out = -10
            # if self.clusters["nbc_max"] > 10 and self.clusters["nbc_max"] < 20:
            v_out = -1           
            ######
            max_dist = clusters["uniq_dds"][self.getCNb()]
            nn = sorted(numpy.where(clusters["dds"]>=max_dist)[0], key=lambda x: clusters["nodesc"][x])
            ## nn = sorted(numpy.where((self.clusters["nodesc"]>0) & (self.clusters["nodesc"]<nb+2))[0], key=lambda x: self.clusters["nodesc"][x])
            orids = sorted(range(len(nn)), key=lambda x: clusters["order"][x])
            details["orids"] = orids
            # print "NBC", v_out, nb, len(nn), nn
            assign_rprt = numpy.argmin(ddER["dists"][:, nn], axis=1)
            ## for i, v in enumerate(assign_rprt):
            for i in range(numpy.max(assign_rprt)+1):
                nodes = numpy.where(assign_rprt==i)[0]
                normm = 1+len(nodes)*numpy.max(ddER["dists"][nodes,:][:,nodes])
                center = numpy.argmin(numpy.max(ddER["dists"][nodes,:][:,nodes], axis=0)+numpy.sum(ddER["dists"][nodes,:][:,nodes], axis=0)/normm)
                max_d = numpy.max(ddER["dists"][nodes[center],nodes])
                occ_avg = numpy.mean(1*etor[ddER["e_rprt"][nodes],:], axis=0)
                occ_cnt = 1*etor[ddER["e_rprt"][nodes[center]],:]
                details[i] = {"center": center, "max_d": max_d, "occ_avg": occ_avg, "occ_cnt": occ_cnt}
                # print i, max_d, nodes[center_n]
                
            if ddER["e_to_rep"] is not None:
                vec = v_out*numpy.ones(ddER["e_to_rep"].shape, dtype=int)
                for i,v in enumerate(assign_rprt):
                    vec[ddER["e_to_rep"] == i] = clusters["order"][v]
            else:
                vec = clusters["order"][assign_rprt]

        vec_dets = {"typeId": 2, "single": True} ### HERE bin lbls        
        vec_dets["binVals"] = numpy.unique(vec[vec>=0]) #numpy.concatenate([numpy.unique(vec[vec>=0]),[-1]])
        vec_dets["binLbls"] = ["c%d %d" % (b,numpy.sum(vec==b)) for b in vec_dets["binVals"]]
        
        nb = [v-0.5 for v in vec_dets["binVals"]]
        nb.append(nb[-1]+1)
        
        vec_dets["binHist"] = nb        
        vec_dets["more"] = details
        vec_dets["min_max"] = (0, numpy.max(clusters["order"])) 
        
        return vec, vec_dets

    def getCoordsXY(self, id):
        if self.coords_proj is None:
            return (0,0)
        else:
            return self.coords_proj[0][:,id,0]
    def getCoordsXYA(self, id):
        return self.getCoordsXY(id)
        
    def getCoords(self, axi=None, ids=None):
        if self.coords_proj is None:
            return self.coords_proj
        if axi is None:
            self.coords_proj[0][:,:,0]
        elif ids is None:
            return self.coords_proj[0][axi,:,0]
        return self.coords_proj[0][axi,ids,0]
    
    def drawMap(self):
        """ Draws the map
        """
        # if self.getParentCoords() is None:
        #     self.coords_proj = None
        #     return
        if not hasattr( self, 'axe' ):
            self.bm, self.bm_args = MapBase.makeBasemapProj(self.getParentPreferences(), self.getParentCoordsExtrema())

            self.coords_proj = self.mapCoords(self.getParentCoords(), self.bm)
            if self.bm is not None:
                self.axe = self.MapfigMap.add_axes([0, 0, 1, 1])
                self.bm.ax = self.axe
            else:
                llon, ulon, llat, ulat = self.getParentCoordsExtrema()
                midlon, midlat = (llon + ulon)/2, (llat + ulat)/2
                mside = max(abs(llon-midlon), abs(llat-midlat))
                self.axe = self.MapfigMap.add_subplot(111,
                                                      xlim=[midlon-1.05*mside, midlon+1.05*mside],
                                                      ylim=[midlat-1.05*mside, midlat+1.05*mside])
            ## self.MapcanvasMap.draw()
            # self.axe = self.MapfigMap.add_axes([llon, llat, ulat-llat, ulon-llon])
            self.prepareInteractive()
            self.MapcanvasMap.draw()
            
    def makeBackground(self):
        MapBase.makeBasemapBack(self.getParentPreferences(), self.bm_args, self.bm)

    def mapCoords(self, coords, bm=None):
        self.mapoly = False #self.getMapPoly() & (min([len(cs) for cs in coords[0]]) > 2)

        nbc_max = max([len(c) for c in coords[0]])
        proj_coords = [numpy.zeros((2, len(coords[0]), nbc_max+1)), []]

        for i in range(len(coords[0])):
            if bm is None:
                p0, p1 = (coords[0][i], coords[1][i])
            else:
                p0, p1 = bm(coords[0][i], coords[1][i])
            proj_coords[1].append(len(p0)+1)
            proj_coords[0][0,i,0] = numpy.mean(p0)
            proj_coords[0][0,i,1:proj_coords[1][-1]] = p0
            proj_coords[0][1,i,0] = numpy.mean(p1)
            proj_coords[0][1,i,1:proj_coords[1][-1]] = p1
        return proj_coords


    def getCMap(self, ltid):
        return plt.get_cmap("rainbow")

    def isReadyPlot(self):
        return self.clusters is not None

    def updateMap(self):
        """ Redraws the map
        """
        if self.isReadyPlot():
            self.clearPlot()

            self.makeBackground()   
            draw_settings = self.getDrawSettings()

            ### SELECTED DATA
            selected = self.getUnvizRows()
            # selected = self.getParentData().selectedRows()
            selp = 0.5
            if self.sld_sel is not None:
                selp = self.sld_sel.GetValue()/100.
            # nbrows = self.getParentData().nbRows()
            # if selp == 0:
            #     nbrows -= len(selected)
            # self.nbc = int(2+(self.grow_nbc**(rnbc))/(self.grow_nbc**10)*(nbrows/2.))
            
            x0, x1, y0, y1 = self.getAxisLims()
            bx, by = (x1-x0)/100.0, (y1-y0)/100.0
            corners = (x0, x1, y0, y1, bx, by)
            vec, vec_dets = self.getValVec()
            self.vals = {"vec": vec, "vec_dets": vec_dets}
            self.dots_draws, mapper = self.prepareSingleVarDots(vec, vec_dets, draw_settings, delta_on=self.getDeltaOn())
                
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
                corners = self.plotMapperHist(self.axe, vec, vec_dets, mapper, -1, corners, draw_settings)

            # self.plotOccs(self.axe, vec, vec_dets, mapper, corners)
            ###########################
            ###########################
            self.makeFinish(corners[:4], corners[4:])
            self.updateEmphasize(review=False)
            self.MapcanvasMap.draw()
            self.MapfigMap.canvas.SetFocus()
        else:
            self.plot_void()      


    def plotMapperHist(self, axe, vec, vec_dets, mapper, nb_bins, corners, draw_settings):

        norm = matplotlib.colors.Normalize(vmin=0, vmax=1, clip=True)
        mappers = [matplotlib.cm.ScalarMappable(norm=norm, cmap="Purples"),
                   matplotlib.cm.ScalarMappable(norm=norm, cmap="binary")]

        x0, x1, y0, y1, bx, by = corners
        fracts = [.25, .05] ## ratio bars occ/fixed
        nbc = len(vec_dets["binLbls"])        
        bins_ticks = numpy.arange(nbc)
        tmpb = [b-0.5 for b in bins_ticks]
        tmpb.append(tmpb[-1]+1)

        # norm_bins_ticks = [(bi-tmpb[0])/float(tmpb[-1]-tmpb[0]) * 0.95*float(y1-y0) + y0 + 0.025*float(y1-y0) for bi in bins_ticks]
        # norm_bins = [(bi-tmpb[0])/float(tmpb[-1]-tmpb[0]) * 0.95*float(y1-y0) + y0 + 0.025*float(y1-y0) for bi in tmpb]
        norm_bins_ticks = [(bi-tmpb[0])/float(tmpb[-1]-tmpb[0]) *float(y1-y0) + y0 for bi in bins_ticks]
        norm_bins = [(bi-tmpb[0])/float(tmpb[-1]-tmpb[0]) *float(y1-y0) + y0 for bi in tmpb]
        left = [norm_bins[i] for i in range(nbc)]
        width = [norm_bins[i+1]-norm_bins[i] for i in range(nbc)]


        nbr = vec_dets["more"][0]["occ_cnt"].shape[0]
        h_occ = (fracts[0]*(x1-x0))/nbr
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
        
        axe.barh(y0, nbr*h_occ+h_hist, y1-y0, x1, color=bckc, edgecolor=bckc)
        # axe.plot([bottom_occ, bottom_occ], [y0, y1-y0], color="blue")
        # axe.plot([bottom_hist, bottom_hist], [y0, y1-y0], color="red")
        # axe.plot([bottom+nbr*h, bottom+nbr*h], [y0, y1-y0], color="red")
        axe.barh(left, numpy.ones(nbc)*h_hist, width, numpy.ones(nbc)*bottom_hist, color=colors, edgecolor=bckc, linewidth=2)
        axe.plot([bottom_hist, bottom_hist], [norm_bins[0], norm_bins[-1]], color="black", linewidth=.2)
        axe.plot([bottom_occ, bottom_occ], [norm_bins[0], norm_bins[-1]], color="black", linewidth=.2)
        

        for pi, i in enumerate(vec_dets["more"]["orids"]):
            clrs = [mappers[int(vec_dets["more"][i]["occ_cnt"][j])].to_rgba(vec_dets["more"][i]["occ_avg"][j]) for j,v in enumerate(vec_dets["more"][i]["occ_avg"])]
            axe.barh(numpy.ones(nbr)*left[pi], numpy.ones(nbr)*h_occ, numpy.ones(nbr)*width[pi], btms, color=clrs, edgecolor=bckc, linewidth=0)
        
        x1 += nbr*h_occ+h_hist #(fracts[0]+fracts[1])*(x1-x0)+2*bx

        self.hist_click_info = {"left_edge_map": x0, "right_edge_map": bottom_occ, "right_edge_occ": bottom_hist, "right_edge_hist": x1,
                                 "hedges_hist": norm_bins, "vedges_occ": btms}
        
        axe.set_yticks(norm_bins_ticks)
        axe.set_yticklabels(bins_lbl) #, size=25) # "xx-large")
        # self.axe.yaxis.tick_right()
        axe.tick_params(direction="inout", left="off", right="on",
                            labelleft="off", labelright="on")
        return (x0, x1, y0, y1, bx, by)
            
    def getAxisLims(self):
        xx = self.axe.get_xlim()
        yy = self.axe.get_ylim()
        return (xx[0], xx[1], yy[0], yy[1])

    def setCurrent(self, reds_map):
        self.reds = dict(reds_map)
        self.srids = [rid for (rid, red) in reds_map]
        self.getEtoR()
        self.getClusters()
        if self.choice_dist is not None:
            opts = self.getDistOpts()
            self.choice_dist.SetItems(opts)
            self.choice_dist.SetSelection(numpy.min([len(opts)-1, self.distc]))
        self.updateMap()

    def getSettMaxClust(self):
        t = self.getParentPreferences()
        try:
            v = t["max_clus"]["data"]
        except:            
            v = self.NBC
        return v

        
    def getDistOpts(self):
        if self.clusters is not None:
            nb = numpy.max(self.clusters["nodesc"])+1
            # return ["%d" % d for d in range(1,nb)]
            return ["%d" % d for d in self.clusters["uniq_dds"]]
        else:
            return ["%d" % d for d in range(1,3)]
        
    def additionalElements(self):
        t = self.parent.dw.getPreferences()
        td_def = 50
        
        flags = wx.ALIGN_CENTER | wx.ALL # | wx.EXPAND

        self.buttons = []
        self.choice_dist = wx.Choice(self.panel, -1)
        self.choice_dist.SetItems(self.getDistOpts())
        self.choice_dist.SetSelection(2)
        self.sld_sel = wx.Slider(self.panel, -1, 10, 0, 100, wx.DefaultPosition, (self.sld_w, -1), wx.SL_HORIZONTAL)

        ##############################################
        add_boxB = wx.BoxSizer(wx.HORIZONTAL)
        add_boxB.AddSpacer((self.getSpacerWn()/2.,-1))

        v_box = wx.BoxSizer(wx.VERTICAL)
        label = wx.StaticText(self.panel, wx.ID_ANY,u"- opac. disabled +")
        label.SetFont(wx.Font(8, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
        v_box.Add(label, 0, border=1, flag=flags) #, userData={"where": "*"})
        v_box.Add(self.sld_sel, 0, border=1, flag=flags) #, userData={"where":"*"})
        add_boxB.Add(v_box, 0, border=1, flag=flags)
        add_boxB.AddSpacer((self.getSpacerWn(),-1))

        v_box = wx.BoxSizer(wx.VERTICAL)
        label = wx.StaticText(self.panel, wx.ID_ANY, "dist. inter c")
        label.SetFont(wx.Font(8, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
        # v_box.Add(label, 0, border=1, flag=flags) #, userData={"where": "*"})
        # v_box.Add(self.sld, 0, border=1, flag=flags) #, userData={"where": "*"})
        # add_boxB.Add(v_box, 0, border=1, flag=flags)
        add_boxB.Add(label, 0, border=1, flag=flags)
        add_boxB.Add(self.choice_dist, 0, border=1, flag=flags)   

        add_boxB.AddSpacer((self.getSpacerWn()/2.,-1))
        
        #return [add_boxbis, add_box]
        return [add_boxB]

    def additionalBinds(self):
        self.choice_dist.Bind(wx.EVT_CHOICE, self.OnUpd)
        #self.sld.Bind(wx.EVT_SCROLL_THUMBRELEASE, self.OnSlide)
        self.sld_sel.Bind(wx.EVT_SCROLL_THUMBRELEASE, self.OnUpd)
        
    def OnUpd(self, event):
        self.updateMap()
        
    def getCanvasConnections(self):
        return [('button_release_event', self.on_click)]
    def inCapture(self, event):
        return self.getCoords() is not None and self.vals is not None and event.inaxes == self.axe
   
    def on_click(self, event):
        # print "Event location:", event.xdata, event.ydata
        if self.clickActive() and self.inCapture(event):
            if event.xdata > self.hist_click_info['right_edge_occ'] and event.xdata < self.hist_click_info['right_edge_hist'] and \
              event.ydata > self.hist_click_info['hedges_hist'][0] and event.ydata < self.hist_click_info['hedges_hist'][-1]:
                self.on_click_hist(event)
            elif event.xdata > self.hist_click_info['right_edge_map'] and event.xdata < self.hist_click_info['right_edge_occ'] and \
              event.ydata > self.hist_click_info['hedges_hist'][0] and event.ydata < self.hist_click_info['hedges_hist'][-1]:
                self.on_click_occ(event)
            elif event.xdata > self.hist_click_info['left_edge_map'] and event.xdata < self.hist_click_info['right_edge_map'] and \
              event.ydata > self.hist_click_info['hedges_hist'][0] and event.ydata < self.hist_click_info['hedges_hist'][-1]:
                lid = self.getLidAt(event.xdata, event.ydata)
                if lid is not None:
                    print "LID: ", lid, 1*self.etor[lid]
                    self.sendEmphasize([lid])

    def on_click_hist(self, event):
        bini = 0
        while event.ydata > self.hist_click_info['hedges_hist'][bini]:
            bini += 1
        bval = self.vals["vec_dets"]["binVals"][bini-1]
        lids = numpy.where(self.vals["vec"] == bval)[0]
        if len(lids) > 0:
            self.sendEmphasize(lids)

    def on_click_occ(self, event):
        bini = 0
        while bini < len(self.hist_click_info['hedges_hist']) and event.ydata > self.hist_click_info['hedges_hist'][bini]:
            bini += 1
        ri = 0
        while ri < len(self.hist_click_info['vedges_occ']) and event.xdata > self.hist_click_info['vedges_occ'][ri]:
            ri += 1
        # status = 1
        # if event.ydata < (self.hist_click_info['hedges_hist'][bini]+self.hist_click_info['hedges_hist'][bini-1])/2.:
        #     status = 0
        bval = self.vals["vec_dets"]["binVals"][bini-1]
        etor = self.getEtoR()
        lids = numpy.where(etor[:,ri-1] & (self.vals["vec"] == bval))[0]
        if len(lids) > 0:
            self.sendEmphasize(lids)

    #### BM            
    def getLidAt(self, x, y):
        ids_drawn = numpy.where(self.dots_draws["draw_dots"])[0]
        if False: #self.drawPoly():
            d = scipy.spatial.distance.cdist(self.getCoordsXY(ids_drawn).T, [(x,y)])
            cands = [ids_drawn[i[0]] for i in numpy.argsort(d, axis=0)[:5]]
            i = 0
            while i < len(cands):
                path = Polygon(self.getCoordsP(cands[i]), closed=True)
                if path.contains_point((x,y), radius=0.0):
                    return cands[i]
                i += 1
        else:
            sz = self.getPlotProp(0, "sz")
            size_dots = self.MapfigMap.get_dpi()*self.MapfigMap.get_size_inches()
            xlims = self.axe.get_xlim()
            ylims = self.axe.get_ylim()
            ### resolution: value delta per figure dot
            res = ((xlims[1]-xlims[0])/size_dots[0], (ylims[1]-ylims[0])/size_dots[1])

            coords = self.getCoordsXY(ids_drawn)
            for ss in range(3):
                sc = sz*(ss+1)
                tX = numpy.where((coords[0]-sc*res[0] <= x) & (x <= coords[0]+sc*res[0]) & (coords[1]-sc*res[1] <= y) & (y <= coords[1]+sc*res[1]))[0]
                # print ss, sc, "-->", tX
                # pdb.set_trace()
                ## print tX
                if len(tX) > 0:
                    # print "FOUND", (coords[0][tX[0]], coords[1][tX[0]]), (x, y), res
                    return ids_drawn[tX[0]]
            # print "NOT FOUND", "---", (x, y), res

        return None

    def hasDotsReady(self):
        return self.dots_draws is not None

    def getAnnXY(self):
        return self.ann_xy

    def drawEntity(self, idp, fc, ec, sz, zo=4, dsetts={}):
        x, y = self.getCoordsXY(idp)
        return self.axe.plot(x, y, mfc=fc, mec=ec, marker=dsetts.get("shape"), markersize=sz, linestyle=dsetts.get("linestyle", 'None'), zorder=zo)
    
    def drawAnnotation(self, xy, ec, tag, xytext=(-10, 15)):
        return [self.axe.annotate(tag, xy=xy, zorder=8,
                                xycoords='data', xytext=xytext, textcoords='offset points',
                                color=ec, size=10, va="center", backgroundcolor="#FFFFFF",
                                bbox=dict(boxstyle="round", facecolor="#FFFFFF", ec=ec),
                                arrowprops=dict(arrowstyle="wedge,tail_width=1.", fc="#FFFFFF", ec=ec,
                                                    patchA=None, patchB=self.el, relpos=(0.2, 0.5)))]
    
    def emphasizeOn(self, lids, hover=False):
        dsetts = self.getDrawSettDef()
        if not self.hasDotsReady():
            return

        hgs = {}
        for lid in self.needingHighlight(lids):
            hg = self.drawEntity(lid, self.getColorHigh(), self.getPlotColor(lid, "ec"), self.getPlotProp(lid, "sz"), self.getPlotProp(lid, "zord"), dsetts)
            if lid not in hgs:
                hgs[lid] = []
            hgs[lid].extend(hg)
            
        for lid in self.needingHighLbl(lids):
            if self.vals["vec"][lid] >= 0:
                tag = "%s: c%s" % (self.getParentData().getRName(lid), self.vals["vec"][lid])
            else:
                tag = self.getParentData().getRName(lid)
            hg = self.drawAnnotation(self.getCoordsXYA(lid), self.getPlotColor(lid, "ec"), tag, self.getAnnXY())
            if lid not in hgs:
                hgs[lid] = []
            hgs[lid].extend(hg)

        self.addHighlighted(hgs, hover)
