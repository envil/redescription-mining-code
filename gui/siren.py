import os
import pprint
import random
import wx, wx.grid, wx.html, wx.richtext
from wx.lib import wordwrap
#from wx.prop import basetableworker
import threading as th
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
from DataWrapper import DataWrapper
from ICList import ICList

def filterRedsToOne(reds_list, selected_id, compare_ids, redundant_func, thres):
    redundant_ids = []
    for compare_id in compare_ids:
        if redundant_func(reds_list[selected_id], reds_list[compare_id], thres):
            redundant_ids.append(compare_id)
    return redundant_ids

def isRedundantArea(redA, redB, thres= 0.5):
    redundant = False
    for side in [0,1]:
        # areaA = len(redA.supp(side))*len(redA.invColsSide(side))
        # areaB = len(redB.supp(side))*len(redB.invColsSide(side))
        areaI = len(redB.supp(side) & redA.supp(side))* len(redB.invColsSide(side) & redA.invColsSide(side))
        areaU = len(redB.supp(side) | redA.supp(side))* len(redB.invColsSide(side) | redA.invColsSide(side))
        if areaU > 0 and  areaI / areaU > thres:
            redundant = True
    return redundant
    

# Thread class that executes processing
class ExpanderThread(th.Thread):
    """Expander Thread Class."""
    def __init__(self, data, setts, red, logger):
        """Init Expander Thread Class."""
        th.Thread.__init__(self)
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

class MinerThread(th.Thread):
    """Miner Thread Class."""
    def __init__(self, data, setts, logger):
        """Init Miner Thread Class."""
        th.Thread.__init__(self)
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

class CustViewer(wx.grid.PyGridCellRenderer):

    BACKGROUND_SELECTED = wx.Colour(100,100,100)
    TEXT_SELECTED = wx.Colour(100,100,100)
    BACKGROUND = wx.Colour(100,100,100)
    TEXT = wx.Colour(100,100,100)
    BACKGROUND_GREY = wx.Colour(240,255,240)
    TEXT_GREY = wx.Colour(131,139,131)

    """Base class for editors"""

    ### Customisation points
    def Draw(self, grid, attr, dc, rect, row, col, isSelected):
        """Customisation Point: Draw the data from grid in the rectangle with attributes using the dc"""

        dc.SetClippingRegion( rect.x, rect.y, rect.width, rect.height )
        if row in grid.GetSelectedRows():
            dc.SetTextForeground( self.TEXT_SELECTED )
            dc.SetTextBackground( self.BACKGROUND_SELECTED)
            dc.SetBrush( wx.Brush( self.BACKGROUND_SELECTED) )
        elif grid.GetTable().visibleStatus(row) == 0:
            dc.SetTextForeground( self.TEXT_GREY )
            dc.SetTextBackground( self.BACKGROUND_GREY)
            dc.SetBrush( wx.Brush( self.BACKGROUND_GREY) )
        else:
            dc.SetBrush( wx.Brush( self.BACKGROUND, wx.SOLID) )
            dc.SetTextForeground( self.TEXT )
        try:
            dc.SetPen(wx.TRANSPARENT_PEN)
            dc.DrawRectangle( rect.x, rect.y, rect.width, rect.height )
            value = grid.GetCellValue( row, col )
            dc.SetFont( wx.NORMAL_FONT )
            dc.DrawText( value, rect.x+2,rect.y+2 )
        finally:
            dc.SetTextForeground( self.TEXT)
            dc.SetTextBackground( self.BACKGROUND)
            dc.SetPen( wx.NullPen )
            dc.SetBrush( wx.NullBrush )
            dc.DestroyClippingRegion( )

    def GetBestSize(self, grid, attr, dc, row, col):
        """Customisation Point: Determine the appropriate (best) size for the control, return as wxSize
        Note: You _must_ return a wxSize object.  Returning a two-value-tuple
        won't raise an error, but the value won't be respected by wxPython.
        """         
        x,y = dc.GetTextExtent( "%s" % grid.GetCellValue( row, col ) )
        # note that the two-tuple returned by GetTextExtent won't work,
        # need to give a wxSize object back!
        return wx.Size( min(x, 10), min(y, 10))


