import os, os.path
import wx
import threading
import time
import sys
# import wx.lib.agw.pybusyinfo as PBI
import wx.lib.dialogs

from reremi.toolLog import Log
from reremi.classMiner import Miner
from reremi.classData import Data, DataError
from reremi.classConstraints import Constraints
from reremi.classBatch import Batch
from reremi.toolICList import ICList

from classGridTable import VarTable, RedTable
from classMapolyView import MapView
from classParaView import ParaView
from classProjView import ProjView
from DataWrapper import DataWrapper, findFile
from classPreferencesDialog import PreferencesDialog
from miscDialogs import ImportDataDialog, ImportDataCSVDialog

import pdb

# Thread class that executes processing
class WorkerThread(threading.Thread):
    def __init__(self, id, data, preferences, logger, params=None):
        """Init Expander Thread Class."""
        threading.Thread.__init__(self)
        self.miner = Miner(data, preferences, logger, id)
        self.params = params
        self.start()

    def run(self):
        pass

    def abort(self):
        self.miner.kill()

class MinerThread(WorkerThread):
    """Miner Thread Class."""

    def run(self):
        self.miner.full_run()

class ExpanderThread(WorkerThread):
    """Expander Thread Class."""

    def run(self):
        self.miner.part_run(self.params)


class Message(wx.PyEvent):
    TYPES_MESSAGES = {'*': wx.NewId(), 'log': wx.NewId(), 'time': wx.NewId(), 'result': wx.NewId(), 'progress': wx.NewId(), 'status': wx.NewId()}
    
    """Simple event for communication purposes."""
    def __init__(self, type_event, data):
        """Init Result Event."""
        wx.PyEvent.__init__(self)
        self.SetEventType(type_event)
        self.data = data

    def sendMessage(output, message, type_message, source):
        if Message.TYPES_MESSAGES.has_key(type_message):
           wx.PostEvent(output.toolFrame, Message(Message.TYPES_MESSAGES[type_message], (source, message)))
    sendMessage = staticmethod(sendMessage)


class CErrorDialog:

    def showBox(output, message, type_message, source):
        if output.busyDlg is not None:
            del output.busyDlg
            output.busyDlg = None
        dlg = wx.MessageDialog(output.toolFrame, message, style=wx.OK|wx.ICON_EXCLAMATION|wx.STAY_ON_TOP, caption=type_message)
        dlg.ShowModal()
        dlg.Destroy()
    showBox = staticmethod(showBox)


