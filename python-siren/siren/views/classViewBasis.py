import wx, re
import numpy
import matplotlib.pyplot as plt

from ..clired.classSParts import SSetts
from ..clired.classCol import ColM
from ..clired.classData import RowE
from ..clired.classRedescription import Redescription

from .classProj import ProjFactory

#### Classes for preparing the data
####################################################
from .classPltDtHandler import PltDtHandlerBasis, PltDtHandlerRed, PltDtHandlerRedWithCoords, PltDtHandlerRedWithTime
from .classPltDtHList import PltDtHandlerListVarSplits, PltDtHandlerListClust, PltDtHandlerListBlocksCoords, PltDtHandlerTextList

#### Classes for laying out the window
####################################################
from .classLayoutHandler import LayoutHandlerBasis, LayoutHandlerQueries, LayoutHandlerText

#### Classes for drawing the figure
####################################################
from .classDrawerBasis import DrawerBasis, DrawerEntitiesTD
from .classDrawerProj import DrawerEntitiesProj, DrawerClustProj
from .classDrawerPara import DrawerRedPara
from .classDrawerTree import DrawerRedTree
try:
    # from .classDrawerMap import DrawerEntitiesMap, DrawerClustMap
    from .classDrawerMapCarto import DrawerEntitiesMap, DrawerClustMap
    from .classDrawerMappoly import DrawerEntitiesMappoly, DrawerClustMappoly, DrawerBorders
    WITHMAPS = True
except ModuleNotFoundError as e:
    print(e)
    print("Map-based views will not be available!")
    WITHMAPS = False
from .classDrawerTimeSeries import DrawerRedTimeSeries
from .classDrawerCorrel import DrawerRedCorrel

import pdb

HTML_COLOR_PATT = "#[0-9A-Fa-f]{6}([0-9A-Fa-f]{2})?$"

def typeIWhat(what):
    if type(what) == str:
        return what
    if isinstance(what, ColM) or isinstance(what, RowE):
        return "v"
    if isinstance(what, Redescription):
        if what.typeId() is not None:
            return "v"
        else:
            return "r"
    elif type(what) is list and len(what) > 0 and len(what[0]) == 2:
        if all([isinstance(c[1], Redescription) for c in what]):
            return "R"
        elif all([isinstance(c[1], ColM) for c in what]):
            return "V"
        

