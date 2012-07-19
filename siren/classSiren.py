import os
import wx, wx.html
import threading

from reremi.toolLog import Log
from reremi.classMiner import Miner
from reremi.classData import Data
from reremi.classConstraints import Constraints
from reremi.classBatch import Batch
from reremi.toolICList import ICList

from classGridTable import VarTable, RedTable
from classMapView import MapView
from DataWrapper import DataWrapper
from classPreferencesDialog import PreferencesDialog

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
           wx.PostEvent(output, Message(Message.TYPES_MESSAGES[type_message], (source, message)))
    sendMessage = staticmethod(sendMessage)

class ImportFileDialog(object):
    """Helper class to show the dialog for importing data file triplets"""
    def __init__(self, parent):
        self.parent = parent
        self.dlg = wx.Dialog(self.parent, title="Import files")

        LHStext = wx.StaticText(self.dlg, label='Left-hand side data file')
        RHStext = wx.StaticText(self.dlg, label='Right-hand side data file')
        Cootext = wx.StaticText(self.dlg, label='Coordinates file')

        self.LHSfile = None
        self.RHSfile = None
        self.Coofile = None

        self.LHSfileTxt = wx.TextCtrl(self.dlg, label='', style=wx.TE_READONLY)
        self.RHSfileTxt = wx.TextCtrl(self.dlg, label='', style=wx.TE_READONLY)
        self.CoofileTxt = wx.TextCtrl(self.dlg, label='', style=wx.TE_READONLY)

        LHSbtn = wx.Button(self.dlg, label='Choose')
        RHSbtn = wx.Button(self.dlg, label='Choose')
        Coobtn = wx.Button(self.dlg, label='Choose')

        self.dlg.Bind(wx.EVT_BUTTON, self.onLHS, LHSbtn)
        self.dlg.Bind(wx.EVT_BUTTON, self.onRHS, RHSbtn)
        self.dlg.Bind(wx.EVT_BUTTON, self.onCoo, Coobtn)

        gridSizer = wx.GridSizer(rows = 3, cols = 3, hgap = 5, vgap = 5)
        gridSizer.AddMany([(LHStext, 0, wx.ALIGN_LEFT), (self.LHSfileTxt, 0, wx.EXPAND), (LHSbtn, 0),
                           (RHStext, 0, wx.ALIGN_LEFT), (self.RHSfileTxt, 0, wx.EXPAND), (RHSbtn, 0),
            (Cootext, 0, wx.ALIGN_LEFT), (self.CoofileTxt, 0, wx.EXPAND), (Coobtn, 0)])

        btnSizer = self.dlg.CreateButtonSizer(wx.OK|wx.CANCEL)
        topSizer = wx.BoxSizer(wx.VERTICAL)
        topSizer.Add(gridSizer, flag=wx.ALL, border=5)
        topSizer.Add(btnSizer, flag=wx.ALL, border=5)

        self.dlg.SetSizer(topSizer)
        self.dlg.Fit()

        if self.dlg.ShowModal() == wx.ID_OK:
            try:
                self.parent.dw.importDataFromFiles([self.LHSfile, self.RHSfile], None, self.Coofile)
            except IOError, error:
                mdlg = wx.MessageDialog(self.parent.toolFrame, 'Error opening files '+str(self.LHSfile)
                                       +', '+str(self.RHSfile)+', and '+str(self.Coofile)+':\n'
                                       +str(error))
                mdlg.ShowModal()
                mdlg.Destroy()
            self.parent.details = {'names': self.parent.dw.getColNames()}
            self.parent.reloadVars()
            self.parent.reloadReds()
            
        self.dlg.Destroy()

    def onLHS(self, e):
        pass
    def onRHS(self, e):
        pass
    def onCoo(self, e):
        pass

        

        
        

