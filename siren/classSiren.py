import os, os.path
import wx
import time
import sys
# import wx.lib.agw.pybusyinfo as PBI
import wx.lib.dialogs

from reremi.toolLog import Log
from reremi.classData import Data, DataError
from reremi.classConstraints import Constraints
from reremi.classBatch import Batch
from reremi.toolICList import ICList

from classGridTable import VarTable, RedTable, RowTable
from DataWrapper import DataWrapper, findFile
from classPreferencesDialog import PreferencesDialog
from miscDialogs import ImportDataDialog, ImportDataCSVDialog, FindDialog
from factView import ViewFactory
import toolCommMultip


import pdb
 
class Siren():
    """ The main frame of the application
    """

    titleTool = 'SIREN :: tools'
    titlePref = 'SIREN :: '
    titleHelp = 'SIREN :: help'
    curr_dir = os.path.dirname(os.path.abspath(__file__))
    helpURL = findFile('index.html', ['help', curr_dir+'/help'])
    helpInternetURL = 'http://www.cs.Helsinki.FI/u/galbrun/redescriptors/siren'
 

    # For About dialog
    name = "Siren"    
    programURL = "http://www.cs.helsinki.fi/u/galbrun/redescriptors/siren"
    version = '1.1.0'
    cpyright = '(C) 2012 Esther Galbrun and Pauli Miettinen'

    pref_dir = os.path.dirname(__file__)
    about_file = findFile('ABOUT', [pref_dir])
    icon_file = findFile('siren_icon32x32.png', ['icons', pref_dir + '/icons'])

    license_file = findFile('LICENSE', [pref_dir])
    external_licenses = ['basemap', 'matplotlib', 'python', 'wx']

    results_delay = 1000
         
    def __init__(self):
        self.busyDlg = None
        self.findDlg = None
        self.dw = None
        self.plant = None
        self.tabs = {0: {"title":"LHS Variables", "short": "LHS", "type":"Var", "hide":False, "style":None},
                     1: {"title":"RHS Variables", "short": "RHS", "type":"Var", "hide":False, "style":None},
                     "rows": {"title":"Entities", "short": "Ent", "type":"Row", "hide":False, "style":None},
                     "reds": {"title":"Redescriptions", "short": "R", "type":"Reds", "hide":False, "style":None},
                     "exp": {"title":"Expansions",  "short": "E", "type":"Reds", "hide":True, "style":None},
                     "hist": {"title":"History", "short": "H", "type":"Reds", "hide":True, "style":None},
                     "log": {"title":"Log", "short": "Log", "type":"Text", "hide": True, "style": wx.TE_READONLY|wx.TE_MULTILINE}
                     }
        self.tabs_keys = ["rows", 0, 1, "reds", "exp", "hist", "log"]
        self.selectedTab = self.tabs[self.tabs_keys[0]]
        stn = "reds"

        self.logger = Log()

        tmp = wx.DisplaySize()
        self.toolFrame = wx.Frame(None, -1, self.titleTool, size=(tmp[0]*0.66,tmp[1]*0.9))
        self.toolFrame.Bind(wx.EVT_CLOSE, self.OnQuit)
        
        self.view_ids = {}
        self.selectedViewX = -1
        self.buffer_copy = None
        
        self.call_check = None
        
        self.create_tool_panel()
        self.changePage(stn)

        # #### COMMENT OUT TO LOAD DBLP ON STARTUP
        # tmp_num_filename='../data/dblp/coauthor_picked.datnum'
        # tmp_bool_filename='../data/dblp/conference_picked.datnum'
        # tmp_coo_filename='../data/dblp/coordinates_rand.names'
        # tmp_redescriptions_filename='../data/dblp/dblp_picked_real.queries'
        # tmp_settings_filename='../data/dblp/dblp_picked_real.conf'

        # #### COMMENT OUT TO LOAD RAJAPAJA ON STARTUP
        # tmp_num_filename='../rajapaja/worldclim_tp.densenum'
        # tmp_bool_filename='../rajapaja/mammals.datbool'
        # tmp_coo_filename='../rajapaja/coordinates.names'
        # tmp_redescriptions_filename='../rajapaja/rajapaja.queries'
        # tmp_settings_filename='../rajapaja/rajapaja_conf.xml'

        # ### COMMENT OUT TO LOAD US ON STARTUP
        # tmp_num_filename='../data/us/us_politics_funds_cont.densenum'
        # tmp_bool_filename='../data/us/us_socio_eco_cont.densenum'
        # tmp_coo_filename='../data/us/us_coordinates_cont.names'
        # tmp_redescriptions_filename='../data/us/us.queries'
        # tmp_settings_filename='../data/us/us.conf'

        # #### COMMENT OUT TO LOAD SOMETHING ON STARTUP
        # (Almost) all of the above should stay in dw
        self.dw = DataWrapper(self.logger)

        ### About dialog
        self.info =  wx.AboutDialogInfo()
        self.info.SetName(self.name)
        self.info.SetWebSite(self.programURL)
        self.info.SetCopyright(self.cpyright)
        self.info.SetVersion(self.version)
        self.info.SetIcon(wx.Icon(self.icon_file, wx.BITMAP_TYPE_PNG))
        with open(self.about_file) as f:
            self.info.SetDescription(f.read())
        #with open(self.licence_file) as f:
        #    self.info.SetLicence(f.read())

        # init helpFrame
        self.helpFrame = None
        
        ## Register file reading message functions to DataWrapper
        self.dw.registerStartReadingFileCallback(self.startFileActionMsg)
        self.dw.registerStopReadingFileCallback(self.stopFileActionMsg)
        self.readingFileDlg = None

        ## Comment (out) to toggle between loading data in input and not
        #self.dw.importDataFromMulFiles([tmp_bool_filename, tmp_num_filename], None, tmp_coo_filename)
        #self.dw.importRedescriptionsTXTFromFile(tmp_redescriptions_filename)
        #self.dw.importPreferencesFromFile(tmp_settings_filename)

 
        ### INITIALISATION OF DATA
        self.resetLogger()
        self.resetConstraints()
        self.resetCoordinates()
        self.reloadAll()

        ### W/O THIS DW THINK IT'S CHANGED!
        self.dw.isChanged = False

    def getReds(self):
        if self.dw is not None:
            return self.dw.getReds()
        return []
    def getData(self):
        if self.dw is not None:
            return self.dw.getData()
    def getPreferences(self):
        if self.dw is not None:
            return self.dw.getPreferences()
    def getLogger(self):
        return self.logger
        