class CustomGridTable(wx.grid.PyGridTableBase):

    def __init__(self, parent, tabId, frame):
        wx.grid.PyGridTableBase.__init__(self)
        self.parent = parent
        self.tabId = tabId
        self.fields = []
        self.data = []
        self.sortids = []
        self.details = {}
        self.bShowHidden = True
        self.sortP = (None, False)
        self.currentRows = len(self.visiblesAll())
        self.currentColumns = len(self.fields)

        #### GRID
        self.grid = wx.grid.Grid(frame)
        self.grid.SetTable(self)
        self.grid.EnableEditing(False)
        self.grid.AutoSizeColumns(True)

        self.grid.RegisterDataType(wx.grid.GRID_VALUE_STRING,
                                   CustViewer(),
                                   wx.grid.GridCellAutoWrapStringEditor())

        self.grid.RegisterDataType(wx.grid.GRID_VALUE_BOOL,
                              wx.grid.GridCellBoolRenderer(),
                              wx.grid.GridCellBoolEditor()) 

        # attr = wx.grid.GridCellAttr()
        # attr.SetEditor(wx.grid.GridCellBoolEditor())
        # attr.SetRenderer(wx.grid.GridCellBoolRenderer())
        # self.grid.SetColAttr(0,attr)

        self.grid.Bind(wx.grid.EVT_GRID_LABEL_LEFT_CLICK, self.sortData)
        self.grid.Bind(wx.grid.EVT_GRID_CELL_LEFT_DCLICK, self.OnViewData)
        self.grid.Bind(wx.grid.EVT_GRID_CELL_RIGHT_CLICK, self.OnRightClick)
        self.grid.Bind(wx.grid.EVT_GRID_CELL_LEFT_CLICK, self.OnMouse)
        
    # def showPopupMenu(self, event):
    #     self.table.highlightRow(event.GetRow())
    #     parent.currentList = self

    def GetNumberRows(self):
        """Return the number of rows in the grid"""
        return len(self.visiblesAll())

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
        return self.GetValue(row, col) == None

    def GetTypeName(self, row, col):
        """Return the name of the data type of the value in the cell"""
        if (col == 0):
            return wx.grid.GRID_VALUE_BOOL
        else:
            return wx.grid.GRID_VALUE_STRING
        # if row < len(self.sortids) and col < len(self.fields):
        #     x = self.sortids[row]
        #     methode = eval(self.fields[col][0])
        #     return type(methode(self.details))
        # else:
        #     return None

    def GetValue(self, row, col):
        """Return the value of a cell"""
        if row < len(self.visiblesAll()) and col < len(self.fields):
            x = self.visiblesAll()[row]
            methode = eval(self.fields[col][0])
            if callable(methode):
                return "%s" % methode(self.details)
            else:
                return methode
        else:
            return None

    def GetRowData(self, row):
        """Return the data of a row"""
        if row < len(self.visiblesAll()):
            return self.data[self.visibleOrgId(row)]
        else:
            return None
                                  
    def SetValue(self, row, col, value):
        pass

    def resetData(self, data, fieldsRed=[], details=[], srids=None):
        if details != []:
            self.details = details
        if fieldsRed != []:
            self.fields = fieldsRed
        self.data = data
        if srids != None:
            self.sortids = srids
        else:
            self.sortids = [[idi, 1] for idi in range(len(self.data))]
        self.updateSort()
        self.ResetView()
        self.GetView().AutoSize()

    def appendRow(self, rowD):
        if len(self.sortids) == 0 or self.data[-1] != rowD:
            self.sortids.append([len(self.data), 1])
            self.data.append(rowD)
            self.updateSort()
            self.ResetView()

    def extendData(self, rowsD):
        self.sortids.extend([[len(self.data)+ i, 1] for i in range(len(rowsD))])
        self.data.extend(rowsD)
        self.updateSort()
        self.ResetView()

    def setHidden(self, row):
        self.sortids[self.visibleSortId(row)][1] = 0
        self.ResetView()
    def setHiddens(self, rows):
        sids = [self.visiblesAll()[row][1] for row in rows]
        for sid in sids:
            self.sortids[sid][1] = 0
        self.ResetView()

    def flipHidden(self, row):
        self.sortids[self.visibleSortId(row)][1] = 1- self.sortids[self.visibleSortId(row)][1]
        self.ResetView()
    def flipHiddens(self, rows):
        sids = [self.visiblesAll()[row][1] for row in rows]
        for sid in sids:
            self.sortids[sid][1] = 1-self.sortids[sid][1]
        self.ResetView()

    def toggleHide(self):
        self.bShowHidden = not self.bShowHidden
        self.ResetView()

    def orgToSortIds(self, org_ids):
        return [self.visiblesIds().index(org_id) for org_id in org_ids] 
        
    def visibleStatus(self, row):
        return self.visiblesAll()[row][2]

    def visibleOrgId(self, row):
        return self.visiblesAll()[row][0]

    def visibleSortId(self, row):
        return self.visiblesAll()[row][1]

    def visiblesAll(self):
        return [(idi[0], si, idi[1])  for si, idi in enumerate(self.sortids) if (self.bShowHidden or idi[1])]

    def visiblesIds(self):
        return [idi[0]  for idi in self.sortids if (self.bShowHidden or idi[1])]

    def OnMouse(self,event):
        if event.GetRow() < len(self.visiblesAll()):
            if event.Col == 0:
                self.flipHidden(event.GetRow())
            else:
                self.setSelectedRow(event.GetRow())
       
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
        self.currentRows = len(self.visiblesAll())
        self.currentColumns = len(self.fields)

        if self.getSelectedRowId() != None and not self.grid.IsVisible(self.getSelectedRowId(), 0):
            self.grid.MakeCellVisible(self.getSelectedRowId(), 0)

    def deleteHidden(self):
        pass

    def getSelectedRowData(self):
        if self.getSelectedRowId() != None:
            return self.GetRowData(self.getSelectedRowId())
        return
    
    def getSelectedRowId(self):
        if len(self.GetView().GetSelectedRows()) > 0:
            return self.GetView().GetSelectedRows()[0]
        else:
            return None

    def setSelectedRow(self,row):
        self.GetView().SetGridCursor(row,0)
        self.GetView().SelectRow(row)

    def sortData(self, event):
        colS = event.GetCol()
        if colS == -1:
            pass
