import os, os.path, random
import wx
import time, math
import sys
import pickle
# import wx.lib.agw.pybusyinfo as PBI
import wx.lib.dialogs

from ..reremi.toolLog import Log
from ..reremi.classData import Data, DataError
from ..reremi.classConstraints import Constraints
from ..reremi.classBatch import Batch
from ..reremi.toolICList import ICList

from DataWrapper import DataWrapper, findFile
from classGridTable import VarTable, RedTable, RowTable
from classPreferencesDialog import PreferencesDialog
from classConnectionDialog import ConnectionDialog
from classSplitDialog import SplitDialog
from miscDialogs import ImportDataCSVDialog, FindDialog
from ..views.factView import ViewFactory
from ..views.classFiller import Filler
from ..work.toolWP import WorkPlant
from ..common_details import common_variables

import pdb

def getRandomColor():
    return (random.randint(0,255), random.randint(0,255), random.randint(0,255))
 
class Siren():
    """ The main frame of the application
    """
    curr_dir = os.path.dirname(os.path.abspath(__file__))
    root_dir = os.path.split(os.path.split(curr_dir)[0])[0]
    
    titleTool = common_variables["PROJECT_NAME"]+' :: tools'
    titlePref = common_variables["PROJECT_NAME"]+' :: '
    titleHelp = common_variables["PROJECT_NAME"]+' :: help'
    helpURL = findFile('index.html', ['../../help', root_dir+'/help', './help'])
    helpInternetURL = common_variables["PROJECT_URL"]+'help'
    
    # For About dialog
    name = common_variables["PROJECT_NAME"]    
    programURL = common_variables["PROJECT_URL"]
    version = common_variables["VERSION"]
    cpyright = '(c) '+common_variables["COPYRIGHT_YEAR_FROM"]+'-' \
               +common_variables["COPYRIGHT_YEAR_TO"]+' ' \
               +common_variables["PROJECT_AUTHORS"]
    about_text = common_variables["PROJECT_DESCRIPTION_LINE"]+"\n"
    

    icon_file = findFile('siren_icon32x32.png', ['../../icons', root_dir + '/icons', './icons'])
    license_file = findFile('LICENSE', ['../../licenses', root_dir+ '/licenses', './licenses'])
    external_licenses = ['basemap', 'matplotlib', 'python', 'wx', 'grako']

    results_delay = 1000
    viz_grid = [2,2]
    intab = False #True
    color_add = (16, 82, 0)
    color_drop = (190, 10, 10)
    color_vizb = (20, 20, 20)

         
    def __init__(self):
        self.initialized = True
        self.busyDlg = None
        self.findDlg = None
        self.dw = None
        self.plant = WorkPlant()
        tmp_tabs = [{"id": "rows", "title":"Entities", "short": "Ent", "type":"Row", "hide":False, "style":None},
                    {"id": 0, "title":"LHS Variables", "short": "LHS", "type":"Var", "hide":False, "style":None},
                    {"id": 1, "title":"RHS Variables", "short": "RHS", "type":"Var", "hide":False, "style":None},
                    {"id": "reds", "title":"Redescriptions", "short": "R", "type":"Reds", "hide":False, "style":None},
                    {"id": "exp", "title":"Expansions",  "short": "E", "type":"Reds", "hide":True, "style":None},
                    {"id": "hist", "title":"History", "short": "H", "type":"Reds", "hide":True, "style":None},
                    {"id": "viz", "title":"Visualizations", "short": "V", "type":"Viz", "hide": False, "style":None},
                    {"id": "log", "title":"Log", "short": "Log", "type":"Text", "hide": True, "style": wx.TE_READONLY|wx.TE_MULTILINE}]
        
        self.tabs = dict([(p["id"], p) for p in tmp_tabs])
        self.tabs_keys = [p["id"] for p in tmp_tabs]
        self.viz_postab = self.tabs_keys.index("viz")
        self.selectedTab = self.tabs[self.tabs_keys[0]]
        stn = self.tabs_keys[0]

        self.logger = Log()

        tmp = wx.DisplaySize()
        self.toolFrame = wx.Frame(None, -1, self.titleTool, pos = wx.DefaultPosition,
                                  size=(tmp[0]*0.66,tmp[1]*0.9), style = wx.DEFAULT_FRAME_STYLE)
        self.toolFrame.Bind(wx.EVT_CLOSE, self.OnQuit)
        self.toolFrame.Bind(wx.EVT_SIZE, self.OnSize)
        self.toolFrame.SetIcon(wx.Icon(self.icon_file, wx.BITMAP_TYPE_PNG))

        self.view_ids = {}
        self.selectedViewX = -1
        self.buffer_copy = None
        
        self.call_check = None
        
        self.create_tool_panel()
        self.changePage(stn)
        
        self.dw = DataWrapper(self.logger)

        ### About dialog
        self.info =  wx.AboutDialogInfo()
        self.info.SetName(self.name)
        self.info.SetWebSite(self.programURL)
        self.info.SetCopyright(self.cpyright)
        self.info.SetVersion(self.version)
        self.info.SetIcon(wx.Icon(self.icon_file, wx.BITMAP_TYPE_PNG))
        self.info.SetDescription(self.about_text)
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
        self.resetConstraints()
        self.resetCoordinates()
        self.reloadAll()

        ### W/O THIS DW THINK IT'S CHANGED!
        self.dw.isChanged = False
        self.plant.setUpCall([self.doUpdates, self.resetLogger])
        self.resetLogger()

        self.initialized = True
        self.toolFrame.Show()

    def isInitialized(self):
        return self.initialized

    def hasDataLoaded(self):
        if self.dw is not None:
            return self.dw.getData() is not None
        return False
    
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
        self.splitter = wx.SplitterWindow(self.toolFrame)
        
	self.tabbed = wx.Notebook(self.splitter, -1, style=(wx.NB_TOP)) #, size=(3600, 1200))

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

            elif self.tabs[tab_id]["type"] == "Viz":
                #self.tabs[tab_id]["tab"] = wx.Panel(self.tabbed, -1)
                self.tabs[tab_id]["tab"] = wx.ScrolledWindow(self.tabbed, -1, style=wx.HSCROLL|wx.VSCROLL)
                self.tabs[tab_id]["tab"].SetScrollRate( 5, 5 )        
                # self.tabs[tab_id]["tab"].SetSizer(wx.GridSizer(rows=2, cols=3, vgap=0, hgap=0))
                self.tabs[tab_id]["tab"].SetSizer(wx.GridBagSizer(vgap=0, hgap=0))
                if self.tabs[tab_id]["hide"]:
                    self.tabs[tab_id]["tab"].Hide()
                self.tabbed.AddPage(self.tabs[tab_id]["tab"], self.tabs[tab_id]["title"])

        self.toolFrame.Bind(wx.EVT_NOTEBOOK_PAGE_CHANGED, self.OnPageChanged)        
        self.splitter.Initialize(self.tabbed)
        self.splitter.SetSashGravity(1.)
        self.splitter.SetMinimumPaneSize(0)
        self.splitter.Bind(wx.EVT_SPLITTER_UNSPLIT, self.OnSplitchange)
        # self.splitter.Initialize(self.tabbed)
        # self.splitter.SplitHorizontally(self.tabbed, self.tabs["viz"]["tab"])
        self.tabbed.Bind(wx.EVT_SIZE, self.OnSize)

    def makeStatus(self, frame):
        ### status bar
        self.statusbar = frame.CreateStatusBar()
        self.statusbar.SetFieldsCount(4)
        self.statusbar.SetStatusWidths([25, 300, 150, -1])

        rect = self.statusbar.GetFieldRect(0)
        self.buttViz = wx.ToggleButton(self.statusbar, wx.NewId(), "", style=wx.ALIGN_CENTER, size=(rect.height,rect.height))
        self.buttViz.SetBackgroundColour(getRandomColor())
        self.buttViz.SetPosition((rect.x+2, rect.y+2))
        self.buttViz.Bind(wx.EVT_TOGGLEBUTTON, self.OnSplitchange)

        self.progress_bar = wx.Gauge(self.statusbar, -1, style=wx.GA_HORIZONTAL|wx.GA_SMOOTH)
        rect = self.statusbar.GetFieldRect(2)
        self.progress_bar.SetPosition((rect.x+2, rect.y+2))
        self.progress_bar.SetSize((rect.width-2, rect.height-2))
        self.progress_bar.Hide()

