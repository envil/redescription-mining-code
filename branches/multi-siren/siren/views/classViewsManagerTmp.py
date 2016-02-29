import wx
from factView import ViewFactory

import pdb

class ViewsManager:

    def __init__(self, parent):
        self.parent = parent
        self.view_ids = {}

        self.selectedViewX = -1
        self.opened_edits = {}
        self.opened_views = {}
        self.emphasized = {}

    def isGeospatial(self):
        return self.parent.dw.isGeospatial()

    def getViewsItems(self, tab_type=None, queries=None, excludeT=None):
        return ViewFactory.getViewsInfo(tab_type, self.isGeospatial(), queries, excludeT)

    def getDefaultViewT(self, type_tab=None):
        return ViewFactory.getDefaultViewT(geo=self.isGeospatial(), type_tab=type_tab)

    def getNbActiveViewsForMenu(self):
        return len(self.view_ids)
    def getActiveViewsForMenu(self):
        return sorted([(vid, view.getShortDesc()) for (vid, view) in self.view_ids.items() if not view.isIntab()], key=lambda x: x[1])


    def accessViewX(self, mid):
        if mid in self.view_ids:
            return self.view_ids[mid]
    def iterateViews(self):
        return self.view_ids.items()


    def getViewX(self, vid=None, viewT=None):
        if viewT is None:
            viewT = self.getDefaultViewT()
            
        if (viewT, vid) not in self.view_ids:
            view = ViewFactory.getView(viewT, self.parent, wx.NewId())
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
            self.parent.plant.getWP().layOff(self.parent.plant.getWP().findWid([("wtyp", "project"), ("vid", vK)]))
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
        self.parent.updateMenus()


################################### GRID
    def viewData(self, viewT, pos=None, oid=None, red=None, tabId=None):
        print "View data", viewT, pos, oid
        if oid is not None:
            if oid in self.opened_edits:
                pos = self.opened_edits[oid]
        vid = None
        for (k,v) in self.opened_edits.items():
            if v == pos and viewT == k[0]:
                vid = k[1]
                break
            
        mapV = self.getViewX(vid, viewT)
        if vid is None and mapV is not None:
            self.registerView(mapV.getId(), pos, upMenu=False)
            #### VIEW MAN
            mapV.setCurrent(red, tabId)
            mapV.updateTitle()
            self.parent.updateMenus()
            
    def registerView(self, key, pos, upMenu=True):
        self.opened_edits[key] = pos
        if upMenu:
            self.parent.updateMenus()

    def unregisterView(self, key, upMenu=True):
        if key in self.opened_edits.keys():
            pos = self.opened_edits[key]
            del self.opened_edits[key]
            ### if there are no other view referring to same red, clear emphasize lines
            if pos not in self.opened_edits.values():
                if pos in self.emphasized:
                    del self.emphasized[pos]
            if upMenu:
                self.parent.updateMenus()

    def OnViewTop(self, event):
        self.viewToTop(event.GetId())

    def viewToTop(self, vid):
        if vid in self.opened_views and \
               self.opened_views[vid] in self.view_ids:
            self.view_ids[self.opened_views[vid]].toTop()

    def OnCloseViews(self, event):
        self.closeViews()
        self.parent.toTop()

    def closeViews(self):
        view_keys = self.view_ids.keys()
        for key in view_keys:
            if self.view_ids[key].isIntab():
                self.view_ids[key].OnQuit()

    def makeViewsMenu(self, frame, menuViews):
        self.opened_views = {}

        for vid, desc in self.getActiveViewsForMenu():
            ID_VIEW = wx.NewId()
            self.opened_views[ID_VIEW] = vid 
            m_view = menuViews.Append(ID_VIEW, "%s" % desc, "Bring view %s on top." % desc)
            frame.Bind(wx.EVT_MENU, self.OnViewTop, m_view)

        if self.getNbActiveViewsForMenu() == 0:
            ID_NOP = wx.NewId()
            m_nop = menuViews.Append(ID_NOP, "No view opened", "There is no view currently opened.")
            menuViews.Enable(ID_NOP, False)
        else:
            menuViews.AppendSeparator()
            ID_VIEW = wx.NewId()
            m_view = menuViews.Append(ID_VIEW, "Close all views", "Close all views.")
            frame.Bind(wx.EVT_MENU, self.OnCloseViews, m_view)
        return menuViews

    def makeMenusForViews(self):
        for vid, view in self.view_ids.items():
            view.makeMenu()
            
    def getToed(self, edit_key):
        if edit_key in self.opened_edits.keys():
            return self.opened_edits[edit_key]
        return None
            
    def updateEdit(self, edit_key, red, toed, tabId):
        for k,v in self.opened_edits.items():
            if v == toed and k != edit_key:
                mc = self.accessViewX(k)
                if mc is not None:
                    mc.setCurrent(red, tabId)

    def updateEditHist(self, edit_key, red, new_toed, old_toed, tabId):
        for k,v in self.opened_edits.items():
            if v == old_toed:
                self.opened_edits[k] = new_toed 
                mc = self.accessViewX(k)
                if mc is not None:
                    mc.updateTitle()
                    if k != edit_key:
                        mc.setCurrent(red, tabId)

        if old_toed in self.emphasized and edit_key in self.opened_edits:
            self.emphasized[self.opened_edits[edit_key]] = self.emphasized[old_toed]
            del self.emphasized[old_toed]

        self.parent.updateMenus()

    def getViewsCount(self, edit_key):
        count = 0
        if edit_key in self.opened_edits.keys():
            toed = self.opened_edits[edit_key]
        if toed is not None and toed >= 0: ### VIEW MAN  and toed < len(self.data):
            for k,v in self.opened_edits.items():
                if v == toed: # and k != edit_key:
                    count += 1
        return count

    def addAndViewTop(self, queries, viewT):
        mapV = self.getViewX(None, viewT)
        red = mapV.setCurrent(queries)
        ### VIEW MAN 
        # self.registerView(mapV.getId(), len(self.data)-1, upMenu=False)
        # mapV.setSource(self.tabId)
        self.parent.updateMenus()
        mapV.updateTitle()



