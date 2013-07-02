import wx
import threading
import time
import sys
# import wx.lib.agw.pybusyinfo as PBI
import wx.lib.dialogs

from reremi.classMiner import Miner

import pdb

# Thread class that executes processing
class WorkerThread(threading.Thread):
    def __init__(self, id, data, preferences, logger, params=None):
        """Init Expander Thread Class."""
        threading.Thread.__init__(self)
        self.proj = ProjFactory.getProj(self.parent.dw.getData(), rid)
        self.miner = Miner(data, preferences, logger, id)
        self.params = params
        self.start()

    def run(self):
        pass

    def abort(self):
        self.miner.kill()

class MinerThread(WorkerThread):
    """Miner Thread Class."""

    def run(self):
        self.miner.full_run()

class ExpanderThread(WorkerThread):
    """Expander Thread Class."""

    def run(self):
        self.miner.part_run(self.params)


# Thread class that executes processing
class ProjThread(threading.Thread):
    def __init__(self, id, proj):
        """Init Proj Thread Class."""
        threading.Thread.__init__(self)
        self.proj = proj
        self.start()

    def run(self):
        self.proj.do()
        pass

    def abort(self):
        self.proj.kill()



class Message(wx.PyEvent):
    TYPES_MESSAGES = {'*': wx.NewId(), 'log': wx.NewId(), 'time': wx.NewId(), 'result': wx.NewId(), 'progress': wx.NewId(), 'status': wx.NewId()}
    
    """Simple event for communication purposes."""
    def __init__(self, type_event, data):
        """Init Result Event."""
        wx.PyEvent.__init__(self)
        self.SetEventType(type_event)
        self.data = data

    def sendMessage(output, message, type_message, source):
        if Message.TYPES_MESSAGES.has_key(type_message):
           wx.PostEvent(output, Message(Message.TYPES_MESSAGES[type_message], (source, message)))
    sendMessage = staticmethod(sendMessage)


class CErrorDialog:

    def showBox(output, message, type_message, source):
        if output.busyDlg is not None:
            del output.busyDlg
            output.busyDlg = None
        dlg = wx.MessageDialog(output.toolFrame, message, style=wx.OK|wx.ICON_EXCLAMATION|wx.STAY_ON_TOP, caption=type_message)
        dlg.ShowModal()
        dlg.Destroy()
    showBox = staticmethod(showBox)
 
