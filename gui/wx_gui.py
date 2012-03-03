import os
import pprint
import random
import wx

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

class BarsFrame(wx.Frame):
    """ The main frame of the application
    """
    title = 'SpatIal REdescription miniNg'
    
    def __init__(self):
        wx.Frame.__init__(self, None, -1, self.title)

        self.coord = None
        self.coord_proj = None
        self.data = None

        self.lines = []
        self.num_filename='/home/galbrun/TKTL/redescriptors/sandbox/gui/worldclim_tp.densenum'
        self.bool_filename='/home/galbrun/TKTL/redescriptors/sandbox/gui/mammals.datbool'
        self.coo_filename='/home/galbrun/TKTL/redescriptors/sandbox/gui/coordinates.names'
        self.queries_filename='/home/galbrun/TKTL/redescriptors/sandbox/gui/rajapaja.queries'
        self.reds = []

        self.loadData()
        self.loadCoordinates()
        self.populateReds()
	
        self.create_menu()
        self.create_main_panel()
        
	self.textbox_num_filename.SetValue(str(self.num_filename))
	self.textbox_bool_filename.SetValue(str(self.bool_filename))
        self.textbox_coo_filename.SetValue(str(self.coo_filename))
        self.textbox_queries_filename.SetValue(str(self.queries_filename))
        self.fillListRed()
        self.redsc = self.reds[6]
        self.redMapQL.SetValue(self.redsc.queries[0].dispU(self.names[0]))
        self.redMapQR.SetValue(self.redsc.queries[1].dispU(self.names[1]))
        self.redMapInfo.SetValue(self.redsc.dispCaracteristiquesSimple())
        self.redraw_map()

    def fillListRed(self):
        tmp = []
        for red in self.reds:
            tmp.append(red.dispQueriesU(self.names))
        self.redList.Set(tmp)

    def create_menu(self):
        self.menubar = wx.MenuBar()
        
        menu_file = wx.Menu()
        m_exit = menu_file.Append(-1, "E&xit\tCtrl-X", "Exit")
        self.Bind(wx.EVT_MENU, self.on_exit, m_exit)
        self.SetMenuBar(self.menubar)

    def create_main_panel(self):
        """ Creates the main panel with all the controls on it:
             * mpl canvas 
             * mpl navigation toolbar
             * Control panel for interaction
        """

	self.tabbed = wx.Notebook(self, -1, style=(wx.NB_TOP))
        self.panel1 = wx.Panel(self.tabbed, -1)
        self.panel3 = wx.Panel(self.tabbed, -1)
        self.tabbed.AddPage(self.panel3, "Map")
        self.tabbed.AddPage(self.panel1, "Files")
        
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
 
        self.redMapQL = wx.TextCtrl(self.panel3, size=(900,-1), style=wx.TE_PROCESS_ENTER)
        self.redMapQR = wx.TextCtrl(self.panel3, size=(900,-1), style=wx.TE_PROCESS_ENTER)
        self.redMapInfo = wx.TextCtrl(self.panel3, size=(300,-1), style=wx.TE_READONLY)
        self.redList = wx.ListBox(self.panel3, 26, wx.DefaultPosition, (770, 550), [], wx.LB_SINGLE)
        self.redList.SetFont(wx.Font(9, wx.FONTFAMILY_MODERN, wx.FONTWEIGHT_NORMAL, wx.FONTSTYLE_NORMAL))
        self.redList.Bind(wx.EVT_LISTBOX, self.OnSelectListRed)
        self.redMapQL.Bind(wx.EVT_TEXT_ENTER, self.redraw_map)
        self.redMapQR.Bind(wx.EVT_TEXT_ENTER, self.redraw_map)

        self.figMap = plt.figure(figsize=(6,7))
        self.curr_mapi = 0
        self.canvasMap = FigCanvas(self.panel3, -1, self.figMap)
        self.draw_map()

        # self.buttonPlotMap = wx.Button(self.panel3, wx.NewId(), "Plot")
        # self.figurecanvas.Bind(wx.EVT_LEFT_DCLICK, self.on_dclick)
        # self.buttonPlotMap.Bind(wx.EVT_BUTTON, self.draw_map)
        self.toolbarMap = NavigationToolbar(self.canvasMap)
        # self.subframe_opened = False
        #
        # Layout with box sizers
        #

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

        self.vbox1.Add(self.hboxL1, 0, flag = wx.ALIGN_LEFT | wx.TOP)
        self.vbox1.Add(self.hboxR1, 0, flag = wx.ALIGN_LEFT | wx.TOP)
        self.vbox1.Add(self.hboxC1, 0, flag = wx.ALIGN_LEFT | wx.TOP)
        self.vbox1.Add(self.hboxQ1, 0, flag = wx.ALIGN_LEFT | wx.TOP)
        
        self.panel1.SetSizer(self.vbox1)
        self.vbox1.Fit(self)


        self.vbox3 = wx.BoxSizer(wx.VERTICAL)

        self.hbox30 = wx.BoxSizer(wx.HORIZONTAL)
        flags = wx.ALIGN_LEFT | wx.ALL | wx.ALIGN_CENTER_VERTICAL

        self.vbox300 = wx.BoxSizer(wx.VERTICAL)
        self.vbox300.Add(self.redMapQL, 0, border=3, flag=flags)
        self.vbox300.Add(self.redMapQR, 0, border=3, flag=flags)
        self.hbox30.Add(self.vbox300, 0, border=3, flag=flags)

        self.vbox301 = wx.BoxSizer(wx.VERTICAL)
        self.vbox301.Add(self.redMapInfo, 0, border=3, flag=flags)
        self.vbox301.Add(self.toolbarMap, 0, wx.EXPAND)
        self.hbox30.Add(self.vbox301, 0, border=3, flag=flags)
        
        self.hbox30.AddSpacer(10)
        
        self.vbox3.Add(self.hbox30, 0, border=3, flag=flags)

        self.hbox3 = wx.BoxSizer(wx.HORIZONTAL)
        flags = wx.ALIGN_LEFT | wx.ALL  | wx.EXPAND | wx.ALIGN_CENTER_VERTICAL
        
        #self.vvbox32 = wx.BoxSizer(wx.VERTICAL)
        self.hbox3.Add(self.redList, 0, border=3, flag=flags)
        #self.hbox3.Add(self.vvbox32, 0, flag = wx.ALIGN_CENTER | wx.EXPAND)

        #self.vvbox31 = wx.BoxSizer(wx.VERTICAL)
        self.hbox3.Add(self.canvasMap, 1, wx.ALIGN_CENTER | wx.TOP | wx.EXPAND)
        #self.hbox3.Add(self.vvbox31, 0, flag = wx.ALIGN_CENTER | wx.EXPAND)

	#self.hbox3.AddSpacer(10)

        self.vbox3.Add(self.hbox3, 0, flag = wx.ALIGN_CENTER | wx.EXPAND)

        self.panel3.SetSizer(self.vbox3)
        self.vbox3.Fit(self)

        # self.vbox3.Add(self.hbox3, 0, flag = wx.ALIGN_LEFT | wx.TOP)
        # self.panel3.SetSizer(self.vbox3)
        # self.vbox3.Fit(self)

    def doOpenFileB(self, event):
        file_name = os.path.basename(self.bool_filename)
        wcd = 'All files (*)|*|Editor files (*.ef)|*.ef|'
        dir = os.getcwd()
        open_dlg = wx.FileDialog(self, message='Choose a file', defaultDir=dir, defaultFile='', 
			wildcard=wcd, style=wx.OPEN|wx.CHANGE_DIR)
        if open_dlg.ShowModal() == wx.ID_OK:
            path = open_dlg.GetPath()

            try:
                file = open(path, 'r')
		self.bool_filename = path
		self.textbox_bool_filename.SetValue(str(self.bool_filename))

            except IOError, error:
                dlg = wx.MessageDialog(self, 'Error opening file\n' + str(error))
                dlg.ShowModal()
        open_dlg.Destroy()

    def doOpenFileN(self, event):
        file_name = os.path.basename(self.num_filename)
        wcd = 'All files (*)|*|Editor files (*.ef)|*.ef|'
        dir = os.getcwd()
        open_dlg = wx.FileDialog(self, message='Choose a file', defaultDir=dir, defaultFile='', 
			wildcard=wcd, style=wx.OPEN|wx.CHANGE_DIR)
        if open_dlg.ShowModal() == wx.ID_OK:
            path = open_dlg.GetPath()

            try:
                file = open(path, 'r')
		self.num_filename = path
		self.textbox_num_filename.SetValue(str(self.num_filename))

            except IOError, error:
                dlg = wx.MessageDialog(self, 'Error opening file\n' + str(error))
                dlg.ShowModal()
        open_dlg.Destroy()


    def doOpenFileC(self, event):
        file_name = os.path.basename(self.coo_filename)
        wcd = 'All files (*)|*|Editor files (*.ef)|*.ef|'
        dir = os.getcwd()
        open_dlg = wx.FileDialog(self, message='Choose a file', defaultDir=dir, defaultFile='', 
			wildcard=wcd, style=wx.OPEN|wx.CHANGE_DIR)
        if open_dlg.ShowModal() == wx.ID_OK:
            path = open_dlg.GetPath()

            try:
                file = open(path, 'r')
		self.coo_filename = path
		self.textbox_coo_filename.SetValue(str(self.coo_filename))

            except IOError, error:
                dlg = wx.MessageDialog(self, 'Error opening file\n' + str(error))
                dlg.ShowModal()
        open_dlg.Destroy()


    def doOpenFileQ(self, event):
        file_name = os.path.basename(self.queries_filename)
        wcd = 'All files (*)|*|Editor files (*.ef)|*.ef|'
        dir = os.getcwd()
        open_dlg = wx.FileDialog(self, message='Choose a file', defaultDir=dir, defaultFile='', 
			wildcard=wcd, style=wx.OPEN|wx.CHANGE_DIR)
        if open_dlg.ShowModal() == wx.ID_OK:
            path = open_dlg.GetPath()

            try:
                file = open(path, 'r')
		self.queries_filename = path
		self.textbox_queries_filename.SetValue(str(self.queries_filename))

            except IOError, error:
                dlg = wx.MessageDialog(self, 'Error opening file\n' + str(error))
                dlg.ShowModal()
        open_dlg.Destroy()

        
    def OnSelectListRed(self, event):
        index = event.GetSelection()
        self.redsc = self.reds[index]
        self.redMapQL.SetValue(self.redsc.queries[0].dispU(self.names[0]))
        self.redMapQR.SetValue(self.redsc.queries[1].dispU(self.names[1]))
        self.redMapInfo.SetValue(self.redsc.dispCaracteristiquesSimple())
        self.redraw_map()

    def parseRed(self):
        ### TODO HERE COMES THE HARD WORK...
        queryL = Query.parseU(self.redMapQL.GetValue().strip(), self.names[0])
        queryR = Query.parseU(self.redMapQR.GetValue().strip(), self.names[1])
        if queryL != None and queryR != None: 
            return Redescription.fromQueriesPair([queryL, queryR], self.data) 
        
    def draw_map(self):
        """ Draws the map
        """
        
        self.figMap.clear()
        m = Basemap(llcrnrlon=self.coord_extrema[0][0], \
                llcrnrlat=self.coord_extrema[1][0], \
                urcrnrlon=self.coord_extrema[0][1], \
                urcrnrlat=self.coord_extrema[1][1], \
                resolution = 'c', \
                projection = 'mill', \
                lon_0 = self.coord_extrema[0][0] + (self.coord_extrema[0][1]-self.coord_extrema[0][0])/2.0, \
                lat_0 = self.coord_extrema[1][0] + (self.coord_extrema[1][1]-self.coord_extrema[1][0])/2.04)
        self.axe = m
        m.ax = self.figMap.add_axes([0, 0, 1, 1])

        m.drawcoastlines(color='gray')
        m.drawcountries(color='gray')
        m.drawmapboundary(fill_color='#EEFFFF') 
        m.fillcontinents(color='#FFFFFF', lake_color='#EEFFFF')
