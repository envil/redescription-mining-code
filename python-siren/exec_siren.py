#!/usr/bin/env python

import wx
import multiprocessing
import time

# import warnings
# warnings.simplefilter("ignore")

from blocks.mine.classData import Data
from blocks.interface.classSiren import Siren
from blocks.interface.classGridTable import CustRenderer
from blocks.mine.classPreferencesManager import getPreferencesReader
from blocks.mine.classPackage import IOTools

import pdb

## MAIN APP CLASS ###


class SirenApp(wx.App):
    def __init__(self, *args, **kwargs):
        wx.App.__init__(self, *args, **kwargs)
        # Catches events when the app is asked to activate by some other process
        self.Bind(wx.EVT_ACTIVATE_APP, self.OnActivate)

    def OnInit(self):
        # Set the app name here to *hard coded* Siren
        self.SetAppName("Siren")
        self.frame = Siren()
        series = ""
        import sys
        import os
        import platform
        import re

        params = {}
        if len(sys.argv) > 1 and platform.system() != 'Darwin':
            # On OSX, MacOpenFile() gets called with sys.argv's contents, so don't load anything here
            # print("Loading file", sys.argv[-1])
            preferences_reader = self.frame.dw.getPreferencesReader()
            params, leftover_args, preferences_mod = preferences_reader.getPreferences(sys.argv)
            if "src_folder" in params.get("filename", {}):
                src_folder = params["filename"]["src_folder"]
            else:
                src_folder = os.path.dirname(os.path.abspath(__file__))

            if "pack_file" in params.get("filename", {}):
                pack_filename = params["filename"]["pack_file"][0]
                try:
                    self.frame.dw.openPackage(pack_filename)
                except Exception:
                    del params["filename"]["pack_file"]
            self.frame.dw.updatePreferences(params)

            filenames = IOTools.prepareFilenames(params, src_folder=src_folder)
            if not "pack_file" in params.get("filename", {}) and os.path.exists(filenames["LHS_data"]) and os.path.exists(filenames["RHS_data"]):
                data = Data([filenames["LHS_data"], filenames["RHS_data"]]+filenames["add_info"], filenames["style_data"])
                data.loadExtensions(ext_keys=params.get("activated_extensions", []), filenames=filenames.get("extensions"), params=params)
                self.frame.dw.setData(data)
                self.frame.dw.applyVarsMask(params)
                self.frame.dw._isChanged = True
                self.frame.dw._isFromPackage = False

            if self.frame.dw.getData() is not None:
                for filename in filenames["all_queries"]:
                    if filename != "-" and os.path.isfile(filename):
                        self.frame.dw.loadRedescriptionsFromFile(filename)

        self.frame.refresh()

        if params.get("debug", False):
            # self.frame.OnPreferencesDialog(None)
            # self.frame.OnExtensionsDialog(None)
            self.frame.OnFoldsDialog(None)
            # self.frame.OnConnectionDialog(None)
            # print "No debug action..."
            # print("Loading file", sys.argv[-1])
            # self.frame.expand()

            # self.frame.OnRunTest(None)

            # ### SPLITS
            # self.frame.dw.getData().extractFolds(1, 12)
            # splits_info = self.frame.dw.getData().getFoldsInfo()
            # stored_splits_ids = sorted(splits_info["split_ids"].keys(), key=lambda x: splits_info["split_ids"][x])
            # ids = {}
            # checked = [("learn", range(1,len(stored_splits_ids))), ("test", [0])]
            # for lt, bids in checked:
            #     ids[lt] = [stored_splits_ids[bid] for bid in bids]
            # self.frame.dw.getData().assignLT(ids["learn"], ids["test"])
            # self.frame.recomputeAll()

            # # fmts = ["tiff"] #, "png"] #, "eps"]
            # fmts = ["eps"] #, "eps"]
            # fmts = ["svg", "eps"]
            # # (1641, 670), (1064, 744), (551, 375)
            # # tab, fname, dims = ("reds", "/home/egalbrun/R%d_map_2K-d100.", (1920, 1190)) ### MAP RED
            # # tab, fname, dims = ("vars", "/home/egalbrun/V%d-%d_map_2K-d100.", (2350, 1190)) ### MAP VAR
            # folder = "/home/egalbrun/figs"
            # if len(series) > 0:
            #     folder += "/"+series
            # tab, fname, dims = ("reds", folder+"/R%d_%s_2K-d100.", (1920, 1190)) ### MAP RED
            # #tab, fname, dims = ("vars", folder+"/V%d-%d_map_2K-d100.", (2500, 1190)) ### MAP VAR
            # if not os.path.exists(folder):
            #     os.mkdir(folder)
            # # for i in self.frame.tabs[tab]["tab"].getDataHdl().getAllIids():
            # for (i,what) in [(0, "MAP"), (0, "PC"), (1, "PC"), (1, "TR"), (2, "TR")]:
            #     mapV = self.frame.tabs[tab]["tab"].viewData(i, what)
            #     mapV.mapFrame.SetClientSizeWH(dims[0], dims[1])
            #     for fmt in fmts:
            #         if fmt in ["png", "svg"]:
            #             mapV.savefig((fname % (i, what))+fmt, format=fmt)
            #         else:
            #             mapV.savefig((fname % (i, what))+fmt, dpi=30, format=fmt)
            #     mapV.OnKil()

            # iid = 1
            # # self.frame.viewOpen(self.frame.getRed(iid), iid=iid, viewT="AXE_entities") #"CLM")
            # iid = (1, 33)
            # # self.frame.viewOpen(self.frame.getData().getItem(iid), iid=iid, viewT="AXE_entities")
            # self.frame.viewOpen(self.frame.getData().getItem(iid), iid=iid, viewT="MAP")

            # iids = self.frame.getData().getIidsList((0,0))
            # what = [(iid, self.frame.getData().getItem(iid)) for iid in iids]
            # # iids = self.frame.getRedLists().getIidsList(3)
            # # what = [(iid, self.frame.getRedLists().getItem(iid)) for iid in iids]
            # # self.frame.viewOpen(what, iid=-1, viewT="LRNG")

            # tab ="vars"
            # self.frame.dw.getData().getMatrix()
            # self.frame.dw.getData().selected_rows = set(range(400))
            # for i in [5]: #range(4):
            #     self.frame.tabs[tab]["tab"].viewData(i, "TR")
            # vw = self.frame.tabs[tab]["tab"].viewData((0,9), "MAP")
            #vw.updateRSets({'rset_id': 'test'})

        return True

    def BringWindowToFront(self):
        try:
            pass
            # self.frame.toolFrame.Raise()
        except:
            pass

    def OnActivate(self, event):
        pass
        # if event.GetActive():
        #     self.BringWindowToFront()
        # event.Skip()

    def MacOpenFiles(self, filenames):
        """Called for files dropped on dock icon, or opened via Finder's context menu"""
        import sys
        import os.path
        filename = filenames[0]
        # When start from command line, this gets called with the script file's name
        if filename != sys.argv[0]:
            if self.frame.dw.getData() is not None:
                if not self.frame.checkAndProceedWithUnsavedChanges():
                    return
            (p, ext) = os.path.splitext(filename)
            if ext == '.siren':
                self.frame.LoadFile(filename)
            elif ext == '.csv':

                self.frame.dw.importDataFromCSVFiles([filename, filename]+IOTools.getDataAddInfo())
                self.frame.refresh()
            else:
                wx.MessageDialog(self.frame.toolFrame, 'Unknown file type "'+ext+'" in file '+filename, style=wx.OK, caption='Unknown file type').ShowModal()

    def MacReopenApp(self):
        """Called when the doc icon is clicked, and ???"""
        self.BringWindowToFront()

    def MacNewFile(self):
        pass

    def MacPrintFile(self, filepath):
        pass


def siren_run():
    app = SirenApp(False)

    CustRenderer.BACKGROUND_SELECTED = wx.SystemSettings.GetColour(wx.SYS_COLOUR_HIGHLIGHT)
    CustRenderer.TEXT_SELECTED = wx.SystemSettings.GetColour(wx.SYS_COLOUR_HIGHLIGHTTEXT)
    CustRenderer.BACKGROUND = wx.SystemSettings.GetColour(wx.SYS_COLOUR_WINDOW)
    CustRenderer.TEXT = wx.SystemSettings.GetColour(wx.SYS_COLOUR_WINDOWTEXT)

    #app.frame = Siren()
    app.MainLoop()


def main():
    multiprocessing.freeze_support()
    siren_run()


if __name__ == '__main__':
    main()