######################################################################
###########     INTAB VIZ TAB
######################################################################

    #### HERE INTAB SWITCH
    def showVizIntab(self):
        return self.hasVizIntab() and self.intab

    def hasVizIntab(self):
        return (self.viz_grid[0]*self.viz_grid[1]) > 0

    def isReadyVizIntab(self):
        return self.hasVizIntab() and hasattr(self, 'vfiller_ids') and len(self.vfiller_ids) + len(self.vused_ids) + len(self.buttons) > 0


    def getVizBbsiz(self):
        return 9
    def getVizBb(self):
        return self.getVizBbsiz()+3
        
    def initVizTab(self):
        self.vfiller_ids = {}
        self.vused_ids = {}
        self.buttons = {}
        
        if self.dw is not None:
            self.viz_grid = [self.dw.getPreference('intab_nbr'), self.dw.getPreference('intab_nbc')]

        if self.hasVizIntab():
            self.fillInViz()
            self.addVizExts()
            self.setVizButtAble()
            self.updateVizcellSelected()
            if not self.tabs["viz"]["hide"]:
                self.tabs["viz"]["tab"].Show()
            if self.viz_postab > len(self.tabs_keys) or self.tabs_keys[self.viz_postab] != "viz":
                self.tabs_keys.insert(self.viz_postab, "viz")

        else:
            self.tabs["viz"]["tab"].Hide()
            if self.viz_postab < len(self.tabs_keys) and self.tabs_keys[self.viz_postab] == "viz":
                self.tabs_keys.pop(self.viz_postab)

    def clearVizTab(self):
        for sel in self.vfiller_ids:
            panel = self.vfiller_ids[sel].popSizer()
            panel.Destroy()
        for sel in self.vused_ids:
            ### Free another view            
            self.view_ids[self.vused_ids[sel][0]].OnQuit(upMenu=False, freeing=False)
            
        for bi, bb in self.buttons.items():
            self.tabs["viz"]["tab"].GetSizer().Detach(bb["button"])
            bb["button"].Destroy()

        self.vfiller_ids = {}
        self.vused_ids = {}
        self.buttons = {}
        self.selected_cell = None

    def reloadVizTab(self):
        if self.isReadyVizIntab():
            self.clearVizTab()
        self.initVizTab()
        self.doUpdates({"menu":True})
            
    def getVizcellSelected(self):
        return self.selected_cell
    def setVizcellSelected(self, pos):
        self.selected_cell = pos
    def updateVizcellSelected(self):
        if len(self.vfiller_ids) > 0:
            self.selected_cell = sorted(self.vfiller_ids.keys(), key=lambda x: x[0]+x[1])[0]
            uid = self.selected_cell
        else:
            self.selected_cell = sorted(self.vused_ids.keys(), key=lambda x: self.vused_ids[x][1])[0]
            uid = None
        self.setActiveViz(uid)

    def getVizPlotPos(self, vid):
        sel = self.getVizcellSelected()
        if sel in self.vfiller_ids:
            pv = self.vfiller_ids.pop(sel)
            panel = pv.popSizer()
            panel.Destroy()
        else:
            ### Free another view            
            self.view_ids[self.vused_ids[sel][0]].OnQuit(upMenu=False, freeing=False)

        #### mark cell used    
        self.vused_ids[sel] = (vid, len(self.vused_ids))            
        self.updateVizcellSelected()
        return sel

    def getVizGridSize(self):
        return self.viz_grid
    def getVizGridNbDim(self, dim=None):
        if dim is None:
            return self.viz_grid
        else:
            return self.viz_grid[dim]
    
    def decrementVizGridDim(self, dim, id):
        self.viz_grid[dim] -= 1
        self.dropGridDimViz(dim, id)
        self.resizeViz()
        self.setVizButtAble()
        self.updateVizcellSelected()

    def incrementVizGridDim(self, dim):
        self.viz_grid[dim] += 1
        self.addGridDimViz(dim)
        self.resizeViz()
        self.setVizButtAble()
        self.updateVizcellSelected()
        
    def fillInViz(self):
        for i in range(1, self.getVizGridNbDim(0)+1):
            for j in range(1, self.getVizGridNbDim(1)+1):
                self.vfiller_ids[(i,j)] = Filler(self, (i,j))

    def addGridDimViz(self, dim):
        for bi, but in self.buttons.items():
            if but["action"][1] == -1:
                self.tabs["viz"]["tab"].GetSizer().Detach(but["button"])
                ddim = but["action"][0]
                ppos, pspan = ([1, 1], [1, 1])
                ppos[ddim] += self.getVizGridNbDim(ddim)
                pspan[1-ddim] = self.getVizGridNbDim(1-ddim)
                self.tabs["viz"]["tab"].GetSizer().Add(but["button"], pos=ppos, span=pspan, flag=wx.EXPAND|wx.ALIGN_CENTER, border=0)

        sizeb = (self.getVizBbsiz(), 1)
        bid = wx.NewId()
        but = wx.Button(self.tabs["viz"]["tab"], bid, "", style=wx.NO_BORDER, size=(sizeb[dim], sizeb[1-dim]))
        but.SetBackgroundColour(self.color_drop)
        posb = [0,0]
        posb[dim] = self.getVizGridNbDim(dim)
        self.tabs["viz"]["tab"].GetSizer().Add(but, pos=tuple(posb), flag=wx.EXPAND|wx.ALIGN_CENTER, border=0)
        self.buttons[bid] = {"action": (dim, self.getVizGridNbDim(dim)), "button": but}
        but.Bind(wx.EVT_BUTTON, self.OnChangeGridViz)
        ## but.Bind(wx.EVT_ENTER_WINDOW, self.OnPrintName)

        ppos = [self.getVizGridNbDim(dim), self.getVizGridNbDim(dim)]
        for i in range(1, self.getVizGridNbDim(1-dim)+1):
            ppos[1-dim] = i
            self.vfiller_ids[tuple(ppos)] = Filler(self, tuple(ppos))

    def dropGridDimViz(self, dim, cid):
        ssel = [0,0]
        ssel[dim] = cid
        for i in range(1, self.getVizGridNbDim(1-dim)+1):
            ssel[1-dim] = i
            sel = tuple(ssel)
            if sel in self.vfiller_ids:
                pv = self.vfiller_ids.pop(sel)
                panel = pv.popSizer()
                panel.Destroy()
            else:
                # ## Free another view
                self.view_ids[self.vused_ids[sel][0]].OnQuit(upMenu=False, freeing=False)

        for ccid in range(cid+1, self.getVizGridNbDim(dim)+2):
            ssel = [0,0]
            ssel[dim] = ccid
            nnel = [0,0]
            nnel[dim] = ccid-1

            for i in range(1, self.getVizGridNbDim(1-dim)+1):
                ssel[1-dim] = i
                nnel[1-dim] = i
                sel = tuple(ssel)
                nel = tuple(nnel)
                if sel in self.vfiller_ids:
                    self.vfiller_ids[sel].resetGPos(nel)
                    self.vfiller_ids[nel] = self.vfiller_ids.pop(sel)
                else:
                    self.view_ids[self.vused_ids[sel][0]].resetGPos(nel)
                    self.vused_ids[nel] = self.vused_ids.pop(sel)
                    
        ### adjust buttons
        bis = self.buttons.keys()
        for bi in bis:
            but = self.buttons[bi]
            if but["action"][1] == -1:
                self.tabs["viz"]["tab"].GetSizer().Detach(but["button"])
                ddim = but["action"][0]
                ppos, pspan = ([1, 1], [1, 1])
                ppos[ddim] += self.getVizGridNbDim(ddim)
                pspan[1-ddim] = self.getVizGridNbDim(1-ddim)
                self.tabs["viz"]["tab"].GetSizer().Add(but["button"], pos=ppos, span=pspan, flag=wx.EXPAND|wx.ALIGN_CENTER, border=0)
            elif but["action"][0] == dim and but["action"][1] == self.getVizGridNbDim(dim)+1:
                bb = self.buttons.pop(bi)
                self.tabs["viz"]["tab"].GetSizer().Detach(bb["button"])
                bb["button"].Destroy()

    def addVizExts(self):
        sizeb = (self.getVizBbsiz(), 1)
        for which in [0, 1]:
            posb = [0,0]
            for i in range(1, self.getVizGridNbDim(which)+1):
                bid = wx.NewId()
                but = wx.Button(self.tabs["viz"]["tab"], bid, "", style=wx.NO_BORDER, size=(sizeb[which], sizeb[1-which]))
                but.SetBackgroundColour(self.color_drop)
                posb[which] = i
                self.tabs["viz"]["tab"].GetSizer().Add(but, pos=tuple(posb), flag=wx.EXPAND|wx.ALIGN_CENTER, border=0)
                self.buttons[bid] = {"action": (which, i), "button": but}
                but.Bind(wx.EVT_BUTTON, self.OnChangeGridViz)
                # but.Bind(wx.EVT_ENTER_WINDOW, self.OnPrintName)

            bid = wx.NewId()
            but = wx.Button(self.tabs["viz"]["tab"], bid, "", style=wx.NO_BORDER, size=(sizeb[1-which], sizeb[which]))
            but.SetBackgroundColour(self.color_add)
            ppos, pspan = ([1, 1], [1, 1])
            ppos[which] += self.getVizGridNbDim(which)
            pspan[1-which] = self.getVizGridNbDim(1-which)
            self.tabs["viz"]["tab"].GetSizer().Add(but, pos=ppos, span=pspan, flag=wx.EXPAND|wx.ALIGN_CENTER, border=0)
            self.buttons[bid] = {"action": (which, -1), "button": but}
            but.Bind(wx.EVT_BUTTON, self.OnChangeGridViz)
            ## but.Bind(wx.EVT_ENTER_WINDOW, self.OnPrintName)

    def setVizButtAble(self):
        for bi, bb in self.buttons.items():
            if bb["action"][1] == 1 and self.getVizGridNbDim(bb["action"][0]) == 1:
                bb["button"].Disable()
            else:
                bb["button"].Enable()

    # def OnPrintName(self, event=None):
    #     if event.GetId() in self.buttons:
    #         print "button", self.buttons[event.GetId()]["action"]
    #     else:
    #         print "button", event.GetId(), "not there"
    #     event.Skip()

    def OnChangeGridViz(self, event=None):
        if self.buttons[event.GetId()]["action"][1] == -1:
            self.incrementVizGridDim(self.buttons[event.GetId()]["action"][0])
        else:
            self.decrementVizGridDim(self.buttons[event.GetId()]["action"][0], self.buttons[event.GetId()]["action"][1])
    def setActiveViz(self, fid=None):
        for k,v in self.vfiller_ids.items():
            if k == fid:
                self.setVizcellSelected(fid)
                v.setActive()
            else:
                v.setUnactive()

    def resizeViz(self):
        if self.isReadyVizIntab():
            for (vid, view) in self.view_ids.items():
                if view.isIntab():
                    view._SetSize()
            for (vid, view) in self.vfiller_ids.items():
                view._SetSize()

    def hideShowBxViz(self):
        if self.isReadyVizIntab():
            for (vid, view) in self.view_ids.items():
                if view.isIntab():
                    view.hideShowOpt()
                    # view._SetSize()
            # for (vid, view) in self.vfiller_ids.items():
            #     view._SetSize()


    def setVizcellFreeded(self, pos):
        self.vused_ids.pop(pos)
        self.vfiller_ids[pos] = Filler(self, pos)
        self.updateVizcellSelected()

    def isVizSplit(self):
        return self.splitter.IsSplit()
    
    def vizTabToSplit(self):
        self.tabbed.RemovePage(self.viz_postab)
        self.tabs_keys.pop(self.viz_postab)
        self.tabs["viz"]["tab"].Reparent(self.splitter)
        self.splitter.SplitHorizontally(self.tabbed, self.tabs["viz"]["tab"])

    def vizSplitToTab(self):
        if self.splitter.IsSplit():
            self.splitter.Unsplit(self.tabs["viz"]["tab"])
        self.tabs["viz"]["tab"].Reparent(self.tabbed)
        self.tabbed.InsertPage(self.viz_postab, self.tabs["viz"]["tab"], self.tabs["viz"]["title"])
        self.tabs["viz"]["tab"].Show()
        self.tabs_keys.insert(self.viz_postab, "viz")

    def OnSplitchange(self, event):
        if self.hasVizIntab():
            if self.viz_postab < len(self.tabs_keys) and self.tabs_keys[self.viz_postab] == "viz":
                self.vizTabToSplit()
            else:
                self.vizSplitToTab()
            self.hideShowBxViz()
            self.doUpdates({"menu":True})
        self.buttViz.SetBackgroundColour(getRandomColor())
                
