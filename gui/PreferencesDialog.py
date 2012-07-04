from classSettings import Settings
import wx

conf = None

class PreferencesDialog(wx.Dialog):
    """
    Creates a preferences dialog to change the settings
    """

    def __init__(self, parent, config):
        """
        Initialize the config dialog
        """
        global conf
        conf = config
        wx.Dialog.__init__(self, parent, wx.ID_ANY, 'Preferences', size=(550, 300))
        nb = wx.Notebook(self, wx.ID_ANY)
        outlook_p = wx.Panel(nb, -1)
        mining_p = wx.Panel(nb, -1)
        nb.AddPage(outlook_p, "Outlook")
        nb.AddPage(mining_p, "Mining")
        self.Centre()
        # Apparently for Windows (?)
        self.SetSize((550, 300))


###############################
# For debugging
#
class MyApp(wx.App):
    def OnInit(self):
        # Load configuration data
        minesettings = Settings('mine', ['part_run_gui', 'rajapaja/rajapaja.conf'])
        minesettings.getParams()
        d = PreferencesDialog(None, minesettings)
        print "Modal dialog returned :", d.ShowModal()
        d.Destroy()

        return True

if __name__ == "__main__":
    app = MyApp(False)
    app.MainLoop()
        