class Siren():
    """ The main frame of the application
    """

    titleTool = 'SIREN :: tools'
    titleMap = 'SIREN :: maps'
    titleHelp = 'SIREN :: help'
    helpURL = "http://www.cs.helsinki.fi/u/galbrun/redescriptors/"

    # For About dialog
    name = "Siren"
    about_file = 'ABOUT'
    licence_file = 'LICENCE_short'
    programURL = "http://www.cs.helsinki.fi/u/galbrun/redescriptors/siren"
    version = '0.9b'
    cpyright = '(C) 2012 Esther Galbrun and Pauli Miettinen'
    icon_file = 'icons/siren_icon32x32.png'
    
         
    def __init__(self):
        self.tabs = {0: {"title":"LHS Variables", "type":"Var", "hide":False, "style":None},
                     1: {"title":"RHS Variables", "type":"Var", "hide":False, "style":None},
                     "reds": {"title":"Redescriptions", "type":"Reds", "hide":False, "style":None},
                     "exp": {"title":"Expanding", "type":"Reds", "hide":False, "style":None},
                     "log": {"title":"Log", "type":"Text", "hide": True, "style": wx.TE_READONLY|wx.TE_MULTILINE}
                     }
        self.tabs_keys = [0, 1, "reds", "exp", "log"]
        self.selectedTab = self.tabs[self.tabs_keys[0]]
        self.ids_stoppers = {}
        self.check_tab = {}
        
        self.toolFrame = wx.Frame(None, -1, self.titleTool)
        self.toolFrame.Bind(wx.EVT_CLOSE, self.OnQuit)

        self.toolFrame.Connect(-1, -1, Message.TYPES_MESSAGES['*'], self.OnMessLogger)
        self.toolFrame.Connect(-1, -1, Message.TYPES_MESSAGES['log'], self.OnMessLogger)
        self.toolFrame.Connect(-1, -1, Message.TYPES_MESSAGES['time'], self.OnMessLogger)
        self.toolFrame.Connect(-1, -1, Message.TYPES_MESSAGES['status'], self.OnMessLogger)
        self.toolFrame.Connect(-1, -1, Message.TYPES_MESSAGES['result'], self.OnMessResult)
        self.toolFrame.Connect(-1, -1, Message.TYPES_MESSAGES['progress'], self.OnMessProgress)
        self.toolFrame.Connect(-1, -1, Message.TYPES_MESSAGES['status'], self.OnMessStatus)

        self.num_filename=''
        self.bool_filename=''
        self.coo_filename=''
        self.queries_filename=''
        self.settings_filename=''
        
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
        # tmp_queries_filename='../data/dblp/dblp_picked_real.queries'
        # tmp_settings_filename='../data/dblp/dblp_picked_real.conf'


        #### COMMENT OUT TO LOAD RAJAPAJA ON STARTUP
        tmp_num_filename='../rajapaja/worldclim_tp.densenum'
        tmp_bool_filename='../rajapaja/mammals.datbool'
        tmp_coo_filename='../rajapaja/coordinates.names'
        tmp_queries_filename='../rajapaja/rajapaja.queries'
        tmp_settings_filename='../rajapaja/rajapaja_conf.xml'


        # ### COMMENT OUT TO LOAD US ON STARTUP
        # tmp_num_filename='../data/us/us_politics_funds_cont.densenum'
        # tmp_bool_filename='../data/us/us_socio_eco_cont.densenum'
        # tmp_coo_filename='../data/us/us_coordinates_cont.names'
        # tmp_queries_filename='../data/us/us.queries'
        # tmp_settings_filename='../data/us/us.conf'

        # #### COMMENT OUT TO LOAD SOMETHING ON STARTUP
        # (Almost) all of the above should stay in dw
        self.dw = DataWrapper()

        ### About dialog
        self.info =  wx.AboutDialogInfo()
        self.info.SetName(self.name)
        self.info.SetWebSite(self.programURL)
        self.info.SetCopyright(self.cpyright)
        self.info.SetVersion(self.version)
        self.info.SetIcon(wx.Icon('icons/siren_icon32x32.png', wx.BITMAP_TYPE_PNG))
        with open(self.about_file) as f:
            self.info.SetDescription(f.read())
        with open(self.licence_file) as f:
            self.info.SetLicence(f.read())

        ## Register file reading message functions to DataWrapper
        self.dw.registerStartReadingFileCallback(self.startReadingFileMsg)
        self.dw.registerStopReadingFileCallback(self.stopReadingFileMsg)
        self.readingFileDlg = None

        ## Comment (out) to toggle between loading data in input and not
        self.dw.importDataFromFiles([tmp_bool_filename, tmp_num_filename], None, tmp_coo_filename)
        self.dw.importQueriesTXTFromFile(tmp_queries_filename)
        self.dw.importPreferencesFromFile(tmp_settings_filename)

 
        ### INITIALISATION OF DATA
        self.resetLogger()
        self.resetConstraints()
        self.details = {'names': self.dw.getColNames()}
        self.reloadVars()
        self.resetCoordinates()
        self.reloadReds()

        
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
        
        if self.selectedTab["type"] in ["Var","Reds"]:
            ID_NEWW = wx.NewId()
            m_neww = menuRed.Append(ID_NEWW, "&View in new window\tCtrl+W", "View redescription in new window.")
            frame.Bind(wx.EVT_MENU, self.OnNewW, m_neww)

            ID_ENABLED = wx.NewId()
            m_enabled = menuRed.Append(ID_ENABLED, "E&nable/Disable\tCtrl+D", "Enable/Disable current redescription.")
            frame.Bind(wx.EVT_MENU, self.OnFlipEnabled, m_enabled)

            ID_ENABLEDALL = wx.NewId()
            m_enabledall = menuRed.Append(ID_ENABLEDALL, "Ena&ble All", "Enable all redescriptions.")
            frame.Bind(wx.EVT_MENU, self.OnEnabledAll, m_enabledall)

            ID_DISABLEDALL = wx.NewId()
            m_disabledall = menuRed.Append(ID_DISABLEDALL, "Disa&ble All", "Disable all redescriptions.")
            frame.Bind(wx.EVT_MENU, self.OnDisabledAll, m_disabledall)


        if self.selectedTab["type"] == "Reds":
            ID_EXPAND = wx.NewId()
            m_expand = menuRed.Append(ID_NEWW, "&Expand\tCtrl+E", "Expand redescription.")
            frame.Bind(wx.EVT_MENU, self.OnExpand, m_expand)

            ID_FILTER_ONE = wx.NewId()
            m_filter_one = menuRed.Append(ID_FILTER_ONE, "&Filter redundant to current\tCtrl+F", "Disable redescriptions redundant to current downwards.")
            frame.Bind(wx.EVT_MENU, self.OnFilterToOne, m_filter_one)

            ID_FILTER_ALL = wx.NewId()
            m_filter_all = menuRed.Append(ID_FILTER_ALL, "&Filter redundant\tCtrl+F", "Disable redescriptions redundant to previous encountered.")
            frame.Bind(wx.EVT_MENU, self.OnFilterAll, m_filter_all)

            ID_PROCESS = wx.NewId()
            m_process = menuRed.Append(ID_PROCESS, "&Process redescriptions\tCtrl+F", "Sort and filter current redescription list.")
            frame.Bind(wx.EVT_MENU, self.OnProcessAll, m_process)

            ID_DELDISABLED = wx.NewId()
            m_deldisabled = menuRed.Append(ID_DELDISABLED, "Delete Disa&bled", "Delete all disabled redescriptions.")
            frame.Bind(wx.EVT_MENU, self.OnDeleteDisabled, m_deldisabled)
            
            m_cut = menuRed.Append(wx.ID_CUT, "Cu&t", "Cut current redescription.")
            frame.Bind(wx.EVT_MENU, self.OnCut, m_cut)
            
            m_copy = menuRed.Append(wx.ID_COPY, "&Copy", "Copy current redescription.")
            frame.Bind(wx.EVT_MENU, self.OnCopy, m_copy)
            
            m_paste = menuRed.Append(wx.ID_PASTE, "&Paste", "Paste current redescription.")
            frame.Bind(wx.EVT_MENU, self.OnPaste, m_paste)
 
        return menuRed

    def makeStoppersMenu(self, frame):
        menuStoppers = wx.Menu()
        self.ids_stoppers = {}
        for worker_id in self.workers.keys(): 
            ID_STOP = wx.NewId()
            self.ids_stoppers[ID_STOP] = worker_id 
            m_stop = menuStoppers.Append(ID_STOP, "Stop #%s" % worker_id, "Interrupt mining process #%s." % worker_id)
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
        
        submenuFile = wx.Menu()
        ID_IMPORT_DATA = wx.NewId()
        m_impData = submenuFile.Append(ID_IMPORT_DATA, "Import &Data", "Import data into the project.")
        frame.Bind(wx.EVT_MENU, self.OnImportData, m_impData)

        ID_IMPORT_QUERIES = wx.NewId()
        m_impQueries = submenuFile.Append(ID_IMPORT_QUERIES, "Import Q&ueries", "Import queries into the project.")
        frame.Bind(wx.EVT_MENU, self.OnImportQueries, m_impQueries)

        ID_IMPORT_PREFERENCES = wx.NewId()
        m_impPreferences = submenuFile.Append(ID_IMPORT_PREFERENCES, "Import Preferences", "Import preferences into the project.")
        frame.Bind(wx.EVT_MENU, self.OnImportPreferences, m_impPreferences)

        ID_IMPORT = wx.NewId()
        m_import = menuFile.AppendMenu(ID_IMPORT, "&Import", submenuFile)

        ID_EXPORT = wx.NewId()
        m_export = menuFile.Append(ID_EXPORT, "&Export Redescriptions\tShift+Ctrl+E", "Export redescriptions.")
        frame.Bind(wx.EVT_MENU, self.OnExportQueries, m_export)

        m_quit = menuFile.Append(wx.ID_EXIT, "&Quit", "Close window and quit program.")
        frame.Bind(wx.EVT_MENU, self.OnQuit, m_quit)

        ### MENU RED
        menuRed = self.makeContextMenu(frame)

        #ID_PREFERENCESDIA = wx.NewId()
        m_preferencesdia = menuRed.Append(wx.ID_PREFERENCES, "Preferences...", "Set preferences.")
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
        
        ### PUT TOGETHER
        menuBar = wx.MenuBar()
        menuBar.Append(menuFile, "&File")
        menuBar.Append(menuRed, "&Edit")
        menuBar.Append(menuStoppers, "&Tools")
        menuBar.Append(menuView, "&View")
        menuBar.Append(menuHelp, "&Help")
        frame.SetMenuBar(menuBar)

