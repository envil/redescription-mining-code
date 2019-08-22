import wx
import numpy
from .factView import ViewFactory

import pdb

######################################################################
###########     VIEWS MANAGER
######################################################################

class ViewsManager:

    def __init__(self, parent):
        self.parent = parent
        self.view_map = {}
        self.vtoi = {}
        self.itov = {}
        ### Record highlight rows for reds views
        self.emphasized = {}
        ### MENU ids to opened views
        self.menu_opened_views = {}
        
        self.selectedViewX = -1

    def getTypeD(self):
        if self.parent.dw is not None:
            return self.parent.dw.getTypeD()
        return {}
    def getExtensionKeys(self):
        if self.parent.dw is not None:
            return self.parent.dw.getExtensionKeys()
        return []

    def getViewsItems(self, what=None, vkey=None):
        excludeT = None
        typeI = ViewFactory.typeIWhat(what)
        if vkey in self.vtoi:
            typeI = self.vtoi[vkey][0]
            excludeT = [vkey[0]]
        return ViewFactory.getViewsInfo(typeI, self.getTypeD(), self.getExtensionKeys(), what, excludeT)

    def getTableViewT(tcl, typeI="r"):
        return ViewFactory.getTableViewT(typeI)
    
    def getDefaultViewT(self, typeI="r"):
        return ViewFactory.getDefaultViewT(typeI, self.getTypeD())

    def getNbViews(self):
        return len(self.view_map)

    def getNbActiveViewsForMenu(self):
        return len([vkey for (vkey, view) in self.view_map.items() if not view.isIntab()])
    def getActiveViewsForMenu(self):
        return sorted([(vkey, view.getShortDesc()) for (vkey, view) in self.view_map.items() if not view.isIntab()], key=lambda x: x[1])

    def accessViewX(self, vkey):
        if vkey in self.view_map:
            return self.view_map[vkey]
    def iterateViews(self):
        return list(self.view_map.items())
    def getVKeys(self):
        return list(self.itov.keys())
    
    def refreshTables(self, lids=None, iids=[]):
        for vid, view in self.iterateViews():
            if view.isTable():
                view.refreshTable(lids, iids)        
    
    def getViewX(self, viewT, vid=None):
        if (viewT, vid) not in self.view_map:
            view = ViewFactory.getView(viewT, self.parent, wx.NewId())
            if view is None:
                return
            self.selectedViewX = view.getId()
            self.view_map[self.selectedViewX] = view
        else:
            self.selectedViewX = (viewT, vid)
        self.view_map[self.selectedViewX].toTop()
        return self.view_map[self.selectedViewX]

    def deleteView(self, vkey, freeing=True):
        if vkey in self.view_map:
            self.parent.plant.getWP().layOff(self.parent.plant.getWP().findWid([("task", "project"), ("vid", vkey)]))
            pos = self.view_map[vkey].getGPos()
            intab = self.view_map[vkey].isIntab()
            self.view_map[vkey].destroy()

            if intab and freeing:
                self.parent.vizm.setVizcellFreeded(pos)
            del self.view_map[vkey]

    def deleteAllViews(self):
        self.selectedViewX = -1
        vkeys = list(self.view_map.keys())
        for vkey in vkeys:
            self.view_map[vkey].OnQuit(None, upMenu=False)
        self.view_map = {}
        self.parent.updateMenus()

    def viewOther(self, viewT, vkey):
        if vkey in self.vtoi:
            what = self.view_map[vkey].getWhat()
            (typeI, iid) = self.vtoi[vkey]
            self.viewData(what, iid, viewT)

    def viewData(self, what, iid, viewT=None):
        typeI = ViewFactory.typeIWhat(what)
        if viewT is None:
            viewT = self.getDefaultViewT(typeI)            
        vid = None
        ## if iid == -1 and
        if ord(typeI) < ord("a"):
            #### HERE SIMPLIFY LIST ELEMENT ID            
            # pdb.set_trace()
            # iid = -numpy.sum([2**k for (k,v) in what])
            # if iid < -99:
            if iid is None or iid < 0:                
                iid = numpy.min([0]+[k[-1] for k in self.vtoi.values() if ord(k[0]) < ord("a") and k[-1] < 0])-1
            ikey = (typeI, iid)
        else:
            ikey = ("r", iid)
            
        if ikey in self.itov and viewT in self.itov[ikey]:
            vid = self.itov[ikey][viewT]
            
        mapV = self.getViewX(viewT, vid)
        if vid is None and mapV is not None:
            if ikey[0] != -1:
                self.registerView(mapV.getId(), ikey, upMenu=False)
            mapV.setCurrent(what, iid)
            if ikey[0] != -1:
                mapV.updateTitle()
                mapV.lastStepInit()
                mapV.addStamp(viewT)
                self.parent.updateMenus()
        return mapV
            
    def registerView(self, vkey, ikey, upMenu=True):        
        self.vtoi[vkey] = ikey
        if ikey not in self.itov:
            self.itov[ikey] = {}
        self.itov[ikey][vkey[0]] = vkey[1]
        if upMenu:
            self.parent.updateMenus()

    def unregisterView(self, vkey, upMenu=True):
        if vkey in self.vtoi:
            ikey = self.vtoi[vkey]

            del self.vtoi[vkey]
            del self.itov[ikey][vkey[0]]

            ### if there are no other view referring to same red, clear emphasize lines
            if len(self.itov[ikey]) == 0:
                del self.itov[ikey]
                if ikey in self.emphasized:
                    del self.emphasized[ikey]

            if upMenu:
                self.parent.updateMenus()

    def OnViewTop(self, event):
        self.viewToTop(event.GetId())

    def viewToTop(self, vid):
        if vid in self.menu_opened_views and \
               self.menu_opened_views[vid] in self.view_map:
            self.view_map[self.menu_opened_views[vid]].toTop()

    def OnCloseViews(self, event):
        self.closeViews()
        self.parent.toTop()

    def closeViews(self):
        vkeys = list(self.view_map.keys())
        for vkey in vkeys:
            if not self.view_map[vkey].isIntab():
                self.view_map[vkey].OnQuit()

    def makeViewsMenu(self, frame, menuViews):
        self.menu_opened_views = {}

        for vid, desc in self.getActiveViewsForMenu():
            ID_VIEW = wx.NewId()
            self.menu_opened_views[ID_VIEW] = vid 
            m_view = menuViews.Append(ID_VIEW, "%s" % desc, "Bring view %s on top." % desc)
            frame.Bind(wx.EVT_MENU, self.OnViewTop, m_view)

        if self.getNbActiveViewsForMenu() == 0:
            ID_NOP = wx.NewId()
            menuViews.Append(ID_NOP, "No view opened", "There is no view currently opened.")
            menuViews.Enable(ID_NOP, False)
        else:
            menuViews.AppendSeparator()
            ID_VIEW = wx.NewId()
            m_view = menuViews.Append(ID_VIEW, "Close all views", "Close all views.")
            frame.Bind(wx.EVT_MENU, self.OnCloseViews, m_view)
        return menuViews

    def makeMenusForViews(self):
        for vid, view in self.view_map.items():
            view.makeMenu()
                        
    def refresh(self, iids=None):
        for vkey, view in self.view_map.items():
            if iids is None or self.vtoi[vkey][1] in iids:
                view.refresh()
    def getItemId(self, vkey):
        if vkey in self.vtoi:
            return "%s%s" % self.vtoi[vkey]
        return "?"    
    def getItemViewCount(self, vkey):
        if vkey in self.vtoi:
            return len(self.itov[self.vtoi[vkey]])
        return 0
    def dispatchEdit(self, red, ikey=None, vkey=None):
        if ikey is None and vkey in self.vtoi:
            ikey = self.vtoi[vkey]            
        self.parent.applyEditToData(red, ikey, vkey)
        
    def backEdit(self, red, ikey=None, vkey=None):
        # if ikey is None:
        #     typeI = ViewFactory.typeIWhat(red)
        #     if iid is None:
        #         iid = red.getUid()
        #     ikey = (typeI, iid)
            
        for (vt, vid) in self.itov.get(ikey, {}).items():
            if (vt, vid) != vkey:
                if red is not None:
                    mm = self.accessViewX((vt, vid))
                    mm.setCurrent(red)
                else:
                    self.deleteView(vkey= (vt, vid))

    def doFlipEmphasizedR(self, vkey):
        if vkey in self.vtoi and self.vtoi[vkey] in self.emphasized:
            emph = list(self.emphasized[self.vtoi[vkey]])
            self.setEmphasizedR(vkey, self.emphasized[self.vtoi[vkey]])
            self.parent.OnActContent("FlipEnabled", more_info={"row_ids": emph, "tab_type": "e"})

    def getEmphasizedR(self, vkey):
        if vkey in self.vtoi and self.vtoi[vkey] in self.emphasized:
            return self.emphasized[self.vtoi[vkey]]
        return set()

    def setAllEmphasizedR(self, lids=None, show_info=False, no_off=False):
        for vkey in self.vtoi:
            self.setEmphasizedR(vkey, lids, show_info, no_off)

    def setEmphasizedR(self, vkey, lids=None, show_info=False, no_off=False):
        if vkey in self.vtoi:
            toed = self.vtoi[vkey]
            if toed not in self.emphasized:
                self.emphasized[toed] = set()
            if lids is None:
                turn_off = self.emphasized[toed]
                turn_on =  set()
                self.emphasized[toed] = set()
            else:
                turn_on =  set(lids) - self.emphasized[toed]
                if no_off:
                    turn_off = set()
                    self.emphasized[toed].update(turn_on)
                else:
                    turn_off = set(lids) & self.emphasized[toed]
                    self.emphasized[toed].symmetric_difference_update(lids)

            for (vt, vid) in self.itov[toed].items():
                mm = self.accessViewX((vt, vid))
                mm.emphasizeOnOff(turn_on=turn_on, turn_off=turn_off)
            
            if len(turn_on) == 1 and show_info:
                self.parent.showDetailsBox(toed, turn_on)
                        