#            self.setHiddens(range(10))
        else:
            old = self.sortP[0]
            if self.sortP[0] == colS:
                self.sortP = (self.sortP[0], not self.sortP[1])
            else:
                self.sortP = (colS, True)
            self.updateSort()
            self.ResetView()
        
    def updateSort(self):
        selected_row = self.getSelectedRowId()
        selected_id = None
        if selected_row != None and selected_row < len(self.sortids) :
            selected_id = self.visibleOrgId(selected_row)

        if self.sortP[0] != None:
            self.sortids.sort(key= lambda x: eval(self.fields[self.sortP[0]][0])(self.details), reverse=self.sortP[1])
        if selected_id != None and selected_id in self.visiblesIds():
            self.setSelectedRow(self.visiblesIds().index(selected_id))
            
    def OnRightClick(self, event):
        if event.GetRow() < len(self.data):
            self.setSelectedRow(event.GetRow())
            self.parent.selectedList = self
            self.parent.makePopupMenu(self.parent.toolFrame)

    def OnViewData(self, event):
        if event.GetRow() < len(self.data):
            self.setSelectedRow(event.GetRow())
            self.viewData()

    def duplicate(self):
        red = self.getSelectedRowData().copy()
        self.sortids.insert(self.visibleSortId(self.getSelectedRowId()), [len(self.data), 1])
        self.data.append(red)
        self.ResetView()

    def filterToOne(self):
        if self.getSelectedRowId() < len(self.visiblesIds()): 
            compare_ids = self.visiblesIds()[self.getSelectedRowId():]
            selected_id = compare_ids.pop(0)
            redundant_ids = filterRedsToOne(self.data, selected_id, compare_ids, isRedundantArea, 0.5)
            self.setHiddens(self.orgToSortIds(redundant_ids))

class RedGridTable(CustomGridTable):
    def viewData(self):
        mapV = self.parent.getSelectedMapView()
        mapV.setCurrentRed(self.getSelectedRowData(), self.tabId, self.visibleOrgId(self.getSelectedRowId()))
        mapV.updateRed(self.tabId != "Hist")

    def deleteHidden(self):
        new_data = [self.data[i] for i in self.sortids if i[1]]
        self.resetData(new_data)

    def updateRow(self, rowId, red):
        if rowId < len(self.data):
            self.data[rowId] = red
            self.ResetView()