class Siren():
    """ The main frame of the application
    """

    titleTool = 'SIREN :: tools'
    titleMap = 'SIREN :: maps'
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
    
         
    def __init__(self):
        self.busyDlg = None
        self.tabs = {0: {"title":"LHS Variables", "type":"Var", "hide":False, "style":None},
                     1: {"title":"RHS Variables", "type":"Var", "hide":False, "style":None},
                     "reds": {"title":"Redescriptions", "type":"Reds", "hide":False, "style":None},
                     "exp": {"title":"Expansions", "type":"Reds", "hide":True, "style":None},
                     "hist": {"title":"History", "type":"Reds", "hide":True, "style":None},
                     "log": {"title":"Log", "type":"Text", "hide": True, "style": wx.TE_READONLY|wx.TE_MULTILINE}
                     }
        self.tabs_keys = [0, 1, "reds", "exp", "hist", "log"]
        self.selectedTab = self.tabs[self.tabs_keys[0]]
        self.ids_stoppers = {}
        self.check_tab = {}
        self.logger = Log()
        
        self.toolFrame = wx.Frame(None, -1, self.titleTool)
        self.toolFrame.Bind(wx.EVT_CLOSE, self.OnQuit)

        self.toolFrame.Connect(-1, -1, Message.TYPES_MESSAGES['*'], self.OnMessLogger)
        self.toolFrame.Connect(-1, -1, Message.TYPES_MESSAGES['log'], self.OnMessLogger)
        self.toolFrame.Connect(-1, -1, Message.TYPES_MESSAGES['time'], self.OnMessLogger)
        self.toolFrame.Connect(-1, -1, Message.TYPES_MESSAGES['status'], self.OnMessLogger)
        self.toolFrame.Connect(-1, -1, Message.TYPES_MESSAGES['result'], self.OnMessResult)
        self.toolFrame.Connect(-1, -1, Message.TYPES_MESSAGES['progress'], self.OnMessProgress)
        self.toolFrame.Connect(-1, -1, Message.TYPES_MESSAGES['status'], self.OnMessStatus)
        
        self.mapViews = {}
        self.selectedMap = -1
        self.buffer_copy = None
        
        self.details = None
        self.workers = {}
        self.next_workerid = 0

        self.create_tool_panel()

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
        self.details = {'names': self.dw.getColNames()}
        self.reloadVars()
        self.resetCoordinates()
        self.reloadReds()

        ### W/O THIS DW THINK IT'S CHANGED!
        self.dw.isChanged = False

        
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
	self.makeMenu(self.toolFrame)
        self.makeStatus(self.toolFrame)
	self.tabbed = wx.Notebook(self.toolFrame, -1, style=(wx.NB_TOP)) #, size=(3600, 1200))

        #### Draw tabs
        for tab_id in self.tabs_keys:
            if self.tabs[tab_id]["type"] == "Reds":
                self.tabs[tab_id]["tab"] = RedTable(self, tab_id, self.tabbed)
                if self.tabs[tab_id]["hide"]:
                    self.tabs[tab_id]["tab"].grid.Hide()
                self.tabbed.AddPage(self.tabs[tab_id]["tab"].grid, self.tabs[tab_id]["title"])

            elif self.tabs[tab_id]["type"] == "Var":
                self.tabs[tab_id]["tab"] = VarTable(self, tab_id, self.tabbed)
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

    def makeProgressBar(self):
        work_estimate = 0
        work_progress = 0
        for worker in self.workers.values():
            work_estimate += worker["work_estimate"]
            work_progress += worker["work_progress"]
        ### progress should not go over estimate, but well...
        work_progress = min(work_progress, work_estimate)
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
        menuRed = self.makeContextMenu(frame)
        frame.PopupMenu(menuRed)
        menuRed.Destroy()

    def makeContextMenu(self, frame):
        ### Todo checks for cut, paste, etc
        menuRed = wx.Menu()

        ID_MINE = wx.NewId()
        m_mine = menuRed.Append(ID_MINE, "&Mine redescriptions\tCtrl+M", "Mine redescriptions from the dataset according to current constraints.")
        frame.Bind(wx.EVT_MENU, self.OnMineAll, m_mine)
        
        if self.selectedTab["type"] in ["Var","Reds"]:
            if self.selectedTab.has_key("tab") and self.selectedTab["tab"].GetNumberRows() > 0:

                ID_NEWWPC = wx.NewId()
                m_newwpc = menuRed.Append(ID_NEWWPC, "&View para. co. in new window\tCtrl+P", "Plot redescription on parallel coordinates in new window.")
                frame.Bind(wx.EVT_MENU, self.OnNewWPC, m_newwpc)
                
                if self.dw.isGeospatial():
                    ID_NEWWM = wx.NewId()
                    m_newwm = menuRed.Append(ID_NEWWM, "&View map in new window\tCtrl+W", "Plot redescription on a map in new window.")
                    frame.Bind(wx.EVT_MENU, self.OnNewWM, m_newwm)

                ID_NEWWPJ = wx.NewId()
                m_newwpj = menuRed.Append(ID_NEWWPJ, "&View projection in new window\tCtrl+P", "Plot redescription on two-dimension projection in new window.")
                frame.Bind(wx.EVT_MENU, self.OnNewWPJ, m_newwpj)


                ID_ENABLED = wx.NewId()
                m_enabled = menuRed.Append(ID_ENABLED, "En&able/Disable\tCtrl+D", "Enable/Disable current redescription.")
                frame.Bind(wx.EVT_MENU, self.OnFlipEnabled, m_enabled)

                ID_ENABLEDALL = wx.NewId()
                m_enabledall = menuRed.Append(ID_ENABLEDALL, "&Enable All", "Enable all redescriptions.")
                frame.Bind(wx.EVT_MENU, self.OnEnabledAll, m_enabledall)

                ID_DISABLEDALL = wx.NewId()
                m_disabledall = menuRed.Append(ID_DISABLEDALL, "&Disable All", "Disable all redescriptions.")
                frame.Bind(wx.EVT_MENU, self.OnDisabledAll, m_disabledall)


        if self.selectedTab["type"] == "Reds":
            if self.selectedTab.has_key("tab") and self.selectedTab["tab"].GetNumberRows() > 0:
                ID_EXPAND = wx.NewId()
                m_expand = menuRed.Append(ID_EXPAND, "E&xpand\tCtrl+E", "Expand redescription.")
                frame.Bind(wx.EVT_MENU, self.OnExpand, m_expand)

                ID_FILTER_ONE = wx.NewId()
                m_filter_one = menuRed.Append(ID_FILTER_ONE, "&Filter redundant to current\tCtrl+F", "Disable redescriptions redundant to current downwards.")
                frame.Bind(wx.EVT_MENU, self.OnFilterToOne, m_filter_one)

                ID_FILTER_ALL = wx.NewId()
                m_filter_all = menuRed.Append(ID_FILTER_ALL, "Filter red&undant\tShift+Ctrl+F", "Disable redescriptions redundant to previous encountered.")
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

                m_cut = menuRed.Append(wx.ID_CUT, "Cu&t", "Cut current redescription.")
                frame.Bind(wx.EVT_MENU, self.OnCut, m_cut)

                m_copy = menuRed.Append(wx.ID_COPY, "&Copy", "Copy current redescription.")
                frame.Bind(wx.EVT_MENU, self.OnCopy, m_copy)

            if self.buffer_copy is not None:
                m_paste = menuRed.Append(wx.ID_PASTE, "&Paste", "Paste current redescription.")
                frame.Bind(wx.EVT_MENU, self.OnPaste, m_paste)

            ID_DUP = wx.NewId()
            m_dup = menuRed.Append(ID_DUP, "&Duplicate", "Duplicate current redescription.")
            frame.Bind(wx.EVT_MENU, self.OnDuplicate, m_dup)
 
        return menuRed

    def makeStoppersMenu(self, frame):
        menuStoppers = wx.Menu()
        self.ids_stoppers = {}
        if len(self.workers) == 0:
            ID_NOP = wx.NewId()
            m_nop = menuStoppers.Append(ID_NOP, "No process running", "There is no process currently running.")
            menuStoppers.Enable(ID_NOP, False)

        for worker_id in self.workers.keys(): 
            ID_STOP = wx.NewId()
            self.ids_stoppers[ID_STOP] = worker_id 
            m_stop = menuStoppers.Append(ID_STOP, "Stop #&%s" % worker_id, "Interrupt mining process #%s." % worker_id)
            frame.Bind(wx.EVT_MENU, self.OnStop, m_stop)
        return menuStoppers

    def makeTabsViewMenu(self, frame):
        menuView = wx.Menu()

        self.check_tab = {}
        for tab_id in self.tabs_keys:
            tab_prop = self.tabs[tab_id]
            ID_CHECK = wx.NewId()
            self.check_tab[ID_CHECK] = tab_id 
            m_check = menuView.AppendCheckItem(ID_CHECK, "%s" % tab_prop["title"], "Show %s." % tab_prop["title"])
            frame.Bind(wx.EVT_MENU, self.OnTabW, m_check)
            if tab_prop["hide"] == False:
                m_check.Check()
        return menuView


    def makeMenu(self, frame):
        ### menu bar
        
        ### MENU FILE
        menuFile = wx.Menu()
        m_open = menuFile.Append(wx.ID_OPEN, "&Open\tCtrl+O", "Open a project.")
        frame.Bind(wx.EVT_MENU, self.OnOpen, m_open)
        
        m_save = menuFile.Append(wx.ID_SAVE, "&Save\tCtrl+S", "Save the current project.")
        frame.Bind(wx.EVT_MENU, self.OnSave, m_save)
        
        m_saveas = menuFile.Append(wx.ID_SAVEAS, "Save &As...\tShift+Ctrl+S", "Save the current project as...")
        frame.Bind(wx.EVT_MENU, self.OnSaveAs, m_saveas)

        submenuImportData = wx.Menu()
        ID_IMPORT_DATA_CSV = wx.NewId()
        m_impDataCSV = submenuImportData.Append(ID_IMPORT_DATA_CSV, "Import from CSV files", "Import data in CSV format.")
        frame.Bind(wx.EVT_MENU, self.OnImportDataCSV, m_impDataCSV)
        ID_IMPORT_DATA_XML = wx.NewId()
        m_impDataXML = submenuImportData.Append(ID_IMPORT_DATA_XML, "Import from XML", "Import data in XML format.")
        frame.Bind(wx.EVT_MENU, self.OnImportDataXML, m_impDataXML)
        ID_IMPORT_DATA_TRIPLE = wx.NewId()
        m_impDataTriple = submenuImportData.Append(ID_IMPORT_DATA_TRIPLE, "Import from separate files", "Import data from separate files")
        frame.Bind(wx.EVT_MENU, self.OnImportData, m_impDataTriple)
        
        submenuFile = wx.Menu()
        ID_IMPORT_DATA = wx.NewId()
        m_impData = submenuFile.AppendMenu(ID_IMPORT_DATA, "Import &Data", submenuImportData)
        #m_impData = submenuFile.Append(ID_IMPORT_DATA, "Import &Data", "Import data into the project.")
        #frame.Bind(wx.EVT_MENU, self.OnImportData, m_impData)

        ID_IMPORT_REDESCRIPTIONS = wx.NewId()
        m_impRedescriptions = submenuFile.Append(ID_IMPORT_REDESCRIPTIONS, "Import &Redescriptions", "Import redescriptions into the project.")
        frame.Bind(wx.EVT_MENU, self.OnImportRedescriptions, m_impRedescriptions)

        ID_IMPORT_PREFERENCES = wx.NewId()
        m_impPreferences = submenuFile.Append(ID_IMPORT_PREFERENCES, "Import &Preferences", "Import preferences into the project.")
        frame.Bind(wx.EVT_MENU, self.OnImportPreferences, m_impPreferences)

        ID_IMPORT = wx.NewId()
        m_import = menuFile.AppendMenu(ID_IMPORT, "&Import", submenuFile)

        ID_EXPORT = wx.NewId()
        m_export = menuFile.Append(ID_EXPORT, "&Export Redescriptions\tShift+Ctrl+E", "Export redescriptions.")
        frame.Bind(wx.EVT_MENU, self.OnExportRedescriptions, m_export)

        m_quit = menuFile.Append(wx.ID_EXIT, "&Quit", "Close window and quit program.")
        frame.Bind(wx.EVT_MENU, self.OnQuit, m_quit)

        ### MENU RED
        menuRed = self.makeContextMenu(frame)

        #ID_PREFERENCESDIA = wx.NewId()
        m_preferencesdia = menuRed.Append(wx.ID_PREFERENCES, "P&references...\tCtrl+,", "Set preferences.")
        frame.Bind(wx.EVT_MENU, self.OnPreferencesDialog, m_preferencesdia)


        ### MENU STOPPERS
        menuStoppers = self.makeStoppersMenu(frame)

        ### MENU VIEW
        menuView =  self.makeTabsViewMenu(frame)

        ### MENU HELP
        menuHelp = wx.Menu()
        m_help = menuHelp.Append(wx.ID_HELP, "C&ontent", "Access the instructions.")
        frame.Bind(wx.EVT_MENU, self.OnHelp, m_help)
        
        m_about = menuHelp.Append(wx.ID_ABOUT, "&About", "About...")
        frame.Bind(wx.EVT_MENU, self.OnAbout, m_about)

        ID_LICENSE = wx.NewId()
        m_license = menuHelp.Append(ID_LICENSE, "&License", "View the license(s).")
        frame.Bind(wx.EVT_MENU, self.OnLicense, m_license)
        
        ### PUT TOGETHER
        menuBar = wx.MenuBar()
        menuBar.Append(menuFile, "&File")
        menuBar.Append(menuRed, "&Edit")
        menuBar.Append(menuStoppers, "&Process")
        menuBar.Append(menuView, "&View")
        menuBar.Append(menuHelp, "&Help")
        frame.SetMenuBar(menuBar)
        frame.Layout()
        frame.SendSizeEvent()

