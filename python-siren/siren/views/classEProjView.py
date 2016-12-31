import re

import wx
### from wx import ALIGN_BOTTOM, ALIGN_CENTER, ALIGN_LEFT, ALIGN_RIGHT, ALL, HORIZONTAL, VERTICAL, ID_ANY, EXPAND, RAISED_BORDER, SL_HORIZONTAL
### from wx import EVT_BUTTON, EVT_SCROLL_THUMBRELEASE, FONTFAMILY_DEFAULT, FONTSTYLE_NORMAL, FONTWEIGHT_NORMAL
### from wx import BoxSizer, Button, CallLater, CheckBox, Choice, DefaultPosition, Font, NewId, Panel,  Slider, StaticText, TextCtrl

import numpy
# The recommended way to use wx with mpl is with the WXAgg backend. 
# import matplotlib
# matplotlib.use('WXAgg')

import matplotlib.pyplot as plt
import scipy.spatial.distance
from matplotlib.patches import Ellipse
from matplotlib.lines import Line2D

from ..reremi.toolLog import Log
from ..reremi.classQuery import Query
from ..reremi.classSParts import SSetts
from ..reremi.classRedescription import Redescription
from classTDView import TDView
from classProj import ProjFactory
from classInterObjects import MaskCreator

import pdb

