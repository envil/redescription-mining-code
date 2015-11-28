import wx, wx.grid, re, colorsys, random, datetime, math
from ..reremi.toolICList import ICList
from ..reremi.classQuery import SYM, Query, Literal
from ..reremi.classRedescription import Redescription

import pdb

def getRGB(h,l, s):
    Brgb = map(int, [255*v for v in colorsys.hls_to_rgb(h, l, s)])
    if l > 0.5:
        Frgb = map(int, [255*v for v in colorsys.hls_to_rgb(h, 0, s)])
    else:
        Frgb = map(int, [255*v for v in colorsys.hls_to_rgb(h, 1, s)])
    return Brgb, Frgb


class CustRenderer(wx.grid.PyGridCellRenderer):

    BACKGROUND = wx.Colour(100,100,100)
    TEXT = wx.Colour(100,100,100)
    SBRUSH = wx.SOLID
    
    BACKGROUND_SELECTED = wx.Colour(100,100,100)
    TEXT_SELECTED = wx.Colour(100,100,100)
    SBRUSH_SELECTED = wx.SOLID

    BACKGROUND_GREY = wx.Colour(240,255,240)
    TEXT_GREY = wx.Colour(131,139,131)
    SBRUSH_GREY = wx.SOLID

    MAP_SORT_NAN = {float('Nan'): None}
    
    """Base class for editors"""

    ### Customisation points
    def Draw(self, grid, attr, dc, rect, row, col, isSelected):
        """Customisation Point: Draw the data from grid in the rectangle with attributes using the dc"""

        dc.SetClippingRegion( rect.x, rect.y, rect.width, rect.height )
        back, fore, bstyle = self.BACKGROUND, self.TEXT, self.SBRUSH
        value = grid.GetCellValue( row, col )
        
        if row in grid.GetSelectedRows():
            back, fore, bstyle = self.BACKGROUND_SELECTED, self.TEXT_SELECTED, self.SBRUSH_SELECTED
        elif grid.GetTable().getEnabled(row) == 0:
            back, fore, bstyle = self.BACKGROUND_GREY, self.TEXT_GREY, self.SBRUSH_GREY
        try:
            dc.SetTextForeground( fore )
            dc.SetTextBackground( back)
            dc.SetBrush( wx.Brush( back, bstyle) )
            dc.SetPen(wx.TRANSPARENT_PEN)
            dc.DrawRectangle( rect.x, rect.y, rect.width, rect.height )
            dc.SetFont( wx.NORMAL_FONT )
            dc.DrawText( value, rect.x+2,rect.y+2 )
        finally:
            dc.SetTextForeground( self.TEXT)
            dc.SetTextBackground( self.BACKGROUND)
            dc.SetPen( wx.NullPen )
            dc.SetBrush( wx.NullBrush )
            dc.DestroyClippingRegion( )

    # def GetBestSize(self, grid, attr, dc, row, col):
    #     """Customisation Point: Determine the appropriate (best) size for the control, return as wxSize
    #     Note: You _must_ return a wxSize object.  Returning a two-value-tuple
    #     won't raise an error, but the value won't be respected by wxPython.
    #     """         
    #     x,y = dc.GetTextExtent( "%s" % grid.GetCellValue( row, col ) )
    #     # note that the two-tuple returned by GetTextExtent won't work,
    #     # need to give a wxSize object back!
    #     return wx.Size( min(x, 10), min(y, 10))


class ColorRenderer(CustRenderer):

    ### Customisation points
    def Draw(self, grid, attr, dc, rect, row, col, isSelected):
        """Customisation Point: Draw the data from grid in the rectangle with attributes using the dc"""

        dc.SetClippingRegion( rect.x, rect.y, rect.width, rect.height )
        back, fore, bstyle = self.BACKGROUND, self.TEXT, self.SBRUSH
        value = grid.GetCellValue( row, col )
        
        tmp = re.match("^#h(?P<h>[0-9]*)l(?P<l>[0-9]*)#(?P<val>.*)$", value)
        if tmp is not None:
            s = 1
            if row in grid.GetSelectedRows(): s=0.5
            elif grid.GetTable().getEnabled(row) == 0: s= 0.2 
            rgb_back, rgb_fore = getRGB(int(tmp.group("h"))/255.0, int(tmp.group("l"))/255.0, s)
            back, fore, bstyle = wx.Colour(*rgb_back), wx.Colour(*rgb_fore), self.SBRUSH
            value = tmp.group("val")
        elif row in grid.GetSelectedRows():
            back, fore, bstyle = self.BACKGROUND_SELECTED, self.TEXT_SELECTED, self.SBRUSH_SELECTED
        elif grid.GetTable().getEnabled(row) == 0:
            back, fore, bstyle = self.BACKGROUND_GREY, self.TEXT_GREY, self.SBRUSH_GREY
        try:
            dc.SetTextForeground( fore )
            dc.SetTextBackground( back)
            dc.SetBrush( wx.Brush( back, bstyle) )
            dc.SetPen(wx.TRANSPARENT_PEN)
            dc.DrawRectangle( rect.x, rect.y, rect.width, rect.height )
            dc.SetFont( wx.NORMAL_FONT )
            dc.DrawText( value, rect.x+2,rect.y+2 )
        finally:
            dc.SetTextForeground( self.TEXT)
            dc.SetTextBackground( self.BACKGROUND)
            dc.SetPen( wx.NullPen )
            dc.SetBrush( wx.NullBrush )
            dc.DestroyClippingRegion( )

    # def GetBestSize(self, grid, attr, dc, row, col):
    #     """Customisation Point: Determine the appropriate (best) size for the control, return as wxSize
    #     Note: You _must_ return a wxSize object.  Returning a two-value-tuple
    #     won't raise an error, but the value won't be respected by wxPython.
    #     """         
    #     x,y = dc.GetTextExtent( "%s" % grid.GetCellValue( row, col ) )
    #     # note that the two-tuple returned by GetTextExtent won't work,
    #     # need to give a wxSize object back!
    #     return wx.Size( min(x, 10), min(y, 10))