######################################################################
###########     TOOL PANEL
######################################################################
## main panel, contains GridTables for the variables and redescriptions plus settings, log, etc.
        
    def create_tool_panel(self):
        """ Creates the main panel with all the controls on it:
             * mpl canvas 
             * mpl navigation toolbar
             * Control panel for interaction
        """
        self.makeStatus(self.toolFrame)
        self.doUpdates()
	self.tabbed = wx.Notebook(self.toolFrame, -1, style=(wx.NB_TOP)) #, size=(3600, 1200))

        #### Draw tabs
        for tab_id in self.tabs_keys:
            if self.tabs[tab_id]["type"] == "Reds":
                self.tabs[tab_id]["tab"] = RedTable(self, tab_id, self.tabbed, self.tabs[tab_id]["short"])
                if self.tabs[tab_id]["hide"]:
                    self.tabs[tab_id]["tab"].grid.Hide()
                self.tabbed.AddPage(self.tabs[tab_id]["tab"].grid, self.tabs[tab_id]["title"])

            elif self.tabs[tab_id]["type"] == "Var":
                self.tabs[tab_id]["tab"] = VarTable(self, tab_id, self.tabbed, self.tabs[tab_id]["short"])
                if self.tabs[tab_id]["hide"]:
                    self.tabs[tab_id]["tab"].grid.Hide()
                self.tabbed.AddPage(self.tabs[tab_id]["tab"].grid, self.tabs[tab_id]["title"])

            elif self.tabs[tab_id]["type"] == "Row":
                self.tabs[tab_id]["tab"] = RowTable(self, tab_id, self.tabbed, self.tabs[tab_id]["short"])
                if self.tabs[tab_id]["hide"]:
                    self.tabs[tab_id]["tab"].grid.Hide()
                self.tabbed.AddPage(self.tabs[tab_id]["tab"].grid, self.tabs[tab_id]["title"])

            elif self.tabs[tab_id]["type"] == "Text":
                self.tabs[tab_id]["tab"] = wx.Panel(self.tabbed, -1)
                self.tabs[tab_id]["text"] = wx.TextCtrl(self.tabs[tab_id]["tab"], size=(-1,-1), style=self.tabs[tab_id]["style"])
                if self.tabs[tab_id]["hide"]:
                    self.tabs[tab_id]["tab"].Hide()
                self.tabbed.AddPage(self.tabs[tab_id]["tab"], self.tabs[tab_id]["title"])
                boxS = wx.BoxSizer(wx.VERTICAL)
                boxS.Add(self.tabs[tab_id]["text"], 1, wx.ALIGN_CENTER | wx.TOP | wx.EXPAND)
                self.tabs[tab_id]["tab"].SetSizer(boxS)

        self.toolFrame.Bind(wx.EVT_NOTEBOOK_PAGE_CHANGED, self.OnPageChanged)        
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


