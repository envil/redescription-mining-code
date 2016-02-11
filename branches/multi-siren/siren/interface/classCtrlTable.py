import sys
import wx
import wx.lib.mixins.listctrl  as  listmix

from ..reremi.classQuery import SYM, Query, Literal
from ..reremi.classRedescription import Redescription

import pdb

class ListDrop(wx.PyDropTarget):
    """ Drop target for simple lists. """

    def __init__(self, setFn):
        """ Arguments:
         - setFn: Function to call on drop.
        """
        wx.PyDropTarget.__init__(self)

        self.setFn = setFn

        # specify the type of data we will accept
        self.data = wx.PyTextDataObject()
        self.SetDataObject(self.data)

    # Called when OnDrop returns True.  We need to get the data and
    # do something with it.
    def OnData(self, x, y, d):
        # copy the data from the drag source to our data object
        if self.GetData():
            self.setFn(x, y, self.data.GetText())

        # what is returned signals the source what to do
        # with the original data (move, copy, etc.)  In this
        # case we just return the suggested value given to us.
        return d


class ListCtrlBasis(wx.ListCtrl, listmix.ListCtrlAutoWidthMixin):
    type_lc = "-"

    def __init__(self, parent, ID=wx.ID_ANY, pos=wx.DefaultPosition,
                     size=wx.DefaultSize, style=0):
        wx.ListCtrl.__init__(self, parent, ID, pos, size, style)
        listmix.ListCtrlAutoWidthMixin.__init__(self)
        self.parent = parent
        self.data_src = None
        self.pid = None
        self.upOn = True

        dt = ListDrop(self._dd)
        self.SetDropTarget(dt)

        self.Bind(wx.EVT_LIST_ITEM_SELECTED, self._onSelect)
        #self.Bind(wx.EVT_LIST_KEY_DOWN, self.OnKeyDown)
        self.Bind(wx.EVT_KEY_DOWN, self.OnKeyDown)
        self.Bind(wx.EVT_LIST_COL_CLICK, self.OnColClick)

    def setDataSrc(self, data_src, pid=None):
        self.data_src = data_src
        self.pid = pid
    def getDataSrc(self):
        return self.data_src
    def hasDataSrc(self):
        return self.data_src is not None
    def getPid(self):
        return self.pid

    def turnUp(self, val):
        self.upOn = val
    def isUp(self):
        return self.upOn

    def getAssociated(self, which):
        if self.hasDataSrc():
            return self.getDataSrc().getAssociated(self.getPid(), which)
        return None
    
    def OnColClick(self, event):
        pass 

    def OnKeyDown(self, event):
        pass
        # print event.GetKeyCode(), event.GetModifiers()
        # if event.GetKeyCode() in [wx.WXK_LEFT, wx.WXK_RIGHT]:
        #     print "navigate"
        #     # self.listm.jumpToNextLC(self)

    def _onSelect(self, event):
        pass
    
    # def OnDeSelect(self, event):
    #     index = event.GetIndex()
    #     self.SetItemBackgroundColour(index, 'WHITE')

    def OnFocus(self, event):
        self.SetItemBackgroundColour(0, wx.SystemSettings_GetColour(wx.SYS_COLOUR_3DHIGHLIGHT))

    def _onInsert(self, event):
        # Sequencing on a drop event is:
        # wx.EVT_LIST_ITEM_SELECTED
        # wx.EVT_LIST_BEGIN_DRAG
        # wx.EVT_LEFT_UP
        # wx.EVT_LIST_ITEM_SELECTED (at the new index)
        # wx.EVT_LIST_INSERT_ITEM
        #--------------------------------
        # this call to onStripe catches any addition to the list; drag or not
        if self.hasDataSrc():
            self._onStripe()
            # self.getDataSrc().setIndices(self.getPid(), "drag", -1)
            event.Skip()

    def _onDelete(self, event):
        if self.hasDataSrc():
            self._onStripe()
            event.Skip()

    def getSelection(self):
        l = []
        idx = -1
        while True: # find all the selected items and put them in a list
            idx = self.GetNextItem(idx, wx.LIST_NEXT_ALL, wx.LIST_STATE_SELECTED)
            if idx == -1:
                break
            l.append(idx)
        return l

    def onExtDelete(self, event):
        """ Put together a data object for drag-and-drop _from_ this list. """
        # Create the data object: Just use plain text.
        print self.getSelection()

    def _startDrag(self, e):
        """ Put together a data object for drag-and-drop _from_ this list. """
        # Create the data object: Just use plain text.
        if self.hasDataSrc():
            txt = ",".join(map(str, self.getSelection()))
            data = wx.PyTextDataObject()
            data.SetText(txt)

            ### single item select
            # idx = e.GetIndex()
            # data.SetText("%s" % idx)

            # Create drop source and begin drag-and-drop.
            dropSource = wx.DropSource(self)
            dropSource.SetData(data)
            res = dropSource.DoDragDrop(flags=wx.Drag_DefaultMove)

    def _dd(self, x, y, text): ## drag release
        # Find insertion point.
        if self.hasDataSrc():
            trg_where = {"index": None, "after": False}
            index, flags = self.HitTest((x, y))
            if index == wx.NOT_FOUND: ### if not found move to end
                trg_where["index"] = -1
            else:
                trg_where["index"] = index
                # Get bounding rectangle for the item the user is dropping over.
                rect = self.GetItemRect(index)
                # If the user is dropping into the lower half of the rect, we want to insert _after_ this item.
                if y > (rect.y - rect.height/2.):
                    trg_where["after"] = True
            self.getDataSrc().manageDrag(self, trg_where, text)

    def _onStripe(self):
        if self.GetItemCount()>0:
            for x in range(self.GetItemCount()):
                if x % 2==0:
                    self.SetItemBackgroundColour(x,wx.SystemSettings_GetColour(wx.SYS_COLOUR_3DLIGHT))
                else:
                    self.SetItemBackgroundColour(x,wx.WHITE)

