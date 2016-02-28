import sys
import wx
import wx.lib.mixins.listctrl  as  listmix
from ..reremi.classQuery import SYM
from ..reremi.classRedescription import Redescription
from ..reremi.classBatch import Batch

import pdb

LIST_TYPES_NAMES = ['file', 'run', 'manual', 'history']
LIST_TYPES_ICONS = [wx.ART_REPORT_VIEW, wx.ART_EXECUTABLE_FILE, wx.ART_LIST_VIEW, wx.ART_LIST_VIEW]

def makeContainersIL(icons):
    il = wx.ImageList(32, 32)
    for (i, icon) in enumerate(icons): 
        il.Add(wx.ArtProvider.GetBitmap(icon, wx.ART_FRAME_ICON))
    return il

###### DRAG AND DROP UTILITY
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
        self.cm = None
        self.pid = None
        self.upOn = True
        self.InsertColumn(0, '')
        dt = ListDrop(self._dd)
        self.SetDropTarget(dt)
        self.Bind(wx.EVT_LIST_ITEM_RIGHT_CLICK, self.OnRightClick)

    def OnRightClick(self, event):
        if self.hasCManager():
            self.getViewHdl().markFocus(self)
            self.getCManager().makePopupMenu()

    def getTypeL(self):
        return self.type_lc
    def isItemsL(self):
        return False
    def isContainersL(self):
        return False

    def setCManager(self, cm, pid=None):
        self.cm = cm
        self.pid = pid
    def getCManager(self):
        return self.cm
    def getDataHdl(self):
        if self.hasCManager():
            return self.cm.getDataHdl()
    def getViewHdl(self):
        if self.hasCManager():
            return self.cm.getViewHdl()

    def hasCManager(self):
        return self.cm is not None
    def getPid(self):
        return self.pid

    def turnUp(self, val):
        self.upOn = val
    def isUp(self):
        return self.upOn

    def getAssociated(self, which):
        if self.hasCManager():
            return self.getCManager().getAssociated(self.getPid(), which)
        return None

    # def OnKeyDown(self, event):
    #     pass
        # print event.GetKeyCode(), event.GetModifiers()
        # if event.GetKeyCode() in [wx.WXK_LEFT, wx.WXK_RIGHT]:
        #     print "navigate"
        #     # self.listm.jumpToNextLC(self)
    
    # def OnDeSelect(self, event):
    #     index = event.GetIndex()
    #     self.SetItemBackgroundColour(index, 'WHITE')

    # def OnFocus(self, event):
    #     self.SetItemBackgroundColour(0, wx.SystemSettings_GetColour(wx.SYS_COLOUR_3DHIGHLIGHT))

    def _onInsert(self, event):
        # Sequencing on a drop event is:
        # wx.EVT_LIST_ITEM_SELECTED
        # wx.EVT_LIST_BEGIN_DRAG
        # wx.EVT_LEFT_UP
        # wx.EVT_LIST_ITEM_SELECTED (at the new index)
        # wx.EVT_LIST_INSERT_ITEM
        #--------------------------------
        # this call to onStripe catches any addition to the list; drag or not
        if self.hasCManager():
            self._onStripe()
            # self.getCManager().setIndices(self.getPid(), "drag", -1)
            event.Skip()

    def _onDelete(self, event):
        if self.hasCManager():
            self._onStripe()
            event.Skip()

    def getFirstSelection(self):
        return self.GetFirstSelected()
    def getSelection(self):
        l = []
        idx = -1
        while True: # find all the selected items and put them in a list
            idx = self.GetNextItem(idx, wx.LIST_NEXT_ALL, wx.LIST_STATE_SELECTED)
            if idx == -1:
                break
            l.append(idx)
        return l
    def getNbSelected(self):
        return self.GetSelectedItemCount()
    def setFocusRow(self, row):
        self.Focus(row)
    def setFoundRow(self, row):
        self.Focus(row)
        # #self.SetItemBackgroundColour(0, wx.SystemSettings_GetColour(wx.SYS_COLOUR_WINDOWTEXT))
        # if self.IsSelected(row):
        #     self.SetItemTextColour(row, wx.Colour(0,222,222))
        # else:
        self.SetItemTextColour(row, wx.Colour(139,0,0))
    def setUnfoundRow(self, row):
        self.SetItemTextColour(row, wx.SystemSettings_GetColour(wx.SYS_COLOUR_WINDOWTEXT))


    def clearSelection(self):
        sels = self.getSelection()
        for sel in sels:
            self.Select(sel, on=0)
        return sels
    def setSelection(self, sels):
        self.clearSelection()
        for sel in sels:
            self.Select(sel, on=1)


    def onExtDelete(self, event):
        """ Put together a data object for drag-and-drop _from_ this list. """
        # Create the data object: Just use plain text.
        print self.getSelection()

    def _startDrag(self, e):
        """ Put together a data object for drag-and-drop _from_ this list. """
        # Create the data object: Just use plain text.
        if self.hasCManager():
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
        if self.hasCManager():
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
            self.getCManager().manageDrag(self, trg_where, text)

    def _onStripe(self):
        if self.GetItemCount()>0:
            for x in range(self.GetItemCount()):
                if x % 2==0:
                    self.SetItemBackgroundColour(x,wx.SystemSettings_GetColour(wx.SYS_COLOUR_3DLIGHT))
                else:
                    self.SetItemBackgroundColour(x,wx.WHITE)

    def GetNumberRows(self):
        return self.GetItemCount()
    def GetNumberCols(self):
        return self.GetColumnCount()


