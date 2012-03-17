import os
import pprint
import random
import wx, wx.grid, wx.html, wx.richtext
from threading import *
# import warnings
# warnings.simplefilter("ignore")

# The recommended way to use wx with mpl is with the WXAgg
# backend. 
#
import matplotlib
matplotlib.use('WXAgg')
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
from mpl_toolkits.basemap import Basemap
from matplotlib.backends.backend_wxagg import \
    FigureCanvasWxAgg as FigCanvas, \
    NavigationToolbar2WxAgg as NavigationToolbar
import numpy as np
#import matplotlib.pyplot as plt
import re, random
import pdb
from classRedescription import Redescription
from classData import Data
from classQuery import Query
from classSettings import Settings
from classLog import Log
import greedyRedescriptions as greedyRed

# Thread class that executes processing
class ExpanderThread(Thread):
    """Expander Thread Class."""
    def __init__(self, data, setts, red, logger):
        """Init Expander Thread Class."""
        Thread.__init__(self)
        self.want_to_live = True
        self.data = data
        self.setts = setts
        self.red = red
        self.logger = logger

        # This starts the thread running on creation, but you could
        # also make the GUI thread responsible for calling this
        self.start()

    def run(self):
        tmpE = greedyRed.part_run(self)

    def abort(self):
        self.want_to_live = False

class MinerThread(Thread):
    """Miner Thread Class."""
    def __init__(self, data, setts, logger):
        """Init Miner Thread Class."""
        Thread.__init__(self)
        self.want_to_live = True
        self.data = data
        self.setts = setts
        self.logger = logger

        # This starts the thread running on creation, but you could
        # also make the GUI thread responsible for calling this
        self.start()

    def run(self):
        tmpE = greedyRed.full_run(self)
        
    def abort(self):
        self.want_to_live = False


class Message(wx.PyEvent):
    TYPES_MESSAGES = {None: wx.NewId(), 'result': wx.NewId(), 'progress': wx.NewId(), 'status': wx.NewId()}
    
    """Simple event for communication purposes."""
    def __init__(self, type_event, data):
        """Init Result Event."""
        wx.PyEvent.__init__(self)
        self.SetEventType(type_event)
        self.data = data

    def sendMessage(output, message, type_message):
        if Message.TYPES_MESSAGES.has_key(type_message):
           wx.PostEvent(output, Message(Message.TYPES_MESSAGES[type_message], message))
    sendMessage = staticmethod(sendMessage)

class CustomGridTable(wx.grid.PyGridTableBase):
    def __init__(self, parent, tabId, frame):
        wx.grid.PyGridTableBase.__init__(self)
        self.parent = parent
        self.tabId = tabId
        self.fields = []
        self.data = []
        self.sortids = []
        self.details = {}
        self.sortP = (None, False)
        self.currentRows = len(self.sortids)
        self.currentColumns = len(self.fields)

        #### GRID
        self.grid = wx.grid.Grid(frame)
        self.grid.SetTable(self)
        self.grid.Bind(wx.grid.EVT_GRID_LABEL_LEFT_CLICK, self.sortData)
        self.grid.SetLabelBackgroundColour('#DBD4D4')
        self.grid.RegisterDataType(wx.grid.GRID_VALUE_STRING,
                              wx.grid.GridCellAutoWrapStringRenderer(),
                              wx.grid.GridCellAutoWrapStringEditor()) 
        self.grid.Bind(wx.grid.EVT_GRID_CELL_LEFT_CLICK, self.OnSelectData)
        self.grid.Bind(wx.grid.EVT_GRID_CELL_LEFT_DCLICK, self.OnViewData)
        self.grid.Bind(wx.grid.EVT_GRID_CELL_RIGHT_CLICK, self.OnRightClick)

        self.grid.EnableEditing(False)
        self.grid.AutoSizeColumns(True)

    # def showPopupMenu(self, event):
    #     self.table.highlightRow(event.GetRow())
    #     parent.currentList = self

    def GetNumberRows(self):
        """Return the number of rows in the grid"""
        return len(self.sortids)

    def GetColLabelValue(self, col):
        """Return the number of rows in the grid"""
        direct = '  '
        if col == self.sortP[0]:
            if self.sortP[1]:
                direct = u"\u2191"
            else:
                direct = u"\u2193" 
        return "  %s %s" % (self.fields[col][1], direct)

    def GetNumberCols(self):
        """Return the number of columns in the grid"""
        return len(self.fields)

    def IsEmptyCell(self, row, col):
        """Return True if the cell is empty"""
        if row < len(self.sortids) and col < len(self.fields):
            x = self.sortids[row]
            methode = eval(self.fields[col][0])
            return methode(self.details) == None
        else:
            return True

    def GetTypeName(self, row, col):
        """Return the name of the data type of the value in the cell"""
        return wx.grid.GRID_VALUE_STRING
        # if row < len(self.sortids) and col < len(self.fields):
        #     x = self.sortids[row]
        #     methode = eval(self.fields[col][0])
        #     return type(methode(self.details))
        # else:
        #     return None

    def GetValue(self, row, col):
        """Return the value of a cell"""
        if row < len(self.sortids) and col < len(self.fields):
            x = self.sortids[row]
            methode = eval(self.fields[col][0])
            return "%s" % methode(self.details)
        else:
            return None

    def GetRowData(self, row):
        """Return the data of a row"""
        if row < len(self.sortids):
            return self.data[self.sortids[row]]
        else:
            return None
                                  
    def SetValue(self, row, col, value):
        pass

    def updateData(self, data, fieldsRed, details):
        self.details = details
        self.fields = fieldsRed
        self.resetData(data)
        self.currentColumns = len(self.fields)

    def appendRow(self, rowD):
        if len(self.sortids) == 0 or self.data[self.sortids[-1]] != rowD:
            self.sortids.append(len(self.data))
            self.data.append(rowD)
            self.updateSort()
            self.ResetView()
            self.currentRows = len(self.sortids)

    def extendData(self, rowsD):
        self.sortids.extend([len(self.data)+ i for i in range(len(rowsD))])
        self.data.extend(rowsD)
        self.updateSort()
        self.ResetView()
        self.currentRows = len(self.sortids)

    def resetData(self, rowsD):
        self.data = rowsD
        self.sortids = range(len(rowsD))
        self.updateSort()
        self.ResetView()
        self.currentRows = len(self.sortids)
       
    def ResetView(self):
        """Trim/extend the control's rows and update all values"""
        self.GetView().BeginBatch()
        for current, new, delmsg, addmsg in [
                (self.currentRows, self.GetNumberRows(), wx.grid.GRIDTABLE_NOTIFY_ROWS_DELETED, wx.grid.GRIDTABLE_NOTIFY_ROWS_APPENDED),
                (self.currentColumns, self.GetNumberCols(), wx.grid.GRIDTABLE_NOTIFY_COLS_DELETED, wx.grid.GRIDTABLE_NOTIFY_COLS_APPENDED),
        ]:
            if new < current:
                msg = wx.grid.GridTableMessage(
                        self,
                        delmsg,
                        new,    # position
                        current-new,
                )
                self.GetView().ProcessTableMessage(msg)
            elif new > current:
                msg = wx.grid.GridTableMessage(
                        self,
                        addmsg,
                        new-current
                )
                self.GetView().ProcessTableMessage(msg)
        self.GetView().EndBatch()
        self.GetView().AutoSize()

    def setHighlightRow(self, row):
        #pass
        self.GetView().SelectRow(row)
        self.GetView().SetGridCursor(row,0)
        # for j in range(self.GetNumberCols()):
        #     self.GetView().SetCellBackgroundColour(row,j,'#DBD4FF')
        self.GetView().ForceRefresh()

    def getHighlightRow(self):
        return self.GetRowData(self.GetView().GetGridCursorRow())
        
    def sortData(self, event):
        colS = event.GetCol()
        old = self.sortP[0]
        if self.sortP[0] == colS:
            self.sortP = (self.sortP[0], not self.sortP[1])
        else:
            self.sortP = (colS, True)
        self.updateSort()
        self.ResetView()
        
    def updateSort(self):
        selected_rows = self.GetView().GetSelectedRows()
        selected_id = None
        if len(selected_rows) > 0 and selected_rows[0] < len(self.sortids) :
            selected_id = self.sortids[selected_rows[0]]

        if self.sortP[0] != None:
            self.sortids.sort(key= lambda x: eval(self.fields[self.sortP[0]][0])(self.details), reverse=self.sortP[1])
        if selected_id != None:
            self.setHighlightRow(self.sortids.index(selected_id))

    def OnSelectData(self, event):
        if event.GetRow() < len(self.data):
            self.setHighlightRow(event.GetRow())

    def OnRightClick(self, event):
        if event.GetRow() < len(self.data):
            self.setHighlightRow(event.GetRow())
            self.parent.selectedList = self
            self.parent.makePopupMenu(self.parent.toolFrame)

    def OnViewData(self, event):
        if event.GetRow() < len(self.data):
            self.setHighlightRow(event.GetRow())
            self.viewData()

