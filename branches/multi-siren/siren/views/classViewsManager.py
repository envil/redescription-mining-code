import wx
from classFiller import Filler
from factView import ViewFactory

import pdb

######################################################################
###########     INTAB VIZ TAB
######################################################################

class VizManager:

    viz_grid = [2,0]
    intab = False #True
    color_add = (16, 82, 0)
    color_drop = (190, 10, 10)
    color_vizb = (20, 20, 20)

    def __init__(self, parent, tabId, frame, short=None):
        self.parent = parent
        self.tabId = tabId
        self.short = short
        self.viz_postab = self.parent.tabs_keys.index(self.tabId)

        self.vfiller_ids = {}
        self.vused_ids = {}
        self.buttons = {}
        self.selected_cell = None
        
        self.drawSW(frame)
        self.initialize()
        
    def initialize(self):
        if self.parent.dw is not None:
            self.viz_grid = [self.parent.dw.getPreference('intab_nbr'),
                             self.parent.dw.getPreference('intab_nbc')]

        if self.hasVizIntab():
            self.fillInViz()
            self.addVizExts()
            self.setVizButtAble()
            self.updateVizcellSelected()
            if not self.parent.tabs["viz"]["hide"] and self.parent.sysTLin():
                self.getSW().Show()
            if self.viz_postab >= len(self.parent.tabs_keys) or self.parent.tabs_keys[self.viz_postab] != "viz":
                # print "In Viz"
                self.parent.tabs_keys.insert(self.viz_postab, "viz")

        else:
            self.getSW().Hide()
            if self.viz_postab < len(self.parent.tabs_keys) and self.parent.tabs_keys[self.viz_postab] == "viz":
                # print "Pop Viz"
                self.parent.tabs_keys.pop(self.viz_postab)

    def getTitle(self):
        return self.short

    def setVizCheck(self, check=True):
        self.intab = check

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

    def drawSW(self, frame):
        self.sw = wx.ScrolledWindow(frame, -1, style=wx.HSCROLL|wx.VSCROLL)
        self.sw.SetScrollRate(5, 5)        
        # sw.SetSizer(wx.GridSizer(rows=2, cols=3, vgap=0, hgap=0))
        self.sw.SetSizer(wx.GridBagSizer(vgap=0, hgap=0))

    def getSW(self):
        return self.sw

    def clearVizTab(self):
        for sel in self.vfiller_ids:
            panel = self.vfiller_ids[sel].popSizer()
            panel.Destroy()
        for sel in self.vused_ids:
            ### Free another view            
            ## TODO VM
            self.parent.accessViewX(self.vused_ids[sel][0]).OnQuit(upMenu=False, freeing=False)
            
        for bi, bb in self.buttons.items():
            self.getSW().GetSizer().Detach(bb["button"])
            bb["button"].Destroy()

        self.vfiller_ids = {}
        self.vused_ids = {}
        self.buttons = {}
        self.selected_cell = None

    def reloadVizTab(self):
        if self.isReadyVizIntab():
            self.clearVizTab()
        self.initialize()
        self.parent.doUpdates({"menu":True})
            
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
            ## TODO VM
            self.parent.accessViewX(self.vused_ids[sel][0]).OnQuit(upMenu=False, freeing=False)

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
                self.vfiller_ids[(i,j)] = Filler(self.parent, (i,j))

    def addGridDimViz(self, dim):
        for bi, but in self.buttons.items():
            if but["action"][1] == -1:
                self.getSW().GetSizer().Detach(but["button"])
                ddim = but["action"][0]
                ppos, pspan = ([1, 1], [1, 1])
                ppos[ddim] += self.getVizGridNbDim(ddim)
                pspan[1-ddim] = self.getVizGridNbDim(1-ddim)
                self.getSW().GetSizer().Add(but["button"], pos=ppos, span=pspan, flag=wx.EXPAND|wx.ALIGN_CENTER, border=0)

        sizeb = (self.getVizBbsiz(), 1)
        bid = wx.NewId()
        but = wx.Button(self.getSW(), bid, "", style=wx.NO_BORDER, size=(sizeb[dim], sizeb[1-dim]))
        but.SetBackgroundColour(self.color_drop)
        posb = [0,0]
        posb[dim] = self.getVizGridNbDim(dim)
        self.getSW().GetSizer().Add(but, pos=tuple(posb), flag=wx.EXPAND|wx.ALIGN_CENTER, border=0)
        self.buttons[bid] = {"action": (dim, self.getVizGridNbDim(dim)), "button": but}
        but.Bind(wx.EVT_BUTTON, self.OnChangeGridViz)
        ## but.Bind(wx.EVT_ENTER_WINDOW, self.OnPrintName)

        ppos = [self.getVizGridNbDim(dim), self.getVizGridNbDim(dim)]
        for i in range(1, self.getVizGridNbDim(1-dim)+1):
            ppos[1-dim] = i
            self.vfiller_ids[tuple(ppos)] = Filler(self.parent, tuple(ppos))

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
                ## TODO VM
                self.parent.accessViewX(self.vused_ids[sel][0]).OnQuit(upMenu=False, freeing=False)

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
                    self.parent.accessViewX(self.vused_ids[sel][0]).resetGPos(nel)
                    self.vused_ids[nel] = self.vused_ids.pop(sel)
                    
        ### adjust buttons
        bis = self.buttons.keys()
        for bi in bis:
            but = self.buttons[bi]
            if but["action"][1] == -1:
                self.getSW().GetSizer().Detach(but["button"])
                ddim = but["action"][0]
                ppos, pspan = ([1, 1], [1, 1])
                ppos[ddim] += self.getVizGridNbDim(ddim)
                pspan[1-ddim] = self.getVizGridNbDim(1-ddim)
                self.getSW().GetSizer().Add(but["button"], pos=ppos, span=pspan, flag=wx.EXPAND|wx.ALIGN_CENTER, border=0)
            elif but["action"][0] == dim and but["action"][1] == self.getVizGridNbDim(dim)+1:
                bb = self.buttons.pop(bi)
                self.getSW().GetSizer().Detach(bb["button"])
                bb["button"].Destroy()

    def addVizExts(self):
        sizeb = (self.getVizBbsiz(), 1)
        for which in [0, 1]:
            posb = [0,0]
            for i in range(1, self.getVizGridNbDim(which)+1):
                bid = wx.NewId()
                but = wx.Button(self.getSW(), bid, "", style=wx.NO_BORDER, size=(sizeb[which], sizeb[1-which]))
                but.SetBackgroundColour(self.color_drop)
                posb[which] = i
                self.getSW().GetSizer().Add(but, pos=tuple(posb), flag=wx.EXPAND|wx.ALIGN_CENTER, border=0)
                self.buttons[bid] = {"action": (which, i), "button": but}
                but.Bind(wx.EVT_BUTTON, self.OnChangeGridViz)
                ## but.Bind(wx.EVT_ENTER_WINDOW, self.OnPrintName)

            bid = wx.NewId()
            but = wx.Button(self.getSW(), bid, "", style=wx.NO_BORDER, size=(sizeb[1-which], sizeb[which]))
            but.SetBackgroundColour(self.color_add)
            ppos, pspan = ([1, 1], [1, 1])
            ppos[which] += self.getVizGridNbDim(which)
            pspan[1-which] = self.getVizGridNbDim(1-which)
            self.getSW().GetSizer().Add(but, pos=ppos, span=pspan, flag=wx.EXPAND|wx.ALIGN_CENTER, border=0)
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
            self.decrementVizGridDim(self.buttons[event.GetId()]["action"][0],
                                     self.buttons[event.GetId()]["action"][1])
    def setActiveViz(self, fid=None):
        for k,v in self.vfiller_ids.items():
            if k == fid:
                self.setVizcellSelected(fid)
                v.setActive()
            else:
                v.setUnactive()

    def resizeViz(self):
        if self.isReadyVizIntab():
            ### TODO VM
            for (vid, view) in self.parent.viewsm.iterateViews():
                if view.isIntab():
                    view._SetSize()
            for (vid, view) in self.vfiller_ids.items():
                view._SetSize()

    def hideShowBxViz(self):
        if self.isReadyVizIntab():
            ### TODO VM
            for (vid, view) in self.parent.viewsm.iterateViews():
                if view.isIntab():
                    view.hideShowOpt()
                    # view._SetSize()
            # for (vid, view) in self.vfiller_ids.items():
            #     view._SetSize()


    def setVizcellFreeded(self, pos):
        self.vused_ids.pop(pos)
        self.vfiller_ids[pos] = Filler(self.parent, pos)
        self.updateVizcellSelected()

    def isVizSplit(self):
        return self.parent.hasSplit() and self.parent.splitter.IsSplit()
    
    def vizTabToSplit(self):
        if not self.parent.hasSplit():
            return
        self.parent.tabbed.RemovePage(self.viz_postab)
        # print "Pop viz tab key"
        self.parent.tabs_keys.pop(self.viz_postab)
        self.getSW().Reparent(self.parent.splitter)
        self.parent.splitter.SplitHorizontally(self.parent.tabbed, self.getSW())

    def vizSplitToTab(self):
        if not self.parent.hasSplit():
            return
        if self.isVizSplit():
            self.parent.splitter.Unsplit(self.getSW())
        self.getSW().Reparent(self.parent.tabbed)
        self.parent.tabbed.InsertPage(self.viz_postab, self.getSW(), self.getTitle())
        if self.parent.sysTLin():
            self.getSW().Show()
        # print "Insert viz tab key"
        self.parent.tabs_keys.insert(self.viz_postab, "viz")
        

    def OnSplitchange(self):
        if not self.parent.hasSplit():
            return

        if self.hasVizIntab():
            if self.viz_postab < len(self.parent.tabs_keys) and self.parent.tabs_keys[self.viz_postab] == "viz":
                self.vizTabToSplit()
                self.parent.buttViz.SetBitmap(self.parent.icons["unsplit_frame"])
                # self.parent.buttViz.SetValue(False)
                # self.parent.buttViz.SetLabel("u")
                # self.parent.buttViz.SetForegroundColour((255, 255, 255))
                # self.parent.buttViz.SetBackgroundColour((0, 0, 0))
            else:
                self.vizSplitToTab()
                self.parent.buttViz.SetBitmap(self.parent.icons["split_frame"])
                # self.parent.buttViz.SetValue(False)
                # self.parent.buttViz.SetLabel("s")
                # self.parent.buttViz.SetForegroundColour((0,0,0))
                # self.parent.buttViz.SetBackgroundColour((255, 255, 255))

            self.hideShowBxViz()
            self.parent.doUpdates({"menu":True})