class ListCtrlContainers(ListCtrlBasis):
    type_lc = "containers" 
    list_width = 150
    
    def __init__(self, parent, ID=wx.ID_ANY, pos=wx.DefaultPosition,
                 size=wx.DefaultSize):
        ListCtrlBasis.__init__(self, parent, ID, pos, size,
                               style=wx.LC_REPORT | wx.LC_HRULES | wx.LC_NO_HEADER | wx.LC_SINGLE_SEL)
        self.InsertColumn(0, '')
        self.Bind(wx.EVT_LIST_ITEM_SELECTED, self._onSelect)
        self.AssignImageList(makeContainersIL(LIST_TYPES_ICONS), wx.IMAGE_LIST_SMALL)
        # self.Bind(wx.EVT_KEY_DOWN, self.OnKeyDown)
        
    def isContainersL(self):
        return True

    def setCManager(self, cm, pid=None):
        ListCtrlBasis.setCManager(self, cm, pid)

    def upItem(self, i, llid):
        self.SetStringItem(i, 0, self.getDataHdl().getList(llid).getShortStr())
        self.SetItemImage(i, self.getDataHdl().getList(llid).getSrcTypId())

    def loadData(self, lid=None, cascade=True):
        if self.GetItemCount() > 0:
            self.DeleteAllItems()
        if self.getPid() is not None:
            for (i, llid) in enumerate(self.getDataHdl().getOrdLists()):
                self.InsertStringItem(i, "")
                self.upItem(i, llid)
                if llid == lid:
                    if not cascade:
                        self.turnUp(False)
                    self.Select(i)
                    if not cascade:
                        self.turnUp(True)

        # if lid is None and cascade:
        #     ll = self.getAssociated("items")
        #     ll.loadData(lid)

    def _onSelect(self, event):
        if self.isUp():
            self.getViewHdl().setLid(self.getPid(), lid=None, pos=event.GetIndex())

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
        self.Bind(wx.EVT_LIST_BEGIN_DRAG, self._startDrag)        
        self.Bind(wx.EVT_LIST_INSERT_ITEM, self._onInsert)
        self.Bind(wx.EVT_LIST_DELETE_ITEM, self._onDelete)
        self.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.OnViewData)
        self.Bind(wx.EVT_LIST_COL_CLICK, self.OnColClick)
        self.upck = True

    def isItemsL(self):
        return True

    def getNbCols(self):
        return self.getDataHdl().getNbFields()
    def getColsInfo(self, lid=None, cs=None):
        return self.getDataHdl().getColsInfo(lid, cs)
    def getItemForIid(self, iid):
        try:
            return self.getDataHdl().getItemForIid(iid)
        except KeyError:
            return None
    def getItemForPos(self, pos):
        try:
            return self.getDataHdl().getItemForPos(pos) ### implement
        except KeyError:
            return None
    def getItemData(self, iid, pos):
        return self.getDataHdl().getItemData(iid, pos)

    def setCManager(self, cm, pid=None):
        self.cm = cm
        self.pid = pid

    def OnCheckItem(self, index, flag):
        #### set disabled on item
        if self.upck:
            lid = self.getAssociated("lid")
            self.getDataHdl().checkItem(lid, index, flag)
            self.setBckColor(index, flag)

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
        for cid, col in enumerate(self.getColsInfo(lid)):
            tmp = self.GetColumn(cid)
            tmp.SetText(col["title"])
            self.SetColumn(cid, tmp)

    def loadData(self, lid=None):
        if self.GetItemCount() > 0:
            self.DeleteAllItems()
        if lid is None:
            return
        ### check nb cols match
        if self.getNbCols() != self.GetColumnCount():
            self.DeleteAllColumns()
            for cid, col in enumerate(self.getDataHdl().getColsInfo(lid)):
                self.InsertColumn(cid, col["title"], format=col["format"], width=col["width"])
        else:
            self.updateColsTitles(lid)

        ll = self.getDataHdl().getList(lid)
        if ll is not None:
            # for item in ll.getItems():
            #     print item.status, item
            for i in range(len(ll)):
                self.InsertStringItem(i, "")
                self.loadItem(ll, i)

    def loadItem(self, ll, i):
        pap = self.IsSelected(i)
        rdt = ll.getItemDataAtPos(i)
        self.upItem(i, rdt)
        self.Select(i, pap)

    def OnColClick(self, event):
        colS = event.GetColumn()
        if colS == -1:
            event.Skip()
        else:
            lid = self.getAssociated("lid")
            ll = self.getDataHdl().getList(lid)
            (oldC, newC) = ll.setSort(colS)
            if oldC is not None or newC is not None:
                self.updateColsTitles(lid)
            new_poss = ll.updateSort(self.getSelection())
            if new_poss is not None:
                self.loadData(lid)
                for pos in new_poss:
                    self.Select(pos)

