import re, datetime
import wx
import wx.lib.mixins.listctrl  as  listmix
from ..clired.classQuery import SYM
from ..clired.classCol import ColM
from ..clired.classRedescription import Redescription
from ..clired.classContent import StoredContainer

import pdb

TYPE_ICONS_DEF = wx.ART_LIST_VIEW
TYPE_ICONS_MAP = {StoredContainer.NFILE: wx.ART_REPORT_VIEW,
                  StoredContainer.NRUN: wx.ART_EXECUTABLE_FILE}

LIST_TYPES_NAMES = StoredContainer.STORED_TYPES_NAMES
LIST_TYPES_ICONS = [TYPE_ICONS_MAP.get(x, TYPE_ICONS_DEF) for x in LIST_TYPES_NAMES]
REPLACE_NONE = "-"

def makeContainersIL(icons):
    size_side = 16
    il = wx.ImageList(size_side, size_side)
    for (i, icon) in enumerate(icons): 
        il.Add(wx.ArtProvider.GetBitmap(icon, wx.ART_FRAME_ICON, (size_side, size_side)))
    return il

###### DRAG AND DROP UTILITY
class ListDrop(wx.DropTarget):
    """ Drop target for simple lists. """

    def __init__(self, setFn):
        """ Arguments:
         - setFn: Function to call on drop.
        """
        wx.DropTarget.__init__(self)

        self.setFn = setFn

        # specify the type of data we will accept
        self.data = wx.TextDataObject()
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


#----------------------------------------------------------------------------
#----------------------------------------------------------------------------
from bisect import bisect