######################################################################
######################################################################
######################################################################

# class ViewsManager:

#     def __init__(self, parent):
#         self.parent = parent
#         self.vid_to_rid = {}
#         self.rid_to_vids = {}

#         self.selectedViewX = -1
#         self.opened_edits = {}
#         self.emphasized = {}

#     def isGeospatial(self):
#         return self.parent.dw.isGeospatial()

#     def registerView(self, rid, vid):
#         self.vid_to_rid[vid] = rid
#         if rid not in self.rid_to_vids:
#             self.rid_to_vids[rid] = []
#         self.rid_to_vids[rid].append(vid)

#     def unregisterView(self, vid):
#         if vid in self.vid_to_rid:
#             rid = self.vid_to_rid[vid]
#             self.rid_to_vids[rid].remove(vid)
#             del self.vid_to_rid[vid]

#             if len(self.rid_to_vids[rid]) == 0:
#                 del self.rid_to_vids[rid]
#                 if rid in self.emphasized:
#                     del self.emphasized[rid]
#             return self.nbViews(rid)
#         return -1

#     def nbViews(self, rid):
#         return len(self.rid_to_vids.get(rid, []))
            
#     def updateEdit(self, edit_vid, red, toed=None):
#         rid = self.vid_to_rid.get(edit_vid)
#         if rid is not None:
            