class SplitBrowser:

    def __init__(self, parent, pid, frame):
        self.parent = parent
        self.pid = pid
        self.active_lid = None
        self.cm = None
        self.last_foc = None

        self.sw = wx.SplitterWindow(frame, -1, style=wx.SP_LIVE_UPDATE) #|wx.SP_NOBORDER)
        panelL = wx.Panel(self.sw, -1)
        panelR = wx.Panel(self.sw, -1)
        
        self.lcc = ListCtrlContainers(panelL, -1)
        self.lci = ListCtrlItems(panelR, -1)

        vbox1 = wx.BoxSizer(wx.HORIZONTAL)
        vbox1.Add(self.lcc, 1, wx.EXPAND)
        panelL.SetSizer(vbox1)
        vbox1 = wx.BoxSizer(wx.HORIZONTAL)
        vbox1.Add(self.lci, 1, wx.EXPAND)
        panelR.SetSizer(vbox1)
        
        self.sw.SplitVertically(panelL, panelR, self.lcc.list_width)
        self.sw.SetSashGravity(0.)
        self.sw.SetMinimumPaneSize(1)

        ### WITHOUT SPLITTER
        # panel = wx.Panel(frame, wx.NewId())

        # list1 = ListCtrlContainers(panel, -1)
        # list2 = ListCtrlItems(panel, -1)
        
        # vbox1 = wx.BoxSizer(wx.HORIZONTAL)
        # vbox1.Add(list1, 1, wx.EXPAND)
        # vbox1.Add(list2, 1, wx.EXPAND)
        # panel.SetSizer(vbox1)
        # self.sw = panel

    def getSW(self):
        return self.sw
    def getCM(self):
        return self.cm
    def getDataHdl(self):
        if self.cm is not None:
            return self.cm.getDataHdl()
        return None
    def getLid(self):
        return self.active_lid
    def getLCC(self):
        return self.lcc
    def getLCI(self):
        return self.lci
    def getPid(self):
        return self.pid

    def getWhich(self, which):
        if which == "items":
            return self.lci
        if which == "containers":
            return self.lcc
        if which == "pid":
            return self.pid
        if which == "lid":
            return self.active_lid
    def getFocused(self):
        ff = self.sw.FindFocus()
        if ff is not None:
            return ff
        return self.last_foc
    def getFocusedL(self):
        ret = None
        ff = self.sw.FindFocus()
        if ff is not None and (ff == self.lci or ff == self.lcc):
            ret = ff
        if (self.last_foc == self.lci or self.last_foc == self.lcc):
            ret = self.last_foc
        return ret

    def markFocus(self, foc=None):
        if foc is not None:
            self.last_foc = foc
        else:
            self.last_foc = self.sw.FindFocus()

    def GetNumberRowsItems(self):
        return self.lci.GetNumberRows()
    def GetNumberRowsContainers(self):
        return self.lcc.GetNumberRows()
    def GetNumberColsItems(self):
        return self.lci.GetNumberCols()
    def GetNumberColsContainers(self):
        return self.lcc.GetNumberCols()
    def GetNumberRowsFocused(self):
        ll = self.getFocusedL()
        if ll is not None:
            return ll.GetNumberRows()
        return 0
    def GetNumberColsFocused(self):
        ll = self.getFocusedL()
        if ll is not None:
            return ll.GetNumberCols()
        return 0
    def GetNumberRows(self):
        return self.GetNumberRowsFocused()
    def GetNumberCols(self):
        return self.GetNumberColsFocused()
    def nbItems(self):
        return self.lci.GetNumberRows()
    def nbLists(self):
        return self.lcc.GetNumberRows()

    def nbSelectedItems(self):
        return self.lci.getNbSelected()
    def nbSelectedLists(self):
        return self.lcc.getNbSelected()
    def nbSelectedFocused(self):
        ll = self.getFocusedL()
        if ll is not None:
            return ll.getNbSelected()
        return 0
    def nbSelected(self):
        return self.nbSelectedFocused()

    def Hide(self):
        self.getSW().Hide()

    def Show(self):
        self.getSW().Show()

    def resetCM(self, cm=None):
        self.cm = cm
        if cm is not None:
            self.lcc.setCManager(cm, self.pid)
            self.lci.setCManager(cm, self.pid)
            if len(self.getDataHdl().getOrdLists()) > 0:
                self.active_lid = self.getDataHdl().getOrdLists()[0]
                self.lcc.loadData(self.active_lid)

    def refresh(self, cascade=True):
        self.lcc.loadData(self.active_lid, cascade)

    def updateLid(self, lid):
        if lid != self.active_lid: # check validity lid 
            self.active_lid = lid
            self.refresh()

    def setLid(self, pid=0, lid=None, pos=None):
        if lid is not None:
            self.active_lid = lid
            self.lcc.setFocusRow(self.getDataHdl().getListPosForId(lid))
        elif pos is not None:
            lid = self.getDataHdl().getListIdAtPos(pos)
            self.active_lid = lid
            self.lci.loadData(lid)

    def setSelectedItem(self, iid):
        pos = self.getDataHdl().getList(self.getLid()).getPosForIid(iid)
        self.lci.setFocusRow(pos)


        