######################################################################
###########     MENUS
######################################################################

    def callOnTab(self, source_id=None, meth=None, args={}):
        if source_id is not None and source_id in self.tabs:
            try:
                mett = getattr(self.tabs[source_id]["tab"], meth)
                return mett(**args)
            except AttributeError:
                return None

    def updateProgressBar(self):
        if not self.plant.getWP().isActive():
            work_estimate, work_progress = (0, 0)
        else:
            work_estimate, work_progress = self.plant.getWP().getWorkEstimate()
        # print "PROGRESS", work_estimate, work_progress, type(work_estimate)
        if work_estimate > 0:
            self.progress_bar.SetRange(10**5)
            self.progress_bar.SetValue(math.floor(10**5*(work_progress/float(work_estimate))))
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

                ID_NOR = wx.NewId()
                m_nor = menuRed.Append(ID_NOR, "&Normalize", "Normalize current redescription.")
                frame.Bind(wx.EVT_MENU, self.OnNormalize, m_nor)

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

            #### not for popup menu
            if self.hasVizIntab():
                ID_CHECK = wx.NewId()
                m_check = menuViz.AppendCheckItem(ID_CHECK, "Plot in tab", "Plot inside visualization tab.")
                frame.Bind(wx.EVT_MENU, self.OnVizCheck, m_check)
                if self.intab:
                    m_check.Check()
            
        if self.selectedTab["type"] in ["Var","Reds", "Row"]:
            if "tab" in self.selectedTab and self.selectedTab["tab"].GetNumberRows() > 0:
                queries = None
                if self.selectedTab["type"] == "Reds":
                    queries = self.selectedTab["tab"].getSelectedQueries()
                for item in self.getViewsItems(self.selectedTab["type"], queries=queries):
                    ID_NEWV = wx.NewId()
                    m_newv = menuViz.Append(ID_NEWV, "%s" % item["title"],
                                              "Plot %s in new window." % item["title"])
                    frame.Bind(wx.EVT_MENU, self.OnNewV, m_newv)
                    self.ids_viewT[ID_NEWV] = item["viewT"]
        return menuViz

    def getViewsItems(self, tab_type=None, queries=None, excludeT=None):
        return ViewFactory.getViewsInfo(tab_type, self.dw.isGeospatial(), queries, excludeT)

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
        if self.plant.getWP().nbWorkers() == 0:
            ID_NOP = wx.NewId()
            m_nop = menuStop.Append(ID_NOP, "No process running", "There is no process currently running.")
            menuStop.Enable(ID_NOP, False)

        else:
            for wdt in self.plant.getWP().getWorkersDetails(): 
                ID_STOP = wx.NewId()
                self.ids_stoppers[ID_STOP] = wdt["wid"] 
                m_stop = menuStop.Append(ID_STOP, "Stop %s #&%s" % (wdt["wtyp"], wdt["wid"]), "Interrupt %s process #%s." % (wdt["wtyp"], wdt["wid"]))
                frame.Bind(wx.EVT_MENU, self.OnStop, m_stop)
        if self.plant.getWP().isActive():
            menuStop.AppendSeparator()
            ID_PLT = wx.NewId()
            m_plt = menuStop.Append(ID_PLT, self.plant.getWP().infoStr(), "Where processes are handled.")
            menuStop.Enable(ID_PLT, False)

        return menuStop

    def makeViewsMenu(self, frame, menuViews=None):
        if menuViews is None:
            menuViews = wx.Menu()

        menuViews.AppendMenu(wx.NewId(), "&Tabs",self.makeTabsMenu(frame))

        for vid, desc in sorted([(vid, view.getShortDesc()) for (vid, view) in self.view_ids.items() if not view.isIntab()], key=lambda x: x[1]):
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

        ## Save  
        m_save = menuFile.Append(wx.ID_SAVE, "&Save\tCtrl+S", "Save the current project.")
        if self.getData() is not None and self.dw.isFromPackage and self.dw.getPackageSaveFilename() is not None:
            frame.Bind(wx.EVT_MENU, self.OnSave, m_save)
        else:
            menuFile.Enable(wx.ID_SAVE, False)

        ## Save As...
        m_saveas = menuFile.Append(wx.ID_SAVEAS, "Save &As...\tShift+Ctrl+S", "Save the current project as...")
        if self.getData() is None:
            menuFile.Enable(wx.ID_SAVEAS, False)
        else:
            frame.Bind(wx.EVT_MENU, self.OnSaveAs, m_saveas)

        ## Import submenu
        submenuImport = wx.Menu()
        #submenuImportData = wx.Menu()
        ID_IMPORT_DATA_CSV = wx.NewId()
        m_impDataCSV = submenuImport.Append(ID_IMPORT_DATA_CSV, "Import Data", "Import data in CSV format.")
        frame.Bind(wx.EVT_MENU, self.OnImportDataCSV, m_impDataCSV)
        # ID_IMPORT_DATA_XML = wx.NewId()
        # m_impDataXML = submenuImport.Append(ID_IMPORT_DATA_XML, "Import Data from XML", "Import data in XML format.")
        # frame.Bind(wx.EVT_MENU, self.OnImportDataXML, m_impDataXML)
        # ID_IMPORT_DATA_TRIPLE = wx.NewId()
        # m_impDataTriple = submenuImport.Append(ID_IMPORT_DATA_TRIPLE, "Import Data from separate files", "Import data from separate files")
        # frame.Bind(wx.EVT_MENU, self.OnImportData, m_impDataTriple)
        
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

        
        ## Export submenu
        submenuExport = wx.Menu() # Submenu for exporting
        
        ID_EXPORT_REDESCRIPTIONS = wx.NewId()
        m_exportRedescriptions = submenuExport.Append(ID_EXPORT_REDESCRIPTIONS, "&Export Redescriptions\tShift+Ctrl+E", "Export redescriptions.")
        if len(self.getReds()) == 0:
            submenuExport.Enable(ID_EXPORT_REDESCRIPTIONS, False)
        else:
            frame.Bind(wx.EVT_MENU, self.OnExportRedescriptions, m_exportRedescriptions)

        ID_EXPORT_PREF = wx.NewId()
        m_exportPref = submenuExport.Append(ID_EXPORT_PREF, "&Export Preferences", "Export preferences.")
        frame.Bind(wx.EVT_MENU, self.OnExportPreferences, m_exportPref)

        ID_EXPORT = wx.NewId()
        m_export = menuFile.AppendMenu(ID_EXPORT, "&Export", submenuExport)
        
        ## Preferences
        menuFile.AppendSeparator()
        m_preferencesdia = menuFile.Append(wx.ID_PREFERENCES, "P&references...\tCtrl+,", "Set preferences.")
        frame.Bind(wx.EVT_MENU, self.OnPreferencesDialog, m_preferencesdia)

        ## Worker setup
        if True:
                ID_CONN = wx.NewId()
                m_conndia = menuFile.Append(ID_CONN, "Wor&ker setup...\tCtrl+k", "Setup worker's connection.")
                frame.Bind(wx.EVT_MENU, self.OnConnectionDialog, m_conndia)

        ## Split setup
        if True:
                ID_SPLT = wx.NewId()
                m_spltdia = menuFile.Append(ID_SPLT, "Sp&lits setup...\tCtrl+l", "Setup learn/test data splits.")
                frame.Bind(wx.EVT_MENU, self.OnSplitDialog, m_spltdia)

        menuFile.AppendSeparator()
        ## Quit
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

    def deleteView(self, vK, freeing=True):
        if vK in self.view_ids:
            self.plant.getWP().layOff(self.plant.getWP().findWid([("wtyp", "project"), ("vid", vK)]))
            if not self.view_ids[vK].isIntab():
                self.view_ids[vK].mapFrame.Destroy()
            else:
                pos = self.view_ids[vK].getGPos()
                panel = self.view_ids[vK].popSizer()
                panel.Destroy()
                if freeing:
                    self.setVizcellFreeded(pos)
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

        if self.dw.getPackageSaveFilename() is not None:
            dir_name = os.path.dirname(self.dw.getPackageSaveFilename())
        else:
            dir_name = os.path.expanduser('~/')
        path = dir_name            
        open_dlg = wx.FileDialog(self.toolFrame, message='Choose a file', defaultDir=dir_name,  
			wildcard=wcd, style=wx.OPEN|wx.CHANGE_DIR)
        if open_dlg.ShowModal() == wx.ID_OK:
            path = open_dlg.GetPath()
            self.LoadFile(path)
        open_dlg.Destroy()
        self.changePage("reds")
        # DEBUGGING
        #wx.MessageDialog(self.toolFrame, 'Opened package from '+path).ShowModal()

    def LoadFile(self, path):
        try:
            self.dw.openPackage(path)
        except:
            raise
            return False
        else:
            self.reloadAll()
            return True

    def expand(self, params={}):
        if params is None:
            params = {}
        self.progress_bar.Show()
        if "red" in params and params["red"] is not None and params["red"].length(0) + params["red"].length(1) > 0:
            self.plant.getWP().addWorker("expander", self, params,
                                 {"results_track":0,
                                  "batch_type": "partial",
                                  "results_tab": "exp"})
        else:
            self.plant.getWP().addWorker("miner", self, params,
                                 {"results_track":0,
                                  "batch_type": "final",
                                  "results_tab": "exp"})
        self.checkResults(menu=True)

    def project(self, proj=None, vid=None):
        self.progress_bar.Show()
        if proj is not None and vid is not None:
            wid = self.plant.getWP().findWid([("wtyp", "projector"), ("vid", vid)])
            if wid is None:
                self.plant.getWP().addWorker("projector", self, proj,
                                     {"vid": vid})
                self.checkResults(menu=True)

    def checkResults(self, menu=False):
        updates = self.plant.getWP().checkResults(self)
        if menu:
            updates["menu"] = True
        if self.plant.getWP().nbWorking() > 0:
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
            self.appendLog("\n\n***" + updates["error"] + "***\n")
        if "menu" in updates:
            self.updateMenus()
        if "progress" in updates:
            self.updateProgressBar()
        if "status" in updates:
            self.statusbar.SetStatusText(updates["status"], 1)
        if "log" in updates:
            self.appendLog(updates["log"])

    def loggingDWError(self, output, message, type_message, source):
        self.errorBox(message)
        self.appendLog("\n\n***" + message + "***\n")

    def loggingLogTab(self, output, message, type_message, source):
        text = "%s" % message
        header = "@%s:\t" % source
        text = text.replace("\n", "\n"+header)
        self.appendLog(text+"\n")

    def appendLog(self, text):
        self.tabs["log"]["text"].AppendText(text)


    def OnStop(self, event):
        if event.GetId() in self.ids_stoppers:
            self.plant.getWP().layOff(self.ids_stoppers[event.GetId()])
            self.checkResults(menu=True)

    def OnViewTop(self, event):
        if event.GetId() in self.opened_views and \
               self.opened_views[event.GetId()] in self.view_ids:
            self.view_ids[self.opened_views[event.GetId()]].toTop()

    def OnCloseViews(self, event):
        view_keys = self.view_ids.keys()
        for key in view_keys:
            if self.view_ids[key].isIntab():
                self.view_ids[key].OnQuit()
        self.toTop()
            
    def OnSave(self, event):
        if not (self.dw.isFromPackage and self.dw.getPackageSaveFilename() is not None):
            wx.MessageDialog(self.toolFrame, 'Cannot save data that is not from a package\nUse Save As... instead', style=wx.OK|wx.ICON_EXCLAMATION, caption='Error').ShowModal()
            return
        try:
            self.dw.savePackage()
        except:
            pass
            
    def OnSaveAs(self, event):
        if self.dw.getPackageSaveFilename() is not None:
            dir_name = os.path.dirname(self.dw.getPackageSaveFilename())
        else:
            dir_name = os.path.expanduser('~/')

        save_dlg = wx.FileDialog(self.toolFrame, message="Save as", defaultDir=dir_name,
                                 style=wx.SAVE|wx.CHANGE_DIR)
        if save_dlg.ShowModal() == wx.ID_OK:
            path = save_dlg.GetPath()
            try:
                self.dw.savePackageToFile(path)
                self.updateMenus()
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

    # def OnImportData(self, event):
    #     """Shows a custom dialog to open the three data files"""
    #     if self.dw.getData() is not None:
    #         if not self.checkAndProceedWithUnsavedChanges():
    #             return
    #     if len(self.dw.reds) > 0:
    #         sure_dlg = wx.MessageDialog(self.toolFrame, 'Importing new data erases old redescriptions.\nDo you want to continue?', caption="Warning!", style=wx.OK|wx.CANCEL)
    #         if sure_dlg.ShowModal() != wx.ID_OK:
    #             return
    #         sure_dlg.Destroy()

    #     dlg = ImportDataDialog(self)
    #     dlg.showDialog()

    def OnImportDataCSV(self, event):
        """Shows a custom dialog to open the two data files"""
        if self.dw.getData() is not None:
            if not self.checkAndProceedWithUnsavedChanges():
                return
        if self.dw.reds is not None and len(self.dw.reds) > 0:
            sure_dlg = wx.MessageDialog(self.toolFrame, 'Importing new data erases old redescriptions.\nDo you want to continue?', caption="Warning!", style=wx.OK|wx.CANCEL)
            if sure_dlg.ShowModal() != wx.ID_OK:
                return
            sure_dlg.Destroy()

        dlg = ImportDataCSVDialog(self)
        dlg.showDialog()
        self.changePage("rows")
            
    # def OnImportDataXML(self, event):
    #     if self.dw.getData() is not None:
    #         if not self.checkAndProceedWithUnsavedChanges():
    #             return
    #     if self.dw.reds is not None and len(self.dw.reds) > 0:
    #         sure_dlg = wx.MessageDialog(self.toolFrame, 'Importing new data erases old redescriptions.\nDo you want to continue?', caption="Warning!", style=wx.OK|wx.CANCEL)
    #         if sure_dlg.ShowModal() != wx.ID_OK:
    #             return
    #         sure_dlg.Destroy()

    #     dir_name = os.path.expanduser('~/')
    #     open_dlg = wx.FileDialog(self.toolFrame, message="Choose file", defaultDir = dir_name,
    #                              style = wx.OPEN|wx.CHANGE_DIR)
    #     if open_dlg.ShowModal() == wx.ID_OK:
    #         path = open_dlg.GetPath()
    #         try:
    #             self.dw.importDataFromXMLFile(path)
    #         except:
    #             pass
    #         else:
    #             self.reloadAll()

    #     open_dlg.Destroy()
                
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
        self.changePage("reds")
        
    def OnExportRedescriptions(self, event):
        if len(self.getReds()) == 0:
            wx.MessageDialog(self.toolFrame, 'Cannot export redescriptions: no redescriptions loaded',
                             style=wx.OK|wx.ICON_EXCLAMATION, caption='Error').ShowModal()
            return
        
        if self.dw.getPackageSaveFilename() is not None:
            dir_name = os.path.dirname(self.dw.getPackageSaveFilename())
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

    def OnExportPreferences(self, event):
        if self.dw.getPackageSaveFilename() is not None:
            dir_name = os.path.dirname(self.dw.getPackageSaveFilename())
        else:
            dir_name = os.path.expanduser('~/')

        save_dlg = wx.FileDialog(self.toolFrame, message='Export preferences to:', defaultDir = dir_name, style = wx.SAVE|wx.CHANGE_DIR)
        if save_dlg.ShowModal() == wx.ID_OK:
            path = save_dlg.GetPath()
            try:
                self.dw.exportPreferences(path, inc_def=True)
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
            red = self.selectedTab["tab"].getSelectedItem()
            self.showTab("exp")
            if red is not None:
                params = {"red": red.copy()}
                self.expand(params)

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

    def OnNormalize(self, event):
        if self.selectedTab["type"] in ["Reds"]:
            red = self.selectedTab["tab"].getSelectedItem()
            if red is not None:
                redn, changed = red.getNormalized(self.dw.getData())
                if changed:
                    self.selectedTab["tab"].updateEdit(None, redn, self.selectedTab["tab"].getSelectedRow())
                if self.selectedTab["id"] != "hist":
                    self.tabs["hist"]["tab"].insertItem(red, row=-1)
                    
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
        restrict = self.dw.getData().nonselectedRows()
        for tab in self.tabs.values():
            if tab["type"] == "Reds":
                tab["tab"].recomputeAll(restrict)

    def OnVizCheck(self, event):
        self.intab = event.IsChecked()
            
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

    def OnConnectionDialog(self, event):
        d = ConnectionDialog(self.toolFrame, self.dw, self.plant)
        d.ShowModal()
        d.Destroy()

    def OnSplitDialog(self, event):
        d = SplitDialog(self.toolFrame, self.dw, self)
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
        import urllib
        import platform
        # DEBUG
        #self.toolFrame.Bind(wx.html2.EVT_WEBVIEW_ERROR, lambda evt: wx.MessageDialog(self.toolFrame, str(evt), style=wx.OK, caption='WebView Error').ShowModal())
        #self.toolFrame.Bind(wx.html2.EVT_WEBVIEW_LOADED, lambda evt: wx.MessageDialog(self.toolFrame, 'Help files loaded from '+evt.GetURL(), style=wx.OK, caption='Help files loaded!').ShowModal())
        if self.helpURL is None:
            self._onHelpOldSystem()
            return
        if self.helpFrame is None:
            self.helpFrame = wx.Frame(self.toolFrame, -1, self.titleHelp)
            self.helpFrame.Bind(wx.EVT_CLOSE, self._helpHTML2Close)
            sizer = wx.BoxSizer(wx.VERTICAL)
            url = 'file://'+os.path.abspath(self.helpURL)
            if platform.system() == "Darwin":
                # OS X returns UTF-8 encoded path names, decode to Unicode
                #url = url.decode('utf-8')
                # URLLIB doesn't like unicode strings, so keep w/ UTF-8 encoding
                # make the URL string URL-safe for OS X
                url = urllib.quote(url)
            browser = wx.html2.WebView.New(self.helpFrame, url=url)
            #browser.LoadURL('file://'+os.path.abspath(self.helpURL))
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
                dets += ("\t%s=\t%s\n" % (self.dw.getData().col(side,lit.colId()).getName(), self.dw.getData().getValue(side, lit.colId(), rid)))
        return dets

    def OnSize(self, event):
        self.resizeViz()
        event.Skip()
                
    def OnQuit(self, event):
        if self.plant.getWP().isActive():
            self.plant.getWP().closeDown(self)
        if not self.checkAndProceedWithUnsavedChanges(what="quit"):
                return
        self.deleteAllViews()
        self.toolFrame.Destroy()
        sys.exit()

    def OnLicense(self, event):
        import codecs # we want to be able to read UTF-8 license files
        license_text = None
        try:
            f = codecs.open(self.license_file, 'r', encoding='utf-8', errors='replace')
            license_text = f.read()
        except:
            wx.MessageDialog(self.toolFrame, 'No license found.', style=wx.OK, caption="No license").ShowModal()
            return

        external_license_texts = ''
        for ext in self.external_licenses:
            lic = 'LICENSE_'+ext
            try:
                f = codecs.open(findFile(lic, ["../../licenses", self.root_dir+"/licenses", "./licenses"]), 'r', encoding='utf-8', errors='replace')
                external_license_texts += '\n\n***********************************\n\n' + f.read()
                f.close()
            except:
                pass # We don't care about errors here

        if len(external_license_texts) > 0:
            license_text += "\n\nSiren comes bundled with other software for your convinience.\nThe licenses for this bundled software are below." + external_license_texts

        # Show dialog
        try:
            dlg = wx.lib.dialogs.ScrolledMessageDialog(self.toolFrame, license_text, "LICENSE")
        except Exception as e:
            wx.MessageDialog(self.toolFrame, 'Cannot show the license: '+str(e), style=wx.OK, caption="ERROR").ShowModal()
            sys.stderr.write(str(e))
        else:
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
        self.constraints = Constraints(self.dw.getData(), self.dw.getPreferences())

    def resetLogger(self):
        verb = 1
        if self.dw.getPreferences() is not None and self.dw.getPreference('verbosity') is not None:
            verb = self.dw.getPreference('verbosity')

        self.logger.resetOut()
        if self.plant.getWP().isActive() and self.plant.getWP().getOutQueue() is not None:
            self.logger.addOut({"log": verb, "error": 0, "status":1, "time":0, "progress":2, "result":1}, self.plant.getWP().getOutQueue(), self.plant.getWP().sendMessage)
        else:
            self.logger.addOut({"*": verb,  "error":1,  "status":0, "result":0, "progress":0}, None, self.loggingLogTab)
        self.logger.addOut({"error":1, "dw_error":1}, "stderr")
        self.logger.addOut({"dw_error":1}, None, self.loggingDWError)

    def reloadAll(self):
        if self.plant is not None:
            self.plant.getWP().closeDown(self)
        self.reloadVars(review=False)
        self.reloadRows()

        # self.plant, msg, err = toolCommMultip.getWP("127.0.0.1", 55444, "sesame")
        # self.plant = toolWP.setupWorkPlant(self.dw.getPreference("workserver_ip"), self.dw.getPreference("workserver_port"), self.dw.getPreference("workserver_authkey"))
        # msg, err = self.plant.getWP().reset(self.dw.getPreference("workserver_ip"), self.dw.getPreference("workserver_port"), self.dw.getPreference("workserver_authkey"))
        # self.logger.printL(1, msg, "status", "WP")
        # if len(err) > 0:
        #     self.logger.printL(1, err, "error", "WP")
        self.reloadReds()
        self.reloadVizTab()

    def reloadVars(self, review=True):
        ## Initialize variable lists data
        for side in [0,1]:
            if self.dw.getData() is not None:
                self.tabs[side]["tab"].resetData(self.dw.getDataCols(side))
            else:
                self.tabs[side]["tab"].resetData(ICList())
        if self.dw.getData() is not None:
            details = {"names": self.dw.getData().getNames()}
            for tk, tv in self.tabs.items():
                if tv["type"] == "Reds":
                    tv["tab"].resetDetails(details, review)
                elif tv["type"] == "Row":
                    tv["tab"].resetFields(self.dw, review)

    def reloadRows(self):
        ## Initialize variable lists data
        if self.dw.getData() is not None:
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
        self.statusbar.SetStatusText(short_msg, 1)
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
        self.statusbar.SetStatusText(msg, 1)
        
    def errorBox(self, message):
        if self.busyDlg is not None:
            del self.busyDlg
            self.busyDlg = None
        dlg = wx.MessageDialog(self.toolFrame, message, style=wx.OK|wx.ICON_EXCLAMATION|wx.STAY_ON_TOP, caption="Error")
        dlg.ShowModal()
        dlg.Destroy()

    # def warningBox(self, message):
    #     # if self.busyDlg is not None:
    #     #     del self.busyDlg
    #     #     self.busyDlg = None
    #     dlg = wx.MessageDialog(self.toolFrame, message, style=wx.OK|wx.ICON_INFORMATION|wx.STAY_ON_TOP, caption="Warning")
    #     dlg.ShowModal()
    #     dlg.Destroy()

    def readyReds(self, reds, tab):
        if len(reds) > 0 and tab in self.tabs:
            for red in reds:
                red.recompute(self.getData())
                red.setRestrictedSupp(self.getData())
            self.tabs[tab]["tab"].insertItems(reds)

    def readyProj(self, vid, proj):
        if vid in self.view_ids:
            self.view_ids[vid].readyProj(proj)
