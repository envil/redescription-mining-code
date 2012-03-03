import os
import pprint
import random
import wx, wx.grid
import warnings
warnings.simplefilter("ignore")

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


class MyGridTable(wx.grid.PyGridTableBase):
    def __init__(self):
        wx.grid.PyGridTableBase.__init__(self)
        self.fields = []
        self.data = []
        self.details = {}
        self.sortP = (None, False)
        self.currentRows = len(self.data)
        self.currentColumns = len(self.fields)

    def GetNumberRows(self):
        """Return the number of rows in the grid"""
        return len(self.data)

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
        if row < len(self.data) and col < len(self.fields):
            x = self.data[row]
            methode = eval(self.fields[col][0])
            return methode(self.details) == None
        else:
            return True

    def GetTypeName(self, row, col):
        """Return the name of the data type of the value in the cell"""
        if row < len(self.data) and col < len(self.fields):
            x = self.data[row]
            methode = eval(self.fields[col][0])
            return type(methode(self.details))
        else:
            return None

    def GetValue(self, row, col):
        """Return the value of a cell"""
        if row < len(self.data) and col < len(self.fields):
            x = self.data[row]
            methode = eval(self.fields[col][0])
            return methode(self.details)
        else:
            return None
                                  
    def SetValue(self, row, col, value):
        pass

    def updateData(self, data, fieldsRed, details):
        self.data = data
        self.details = details
        self.fields = fieldsRed
        self.ResetView()
        self.currentRows = len(self.data)
        self.currentColumns = len(self.fields)

    def appendRow(self, rowD):
        if len(self.data) == 0 or self.data[-1] != rowD:
            self.data.append(rowD)
            self.ResetView()
            self.currentRows = len(self.data)
       
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

    def HighlightRow(self, row):
        pass
        # for j in range(self.GetNumberCols()):
        #     self.GetView().SetCellBackgroundColour(row,j,'#DBD4FF')
        # self.GetView().ForceRefresh()
        
    def sortData(self, event):
        colS = event.GetCol()
        old = self.sortP[0]
        if self.sortP[0] == colS:
            self.sortP = (self.sortP[0], not self.sortP[1])
        else:
            self.sortP = (colS, False)
        self.data.sort(key= lambda x: eval(self.fields[self.sortP[0]][0])(self.details), reverse=self.sortP[1])
        self.ResetView()

class MySheet(wx.grid.Grid):
    def __init__(self, parent):
        wx.grid.Grid.__init__(self, parent)
        self.table = MyGridTable()
        self.SetTable(self.table)
        self.Bind(wx.grid.EVT_GRID_LABEL_LEFT_CLICK, self.table.sortData)
        self.SetLabelBackgroundColour('#DBD4D4')
        self.EnableEditing(False)
        self.AutoSizeColumns(True)
        
