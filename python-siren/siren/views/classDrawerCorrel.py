import wx
### from wx import ALIGN_CENTER, ALL, EXPAND, HORIZONTAL
### from wx import FONTFAMILY_DEFAULT, FONTSTYLE_NORMAL, FONTWEIGHT_NORMAL
### from wx import BoxSizer, Button, Font, NewId
### from wx import EVT_BUTTON, EVT_LEFT_DCLICK

import numpy
from scipy.sparse.linalg import eigsh
# The recommended way to use wx with mpl is with the WXAgg
# backend. 
# import matplotlib
# matplotlib.use('WXAgg')
import matplotlib
matplotlib.use('WXAgg')


import matplotlib.pyplot as plt
import matplotlib.cm as cm
from matplotlib.patches import Circle
from matplotlib.collections import PatchCollection

from ..clired.classSParts import SSetts
from ..clired.classRedescription import Redescription
from .classDrawerBasis import DrawerEntitiesTD

import pdb

MAP_SIDES = ["LHS", "RHS"]

class DrawerRedCorrel(DrawerEntitiesTD):
    
    # all_width = 1.
    # height_inter = [2., 3.] ### starting at zero creates troubles with supp drawing, since it's masking non zero values..
    # maj_space = 0.02
    # min_space = 0.01
    # flat_space = 0.03
    # margins_sides = 0.5
    # margins_tb = 0.1
    # margin_hov = min_space/2.
    # missing_yy = -1./6

    # ann_xy = (10,0)
    
    def __init__(self, view):
        self.view = view
        self.store_supp = None
        self.elements = {"active_info": False, "act_butt": [1]}
        ### TEMPORARY
        self.parts_in = {SSetts.Exx: True, SSetts.Exo: False, SSetts.Eox: False, SSetts.Eoo: False}
        self.parts_out = {SSetts.Exx: True, SSetts.Exo: True, SSetts.Eox: True, SSetts.Eoo: True}
        self.types_in = dict([(tid, True) for (name, tid) in self.getNamesTids()])
        ## self.sides_in = {"rows_LHS": True, "rows_RHS": True, "cols_LHS": True, "cols_RHS": True}
        self.sides_in = {"rows_LHS": True, "rows_RHS": False, "cols_LHS": False, "cols_RHS": True}
        # self.types_in[self.getTidForName("Boolean")] = False
        # self.types_in[self.getTidForName("Categorical")] = False
        # self.parts_in = {SSetts.Exx: False, SSetts.Exo: True, SSetts.Eox: False, SSetts.Eoo: False}
        # self.parts_out = {SSetts.Exx: True, SSetts.Exo: True, SSetts.Eox: True, SSetts.Eoo: True}
        self.fixed_radius = True
        self.initPlot()
        self.plot_void()
        ## self.draw()
        
    def getCanvasConnections(self):
        return []

    def getVecAndDets(self, inter_params=None):
        vec_dets = self.getPltDtH().getVecDets(inter_params)
        return vec, vec_dets
        

    def OnRedraw(self, event=None):
        self.update()

    def update_params(self, elems=None):
        ks = self.parts_in.keys()
        if elems is not None:
            for k in ks:
                lbl_in = "in_%s" % SSetts.labels[k]
                lbl_out = "out_%s" % SSetts.labels[k]
                if lbl_in in elems:
                    if elems[lbl_in].IsChecked():
                        self.parts_in[k] = True
                    else:
                        self.parts_in[k] = False
                if lbl_out in elems:
                    if elems[lbl_out].IsChecked():
                        self.parts_out[k] = True
                    else:
                        self.parts_out[k] = False
                        
            for lbl, i in self.getNamesTids():
                ll = "types_%d" % i
                if ll in elems:
                    if elems[ll].IsChecked():
                        self.types_in[i] = True
                    else:
                        self.types_in[i] = False

            for ll in self.sides_in.keys():
                if ll in elems:
                    if elems[ll].IsChecked():
                        self.sides_in[ll] = True
                    else:
                        self.sides_in[ll] = False

            if "fixed_radius" in elems:
                if elems["fixed_radius"].IsChecked():
                    self.fixed_radius = True
                else:
                    self.fixed_radius = False
                        
        
    def update(self, update_trees=True):
        if self.view.wasKilled():
            return

        if self.readyPlot():

            self.update_params(self.getElement("inter_elems"))
            
            vec = self.getPltDtH().getSuppABCD()
            tt = [k for (k,v) in self.types_in.items() if v]
            side_cols = [(k,None) for (k,v) in enumerate(MAP_SIDES) if (self.sides_in["rows_%s" %v] or self.sides_in["cols_%s" %v])]            
            
            if len(tt) == 0:
                tt = None
            if len(side_cols) == 0:
                side_cols = None
            mat, details, mcols = self.getParentData().getMatrix(side_cols=side_cols, nans=numpy.nan, types=tt, only_able=True)
            ids_rc = {}
            for rc in ["rows", "cols"]:
                ssides = [k for k,v in enumerate(MAP_SIDES) if self.sides_in["%s_%s" % (rc, v)]]
                ids_rc[rc] = [i for i,v in enumerate(details) if (len(ssides) == 0 or v["side"] in ssides)]
            self.clearPlot()

            pos_in = numpy.zeros(vec.shape, dtype=bool)
            pos_out = numpy.zeros(vec.shape, dtype=bool)
            for part, v in self.parts_in.items():
                if v:
                    pos_in |= (vec == part)
            for part, v in self.parts_out.items():
                if v:
                    pos_out |= (vec == part)

            ### (DE)ACTIVATE COUNT PLOTS
            # if tt == self.getTidForName(["Boolean"]):
            #     self.makeCountsPlot(mat, pos_in, pos_out, details)
            # else:
            self.makeCorrelPlot(mat, pos_in, pos_out, details, ids_rc)
            self.draw()
            self.setFocus()
        else:
            self.plot_void()
                
    def makeCountsPlot(self, mat, pos_in, pos_out, details):
        Rall = numpy.sum(mat, axis=1)
        if numpy.sum(pos_in) > 0:
            Nbin = float(numpy.sum(pos_in))
            Rin = numpy.sum(mat[:, pos_in], axis=1)
        else:
            Nbin = float(mat.shape[1])
            Rin = Rall
        if numpy.sum(pos_out) > 0:
            Nbout = float(numpy.sum(pos_out))
            Rout = numpy.sum(mat[:, pos_out], axis=1)
        else:
            Nbout = float(mat.shape[1])
            Rout = Rout
        nnz_ids = numpy.where(Rin > (numpy.sum(pos_in)/10.))[0]
        sids = nnz_ids[numpy.argsort(Rin[nnz_ids])]
        cmap = cm.get_cmap('PuOr')
        self.axe.barh(numpy.arange(len(sids))+.025, Rin[sids]/Nbin, left=.33, height=.95, color=cmap(100), align="edge")
        self.axe.barh(numpy.arange(len(sids))+.025, Rout[sids]/Nbout, left=-Rout[sids]/Nbout-.33, height=.95, color=cmap(0), align="edge")
        for ii, i in enumerate(sids):
            self.axe.text(0, ii+.5, details[i]["name"], va="center", ha="center", **self.view.getFontProps())
        self.axe.set_ylim([0, len(sids)])
        self.axe.set_xlim([-1.33, 1.33])
        ticks = [0, .25, .5, .75, 1.]
        self.axe.set_xticks([-i-.33 for i in ticks[::-1]]+[i+.33 for i in ticks])
        self.axe.set_xticklabels(ticks[::-1]+ticks)
        self.axe.set_yticks([])
        # pdb.set_trace()
            
    def makeCorrelPlot(self, mat, pos_in, pos_out, details, ids_rc):
        extra_v = 1.1
        Rall = numpy.corrcoef(mat)
        if numpy.sum(pos_in) > 0:
            variant = numpy.max(mat[:, pos_in], axis=1) != numpy.min(mat[:, pos_in], axis=1)
            if numpy.all(variant):
                Rin = numpy.corrcoef(mat[:, pos_in])
            else:
                Rin = -extra_v*numpy.ones((variant.shape[0], variant.shape[0]))
                CC = numpy.corrcoef(mat[variant,:][:, pos_in])
                for i,p in enumerate(numpy.where(variant)[0]):
                    Rin[p,variant] = CC[i,:]
        else:
            Rin = Rall
        if numpy.sum(pos_out) > 0:
            variant = numpy.max(mat[:, pos_out], axis=1) != numpy.min(mat[:, pos_out], axis=1)
            if numpy.all(variant):
                Rout = numpy.corrcoef(mat[:, pos_out])
            else:
                Rout = -extra_v*numpy.ones((variant.shape[0], variant.shape[0]))
                CC = numpy.corrcoef(mat[variant,:][:, pos_out])
                for i,p in enumerate(numpy.where(variant)[0]):
                    Rout[p,variant] = CC[i,:]
        else:
            Rout = Rall

        # labels = [d["name"] for d in details]
        # self.drawCorrelPlotTriangle(Rin, Rout, labels, extra_v)
            
        # A = (Rall+1)/2.
        A = 10**(-2*Rall)
        L = numpy.diag(numpy.sum(A, axis=1)) - A 
        eival, eivect = eigsh(L, 2)
        s = numpy.argsort(eivect[:,1])
        if s[0] > s[-1]:
            s = s[::-1]

        ids_rows = [i for i in s if i in ids_rc["rows"]]
        ids_cols = [i for i in s if i in ids_rc["cols"]]
            
        Rin = Rin[ids_cols, :][:, ids_rows]
        Rout = Rout[ids_cols, :][:, ids_rows]
        Rall = Rall[ids_cols, :][:, ids_rows]
        labels_rows = [details[d]["name"] for d in ids_rows]
        labels_cols = [details[d]["name"] for d in ids_cols]
        #pdb.set_trace()        
        # #### store the corrcoeffs to file(s)
        # import re
        # filename = "/home/egalbrun/corr_values_%s.csv" % self.view.getItemId()
        # vnames = [d["name"] for d in details]
        # keep_ids = [i for i,v in enumerate(vnames) if re.match("bio", v)]
        # header = ",".join([vnames[i] for i in keep_ids])
        # keep_ids = numpy.array(keep_ids)
        # # numpy.savetxt(filename, Rin[keep_ids,:][:,keep_ids], fmt=str("%.6f"), delimiter=",", header=header)
        # # if self.view.getItemId() == "r20":
        # #     filename = "/home/egalbrun/corr_values_overall.csv"
        # #     numpy.savetxt(filename, Rall[keep_ids,:][:,keep_ids], fmt=str("%.6f"), delimiter=",", header=header)
        # # filename = "/home/egalbrun/corr_values_globe.csv"
        # # numpy.savetxt(filename, Rall[keep_ids,:][:,keep_ids], fmt=str("%.6f"), delimiter=",", header=header)
        
        self.drawCorrelPlotSquare(Rin, Rout, labels_rows, labels_cols, extra_v)

    def drawCorrelPlotTriangle(self, Rin, Rout, labels, extra_v):
        cmap = cm.get_cmap('PuOr')
        xs, ys = numpy.meshgrid(numpy.arange(Rout.shape[0]), numpy.arange(Rout.shape[0]))
        flt_xs, flt_ys, flt_Rout, flt_Rin = numpy.ravel(xs), numpy.ravel(ys), numpy.ravel(Rout), numpy.ravel(Rin)
        ids_under = (flt_ys == 0) | (flt_xs == Rout.shape[0]-1)
        ids_under = flt_ys > flt_xs
        flt_xs, flt_ys, flt_Rout, flt_Rin = flt_xs[ids_under], flt_ys[ids_under], flt_Rout[ids_under], flt_Rin[ids_under]
        angle = numpy.pi*1/4
        rot = numpy.array([[numpy.cos(angle), -numpy.sin(angle)],[numpy.sin(angle), numpy.cos(angle)]])
        rot_xys = numpy.dot(numpy.vstack([flt_xs, flt_ys]).T, rot)           

        width_band = .45
        margband_bot = width_band
        margband_top = 1.
        
        for i, lbl in enumerate(labels):
            cline = "#888888" if i %2 == 0 else "#CCCCCC"
            if i > 0:
                xys = numpy.dot(numpy.array([[-1, i], [-margband_top, i-width_band], [-margband_top, i+width_band], [(i-1)+margband_bot, i+width_band], [(i-1)+margband_bot, i-width_band]]), rot)
                self.axe.fill(xys[1:, 0], xys[1:, 1], color=cline, alpha=.7, zorder=1)
                self.axe.text(xys[0, 0], xys[0, 1], lbl, rotation=-numpy.degrees(angle), ha="right", va="bottom", **self.view.getFontProps())

            if i < len(labels)-1:
                xys = numpy.dot(numpy.array([[i, Rout.shape[0]], [i-width_band, (Rout.shape[0]-1)+margband_top], [i+width_band, (Rout.shape[0]-1)+margband_top], [i+width_band, (i+1)-margband_bot], [i-width_band, (i+1)-margband_bot]]), rot)
                self.axe.fill(xys[1:, 0], xys[1:, 1], color=cline, alpha=.7, zorder=1)
                self.axe.text(xys[0, 0], xys[0, 1], lbl, rotation=numpy.degrees(angle), ha="left", va="bottom", **self.view.getFontProps())

        if self.fixed_radius:
            rads = .44*numpy.ones(flt_Rin.shape)
        else:
            rads = .48*numpy.abs(flt_Rin)
        
        patches = [Circle((rot_xys[i,0], rot_xys[i,1]), radius=rads[i]) for i in range(flt_Rin.shape[0])]
        ## .1+.4*numpy.abs(flt_Rin[i]-flt_Rout[i])
        fcolors = [cmap((flt_Rin[i]+extra_v)/(2*extra_v)) for i in range(flt_Rin.shape[0])]
        ecolors = [cmap((flt_Rout[i]+extra_v)/(2*extra_v)) for i in range(flt_Rin.shape[0])]
        # ecolors = [ecmap(.5*numpy.abs(flt_Rin[i]-flt_Rout[i])) for i in range(flt_Rin.shape[0])]
        p = PatchCollection(patches, alpha=1., zorder=10, facecolors = fcolors, edgecolors = ecolors, linewidths=(2.,))
        self.axe.add_collection(p)

        diag_size = numpy.sqrt(2)*(Rout.shape[0]-1)
        nb_bins = 100
        width_bin = diag_size/nb_bins
        for i in range(nb_bins):
            self.axe.fill([i*width_bin, (i+1)*width_bin, (i+1)*width_bin, i*width_bin], [-.75, -.75, -1.25, -1.25], color=cmap(i/(nb_bins-1.)))

        self.axe.text(-1, -1., "-1", ha="center", va="center", **self.view.getFontProps())
        self.axe.text(diag_size+1, -1., "+1", ha="center", va="center", **self.view.getFontProps())
                
        self.axe.set_xlim([0-.2*Rout.shape[0], diag_size+.2*Rout.shape[0]])
        self.axe.set_ylim([-2, diag_size/2+.2*Rout.shape[0]])
        self.axe.set_xticks([])
        self.axe.set_yticks([])

    def drawCorrelPlotSquare(self, Rin, Rout, labels_rows, labels_cols, extra_v):
        # cmap = cm.get_cmap('PuOr')
        cmap = cm.get_cmap('PiYG')
        xs, ys = numpy.meshgrid(numpy.arange(Rout.shape[0]), numpy.arange(Rout.shape[1]))
        flt_xs, flt_ys, flt_Rout, flt_Rin = numpy.ravel(xs), numpy.ravel(ys), numpy.ravel(Rout), numpy.ravel(Rin)
        # ids_under = (flt_ys == 0) | (flt_xs == Rout.shape[0]-1)
        # ids_under = flt_ys > flt_xs
        # flt_xs, flt_ys, flt_Rout, flt_Rin = flt_xs[ids_under], flt_ys[ids_under], flt_Rout[ids_under], flt_Rin[ids_under]
        # angle = 0 #numpy.pi*1/4
        # rot = numpy.array([[numpy.cos(angle), -numpy.sin(angle)],[numpy.sin(angle), numpy.cos(angle)]])
        # rot_xys = numpy.dot(numpy.vstack([flt_xs, flt_ys]).T, rot)
        rot_xys = numpy.vstack([flt_xs, flt_ys]).T

        for i, lbl in enumerate(labels_rows):
            self.axe.text(Rout.shape[0]+.2, i, lbl, ha="left", va="center", **self.view.getFontProps())
        for i, lbl in enumerate(labels_cols):
            self.axe.text(i-.5, Rout.shape[1]+.2, lbl, rotation=60, va="bottom", **self.view.getFontProps())

        if self.fixed_radius:
            rads = .40*numpy.ones(flt_Rin.shape)
        else:
            rads = .45*numpy.abs(flt_Rin)
        
        patches = [Circle((rot_xys[i,0], rot_xys[i,1]), radius=rads[i]) for i in range(flt_Rin.shape[0])]
        ## .1+.4*numpy.abs(flt_Rin[i]-flt_Rout[i])
        fcolors = [cmap((flt_Rin[i]+extra_v)/(2*extra_v)) for i in range(flt_Rin.shape[0])]
        ecolors = [cmap((flt_Rout[i]+extra_v)/(2*extra_v)) for i in range(flt_Rin.shape[0])]
        # ecolors = [ecmap(.5*numpy.abs(flt_Rin[i]-flt_Rout[i])) for i in range(flt_Rin.shape[0])]
        p = PatchCollection(patches, alpha=1., zorder=10, facecolors = fcolors, edgecolors = ecolors, linewidths=(2.,))
        self.axe.add_collection(p)

        diag_size = float(Rout.shape[0]-1)
        nb_bins = 100
        width_bin = diag_size/(nb_bins+3)
        for i in range(nb_bins):
            self.axe.fill([(i+1)*width_bin, (i+2)*width_bin, (i+2)*width_bin, (i+1)*width_bin], [-1.75, -1.75, -2.25, -2.25], color=cmap(i/(nb_bins-1.)))

        self.axe.text(0, -2., "-1", ha="right", va="center", **self.view.getFontProps())
        self.axe.text(diag_size, -2., "+1", ha="left", va="center", **self.view.getFontProps())
                
        self.axe.set_xlim([-.1*Rout.shape[0], 1.2*Rout.shape[0]])
        self.axe.set_ylim([-3, 1.2*Rout.shape[1]])
        self.axe.set_xticks([])
        self.axe.set_yticks([])

            
    # def makeAdditionalElements(self, panel=None):
    #     self.setElement("buttons", [])
    #     self.setElement("inter_elems", {})
    #     return []

    def makeAdditionalElements(self, panel=None):
        if panel is None:
            panel = self.getLayH().getPanel()
        flags = wx.ALIGN_CENTER | wx.ALL # | wx.EXPAND

        buttons = []
        buttons.extend([{"element": wx.Button(panel, size=(self.getLayH().butt_w,-1), label="Expand"),
                         "function": self.view.OnExpandSimp},
                        {"element": wx.Button(panel, size=(self.getLayH().butt_w,-1), label="Redraw"),
                         "function": self.OnRedraw}])
        

        for i in range(len(buttons)):
            buttons[i]["element"].SetFont(wx.Font(8, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))

        inter_elems = {}

        ##############################################
        add_boxA = wx.BoxSizer(wx.HORIZONTAL)
        add_boxA.AddSpacer(self.getLayH().getSpacerWn()/2)
        for lbl, i in self.getNamesTids():
            inter_elems["types_%d" % i] = wx.CheckBox(panel, wx.NewId(), "", style=wx.ALIGN_RIGHT)
            inter_elems["types_%d" % i].SetValue(self.types_in[i])

            label = wx.StaticText(panel, wx.ID_ANY, "%s:" % lbl)
            label.SetFont(wx.Font(8, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
            add_boxA.Add(label, 0, border=0, flag=flags)
            add_boxA.Add(inter_elems["types_%d" % i], 0, border=0, flag=flags)
            
        add_boxA.AddSpacer(self.getLayH().getSpacerWn())
        inter_elems["fixed_radius"] = wx.CheckBox(panel, wx.NewId(), "", style=wx.ALIGN_RIGHT)
        inter_elems["fixed_radius"].SetValue(self.fixed_radius)

        label = wx.StaticText(panel, wx.ID_ANY, "fix r:")
        label.SetFont(wx.Font(8, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
        add_boxA.Add(label, 0, border=0, flag=flags)
        add_boxA.Add(inter_elems["fixed_radius"], 0, border=0, flag=flags)        
        add_boxA.AddSpacer(self.getLayH().getSpacerWn()/2)

        add_boxB = wx.BoxSizer(wx.HORIZONTAL)
        add_boxB.AddSpacer(self.getLayH().getSpacerWn()/2)
        for k,v in self.sides_in.items():
            inter_elems[k] = wx.CheckBox(panel, wx.NewId(), "", style=wx.ALIGN_RIGHT)
            inter_elems[k].SetValue(v)

            label = wx.StaticText(panel, wx.ID_ANY, "%s:" % k)
            label.SetFont(wx.Font(8, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
            add_boxB.Add(label, 0, border=0, flag=flags)
            add_boxB.Add(inter_elems[k], 0, border=0, flag=flags)
        add_boxB.AddSpacer(self.getLayH().getSpacerWn()/2)
        
        add_boxC = wx.BoxSizer(wx.HORIZONTAL)
        add_boxC.AddSpacer(self.getLayH().getSpacerWn()/2)

        for part, v in self.parts_in.items():
            sub = SSetts.labels[part] 
            inter_elems["in_"+sub] = wx.CheckBox(panel, wx.NewId(), "", style=wx.ALIGN_RIGHT)
            inter_elems["in_"+sub].SetValue(v)
            inter_elems["out_"+sub] = wx.CheckBox(panel, wx.NewId(), "", style=wx.ALIGN_RIGHT)
            inter_elems["out_"+sub].SetValue(self.parts_out[part])

            v_box = wx.BoxSizer(wx.VERTICAL)
            label = wx.StaticText(panel, wx.ID_ANY, sub)
            label.SetFont(wx.Font(8, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
            v_box.Add(label, 0, border=1, flag=flags) #, userData={"where": "*"})
            v_box.Add(inter_elems["in_"+sub], 0, border=1, flag=flags) #, userData={"where":"*"})
            v_box.Add(inter_elems["out_"+sub], 0, border=1, flag=flags) #, userData={"where":"*"})
            add_boxC.Add(v_box, 0, border=1, flag=flags)
        
        add_boxC.AddSpacer(self.getLayH().getSpacerWn())
        add_boxC.Add(buttons[0]["element"], 0, border=1, flag=flags)
        add_boxC.AddSpacer(self.getLayH().getSpacerWn())
        add_boxC.Add(buttons[1]["element"], 0, border=1, flag=flags)

        add_boxC.AddSpacer(self.getLayH().getSpacerWn()/2)

        self.setElement("buttons", buttons)
        self.setElement("inter_elems", inter_elems)
        return [add_boxA, add_boxB, add_boxC]


    # def OnPick(self, event):

    # def hasDotsReady(self):
    #     return self.store_supp is not None
    
    # def drawAnnotation(self, xy, ec, tag, xytext=None):

    # def inCapture(self, event):
               
    # def getLidAt(self, x, y):