class VarGridTable(CustomGridTable):     
    def viewData(self):
        mapV = self.parent.getSelectedMapView()
        datVar = self.getSelectedRowData()
        if datVar.side == 1:
            mapV.MapredMapQL.ChangeValue("")
            mapV.MapredMapQR.ChangeValue(datVar.getItem().dispU(False, self.parent.details['names'][1]))
        else:
            mapV.MapredMapQL.ChangeValue(datVar.getItem().dispU(False, self.parent.details['names'][0]))
            mapV.MapredMapQR.ChangeValue("")
#            mapV.MapredMapInfo.ChangeValue("")
        mapV.setMapredInfo(None)
        mapV.updateRed(False)


    def setHidden(self, row):
        self.data[self.sortids[self.visibleSortId(row)][0]].setUnusable()
        self.sortids[self.visibleSortId(row)][1] = 0
        self.ResetView()
    def setHiddens(self, rows):
        sids = [self.visiblesAll()[row] for row in rows]
        for sid in sids:
            self.data[sid[0]].setUnusable()
            self.sortids[sid[1]][1] = 0
        self.ResetView()

    def flipHidden(self, row):
        self.data[self.sortids[self.visibleSortId(row)][0]].flipUsable()
        self.sortids[self.visibleSortId(row)][1] = 1- self.sortids[self.visibleSortId(row)][1]
        self.ResetView()
    def flipHiddens(self, rows):
        sids = [self.visiblesAll()[row] for row in rows]
        for sid in sids:
            self.data[sid[0]].flipUsable()
            self.sortids[sid[1]][1] = 1-self.sortids[sid][1]
        self.ResetView()

    def updateRow(self, rowId, red):
        pass


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
        self.source_data = None
        self.source_id = None
        self.vid = vid
        self.lines = []
        self.coord_proj = None
        self.mapFrame = wx.Frame(None, -1, self.parent.titleMap)
        self.mapFrame.Bind(wx.EVT_CLOSE, self.OnQuit)
        self.mapFrame.Bind(wx.EVT_ENTER_WINDOW, self.OnFocus)
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
        self.button_stop = wx.Button(self.mapFrame, size=(80,-1), label="Stop")
        self.button_expand.Bind(wx.EVT_BUTTON, self.parent.OnExpand)
        self.button_stop.Bind(wx.EVT_BUTTON, self.parent.OnStop)
        self.MapredMapQL.Bind(wx.EVT_TEXT_ENTER, self.OnEditRed)
        self.MapredMapQR.Bind(wx.EVT_TEXT_ENTER, self.OnEditRed)

        self.MapfigMap = plt.figure()
        self.Mapcurr_mapi = 0
        self.MapcanvasMap = FigCanvas(self.mapFrame, -1, self.MapfigMap)
        
        self.MaptoolbarMap = NavigationToolbar(self.MapcanvasMap)
 
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

    def setCurrentRed(self, red, source_data=None, source_id = None):
        self.source_data=source_data
        self.source_id =source_id
        self.MapredMapQL.ChangeValue(red.queries[0].dispU(self.parent.details['names'][0]))
        self.MapredMapQR.ChangeValue(red.queries[1].dispU(self.parent.details['names'][1]))
