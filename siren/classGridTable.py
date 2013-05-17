import wx, wx.grid
from classProjView import ProjView
from classParaView import ParaView
from reremi.toolICList import ICList
from reremi.classQuery import Query, Literal
from reremi.classRedescription import Redescription

import pdb

class CustRenderer(wx.grid.PyGridCellRenderer):

    BACKGROUND_SELECTED = wx.Colour(100,100,100)
    TEXT_SELECTED = wx.Colour(100,100,100)
    BACKGROUND = wx.Colour(100,100,100)
    TEXT = wx.Colour(100,100,100)
    BACKGROUND_GREY = wx.Colour(240,255,240)
    TEXT_GREY = wx.Colour(131,139,131)

    """Base class for editors"""

    ### Customisation points
    def Draw(self, grid, attr, dc, rect, row, col, isSelected):
        """Customisation Point: Draw the data from grid in the rectangle with attributes using the dc"""

        dc.SetClippingRegion( rect.x, rect.y, rect.width, rect.height )
        if row in grid.GetSelectedRows():
            dc.SetTextForeground( self.TEXT_SELECTED )
            dc.SetTextBackground( self.BACKGROUND_SELECTED)
            dc.SetBrush( wx.Brush( self.BACKGROUND_SELECTED) )
        elif grid.GetTable().getEnabled(row) == 0:
            dc.SetTextForeground( self.TEXT_GREY )
            dc.SetTextBackground( self.BACKGROUND_GREY)
            dc.SetBrush( wx.Brush( self.BACKGROUND_GREY) )
        else:
            dc.SetBrush( wx.Brush( self.BACKGROUND, wx.SOLID) )
            dc.SetTextForeground( self.TEXT )
        try:
            dc.SetPen(wx.TRANSPARENT_PEN)
            dc.DrawRectangle( rect.x, rect.y, rect.width, rect.height )
            value = grid.GetCellValue( row, col )
            dc.SetFont( wx.NORMAL_FONT )
            dc.DrawText( value, rect.x+2,rect.y+2 )
        finally:
            dc.SetTextForeground( self.TEXT)
            dc.SetTextBackground( self.BACKGROUND)
            dc.SetPen( wx.NullPen )
            dc.SetBrush( wx.NullBrush )
            dc.DestroyClippingRegion( )

    def GetBestSize(self, grid, attr, dc, row, col):
        """Customisation Point: Determine the appropriate (best) size for the control, return as wxSize
        Note: You _must_ return a wxSize object.  Returning a two-value-tuple
        won't raise an error, but the value won't be respected by wxPython.
        """         
        x,y = dc.GetTextExtent( "%s" % grid.GetCellValue( row, col ) )
        # note that the two-tuple returned by GetTextExtent won't work,
        # need to give a wxSize object back!
        return wx.Size( min(x, 10), min(y, 10))


class GridTable(wx.grid.PyGridTableBase):

    fields_def = []

    def __init__(self, parent, tabId, frame):
        wx.grid.PyGridTableBase.__init__(self)
        self.parent = parent
        self.tabId = tabId
        self.fields = self.fields_def
        self.data = ICList()
        self.sortids = ICList()
        self.details = {}
        self.sortP = (None, False)
        self.currentRows = self.nbItems()
        self.currentColumns = len(self.fields)

        #### GRID
        self.grid = wx.grid.Grid(frame)
        self.grid.SetTable(self)
        self.grid.EnableEditing(False)
        self.grid.AutoSizeColumns(True)

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
        self.grid.Bind(wx.grid.EVT_GRID_CELL_LEFT_DCLICK, self.OnViewData)
        self.grid.Bind(wx.grid.EVT_GRID_CELL_RIGHT_CLICK, self.OnRightClick)
        self.grid.Bind(wx.grid.EVT_GRID_CELL_LEFT_CLICK, self.OnMouse)
        
    # def showPopupMenu(self, event):
    #     self.table.highlightRow(event.GetRow())
    #     parent.currentList = self

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
        #     x = self.sortids[row]
        #     methode = eval(self.fields[col][0])
        #     return type(methode(self.details))
        # else:
        #     return None

    ### GRID METHOD
    def GetValue(self, row, col):
        """Return the value of a cell"""
        if row < self.nbItems() and col < len(self.fields):
            x = self.sortids[row]
            methode = eval(self.fields[col][1])
            if callable(methode):
                return "%s" % methode(self.details)
            else:
                return methode
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

    def resetData(self, data, details=[], srids=None):
        self.data = data
        
        if details != []:
            self.details = details

        if srids is not None:
            self.sortids = srids
        else:
            self.sortids = ICList([idi for idi in range(len(self.data))], True)

        self.resetFields()

        self.updateSort()
        self.ResetView()
        self.GetView().AutoSize()

    def resetFields(self):
        pass

    def getEnabled(self, row):
        return self.getItemAtRow(row).getEnabled()

    def flipEnabled(self, row):
        self.data[self.sortids[row]].flipEnabled()
        self.data.isChanged = True
        self.ResetView()

    def setAllDisabled(self):
        for item in self.data:
            item.setDisabled()
        self.data.isChanged = True
        self.ResetView()

    def setAllEnabled(self):
        for item in self.data:
            item.setEnabled()
        self.data.isChanged = True
        self.ResetView()

    def OnMouse(self,event):
        if event.GetRow() < self.nbItems():
            self.setSelectedRow(event.GetRow())
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

    def setSelectedRow(self,row):
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
        
    def updateSort(self):
        selected_row = self.getSelectedRow()
        selected_id = None
        if selected_row is not None:
            selected_id = self.getPositionFromRow(selected_row)

        if self.sortP[0] is not None:
            sort_c = 1
            if len(self.fields[self.sortP[0]]) > 2:
                sort_c = 2
            self.sortids.sort(key= lambda x: eval(self.fields[self.sortP[0]][sort_c])(self.details), reverse=self.sortP[1])
        if selected_id is not None:
            self.setSelectedRow(self.getRowFromPosition(selected_id))
            
    def OnRightClick(self, event):
        if event.GetRow() < self.nbItems():
            self.setSelectedRow(event.GetRow())
            self.parent.makePopupMenu(self.parent.toolFrame)

    def OnKU(self, event):
        if self.grid.GetGridCursorRow() < self.nbItems():
            self.setSelectedRow(self.grid.GetGridCursorRow())
        event.Skip()

    def OnViewData(self, event):
        if event.GetRow() < self.nbItems():
            self.setSelectedRow(event.GetRow())
            self.viewData()