######################################################################
###########     MAP VIEWS
######################################################################

    def getMapView(self, vid=None):
        if vid not in self.mapViews.keys():
            self.selectedMap = wx.NewId()
            self.mapViews[self.selectedMap] = MapView(self, self.selectedMap)    
        self.mapViews[self.selectedMap].mapFrame.Raise()
        return self.mapViews[self.selectedMap]

    def deleteView(self, vid):
        if vid in self.mapViews.keys():
            self.mapViews[vid].mapFrame.Destroy()
            del self.mapViews[vid]

    def deleteAllViews(self):
        self.selectedMap = -1
        for mapV in self.mapViews.values():
            mapV.mapFrame.Destroy()
        self.mapViews = {}
        

######################################################################
###########     ACTIONS
######################################################################

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
            self.LoadFile(path)
        open_dlg.Destroy()
        # DEBUGGING
        #wx.MessageDialog(self.toolFrame, 'Opened package from '+path).ShowModal()

    def LoadFile(self, path):
        try:
            self.dw.openPackage(path)
        except IOError as error:
            dlg = wx.MessageDialog(self.toolFrame, 'Error opening file '+str(path)+':\n' + str(error))
            dlg.ShowModal()
            return False
        else:
            self.details = {'names': self.dw.getColNames()}
            self.reloadVars()
            self.reloadReds()
            return True