class MyTextEditMixin:
    """    
    A mixin class that enables any text in any column of a
    multi-column listctrl to be edited by clicking on the given row
    and column.  You close the text editor by hitting the ENTER key or
    clicking somewhere else on the listctrl. You switch to the next
    column by hiting TAB.

    To use the mixin you have to include it in the class definition
    and call the __init__ function::

        class TestListCtrl(wx.ListCtrl, TextEditMixin):
            def __init__(self, parent, ID, pos=wx.DefaultPosition,
                         size=wx.DefaultSize, style=0):
                wx.ListCtrl.__init__(self, parent, ID, pos, size, style)
                TextEditMixin.__init__(self) 


    Authors:     Steve Zatz, Pim Van Heuven (pim@think-wize.com)
    """

    editorBgColour = wx.Colour(255,255,175) # Yellow
    editorFgColour = wx.Colour(0,0,0)       # black
        
    def __init__(self):
        #editor = wx.TextCtrl(self, -1, pos=(-1,-1), size=(-1,-1),
        #                     style=wx.TE_PROCESS_ENTER|wx.TE_PROCESS_TAB \
        #                     |wx.TE_RICH2)

        self.make_editor()
        self.Bind(wx.EVT_TEXT_ENTER, self.CloseEditor)
        # self.Bind(wx.EVT_LEFT_DOWN, self.OnLeftDown)
        self.Bind(wx.EVT_LEFT_DCLICK, self.OnLeftDown)
        self.Bind(wx.EVT_LIST_ITEM_SELECTED, self.OnItemSelected, self)


    def make_editor(self, col_style=wx.LIST_FORMAT_LEFT):
        
        style =wx.TE_PROCESS_ENTER|wx.TE_PROCESS_TAB|wx.TE_RICH2
        style |= {wx.LIST_FORMAT_LEFT: wx.TE_LEFT,
                  wx.LIST_FORMAT_RIGHT: wx.TE_RIGHT,
                  wx.LIST_FORMAT_CENTRE : wx.TE_CENTRE
                  }[col_style]
        
        editor = wx.TextCtrl(self, -1, style=style)
        editor.SetBackgroundColour(self.editorBgColour)
        editor.SetForegroundColour(self.editorFgColour)
        font = self.GetFont()
        editor.SetFont(font)

        self.curRow = 0
        self.curCol = 0

        editor.Hide()
        if hasattr(self, 'editor'):
            self.editor.Destroy()
        self.editor = editor

        self.col_style = col_style
        self.editor.Bind(wx.EVT_CHAR, self.OnChar)
        self.editor.Bind(wx.EVT_KILL_FOCUS, self.CloseEditor)
        
        
    def OnItemSelected(self, evt):
        self.curRow = evt.GetIndex()
        evt.Skip()
        

    def OnChar(self, event):
        ''' Catch the TAB, Shift-TAB, cursor DOWN/UP key code
            so we can open the editor at the next column (if any).'''

        keycode = event.GetKeyCode()
        if keycode == wx.WXK_TAB and event.ShiftDown():
            self.CloseEditor()
            if self.curCol-1 >= 0:
                self.OpenEditor(self.curCol-1, self.curRow)
            
        elif keycode == wx.WXK_TAB:
            self.CloseEditor()
            if self.curCol+1 < self.GetColumnCount():
                self.OpenEditor(self.curCol+1, self.curRow)

        elif keycode == wx.WXK_ESCAPE:
            self.CloseEditor()

        elif keycode == wx.WXK_DOWN:
            self.CloseEditor()
            if self.curRow+1 < self.GetItemCount():
                self._SelectIndex(self.curRow+1)
                self.OpenEditor(self.curCol, self.curRow)

        elif keycode == wx.WXK_UP:
            self.CloseEditor()
            if self.curRow > 0:
                self._SelectIndex(self.curRow-1)
                self.OpenEditor(self.curCol, self.curRow)
            
        else:
            event.Skip()

    
    def OnLeftDown(self, evt=None):
        ''' Examine the click and double
        click events to see if a row has been click on twice. If so,
        determine the current row and columnn and open the editor.'''
        if self.editor.IsShown():
            self.CloseEditor()
            
        x,y = evt.GetPosition()
        row,flags = self.HitTest((x,y))
    
        if row != self.curRow: # self.curRow keeps track of the current row
            evt.Skip()
            return
        
        # the following should really be done in the mixin's init but
        # the wx.ListCtrl demo creates the columns after creating the
        # ListCtrl (generally not a good idea) on the other hand,
        # doing this here handles adjustable column widths
        
        self.col_locs = [0]
        loc = 0
        for n in range(self.GetColumnCount()):
            loc = loc + self.GetColumnWidth(n)
            self.col_locs.append(loc)

        
        col = bisect(self.col_locs, x+self.GetScrollPos(wx.HORIZONTAL)) - 1
        self.OpenEditor(col, row)


    def OpenEditor(self, col, row):
        ''' Opens an editor at the current position. '''

        # give the derived class a chance to Allow/Veto this edit.
        evt = wx.ListEvent(wx.wxEVT_COMMAND_LIST_BEGIN_LABEL_EDIT, self.GetId())
        evt.m_itemIndex = row
        evt.m_col = col
        item = self.GetItem(row, col)
        evt.m_item.SetId(item.GetId()) 
        evt.m_item.SetColumn(item.GetColumn()) 
        evt.m_item.SetData(item.GetData()) 
        evt.m_item.SetText(item.GetText()) 
        ret = self.GetEventHandler().ProcessEvent(evt)
        if ret and not evt.IsAllowed():
            return   # user code doesn't allow the edit.

        if self.GetColumn(col).m_format != self.col_style:
            self.make_editor(self.GetColumn(col).m_format)
    
        x0 = self.col_locs[col]
        x1 = self.col_locs[col+1] - x0

        scrolloffset = self.GetScrollPos(wx.HORIZONTAL)

        # scroll forward
        if x0+x1-scrolloffset > self.GetSize()[0]:
            if wx.Platform == "__WXMSW__":
                # don't start scrolling unless we really need to
                offset = x0+x1-self.GetSize()[0]-scrolloffset
                # scroll a bit more than what is minimum required
                # so we don't have to scroll everytime the user presses TAB
                # which is very tireing to the eye
                addoffset = self.GetSize()[0]/4
                # but be careful at the end of the list
                if addoffset + scrolloffset < self.GetSize()[0]:
                    offset += addoffset

                self.ScrollList(offset, 0)
                scrolloffset = self.GetScrollPos(wx.HORIZONTAL)
            else:
                # Since we can not programmatically scroll the ListCtrl
                # close the editor so the user can scroll and open the editor
                # again
                self.editor.SetValue(self.GetItem(row, col).GetText())
                self.curRow = row
                self.curCol = col
                self.CloseEditor()
                return

        y0 = self.GetItemRect(row)[1]
        
        editor = self.editor
        editor.SetDimensions(x0-scrolloffset,y0, x1,-1)
        
        editor.SetValue(self.getCManager().getRowDataDict(self, pos=item.GetId()).get("name", "")) 
        editor.Show()
        editor.Raise()
        editor.SetSelection(-1,-1)
        editor.SetFocus()
    
        self.curRow = row
        self.curCol = col

    
    # FIXME: this function is usually called twice - second time because
    # it is binded to wx.EVT_KILL_FOCUS. Can it be avoided? (MW)
    def CloseEditor(self, evt=None):
        ''' Close the editor and save the new value to the ListCtrl. '''
        if not self.editor.IsShown():
            return
        text = self.editor.GetValue()
        self.editor.Hide()
        self.SetFocus()
        
        # post wxEVT_COMMAND_LIST_END_LABEL_EDIT
        # Event can be vetoed. It doesn't has SetEditCanceled(), what would 
        # require passing extra argument to CloseEditor() 
        evt = wx.ListEvent(wx.wxEVT_COMMAND_LIST_END_LABEL_EDIT, self.GetId())
        evt.m_itemIndex = self.curRow
        evt.m_col = self.curCol
        item = self.GetItem(self.curRow, self.curCol)
        evt.m_item.SetId(item.GetId()) 
        evt.m_item.SetColumn(item.GetColumn()) 
        evt.m_item.SetData(item.GetData()) 
        evt.m_item.SetText(text) #should be empty string if editor was canceled
        ret = self.GetEventHandler().ProcessEvent(evt)
        if not ret or evt.IsAllowed():
            self.getCManager().editedName(self, pos=item.GetId(), name=text)
            # if self.IsVirtual():
            #     # replace by whather you use to populate the virtual ListCtrl
            #     # data source
            #     self.SetVirtualData(self.curRow, self.curCol, text)
            # else:
            #     self.SetItem(self.curRow, self.curCol, text)
        self.RefreshItem(self.curRow)

    def _SelectIndex(self, row):
        listlen = self.GetItemCount()
        if row < 0 and not listlen:
            return
        if row > (listlen-1):
            row = listlen -1
            
        self.SetItemState(self.curRow, ~wx.LIST_STATE_SELECTED,
                          wx.LIST_STATE_SELECTED)
        self.EnsureVisible(row)
        self.SetItemState(row, wx.LIST_STATE_SELECTED,
                          wx.LIST_STATE_SELECTED)



#----------------------------------------------------------------------------
#----------------------------------------------------------------------------


