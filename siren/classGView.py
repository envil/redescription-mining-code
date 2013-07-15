### TODO check which imports are needed 
import wx
import numpy as np
# The recommended way to use wx with mpl is with the WXAgg
# backend. 
import matplotlib
#matplotlib.use('WXAgg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_wxagg import \
    FigureCanvasWxAgg as FigCanvas, \
    NavigationToolbar2WxAgg as NavigationToolbar
from matplotlib.lines import Line2D
from matplotlib.patches import Polygon
from matplotlib.path import Path

from reremi.classQuery import Query
from reremi.classSParts import SParts
from reremi.classRedescription import Redescription

import pdb

class GView(object):

    label_jacc="acc     ="
    label_pval="p-value   ="
    label_cardAlpha=u"|E_{1,0}|  ="
    label_cardBeta=u"|E_{0,1}|  ="
    label_cardU=u"|E\E_{0,0}| ="
    label_cardI=u"|E_{1,1}|  ="
    label_cardO=u"|E_{0,0}|  ="
    label_cardT=u"|E|      ="

    colors_def = [("color_l", (255,0,0)), ("color_r", (0,0,255)), ("color_i", (160,32,240))]
    DOT_ALPHA = 0.6
        
    COLHIGH='#FFFF00'

    DOT_SHAPE = 's'
    DOT_SIZE = 3

    map_select_supp = {"l": [SParts.alpha], "r": [SParts.beta], "i": [SParts.gamma], "o": [SParts.delta]}

    TID = "G"
    ordN = 0
    title_str = "View"
    geo = False
    typesI = ["Var", "Reds"]

    @classmethod
    def getViewsDetails(tcl):
        return {tcl.TID: {"title": tcl.title_str, "class": tcl, "more": None, "ord": tcl.ordN}}


    def __init__(self, parent, vid, more=None):
        self.parent = parent
        self.source_list = None
        self.mc = None
        self.sld_sel = None
        self.vid = vid
        self.circle = None
        self.buttons = []
        self.highl = {}
        self.hight = {}
        self.mapFrame = wx.Frame(None, -1, "%s%s" % (self.parent.titlePref, self.title_str))
        self.panel = wx.Panel(self.mapFrame, -1)
        self.drawMap()
        self.drawFrame()
        self.binds()
        self.mapFrame.Show()
        self.queries = [Query(), Query()]
        self.suppABCD = None
        
    def getId(self):
        return (self.TID, self.vid)

    def getVId(self):
        return self.vid

    def drawFrame(self):
        self.QIds = [wx.NewId(), wx.NewId()]
        self.MapredMapQ = [wx.TextCtrl(self.mapFrame, self.QIds[0], style=wx.TE_PROCESS_ENTER),
                           wx.TextCtrl(self.mapFrame, self.QIds[1], style=wx.TE_PROCESS_ENTER)]
        colors = self.getColors()
        self.MapredMapQ[0].SetForegroundColour(colors[0])
        self.MapredMapQ[1].SetForegroundColour(colors[1])
        ssizetxt = 90
        lsizetxt = 90
        self.MapredMapInfoJL = wx.StaticText(self.mapFrame, size=(lsizetxt,-1), style=wx.ALIGN_RIGHT|wx.ALL)
        self.MapredMapInfoVL = wx.StaticText(self.mapFrame, size=(lsizetxt,-1), style=wx.ALIGN_RIGHT|wx.ALL)
        self.MapredMapInfoJV = wx.StaticText(self.mapFrame, size=(ssizetxt,-1), style=wx.ALIGN_LEFT|wx.ALL)
        self.MapredMapInfoVV = wx.StaticText(self.mapFrame, size=(ssizetxt,-1), style=wx.ALIGN_LEFT|wx.ALL)
        self.MapredMapInfoIL = wx.StaticText(self.mapFrame, size=(lsizetxt,-1), style=wx.ALIGN_RIGHT|wx.ALL)
        self.MapredMapInfoUL = wx.StaticText(self.mapFrame, size=(lsizetxt,-1), style=wx.ALIGN_RIGHT|wx.ALL)
        self.MapredMapInfoIV = wx.StaticText(self.mapFrame, size=(ssizetxt,-1), style=wx.ALIGN_LEFT|wx.ALL)
        self.MapredMapInfoUV = wx.StaticText(self.mapFrame, size=(ssizetxt,-1), style=wx.ALIGN_LEFT|wx.ALL)
        self.MapredMapInfoRL = wx.StaticText(self.mapFrame, size=(lsizetxt,-1), style=wx.ALIGN_RIGHT|wx.ALL)
        self.MapredMapInfoBL = wx.StaticText(self.mapFrame, size=(lsizetxt,-1), style=wx.ALIGN_RIGHT|wx.ALL)
        self.MapredMapInfoRV = wx.StaticText(self.mapFrame, size=(ssizetxt,-1), style=wx.ALIGN_LEFT|wx.ALL)
        self.MapredMapInfoBV = wx.StaticText(self.mapFrame, size=(ssizetxt,-1), style=wx.ALIGN_LEFT|wx.ALL)

        self.MapredMapInfoOL = wx.StaticText(self.mapFrame, size=(lsizetxt,-1), style=wx.ALIGN_RIGHT|wx.ALL)
        self.MapredMapInfoTL = wx.StaticText(self.mapFrame, size=(lsizetxt,-1), style=wx.ALIGN_RIGHT|wx.ALL)
        self.MapredMapInfoOV = wx.StaticText(self.mapFrame, size=(ssizetxt,-1), style=wx.ALIGN_LEFT|wx.ALL)
        self.MapredMapInfoTV = wx.StaticText(self.mapFrame, size=(ssizetxt,-1), style=wx.ALIGN_LEFT|wx.ALL)

        colors = self.getColors()
        self.MapredMapInfoBV.SetForegroundColour(colors[0])
        self.MapredMapInfoRV.SetForegroundColour(colors[1])
        self.MapredMapInfoIV.SetForegroundColour(colors[2])
        
        flags = wx.ALL
        self.MapValbox1 = wx.BoxSizer(wx.VERTICAL)
        self.MapValbox1.Add(self.MapredMapInfoJL, 0, border=0, flag=flags)
        self.MapValbox1.Add(self.MapredMapInfoVL, 0, border=0, flag=flags)
        
        self.MapValbox3 = wx.BoxSizer(wx.VERTICAL)
        self.MapValbox3.Add(self.MapredMapInfoBL, 0, border=0, flag=flags)
        self.MapValbox3.Add(self.MapredMapInfoUL, 0, border=0, flag=flags)

        self.MapValbox5 = wx.BoxSizer(wx.VERTICAL)
        self.MapValbox5.Add(self.MapredMapInfoIL, 0, border=0, flag=flags)
        self.MapValbox5.Add(self.MapredMapInfoOL, 0, border=0, flag=flags)

        self.MapValbox7 = wx.BoxSizer(wx.VERTICAL)
        self.MapValbox7.Add(self.MapredMapInfoRL, 0, border=0, flag=flags)
        self.MapValbox7.Add(self.MapredMapInfoTL, 0, border=0, flag=flags)

        flags = wx.EXPAND | wx.ALL
        self.MapValbox2 = wx.BoxSizer(wx.VERTICAL)
        self.MapValbox2.Add(self.MapredMapInfoJV, 0, border=0, flag=flags)
        self.MapValbox2.Add(self.MapredMapInfoVV, 0, border=0, flag=flags)

        self.MapValbox4 = wx.BoxSizer(wx.VERTICAL)
        self.MapValbox4.Add(self.MapredMapInfoBV, 0, border=0, flag=flags)
        self.MapValbox4.Add(self.MapredMapInfoUV, 0, border=0, flag=flags)

        self.MapValbox6 = wx.BoxSizer(wx.VERTICAL)
        self.MapValbox6.Add(self.MapredMapInfoIV, 0, border=0, flag=flags)
        self.MapValbox6.Add(self.MapredMapInfoOV, 0, border=0, flag=flags)

        self.MapValbox8 = wx.BoxSizer(wx.VERTICAL)
        self.MapValbox8.Add(self.MapredMapInfoRV, 0, border=0, flag=flags)
        self.MapValbox8.Add(self.MapredMapInfoTV, 0, border=0, flag=flags)


        self.MaphboxVals = wx.BoxSizer(wx.HORIZONTAL)
        self.MaphboxVals.Add(self.MapValbox1, 0, border=3, flag=wx.ALIGN_RIGHT | wx.ALL | wx.EXPAND)
        self.MaphboxVals.Add(self.MapValbox2, 0, border=3, flag=wx.ALIGN_LEFT | wx.ALL | wx.EXPAND)
        self.MaphboxVals.Add(self.MapValbox3, 0, border=3, flag=wx.ALIGN_RIGHT | wx.ALL | wx.EXPAND)
        self.MaphboxVals.Add(self.MapValbox4, 0, border=3, flag=wx.ALIGN_LEFT | wx.ALL | wx.EXPAND)
        self.MaphboxVals.Add(self.MapValbox5, 0, border=3, flag=wx.ALIGN_RIGHT | wx.ALL | wx.EXPAND)
        self.MaphboxVals.Add(self.MapValbox6, 0, border=3, flag=wx.ALIGN_LEFT | wx.ALL | wx.EXPAND)
        self.MaphboxVals.Add(self.MapValbox7, 0, border=3, flag=wx.ALIGN_RIGHT | wx.ALL | wx.EXPAND)
        self.MaphboxVals.Add(self.MapValbox8, 0, border=3, flag=wx.ALIGN_LEFT | wx.ALL | wx.EXPAND)

        self.Mapvbox3 = wx.BoxSizer(wx.VERTICAL)
        flags = wx.ALIGN_CENTER | wx.ALL | wx.ALIGN_CENTER_VERTICAL
        ## if self.parent.dw.getCoords() is not None:
        self.Mapvbox3.Add(self.MapcanvasMap, 1, wx.ALIGN_CENTER | wx.TOP | wx.EXPAND)
        
        self.Mapvbox3.Add(self.MapredMapQ[0], 0, border=3, flag=flags | wx.EXPAND)
        self.Mapvbox3.Add(self.MapredMapQ[1], 0, border=3, flag=flags | wx.EXPAND)
        self.Mapvbox3.Add(self.MaphboxVals, 0, border=3, flag=flags)

        for add_box in self.additionalElements():
            self.Mapvbox3.Add(add_box, 0, border=3, flag=flags)
            
        self.mapFrame.SetSizer(self.Mapvbox3)
        self.Mapvbox3.Fit(self.mapFrame)

    def additionalElements(self):
        return []

    def additionalBinds(self):
        for button in self.buttons:
            button["element"].Bind(wx.EVT_BUTTON, button["function"])

    def binds(self):
        # self.mapFrame.Bind(wx.EVT_KEY_UP, self.mkey_press_callback)
        self.mapFrame.Bind(wx.EVT_CLOSE, self.OnQuit)