class RedTable(GridTable):

    fields_def = [('', 'self.data[x].getEnabled'),
                 ('query LHS', 'self.data[x].getQueryLU'),
                 ('query RHS', 'self.data[x].getQueryRU'),
                 ('accuracy', 'self.data[x].getAcc'),
                 ('p-value', 'self.data[x].getPVal'),
                 ('|E_{1,1}|', 'self.data[x].getSupp'),
                  ('track', 'self.data[x].getTrackStr', 'self.data[x].getTrack')]

    def __init__(self, parent, tabId, frame):
        GridTable.__init__(self, parent, tabId, frame)
        self.opened_edits = {}

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
            if upView:
                self.ResetView()

    def viewData(self, viewT=None):
        pos = self.getSelectedPos()
        vid = None
        for (k,v) in self.opened_edits.items():
            if viewT != ProjView.TID and v == pos and viewT == k[0]:
                vid = k[1]
                break
            
        if vid is None:
            mapV = self.parent.getMapView(None, viewT)
            self.registerView(mapV.getId(), pos)
            mapV.setCurrent(self.getSelectedItem(), self.tabId)
        else:
            self.parent.getMapView(vid, viewT)

    def registerView(self, key, pos):
        self.opened_edits[key] = pos

    def unregisterView(self, key):
        if key in self.opened_edits.keys():
            del self.opened_edits[key]
            
    def updateEdit(self, edit_key, red):
        if edit_key in self.opened_edits.keys() \
               and self.opened_edits[edit_key] >= 0 and self.opened_edits[edit_key] < len(self.data):
            if self.tabId != "hist":
                toed = self.opened_edits[edit_key]
                self.data[toed] = red

                for k,v in self.opened_edits.items():
                    if k != edit_key and v == toed:
                        mc = self.parent.accessMapView(k)
                        if mc is not None:
                            mc.setCurrent(red, self.tabId)

            else:
                self.opened_edits[edit_key] = len(self.data)
                self.parent.tabs["hist"]["tab"].insertItem(red, -1)
            self.ResetView()
        ### TODO else insert (e.g. created from variable)

    def sendHighlight(self, edit_key, lid, turn_on=True):
        if edit_key in self.opened_edits.keys() \
               and self.opened_edits[edit_key] >= 0 and self.opened_edits[edit_key] < len(self.data):

            toed = self.opened_edits[edit_key]
            mc = None
            for k,v in self.opened_edits.items():
                if k[0] == ParaView.TID and v == toed:
                    mc = self.parent.accessMapView(k)

            if mc is None:
                mc = self.parent.getMapView(None, ParaView.TID)
                self.registerView(mc.getId(), toed)
                mc.setCurrent(self.data[toed], self.tabId)
            if turn_on:
                mc.emphasizeLine(lid)
            else:
                mc.clearEmphasize([lid])

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
                       ('name', 'self.data[x].getName'),
                       ('type', 'self.data[x].getType')]
    fields_var = {1: [('density', 'self.data[x].getDensity')],
                  2:[('categories', 'self.data[x].getCategories')],
                  3:[('min', 'self.data[x].getMin'), ('max', 'self.data[x].getMax')]}

    def viewData(self, viewT=None):
        mapV = self.parent.getMapView(None, viewT)
        datVar = self.getSelectedItem()
        queries = [Query(), Query()]
        queries[datVar.side].extend(-1, Literal(False, datVar.getTerm()))
        mapV.setCurrent(queries)
 
    def updateEdit(self, edit_key, red):
        pass

    def resetFields(self):
        self.fields = []
        self.fields.extend(self.fields_def)
        for tyid in set([r.type_id for r in self.data]):
            self.fields.extend(self.fields_var[tyid])