class ListCtrlContainers(ListCtrlBasis):
    type_lc = "containers" 

    def __init__(self, parent, ID=wx.ID_ANY, pos=wx.DefaultPosition,
                 size=wx.DefaultSize):
        ListCtrlBasis.__init__(self, parent, ID, pos, size,
                               style=wx.LC_REPORT | wx.LC_HRULES | wx.LC_NO_HEADER | wx.LC_SINGLE_SEL)
        self.InsertColumn(0, '')

    def setDataSrc(self, data_src, pid=None):
        ListCtrlBasis.setDataSrc(self, data_src, pid)
        self.SetImageList(self.getDataSrc().getContainersIL(), wx.IMAGE_LIST_SMALL)

    def upItem(self, i, llid):
        self.SetStringItem(i, 0, self.getDataSrc().getList(llid).getShortStr())
        self.SetItemImage(i, self.getDataSrc().getList(llid).getSrcTypId())

    def loadData(self, lid=None, cascade=True):
        self.DeleteAllItems()
        if self.getPid() is not None:
            for (i, llid) in enumerate(self.getDataSrc().getOrdLists()):
                self.InsertStringItem(i, "")
                self.upItem(i, llid)
                if llid == lid:
                    if not cascade:
                        self.turnUp(False)
                    self.Select(i)
                    if not cascade:
                        self.turnUp(True)

        if lid is None and cascade:
            ll = self.getAssociated("reds")
            ll.loadData(lid)

    def _onSelect(self, event):
        if self.isUp():
            self.getDataSrc().setLid(self.getPid(), lid=None, pos=event.GetIndex())

    def _onStripe(self):
        pass