#        self.MapredMapInfo.ChangeValue(red.dispLParts())
        self.setMapredInfo(red)
        
    def updateRed(self, addHist=True):
        red = self.redraw_map()
        if red != None and addHist:
            self.parent.lists["Hist"].appendRow(red)
            if self.source_data != None and self.parent.lists.has_key(self.source_data) and self.source_id != None:
                self.parent.lists[self.source_data].updateRow(self.source_id, red)
        return red
        
    def parseRed(self):
        queryL = Query.parseAny(self.MapredMapQL.GetValue().strip(), self.parent.details['names'][0])
        queryR = Query.parseAny(self.MapredMapQR.GetValue().strip(), self.parent.details['names'][1])
        if queryL != None and queryR != None: 
            return Redescription.fromQueriesPair([queryL, queryR], self.parent.dw.data) 
        
    def draw_map(self):
        """ Draws the map
        """
        self.MapfigMap.clear()
        if self.parent.coord_extrema != None and self.parent.dw.coord != None:            

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

            m.drawcoastlines(color=MapView.LINES_COLOR)
            m.drawcountries(color=MapView.LINES_COLOR)
            m.drawmapboundary(fill_color=MapView.WATER_COLOR) 
            m.fillcontinents(color=MapView.GROUND_COLOR, lake_color=MapView.WATER_COLOR) #'#EEFFFF')
            #m.etopo()
            self.coord_proj = m(self.parent.dw.coord[0], self.parent.dw.coord[1])
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

        if self.parent.coord_extrema != None and self.parent.dw.coord != None:
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
                    # for id in part:
                    #     self.lines.extend(plt.fill(self.corners[id][0], self.corners[id][1], fc=colors[i], ec=colors[i], alpha=0.5))
                    lip = list(part)
                    self.points_ids.extend(lip)
                    ids = np.array(lip)
                    self.lines.extend(m.plot(self.coord_proj[0][ids],self.coord_proj[1][ids], mfc=colors[i], mec=colors[i], marker=markers[i], markersize=sizes[i], linestyle='None', alpha=MapView.DOT_ALPHA, picker=3))
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
    fieldsRed = [('x[2]', ''), ('self.data[x[0]].getQueryLU', 'Query LHS'), ('self.data[x[0]].getQueryRU', 'Query RHS'), ('self.data[x[0]].getAcc', 'Acc'), ('self.data[x[0]].getPVal', 'p-Value'), ('self.data[x[0]].getSupp', 'Support')]
    fieldsVar = [('self.data[x[0]].getUsable', ''), ('self.data[x[0]].getId', 'Id'), ('self.data[x[0]].getName', 'Name'), ('self.data[x[0]].getType', 'Type')]
    fieldsVarTypes = {1: [('self.data[x[0]].getDensity', 'Density')], 2:[('self.data[x[0]].getCategories', 'Categories')], 3:[('self.data[x[0]].getMin', 'Min'), ('self.data[x[0]].getMax', 'Max')]}

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
 
        self.coord_extrema = None
        self.details = None
        self.worker = None

        self.create_tool_panel()

        # #### COMMENT OUT TO LOAD DBLP ON STARTUP
        # tmp_num_filename='./dblp/coauthor_picked.datnum'
        # tmp_bool_filename='./dblp/conference_picked.datnum'
        # tmp_coo_filename='./dblp/coordinates_rand.names'
        # tmp_queries_filename='./dblp/dblp_picked_real.queries'
        # tmp_settings_filename='./dblp/dblp_picked_real.conf'


        # # # #### COMMENT OUT TO LOAD RAJAPAJA ON STARTUP
        tmp_num_filename='./rajapaja/worldclim_tp.densenum'
        tmp_bool_filename='./rajapaja/mammals.datbool'
        tmp_coo_filename='./rajapaja/coordinates.names'
        tmp_queries_filename='./rajapaja/rajapaja.queries'
        tmp_settings_filename='./rajapaja/rajapaja.conf'


        # #### COMMENT OUT TO LOAD US ON STARTUP
        # tmp_num_filename='./us/us_politics_funds_cont.densenum'
        # tmp_bool_filename='./us/us_socio_eco_cont.densenum'
        # tmp_coo_filename='./us/us_coordinates_cont.names'
        # tmp_queries_filename='./us/us.queries'
        # tmp_settings_filename='./us/us.conf'

        # #### COMMENT OUT TO LOAD SOMETHING ON STARTUP
        # (Almost) all of the above should stay in dw
        self.dw = DataWrapper(tmp_coo_filename, [tmp_bool_filename, tmp_num_filename], tmp_queries_filename, tmp_settings_filename)

        ### TODO DW
        self.resetLogger()
        self.details = {'names': self.dw.names}
        self.reloadVars()
        self.resetCoordinates()
        self.reloadReds()
        self.text_setts.LoadFile(self.dw.settings_filename)
	
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
            self.worker = ExpanderThread(self.dw.data, self.dw.minesettings, red, self.logger)
        else:
            self.worker = MinerThread(self.dw.data, self.dw.minesettings, self.logger)

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
        ID_FILTER = wx.NewId()
        ID_DUPLICATE = wx.NewId()
        ID_TOGHI = wx.NewId()
        ID_EXPAND = wx.NewId()
        
        menuRed = wx.Menu()
        m_neww = menuRed.Append(ID_NEWW, "&View in new window", "View redescription in new window.")
        if not self.selectedList.tabId in [0,1]:
            m_filter = menuRed.Append(ID_FILTER, "&Filter redundant", "Filter redundant.")
            m_duplicate = menuRed.Append(ID_DUPLICATE, "&Duplicate", "Duplicate redescription.")
            frame.Bind(wx.EVT_MENU, self.OnFilterToOne, m_filter)
            frame.Bind(wx.EVT_MENU, self.OnDuplicate, m_duplicate)

        m_toghi = menuRed.Append(ID_TOGHI, "&Hide/show", "Hide/show.")
        m_expand = menuRed.Append(ID_EXPAND, "&Expand", "Expand redescription.")
        m_stop = menuRed.Append(wx.ID_STOP, "&Stop", "Stop expansion.")
        m_cut = menuRed.Append(wx.ID_CUT, "Cu&t", "Cut current redescription.")
        m_copy = menuRed.Append(wx.ID_COPY, "&Copy", "Copy current redescription.")
        m_paste = menuRed.Append(wx.ID_PASTE, "&Paste", "Paste current redescription.")

        frame.Bind(wx.EVT_MENU, self.OnNewW, m_neww)
        frame.Bind(wx.EVT_MENU, self.OnToggleHide, m_toghi)
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
        ID_FILTER = wx.NewId()
        ID_EXPAND = wx.NewId()
        ID_HIDE = wx.NewId()

        m_neww = menuRed.Append(ID_NEWW, "&View in new window\tAlt+V", "View redescription in new window.")
        m_filter = menuRed.Append(ID_FILTER, "&Filter redundant", "Filter redundant.")
        m_expand = menuRed.Append(ID_EXPAND, "&Expand\tCtrl+E", "Expand redescription.")
        m_stop = menuRed.Append(wx.ID_STOP, "&Stop", "Stop expansion.")
        m_cut = menuRed.Append(wx.ID_CUT, "Cu&t\tCtrl+X", "Cut current redescription.")
        m_copy = menuRed.Append(wx.ID_COPY, "&Copy\tCtrl+C", "Copy current redescription.")
        m_paste = menuRed.Append(wx.ID_PASTE, "&Paste\tCtrl+V", "Paste current redescription.")
        m_hide = menuRed.AppendCheckItem(ID_HIDE, "&Show hidden", "Show hidden redescriptions.")
        m_delete = menuRed.Append(wx.ID_DELETE, "&Delete", "Delete hidden redescriptions.")
        
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
        frame.Bind(wx.EVT_MENU, self.OnFilterToOne, m_filter)
        frame.Bind(wx.EVT_MENU, self.OnExpand, m_expand)
        frame.Bind(wx.EVT_MENU, self.OnStop, m_stop)
        frame.Bind(wx.EVT_MENU, self.OnCut, m_cut)
        frame.Bind(wx.EVT_MENU, self.OnCopy, m_copy)
        frame.Bind(wx.EVT_MENU, self.OnPaste, m_paste)
        # frame.Bind(wx.EVT_MENU, self.OnToggleHide, m_hide) ## Tab by tab, not here...
        # frame.Bind(wx.EVT_MENU, self.OnDelete, m_delete)
        frame.Bind(wx.EVT_MENU, self.OnLogW, m_logw)
        frame.Bind(wx.EVT_MENU, self.OnSettsW, m_settsw)
        frame.Bind(wx.EVT_MENU, self.OnHistW, m_histw)
        frame.Bind(wx.EVT_MENU, self.OnHelp, m_help)
        frame.Bind(wx.EVT_MENU, self.OnAbout, m_about)