class GridTable(wx.grid.PyGridTableBase):

    fields_def = []
    renderer = CustRenderer
    name_m = None

    #### COLUMN WIDTHS
    width_colcheck = 25
    width_colid = 50
    width_colname = 150
    width_colnamew = 300
    width_colinfo = 80
    width_colinfow = 100
    width_colinfon = 8


    def __init__(self, parent, tabId, frame, short=None):
        wx.grid.PyGridTableBase.__init__(self)
        self.details = {}
        self.short = short
        self.sc = set()
        self.fvc = 0
        self.parent = parent
        self.tabId = tabId
        self.fields = self.fields_def
        self.data = ICList()
        self.sortids = ICList()
        self.sortP = (None, False)
        self.currentRows = self.nbItems()
        self.currentColumns = len(self.fields)
        self.matching = []
        
        #### GRID
        self.grid = wx.grid.Grid(frame)
        self.grid.SetTable(self)
        self.setSelectedRow(0)
        self.grid.EnableEditing(False)
        #self.grid.AutoSizeColumns(True)

        self.grid.RegisterDataType(wx.grid.GRID_VALUE_STRING,
                                   self.renderer(),
                                   wx.grid.GridCellAutoWrapStringEditor())

        self.grid.RegisterDataType(wx.grid.GRID_VALUE_BOOL,
                              wx.grid.GridCellBoolRenderer(),
                              wx.grid.GridCellBoolEditor()) 

        # attr = wx.grid.GridCellAttr()
        # attr.SetEditor(wx.grid.GridCellBoolEditor())
        # attr.SetRenderer(wx.grid.GridCellBoolRenderer())
        # self.grid.SetColAttr(0,attr)

        self.grid.Bind(wx.EVT_KEY_UP, self.OnKU)
        self.grid.Bind(wx.grid.EVT_GRID_LABEL_LEFT_CLICK, self.setSort)
        self.grid.Bind(wx.grid.EVT_GRID_LABEL_RIGHT_CLICK, self.setFocus)
        self.grid.Bind(wx.grid.EVT_GRID_CELL_LEFT_DCLICK, self.OnViewData)
        self.grid.Bind(wx.grid.EVT_GRID_CELL_RIGHT_CLICK, self.OnRightClick)
        self.grid.Bind(wx.grid.EVT_GRID_CELL_LEFT_CLICK, self.OnMouse)
        
    # def showPopupMenu(self, event):
    #     self.table.highlightRow(event.GetRow())
    #     parent.currentList = self

    def GetCellBackgroundColor(self, row, col):
        """Return the value of a cell"""
        return wx.Colour(100,100,100)

    def Hide(self):
        self.grid.Hide()

    def Show(self):
        self.grid.Show()

    ### GRID METHOD
    def GetNumberRows(self):
        """Return the number of rows in the grid"""
        return self.nbItems()

    ### GRID METHOD
    def GetColLabelValue(self, col):
        """Return the number of rows in the grid"""
        direct = '  '
        if col == self.sortP[0]:
            if self.sortP[1]:
                direct = SYM.SYM_ARRTOP
            else:
                direct = SYM.SYM_ARRBOT
        return "  %s %s" % (self.fields[col][0], direct)

    ### GRID METHOD
    def GetNumberCols(self):
        """Return the number of columns in the grid"""
        return len(self.fields)

    ### GRID METHOD
    def IsEmptyCell(self, row, col):
        """Return True if the cell is empty"""
        return self.GetValue(row, col) is None

    ### GRID METHOD
    def GetTypeName(self, row, col):
        """Return the name of the data type of the value in the cell"""
        if (col == 0):
            return wx.grid.GRID_VALUE_BOOL
        else:
            return wx.grid.GRID_VALUE_STRING
        # if row < len(self.sortids) and col < len(self.fields):
        #     return self.getFieldV(self.sortids[row], self.fields[col], dict(self.details))
        # else:
        #     return None

    def getFieldV(self, x, field, details):
        self.fvc += 1
        methode = eval(field[1])
        if callable(methode):
            if len(field) > 2 and field[2] is not None:
                details.update(field[2])
            try:
                return methode(details)
            except IndexError:
                methode(details)
        else:
            return methode

    ### GRID METHOD
    def GetValue(self, row, col):
        """Return the value of a cell"""
        if row < self.nbItems() and col < len(self.fields):
            details = {"aim": "list"}
            details.update(self.details)
            return "%s" % self.getFieldV(self.sortids[row], self.fields[col], details)
        else:
            return None

    ### GRID METHOD
    def SetValue(self, row, col, value):
        pass

    def getNamesList(self):
        """Return the value of a cell"""
        names_list = []
        details = {"aim": "list"}
        details.update(self.details)
        if self.name_m is not None:
            for x in self.sortids:
                v = "%s" % self.getFieldV(x, (0, self.name_m), details)
                names_list.append((x,v))
        return names_list

    def nbItems(self):
        return len(self.sortids)

    def getItemAtRow(self, row):
        """Return the data of a row"""
        if row < self.nbItems() and self.sortids[row] < len(self.data):
            return self.data[self.sortids[row]]
        else:
            return None

    def getRowForItem(self, rid):
        """Return the row of an entry"""
        try:
            return self.sortids.index(rid)
        except:
            return None

    def getPositionFromRow(self, row):
        if row is not None and row < self.nbItems() and self.sortids[row] < len(self.data):
            return self.sortids[row]
        else:
            return None

    def getRowFromPosition(self, pos):
        try:
            return self.sortids.index(pos)
        except:
            return None

    def resetSizes(self):
        self.GetView().AutoSize()
        for coli, f in enumerate(self.fields):
            if len(f) > 3:
                self.GetView().SetColSize(coli, f[3])

    def resetDetails(self, details={}, review=True):
        self.sortP = (None, False)
        self.details = details
        if review:
            self.ResetView()
            self.resetSizes()
            
    def resetData(self, data, srids=None):
        self.data = data
        
        if srids is not None:
            self.sortids = srids
        else:
            self.sortids = ICList([idi for idi in range(len(self.data))], True)

        self.resetFields()
        self.updateSort()
        self.ResetView()
        self.resetSizes()

    def resetFields(self, dw=None, review=True):
        self.sortP = (None, False)

    def getEnabled(self, row):
        return self.getItemAtRow(row).getEnabled()

    def notify_change(self):
        if type(self.data) == ICList:
            self.data.isChanged = True

    def flipEnabled(self, row):
        self.data[self.sortids[row]].flipEnabled()
        self.notify_change()
        self.ResetView()

    def flipAllEnabled(self, dids=None):
        if dids is None:
            dids = range(len(self.data))
        for did in dids:
            self.data[did].flipEnabled()
        self.notify_change()
        self.ResetView()

    def setAllDisabled(self, dids=None):
        if dids is None:
            dids = range(len(self.data))
        for did in dids:
            self.data[did].setDisabled()
        self.notify_change()
        self.ResetView()

    def setAllEnabled(self, dids=None):
        if dids is None:
            dids = range(len(self.data))
        for did in dids:
            self.data[did].setEnabled()
        self.notify_change()
        self.ResetView()

    def OnMouse(self,event):
        if event.GetRow() < self.nbItems():
            self.setSelectedRow(event.GetRow(), event.GetCol())
            if event.Col == 0:
                self.flipEnabled(event.GetRow())                
       
    def ResetView(self):
        """Trim/extend the control's rows and update all values"""
        self.GetView().BeginBatch()
        for current, new, delmsg, addmsg in [
                (self.currentRows, self.GetNumberRows(), wx.grid.GRIDTABLE_NOTIFY_ROWS_DELETED, wx.grid.GRIDTABLE_NOTIFY_ROWS_APPENDED),
                (self.currentColumns, self.GetNumberCols(), wx.grid.GRIDTABLE_NOTIFY_COLS_DELETED, wx.grid.GRIDTABLE_NOTIFY_COLS_APPENDED),
        ]:
            if new < current:
                msg = wx.grid.GridTableMessage(
                        self,
                        delmsg,
                        new,    # position
                        current-new,
                )
                self.GetView().ProcessTableMessage(msg)
            elif new > current:
                msg = wx.grid.GridTableMessage(
                        self,
                        addmsg,
                        new-current
                )
                self.GetView().ProcessTableMessage(msg)
        self.GetView().EndBatch()
        self.currentRows = self.nbItems()
        self.currentColumns = len(self.fields)

        if self.getSelectedRow() is not None and not self.grid.IsVisible(self.getSelectedRow(), 0):
            self.grid.MakeCellVisible(self.getSelectedRow(), 0)

    def deleteDisabled(self):
        pass

    def getSelectedItem(self):
        if self.getSelectedRow() is not None:
            return self.getItemAtRow(self.getSelectedRow())
        return

    def getSelectedPos(self):
        if self.getSelectedRow() is not None:
            return self.getPositionFromRow(self.getSelectedRow())
        return
    
    def getSelectedRow(self):
        if len(self.GetView().GetSelectedRows()) > 0:
            return self.GetView().GetSelectedRows()[0]
        else:
            return None

    def getSelectedCol(self):
        return max(0,self.GetView().GetGridCursorCol())

    def setSelectedRow(self, row, col=0):
        if row is None: row = 0
        if col is None: col = 0
        self.GetView().SetGridCursor(row,col)
        self.GetView().SelectRow(row)
        
    def neutraliseSort(self):
        self.sortP = (None, False)

    def setSort(self, event):
        colS = event.GetCol()
        if colS == -1:
            pass ### TODO select all
        else:
            old = self.sortP[0]
            if self.sortP[0] == colS:
                self.sortP = (self.sortP[0], not self.sortP[1])
            else:
                self.sortP = (colS, True)
            self.updateSort()
            self.ResetView()

    def setFocus(self, event):
        pass
        
    def updateSort(self):
        selected_row = self.getSelectedRow()
        selected_col = self.getSelectedCol()
        selected_id = None
        if selected_row is not None:
            selected_id = self.getPositionFromRow(selected_row)

        if self.sortP[0] is not None:
            details = {"aim": "sort"}
            details.update(self.details)
            self.sortids.sort(key= lambda x: self.getFieldV(x, self.fields[self.sortP[0]], details), reverse=self.sortP[1])
        if selected_id is not None:
            self.setSelectedRow(self.getRowFromPosition(selected_id), selected_col)

    def updateFindO(self, matching, non_matching, cid=None):
        if len(matching) > 0:
            self.sortP = (None, False)
            selected_col = self.getSelectedCol()
            self.sortids = matching+non_matching
            self.matching = matching
            self.setSelectedRow(len(matching)-1, selected_col)
            self.ResetView()

    def updateFind(self, matching=None, non_matching=None, cid=None):
        if matching is not None:
            self.matching = matching
        if matching is None or len(matching) > 0:
            self.setSelectedRow(self.getNextMatch(cid), self.getSelectedCol())
            self.ResetView()

    def getNextMatch(self, n=None):
        if n is None:
            n = self.getSelectedRow()
        
        if len(self.matching) > 0:
            if n >= self.getRowForItem(self.matching[-1]):
                return self.getRowForItem(self.matching[0])
            else:
                for si in range(len(self.matching)):
                    if self.getRowForItem(self.matching[si]) > n:
                        return self.getRowForItem(self.matching[si])
        else:
            n += 1
            if n == self.nbItems():
                n = 0
            return n
            
    def OnRightClick(self, event):
        if event.GetRow() < self.nbItems():
            self.setSelectedRow(event.GetRow(), event.GetCol())
            self.parent.makePopupMenu(self.parent.toolFrame)

    def OnKU(self, event):
        if self.grid.GetGridCursorRow() < self.nbItems():
            self.setSelectedRow(self.grid.GetGridCursorRow(), self.grid.GetGridCursorCol())
        event.Skip()

    def OnViewData(self, event):
        if event.GetRow() < self.nbItems():
            self.setSelectedRow(event.GetRow(), event.GetCol())
            self.viewData(self.parent.getDefaultViewT(self.tabId))