#         if toed is not None and toed >= 0 and toed < len(self.data):
#             if self.tabId != "hist":
#                 self.data[toed] = red

#                 for k,v in self.opened_edits.items():
#                     if v == toed and k != edit_key:
#                         mc = self.parent.accessViewX(k)
#                         if mc is not None:
#                             mc.setCurrent(red, self.tabId)

#             else:
#                 old_toed = toed
#                 new_toed = len(self.data)
#                 row_inserted = self.insertItem(red, -1)
#                 if edit_key is None: ## edit comes from the tab itself, not from a view
#                     self.setSelectedRow(row_inserted)
            
#                 for k,v in self.opened_edits.items():
#                     if v == old_toed:
#                         self.opened_edits[k] = new_toed 
#                         mc = self.parent.accessViewX(k)
#                         if mc is not None:
#                             mc.updateTitle()
#                             if k != edit_key:
#                                 mc.setCurrent(red, self.tabId)

#                 if old_toed in self.emphasized and edit_key in self.opened_edits:
#                     self.emphasized[self.opened_edits[edit_key]] = self.emphasized[old_toed]
#                     del self.emphasized[old_toed]

#                 self.parent.updateMenus()
#             self.ResetView()
#         ### TODO else insert (e.g. created from variable)

#     def getViewsCount(self, edit_key):
#         count = 0
#         if edit_key in self.opened_edits.keys():
#             toed = self.opened_edits[edit_key]
#         if toed is not None and toed >= 0 and toed < len(self.data):
#             for k,v in self.opened_edits.items():
#                 if v == toed: # and k != edit_key:
#                     count += 1
#         return count