class RedGridTable(CustomGridTable):
    def viewData(self):
        mapV = self.parent.getSelectedMapView()
        mapV.setCurrentRed(self.getHighlightRow())
        mapV.updateRed(self.tabId != "Hist")

class VarGridTable(CustomGridTable):     
    def viewData(self):
        mapV = self.parent.getSelectedMapView()
        datVar = self.getHighlightRow()
        if datVar.side == 1:
            mapV.MapredMapQL.ChangeValue("")
            mapV.MapredMapQR.ChangeValue(datVar.getItem().dispU(False, self.parent.details['names'][1]))
        else:
            mapV.MapredMapQL.ChangeValue(datVar.getItem().dispU(False, self.parent.details['names'][0]))
            mapV.MapredMapQR.ChangeValue("")
#            mapV.MapredMapInfo.ChangeValue("")
        mapV.setMapredInfo(None)
        mapV.updateRed(False)



class MapView:
    def __init__(self, parent, vid):
        self.parent = parent
        self.vid = vid
        self.lines = []
        self.coord_proj = None
        self.mapFrame = wx.Frame(None, -1, self.parent.titleMap)
        self.mapFrame.Bind(wx.EVT_CLOSE, self.OnQuit)
        self.mapFrame.Bind(wx.EVT_ENTER_WINDOW, self.OnFocus)
        self.MapredMapQL = wx.TextCtrl(self.mapFrame, style=wx.TE_PROCESS_ENTER) # , size=(550,-1)
        self.MapredMapQL.SetForegroundColour('blue')
        self.MapredMapQR = wx.TextCtrl(self.mapFrame, style=wx.TE_PROCESS_ENTER)
        self.MapredMapQR.SetForegroundColour('red')
        sizetxt = 100
        self.MapredMapInfoJL = wx.StaticText(self.mapFrame, size=(sizetxt,-1))
        self.MapredMapInfoVL = wx.StaticText(self.mapFrame, size=(sizetxt,-1))
        self.MapredMapInfoJV = wx.StaticText(self.mapFrame, size=(sizetxt,-1))
        self.MapredMapInfoVV = wx.StaticText(self.mapFrame, size=(sizetxt,-1))
        self.MapredMapInfoIL = wx.StaticText(self.mapFrame, size=(sizetxt,-1))
        self.MapredMapInfoUL = wx.StaticText(self.mapFrame, size=(sizetxt,-1))
        self.MapredMapInfoIV = wx.StaticText(self.mapFrame, size=(sizetxt,-1))
        self.MapredMapInfoUV = wx.StaticText(self.mapFrame, size=(sizetxt,-1))
        self.MapredMapInfoRL = wx.StaticText(self.mapFrame, size=(sizetxt,-1))
        self.MapredMapInfoBL = wx.StaticText(self.mapFrame, size=(sizetxt,-1))
        self.MapredMapInfoRV = wx.StaticText(self.mapFrame, size=(sizetxt,-1))
        self.MapredMapInfoBV = wx.StaticText(self.mapFrame, size=(sizetxt,-1))
        self.MapredMapInfoIV.SetForegroundColour('purple')
        self.MapredMapInfoBV.SetForegroundColour('blue')
        self.MapredMapInfoRV.SetForegroundColour('red')
        self.button_expand = wx.Button(self.mapFrame, size=(80,-1), label="Expand")
        self.button_stop = wx.Button(self.mapFrame, size=(80,-1), label="Stop")
        self.button_expand.Bind(wx.EVT_BUTTON, self.parent.OnExpand)
        self.button_stop.Bind(wx.EVT_BUTTON, self.parent.OnStop)
        self.MapredMapQL.Bind(wx.EVT_TEXT_ENTER, self.OnEditRed)
        self.MapredMapQR.Bind(wx.EVT_TEXT_ENTER, self.OnEditRed)

        self.MapfigMap = plt.figure()
        self.Mapcurr_mapi = 0
        self.MapcanvasMap = FigCanvas(self.mapFrame, -1, self.MapfigMap)
        
        self.MaptoolbarMap = NavigationToolbar(self.MapcanvasMap)
 
        flags = wx.ALIGN_RIGHT | wx.EXPAND
        self.MapValbox1 = wx.BoxSizer(wx.VERTICAL)
        self.MapValbox1.Add(self.MapredMapInfoJL, 0, border=3, flag=flags)
        self.MapValbox1.Add(self.MapredMapInfoVL, 0, border=3, flag=flags)
        
        self.MapValbox3 = wx.BoxSizer(wx.VERTICAL)
        self.MapValbox3.Add(self.MapredMapInfoIL, 0, border=3, flag=flags)
        self.MapValbox3.Add(self.MapredMapInfoUL, 0, border=3, flag=flags)

        self.MapValbox5 = wx.BoxSizer(wx.VERTICAL)
        self.MapValbox5.Add(self.MapredMapInfoBL, 0, border=3, flag=flags)
        self.MapValbox5.Add(self.MapredMapInfoRL, 0, border=3, flag=flags)

        flags = wx.ALIGN_LEFT | wx.EXPAND
        self.MapValbox2 = wx.BoxSizer(wx.VERTICAL)
        self.MapValbox2.Add(self.MapredMapInfoJV, 0, border=3, flag=flags)
        self.MapValbox2.Add(self.MapredMapInfoVV, 0, border=3, flag=flags)

        self.MapValbox4 = wx.BoxSizer(wx.VERTICAL)
        self.MapValbox4.Add(self.MapredMapInfoIV, 0, border=3, flag=flags)
        self.MapValbox4.Add(self.MapredMapInfoUV, 0, border=3, flag=flags)

        self.MapValbox6 = wx.BoxSizer(wx.VERTICAL)
        self.MapValbox6.Add(self.MapredMapInfoBV, 0, border=3, flag=flags)
        self.MapValbox6.Add(self.MapredMapInfoRV, 0, border=3, flag=flags)

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
        self.Maphbox4.Add(self.button_stop, 0, border=3, flag=flags)

        self.Mapvbox3 = wx.BoxSizer(wx.VERTICAL)
        flags = wx.ALIGN_CENTER | wx.ALL | wx.ALIGN_CENTER_VERTICAL
        self.Mapvbox3.Add(self.MapcanvasMap, 1, wx.ALIGN_CENTER | wx.TOP | wx.EXPAND)
        self.Mapvbox3.Add(self.MapredMapQL, 0, border=3, flag=flags | wx.EXPAND)
        self.Mapvbox3.Add(self.MapredMapQR, 0, border=3, flag=flags | wx.EXPAND)
        self.Mapvbox3.Add(self.MaphboxVals, 0, border=3, flag=flags)
        self.Mapvbox3.Add(self.Maphbox4, 0, border=3, flag=flags)
        self.mapFrame.SetSizer(self.Mapvbox3)
        self.Mapvbox3.Fit(self.mapFrame)
        self.draw_map()
        self.mapFrame.Show()

    def OnFocus(self, event):
        self.mapFrame.Raise()
        self.parent.selectedMap = self.vid
        
    def OnQuit(self, event):
        self.parent.deleteView(self.vid)
        
    def OnEditRed(self, event):
        self.updateRed()

    def setCurrentRed(self, red):
        self.MapredMapQL.ChangeValue(red.queries[0].dispU(self.parent.details['names'][0]))
        self.MapredMapQR.ChangeValue(red.queries[1].dispU(self.parent.details['names'][1]))