class RedTable(GridTable):

    fields_sizes = []
    fields_def_nosplit = [('', 'self.data[x].getEnabled'),
                          ('id', 'self.getRedIdStr(x)', None, 60),
                          ('query LHS', 'self.data[x].getQueryLU', None, 300),
                          ('query RHS', 'self.data[x].getQueryRU', None, 300),
                          ('J', 'self.data[x].getRoundAcc', None, 60),
                          ('p-value', 'self.data[x].getRoundPVal', None, 60),
                          ('|E'+SYM.SYM_GAMMA+'|', 'self.data[x].getLenI', None, 60),
                          ('track', 'self.data[x].getTrack', None, 80)]

    fields_def_splits = [('', 'self.data[x].getEnabled'),
                         ('id', 'self.getRedIdStr(x)', None, 60),
                         ('query LHS', 'self.data[x].getQueryLU', None, 300),
                         ('query RHS', 'self.data[x].getQueryRU', None, 300),
                         (SYM.SYM_RATIO+'J', 'self.data[x].getRoundAccRatio', {"rset_id_num": "test", "rset_id_den": "learn"}, 60),
                         (SYM.SYM_LEARN+'J', 'self.data[x].getRoundAcc', {"rset_id": "learn"}, 60),
                         (SYM.SYM_TEST+'J', 'self.data[x].getRoundAcc', {"rset_id": "test"}, 60),
                         (SYM.SYM_LEARN+'pV', 'self.data[x].getRoundPVal', {"rset_id": "learn"}, 60),
                         (SYM.SYM_TEST+'pV', 'self.data[x].getRoundPVal', {"rset_id": "test"}, 60),
                         (SYM.SYM_LEARN+'|E'+SYM.SYM_GAMMA+'|', 'self.data[x].getLenI', {"rset_id": "learn"}, 60),
                         (SYM.SYM_TEST+'|E'+SYM.SYM_GAMMA+'|', 'self.data[x].getLenI', {"rset_id": "test"}, 60),
                         ('track', 'self.data[x].getTrack', None, 80)]
    fields_def = fields_def_nosplit
    #fields_def = fields_def_splits
    name_m = 'self.data[x].getQueriesU'

    def __init__(self, parent, tabId, frame, short=None):
        GridTable.__init__(self, parent, tabId, frame, short)
        self.rids = []
        self.last_rid = 0
        self.opened_edits = {}
        self.emphasized = {}
        if self.parent.hasDataLoaded() and self.parent.dw.getData().hasLT():
            self.fields = self.fields_def_splits
        else:
            self.fields = self.fields_def_nosplit
        self.uptodate = True

    def setSelectedRow(self,row, col=0):
        self.GetView().SetGridCursor(row,0)
        self.GetView().SelectRow(row)
        self.parent.updateMenus()

    def resetData(self, data, srids=None):
        GridTable.resetData(self, data, srids)
        self.rids = [i+1 for i in range(len(self.data))]
        self.last_rid = len(self.data)
        
    def ResetView(self):
        self.refreshRestrict()
        GridTable.ResetView(self)

    def refreshRestrict(self):
        if self.uptodate:
            return
        tic = datetime.datetime.now()
        for red in self.data:
            red.setRestrictedSupp(self.parent.dw.getData())
        #print "Done restrict support ", self.tabId, len(self.data), datetime.datetime.now() - tic
        self.uptodate = True

    def refreshComp(self):
        if self.uptodate:
            return
        tic = datetime.datetime.now()
        for red in self.data:
            red.recompute(self.parent.dw.getData())
        #print "Done restrict support ", self.tabId, len(self.data), datetime.datetime.now() - tic
        self.uptodate = True


    def recomputeAll(self, restrict):
        self.uptodate = False
        # self.refreshRestrict()
        self.refreshComp()
        for k,v in self.opened_edits.items():
            mc = self.parent.accessViewX(k)
            if mc is not None:
                mc.refresh()
        if self.parent.hasDataLoaded() and self.parent.dw.getData().hasLT():
            self.fields = self.fields_def_splits
        else:
            self.fields = self.fields_def_nosplit
        self.ResetView()

    def insertItems(self, items):
        for item in items:
            self.insertItem(item, None, False)
        self.neutraliseSort()
        self.ResetView()

    def insertItem(self, item, row=None, upView=True):
        if row is None or row >= len(self.sortids):
            row_inserted = len(self.data)
            self.sortids.append(len(self.data))
        else:
            row_inserted = row+1
            self.sortids.insert(row+1, len(self.data))
        self.last_rid += 1
        self.rids.append(self.last_rid)
        self.data.append(item)
        if upView:
            self.neutraliseSort()
            self.ResetView()
        return row_inserted

    def deleteItem(self, pos, upView=True):
        upMenu = False
        row = self.getRowFromPosition(pos)
        if row is not None:
            self.sortids.pop(row)
            for i in range(len(self.sortids)):
                self.sortids[i] -= (self.sortids[i] > pos)
                i+=1
            #### TODO BUG MOVE
            ### TODO destruct the associated mapView if any?? 
            ### TODO add possibility to undo delete here
            self.rids.pop(pos)
            self.data.pop(pos)
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
            if upView:
                self.ResetView()
            if upMenu:
                self.parent.updateMenus()

    def getSelectedQueries(self):
        if self.getSelectedRow() is not None:
            red = self.getItemAtRow(self.getSelectedRow())
            if isinstance(red, Redescription):
                return red.getQueries()
        return

    def getRedId(self, pos):
        if pos is None:
            return (None, None)
        if pos < len(self.rids):
            return (self.short, self.rids[pos])
        return (self.short, None)

    def getRedIdStr(self, pos):
        try:
            tsh, rid = self.getRedId(pos)
        except TypeError:
            print "Error getRedIdStr", pos
            pdb.set_trace()
        if rid is None: rid = "?"
        if tsh is None: tsh = "?"
        return "%s%s" % (tsh, rid)
                
    def getRedIdOID(self, oid):
        # if oid not in self.opened_edits:
        #     pdb.set_trace()
        return self.getRedIdStr(self.opened_edits.get(oid, None))

    def viewData(self, viewT, pos=None, oid=None):
        if oid is not None:
            if oid in self.opened_edits:
                pos = self.opened_edits[oid]
        if pos is None:
            pos = self.getSelectedPos()
        vid = None
        for (k,v) in self.opened_edits.items():
            if v == pos and viewT == k[0]:
                vid = k[1]
                break
            
        mapV = self.parent.getViewX(vid, viewT)
        if vid is None and mapV is not None:
            self.registerView(mapV.getId(), pos, upMenu=False)
            mapV.setCurrent(self.getItemAtRow(self.getRowFromPosition(pos)), self.tabId)
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

            
    def updateEdit(self, edit_key, red, toed=None):
        if edit_key in self.opened_edits.keys():
            toed = self.opened_edits[edit_key]
        if toed is not None and toed >= 0 and toed < len(self.data):
            if self.tabId != "hist":
                self.data[toed] = red

                for k,v in self.opened_edits.items():
                    if v == toed and k != edit_key:
                        mc = self.parent.accessViewX(k)
                        if mc is not None:
                            mc.setCurrent(red, self.tabId)

            else:
                old_toed = toed
                new_toed = len(self.data)
                row_inserted = self.insertItem(red, -1)
                if edit_key is None: ## edit comes from the tab itself, not from a view
                    self.setSelectedRow(row_inserted)
            
                for k,v in self.opened_edits.items():
                    if v == old_toed:
                        self.opened_edits[k] = new_toed 
                        mc = self.parent.accessViewX(k)
                        if mc is not None:
                            mc.updateTitle()
                            if k != edit_key:
                                mc.setCurrent(red, self.tabId)

                if old_toed in self.emphasized and edit_key in self.opened_edits:
                    self.emphasized[self.opened_edits[edit_key]] = self.emphasized[old_toed]
                    del self.emphasized[old_toed]

                self.parent.updateMenus()
            self.ResetView()
        ### TODO else insert (e.g. created from variable)

    def getViewsCount(self, edit_key):
        count = 0
        if edit_key in self.opened_edits.keys():
            toed = self.opened_edits[edit_key]
        if toed is not None and toed >= 0 and toed < len(self.data):
            for k,v in self.opened_edits.items():
                if v == toed: # and k != edit_key:
                    count += 1
        return count

    def addAndViewTop(self, queries, viewT):
        mapV = self.parent.getViewX(None, viewT)
        red = mapV.setCurrent(queries)
        self.registerView(mapV.getId(), len(self.data)-1, upMenu=False)
        mapV.setSource(self.tabId)
        self.parent.updateMenus()
        mapV.updateTitle()

    def doFlipEmphasizedR(self, edit_key):
        if edit_key in self.opened_edits.keys() and self.opened_edits[edit_key] in self.emphasized:
            self.parent.flipRowsEnabled(self.emphasized[self.opened_edits[edit_key]])
            self.setEmphasizedR(edit_key, self.emphasized[self.opened_edits[edit_key]])

    def getEmphasizedR(self, edit_key):
        if edit_key in self.opened_edits.keys() \
               and self.opened_edits[edit_key] >= 0 and self.opened_edits[edit_key] < len(self.data) \
               and self.opened_edits[edit_key] in self.emphasized:
            return self.emphasized[self.opened_edits[edit_key]]
        return set()

    def setAllEmphasizedR(self, lids=None, show_info=False, no_off=False):
        for edit_key in self.opened_edits.keys():
            self.setEmphasizedR(edit_key, lids, show_info, no_off)

    def setEmphasizedR(self, edit_key, lids=None, show_info=False, no_off=False):
        if edit_key in self.opened_edits.keys() \
               and self.opened_edits[edit_key] >= 0 and self.opened_edits[edit_key] < len(self.data):

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
                    mm = self.parent.accessViewX(k)
                    mm.emphasizeOnOff(turn_on=turn_on, turn_off=turn_off)
            
            if len(turn_on) == 1 and show_info:
                for lid in turn_on:
                    self.parent.showDetailsBox(lid, self.data[toed])

    def deleteDisabled(self):
        i = 0
        while i < len(self.data):
            if not self.data[i].getEnabled():
                self.deleteItem(i, False)
            else:
                i+=1
        self.ResetView()

    def moveEnabled(self, dest):
        #### HERE NOW
        reds = []
        i = 0
        while i < len(self.data):
            if self.data[i].getEnabled():
                reds.append(self.data[i])
                self.deleteItem(i, False)
            else:
                i+=1
        if len(reds) > 0:
            dest.insertItems(reds)
            self.ResetView()

    def copyItem(self, row):
        pos = self.getPositionFromRow(row)
        if pos is not None:
            self.parent.buffer_copy = self.data[pos].copy()

    def cutItem(self, row):
        pos = self.getPositionFromRow(row)
        if pos is not None:
            self.parent.buffer_copy = self.data[pos].copy()
            self.deleteItem(pos)

    def pasteItem(self, row = None):
        if self.parent.buffer_copy is not None:
            row_inserted = self.insertItem(self.parent.buffer_copy, row)
            self.setSelectedRow(row_inserted)
            self.parent.buffer_copy = None
            
    def filterToOne(self, parameters):
        if self.getSelectedRow() < self.nbItems(): 
            compare_ids = self.sortids[self.getSelectedRow():]
            disable_ids = self.data.filtertofirstIds(compare_ids, parameters, complement=True)
            self.data.applyFunctTo(".setDisabled()", disable_ids, changes= True)
            self.ResetView()

    def filterAll(self, parameters):
        all_ids = list(self.sortids)
        disable_ids = self.data.filterpairsIds(all_ids, parameters, complement=True)
        self.data.applyFunctTo(".setDisabled()", disable_ids, changes= True)
        self.ResetView()

    def processAll(self, actions_parameters, init_current=True):
        selected_row = self.getSelectedRow()
        selected_id = None
        if selected_row is not None:
            selected_id = self.getPositionFromRow(selected_row)


        current_ids = None
        if init_current:
            current_ids = [i for i in self.sortids if self.data[i].getEnabled()]
            
        selected_ids = self.data.selected(actions_parameters, current_ids)
        top, middle, bottom = [], [], []
        while len(self.sortids)>0:
            i = self.sortids.pop(0)
            if i not in selected_ids:
                if self.data[i].getEnabled():
                    middle.append(i)
                else:
                    bottom.append(i)
        self.data.applyFunctTo(".setDisabled()", middle)
        self.sortids.extend(selected_ids+middle+bottom)

        if selected_id is not None:
            self.setSelectedRow(self.getRowFromPosition(selected_id))

        self.ResetView()