class ViewBare(object):
    
    TID = "-"
    SDESC = "-"
    ordN = 0
    title_str = "Bare View"
    typeD = {}
    ext_keys = None
    typesI = ""

    subcl_layh = LayoutHandlerBasis
    subcl_drawer = None
    subcl_pltdt = PltDtHandlerBasis

    @classmethod
    def getTypesI(tcl):
        return tcl.typesI
    @classmethod
    def getTID(tcl):
        return tcl.TID
    @classmethod
    def isTable(tcl):
        return False

    @classmethod
    def suitableD(tcl, typeD={}):
        return all([typeD.get(k)==v for k,v in tcl.typeD.items()])

    def getFrame(self):
        if self.isIntab():
            return self.parent.getFrame()
        return self.layH.getFrame()
        
    def __init__(self, parent, vid, more=None):
        self.parent = parent
        self.vid = vid
        self.data = {}
        self.layH = self.subcl_layh(self)
        self.pltdtH = self.subcl_pltdt(self)
        if self.subcl_drawer is not None:
            self.drawer = self.subcl_drawer(self)
            self.layH.setToolbarDrawer(self.drawer)
            boxes = self.drawer.prepareInteractive(self.layH.getPanel())
        else:
            self.drawer = None
            boxes = []
        self.layH.finalize_init(boxes)
        
    def getLayH(self):
        return self.layH
    def getDrawer(self):
        return self.drawer
    def hasDrawer(self):
        return self.drawer is not None
    def getPltDtH(self):
        return self.pltdtH
    def getParent(self):
        return self.parent
        
    #### SEC: VIEW IDENTIFICATION
    ###########################################

    @classmethod
    def getViewsDetails(tcl):
        if tcl.getTID() is not None:
            return {tcl.getTID(): {"title": tcl.title_str, "class": tcl, "more": None, "ord": tcl.ordN}}
        return {}

    @classmethod
    def suitableExts(tcl, ext_keys=None):
        ext_suit = True
        if tcl.ext_keys is not None:
            if ext_keys is None:
                ext_suit = False
            else:
                ext_suit = all([k in ext_keys for k in tcl.ext_keys])
        return ext_suit

    @classmethod
    def suitableViewBase(tcl, typeD={}, ext_keys=None, what=None):
        return tcl.suitableD(typeD) and tcl.suitableExts(ext_keys)
    @classmethod
    def suitableView(tcl, typeD={}, ext_keys=None, what=None):
        return tcl.suitableViewBase(typeD, ext_keys, what)
    
    def getItemId(self):
        if self.hasParent():
            return self.getParentViewsm().getItemId(self.getId())
        return self.vid
    
    def getShortDesc(self):
        return "%s %s" % (self.getItemId(), self.SDESC)

    def getTitleDesc(self):
        return "%s %s" % (self.getItemId(), self.title_str)

    def getId(self):
        return (self.TID, self.vid)

    def getVId(self):
        return self.vid

    
    #### SEC: PARENT ACCESS
    ###########################################

    def hasParent(self):
        return self.parent is not None
    def getParentVizm(self):
        if self.hasParent():
            return self.parent.getVizm()
    def getParentViewsm(self):
        if self.hasParent():
            return self.parent.getViewsm()
    def getParentTab(self, which):
        if self.hasParent():
            return self.parent.getTTab(which)
    def getParentData(self):
        if self.hasParent():
            return self.parent.dw.getData()
    def getParentPreferences(self):
        if self.hasParent():
            return self.parent.dw.getPreferences()
        return {}
    def getParentIcon(self, key=None):
        if self.hasParent():
            return self.parent.icons.get(key)
    def getParentTitlePref(self):
        if self.hasParent():
            return self.parent.titlePref
        return "Standalone "

    def isIntab(self):
        return self.getLayH().isInTab
    def toTop(self):
        self.getLayH().toTop()
    def _SetSize(self):
        self.getLayH()._SetSize()
    def updateTitle(self):
        self.getLayH().updateTitle()
    def getGPos(self):
        return self.getLayH().getGPos()
    def popSizer(self):
        return self.getLayH().popSizer()
    def destroy(self):
        self.getLayH().destroy()
    def wasKilled(self):
        return self.getLayH().wasKilled()
    def updateRSets(self, new_rsets=None):
        self.getPltDtH().updateRSets(new_rsets)
        
        
    def lastStepInit(self, blocking=False):
        pass
    def OnQuit(self, event=None, upMenu=True, freeing=True):
        if self.hasParent():
            self.getParentViewsm().deleteView(self.getId(), freeing)
            self.getParentViewsm().unregisterView(vkey=self.getId(), upMenu=upMenu)
        else:
            self.getLayH().Destroy()
            
    #### SEC: MENU
    ######################################
    def makeMenu(self, frame=None):
        """
        Prepare the menu for this view.

        @type  frame: wx.Frame
        @param frame: The frame in which the menu resides
        """
        
        if self.isIntab():
            return
        
        if frame is None:
            frame = self.getLayH().getFrame()

        menuBar = wx.MenuBar()
        if self.hasParent():
            menuBar.Append(self.parent.makeFileMenu(frame), "&File")
        menuBar.Append(self.makeActionsMenu(frame), "&Edit")
        menuBar.Append(self.makeVizMenu(frame), "&View")
        menuBar.Append(self.makeProcessMenu(frame), "&Process")
        
        if self.hasParent():
            menuBar.Append(self.parent.makeViewsMenu(frame), "&Windows")
            menuBar.Append(self.parent.makeHelpMenu(frame), "&Help")
        frame.SetMenuBar(menuBar)
        frame.Layout()

    def makeActionsMenu(self, frame, menuAct=None):
        if self.hasDrawer():
            return self.getDrawer().makeActionsMenu(frame, menuAct)
        elif menuAct is None:
            menuAct = wx.Menu()
            self.getParent().appendEmptyMenuEntry(menuAct, "No Actions", "There are no edit actions.")
        return menuAct
        
    def enumerateVizItems(self):
        if self.hasParent():
            return self.getParentViewsm().getViewsItems(vkey=self.getId(), what=self.getWhat())
        return []
    def makeVizMenu(self, frame, menuViz=None):
        self.ids_viewT = {}
        if menuViz is None:
            menuViz = wx.Menu()
        for item in self.enumerateVizItems():
            ID_NEWV = wx.NewId()
            m_newv = menuViz.Append(ID_NEWV, "%s" % item["title"],
                                    "Plot %s." % item["title"])
            if not item["suitable"]:
                m_newv.Enable(False)

            frame.Bind(wx.EVT_MENU, self.OnOtherV, m_newv)
            self.ids_viewT[ID_NEWV] = item["viewT"]
        if menuViz.GetMenuItemCount() == 0:
            self.getParent().appendEmptyMenuEntry(menuViz, "No Views", "There are no other views.")
        return menuViz       
    def OnOtherV(self, event):
        if self.hasParent():
            self.getParentViewsm().viewOther(viewT=self.ids_viewT[event.GetId()], vkey=self.getId())

    def makeProcessMenu(self, frame, menuPro=None):
        self.menu_map_pro = {}
        if menuPro is None:
            menuPro = wx.Menu()

        for process, details in self.getLayH().getProcesses():
            ID_PRO = wx.NewId()
            m_pro = menuPro.Append(ID_PRO, details["label"], details["legend"])
            if self.q_expand(details["more"]):
                frame.Bind(wx.EVT_MENU, self.OnExpandAdv, m_pro)
                self.menu_map_pro[ID_PRO] = process
            else:
                menuPro.Enable(ID_PRO, False)
        ct = menuPro.GetMenuItemCount()
        if self.hasParent():
            menuPro = self.parent.makeStoppersMenu(frame, menuPro)
        if ct < menuPro.GetMenuItemCount():
            menuPro.InsertSeparator(ct)
        return menuPro
            
    #### SEC: HANDLING SETTINGS
    ###########################################
    def getSettV(self, key, default=False):
        t = self.getParentPreferences()
        try:
            v = t[key]["data"]
        except:            
            v = default
        return v

    def getFontProps(self):
        return {"fontsize": self.getSettV("plot_fontsize")}
    def getFontSizeProp(self):
        return self.getSettV("plot_fontsize")

    def isHexColor(self, s):
        return re.match(HTML_COLOR_PATT, s)
    def colorHexto255(self, color_hex):
        if self.isHexColor(color_hex):
            return (int(color_hex[1:3], 16), int(color_hex[3:5], 16), int(color_hex[5:7], 16), int(color_hex[7:9], 16) if len(color_hex[7:9]) > 0 else 0)
        return None
        
    def getColorKey1(self, key, dsetts=None):
        if dsetts is None:
            dsetts = self.getParentPreferences()
        if key in dsetts:
            tc = dsetts[key]["data"]
        elif key in self.colors_def:
            tc = self.colors_def[key]
        else:
            tc = self.colors_def[-1]
        return [i/255.0 for i in tc]+[1.]
    def getColorKey255(self, key, dsetts=None):
        if dsetts is None:
            dsetts = self.getParentPreferences()
        if key in dsetts:
            tc = dsetts[key]["data"]
        elif key in self.colors_def:
            tc = self.colors_def[key]
        else:
            tc = self.colors_def[-1]
        return tc
    
    def getAlpha(self, alpha=None, color=None):
        if self.alpha_off:
            alpha = 1.
        else:
            if alpha is None:
                 alpha = self.DOT_ALPHA
            elif alpha < -1 or alpha > 1:
                alpha = numpy.sign(alpha)*(numpy.abs(alpha)%1)*self.DOT_ALPHA
            if alpha < 0:
                alpha = -color[3]*alpha
        return alpha
    
    def getColorA(self, color, alpha=None):
        alpha = self.getAlpha(alpha, color)
        return tuple([color[0], color[1], color[2], alpha])
    
    def getColorHigh(self):
        return self.getColorA(self.getColorKey1("color_h"))

    def getColors255(self):
        return  [ self.getColorKey255(color_k) for color_k in self.colors_ord ]

    def getColors1(self):
        return  [ self.getColorKey1(color_k) for color_k in self.colors_ord ]
    
    def getDrawSettDef(self):
        t = self.getParentPreferences()
        try:
            dot_shape = t["dot_shape"]["data"]
            dot_size = t["dot_size"]["data"]
        except:
            dot_shape = self.DOT_SHAPE
            dot_size = self.DOT_SIZE

        return {"color_f": self.getColorA(self.getColorKey1("grey_basic")),
                "color_e": self.getColorA(self.getColorKey1("grey_basic"), 1.),
                "shape": dot_shape, "size": dot_size, "zord": self.DEF_ZORD}

    def setAlphaOnOff(self):
        t = self.getParentPreferences()
        if t["alpha_off"]["data"] == 'yes':
            self.alpha_off = True
        else:
            self.alpha_off = False

    def getCustomCCMapSettings(self):
        t = self.getParentPreferences()
        ccmap = t["custom_ccmap"]["data"].strip()
        if len(ccmap) > 0:
            if "," in ccmap or ":" in ccmap:
                cmap_parts = {} 
                for i, p in enumerate(t["custom_ccmap"]["data"].strip().split(",")):
                    qs = [q.strip() for q in p.split(":")]
                    if self.isHexColor(qs[-1]):
                        if len(qs) > 1:
                            cmap_parts[":".join(qs[:-1])] = qs[-1] # self.colorHexto255(qs[-1])
                        else:
                            cmap_parts[i] = qs[-1] # self.colorHexto255(qs[-1])
                if len(cmap_parts) > 0:
                    return cmap_parts
            else:
                try:
                    plt.get_cmap(ccmap)
                    return ccmap
                except ValueError:
                    ccmap = None
        return None
    def getDrawSettings(self):
        self.setAlphaOnOff()
        colors = self.getColors1()
        colhigh = self.getColorHigh()
        fontprops = self.getFontProps()
        defaults = self.getDrawSettDef()
        if self.getSettV('miss_details'):
            zord_miss = self.DEF_ZORD
        else:
            zord_miss = -1       
        draw_pord = dict([(v,p) for (p,v) in enumerate([SSetts.Emm, SSetts.Exm, SSetts.Emx,
                                                        SSetts.Eom, SSetts.Emo,
                                                        SSetts.Eoo, SSetts.Eox,
                                                        SSetts.Exo, SSetts.Exx])])
            
        dd = numpy.nan*numpy.ones(numpy.max(list(draw_pord.keys()))+1)
        for (p,v) in enumerate([SSetts.Eoo, SSetts.Eox, SSetts.Exo, SSetts.Exx]):
            dd[v] = p
        for (v, veq) in [(SSetts.Eom, SSetts.Eoo), (SSetts.Exm, SSetts.Exo)]:
            dd[v] = dd[veq]

        css = {"fontprops": fontprops, "draw_pord": draw_pord, "draw_ppos": dd, "shape": defaults["shape"], "colhigh": colhigh,
               "delta_on": self.getSettV('draw_delta', self.DELTA_ON), "custom_ccmap": self.getCustomCCMapSettings()}
        for (p, iid) in enumerate([SSetts.Exo, SSetts.Eox, SSetts.Exx, SSetts.Eoo]):
            css[iid] = {"color_f": self.getColorA(colors[p]),
                        "color_e": self.getColorA(colors[p], 1.),
                        "shape": defaults["shape"], "size": defaults["size"],
                        "zord": self.DEF_ZORD}
        for (p, iid) in enumerate([SSetts.Exm, SSetts.Emx]):
            css[iid] = {"color_f": self.getColorA(colors[SSetts.Eoo], -.9),
                        "color_e": self.getColorA(colors[p], .9),
                        "shape": defaults["shape"], "size": defaults["size"]-1,
                        "zord": zord_miss}
        for (p, iid) in enumerate([SSetts.Emo, SSetts.Eom]):
            css[iid] = {"color_f": self.getColorA(colors[p], -.9),
                        "color_e": self.getColorA(colors[SSetts.Eoo], .9),
                        ## "color_e": self.getColorA(defaults["color_e"], .9),
                        "shape": defaults["shape"], "size": defaults["size"]-1,
                        "zord": zord_miss}
        css[SSetts.Emm] = {"color_f": self.getColorA(colors[SSetts.Eoo], -.9),
                           "color_e": self.getColorA(colors[SSetts.Eoo], .9),
                           "shape": defaults["shape"], "size": defaults["size"]-1,
                           "zord": zord_miss}
        # css[SSetts.Eoo] = {"color_f": self.getColorA(defaults["color_f"]),
        #                      "color_e": self.getColorA(defaults["color_e"], 1.),
        #                      "color_l": self.getColorA(defaults["color_l"]),
        #                      "shape": defaults["shape"], "size": defaults["size"]-1,
        #                      "zord": self.DEF_ZORD}
        css[-1] = {"color_f": self.getColorA(defaults["color_f"], .5),
                   "color_e": self.getColorA(defaults["color_e"], .5),
                   "shape": defaults["shape"], "size": defaults["size"]-1,
                   "zord": self.DEF_ZORD}
        css["default"] = defaults
        css[SSetts.Exo]["zord"] += 1
        css[SSetts.Eox]["zord"] += 1
        css[SSetts.Exx]["zord"] += 2
        css[SSetts.Eoo]["zord"] -= 1
        # print("---- COLOR SETTINGS")
        # for k,v in css.items():
        #     if type(k) is int:
        #         print("* %s" % k)
        #         for kk,vv in v.items():
        #             print("\t%s\t%s" % (kk,vv))
        return css

    #### SEC: DATA HANDLING
    ###########################################   
    def setCurrent(self, qr=None, iid=None):
        return self.getPltDtH().setCurrent(qr, iid)

    def getWhat(self):
        return self.getPltDtH().getWhat()
    
    def isSingleVar(self):
        return self.getPltDtH().isSingleVar()
        
    def refresh(self):
        self.getLayH().autoShowFoldsBoxes()
        if self.isIntab():
            self.getLayH()._SetSize()

    def addStamp(self, pref="", force=False):
        pass
            