#        self.MapredMapInfo.ChangeValue(red.dispLParts())
        self.setMapredInfo(red)
        
    def updateRed(self, addHist=True):
        red = self.redraw_map()
        if red != None and addHist:
            self.parent.lists["Hist"].appendRow(red)
        return red
        
    def parseRed(self):
        queryL = Query.parseAny(self.MapredMapQL.GetValue().strip(), self.parent.details['names'][0])
        queryR = Query.parseAny(self.MapredMapQR.GetValue().strip(), self.parent.details['names'][1])
        if queryL != None and queryR != None: 
            return Redescription.fromQueriesPair([queryL, queryR], self.parent.data) 
        
    def draw_map(self):
        """ Draws the map
        """

        self.MapfigMap.clear()
        if self.parent.coord_extrema != None and self.parent.coord != None:            

            m = Basemap(llcrnrlon=self.parent.coord_extrema[0][0], \
                    llcrnrlat=self.parent.coord_extrema[1][0], \
                    urcrnrlon=self.parent.coord_extrema[0][1], \
                    urcrnrlat=self.parent.coord_extrema[1][1], \
                    resolution = 'c', \
                    projection = 'mill', \
                    lon_0 = self.parent.coord_extrema[0][0] + (self.parent.coord_extrema[0][1]-self.parent.coord_extrema[0][0])/2.0, \
                    lat_0 = self.parent.coord_extrema[1][0] + (self.parent.coord_extrema[1][1]-self.parent.coord_extrema[1][0])/2.04)
            self.axe = m
            m.ax = self.MapfigMap.add_axes([0, 0, 1, 1])

            m.drawcoastlines(color='gray')
            m.drawcountries(color='gray')
            m.drawmapboundary(fill_color='#EEFFFF') 
            m.fillcontinents(color='#FFFFFF', lake_color='#EEFFFF')
            #m.etopo()
            self.coord_proj = m(self.parent.coord[0], self.parent.coord[1])
            height = 3; width = 3
            self.gca = plt.gca()
            #self.corners= [ zip(*[ m(self.coord[0][id]+off[0]*width, self.coord[1][id]+off[1]*height) for off in [(-1,-1), (-1,1), (1,1), (1,-1)]]) for id in range(len(self.coord[0]))] 
            self.MapcanvasMap.draw()
            
    def redraw_map(self, event=None):
        """ Redraws the map
        """
        red = self.parseRed()
        if red == None:
            return self.parent.lists["Hist"].data[-1]

        self.MapredMapQL.ChangeValue(red.queries[0].dispU(self.parent.details['names'][0]))
        self.MapredMapQR.ChangeValue(red.queries[1].dispU(self.parent.details['names'][1]))
        #self.MapredMapInfo.ChangeValue(red.dispLParts())
        self.setMapredInfo(red)

        if self.parent.coord_extrema != None and self.parent.coord != None:
            m = self.axe
            colors = ['b', 'r', 'purple']
            sizes = [3, 3, 4]
            markers = ['s', 's', 's']
            i = 0
            while len(self.lines):
                #plt.gca().patches.remove(self.lines.pop())
                self.gca.axes.lines.remove(self.lines.pop())
            self.points_ids = []
            for part in red.partsNoMiss():
                if len(part) > 0:
                    # for id in part:
                    #     self.lines.extend(plt.fill(self.corners[id][0], self.corners[id][1], fc=colors[i], ec=colors[i], alpha=0.5))
                    lip = list(part)
                    self.points_ids.extend(lip)
                    ids = np.array(lip)
                    self.lines.extend(m.plot(self.coord_proj[0][ids],self.coord_proj[1][ids], mfc=colors[i], mec=colors[i], marker=markers[i], markersize=sizes[i], linestyle='None', alpha=0.5, picker=3))
                else:
                    self.lines.extend(m.plot([],[], mfc=colors[i], mec=colors[i], marker=markers[i], markersize=sizes[i], linestyle='None'))
                i += 1
            #plt.legend(('Left query only', 'Right query only', 'Both queries'), 'upper left', shadow=True, fancybox=True)
            self.MapfigMap.canvas.mpl_connect('pick_event', self.OnPick)
            self.MapcanvasMap.draw()
        return red

    def OnPick(self, event):
        inds = event.ind
        for ind in inds:
            print self.points_ids[ind], self.coord_proj[0][self.points_ids[ind]], self.coord_proj[1][self.points_ids[ind]]

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

        
class Siren():
    """ The main frame of the application
    """
    # titleTool = 'SpatIal REdescription miniNg :: TOOLS'
    # titleMap = 'SpatIal REdescription miniNg :: MAPS'
    titleTool = 'SIREN :: tools'
    titleMap = 'SIREN :: maps'
    titleHelp = 'SIREN :: help'
    helpURL = "http://www.cs.helsinki.fi/u/galbrun/redescriptors/"
    fieldsRed = [('self.data[x].getQueryLU', 'Query LHS'), ('self.data[x].getQueryRU', 'Query RHS'), ('self.data[x].getAcc', 'Acc'), ('self.data[x].getPVal', 'p-Value')]
    fieldsVar = [('self.data[x].getId', 'Id'), ('self.data[x].getName', 'Name'), ('self.data[x].getType', 'Type')]
    fieldsVarTypes = {1: [('self.data[x].getDensity', 'Density')], 2:[('self.data[x].getCategories', 'Categories')], 3:[('self.data[x].getMin', 'Min'), ('self.data[x].getMax', 'Max')]}

    def getFieldRed(red, fieldId):
        methode = eval(Siren.fieldsRed[fieldId][0])
        return methode(self.details)

    def getFieldLabel(fieldId):
        return Siren.fieldsRed[fieldId][1]

    def __init__(self):
        self.toolFrame = wx.Frame(None, -1, self.titleTool)
        self.toolFrame.Bind(wx.EVT_CLOSE, self.OnQuit)

        self.toolFrame.Connect(-1, -1, Message.TYPES_MESSAGES[None], self.OnLogger)
        self.toolFrame.Connect(-1, -1, Message.TYPES_MESSAGES['result'], self.OnResult)
        self.toolFrame.Connect(-1, -1, Message.TYPES_MESSAGES['progress'], self.OnProgress)
        self.toolFrame.Connect(-1, -1, Message.TYPES_MESSAGES['status'], self.OnStatus)

        self.num_filename=''
        self.bool_filename=''
        self.coo_filename=''
        self.queries_filename=''
        self.settings_filename=''
        
        self.mapViews = {}
        self.selectedMap = -1
 
        self.coord = None
        self.coord_extrema = None
        self.data = None
        self.details = None
        self.worker = None
        
        self.reloadSettings()
        self.create_tool_panel()

        # #### COMMENT OUT TO LOAD RAJAPAJA ON STARTUP
        # self.num_filename='./rajapaja/worldclim_tp.densenum'
        # self.bool_filename='./rajapaja/mammals.datbool'
        # self.coo_filename='./rajapaja/coordinates.names'
        # self.queries_filename='./rajapaja/rajapaja.queries'
        # self.settings_filename='./rajapaja/rajapaja.conf'

        # #### COMMENT OUT TO LOAD US ON STARTUP
        # self.num_filename='./us/us_politics_funds_cont.densenum'
        # self.bool_filename='./us/us_socio_eco_cont.densenum'
        # self.coo_filename='./us/us_coordinates_cont.names'
        # self.queries_filename='./us/us.queries'
        # self.settings_filename='./us/us.conf'

        # #### COMMENT OUT TO LOAD SOMETHING ON STARTUP
        # self.reloadData()
        # self.reloadCoordinates()
        # self.reloadReds()
        # self.text_setts.LoadFile(self.settings_filename)
	# self.textbox_num_filename.SetValue(str(self.num_filename))
	# self.textbox_bool_filename.SetValue(str(self.bool_filename))
        # self.textbox_coo_filename.SetValue(str(self.coo_filename))
        # self.textbox_queries_filename.SetValue(str(self.queries_filename))
        # self.textbox_settings_filename.SetValue(str(self.settings_filename))
	
    def deleteView(self, vid):
        if vid in self.mapViews.keys():
            self.mapViews[vid].mapFrame.Destroy()
            del self.mapViews[vid]

    def deleteAllViews(self):
        self.selectedMap = -1
        for mapV in self.mapViews.values():
            mapV.mapFrame.Destroy()
        self.mapViews = {}
        
    def getSelectedMapView(self):
        if self.selectedMap not in self.mapViews.keys():
            self.selectedMap = len(self.mapViews)
            self.mapViews[self.selectedMap] = MapView(self, self.selectedMap)    
        return self.mapViews[self.selectedMap]


    def OnExpand(self, event):
        self.progress_bar.Show()
        red = self.getSelectedMapView().redraw_map()
        if red.length(0) + red.length(1) > 0:
            self.worker = ExpanderThread(self.data, self.setts, red, self.logger)
        else:
            self.worker = MinerThread(self.data, self.setts, self.logger)

    def OnStop(self, event):
        """Show Result status."""
        if self.worker != None:
            self.worker.abort()
        
    def OnResult(self, event):
        """Show Result status."""
        if event.data != None:
            if event.data[0] == 1:
                self.lists["Exp"].extendData(event.data[1])
            if event.data[0] == 0:
                self.lists["Exp"].resetData(event.data[1])

    def OnProgress(self, event):
        """Update progress status."""
        brange, bvalue = event.data
        if brange == -1:
            self.progress_bar.SetValue(0)
            self.progress_bar.Hide()
        brange = max(brange, bvalue)
        if self.progress_bar.GetRange() != brange:
            self.progress_bar.SetRange(brange)
        self.progress_bar.SetValue(bvalue)

    def OnLogger(self, event):
        """Show Result status."""
        if event.data != None:
            self.text_log.AppendText("%s\n" % event.data)

    def OnStatus(self, event):
        """Show Result status."""
        if event.data != None:
            self.statusbar.SetStatusText("%s" % event.data, 0)

    def create_tool_panel(self):
        """ Creates the main panel with all the controls on it:
             * mpl canvas 
             * mpl navigation toolbar
             * Control panel for interaction
        """
	self.makeMenu(self.toolFrame)
        self.makeStatus(self.toolFrame)
	self.tabbed = wx.Notebook(self.toolFrame, -1, style=(wx.NB_TOP)) #, size=(3600, 1200))

        ### FILES PANEL
        self.panel1 = wx.Panel(self.tabbed, -1)
	self.button_num_filename = wx.Button(self.panel1, size=(150,-1), label="Change Left File")
	self.button_num_filename.Bind(wx.EVT_BUTTON, self.doOpenFileN)
	self.textbox_num_filename = wx.TextCtrl(self.panel1, size=(500,-1), style=wx.TE_READONLY)
	self.button_bool_filename = wx.Button(self.panel1, size=(150,-1), label="Change Right File")
	self.button_bool_filename.Bind(wx.EVT_BUTTON, self.doOpenFileB)
	self.textbox_bool_filename = wx.TextCtrl(self.panel1, size=(500,-1), style=wx.TE_READONLY)
	self.button_coo_filename = wx.Button(self.panel1, size=(150,-1), label="Change Coordinates File")
	self.button_coo_filename.Bind(wx.EVT_BUTTON, self.doOpenFileC)
	self.textbox_coo_filename = wx.TextCtrl(self.panel1, size=(500,-1), style=wx.TE_READONLY)
        self.button_queries_filename = wx.Button(self.panel1, size=(150,-1), label="Change Queries File")
	self.button_queries_filename.Bind(wx.EVT_BUTTON, self.doOpenFileQ)
	self.textbox_queries_filename = wx.TextCtrl(self.panel1, size=(500,-1), style=wx.TE_READONLY)
        self.button_settings_filename = wx.Button(self.panel1, size=(150,-1), label="Change Settings File")
	self.button_settings_filename.Bind(wx.EVT_BUTTON, self.doOpenFileS)
	self.textbox_settings_filename = wx.TextCtrl(self.panel1, size=(500,-1), style=wx.TE_READONLY)
        self.tabbed.AddPage(self.panel1, "Files")

        ### LISTS PANELS
        self.selectedList = None
        self.lists = {}
        lists_settings = [(0, "LHS Variables", "Var", False),
                          (1, "RHS Variables", "Var", False),
                          ("Reds", "Redescriptions", "Red", False),
                          ("Exp", "Expanding", "Red", False),
                          ("Hist", "History", "Red", True)]
        for (tabId, titleTab, typeList, hide) in lists_settings:
            if typeList == "Red":
                self.lists[tabId] = RedGridTable(self, tabId, self.tabbed)
            elif typeList == "Var":
                self.lists[tabId] = VarGridTable(self, tabId, self.tabbed)
            if hide:
                self.lists[tabId].grid.Hide()
            self.tabbed.AddPage(self.lists[tabId].grid, titleTab)

        ### LOG PANEL
        self.panelLog = wx.Panel(self.tabbed, -1)
        self.panelLog.Hide()
	self.text_log = wx.TextCtrl(self.panelLog, size=(-1,-1), style=wx.TE_READONLY|wx.TE_MULTILINE)
        self.tabbed.AddPage(self.panelLog, "Log")

        ### SETTINGS PANEL
        self.panelSetts = wx.Panel(self.tabbed, -1)
        self.panelSetts.Hide()
        self.text_setts = wx.TextCtrl(self.panelSetts, size=(-1,-1), style=wx.TE_MULTILINE)
        self.tabbed.AddPage(self.panelSetts, "Settings")

        ### SIZER FOR FILES PANEL
	self.vbox1 = wx.BoxSizer(wx.VERTICAL)
        
        self.hboxL1 = wx.BoxSizer(wx.HORIZONTAL)
        flags = wx.ALIGN_LEFT | wx.ALL | wx.ALIGN_CENTER_VERTICAL
        self.hboxL1.Add(self.button_num_filename, 0, border=3, flag=flags)
	self.hboxL1.AddSpacer(10)
        self.hboxL1.Add(self.textbox_num_filename, 0, border=3, flag=flags)

        self.hboxR1 = wx.BoxSizer(wx.HORIZONTAL)
        flags = wx.ALIGN_LEFT | wx.ALL | wx.ALIGN_CENTER_VERTICAL
        self.hboxR1.Add(self.button_bool_filename, 0, border=3, flag=flags)
	self.hboxR1.AddSpacer(10)
        self.hboxR1.Add(self.textbox_bool_filename, 0, border=3, flag=flags)

        self.hboxC1 = wx.BoxSizer(wx.HORIZONTAL)
        flags = wx.ALIGN_LEFT | wx.ALL | wx.ALIGN_CENTER_VERTICAL
        self.hboxC1.Add(self.button_coo_filename, 0, border=3, flag=flags)
	self.hboxC1.AddSpacer(10)
        self.hboxC1.Add(self.textbox_coo_filename, 0, border=3, flag=flags)

        self.hboxQ1 = wx.BoxSizer(wx.HORIZONTAL)
        flags = wx.ALIGN_LEFT | wx.ALL | wx.ALIGN_CENTER_VERTICAL
        self.hboxQ1.Add(self.button_queries_filename, 0, border=3, flag=flags)
	self.hboxQ1.AddSpacer(10)
        self.hboxQ1.Add(self.textbox_queries_filename, 0, border=3, flag=flags)

        self.hboxS1 = wx.BoxSizer(wx.HORIZONTAL)
        flags = wx.ALIGN_LEFT | wx.ALL | wx.ALIGN_CENTER_VERTICAL
        self.hboxS1.Add(self.button_settings_filename, 0, border=3, flag=flags)
	self.hboxS1.AddSpacer(10)
        self.hboxS1.Add(self.textbox_settings_filename, 0, border=3, flag=flags)

        self.vbox1.Add(self.hboxL1, 0, flag = wx.ALIGN_LEFT | wx.TOP)
        self.vbox1.Add(self.hboxR1, 0, flag = wx.ALIGN_LEFT | wx.TOP)
        self.vbox1.Add(self.hboxC1, 0, flag = wx.ALIGN_LEFT | wx.TOP)
        self.vbox1.Add(self.hboxQ1, 0, flag = wx.ALIGN_LEFT | wx.TOP)
        self.vbox1.Add(self.hboxS1, 0, flag = wx.ALIGN_LEFT | wx.TOP)
        
        self.panel1.SetSizer(self.vbox1)
        self.vbox1.Fit(self.toolFrame)

        ### SIZER FOR LOG
        self.vboxL = wx.BoxSizer(wx.VERTICAL)
        self.vboxL.Add(self.text_log, 1, wx.ALIGN_CENTER | wx.TOP | wx.EXPAND)
        self.panelLog.SetSizer(self.vboxL)