#        self.mapFrame.Bind(wx.EVT_ENTER_WINDOW, self.OnFocus)
        self.panel.Bind(wx.EVT_SET_FOCUS, self.OnFocus)                
        self.MapredMapQ[0].Bind(wx.EVT_TEXT_ENTER, self.OnEditQuery)
        self.MapredMapQ[1].Bind(wx.EVT_TEXT_ENTER, self.OnEditQuery)
        self.additionalBinds()
        
    def OnExpand(self, event):
        red = self.updateQuery()
        self.parent.expandFV(red)

    def OnFocus(self, event):
        self.parent.selectedMap = self.getId()
        event.Skip()
        
    def OnQuit(self, event):
        if self.source_list is not None and self.parent.tabs.has_key(self.source_list):
            self.parent.tabs[self.source_list]["tab"].unregisterView(self.getId())
        self.parent.deleteView(self.getId())

    def OnEditQuery(self, event):
        if event.GetId() in self.QIds:
            side = self.QIds.index(event.GetId())
            self.updateQuery(side)

    def refresh(self):
        red = Redescription.fromQueriesPair(self.queries, self.parent.dw.data)
        red.setRestrictedSupp(self.parent.dw.data)
        self.suppABCD = red.supports().getVectorABCD()
        self.updateText(red)
        self.updateMap()

    def updateQuery(self, sd=None, query=None):
        if sd is None:
            queries = [self.parseQuery(0),self.parseQuery(1)]
        else:
            queries = [None, None]
            if query is None:
                queries[sd] = self.parseQuery(sd)
            else:
                queries[sd] = query

        changed = False
        for side in [0,1]:
            if queries[side] != None and queries[side] != self.queries[side]:
                self.queries[side] = queries[side]
                changed = True

        if changed:
            red = Redescription.fromQueriesPair(self.queries, self.parent.dw.data)
            red.setRestrictedSupp(self.parent.dw.data)
            self.suppABCD = red.supports().getVectorABCD()
            self.updateText(red)
            self.updateMap()
            self.updateOriginal(red)
            self.updateHist(red)
        else: ### wrongly formatted query or not edits, revert
            for side in [0,1]:
                self.updateQueryText(self.queries[side], side)
            red = Redescription.fromQueriesPair(self.queries, self.parent.dw.data)
        return red

    def setSource(self, source_list=None):
        self.source_list=source_list

    def setCurrent(self, qr=None, source_list=None):
        if qr is not None:
            if type(qr) in [list, tuple]:
                queries = qr
                red = Redescription.fromQueriesPair(qr, self.parent.dw.data)
            else:
                red = qr
                queries = [red.query(0), red.query(1)]
            self.queries = queries
            red.setRestrictedSupp(self.parent.dw.data)
            self.suppABCD = red.supports().getVectorABCD()
            self.setSource(source_list)
            self.updateText(red)
            self.updateMap()
            self.updateHist(red)
            return red

    def parseQuery(self, side):
        stringQ = self.MapredMapQ[side].GetValue().strip()
        try:
            query = Query.parse(stringQ, self.parent.dw.data.getNames(side))
        except:
            query = None
        if query is not None and (len(stringQ) > 0 and len(query) == 0):
            query = None
        return query                    
        
    def drawMap(self):
        """ Draws the map
        """
        pass
            
    def updateMap(self):
        """ Redraws the map
        """
        pass


    def updateHist(self, red = None):
        if red is not None:
            if self.source_list != "hist":
                self.parent.tabs["hist"]["tab"].insertItem(red, -1)

    def updateOriginal(self, red = None):
        if red is not None and self.source_list is not None and self.parent.tabs.has_key(self.source_list):
            self.parent.tabs[self.source_list]["tab"].updateEdit(self.getId(), red)

    def updateQueryText(self, query, side):
        self.MapredMapQ[side].ChangeValue(query.dispU(self.parent.dw.data.getNames(side)))

    def updateText(self, red = None):
        """ Reset red fields and info
        """
        if red is not None:
            for side in [0, 1]:
                self.updateQueryText(red.queries[side], side)
            self.setMapredInfo(red)

    def setMapredInfo(self, red = None, details=None):
        if red is None:
            self.MapredMapInfoJL.SetLabel("")
            self.MapredMapInfoJV.SetLabel("")
            self.MapredMapInfoVL.SetLabel("")
            self.MapredMapInfoVV.SetLabel("")
            self.MapredMapInfoIL.SetLabel("")
            self.MapredMapInfoIV.SetLabel("")
            self.MapredMapInfoUL.SetLabel("")
            self.MapredMapInfoUV.SetLabel("")
            self.MapredMapInfoBL.SetLabel("")
            self.MapredMapInfoBV.SetLabel("")
            self.MapredMapInfoRL.SetLabel("")
            self.MapredMapInfoRV.SetLabel("")
            self.MapredMapInfoOL.SetLabel("")
            self.MapredMapInfoOV.SetLabel("")
            self.MapredMapInfoTL.SetLabel("")
            self.MapredMapInfoTV.SetLabel("")

        else:
            self.MapredMapInfoJL.SetLabel(self.label_jacc)
            self.MapredMapInfoJV.SetLabel("%1.5f" % red.getRoundAcc())
            self.MapredMapInfoVL.SetLabel(self.label_pval)
            self.MapredMapInfoVV.SetLabel("%1.5f" % red.getRoundPVal())
            self.MapredMapInfoIL.SetLabel(self.label_cardI)
            self.MapredMapInfoIV.SetLabel("%i" % red.getLenI())
            self.MapredMapInfoUL.SetLabel(self.label_cardU)
            self.MapredMapInfoUV.SetLabel("%i" % red.getLenU())
            self.MapredMapInfoBL.SetLabel(self.label_cardAlpha)
            self.MapredMapInfoBV.SetLabel("%i" % red.getLenA())
            self.MapredMapInfoRL.SetLabel(self.label_cardBeta)
            self.MapredMapInfoRV.SetLabel("%i" % red.getLenB())

            self.MapredMapInfoOL.SetLabel(self.label_cardO)
            self.MapredMapInfoOV.SetLabel("%i" % red.getLenO())
            self.MapredMapInfoTL.SetLabel(self.label_cardT)
            self.MapredMapInfoTV.SetLabel("%i" % red.getLenT())

    def updateEmphasize(self, colhigh='#FFFF00', review=True):
        if self.source_list is not None:
            lids = self.parent.tabs[self.source_list]["tab"].getEmphasizedR(self.getId())
            self.emphasizeOnOff(turn_on=lids, turn_off=None, colhigh=colhigh, review=review)

    def emphasizeOnOff(self, turn_on=set(), turn_off=set(), colhigh='#FFFF00', review=True):
        self.emphasizeOff(turn_off)
        self.emphasizeOn(turn_on, colhigh)
        if review:
            self.MapcanvasMap.draw()

    def emphasizeOn(self, lids,  colhigh='#FFFF00'):
        draw_settings = self.getDrawSettings()
        for lid in lids:
            if self.highl.has_key(lid):
                continue
            pi = self.suppABCD[lid]
            self.highl[lid] = []
            self.highl[lid].extend(self.axe.plot(self.getCoords(0,lid), self.getCoords(1,lid),
                                          mfc=colhigh, mec=draw_settings[pi]["color_e"],
                                          marker=draw_settings["shape"], markersize=draw_settings[pi]["size"],
                                          markeredgewidth=1, linestyle='None'))

            if len(lids) == 1:
                self.hight[lid] = []
                self.hight[lid].append(self.axe.annotate('%d' % lid, xy=(self.getCoords(0,lid), self.getCoords(1,lid)),  xycoords='data',
                                                     xytext=(-10, 15), textcoords='offset points', color= draw_settings[pi]["color_e"],
                                                     size=10, va="center", backgroundcolor="#FFFFFF",
                                                     bbox=dict(boxstyle="round", facecolor="#FFFFFF", ec=draw_settings[pi]["color_e"]),
                                                     arrowprops=dict(arrowstyle="wedge,tail_width=1.", fc="#FFFFFF", ec=draw_settings[pi]["color_e"],
                                                                     patchA=None, patchB=self.el, relpos=(0.2, 0.5))
                                                     ))
            
    def emphasizeOff(self, lids = None):
        if lids is None:
            lids = self.highl.keys()
        for lid in lids:
            if self.hight.has_key(lid):
                while len(self.hight[lid]) > 0:
                    t = self.hight[lid].pop()
                    if t in self.axe.texts:
                        self.axe.texts.remove(t)
                del self.hight[lid]

            if self.highl.has_key(lid):
                while len(self.highl[lid]) > 0:
                    t = self.highl[lid].pop()
                    if t in self.axe.lines:
                        self.axe.lines.remove(t)
                del self.highl[lid]

    def sendEmphasize(self, lids):
        if self.source_list is not None and self.parent.tabs.has_key(self.source_list):
            self.parent.tabs[self.source_list]["tab"].setEmphasizedR(self.getId(), lids, True)

    def sendFlipEmphasizedR(self):
        if self.source_list is not None and self.parent.tabs.has_key(self.source_list):
            self.parent.tabs[self.source_list]["tab"].doFlipEmphasizedR(self.getId())

    def OnPick(self, event):
        if event.mouseevent.button == 3 and (isinstance(event.artist, Line2D) or isinstance(event.artist, Polygon)):
            self.sendEmphasize([int(event.artist.get_gid().split(".")[0])])

    def key_press_callback(self, event):
        if event.inaxes:
            self.do_key(event.key)

    def mkey_press_callback(self, event):
        self.do_key(chr(event.GetKeyCode()).lower())
        
    def do_key(self, key):
        'whenever a key is pressed'
        points = set()
        if key=='s' and self.mc is not None:
            points = self.apply_mask(self.mc.get_path())
            self.mc.clear()
        elif key in self.map_select_supp.keys():
            points = [i for (i,p) in enumerate(self.suppABCD) if p in self.map_select_supp[key]]
        elif key == " ":
            self.sendFlipEmphasizedR()
        if len(points) > 0:
            self.sendEmphasize(points)
        return points

    def apply_mask(self, path, radius=0.0):
        if path is not None and self.getCoords() is not None:
            points = np.transpose((self.getCoords(0), self.getCoords(1)))
            return [i for i,point in enumerate(points) if path.contains_point(point, radius=radius)]
        return []

    def getCoords(axi=None, ids=None):
        return None

    def getColors(self):
        t = self.parent.dw.getPreferences()
        colors = []
        for color_k, color in GView.colors_def:
            try:
                color_t = t[color_k]["data"]
            except:
                color_t = color
            colors.append(color_t)
        return colors

    def getDot(self):
        t = self.parent.dw.getPreferences()
        try:
            dot_shape = t["dot_shape"]["data"]
            dot_size = t["dot_size"]["data"]
        except:
            dot_shape = GView.DOT_SHAPE
            dot_size = GView.DOT_SIZE
        return (dot_shape, dot_size)

    def getMissDetails(self):
        t = self.parent.dw.getPreferences()
        if t["miss_details"]["data"] == "Yes":
            return True
        return False

    def getDrawSettings(self):
        colors = self.getColors()
        dot_shape, dot_size = self.getDot()
        return {"draw_pord": dict([(v,p) for (p,v) in enumerate([SParts.mud, SParts.mua, SParts.mub, SParts.muaB, SParts.mubB,
                              SParts.delta, SParts.beta, SParts.alpha, SParts.gamma])]),
                "shape": dot_shape,
                SParts.alpha: {"color_e": [i/255.0 for i in colors[0]],
                               "color_f": [i/255.0 for i in colors[0]],
                               "alpha": GView.DOT_ALPHA, "size": dot_size},
                SParts.beta: {"color_e": [i/255.0 for i in colors[1]],
                              "color_f": [i/255.0 for i in colors[1]],
                               "alpha": GView.DOT_ALPHA, "size": dot_size},
                SParts.gamma: {"color_e": [i/255.0 for i in colors[2]],
                               "color_f": [i/255.0 for i in colors[2]],
                               "alpha": GView.DOT_ALPHA, "size": dot_size},
                SParts.mua: {"color_e": [i/255.0 for i in colors[0]],
                             "color_f": [0.5,0.5,0.5],
                             "alpha": GView.DOT_ALPHA, "size": dot_size-1},
                SParts.mub: {"color_e": [i/255.0 for i in colors[1]],
                             "color_f": [0.5,0.5,0.5],
                             "alpha": GView.DOT_ALPHA, "size": dot_size-1},
                SParts.muaB: {"color_e": [0.5,0.5,0.5],
                              "color_f": [i/255.0 for i in colors[1]],
                              "alpha": GView.DOT_ALPHA, "size": dot_size-1},
                SParts.mubB: {"color_e": [0.5,0.5,0.5],
                              "color_f": [i/255.0 for i in colors[0]],
                              "alpha": GView.DOT_ALPHA, "size": dot_size-1},
                SParts.mud: {"color_e": [0.5,0.5,0.5],
                             "color_f": [0.5, 0.5, 0.5],
                             "alpha": GView.DOT_ALPHA, "size": dot_size-1},
                SParts.delta: {"color_e": [0.5,0.5,0.5],
                               "color_f": [0.5, 0.5, 0.5],
                               "alpha": GView.DOT_ALPHA, "size": dot_size}
                }

        
def HTMLColorToRGB(colorstring):
    """ convert #RRGGBB to an (R, G, B) tuple """
    colorstring = colorstring.strip()
    if colorstring[0] == '#': colorstring = colorstring[1:]
    if len(colorstring) != 6:
        raise ValueError, "input #%s is not in #RRGGBB format" % colorstring
    r, g, b = colorstring[:2], colorstring[2:4], colorstring[4:]
    r, g, b = [int(n, 16) for n in (r, g, b)]
    return (r, g, b)
