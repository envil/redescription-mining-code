import wx, wx.grid, re, colorsys, random, datetime
from factView import ViewFactory
from reremi.toolICList import ICList
from reremi.classQuery import Query, Literal
from reremi.classRedescription import Redescription

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
    
    """Base class for editors"""

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

    def __init__(self, parent, tabId, frame):
        wx.grid.PyGridTableBase.__init__(self)
        self.details = {}
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

        #### GRID
        self.grid = wx.grid.Grid(frame)
        self.grid.SetTable(self)
        self.setSelectedRow(0)
        self.grid.EnableEditing(False)
        #self.grid.AutoSizeColumns(True)

        self.grid.RegisterDataType(wx.grid.GRID_VALUE_STRING,
                                   CustRenderer(),
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
                direct = u"\u2191"
            else:
                direct = u"\u2193" 
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
            return methode(details)
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

    def resetFields(self):
        pass

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

    def setSelectedRow(self,row, col=0):
        self.GetView().SetGridCursor(row,0)
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
    fields_def = [('', 'self.data[x].getEnabled'),
                  ('query LHS', 'self.data[x].getQueryLU', None, 300),
                  ('query RHS', 'self.data[x].getQueryRU', None, 300),
                  ('J', 'self.data[x].getRoundAcc', None, 60),
                  ('p-value', 'self.data[x].getRoundPVal', None, 60),
                  (u'|E\u2081\u2081|', 'self.data[x].getLenI', None, 60),
                  ('track', 'self.data[x].getTrack', None, 80)]

    def __init__(self, parent, tabId, frame):
        GridTable.__init__(self, parent, tabId, frame)
        self.opened_edits = {}
        self.emphasized = {}
        self.uptodate = True

    def ResetView(self):
        self.refreshRestrict()
        GridTable.ResetView(self)

    def refreshRestrict(self):
        if self.uptodate:
            return
        tic = datetime.datetime.now()
        for red in self.data:
            red.setRestrictedSupp(self.parent.dw.data)
        #print "Done restrict support ", self.tabId, len(self.data), datetime.datetime.now() - tic
        self.uptodate = True

    def recomputeAll(self, restrict):
        self.uptodate = False
        self.refreshRestrict()
        for k,v in self.opened_edits.items():
            mc = self.parent.accessViewX(k)
            if mc is not None:
                mc.refresh()

    def insertItems(self, items):
        for item in items:
            self.insertItem(item, None, False)
        self.neutraliseSort()
        self.ResetView()

    def insertItem(self, item, row=None, upView=True):
        if row is None or row >= len(self.sortids):
            self.sortids.append(len(self.data))
        else:
            self.sortids.insert(row+1, len(self.data))
        item.setRestrictedSupp(self.parent.dw.data)
        self.data.append(item)
        if upView:
            self.neutraliseSort()
            self.ResetView()

    def deleteItem(self, pos, upView=True):
        row = self.getRowFromPosition(pos)
        if row is not None:
            self.sortids.pop(row)
            for i in range(len(self.sortids)):
                self.sortids[i] -= (self.sortids[i] > pos)
                i+=1
            ### TODO destruct the associated mapView if any?? 
            ### TODO add possibility to undo delete here
            self.data.pop(pos)
            for edit_key in self.opened_edits.keys():
                if self.opened_edits[edit_key] == pos:
                    self.opened_edits[edit_key] = None
                elif self.opened_edits[edit_key] > pos:
                    self.opened_edits[edit_key] -= 1
            ks = sorted(self.emphasized.keys())
            for k in ks:
                if k == pos:
                    del self.emphasized[k]
                elif k > pos:
                    self.emphasized[k-1] = self.emphasized[k]
                    del self.emphasized[k]
            if upView:
                self.ResetView()

    def viewData(self, viewT, pos=None, oid=None):
        if oid is not None:
            if self.opened_edits.has_key(oid):
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
            self.registerView(mapV.getId(), pos)
            mapV.setCurrent(self.getItemAtRow(self.getRowFromPosition(pos)), self.tabId)

    def registerView(self, key, pos):
        self.opened_edits[key] = pos

    def unregisterView(self, key):
        if key in self.opened_edits.keys():
            pos = self.opened_edits[key]
            del self.opened_edits[key]
            if pos not in self.opened_edits.values():
                if self.emphasized.has_key(pos):
                    del self.emphasized[pos]
            
    def updateEdit(self, edit_key, red):
        if edit_key in self.opened_edits.keys() \
               and self.opened_edits[edit_key] >= 0 and self.opened_edits[edit_key] < len(self.data):
            if self.tabId != "hist":
                toed = self.opened_edits[edit_key]
                self.data[toed] = red

                for k,v in self.opened_edits.items():
                    if v == toed and k != edit_key:
                        mc = self.parent.accessViewX(k)
                        if mc is not None:
                            mc.setCurrent(red, self.tabId)

            else:
                old_toed = self.opened_edits[edit_key]
                self.opened_edits[edit_key] = len(self.data)
                if self.emphasized.has_key(old_toed):
                    self.emphasized[self.opened_edits[edit_key]] = self.emphasized[old_toed]
                    del self.emphasized[old_toed]
                self.insertItem(red, -1)
            self.ResetView()
        ### TODO else insert (e.g. created from variable)

    def addAndViewTop(self, queries, viewT):
        mapV = self.parent.getViewX(None, viewT)
        red = mapV.setCurrent(queries)
        self.registerView(mapV.getId(), len(self.data)-1)
        mapV.setSource(self.tabId)

    def doFlipEmphasizedR(self, edit_key):
        if edit_key in self.opened_edits.keys() and self.emphasized.has_key(self.opened_edits[edit_key]):
            self.parent.flipRowsEnabled(self.emphasized[self.opened_edits[edit_key]])
            self.setEmphasizedR(edit_key, self.emphasized[self.opened_edits[edit_key]])

    def getEmphasizedR(self, edit_key):
        if edit_key in self.opened_edits.keys() \
               and self.opened_edits[edit_key] >= 0 and self.opened_edits[edit_key] < len(self.data) \
               and self.emphasized.has_key(self.opened_edits[edit_key]):
            return self.emphasized[self.opened_edits[edit_key]]
        return set()

    def setEmphasizedR(self, edit_key, lids=None, show_info=False):
        if edit_key in self.opened_edits.keys() \
               and self.opened_edits[edit_key] >= 0 and self.opened_edits[edit_key] < len(self.data):

            toed = self.opened_edits[edit_key]
            if not self.emphasized.has_key(toed):
                self.emphasized[toed] = set()
            if lids is None:
                turn_off = self.emphasized[toed]
                turn_on =  set()
                self.emphasized[toed] = set()
            else:
                turn_off = set(lids) & self.emphasized[toed]
                turn_on =  set(lids) - self.emphasized[toed]
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
            self.insertItem(self.parent.buffer_copy, row)
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

    fields_def = [('','self.data[x].getEnabled'),
                       ('id', 'self.data[x].getId'),
                       ('name', 'self.data[x].getName', None, 300),
                       ('type', 'self.data[x].getType', None, 100)]
    fields_var = {1: [('density', 'self.data[x].getDensity', None, 80)],
                  2:[('categories', 'self.data[x].getCategories', None, 80)],
                  3:[('min', 'self.data[x].getMin', None, 80), ('max', 'self.data[x].getMax', None, 80)]}

    def viewData(self, viewT, pos=None):
        if pos is None:
            datVar = self.getSelectedItem()
        else:
            dataVar = self.getItemAtRow(pos)
        queries = [Query(), Query()]
        queries[datVar.side].extend(-1, Literal(False, datVar.getTerm()))
        self.parent.newRedVHist(queries, viewT)
 
    def updateEdit(self, edit_key, red):
        pass

    def resetFields(self):
        self.fields = []
        self.fields.extend(self.fields_def)
        for tyid in set([r.type_id for r in self.data]):
            self.fields.extend(self.fields_var[tyid])


class RowTable(GridTable):     

    fields_def = [('','self.data[x].getEnabled'),
                  ('id', 'self.data[x].getId')]

    def setSelectedRow(self,row, col=0):
        if row is None: row = 0
        if col is None: col = 0
        self.GetView().SetGridCursor(row,col)
        self.GetView().SelectRow(row)

    def viewData(self, viewT, pos=None):
        queries = [Query(), Query()]
        self.parent.newRedVHist(queries, viewT)
 
    def updateEdit(self, edit_key, red):
        pass

    def resetFields(self, dw=None, review=True):
        if dw is not None:
            self.cols_map = {}
            self.fields = []
            self.fields.extend(self.fields_def)
            for side, sideS in [(0, "LHS"),(1, "RHS")]:
                nb = max(1,len(dw.getDataCols(side))-1.0)
                for ci, col in enumerate(dw.getDataCols(side)):
                    self.cols_map[(side, col.getId())] = len(self.fields)
                    self.fields.append(("%s:%s" % (sideS, col.getName()), 'self.data[x].getValue', {"side":side, "col": col.getId(), "range": col.getRange(), "r":ci/nb}))
            if review:
                self.ResetView()


    ### GRID METHOD
    def GetValue(self, row, col):
        """Return the value of a cell"""
        if row < self.nbItems() and col < len(self.fields):
            details = {"aim": "list"}
            details.update(self.details)
            tmp = self.getFieldV(self.sortids[row], self.fields[col], details)
            if col < 2:
                return tmp
            else:
                h = 125*self.fields[col][2]["side"] + int(100*self.fields[col][2]["r"])
                if tmp == "-":
                    l = 255
                else:
                    rangeV = self.fields[col][2]["range"]
                    lr = row/(1.0*self.nbItems())
                    if type(rangeV) is dict:
                        lr = rangeV.get(tmp, 0)/(len(rangeV)-1.0)
                    elif type(rangeV) is tuple and rangeV[0] != rangeV[1]:
                        lr = (tmp - rangeV[0])/(rangeV[1]-rangeV[0])
                    l = 125*lr+100

                # sc = 1.0*self.fields[col][2]["max"] - self.fields[col][2]["min"]
                # if sc == 0:
                #     lr = 0.5
                # else:
                #     lr = (tmp - self.fields[col][2]["min"])/sc
                if col in self.sc:
                    return "#h%dl%d#%s" % (h,l,tmp)
                else:
                    return "#h%dl%d#%s" % (h,l,"")
        else:
            return None

    ### GRID METHOD
    def GetColLabelValue(self, col):
        """Return the column label"""
        if col not in self.sc:
            name = ""
        else:
            name = " %s " % self.fields[col][0]
        direct = '  '
        if col == self.sortP[0]:
            if self.sortP[1]:
                direct = u"\u2191"
            else:
                direct = u"\u2193" 
        return name + direct

    def notify_change(self):
        self.parent.recomputeAll()
        
    def resetData(self, data, srids=None):
        self.data = data
        if srids is not None:
            self.sortids = srids
        else:
            self.sortids = ICList([idi for idi in range(len(self.data))], True)
        self.resetFields()
        self.updateSort()
        self.redraw()

    def resetDetails(self, details={}, review=True):
        self.details = details
        if review:
            self.redraw()

    def redraw(self, details={}, review=True):
        crow, ccol = self.GetView().GetGridCursorRow(), self.GetView().GetGridCursorCol()
        self.ResetView()
        self.GetView().SetColMinimalAcceptableWidth(5)
        #self.GetView().SetRowMinimalAcceptableHeight(5)
        self.GetView().SetDefaultColSize(1, True)
        #self.GetView().SetDefaultRowSize(1, True)
        self.GetView().SetColSize(0, 30)
        self.GetView().SetColSize(1, 30)
        for cid in self.sc:
            self.GetView().SetColSize(cid, 10*len(self.fields[cid][0]))
#         self.GetView().SetRowSize(self.getSelectedRow(), 10)
# #            self.GetView().SetColSize(cid, wx.DC().GetTextExtent(self.fields[cid][0]))
        self.GetView().DisableDragColSize()
        self.GetView().DisableDragRowSize()
        self.GetView().SetGridCursor(crow,ccol)

    def setFocus(self, event):
        self.flipFocusCol(event.GetCol())

    def flipFocusCol(self, cid):
        if cid > 1:
            if cid in self.sc:
                self.sc.remove(cid)
            else:
                self.sc.add(cid)
            self.redraw()

    def setFocusCol(self, cid):
        if cid > 1:
            if cid not in self.sc:
                self.sc.add(cid)
            self.redraw()

    def delFocusCol(self, cid):
        if cid > 1:
            if cid in self.sc:
                self.sc.remove(cid)
            self.redraw()


    def showRidRed(self, rid, red=None):
        row = self.getRowForItem(rid)
        if row is not None:
            self.setSelectedRow(row)
            if red is not None:
                for side in [0,1]:
                    for l in red.queries[side].listLiterals():
                        self.sc.add(self.cols_map[(side, l.col())])
            self.redraw()
        return row

    def setSort(self, event):
        self.setFocusCol(event.GetCol())
        GridTable.setSort(self, event)
        
    def resetSizes(self):
        pass
