### TODO check which imports are needed 
import wx
import numpy as np
# The recommended way to use wx with mpl is with the WXAgg
# backend. 
import matplotlib
matplotlib.use('WXAgg')
import matplotlib.pyplot as plt
from mpl_toolkits.basemap import Basemap
from matplotlib.backends.backend_wxagg import \
    FigureCanvasWxAgg as FigCanvas, \
    NavigationToolbar2WxAgg as NavigationToolbar

from reremi.classQuery import Query
from reremi.classRedescription import Redescription

import pdb

class MapView:

    label_jacc="acc     ="
    label_pval="p-value   ="
    label_cardAlpha=u"|E_{1,0}|  ="
    label_cardBeta=u"|E_{0,1}|  ="
    label_cardU=u"|E\E_{0,0}| ="
    label_cardI=u"|E_{1,1}|  ="
    label_cardO=u"|E_{0,0}|  ="
    label_cardT=u"|E|      ="

    colors_def = [("color_l", (0,0,255)), ("color_r", (255,0,0)), ("color_i", (160,32,240))]
    DOT_ALPHA = 0.6
        
    WATER_COLOR = "#FFFFFF"
    GROUND_COLOR = "#FFFFFF"
    LINES_COLOR = "gray"

    DOT_SHAPE = 's'
    DOT_SIZE = 3

    
    def __init__(self, parent, vid):
        self.parent = parent
        self.source_list = None
        self.vid = vid
        self.lines = []
        self.coords_proj = None
        self.mapFrame = wx.Frame(None, -1, self.parent.titleMap)
        self.panel = wx.Panel(self.mapFrame, -1)
        self.drawMap()
        self.drawFrame()
        self.binds()
        self.mapFrame.Show()
        self.queries = [Query(), Query()]

    def getId(self):
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
        self.button_expand = wx.Button(self.mapFrame, size=(80,-1), label="Expand")

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


        self.Maphbox4 = wx.BoxSizer(wx.HORIZONTAL)
        flags = wx.ALIGN_CENTER | wx.ALL
        if self.parent.dw.getCoords() is not None:
            self.Maphbox4.Add(self.MaptoolbarMap, 0, border=3, flag=flags)
        self.Maphbox4.Add(self.button_expand, 0, border=3, flag=flags)

        self.Mapvbox3 = wx.BoxSizer(wx.VERTICAL)
        flags = wx.ALIGN_CENTER | wx.ALL | wx.ALIGN_CENTER_VERTICAL
        if self.parent.dw.getCoords() is not None:
            self.Mapvbox3.Add(self.MapcanvasMap, 1, wx.ALIGN_CENTER | wx.TOP | wx.EXPAND)
        self.Mapvbox3.Add(self.MapredMapQ[0], 0, border=3, flag=flags | wx.EXPAND)
        self.Mapvbox3.Add(self.MapredMapQ[1], 0, border=3, flag=flags | wx.EXPAND)
        self.Mapvbox3.Add(self.MaphboxVals, 0, border=3, flag=flags)
        self.Mapvbox3.Add(self.Maphbox4, 0, border=3, flag=flags)
        self.mapFrame.SetSizer(self.Mapvbox3)
        self.Mapvbox3.Fit(self.mapFrame)

    def binds(self):
        self.mapFrame.Bind(wx.EVT_CLOSE, self.OnQuit)
