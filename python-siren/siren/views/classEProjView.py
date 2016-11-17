### TODO check which imports are needed 
import re
import wx
import numpy
# The recommended way to use wx with mpl is with the WXAgg
# backend. 
import matplotlib
#matplotlib.use('WXAgg')
import matplotlib.pyplot as plt
import scipy.spatial.distance
from matplotlib.patches import Ellipse
from matplotlib.lines import Line2D

from ..reremi.toolLog import Log
from ..reremi.classQuery import Query
from ..reremi.classSParts import SSetts
from ..reremi.classRedescription import Redescription
from classGView import GView
from classProj import ProjFactory
from classInterObjects import MaskCreator

import pdb

class EProjView(GView):

    TID = "EPJ"
    SDESC = "E.Proj."
    ordN = 10
    what = "entities"
    title_str = "Entities Projection"
    typesI = ["Var", "Reds", "Row"]
    defaultViewT = ProjFactory.defaultView.PID + "_" + what
    wait_delay = 300

    #info_band_height = 240
    margin_hov = 0.01

    @classmethod
    def getViewsDetails(tcl):
        return ProjFactory.getViewsDetails(tcl, what=tcl.what)
    
    def __init__(self, parent, vid, more=None):
        self.repbut = None
        self.active_info = False
        self.parent = parent
        self.queries = [Query(), Query()]
        self.source_list = None
        self.pos = None
        self.boxL = None
        self.boxT = None
        self.icons = self.parent.icons
        self.rsets = None
        self.vid = vid
        self.buttons = []
        self.act_butt = [1]
        self.highl = {}
        self.hight = {}
        self.current_hover = None
        self.intab = self.parent.showVizIntab()
        self.initProject(more)
        self.store_size = None
        
        if self.isIntab():
            self.mapFrame = self.parent.tabs["viz"]["tab"]
        else:        
            self.mapFrame = wx.Frame(None, -1, "%s%s" % (self.parent.titlePref, self.getTitleDesc()))
            self.mapFrame.SetMinSize((self.getFWidth(), self.getFHeight()))
            self.mapFrame.SetSizer(wx.BoxSizer(wx.HORIZONTAL))
        self.panel = wx.Panel(self.mapFrame, -1, style=wx.RAISED_BORDER)
        self.drawFrame()
        self.binds()
        self.prepareActions()
        self.setKeys()
        self.prepareProcesses()
        self.makeMenu()
        self.initSizeRelative()
        if not self.isIntab():
            self.mapFrame.Show()
        self.suppABCD = None

    def lastStepInit(self):
        if not self.wasKilled() and self.getCoords() is None:
            self.runProject()

    def getShortDesc(self):
        return "%s %s" % (self.getRedId(), self.getProj().SDESC)

    def getTitleDesc(self):
        return "%s %s" % (self.getRedId(), self.getProj().getTitle())

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
        for button in self.buttons:
            button["element"].Bind(wx.EVT_BUTTON, button["function"])
        self.sld_sel.Bind(wx.EVT_SCROLL_THUMBRELEASE, self.OnSlide)

    def OnSlide(self, event):
        self.updateMap()

    def OnReproject(self, rid=None):
        self.getProj().initParameters(self.boxes)
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

        # self.MapfigMap = plt.figure()
        # self.MapcanvasMap = FigCanvas(self.mapFrame, -1, self.MapfigMap)
        # self.MaptoolbarMap = CustToolbar(self.MapcanvasMap, self)
        # self.MapfigMap.clear()
        # self.axe = self.MapfigMap.add_subplot(111)

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

    def plot_void(self):
        if self.wasKilled():
            return
        self.axe.cla()
        self.axe.plot([r/10.0+0.3 for r in [0,2,4]], [0.5 for r in [0,2,4]], 's', markersize=10, mfc="#DDDDDD", mec="#DDDDDD")
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
            
    def updateMap(self):
        """ Redraws the map
        """
        if self.wasKilled():
            return

        if self.suppABCD is not None and self.getCoords() is not None:
            self.highl = {}
            self.hight = {}
            ## self.hover_access = [i for (i, v) in enumerate(self.suppABCD) if v != SSetts.delta] 

            axxs = self.MapfigMap.get_axes()
            for ax in axxs:
                ax.cla()
                if ax != self.axe:
                    self.MapfigMap.delaxes(ax)
            
            draw_settings = self.getDrawSettings()

            ### SELECTED DATA
            selected = self.getUnvizRows()
            # selected = self.parent.dw.getData().selectedRows()
            selp = 0.5
            if self.sld_sel is not None:
                selp = self.sld_sel.GetValue()/100.0

            x0, x1, y0, y1 = self.getProj().getAxisLims()
            bx, by = (x1-x0)/100.0, (y1-y0)/100.0
            pick = self.getPickerOn()

            dsetts = draw_settings["default"]
            sz_dots = numpy.ones(len(self.suppABCD))*dsetts["size"]
            draw_indices = range(len(self.suppABCD))

            if self.isSingleVar():
                ccs = self.getQCols()
                ltid = self.getLitTypeId(ccs[0][0], ccs[0][1])
                vec = self.getValVector(ccs[0][0], ccs[0][1])
                cmap, vmin, vmax = (self.getCMap(ltid), numpy.min(vec), numpy.max(vec))
                
                norm = matplotlib.colors.Normalize(vmin=vmin, vmax=vmax, clip=True)
                mapper = matplotlib.cm.ScalarMappable(norm=norm, cmap=cmap)
                ec_dots = numpy.array([mapper.to_rgba(v) for v in vec])
                fc_dots = ec_dots.copy()
                fc_dots[:,-1] = dsetts["alpha"]
                mapper.set_array(vec)

            else:
                mapper = None
                vec = numpy.array(self.suppABCD)
                u, indices = numpy.unique(vec, return_inverse=True)
                ec_clusts = numpy.array([draw_settings[i]["color_e"]+[1.] for i in u])
                ec_dots = ec_clusts[indices]
                fc_clusts = numpy.array([draw_settings[i]["color_f"]+[ draw_settings[i]["alpha"] ] for i in u])
                fc_dots = fc_clusts[indices]

                if self.getDeltaOn():
                    sz_dots[numpy.where(vec==SSetts.delta)[0]] *= 0.5
                else:
                    draw_indices = numpy.where(vec!=SSetts.delta)[0]

            if len(selected) > 0:
                fc_dots[numpy.array(list(selected)), -1] *= selp
                
            self.dots_draws = {"fc_dots": fc_dots, "ec_dots": ec_dots, "sz_dots": sz_dots}
            if not pick: ##  #### NO PICKER, FASTER PLOTTING.
                self.axe.scatter(self.getProj().getCoords(0)[draw_indices],
                                 self.getProj().getCoords(1)[draw_indices],
                                 c=fc_dots[draw_indices,:], edgecolors=ec_dots[draw_indices,:],
                                 s=5*sz_dots[draw_indices], marker=dsetts["shape"], zorder=10)
            else:
                for idp in draw_indices:
                        self.drawEntity(idp, self.getPlotColor(idp, "fc"), self.getPlotColor(idp, "ec"),
                                                self.getPlotProp(idp, "sz"), dsetts, picker=pick)
            if mapper is not None:
                ax2 = self.axe.twinx()
                nb = 20
                if ltid == 2:
                    nb = [b-0.5 for b in numpy.unique(vec)]
                    nb.append(nb[-1]+1)
                n, bins, patches = plt.hist(vec, bins=nb)
                sum_h = numpy.max(n)
                norm_h = [ni*0.1*float(x1-x0)/sum_h+0.03*float(x1-x0) for ni in n]
                left = [bins[i] for i in range(len(n))]
                width = [bins[i+1]-bins[i] for i in range(len(n))]
                colors = [mapper.to_rgba(numpy.mean(bins[i:i+2])) for i in range(len(n))]
                ax2.barh(left, norm_h, width, x1+5*bx, color=colors)
                ax2.plot([x1+5*bx+0.03*(x1-x0), x1+5*bx+0.03*(x1-x0)], [bins[0], bins[-1]], "-k")
                x1 += 0.13*(x1-x0)+5*bx
                bby = (bins[-1]- bins[0])/100.
                ax2.set_ylim([bins[0]-bby, bins[-1]+bby])
                
            if self.getProj().getAxisLabel(0) is not None:
                self.axe.set_xlabel(self.getProj().getAxisLabel(0),fontsize=12)
            if self.getProj().getAxisLabel(1) is not None:
                self.axe.set_ylabel(self.getProj().getAxisLabel(1),fontsize=12)
            self.axe.axis([x0-bx, x1+bx, y0-by, y1+by])
            self.updateEmphasize(self.COLHIGH, review=False)
            self.MapcanvasMap.draw()
            self.MapfigMap.canvas.SetFocus()
        else:
            self.plot_void()

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

    def hoverActive(self):
        return GView.hoverActive(self) and not self.mc.isActive()

    def on_motion(self, event):
        if self.hoverActive() and self.proj is not None and self.getCoords() is not None:            
            lid = None
            if event.inaxes == self.axe:
                lid = self.getLidAt(event.xdata, event.ydata)
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
