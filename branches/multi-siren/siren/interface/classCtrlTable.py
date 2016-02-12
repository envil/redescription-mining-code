import sys
import wx
import wx.lib.mixins.listctrl  as  listmix

from ..reremi.classQuery import SYM, Query, Literal
from ..reremi.classRedescription import Redescription

import pdb

LIST_TYPES_NAMES = ['file', 'run', 'manual', 'history']
LIST_TYPES_ICONS = [wx.ART_REPORT_VIEW, wx.ART_EXECUTABLE_FILE, wx.ART_LIST_VIEW, wx.ART_LIST_VIEW]

def makeContainersIL(icons):
    il = wx.ImageList(32, 32)
    for (i, icon) in enumerate(icons): 
        il.Add(wx.ArtProvider.GetBitmap(icon, wx.ART_FRAME_ICON))
    return il




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
        print "init ctrl basis"
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
    list_width = 150
    
    def __init__(self, parent, ID=wx.ID_ANY, pos=wx.DefaultPosition,
                 size=wx.DefaultSize):
        ListCtrlBasis.__init__(self, parent, ID, pos, size,
                               style=wx.LC_REPORT | wx.LC_HRULES | wx.LC_NO_HEADER | wx.LC_SINGLE_SEL)
        self.InsertColumn(0, '')

    def setDataSrc(self, data_src, pid=None):
        ListCtrlBasis.setDataSrc(self, data_src, pid)
        self.SetImageList(makeContainersIL(LIST_TYPES_ICONS), wx.IMAGE_LIST_SMALL)

    def upItem(self, i, llid):
        self.SetStringItem(i, 0, self.getDataSrc().getList(llid).getShortStr())
        self.SetItemImage(i, self.getDataSrc().getList(llid).getSrcTypId())

    def loadData(self, lid=None, cascade=True):
        if self.GetItemCount() > 0:
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
            ll = self.getAssociated("items")
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
        self.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.OnViewData)
        self.Bind(wx.EVT_LIST_ITEM_RIGHT_CLICK, self.OnRightClick)
        self.upck = True

    def getNbCols(self):
        return self.getDataSrc().getNbFields()
    def getColsInfo(self, lid=None, cs=None):
        return self.getDataSrc().getColsInfo(lid, cs)
    def getItemForIid(self, iid):
        try:
            return self.getDataSrc().getItemForIid(iid)
        except KeyError:
            return None
    def getItemForPos(self, pos):
        try:
            return self.getDataSrc().getItemForPos(pos) ### implement
        except KeyError:
            return None
    def getItemData(self, iid, pos):
        return self.getDataSrc().getItemData(iid, pos)

    def setDataSrc(self, data_src, pid=None):
        self.data_src = data_src
        self.pid = pid

    def OnCheckItem(self, index, flag):
        #### set disabled on item
        if self.upck:
            lid = self.getAssociated("lid")
            self.getDataSrc().checkItem(lid, index, flag)
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

    def OnRightClick(self, event):
        print "Right Click"

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
            for cid, col in enumerate(self.getDataSrc().getColsInfo(lid)):
                self.InsertColumn(cid, col["title"], format=col["format"], width=col["width"])
        else:
            self.updateColsTitles(lid)

        ll = self.getDataSrc().getList(lid)
        if ll is not None:
            # for item in ll.getItems():
            #     print item.status, item
            for i in range(len(ll)):
                self.InsertStringItem(i, "")
                rdt = ll.getItemDataAtPos(i)
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

    list_types_map = dict([(v,k) for (k,v) in enumerate(LIST_TYPES_NAMES)])
    
    def __init__(self, parent, id, src=('manual', None), name=None, iids=[]):        
        print "init list manager"
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
        return ListManager.list_types_map[self.src[0]]
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
            self.sortids.sort(key= lambda x:
                              self.parent.getItemFieldV(x, self.parent.fields[self.sortP[0]], {"aim": "sort", "iid": x}),
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
        rid = self.getRidAtPos(pos)
        return self.parent.getItemData(rid, pos)

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
    def getIidsAtPoss(self, poss=None):
        if poss is None:
            return list(self.sortids)
        else:
            return [self.getRidAtPos(p) for p in poss]
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

class ContentManager:

    str_item = 'item'
    fields_def = []
    name_m = None
    check_m = None

    def __init__(self):
        print "init content manager"
        self.details = {}
        self.items = {}        
        self.niid = 0
        self.nlid = 0
        self.lists = {}
        self.lists_ord = []

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
            sort_info = self.lists[lid].getSortInfo() ### TODO implement
            if sort_info[0] is not None:
                infos[sort_info[0]]["title"] += sort_info[1] 
        return infos
    def getItemForIid(self, iid):
        return self.items[iid]
    def getItemData(self, iid, pos):
        details = {"aim": "list", "id": iid, "pos": pos} ## TODO rid -> id in redescription
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
        iids = [self.niid+i for i in range(len(items))]
        nlid = self.nlid
        self.nlid += 1
        self.niid += len(items)

        self.items.update(dict(zip(iids, items)))
        ## TODO handle sord (order of display)
        self.lists[nlid] = ListManager(self, nlid, src, "", iids) 
        self.lists_ord.append(nlid)
        return nlid

    def resetLists(self, items, src=None, sord=None):
        self.clearLists()
        ## TODO handle sord (order of display)
        nlid = self.addList(items, src, sord)
        return nlid

    def resetDetails(self, details={}, review=True):
        self.resetAllSorts()
        self.details = details
        if review:
            self.splitctrl.updateAllPanels()

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
        self.items = {}
        self.lists_ord = []

    def deleteItemsLid(self, lid, sel=None):
        diids = self.lists[lid].deleteItems(sel)
        self.deleteItems(diids)
    def deleteItems(self, diids=None):
        if diids is None:
            diids = self.items.keys()
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
        iids = self.lists[lid].getIidsatPoss(sel)
        self.setBuffer(iids, 'copy')
        return iids

    def pasteItems(self, lid, pos):
        iids = []
        if "action" in self.buffer and lid in self.lists:
            if self.buffer["action"] == 'copy':
                rcop = [self.items[rid].copy() for rid in self.buffer["iids"]]
                iids = [self.niid+i for i in range(len(rcop))]
                self.niid += len(rcop)
                self.items.update(dict(zip(iids, rcop)))
            elif self.buffer["action"] == 'cut':
                iids = self.buffer["iids"]
            if len(iids) > 0:
                self.lists[lid].insertIids(iids, pos)
                self.buffer = {}
            else:
                self.clearBuffer()
        return iids
    
    def setBuffer(self, iids, action):
        self.clearBuffer()
        self.buffer["iids"] = iids
        self.buffer["action"] = action
        print self.buffer

    def clearBuffer(self):
        if "action" in self.buffer:
            if self.buffer["action"] == "cut":
                self.deleteItems(self.buffer["iids"])
            self.buffer = {}

    def doDrag(self, lid, sel, pos):
        iids = self.lists[lid].deleteItems(sel)
        self.lists[nlid].insertIids(iids, pos)

    def checkItem(self, lid, index, check):
        if lid is not None:
            iid = self.getList(lid).getIidAtPos(index)
            if iid is not None:
                ck = self.getItemFieldV(iid, self.getCheckF(), {})
                if (ck == 1 and not check) or ( ck == 0 and check):
                    self.getItemForRid(rid).flipEnabled()
        
class SplitCtrl:

    def __init__(self, parent, frame):
        print "init split ctrl"
        self.parent = parent
        self.panels = []
        self.cm = None
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
            return self.panels[pid]["items"].nbItems()
        return 0

    def GetNumberCols(self):
        """Return the number of columns in the active items ctrl"""
        return self.panels[pid]["items"].nbCols()

    def nbItems(self):
        return self.GetNumberRows()

    def Hide(self):
        self.getSplitP().Hide()

    def Show(self):
        self.getSplitP().Show()

    def resetCM(self, cm, pid=None):
        if pid is None:
            pid = 0
        self.cm = cm
        self.panels[pid]["containers"].setDataSrc(cm, pid)
        self.panels[pid]["items"].setDataSrc(cm, pid)
        if len(self.cm.getOrdLists()) > 0:
            self.panels[pid]["lid"] = self.cm.getOrdLists()[0]
            self.panels[pid]["containers"].loadData(self.panels[pid]["lid"])

    def getCM(self):
        return self.cm
        
    def updateAllPanels(self, cascade=True):
        for p in self.panels:
            print "update all", p["lid"], self.cm.getOrdLists(), self.cm.lists
            p["containers"].loadData(p["lid"], cascade)

    def addData(self, data, src=None, sord=None):
        nlid = self.cm.addList(items=data, src=src, sord=sord)
        for p in self.panels:
            if p["lid"] is None:
                p["lid"] = nlid
        self.updateAllPanels()
        return nlid

    def resetData(self, data, src=None, sord=None):
        self.cm.clearLists()
        return self.addData(data, src=src, sord=sord)
    
    def onNewList(self):
        self.addData(data=[], src=('manual', None))
        self.updateAllPanels(cascade=False)

    def onDeleteLists(self, sel):
        def_lid = self.cm.deleteLists(sel=sel)
        for p in self.panels:
            if p["lid"] == lid:
                p["lid"] = def_lid
            p["containers"].loadData(p["lid"]) ## triggers loadData for associated items
    def onDeleteItems(self, pid, sel):
        lid = self.panels[pid]["lid"]
        self.cm.deleteItemsLid(lid, sel)
        self.updateAllPanels()

    def onCutLists(self, sel):
        iids = self.cutLists(sel=sel)
        self.updateAllPanels()        
    def onCutItems(self, pid, sel=None):
        lid = self.panels[pid]["lid"]
        iids = self.cm.cutItemsLid(lid, sel)
        self.updateAllPanels()

    def onCopyLists(self, sel):
        iids = self.cutLists(sel=sel)
    def onCopyItems(self, pid, sel=None):
        lid = self.panels[pid]["lid"]
        iids = self.cm.cutItemsLid(lid, sel)

    def onPasteAny(self, ctrl, sel):
        lid = self.panels[ctrl.getPid()]["lid"]
        if ctrl.type_lc == "containers":
            pos = -1
        else:
            pos = sel
        iids = self.cm.pasteItems(lid, pos)
        if len(iids) > 0:
            self.updateAllPanels()
                

    def getSplitP(self):
        return self.splitP

    def setLid(self, pid=0, lid=None, pos=None):
        if lid is not None:
            self.panels[pid]["lid"] = lid
            self.panels[pid]["containers"].Focus(self.cm.getListPosForId(lid))
        elif pos is not None:
            lid = self.cm.getListIdAtPos(pos)
            self.panels[pid]["lid"] = lid
            self.panels[pid]["items"].loadData(lid)

    def getAssociated(self, pid, which):
        try:
            return self.panels[pid][which]
        except IndexError:
            return None


    # def jumpToNextLC(self, lc):
    #     if lc.type_lc == "items":
    #         fc = self.lcs["containers"]
    #     else:
    #         fc = self.lcs["items"]
    #     fc.SetFocus()
    #     if fc.GetFirstSelected() == -1:
    #         fc.Select(0)

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
        subsplitter.SplitVertically(panelL, panelR, list1.list_width)
        subsplitter.SetSashGravity(0.)
        subsplitter.SetMinimumPaneSize(1)
        
        self.splitP = subsplitter
        return list1, list2

    def addSplitPanel(self, frame, lid=None):
        list1, list2 = self.drawSplitPanel(frame)

        # if lid is None and len(self.lists) > 0:
        #     lid = self.lists_ord[0]

        pid = len(self.panels)
        self.panels.append({"containers": list1, "items": list2, "lid": lid, "pid": pid}) 
        
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
                self.cm.onDeleteLists(sel)
            elif ctrl.type_lc == "items":
                self.cm.onDeleteItems(ctrl.getPid(), sel)

    def onCut(self, event):
        ctrl = self.getSplitP().FindFocus()
        sel = ctrl.getSelection()
        if len(sel) > 0:
            if ctrl.type_lc == "containers":
                self.cm.onCutLists(sel)
            elif ctrl.type_lc == "items":
                self.cm.onCutItems(ctrl.getPid(), sel)
    def onCopy(self, event):
        ctrl = self.getSplitP().FindFocus()
        sel = ctrl.getSelection()
        if len(sel) > 0:
            if ctrl.type_lc == "containers":
                self.cm.onCopyLists(sel)
            elif ctrl.type_lc == "items":
                self.cm.onCopyItems(ctrl.getPid(), sel)
    def onPaste(self, event):
        ctrl = self.getSplitP().FindFocus()
        sel = ctrl.GetFocusedItem()
        self.cm.onPasteAny(ctrl, sel)

    def onFind(self, event):
        pass
    
    def manageDrag(self, ctrl, trg_where, text):
        lid = self.panels[ctrl.getPid()]["lid"]
        sel = map(int, text.split(','))
        pos = None
        if ctrl.type_lc == "containers":
            if trg_where['index'] != -1:
                nlid = self.cm.getLidAtPos(trg_where['index'])
                if nlid != lid:
                    pos = -1
        else:
            nlid = lid
            pos = trg_where['index']
            if trg_where['after'] and pos != -1:
                pos += 1
        if pos is not None:
            self.cm.doDrag(lid, sel, pos)
        self.updateAllPanels()



class RedsManager(ContentManager):
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

    def __init__(self, parent, tabId, frame, short=None):
        ContentManager.__init__(self)
        self.tabId = tabId
        self.parent = parent
        if self.parent.hasDataLoaded() and self.parent.dw.getData().hasLT():
            self.fields = self.fields_def_splits
        else:
            self.fields = self.fields_def_nosplit
        self.splitctrl = SplitCtrl(self, frame)
        self.splitctrl.resetCM(self, 0)
        print "init reds manager done"

    def getAssociated(self, pid, which):
        return self.splitctrl.getAssociated(pid, which)

    def getSplitP(self):
        return self.splitctrl.getSplitP()

    def resetData(self, data, src=None, sord=None):
        self.clearLists()
        self.splitctrl.addData(data, src, sord)

    def setLid(self, pid=0, lid=None, pos=None):
        self.splitctrl.setLid(pid, lid, pos)