##    def OnExpand(self, event):


    def expand(self, red):
        self.progress_bar.Show()
        self.next_workerid += 1
        if red.length(0) + red.length(1) > 0:
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
        if worker_id != None and worker_id in self.workers.keys():
            tap = None
            source = self.workers[worker_id]
            if source["batch_type"] == "partial":
                tap = source["worker"].miner.partial["batch"]
            elif source["batch_type"] == "final":
                tap = source["worker"].miner.final["batch"]
            if tap != None:
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
        if worker_id != None and worker_id in self.workers.keys():
            del self.workers[worker_id]
            self.makeMenu(self.toolFrame) ## To update the worker stoppers

    def OnMessResult(self, event):
        """Show Result status."""
        ###### TODO, here receive results
        (source, progress) = event.data
        if source != None and source in self.workers.keys():
            self.getResults(source)

    def OnMessProgress(self, event):
        """Update progress status."""
        (source, progress) = event.data
        if source != None and source in self.workers.keys():
            if progress == None:
                self.endwork(source)
            else:
                self.workers[source]["work_progress"] = progress[1]
                self.workers[source]["work_estimate"] = progress[0]
            self.makeProgressBar()

    def OnMessLogger(self, event):
        """Show Result status."""
        if event.data != None:
            text = "%s" % event.data[1]
            header = "@%s:\t" % event.data[0]
            text = text.replace("\n", "\n"+header)
            self.tabs["log"]["text"].AppendText(header+text+"\n")

    def OnMessStatus(self, event):
        """Show Result status."""
        if event.data != None:
            self.statusbar.SetStatusText("@%s:%s" % tuple(event.data), 0)

    def OnStop(self, event):
        """Show Result status."""
        ## TODO Implement stop
        if event.GetId() in self.ids_stoppers.keys():
            worker_id = self.ids_stoppers[event.GetId()]
            if worker_id != None and worker_id in self.workers.keys():
                self.workers[worker_id]["worker"].abort()

    def OnSave(self, event):
        if not (self.dw.isFromPackage and self.dw.package_filename is not None):
            wx.MessageDialog(self.toolFrame, 'Cannot save data that is not from a package\nUse Save As... instead').ShowModal()
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
        if len(self.dw.reds) > 0:
            sure_dlg = wx.MessageDialog(self.toolFrame, 'Importing new data erases old redescriptions.\nDo you want to continue?', caption="Warning!", style=wx.OK|wx.CANCEL)
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

                open_coord_dlg = wx.FileDialog(self.toolFrame, message='Choose coordinates file', defaultDir=os.path.dirname(left_path),  
			wildcard=wcd, style=wx.OPEN|wx.CHANGE_DIR)
                if open_coord_dlg.ShowModal() == wx.ID_OK:
                    coord_path = open_coord_dlg.GetPath()

                    try:
                        self.dw.importDataFromFiles([left_path, right_path], None, coord_path)
                    except IOError, error:
                        dlg = wx.MessageDialog(self.toolFrame, 'Error opening files '+str(left_path)
                                               +', '+str(right_path)+' and '+str(coord_path)+':\n' + str(error))
                        dlg.ShowModal()

                    self.details = {'names': self.dw.getColNames()}
                    self.reloadVars()
                    self.reloadReds()

                open_coord_dlg.Destroy()
            open_right_dlg.Destroy()
        open_left_dlg.Destroy()

    def OnImportPreferences(self, event):
        dir_name = os.path.expanduser('~/')
        open_dlg = wx.FileDialog(self.toolFrame, message='Choose file', defaultDir = dir_name,
                                 style = wx.OPEN|wx.CHANGE_DIR)
        if open_dlg.ShowModal() == wx.ID_OK:
            path = open_dlg.GetPath()
            try:
                self.dw.importPreferencesFromFile(path)
            except IOError as error:
                wx.MessageDialog(self.toolFrame, 'Error opening file '+str(path)+':\n'+str(error)).ShowModal()
        open_dlg.Destroy()
        
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
        self.reloadReds()
        
    def OnExportQueries(self, event):
        if self.dw.reds is None:
            wx.MessageDialog(self.toolFrame, 'Cannot export redescriptions: no redescriptions loaded').ShowModal()
            return
        
        if self.dw.package_filename is not None:
            dir_name = os.path.dirname(self.dw.package_filename)
        else:
            dir_name = os.path.expanduser('~/')

        save_dlg = wx.FileDialog(self.toolFrame, message='Export redescriptions to:', defaultDir = dir_name, style = wx.SAVE|wx.CHANGE_DIR)
        if save_dlg.ShowModal() == wx.ID_OK:
            path = save_dlg.GetPath()
            try:
                self.dw.exportQueries(path)

            except IOError as error:
                wx.MessageDialog(self.toolFrame, 'Error while exporting redescriptions to file '
                                 +str(path)+':\n'+str(error)).ShowModal()
        save_dlg.Destroy()

    def OnPageChanged(self, event):
        self.selectedTab = self.tabs[self.tabs_keys[self.tabbed.GetSelection()]]
        self.makeMenu(self.toolFrame)

    def OnNewW(self, event):
        if self.selectedTab["type"] in ["Var", "Reds"]:
            self.selectedMap = -1
            self.selectedTab["tab"].viewData()

    def OnExpand(self, event):
        if self.selectedTab["type"] in ["Reds"]:
            red = self.selectedTab["tab"].getSelectedItem()
            if red != None:
                self.expand(red)

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

    def OnCut(self, event):
        if self.selectedTab["type"] in ["Reds"]:
            self.selectedTab["tab"].cutItem(self.selectedTab["tab"].getSelectedRow())

    def OnCopy(self, event):
        if self.selectedTab["type"] in ["Reds"]:
            self.selectedTab["tab"].copyItem(self.selectedTab["tab"].getSelectedRow())

    def OnPaste(self, event):
        if self.selectedTab["type"] in ["Reds"]:
            self.selectedTab["tab"].pasteItem(self.selectedTab["tab"].getSelectedRow())

    def OnTabW(self, event):
        if event.GetId() in self.check_tab.keys():
            tab_id = self.check_tab[event.GetId()]
            if event.IsChecked():
                self.tabs[tab_id]["hide"] = False
                self.tabs[tab_id]["tab"].Show()
            else:
                self.tabs[tab_id]["hide"] = True
                self.tabs[tab_id]["tab"].Hide()

    def OnPreferencesDialog(self, event):
        d = PreferencesDialog(self.toolFrame, self.dw)
        d.ShowModal()
        d.Destroy()

    def OnHelp(self, event):
        self.helpFrame = wx.Frame(self.toolFrame, -1, self.titleHelp)
        html = wx.html.HtmlWindow(self.helpFrame)
        if "gtk2" in wx.PlatformInfo:
            html.SetStandardFonts()        
        wx.CallAfter(html.LoadPage, self.helpURL)
        self.helpFrame.Show()

    def OnAbout(self, event):
        wx.AboutBox(self.info)
    
    def OnQuit(self, event):
        self.deleteAllViews()
        self.toolFrame.Destroy()
        exit()
  
    def resetCoordinates(self):
        self.deleteAllViews()

    def resetConstraints(self):
        self.constraints = Constraints(self.dw.getNbRows(), self.dw.getPreferences())

    def resetLogger(self):
        #### TODO
        if self.dw.getPreferences() != None and self.dw.getPreference('verbosity') != None:
            self.logger = Log({"*": self.dw.getPreference('verbosity'), "progress":2, "result":1}, self.toolFrame, Message.sendMessage)
        else:
            self.logger = Log({"*": 1, "progress":2, "result":1}, self.toolFrame, Message.sendMessage)
            

    def reloadVars(self):
        ## Initialize variable lists data
        for side in [0,1]:
            if self.dw.data != None and self.details != None:
                self.tabs[side]["tab"].resetData(self.dw.getDataCols(side), self.details)
            else:
                self.tabs[side]["tab"].resetData(ICList(), self.details)
            
    def reloadReds(self):
        ## Initialize red lists data
        self.tabs["reds"]["tab"].resetData(self.dw.getReds(), self.details, self.dw.getShowIds())
        self.tabs["exp"]["tab"].resetData(Batch(), self.details)
#        self.getMapView().setCurrentRed(redsTmp[0])
#        self.getMapView().updateRed()

    def startReadingFileMsg(self, filenames):
        """Shows a dialog that we're reading a file"""
        msg = 'Reading file'
        if len(filenames) <= 1:
            msg += ' '+filename
        else:
            msg += 's'
            for filename in filenames:
                msg += ' '.join(filename)
        self.toolFrame.Enable(False)
        self.busyDlg = wx.BusyInfo(msg, self.toolFrame)
        

    def stopReadingFileMsg(self):
        """Removes the BusyInfo dialog"""
        self.busyDlg = None
        self.toolFrame.Enable(True)
        
