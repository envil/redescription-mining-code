import os, os.path, random, re, numpy, glob
import time, math
import sys
import pickle

import wx, wx.adv
# import wx.lib.agw.pybusyinfo as PBI

### from wx import AboutBox, AboutDialogInfo, Bitmap, BoxSizer, BusyInfo, Button, CallLater, DefaultPosition, DisplaySize, FileDialog, Frame, Gauge, GridBagSizer, GridSizer, Icon
### from wx import ALIGN_CENTER, BITMAP_TYPE_PNG, CANCEL, CHANGE_DIR, DEFAULT_FRAME_STYLE, VERTICAL, VSCROLL, YES_NO, EXPAND, GA_HORIZONTAL, GA_SMOOTH, HSCROLL
### from wx import NB_TOP,  NO_BORDER, NO_DEFAULT, OK, OPEN, SAVE, STAY_ON_TOP, TE_MULTILINE, TE_READONLY, TE_RICH, TOP
### from wx import EVT_BUTTON, EVT_CLOSE, EVT_ENTER_WINDOW, EVT_LEFT_UP, EVT_MENU, EVT_NOTEBOOK_PAGE_CHANGED, EVT_SIZE, EVT_SPLITTER_UNSPLIT
### from wx import ICON_EXCLAMATION, ICON_INFORMATION
### from wx import ID_ABOUT, ID_COPY, ID_CUT, ID_EXIT, ID_HELP, ID_NO, ID_OK, ID_OPEN, ID_PASTE, ID_PREFERENCES, ID_SAVE, ID_SAVEAS
### from wx import Menu, MenuBar, MessageDialog, NewId, Notebook, NullBitmap, Panel, ScrolledWindow, SplitterWindow, StaticBitmap, TextCtrl, ToggleButton

import wx.lib.dialogs

WITHVIEWS = True #False

from ..clired.toolLog import Log
from ..clired.classProps import findFile
from ..clired.classRedescription import Redescription
from ..clired.classCol import DataError, ColM
from ..clired.classQuery import Literal, Query
from ..clired.classData import RowE, Data

from .DataWrapper import DataWrapper
from .classGridTable import RowTable
from .classContentTable import RedsTable, VarsTable
from .classPreferencesDialog import PreferencesDialog
from .classConnectionDialog import ConnectionDialog
from .classFoldsDialog import FoldsDialog
from .classExtensionsDialog import ExtensionsDialog
from .miscDialogs import ImportDataCSVDialog, ExportFigsDialog, FindDialog, MultiSelectorDialog, ChoiceElement
from ..work.toolWP import WorkPlant
from ..work.classWorkClient import WorkClient
from ..common_details import common_variables
if WITHVIEWS:
    from ..views.classVizManager import VizManager
    from ..views.classViewsManager import ViewsManager

import pdb

  
def getRandomColor():
    return (random.randint(0,255), random.randint(0,255), random.randint(0,255))

Redescription.setUidGen(mp_lock=True)

class ERCache():
    
    def __init__(self, parent):
        self.parent = parent
        self.rids = []
        self.spids = None
        self.etor = None
        self.ddER = None

    def getRids(self):
        return self.rids
    def getSPids(self):
        return self.spids

    def gatherReds(self, spids=None):
        reds_map = self.parent.getAllReds()
        self.setReds(reds_map, spids)

    def needsRecompute(self, spids=None):
        if self.etor is None:
            return True
        reds_map = self.parent.getAllReds()
        rids = [rid for (rid, red) in reds_map]
        return rids != self.getRids() or spids != self.getSPids()
        
        
    def setReds(self, reds_map, spids=None):
        self.etor = None
        self.ddER = None
        reds = dict(reds_map)
        self.rids = [rid for (rid, red) in reds_map]
        self.spids = spids
        
        nbE = 0
        if len(self.rids) > 0:
            nbE = reds[self.rids[0]].sParts.nbRows()
        self.etor = numpy.zeros((nbE, len(self.rids)), dtype=bool)
        for r, rid in enumerate(self.rids):
            if spids == "I" or spids is None:
                self.etor[list(reds[rid].getSuppI()), r] = True
            elif spids == "U":
                self.etor[list(reds[rid].getSuppU()), r] = True
            else:
                for pid in spids:
                    self.etor[list(reds[rid].supports().part(pid)), r] = True

    def getRPos(self, rids):
        r_to_p = dict([(r,p) for (p,r) in enumerate(self.rids)])
        return [r_to_p[rid] for rid in rids if rid in r_to_p]
            
    def getEtoR(self, rids=None, eids=None, spids=None):
        if self.needsRecompute(spids):
            self.gatherReds(spids)
            
        sub_etor = self.etor
        if eids is not None:
            sub_etor = sub_etor[eids,:]
        if rids is not None:
            ps = self.getRPos(rids)
            return sub_etor[:,ps]
        return sub_etor
    
    def computeDeduplicateER(self, etor=None, spids=None):
        if etor is None:
            if self.etor is None:
                self.gatherReds(spids)
            etor = self.etor

        nbE, nbR = etor.shape
        if etor.dtype == "bool": ### etor is boolean

            eb, rb = ({}, {})
            matches_E_ones, matches_E_zeroes = numpy.zeros((1,1), dtype=int), nbR*numpy.ones((1,1), dtype=int)
            matches_R_ones, matches_R_zeroes = numpy.zeros((nbR,nbR), dtype=int), nbE*numpy.ones((nbR,nbR), dtype=int)
            keep_es, e_to_rep = numpy.array([], dtype=int), -numpy.ones(nbE, dtype=int)
            keep_rs, r_to_rep = numpy.array([nbR-1], dtype=int), -numpy.ones(nbR, dtype=int)
            
            if not numpy.any(etor): ### etor is all empty > no need to check matches, construct results quickly
                r_to_rep = numpy.zeros(nbR, dtype=int)
            else: 
                matches_R_ones = numpy.dot(1*etor.T, 1*etor)        
                matches_R_zeroes = numpy.dot(1-etor.T, 1-etor)
                matches_E_ones = numpy.dot(1*etor, 1*etor.T)
                matches_E_zeroes = numpy.dot(1-etor, 1-etor.T)

                #### DE-DUPLICATE REDS
                for x,y in zip(*numpy.where(numpy.triu(matches_R_zeroes + matches_R_ones, 1) >= nbE)):
                    rb[x] = y
                keep_rs = numpy.array([i for i in range(nbR) if i not in rb], dtype=int)
                            
                #### DE-DUPLICATE ENTITIES
                ### e_to_rep == -1 -> entity does not support any red        
                for x,y in zip(*numpy.where(numpy.triu(matches_E_zeroes + matches_E_ones, 1) >= nbR)):
                    eb[x] = y
                keep_es = numpy.array([i for i in range(nbE) if i not in eb and numpy.sum(etor[i,:])>0], dtype=int)

                r_to_rep[keep_rs] = numpy.arange(len(keep_rs))
                if len(rb) > 0:
                    rfrm, rtt = zip(*rb.items())
                    r_to_rep[numpy.array(rfrm)] = r_to_rep[numpy.array(rtt)]
                
                e_to_rep[keep_es] = numpy.arange(len(keep_es))
                if len(eb) > 0:
                    efrm, ett = zip(*eb.items())
                    e_to_rep[numpy.array(efrm)] = e_to_rep[numpy.array(ett)]
                
            r_counts, e_counts = numpy.bincount(r_to_rep), numpy.bincount(e_to_rep+1)

        else:
            CCR = numpy.corrcoef(etor.T)
            matches_R_ones = numpy.array(numpy.maximum(0,CCR)*nbE, dtype=int)
            matches_R_zeroes = numpy.array(numpy.maximum(0,-CCR)*nbE, dtype=int)

            CCE = numpy.corrcoef(etor)
            matches_E_ones = numpy.array(numpy.maximum(0,CCE)*nbR, dtype=int)
            matches_E_zeroes = numpy.array(numpy.maximum(0,-CCE)*nbR, dtype=int)
            # matches_R_ones = numpy.zeros((etor.shape[1], etor.shape[1]), dtype=int)
            # matches_E_ones = numpy.zeros((etor.shape[0], etor.shape[0]), dtype=int)
            # for i in range(etor.shape[1]):
            #     matches_R_ones[i,i] = nbE
            #     for j in range(i):
            #         matches_R_ones[i,j] = numpy.sum(etor[:,i]==etor[:,j])
            # for i in range(etor.shape[0]):
            #     matches_E_ones[i,i] = nbR
            #     for j in range(i):
            #         matches_E_ones[i,j] = numpy.sum(etor[i,:]==etor[j,:])
            # matches_R_zeroes = numpy.zeros(matches_R_ones.shape, dtype=int)
            # matches_E_zeroes = numpy.zeros(matches_E_ones.shape, dtype=int)

            keep_rs = numpy.arange(nbR)
            r_to_rep = numpy.arange(nbR)
            keep_es = numpy.arange(nbE)
            e_to_rep = numpy.arange(nbE)
            r_counts, e_counts = numpy.ones(nbR, dtype=int), numpy.ones(nbE+1, dtype=int)
            
        # e_counts = numpy.concatenate((e_counts[1:], [e_counts[0]])) ### put -1 counts to end
        xps = {"E": {"nb": nbE, "nb_other": nbR, "rprt": keep_es, "to_rep": e_to_rep, "counts": e_counts[1:],
              "matches_ones": matches_E_ones[keep_es,:][:, keep_es],
              "matches_zeroes": matches_E_zeroes[keep_es,:][:, keep_es]},
              "R": {"nb": nbR, "nb_other": nbE, "rprt": keep_rs, "to_rep": r_to_rep, "counts": r_counts,
              "matches_ones": matches_R_ones[keep_rs,:][:, keep_rs],
              "matches_zeroes": matches_R_zeroes[keep_rs,:][:, keep_rs]}}
        return xps 

    def getDeduplicateER(self, rids=None, eids=None, spids=None):
        if self.etor is None:
            self.gatherReds(spids)

        if eids is None:
            eids = numpy.arange(self.etor.shape[0])
        if rids is None:
            rids = numpy.arange(self.etor.shape[1])
        ps = self.getRPos(rids)
        return self.computeDeduplicateER(self.etor[eids,:][:,ps], spids)


class ProjCache():

    def __init__(self, capac=10):
        self.cache = {}
        ### for now, unused
        self.capac = capac

    def queryPC(self, proj, vid):
        phsh = "%s:%s" % (vid[0], proj.getParamsHash())
        if phsh in self.cache:
            if self.cache[phsh]["coords"] is not None:
                proj.setCoords(self.cache[phsh]["coords"])
                self.cache[phsh]["served"].append((vid, proj)) 
                return 0
            else:
                self.cache[phsh]["waiting"].append((vid, proj)) 
                return 1
        elif "random_state" not in proj.getParameters():
            self.cache[phsh] = {"coords": None, "waiting": [], "served": []}
        return -1

    def incomingPC(self, proj, vid):
        phsh = "%s:%s" % (vid[0], proj.getParamsHash())
        if phsh in self.cache:
            self.cache[phsh]["coords"] = proj.getCoords()
            while len(self.cache[phsh]["waiting"]) > 0:
                tmp =  self.cache[phsh]["waiting"].pop()
                tmp[1].setCoords(self.cache[phsh]["coords"])
                self.cache[phsh]["served"].append(tmp)
            return self.cache[phsh]["served"] 
        return []
 