class RefsList:

    list_types_map = dict([(v,k) for (k,v) in enumerate(LIST_TYPES_NAMES)])
    
    def __init__(self, parent, id, src=('manual', None), name=None, iids=[]):        
        self.id = id
        self.src = src
        self.parent = parent
        self.sortids = list(iids)
        self.sortP = (None, False)
        if name is None:
            self.name = "List#%d" % self.id
        else:
            self.name = name

    def getSrcTyp(self):
        return self.src[0]
    def getSrcTypId(self):
        return RefsList.list_types_map[self.src[0]]
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
            idxs = set([self.getIidAtPos(pos) for pos in poss])

        if self.sortP[0] is not None:
            tmp = [(x, self.parent.getItemFieldV(x, self.parent.fields[self.sortP[0]], {"aim": "sort", "id": x})) for x in self.sortids]
            self.sortids.sort(key= lambda x:
                              self.parent.getItemFieldV(x, self.parent.fields[self.sortP[0]], {"aim": "sort", "id": x}),
                              reverse=self.sortP[1])
            new_poss = []
            if len(idxs) > 0:
                new_poss = [pos for (pos, idx) in enumerate(self.sortids) if idx in idxs] 
            return new_poss
        return None
    
    def setIids(self, iids):
        self.sortids = list(iids)    
    def insertIids(self, iids, pos=-1):
        if pos == -1:
            pos = len(self.sortids)
        for p in iids[::-1]:
            self.sortids.insert(pos, p)
        self.setSort()
        
    def getIids(self):
        return self.sortids

    def getItemDataAtPos(self, pos):
        rid = self.getIidAtPos(pos)
        return self.parent.getItemData(rid, pos)

    def getPosForIid(self, idx):
        try:
            return self.sortids.index(idx)
        except IndexError:
            return None

    def getIidAtPos(self, pos):
        try:
            return self.sortids[pos]
        except IndexError:
            return None
    def getIidsAtPoss(self, poss=None):
        if poss is None:
            return list(self.sortids)
        else:
            return [self.getIidAtPos(p) for p in poss]
    def getIidsAfterPos(self, pos=None):
        if pos is None:
            return list(self.sortids)
        else:
            return list(self.sortids[pos:])
    def getVIidsAtPoss(self, poss=None):
        return [l for l in self.getIidsAtPoss(poss) if l is not None]

    def getShortStr(self):
        return "%s (%d)" % (self.name, len(self.sortids))
    def nbItems(self):
        return len(self.sortids)

    def __len__(self):
        return len(self.sortids)
    def __str__(self):
        return "%s (%d)" % (self.name, len(self.sortids))

    def deleteItems(self, poss=None):
        if poss is None:
            del_iids = list(self.sortids)
            del self.sortids
        else:
            del_iids = []
            poss = sorted(poss)
            while len(poss) > 0:
                del_iids.append(self.sortids.pop(poss.pop()))
        return del_iids[::-1]

        # ttd = numpy.ones(len(self.sortids), dtype=int)
        # ttd[[self.sortids[p] for p in poss]] = 0
        # csum = ttd.cumsum()-1
        # self.sortids = [csum[i] for i in self.sortids if ttd[i]==1]
        # for i in range(len(ttd)-1, -1, -1):
        #     if ttd[i] == 0:
        #         self.items.pop(i)


