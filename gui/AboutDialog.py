import wx
import time

class Foo(object):
    def onAbout(self, event):
        about_file = 'ABOUT'
        licence_file = 'LICENCE'
        dlg = wx.AboutDialogInfo()
        dlg.SetName('Siren')
        # Find icon somewhere
        #dlg.SetIcon(icn)
        with open(about_file) as f:
            dlg.SetDescription(f.read())
        with open(licence_file) as f:
            dlg.SetLicence(f.read())
        dlg.SetWebSite('http://www.cs.helsinki.fi/u/galbrun/redescriptors/siren/')
        #dlg.SetDevelopers(['Esther Galbrun', 'Pauli Miettinen'])
        dlg.SetCopyright('(C) 2012 Esther Galbrun and Pauli Miettinen')
        dlg.SetVersion('0.9')
        dlg.SetIcon(wx.Icon('icons/siren_icon32x32.png', wx.BITMAP_TYPE_PNG))
        wx.AboutBox(dlg)
        #time.sleep(20)

###############################
# For debugging
#
class MyApp(wx.App):
    def OnInit(self):
        f = Foo()
        f.onAbout('1')
        return True

if __name__ == "__main__":
    app = MyApp(False)
    app.MainLoop()