######################################################################
###########     MAP VIEWS
######################################################################

    def accessMapView(self, mid):
        if self.mapViews.has_key(mid):
            return self.mapViews[mid]

    def getMapView(self, vid=None, viewT=None):
        if viewT is None:
            if self.dw.isGeospatial():
                viewT = MapView.TID
            else:
                viewT = ParaView.TID

        if (viewT, vid) not in self.mapViews.keys():
            vid = wx.NewId()
            self.selectedMap = (viewT, vid)
            if viewT == MapView.TID:
                self.mapViews[self.selectedMap] = MapView(self, vid)
            elif viewT == ProjView.TID:
                self.mapViews[self.selectedMap] = ProjView(self, vid)
            else:
                self.mapViews[self.selectedMap] = ParaView(self, vid)
        else:
            self.selectedMap = (viewT, vid)
        self.mapViews[self.selectedMap].mapFrame.Raise()
        return self.mapViews[self.selectedMap]


    def deleteView(self, vid):
        if vid in self.mapViews.keys():
            self.mapViews[vid].mapFrame.Destroy()
            del self.mapViews[vid]

    def deleteAllViews(self):
        self.selectedMap = -1
        for mapK in self.mapViews.keys():
            self.mapViews[mapK].OnQuit(None)
        self.mapViews = {}
        

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
            self.details = {'names': self.dw.getColNames()}
            self.reloadVars()
            self.reloadReds()
            return True

    def expand(self, red=None):
        self.progress_bar.Show()
        self.next_workerid += 1
        if red != None and red.length(0) + red.length(1) > 0:
            self.workers[self.next_workerid] = {"worker":ExpanderThread(self.next_workerid, self.dw.data,
                                                                        self.dw.getPreferences(), self.logger, red.copy()),
                                                "results_track":0,
                                                "batch_type": "partial",
                                                "results_tab": "exp",
                                                "work_progress":0,
                                                "work_estimate":0}
        else:
            self.workers[self.next_workerid] = {"worker":MinerThread(self.next_workerid, self.dw.data,
                                                                        self.dw.getPreferences(), self.logger),
                                                "results_track":0,
                                                "batch_type": "final",
                                                "results_tab": "exp",
                                                "work_progress":0,
                                                "work_estimate":0}

        self.makeMenu(self.toolFrame) ## To update the worker stoppers

    def getResults(self, worker_id=None):
        if worker_id is not None and worker_id in self.workers.keys():
            tap = None
            source = self.workers[worker_id]
            if source["batch_type"] == "partial":
                tap = source["worker"].miner.partial["batch"]
            elif source["batch_type"] == "final":
                tap = source["worker"].miner.final["batch"]
            if tap is not None:
                nb_tap = len(tap)
                if nb_tap > source["results_track"]:
                    tmp = []
                    for red in tap[source["results_track"]:nb_tap]:
                           redc = red.copy()
                           redc.track.insert(0, (worker_id, "W"))
                           tmp.append(redc)
                    self.tabs[source["results_tab"]]["tab"].insertItems(tmp)
                    source["results_track"] = nb_tap

    def endwork(self, worker_id=None):
        if worker_id is not None and worker_id in self.workers.keys():
            del self.workers[worker_id]
            self.makeMenu(self.toolFrame) ## To update the worker stoppers

    def OnMessResult(self, event):
        """Show Result status."""
        ###### TODO, here receive results
        (source, progress) = event.data
        if source is not None and source in self.workers.keys():
            self.getResults(source)

    def OnMessProgress(self, event):
        """Update progress status."""
        (source, progress) = event.data
        if source is not None and source in self.workers.keys():
            if progress is None:
                self.endwork(source)
            else:
                self.workers[source]["work_progress"] = progress[1]
                self.workers[source]["work_estimate"] = progress[0]
            self.makeProgressBar()

    def OnMessLogger(self, event):
        """Show Result status."""
        if event.data is not None:
            text = "%s" % event.data[1]
            header = "@%s:\t" % event.data[0]
            text = text.replace("\n", "\n"+header)
            self.tabs["log"]["text"].AppendText(header+text+"\n")

    def OnMessStatus(self, event):
        """Show Result status."""
        if event.data is not None:
            self.statusbar.SetStatusText("@%s:%s" % tuple(event.data), 0)

    def OnStop(self, event):
        """Show Result status."""
        ## TODO Implement stop
        if event.GetId() in self.ids_stoppers.keys():
            worker_id = self.ids_stoppers[event.GetId()]
            if worker_id is not None and worker_id in self.workers.keys():
                self.workers[worker_id]["worker"].abort()

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
        if len(self.dw.reds) > 0:
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
                self.details = {'names': self.dw.getColNames()}
                self.reloadVars()
                self.reloadReds()

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
        self.reloadReds()
        
    def OnExportRedescriptions(self, event):
        if self.dw.reds is None:
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

    def OnPageChanged(self, event):
        self.selectedTab = self.tabs[self.tabs_keys[self.tabbed.GetSelection()]]
        self.makeMenu(self.toolFrame)

    def OnNewWM(self, event):
        if self.selectedTab["type"] in ["Var", "Reds"]:
            self.selectedMap = -1
            self.selectedTab["tab"].viewData(MapView.TID)

    def OnNewWPC(self, event):
        if self.selectedTab["type"] in ["Var", "Reds"]:
            self.selectedMap = -1
            self.selectedTab["tab"].viewData(ParaView.TID)

    def OnNewWPJ(self, event):
        if self.selectedTab["type"] in ["Var", "Reds"]:
            self.selectedMap = -1
            self.selectedTab["tab"].viewData(ProjView.TID)

    def OnExpand(self, event):
        if self.selectedTab["type"] in ["Reds"]:
            self.showTab("exp")
            red = self.selectedTab["tab"].getSelectedItem()
            if red is not None:
                self.expand(red)

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

    def OnFlipEnabled(self, event):
        if self.selectedTab["type"] in ["Var", "Reds"]:
            self.selectedTab["tab"].flipEnabled(self.selectedTab["tab"].getSelectedRow())

    def OnEnabledAll(self, event):
        if self.selectedTab["type"] in ["Var", "Reds"]:
            self.selectedTab["tab"].setAllEnabled()

    def OnDisabledAll(self, event):
        if self.selectedTab["type"] in ["Var", "Reds"]:
            self.selectedTab["tab"].setAllDisabled()

    def OnDeleteDisabled(self, event):
        if self.selectedTab["type"] in ["Reds"]:
            self.selectedTab["tab"].deleteDisabled()

    def OnMoveReds(self, event):
        self.tabs["exp"]["tab"].moveEnabled(self.tabs["reds"]["tab"])

    def OnCut(self, event):
        if self.selectedTab["type"] in ["Reds"]:
            self.selectedTab["tab"].cutItem(self.selectedTab["tab"].getSelectedRow())
            self.makeMenu(self.toolFrame) ### update paste entry

    def OnCopy(self, event):
        if self.selectedTab["type"] in ["Reds"]:
            self.selectedTab["tab"].copyItem(self.selectedTab["tab"].getSelectedRow())
            self.makeMenu(self.toolFrame) ### update paste entry

    def OnPaste(self, event):
        if self.selectedTab["type"] in ["Reds"]:
            self.selectedTab["tab"].pasteItem(self.selectedTab["tab"].getSelectedRow())
            self.makeMenu(self.toolFrame) ### update paste entry

    def OnDuplicate(self, event):
        if self.selectedTab["type"] in ["Reds"]:
            self.selectedTab["tab"].copyItem(self.selectedTab["tab"].getSelectedRow())
            self.selectedTab["tab"].pasteItem(self.selectedTab["tab"].getSelectedRow())
            self.makeMenu(self.toolFrame) ### update paste entry
            
    def OnTabW(self, event):
        if event.GetId() in self.check_tab.keys():
            tab_id = self.check_tab[event.GetId()]
            if event.IsChecked():
                self.showTab(tab_id)
            else:
                self.showTab(tab_id)

    def showTab(self, tab_id):
        self.tabs[tab_id]["hide"] = False
        self.tabs[tab_id]["tab"].Show()

    def hideTab(self, tab_id):
        self.tabs[tab_id]["hide"] = True
        self.tabs[tab_id]["tab"].Hide()

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

            
    def showDetailsBox(self, rid, red):
        dlg = wx.MessageDialog(self.toolFrame,
                               self.prepareDetails(rid, red),"Point Details", wx.OK|wx.ICON_INFORMATION)
        result = dlg.ShowModal()
        dlg.Destroy()

    def prepareDetails(self, rid, red):
        dets = "%d:\n" % rid 
        for side,pref in [(0,""), (1,"")]:
            dets += "\n"
            for lit in red.queries[side].listLiterals():
                dets += ("\t%s=\t%s\n" % (self.details['names'][side][lit.col()], self.dw.getData().getValue(side, lit.col(), rid)))
        return dets

    def OnQuit(self, event):
        if not self.checkAndProceedWithUnsavedChanges():
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
         

    def checkAndProceedWithUnsavedChanges(self, test=None):
        """Checks for unsaved changes and returns False if they exist and user doesn't want to continue
        and True if there are no unsaved changes or user wants to proceed in any case.

        If additional parameter 'test' is given, asks the question if it is true."""
        if (test is not None and test) or (test is None and self.dw.isChanged):
            dlg = wx.MessageDialog(self.toolFrame, 'Unsaved changes might be lost.\nAre you sure you want to continue?', style=wx.YES_NO|wx.NO_DEFAULT|wx.ICON_EXCLAMATION, caption='Unsaved changes!')
            if dlg.ShowModal() == wx.ID_NO:
                return False
        return True

    def resetCoordinates(self):
        self.deleteAllViews()

    def resetConstraints(self):
        self.constraints = Constraints(self.dw.getNbRows(), self.dw.getPreferences())

    def resetLogger(self):
        if self.dw.getPreferences() is not None and self.dw.getPreference('verbosity') is not None:
            self.logger.resetOut()
            self.logger.addOut({"*": self.dw.getPreference('verbosity'), "error":1, "progress":2, "result":1}, self, Message.sendMessage)
            self.logger.addOut({"error":1}, "stderr")
            self.logger.addOut({"error":1}, self, CErrorDialog.showBox)
        else:
            self.logger.resetOut()
            self.logger.addOut({"*": 1, "progress":2, "result":1}, self, Message.sendMessage)
            self.logger.addOut({"error":1}, "stderr")

    def reloadVars(self):
        ## Initialize variable lists data
        for side in [0,1]:
            if self.dw.data is not None and self.details is not None:
                self.tabs[side]["tab"].resetData(self.dw.getDataCols(side), self.details)
            else:
                self.tabs[side]["tab"].resetData(ICList(), self.details)
            
    def reloadReds(self):
        ## Initialize red lists data
        self.tabs["reds"]["tab"].resetData(self.dw.getReds(), self.details, self.dw.getShowIds())
        self.tabs["exp"]["tab"].resetData(Batch(), self.details)
        self.tabs["hist"]["tab"].resetData(Batch(), self.details)
        self.deleteAllViews()
        self.makeMenu(self.toolFrame)
#        self.getMapView().setCurrentRed(redsTmp[0])
#        self.getMapView().updateRed()

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
        