class DataSet:

    str_item = 'item'
    fields_def = []
    name_m = None
    check_m = None

    def __init__(self):
        self.details = {}
        self.items = Batch()
        self.nlid = 0
        self.lists = {}
        self.lists_ord = []
        self.buffer = {}

    #### ACCESSING LISTS
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


    #### ACCESSING ITEMS
    def getCheckF(self):
        return ('', self.check_m)
    def getNameF(self):
        return ('name', self.name_m)
    def getDataF(self, i):
        if i < len(self.fields):
            return self.fields[i]
        return None

    def getFields(self):
        return self.fields
    def getNbFields(self):
        return len(self.fields)
    def getColsInfo(self, lid=None, cs=None):
        infos = [{"title": field[0], "format": field[-1], "width": field[-2]} for field in self.getFields()]
        if lid is not None:
            sort_info = self.lists[lid].getSortInfo()
            if sort_info[0] is not None:
                infos[sort_info[0]]["title"] += sort_info[1] 
        return infos
    def getItemForIid(self, iid):
        return self.items[iid]
    def getItemData(self, iid, pos):
        details = {"aim": "list", "id": iid, "pos": pos} 
        dt = ["%s" % self.getItemFieldV(iid, field, details) for field in self.getFields()]
        ck = self.getItemFieldV(iid, self.getCheckF(), details)==1
        return {"cols": dt, "checked": ck}
    
    def getItemFieldV(self, iid, field, details):
        if iid is None or field is None:
            return ""
        item = self.items[iid]
        methode = eval(field[1])
        if callable(methode):
            if len(field) > 2 and field[2] is not None:
                details.update(field[2])
            details.update(self.details)
            try:
                return methode(details)
            except IndexError:
                methode(details)
        else:
            return methode

    #### MANIPULATING CONTENT
    def addList(self, items=[], src=None, sord=None):
        if src is None:
            src = ('manual', None)
        nlid = self.nlid
        self.nlid += 1

        iids = self.items.extend(items)
        ## TODO handle sord (order of display)
        self.lists[nlid] = RefsList(self, nlid, src, "", iids) 
        self.lists_ord.append(nlid)
        return nlid

    def resetLists(self, items, src=None, sord=None):
        self.clearLists()
        ## TODO handle sord (order of display)
        nlid = self.addList(items, src, sord)
        return nlid

    def resetDetails(self, details={}):
        self.resetAllSorts()
        self.details = details

    def resetAllSorts(self):
        for lk, ll in self.lists.items():
            ll.setSort()

    def getListsDict(self):
        return self.lists
    def getItemsDict(self):
        return self.items

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

    def substituteItem(self, item, iid):
        if iid in self.items:
            self.items[iid] = item

    ####### DATA ACTION
    def deleteLists(self, lids=[], sel=None):
        if len(lids) == 0 and sel is not None:
            lids = self.getVLidsAtPoss(sel)
        for lid in lids:
            self.lists_ord.remove(lid)
            self.deleteItems(self.lists[lid].getIids())
            del self.lists[lid]
        def_lid = None
        if len(self.lists_ord) > 0:
            def_lid = self.lists_ord[0]
        return def_lid
    def deleteList(self, lid):
        if lid in self.lists:
            diids = self.lists[lid].deleteItems()
            self.deleteItems(diids)
            self.lists_ord.remove(lid)
            del self.lists[lid]
    def clearLists(self):
        self.lists = {}
        self.items.reset()
        self.lists_ord = []

    def deleteItemsLid(self, lid, sel=None):
        diids = self.lists[lid].deleteItems(sel)
        self.deleteItems(diids)
    def deleteItems(self, diids=None):
        if diids is None:
            diids = self.items.getIds()
        for drid in diids:
            self.deleteItem(drid)
    def deleteItem(self, drid):
        del self.items[drid]        

    def cutLists(self, lids=[], sel=None):
        if len(lids) == 0 and sel is not None:
            lids = self.getVLidsAtPoss(sel)
        iids = []
        for lid in lids:
            iids.extend(self.lists[lid].deleteItems())
        self.setBuffer(iids, 'cut')
        return iids
    def cutItemsLid(self, lid, sel=None):
        iids = self.lists[lid].deleteItems(sel)
        self.setBuffer(iids, 'cut')
        return iids
    
    def copyLists(self, lids=[], sel=None):
        if len(lids) == 0 and sel is not None:
            lids = self.getVLidsAtPoss(sel)
        iids = []
        for lid in lids:
            iids.extend(self.lists[lid].getIids())
        self.setBuffer(iids, 'copy')
        return iids
    def copyItemsLid(self, lid, sel=None):
        iids = self.lists[lid].getIidsAtPoss(sel)
        self.setBuffer(iids, 'copy')
        return iids

    def pasteItems(self, lid, pos):
        iids = []
        if "action" in self.buffer and lid in self.lists:
            if self.buffer["action"] == 'copy':
                rcop = [self.items[rid].copy() for rid in self.buffer["iids"]]
                iids = self.items.extend(rcop)
            elif self.buffer["action"] == 'cut':
                iids = self.buffer["iids"]
            if len(iids) > 0:
                self.lists[lid].insertIids(iids, pos)
                self.buffer = {}
            else:
                self.clearBuffer()
        return iids

    def isEmptyBuffer(self):
        return len(self.buffer) == 0
    
    def setBuffer(self, iids, action):
        self.clearBuffer()
        self.buffer["iids"] = iids
        self.buffer["action"] = action
        print "Buffer:", self.buffer

    def clearBuffer(self):
        if "action" in self.buffer:
            if self.buffer["action"] == "cut":
                self.deleteItems(self.buffer["iids"])
            self.buffer = {}

    def moveItems(self, lid, nlid, sel, pos):
        iids = self.lists[lid].deleteItems(sel)
        self.lists[nlid].insertIids(iids, pos)

    def checkItem(self, lid, index, check):
        if lid is not None:
            iid = self.getList(lid).getIidAtPos(index)
            if iid is not None:
                ck = self.getItemFieldV(iid, self.getCheckF(), {})
                if (ck == 1 and not check) or ( ck == 0 and check):
                    self.getItemForIid(iid).flipEnabled()
        
    def getNamesList(self, lid):
        """list of queries for search"""
        names_list = []
        details = {"aim": "list"}
        details.update(self.details)
        return [(x, "%s" % self.getItemFieldV(iid, self.getNameF(), details)) for (x, iid) in enumerate(self.getList(lid).getIids())]
        # return [(x, "%s" % self.getItemFieldV(x, self.getNameF(), details)) for x in self.getList(lid).getIids()]

    def filterToOne(self, compare_ids, parameters):
        disable_ids = self.items.filtertofirstIds(compare_ids, parameters, complement=True)
        self.items.applyFunctTo(".setDisabled()", disable_ids, changes= True)

    def filterAll(self, compare_ids, parameters):
        disable_ids = self.items.filterpairsIds(compare_ids, parameters, complement=True)
        self.items.applyFunctTo(".setDisabled()", disable_ids, changes= True)

    # def processAll(self, actions_parameters, init_current=True):
    #     ### TODO