class ListCtrlBasis(wx.ListCtrl, listmix.ListCtrlAutoWidthMixin):
    type_lc = "-"

    def __init__(self, parent, cm, ID=wx.ID_ANY, pos=wx.DefaultPosition,
                     size=wx.DefaultSize, style=0):
        wx.ListCtrl.__init__(self, parent, ID, pos, size, style)
        listmix.ListCtrlAutoWidthMixin.__init__(self)
        self.cm = cm
        self.upOn = True
        self.InsertColumn(0, '')
        dt = ListDrop(self._dd)
        self.SetDropTarget(dt)
        self.Bind(wx.EVT_LIST_ITEM_RIGHT_CLICK, self.OnRightClick)
        self.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.OnItemActivated)
        # self.Bind(wx.EVT_LIST_ITEM_FOCUSED, self.OnFoc)
        self.Bind(wx.EVT_LEFT_UP, self.OnLeftClick)
        
    def getTypeL(self):
        return self.type_lc
    def isItemsL(self):
        return False
    def isContainersL(self):
        return False

    def getCManager(self):
        return self.cm

    def loadData(self, rows_data, cols_info=[], select_ids=[], refresh_cols=False):
        nbI = self.GetItemCount()
        if nbI > 0 and (nbI > len(rows_data) or refresh_cols or len(cols_info) != self.GetColumnCount()):
            self.DeleteAllItems()
            nbI = 0
        self.initColumns(cols_info, refresh_cols)

        for (i, ll) in enumerate(rows_data):
            self.upItem(i, ll, ll.get("id") in select_ids, init=(i >= nbI))

            
    def RefreshItem(self, row):
        rdt = self.getCManager().getRowData(self, row)
        self.upItem(row, rdt, self.IsSelected(row))

    def initColumns(self, cols_info=[], refresh=False):
        pass       
    def initRow(self, row, rdt):
        self.InsertStringItem(row, "")
    def upItem(self, row, rdt, selected=False, init=False):
        pass
    
    def OnItemActivated(self, event):
        self.getCManager().fwdeventItemActivated(self, event)                
    def OnLeftClick(self, event):
        self.getCManager().fwdeventLeftClick(self, event)
    def OnRightClick(self, event):
        self.getCManager().fwdeventRightClick(self, event)       
    def _onSelect(self, event):
        self.getCManager().fwdeventSelect(self, event)
        event.Skip()
        
    # def turnUp(self, val):
    #     self.upOn = val
    # def isUp(self):
    #     return self.upOn

    def _onInsert(self, event):
        # Sequencing on a drop event is:
        # wx.EVT_LIST_ITEM_SELECTED
        # wx.EVT_LIST_BEGIN_DRAG
        # wx.EVT_LEFT_UP
        # wx.EVT_LIST_ITEM_SELECTED (at the new index)
        # wx.EVT_LIST_INSERT_ITEM
        #--------------------------------
        # this call to onStripe catches any addition to the list; drag or not
        self._onStripe()
        event.Skip()

    def _onDelete(self, event):
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
        # #self.SetItemBackgroundColour(0, wx.SystemSettings.GetColour(wx.SYS_COLOUR_WINDOWTEXT))
        # if self.IsSelected(row):
        #     self.SetItemTextColour(row, wx.Colour(0,222,222))
        # else:
        self.SetItemTextColour(row, wx.Colour(139,0,0))
    def setUnfoundRow(self, row):
        self.SetItemTextColour(row, wx.SystemSettings.GetColour(wx.SYS_COLOUR_WINDOWTEXT))

    def clearSelection(self):
        sels = self.getSelection()
        for sel in sels:
            self.Select(sel, on=0)
        return sels
    def setSelection(self, sels):
        self.clearSelection()
        for sel in sels:
            self.Select(sel, on=1)

    def _startDrag(self, e):
        """ Put together a data object for drag-and-drop _from_ this list. """
        # Create the data object: Just use plain text.        
        txt = ",".join(map(str, self.getSelection()))
        data = wx.TextDataObject()
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
                    self.SetItemBackgroundColour(x,wx.SystemSettings.GetColour(wx.SYS_COLOUR_3DLIGHT))
                else:
                    self.SetItemBackgroundColour(x,wx.WHITE)

    def GetNumberRows(self):
        return self.GetItemCount()
    def GetNumberCols(self):
        return self.GetColumnCount()
        

class ListCtrlContainers(ListCtrlBasis): #, MyTextEditMixin):
    type_lc = "containers" 
    list_width = 150
    
    def __init__(self, parent, cm, ID=wx.ID_ANY, pos=wx.DefaultPosition,
                 size=wx.DefaultSize):
        ListCtrlBasis.__init__(self, parent, cm, ID, pos, size,
                               style=wx.LC_REPORT | wx.LC_HRULES | wx.LC_NO_HEADER | wx.LC_SINGLE_SEL)
        # MyTextEditMixin.__init__(self)
        self.InsertColumn(0, '')
        self.SetColumnWidth(0, self.list_width)
        self.Bind(wx.EVT_LIST_ITEM_SELECTED, self._onSelect)
        if self.getCManager().withListIcons():
            self.AssignImageList(makeContainersIL(LIST_TYPES_ICONS), wx.IMAGE_LIST_SMALL)
        # self.Bind(wx.EVT_KEY_DOWN, self.OnKeyDown)
        
    def isContainersL(self):
        return True

    def initColumns(self, cols_info=[], refresh=False):
        pass       
    def upItem(self, row, rdt, selected=False, init=False):
        if init:
            self.Append([rdt.get("name", "")])
        else:
            self.SetItem(row, 0, rdt.get("name", ""))
        if self.getCManager().withListIcons():
            self.SetItemImage(row, rdt.get("src_typid", 0))
        if selected:
            self.Select(row)
        
    def _onStripe(self):
        pass