class Siren():
    """ The main frame of the application
    """
    
    siren_srcdir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if sys.platform == 'win32' and siren_srcdir.find("library.zip") > -1:
        siren_srcdir = re.sub("library.zip.*", "", siren_srcdir)
    if 'SIRENDATA' in os.environ:
        siren_datadir = os.environ['SIRENDATA']
        if not os.path.isdir(siren_datadir):
            raise RuntimeError('Path in environment SIRENDATA not a directory')
    else:
        siren_datadir = os.path.join(siren_srcdir, 'data')
        if not os.path.isdir(siren_datadir):
            siren_datadir = siren_srcdir    
        
    @classmethod
    def searchData(tcl, filen, folder=None, path=[], pref='data/'):
        ff = []
        for fldr in path:
            ff += ['../'+fldr, tcl.siren_srcdir+'/'+fldr]
        if folder is not None:
            ff += ['../'+pref+folder, tcl.siren_datadir+'/'+folder]
        return findFile(filen, path+ff)
        # tmp = findFile(filen, ff)
        # if tmp is None:
        #    raise Exception("findFile %s %s\t-->\t%s" % (filen, path+ff, tmp))
        #    print("findFile %s %s\t-->\t%s" % (filen, ff, tmp))
        # return tmp
    
    @classmethod
    def initIcons(tcl, icons_setts, path=[]):
        icons = {}
        for icon_name, icon_file in icons_setts.items():
            tmp = tcl.searchData(icon_file+".png", "icons", path)
            if tmp is not None:    
                icons[icon_name] = wx.Bitmap(tmp)
            else:
                icons[icon_name] = wx.NullBitmap
        return icons    
    @classmethod
    def initConfs(tcl, cfiles):
        conf_defs = []
        for (filen, folder) in cfiles:
            cf = tcl.searchData(filen, "conf", path=[folder])
            if cf is not None:
                conf_defs.append(cf)
        return conf_defs
    @classmethod
    def initProps(tcl, vffiles, rffiles):
        vfields_fns = []
        for filen, folder in vffiles:
            cf = tcl.searchData(filen, "conf", path=[folder])
            if cf is not None:                
                vfields_fns.append(cf)
                for mf in glob.glob(re.sub(filen, tcl.vff_mtch, cf)):
                    if mf != cf:
                        vfields_fns.append(mf)
        ColM.setupRP(vfields_fns)

        rfields_fns = []
        for filen, folder in rffiles:
            cf = tcl.searchData(filen, "conf", path=[folder])
            if cf is not None:                
                rfields_fns.append(cf)
                for mf in glob.glob(re.sub(filen, tcl.rff_mtch, cf)):
                    if mf != cf:
                        rfields_fns.append(mf)
        Redescription.setupRP(rfields_fns)
    
    titleTool = common_variables["PROJECT_NAME"]+' :: tools'
    titlePref = common_variables["PROJECT_NAME"]+' :: '
    titleHelp = common_variables["PROJECT_NAME"]+' :: help'
    helpInternetURL = common_variables["PROJECT_URL"]+'help'
    
    # For About dialog
    name = common_variables["PROJECT_NAME"]    
    programURL = common_variables["PROJECT_URL"]
    version = common_variables["VERSION"]
    cpyright = '(c) '+common_variables["COPYRIGHT_YEAR_FROM"]+'-' \
               +common_variables["COPYRIGHT_YEAR_TO"]+' ' \
               +common_variables["PROJECT_AUTHORS"]
    about_text = common_variables["PROJECT_DESCRIPTION_LINE"]+"\n"

    icons_setts = {"split_frame": "split",
                   "unsplit_frame": "unsplit",
                   "learn_act": "learn_act", 
                   "test_act": "test_act",
                   "learn_dis": "learn_dis",
                   "test_dis": "test_dis",
                   "kil": "cross",
                   "stamp": "stamp",
                   "inout": "up_right",
                   "outin": "down_right",
                   "save": "savefig"}

    main_tabs_ids = {"r": "reds", "e": "rows", "t": "log", "z": "viz", "v0": 0, "v1": 1, "v": "vars"}

    external_licenses = ['basemap', 'matplotlib', 'python', 'wx', 'grako']
    rffiles = [('fields_rdefs_basic.txt', 'clired')]
    vffiles = [('fields_vdefs_basic.txt', 'clired')]
    rff_mtch = 'fields_rdefs_*.txt'
    vff_mtch = 'fields_vdefs_*.txt'
    cfiles = [('miner_confdef.xml', 'clired'), ('dataext_confdef.xml', 'clired'), ('ui_confdef.xml', 'interface')]
    if WITHVIEWS:
        cfiles.append(('views_confdef.xml', 'views'))
    cfiles_io = [('inout_confdef.xml', 'clired')]
    
    results_delay = 1000

    def addTmpStore(self, k,v):
        self.tmp_store[k] = v
    def getTmpStore(self, k):
        return self.tmp_store.get(k)
        
    
    def __init__(self):
        self.tmp_store = {}
        self.initialized = True
        self.busyDlg = None
        self.findDlg = None
        self.proj_cache = ProjCache()
        self.er_cache = ERCache(self)
        self.dw = None
        self.vizm = None
        self.plant = WorkPlant()
        if WITHVIEWS:
            self.viewsm = ViewsManager(self)
        else:
            self.viewsm = None

        self.conf_defs = Siren.initConfs(self.cfiles)
        self.conf_defs_io = Siren.initConfs(self.cfiles_io)
        self.icon_file = Siren.searchData('siren_icon32x32.png', 'icons')
        self.license_file = Siren.searchData('LICENSE', 'licenses')
        self.helpURL = Siren.searchData('index.html', 'help')

                    # {"id": self.getDefaultTabId("v0"), "title":"LHS Variables",
                    #  "short": "LHS", "type":"v", "hide":False, "style":None},
                    # {"id": self.getDefaultTabId("v1"), "title":"RHS Variables",
                    #  "short": "RHS", "type":"v", "hide":False, "style":None},
        
        tmp_tabs = [{"id": self.getDefaultTabId("e"), "title":"Entities",
                     "short": "Ent", "type":"e", "style":None},
                    {"id": self.getDefaultTabId("v"), "title":"Variables",
                     "short": "Vars", "type":"v", "style":None},
                    {"id": self.getDefaultTabId("r"), "title":"Redescriptions",
                     "short": "Reds", "type":"r", "style":None},
                    {"id": self.getDefaultTabId("t"), "title":"Log",
                     "short": "Log", "type":"t", "style": wx.TE_READONLY|wx.TE_MULTILINE},
                    ]
        if self.withViews():
            tmp_tabs.insert(3, {"id": self.getDefaultTabId("z"), "title":"Visualizations",
                "short": "Viz", "type":"z", "style":None})
            
            
        self.tabs = dict([(p["id"], p) for p in tmp_tabs])
        self.tabs_keys = [p["id"] for p in tmp_tabs]
        stn = list(self.tabs.keys())[0]
        if self.getDefaultTabId("v") in self.tabs:
            stn = self.getDefaultTabId("v")
        elif self.getDefaultTabId("e") in self.tabs:
            stn = self.getDefaultTabId("e")
        self.selectedTab = self.tabs[stn]

        self.logger = Log()
        self.icons = Siren.initIcons(self.icons_setts)
        Siren.initProps(self.vffiles, self.rffiles)
        tmp = wx.DisplaySize()
        self.toolFrame = wx.Frame(None, -1, self.titleTool, pos = wx.DefaultPosition,
                                  size=(tmp[0]*0.66,tmp[1]*0.9), style = wx.DEFAULT_FRAME_STYLE)

        self.toolFrame.Bind(wx.EVT_CLOSE, self.OnQuit)
        self.toolFrame.Bind(wx.EVT_SIZE, self.OnSize)
        self.toolFrame.SetIcon(wx.Icon(self.icon_file, wx.BITMAP_TYPE_PNG))

        self.buffer_copy = None
        
        self.call_check = None

        self.dw = DataWrapper(self.logger, conf_defs=self.conf_defs)
        
        self.create_tool_panel()
        self.changePage(stn)       

        ### About dialog
        self.info =  wx.adv.AboutDialogInfo()
        self.info.SetName(self.name)
        self.info.SetWebSite(self.programURL)
        self.info.SetCopyright(self.cpyright)
        self.info.SetVersion(self.version)
        self.info.SetIcon(wx.Icon(self.icon_file, wx.BITMAP_TYPE_PNG))
        self.info.SetDescription(self.about_text)
        #with open(self.licence_file) as f:
        #    self.info.SetLicence(f.read())

        self.helpFrame = None
        
        ## Register file reading message functions to DataWrapper
        self.dw.registerStartReadingFileCallback(self.startFileActionMsg)
        self.dw.registerStopReadingFileCallback(self.stopFileActionMsg)

        ### INITIALISATION OF DATA
        self.toolFrame.Show()
        
        ### W/O THIS DW THINK IT'S CHANGED!
        self.dw.isChanged = False
        
        self.plant.setUpCall([self.doUpdates, self.resetLogger])
        self.refresh()
        
        self.initialized = True
        
    def getTTab(self, which):
        if which in self.tabs:
            return self.tabs[which]["tab"]
    def getRTab(self):
        stn = self.getDefaultTabId("r")
        return self.tabs[stn]["tab"]
    def getVTab(self):
        stn = self.getDefaultTabId("v")
        return self.tabs[stn]["tab"]
    def getETab(self):
        stn = self.getDefaultTabId("e")
        return self.tabs[stn]["tab"]

    def sysTLin(self):
        return sys.platform not in ["darwin", 'win32']

    def isInitialized(self):
        return self.initialized
    def getFrame(self):
        return self.toolFrame

    def withViews(self):
        return self.viewsm is not None
    
    def hasDataLoaded(self):
        if self.dw is not None:
            return self.dw.getData() is not None
        return False
    def getData(self):
        if self.dw is not None:
            return self.dw.getData()
    def getAllCols(self):
        if self.dw is not None:
            return self.dw.getAllCols()
        return []
        
    def getRed(self, iid):
        if self.dw is not None:
            return self.dw.getRed(iid)
    def getReds(self, lid=None):
        if self.dw is not None:
            return self.dw.getReds(lid)
        return []
    def getRedLists(self):
        if self.dw is not None:
            return self.dw.getRedLists()
        return []
    def getAllReds(self):
        if self.dw is not None:
            return self.dw.getAllReds()
        return []
    def getNbReds(self):
        if self.dw is not None:
            return self.dw.getNbReds()
        return -1
    
    def getPreferences(self):
        if self.dw is not None:
            return self.dw.getPreferences()
    def getLogger(self):
        return self.logger
    def getVizm(self):
        return self.vizm
    def getViewsm(self):
        return self.viewsm
    def getERCache(self):
        return self.er_cache
        
    ######################################################################
    ###########     TOOL PANEL
    ######################################################################
    ## main panel, contains tables for the variables and redescriptions plus settings, log, etc.        
    def create_tool_panel(self):
        """ Creates the main panel with all the controls on it:
             * mpl canvas 
             * mpl navigation toolbar
             * Control panel for interaction
        """
        self.makeStatus(self.toolFrame)
        self.doUpdates()
        if self.isSplit():
            self.splitter = wx.SplitterWindow(self.toolFrame)
            self.tabbed = wx.Notebook(self.splitter, -1, style=(wx.NB_TOP)) #, size=(3600, 1200))
        else:
            self.tabbed = wx.Notebook(self.toolFrame, -1, style=(wx.NB_TOP)) #, size=(3600, 1200))
        # self.tabbed.Bind(wx.EVT_LEFT_DOWN, self.testLeftD)

        tmp_keys = list(self.tabs_keys)
        #### Draw tabs
        for tab_id in tmp_keys:
            if self.tabs[tab_id]["type"] == "r":
                self.tabs[tab_id]["tab"] = RedsTable(self, tab_id, "r", self.tabbed, self.tabs[tab_id]["short"])
                self.tabbed.AddPage(self.tabs[tab_id]["tab"].getSW(), self.tabs[tab_id]["title"])

            elif self.tabs[tab_id]["type"] == "v":
                self.tabs[tab_id]["tab"] = VarsTable(self, tab_id, "v", self.tabbed, self.tabs[tab_id]["short"])
                self.tabbed.AddPage(self.tabs[tab_id]["tab"].getSW(), self.tabs[tab_id]["title"])

            elif self.tabs[tab_id]["type"] == "e":
                self.tabs[tab_id]["tab"] = RowTable(self, tab_id, self.tabbed, self.tabs[tab_id]["short"])
                self.tabbed.AddPage(self.tabs[tab_id]["tab"].grid, self.tabs[tab_id]["title"])

            elif self.tabs[tab_id]["type"] == "t":
                self.tabs[tab_id]["tab"] = wx.Panel(self.tabbed, -1)
                self.tabs[tab_id]["text"] = wx.TextCtrl(self.tabs[tab_id]["tab"], size=(-1,-1), style=self.tabs[tab_id]["style"])
                self.tabbed.AddPage(self.tabs[tab_id]["tab"], self.tabs[tab_id]["title"])
                boxS = wx.BoxSizer(wx.VERTICAL)
                boxS.Add(self.tabs[tab_id]["text"], 1, wx.EXPAND) # wx.ALIGN_CENTER | wx.TOP | 
                self.tabs[tab_id]["tab"].SetSizer(boxS)

            elif self.tabs[tab_id]["type"] == "z":
                self.vizm = VizManager(self, tab_id, self.tabbed, self.tabs[tab_id]["title"]) 
                #self.tabs[tab_id]["tab"] = wx.Panel(self.tabbed, -1)
                self.tabs[tab_id]["tab"] = self.vizm.getSW()
                self.vizm.initialize()
                self.tabbed.AddPage(self.tabs[tab_id]["tab"], self.tabs[tab_id]["title"])
                
        self.tabbed.Bind(wx.EVT_NOTEBOOK_PAGE_CHANGED, self.OnPageChanged)
        ### splitter
        if self.isSplit():
            self.splitter.Initialize(self.tabbed)
            self.splitter.SetSashGravity(1.)
            self.splitter.SetMinimumPaneSize(0)
            self.splitter.Bind(wx.EVT_SPLITTER_UNSPLIT, self.OnSplitchange)
        # # self.splitter.Initialize(self.tabbed)
        # # self.splitter.SplitHorizontally(self.tabbed, self.tabs["viz"]["tab"])
        self.tabbed.Bind(wx.EVT_SIZE, self.OnSize)
       
    ######################################################################
    ###########     INTERFACE MAINTENANCE
    ######################################################################
    def getTabId(self, tab=None):
        if tab is None:
            tab = self.selectedTab
        if "tab" in tab:
            return tab["id"]
        return None
    def getTabType(self, tab=None):
        if tab is None:
            tab = self.selectedTab
        if "tab" in tab:
            return tab["type"].lower()
        return "-"
    def matchTabType(self, ffilter, tab=None, detached=False):
        if not detached:
            return self.getTabType(tab) in ffilter
        else:
            return "r" in ffilter
    def getTabsMatchType(self, ffilter):
        return [(ti,tab) for (ti, tab) in self.tabs.items() if self.matchTabType(ffilter, tab)]
    def getDefaultTabId(self, tabType):
        return self.main_tabs_ids[tabType]
    def getDefaultTab(self, tabType=None, tab=None):
        if tab is not None:
            return tab
        if tabType is None:
            return self.selectedTab
        if self.getDefaultTabId(tabType) in self.tabs:
            return self.tabs[self.getDefaultTabId(tabType)]
    def getDefaultTTab(self, tabType=None, tab=None):
        tt = self.getDefaultTab(tabType, tab)
        if "tab" in tt:
            return tt["tab"]
        return tt
        
    def getSelectionTab(self):
        return self.tabbed.GetSelection()
    def OnTabW(self, event):
        if event.GetId() in self.check_tab:
            tab_id = self.check_tab[event.GetId()]
            self.showTab(tab_id)
    def showTab(self, tab_id):
        self.changePage(tab_id)
        

    def makeStatus(self, frame):
        ### status bar
        self.statusbar = frame.CreateStatusBar()
        self.statusbar.SetFieldsCount(5)
        self.statusbar.SetStatusWidths([25, 300, 150, -1, 200])
        self.updateDataInfo()
        rect = self.statusbar.GetFieldRect(0)
        self.buttViz = wx.StaticBitmap(self.statusbar, wx.NewId(), self.icons["split_frame"], size=(rect.height+4, rect.height+4))
        # self.buttViz.SetMargins(0, 0)
        # self.buttViz = wx.ToggleButton(self.statusbar, wx.NewId(), "s", style=wx.ALIGN_CENTER|wx.TE_RICH, size=(rect.height+4, rect.height+4))
        # self.buttViz.SetForegroundColour((0,0,0))
        # self.buttViz.SetBackgroundColour((255,255,255))
        self.buttViz.SetPosition((rect.x, rect.y))
        self.buttViz.Bind(wx.EVT_LEFT_UP, self.OnSplitchange)

        self.progress_bar = wx.Gauge(self.statusbar, -1, style=wx.GA_HORIZONTAL|wx.GA_SMOOTH)
        rect = self.statusbar.GetFieldRect(2)
        self.progress_bar.SetPosition((rect.x+2, rect.y+2))
        self.progress_bar.SetSize((rect.width-2, rect.height-2))
        self.progress_bar.Hide()

    def updateDataInfo(self):
        if self.hasDataLoaded():            
            self.statusbar.SetStatusText("%s" % self.dw.getData(), 4)
        else:
            self.statusbar.SetStatusText("No data loaded", 4)
        
    def isSplit(self):
        return True #False
    def OnSplitchange(self, event):
        if self.isSplit():
            ## if event.GetEventType() == 10022 or event.GetEventType() == 10029 or \
            ##        event.GetWindowBeingRemoved().GetParent().GetId() == self.splitter.GetId():
            if type(event) == wx.MouseEvent or \
               ( type(event) == wx.SplitterEvent and event.GetWindowBeingRemoved().GetParent().GetId() == self.splitter.GetId()):
                 self.getVizm().OnSplitchange()
                 
    def OnVizCheck(self, event):
        self.getVizm().setVizCheck(not event.IsChecked())
                    
    def toTop(self):
        self.toolFrame.Raise()
        self.toolFrame.SetFocus()
        
    def changePage(self, tabn):
        if tabn in self.tabs: # and not self.tabs[tabn]["hide"]:
            self.tabbed.ChangeSelection(self.tabs_keys.index(tabn))            
            self.OnPageChanged(-1)
    def OnListChanged(self, event):
        if self.findDlg is not None:
            self.findDlg.resetFind(self.getDefaultTTab())            
    def OnPageChanged(self, event):
        if not self.sysTLin() and type(event) == wx.BookCtrlEvent:
            self.tabbed.ChangeSelection(event.GetSelection())
            ## self.getDefaultTTab().Show()

        self.setSelectedTab()            
        self.OnListChanged(event)

    def setSelectedTab(self):
        tsel = self.tabbed.GetSelection()
        if tsel >= 0 and tsel < len(self.tabs_keys): 
            self.selectedTab = self.tabs[self.tabs_keys[tsel]]
            self.doUpdates()
        
    def loggingDWError(self, output, message, type_message, source):
        self.errorBox(message)
        self.appendLog("\n\n***" + message + "***\n")

    def loggingLogTab(self, output, message, type_message, source):
        text = "%s" % message
        header = "@%s:\t" % source
        text = text.replace("\n", "\n"+header)
        self.appendLog(text+"\n")

    def appendLog(self, text):
        if "log" in self.tabs:
            self.tabs["log"]["text"].AppendText(text)

    def OnStop(self, event):
        if event.GetId() in self.ids_stoppers:
            self.plant.getWP().layOff(self.ids_stoppers[event.GetId()])
            self.checkResults(menu=True)
                
    def OnSize(self, event):
        if self.getVizm() is not None:
            self.getVizm().resizeViz()
        event.Skip()
                
    def OnQuit(self, event):
        if self.plant.getWP().isActive():  
            if isinstance(self.plant.getWP(), WorkClient) and self.plant.getWP().nbWorking()>0:
                collectLater = self.quitReturnLaterDialog(what=self.plant.getWP().getHid())
                if collectLater == 0:
                    return
                self.plant.getWP().closeDown(self, collectLater > 0)   
            else :
                self.plant.getWP().closeDown(self)        
        if not self.checkAndProceedWithUnsavedChanges(what="quit"):
            return
        if self.withViews():
            self.viewsm.deleteAllViews()
        if self.getVizm() is not None:
            self.vizm.OnQuit()
        self.toolFrame.Destroy()
        sys.exit()
         
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

            
    ######################################################################
    ###########     MENUS
    ######################################################################
    def updateProgressBar(self):
        if not self.plant.getWP().isActive():
            work_estimate, work_progress = (0, 0)
        else:
            work_estimate, work_progress = self.plant.getWP().getWorkEstimate()
        # print("PROGRESS", work_estimate, work_progress, type(work_estimate))
        if work_estimate > 0:
            self.progress_bar.SetRange(10**5)
            self.progress_bar.SetValue(math.floor(10**5*(work_progress/float(work_estimate))))
            self.progress_bar.Show()
        else:
            self.progress_bar.SetRange(1)
            self.progress_bar.SetValue(0)
            self.progress_bar.Hide()

    def makePopupMenu(self, caller):
        tab = None
        if caller is None:
            frame = self.getFrame()
        else:
            if caller.isDetached():
                tab = caller.getTab()
            frame = caller.getFrame()
        """
        Create and display a popup menu on right-click event
        """
        if self.matchTabType("t", tab=tab):
            return
        # Popup the menu.  If an item is selected then its handler
        # will be called before PopupMenu returns.
        ct = 0
        menuCon = self.makeConSMenu(frame, tab=tab)
        if menuCon.GetMenuItemCount() > ct:
            ct = menuCon.GetMenuItemCount()
            menuCon.AppendSeparator()

        if self.matchTabType("evr", tab=tab):
            if self.withViews():
                submenuViz = wx.Menu()
                self.makeVizMenu(frame, submenuViz, tab=tab)
                ID_VIZ = wx.NewId()
                menuCon.Append(ID_VIZ, "&View", submenuViz)

            self.makeEditMenu(frame, menuCon, tab=tab)
        # if menuCon.GetMenuItemCount() > ct:
        #     ct = menuCon.GetMenuItemCount()
        #     menuCon.AppendSeparator()
        # if self.matchTabType("evr", tab=tab):
        #     self.makeVizMenu(frame, menuCon, tab=tab)
        frame.PopupMenu(menuCon)
        menuCon.Destroy()

    def makeConSMenu(self, frame, menuCon=None, tab=None):
        if menuCon is None:
            menuCon = wx.Menu()
        if self.matchTabType("e", tab=tab):            
            ID_FOC = wx.NewId()
            m_foc = menuCon.Append(ID_FOC, "Expand/Shrink column", "Expand/Shrink current column.")
            frame.Bind(wx.EVT_MENU, self.OnFlipExCol, m_foc)
        return menuCon

    def makeEditMenu(self, frame, menuEdit=None, tab=None):
        
        if menuEdit is None:
            menuEdit = wx.Menu()
                    
        info = self.getContentInfo(tab=tab)
        if self.matchTabType("r", tab=tab):
            if self.getDefaultTTab(tab=tab).hasFocusContainersL():
                act_details = self.dw.getExtraAct("NewList")
                if act_details is not None:
                    ID_AC = wx.NewId()
                    m_newl = menuEdit.Append(ID_AC, act_details["label"], act_details["legend"])
                    frame.Bind(wx.EVT_MENU, self.OnActContent, m_newl)
                    self.ids_contentAct[ID_AC] = (tab, act_details["key"])

                ### POP LIST
                if self.getDefaultTTab(tab=tab).nbSelected() > 0 and tab is None:                    
                    dets_tbl = self.viewsm.getTableViewT(typeI="r") if self.withViews() else None
                    if dets_tbl is not None:
                        ID_POPL = wx.NewId()
                        m_popl = menuEdit.Append(ID_POPL, "Pop list", "Pop list.")
                        frame.Bind(wx.EVT_MENU, self.OnPopList, m_popl)                    
                    
            if info["lid"] is not None:
                act_details = self.dw.getExtraAct("AddDelListToPack")
                if act_details is not None:
                    ID_AC = wx.NewId()
                    m_adp = menuEdit.Append(ID_AC, act_details["label"], act_details["legend"])
                    if info["pck_path"] is not None and not info["is_hist"]:                    
                        frame.Bind(wx.EVT_MENU, self.OnActContent, m_adp)
                        self.ids_contentAct[ID_AC] = (tab, act_details["key"])
                        if info["in_pack"]:
                            m_adp.SetItemLabel("Remove from package") # SetText
                    else:
                        menuEdit.Enable(ID_AC, False)

                ID_SV = wx.NewId()
                m_svl = menuEdit.Append(ID_SV, "Save list\tCtrl+L", "Save list.")
                frame.Bind(wx.EVT_MENU, self.OnSaveRedList, m_svl)
                self.ids_evTabs[ID_SV] = tab
                if info["path"] is None:
                    menuEdit.Enable(ID_SV, False)

                ID_SVA = wx.NewId()
                m_svla = menuEdit.Append(ID_SVA, "Save list as...\tShift+Ctrl+L", "Save list as...")
                frame.Bind(wx.EVT_MENU, self.OnSaveRedListAs, m_svla)
                self.ids_evTabs[ID_SVA] = tab
                if info["is_hist"]:
                    menuEdit.Enable(ID_SVA, False)

            elif info["nb"] > 0:
                ID_SVE = wx.NewId()
                m_ex = menuEdit.Append(ID_SVE, "Export\tCtrl+E", "Export selected redescriptions")
                frame.Bind(wx.EVT_MENU, self.OnExportReds, m_ex)
                self.ids_evTabs[ID_SVE] = tab

        if self.matchTabType("vr", tab=tab):
            ID_SVLP = wx.NewId()
            m_svlp = menuEdit.Append(ID_SVLP, "Save figs as...\tShift+Ctrl+P", "Draw figures and save as...")
            frame.Bind(wx.EVT_MENU, self.OnExportFigs, m_svlp)
            self.ids_evTabs[ID_SVLP] = tab
                
        if self.withViews() and self.getDefaultTTab(tab=tab).hasFocusItemsL() and self.getDefaultTTab(tab=tab).nbSelected() == 1:
            if self.matchTabType("vr", tab=tab):
                ID_DETAILS = wx.NewId()
                m_details = menuEdit.Append(ID_DETAILS, "View details", "View variable values.")
                frame.Bind(wx.EVT_MENU, self.OnShowCol, m_details)
                self.ids_evTabs[ID_DETAILS] = tab
                
            elif self.matchTabType("e", tab=tab):
                ID_HIGH = wx.NewId()
                m_high = menuEdit.Append(ID_HIGH, "Highlight in views", "Highlight the entity in all opened views.")
                frame.Bind(wx.EVT_MENU, self.OnHigh, m_high)
                if self.viewsm.getNbViews() < 1:
                    menuEdit.Enable(ID_HIGH, False)

        if self.getDefaultTTab(tab=tab).hasFocusItemsL():
            ID_FIND = wx.NewId()
            m_find = menuEdit.Append(ID_FIND, "Find\tCtrl+F", "Find by name.")
            frame.Bind(wx.EVT_MENU, self.OnFind, m_find)
            self.ids_evTabs[ID_FIND] = tab
            if self.getDefaultTTab(tab=tab).GetNumberRows() == 0:
                menuEdit.Enable(ID_FIND, False)

            for act_details in self.dw.getGroupActs("able"):
                ID_AC = wx.NewId()
                m_ac = menuEdit.Append(ID_AC, act_details["label"], act_details["legend"])
                self.ids_contentAct[ID_AC] = (tab, act_details["key"])
                frame.Bind(wx.EVT_MENU, self.OnActContent, m_ac)
                if self.getDefaultTTab(tab=tab).GetNumberRows() == 0:
                    menuEdit.Enable(ID_AC, False)

        if True: #self.getDefaultTTab(tab=tab).hasFocusItemsL():
            if self.matchTabType("r", tab=tab):
                for act_details in self.dw.getGroupActs("redCCP"):
                    ID_AC = wx.NewId()
                    m_ac = menuEdit.Append(ID_AC, act_details["label"], act_details["legend"])
                    self.ids_contentAct[ID_AC] = (tab, act_details["key"])
                    frame.Bind(wx.EVT_MENU, self.OnActContent, m_ac)
                    if act_details["key"] == "Paste":
                        if self.getDefaultTTab(tab=tab).isEmptyBuffer():
                            menuEdit.Enable(ID_AC, False)
                    else:
                        # if self.getDefaultTTab(tab=tab).GetNumberRows() == 0:
                        if self.getDefaultTTab(tab=tab).nbSelected() == 0:
                            menuEdit.Enable(ID_AC, False)

        if self.getDefaultTTab(tab=tab).hasFocusItemsL():
            if self.matchTabType("r", tab=tab):
                if self.getDefaultTTab(tab=tab).GetNumberRows() > 0:
                    if menuEdit.GetMenuItemCount() > 0:
                        menuEdit.AppendSeparator()                    

                    ID_EXPAND = wx.NewId()
                    m_expand = menuEdit.Append(ID_EXPAND, "E&xpand\tCtrl+M", "Expand redescription(s).")
                    frame.Bind(wx.EVT_MENU, self.OnExpand, m_expand)
                    self.ids_evTabs[ID_EXPAND] = tab
                    
                    ID_IMPROVE = wx.NewId()
                    m_improve = menuEdit.Append(ID_IMPROVE, "Improve\tCtrl+I", "Improve redescription(s).")
                    frame.Bind(wx.EVT_MENU, self.OnImprove, m_improve)
                    self.ids_evTabs[ID_IMPROVE] = tab

                    acts_details = self.dw.getGroupActs("redsMod")
                    for act_details in acts_details:
                        ID_AC = wx.NewId()
                        m_ac = menuEdit.Append(ID_AC, act_details["label"], act_details["legend"])
                        self.ids_contentAct[ID_AC] = (tab, act_details["key"])
                        frame.Bind(wx.EVT_MENU, self.OnActContent, m_ac)
                    
                    acts_details = self.dw.getGroupActs("redsFilter")
                    # if menuEdit.GetMenuItemCount() > 0 and len(acts_details) > 0:
                    #     menuEdit.AppendSeparator()                    
                    for act_details in acts_details:
                        ID_AC = wx.NewId()
                        m_ac = menuEdit.Append(ID_AC, act_details["label"], act_details["legend"])
                        self.ids_contentAct[ID_AC] = (tab, act_details["key"])
                        frame.Bind(wx.EVT_MENU, self.OnActContent, m_ac)                    
        return menuEdit

    def makeVizMenu(self, frame, menuViz=None, tab=None):
        if menuViz is None:
            countIts = 0
            menuViz = wx.Menu()
            
            #### not for popup menu
            if self.getVizm() is not None and self.getVizm().hasVizIntab():
                ID_CHECK = wx.NewId()
                m_check = menuViz.AppendCheckItem(ID_CHECK, "Plots in external windows", "Plot in external windows rather than the visualization tab.")
                if not self.getVizm().showVizIntab():
                    m_check.Check()
                frame.Bind(wx.EVT_MENU, self.OnVizCheck, m_check)
                menuViz.AppendSeparator()

        countIts = menuViz.GetMenuItemCount()

        ### MENU VIZ FOR SINGLE ITEMS 
        if self.withViews() and (self.matchTabType("e", tab=tab) or \
          ( self.matchTabType("vr", tab=tab) and self.getDefaultTTab(tab=tab).hasFocusItemsL() and self.getDefaultTTab(tab=tab).nbSelected() == 1 )):
            what = self.getDefaultTTab(tab=tab).getSelectedItem()
            for ix, item in enumerate(self.viewsm.getViewsItems(what=what)):
                ID_NEWV = wx.NewId()
                m_newv = menuViz.Append(ID_NEWV, "%s%s" % (item["title"], "\tCtrl+P"*(ix==0)), "Plot %s." % item["title"])
                if not item["suitable"]:
                    m_newv.Enable(False)
                frame.Bind(wx.EVT_MENU, self.OnNewV, m_newv)
                self.ids_viewT[ID_NEWV] = (tab, item["viewT"])

        ### MENU VIZ FOR MULTIPLE ITEMS 
        if self.withViews() and (self.matchTabType("vr", tab=tab) and \
          (( self.getDefaultTTab(tab=tab).hasFocusContainersL() and self.getDefaultTTab(tab=tab).nbSelected() > 0) or \
           ( self.getDefaultTTab(tab=tab).hasFocusItemsL() and self.getDefaultTTab(tab=tab).nbSelected() > 1 ))):
            what = self.getDefaultTTab(tab=tab).getSelectedItems()
            for ix, item in enumerate(self.viewsm.getViewsItems(what=what)):
                ID_NEWV = wx.NewId()
                m_newv = menuViz.Append(ID_NEWV, "%s%s" % (item["title"], "\tCtrl+P"*(ix==0)), "Plot %s." % item["title"])
                if not item["suitable"]:
                    m_newv.Enable(False)
                frame.Bind(wx.EVT_MENU, self.OnNewV, m_newv)
                self.ids_viewT[ID_NEWV] = (tab, item["viewT"])
                
        if menuViz.GetMenuItemCount() == countIts:
            self.appendEmptyMenuEntry(menuViz, "No visualization", "There are no visualizations.")

        return menuViz

    def makeProcessMenu(self, frame, menuPro=None, tab=None):
        if menuPro is None:
            menuPro = wx.Menu()
        ID_MINE = wx.NewId()
        m_mine = menuPro.Append(ID_MINE, "&Mine redescriptions\tShift+Ctrl+M", "Mine redescriptions from the dataset according to current constraints.")
        if self.getData() is None:
            menuPro.Enable(ID_MINE, False)
        else:
            frame.Bind(wx.EVT_MENU, self.OnMineAll, m_mine)

        ct = menuPro.GetMenuItemCount()
        menuPro = self.makeStoppersMenu(frame, menuPro, tab=tab)
        if ct < menuPro.GetMenuItemCount():
            menuPro.InsertSeparator(ct)
        return menuPro

    def makeStoppersMenu(self, frame, menuStop=None, tab=None):
        if menuStop is None:
            menuStop = wx.Menu()
        if self.plant.getWP().nbWorkers() == 0:
            ID_NOP = wx.NewId()
            m_nop = menuStop.Append(ID_NOP, "No process running", "There is no process currently running.")
            menuStop.Enable(ID_NOP, False)

        else:
            for ix, wdt in enumerate(self.plant.getWP().getWorkersDetails()): 
                ID_STOP = wx.NewId()
                self.ids_stoppers[ID_STOP] = wdt["wid"]
                m_stop = menuStop.Append(ID_STOP, "Stop %s #&%s%s" % (wdt["task"], wdt["wid"], "\tCtrl+K"*(ix==0)),
                                         "Interrupt %s process #%s." % (wdt["task"], wdt["wid"]))
                frame.Bind(wx.EVT_MENU, self.OnStop, m_stop)
        if self.plant.getWP().isActive():
            menuStop.AppendSeparator()
            ID_PLT = wx.NewId()
            m_plt = menuStop.Append(ID_PLT, self.plant.getWP().infoStr(), "Where processes are handled.")
            menuStop.Enable(ID_PLT, False)

        return menuStop

    def makeViewsMenu(self, frame, menuViews=None, tab=None):
        if menuViews is None:
            menuViews = wx.Menu()

        menuViews.Append(wx.NewId(), "&Tabs", self.makeTabsMenu(frame, tab=tab))
        # self.makeTabsMenu(frame, menuViews)
        # if menuViews.GetMenuItemCount() > 0:
        #     menuViews.AppendSeparator()

        if self.withViews():
            self.viewsm.makeViewsMenu(frame, menuViews) 
        return menuViews

    def makeTabsMenu(self, frame, menuTabs=None, tab=None):
        if menuTabs is None:
            menuTabs = wx.Menu()

        # ID_AC = wx.NewId()
        # m_ac = menuTabs.Append(ID_AC, "Print tracks", "Debug")
        # frame.Bind(wx.EVT_MENU, self.OnPrintTracks, m_ac)
            
        for tab_id in self.tabs_keys:
            tab_prop = self.tabs[tab_id]
            ID_CHECK = wx.NewId()
            self.check_tab[ID_CHECK] = tab_id 
            m_check = menuTabs.Append(ID_CHECK, "%s" % tab_prop["title"], "Switch to %s tab." % tab_prop["title"])
            frame.Bind(wx.EVT_MENU, self.OnTabW, m_check)
        return menuTabs

    def makeFileMenu(self, frame, menuFile=None, tab=None):
        if menuFile is None:
            menuFile = wx.Menu()

        m_open = menuFile.Append(wx.ID_OPEN, "&Open\tCtrl+O", "Open a project.")
        frame.Bind(wx.EVT_MENU, self.OnOpenPck, m_open)

        ## Save  
        m_save = menuFile.Append(wx.ID_SAVE, "&Save\tCtrl+S", "Save the current project.")
        if self.getData() is not None and self.dw.isFromPackage and self.dw.getPackageSaveFilename() is not None:
            frame.Bind(wx.EVT_MENU, self.OnSave, m_save)
        else:
            menuFile.Enable(wx.ID_SAVE, False)

        ## Save As...
        m_saveas = menuFile.Append(wx.ID_SAVEAS, "Save &as...\tShift+Ctrl+S", "Save the current project as...")
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
        # m_impData = submenuImport.Append(ID_IMPORT_DATA, "Import &Data", submenuImportData)
        #m_impData = submenuImport.Append(ID_IMPORT_DATA, "Import &Data", "Import data into the project.")
        #frame.Bind(wx.EVT_MENU, self.OnImportData, m_impData)
        
        ID_IMPORT_PREFERENCES = wx.NewId()
        m_impPreferences = submenuImport.Append(ID_IMPORT_PREFERENCES, "Import &Preferences", "Import preferences into the project.")
        frame.Bind(wx.EVT_MENU, self.OnImportPreferences, m_impPreferences)
        
        ID_IMPORT_REDESCRIPTIONS = wx.NewId()
        m_impRedescriptions = submenuImport.Append(ID_IMPORT_REDESCRIPTIONS, "Import &Redescriptions", "Import redescriptions into the project.")
        if self.getData() is not None:
            frame.Bind(wx.EVT_MENU, self.OnImportRedescriptions, m_impRedescriptions)
        else:
            submenuImport.Enable(ID_IMPORT_REDESCRIPTIONS, False)

        ID_IMPORT = wx.NewId()
        m_import = menuFile.Append(ID_IMPORT, "&Import", submenuImport)

        
        ## Export submenu
        submenuExport = wx.Menu() # Submenu for exporting
        
        ID_EXPORT_REDESCRIPTIONS = wx.NewId()
        m_exportRedescriptions = submenuExport.Append(ID_EXPORT_REDESCRIPTIONS, "&Export Redescriptions\tShift+Ctrl+E", "Export redescriptions.")
        if self.dw.hasRedsToExport():
            frame.Bind(wx.EVT_MENU, self.OnExportReds, m_exportRedescriptions)
        else:
            submenuExport.Enable(ID_EXPORT_REDESCRIPTIONS, False)

        ID_EXPORT_PREF = wx.NewId()
        m_exportPref = submenuExport.Append(ID_EXPORT_PREF, "&Export Preferences", "Export preferences.")
        frame.Bind(wx.EVT_MENU, self.OnPrintoutPreferences, m_exportPref)

        ID_TMPL_PREF = wx.NewId()
        m_tmplPref = submenuExport.Append(ID_TMPL_PREF, "Export Prefs Template", "Print out preferences template.")
        frame.Bind(wx.EVT_MENU, self.OnPrintoutPreferencesTmpl, m_tmplPref)
        ID_DEF_PREF = wx.NewId()
        m_defPref = submenuExport.Append(ID_DEF_PREF, "Export Prefs Default", "Print out default preferences.")
        frame.Bind(wx.EVT_MENU, self.OnPrintoutPreferencesDef, m_defPref)
        
        ID_EXPORT = wx.NewId()
        m_export = menuFile.Append(ID_EXPORT, "&Export", submenuExport)
            
        ## Preferences
        menuFile.AppendSeparator()
        m_preferencesdia = menuFile.Append(wx.ID_PREFERENCES, "P&references...\tCtrl+,", "Set preferences.")
        frame.Bind(wx.EVT_MENU, self.OnPreferencesDialog, m_preferencesdia)

        ## Worker setup
        if True:
                ID_CONN = wx.NewId()
                m_conndia = menuFile.Append(ID_CONN, "Wor&ker setup...", "Setup worker's connection.")
                frame.Bind(wx.EVT_MENU, self.OnConnectionDialog, m_conndia)

        ## Folds setup
        if True:
                ID_FLDS = wx.NewId()
                m_fldsdia = menuFile.Append(ID_FLDS, "Fo&lds setup...", "Setup data folds for cross-tests.")
                frame.Bind(wx.EVT_MENU, self.OnFoldsDialog, m_fldsdia)
                if not self.hasDataLoaded():
                        menuFile.Enable(ID_FLDS, False)

        ## Extensions setup
        if True:
                ID_EXTD = wx.NewId()
                m_extdia = menuFile.Append(ID_EXTD, "Extensions setup...", "Setup data extensions.")
                frame.Bind(wx.EVT_MENU, self.OnExtensionsDialog, m_extdia)
                if not self.hasDataLoaded():
                        menuFile.Enable(ID_EXTD, False)
                        
        ## Export submenu
        submenuFields = wx.Menu() # Submenu for exporting

        ID_FLD_VGUI = wx.NewId()
        m_fldvgui = submenuFields.Append(ID_FLD_VGUI, "Variables GUI", "Variables fields for GUI.")
        frame.Bind(wx.EVT_MENU, self.OnDefVarsFieldsGUI, m_fldvgui)

        ID_FLD_GUI = wx.NewId()
        m_fldgui = submenuFields.Append(ID_FLD_GUI, "Redescriptions GUI", "Redescription fields for GUI.")
        frame.Bind(wx.EVT_MENU, self.OnDefRedsFieldsGUI, m_fldgui)
        ID_FLD_TXT = wx.NewId()
        m_fldtxt = submenuFields.Append(ID_FLD_TXT, "Redescriptions text export", "Redescription fields for text export.")
        frame.Bind(wx.EVT_MENU, self.OnDefRedsFieldsOutTxt, m_fldtxt)
        ID_FLD_TEX = wx.NewId()
        m_fldtex = submenuFields.Append(ID_FLD_TEX, "Redescriptions LaTeX export", "Redescription fields for LaTeX export.")
        frame.Bind(wx.EVT_MENU, self.OnDefRedsFieldsOutTex, m_fldtex)

        ID_VDEFS_FILE = wx.NewId()
        m_vdefs = submenuFields.Append(ID_VDEFS_FILE, "Load fields for variables", "Load definitions of fields for variables from file.")
        frame.Bind(wx.EVT_MENU, self.OnDefVarsFieldsFile, m_vdefs)
        ID_RDEFS_FILE = wx.NewId()
        m_rdefs = submenuFields.Append(ID_RDEFS_FILE, "Load fields for redescriptions", "Load definitions of fields for redescriptions from file.")
        frame.Bind(wx.EVT_MENU, self.OnDefRedsFieldsFile, m_rdefs)
        ID_RACTS_FILE = wx.NewId()
        m_racts = submenuFields.Append(ID_RACTS_FILE, "Load actions for redescriptions", "Load definitions of actions for redescriptions from file.")
        frame.Bind(wx.EVT_MENU, self.OnDefRedsActionsFile, m_racts)

        
        ID_FLD = wx.NewId()
        m_fld = menuFile.Append(ID_FLD, "Fields setup", submenuFields)

        menuFile.AppendSeparator()
        ## Quit
        m_quit = menuFile.Append(wx.ID_EXIT, "&Quit", "Close window and quit program.")
        frame.Bind(wx.EVT_MENU, self.OnQuit, m_quit)
        return menuFile

    def makeHelpMenu(self, frame, menuHelp=None, tab=None):
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

    def appendEmptyMenuEntry(self, menu, entry_text, entry_leg=""):
        ID_NOR = wx.NewId()
        menu.Append(ID_NOR, entry_text, entry_leg)
        menu.Enable(ID_NOR, False)
    def makeMenuEmpty(self, menu_action, menuEmpty=None):
        if menuEmpty is None:
            menuEmpty = wx.Menu()
        self.appendEmptyMenuEntry(menuEmpty, "Nothing to %s" % menu_action, "Nothing to %s." % menu_action)
        return menuEmpty
        
    def makeMenu(self, caller=None):
        tab = None
        if caller is None:
            frame = self.getFrame()
        else:
            if caller.isDetached():
                tab = caller.getTab()
            frame = caller.getFrame()

        menuBar = wx.MenuBar()
        menuBar.Append(self.makeFileMenu(frame, tab=tab), "&File")
        me = None
        if self.matchTabType("evr", tab=tab):
            me = self.makeEditMenu(frame, tab=tab)
        if me is None or me.GetMenuItemCount() == 0:
            me = self.makeMenuEmpty("edit", menuEmpty=me)
        menuBar.Append(me, "&Edit")
        ## if self.matchTabType("evr", tab=tab):
        if self.withViews():
            menuBar.Append(self.makeVizMenu(frame, tab=tab), "&View")
        ## else:
        ##     menuBar.Append(self.makeMenuEmpty("visualize"), "&View")
        menuBar.Append(self.makeProcessMenu(frame, tab=tab), "&Process")
        menuBar.Append(self.makeViewsMenu(frame, tab=tab), "&Windows")
        menuBar.Append(self.makeHelpMenu(frame, tab=tab), "&Help")
        frame.SetMenuBar(menuBar)
        frame.Layout()
        frame.SendSizeEvent()

    def updateMenus(self):
        self.ids_contentAct = {}
        self.ids_evTabs = {}
        self.ids_viewT = {}
        self.ids_stoppers = {}
        self.check_tab = {}
        self.makeMenu()
        if self.withViews():
            self.viewsm.makeMenusForViews()

    ######################################################################
    ###########     DIALOGS AND BOXES
    ######################################################################
    #### MISCS DIALOG
    def OnPreferencesDialog(self, event):
        d = PreferencesDialog(self.toolFrame, self.dw)
        d.ShowModal()
        d.Destroy()
        self.refresh()
    def OnExtensionsDialog(self, event):
        d = ExtensionsDialog(self.toolFrame, self.dw)
        d.ShowModal()
        d.Destroy()
        self.refresh()
    def OnConnectionDialog(self, event):
        d = ConnectionDialog(self.toolFrame, self.dw, self.plant, self)
        tt = d.ShowModal()
        d.Destroy()
        self.refresh()
    def OnFoldsDialog(self, event):
        d = FoldsDialog(self.toolFrame, self.dw, self)
        d.ShowModal()
        d.Destroy()
        self.refresh()
            
    #### FIND DIALOG
    def quitFind(self):
        if self.findDlg is not None:
            self.findDlg = None

    def OnFind(self, event):
        """Shows a custom dialog to open the three data files"""
        tab = self.ids_evTabs.get(event.GetId())
        tt = self.getDefaultTTab(tab=tab)
        if self.findDlg is not None:
            if tt.getFrame() == self.findDlg.getFrame():
                self.findDlg.doNext()
            else:
                self.findDlg.quit()
        if self.findDlg is None:
            self.findDlg = FindDialog(self, tt)
            self.findDlg.showDialog()

            
    #### FIELDS DIALOG
    def OnDefRedsFieldsOutTex(self, event):
        self.OnDefFields("tex", "r")
    def OnDefRedsFieldsOutTxt(self, event):
        self.OnDefFields("txt", "r")        
    def OnDefRedsFieldsGUI(self, event):
        self.OnDefFields("gui", "r")
    def OnDefVarsFieldsGUI(self, event):
        self.OnDefFields("gui", "v")
    def OnDefFields(self, flk, tab_type="r"):
        rp = None
        if tab_type == "v":
            rp = ColM.getRP()
        elif tab_type == "r":
            rp = Redescription.getRP()
        if rp is None or self.dw.getData() is None:
            return        
        modifiers = rp.getModifiersForData(self.dw.getData())
        if tab_type == "v":
            var_list = self.getAllCols()
            types_letters = [] if self.dw.getData() is not None else None
            modifiers = rp.updateModifiers(modifiers=modifiers, var_list=var_list, types_letters=types_letters)
        
        choice_list = []
        for k in rp.getAllFields(flk, modifiers):
            choice_list.append((k, ChoiceElement(k, "%s" % k)))
        selected_ids = rp.getCurrentListFields(flk, modifiers)
        
        dlg = MultiSelectorDialog(self, choice_list, selected_ids)
        fields = dlg.showDialog()
        if fields is not None:
            if fields == -1:
                rp.dropCustListFields(flk, modifiers)
            else:
                rp.setCurrentListFields(fields, flk, modifiers)
            self.dw.addReloadFields(tab_type)
            self.refresh()
        return fields            

    def OnDefVarsFieldsFile(self, event):
        self.OnDefFile("fields_vdefs")
    def OnDefRedsFieldsFile(self, event):
        self.OnDefFile("fields_rdefs")
    def OnDefRedsActionsFile(self, event):
        self.OnDefFile("actions_rdefs")
    #### HERE
    def OnDefFile(self, fld_type="fields_rdefs"):
        dir_name = os.path.expanduser('~/')
        open_dlg = wx.FileDialog(self.toolFrame, message='Choose file', defaultDir = dir_name,
                                 style = wx.FD_OPEN|wx.FD_CHANGE_DIR)
        if open_dlg.ShowModal() == wx.ID_OK:
            path = open_dlg.GetPath()
            try:
                self.dw.loadDefsFromFile(path, fld_type)
            except:
                pass
        open_dlg.Destroy()
        self.refresh()

    
    #### DIALOGS BEFORE QUIT
    def quitReturnLaterDialog(self, test=None, what="continue"):
        reponse = -1
        dlg = wx.MessageDialog(self.toolFrame,'Some computations are underway (client id %s).\nDo you intend to collect the results later on?' % what, style=wx.YES_NO|wx.CANCEL|wx.NO_DEFAULT|wx.ICON_EXCLAMATION, caption='Computations in progress')
        tt = dlg.ShowModal()
        if tt == wx.ID_CANCEL: 
            reponse = 0
        if tt == wx.ID_YES: 
            reponse = 1
        return reponse
    
    #### HELP BOX           
    def OnHelp(self, event):
        self._onHelpOutside()
        # wxVer = map(int, wx.__version__.split('.'))
        # new_ver = wxVer[0] > 2 or (wxVer[0] == 2 and wxVer[1] > 9) or (wxVer[0] == 2 and wxVer[1] == 9 and wxVer[2] >= 3)
        # if new_ver:
        #     try:                                                      
        #         self._onHelpInside()
        #     except NotImplementedError:
        #         new_ver = False
        # if not new_ver:
        #    self._onHelpOutside()

    def _onHelpInside(self):
        import wx.html2
        import urllib
        import platform
        # DEBUG
        #self.toolFrame.Bind(wx.html2.EVT_WEBVIEW_ERROR, lambda evt: wx.MessageDialog(self.toolFrame, str(evt), style=wx.OK, caption='WebView Error').ShowModal())
        #self.toolFrame.Bind(wx.html2.EVT_WEBVIEW_LOADED, lambda evt: wx.MessageDialog(self.toolFrame, 'Help files loaded from '+evt.GetURL(), style=wx.OK, caption='Help files loaded!').ShowModal())
        if self.helpURL is None:
            self._onHelpOutside()
            return
        if self.helpFrame is None:
            self.helpFrame = wx.Frame(self.toolFrame, -1, self.titleHelp)
            self.helpFrame.Bind(wx.EVT_CLOSE, self._helpInsideClose)
            sizer = wx.BoxSizer(wx.VERTICAL)
            url = 'file://'+os.path.abspath(self.helpURL)
            if sys.platform == "darwin":
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

    def _helpInsideClose(self, event):
        self.helpFrame.Destroy()
        self.helpFrame = None

    def _onHelpOutside(self):
        import webbrowser
        helped = False
        if self.helpURL is not None:
            try:
                webbrowser.open("file://"+ self.helpURL, new=1, autoraise=True)
                helped = True
            except webbrowser.Error as e:
                helped = False
        if not helped:
            try:
                webbrowser.open(self.helpInternetURL, new=1, autoraise=True)
            except webbrowser.Error as e:
                self.logger.printL(1,'Cannot show help file: '+str(e)
                                   +'\nYou can find help at '+self.helpInternetURL+'\nor '+self.helpURL, "error", "help")        

    #### LICENSE BOX
    def OnLicense(self, event):
        license_text = None
        try:
            f = open(self.license_file, 'r')
            license_text = f.read()
        except:
            wx.MessageDialog(self.toolFrame, 'No license found.', style=wx.OK, caption="No license").ShowModal()
            return

        external_license_texts = ''
        for ext in self.external_licenses:
            lic = 'LICENSE_'+ext
            try:
                lfile = Siren.searchData(lic, 'licenses')
                if lfile is not None:
                    f = open(lfile, 'r')
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
            
    #### ABOUT BOX
    def OnAbout(self, event):
        wx.AboutBox(self.info)        

    #### ERROR BOX
    def errorBox(self, message):
        if self.busyDlg is not None:
            del self.busyDlg
            self.busyDlg = None
        dlg = wx.MessageDialog(self.toolFrame, message, style=wx.OK|wx.ICON_EXCLAMATION|wx.STAY_ON_TOP, caption="Error")
        dlg.ShowModal()
        dlg.Destroy()

    #### FILE MESSAGE BOX
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
        
                                     
    ######################################################################
    ###########     WORKERS JOBS
    ######################################################################       
    def expand(self, params={}):
        if params is None:
            params = {}
        self.progress_bar.Show()
        self.plant.getWP().addWorker(self, params)
        self.checkResults(menu=True)

    def project(self, proj=None, vid=None):
        self.progress_bar.Show()
        if proj is not None and vid is not None:
            out = self.proj_cache.queryPC(proj, vid)
            if out == 0:
                self.readyProj(None, vid, proj)
            elif out < 0:
                wid = self.plant.getWP().findWid([("task", "project"), ("vid", vid)])
                if wid is None:
                    self.plant.getWP().addWorker(self, proj, {"vid": vid})
                    self.checkResults(menu=True)
            # else:
            #     print("Waiting previous proj")

    def checkResults(self, menu=False, once=False):
        # print("Check results\tnb working", self.plant.getWP().infoStr(), self.plant.getWP().nbWorking())
        updates = self.plant.getWP().checkResults(self)
        if menu:
            updates["menu"] = True
        if not once: 
            if self.plant.getWP().nbWorking() > 0:
                if self.call_check is None:
                    self.call_check = wx.CallLater(Siren.results_delay, self.checkResults)
                else:
                    self.call_check.Restart(Siren.results_delay)
            else:
                self.call_check = None

        if once or not self.plant.getWP().isActive():
            updates["progress"] = True
        self.doUpdates(updates) ## To update the worker stoppers

    ##### receiving results
    def OnPrintTracks(self, event):
        print(self.dw.reds.tracksToStr())
    def readyTracks(self, tracks, source):
        if len(tracks) > 0:            
            self.dw.importTracks(tracks, source)
    def readyReds(self, wid, reds, tab):
        self.appendMinedReds(wid, reds)

    def readyProj(self, wid, vid, proj):
        if not self.withViews():
            return
        adjunct_vps = self.proj_cache.incomingPC(proj, vid)
        vv = self.viewsm.accessViewX(vid)
        if vv is not None:
            vv.readyProj(proj)
        for (avid, aproj) in adjunct_vps:
            vv = self.viewsm.accessViewX(avid)
            if vv is not None:
                vv.readyProj(aproj)
                

    ######################################################################
    ###########     VIEWS
    ######################################################################                       
    def OnPopList(self, event):
        if not self.withViews():
            return
        viewT = self.viewsm.getTableViewT(typeI=self.getTabType())
        if viewT is not None:
            if self.getDefaultTTab().hasFocusContainersL():
                for lid in self.getDefaultTTab().getSelectedLids():
                    what = self.getDefaultTTab().getItemsList(lid)
                    return self.viewsm.viewData(what, lid, viewT)

    def OnNewV(self, event=None):
        if not self.withViews():
            return
        tab, viewT = None, None
        if isinstance(event, wx.Event) and event.GetId() in self.ids_viewT:
            tab, viewT = self.ids_viewT[event.GetId()]
        if self.matchTabType("evr", tab=tab):
            what, iid = self.getViewWhatIid(tab)
            self.viewOpen(what, iid, viewT)

    def getViewWhatIid(self, tab=None):
        if not self.withViews():
            return
        what, iid = (None, None)
        if self.matchTabType("evr", tab=tab):
            iid = None
            if self.getDefaultTTab(tab=tab).hasFocusItemsL() and self.getDefaultTTab(tab=tab).nbSelected() == 1:
                what = self.getDefaultTTab(tab=tab).getSelectedItem()
                if what is not None:
                    iid = what.getUid()
            elif self.getDefaultTTab(tab=tab).nbSelected() > 0:
                what = self.getDefaultTTab(tab=tab).getSelectedItems()
                if what is not None and len(what) > 0:
                    if self.getDefaultTTab(tab=tab).hasFocusContainersL() and len(self.getDefaultTTab(tab=tab).getSelectedLids()) == 1:
                        iid = self.getDefaultTTab().getSelectedLids()[0]
                    else:
                        iid = -1
        return what, iid
        
    def viewOpen(self, what=None, iid=None, viewT=None):
        if not self.withViews():
            return
        if isinstance(what, ColM) or isinstance(what, RowE):
            what = self.createRedFromCol(what)
            iid = what.getUid()
        elif isinstance(what, Redescription):
            what = what.copy()
        if iid is not None:
            return self.viewsm.viewData(what, iid, viewT)


    ######################################################################
    ###########     ROWS / ENTITIES TAB HANDLING
    ######################################################################       
    def OnHigh(self, event):
        if self.matchTabType("e") and self.withViews():
            self.viewsm.setAllEmphasizedR([self.getDefaultTTab().getSelectedPos()], show_info=False, no_off=True)
            
    def OnShowCol(self, event):
        shw = False
        tab = self.ids_evTabs.get(event.GetId())
        if self.matchTabType("vr", tab=tab) and self.getDefaultTabId("e") in self.tabs:
            row = self.tabs[self.getDefaultTabId("e")]["tab"].showRidRed(self.tabs[self.getDefaultTabId("e")]["tab"].getSelectedRow(), self.getDefaultTTab(tab=tab).getSelectedItem())
            shw = True
        if shw:
            self.showTab(self.getDefaultTabId("e"))
            
    def showCol(self, side, col):
        if self.getDefaultTabId("e") in self.tabs:
            self.tabs[self.getDefaultTabId("e")]["tab"].showCol(side, col)

    def showDetailsBox(self, iid, turn_on):
        row_id, red = (None, None)
        if turn_on is not None and len(turn_on) == 1:
            row_id = list(turn_on)[0]
        if iid is not None:
            red = self.getRed(iid)            
        if self.getDefaultTabId("e") in self.tabs and row_id is not None:
            row = self.tabs[self.getDefaultTabId("e")]["tab"].showRidRed(row_id, red)
        if row is not None:
            self.showTab(self.getDefaultTabId("e"))
        elif isinstance(red, Redescription):
            dlg = wx.MessageDialog(self.toolFrame,
                                   self.prepareDetails(row_id, red),"Point Details", wx.OK|wx.ICON_INFORMATION)
            result = dlg.ShowModal()
            dlg.Destroy()

    def prepareDetails(self, row_id, red):
        dets = "%d:\n" % row_id
        isinstance(red, Redescription)
        for side,pref in [(0,""), (1,"")]:
            dets += "\n"
            for lit in red.queries[side].listLiterals():
                dets += ("\t%s=\t%s\n" % (self.dw.getData().col(side,lit.colId()).getName(), self.dw.getData().getValue(side, lit.colId(), row_id)))
        return dets

    def OnFlipExCol(self, event):
        if self.matchTabType("e"):
            self.getDefaultTTab().flipFocusCol(self.getDefaultTTab().getSelectedCol())
            

    ######################################################################
    ###########     REDS TAB HANDLING
    ######################################################################
    def OnActContent(self, event, more_info={}):
        tab = None
        if isinstance(event, wx.Event) and event.GetId() in self.ids_contentAct:
            tab, event = self.ids_contentAct[event.GetId()]
        info = self.getContentInfo(more_info, tab=tab)
        self.dw.OnActContent(event, info)
        self.refresh()
                        
    def OnExpand(self, event, task="expand"):
        tab = self.ids_evTabs.get(event.GetId())            
        if self.matchTabType("r", tab=tab):
            reds = self.getDefaultTTab(tab=tab).getSelectedItems()
            if len(reds) > 0:
                params = {"reds": [red for (rid, red) in reds], "task": task}
                self.expand(params)
    def OnImprove(self, event):
        self.OnExpand(event, task="improve")
            
    def OnMineAll(self, event):
        self.expand()
                    
    def createRedFromCol(self, col):
        red = Redescription.fromCol(col, self.getData())        
        self.dw.addItemToHist(red)
        self.refresh()
        return red
    
    def applyEditToData(self, red, ikey, vkey=None): ## + forward edits to views from there?
        old_red = self.dw.substituteRed(ikey[1], red, backup=True)
        if old_red is not None:
            self.refresh()
            
    def appendMinedReds(self, wid, reds):
        if len(reds) > 0:
            src = ('run', wid)
            trg_lid, iids, new_src = self.dw.appendRedsToSrc(reds, src)
            self.refresh()
                
    ######################################################################
    ###########     RESETS
    ######################################################################
    def refresh(self, rneeds=1):
        if rneeds == -1:
            rneeds = {"reset_all": True}
        elif rneeds == 1:
            rneeds = self.dw.getNeedsReloadDone()
            if rneeds.get("recompute"):
                self.dw.recompute()
                rneeds = self.dw.getNeedsReloadDone()
                
        if not type(rneeds) is dict:
            return
        
        rall = rneeds.get("reset_all", False)
        rdatainfo = rall
        if rall:
            if self.plant is not None:
                self.plant.getWP().closeDown(self)
            if self.withViews():
                self.viewsm.deleteAllViews()
            if self.getVizm() is not None:
                self.getVizm().reloadVizTab()
            self.resetLogger()

        ### RELOADING VIEWS
        if not rall and self.withViews():
            views_rneeds = rneeds.get("z", {})
            if views_rneeds.get("data"):
                for ikey in self.viewsm.getVKeys():
                    item = None
                    if ikey[0] == "r":
                        item = self.getRed(ikey[1])
                    self.viewsm.backEdit(item, ikey)
            else:
                if views_rneeds.get("fields"):
                    self.viewsm.refresh()
                for iid in views_rneeds.get("items", []):
                    item = self.getRed(iid)
                    self.viewsm.backEdit(item, ("r", iid))
            

        ### RELOADING ENTITIES
        entities_rneeds = rneeds.get("e", {})
        if entities_rneeds.get("data", rall):
            dt_rows = None
            if self.dw.getData() is not None:
                dt_rows = self.dw.getDataRows()
            self.getETab().resetData(dt_rows, fields_data=self.dw.getData())
            rdatainfo = True
        elif entities_rneeds.get("fields"):
            self.getETab().resetFields(self.dw.getData())
            rdatainfo = True
        elif len(entities_rneeds.get("lists", []))+len(entities_rneeds.get("lists_content", []))+len(entities_rneeds.get("items", [])) > 0:
            self.getETab().ResetView()
            
        ### RELOADING VARS
        vars_rneeds = rneeds.get("v", {})
        if "switch" in vars_rneeds:
            self.getVTab().setActiveLid(vars_rneeds.get("switch"))
        if vars_rneeds.get("data", rall) or vars_rneeds.get("fields"):
            self.getVTab().load(rfields=vars_rneeds.get("fields", rall))
            rdatainfo = True
        else:
            for (lid, selected_iids, new_lid) in vars_rneeds.get("lists_content", []):
                rdatainfo = True
                self.getVTab().refreshListContent(lid, selected_iids, new_lid)
            for lid in vars_rneeds.get("lists", []):
                rdatainfo = True
                self.getVTab().refreshList(lid)
            for iid in vars_rneeds.get("items", []):
                self.getVTab().refreshItem(iid)

        ### RELOADING REDS
        reds_rneeds = rneeds.get("r", {})
        if rneeds.get("actions_filters", rall):
            self.dw.setupFilterActs()
        if "switch" in reds_rneeds:
            self.getRTab().setActiveLid(reds_rneeds.get("switch"))
        if reds_rneeds.get("data", rall) or reds_rneeds.get("fields"):
            if reds_rneeds.get("fields", rall):
                details = {}
                if self.dw.getData() is not None:
                    details["names"] = self.dw.getData().getNames()
                    details["fmts"] = self.dw.getData().getFmts()
                self.getRTab().resetDetails(details)
            self.getRTab().load(rfields=reds_rneeds.get("fields", rall))
            if self.withViews():
                self.viewsm.refreshTables()
        else:
            lids, iids = set([]), set([])
            for (lid, selected_iids, new_lid) in reds_rneeds.get("lists_content", []):
                self.getRTab().refreshListContent(lid, selected_iids, new_lid)
                if not new_lid:
                    lids.add(lid)
            for lid in reds_rneeds.get("lists", []):
                self.getRTab().refreshList(lid)
                lids.add(lid)
            for iid in reds_rneeds.get("items", []):
                self.getRTab().refreshItem(iid)
                iids.add(iid)
            if self.withViews():
                self.viewsm.refreshTables(lids, iids)
            
        if rdatainfo: 
            self.updateDataInfo()
        if rneeds.get("switch") is not None:
            self.changePage(self.getDefaultTabId(rneeds.get("switch")))
        if rneeds.get("menus", True):
            self.updateMenus()
        
    def resetLogger(self):
        vlog = None
        if self.dw.getPreferences() is not None and self.dw.getPreference('verbosity') is not None:
            vlog = self.dw.getPreference('verbosity')

        self.logger.resetOut()
        if self.plant.getWP().isActive() and self.plant.getWP().getOutQueue() is not None:
            self.logger.addOut("inter", vlog, self.plant.getWP().getOutQueue(), self.plant.getWP().sendMessage)
        else:
            self.logger.addOut("quiet", vlog, None, self.loggingLogTab)
        self.logger.addOut("error", {"dw_error":1}, "stderr")
        self.logger.addOut("shut", {"dw_error":1}, None, self.loggingDWError)

    def getContentInfo(self, more_info={}, tab=None):
        tt = self.getDefaultTab(tab=tab)
        tab = self.getDefaultTTab(tab=tab)
        info_in = {"active_lid": None, "lids": None, "iids": [], "tab_type": tt["type"], "tab_id": tt["id"]}
        if "tab_type" in more_info:
            ttab = self.getTTab(self.getDefaultTabId(more_info["tab_type"]))
            if ttab is not None:
                tab = ttab
                info_in["tab_id"] = None
        if info_in["tab_id"] is None:
            info_in.update(more_info)            
        elif info_in["tab_type"] == "r" or info_in["tab_type"] == "v":
            info_in["active_lid"] = tab.getActiveLid()
            if "iids" in more_info:
                info_in["iids"] = more_info["iids"]
            elif tab.hasFocusItemsL():
                info_in["iids"] = tab.getSelectedIids()
            elif tab.hasFocusContainersL():
                info_in["lids"] = tab.getSelectedLids()
        elif info_in["tab_type"] == "e":
            info_in["iids"] = tab.getSelectedIids()
            info_in["row_ids"] = tab.getSelectedRowIds()
        info = self.dw.getContentInfo(info_in)
        return info
    
    def checkAndProceedWithUnsavedChanges(self, test=None, what="continue"):
        """Checks for unsaved changes and returns False if they exist and user doesn't want to continue
        and True if there are no unsaved changes or user wants to proceed in any case.
        If additional parameter 'test' is given, asks the question if it is true."""
        if test is None:
            test = self.dw.hasRedsChanged(inc_hist=False, inc_buffer=False) | self.dw.isChanged
        if test:
            dlg = wx.MessageDialog(self.toolFrame, 'Unsaved changes might be lost.\nAre you sure you want to %s?' % what, style=wx.YES_NO|wx.NO_DEFAULT|wx.ICON_EXCLAMATION, caption='Unsaved changes!')
            if dlg.ShowModal() == wx.ID_NO:
                return False
        return True
    

    ######################################################################
    ###########     IMPORT / EXPORT
    ######################################################################
    #### DATA
    def OnImportDataCSV(self, event):
        """Shows a custom dialog to open the two data files"""
        if not self.checkAndProceedWithUnsavedChanges():
            return 
        dlg = ImportDataCSVDialog(self)
        dlg.showDialog()
        self.refresh()
        
    def OnSaveVecAsVar(self, vec, name, side=1, force_type=None):
        self.dw.addVecCol(vec, name, side, force_type)
        self.refresh()

    #### PREFERENCES
    def OnImportPreferences(self, event):
        if not self.checkAndProceedWithUnsavedChanges(self.dw.preferences.isChanged):
            return
        dir_name = os.path.expanduser('~/')
        open_dlg = wx.FileDialog(self.toolFrame, message='Choose file', defaultDir = dir_name,
                                 style = wx.FD_OPEN|wx.FD_CHANGE_DIR)
        if open_dlg.ShowModal() == wx.ID_OK:
            path = open_dlg.GetPath()
            try:
                self.dw.importPreferencesFromFile(path)
            except:
                pass
        open_dlg.Destroy()
        self.refresh()

    def OnExportPreferences(self, mess="preferences", inc_def=False, conf_def=None):
        if self.dw.getPackageSaveFilename() is not None:
            dir_name = os.path.dirname(self.dw.getPackageSaveFilename())
        else:
            dir_name = os.path.expanduser('~/')

        save_dlg = wx.FileDialog(self.toolFrame, message='Save %s template to:' % mess, defaultDir = dir_name, style = wx.FD_SAVE|wx.FD_CHANGE_DIR)
        if save_dlg.ShowModal() == wx.ID_OK:
            path = save_dlg.GetPath()
            try:
                self.dw.exportPreferences(path, inc_def, conf_def)
            except Exception: 
                pass
        save_dlg.Destroy()
        self.refresh()
    def OnPrintoutPreferences(self, event):
        self.OnExportPreferences(mess="preferences")
    def OnPrintoutPreferencesTmpl(self, event):
        self.OnExportPreferences(mess="preferences template", conf_def=self.conf_defs+self.conf_defs_io)
    def OnPrintoutPreferencesDef(self, event):
        self.OnExportPreferences(mess="default preferences", inc_def=True, conf_def=self.conf_defs+self.conf_defs_io)
        
    #### PACKAGE
    def OnOpenPck(self, event):
        if not self.checkAndProceedWithUnsavedChanges():
            return
        wcd = 'All files|*|Siren packages (*.siren)|*.siren'

        if self.dw.getPackageSaveFilename() is not None:
            dir_name = os.path.dirname(self.dw.getPackageSaveFilename())
        else:
            dir_name = os.path.expanduser('~/')
        path = dir_name            
        open_dlg = wx.FileDialog(self.toolFrame, message='Choose a file', defaultDir=dir_name,  
			wildcard=wcd, style=wx.FD_OPEN|wx.FD_CHANGE_DIR)
        if open_dlg.ShowModal() == wx.ID_OK:
            path = open_dlg.GetPath()
            try:
                self.dw.openPackage(path)
            except:
                raise
        open_dlg.Destroy()
        self.refresh()
        # DEBUGGING
        #wx.MessageDialog(self.toolFrame, 'Opened package from '+path).ShowModal()
        
    def OnSave(self, event):
        if not (self.dw.isFromPackage and self.dw.getPackageSaveFilename() is not None):
            wx.MessageDialog(self.toolFrame, 'Cannot save data that is not from a package\nUse Save As... instead', style=wx.OK|wx.ICON_EXCLAMATION, caption='Error').ShowModal()
            return
        try:
            self.dw.savePackage()
        except:
            pass
        self.refresh()
    def OnSaveAs(self, event):
        if self.dw.getPackageSaveFilename() is not None:
            dir_name = os.path.dirname(self.dw.getPackageSaveFilename())
        else:
            dir_name = os.path.expanduser('~/')

        save_dlg = wx.FileDialog(self.toolFrame, message="Save as", defaultDir=dir_name,
                                 style=wx.FD_SAVE|wx.FD_CHANGE_DIR)
        if save_dlg.ShowModal() == wx.ID_OK:
            path = save_dlg.GetPath()
            try:
                self.dw.savePackageToFile(path)
            except:
                pass
        save_dlg.Destroy()
        self.refresh()

    #### REDESCRIPTIONS
    def OnImportRedescriptions(self, event):
        if not self.checkAndProceedWithUnsavedChanges():
            return
        reds, sortids, path  = (None, None, "")
        wcd = 'All files|*|Query files (*.queries)|*.queries|'
        dir_name = os.path.expanduser('~/')

        open_dlg = wx.FileDialog(self.toolFrame, message='Choose file', defaultDir = dir_name,
                                 style = wx.FD_OPEN|wx.FD_CHANGE_DIR)
        if open_dlg.ShowModal() == wx.ID_OK:
            path = open_dlg.GetPath()
            try:
                trg_lid, iids, newl = self.dw.loadRedescriptionsFromFile(path)
            except:
                pass
        open_dlg.Destroy()        
        self.refresh()
        
    def OnExportReds(self, event):
        tab = self.ids_evTabs.get(event.GetId())
        info = self.getContentInfo(tab=tab)
        if info["nb"] < 1:
            wx.MessageDialog(self.toolFrame, 'No redescription to export!',
                                 style=wx.OK|wx.ICON_EXCLAMATION, caption='Error').ShowModal()
            return

        if info["path"] is not None:
            dir_name = os.path.dirname(info["path"])
        elif self.dw.getPackageSaveFilename() is not None:
            dir_name = os.path.dirname(self.dw.getPackageSaveFilename())
        else:
            dir_name = os.path.expanduser('~/')

        save_dlg = wx.FileDialog(self.toolFrame, message='Save redescriptions to:', defaultDir = dir_name, style = wx.FD_SAVE|wx.FD_CHANGE_DIR)
        if save_dlg.ShowModal() == wx.ID_OK:
            new_path = save_dlg.GetPath()
            try:
                self.dw.exportRedescriptions(new_path, iids=info["iids"], lid=info["lid"])
            except:
                pass
        save_dlg.Destroy()        
        self.refresh()            
    def OnSaveRedList(self, event):
        tab = self.ids_evTabs.get(event.GetId())
        if not self.matchTabType("r", tab=tab):
            return
        info = self.getContentInfo(tab=tab)
        if info["nb"] < 1:
            wx.MessageDialog(self.toolFrame, 'Cannot save list: no redescription loaded',
                                 style=wx.OK|wx.ICON_EXCLAMATION, caption='Error').ShowModal()
            return

        elif info["path"] is None:
            wx.MessageDialog(self.toolFrame, 'Cannot save list, no output\nUse Save List As... instead', style=wx.OK|wx.ICON_EXCLAMATION, caption='Error').ShowModal()
            return
        try:
            self.dw.exportRedescriptions(info["path"], iids=info["iids"], lid=info["lid"])
        except:
            pass
        self.refresh()            
    def OnSaveRedListAs(self, event):
        tab = self.ids_evTabs.get(event.GetId())
        if not self.matchTabType("r", tab=tab):
            return
        self.saveRedListAs(tab, self.getFrame())
    def saveRedListAs(self, tab, frame):
        info = self.getContentInfo(tab=tab)
        if info["nb"] < 1:
            wx.MessageDialog(frame, 'Cannot save list: no redescription loaded',
                                 style=wx.OK|wx.ICON_EXCLAMATION, caption='Error').ShowModal()
            return

        if info["path"] is not None:
            dir_name = os.path.dirname(info["path"])
        elif self.dw.getPackageSaveFilename() is not None:
            dir_name = os.path.dirname(self.dw.getPackageSaveFilename())
        else:
            dir_name = os.path.expanduser('~/')

        save_dlg = wx.FileDialog(frame, message='Save redescription list to:', defaultDir = dir_name, style = wx.FD_SAVE|wx.FD_CHANGE_DIR)
        if save_dlg.ShowModal() == wx.ID_OK:
            new_path = save_dlg.GetPath()
            try:
                self.dw.exportRedescriptions(new_path, iids=info["iids"], lid=info["lid"])
            except:
                pass
        save_dlg.Destroy()
        self.refresh()
        
    def OnExportFigs(self, event):
        if not self.withViews():
            return
        tab = self.ids_evTabs.get(event.GetId())
        if not self.matchTabType("vr", tab=tab):
            return
        info = self.getContentInfo(tab=tab)
        if info["nb"] < 1:
            wx.MessageDialog(self.toolFrame, 'Cannot save plots: no redescription loaded',
                                 style=wx.OK|wx.ICON_EXCLAMATION, caption='Error').ShowModal()
            return

        if info["path"] is not None:
            dir_name = os.path.dirname(info["path"])
        elif self.dw.getPackageSaveFilename() is not None:
            dir_name = os.path.dirname(self.dw.getPackageSaveFilename())
        else:
            dir_name = os.path.expanduser('~/')

        items = self.dw.getVarsOrRedsForInfo(info)
        what = None
        if len(items) > 0:
            what = items[0][1] ### assume all to plot yield the same
        view_items = self.viewsm.getViewsItems(what=what)
        dlg = ExportFigsDialog(self, view_items, items, dir_name)
        dlg.showDialog()