class VarTable(GridTable):     

    fields_def = [('','self.data[x].getEnabled', None, GridTable.width_colcheck),
                  ('id', 'self.data[x].getId', None, GridTable.width_colid),
                  ('name', 'self.data[x].getName', None, GridTable.width_colnamew),
                  ('type', 'self.data[x].getType', None, GridTable.width_colinfow)]
    fields_miss = [('missing', 'self.data[x].getMissInfo', None, GridTable.width_colinfo)]
    fields_var = {1: [('density', 'self.data[x].getDensity', None, GridTable.width_colinfo)],
                  2:[('categories', 'self.data[x].getCategories', None, GridTable.width_colinfo)],
                  3:[('min', 'self.data[x].getMin', None, GridTable.width_colinfo),
                     ('max', 'self.data[x].getMax', None, GridTable.width_colinfo)]}
    name_m = 'self.data[x].getName'

    def viewData(self, viewT, pos=None):
        if pos is None:
            datVar = self.getSelectedItem()
        else:
            datVar = self.getItemAtRow(pos)
        queries = [Query(), Query()]
        queries[datVar.side].extend(-1, Literal(False, datVar.getTerm()))
        self.parent.newRedVHist(queries, viewT)
 
    def updateEdit(self, edit_key, red):
        pass

    def resetFields(self, dw=None, review=True):
        self.sortP = (None, False)
        self.fields = []
        self.fields.extend(self.fields_def)
        if len([r for r in self.data if r.hasMissing()]) > 0:
            self.fields.extend(self.fields_miss)
        for tyid in set([r.typeId() for r in self.data]):
            self.fields.extend(self.fields_var[tyid])