class ListCtrlItems(ListCtrlBasis, listmix.CheckListCtrlMixin):
    type_lc = "items" 

    def __init__(self, parent, ID=wx.ID_ANY, pos=wx.DefaultPosition,
                 size=wx.DefaultSize):
        ListCtrlBasis.__init__(self, parent, ID, pos, size,
                               style=wx.LC_REPORT | wx.LC_HRULES) # | wx.LC_NO_HEADER)
        listmix.CheckListCtrlMixin.__init__(self)

        self.Bind(wx.EVT_LIST_BEGIN_DRAG, self._startDrag)        
        self.Bind(wx.EVT_LIST_INSERT_ITEM, self._onInsert)
        self.Bind(wx.EVT_LIST_DELETE_ITEM, self._onDelete)
        
        self.upck = True

    def setDataSrc(self, data_src, pid=None):
        self.data_src = data_src
        self.pid = pid
        self.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.data_src.OnViewData)
        self.Bind(wx.EVT_LIST_ITEM_RIGHT_CLICK, self.data_src.OnRightClick)

    def OnCheckItem(self, index, flag):
        #### set disabled on red
        if self.upck:
            self.getDataSrc().checkItem(self.getPid(), index, flag)
            self.setBckColor(index, flag)

    def upItem(self, i, rdt):
        for (cid, cv) in enumerate(rdt["cols"]):
            self.SetStringItem(i, cid, cv)
        if "checked" in rdt:
            self.upck = False
            self.CheckItem(i, rdt["checked"])
            self.setBckColor(i, rdt["checked"])
            self.upck = True

    def setBckColor(self, i, checked=False):
        if checked:
            self.SetItemTextColour(i, wx.SystemSettings_GetColour( wx.SYS_COLOUR_WINDOWTEXT ))
        else:
            self.SetItemTextColour(i, wx.SystemSettings_GetColour( wx.SYS_COLOUR_GRAYTEXT ))

    def updateColsTitles(self, lid):
        for cid, col in enumerate(self.getDataSrc().getColsInfo(lid)):
            tmp = self.GetColumn(cid)
            tmp.SetText(col["title"])
            self.SetColumn(cid, tmp)


    def loadData(self, lid=None):
        self.DeleteAllItems()
        if lid is None:
            return
        ### check nb cols match
        if self.getDataSrc().getNbCols() != self.GetColumnCount():
            self.DeleteAllColumns()
            for cid, col in enumerate(self.getDataSrc().getColsInfo(lid)):
                self.InsertColumn(cid, col["title"], format=col["format"], width=col["width"])
        else:
            self.updateColsTitles(lid)

        ll = self.getDataSrc().getList(lid)
        if ll is not None:
            # for red in ll.getReds():
            #     print red.status, red
            for i in range(len(ll)):
                self.InsertStringItem(i, "")
                rdt = ll.getRedDataAtPos(i)
                self.upItem(i, rdt)

    def OnColClick(self, event):
        colS = event.GetColumn()
        if colS == -1:
            pass ### TODO select all
        else:
            lid = self.getAssociated("lid")
            ll = self.getDataSrc().getList(lid)
            (oldC, newC) = ll.setSort(colS)
            if oldC is not None or newC is not None:
                self.updateColsTitles(lid)
            new_poss = ll.updateSort(self.getSelection())
            if new_poss is not None:
                self.loadData(lid)
                for pos in new_poss:
                    self.Select(pos)

    # def makeToolbar(self, handle):
    #     toolbar = self.frame.CreateToolBar()
    #     toolbar.AddLabelTool(wx.ID_OPEN, 'Open', wx.ArtProvider.GetBitmap(wx.ART_FILE_OPEN, wx.ART_TOOLBAR))
    #     toolbar.AddLabelTool(wx.ID_SAVE, 'Save', wx.ArtProvider.GetBitmap(wx.ART_FILE_SAVE, wx.ART_TOOLBAR))
    #     toolbar.AddLabelTool(wx.ID_SAVEAS, 'Save as', wx.ArtProvider.GetBitmap(wx.ART_FILE_SAVE_AS, wx.ART_TOOLBAR))
    #     #toolbar.InsertSeparator(3)
    #     toolbar.AddLabelTool(wx.ID_NEW, 'New folder', wx.ArtProvider.GetBitmap(wx.ART_NEW_DIR, wx.ART_TOOLBAR))
    #     toolbar.AddLabelTool(wx.ID_DELETE, 'Delete', wx.ArtProvider.GetBitmap(wx.ART_DELETE, wx.ART_TOOLBAR))
    #     toolbar.InsertSeparator(5)
    #     toolbar.AddLabelTool(wx.ID_CUT, 'Cut', wx.ArtProvider.GetBitmap(wx.ART_CUT, wx.ART_TOOLBAR))
    #     toolbar.AddLabelTool(wx.ID_COPY, 'Copy', wx.ArtProvider.GetBitmap(wx.ART_COPY, wx.ART_TOOLBAR))
    #     toolbar.AddLabelTool(wx.ID_PASTE, 'Paste', wx.ArtProvider.GetBitmap(wx.ART_PASTE, wx.ART_TOOLBAR))
    #     toolbar.AddLabelTool(wx.ID_FIND, 'Find', wx.ArtProvider.GetBitmap(wx.ART_FIND, wx.ART_TOOLBAR))
    #     toolbar.Realize()

    #     self.frame.Bind(wx.EVT_TOOL, handle.onOpen, id=wx.ID_OPEN)
    #     self.frame.Bind(wx.EVT_TOOL, handle.onSave, id=wx.ID_SAVE)
    #     self.frame.Bind(wx.EVT_TOOL, handle.onSaveAs, id=wx.ID_SAVEAS)
    #     self.frame.Bind(wx.EVT_TOOL, handle.onNewFolder, id=wx.ID_NEW)
    #     self.frame.Bind(wx.EVT_TOOL, handle.onTrash, id=wx.ID_DELETE)
    #     self.frame.Bind(wx.EVT_TOOL, handle.onCut, id=wx.ID_CUT)
    #     self.frame.Bind(wx.EVT_TOOL, handle.onCopy, id=wx.ID_COPY)
    #     self.frame.Bind(wx.EVT_TOOL, handle.onPaste, id=wx.ID_PASTE)
    #     self.frame.Bind(wx.EVT_TOOL, handle.onFind, id=wx.ID_FIND)