#        m.etopo()
        self.coord_proj = m(self.coord[0], self.coord[1])
        height = 3; width = 3
#        self.corners= [ zip(*[ m(self.coord[0][id]+off[0]*width, self.coord[1][id]+off[1]*height) for off in [(-1,-1), (-1,1), (1,1), (1,-1)]]) for id in range(len(self.coord[0]))] 
        self.canvasMap.draw()

    def redraw_map(self, event=None):
        """ Redraws the map
        """
        redesc = self.parseRed()
        if redesc == None:
            return

        self.redsc = redesc
        self.redMapQL.SetValue(self.redsc.queries[0].dispU(self.names[0]))
        self.redMapQR.SetValue(self.redsc.queries[1].dispU(self.names[1]))
        self.redMapInfo.SetValue(self.redsc.dispCaracteristiquesSimple())
        m = self.axe
        colors = ['b', 'r', 'purple']
        sizes = [3, 3, 4]
        markers = ['s', 's', 's']
        i = 0
        while len(self.lines):
#            plt.gca().patches.remove(self.lines.pop())
            plt.gca().axes.lines.remove(self.lines.pop())

        for part in redesc.partsNoMiss():
            if len(part) > 0:
                # for id in part:
                #     self.lines.extend(plt.fill(self.corners[id][0], self.corners[id][1], fc=colors[i], ec=colors[i], alpha=0.5))
                    
                ids = np.array(list(part))
                self.lines.extend(m.plot(self.coord_proj[0][ids],self.coord_proj[1][ids], mfc=colors[i], mec=colors[i], marker=markers[i], markersize=sizes[i], linestyle='None', alpha=0.5))
            else:
                self.lines.extend(m.plot([],[], mfc=colors[i], mec=colors[i], marker=markers[i], markersize=sizes[i], linestyle='None'))
            i += 1
        plt.legend(('Left query only', 'Right query only', 'Both queries'), 'upper left', shadow=True, fancybox=True)
        self.canvasMap.draw()
        
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
            self, 
            message="Save plot as...",
            defaultDir=os.getcwd(),
            defaultFile="plot.png",
            wildcard=file_choices,
            style=wx.SAVE)
        
        if dlg.ShowModal() == wx.ID_OK:
            path = dlg.GetPath()
            self.canvas.print_figure(path, dpi=self.dpi)
            self.flash_status_message("Saved to %s" % path)
        
    def on_exit(self, event):
        self.Destroy()

    def loadData(self):
        self.data = Data([self.bool_filename, self.num_filename])
        self.names = self.data.getNames([self.bool_filename, self.num_filename])

    def loadCoordinates(self):
        ### WARNING COORDINATES ARE INVERTED!!!
        self.coord = np.loadtxt(self.coo_filename, unpack=True, usecols=(1,0))
        self.coord_extrema = [[min(self.coord[0]), max(self.coord[0])],[min(self.coord[1]), max(self.coord[1])]]

        # coo_fp = open(self.coo_filename)
        # coo_tmp = [[], []]
        # ok = True
        # for line in coo_fp:
        #     parts = line.strip().split()
        #     if len(parts) == 2:
        #         try:
        #             lat = float(parts[0])
        #             lon = float(parts[1])
        #         except ValueError:
        #             ok = False
        #         coo_tmp[1].append(lat)
        #         coo_tmp[0].append(lon)
        #     else:
        #         ok = False
        # if ok:
        #     self.coord = coo_tmp
        #     self.coord_proj = m(self.coord[0], self.coord[1])
        
    def populateReds(self):
        reds_fp = open(self.queries_filename)
        self.reds = []
        for line in reds_fp:
            parts = line.strip().split('\t')
            if len(parts) > 1:
                queryL = Query.parse(parts[0])
                queryR = Query.parse(parts[1])
                red = Redescription.fromQueriesPair([queryL, queryR], self.data) 
                if red != None:
                    self.reds.append(red)