######################################################################
###########     MENUS
######################################################################


    def updateProgressBar(self):
        if self.plant is None:
            work_estimate, work_progress = (0, 0)
        else:
            work_estimate, work_progress = self.plant.getWorkEstimate()
        if work_estimate > 0:
            self.progress_bar.SetRange(work_estimate)
            self.progress_bar.SetValue(work_progress)
            self.progress_bar.Show()
        else:
            self.progress_bar.SetRange(1)
            self.progress_bar.SetValue(0)
            self.progress_bar.Hide()

    def makePopupMenu(self, frame):
        """
        Create and display a popup menu on right-click event
        """
        if self.selectedTab["type"] == ["Text"]:
            return
        # Popup the menu.  If an item is selected then its handler
        # will be called before PopupMenu returns.
        ct = 0
        menuCon = self.makeConSMenu(frame)
        if menuCon.GetMenuItemCount() > ct:
            ct = menuCon.GetMenuItemCount()
            menuCon.AppendSeparator()
        self.makeRedMenu(frame, menuCon)
        if menuCon.GetMenuItemCount() > ct:
            ct = menuCon.GetMenuItemCount()
            menuCon.AppendSeparator()
        # menuCon.AppendMenu(wx.NewId(), "&View", self.makeVizMenu(frame))
        self.makeVizMenu(frame, menuCon)

        frame.PopupMenu(menuCon)
        menuCon.Destroy()

    def makeConSMenu(self, frame, menuCon=None):
        if menuCon is None:
            menuCon = wx.Menu()
        if self.selectedTab["type"] in ["Row"]:
            
            ID_FOC = wx.NewId()
            m_foc = menuCon.Append(ID_FOC, "Expand/Shrink column", "Expand/Shrink current column.")
            frame.Bind(wx.EVT_MENU, self.OnFlipExCol, m_foc)

        return menuCon

    def makeRedMenu(self, frame, menuRed=None):
        ### Todo checks for cut, paste, etc
        if menuRed is None:
            menuRed = wx.Menu()
        
        if self.selectedTab["type"] in ["Var","Reds", "Row"]:
            if "tab" in self.selectedTab and self.selectedTab["tab"].GetNumberRows() > 0:

                if self.selectedTab["type"] in ["Reds", "Var"]:
                    ID_DETAILS = wx.NewId()
                    m_details = menuRed.Append(ID_DETAILS, "View details", "View variable values.")
                    frame.Bind(wx.EVT_MENU, self.OnShowCol, m_details)

                if self.selectedTab["type"] in ["Row"]:
                    ID_HIGH = wx.NewId()
                    m_high = menuRed.Append(ID_HIGH, "Highlight in views", "Highlight the entity in all opened views.")
                    frame.Bind(wx.EVT_MENU, self.OnHigh, m_high)

                if self.selectedTab["type"] in ["Row", "Var", "Reds"]:
                    ID_FIND = wx.NewId()
                    m_find = menuRed.Append(ID_FIND, "Find\tCtrl+F", "Find by name.")
                    frame.Bind(wx.EVT_MENU, self.OnFind, m_find)

                    
                ID_ENABLED = wx.NewId()
                m_enabled = menuRed.Append(ID_ENABLED, "En&able/Disable\tCtrl+D", "Enable/Disable current item.")
                frame.Bind(wx.EVT_MENU, self.OnFlipEnabled, m_enabled)

                ID_ENABLEDALL = wx.NewId()
                m_enabledall = menuRed.Append(ID_ENABLEDALL, "&Enable All", "Enable all items.")
                frame.Bind(wx.EVT_MENU, self.OnEnabledAll, m_enabledall)

                ID_DISABLEDALL = wx.NewId()
                m_disabledall = menuRed.Append(ID_DISABLEDALL, "&Disable All", "Disable all items.")
                frame.Bind(wx.EVT_MENU, self.OnDisabledAll, m_disabledall)

        if self.selectedTab["type"] == "Reds":
            if "tab" in self.selectedTab and self.selectedTab["tab"].GetNumberRows() > 0:
                ID_EXPAND = wx.NewId()
                m_expand = menuRed.Append(ID_EXPAND, "E&xpand\tCtrl+E", "Expand redescription.")
                frame.Bind(wx.EVT_MENU, self.OnExpand, m_expand)

                ID_FILTER_ONE = wx.NewId()
                m_filter_one = menuRed.Append(ID_FILTER_ONE, "&Filter redundant to current\tCtrl+R", "Disable redescriptions redundant to current downwards.")
                frame.Bind(wx.EVT_MENU, self.OnFilterToOne, m_filter_one)

                ID_FILTER_ALL = wx.NewId()
                m_filter_all = menuRed.Append(ID_FILTER_ALL, "Filter red&undant\tShift+Ctrl+R", "Disable redescriptions redundant to previous encountered.")
                frame.Bind(wx.EVT_MENU, self.OnFilterAll, m_filter_all)

                ID_PROCESS = wx.NewId()
                m_process = menuRed.Append(ID_PROCESS, "&Process redescriptions\tCtrl+P", "Sort and filter current redescription list.")
                frame.Bind(wx.EVT_MENU, self.OnProcessAll, m_process)

                ID_DELDISABLED = wx.NewId()
                m_deldisabled = menuRed.Append(ID_DELDISABLED, "De&lete Disabled", "Delete all disabled redescriptions.")
                frame.Bind(wx.EVT_MENU, self.OnDeleteDisabled, m_deldisabled)

                if self.selectedTab["title"] == "Expansions":
                    ID_MOVEREDS = wx.NewId()
                    m_movereds = menuRed.Append(ID_MOVEREDS, "A&ppend Enabled to Redescriptions", "Move all enabled redescriptions to main Redescriptions tab.")
                    frame.Bind(wx.EVT_MENU, self.OnMoveReds, m_movereds)

                ID_DUP = wx.NewId()
                m_dup = menuRed.Append(ID_DUP, "&Duplicate", "Duplicate current redescription.")
                frame.Bind(wx.EVT_MENU, self.OnDuplicate, m_dup)

                m_cut = menuRed.Append(wx.ID_CUT, "Cu&t", "Cut current redescription.")
                frame.Bind(wx.EVT_MENU, self.OnCut, m_cut)

                m_copy = menuRed.Append(wx.ID_COPY, "&Copy", "Copy current redescription.")
                frame.Bind(wx.EVT_MENU, self.OnCopy, m_copy)

            if self.buffer_copy is not None:
                m_paste = menuRed.Append(wx.ID_PASTE, "&Paste", "Paste current redescription.")
                frame.Bind(wx.EVT_MENU, self.OnPaste, m_paste)

        if menuRed.GetMenuItemCount() == 0:
            ID_NOR = wx.NewId()
            m_nor = menuRed.Append(ID_NOR, "No items", "There are no items to edit.")
            menuRed.Enable(ID_NOR, False)

        return menuRed

    def makeVizMenu(self, frame, menuViz=None):
        if menuViz is None:
            menuViz = wx.Menu()
        if self.selectedTab["type"] in ["Var","Reds", "Row"]:
            if "tab" in self.selectedTab and self.selectedTab["tab"].GetNumberRows() > 0:
                for item in ViewFactory.getViewsInfo(self.dw.isGeospatial(), self.selectedTab["type"]):
                    ID_NEWV = wx.NewId()
                    m_newv = menuViz.Append(ID_NEWV, "%s" % item["title"],
                                              "Plot %s in new window." % item["title"])
                    frame.Bind(wx.EVT_MENU, self.OnNewV, m_newv)
                    self.ids_viewT[ID_NEWV] = item["viewT"]
        return menuViz

    def makeProcessMenu(self, frame, menuPro=None):
        if menuPro is None:
            menuPro = wx.Menu()
        ID_MINE = wx.NewId()
        m_mine = menuPro.Append(ID_MINE, "&Mine redescriptions\tCtrl+M", "Mine redescriptions from the dataset according to current constraints.")
        if self.getData() is None:
            menuPro.Enable(ID_MINE, False)
        else:
            frame.Bind(wx.EVT_MENU, self.OnMineAll, m_mine)

        ct = menuPro.GetMenuItemCount()
        menuPro = self.makeStoppersMenu(frame, menuPro)
        if ct < menuPro.GetMenuItemCount():
            menuPro.InsertSeparator(ct)
        return menuPro

    def makeStoppersMenu(self, frame, menuStop=None):
        if menuStop is None:
            menuStop = wx.Menu()
        if self.plant is None or self.plant.nbWorkers() == 0:
            ID_NOP = wx.NewId()
            m_nop = menuStop.Append(ID_NOP, "No process running", "There is no process currently running.")
            menuStop.Enable(ID_NOP, False)

        else:
            for wdt in self.plant.getWorkersDetails(): 
                ID_STOP = wx.NewId()
                self.ids_stoppers[ID_STOP] = wdt["wid"] 
                m_stop = menuStop.Append(ID_STOP, "Stop %s #&%s" % (wdt["wtyp"], wdt["wid"]), "Interrupt %s process #%s." % (wdt["wtyp"], wdt["wid"]))
                frame.Bind(wx.EVT_MENU, self.OnStop, m_stop)
        if self.plant is not None:
            menuStop.AppendSeparator()
            ID_PLT = wx.NewId()
            m_plt = menuStop.Append(ID_PLT, self.plant.infoStr(), "Where processes are handled.")
            menuStop.Enable(ID_PLT, False)

        return menuStop

    def makeViewsMenu(self, frame, menuViews=None):
        if menuViews is None:
            menuViews = wx.Menu()

        menuViews.AppendMenu(wx.NewId(), "&Tabs",self.makeTabsMenu(frame))

        for vid, desc in sorted([(vid, view.getShortDesc()) for (vid, view) in self.view_ids.items()], key=lambda x: x[1]):
            ID_VIEW = wx.NewId()
            self.opened_views[ID_VIEW] = vid 
            m_view = menuViews.Append(ID_VIEW, "%s" % desc, "Bring view %s on top." % desc)
            frame.Bind(wx.EVT_MENU, self.OnViewTop, m_view)

        if len(self.view_ids) == 0:
            ID_NOP = wx.NewId()
            m_nop = menuViews.Append(ID_NOP, "No view opened", "There is no view currently opened.")
            menuViews.Enable(ID_NOP, False)
        else:
            menuViews.AppendSeparator()
            ID_VIEW = wx.NewId()
            m_view = menuViews.Append(ID_VIEW, "Close all views", "Close all views.")
            frame.Bind(wx.EVT_MENU, self.OnCloseViews, m_view)
        return menuViews

    def makeTabsMenu(self, frame, menuTabs=None):
        if menuTabs is None:
            menuTabs = wx.Menu()

        for tab_id in self.tabs_keys:
            tab_prop = self.tabs[tab_id]
            ID_CHECK = wx.NewId()
            self.check_tab[ID_CHECK] = tab_id 
            m_check = menuTabs.AppendCheckItem(ID_CHECK, "%s" % tab_prop["title"], "Show %s." % tab_prop["title"])
            frame.Bind(wx.EVT_MENU, self.OnTabW, m_check)
            if tab_prop["hide"] == False:
                m_check.Check()
        return menuTabs

    def makeFileMenu(self, frame, menuFile=None):
        if menuFile is None:
            menuFile = wx.Menu()
        m_open = menuFile.Append(wx.ID_OPEN, "&Open\tCtrl+O", "Open a project.")
        frame.Bind(wx.EVT_MENU, self.OnOpen, m_open)
        
        m_save = menuFile.Append(wx.ID_SAVE, "&Save\tCtrl+S", "Save the current project.")
        if self.getData() is not None and self.dw.isFromPackage and self.dw.package_filename is not None:
            frame.Bind(wx.EVT_MENU, self.OnSave, m_save)
        else:
            menuFile.Enable(wx.ID_SAVE, False)
        
        m_saveas = menuFile.Append(wx.ID_SAVEAS, "Save &As...\tShift+Ctrl+S", "Save the current project as...")
        if self.getData() is None:
            menuFile.Enable(wx.ID_SAVEAS, False)
        else:
            frame.Bind(wx.EVT_MENU, self.OnSaveAs, m_saveas)

        submenuImport = wx.Menu()
        #submenuImportData = wx.Menu()
        ID_IMPORT_DATA_CSV = wx.NewId()
        m_impDataCSV = submenuImport.Append(ID_IMPORT_DATA_CSV, "Import Data from CSV files", "Import data in CSV format.")
        frame.Bind(wx.EVT_MENU, self.OnImportDataCSV, m_impDataCSV)
        ID_IMPORT_DATA_XML = wx.NewId()
        m_impDataXML = submenuImport.Append(ID_IMPORT_DATA_XML, "Import Data from XML", "Import data in XML format.")
        frame.Bind(wx.EVT_MENU, self.OnImportDataXML, m_impDataXML)
        ID_IMPORT_DATA_TRIPLE = wx.NewId()
        m_impDataTriple = submenuImport.Append(ID_IMPORT_DATA_TRIPLE, "Import Data from separate files", "Import data from separate files")
        frame.Bind(wx.EVT_MENU, self.OnImportData, m_impDataTriple)
        
        # ID_IMPORT_DATA = wx.NewId()
        # m_impData = submenuImport.AppendMenu(ID_IMPORT_DATA, "Import &Data", submenuImportData)
        #m_impData = submenuImport.Append(ID_IMPORT_DATA, "Import &Data", "Import data into the project.")
        #frame.Bind(wx.EVT_MENU, self.OnImportData, m_impData)

        ID_IMPORT_REDESCRIPTIONS = wx.NewId()
        m_impRedescriptions = submenuImport.Append(ID_IMPORT_REDESCRIPTIONS, "Import &Redescriptions", "Import redescriptions into the project.")
        if self.getData() is not None:
            frame.Bind(wx.EVT_MENU, self.OnImportRedescriptions, m_impRedescriptions)
        else:
            submenuImport.Enable(ID_IMPORT_REDESCRIPTIONS, False)


        ID_IMPORT_PREFERENCES = wx.NewId()
        m_impPreferences = submenuImport.Append(ID_IMPORT_PREFERENCES, "Import &Preferences", "Import preferences into the project.")
        frame.Bind(wx.EVT_MENU, self.OnImportPreferences, m_impPreferences)

        ID_IMPORT = wx.NewId()
        m_import = menuFile.AppendMenu(ID_IMPORT, "&Import", submenuImport)

        ID_EXPORT = wx.NewId()
        m_export = menuFile.Append(ID_EXPORT, "&Export Redescriptions\tShift+Ctrl+E", "Export redescriptions.")
        if len(self.getReds()) == 0:
            menuFile.Enable(ID_EXPORT, False)
        else:
            frame.Bind(wx.EVT_MENU, self.OnExportRedescriptions, m_export)

        m_preferencesdia = menuFile.Append(wx.ID_PREFERENCES, "P&references...\tCtrl+,", "Set preferences.")
        frame.Bind(wx.EVT_MENU, self.OnPreferencesDialog, m_preferencesdia)

        m_quit = menuFile.Append(wx.ID_EXIT, "&Quit", "Close window and quit program.")
        frame.Bind(wx.EVT_MENU, self.OnQuit, m_quit)
        return menuFile

    def makeHelpMenu(self, frame, menuHelp=None):
        if menuHelp is None:
            menuHelp = wx.Menu()
        m_help = menuHelp.Append(wx.ID_HELP, "C&ontent", "Access the instructions.")
        frame.Bind(wx.EVT_MENU, self.OnHelp, m_help)
        
        m_about = menuHelp.Append(wx.ID_ABOUT, "&About", "About...")
        frame.Bind(wx.EVT_MENU, self.OnAbout, m_about)

        ID_LICENSE = wx.NewId()
        m_license = menuHelp.Append(ID_LICENSE, "&License", "View the license(s).")
        frame.Bind(wx.EVT_MENU, self.OnLicense, m_license)
        return menuHelp

    def makeMenu(self, frame):
        menuBar = wx.MenuBar()
        menuBar.Append(self.makeFileMenu(frame), "&File")
        menuBar.Append(self.makeRedMenu(frame), "&Edit")
        menuBar.Append(self.makeVizMenu(frame), "&View")
        menuBar.Append(self.makeProcessMenu(frame), "&Process")
        menuBar.Append(self.makeViewsMenu(frame), "&Windows")
        menuBar.Append(self.makeHelpMenu(frame), "&Help")
        frame.SetMenuBar(menuBar)
        frame.Layout()
        frame.SendSizeEvent()

    def updateMenus(self):
        self.opened_views = {}
        self.ids_viewT = {}
        self.ids_stoppers = {}
        self.check_tab = {}
        self.makeMenu(self.toolFrame)
        for vid, view in self.view_ids.items():
            view.makeMenu()