#        self.mapFrame.Bind(wx.EVT_ENTER_WINDOW, self.OnFocus)
        self.panel.Bind(wx.EVT_SET_FOCUS, self.OnFocus)
        self.button_expand.Bind(wx.EVT_BUTTON, self.OnExpand)
        self.MapredMapQ[0].Bind(wx.EVT_TEXT_ENTER, self.OnEditQuery)
        self.MapredMapQ[1].Bind(wx.EVT_TEXT_ENTER, self.OnEditQuery)

    def OnExpand(self, event):
        red = self.updateQueries()
        self.parent.expand(red)

    def OnFocus(self, event):
        self.parent.selectedMap = self.vid
        event.Skip()
        
    def OnQuit(self, event):
        if self.source_list is not None and self.parent.tabs.has_key(self.source_list):
            self.parent.tabs[self.source_list]["tab"].unregisterView(self.vid)
        self.parent.deleteView(self.vid)

    def OnEditQuery(self, event):
        if event.GetId() in self.QIds:
            side = self.QIds.index(event.GetId())
            self.updateQuery(side)

    def updateQuery(self, side):
        query = self.parseQuery(side)
        if query != None and query != self.queries[side]:
            self.queries[side] = query
            red = Redescription.fromQueriesPair(self.queries, self.parent.dw.data)
            self.updateText(red)
            self.updateMap(red)
            self.updateOriginal(red)
            self.updateHist(red)
        else:
            self.updateQueryText(self.queries[side], side)
        return self.queries[side]

    def updateQueries(self):
        queries = [self.parseQuery(0),self.parseQuery(1)]
        for side in [0,1]:
            if queries[side] is None:
                queries[side] = self.queries[side]
        if queries != self.queries:
            self.queries = queries
            red = Redescription.fromQueriesPair(self.queries, self.parent.dw.data)
            self.updateText(red)
            self.updateMap(red)
            self.updateOriginal(red)
            self.updateHist(red)
        else:
            red = Redescription.fromQueriesPair(self.queries, self.parent.dw.data)
            for side in [0,1]:
                self.updateQueryText(self.queries[side], side)
        return red

    def setCurrent(self, qr=None, source_list=None):
        if qr is not None:
            if type(qr) in [list, tuple]:
                queries = qr
                red = Redescription.fromQueriesPair(qr, self.parent.dw.data)
            else:
                red = qr
                queries = [red.query(0), red.query(1)]
            self.queries = queries
            self.source_list=source_list
            self.updateText(red)
            self.updateMap(red)
            self.updateHist(red)

    def parseQuery(self, side):
        stringQ = self.MapredMapQ[side].GetValue().strip()
        try:
            query = Query.parse(stringQ, self.parent.details['names'][side])
        except:
            query = None
        if query is not None and (len(stringQ) > 0 and len(query) == 0):
            query = None
        return query                    

        
    def drawMap(self):
        """ Draws the map
        """
        if self.parent.dw.getCoords() is None:
            self.coords_proj = None
            return
        self.MapfigMap = plt.figure()
        self.Mapcurr_mapi = 0
        self.MapcanvasMap = FigCanvas(self.mapFrame, -1, self.MapfigMap)
        
        self.MaptoolbarMap = NavigationToolbar(self.MapcanvasMap)

        self.MapfigMap.clear()
        llon, ulon, llat, ulat = self.parent.dw.getCoordsExtrema()
        m = Basemap(llcrnrlon=llon, llcrnrlat=llat, urcrnrlon=ulon, urcrnrlat=ulat, \
                    resolution = 'c', projection = 'mill', \
                    lon_0 = llon + (ulon-llon)/2.0, \
                    lat_0 = llat + (ulat-llat)/2.04)
        self.axe = m
        m.ax = self.MapfigMap.add_axes([0, 0, 1, 1])

        m.drawcoastlines(color=MapView.LINES_COLOR)
        m.drawcountries(color=MapView.LINES_COLOR)
        m.drawmapboundary(fill_color=MapView.WATER_COLOR) 
        m.fillcontinents(color=MapView.GROUND_COLOR, lake_color=MapView.WATER_COLOR) #'#EEFFFF')
            #m.etopo()

        if self.parent.dw.getCoords() is not None:
            self.coords_proj = m(self.parent.dw.getCoords()[0], self.parent.dw.getCoords()[1])
            height = 3; width = 3
            self.gca = plt.gca()

        self.MapcanvasMap.draw()
            
    def updateMap(self, red = None):
        """ Redraws the map
        """

        if red is not None and self.coords_proj is not None:
            m = self.axe

            colors = self.getColors()
            dot_shape, dot_size = self.getDot()
            (alpha, beta, gamma, delta, mua, mub, muaB, mubB, mud) = range(9)
            draw_settings = {alpha: {"color_e": [i/255.0 for i in colors[0]], "color_f": [i/255.0 for i in colors[0]],
                                     "size": dot_size, "shape": dot_shape, "alpha": MapView.DOT_ALPHA},
                             beta: {"color_e": [i/255.0 for i in colors[1]], "color_f": [i/255.0 for i in colors[1]],
                                     "size": dot_size, "shape": dot_shape, "alpha": MapView.DOT_ALPHA},
                             gamma: {"color_e": [i/255.0 for i in colors[2]], "color_f": [i/255.0 for i in colors[2]],
                                     "size": dot_size, "shape": dot_shape, "alpha": MapView.DOT_ALPHA},
                             mua: {"color_e": [i/255.0 for i in colors[0]], "color_f": [0.5,0.5,0.5],
                                     "size": dot_size-1, "shape": dot_shape, "alpha": MapView.DOT_ALPHA-0.3},
                             mub: {"color_e": [i/255.0 for i in colors[1]], "color_f": [0.5,0.5,0.5],
                                     "size": dot_size-1, "shape": dot_shape, "alpha": MapView.DOT_ALPHA-0.3},
                             muaB: {"color_e": [0.5,0.5,0.5], "color_f": [i/255.0 for i in colors[1]],
                                     "size": dot_size-1, "shape": dot_shape, "alpha": MapView.DOT_ALPHA-0.3},
                             mubB: {"color_e": [0.5,0.5,0.5], "color_f": [i/255.0 for i in colors[0]],
                                     "size": dot_size-1, "shape": dot_shape, "alpha": MapView.DOT_ALPHA-0.3},
                             mud: {"color_e": [0.5,0.5,0.5], "color_f": [0.5, 0.5, 0.5],
                                     "size": dot_size-1, "shape": dot_shape, "alpha": MapView.DOT_ALPHA-0.3}
                             }
            
            while len(self.lines):
                #plt.gca().patches.remove(self.lines.pop())
                self.gca.axes.lines.remove(self.lines.pop())
            self.points_ids = []
            if self.getMissDetails():
                parts = red.partsAll()
            else:
                parts = red.partsThree()
            for pi, part in enumerate(parts):
                if len(part) > 0 and draw_settings.has_key(pi):
                    lip = list(part)
                    self.points_ids.extend(lip)
                    ids = np.array(lip)
                    self.lines.extend(m.plot(self.coords_proj[0][ids], self.coords_proj[1][ids],
                                             mfc=draw_settings[pi]["color_f"], mec=draw_settings[pi]["color_e"],
                                             marker=draw_settings[pi]["shape"], markersize=draw_settings[pi]["size"],
                                             linestyle='None', alpha=draw_settings[pi]["alpha"], picker=3))
                else:
                    self.lines.extend(m.plot([],[]))

            #plt.legend(('Left query only', 'Right query only', 'Both queries'), 'upper left', shadow=True, fancybox=True)