class ListManager:
    def __init__(self, parent, id, src=('manual', None), name=None, rids=[]):        
        self.id = id
        self.src = src
        self.parent = parent
        # self.rids = rids
        self.sortids = list(rids)
        self.sortP = (None, False)
        # self.sortP = (0, False)
        if name is None:
            self.name = "List#%d" % self.id
        else:
            self.name = name

    def getSrcTyp(self):
        return self.src[0]
    def getSrcTypId(self):
        return RedCtrl.list_types_map[self.src[0]]
    def getSrcInfo(self):
        return self.src[1]
    def setSrc(self, src_typ, src_info=None):
        self.src = (src_typ, src_info)

    def getSortInfo(self):
        direct = '  '
        if self.sortP[0] is not None:
            if self.sortP[1]:
                direct = SYM.SYM_ARRTOP
            else:
                direct = SYM.SYM_ARRBOT
        return (self.sortP[0], direct)

    def setSort(self, colS=None):
        old = self.sortP[0]
        if colS is not None:
            if self.sortP[0] == colS:
                self.sortP = (self.sortP[0], not self.sortP[1])
            else:
                self.sortP = (colS, False)
        else:
            self.sortP = (None, False)
        return (old, colS)

    def updateSort(self, poss=None):
        idxs = []
        if poss is not None:
            idxs = set([self.getRidAtPos(pos) for pos in poss])

        if self.sortP[0] is not None:
            details = {"aim": "sort"}
            details.update(self.parent.details)
            details_list = details.items()
            self.sortids.sort(key= lambda x: self.parent.getFieldV(x, self.parent.fields[self.sortP[0]], dict(details_list+[("rid", x)])), reverse=self.sortP[1])

            new_poss = []
            if len(idxs) > 0:
                new_poss = [pos for (pos, idx) in enumerate(self.sortids) if idx in idxs] 
            return new_poss
        return None
    
    def setRids(self, rids):
        self.sortids = list(rids)    
    def insertRids(self, rids, pos=-1):
        if pos == -1:
            pos = len(self.sortids)
        for p in rids[::-1]:
            self.sortids.insert(pos, p)
        self.setSort()
        
    def getRids(self):
        return self.sortids

    def getRedDataAtPos(self, pos):
        rid = self.getRidAtPos(pos)
        return self.parent.getRedData(rid, pos)

    def getPosForRid(self, idx):
        try:
            return self.sortids.index(idx)
        except IndexError:
            return None

    def getRidAtPos(self, pos):
        try:
            return self.sortids[pos]
        except IndexError:
            return None
    def getRidsAtPoss(self, poss=None):
        if poss is None:
            return list(self.sortids)
        else:
            return [self.getRidAtPos(p) for p in poss]
    def getVRidsAtPoss(self, poss=None):
        return [l for l in self.getRidsAtPoss(poss) if l is not None]

    def getShortStr(self):
        return "%s (%d)" % (self.name, len(self.sortids))
    def nbItems(self):
        return len(self.sortids)

    def __len__(self):
        return len(self.sortids)
    def __str__(self):
        return "%s (%d)" % (self.name, len(self.sortids))

    def deleteReds(self, poss=None):
        if poss is None:
            del_rids = list(self.sortids)
            del self.sortids
        else:
            del_rids = []
            poss = sorted(poss)
            while len(poss) > 0:
                del_rids.append(self.sortids.pop(poss.pop()))
        return del_rids[::-1]

        # ttd = numpy.ones(len(self.sortids), dtype=int)
        # ttd[[self.sortids[p] for p in poss]] = 0
        # csum = ttd.cumsum()-1
        # self.sortids = [csum[i] for i in self.sortids if ttd[i]==1]
        # for i in range(len(ttd)-1, -1, -1):
        #     if ttd[i] == 0:
        #         self.reds.pop(i)
        
class RedCtrl:

    list_types_names = ['file', 'run', 'manual', 'history']
    list_types_icons = [wx.ART_REPORT_VIEW, wx.ART_EXECUTABLE_FILE, wx.ART_LIST_VIEW, wx.ART_LIST_VIEW]