#     def addAndViewTop(self, queries, viewT):
#         mapV = self.parent.getViewX(None, viewT)
#         red = mapV.setCurrent(queries)
#         self.registerView(mapV.getId(), len(self.data)-1, upMenu=False)
#         mapV.setSource(self.tabId)
#         self.parent.updateMenus()
#         mapV.updateTitle()

# # ######################################################################
# # ###########     MAP VIEWS
# # ######################################################################

#     def getNbActiveViewsForMenu(self, view_ids):
#         return len(view_ids)
#     def getActiveViewsForMenu(self, view_ids):
#         return sorted([(vid, view.getShortDesc()) for (vid, view) in view_ids.items() if not view.isIntab()], key=lambda x: x[1])

#     def getViewsItems(self, tab_type=None, geospatial=False, queries=None, excludeT=None):
#         return ViewFactory.getViewsInfo(tab_type, geospatial, queries, excludeT)
#     def getDefaultViewT(self, geo=False, type_tab="Reds"):
#         return ViewFactory.getDefaultViewT(geo=self.dw.isGeospatial(), type_tab=self.tabs[tabId]["type"])

# ######################################################################
# ######################################################################
# ######################################################################


# ################################################################################
# ################################### SIREN

# class ViewsManager:

#     def __init__(self, parent):
#         self.parent = parent
#         self.view_ids = {}

#         self.selectedViewX = -1
#         self.opened_edits = {}
#         self.emphasized = {}

#     def isGeospatial(self):
#         return self.parent.dw.isGeospatial()

#     def getViewsItems(self, tab_type=None, queries=None, excludeT=None):
#         return ViewFactory.getViewsInfo(tab_type, self.isGeospatial(), queries, excludeT)

#     def getDefaultViewT(self, type_tab=None):
#         return ViewFactory.getDefaultViewT(geo=self.isGeospatial(), type_tab=type_tab)

#     def accessViewX(self, mid):
#         if mid in self.view_ids:
#             return self.view_ids[mid]

#     def getViewX(self, vid=None, viewT=None):
#         if viewT is None:
#             viewT = self.getDefaultViewT()
            
#         if (viewT, vid) not in self.view_ids:
#             view = ViewFactory.getView(viewT, self, wx.NewId())
#             if view is None:
#                 return
#             self.selectedViewX = view.getId()
#             self.view_ids[self.selectedViewX] = view
#         else:
#             self.selectedViewX = (viewT, vid)
#         self.view_ids[self.selectedViewX].toTop()
#         return self.view_ids[self.selectedViewX]

#     def deleteView(self, vK, freeing=True):
#         if vK in self.view_ids:
#             self.parent.plant.getWP().layOff(self.parent.plant.getWP().findWid([("wtyp", "project"), ("vid", vK)]))
#             if not self.view_ids[vK].isIntab():
#                 self.view_ids[vK].mapFrame.Destroy()
#             else:
#                 pos = self.view_ids[vK].getGPos()
#                 panel = self.view_ids[vK].popSizer()
#                 panel.Destroy()
#                 if freeing:
#                     self.setVizcellFreeded(pos)
#             del self.view_ids[vK]