class RowTable(GridTable):     

    fields_def = [('','self.data[x].getEnabled'),
                  ('id', 'self.data[x].getId')]
    name_m = 'self.data[x].getRName'
    renderer = ColorRenderer

    def __init__(self, parent, tabId, frame, short=None):
        GridTable.__init__(self, parent, tabId, frame, short)
        self.fix_col = 0

    def viewData(self, viewT, pos=None):
        queries = [Query(), Query()]
        self.parent.newRedVHist(queries, viewT)
 
    def updateEdit(self, edit_key, red):
        pass

    def resetFields(self, dw=None, review=True):
        self.sortP = (None, False)
        self.fix_col = 2
        if dw is not None:
            self.cols_map = {}
            self.fields = []
            self.fields.extend(self.fields_def)
            if dw.getData().hasRNames():
                self.fields.append(('name', 'self.data[x].getRName'))
                name_m = 'self.data[x].getRName'
                self.fix_col += 1
            for side, sideS in [(0, "LHS"),(1, "RHS")]:
                nb = max(1,len(dw.getDataCols(side))-1.0)
                for ci, col in enumerate(dw.getDataCols(side)):
                    self.cols_map[(side, col.getId())] = len(self.fields)
                    self.fields.append(("%s:%s" % (sideS, col.getName()), 'self.data[x].getValue', {"side":side, "col": col.getId(), "range": col.getRange(), "NA": col.NA, "r":ci/nb}))
            if review:
                self.ResetView()


    ### GRID METHOD
    def GetValue(self, row, col):
        """Return the value of a cell"""
        if row < self.nbItems() and col < len(self.fields):
            details = {"aim": "row"}
            details.update(self.details)
            tmp = self.getFieldV(self.sortids[row], self.fields[col], details)
            details = {"aim": "list"}
            details.update(self.details)
            labl = self.getFieldV(self.sortids[row], self.fields[col], details)
            if col >= self.fix_col:
                h = 125*self.fields[col][2]["side"] + int(100*self.fields[col][2]["r"])
                if tmp == "-" or (math.isnan(tmp) and math.isnan(self.fields[col][2]["NA"])) \
                       or (tmp == self.fields[col][2]["NA"]):
                    l = 255
                else:
                    rangeV = self.fields[col][2]["range"]
                    lr = row/(1.0*self.nbItems())
                    if type(rangeV) is dict:
                        if len(rangeV) > 1:
                            lr = rangeV.get(tmp, 0)/(len(rangeV)-1.0)
                        else:
                            lr = 1
                    elif type(rangeV) is tuple:
                        if rangeV[0] != rangeV[1]:
                            lr = (rangeV[1]-tmp)/(rangeV[1]-rangeV[0])
                        else:
                            lr = 1
                    l = 125*lr+100

                # sc = 1.0*self.fields[col][2]["max"] - self.fields[col][2]["min"]
                # if sc == 0:
                #     lr = 0.5
                # else:
                #     lr = (tmp - self.fields[col][2]["min"])/sc
                if col in self.sc:
                    return "#h%dl%d#%s" % (h,l,labl)
                else:
                    try:
                        return "#h%dl%d#%s" % (h,l,"")
                    except TypeError:
                        print h,l, tmp, self.fields[col][2]["range"], self.fields[col][2]["NA"]
            else:
                return tmp
        else:
            return None

    ### GRID METHOD
    def GetColLabelValue(self, col):
        """Return the column label"""
        if col >= self.fix_col and col not in self.sc:
            name = ""
        else:
            name = " %s " % self.fields[col][0]
        direct = '  '
        if col == self.sortP[0]:
            if self.sortP[1]:
                direct = SYM.SYM_ARRTOP
            else:
                direct = SYM.SYM_ARRBOT
        return name + direct

    def notify_change(self):
        self.parent.recomputeAll()
        
    def resetData(self, data, srids=None):
        self.data = data
        if srids is not None:
            self.sortids = srids
        else:
            self.sortids = ICList([idi for idi in range(len(self.data))], True)
        self.sortP = (None, False)
        self.redraw()

    def resetDetails(self, details={}, review=True):
        self.sortP = (None, False)
        self.details = details
        if review:
            self.redraw()

    def redraw(self, details={}, review=True):
        crow, ccol = self.GetView().GetGridCursorRow(), self.GetView().GetGridCursorCol()
        self.ResetView()
        self.GetView().SetColMinimalAcceptableWidth(8)
        #self.GetView().SetRowMinimalAcceptableHeight(5)
        self.GetView().SetDefaultColSize(8, True)
        #self.GetView().SetDefaultRowSize(1, True)
        self.GetView().SetColSize(0, self.width_colcheck)
        self.GetView().SetColSize(1, self.width_colid)
        for i in range(2, self.fix_col):
            # details = {"aim": "list"}
            # details.update(self.details)
            # sz = max([len("%s" % self.getFieldV(sid, self.fields[i], details)) for sid in self.sortids])
            self.GetView().SetColSize(i, self.width_colname) #10*(sz+2))
        for cid in self.sc:
            pls = 2
            if cid == self.sortP[0]:
                pls = 4
            self.GetView().SetColSize(cid, 10*(len(self.fields[cid][0])+pls))
