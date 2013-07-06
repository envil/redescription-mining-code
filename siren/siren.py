#!/usr/bin/env python

import wx
#import wx.richtext
#from wx.lib import wordwrap
#from wx.prop import basetableworker
# import warnings
# warnings.simplefilter("ignore")
#import matplotlib.pyplot as plt

import pdb
#from reremi import *

from classSiren import Siren
from classGridTable import CustRenderer
             
## MAIN APP CLASS ###
class SirenApp(wx.App):
    def __init__(self, *args, **kwargs):
        wx.App.__init__(self, *args, **kwargs)
        # Catches events when the app is asked to activate by some other process
        self.Bind(wx.EVT_ACTIVATE_APP, self.OnActivate)

    def OnInit(self):
        self.frame = Siren()

        import sys
        if len(sys.argv) > 1:
            # DEBUG
            #print "Loading file", sys.argv[-1]
            self.frame.LoadFile(sys.argv[1])


        if len(sys.argv) > 2 and sys.argv[2] == "debug":
            # DEBUG
            #print "Loading file", sys.argv[-1]
            self.frame.tabs["reds"]["tab"].setSelectedRow(12)
            mapV = self.frame.getMapView(None, "PC")
            pos = self.frame.tabs["reds"]["tab"].getSelectedPos()
            self.frame.tabs["reds"]["tab"].registerView(mapV.getId(), pos)
            mapV.setCurrent(self.frame.tabs["reds"]["tab"].getSelectedItem(), self.frame.tabs["reds"]["tab"].tabId)

        return True

    def BringWindowToFront(self):
        try:
            pass
            #self.frame.toolFrame.Raise()
        except:
            pass

    def OnActivate(self, event):
        if event.GetActive():
            self.BringWindowToFront()
        event.Skip()

    def MacOpenFile(self, filename):
        """Called for files dropped on dock icon, or opened via Finder's context menu"""
        import sys
        # When start from command line, this gets called with the script file's name
        if filename != sys.argv[0]:
            self.frame.LoadFile(filename)

    def MacReopenApp(self):
        """Called when the doc icon is clicked, and ???"""
        self.BringWindowToFront()

    def MacNewFile(self):
        pass

    def MacPrintFile(self, filepath):
        pass

def siren_run():
    app = SirenApp(False)

    CustRenderer.BACKGROUND_SELECTED = wx.SystemSettings_GetColour( wx.SYS_COLOUR_HIGHLIGHT )
    CustRenderer.TEXT_SELECTED = wx.SystemSettings_GetColour( wx.SYS_COLOUR_HIGHLIGHTTEXT )
    CustRenderer.BACKGROUND = wx.SystemSettings_GetColour( wx.SYS_COLOUR_WINDOW  )
    CustRenderer.TEXT = wx.SystemSettings_GetColour( wx.SYS_COLOUR_WINDOWTEXT  )

    #app.frame = Siren()
    app.MainLoop()


if __name__ == '__main__':
    siren_run()