######################################################################
###########     MAP VIEWS
######################################################################

    def getDefaultViewT(self, tabId=None):
        if tabId is not None and tabId in self.tabs:
            return ViewFactory.getDefaultViewT(geo=self.dw.isGeospatial(), type_tab=self.tabs[tabId]["type"])
        else:
            return ViewFactory.getDefaultViewT(geo=self.dw.isGeospatial())

    def accessViewX(self, mid):
        if mid in self.view_ids:
            return self.view_ids[mid]

    def getViewX(self, vid=None, viewT=None):
        if viewT is None:
            viewT = self.getDefaultViewT()
            
        if (viewT, vid) not in self.view_ids:
            view = ViewFactory.getView(viewT, self, wx.NewId())
            if view is None:
                return
            self.selectedViewX = view.getId()
            self.view_ids[self.selectedViewX] = view
        else:
            self.selectedViewX = (viewT, vid)
        self.view_ids[self.selectedViewX].toTop()
        return self.view_ids[self.selectedViewX]

    def deleteView(self, vK):
        if vK in self.view_ids:
            self.plant.layOff(self.plant.findWid([("wtyp", "project"), ("vid", vK)]))
            self.view_ids[vK].mapFrame.Destroy()
            del self.view_ids[vK]

    def deleteAllViews(self):
        self.selectedViewX = -1
        for vK in self.view_ids.keys():
            self.view_ids[vK].OnQuit(None, upMenu=False)
        self.view_ids = {}
        self.updateMenus()
        

