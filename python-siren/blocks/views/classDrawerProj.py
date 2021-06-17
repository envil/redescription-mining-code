import wx
### from wx import ALIGN_BOTTOM, ALIGN_CENTER, ALIGN_LEFT, ALIGN_RIGHT, ALL, HORIZONTAL, VERTICAL, ID_ANY, EXPAND, RAISED_BORDER, SL_HORIZONTAL
### from wx import EVT_BUTTON, EVT_SCROLL_THUMBRELEASE, FONTFAMILY_DEFAULT, FONTSTYLE_NORMAL, FONTWEIGHT_NORMAL
### from wx import BoxSizer, Button, CallLater, CheckBox, Choice, DefaultPosition, Font, NewId, Panel,  Slider, StaticText, TextCtrl

import numpy
# The recommended way to use wx with mpl is with the WXAgg backend.
# import matplotlib
# matplotlib.use('WXAgg')
from .classDrawerBasis import DrawerEntitiesTD, DrawerBasis
from .classDrawerClust import DrawerClustTD
from .classProj import AxesProj

import pdb


class DrawerProj(DrawerBasis):

    #info_band_height = 240
    margin_hov = 0.01

    def makeAdditionalElements(self, panel=None):
        if panel is None:
            panel = self.getLayH().getPanel()
        flags = wx.ALIGN_CENTER | wx.ALL  # | wx.EXPAND

        buttons = []
        buttons.extend([{"element": wx.Button(panel, size=(self.getLayH().butt_w, -1), label="Expand"),
                         "function": self.view.OnExpandSimp},
                        {"element": wx.Button(panel, size=(self.getLayH().butt_w, -1), label="Reproject"),
                         "function": self.view.OnReproject}])

        for i in range(len(buttons)):
            buttons[i]["element"].SetFont(wx.Font(8, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))

        inter_elems = {}
        inter_elems["slide_opac"] = wx.Slider(panel, -1, 10, 0, 100, wx.DefaultPosition, (self.getLayH().sld_w, -1), wx.SL_HORIZONTAL)

        ##############################################
        add_boxB = wx.BoxSizer(wx.HORIZONTAL)
        add_boxB.AddSpacer(self.getLayH().getSpacerWn()/2)

        v_box = wx.BoxSizer(wx.VERTICAL)
        label = wx.StaticText(panel, wx.ID_ANY, u"- opac. disabled +")
        label.SetFont(wx.Font(8, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
        v_box.Add(label, 0, border=1, flag=flags)  # , userData={"where": "*"})
        v_box.Add(inter_elems["slide_opac"], 0, border=1, flag=flags)  # , userData={"where":"*"})
        add_boxB.Add(v_box, 0, border=1, flag=flags)

        add_boxB.AddSpacer(self.getLayH().getSpacerWn())
        add_boxB.Add(buttons[0]["element"], 0, border=1, flag=flags)
        add_boxB.AddSpacer(self.getLayH().getSpacerWn())
        add_boxB.Add(buttons[1]["element"], 0, border=1, flag=flags)

        add_boxB.AddSpacer(self.getLayH().getSpacerWn()/2)

        self.setElement("buttons", buttons)
        self.setElement("inter_elems", inter_elems)
        self.setElement("rep_butt", buttons[-1]["element"])
        return [add_boxB]

    def getProj(self):
        return self.view.getProj()

    def setAxisLims(self, xylims, bxys=None):
        if bxys is not None:
            bx, by = bxys[0], bxys[1]
        else:
            bx, by = (xylims[1]-xylims[0])/100.0, (xylims[3]-xylims[2])/100.0
        if xylims[0]-bx == xylims[1]+bx:
            bx = .5
        if xylims[2]-by == xylims[3]+by:
            by = .5
        self.axe.axis([xylims[0]-bx, xylims[1]+bx, xylims[2]-by, xylims[3]+by])

    def makeFinish(self, xylims, bxys=None):
        if self.getProj().readyCoords():
            fs = self.view.getFontSizeProp()
            if self.getProj().getVarsP() is not None:
                for i, (x, y, l) in enumerate(zip(*self.getProj().getVarsP())):
                    self.axe.plot((0, x), (0, y), "k-", linewidth=1.)
                    self.axe.text(x, y, l, fontsize=fs)

            if self.getProj().getAxisLabel(0) is not None:
                self.axe.set_xlabel(self.getProj().getAxisLabel(0), fontsize=fs)
            if self.getProj().getAxisLabel(1) is not None:
                self.axe.set_ylabel(self.getProj().getAxisLabel(1), fontsize=fs)
            # xx, yy = self.getProj().getCoords()
            # print "CORR %s vs. %s = %.4f" % (self.getProj().getAxisLabel(0), self.getProj().getAxisLabel(1), numpy.corrcoef(xx, yy)[0,1])
            # self.axe.plot([xylims[0]-xybs[0], xylims[1]+xybs[0]], [xylims[0]-xybs[0], xylims[1]+xybs[0]], "k--")
            self.setAxisLims(xylims, bxys)

    def readyPlot(self):
        return self.getProj() is not None and self.getProj().readyCoords()

    def readyCoords(self):
        return self.getProj() is not None and self.getProj().readyCoords()

    def getAxisCorners(self):
        return self.getProj().getAxisCorners()

    def drawPoly(self):
        return False

    def getCoordsXY(self, id):
        if self.getProj() is None:
            return (0, 0)
        else:
            return (self.getProj().getCoords(0, ids=id), self.getProj().getCoords(1, ids=id))

    def getCoords(self, axi=None, ids=None):
        if self.getProj() is None:
            return None
        else:
            return self.getProj().getCoords(axi, ids)

    def getCoordsXYA(self, idp):
        return self.getCoordsXY(idp)


class DrawerEntitiesProj(DrawerProj, DrawerEntitiesTD):

    # def shortcut(self, axe, vec, draw_settings):
    #     facx, facy = (100, 100)
    #     if numpy.max(self.getProj().coords_proj[0]) < 0.01:
    #         self.getProj().coords_proj = (self.getProj().coords_proj[0] * facx, self.getProj().coords_proj[1] * facy)
    #     # numpy.savetxt("points.csv", numpy.vstack([dots_draw["zord_dots"][draw_indices], self.getCoords(0), self.getCoords(1)]).T, "%.6f")

    #     def func(x):
    #         return 1.9*x-facy*0.0022
    #     # return 2*x-0.0024

    #     marg = facx*0.0004
    #     # lowx, upx = (facx*.0002, facx*.0032)
    #     lowx, upx = (numpy.min(self.getProj().coords_proj[0]), numpy.max(self.getProj().coords_proj[0]))
    #     lowx -= .5*(upx-lowx)
    #     upx += .5*(upx-lowx)

    #     bndsX = numpy.array([lowx, lowx, upx, upx, lowx])
    #     offX = numpy.array([-marg/2, marg/2, marg/2, -marg/2, -marg/2])
    #     bndsY = func(bndsX)

    #     axe.plot([lowx, upx], [func(lowx), func(upx)], ":", color="#74A8F6", zorder=20)
    #     axe.fill(bndsX+offX, bndsY, facecolor="#74A8F6", alpha=0.4)

    #     xs = self.getCoords(0)
    #     ys = self.getCoords(1)
    #     inout = numpy.abs(func(xs)-ys) < marg
    #     reds = (vec == 0) | (vec == 1)

    #     vec[inout & reds] = 2
    #     vec[inout & ~reds] = 1
    #     vec[~inout & reds] = 0
    #     vec[~inout & ~reds] = 3

    def plotDotsSimple(self, axe, dots_draw, draw_indices, draw_settings):
        # if isinstance(self.getProj(), AxesProj) and self.getProj().getAxVars() is not None:
        #     xvar, yvar = self.getProj().getAxVars()
        #     # self.getParentData()
        #     # data.col(side, l.colId()).numEquiv()
        #     # self.isTypeId(l.typeId(), "Categorical"):

        #     # pdb.set_trace()
        #     # print "PROJ V", self.getProj()
        DrawerEntitiesTD.plotDotsSimple(self, axe, dots_draw, draw_indices, draw_settings)


class DrawerClustProj(DrawerProj, DrawerClustTD):

    def makeAdditionalElements(self, panel=None):
        if panel is None:
            panel = self.getLayH().getPanel()
        flags = wx.ALIGN_CENTER | wx.ALL  # | wx.EXPAND

        buttons = []
        buttons.extend([{"element": wx.Button(panel, size=(self.getLayH().butt_w, -1), label="Reproject"),
                         "function": self.view.OnReproject}])

        for i in range(len(buttons)):
            buttons[i]["element"].SetFont(wx.Font(8, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))

        inter_elems = {}
        inter_elems["slide_opac"] = wx.Slider(panel, -1, 10, 0, 100, wx.DefaultPosition, (self.getLayH().sld_w, -1), wx.SL_HORIZONTAL)
        inter_elems["choice_nbc"] = wx.Choice(panel, -1)
        inter_elems["choice_nbc"].SetItems(["1"])
        inter_elems["choice_nbc"].SetSelection(0)

        ##############################################
        add_boxB = wx.BoxSizer(wx.HORIZONTAL)
        add_boxB.AddSpacer(self.getLayH().getSpacerWn()/2)

        v_box = wx.BoxSizer(wx.VERTICAL)
        label = wx.StaticText(panel, wx.ID_ANY, u"- opac. disabled +")
        label.SetFont(wx.Font(8, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
        v_box.Add(label, 0, border=1, flag=flags)  # , userData={"where": "*"})
        v_box.Add(inter_elems["slide_opac"], 0, border=1, flag=flags)  # , userData={"where":"*"})
        add_boxB.Add(v_box, 0, border=1, flag=flags)

        add_boxB.AddSpacer(self.getLayH().getSpacerWn())
        add_boxB.Add(buttons[0]["element"], 0, border=1, flag=flags)

        add_boxB.AddSpacer(self.getLayH().getSpacerWn())
        v_box = wx.BoxSizer(wx.VERTICAL)
        label = wx.StaticText(panel, wx.ID_ANY, "dist. inter c")
        label.SetFont(wx.Font(8, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
        add_boxB.Add(label, 0, border=1, flag=flags)
        add_boxB.Add(inter_elems["choice_nbc"], 0, border=1, flag=flags)

        add_boxB.AddSpacer(self.getLayH().getSpacerWn()/2)

        self.setElement("buttons", buttons)
        self.setElement("inter_elems", inter_elems)
        self.setElement("rep_butt", buttons[-1]["element"])
        return [add_boxB]
