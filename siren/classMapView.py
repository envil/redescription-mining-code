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

class MapView:

    COLOR_LEFT = (255,0,0)
    COLOR_RIGHT = (0,0,255)
    COLOR_INTER = (160,32,240)
    DOT_ALPHA = 0.6
    
    # COLOR_LEFT = (175,175,175)
    # COLOR_RIGHT = (125,125,125)
    # COLOR_INTER = (25,25,25)
    # DOT_ALPHA = 0.6
    
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
        self.coord_proj = None
        self.mapFrame = wx.Frame(None, -1, self.parent.titleMap)
        self.panel = wx.Panel(self.mapFrame, -1)
        self.draw_map()
        self.draw_frame()
        self.binds()
        self.mapFrame.Show()

    def getId(self):
        return self.vid

    def draw_frame(self):
        self.MapredMapQL = wx.TextCtrl(self.mapFrame, style=wx.TE_PROCESS_ENTER) # , size=(550,-1)
        self.MapredMapQL.SetForegroundColour(MapView.COLOR_LEFT)
        self.MapredMapQR = wx.TextCtrl(self.mapFrame, style=wx.TE_PROCESS_ENTER)
        self.MapredMapQR.SetForegroundColour(MapView.COLOR_RIGHT)
        ssizetxt = 40
        lsizetxt = 90
        self.MapredMapInfoJL = wx.StaticText(self.mapFrame, size=(ssizetxt,-1), style=wx.ALIGN_RIGHT|wx.ALL)
        self.MapredMapInfoVL = wx.StaticText(self.mapFrame, size=(ssizetxt,-1), style=wx.ALIGN_RIGHT|wx.ALL)
        self.MapredMapInfoJV = wx.StaticText(self.mapFrame, size=(lsizetxt,-1), style=wx.ALIGN_LEFT|wx.ALL)
        self.MapredMapInfoVV = wx.StaticText(self.mapFrame, size=(lsizetxt,-1), style=wx.ALIGN_LEFT|wx.ALL)
        self.MapredMapInfoIL = wx.StaticText(self.mapFrame, size=(lsizetxt,-1), style=wx.ALIGN_RIGHT|wx.ALL)
        self.MapredMapInfoUL = wx.StaticText(self.mapFrame, size=(lsizetxt,-1), style=wx.ALIGN_RIGHT|wx.ALL)
        self.MapredMapInfoIV = wx.StaticText(self.mapFrame, size=(ssizetxt,-1), style=wx.ALIGN_LEFT|wx.ALL)
        self.MapredMapInfoUV = wx.StaticText(self.mapFrame, size=(ssizetxt,-1), style=wx.ALIGN_LEFT|wx.ALL)
        self.MapredMapInfoRL = wx.StaticText(self.mapFrame, size=(lsizetxt,-1), style=wx.ALIGN_RIGHT|wx.ALL)
        self.MapredMapInfoBL = wx.StaticText(self.mapFrame, size=(lsizetxt,-1), style=wx.ALIGN_RIGHT|wx.ALL)
        self.MapredMapInfoRV = wx.StaticText(self.mapFrame, size=(ssizetxt,-1), style=wx.ALIGN_LEFT|wx.ALL)
        self.MapredMapInfoBV = wx.StaticText(self.mapFrame, size=(ssizetxt,-1), style=wx.ALIGN_LEFT|wx.ALL)
        self.MapredMapInfoIV.SetForegroundColour(MapView.COLOR_INTER)
        self.MapredMapInfoBV.SetForegroundColour(MapView.COLOR_LEFT)
        self.MapredMapInfoRV.SetForegroundColour(MapView.COLOR_RIGHT)
        self.button_expand = wx.Button(self.mapFrame, size=(80,-1), label="Expand")

        flags = wx.ALL
        self.MapValbox1 = wx.BoxSizer(wx.VERTICAL)
        self.MapValbox1.Add(self.MapredMapInfoJL, 0, border=0, flag=flags)
        self.MapValbox1.Add(self.MapredMapInfoVL, 0, border=0, flag=flags)
        
        self.MapValbox3 = wx.BoxSizer(wx.VERTICAL)
        self.MapValbox3.Add(self.MapredMapInfoIL, 0, border=0, flag=flags)
        self.MapValbox3.Add(self.MapredMapInfoUL, 0, border=0, flag=flags)

        self.MapValbox5 = wx.BoxSizer(wx.VERTICAL)
        self.MapValbox5.Add(self.MapredMapInfoBL, 0, border=0, flag=flags)
        self.MapValbox5.Add(self.MapredMapInfoRL, 0, border=0, flag=flags)

        flags = wx.EXPAND | wx.ALL
        self.MapValbox2 = wx.BoxSizer(wx.VERTICAL)
        self.MapValbox2.Add(self.MapredMapInfoJV, 0, border=0, flag=flags)
        self.MapValbox2.Add(self.MapredMapInfoVV, 0, border=0, flag=flags)

        self.MapValbox4 = wx.BoxSizer(wx.VERTICAL)
        self.MapValbox4.Add(self.MapredMapInfoIV, 0, border=0, flag=flags)
        self.MapValbox4.Add(self.MapredMapInfoUV, 0, border=0, flag=flags)

        self.MapValbox6 = wx.BoxSizer(wx.VERTICAL)
        self.MapValbox6.Add(self.MapredMapInfoBV, 0, border=0, flag=flags)
        self.MapValbox6.Add(self.MapredMapInfoRV, 0, border=0, flag=flags)

        self.MaphboxVals = wx.BoxSizer(wx.HORIZONTAL)
        self.MaphboxVals.Add(self.MapValbox1, 0, border=3, flag=wx.ALIGN_RIGHT | wx.ALL | wx.EXPAND)
        self.MaphboxVals.Add(self.MapValbox2, 0, border=3, flag=wx.ALIGN_LEFT | wx.ALL | wx.EXPAND)
        self.MaphboxVals.Add(self.MapValbox3, 0, border=3, flag=wx.ALIGN_RIGHT | wx.ALL | wx.EXPAND)
        self.MaphboxVals.Add(self.MapValbox4, 0, border=3, flag=wx.ALIGN_LEFT | wx.ALL | wx.EXPAND)
        self.MaphboxVals.Add(self.MapValbox5, 0, border=3, flag=wx.ALIGN_RIGHT | wx.ALL | wx.EXPAND)
        self.MaphboxVals.Add(self.MapValbox6, 0, border=3, flag=wx.ALIGN_LEFT | wx.ALL | wx.EXPAND)

        self.Maphbox4 = wx.BoxSizer(wx.HORIZONTAL)
        flags = wx.ALIGN_CENTER | wx.ALL
        self.Maphbox4.Add(self.MaptoolbarMap, 0, border=3, flag=flags)
        self.Maphbox4.Add(self.button_expand, 0, border=3, flag=flags)

        self.Mapvbox3 = wx.BoxSizer(wx.VERTICAL)
        flags = wx.ALIGN_CENTER | wx.ALL | wx.ALIGN_CENTER_VERTICAL
        self.Mapvbox3.Add(self.MapcanvasMap, 1, wx.ALIGN_CENTER | wx.TOP | wx.EXPAND)
        self.Mapvbox3.Add(self.MapredMapQL, 0, border=3, flag=flags | wx.EXPAND)
        self.Mapvbox3.Add(self.MapredMapQR, 0, border=3, flag=flags | wx.EXPAND)
        self.Mapvbox3.Add(self.MaphboxVals, 0, border=3, flag=flags)
        self.Mapvbox3.Add(self.Maphbox4, 0, border=3, flag=flags)
        self.mapFrame.SetSizer(self.Mapvbox3)
        self.Mapvbox3.Fit(self.mapFrame)

    def binds(self):
        self.mapFrame.Bind(wx.EVT_CLOSE, self.OnQuit)