class Siren():
    """ The main frame of the application
    """
    titleTool = 'SpatIal REdescription miniNg :: TOOLS'
    titleMap = 'SpatIal REdescription miniNg :: MAPS'

    fieldsRed = [('x.getQueryLU', 'Query LHS'), ('x.getQueryRU', 'Query RHS'), ('x.getAcc', 'Acc'), ('x.getPVal', 'p-Value')]
    fieldsVar = [('x.getId', 'Id'), ('x.getName', 'Name'), ('x.getType', 'Type')]
    fieldsVarTypes = {1: [('x.getDensity', 'Density')], 2:[('x.getCategories', 'Categories')], 3:[('x.getMin', 'Min'), ('x.getMax', 'Max')]}

    def getFieldRed(red, fieldId):
        methode = eval(Siren.fieldsRed[fieldId][0])
        return methode(self.details)

    def getFieldLabel(fieldId):
        return Siren.fieldsRed[fieldId][1]

    def __init__(self):
        self.toolFrame = wx.Frame(None, -1, self.titleTool)
        self.mapFrame = wx.Frame(None, -1, self.titleMap)

        self.coord = None
        self.coord_proj = None
        self.data = None

        self.lines = []
        self.num_filename='./rajapaja/worldclim_tp.densenum'
        self.bool_filename='./rajapaja/mammals.datbool'
        self.coo_filename='./rajapaja/coordinates.names'
        self.queries_filename='./rajapaja/rajapaja.queries'
        self.settings_filename='./rajapaja/rajapaja.conf'

        self.setts = Settings('mine', ['part_run_gui', self.settings_filename])
        self.setts.getParams()
        
        self.create_tool_panel()
        self.create_map_panel()

        Data.logger = self.logger
        self.loadData()
        self.loadCoordinates()
        redsTmp = self.populateReds()

	self.textbox_num_filename.SetValue(str(self.num_filename))
	self.textbox_bool_filename.SetValue(str(self.bool_filename))
        self.textbox_coo_filename.SetValue(str(self.coo_filename))
        self.textbox_queries_filename.SetValue(str(self.queries_filename))
        self.textbox_settings_filename.SetValue(str(self.settings_filename))

        self.draw_map()

        ## Initialize variable lists data
        for side in [0,1]:
            fieldsVar = []
            fieldsVar.extend(self.fieldsVar)
            for tyid in set([r.type_id for r in self.data.cols[side]]):
                fieldsVar.extend(self.fieldsVarTypes[tyid])
            self.varList[side].table.updateData(self.data.cols[side], fieldsVar, self.details)

        ## Initialize red lists data
        self.histList.table.updateData([], self.fieldsRed, self.details)
        self.redList.table.updateData(redsTmp, self.fieldsRed, self.details)
        self.expList.table.updateData([], self.fieldsRed, self.details)
        self.setCurrentRed(redsTmp[0])
        self.updateRed()
        
    def showFrames(self):
        self.toolFrame.Show()
        self.mapFrame.Show()

    def create_map_panel(self):
        """ Creates the main panel with all the controls on it:
             * mpl canvas 
             * mpl navigation toolbar
             * Control panel for interaction
        """

        self.MapredMapQL = wx.TextCtrl(self.mapFrame, size=(550,-1), style=wx.TE_PROCESS_ENTER)
        self.MapredMapQR = wx.TextCtrl(self.mapFrame, size=(550,-1), style=wx.TE_PROCESS_ENTER)
        self.MapredMapInfo = wx.TextCtrl(self.mapFrame, size=(550,-1), style=wx.TE_READONLY)
        self.button_expand = wx.Button(self.mapFrame, size=(80,-1), label="Expand")
        self.button_expand.Bind(wx.EVT_BUTTON, self.expandRed)
        self.MapredMapQL.Bind(wx.EVT_TEXT_ENTER, self.OnEditRed)
        self.MapredMapQR.Bind(wx.EVT_TEXT_ENTER, self.OnEditRed)

        self.MapfigMap = plt.figure(figsize=(6,7))
        self.Mapcurr_mapi = 0
        self.MapcanvasMap = FigCanvas(self.mapFrame, -1, self.MapfigMap)
        
        self.MaptoolbarMap = NavigationToolbar(self.MapcanvasMap)
 
        self.Mapvbox0 = wx.BoxSizer(wx.VERTICAL)
        flags = wx.ALIGN_CENTER #| wx.ALL | wx.ALIGN_CENTER_VERTICAL
        self.Mapvbox0.Add(self.MapredMapQL, 0, border=3, flag=flags)
        self.Mapvbox0.Add(self.MapredMapQR, 0, border=3, flag=flags)

        self.Maphbox1 = wx.BoxSizer(wx.HORIZONTAL)
        flags = wx.ALIGN_CENTER | wx.ALL
        self.Maphbox1.Add(self.Mapvbox0, 0, border=3, flag=flags)