if wx.__version__ >= "4.1.0":
    class ListCheckBasis:
        def __init__(self):
            self.EnableCheckBoxes()
            self.Bind(wx.EVT_LIST_ITEM_CHECKED, self.OnCheckItem)
            self.Bind(wx.EVT_LIST_ITEM_UNCHECKED, self.OnCheckItem)

        def OnCheckItem(self, event):
            if self.upck:
                self.getCManager().fwdeventCheckItem(self, event)
            
else:
    class ListCheckBasis(listmix.CheckListCtrlMixin):
        def __init__(self):
            listmix.CheckListCtrlMixin.__init__(self)

        def OnCheckItem(self, index, flag):
            if self.upck:
                self.getCManager().fwdeventCheckItem(self, index)

class ListCtrlItems(ListCtrlBasis, ListCheckBasis):
    type_lc = "items" 
        
    def __init__(self, parent, cm, ID=wx.ID_ANY, pos=wx.DefaultPosition,
                 size=wx.DefaultSize):
        ListCtrlBasis.__init__(self, parent, cm, ID, pos, size,
                               style=wx.LC_REPORT | wx.LC_HRULES) # | wx.LC_NO_HEADER)
        ListCheckBasis.__init__(self)         
        self.Bind(wx.EVT_LIST_BEGIN_DRAG, self._startDrag)        
        self.Bind(wx.EVT_LIST_BEGIN_DRAG, self._startDrag)        
        self.Bind(wx.EVT_LIST_INSERT_ITEM, self._onInsert)
        self.Bind(wx.EVT_LIST_DELETE_ITEM, self._onDelete)
        self.Bind(wx.EVT_LIST_COL_CLICK, self.OnColClick)
        self.upck = True
        
    def isItemsL(self):
        return True
        
    def OnColClick(self, event):
        colS = event.GetColumn()
        if colS == -1:
            event.Skip()
        else:
            self.getCManager().fwdeventColClick(self, event)
            
    def initColumns(self, cols_info=[], refresh=False):
        if refresh or len(cols_info) != self.GetColumnCount():
            self.DeleteAllColumns()
            for cid, col in enumerate(cols_info):
                self.InsertColumn(cid, col["title"], format=col["format"], width=col["width"])
        else:
            for cid, col in enumerate(cols_info):
                tmp = self.GetColumn(cid)
                tmp.SetText(col["title"])
                self.SetColumn(cid, tmp)   

    def upItem(self, row, rdt, selected=False, init=False):
        if init:
            self.Append(rdt["cols"])
        else:
            for (cid, cv) in enumerate(rdt["cols"]):
                self.SetItem(row, cid, cv)
        if "checked" in rdt:
            self.upck = False
            self.CheckItem(row, rdt["checked"])
            self.setBckColor(row, rdt["checked"])
            self.upck = True
        if selected:
            self.Select(row)
                    
    def setBckColor(self, row, checked=False):
        if checked:
            self.SetItemTextColour(row, wx.SystemSettings.GetColour( wx.SYS_COLOUR_WINDOWTEXT ))
        else:
            self.SetItemTextColour(row, wx.SystemSettings.GetColour( wx.SYS_COLOUR_GRAYTEXT ))

class TableView:

    def __init__(self, cm, frame, detached_handle=None):
        self.detached_handle = detached_handle

    def isDetached(self):
        return self.detached_handle is not None
    def getDetachedHandle(self):
        return self.detached_handle

class SplitView(TableView):

    def __init__(self, cm, frame, detached_handle=None):
        TableView.__init__(self, cm, frame, detached_handle)
        self.last_foc = None

        self.sw = wx.SplitterWindow(frame, -1, style=wx.SP_LIVE_UPDATE) #|wx.SP_NOBORDER)
        panelL = wx.Panel(self.sw, -1)
        panelR = wx.Panel(self.sw, -1)
        
        self.lcc = ListCtrlContainers(panelL, cm, -1)
        self.lci = ListCtrlItems(panelR, cm, -1)

        vbox1 = wx.BoxSizer(wx.HORIZONTAL)
        vbox1.Add(self.lcc, 1, wx.EXPAND)
        panelL.SetSizer(vbox1)
        vbox1 = wx.BoxSizer(wx.HORIZONTAL)
        vbox1.Add(self.lci, 1, wx.EXPAND)
        panelR.SetSizer(vbox1)
        
        self.sw.SplitVertically(panelL, panelR, self.lcc.list_width)
        self.sw.SetSashGravity(0.)
        self.sw.SetMinimumPaneSize(1)
        
    def getFocusedL(self):
        ret = None
        ff = self.sw.FindFocus()
        if ff is not None and (ff == self.lci or ff == self.lcc):
            ret = ff
        elif (self.last_foc == self.lci or self.last_foc == self.lcc):
            ret = self.last_foc
        return ret

    def markFocus(self, foc=None):
        if foc is not None:
            self.last_foc = foc
        else:
            self.last_foc = self.sw.FindFocus()
        
    def getSW(self):
        return self.sw
    def getLCC(self):
        return self.lcc
    def getLCI(self):
        return self.lci
    def isLCC(self, ll):
        return self.lcc == ll
    def isLCI(self, ll):
        return self.lci == ll
    def hasFocusLCC(self):
        return self.isLCC(self.getFocusedL())
    def hasFocusLCI(self):
        return self.isLCI(self.getFocusedL())