#        self.mapFrame.Bind(wx.EVT_ENTER_WINDOW, self.OnFocus)
        self.panel.Bind(wx.EVT_SET_FOCUS, self.OnFocus)
        self.button_expand.Bind(wx.EVT_BUTTON, self.OnExpand)
        self.MapredMapQL.Bind(wx.EVT_TEXT_ENTER, self.OnEditRed)
        self.MapredMapQR.Bind(wx.EVT_TEXT_ENTER, self.OnEditRed)

    def OnExpand(self, event):
        red = self.redraw_map()
        self.parent.expand(red)

    def OnFocus(self, event):
        self.parent.selectedMap = self.vid
        event.Skip()
        
    def OnQuit(self, event):
        if self.source_list != None and self.parent.tabs.has_key(self.source_list):
            self.parent.tabs[self.source_list]["tab"].unregisterView(self.vid)
        self.parent.deleteView(self.vid)
        
    def OnEditRed(self, event):
        self.updateRed()

    def setCurrentRed(self, red, source_list=None):
        self.source_list=source_list
        self.MapredMapQL.ChangeValue(red.queries[0].dispU(self.parent.details['names'][0]))
        self.MapredMapQR.ChangeValue(red.queries[1].dispU(self.parent.details['names'][1]))
#        self.MapredMapInfo.ChangeValue(red.dispLParts())
        self.setMapredInfo(red)
        
    def updateRed(self):
        red = self.redraw_map()
        if red != None and self.source_list != None and self.parent.tabs.has_key(self.source_list):
            self.parent.tabs[self.source_list]["tab"].updateEdit(self.vid, red)
        return red
        
    def parseRed(self):
        queryL = Query.parse(self.MapredMapQL.GetValue().strip(), self.parent.details['names'][0])
        queryR = Query.parse(self.MapredMapQR.GetValue().strip(), self.parent.details['names'][1])
        if queryL != None and queryR != None: 
            return Redescription.fromQueriesPair([queryL, queryR], self.parent.dw.data) 
        
    def draw_map(self):
        """ Draws the map
        """
        self.MapfigMap = plt.figure()
        self.Mapcurr_mapi = 0
        self.MapcanvasMap = FigCanvas(self.mapFrame, -1, self.MapfigMap)
        
        self.MaptoolbarMap = NavigationToolbar(self.MapcanvasMap)

        self.MapfigMap.clear()
        llon, ulon, llat, ulat = self.parent.dw.getCoordExtrema()
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

        if self.parent.dw.getCoord() != None:
            self.coord_proj = m(self.parent.dw.getCoord()[0], self.parent.dw.getCoord()[1])
            height = 3; width = 3
            self.gca = plt.gca()

        self.MapcanvasMap.draw()
            
    def redraw_map(self, event=None):
        """ Redraws the map
        """
        red = self.parseRed()
        if red == None:
            return self.parent.tabs["Hist"].data[-1]

        self.MapredMapQL.ChangeValue(red.queries[0].dispU(self.parent.details['names'][0]))
        self.MapredMapQR.ChangeValue(red.queries[1].dispU(self.parent.details['names'][1]))
        #self.MapredMapInfo.ChangeValue(red.dispLParts())
        self.setMapredInfo(red)

        if self.coord_proj != None:
            m = self.axe
            colors = [[i/255.0 for i in MapView.COLOR_LEFT], [i/255.0 for i in MapView.COLOR_RIGHT], [i/255.0 for i in MapView.COLOR_INTER]]
            sizes = [MapView.DOT_SIZE, MapView.DOT_SIZE, MapView.DOT_SIZE]
            markers = [MapView.DOT_SHAPE, MapView.DOT_SHAPE, MapView.DOT_SHAPE]
            i = 0
            while len(self.lines):
                #plt.gca().patches.remove(self.lines.pop())
                self.gca.axes.lines.remove(self.lines.pop())
            self.points_ids = []
            for part in red.partsNoMiss():
                if len(part) > 0:
                    lip = list(part)
                    self.points_ids.extend(lip)
                    ids = np.array(lip)
                    self.lines.extend(m.plot(self.coord_proj[0][ids],self.coord_proj[1][ids], mfc=colors[i], mec=colors[i], marker=markers[i], markersize=sizes[i], linestyle='None', alpha=MapView.DOT_ALPHA, picker=3))
                else:
                    self.lines.extend(m.plot([],[], mfc=colors[i], mec=colors[i], marker=markers[i], markersize=sizes[i], linestyle='None'))
                i += 1
            #plt.legend(('Left query only', 'Right query only', 'Both queries'), 'upper left', shadow=True, fancybox=True)