class ViewBasis(ViewBare):
    """
    The parent class of all visualizations.
    """

    colors_ord = ["color_l", "color_r", "color_i", "color_o"]
    colors_def = {"color_l": (255,0,0), "color_r": (0,0,255), "color_i": (160,32,240), "color_o": (153, 153, 153),
                  "grey_basic": (127,127,127), "grey_light": (153,153,153), "grey_dark": (85,85,85),
                  "color_h": (255, 255, 0), -1: (127, 127, 127)}
    DOT_ALPHA = 0.6
    ## 153 -> 99, 237 -> ed
    DOT_SHAPE = 's'
    DOT_SIZE = 3

    DELTA_ON = False
    DEF_ZORD = 3
    
    TID = "-"
    SDESC = "-"
    ordN = 0
    title_str = "Basis View"
    typeD = {}
    ext_keys = None
    typesI = ""

    subcl_layh = LayoutHandlerBasis
    subcl_drawer = DrawerBasis
    subcl_pltdt = PltDtHandlerBasis

    def emphasizeOnOff(self, turn_on=set(), turn_off=set(), hover=False, review=True):
        self.getDrawer().emphasizeOnOff(turn_on, turn_off, hover, review)
       
    def OnExpandAdv(self, event):
        if self.getPltDtH().hasQueries():
            params = {"red": self.getPltDtH().getRed(), "task": "expand"}
            if event.GetId() in self.menu_map_pro:
                params = self.getLayH().getProcessesParams(self.menu_map_pro[event.GetId()], params)
            self.getParent().expand(params)

    def OnExpandSimp(self, event):
        if self.getPltDtH().hasQueries():
            params = {"red": self.getPltDtH().getRed()}
            if params["red"].length(0) + params["red"].length(1) > 0:
                params["task"] = "expand"
            else:
                params["task"] = "mine"
            self.getParent().expand(params)
    def getWeightCover(self, params):
        params["area"] = self.getDrawer().getHighlightedIds()
        return params
    def q_expand(self, more):
        if not self.getPltDtH().hasQueries():
            return False
        if more is None:
            return True
        res = True
        if "side" in more:
            res &= len(self.getPltDtH().getQuery(1-more["side"])) > 0
        if "in_weight" in more or "out_weight" in more:
            res &= self.getDrawer().q_has_selected()
        return res