#     def deleteAllViews(self):
#         self.selectedViewX = -1
#         for vK in self.view_ids.keys():
#             self.view_ids[vK].OnQuit(None, upMenu=False)
#         self.view_ids = {}
#         self.parent.updateMenus()


# ################################### GRID
#     def viewData(self, viewT, pos=None, oid=None):
#         print "View data", viewT, pos, oid
#         if oid is not None:
#             if oid in self.opened_edits:
#                 pos = self.opened_edits[oid]
#         #### VIEW MAN
#         # if pos is None:
#         #     pos = self.getSelectedPos()
#         vid = None
#         for (k,v) in self.opened_edits.items():
#             if v == pos and viewT == k[0]:
#                 vid = k[1]
#                 break
            
#         mapV = self.getViewX(vid, viewT)
#         if vid is None and mapV is not None:
#             self.registerView(mapV.getId(), pos, upMenu=False)
#             #### VIEW MAN
#             mapV.setCurrent(self.getItemAtRow(self.getRowFromPosition(pos)), self.tabId)
#             mapV.updateTitle()
#             self.parent.updateMenus()
            
#     def registerView(self, key, pos, upMenu=True):
#         self.opened_edits[key] = pos
#         if upMenu:
#             self.parent.updateMenus()

#     def unregisterView(self, key, upMenu=True):
#         if key in self.opened_edits.keys():
#             pos = self.opened_edits[key]
#             del self.opened_edits[key]
#             ### if there are no other view referring to same red, clear emphasize lines
#             if pos not in self.opened_edits.values():
#                 if pos in self.emphasized:
#                     del self.emphasized[pos]
#             if upMenu:
#                 self.parent.updateMenus()

            
#     def updateEdit(self, edit_key, red, toed=None):
#         if edit_key in self.opened_edits.keys():
#             toed = self.opened_edits[edit_key]
#         if toed is not None and toed >= 0: ### VIEW MAN and toed < len(self.data):
#             if self.tabId != "hist":
#                 self.data[toed] = red

#                 for k,v in self.opened_edits.items():
#                     if v == toed and k != edit_key:
#                         mc = self.accessViewX(k)
#                         if mc is not None:
#                             mc.setCurrent(red, self.tabId)

#             else:
#                 old_toed = toed
#                 ### VIEW MAN 
#                 # new_toed = len(self.data)
#                 # row_inserted = self.insertItem(red, -1)
#                 # if edit_key is None: ## edit comes from the tab itself, not from a view
#                 #     self.setSelectedRow(row_inserted)
            
#                 for k,v in self.opened_edits.items():
#                     if v == old_toed:
#                         self.opened_edits[k] = new_toed 
#                         mc = self.accessViewX(k)
#                         if mc is not None:
#                             mc.updateTitle()
#                             if k != edit_key:
#                                 mc.setCurrent(red, self.tabId)

#                 if old_toed in self.emphasized and edit_key in self.opened_edits:
#                     self.emphasized[self.opened_edits[edit_key]] = self.emphasized[old_toed]
#                     del self.emphasized[old_toed]

#                 self.parent.updateMenus()
#             ### VIEW MAN 
#             # self.ResetView()
#         ### TODO else insert (e.g. created from variable)

#     def getViewsCount(self, edit_key):
#         count = 0
#         if edit_key in self.opened_edits.keys():
#             toed = self.opened_edits[edit_key]
#         if toed is not None and toed >= 0: ### VIEW MAN  and toed < len(self.data):
#             for k,v in self.opened_edits.items():
#                 if v == toed: # and k != edit_key:
#                     count += 1
#         return count

#     def addAndViewTop(self, queries, viewT):
#         mapV = self.getViewX(None, viewT)
#         red = mapV.setCurrent(queries)
#         ### VIEW MAN 
#         # self.registerView(mapV.getId(), len(self.data)-1, upMenu=False)
#         # mapV.setSource(self.tabId)
#         self.parent.updateMenus()
#         mapV.updateTitle()
