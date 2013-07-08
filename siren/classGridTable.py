import wx, wx.grid, re, colorsys, random
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
            if len(field) > 2:
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

    def resetDetails(self, details={}, review=True):
        self.details = details
        if review:
            self.ResetView()
            self.GetView().AutoSize()

    def resetData(self, data, srids=None):
        self.data = data
        
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
        if type(self.data) == ICList:
            self.data.isChanged = True
        self.ResetView()

    def setAllDisabled(self):
        for item in self.data:
            item.setDisabled()
        if type(self.data) == ICList:
            self.data.isChanged = True
        self.ResetView()

    def setAllEnabled(self):
        for item in self.data:
            item.setEnabled()
        if type(self.data) == ICList:
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

    def setFocus(self, event):
        pass
        
    def updateSort(self):
        selected_row = self.getSelectedRow()
        selected_id = None
        if selected_row is not None:
            selected_id = self.getPositionFromRow(selected_row)

        if self.sortP[0] is not None:
            details = {"aim": "sort"}
            details.update(self.details)
            self.sortids.sort(key= lambda x: self.getFieldV(x, self.fields[self.sortP[0]], details), reverse=self.sortP[1])
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
            self.viewData(self.parent.getDefaultViewT(self.tabId))

class RedTable(GridTable):

    fields_def = [('', 'self.data[x].getEnabled'),
                 ('query LHS', 'self.data[x].getQueryLU'),
                 ('query RHS', 'self.data[x].getQueryRU'),
                 ('accuracy', 'self.data[x].getAcc'),
                 ('p-value', 'self.data[x].getPVal'),
                 ('|E_{1,1}|', 'self.data[x].getSupp'),
                  ('track', 'self.data[x].getTrack')]

    def __init__(self, parent, tabId, frame):
        GridTable.__init__(self, parent, tabId, frame)
        self.opened_edits = {}
        self.highlights = {}

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
            ks = sorted(self.highlights.keys())
            for k in ks:
                if k == pos:
                    del self.highlights[k]
                elif k > pos:
                    self.highlights[k-1] = self.highlights[k]
                    del self.highlights[k]
            if upView:
                self.ResetView()

    def viewData(self, viewT):
        pos = self.getSelectedPos()
        vid = None
        for (k,v) in self.opened_edits.items():
            if v == pos and viewT == k[0]:
                vid = k[1]
                break
            
        mapV = self.parent.getViewX(vid, viewT)
        if vid is None and mapV is not None:
            self.registerView(mapV.getId(), pos)
            mapV.setCurrent(self.getSelectedItem(), self.tabId)

    def registerView(self, key, pos):
        self.opened_edits[key] = pos

    def unregisterView(self, key):
        if key in self.opened_edits.keys():
            pos = self.opened_edits[key]
            del self.opened_edits[key]
            if pos not in self.opened_edits.values():
                if self.highlights.has_key(pos):
                    del self.highlights[pos]
            
    def updateEdit(self, edit_key, red):
        if edit_key in self.opened_edits.keys() \
               and self.opened_edits[edit_key] >= 0 and self.opened_edits[edit_key] < len(self.data):
            if self.tabId != "hist":
                toed = self.opened_edits[edit_key]
                self.data[toed] = red

                for k,v in self.opened_edits.items():
                    if v == toed:
                        mc = self.parent.accessViewX(k)
                        if k != edit_key and mc is not None:
                            mc.setCurrent(red, self.tabId)

            else:
                self.opened_edits[edit_key] = len(self.data)
                self.parent.tabs["hist"]["tab"].insertItem(red, -1)
            self.ResetView()
        ### TODO else insert (e.g. created from variable)

    def getHighlights(self, edit_key):
        if edit_key in self.opened_edits.keys() \
               and self.opened_edits[edit_key] >= 0 and self.opened_edits[edit_key] < len(self.data) \
               and self.highlights.has_key(self.opened_edits[edit_key]):
            return self.highlights[self.opened_edits[edit_key]]
        return set()

    def sendHighlight(self, edit_key, lid):
        if edit_key in self.opened_edits.keys() \
               and self.opened_edits[edit_key] >= 0 and self.opened_edits[edit_key] < len(self.data):

            toed = self.opened_edits[edit_key]
            if not self.highlights.has_key(toed):
                self.highlights[toed] = set()
            if lid in self.highlights[toed]:
                self.highlights[toed].remove(lid)
                turn_on = False
            else:
                self.highlights[toed].add(lid)
                turn_on = True

            mc = None
            for k,v in self.opened_edits.items():
                if v == toed:
                    mm = self.parent.accessViewX(k)
                    if turn_on:
                        mm.emphasizeLine(lid)
                    else:
                        mm.clearEmphasize([lid])
            if turn_on:
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
                       ('name', 'self.data[x].getName'),
                       ('type', 'self.data[x].getType')]
    fields_var = {1: [('density', 'self.data[x].getDensity')],
                  2:[('categories', 'self.data[x].getCategories')],
                  3:[('min', 'self.data[x].getMin'), ('max', 'self.data[x].getMax')]}

    def viewData(self, viewT):
        mapV = self.parent.getViewX(None, viewT)
        if mapV is not None:
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


class RowTable(GridTable):     

    fields_def = [('','self.data[x].getEnabled'),
                  ('id', 'self.data[x].getId')]

    def viewData(self, viewT):
        mapV = self.parent.getViewX(None, viewT)
 
    def updateEdit(self, edit_key, red):
        pass

    def resetFields(self, dw=None, review=True):
        if dw is not None:
            self.fields = []
            self.fields.extend(self.fields_def)
            for side, sideS in [(0, "LHS"),(1, "RHS")]:
                nb = max(1,len(dw.getDataCols(side))-1.0)
                for ci, col in enumerate(dw.getDataCols(side)):
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
        if col not in self.sc:
            return ""
        """Return the number of rows in the grid"""
        direct = '  '
        if col == self.sortP[0]:
            if self.sortP[1]:
                direct = u"\u2191"
            else:
                direct = u"\u2193" 
        return "  %s %s" % (self.fields[col][0], direct)


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
        self.ResetView()
        self.GetView().SetDefaultColSize(1, True)
        self.GetView().SetColSize(0, 25)
        self.GetView().SetColSize(1, 25)
        for cid in self.sc:
            self.GetView().SetColSize(cid, 10*len(self.fields[cid][0]))
#            self.GetView().SetColSize(cid, wx.DC().GetTextExtent(self.fields[cid][0]))

    def setFocus(self, event):
        cid = event.GetCol()
        if cid < 2:
            pass ### TODO select all
        else:
            if cid in self.sc:
                self.sc.remove(cid)
            else:
                self.sc.add(cid)
            self.redraw()