#         self.GetView().SetRowSize(self.getSelectedRow(), 10)
# #            self.GetView().SetColSize(cid, wx.DC().GetTextExtent(self.fields[cid][0]))
#        self.GetView().DisableDragColSize()
        self.GetView().DisableDragRowSize()
        self.GetView().SetGridCursor(crow,ccol)

    def setFocus(self, event):
        self.flipFocusCol(event.GetCol())

    def flipFocusCol(self, cid):
        if cid >= self.fix_col:
            if cid in self.sc:
                self.sc.remove(cid)
            else:
                self.sc.add(cid)
            self.redraw()
        if self.getSelectedRow() is not None:
            row = self.getSelectedRow()
        else:
            row = 0
        if not self.grid.IsVisible(row, cid):
            self.grid.MakeCellVisible(row, cid)

    def setFocusCol(self, cid):
        if cid >= self.fix_col:
            if cid not in self.sc:
                self.sc.add(cid)
            self.redraw()

    def delFocusCol(self, cid):
        if cid >= self.fix_col:
            if cid in self.sc:
                self.sc.remove(cid)
            self.redraw()

    def showCol(self, side, col):
        if (side, col) in self.cols_map and self.cols_map[(side, col)] not in self.sc:
            self.sc.add(self.cols_map[(side, col)])
            self.redraw()
            self.grid.MakeCellVisible(self.getSelectedRow(), self.cols_map[(side, col)])

    def showRidRed(self, rid, red=None):
        row = self.getRowForItem(rid)
        if row is not None:
            self.setSelectedRow(row)
            if red is not None:
                for side in [0,1]:
                    for l in red.queries[side].listLiterals():
                        self.sc.add(self.cols_map[(side, l.colId())])
            self.redraw()
        return row

    def setSort(self, event):
        self.setFocusCol(event.GetCol())
        GridTable.setSort(self, event)
        
    def resetSizes(self):
        pass