class EProjView(TDView):

    TID = "EPJ"
    SDESC = "E.Proj."
    ordN = 10
    what = "entities"
    title_str = "Entities Projection"
    typesI = "evr"
    defaultViewT = ProjFactory.defaultView.PID + "_" + what
    wait_delay = 300

    #info_band_height = 240
    margin_hov = 0.01
    
    @classmethod
    def getViewsDetails(tcl):
        return ProjFactory.getViewsDetails(tcl, what=tcl.what)
    
    def __init__(self, parent, vid, more=None):
        self.repbut = None
        self.initVars(parent, vid, more)
        self.queries = [Query(), Query()]
        self.initProject(more)
        self.initView()
        self.suppABCD = None

    def lastStepInit(self):
        if not self.wasKilled() and self.getCoords() is None:
            self.runProject()

    def getShortDesc(self):
        return "%s %s" % (self.getItemId(), self.getProj().SDESC)

    def getTitleDesc(self):
        return "%s %s" % (self.getItemId(), self.getProj().getTitle())

    def getId(self):
        return (self.getProj().PID, self.vid)

    def makeBoxes(self, frame, proj):
        boxes = []
        for kp in proj.getTunableParamsK():
            label = wx.StaticText(frame, wx.ID_ANY, kp.replace("_", " ").capitalize()+":")
            ctrls = []
            value = proj.getParameter(kp)
            if type(value) in [int, float]:
                type_ctrl = "text"
                ctrls.append(wx.TextCtrl(frame, wx.NewId(), str(value)))
            elif type(value) is bool:
                type_ctrl = "checkbox" 
                ctrls.append(wx.CheckBox(frame, wx.NewId(), "", style=wx.ALIGN_RIGHT))
                ctrls[-1].SetValue(value)
            elif type(value) is list and kp in proj.options_parameters:
                type_ctrl = "checkbox"
                for k,v in proj.options_parameters[kp]:
                    ctrls.append(wx.CheckBox(frame, wx.NewId(), k, style=wx.ALIGN_RIGHT))
                    ctrls[-1].SetValue(v in value)
            elif kp in proj.options_parameters:
                type_ctrl = "choice" 
                ctrls.append(wx.Choice(frame, wx.NewId()))
                strs = [k for k,v in proj.options_parameters[kp]]
                ctrls[-1].AppendItems(strings=strs)
                try:
                    ind = strs.index(value)
                    ctrls[-1].SetSelection(ind)
                except ValueError:
                    pass
            boxes.append({"key": kp, "label": label, "type_ctrl": type_ctrl, "ctrls":ctrls, "value":value})
        return boxes

    def additionalElements(self):
        setts_boxes = []
        max_w = self.getFWidth()-50
        current_w = 1000
        flags = wx.ALIGN_CENTER | wx.ALL

        self.boxes = self.makeBoxes(self.panel, self.getProj())
        # self.boxes = self.getProj().makeBoxes(self.panel)
        self.boxes.sort(key=lambda x : x["type_ctrl"])
        for box in self.boxes:
            block_w = box["label"].GetBestSize()[0] + sum([c.GetBestSize()[0] for c in box["ctrls"]])
            if current_w + block_w + 10 > max_w:
                setts_boxes.append(wx.BoxSizer(wx.HORIZONTAL))
                setts_boxes[-1].AddSpacer((10,-1))
                current_w = 10
            current_w += block_w + 10
            box["label"].SetFont(wx.Font(8, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
            setts_boxes[-1].Add(box["label"], 0, border=0, flag=flags | wx.ALIGN_RIGHT)
            for c in box["ctrls"]:
                c.SetFont(wx.Font(8, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
                setts_boxes[-1].Add(c, 0, border=0, flag=flags | wx.ALIGN_BOTTOM | wx.ALIGN_LEFT)
            setts_boxes[-1].AddSpacer((10,-1))

        add_boxes = self.additionalElementsPlus()

        setts_boxes.extend(add_boxes)
        #return [add_boxbis, add_box]
        self.nbadd_boxes = len(setts_boxes)-1 
        return setts_boxes


    def additionalElementsPlus(self):
        t = self.parent.dw.getPreferences()
        
        flags = wx.ALIGN_CENTER | wx.ALL # | wx.EXPAND

        self.buttons = []
        self.buttons.extend([{"element": wx.Button(self.panel, size=(self.butt_w,-1), label="Expand"),
                              "function": self.OnExpandSimp},
                             {"element": wx.Button(self.panel, size=(self.butt_w,-1), label="Reproject"),
                              "function": self.OnReproject}])
        self.repbut = self.buttons[-1]["element"]
        for i in range(len(self.buttons)):
            self.buttons[i]["element"].SetFont(wx.Font(8, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))

        self.sld_sel = wx.Slider(self.panel, -1, 50, 0, 100, wx.DefaultPosition, (self.sld_w, -1), wx.SL_HORIZONTAL)
            
        ##############################################
        add_boxB = wx.BoxSizer(wx.HORIZONTAL)
        add_boxB.AddSpacer((self.getSpacerWn()/2.,-1))

        v_box = wx.BoxSizer(wx.VERTICAL)
        label = wx.StaticText(self.panel, wx.ID_ANY,u"- opac. disabled +")
        label.SetFont(wx.Font(8, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
        v_box.Add(label, 0, border=1, flag=flags) #, userData={"where": "*"})
        v_box.Add(self.sld_sel, 0, border=1, flag=flags) #, userData={"where":"*"})
        add_boxB.Add(v_box, 0, border=1, flag=flags)
        
        add_boxB.Add(self.buttons[0]["element"], 0, border=1, flag=flags)
        add_boxB.AddSpacer((self.getSpacerWn(),-1))
        
        add_boxB.Add(self.buttons[1]["element"], 0, border=1, flag=flags)
        add_boxB.AddSpacer((self.getSpacerWn()/2.,-1))

        #return [add_boxbis, add_box]
        return [add_boxB]


    def additionalBinds(self):
        ## self.MapredMapQ[0].Bind(wx.EVT_TEXT_ENTER, self.OnEditQuery)
        ## self.MapredMapQ[1].Bind(wx.EVT_TEXT_ENTER, self.OnEditQuery)
        for button in self.buttons:
            button["element"].Bind(wx.EVT_BUTTON, button["function"])
        self.sld_sel.Bind(wx.EVT_SCROLL_THUMBRELEASE, self.OnSlide)

    def OnSlide(self, event):
        self.updateMap()

    def OnReproject(self, rid=None):
        self.getProj().initParameters(self.boxes)
        self.getProj().addParamsRandrep()
        # tmp_id = self.projkeyf.GetValue().strip(":, ")
        # if (self.proj is None and len(tmp_id) > 0) or tmp_id != self.proj.getCode():
        #     self.initProject(tmp_id)
        # else:
        #     self.initProject()
        self.runProject()

    def initProject(self, rid=None):
        ### print ProjFactory.dispProjsInfo()
        self.proj = ProjFactory.getProj(self.parent.dw.getData(), rid)
        
    def runProject(self):
        self.init_wait()
        if self.repbut is not None:
            self.repbut.Disable()
            self.repbut.SetLabel("Wait...")
        self.getProj().addParamsRandrep({"vids": self.getQCols()})
        self.parent.project(self.getProj(), self.getId())
                      
    def readyProj(self, proj):
        if proj is not None:
            self.proj = proj
        elif self.proj is not None:
            self.proj.clearCoords()
        self.kill_wait()
        self.updateMap()
        if self.repbut is not None:
            self.repbut.Enable()
            self.repbut.SetLabel("Reproject")
            
        
    def drawMap(self):
        """ Draws the map
        """
        self.highl = {}
        self.hight = {}

        if not hasattr( self, 'axe' ):
            self.axe = self.MapfigMap.add_subplot( 111 )

        self.mc = MaskCreator(self.axe, None, buttons_t=[], callback_change=self.makeMenu)

        self.el = Ellipse((2, -1), 0.5, 0.5)
        self.axe.add_patch(self.el)

        self.MapfigMap.canvas.mpl_connect('pick_event', self.OnPick)
        self.MapfigMap.canvas.mpl_connect('key_press_event', self.key_press_callback)
        self.MapfigMap.canvas.mpl_connect('motion_notify_event', self.on_motion)
        self.MapcanvasMap.draw()

    def init_wait(self):
        self.call_wait = wx.CallLater(1, self.plot_wait)
        self.cp = 0

    def kill_wait(self):
        self.call_wait.Stop()
        if self.wasKilled():
            return
        self.axe.cla()
        self.axe.plot([r/10.0+0.3 for r in [1,3]], [0.5, 0.5], 's', markersize=10, mfc="#DDDDDD", mec="#DDDDDD")
        self.axe.plot([r/10.0+0.3 for r in [0,2,4]], [0.5, 0.5, 0.5], 'ks', markersize=10)
        self.axe.axis([0,1,0,1])
        self.MapcanvasMap.draw()

    def plot_wait(self):
        if self.wasKilled():
            return
        self.axe.cla()
        self.axe.plot([r/10.0+0.3 for r in range(5)], [0.5 for r in range(5)], 'ks', markersize=10, mfc="#DDDDDD", mec="#DDDDDD")
        self.axe.plot(((self.cp)%5)/10.0+0.3, 0.5, 'ks', markersize=10)
        self.axe.axis([0,1,0,1])
        self.MapcanvasMap.draw()
        self.cp += 1
        self.call_wait.Restart(self.wait_delay)
            
    def makeBackground(self):   
        pass
    def makeFinish(self, xylims, xybs):   
        if self.getProj().getAxisLabel(0) is not None:
            self.axe.set_xlabel(self.getProj().getAxisLabel(0),fontsize=12)
        if self.getProj().getAxisLabel(1) is not None:
            self.axe.set_ylabel(self.getProj().getAxisLabel(1),fontsize=12)
        self.axe.axis([xylims[0]-xybs[0], xylims[1]+xybs[0], xylims[2]-xybs[1], xylims[3]+xybs[1]])

    def isReadyPlot(self):
        return self.suppABCD is not None and self.getCoords() is not None    
    def getAxisLims(self):
        return self.getProj().getAxisLims()

    def getCoordsXY(self, id):
        if self.proj is None:
            return (0,0)
        else:
            return (self.proj.getCoords(0, ids=id), self.proj.getCoords(1, ids=id))
    def getCoords(self, axi=None, ids=None):
        if self.proj is None:
            return None
        else:
            return self.proj.getCoords(axi, ids)

    def getProj(self):
        return self.proj

    def getLidAt(self, x, y):
        coords = self.getCoords()
        d = scipy.spatial.distance.cdist(zip(*[coords[0], coords[1]]), [(x,y)])
        lid = numpy.argmin(d)
        mmd = scipy.spatial.distance.cdist([(min(coords[0]), min(coords[1]))], [(max(coords[0]), max(coords[1]))])[0,0]
        if d[lid,0] < self.margin_hov * mmd:
            return lid
        return None
        # d = scipy.spatial.distance.cdist(self.coords_proj[0][:,self.hover_access,0].T, numpy.array([(x,y)]))
        # cands = [self.hover_access[i] for i in numpy.argsort(d, axis=0)[:5]]
        # i = 0
        # while i < len(cands):
        #     path = Polygon(self.getCoordsP(cands[i]), closed=True)
        #     if path.contains_point((x,y), radius=0.0):
        #         return cands[i]
        #     i += 1
        # return None