#        self.vboxL.Fit(self.toolFrame)

        ### SIZER FOR SETTINGS
        self.vboxS = wx.BoxSizer(wx.VERTICAL)
        self.vboxS.Add(self.text_setts, 1, wx.ALIGN_CENTER | wx.TOP | wx.EXPAND)
        self.panelSetts.SetSizer(self.vboxS)
#        self.vboxS.Fit(self.toolFrame)
        self.toolFrame.Show()

    def makeStatus(self, frame):
        ### status bar
        self.statusbar = frame.CreateStatusBar()
        self.statusbar.SetFieldsCount(3)
        self.statusbar.SetStatusWidths([300, 150, -1])

        self.progress_bar = wx.Gauge(self.statusbar, -1, style=wx.GA_HORIZONTAL|wx.GA_SMOOTH)
        rect = self.statusbar.GetFieldRect(1)
        self.progress_bar.SetPosition((rect.x+2, rect.y+2))
        self.progress_bar.SetSize((rect.width-2, rect.height-2))
        self.progress_bar.Hide()

    def makePopupMenu(self, frame):
        """
        Create and display a popup menu on right-click event
        """
        ID_NEWW = wx.NewId()
        ID_EXPAND = wx.NewId()
        
        menuRed = wx.Menu()
        m_neww = menuRed.Append(ID_NEWW, "&View in new window", "View redescription in new window.")
        m_expand = menuRed.Append(ID_EXPAND, "&Expand", "Expand redescription.")
        m_stop = menuRed.Append(wx.ID_STOP, "&Stop", "Stop expansion.")
        m_cut = menuRed.Append(wx.ID_CUT, "Cu&t", "Cut current redescription.")
        m_copy = menuRed.Append(wx.ID_COPY, "&Copy", "Copy current redescription.")
        m_paste = menuRed.Append(wx.ID_PASTE, "&Paste", "Paste current redescription.")

        frame.Bind(wx.EVT_MENU, self.OnNewW, m_neww)
        frame.Bind(wx.EVT_MENU, self.OnExpand, m_expand)
        frame.Bind(wx.EVT_MENU, self.OnStop, m_stop)
        frame.Bind(wx.EVT_MENU, self.OnCut, m_cut)
        frame.Bind(wx.EVT_MENU, self.OnCopy, m_copy)
        frame.Bind(wx.EVT_MENU, self.OnPaste, m_paste)
 
        # Popup the menu.  If an item is selected then its handler
        # will be called before PopupMenu returns.
        frame.PopupMenu(menuRed)
        menuRed.Destroy()

    def makeMenu(self, frame):
        ### menu bar
        menuBar = wx.MenuBar()
        menuFile = wx.Menu()
        menuRed = wx.Menu()
        menuWindow = wx.Menu()
        menuHelp = wx.Menu()
        submenuFile = wx.Menu()

        ID_IMPORT = wx.NewId()
        ID_IMPORT_DATA = wx.NewId()
        ID_IMPORT_COORD = wx.NewId()
        ID_IMPORT_QUERIES = wx.NewId()
        ID_EXPORT = wx.NewId()

        m_open = menuFile.Append(wx.ID_OPEN, "&Open\tCtrl+O", "Open a project.")
        m_save = menuFile.Append(wx.ID_SAVE, "&Save\tCtrl+S", "Save the current project.")
        m_saveas = menuFile.Append(wx.ID_SAVEAS, "Save &As...\tShift+Ctrl+S", "Save the current project as...")

        m_impData = submenuFile.Append(ID_IMPORT_DATA, "Import &Data", "Import data into the project.")
        m_impCoord = submenuFile.Append(ID_IMPORT_COORD, "Import C&oordinates", "Import coordinates into ths project.")
        m_impQueries = submenuFile.Append(ID_IMPORT_QUERIES, "Import Q&ueries", "Import queries into the project.")
        
        m_import = menuFile.AppendMenu(ID_IMPORT, "&Import", submenuFile)
        m_export = menuFile.Append(ID_EXPORT, "&Export Redescriptions\tShift+Ctrl+E", "Export redescriptions.")
        m_quit = menuFile.Append(wx.ID_EXIT, "&Quit", "Close window and quit program.")

        ID_NEWW = wx.NewId()
        ID_EXPAND = wx.NewId()

        m_neww = menuRed.Append(ID_NEWW, "&View in new window\tAlt+V", "View redescription in new window.")
        m_expand = menuRed.Append(ID_EXPAND, "&Expand\tCtrl+E", "Expand redescription.")
        m_stop = menuRed.Append(wx.ID_STOP, "&Stop", "Stop expansion.")
        m_cut = menuRed.Append(wx.ID_CUT, "Cu&t\tCtrl+X", "Cut current redescription.")
        m_copy = menuRed.Append(wx.ID_COPY, "&Copy\tCtrl+C", "Copy current redescription.")
        m_paste = menuRed.Append(wx.ID_PASTE, "&Paste\tCtrl+V", "Paste current redescription.")

        ID_HISTW = wx.NewId()
        ID_LOGW = wx.NewId()
        ID_SETTSW = wx.NewId()
        
        m_histw = menuWindow.AppendCheckItem(ID_HISTW, "&History", "Show History.")        
        m_logw = menuWindow.AppendCheckItem(ID_LOGW, "&Log", "Show log.")
        m_settsw = menuWindow.AppendCheckItem(ID_SETTSW, "&Settings", "Show settings.")

        m_help = menuHelp.Append(wx.ID_HELP, "C&ontent", "Access the instructions.")
        m_about = menuHelp.Append(wx.ID_ABOUT, "&About", "About...")

        frame.Bind(wx.EVT_MENU, self.OnOpen, m_open)
        frame.Bind(wx.EVT_MENU, self.OnSave, m_save)
        frame.Bind(wx.EVT_MENU, self.OnSaveAs, m_saveas)
        frame.Bind(wx.EVT_MENU, self.OnImportData, m_impData)
        frame.Bind(wx.EVT_MENU, self.OnImportCoord, m_impCoord)
        frame.Bind(wx.EVT_MENU, self.OnImportQueries, m_impQueries)
        frame.Bind(wx.EVT_MENU, self.OnExport, m_export)
        frame.Bind(wx.EVT_MENU, self.OnQuit, m_quit)
        frame.Bind(wx.EVT_MENU, self.OnNewW, m_neww)
        frame.Bind(wx.EVT_MENU, self.OnExpand, m_expand)
        frame.Bind(wx.EVT_MENU, self.OnStop, m_stop)
        frame.Bind(wx.EVT_MENU, self.OnCut, m_cut)
        frame.Bind(wx.EVT_MENU, self.OnCopy, m_copy)
        frame.Bind(wx.EVT_MENU, self.OnPaste, m_paste)
        frame.Bind(wx.EVT_MENU, self.OnLogW, m_logw)
        frame.Bind(wx.EVT_MENU, self.OnSettsW, m_settsw)
        frame.Bind(wx.EVT_MENU, self.OnHistW, m_histw)
        frame.Bind(wx.EVT_MENU, self.OnHelp, m_help)
        frame.Bind(wx.EVT_MENU, self.OnAbout, m_about)
        self.check_logw = m_logw
        self.check_settsw = m_settsw
        self.check_histw = m_histw

        menuBar.Append(menuFile, "&File")
        menuBar.Append(menuRed, "&Redescriptions")
        menuBar.Append(menuWindow, "&Window")
        menuBar.Append(menuHelp, "&Help")
        frame.SetMenuBar(menuBar)

    def OnOpen(self, event):
        pass
    def OnSave(self, event):
        pass
    def OnSaveAs(self, event):
        pass
    def OnImportData(self, event):
        pass
    def OnImportCoord(self, event):
        pass
    def OnImportQueries(self, event):
        pass
    def OnExport(self, event):
        pass
    def OnNewW(self, event):
        if self.selectedList != None:
            self.selectedMap = -1
            self.selectedList.viewData()

    # def OnExpand(self, event):
    #     pass
    # def OnStop(self, event):
    #     pass
    def OnCut(self, event):
        pass
    def OnCopy(self, event):
        pass
    def OnPaste(self, event):
        pass


    def OnHistW(self, event):
        if self.check_histw.IsChecked():
            self.lists["Hist"].grid.Show()
        else:
            self.lists["Hist"].grid.Hide()

    def OnLogW(self, event):
        if self.check_logw.IsChecked():
            self.panelLog.Show()
        else:
            self.panelLog.Hide()

    def OnSettsW(self, event):
        if self.check_settsw.IsChecked():
            self.panelSetts.Show()
        else:
            self.panelSetts.Hide()

    def OnHelp(self, event):
        self.helpFrame = wx.Frame(self.toolFrame, -1, self.titleHelp)
        html = wx.html.HtmlWindow(self.helpFrame)
        if "gtk2" in wx.PlatformInfo:
            html.SetStandardFonts()        
        wx.CallAfter(html.LoadPage, self.helpURL)
        self.helpFrame.Show()

    def OnAbout(self, event):
        pass
    
    def OnQuit(self, event):
        self.deleteAllViews()
        self.toolFrame.Destroy()
        exit()

    def doOpenFileB(self, event):
        wcd = 'All files|*|Numerical Data|*.densenum/*.datnum|Boolean Data|*.sparsebool/*.datbool'
        if self.bool_filename != '':
            file_name = os.path.basename(self.bool_filename)
            dir_name = ''
        else:
            file_name = ''
            dir_name = os.getcwd()
            
        open_dlg = wx.FileDialog(self.toolFrame, message='Choose a file', defaultDir=dir_name, defaultFile=file_name, 
			wildcard=wcd, style=wx.OPEN|wx.CHANGE_DIR)
        if open_dlg.ShowModal() == wx.ID_OK:
            path = open_dlg.GetPath()

            try:
                file = open(path, 'r')
		self.bool_filename = path
		self.textbox_bool_filename.SetValue(str(self.bool_filename))
                self.reloadData()
            except IOError, error:
                dlg = wx.MessageDialog(self.toolFrame, 'Error opening file\n' + str(error))
                dlg.ShowModal()
        open_dlg.Destroy()

    def doOpenFileN(self, event):
        wcd = 'All files|*|Numerical Data|*.densenum/*.datnum|Boolean Data|*.sparsebool/*.datbool'
        if self.num_filename != '':
            file_name = os.path.basename(self.num_filename)
            dir_name = ''
        else:
            file_name = ''
            dir_name = os.getcwd()
            
        open_dlg = wx.FileDialog(self.toolFrame, message='Choose a file', defaultDir=dir_name, defaultFile=file_name, 
			wildcard=wcd, style=wx.OPEN|wx.CHANGE_DIR)
        if open_dlg.ShowModal() == wx.ID_OK:
            path = open_dlg.GetPath()

            try:
                file = open(path, 'r')
		self.num_filename = path
		self.textbox_num_filename.SetValue(str(self.num_filename))
                self.reloadData()
            except IOError, error:
                dlg = wx.MessageDialog(self.toolFrame, 'Error opening file\n' + str(error))
                dlg.ShowModal()
        open_dlg.Destroy()


    def doOpenFileC(self, event):
        wcd = 'All files|*'
        if self.coo_filename != '':
            file_name = os.path.basename(self.coo_filename)
            dir_name = ''
        else:
            file_name = ''
            dir_name = os.getcwd()
            
        open_dlg = wx.FileDialog(self.toolFrame, message='Choose a file', defaultDir=dir_name, defaultFile=file_name, 
			wildcard=wcd, style=wx.OPEN|wx.CHANGE_DIR)
        if open_dlg.ShowModal() == wx.ID_OK:
            path = open_dlg.GetPath()

            try:
                file = open(path, 'r')
		self.coo_filename = path
		self.textbox_coo_filename.SetValue(str(self.coo_filename))
                self.reloadCoordinates()
            except IOError, error:
                dlg = wx.MessageDialog(self.toolFrame, 'Error opening file\n' + str(error))
                dlg.ShowModal()
                self.coo_filename = ''
		self.textbox_coo_filename.SetValue('')

        open_dlg.Destroy()


    def doOpenFileQ(self, event):
        wcd = 'All files|*|Queries files|*.queries'
        if self.queries_filename != '':
            file_name = os.path.basename(self.queries_filename)
            dir_name = ''
        else:
            file_name = ''
            dir_name = os.getcwd()
            
        open_dlg = wx.FileDialog(self.toolFrame, message='Choose a file', defaultDir=dir_name, defaultFile=file_name, 
			wildcard=wcd, style=wx.OPEN|wx.CHANGE_DIR)
        if open_dlg.ShowModal() == wx.ID_OK:
            path = open_dlg.GetPath()

            try:
                file = open(path, 'r')
		self.queries_filename = path
		self.textbox_queries_filename.SetValue(str(self.queries_filename))
                self.reloadReds()
            except IOError, error:
                dlg = wx.MessageDialog(self.toolFrame, 'Error opening file\n' + str(error))
                dlg.ShowModal()
		self.queries_filename = ''
		self.textbox_queries_filename.SetValue('')

        open_dlg.Destroy()

    def doOpenFileS(self, event):
        wcd = 'All files|*|Settings files|*.conf'
        if self.settings_filename != '':
            file_name = os.path.basename(self.settings_filename)
            dir_name = ''
        else:
            file_name = ''
            dir_name = os.getcwd()
            
        open_dlg = wx.FileDialog(self.toolFrame, message='Choose a file', defaultDir=dir_name, defaultFile=file_name, 
			wildcard=wcd, style=wx.OPEN|wx.CHANGE_DIR)
        if open_dlg.ShowModal() == wx.ID_OK:
            path = open_dlg.GetPath()
            try:
                file = open(path, 'r')
		self.settings_filename = path
		self.textbox_settings_filename.SetValue(str(self.settings_filename))
                self.text_setts.LoadFile(path)

            except IOError, error:
                dlg = wx.MessageDialog(self.toolFrame, 'Error opening file\n' + str(error))
                dlg.ShowModal()
                self.settings_filename = ''
                self.textbox_settings_filename.SetValue('')
                self.text_setts.Clear(path)
        open_dlg.Destroy()

    def reloadData(self):
        if self.bool_filename != '' and self.num_filename != '':
            try:
                self.data = Data([self.bool_filename, self.num_filename])
                self.details = {'names': self.data.getNames([self.bool_filename, self.num_filename])}
                self.reloadVars()
            except:
                self.data = None
                self.details = None
                self.reloadVars()
                
    def reloadCoordinates(self):
        ### WARNING COORDINATES ARE INVERTED!!!
        if self.coo_filename != '':
            self.deleteAllViews()
            self.coord = np.loadtxt(self.coo_filename, unpack=True, usecols=(1,0))
            self.coord_extrema = [[min(self.coord[0]), max(self.coord[0])],[min(self.coord[1]), max(self.coord[1])]]


    def reloadSettings(self):
        self.setts = Settings('mine', ['gui', self.settings_filename])
        self.setts.getParams()
        self.logger = Log(self.setts.param['verbosity'], self.toolFrame, Message.sendMessage)
        Data.logger = self.logger

    def reloadVars(self):
        ## Initialize variable lists data
        for side in [0,1]:
            if self.data != None and self.details != None:
                fieldsVar = []
                fieldsVar.extend(self.fieldsVar)
                for tyid in set([r.type_id for r in self.data.cols[side]]):
                    fieldsVar.extend(self.fieldsVarTypes[tyid])
                self.lists[side].updateData(self.data.cols[side], fieldsVar, self.details)
            else:
                fieldsVar = []
                fieldsVar.extend(self.fieldsVar)
                self.lists[side].updateData([], fieldsVar, self.details)
            
    def reloadReds(self):
        ## Initialize red lists data
        self.lists["Reds"].updateData(self.populateReds(), self.fieldsRed, self.details)
        self.lists["Exp"].updateData([], self.fieldsRed, self.details)
        self.lists["Hist"].updateData([], self.fieldsRed, self.details)
#        self.getSelectedMapView().setCurrentRed(redsTmp[0])
#        self.getSelectedMapView().updateRed()
            
    def populateReds(self):
        reds = []
        if self.queries_filename != '' and self.data != None:
            reds_fp = open(self.queries_filename)
            for line in reds_fp:
                parts = line.strip().split('\t')
                if len(parts) > 1:
                    queryL = Query.parse(parts[0])
                    queryR = Query.parse(parts[1])
                    red = Redescription.fromQueriesPair([queryL, queryR], self.data) 
                    if red != None:
                        reds.append(red)
            return reds

if __name__ == '__main__':
    app = wx.App()
    app.frame = Siren()
    app.MainLoop()