#################################################################
    def deleteItem(self, edit_key):
        upMenu = False
        for edit_key in self.opened_edits.keys():
            if self.opened_edits[edit_key] == pos:
                self.opened_edits[edit_key] = None
            elif self.opened_edits[edit_key] > pos:
                self.opened_edits[edit_key] -= 1
                upMenu = True
                self.parent.accessViewX(edit_key).updateTitle()
        ks = sorted(self.emphasized.keys())
        for k in ks:
            if k == pos:
                del self.emphasized[k]
            elif k > pos:
                self.emphasized[k-1] = self.emphasized[k]
                del self.emphasized[k]
        return upMenu

    def recomputeAll(self):
        for k,v in self.opened_edits.items():
            mc = self.accessViewX(k)
            if mc is not None:
                mc.refresh()

    def doFlipEmphasizedR(self, edit_key):
        if edit_key in self.opened_edits.keys() and self.opened_edits[edit_key] in self.emphasized:
            self.parent.flipRowsEnabled(self.emphasized[self.opened_edits[edit_key]])
            self.setEmphasizedR(edit_key, self.emphasized[self.opened_edits[edit_key]])

    def getEmphasizedR(self, edit_key):
        if edit_key in self.opened_edits.keys() and self.opened_edits[edit_key] >= 0 and \
               self.opened_edits[edit_key] in self.emphasized:
            # and self.opened_edits[edit_key] < len(self.data) and \ 
            return self.emphasized[self.opened_edits[edit_key]]
        return set()

    def setAllEmphasizedR(self, lids=None, show_info=False, no_off=False):
        for edit_key in self.opened_edits.keys():
            self.setEmphasizedR(edit_key, lids, show_info, no_off)

    def setEmphasizedR(self, edit_key, lids=None, show_info=False, no_off=False):
        if edit_key in self.opened_edits.keys() \
               and self.opened_edits[edit_key] >= 0: # and self.opened_edits[edit_key] < len(self.data):

            toed = self.opened_edits[edit_key]
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

            for k,v in self.opened_edits.items():
                if v == toed:
                    mm = self.accessViewX(k)
                    mm.emphasizeOnOff(turn_on=turn_on, turn_off=turn_off)
            
            if len(turn_on) == 1 and show_info:
                for lid in turn_on:
                    self.parent.showDetailsBox(lid, self.data[toed])