class SingleView(TableView):

    def __init__(self, cm, frame, detached_handle=None):
        TableView.__init__(self, cm, frame, detached_handle)
        panelM = wx.Panel(frame, -1)        
        self.lci = ListCtrlItems(panelM, cm, -1)

        vbox1 = wx.BoxSizer(wx.HORIZONTAL)
        vbox1.Add(self.lci, 1, wx.EXPAND)
        panelM.SetSizer(vbox1)
        self.sw = panelM

    def getFocusedL(self):
        return self.lci

    def markFocus(self, foc=None):
        pass
        
    def getSW(self):
        return self.sw
    def getLCC(self):
        return None
    def getLCI(self):
        return self.lci
    def isLCC(self, ll):
        return False
    def isLCI(self, ll):
        return self.lci == ll
    def hasFocusLCC(self):
        return len(self.getLCI().getSelection()) == 0
    def hasFocusLCI(self):
        return len(self.getLCI().getSelection()) > 0


class ContentTable:
    
    str_item = 'item'
    fields_def = []
    name_m = None
    check_m = None
    
    #### COLUMN WIDTHS
    width_colcheck = 25
    width_colid = 50
    width_colname = 150
    width_colnamew = 300
    width_colinfo = 80
    width_colinfow = 100
    width_colinfon = 8
    
    def __init__(self, parent, tabId, tabType, frame, short=None, single=False, detached_handle=None, activate=True):
        self.active = False
        self.active_lid = None
        self.details = {}
        self.tabId = tabId
        self.tabType = tabType
        self.parent = parent
        if single:
            self.view = SingleView(self, frame, detached_handle)
        else:
            self.view = SplitView(self, frame, detached_handle)
        if activate:
            self.load()
            self.active = True

    def isActive(self):
        return self.active and self.hasContentData()
    def isSingle(self):
        return isinstance(self.view, SingleView)
    def isDetached(self):
        return self.view.isDetached()
    def getHandle(self):
        if self.isDetached():
            return self.view.getDetachedHandle()
        return self.parent
    def getFrame(self):
        return self.getHandle().getFrame()
    def getTabId(self):
        return self.tabId
    def getTabType(self):
        return self.tabType
        
    def getTab(self):
        return {"id": self.getTabId(), "type": self.getTabType(), "tab": self, "detached": self.isDetached()}        

    def hasContentData(self):
        return self.getContentData() is not None
    def getContentData(self):
        return None

    def getView(self):
        return self.view
    def getSW(self):
        return self.view.getSW()
    def getLCC(self):
        return self.view.getLCC()
    def getLCI(self):
        return self.view.getLCI()
    def isLCC(self, ll):
        return self.view.isLCC(ll)
    def isLCI(self, ll):
        return self.view.isLCI(ll)

    def getActiveLid(self):
        return self.active_lid
    def setActiveLid(self, lid):
        self.active_lid = lid
        if lid is None:
            self.setDefActiveLid()

    def setDefActiveLid(self):
        olids = self.getOrdLids()
        if self.active_lid is None:
            if len(olids) > 0:
                self.active_lid = olids[0]
        elif self.active_lid not in olids:            
            if len(olids) > 0:
                self.active_lid = olids[0]
            else:
                self.active_lid = None

    def getOrdLids(self):
        if self.hasContentData():
            return self.getContentData().getOrdLids()
        return []
        
    #### FOR PARENT
    def hasFocusItemsL(self):
        return self.view.hasFocusLCI()
    def hasFocusContainersL(self):
        return self.view.hasFocusLCC()
    def GetNumberRows(self):
        return self.getLCI().GetNumberRows()
    def nbSelected(self):
        if self.view.getFocusedL() is not None:
            return self.view.getFocusedL().GetSelectedItemCount()
        return 0
    def getSelectedIids(self):
        lid = self.getActiveLid()
        if lid is not None and self.hasContentData():
            return [self.getContentData().getIidForLidPos(lid, pos) for pos in self.getLCI().getSelection()]
        return []
    def getSelectedLids(self):
        if self.isSingle():
            return [self.getActiveLid()]
        if self.hasContentData():
            return [self.getContentData().getLidForPos(pos) for pos in self.getLCC().getSelection()]
        return []
    def getSelectedItems(self):
        l = []
        if self.hasContentData():
            if self.hasFocusItemsL():
                l = [(iid, self.getContentData().getItem(iid)) for iid in self.getSelectedIids()]
            elif self.hasFocusContainersL():
                for lid in self.getSelectedLids():
                    l.extend([(iid, self.getContentData().getItem(iid)) for iid in self.getContentData().getIidsList(lid)])
        return l

    def getSelectedIid(self):
        if self.nbSelected() == 1 and self.hasFocusItemsL():
            return self.getSelectedIids()[0]        
    def getSelectedItem(self):
        if self.nbSelected() == 1 and self.hasFocusItemsL():
            return self.getSelectedItems()[0][1]

    def getItemsList(self, lid=None):
        if lid is not None and self.hasContentData():
            return [(iid, self.getContentData().getItem(iid)) for iid in self.getContentData().getIidsList(lid)]
        return []
    def getList(self, lid=None):
        if lid is not None and self.hasContentData():
            return self.getContentData().getList(lid)
    def getActiveList(self):
        return self.getList(self.getActiveLid())
    def isEmptyBuffer(self):
        return not self.hasContentData() or self.getContentData().lenBuffer() == 0

    
    #### HANDLING DATA START
    def withListIcons(self):
        return False
    def getRowData(self, lc, row): return {}
    def getNbFields(self):
        return len(self.fields)
    def getColsInfo(self, lid=None, refresh=False):
        infos = [{"title": field[0], "format": field[-1], "width": field[-2]} for field in self.getFields(lid, refresh)]
        if lid is not None and self.hasContentData():
            sort_info = self.getContentData().getList(lid).getSortInfo()
            if sort_info[0] is not None and sort_info[0] < len(infos):
                if sort_info[1]:
                    direct = SYM.SYM_ARRTOP
                else:
                    direct = SYM.SYM_ARRBOT
                infos[sort_info[0]]["title"] += direct
        return infos
    #### HANDLING DATA END

    def getListShortStr(self, lid=None):
        if self.hasContentData():
            if lid is None:
                lid = self.getActiveLid()
            ll = self.getContentData().getList(lid)
            if ll is not None:
                return ll.getShortStr()
                if isinstance(ll, StoredContainer):
                    dt["src_typid"] = ll.getSrcTypId()
                return dt
        
    def getListData(self, lid, pos=None):
        if self.hasContentData():
            if lid is None:
                lid = self.getActiveLid()

            ll = self.getContentData().getList(lid)
            if ll is not None:
                dt = {"name": ll.getShortStr(), "id": lid, "pos": pos}
                if isinstance(ll, StoredContainer):
                    dt["src_typid"] = ll.getSrcTypId()
                return dt
                
    def getCheckF(self):
        return ('', self.check_m)
    def getNameF(self):
        return ('name', self.name_m)
    
    def resetFields(self):
        self.fields = []
        self.fields.extend(self.fields_def)        
        
    def getFields(self, lid=None, refresh=False):
        return self.fields        
        
    def getItemData(self, iid, pos=None):
        dt = ["%s" % self.getItemFieldV(iid, field, {"aim": "list", "id": iid, "pos": pos}) for field in self.getFields()]
        ck = self.getItemFieldV(iid, self.getCheckF(), {"aim": "list", "id": iid, "pos": pos})==1
        return {"cols": dt, "checked": ck, "id": iid}

    def prepareItemVDetails(self, loc_details={}, field=[]):
        f_details = {"replace_none": REPLACE_NONE, "named": True, "style": "U"}
        f_details.update(self.getCDetails())
        f_details.update(loc_details)
        if len(field) > 2 and field[2] is not None:
                f_details.update(field[2])
        return f_details
    
    def getItemFieldV(self, iid, field, details):
        if not self.hasContentData() or iid is None or field is None:
            return ""
        more_details = self.prepareItemVDetails(details, field)
        return self.getContentData().getItemFieldV(iid, field, more_details)

    def changedLid(self, lid=None):
        old_lid = self.getActiveLid()
        if lid is None:
            self.setDefActiveLid()
        else:
            self.setActiveLid(lid)
        if old_lid != self.getActiveLid():
            self.resetFields()
        self.loadData(self.getActiveLid())
    def load(self, lid=None, rfields=True):
        if lid is None:
            self.setDefActiveLid()
        else:
            self.setActiveLid(lid)
        if rfields:
            self.resetFields()
        self.loadData(self.getActiveLid(), rfields=rfields)        
        
    def loadData(self, lid=None, rfields=False, select_iids=[]):
        if not self.hasContentData():
            return
        self.active = False
        if not self.isSingle():
            llids = self.getOrdLids()
            lists_data = [self.getListData(llid, pos) for pos, llid in enumerate(llids)]
            self.getLCC().loadData(lists_data, select_ids=[lid])

        if lid is not None:
            cols_info = self.getColsInfo(lid, refresh=rfields)
            items_data = [self.getItemData(iid, pos) for pos, iid in enumerate(self.getContentData().getIidsList(lid))]
            self.getLCI().loadData(items_data, cols_info, select_ids=select_iids, refresh_cols=rfields)
        self.active = True
        
    def getRowData(self, ll, row):
        if not self.hasContentData():
            return
        if self.isLCC(ll):
            lid = self.getContentData().getLidForPos(row)
            if lid is not None:
                return self.getListData(lid)
        elif self.isLCI(ll):            
            iid = self.getContentData().getIidForLidPos(self.getActiveLid(), row)
            if iid is not None:
                return self.getItemData(iid)
            
    def resetDetails(self, details={}):
        self.details = details
    def getCDetails(self):
        return self.details
    def getCDetail(self, dk):
        return self.details.get(dk)
    def setCDetail(self, dk, v):
        self.details[dk] = v

    def refreshItem(self, iid):
        if not self.hasContentData():
            return
        lid = self.getActiveLid()
        pos = self.getContentData().getPosForLidIid(lid, iid)
        if pos is not None:
            self.refreshList(lid) ### changed status update
            self.getLCI().RefreshItem(pos)    
    def refreshList(self, lid):
        if not self.hasContentData() or self.isSingle():
            return
        pos = self.getContentData().getPosForLid(lid)
        if pos is not None:
            self.getLCC().RefreshItem(pos)    
    def refreshListContent(self, lid, selected_iids=None, new_lid=False):
        if not self.hasContentData():
            return
        if lid is None:
            lid = self.getActiveLid()
        if lid == self.getActiveLid():
            if selected_iids is None:
                selected_iids = self.getSelectedIids()
            self.loadData(lid, select_iids=selected_iids)
        else:
            if new_lid:
                self.loadData()
            self.refreshList(lid)

    ########## HANDLING ACTIONS START
    def fwdeventLeftClick(self, lc, event):
        #### menu
        self.makeMenu()

    def fwdeventRightClick(self, lc, event):
        #### menu
        self.view.markFocus(lc)
        self.makePopupMenu()

    def makeMenu(self):
        self.parent.makeMenu(self)
    def makePopupMenu(self):
        self.parent.makePopupMenu(self)
        
    def fwdeventItemActivated(self, lc, event):
        if self.isLCI(lc):
            what = self.getSelectedItem()
            if what is not None:
                iid = what.getUid()
                self.parent.viewOpen(what, iid)
        elif self.isLCC(lc):
            what = self.getSelectedItems()
            if what is not None:
                iid = self.getActiveLid()
                self.parent.viewOpen(what, iid)


    def fwdeventColClick(self, lc, event):
        if self.isLCI(lc):
            colS = event.GetColumn()
            ll = self.getActiveList()
            if ll is not None:
                lid = ll.getUid()
                fields = self.getFields(lid)
                if colS >= 0 and colS < len(fields):
                    iids_org = self.getSelectedIids()
                    resort = ll.setSort(colS)
                    if resort:
                        self.getContentData().updateSort(lid, fields, self.getCDetails())
                        self.loadData(lid, select_iids=iids_org)
        event.Skip()
                

    def fwdeventCheckItem(self, lc, event):
        if self.isLCI(lc) and self.isActive():
            if type(event) is int:
                pos = event
            else:
                pos = event.GetIndex()
            iid = self.getContentData().getIidForLidPos(self.getActiveLid(), pos)
            self.parent.OnActContent("FlipEnabled", more_info={"iids": [iid]})
            # iid = self.getContentData().getIidForLidPos(self.getActiveLid(), index)
            # if iid is not None:
            #     self.getContentData().getItem(iid).flipEnabled()
            #     self.getLCI().RefreshItem(index)

    def fwdeventSelect(self, lc, event):
        if self.isLCC(lc) and self.isActive():
            pos = event.GetIndex()
            lid = self.getContentData().getLidForPos(pos)
            if lid is not None and lid != self.getActiveLid():
                self.changedLid(lid)
        
    def manageDrag(self, lc, trg_where, text):
        if not self.hasContentData():
            return
        src_lid = self.getActiveLid() 
        sel = sorted(map(int, text.split(',')))
        if len(sel) == 0:
            return
        trg_pos = None
        if self.isLCC(lc):
            if trg_where['index'] != -1:
                trg_lid = self.getContentData().getLidForPos(trg_where['index'])
                if trg_lid != src_lid:
                    trg_pos = -1
        elif self.isLCI(lc):
            trg_lid = src_lid
            trg_pos = trg_where['index']
            if trg_where['after'] and trg_pos != -1:
                trg_pos += 1
        if trg_pos is not None:
            iids = [self.getContentData().getIidForLidPos(src_lid, pos) for pos in sel]
            self.parent.dw.moveIids(tab_type=self.tabType, src_lid=src_lid, iids=iids, trg_lid=trg_lid, trg_pos=trg_pos)
            self.parent.refresh()
        
    def editedName(self, lc, pos, name): pass
    ########## HANDLING ACTIONS END

