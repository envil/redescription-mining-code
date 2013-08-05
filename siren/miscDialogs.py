import sys
import wx
import os.path
from reremi.classData import DataError

import pdb

class ImportDataDialog(object):
    """Helper class to show the dialog for importing data file triplets"""
    def __init__(self, parent):
        self.parent = parent
        self.dlg = wx.Dialog(self.parent.toolFrame, title="Import data")

        LHStext = wx.StaticText(self.dlg, label='Left-hand side variables file:')
        RHStext = wx.StaticText(self.dlg, label='Right-hand side variables file:')
        Cootext = wx.StaticText(self.dlg, label='Coordinates file:')
        RNamestext = wx.StaticText(self.dlg, label='Entities file:')

        self.LHSfile = None
        self.RHSfile = None
        self.Coofile = None
        self.RNamesfile = None

        self.LHSfileTxt = wx.TextCtrl(self.dlg, value='', size=(500,10), style=wx.TE_READONLY)
        self.RHSfileTxt = wx.TextCtrl(self.dlg, value='', style=wx.TE_READONLY)
        self.CoofileTxt = wx.TextCtrl(self.dlg, value='', style=wx.TE_READONLY)
        self.RNamesfileTxt = wx.TextCtrl(self.dlg, value='', style=wx.TE_READONLY)

        LHSbtn = wx.Button(self.dlg, label='Choose', name='LHS')
        RHSbtn = wx.Button(self.dlg, label='Choose', name='RHS')
        Coobtn = wx.Button(self.dlg, label='Choose', name='Coordinates')
        RNamesbtn = wx.Button(self.dlg, label='Choose', name='Entities')

        LHSbtn.Bind(wx.EVT_BUTTON, self.onButton)
        RHSbtn.Bind(wx.EVT_BUTTON, self.onButton)
        Coobtn.Bind(wx.EVT_BUTTON, self.onButton)
        RNamesbtn.Bind(wx.EVT_BUTTON, self.onButton)

        gridSizer = wx.FlexGridSizer(rows = 4, cols = 3, hgap = 5, vgap = 5)
        gridSizer.AddGrowableCol(1, proportion=1)
        gridSizer.SetFlexibleDirection(wx.HORIZONTAL)
        gridSizer.AddMany([(LHStext, 0, wx.ALIGN_RIGHT), (self.LHSfileTxt, 1, wx.EXPAND), (LHSbtn, 0),
                           (RHStext, 0, wx.ALIGN_RIGHT), (self.RHSfileTxt, 1, wx.EXPAND), (RHSbtn, 0),
                           (Cootext, 0, wx.ALIGN_RIGHT), (self.CoofileTxt, 1, wx.EXPAND), (Coobtn, 0),
                           (RNamestext, 0, wx.ALIGN_RIGHT), (self.RNamesfileTxt, 1, wx.EXPAND), (RNamesbtn, 0)])

        btnSizer = self.dlg.CreateButtonSizer(wx.OK|wx.CANCEL)
        topSizer = wx.BoxSizer(wx.VERTICAL)
        topSizer.Add(gridSizer, flag=wx.ALL, border=5)
        topSizer.Add(btnSizer, flag=wx.ALL, border=5)

        self.dlg.SetSizer(topSizer)
        self.dlg.Fit()

        self.open_dir = os.path.expanduser('~/')
        self.wcd = 'All files|*|Numerical Variables (*.densenum / *.datnum)|*.densenum/*.datnum|Boolean Variables (*.sparsebool / *.datbool)|*.sparsebool/*.datbool'
        self.names_wcd = 'All files|*|Information files (*.names)|*.names'


    def showDialog(self):
        if self.dlg.ShowModal() == wx.ID_OK:
            try:
                if self.RHSfile is None:
                    self.parent.dw.importDataFromMulFile(self.LHSfile)
                else:
                    self.parent.dw.importDataFromMulFiles([self.LHSfile, self.RHSfile], None, self.Coofile, self.RNamesfile)
            except:
                pass
                ##raise
            else:
                self.parent.reloadAll()
            finally:
                self.dlg.Destroy()
            return True
        else:
            return False
                
            

    def onButton(self, e):
        button = e.GetEventObject()
        btnName = button.GetName()
        if btnName == 'Coordinates' or  btnName == 'Entities':
            wcd = self.names_wcd
        else:
            wcd = self.wcd
        open_dlg = wx.FileDialog(self.parent.toolFrame, message="Choose "+btnName+" file",
                                 defaultDir=self.open_dir, wildcard=wcd,
                                 style=wx.OPEN|wx.CHANGE_DIR)
        if open_dlg.ShowModal() == wx.ID_OK:
            path = open_dlg.GetPath()
            self.open_dir = os.path.dirname(path)
            if btnName == 'LHS':
                self.LHSfileTxt.ChangeValue(path)
                self.LHSfile = path
                # Both TextCtrl and variable hold the same info, but if the latter is empty is None,
                # making it compatible with dw.importDataFromMulFiles
            elif btnName == 'RHS':
                self.RHSfileTxt.ChangeValue(path)
                self.RHSfile = path
            elif btnName == 'Coordinates':
                self.CoofileTxt.ChangeValue(path)
                self.Coofile = path
            elif btnName == 'Entities':
                self.RNamesfileTxt.ChangeValue(path)
                self.RNamesfile = path