###############################################################################################################
######################################## DEFINING THE DIFFERENT VIEWS
###############################################################################################################               

class ViewEntitiesProj(ViewBasis):
    
    TID = "-"
    SDESC = "-"
    ordN = 0
    what = "entities"
    title_str = "Entities Projection"
    typesI = "vr"
    defaultViewT = ProjFactory.defaultView.getTPIDw(what)

    subcl_drawer = DrawerEntitiesProj
    
    @classmethod
    def getViewsDetails(tcl):
        return ProjFactory.getViewsDetails(tcl, what=tcl.what)
    
    def __init__(self, parent, vid, more=None):
        self.parent = parent
        self.vid = vid
        self.data = {}
        self.initProject(more)
        self.layH = self.subcl_layh(self)
        self.pltdtH = self.subcl_pltdt(self)
        self.drawer = self.subcl_drawer(self)
        self.layH.setToolbarDrawer(self.drawer)
        boxes = self.additionalElements()
        boxes.extend(self.drawer.prepareInteractive(self.layH.getPanel()))
        self.layH.finalize_init(boxes)

    def getShortDesc(self):
        return "%s %s" % (self.getItemId(), self.getProj().SDESC)

    def getTitleDesc(self):
        return "%s %s" % (self.getItemId(), self.getProj().getTitle())

    def getId(self):
        return (self.getProj().getTPID(), self.vid)
            
    def lastStepInit(self, blocking=False):
        if not self.wasKilled():
            if self.getProj().getCoords() is None:
                self.runProject(blocking)
            else:
                self.readyProj(self.proj)

    def getProj(self):
        return self.proj
            
    def OnReproject(self, rid=None, blocking=False):
        self.getProj().initParameters(self.boxes)
        # self.getProj().addParamsRandrep()
        # tmpp_id = self.projkeyf.GetValue().strip(":, ")
        # if (self.proj is None and len(tmpp_id) > 0) or tmpp_id != self.proj.getCode():
        #     self.initProject(tmpp_id)
        # else:
        #     self.initProject()
        self.runProject(blocking)

    def initProject(self, rid=None):
        ### print(ProjFactory.dispProjsInfo())
        self.proj = ProjFactory.getProj(self.getParentData(), rid)
        
    def runProject(self, blocking=False):
        self.drawer.init_wait()
        if self.drawer.hasElement("rep_butt"):
            self.drawer.getElement("rep_butt").Disable()
            self.drawer.getElement("rep_butt").SetLabel("Wait...")
        if self.getPltDtH().hasQueries():
            self.getProj().addParamsRandrep({"vids": self.getPltDtH().getQCols()})

        if blocking:
            try:
                self.proj.do()
            except ValueError as e: #Exception as e:
                self.proj.clearCoords()
            self.readyProj(self.proj)
        else:
            self.parent.project(self.getProj(), self.getId())
        
    def readyProj(self, proj):
        if proj is not None:
            self.proj = proj
        elif self.proj is not None:
            self.proj.clearCoords()
        self.drawer.kill_wait()
        self.drawer.update()
        if self.drawer.hasElement("rep_butt"):
            self.drawer.getElement("rep_butt").Enable()
            self.drawer.getElement("rep_butt").SetLabel("Reproject")
            
    def makeBoxes(self, frame, proj):
        boxes = []
        for kp in proj.getTunableParamsK():          
            label = wx.StaticText(frame, wx.ID_ANY, kp.replace("_", " ").capitalize()+":")
            ctrls = []
            value = proj.getParameter(kp)
            if type(value) in [int, float, str]:
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
                strs = [k for k,v in proj.options_parameters[kp]]
                ctrls.append(wx.Choice(frame, wx.NewId(), choices=strs))
                try:
                    ind = strs.index(value)
                    ctrls[-1].SetSelection(ind)
                except ValueError:
                    pass
            boxes.append({"key": kp, "label": label, "type_ctrl": type_ctrl, "ctrls":ctrls, "value":value})
        return boxes
    
    def additionalElements(self):
        setts_boxes = []
        max_w = self.getLayH().getFWidth()-50
        current_w = 1000
        flags = wx.ALIGN_CENTER | wx.ALL

        self.boxes = self.makeBoxes(self.getLayH().getPanel(), self.getProj())
        # self.boxes = self.getProj().makeBoxes(self.panel)
        self.boxes.sort(key=lambda x : x["type_ctrl"])
        for box in self.boxes:
            block_w = box["label"].GetBestSize()[0] + sum([c.GetBestSize()[0] for c in box["ctrls"]])
            if current_w + block_w + 10 > max_w:
                setts_boxes.append(wx.BoxSizer(wx.HORIZONTAL))
                setts_boxes[-1].AddSpacer(10)
                current_w = 10
            current_w += block_w + 10
            box["label"].SetFont(wx.Font(8, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
            setts_boxes[-1].Add(box["label"], 0, border=0, flag=flags )#| wx.ALIGN_RIGHT)
            for c in box["ctrls"]:
                c.SetFont(wx.Font(8, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
                setts_boxes[-1].Add(c, 0, border=0, flag=flags)# | wx.ALIGN_BOTTOM | wx.ALIGN_LEFT)
            setts_boxes[-1].AddSpacer(10)

        self.nbadd_boxes = len(setts_boxes) 
        return setts_boxes

    
class ViewRed(ViewBasis):

    TID = None
    SDESC = "-"
    title_str = "2D"
    ordN = 0
    typeD = {}
    typesI = "vr"

    subcl_layh = LayoutHandlerQueries
    subcl_drawer = DrawerEntitiesTD
    subcl_pltdt = PltDtHandlerRed
    
    def updateQuery(self, sd=None, query=None):
        return self.getPltDtH().updateQuery(sd, query)
            
    def addStamp(self, pref="", force=False):
        self.getDrawer().addStamp(pref, force=force)


###################
### ENTITIES MAPS
###################
if WITHMAPS:
    class ViewRedMap(ViewRed):
    
        TID = "MAP"
        SDESC = "Map"
        title_str = "Map"
        ordN = 2
        typeD = {"geo": True}
        typesI = "vr"
    
        subcl_layh = LayoutHandlerQueries
        subcl_drawer = DrawerEntitiesMap
        subcl_pltdt = PltDtHandlerRedWithCoords
    
    class ViewRedMappoly(ViewRed):
    
        TID = "MPP"
        SDESC = "Map.Poly"
        title_str = "Map Polygons"
        ordN = 3
        typeD = {"geo": True}
        typesI = "vr"
        ext_keys = ["geoplus"]
        
        subcl_layh = LayoutHandlerQueries
        subcl_drawer = DrawerEntitiesMappoly
        subcl_pltdt = PltDtHandlerRedWithCoords
    
        @classmethod
        def suitableView(tcl, typeD={}, ext_keys=None, what=None):
            if tcl.suitableD(typeD) and tcl.suitableExts(ext_keys):
                what_tid = None        
                if isinstance(what, Redescription) or isinstance(what, ColM):
                    what_tid = what.typeId()
                return DrawerBasis.isTypeId(what_tid, ["Boolean", "Categorical"], default_accept=True)
            return False
############################

    
class ViewRedPara(ViewRed):
    
    TID = "PC"
    SDESC = "Pa.Co."
    ordN = 4
    title_str = "Parallel Coordinates"
    typesI = "vr"
    typeD = {}

    subcl_drawer = DrawerRedPara

class ViewRedTimeSeries(ViewRed):
    
    TID = "TS"
    SDESC = "Time"
    ordN = 1
    title_str = "Time Series"
    typesI = "vr"
    typeD = {"time": True}
    
    subcl_drawer = DrawerRedTimeSeries
    subcl_pltdt = PltDtHandlerRedWithTime
    
class ViewRedCorrel(ViewRed):
    
    TID = "CC"
    SDESC = "Correl"
    ordN = 6
    title_str = "Variable Correlations"
    typesI = "vr"
    typeD = {}

    subcl_drawer = DrawerRedCorrel
    @classmethod
    def suitableView(tcl, typeD={}, ext_keys=None, what=None):
        if tcl.suitableD(typeD) and tcl.suitableExts(ext_keys):
            what_tid = None        
            if isinstance(what, Redescription) or isinstance(what, ColM):
                what_tid = what.typeId()
            return DrawerBasis.isTypeId(what_tid, "Boolean", default_accept=True)
        return False

    
class ViewRedTree(ViewRed):

    TID = "TR"
    SDESC = "Tree"
    ordN = 5
    title_str = "Decision Tree"
    typesI = "vr"
    typeD = {}
    
    subcl_drawer = DrawerRedTree
    subcl_pltdt = PltDtHandlerRed
    
    @classmethod
    def suitableView(tcl, typeD={}, ext_keys=None, what=None):
        return tcl.suitableViewBase(typeD, ext_keys, what) and isinstance(what, Redescription) and what.isTreeCompatible()


class ViewRedProj(ViewEntitiesProj, ViewRed):

    TID = "EPJ"
    SDESC = "E.Proj."
    what = "entities"
    title_str = "Entities Projection"
    ordN = 10

    subcl_layh = LayoutHandlerQueries
    subcl_pltdt = PltDtHandlerRedWithCoords
    subcl_drawer = DrawerEntitiesProj
    
#####################################
### LISTS
#####################################               
class ViewList(ViewBasis):
    
    TID = "L"
    SDESC = "LViz"
    ordN = 0
    title_str = "List View"
    typeD = {}
    typesI = ""

    @classmethod
    def allCompat(tcl, what, names):
        if what is not None and not isinstance(what, Redescription) and not isinstance(what, ColM):
            return all([((isinstance(c[1], Redescription) or isinstance(c[1], ColM)) and DrawerBasis.isTypeId(c[1].typeId(), names, default_accept=True)) for c in what])
        return False
    
class ViewClustProj(ViewEntitiesProj, ViewList):


    TID = "CLP"
    SDESC = "CluProjLViz"
    ordN = 10
    what = "cluster"
    title_str = "Cluster Proj View"
    typesI = "VR"
    typeD = {}

    subcl_drawer = DrawerClustProj
    subcl_pltdt = PltDtHandlerListClust
    subcl_layh = LayoutHandlerBasis
    @classmethod
    def suitableView(tcl, typeD={}, ext_keys=None, what=None):
        return tcl.suitableViewBase(typeD, ext_keys, what) and ViewList.allCompat(what, "Boolean")


###################
### CLUSTERS MAPS
###################
if WITHMAPS:
    class ViewVarSplitsMap(ViewList):
        
        TID = "VSLM"
        SDESC = "VSMapLViz"
        ordN = 0
        title_str = "Variable Split Map"
        typesI = "R"
        typeD = {"geo": True}
        
        subcl_drawer = DrawerClustMap
        subcl_pltdt = PltDtHandlerListVarSplits
        subcl_layh = LayoutHandlerBasis
    
        @classmethod
        def suitableView(tcl, typeD={}, ext_keys=None, what=None):
            return tcl.suitableViewBase(typeD, ext_keys, what) and ViewList.allCompat(what, "Boolean")
    
    class ViewClustMap(ViewList):
        
        TID = "CLM"
        SDESC = "CluMapLViz"
        ordN = 0
        title_str = "Cluster Map"
        typesI = "VR"
        typeD = {"geo": True}
        
        subcl_drawer = DrawerClustMap
        subcl_pltdt = PltDtHandlerListClust
        subcl_layh = LayoutHandlerBasis
    
        @classmethod
        def suitableView(tcl, typeD={}, ext_keys=None, what=None):
            return tcl.suitableViewBase(typeD, ext_keys, what) and ViewList.allCompat(what, "Boolean")
    
        
    class ViewClustMappoly(ViewList):
        
        TID = "CLMPP"
        SDESC = "CluMapPolyLViz"
        ordN = 1
        title_str = "Map Polygons"
        typesI = "VR"
        typeD = {"geo": True}
        ext_keys = ["geoplus"]
            
        subcl_drawer = DrawerClustMappoly
        subcl_pltdt = PltDtHandlerListClust
        subcl_layh = LayoutHandlerBasis
    
        @classmethod
        def suitableView(tcl, typeD={}, ext_keys=None, what=None):
            return tcl.suitableViewBase(typeD, ext_keys, what) and ViewList.allCompat(what, "Boolean")
    
    
    class ViewBorders(ViewList):
        
        TID = "CLBRD"
        SDESC = "BordersMapLViz"
        ordN = 3
        title_str = "Map Borders"
        typesI = "VR"
        typeD = {"geo": True}
        ext_keys = ["geoplus"]
            
        subcl_drawer = DrawerBorders
        subcl_pltdt = PltDtHandlerListBlocksCoords
        subcl_layh = LayoutHandlerBasis
    
        @classmethod
        def suitableView(tcl, typeD={}, ext_keys=None, what=None):
            return tcl.suitableViewBase(typeD, ext_keys, what) # and ViewList.allCompat(what, "Boolean")
############################


    
class ViewText(ViewBare):
    TID = "TXT"
    SDESC = "Text"
    ordN = 0
    title_str = "Text"
    typeD = {}
    typesI = "R"

    @classmethod
    def isTable(tcl):
        return True

class ViewTextList(ViewText):

    TID = "TBL"
    SDESC = "List"
    ordN = 0
    title_str = "list"
    typeD = {}
    typesI = "R"

    subcl_drawer = None
    subcl_pltdt = PltDtHandlerTextList
    subcl_layh = LayoutHandlerText
    
    @classmethod
    def suitableView(tcl, typeD={}, ext_keys=None, what=None):
        return False

    def __init__(self, parent, vid, more=None):
        self.lid = None
        ViewText.__init__(self, parent, vid, more)

    def getLid(self):
        return self.lid
    def getTable(self):
        return self.getLayH().getTable()
    
    def refreshTable(self, lids=None, iids=[]):
        if lids is None or self.getLid() in lids:
            self.getTable().load(self.getLid())
        else:
            for iid in iids:
                self.getTable().refreshItem(iid)
    
    def getListShortStr(self):
        if self.lid is not None:
            dt = self.getLayH().getTable().getListData(self.lid)
            if dt is not None and "name" in dt:
                return dt["name"]                            
        return "?"
        
    def setCurrent(self, qr=None, iid=None):
        self.lid = iid
        self.getLayH().getTable().load(iid)
        return self.getPltDtH().setCurrent(qr, iid)

    #### SEC: MENU
    ######################################
    def makeMenu(self, frame=None):
        self.getLayH().getTable().makeMenu()

    def getShortDesc(self):
        return "%s %s" % (self.SDESC, self.getListShortStr())

    def getTitleDesc(self):
        return "%s %s" % (self.title_str, self.getListShortStr())

# #############################################################################
# from .classPltDtHList import PltDtHandlerListRanges
# from .classDrawerRanges import DrawerRanges

# class ViewRanges(ViewList):
    
#     TID = "LRNG"
#     SDESC = "RangesLViz"
#     ordN = 5
#     title_str = "Variables Ranges"
#     typesI = "R"
#     typeD = {}
#     ext_keys = None
        
#     subcl_drawer = DrawerRanges
#     subcl_pltdt = PltDtHandlerListRanges
#     subcl_layh = LayoutHandlerBasis

#     @classmethod
#     def suitableView(tcl, typeD={}, ext_keys=None, what=None):
#         return tcl.suitableViewBase(typeD, ext_keys, what) # and ViewList.allCompat(what, "Boolean")
# #############################################################################
    