class FindContentTable(ContentTable):
    #### FIND FUNCTIONS

    def __init__(self, parent, tabId, tabType, frame, short=None, single=False, detached_handle=None, activate=True):
        ContentTable.__init__(self, parent, tabId, tabType, frame, short, single, detached_handle, activate)
        self.matching = []
        self.curr_match = None
        self.prev_sels = None
    

    def getNamesList(self):
        if self.hasContentData():
            lid = self.getActiveLid()
            details = {"aim": "list"}
            return [(x, self.getItemFieldV(iid, self.getNameF(), details)) for x,iid in enumerate(self.getContentData().getIidsList(lid))]
        return []

    def updateFind(self, matching=None, non_matching=None, cid=None):
        if matching is not None:
            if self.curr_match is not None and self.curr_match >= 0 and self.curr_match < len(self.matching): 
                self.getLCI().setUnfoundRow(self.matching[self.curr_match])
            self.curr_match = None
            self.matching = matching
        
        if matching is None or len(matching) > 0:
            self.getNextMatch()
            if self.curr_match is None or self.curr_match == -1:
                if self.prev_sels is None:
                    self.prev_sels = self.getLCI().clearSelection()
                self.getLCI().setSelection(self.matching)
            elif self.curr_match == 0:
                self.getLCI().clearSelection()
            if self.curr_match is not None and self.curr_match >= 0:
                self.getLCI().setFoundRow(self.matching[self.curr_match])
                if self.matching[self.curr_match-1] != self.matching[self.curr_match]:
                    self.getLCI().setUnfoundRow(self.matching[self.curr_match-1])
        elif len(matching) == 0:
            self.prev_sels = self.getLCI().clearSelection()
            
    def getNextMatch(self, n=None):
        if len(self.matching) > 0:
            if self.curr_match is None:
                self.curr_match = -1
            else:
                self.curr_match += 1
                if self.curr_match == len(self.matching):
                    self.curr_match = 0

    def quitFind(self, matching=None, non_matching=None, cid=None):
        if self.curr_match is not None and self.curr_match >=0 and self.curr_match < len(self.matching):
            self.getLCI().setUnfoundRow(self.matching[self.curr_match])
        if self.prev_sels is not None and self.curr_match != -1:
            self.getLCI().setSelection(self.prev_sels)
        self.prev_sels = None

        
