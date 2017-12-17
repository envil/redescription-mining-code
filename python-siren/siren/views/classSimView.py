import re
import wx
import numpy

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

def get_cover_far(dists, nb):
    order = -numpy.ones(dists.shape[0])
    nodesc = numpy.zeros(dists.shape[0], dtype=int)
    if dists.shape[0] == 1:
        nodesc[0] = 1
        order[0] = 0
        return nodesc, order
    x,y = numpy.unravel_index(numpy.argmax(dists), dists.shape)
    nodesc[x] = 1
    nodesc[y] = 2
    order[x] = 0.
    order[y] = 1.
    i = 2
    while numpy.sum(nodesc==0) > 0 and i < nb:
        i+=1
        # z = numpy.argmax(numpy.sum(dists[nodesc>0,:], axis=0))
        z = numpy.argmax(numpy.min(dists[nodesc>0,:], axis=0))
        if nodesc[z] > 0:
            print "OUPS! Already picked", z, numpy.where(nodesc>0)
            pdb.set_trace()
        else:
            ww = numpy.max(dists[z, nodesc>0])+1 - dists[z, nodesc>0]
            order[z] = numpy.dot(order[nodesc>0], ww)/numpy.sum(ww)
            nodesc[z] = i
    o = numpy.zeros(numpy.sum(nodesc>0)+1)
    o[nodesc[nodesc>0][numpy.argsort(order[nodesc>0])]-1] = numpy.arange(numpy.sum(nodesc>0))
    return nodesc, o


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
    pick_sz = 5
    wait_delay = 300    
    distc = 5
    NBC = 30
    
    def initVars(self, parent, vid, more=None):
        LView.initVars(self, parent, vid)
        self.clusters = None
        self.choice_dist = None
            
    def computeClusters(self):
        #### HERE: DO BETTER THAN ZIP DIST 0
        rb = {}        
        for x,y in zip(*numpy.where(numpy.triu(numpy.dot(1.-self.etor.T, 1.-self.etor) + numpy.dot(self.etor.T*1., self.etor*1.),1)>=self.etor.shape[0])):
            rb[x] = y
        keep_rs = [i for i in range(self.etor.shape[1]) if i not in rb]

        etor = self.etor[:,keep_rs]
        c01 = numpy.dot(1.-etor, 1.-etor.T) + numpy.dot(etor*1., etor.T*1.)
        nbr = etor.shape[1]
        eb = {}
        for x,y in zip(*numpy.where(numpy.triu(c01,1)>=nbr)):
            eb[x] = y            
        keep_es = numpy.array([i for i in range(etor.shape[0]) if i not in eb and numpy.sum(etor[i,:])>0])
        nb_keep_es = len(keep_es)
        e_to_rep = -numpy.ones(self.etor.shape[0])
        e_to_rep[keep_es] = numpy.arange(len(keep_es))
        efrm, ett = zip(*eb.items())
        e_to_rep[numpy.array(efrm)] = e_to_rep[numpy.array(ett)]

        dists = nbr - c01[keep_es,:][:,keep_es]
        nodesc, order = get_cover_far(dists, self.NBC)

        return {"e_rprt": keep_es, "r_to_rep": rb, "e_to_rep": e_to_rep,
                "nodesc": nodesc, "dists": dists, "order": order, "nbc_max": numpy.sum(nodesc>0)}    
    
    def getValVec(self):
        vec = numpy.empty((0))
        max_ds = []
        if self.clusters is not None:
            v_out = -10
            if self.clusters["nbc_max"] > 10 and self.clusters["nbc_max"] < 20:
                v_out = -1
            nb = self.distc
            ######
            nn = sorted(numpy.where((self.clusters["nodesc"]>0) & (self.clusters["nodesc"]<nb+2))[0], key=lambda x: self.clusters["nodesc"][x])
            # print "NBC", v_out, nb, len(nn), nn
            assign_rprt = numpy.argmin(self.clusters["dists"][:, nn], axis=1)
            for i in range(numpy.max(assign_rprt)+1):
                nodes = numpy.where(assign_rprt==i)[0]
                center_n = numpy.argmin(numpy.max(self.clusters["dists"][nodes,:][:,nodes], axis=0))
                max_ds.append(numpy.max(self.clusters["dists"][nodes[center_n],nodes]))
                # print i, max_d, nodes[center_n]
            
            if self.clusters["e_to_rep"] is not None:
                vec = v_out*numpy.ones(self.clusters["e_to_rep"].shape, dtype=int)
                for i,v in enumerate(assign_rprt):
                    if numpy.sum(self.clusters["e_to_rep"] == i) == 0:
                        pdb.set_trace()
                    # elif numpy.sum(self.clusters["e_to_rep"] == i) == 1:
                    #     vec[self.clusters["e_to_rep"] == i] = -2
                    else:
                        vec[self.clusters["e_to_rep"] == i] = self.clusters["order"][v]
            else:
                vec = self.clusters["order"][assign_rprt]

            ## vec[vec==-2] = self.clusters["matrix_ass"].shape[0]
        # if numpy.min(vec) == -1:
        #     vec += 1 

        # adj = numpy.dot(self.etor*1., self.etor.T*1.)
        # clus = sklearn.cluster.AgglomerativeClustering(n_clusters=self.nbc)
        # clus.fit(adj)
        # vec = clus.fit_predict(adj)
        # G=nx.from_numpy_matrix(adj)
        # nx.draw_spring(G, ax=self.axe)

        vec_dets = {"typeId": 2, "single": True} ### HERE bin lbls        
        # bins_ticks = numpy.unique(vec)
        # bins_ticks = numpy.arange(-2, numpy.max(vec)+1)
        vec_dets["binVals"] = numpy.unique(vec[vec>=0])
        if len(vec_dets["binVals"]) < 50:
            vec_dets["binLbls"] = ["c%d (d=%d)" % (b, max_ds[ii]) for (ii,b) in enumerate(vec_dets["binVals"])]
        else:
            vec_dets["binLbls"] = ["" for b in vec_dets["binVals"]]

        nb = [v-0.5 for v in vec_dets["binVals"]]
        nb.append(nb[-1]+1)        
        vec_dets["binHist"] = nb  
        
        return vec, vec_dets

    def getCoordsXY(self, id):
        if self.coords_proj is None:
            return (0,0)
        else:
            return self.coords_proj[0][:,id,0]

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
            if self.choice_dist is not None:
                self.distc = self.choice_dist.GetSelection()
            # nbrows = self.getParentData().nbRows()
            # if selp == 0:
            #     nbrows -= len(selected)
            # self.nbc = int(2+(self.grow_nbc**(rnbc))/(self.grow_nbc**10)*(nbrows/2.))
            
            x0, x1, y0, y1 = self.getAxisLims()
            bx, by = (x1-x0)/100.0, (y1-y0)/100.0
            corners = (x0, x1, y0, y1, bx, by)
            vec, vec_dets = self.getValVec()

            ## print "------------------", len(numpy.unique(vec))
            # for vv in numpy.unique(vec):
            #     nbl = numpy.sum(vec==vv)
            #     # self.clusters["dp"]
            #     print "Reds C.%d: %d %s" % (vv, nbl, numpy.sum(self.etor[vec==vv], axis=0)) #, numpy.sum(~self.etor[vec==vv], axis=0))

            # vvmax = len(self.clusters["rprt"])+1
            # vvmax = self.clusters["non_unique"]
            # vvmax = numpy.max(vec)
            vvmax = numpy.max(self.clusters["order"])
            vvmin = numpy.min(vec)

            self.dots_draws, mapper = self.prepareSingleVarDots(vec, vec_dets, draw_settings, delta_on=self.getDeltaOn(), min_max=(vvmin, vvmax))
                
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
                vv = vec
                # vv = 1.*vec                
                # vv[numpy.where(vec==0)[0][1:]] = numpy.nan
                corners = self.plotMapperHist(self.axe, vv, vec_dets, mapper, -1, corners)
                
            ###########################
            ###########################
            self.makeFinish(corners[:4], corners[4:])   
            self.MapcanvasMap.draw()
            self.MapfigMap.canvas.SetFocus()
        else:
            self.plot_void()      

    def getAxisLims(self):
        xx = self.axe.get_xlim()
        yy = self.axe.get_ylim()
        return (xx[0], xx[1], yy[0], yy[1])
            
    def getEtoR(self):
        nbE = 0
        if len(self.srids) > 0:
            nbE = self.reds[self.srids[0]].sParts.nbRows()
        etor = numpy.zeros((nbE, len(self.srids)), dtype=bool)
        for r, rid in enumerate(self.srids):
            etor[list(self.reds[rid].getSuppI()), r] = True
        return etor

    def setCurrent(self, reds_map):
        self.reds = dict(reds_map)
        self.srids = [rid for (rid, red) in reds_map]
        self.etor = self.getEtoR()
        self.clusters = self.computeClusters()
        if self.choice_dist is not None:
            opts = self.getDistOpts()
            self.choice_dist.SetItems(opts)
            self.choice_dist.SetSelection(numpy.min([len(opts)-1, self.distc]))
        self.updateMap()

    def getDistOpts(self):
        if self.clusters is not None:
            nb = numpy.max(self.clusters["nodesc"])+1
            return ["%d" % d for d in range(1,nb)]
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
        label = wx.StaticText(self.panel, wx.ID_ANY, "distance")
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
        return self.getCoords() is not None and event.inaxes == self.axe
    def on_click(self, event):
        pass
        # if self.clickActive() and self.inCapture(event):
        #     lid = self.getLidAt(event.xdata, event.ydata)
        #     print "LID: ", lid, 1*self.etor[lid]
            # if lid is not None:
            #     self.sendEmphasize([lid])
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