class MapFrame(wx.Frame):
    """ The map frame of the application
    """
    title = 'Map'
    
    def __init__(self):
        wx.Frame.__init__(self, None, -1, self.title)
	
        self.create_menu()
        self.create_main_panel()

    def set_redsc(self, redsc):
        self.redsc = redesc
        self.redMapQL.SetValue(self.redsc.queries[0].dispU(self.names[0]))
        self.redMapQR.SetValue(self.redsc.queries[1].dispU(self.names[1]))
        self.redMapInfo.SetValue(self.redsc.dispCaracteristiquesSimple())
        self.redraw_map()

 
    def create_main_panel(self):
        """ Creates the main panel with all the controls on it:
             * mpl canvas 
             * mpl navigation toolbar
             * Control panel for interaction
        """

	self.tabbed = wx.Notebook(self, -1, style=(wx.NB_TOP))
        self.panel1 = wx.Panel(self.tabbed, -1)
        self.panel3 = wx.Panel(self.tabbed, -1)
        self.tabbed.AddPage(self.panel3, "Map")
        self.tabbed.AddPage(self.panel1, "Files")
        
 
        self.redMapQL = wx.TextCtrl(self, size=(900,-1), style=wx.TE_PROCESS_ENTER)
        self.redMapQR = wx.TextCtrl(self, size=(900,-1), style=wx.TE_PROCESS_ENTER)
        self.redMapInfo = wx.TextCtrl(self, size=(300,-1), style=wx.TE_READONLY)
        self.redMapQL.Bind(wx.EVT_TEXT_ENTER, self.redraw_map)
        self.redMapQR.Bind(wx.EVT_TEXT_ENTER, self.redraw_map)

        self.figMap = plt.figure(figsize=(6,7))
        self.curr_mapi = 0
        self.canvasMap = FigCanvas(self.panel3, -1, self.figMap)
        self.draw_map()

        # self.buttonPlotMap = wx.Button(self.panel3, wx.NewId(), "Plot")
        # self.figurecanvas.Bind(wx.EVT_LEFT_DCLICK, self.on_dclick)
        # self.buttonPlotMap.Bind(wx.EVT_BUTTON, self.draw_map)
        self.toolbarMap = NavigationToolbar(self.canvasMap)
        # self.subframe_opened = False
        #
        # Layout with box sizers
        #

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

        self.vbox1.Add(self.hboxL1, 0, flag = wx.ALIGN_LEFT | wx.TOP)
        self.vbox1.Add(self.hboxR1, 0, flag = wx.ALIGN_LEFT | wx.TOP)
        self.vbox1.Add(self.hboxC1, 0, flag = wx.ALIGN_LEFT | wx.TOP)
        self.vbox1.Add(self.hboxQ1, 0, flag = wx.ALIGN_LEFT | wx.TOP)
        
        self.panel1.SetSizer(self.vbox1)
        self.vbox1.Fit(self)


        self.vbox3 = wx.BoxSizer(wx.VERTICAL)

        self.hbox30 = wx.BoxSizer(wx.HORIZONTAL)
        flags = wx.ALIGN_LEFT | wx.ALL | wx.ALIGN_CENTER_VERTICAL

        self.vbox300 = wx.BoxSizer(wx.VERTICAL)
        self.vbox300.Add(self.redMapQL, 0, border=3, flag=flags)
        self.vbox300.Add(self.redMapQR, 0, border=3, flag=flags)
        self.hbox30.Add(self.vbox300, 0, border=3, flag=flags)

        self.vbox301 = wx.BoxSizer(wx.VERTICAL)
        self.vbox301.Add(self.redMapInfo, 0, border=3, flag=flags)
        self.vbox301.Add(self.toolbarMap, 0, wx.EXPAND)
        self.hbox30.Add(self.vbox301, 0, border=3, flag=flags)
        
        self.hbox30.AddSpacer(10)
        
        self.vbox3.Add(self.hbox30, 0, border=3, flag=flags)

        self.hbox3 = wx.BoxSizer(wx.HORIZONTAL)
        flags = wx.ALIGN_LEFT | wx.ALL  | wx.EXPAND | wx.ALIGN_CENTER_VERTICAL
        
        #self.vvbox32 = wx.BoxSizer(wx.VERTICAL)
        self.hbox3.Add(self.redList, 0, border=3, flag=flags)
        #self.hbox3.Add(self.vvbox32, 0, flag = wx.ALIGN_CENTER | wx.EXPAND)

        #self.vvbox31 = wx.BoxSizer(wx.VERTICAL)
        self.hbox3.Add(self.canvasMap, 1, wx.ALIGN_CENTER | wx.TOP | wx.EXPAND)
        #self.hbox3.Add(self.vvbox31, 0, flag = wx.ALIGN_CENTER | wx.EXPAND)

	#self.hbox3.AddSpacer(10)

        self.vbox3.Add(self.hbox3, 0, flag = wx.ALIGN_CENTER | wx.EXPAND)

        self.panel3.SetSizer(self.vbox3)
        self.vbox3.Fit(self)

        # self.vbox3.Add(self.hbox3, 0, flag = wx.ALIGN_LEFT | wx.TOP)
        # self.panel3.SetSizer(self.vbox3)
        # self.vbox3.Fit(self)

    def parseRed(self):
        ### TODO HERE COMES THE HARD WORK...
        queryL = Query.parseU(self.redMapQL.GetValue().strip(), self.names[0])
        queryR = Query.parseU(self.redMapQR.GetValue().strip(), self.names[1])
        if queryL != None and queryR != None: 
            return Redescription.fromQueriesPair([queryL, queryR], self.data) 
        
    def draw_map(self):
        """ Draws the map
        """
        
        self.figMap.clear()
        m = Basemap(llcrnrlon=self.coord_extrema[0][0], \
                llcrnrlat=self.coord_extrema[1][0], \
                urcrnrlon=self.coord_extrema[0][1], \
                urcrnrlat=self.coord_extrema[1][1], \
                resolution = 'c', \
                projection = 'mill', \
                lon_0 = self.coord_extrema[0][0] + (self.coord_extrema[0][1]-self.coord_extrema[0][0])/2.0, \
                lat_0 = self.coord_extrema[1][0] + (self.coord_extrema[1][1]-self.coord_extrema[1][0])/2.04)
        self.axe = m
        m.ax = self.figMap.add_axes([0, 0, 1, 1])

        m.drawcoastlines(color='gray')
        m.drawcountries(color='gray')
        m.drawmapboundary(fill_color='#EEFFFF') 
        m.fillcontinents(color='#FFFFFF', lake_color='#EEFFFF')