#    wx.ART_NORMAL_FILE
    list_types_map = dict([(v,k) for (k,v) in enumerate(list_types_names)])
    list_width = 150

    str_red = 'red'
    fields_def_nosplit = [('', str_red+'.getSortAble', None, 20, wx.LIST_FORMAT_LEFT),
                          ('id', str_red+'.getShortRid', None, 40, wx.LIST_FORMAT_LEFT),
                          ('query LHS', str_red+'.getQueryLU', None, 300, wx.LIST_FORMAT_LEFT),
                          ('query RHS', str_red+'.getQueryRU', None, 300, wx.LIST_FORMAT_LEFT),
                          ('J', str_red+'.getRoundAcc', None, 60, wx.LIST_FORMAT_RIGHT),
                          ('p-value', str_red+'.getRoundPVal', None, 60, wx.LIST_FORMAT_RIGHT),
                          ('|E'+SYM.SYM_GAMMA+'|', str_red+'.getLenI', None, 60, wx.LIST_FORMAT_RIGHT),
                          ('track', str_red+'.getTrack', None, 80, wx.LIST_FORMAT_LEFT)]

    fields_def_splits = [('', str_red+'.getSortAble', None, 20, wx.LIST_FORMAT_LEFT),
                         ('id', str_red+'.getShortRid', None, 40, wx.LIST_FORMAT_LEFT),
                         ('query LHS', str_red+'.getQueryLU', None, 300, wx.LIST_FORMAT_LEFT),
                         ('query RHS', str_red+'.getQueryRU', None, 300, wx.LIST_FORMAT_LEFT),
                         (SYM.SYM_RATIO+'J', str_red+'.getRoundAccRatio', {"rset_id_num": "test", "rset_id_den": "learn"}, 60, wx.LIST_FORMAT_RIGHT),
                         (SYM.SYM_LEARN+'J', str_red+'.getRoundAcc', {"rset_id": "learn"}, 60, wx.LIST_FORMAT_RIGHT),
                         (SYM.SYM_TEST+'J', str_red+'.getRoundAcc', {"rset_id": "test"}, 60, wx.LIST_FORMAT_RIGHT),
                         (SYM.SYM_LEARN+'pV', str_red+'.getRoundPVal', {"rset_id": "learn"}, 60, wx.LIST_FORMAT_RIGHT),
                         (SYM.SYM_TEST+'pV', str_red+'.getRoundPVal', {"rset_id": "test"}, 60, wx.LIST_FORMAT_RIGHT),
                         (SYM.SYM_LEARN+'|E'+SYM.SYM_GAMMA+'|', str_red+'.getLenI', {"rset_id": "learn"}, 60, wx.LIST_FORMAT_RIGHT),
                         (SYM.SYM_TEST+'|E'+SYM.SYM_GAMMA+'|', str_red+'.getLenI', {"rset_id": "test"}, 60, wx.LIST_FORMAT_RIGHT),
                         ('track', str_red+'.getTrack', None, 80, wx.LIST_FORMAT_LEFT)]

    fields_def = fields_def_nosplit
    #fields_def = fields_def_splits
    name_m = str_red+'.getQueriesU'
    check_m = str_red+'.getEnabled'

    def getNbCols(self):
        return len(self.fields)
    def getColsInfo(self, lid=None, cs=None):
        infos = [{"title": field[0], "format": field[-1], "width": field[-2]} for field in self.fields]
        if lid is not None:
            sort_info = self.lists[lid].getSortInfo()
            if sort_info[0] is not None:
                infos[sort_info[0]]["title"] += sort_info[1] 
        return infos
    def getRedForRid(self, rid):
        try:
            return self.reds[rid]
        except KeyError:
            return None
        
    def getRedData(self, rid, pos):
        details = {"aim": "list", "rid": rid, "pos": pos}
        details.update(self.details)
        dt = ["%s" % self.getFieldV(rid, field, details) for field in self.fields]
        ck = self.getFieldV(rid, ("", self.check_m), details)==1
        return {"cols": dt, "checked": ck}
        
    def getFieldV(self, rid, field, details):
        if rid is None:
            return ""
        red = self.reds[rid]
        methode = eval(field[1])
        if callable(methode):
            if len(field) > 2 and field[2] is not None:
                details.update(field[2])
                details.update(self.listm.details)
            try:
                return methode(details)
            except IndexError:
                methode(details)
        else:
            return methode

    def __init__(self, parent, tabId, frame, short=None):
        self.details = {}
        self.short = short
        self.sc = set() # show column (for collapsed/expanded columns)
        self.parent = parent
        self.tabId = tabId
        if self.parent.hasDataLoaded() and self.parent.dw.getData().hasLT():
            self.fields = self.fields_def_splits
        else:
            self.fields = self.fields_def_nosplit
        self.matching = [] ### for find function
        self.reds = {}
        
        self.nrid = 0
        self.nlid = 0
        self.lists = {}
        self.lists_ord = []
        self.panels = []
        self.buffer = {}
        self.il = None
        
        #### draw
        self.addSplitPanel(frame)

    def getFocusCtrl(self):
        return self.getSplitP().FindFocus()

    def getFocusPid(self):
        f = self.getFocusCtrl()
        if f is not None:
            if f.getPid() in self.panels:
                return f.getPid()
        return None

    def GetNumberRows(self):
        """Return the number of rows in the active items ctrl"""
        pid = self.GetFocusPid()
        if pid is not None:
            return self.panels[pid]["lid"]["reds"].nbItems()
        return 0

    def GetNumberCols(self):
        """Return the number of columns in the grid"""
        return len(self.fields)

    def nbItems(self):
        return self.GetNumberRows()

    def Hide(self):
        self.getSplitP().Hide()

    def Show(self):
        self.getSplitP().Show()

    def resetAllSorts(self):
        for lk, ll in self.lists.items():
            ll.setSort()

    def resetDetails(self, details={}, review=True):
        self.resetAllSorts()
        self.details = details
        if review:
            self.updateAllPanels()
            # self.resetSizes()

    def resetData(self, data, srids=None):
        self.clearLists()
        nlid = self.addList(src=('run', 'main'), reds=data)
        ## TODO handle srids (order of display)
        self.panels[0]["lid"] = nlid
        self.updateAllPanels()

    def addData(self, data, srids=None):
        self.addList(src=('run', 'main'), reds=data)
        ## TODO handle srids (order of display)
        self.updateAllPanels()
        
    def getLidAtPos(self, pos):
        try:
            return self.lists_ord[pos]
        except KeyError:
            return None
    def getLidsAtPoss(self, poss=None):
        if poss is None:
            return list(self.lists)
        else:
            return [self.getLidAtPos(p) for p in poss]
    def getVLidsAtPoss(self, poss=None):
        return [l for l in self.getLidsAtPoss(poss) if l is not None]

    def addList(self, src=('manual', None), name=None, reds=[]):
        rids = [self.nrid+i for i in range(len(reds))]
        nlid = self.nlid
        self.nlid += 1
        self.nrid += len(reds)

        self.reds.update(dict(zip(rids, reds)))
        self.lists[nlid] = ListManager(self, nlid, src, name, rids) 
        self.lists_ord.append(nlid)
        return nlid
    
    def deleteList(self, lid):
        if lid in self.lists:
            drids = self.lists[lid].deleteReds()
            self.deleteReds(drids)
            self.lists_ord.remove(lid)
            del self.lists[lid]
    def clearLists(self):
        self.lists = {}
        self.reds = {}
        self.lists_ord = []            
            
    def deleteReds(self, drids=None):
        print "close and co" ### DELETE REDS, CLOSE VIEWS, etc.
        if drids is None:
            drids = self.reds.keys()
        for drid in drids:
            self.deleteRed(drid)
    def deleteRed(self, drid):
        del self.reds[drid]        

    def onNewList(self):
        self.addList(src=('manual', None))
        self. updateAllPanels(cascade=False)
        
    def updateAllPanels(self, cascade=True):
        for p in self.panels:
            p["containers"].loadData(p["lid"], cascade)

    def onDeleteLists(self, sel):
        lids = self.getVLidsAtPoss(sel)
        self.deleteLists(lids)
    def deleteLists(self, lids):
        for lid in lids:
            self.lists_ord.remove(lid)
            self.deleteReds(self.lists[lid].getRids())
            del self.lists[lid]
        def_lid = None
        if len(self.lists_ord) > 0:
            def_lid = self.lists_ord[0]
        for p in self.panels:
            if p["lid"] == lid:
                p["lid"] = def_lid
            p["containers"].loadData(p["lid"]) ## triggers loadData for associated reds

    def onDeleteReds(self, pid, sel):
        lid = self.panels[pid]["lid"]
        drids = self.lists[lid].deleteReds(sel)
        self.deleteReds(drids)
        self.updateAllPanels()

    def onCutLists(self, sel):
        lids = self.getVLidsAtPoss(sel)
        self.cutLists(lids)
    def cutLists(self, lids):
        rids = []
        for lid in lids:
            rids.extend(self.lists[lid].deleteReds())
        self.cutReds(drids)
        self.updateAllPanels()
        
    def onCutReds(self, pid, sel=None):
        lid = self.panels[pid]["lid"]
        rids = self.lists[lid].deleteReds(sel)
        self.cutReds(rids)
        self.updateAllPanels()
    def cutReds(self, rids=None):
        if rids is None:
            rids = self.reds.keys()
        self.setBuffer(rids, 'cut')

    def onCopyLists(self, sel):
        lids = self.getVLidsAtPoss(sel)
        self.copyLists(lids)
    def copyLists(self, lids):
        rids = []
        for lid in lids:
            rids.extend(self.lists[lid].getRids())
        self.copyReds(rids)
        
    def onCopyReds(self, pid, sel=None):
        lid = self.panels[pid]["lid"]
        rids = self.lists[lid].getVRidsAtPoss(sel)
        self.copyReds(rids)
    def copyReds(self, rids=None):
        if rids is None:
            rids = self.reds.keys()
        self.setBuffer(rids, 'copy')

    def onPasteAny(self, ctrl, sel):
        lid = self.panels[ctrl.getPid()]["lid"]
        if ctrl.type_lc == "containers":
            pos = -1
        else:
            pos = sel
        self.pasteReds(lid, pos)
    def pasteReds(self, lid, pos):
        if "action" in self.buffer and lid in self.lists:
            rids = None
            if self.buffer["action"] == 'copy':
                rcop = [self.reds[rid].copy() for rid in self.buffer["rids"]]
                rids = [self.nrid+i for i in range(len(rcop))]
                self.nrid += len(rcop)
                self.reds.update(dict(zip(rids, rcop)))
            elif self.buffer["action"] == 'cut':
                rids = self.buffer["rids"]
            if rids is not None:
                self.lists[lid].insertRids(rids, pos)
                self.updateAllPanels()
                self.buffer = {}
            else:
                self.clearBuffer()

    def setBuffer(self, rids, action):
        self.clearBuffer()
        self.buffer["rids"] = rids
        self.buffer["action"] = action
        print self.buffer

    def clearBuffer(self):
        if "action" in self.buffer:
            if self.buffer["action"] == "cut":
                self.deleteReds(self.buffer["rids"])
            self.buffer = {}
        
    def addSplitPanel(self, frame, lid=None):
        list1, list2 = self.drawSplitPanel(frame)

        if lid is None and len(self.lists) > 0:
            lid = self.lists_ord[0]

        pid = len(self.panels)
        self.panels.append({"containers": list1, "reds": list2, "lid": lid, "pid": pid}) 
        list1.setDataSrc(self, pid)
        list2.setDataSrc(self, pid)
        list1.loadData(lid)

    def getSplitP(self):
        return self.splitP

    def setLid(self, pid=0, lid=None, pos=None):
        if lid is not None:
            self.panels[pid]["lid"] = lid
            self.panels[pid]["containers"].Focus(self.getListPosForId(lid))
        elif pos is not None:
            lid = self.getListIdAtPos(pos)
            self.panels[pid]["lid"] = lid
            self.panels[pid]["reds"].loadData(lid)

    def getAssociated(self, pid, which):
        try:
            return self.panels[pid][which]
        except IndexError:
            return None

    def getListPosForId(self, idx):
        try:
            return self.lists_ord.index(idx)
        except IndexError:
            return None
    def getListIdAtPos(self, pos):
        try:
            return self.lists_ord[pos]
        except IndexError:
            return None
    def getList(self, idx):
        try:
            return self.lists[idx]
        except IndexError:
            return None
    def getListAtPos(self, pos):
        try:
            return self.lists[self.lists_ord[pos]]
        except IndexError:
            return None

    def getOrdLists(self):
        return self.lists_ord

    # def jumpToNextLC(self, lc):
    #     if lc.type_lc == "items":
    #         fc = self.lcs["containers"]
    #     else:
    #         fc = self.lcs["items"]
    #     fc.SetFocus()
    #     if fc.GetFirstSelected() == -1:
    #         fc.Select(0)

    def getContainersIL(self):
        if self.il is None:
            self.il = wx.ImageList(32, 32)
            for (i, icon) in enumerate(RedCtrl.list_types_icons): 
                self.il.Add(wx.ArtProvider.GetBitmap(icon, wx.ART_FRAME_ICON))
        return self.il

    ##### drawing
    def drawSplitPanel(self, frame):

        subsplitter = wx.SplitterWindow(frame, -1, style=wx.SP_LIVE_UPDATE) #|wx.SP_NOBORDER)
        panelL = wx.Panel(subsplitter, -1)
        panelR = wx.Panel(subsplitter, -1)
        
        list1 = ListCtrlContainers(panelL, -1)
        list2 = ListCtrlItems(panelR, -1)
        
        vbox1 = wx.BoxSizer(wx.HORIZONTAL)
        vbox1.Add(list1, 1, wx.EXPAND)
        panelL.SetSizer(vbox1)

        vbox1 = wx.BoxSizer(wx.HORIZONTAL)
        vbox1.Add(list2, 1, wx.EXPAND)
        panelR.SetSizer(vbox1)
        subsplitter.SplitVertically(panelL, panelR, self.list_width)
        subsplitter.SetSashGravity(0.)
        subsplitter.SetMinimumPaneSize(1)
        

        self.splitP = subsplitter
        return list1, list2

    def OnViewData(self, event):
        print "View Data"
    #     self.viewData(self.parent.getDefaultViewT(self.tabId))
        
    # def viewData(self, viewT, pos=None, oid=None):
    #     if oid is not None:
    #         if oid in self.opened_edits:
    #             pos = self.opened_edits[oid]
    #     if pos is None:
    #         pos = self.getSelectedPos()
    #     vid = None
    #     for (k,v) in self.opened_edits.items():
    #         if v == pos and viewT == k[0]:
    #             vid = k[1]
    #             break
            
    #     mapV = self.parent.getViewX(vid, viewT)
    #     if vid is None and mapV is not None:
    #         self.registerView(mapV.getId(), pos, upMenu=False)
    #         mapV.setCurrent(self.getItemAtRow(self.getRowFromPosition(pos)), self.tabId)
    #         mapV.updateTitle()
    #         self.parent.updateMenus()

    def OnRightClick(self, event):
        print "Right Click"
        
    def onOpen(self, event):
        self.getSplitP().FindFocus()
        pass
    def onSave(self, event):
        pass
    def onSaveAs(self, event):
        pass
    def onNewFolder(self, event):
        self.onNewList()
    def onTrash(self, event):
        ctrl = self.getSplitP().FindFocus()
        sel = ctrl.getSelection()
        if len(sel) > 0:
            if ctrl.type_lc == "containers":
                lids = [self.lists_ord[p] for p in sel]
                self.onDeleteLists(sel)
            elif ctrl.type_lc == "items":
                self.onDeleteReds(ctrl.getPid(), sel)

    def onCut(self, event):
        ctrl = self.reader.FindFocus()
        sel = ctrl.getSelection()
        if len(sel) > 0:
            if ctrl.type_lc == "containers":
                self.onCutLists(sel)
            elif ctrl.type_lc == "items":
                self.onCutReds(ctrl.getPid(), sel)
    def onCopy(self, event):
        ctrl = self.reader.FindFocus()
        sel = ctrl.getSelection()
        if len(sel) > 0:
            if ctrl.type_lc == "containers":
                self.onCopyLists(sel)
            elif ctrl.type_lc == "items":
                self.onCopyReds(ctrl.getPid(), sel)
    def onPaste(self, event):
        ctrl = self.reader.FindFocus()
        sel = ctrl.GetFocusedItem()
        self.onPasteAny(ctrl, sel)

    def onFind(self, event):
        pass

    def checkItem(self, pid, index, check):
        lid = self.getAssociated(pid, "lid")
        if lid is not None:
            rid = self.getList(lid).getRidAtPos(index)
            if rid is not None:
                ck = self.getFieldV(rid, ("", self.check_m), {})
                if (ck == 1 and not check) or ( ck == 0 and check):
                    self.getRedForRid(rid).flipEnabled()
    
    def manageDrag(self, ctrl, trg_where, text):
        lid = self.panels[ctrl.getPid()]["lid"]
        sel = map(int, text.split(','))
        pos = None
        if ctrl.type_lc == "containers":
            if trg_where['index'] != -1:
                nlid = self.getLidAtPos(trg_where['index'])
                if nlid != lid:
                    pos = -1
        else:
            nlid = lid
            pos = trg_where['index']
            if trg_where['after'] and pos != -1:
                pos += 1
        if pos is not None:
            rids = self.lists[lid].deleteReds(sel)
            self.lists[nlid].insertRids(rids, pos)
        self.updateAllPanels()