#            self.MapfigMap.canvas.mpl_connect('pick_event', self.OnPick)
            self.MapcanvasMap.draw()
        return red

    # def OnPick(self, event):
    #     #### TODO drafting for info on click, uncomment binding  (mpl_connect)
    #     inds = event.ind
    #     for ind in inds:
    #         print self.points_ids[ind], self.coord_proj[0][self.points_ids[ind]], self.coord_proj[1][self.points_ids[ind]]

    def setMapredInfo(self, red):
        if red == None:
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
        else:
            self.MapredMapInfoJL.SetLabel("J=")
            self.MapredMapInfoJV.SetLabel("%1.5f" % red.acc())
            self.MapredMapInfoVL.SetLabel("pVal=")
            self.MapredMapInfoVV.SetLabel("%1.5f" % red.pVal())
            self.MapredMapInfoIL.SetLabel(u"|LHS \u2229 RHS|=")
            self.MapredMapInfoIV.SetLabel("%i" % (red.sParts.lpart(2,0)))
            self.MapredMapInfoUL.SetLabel(u"|LHS \u222A RHS|=")
            self.MapredMapInfoUV.SetLabel("%i" % (red.sParts.lpart(0,0)+red.sParts.lpart(1,0)+red.sParts.lpart(2,0)))
            self.MapredMapInfoBL.SetLabel(u"|LHS \\ RHS|=")
            self.MapredMapInfoBV.SetLabel("%i" % (red.sParts.lpart(0,0)))
            self.MapredMapInfoRL.SetLabel(u"|RHS \\ LHS|=")
            self.MapredMapInfoRV.SetLabel("%i" % (red.sParts.lpart(1,0)))