######################################################################
###########     ACTIONS
######################################################################

    def OnOpen(self, event):
        if not self.checkAndProceedWithUnsavedChanges():
                return

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
            self.LoadFile(path)
        open_dlg.Destroy()
        # DEBUGGING
        #wx.MessageDialog(self.toolFrame, 'Opened package from '+path).ShowModal()

    def LoadFile(self, path):
        try:
            self.dw.openPackage(path)
        except:
            return False
        else:
            self.reloadAll()
            return True

    def expand(self, params={}):
        if params is None:
            params = {}
        self.progress_bar.Show()
        if "red" in params and params["red"] is not None and params["red"].length(0) + params["red"].length(1) > 0:
            self.plant.addWorker("expander", self, params,
                                 {"results_track":0,
                                  "batch_type": "partial",
                                  "results_tab": "exp"})
        else:
            self.plant.addWorker("miner", self, params,
                                 {"results_track":0,
                                  "batch_type": "final",
                                  "results_tab": "exp"})
        self.checkResults(menu=True)

    def project(self, proj=None, vid=None):
        self.progress_bar.Show()
        if proj is not None and vid is not None:
            wid = self.plant.findWid([("wtyp", "projector"), ("vid", vid)])
            if wid is None:
                self.plant.addWorker("projector", self, proj,
                                     {"vid": vid})
                self.checkResults(menu=True)

    def checkResults(self, menu=False):
        updates = self.plant.checkResults(self)
        if menu:
            updates["menu"] = True
        if self.plant.nbWorking() > 0:
            if self.call_check is None:
                self.call_check = wx.CallLater(Siren.results_delay, self.checkResults)
            else:
                self.call_check.Restart(Siren.results_delay)
        else:
            self.call_check = None
        self.doUpdates(updates) ## To update the worker stoppers

    def doUpdates(self, updates=None):
        if updates is None:
            updates={"menu":True }
        if "error" in updates:
            self.errorBox(updates["error"])
        if "menu" in updates:
            self.updateMenus()
        if "progress" in updates:
            self.updateProgressBar()
        if "status" in updates:
            self.statusbar.SetStatusText(updates["status"], 0)
        if "log" in updates:
            self.tabs["log"]["text"].AppendText(updates["log"])

    def OnStop(self, event):
        if event.GetId() in self.ids_stoppers:
            self.plant.layOff(self.ids_stoppers[event.GetId()])
            self.checkResults(menu=True)

    def OnViewTop(self, event):
        if event.GetId() in self.opened_views and \
               self.opened_views[event.GetId()] in self.view_ids:
            self.view_ids[self.opened_views[event.GetId()]].toTop()

    def OnCloseViews(self, event):
        view_keys = self.view_ids.keys()
        for key in view_keys:
            self.view_ids[key].OnQuit()
        self.toTop()
            
    def OnSave(self, event):
        if not (self.dw.isFromPackage and self.dw.package_filename is not None):
            wx.MessageDialog(self.toolFrame, 'Cannot save data that is not from a package\nUse Save As... instead', style=wx.OK|wx.ICON_EXCLAMATION, caption='Error').ShowModal()
            return
        try:
            self.dw.savePackage()
        except:
            pass
            
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
            except:
                pass
        save_dlg.Destroy()

    def quitFind(self):
        if self.findDlg is not None:
            self.findDlg = None

    def OnFind(self, event):
        """Shows a custom dialog to open the three data files"""
        if self.findDlg is None:
            self.findDlg = FindDialog(self, self.selectedTab["tab"].getNamesList(), self.selectedTab["tab"].updateFind)
            self.findDlg.showDialog()
        else:
            self.findDlg.doNext()

    # def OnFindNext(self, event):
    #     """Shows a custom dialog to open the three data files"""
    #     self.selectedTab["tab"].updateFind()

    def OnImportData(self, event):
        """Shows a custom dialog to open the three data files"""
        if self.dw.data is not None:
            if not self.checkAndProceedWithUnsavedChanges():
                return
        if len(self.dw.reds) > 0:
            sure_dlg = wx.MessageDialog(self.toolFrame, 'Importing new data erases old redescriptions.\nDo you want to continue?', caption="Warning!", style=wx.OK|wx.CANCEL)
            if sure_dlg.ShowModal() != wx.ID_OK:
                return
            sure_dlg.Destroy()

        dlg = ImportDataDialog(self)
        dlg.showDialog()

    def OnImportDataCSV(self, event):
        """Shows a custom dialog to open the two data files"""
        if self.dw.data is not None:
            if not self.checkAndProceedWithUnsavedChanges():
                return
        if self.dw.reds is not None and len(self.dw.reds) > 0:
            sure_dlg = wx.MessageDialog(self.toolFrame, 'Importing new data erases old redescriptions.\nDo you want to continue?', caption="Warning!", style=wx.OK|wx.CANCEL)
            if sure_dlg.ShowModal() != wx.ID_OK:
                return
            sure_dlg.Destroy()

        dlg = ImportDataCSVDialog(self)
        dlg.showDialog()
            
    def OnImportDataXML(self, event):
        if self.dw.data is not None:
            if not self.checkAndProceedWithUnsavedChanges():
                return
        if self.dw.reds is not None and len(self.dw.reds) > 0:
            sure_dlg = wx.MessageDialog(self.toolFrame, 'Importing new data erases old redescriptions.\nDo you want to continue?', caption="Warning!", style=wx.OK|wx.CANCEL)
            if sure_dlg.ShowModal() != wx.ID_OK:
                return
            sure_dlg.Destroy()

        dir_name = os.path.expanduser('~/')
        open_dlg = wx.FileDialog(self.toolFrame, message="Choose file", defaultDir = dir_name,
                                 style = wx.OPEN|wx.CHANGE_DIR)
        if open_dlg.ShowModal() == wx.ID_OK:
            path = open_dlg.GetPath()
            try:
                self.dw.importDataFromXMLFile(path)
            except:
                pass
            else:
                self.reloadAll()

        open_dlg.Destroy()
                
    def OnImportPreferences(self, event):
        if not self.checkAndProceedWithUnsavedChanges(self.dw.preferences.isChanged):
            return
        dir_name = os.path.expanduser('~/')
        open_dlg = wx.FileDialog(self.toolFrame, message='Choose file', defaultDir = dir_name,
                                 style = wx.OPEN|wx.CHANGE_DIR)
        if open_dlg.ShowModal() == wx.ID_OK:
            path = open_dlg.GetPath()
            try:
                self.dw.importPreferencesFromFile(path)
            except:
                pass
        open_dlg.Destroy()
        
    def OnImportRedescriptions(self, event):
        if self.dw.reds is not None:
            if not self.checkAndProceedWithUnsavedChanges(self.dw.reds.isChanged or self.dw.rshowids.isChanged):
                return
        wcd = 'All files|*|Query files (*.queries)|*.queries|'
        dir_name = os.path.expanduser('~/')

        open_dlg = wx.FileDialog(self.toolFrame, message='Choose file', defaultDir = dir_name,
                                 style = wx.OPEN|wx.CHANGE_DIR)
        if open_dlg.ShowModal() == wx.ID_OK:
            path = open_dlg.GetPath()
            try:
                self.dw.importRedescriptionsFromFile(path)
            except:
                pass
        open_dlg.Destroy()
        self.reloadReds(all=False)
        
    def OnExportRedescriptions(self, event):
        if len(self.getReds()) == 0:
            wx.MessageDialog(self.toolFrame, 'Cannot export redescriptions: no redescriptions loaded',
                             style=wx.OK|wx.ICON_EXCLAMATION, caption='Error').ShowModal()
            return
        
        if self.dw.package_filename is not None:
            dir_name = os.path.dirname(self.dw.package_filename)
        else:
            dir_name = os.path.expanduser('~/')

        save_dlg = wx.FileDialog(self.toolFrame, message='Export redescriptions to:', defaultDir = dir_name, style = wx.SAVE|wx.CHANGE_DIR)
        if save_dlg.ShowModal() == wx.ID_OK:
            path = save_dlg.GetPath()
            try:
                self.dw.exportRedescriptions(path)
            except:
                pass
        save_dlg.Destroy()

    def changePage(self, tabn):
        if tabn in self.tabs and not self.tabs[tabn]["hide"]:
            self.tabbed.ChangeSelection(self.tabs_keys.index(tabn))
            self.OnPageChanged(-1)

    def OnPageChanged(self, event):
        self.quitFind()
        self.selectedTab = self.tabs[self.tabs_keys[self.tabbed.GetSelection()]]
        self.doUpdates()

    def OnNewV(self, event):
        if self.selectedTab["type"] in ["Var", "Reds", "Row"]:
            self.selectedViewX = -1
            self.selectedTab["tab"].viewData(self.ids_viewT[event.GetId()])

    def newRedVHist(self, queries, viewT):
        self.tabs["hist"]["tab"].addAndViewTop(queries, viewT)
        self.showTab("hist")

    def OnExpand(self, event):
        if self.selectedTab["type"] in ["Reds"]:
            self.showTab("exp")
            red = self.selectedTab["tab"].getSelectedItem()
            if red is not None:
                self.expand(red)

    def expandFV(self, params=None):
        self.showTab("exp")
        self.expand(params)

    def OnHigh(self, event):
        if self.selectedTab["type"] in ["Row"]:
            for tab in ["reds", "exp", "hist"]:
                self.tabs[tab]["tab"].setAllEmphasizedR([self.selectedTab["tab"].getSelectedPos()], show_info=False, no_off=True)

    def OnShowCol(self, event):
        shw = False
        if self.selectedTab["type"] in ["Var"]:
            if self.selectedTab["short"] == "LHS":
                self.showCol(0, self.selectedTab["tab"].getSelectedPos())
                shw = True
            elif self.selectedTab["short"] == "RHS":
                self.showCol(1, self.selectedTab["tab"].getSelectedPos())
                shw = True
        elif self.selectedTab["type"] in ["Reds"]:
            row = self.tabs["rows"]["tab"].showRidRed(self.tabs["rows"]["tab"].getSelectedRow(), self.selectedTab["tab"].getSelectedItem())
            shw = True
        if shw:
            self.showTab("rows")

    def OnMineAll(self, event):
        self.showTab("exp")
        self.expand()

    def OnFilterToOne(self, event):
        if self.selectedTab["type"] in ["Reds"]:
            self.selectedTab["tab"].filterToOne(self.constraints.parameters_filterredundant())

    def OnFilterAll(self, event):
        if self.selectedTab["type"] in ["Reds"]:
            self.selectedTab["tab"].filterAll(self.constraints.parameters_filterredundant())

    def OnProcessAll(self, event):
        if self.selectedTab["type"] in ["Reds"]:
            self.selectedTab["tab"].processAll(self.constraints.actions_final(), True)

    def OnFlipExCol(self, event):
        if self.selectedTab["type"] in ["Row"]:
            self.selectedTab["tab"].flipFocusCol(self.selectedTab["tab"].getSelectedCol())

    def OnFlipEnabled(self, event):
        if self.selectedTab["type"] in ["Var", "Reds", "Row"]:
            self.selectedTab["tab"].flipEnabled(self.selectedTab["tab"].getSelectedRow())

    def OnEnabledAll(self, event):
        if self.selectedTab["type"] in ["Var", "Reds", "Row"]:
            self.selectedTab["tab"].setAllEnabled()

    def OnDisabledAll(self, event):
        if self.selectedTab["type"] in ["Var", "Reds", "Row"]:
            self.selectedTab["tab"].setAllDisabled()

    def OnDeleteDisabled(self, event):
        if self.selectedTab["type"] in ["Reds"]:
            self.selectedTab["tab"].deleteDisabled()

    def OnMoveReds(self, event):
        self.tabs["exp"]["tab"].moveEnabled(self.tabs["reds"]["tab"])

    def OnCut(self, event):
        if self.selectedTab["type"] in ["Reds"]:
            self.selectedTab["tab"].cutItem(self.selectedTab["tab"].getSelectedRow())
            self.doUpdates({"menu":True}) ### update paste entry

    def OnCopy(self, event):
        if self.selectedTab["type"] in ["Reds"]:
            self.selectedTab["tab"].copyItem(self.selectedTab["tab"].getSelectedRow())
            self.doUpdates({"menu":True}) ### update paste entry

    def OnPaste(self, event):
        if self.selectedTab["type"] in ["Reds"]:
            self.selectedTab["tab"].pasteItem(self.selectedTab["tab"].getSelectedRow())
            self.doUpdates({"menu":True}) ### update paste entry

    def OnDuplicate(self, event):
        if self.selectedTab["type"] in ["Reds"]:
            self.selectedTab["tab"].copyItem(self.selectedTab["tab"].getSelectedRow())
            self.selectedTab["tab"].pasteItem(self.selectedTab["tab"].getSelectedRow())
            self.doUpdates({"menu":True}) ### update paste entry

    def flipRowsEnabled(self, rids):
        if "rows" in self.tabs and len(rids)> 0:
            self.tabs["rows"]["tab"].flipAllEnabled(rids)

    def recomputeAll(self):
        restrict = self.dw.data.nonselectedRows()
        for tab in self.tabs.values():
            if tab["type"] == "Reds":
                tab["tab"].recomputeAll(restrict)
            
    def OnTabW(self, event):
        if event.GetId() in self.check_tab:
            tab_id = self.check_tab[event.GetId()]
            if self.toolFrame.FindFocus() is not None and self.toolFrame.FindFocus().GetGrandParent() is not None \
                   and self.toolFrame.FindFocus().GetGrandParent().GetParent() == self.toolFrame:
                if not event.IsChecked():
                    self.hideTab(tab_id)
                    return
            else: self.toTop()
            self.showTab(tab_id)

    def showTab(self, tab_id):
        self.tabs[tab_id]["hide"] = False
        self.tabs[tab_id]["tab"].Show()
        self.changePage(tab_id)

    def hideTab(self, tab_id):
        self.tabs[tab_id]["hide"] = True
        self.tabs[tab_id]["tab"].Hide()

    def toTop(self):
        self.toolFrame.Raise()
        self.toolFrame.SetFocus()

    def OnPreferencesDialog(self, event):
        d = PreferencesDialog(self.toolFrame, self.dw)
        d.ShowModal()
        d.Destroy()

    def OnHelp(self, event):
        wxVer = map(int, wx.__version__.split('.'))
        new_ver = wxVer[0] > 2 or (wxVer[0] == 2 and wxVer[1] > 9) or (wxVer[0] == 2 and wxVer[1] == 9 and wxVer[2] >= 3)
        if new_ver:
            try:                                                      
                self._onHelpHTML2()
            except NotImplementedError:
                new_ver = False
        if not new_ver:
            self._onHelpOldSystem()

    def _onHelpHTML2(self):
        import wx.html2
        if self.helpURL is None:
            self._onHelpOldSystem()
            return
        if self.helpFrame is None:
            self.helpFrame = wx.Frame(self.toolFrame, -1, self.titleHelp)
            self.helpFrame.Bind(wx.EVT_CLOSE, self._helpHTML2Close)
            sizer = wx.BoxSizer(wx.VERTICAL)
            browser = wx.html2.WebView.New(self.helpFrame)
            browser.LoadURL('file://'+os.path.abspath(self.helpURL))
            sizer.Add(browser, 1, wx.EXPAND, 10)
            self.helpFrame.SetSizer(sizer)
            self.helpFrame.SetSize((900, 700))
        self.helpFrame.Show()
        self.helpFrame.Raise()

    def _helpHTML2Close(self, event):
        self.helpFrame.Destroy()
        self.helpFrame = None

    def _onHelpOldSystem(self):
        import webbrowser
        try:
            ##webbrowser.open("file://"+ self.helpURL, new=1, autoraise=True)
            webbrowser.open(self.helpInternetURL, new=1, autoraise=True)
        except webbrowser.Error as e:
            self.logger.printL(1,'Cannot show help file: '+str(e)
                                   +'\nYou can find help at '+self.helpInternetURL+'\nor '+self.helpURL, "error", "help")        

    def OnAbout(self, event):
        wx.AboutBox(self.info)        

    def showCol(self, side, col):
        self.tabs["rows"]["tab"].showCol(side, col)
            
    def showDetailsBox(self, rid, red):
        row = self.tabs["rows"]["tab"].showRidRed(rid, red)
        if row is not None:
            self.showTab("rows")
        else:
            dlg = wx.MessageDialog(self.toolFrame,
                                   self.prepareDetails(rid, red),"Point Details", wx.OK|wx.ICON_INFORMATION)
            result = dlg.ShowModal()
            dlg.Destroy()

    def prepareDetails(self, rid, red):
        dets = "%d:\n" % rid 
        for side,pref in [(0,""), (1,"")]:
            dets += "\n"
            for lit in red.queries[side].listLiterals():
                dets += ("\t%s=\t%s\n" % (self.dw.getData().col(side,lit.col()).getName(), self.dw.getData().getValue(side, lit.col(), rid)))
        return dets

    def OnQuit(self, event):
        if self.plant is not None:
            self.plant.closeDown(self)
        if not self.checkAndProceedWithUnsavedChanges(what="quit"):
                return
        self.deleteAllViews()
        self.toolFrame.Destroy()
        sys.exit()

    def OnLicense(self, event):
        license_text = None
        try:
            f = open(self.license_file)
            license_text = f.read()
        except:
            wx.MessageDialog(self.toolFrame, 'No license found.', style=wx.OK, caption="No license").ShowModal()
            return

        external_license_texts = ''
        for ext in self.external_licenses:
            lic = 'LICENSE_'+ext
            try:
                f = open(findFile(lic, [self.curr_dir]), 'r')
                external_license_texts += '\n\n***********************************\n\n' + f.read()
                f.close()
            except:
                pass # We don't care about errors here

        if len(external_license_texts) > 0:
            license_text += "\n\nSiren comes bundled with other software for your convinience.\nThe licenses for this bundled software are below." + external_license_texts

        # Show dialog
        dlg = wx.lib.dialogs.ScrolledMessageDialog(self.toolFrame, license_text, "LICENSE")
        dlg.ShowModal()
        dlg.Destroy()
         

    def checkAndProceedWithUnsavedChanges(self, test=None, what="continue"):
        """Checks for unsaved changes and returns False if they exist and user doesn't want to continue
        and True if there are no unsaved changes or user wants to proceed in any case.

        If additional parameter 'test' is given, asks the question if it is true."""
        if (test is not None and test) or (test is None and self.dw.isChanged):
            dlg = wx.MessageDialog(self.toolFrame, 'Unsaved changes might be lost.\nAre you sure you want to %s?' % what, style=wx.YES_NO|wx.NO_DEFAULT|wx.ICON_EXCLAMATION, caption='Unsaved changes!')
            if dlg.ShowModal() == wx.ID_NO:
                return False
        return True

    def resetCoordinates(self):
        self.deleteAllViews()

    def resetConstraints(self):
        self.constraints = Constraints(self.dw.getNbRows(), self.dw.getPreferences())

    def resetLogger(self):
        verb = 1
        if self.dw.getPreferences() is not None and self.dw.getPreference('verbosity') is not None:
            verb = self.dw.getPreference('verbosity')

        self.logger.resetOut()
        if self.plant is not None and self.plant.getOutQueue() is not None:
            self.logger.addOut({"*": verb, "error":1, "progress":2, "result":1}, self.plant.getOutQueue(), self.plant.sendMessage)
        self.logger.addOut({"error":1}, "stderr")

    def reloadAll(self):
        if self.plant is not None:
            self.plant.closeDown(self)
        self.reloadVars(review=False)
        self.reloadRows()
        self.reloadReds()

        self.plant, msg, err = toolCommMultip.getWP(self.dw.getPreference("workserver_ip"), self.dw.getPreference("workserver_port"), self.dw.getPreference("workserver_authkey"))
        self.logger.printL(1, msg, "status", "WP")
        if len(err) > 0:
            self.logger.printL(1, err, "error", "WP")


    def reloadVars(self, review=True):
        ## Initialize variable lists data
        for side in [0,1]:
            if self.dw.data is not None:
                self.tabs[side]["tab"].resetData(self.dw.getDataCols(side))
            else:
                self.tabs[side]["tab"].resetData(ICList())
        if self.dw.data is not None:
            details = {"names": self.dw.data.getNames()}
            for tk, tv in self.tabs.items():
                if tv["type"] == "Reds":
                    tv["tab"].resetDetails(details, review)
                elif tv["type"] == "Row":
                    tv["tab"].resetFields(self.dw, review)

    def reloadRows(self):
        ## Initialize variable lists data
        if self.dw.data is not None:
            self.tabs["rows"]["tab"].resetData(self.dw.getDataRows())
        else:
            self.tabs["rows"]["tab"].resetData(ICList())

            
    def reloadReds(self, all=True):
        ## Initialize red lists data
        self.tabs["reds"]["tab"].resetData(self.dw.getReds(), self.dw.getShowIds())
        if all:
            self.tabs["exp"]["tab"].resetData(Batch())
            self.tabs["hist"]["tab"].resetData(Batch())
        self.deleteAllViews()
        self.doUpdates({"menu":True})

    def startFileActionMsg(self, msg, short_msg=''):
        """Shows a dialog that we're reading a file"""
        self.statusbar.SetStatusText(short_msg, 0)
        self.toolFrame.Enable(False)
        self.busyDlg = wx.BusyInfo(msg, self.toolFrame)
        #self.busyDlg = CBusyDialog.showBox(self.toolFrame, msg, short_msg, None)
        #self.busyDlg = PBI.PyBusyInfo(msg, parent=self.toolFrame, title=short_msg)
        # DEBUG
        # time.sleep(5)
        

    def stopFileActionMsg(self, msg=''):
        """Removes the BusyInfo dialog"""
        if self.busyDlg is not None:
            self.busyDlg.Destroy()
            # del self.busyDlg # Removes the dialog
            self.busyDlg = None
            self.toolFrame.Enable(True)
            self.statusbar.SetStatusText(msg, 0)
        
    def errorBox(self, message):
        if self.busyDlg is not None:
            del self.busyDlg
            self.busyDlg = None
        dlg = wx.MessageDialog(self.toolFrame, message, style=wx.OK|wx.ICON_EXCLAMATION|wx.STAY_ON_TOP, caption="Error")
        dlg.ShowModal()
        dlg.Destroy()

    def readyReds(self, reds, tab):
        if len(reds) > 0 and tab in self.tabs:
            for red in reds:
                red.recompute(self.getData())
                red.setRestrictedSupp(self.getData())
            self.tabs[tab]["tab"].insertItems(reds)

    def readyProj(self, vid, proj):
        if vid in self.view_ids:
            self.view_ids[vid].readyProj(proj)