class RedsSet(DataSet):
    str_red = 'item'
    ###################### FIELDS REDS
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

    def __init__(self, parent):
        DataSet.__init__(self)
        self.parent = parent
        if self.parent.hasDataLoaded() and self.parent.dw.getData().hasLT():
            self.fields = self.fields_def_splits
        else:
            self.fields = self.fields_def_nosplit

    def recomputeAll(self, data):
        for ri, red in self.items.items():
            red.recompute(data)
        if data.hasLT():
            self.fields = self.fields_def_splits
        else:
            self.fields = self.fields_def_nosplit


class ContentManager:

    def __init__(self, parent, tabId, frame, short=None):
        self.tabId = tabId
        self.parent = parent
        self.matching = []
        self.curr_match = None
        self.prev_sels = None
        self.initData(parent)
        self.initBrowsers(frame)

    def initData(self, parent):
        self.data = DataSet()
    def initBrowsers(self, frame):
        self.browsers = {0: SplitBrowser(self, 0, frame)}
        self.browsers[0].resetCM(self)

    def getAssociated(self, pid, which):
        if pid in self.browsers:
            return self.browsers[pid].getWhich(which)
        return None


    def getDataHdl(self):
        return self.data
    def getViewHdl(self, pid=0):
        return self.browsers[pid]
    def getSW(self, pid=0):
        return self.browsers[0].getSW()

    ################## CONTENT MANAGEMENT METHODS
    def addData(self, data, src=None, sord=None):
        # return None
        nlid = self.getDataHdl().addList(items=data, src=src, sord=sord)
        self.getViewHdl().updateLid(nlid)
        return nlid

    def resetData(self, data, src=None, sord=None):
        self.getDataHdl().clearLists()
        return self.addData(data, src=src, sord=sord)

    def resetDetails(self, details={}, review=True):
        self.getDataHdl().resetDetails(details)
        if review:
            self.refreshAll()

    def refreshAll(self):
        for bi, brs in self.browsers.items():
            brs.refresh()

    def onNewList(self):
        self.addData(data=[], src=('manual', None))
        self.refreshAll()
        
    def onDeleteAny(self):
        lc = self.getViewHdl().getFocusedL()
        if lc is not None:
            if lc.isItemsL():
                sel = lc.getSelection()
                self.onDeleteItems(lc.getPid(), sel)
            elif lc.isContainersL():
                sel = lc.getSelection()
                self.onDeleteLists(sel)        
    def onDeleteLists(self, sel):
        def_lid = self.getDataHdl().deleteLists(sel=sel)
        if len(def_lid) > 0:
            self.refreshAll()
    def onDeleteItems(self, pid, sel):
        lid = self.browsers[pid].getLid()
        self.getDataHdl().deleteItemsLid(lid, sel)
        self.refreshAll()

    def onCutAny(self):
        lc = self.getViewHdl().getFocusedL()
        if lc is not None:
            if lc.isItemsL():
                sel = lc.getSelection()
                self.onCutItems(lc.getPid(), sel)
            elif lc.isContainersL():
                sel = lc.getSelection()
                self.onCutLists(sel)        
    def onCutLists(self, sel):
        iids = self.getDataHdl().cutLists(sel=sel)
        self.refreshAll()
    def onCutItems(self, pid, sel=None):
        lid = self.browsers[pid].getLid()
        iids = self.getDataHdl().cutItemsLid(lid, sel)
        self.refreshAll()

    def onCopyAny(self):
        lc = self.getViewHdl().getFocusedL()
        if lc is not None:
            if lc.isItemsL():
                sel = lc.getSelection()
                self.onCopyItems(lc.getPid(), sel)
            elif lc.isContainersL():
                sel = lc.getSelection()
                self.onCopyLists(sel)
    def onCopyLists(self, sel):
        iids = self.getDataHdl().copyLists(sel=sel)
    def onCopyItems(self, pid, sel=None):
        lid = self.browsers[pid].getLid()
        iids = self.getDataHdl().copyItemsLid(lid, sel)

    def onPasteAny(self):
        lc = self.getViewHdl().getFocusedL()
        if lc is not None:
            lid = self.browsers[lc.getPid()].getLid()
            pos = -1
            if lc.isItemsL():
                sel = lc.getSelection()
                if len(sel) > 0:
                    pos = sel[-1]
            iids = self.getDataHdl().pasteItems(lid, pos)
            if len(iids) > 0:
                self.refreshAll()

            
    def manageDrag(self, ctrl, trg_where, text):
        lid = self.getAssociated(ctrl.getPid(),"lid")
        sel = map(int, text.split(','))
        pos = None
        if ctrl.type_lc == "containers":
            if trg_where['index'] != -1:
                nlid = self.getDataHdl().getLidAtPos(trg_where['index'])
                if nlid != lid:
                    pos = -1
        else:
            nlid = lid
            pos = trg_where['index']
            if trg_where['after'] and pos != -1:
                pos += 1
        if pos is not None:
            self.getDataHdl().moveItems(lid, nlid, sel, pos)
        self.getViewHdl().refresh()


    def getIidsForAction(self, down=True):
        sel = []
        lc = self.getViewHdl().getFocusedL()
        if lc is not None:
            lid = self.browsers[lc.getPid()].getLid()
            if lc.isItemsL():
                sel = lc.getSelection()
                if len(sel) == 1 and down:
                    iids = self.getDataHdl().getList(lid).getIidsAfterPos(sel[0])
                else:
                    iids = self.getDataHdl().getList(lid).getIidsAtPoss(sel)
            elif lc.isContainersL():
                iids = self.getDataHdl().getList(lid).getIids()
        print "IIDS for action", iids
        return iids

    def getIidsForActionDown(self):
        sel = []
        lc = self.getViewHdl().getFocusedL()
        if lc is not None:
            lid = self.browsers[lc.getPid()].getLid()
            if lc.isItemsL():
                sel = lc.getSelection()
                iids = self.getDataHdl().getList(lid).getIidsAtPoss(sel)
            elif lc.isContainersL():
                iids = self.getDataHdl().getList(lid).getIids()
        print "IIDS for action", iids
        return iids

    
    def flipEnabled(self, iids):
        for iid in iids:
            self.getDataHdl().getItemForIid(iid).flipEnabled()
        self.refreshAll()
    def setAllEnabled(self):
        lc = self.getViewHdl().getFocusedL()
        if lc is not None:
            lid = self.browsers[lc.getPid()].getLid()
            iids = self.getDataHdl().getList(lid).getIids()
            for iid in iids:
                self.getDataHdl().getItemForIid(iid).setEnabled()
        self.refreshAll()
    def setAllDisabled(self):
        lc = self.getViewHdl().getFocusedL()
        if lc is not None:
            lid = self.browsers[lc.getPid()].getLid()
            iids = self.getDataHdl().getList(lid).getIids()
            for iid in iids:
                self.getDataHdl().getItemForIid(iid).setDisabled()
        self.refreshAll()

    #### FIND FUNCTIONS
    def getNamesList(self):
        lid = self.getViewHdl().getLid()
        return self.getDataHdl().getNamesList(lid)

    def updateFind(self, matching=None, non_matching=None, cid=None):
        if matching is not None:
            if self.curr_match is not None and self.curr_match >= 0 and self.curr_match < len(self.matching): 
                self.getViewHdl().getLCI().setUnfoundRow(self.matching[self.curr_match])
            self.curr_match = None
            self.matching = matching

        if matching is None or len(matching) > 0:
            self.getNextMatch()
            if self.curr_match == -1:
                if self.prev_sels is None:
                    self.prev_sels = self.getViewHdl().getLCI().clearSelection()
                self.getViewHdl().getLCI().setSelection(self.matching)
            elif self.curr_match == 0:
                self.getViewHdl().getLCI().clearSelection()
            if self.curr_match >= 0:
                self.getViewHdl().getLCI().setFoundRow(self.matching[self.curr_match])
                if self.matching[self.curr_match-1] != self.matching[self.curr_match]:
                    self.getViewHdl().getLCI().setUnfoundRow(self.matching[self.curr_match-1])
            
    def getNextMatch(self, n=None):
        if len(self.matching) > 0:
            if self.curr_match is None:
                self.curr_match = -1
            else:
                self.curr_match += 1
                if self.curr_match == len(self.matching):
                    self.curr_match = 0

    def quitFind(self, matching=None, non_matching=None, cid=None):
        if self.curr_match >=0 and self.curr_match < len(self.matching):
            self.getViewHdl().getLCI().setUnfoundRow(self.matching[self.curr_match])
        if self.prev_sels is not None and self.curr_match != -1:
            self.getViewHdl().getLCI().setSelection(self.prev_sels)
        self.prev_sels = None

    #### Generate pop up menu
    def makePopupMenu(self):
        self.parent.makePopupMenu(self.parent.toolFrame)

    ### TODO
    def filterToOne(self, parameters):
        compare_ids = self.getIidsForAction(down=True) 
        self.getDataHdl().filterToOne(compare_ids, parameters)
        self.refreshAll()
        
    def filterAll(self, parameters):
        compare_ids = self.getIidsForAction(down=True) 
        self.getDataHdl().filterAll(compare_ids, parameters)
        self.refreshAll()

    def processAll(self, actions_parameters, init_current=True):
        ### TODO implement
        pass 

        
    def GetNumberRowsItems(self):
        return self.getViewHdl().GetNumberRowsItems()
    def GetNumberRowsContainers(self):
        return self.getViewHdl().GetNumberRowsContainers()
    def GetNumberColsItems(self):
        return self.getViewHdl().GetNumberColsItems()
    def GetNumberColsContainers(self):
        return self.getViewHdl().GetNumberColsContainers()
    def GetNumberRowsFocused(self):
        return self.getViewHdl().GetNumberRowsFocused()
    def GetNumberColsFocused(self):
        return self.getViewHdl().GetNumberColsFocused()
    def GetNumberRows(self):
        return self.GetNumberRowsFocused()
    def GetNumberCols(self):
        return self.GetNumberColsFocused()
    def nbItems(self):
        return self.getViewHdl().nbItems()
    def nbLists(self):
        return self.getViewHdl().nbLists()

    def nbSelectedItems(self):
        return self.getViewHdl().nbSelectedItems()
    def nbSelectedLists(self):
        return self.getViewHdl().nbSelectedLists()
    def nbSelectedFocused(self):
        return self.getViewHdl().nbSelectedFocused()
    def nbSelected(self):
        return self.getViewHdl().nbSelected()


    def isEmptyBuffer(self):
        return self.getDataHdl().isEmptyBuffer()
    def hasFocusContainersL(self):
        return self.getViewHdl().getFocusedL() is not None and self.getViewHdl().getFocusedL().isContainersL()
    def hasFocusItemsL(self):
        return self.getViewHdl().getFocusedL() is not None and self.getViewHdl().getFocusedL().isItemsL()
    def getNbSelected(self):
        if self.getViewHdl().getFocusedL() is not None:
            return len(self.getViewHdl().getFocusedL().getSelection())
        return 0
    def getSelectedItemPos(self):
        if self.nbSelectedItems() == 1:
            pos = self.getViewHdl().getLCI().getFirstSelection()
            if pos > -1:
                return pos
        return None
    def getSelectedItemIid(self):
        pos = self.getSelectedItemPos()
        if pos > -1:
            return self.getDataHdl().getList(self.getViewHdl().getLid()).getIidAtPos(pos)
        return None
    def getSelectedItem(self):
        iid = self.getSelectedItemIid()
        if iid is not None:
            return self.getDataHdl().getItemForIid(iid)
        return None
    def substituteItem(self, item, iid):
        self.getDataHdl().substituteItem(item, iid)
        # self.refreshAll()
        ll = self.getDataHdl().getList(self.getViewHdl().getLid())
        pos = ll.getPosForIid(iid)
        self.getViewHdl().getLCI().loadItem(ll, pos)
    def substituteSelectedItem(self, item):
        iid = self.getSelectedItemIid()
        if iid is not None:
            self.substituteItem(item, iid)
    def updateEdit(self, edit_key, item, iids):
        if len(iids) == 1:
            self.substituteItem(item, iids[0])

    # def getSelectedRow(self): ### legacy no s
    #     lc = self.getViewHdl().getFocusedL()
    #     if lc is not None:
    #         return lc.getSelection()
    #     return []
    def getSelectedRow(self): ### legacy no s
        return self.getIidsForAction()
    
class RedsManager(ContentManager):

    def initData(self, parent):
        self.data = RedsSet(parent)
    def getSelectedQueries(self):
        red = self.getSelectedItem()
        if red is not None and isinstance(red, Redescription):
            return red.getQueries()
        return 

    def refreshComp(self, data):
        self.getDataHdl().recomputeAll(data)
        self.uptodate = True

    def recomputeAll(self, restrict):
        if self.parent.hasDataLoaded():
            self.uptodate = False
            self.refreshComp(self.parent.dw.getData())
            # for k,v in self.opened_edits.items():
            #     mc = self.parent.accessViewX(k)
            #     if mc is not None:
            #         mc.refresh()
            self.refreshAll()
