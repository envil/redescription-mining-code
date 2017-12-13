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
    nbc = 15
    grow_nbc = 1.6

    def initVars(self, parent, vid, more=None):
        LView.initVars(self, parent, vid)
        self.clusters = None
            
    def computeClusters(self):
        vb = {}
        etor = self.etor
        mx = etor.shape[1]
        c01 = mx-(numpy.dot(1.-etor, 1.-etor.T) + numpy.dot(etor*1., etor.T*1.))

        non_unique = 0
        map_nis = None
        nb_rprt = []
        rprt = []
        if numpy.min(numpy.triu(c01, 1)) == 0: ### there are entities satisfying the same combination of reds
            map_nis = -numpy.ones(c01.shape[0], dtype=int)
            seen = set()
            i = 0
            while i < c01.shape[0]:
                ids = numpy.where(c01[i,:] == 0)[0] ### find entities satisfying the same comb of red as i
                if numpy.sum(etor[i,:]) > 0: ### if this is actually satisfying some
                    map_nis[ids] = len(rprt)
                    nb_rprt.append(len(ids))
                    if len(ids) > 1:
                        non_unique += 1
                    rprt.append(i)
                seen.update(ids)
                while i in seen:
                    i+= 1
            c01_rprt = c01[rprt,:][:,rprt]
        else:
            rprt = range(c01.shape[0])
            nb_rprt = [1 for i in rprt]
            c01_rprt = c01

        minmax_dist = numpy.min(numpy.max(c01_rprt, axis=1))
        c01_rprt += (mx+1)*numpy.eye(c01_rprt.shape[0])

        tot_nodes = float(etor.shape[0])        
        candidates = dict(enumerate(nb_rprt))

        # blk0 = numpy.zeros(len(candidates))
        # blk0[sorted(range(len(nb_rprt)), key=lambda x: -nb_rprt[x])] = numpy.arange(len(candidates), dtype=int)
        blk0 = numpy.arange(len(candidates), dtype=int)
        assigns = [blk0]
        pickeds = [range(len(candidates))]

        thres = 0
        while thres >= 0 and thres < minmax_dist:
        #for thres in range(int(minmax_dist)):
            thres += 1
            nodesc = candidates.keys()
            uncovered = candidates.keys()
            picked, cov_newly, cov_all, scores = ([], [], [], [])
            weights = 1/(1.+numpy.sum(c01_rprt<=thres, axis=1))
            #weights = numpy.ones(c01_rprt.shape[0])
            sss = numpy.dot(c01_rprt[:,uncovered]<=thres, weights[uncovered])
            while len(uncovered) > 0:
                p = max(nodesc, key=lambda i: (sss[i], candidates[i]))
                ## p = max(nodesc, key=lambda i: (numpy.sum(c01_rprt[i,uncovered]<=thres), candidates[i]))
                picked.append(p)
                scores.append(sss[p])
                cov_newly.append([n for n in uncovered if c01_rprt[picked[-1],n]<=thres or n == picked[-1]])
                cov_all.append(set(numpy.where(c01_rprt[picked[-1],:]<=thres)[0]))
                cov_all[-1].add(p)
                uncovered = [n for n in uncovered if c01_rprt[picked[-1],n]>thres and n!= picked[-1]]
                sss = numpy.dot(c01_rprt[:,uncovered]<=thres, weights[uncovered])
                nodesc = [n for n in nodesc if n in uncovered or sss[n] > 0]

            # singletons = [enumerate(picked) if len(cov_newly) <= 1]
            ## print "Thres", thres, len(picked)
            blk0 = numpy.zeros(len(candidates), dtype=int)
            seen_bids = set()
            for ti in range(len(picked))[::-1]:
                bid = assigns[-1][picked[ti]]
                if bid in seen_bids:
                    unseen = set(assigns[-1][cov_newly[ti]]).difference(seen_bids)
                    if len(unseen) > 0:
                        bid = min(unseen)
                    else:
                        print "NO AVAILABLE ID"
                        bid = max(seen_bids)+1
                blk0[cov_newly[ti]] = bid
                seen_bids.add(bid)

            assigns.append(blk0)
            pickeds.append(picked)
            ## blcks.append({"picked": picked, "cov_newly": cov_newly, "cov_all": cov_all, "scores": scores, "assign": blk0})
            if len(picked) == 2:
                thres = -1

        #### sorting ids
        # xx = numpy.vstack(assigns).T
        # # ws = numpy.vstack([nb_rprt for i in assigns]).T
        # mpids = numpy.zeros(xx.shape[0])
        # mpids[numpy.argsort(numpy.bincount(xx.flatten()))[::-1]] = numpy.arange(xx.shape[0])
        ### assigns = mpids[xx] 

        return {"rprt": numpy.array(rprt), "map_nis": map_nis, "assigns": numpy.vstack(assigns).T,
                    "pickeds": pickeds, "non_unique": non_unique}
    
    def getValVec(self):
        vec = numpy.empty((0))
        if self.clusters is not None:
            nb = int((len(self.clusters["pickeds"])-1)*(1.-self.nbc_ratio))
            ## print "NBC>>", self.nbc_ratio, nb, len(self.clusters["pickeds"])
            ######
            assign_rprt = self.clusters["assigns"][:,nb]
            if self.clusters["map_nis"] is not None:
                vec = -10*numpy.ones(self.clusters["map_nis"].shape, dtype=int)
                for i,v in enumerate(assign_rprt):
                    if numpy.sum(self.clusters["map_nis"] == i) == 0:
                        pdb.set_trace()
                    elif numpy.sum(self.clusters["map_nis"] == i) == 1:
                        vec[self.clusters["map_nis"] == i] = -2
                    else:
                        vec[self.clusters["map_nis"] == i] = v
            else:
                vec = assign_rprt

        vec[vec==-2] = len(self.clusters["rprt"])+1
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
        if len(vec_dets["binVals"]) < 15:
            vec_dets["binLbls"] = ["C.%s" % b for b in vec_dets["binVals"]]
        else:
            vec_dets["binLbls"] = ["" for b in vec_dets["binVals"]]

        nb = [v-0.5 for v in vec_dets["binVals"]]
        nb.append(nb[-1]+1)        
        vec_dets["binHist"] = nb  
        
        return vec, vec_dets

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
            if self.sld is not None:
                rnbc = self.sld.GetValue()/10.

            # nbrows = self.getParentData().nbRows()
            # if selp == 0:
            #     nbrows -= len(selected)
            # self.nbc = int(2+(self.grow_nbc**(rnbc))/(self.grow_nbc**10)*(nbrows/2.))
            self.nbc_ratio = rnbc/10.
            
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
            vvmax = numpy.max(vec)
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
        self.updateMap()

    def additionalElements(self):
        t = self.parent.dw.getPreferences()
        td_def = 50
        
        flags = wx.ALIGN_CENTER | wx.ALL # | wx.EXPAND

        self.buttons = []

        self.sld = wx.Slider(self.panel, -1, td_def, 0, 100, wx.DefaultPosition, (self.sld_w, -1), wx.SL_HORIZONTAL)
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
        label = wx.StaticText(self.panel, wx.ID_ANY, "-        clusters       +")
        label.SetFont(wx.Font(8, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
        v_box.Add(label, 0, border=1, flag=flags) #, userData={"where": "*"})
        v_box.Add(self.sld, 0, border=1, flag=flags) #, userData={"where": "*"})
        add_boxB.Add(v_box, 0, border=1, flag=flags)   

        add_boxB.AddSpacer((self.getSpacerWn()/2.,-1))
        
        #return [add_boxbis, add_box]
        return [add_boxB]

    def additionalBinds(self):
        self.sld.Bind(wx.EVT_SCROLL_THUMBRELEASE, self.OnSlide)
        self.sld_sel.Bind(wx.EVT_SCROLL_THUMBRELEASE, self.OnSlide)
        
    def OnSlide(self, event):
        self.updateMap()