class VarsTable(FindContentTable):
    
    str_item = 'item'
    ###################### FIELDS VARS
    FIRST_FIELDS = [('', str_item+'.getSortAble', None, ContentTable.width_colcheck, wx.LIST_FORMAT_LEFT),
                    ('id', str_item+'.getId', None,  ContentTable.width_colid, wx.LIST_FORMAT_LEFT),]
                    # ('name', str_item+'.getName', None, ContentTable.width_colnamew, wx.LIST_FORMAT_LEFT),
                    # ('type', str_item+'.getType', None, ContentTable.width_colinfow, wx.LIST_FORMAT_LEFT)] #,
    LAST_FIELDS = []
    # fields_miss = [('missing', str_item+'.getMissInfo', None, ContentTable.width_colinfo, wx.LIST_FORMAT_RIGHT)]
    # fields_var = {1: [('density', str_item+'.getDensity', None, ContentTable.width_colinfo, wx.LIST_FORMAT_RIGHT)],
    #               2:[('categories', str_item+'.getCategories', None, ContentTable.width_colinfo, wx.LIST_FORMAT_RIGHT)],
    #               3:[('min', str_item+'.getMin', None, ContentTable.width_colinfo, wx.LIST_FORMAT_RIGHT),
    #                  ('max', str_item+'.getMax', None, ContentTable.width_colinfo, wx.LIST_FORMAT_RIGHT)]}

    name_m = str_item+'.getName'
    check_m = str_item+'.getEnabled'

    def getContentData(self):
        if self.parent.dw is not None:
            return self.parent.dw.getData()
        
    def manageDrag(self, lc, trg_where, text): pass
        
    def getFieldsList(self):
        tmp = []
        rp = self.getCDetail("rp")
        if rp is not None and self.parent.hasDataLoaded():
            modifiers = rp.getModifiersForData(self.parent.dw.getData())
            var_list = [(iid, self.getContentData().getItem(iid)) for iid in self.getContentData().getIidsList(self.getActiveLid())]
            modifiers = rp.updateModifiers(var_list, modifiers)
            for fk in rp.getCurrentListFields("gui", modifiers):
                lbl = rp.getFieldLbl(fk, style="gui")
                fmt = rp.getFieldFmt(fk)
                align = wx.LIST_FORMAT_LEFT
                width = ContentTable.width_colinfo
                if re.search("f$", fmt.get("fmt", "")):
                    align = wx.LIST_FORMAT_RIGHT
                if re.search("name", lbl):
                    width = ContentTable.width_colnamew
                tmp.append((lbl, self.str_item+".getEValGUI", {"k": fk}, width, align))
        return tmp
        
        
    def resetFields(self):
        self.fields = []        
        if self.hasContentData() and self.getActiveLid() is not None:
            self.fields.extend(self.FIRST_FIELDS)
            # if self.getContentData().hasMissing():
            #     self.fields.extend(self.fields_miss)
            # for tyid in self.getContentData().getAllTypes(self.getActiveLid()):
            #     self.fields.extend(self.fields_var[tyid])
                
            self.setCDetail("rp", ColM.getRP())
            self.fields.extend(self.getFieldsList())

            self.fields.extend(self.LAST_FIELDS)

        