#        self.check_hide = m_hide
        self.check_logw = m_logw
        self.check_settsw = m_settsw
        self.check_histw = m_histw

        menuBar.Append(menuFile, "&File")
        menuBar.Append(menuRed, "&Redescriptions")
        menuBar.Append(menuWindow, "&Window")
        menuBar.Append(menuHelp, "&Help")
        frame.SetMenuBar(menuBar)

    def OnOpen(self, event):
        wcd = 'All files|*|Siren packages (*.siren)|*.siren'

        if self.dw.package_filename is not None:
            dir_name = os.path.dirname(self.dw.package_filename)
        else:
            dir_name = os.path.expanduser('~/')
        path = dir_name            
        open_dlg = wx.FileDialog(self.toolFrame, message='Choose a file', defaultDir=dir_name,  
			wildcard=wcd, style=wx.OPEN|wx.CHANGE_DIR)
        if open_dlg.ShowModal() == wx.ID_OK:
            path = open_dlg.GetPath()
            try:
                self.dw.openPackage(path)
            except IOError as error:
                dlg = wx.MessageDialog(self.toolFrame, 'Error opening file '+str(path)+':\n' + str(error))
                dlg.ShowModal()
        open_dlg.Destroy()
        # DEBUGGING
        wx.MessageDialog(self.toolFrame, 'Opened package from '+path).ShowModal()

    def OnSave(self, event):
        if not (self.dw.isFromPackage and self.dw.package_filename is not None):
            wx.MessageDialog(self.toolFrame, 'Cannot save data that is not from a package\nUse Save As... instead').showModal()
            return
        try:
            self.dw.savePackage()
        except IOError as error:
            wx.MessageDialog(self.toolFrame, 'Cannot save package to'+str(self.dw.package_filename)+':\n'+str(error)).ShowModal()
            
    def OnSaveAs(self, event):
        if self.dw.package_filename is not None:
            dir_name = os.path.dirname(self.dw.package_filename)
        else:
            dir_name = os.path.expanduser('~/')

        save_dlg = wx.FileDialog(self.toolFrame, message="Save as", defaultDir=dir_name,
                                 style=wx.SAVE|wx.CHANGE_DIR)
        if save_dlg.ShowModal() == wx.ID_OK:
            path = save_dlg.GetPath()
            try:
                self.dw.savePackageToFile(path)
            except IOError as error:
                wx.MessageDialog(self.toolFrame, 'Cannot save to file '+path+':\n'+str(error)).ShowModal()
        save_dlg.Destroy()
                
    def OnImportData(self, event):
        if self.dw.reds is not None or self.dw.coord is not None:
            sure_dlg = wx.MessageDialog(self.toolFrame, 'Importing new data erases old redescriptions and coordinates.\nDo you want to continue?', caption="Warning!", style=wx.OK|wx.CANCEL)
            if sure_dlg.ShowModal() != wx.ID_OK:
                return
            sure_dlg.Destroy()
            
        wcd = 'All files|*|Numerical Data (*.densenum / *.datnum)|*.densenum/*.datnum|Boolean Data (*.sparsebool / *.datbool)|*.sparsebool/*.datbool'
        dir_name = os.path.expanduser('~/')
            
        open_left_dlg = wx.FileDialog(self.toolFrame, message='Choose LHS data file', defaultDir=dir_name,  
			wildcard=wcd, style=wx.OPEN|wx.CHANGE_DIR)
        if open_left_dlg.ShowModal() == wx.ID_OK:
            left_path = open_left_dlg.GetPath()
            open_right_dlg = wx.FileDialog(self.toolFrame, message='Choose RHS data file', defaultDir=os.path.dirname(left_path),  
			wildcard=wcd, style=wx.OPEN|wx.CHANGE_DIR)
            if open_right_dlg.ShowModal() == wx.ID_OK:
                right_path = open_right_dlg.GetPath()

                try:
                    self.dw.importDataFromFiles([left_path, right_path])
                    self.dw.updateNames()
                    self.details = {'names': self.dw.names}
                    self.reloadVars()
                    self.reloadReds()
                except IOError, error:
                    dlg = wx.MessageDialog(self.toolFrame, 'Error opening files '+str(left_path)
                                           +' and '+str(right_path)+':\n' + str(error))
                    dlg.ShowModal()
            open_right_dlg.Destroy()
        open_left_dlg.Destroy()
        # Delete reds and coords
        self.dw.reds = None
        self.dw.queries_filename = None
        self.dw.rshowids = None
        self.dw.coord = None
        self.dw.coo_filename = None
 
    def OnImportCoord(self, event):
        dir_name = os.path.expanduser('~/')
        open_dlg = wx.FileDialog(self.toolFrame, message='Choose file', defaultDir = dir_name,
                                 style = wx.OPEN|wx.CHANGE_DIR)
        if open_dlg.ShowModal() == wx.ID_OK:
            path = open_dlg.GetPath()
            try:
                self.dw.importCoordFromFile(path)
            except IOError as error:
                wx.MessageDialog(self.toolFrame, 'Error opening file '+str(path)+':\n'+str(error)).ShowModal()
        open_dlg.Destroy()
        self.resetCoordinates()
        
    def OnImportQueries(self, event):
        wcd = 'All files|*|Query files (*.queries)|*.queries|'
        dir_name = os.path.expanduser('~/')

        open_dlg = wx.FileDialog(self.toolFrame, message='Choose file', defaultDir = dir_name,
                                 style = wx.OPEN|wx.CHANGE_DIR)
        if open_dlg.ShowModal() == wx.ID_OK:
            path = open_dlg.GetPath()
            try:
                self.dw.importQueriesFromFile(path)
            except IOError as error:
                wx.MessageDialog(self.toolFrame, 'Error opening file '+str(path)+':\n'+str(error)).ShowModal()
        open_dlg.Destroy()
        
    def OnExport(self, event):
        if self.dw.reds is None:
            wx.MessageDialog(self.toolFrame, 'Cannot export redescriptions: no redescriptions loaded').ShowModal()
            return
        
        if self.dw.queries_filename is not None:
            dir_name = os.path.dirname(self.dw.queries_filename)
        else:
            dir_name = os.path.expanduser('~/')

        save_dlg = wx.FileDialog(self.toolFrame, message='Export redescriptions to:', defaultDir = dir_name, style = wx.SAVE|wx.CHANGE_DIR)
        if save_dlg.ShowModal() == wx.ID_OK:
            path = save_dlg.GetPath()
            try:
                self.dw.exportQueries(path, named=True)
                self.dw.exportQueriesLatex(path+".tex", named=True)
            except IOError as error:
                wx.MessageDialog(self.toolFrame, 'Error while exporting redescriptions to file '
                                 +str(path)+':\n'+str(error)).ShowModal()
        save_dlg.Destroy()
        
    def OnNewW(self, event):
        if self.selectedList != None:
            self.selectedMap = -1
            self.selectedList.viewData()

    def OnFilterToOne(self, event):
        if self.selectedList != None:
            self.selectedList.filterToOne()

    def OnDuplicate(self, event):
        if self.selectedList != None:
            self.selectedList.duplicate()

    def OnToggleHide(self, event):
        if self.selectedList != None:
            self.selectedList.toggleHide()

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
  
    def resetCoordinates(self):
        ### WARNING COORDINATES ARE INVERTED!!!
        self.deleteAllViews()
        self.coord_extrema = [[min(self.dw.coord[0]), max(self.dw.coord[0])],[min(self.dw.coord[1]), max(self.dw.coord[1])]]

    def resetLogger(self):
        if self.dw.minesettings != None and self.dw.minesettings.param.has_key('verbosity'):
            self.logger = Log(self.dw.minesettings.param['verbosity'], self.toolFrame, Message.sendMessage)
            Data.logger = self.logger

    def reloadVars(self):
        ## Initialize variable lists data
        for side in [0,1]:
            if self.dw.data != None and self.details != None:
                fieldsVar = []
                fieldsVar.extend(self.fieldsVar)
                for tyid in set([r.type_id for r in self.dw.data.cols[side]]):
                    fieldsVar.extend(self.fieldsVarTypes[tyid])
                self.lists[side].resetData(self.dw.data.cols[side], fieldsVar, self.details)
            else:
                fieldsVar = []
                fieldsVar.extend(self.fieldsVar)
                self.lists[side].resetData([], fieldsVar, self.details)
            
    def reloadReds(self):
        ## Initialize red lists data
        self.lists["Reds"].resetData(self.dw.reds, self.fieldsRed, self.details, self.dw.rshowids)
        self.lists["Exp"].resetData([], self.fieldsRed, self.details)
        self.lists["Hist"].resetData([], self.fieldsRed, self.details)
#        self.getSelectedMapView().setCurrentRed(redsTmp[0])
#        self.getSelectedMapView().updateRed()
            

if __name__ == '__main__':
    app = wx.App()

    CustViewer.BACKGROUND_SELECTED = wx.SystemSettings_GetColour( wx.SYS_COLOUR_HIGHLIGHT )
    CustViewer.TEXT_SELECTED = wx.SystemSettings_GetColour( wx.SYS_COLOUR_HIGHLIGHTTEXT )
    CustViewer.BACKGROUND = wx.SystemSettings_GetColour( wx.SYS_COLOUR_WINDOW  )
    CustViewer.TEXT = wx.SystemSettings_GetColour( wx.SYS_COLOUR_WINDOWTEXT  )

    app.frame = Siren()
    app.MainLoop()
