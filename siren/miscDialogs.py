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

        LHStext = wx.StaticText(self.dlg, label='Left-hand side data file:')
        RHStext = wx.StaticText(self.dlg, label='Right-hand side data file:')
        Cootext = wx.StaticText(self.dlg, label='Coordinates file:')

        self.LHSfile = None
        self.RHSfile = None
        self.Coofile = None

        self.LHSfileTxt = wx.TextCtrl(self.dlg, value='', size=(500,10), style=wx.TE_READONLY)
        self.RHSfileTxt = wx.TextCtrl(self.dlg, value='', style=wx.TE_READONLY)
        self.CoofileTxt = wx.TextCtrl(self.dlg, value='', style=wx.TE_READONLY)

        LHSbtn = wx.Button(self.dlg, label='Choose', name='LHS')
        RHSbtn = wx.Button(self.dlg, label='Choose', name='RHS')
        Coobtn = wx.Button(self.dlg, label='Choose', name='Coordinates')

        LHSbtn.Bind(wx.EVT_BUTTON, self.onButton)
        RHSbtn.Bind(wx.EVT_BUTTON, self.onButton)
        Coobtn.Bind(wx.EVT_BUTTON, self.onButton)

        gridSizer = wx.FlexGridSizer(rows = 3, cols = 3, hgap = 5, vgap = 5)
        gridSizer.AddGrowableCol(1, proportion=1)
        gridSizer.SetFlexibleDirection(wx.HORIZONTAL)
        gridSizer.AddMany([(LHStext, 0, wx.ALIGN_RIGHT), (self.LHSfileTxt, 1, wx.EXPAND), (LHSbtn, 0),
                           (RHStext, 0, wx.ALIGN_RIGHT), (self.RHSfileTxt, 1, wx.EXPAND), (RHSbtn, 0),
            (Cootext, 0, wx.ALIGN_RIGHT), (self.CoofileTxt, 1, wx.EXPAND), (Coobtn, 0)])

        btnSizer = self.dlg.CreateButtonSizer(wx.OK|wx.CANCEL)
        topSizer = wx.BoxSizer(wx.VERTICAL)
        topSizer.Add(gridSizer, flag=wx.ALL, border=5)
        topSizer.Add(btnSizer, flag=wx.ALL, border=5)

        self.dlg.SetSizer(topSizer)
        self.dlg.Fit()

        self.open_dir = os.path.expanduser('~/')
        self.wcd = 'All files|*|Numerical Data (*.densenum / *.datnum)|*.densenum/*.datnum|Boolean Data (*.sparsebool / *.datbool)|*.sparsebool/*.datbool'
        self.coo_wcd = 'All files|*|Information files (*.names)|*.names'


    def showDialog(self):
        if self.dlg.ShowModal() == wx.ID_OK:
            try:
                if self.RHSfile is None:
                    self.parent.dw.importDataFromFile(self.LHSfile)
                else:
                    self.parent.dw.importDataFromFiles([self.LHSfile, self.RHSfile], None, self.Coofile)
            except IOError as error:
                mdlg = wx.MessageDialog(self.parent.toolFrame, 'Error opening files '+str(self.LHSfile)
                                       +', '+str(self.RHSfile)+', and '+str(self.Coofile)+':\n'
                                       +str(error), style=wx.OK|wx.ICON_EXCLAMATION, caption="Error")
                mdlg.ShowModal()
                mdlg.Destroy()
                return False
            except DataError as error:
                mdlg = wx.MessageDialog(self.parent.toolFrame, 'Error importing data:\n'
                                       +str(error), style=wx.OK|wx.ICON_EXCLAMATION, caption="Error")
                mdlg.ShowModal()
                mdlg.Destroy()
                return False

            except:
                mdlg = wx.MessageDialog(self.parent.toolFrame, 'Unexpected Error:\n'+str(sys.exc_info()[1]), style=wx.OK|wx.ICON_EXCLAMATION, caption='Error')
                mdlg.ShowModal()
                mdlg.Destroy()
                return False
            else:
                self.parent.details = {'names': self.parent.dw.getColNames()}
                self.parent.reloadVars()
                self.parent.reloadReds()
            finally:
                self.dlg.Destroy()
            return True
        else:
            return False
                
            

    def onButton(self, e):
        button = e.GetEventObject()
        btnName = button.GetName()
        if btnName == 'Coordinates':
            wcd = self.coo_wcd
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
                # making it compatible with dw.importDataFromFiles
            elif btnName == 'RHS':
                self.RHSfileTxt.ChangeValue(path)
                self.RHSfile = path
            elif btnName == 'Coordinates':
                self.CoofileTxt.ChangeValue(path)
                self.Coofile = path


        