class RedsTable(FindContentTable):
            
    str_item = 'item'

    FIRST_FIELDS = [('', str_item+'.getSortAble', None, ContentTable.width_colcheck, wx.LIST_FORMAT_LEFT),
                    ('id', str_item+'.getShortId', None, ContentTable.width_colid, wx.LIST_FORMAT_LEFT)] #,
                    # ('query LHS', str_item+'.getQueryLU', None, ContentTable.width_colnamew, wx.LIST_FORMAT_LEFT),
                    # ('query RHS', str_item+'.getQueryRU', None, ContentTable.width_colnamew, wx.LIST_FORMAT_LEFT)]
    LAST_FIELDS = [] #('track', str_item+'.getTrack', None, ContentTable.width_colinfo, wx.LIST_FORMAT_LEFT)]
    # LAST_FIELDS = [('cohesion', str_item+'.getCohesion', None, ContentTable.width_colinfo, wx.LIST_FORMAT_RIGHT),
    #                ('cohesionN', str_item+'.getCohesionNat', None, ContentTable.width_colinfo, wx.LIST_FORMAT_RIGHT)]
    
    name_m = str_item+'.getQueriesU'
    check_m = str_item+'.getEnabled'

    def getContentData(self):
        if self.parent.dw is not None:
            return self.parent.dw.reds
    
    def withListIcons(self):
        return True

    def getFieldsList(self):
        tmp = []
        rp = self.getCDetail("rp")
        if rp is not None and self.parent.hasDataLoaded():
            modifiers = rp.getModifiersForData(self.parent.dw.getData())
            for fk in rp.getCurrentListFields("gui", modifiers):
                lbl = rp.getFieldLbl(fk, style="gui")
                fmt = rp.getFieldFmt(fk)
                align = wx.LIST_FORMAT_RIGHT
                width = ContentTable.width_colinfo
                if re.search("s$", fmt.get("fmt", "")):
                    align = wx.LIST_FORMAT_LEFT
                if re.search("query", lbl):
                    width = ContentTable.width_colnamew
                tmp.append((lbl, self.str_item+".getEValGUI", {"k": fk}, width, align))
        return self.FIRST_FIELDS + tmp + self.LAST_FIELDS        
        
    def resetFields(self):
        self.setCDetail("rp", Redescription.getRP())
        self.fields = self.getFieldsList()