#            self.MapfigMap.canvas.mpl_connect('pick_event', self.OnPick)
            self.MapcanvasMap.draw()
        return red

    # def OnPick(self, event):
    #     #### TODO drafting for info on click, uncomment binding  (mpl_connect)
    #     inds = event.ind
    #     for ind in inds:
    #         print self.points_ids[ind], self.coords_proj[0][self.points_ids[ind]], self.coords_proj[1][self.points_ids[ind]]

    def updateHist(self, red = None):
        if red is not None:
            if self.source_list != "hist":
                self.parent.tabs["hist"]["tab"].insertItem(red, -1)

    def updateOriginal(self, red = None):
        if red is not None and self.source_list is not None and self.parent.tabs.has_key(self.source_list):
            self.parent.tabs[self.source_list]["tab"].updateEdit(self.vid, red)

    def updateQueryText(self, query, side):
        self.MapredMapQ[side].ChangeValue(query.dispU(self.parent.details['names'][side]))

    def updateText(self, red = None):
        """ Reset red fields and info
        """
        if red is not None:
            for side in [0, 1]:
                self.updateQueryText(red.queries[side], side)
            self.setMapredInfo(red)

    def setMapredInfo(self, red = None):
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
            self.MapredMapInfoJV.SetLabel("%1.5f" % red.acc())
            self.MapredMapInfoVL.SetLabel(self.label_pval)
            self.MapredMapInfoVV.SetLabel("%1.5f" % red.pVal())
            self.MapredMapInfoIL.SetLabel(self.label_cardI)
            self.MapredMapInfoIV.SetLabel("%i" % (red.sParts.lpart(2,0)))
            self.MapredMapInfoUL.SetLabel(self.label_cardU)
            self.MapredMapInfoUV.SetLabel("%i" % (red.sParts.lpart(0,0)+red.sParts.lpart(1,0)+red.sParts.lpart(2,0)))
            self.MapredMapInfoBL.SetLabel(self.label_cardAlpha)
            self.MapredMapInfoBV.SetLabel("%i" % (red.sParts.lpart(0,0)))
            self.MapredMapInfoRL.SetLabel(self.label_cardBeta)
            self.MapredMapInfoRV.SetLabel("%i" % (red.sParts.lpart(1,0)))

            self.MapredMapInfoOL.SetLabel(self.label_cardO)
            self.MapredMapInfoOV.SetLabel("%i" % (red.sParts.lpart(3,0)))
            self.MapredMapInfoTL.SetLabel(self.label_cardT)
            self.MapredMapInfoTV.SetLabel("%i" % (red.sParts.N))


    def getColors(self):
        t = self.parent.dw.getPreferences()
        colors = []
        for color_k, color in MapView.colors_def:
            try:
                tmp = t[color_k]["data"]
                color_t = HTMLColorToRGB(tmp)
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
            dot_shape = MapView.DOT_SHAPE
            dot_size = MapView.DOT_SIZE
        return (dot_shape, dot_size)

    def getMissDetails(self):
        t = self.parent.dw.getPreferences()
        if t["miss_details"]["data"] == "Yes":
            return True
        return False
        
def HTMLColorToRGB(colorstring):
    """ convert #RRGGBB to an (R, G, B) tuple """
    colorstring = colorstring.strip()
    if colorstring[0] == '#': colorstring = colorstring[1:]
    if len(colorstring) != 6:
        raise ValueError, "input #%s is not in #RRGGBB format" % colorstring
    r, g, b = colorstring[:2], colorstring[2:4], colorstring[4:]
    r, g, b = [int(n, 16) for n in (r, g, b)]
    return (r, g, b)