class ImportDataCSVDialog(object):
    """Helper class to show the dialog for importing data file csv pairs"""
    def __init__(self, parent):
        self.parent = parent
        self.dlg = wx.Dialog(self.parent.toolFrame, title="Import data")

        LHStext = wx.StaticText(self.dlg, label='Left-hand side variables file:')
        RHStext = wx.StaticText(self.dlg, label='Right-hand side variables file:')

        self.dialect_options = {'delimiter': {"label": "Delimiter", "opts": [(None, "(auto)"), ('\t', 'TAB'), (';', ';'), (',', ','), (' ', 'SPC')]}}
        self.LHSfile = None
        self.RHSfile = None

        self.LHSfileTxt = wx.TextCtrl(self.dlg, value='', size=(500,10), style=wx.TE_READONLY)
        self.RHSfileTxt = wx.TextCtrl(self.dlg, value='', style=wx.TE_READONLY)

        so_sizer = wx.GridSizer(rows=1, cols=2*(1+len(self.dialect_options)), hgap=5, vgap=5)

        ctrl_id = wx.NewId()
        label = wx.StaticText(self.dlg, wx.ID_ANY, "Missing:")
        self.missing_ctrl = wx.TextCtrl(self.dlg, ctrl_id, "")
        so_sizer.Add(label, 0, wx.ALIGN_RIGHT)
        so_sizer.Add(self.missing_ctrl, 0)

        self.dialect_ctrl = {}
        for item, details in self.dialect_options.items():
            ctrl_id = wx.NewId()
            label = wx.StaticText(self.dlg, wx.ID_ANY, details['label']+":")
            self.dialect_ctrl[item] = wx.Choice(self.dlg, ctrl_id)
            self.dialect_ctrl[item].AppendItems(strings=[v[1] for v in details['opts']])
            self.dialect_ctrl[item].SetSelection(0)
            so_sizer.Add(label, 0, wx.ALIGN_RIGHT)
            so_sizer.Add(self.dialect_ctrl[item], 0)
                        

        LHSbtn = wx.Button(self.dlg, label='Choose', name='LHS')
        RHSbtn = wx.Button(self.dlg, label='Choose', name='RHS')

        LHSbtn.Bind(wx.EVT_BUTTON, self.onButton)
        RHSbtn.Bind(wx.EVT_BUTTON, self.onButton)

        gridSizer = wx.FlexGridSizer(rows = 2, cols = 3, hgap = 5, vgap = 5)
        gridSizer.AddGrowableCol(1, proportion=1)
        gridSizer.SetFlexibleDirection(wx.HORIZONTAL)
        gridSizer.AddMany([(LHStext, 0, wx.ALIGN_RIGHT), (self.LHSfileTxt, 1, wx.EXPAND), (LHSbtn, 0),
                           (RHStext, 0, wx.ALIGN_RIGHT), (self.RHSfileTxt, 1, wx.EXPAND), (RHSbtn, 0)])

        btnSizer = self.dlg.CreateButtonSizer(wx.OK|wx.CANCEL)
        topSizer = wx.BoxSizer(wx.VERTICAL)
        topSizer.Add(gridSizer, flag=wx.ALL, border=5)
        topSizer.Add(so_sizer, flag=wx.EXPAND|wx.ALL, border=5)
        topSizer.Add(btnSizer, flag=wx.ALL, border=5)

        self.dlg.SetSizer(topSizer)
        self.dlg.Fit()

        self.open_dir = os.path.expanduser('~/')
        self.wcd = 'All files|*|CSV files|*.csv'


    def showDialog(self):
        na = None
        dialect_dict = {}
        if self.dlg.ShowModal() == wx.ID_OK:
            tmp = self.missing_ctrl.GetValue()
            if len(tmp) > 0:
                na = tmp
                
            for item, ctrl_single in self.dialect_ctrl.items():
                tmp = self.dialect_options[item]['opts'][ctrl_single.GetCurrentSelection()][0]
                if tmp is not None:
                    dialect_dict[item] = tmp
            try:
                self.parent.dw.importDataFromCSVFiles([self.LHSfile, self.RHSfile, dialect_dict, na])
            except:
                pass
                raise
            else:
                self.parent.reloadAll()
            finally:
                self.dlg.Destroy()
            return True
        else:
            return False
                
            

    def onButton(self, e):
        button = e.GetEventObject()
        btnName = button.GetName()
        wcd = self.wcd
        open_dlg = wx.FileDialog(self.parent.toolFrame, message="Choose "+btnName+" file",
                                 defaultDir=self.open_dir, wildcard=wcd,
                                 style=wx.OPEN|wx.CHANGE_DIR)
        if open_dlg.ShowModal() == wx.ID_OK:
            path = open_dlg.GetPath()
            self.open_dir = os.path.dirname(path)
            if btnName == 'LHS':
                self.LHSfileTxt.ChangeValue(path)
                self.LHSfile = path
            elif btnName == 'RHS':
                self.RHSfileTxt.ChangeValue(path)
                self.RHSfile = path



