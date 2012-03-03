import sys
import pdb
import wx

EVT_LOGGER_ID = wx.NewId()
class LoggerEvent(wx.PyEvent):
    """Simple event to carry arbitrary logging data."""
    def __init__(self, data):
        """Init Result Event."""
        wx.PyEvent.__init__(self)
        self.SetEventType(EVT_LOGGER_ID)
        self.data = data
        
class Log:

    def EVT_LOGGER(win, func):
        """Define Logger Event."""
        win.Connect(-1, -1, EVT_LOGGER_ID, func)
    EVT_LOGGER = staticmethod(EVT_LOGGER)

    def __init__(self,  verbosity=1, output = '-'):
        self.out = None
        self._notify_window = None
        if type(output) == tuple:
            self._notify_window = output[0]
            self.out = -1
        elif output == '-':
            self.out = sys.stdout
        elif output != None  and len(output) > 0:
            self.out = open(output, 'w')
        self.verbosity = verbosity

    def printL(self, level, message):
        if self.out != None and self.verbosity >= level:
            if self._notify_window != None:
                wx.PostEvent(self._notify_window, LoggerEvent("%s\n" % message))
            else:
                self.out.write("%s\n" % message)
        
        