#	self.Maphbox1.AddSpacer(10)
        self.Maphbox1.Add(self.button_expand, 0, border=3, flag=flags)

        self.Mapvbox3 = wx.BoxSizer(wx.VERTICAL)
        flags = wx.ALIGN_CENTER | wx.ALL | wx.ALIGN_CENTER_VERTICAL
        self.Mapvbox3.Add(self.Maphbox1, 0, border=3, flag=flags)
        self.Mapvbox3.Add(self.MapcanvasMap, 1, wx.ALIGN_CENTER | wx.TOP | wx.EXPAND)
        self.Mapvbox3.Add(self.MapredMapInfo, 0, border=3, flag=flags)
        self.Mapvbox3.Add(self.MaptoolbarMap, 0, border=3, flag=flags)
        self.mapFrame.SetSizer(self.Mapvbox3)
        self.Mapvbox3.Fit(self.mapFrame)

    def create_tool_panel(self):
        """ Creates the main panel with all the controls on it:
             * mpl canvas 
             * mpl navigation toolbar
             * Control panel for interaction
        """

	self.tabbed = wx.Notebook(self.toolFrame, -1, style=(wx.NB_TOP))
        self.panel1 = wx.Panel(self.tabbed, -1)
        self.varList = [MySheet(self.tabbed), MySheet(self.tabbed)]
        self.redList = MySheet(self.tabbed)
        self.expList = MySheet(self.tabbed)
        self.histList = MySheet(self.tabbed)
        self.panelLog = wx.Panel(self.tabbed, -1)
        self.tabbed.AddPage(self.panel1, "Files")
        self.tabbed.AddPage(self.varList[0], "LHS Variables")
        self.tabbed.AddPage(self.varList[1], "RHS Variables")
        self.tabbed.AddPage(self.redList, "Redescriptions")
        self.tabbed.AddPage(self.expList, "Expanding")
        self.tabbed.AddPage(self.histList, "History")
        self.tabbed.AddPage(self.panelLog, "Log")
        
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

        self.varList[0].Bind(wx.grid.EVT_GRID_CELL_LEFT_CLICK, self.OnSelectLHSVar)
        self.varList[1].Bind(wx.grid.EVT_GRID_CELL_LEFT_CLICK, self.OnSelectRHSVar)
        self.redList.Bind(wx.grid.EVT_GRID_CELL_LEFT_CLICK, self.OnSelectListRed)
        self.expList.Bind(wx.grid.EVT_GRID_CELL_LEFT_CLICK, self.OnSelectExpRed)
        self.histList.Bind(wx.grid.EVT_GRID_CELL_LEFT_CLICK, self.OnSelectHistRed) #EVT_GRID_SELECT_CELL

	self.text_log = wx.TextCtrl(self.panelLog, size=(-1,-1), style=wx.TE_READONLY|wx.TE_MULTILINE)
        self.logger = Log(self.setts.param['verbosity'], self.text_log)

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

        self.vboxL = wx.BoxSizer(wx.VERTICAL)
        self.vboxL.Add(self.text_log, 1, wx.ALIGN_CENTER | wx.TOP | wx.EXPAND)
        self.panelLog.SetSizer(self.vboxL)
        self.vbox1.Fit(self.toolFrame)
        
    def on_exit(self, event):
        self.toolFrame.Destroy()
        self.mapFrame.Destroy()

    def on_draw_button(self, event):
        self.draw_figure()
    
    def on_button_plot_map(self, event):
        print "replot"

    def on_text_enter(self, event):
	print "TEXT => DRAW"
        self.draw_figure()

    def on_save_plot(self, event):
        file_choices = "PNG (*.png)|*.png"
        
        dlg = wx.FileDialog(
            self.mapFrame, 
            message="Save plot as...",
            defaultDir=os.getcwd(),
            defaultFile="plot.png",
            wildcard=file_choices,
            style=wx.SAVE)
        
        if dlg.ShowModal() == wx.ID_OK:
            path = dlg.GetPath()
            self.canvas.print_figure(path, dpi=self.dpi)
            self.flash_status_message("Saved to %s" % path)

    def doOpenFileB(self, event):
        file_name = os.path.basename(self.bool_filename)
        wcd = 'All files (*)|*|Editor files (*.ef)|*.ef|'
        dir = os.getcwd()
        open_dlg = wx.FileDialog(self.toolFrame, message='Choose a file', defaultDir=dir, defaultFile='', 
			wildcard=wcd, style=wx.OPEN|wx.CHANGE_DIR)
        if open_dlg.ShowModal() == wx.ID_OK:
            path = open_dlg.GetPath()

            try:
                file = open(path, 'r')
		self.bool_filename = path
		self.textbox_bool_filename.SetValue(str(self.bool_filename))

            except IOError, error:
                dlg = wx.MessageDialog(self.toolFrame, 'Error opening file\n' + str(error))
                dlg.ShowModal()
        open_dlg.Destroy()

    def doOpenFileN(self, event):
        file_name = os.path.basename(self.num_filename)
        wcd = 'All files (*)|*|Editor files (*.ef)|*.ef|'
        dir = os.getcwd()
        open_dlg = wx.FileDialog(self.toolFrame, message='Choose a file', defaultDir=dir, defaultFile='', 
			wildcard=wcd, style=wx.OPEN|wx.CHANGE_DIR)
        if open_dlg.ShowModal() == wx.ID_OK:
            path = open_dlg.GetPath()

            try:
                file = open(path, 'r')
		self.num_filename = path
		self.textbox_num_filename.SetValue(str(self.num_filename))

            except IOError, error:
                dlg = wx.MessageDialog(self.toolFrame, 'Error opening file\n' + str(error))
                dlg.ShowModal()
        open_dlg.Destroy()


    def doOpenFileC(self, event):
        file_name = os.path.basename(self.coo_filename)
        wcd = 'All files (*)|*|Editor files (*.ef)|*.ef|'
        dir = os.getcwd()
        open_dlg = wx.FileDialog(self.toolFrame, message='Choose a file', defaultDir=dir, defaultFile='', 
			wildcard=wcd, style=wx.OPEN|wx.CHANGE_DIR)
        if open_dlg.ShowModal() == wx.ID_OK:
            path = open_dlg.GetPath()

            try:
                file = open(path, 'r')
		self.coo_filename = path
		self.textbox_coo_filename.SetValue(str(self.coo_filename))

            except IOError, error:
                dlg = wx.MessageDialog(self.toolFrame, 'Error opening file\n' + str(error))
                dlg.ShowModal()
        open_dlg.Destroy()


    def doOpenFileQ(self, event):
        file_name = os.path.basename(self.queries_filename)
        wcd = 'All files (*)|*|Editor files (*.ef)|*.ef|'
        dir = os.getcwd()
        open_dlg = wx.FileDialog(self.toolFrame, message='Choose a file', defaultDir=dir, defaultFile='', 
			wildcard=wcd, style=wx.OPEN|wx.CHANGE_DIR)
        if open_dlg.ShowModal() == wx.ID_OK:
            path = open_dlg.GetPath()

            try:
                file = open(path, 'r')
		self.queries_filename = path
		self.textbox_queries_filename.SetValue(str(self.queries_filename))

            except IOError, error:
                dlg = wx.MessageDialog(self.toolFrame, 'Error opening file\n' + str(error))
                dlg.ShowModal()
        open_dlg.Destroy()

    def doOpenFileS(self, event):
        file_name = os.path.basename(self.settings_filename)
        wcd = 'All files (*)|*|Editor files (*.ef)|*.ef|'
        dir = os.getcwd()
        open_dlg = wx.FileDialog(self.toolFrame, message='Choose a file', defaultDir=dir, defaultFile='', 
			wildcard=wcd, style=wx.OPEN|wx.CHANGE_DIR)
        if open_dlg.ShowModal() == wx.ID_OK:
            path = open_dlg.GetPath()

            try:
                file = open(path, 'r')
		self.settings_filename = path
		self.textbox_settings_filename.SetValue(str(self.settings_filename))

            except IOError, error:
                dlg = wx.MessageDialog(self.toolFrame, 'Error opening file\n' + str(error))
                dlg.ShowModal()
        open_dlg.Destroy()

        
    def OnEditRed(self, event):
        self.updateRed()

    def OnSelectLHSVar(self, event):
        if event.GetRow() < len(self.varList[0].table.data):
            self.varList[0].table.HighlightRow(event.GetRow())
            self.MapredMapQL.ChangeValue(self.varList[0].table.data[event.GetRow()].getItem().dispU(False, self.details['names'][0]))
            self.MapredMapQR.ChangeValue("")
            self.MapredMapInfo.ChangeValue("")
            self.updateRed(False)

    def OnSelectRHSVar(self, event):
        if event.GetRow() < len(self.varList[1].table.data):
            self.varList[1].table.HighlightRow(event.GetRow())
            self.MapredMapQR.ChangeValue(self.varList[1].table.data[event.GetRow()].getItem().dispU(False, self.details['names'][1]))
            self.MapredMapQL.ChangeValue("")
            self.MapredMapInfo.ChangeValue("")
            self.updateRed(False)

    def OnSelectListRed(self, event):
        if event.GetRow() < len(self.redList.table.data):
            self.redList.table.HighlightRow(event.GetRow())
            self.setCurrentRed(self.redList.table.data[event.GetRow()])
            self.updateRed()
        
    def OnSelectExpRed(self, event):
        if event.GetRow() < len(self.expList.table.data):
            self.expList.table.HighlightRow(event.GetRow())
            self.setCurrentRed(self.expList.table.data[event.GetRow()])
            self.updateRed()

    def OnSelectHistRed(self, event):
        if event.GetRow() < len(self.histList.table.data):
            self.histList.table.HighlightRow(event.GetRow())
            self.setCurrentRed(self.histList.table.data[event.GetRow()])
            self.updateRed(False)

    def setCurrentRed(self, red):
        self.MapredMapQL.ChangeValue(red.queries[0].dispU(self.details['names'][0]))
        self.MapredMapQR.ChangeValue(red.queries[1].dispU(self.details['names'][1]))
        self.MapredMapInfo.ChangeValue(red.dispLParts())

    def updateRed(self, addHist=True):
        red = self.redraw_map()
        if red != None and addHist:
            self.histList.table.appendRow(red)
        return red
        
    def parseRed(self):
        queryL = Query.parseAny(self.MapredMapQL.GetValue().strip(), self.details['names'][0])
        queryR = Query.parseAny(self.MapredMapQR.GetValue().strip(), self.details['names'][1])
        if queryL != None and queryR != None: 
            return Redescription.fromQueriesPair([queryL, queryR], self.data) 
        
    def draw_map(self):
        """ Draws the map
        """
        
        self.MapfigMap.clear()
        m = Basemap(llcrnrlon=self.coord_extrema[0][0], \
                llcrnrlat=self.coord_extrema[1][0], \
                urcrnrlon=self.coord_extrema[0][1], \
                urcrnrlat=self.coord_extrema[1][1], \
                resolution = 'c', \
                projection = 'mill', \
                lon_0 = self.coord_extrema[0][0] + (self.coord_extrema[0][1]-self.coord_extrema[0][0])/2.0, \
                lat_0 = self.coord_extrema[1][0] + (self.coord_extrema[1][1]-self.coord_extrema[1][0])/2.04)
        self.axe = m
        m.ax = self.MapfigMap.add_axes([0, 0, 1, 1])

        m.drawcoastlines(color='gray')
        m.drawcountries(color='gray')
        m.drawmapboundary(fill_color='#EEFFFF') 
        m.fillcontinents(color='#FFFFFF', lake_color='#EEFFFF')