#        m.etopo()
        self.coord_proj = m(self.coord[0], self.coord[1])
        height = 3; width = 3
#        self.corners= [ zip(*[ m(self.coord[0][id]+off[0]*width, self.coord[1][id]+off[1]*height) for off in [(-1,-1), (-1,1), (1,1), (1,-1)]]) for id in range(len(self.coord[0]))] 
        self.canvasMap.draw()

    def redraw_map(self, event=None):
        """ Redraws the map
        """
        redesc = self.parseRed()
        if redesc == None:
            return

        self.redsc = redesc
        self.redMapQL.SetValue(self.redsc.queries[0].dispU(self.names[0]))
        self.redMapQR.SetValue(self.redsc.queries[1].dispU(self.names[1]))
        self.redMapInfo.SetValue(self.redsc.dispCaracteristiquesSimple())
        m = self.axe
        colors = ['b', 'r', 'purple']
        sizes = [3, 3, 4]
        markers = ['s', 's', 's']
        i = 0
        while len(self.lines):
#            plt.gca().patches.remove(self.lines.pop())
            plt.gca().axes.lines.remove(self.lines.pop())

        for part in redesc.partsNoMiss():
            if len(part) > 0:
                # for id in part:
                #     self.lines.extend(plt.fill(self.corners[id][0], self.corners[id][1], fc=colors[i], ec=colors[i], alpha=0.5))
                    
                ids = np.array(list(part))
                self.lines.extend(m.plot(self.coord_proj[0][ids],self.coord_proj[1][ids], mfc=colors[i], mec=colors[i], marker=markers[i], markersize=sizes[i], linestyle='None', alpha=0.5))
            else:
                self.lines.extend(m.plot([],[], mfc=colors[i], mec=colors[i], marker=markers[i], markersize=sizes[i], linestyle='None'))
            i += 1
        plt.legend(('Left query only', 'Right query only', 'Both queries'), 'upper left', shadow=True, fancybox=True)
        self.canvasMap.draw()

    def on_save_plot(self, event):
        file_choices = "PNG (*.png)|*.png"
        
        dlg = wx.FileDialog(
            self, 
            message="Save plot as...",
            defaultDir=os.getcwd(),
            defaultFile="plot.png",
            wildcard=file_choices,
            style=wx.SAVE)
        
        if dlg.ShowModal() == wx.ID_OK:
            path = dlg.GetPath()
            self.canvas.print_figure(path, dpi=self.dpi)
            self.flash_status_message("Saved to %s" % path)
        
    def on_exit(self, event):
        self.Destroy()


if __name__ == '__main__':
    app = wx.PySimpleApp()
    app.frame = BarsFrame()
    app.frame.Show()
    app.MainLoop()