#        m.etopo()
        self.coord_proj = m(self.coord[0], self.coord[1])
        height = 3; width = 3
#        self.corners= [ zip(*[ m(self.coord[0][id]+off[0]*width, self.coord[1][id]+off[1]*height) for off in [(-1,-1), (-1,1), (1,1), (1,-1)]]) for id in range(len(self.coord[0]))] 
        self.MapcanvasMap.draw()

    def redraw_map(self, event=None):
        """ Redraws the map
        """
        red = self.parseRed()
        if red == None:
            return self.histList.table.data[-1]

        self.MapredMapQL.ChangeValue(red.queries[0].dispU(self.details['names'][0]))
        self.MapredMapQR.ChangeValue(red.queries[1].dispU(self.details['names'][1]))
        self.MapredMapInfo.ChangeValue(red.dispLParts())
        m = self.axe
        colors = ['b', 'r', 'purple']
        sizes = [3, 3, 4]
        markers = ['s', 's', 's']
        i = 0
        while len(self.lines):
#            plt.gca().patches.remove(self.lines.pop())
            plt.gca().axes.lines.remove(self.lines.pop())

        for part in red.partsNoMiss():
            if len(part) > 0:
                # for id in part:
                #     self.lines.extend(plt.fill(self.corners[id][0], self.corners[id][1], fc=colors[i], ec=colors[i], alpha=0.5))
                    
                ids = np.array(list(part))
                self.lines.extend(m.plot(self.coord_proj[0][ids],self.coord_proj[1][ids], mfc=colors[i], mec=colors[i], marker=markers[i], markersize=sizes[i], linestyle='None', alpha=0.5))
            else:
                self.lines.extend(m.plot([],[], mfc=colors[i], mec=colors[i], marker=markers[i], markersize=sizes[i], linestyle='None'))
            i += 1
        plt.legend(('Left query only', 'Right query only', 'Both queries'), 'upper left', shadow=True, fancybox=True)
        self.MapcanvasMap.draw()
        return red

    def loadData(self):
        self.data = Data([self.bool_filename, self.num_filename])
        self.details = {'names': self.data.getNames([self.bool_filename, self.num_filename])}
        
    def loadCoordinates(self):
        ### WARNING COORDINATES ARE INVERTED!!!
        self.coord = np.loadtxt(self.coo_filename, unpack=True, usecols=(1,0))
        self.coord_extrema = [[min(self.coord[0]), max(self.coord[0])],[min(self.coord[1]), max(self.coord[1])]]

    def expandRed(self, event):
        ### POSITION DEPENDENT UPDATE
        self.tabbed.ChangeSelection(6) #self.tabbed.HitTest(self.panelLog))
        red = self.redraw_map()
        expTmp = greedyRed.part_run(self.data, self.setts, red, self.logger)
        self.tabbed.ChangeSelection(5) #self.tabbed.HitTest(self.expList))
        self.expList.table.updateData(expTmp, self.fieldsRed, self.details)

    def populateReds(self):
        reds_fp = open(self.queries_filename)
        reds = []
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
    app = wx.PySimpleApp()
    app.frame = Siren()
    app.frame.showFrames()
    app.MainLoop()
