import wx
### from wx import ALIGN_BOTTOM, ALIGN_CENTER, ALIGN_CENTER_HORIZONTAL, ALIGN_RIGHT, ALL, ID_ANY, CENTER, EXPAND, HORIZONTAL, VERTICAL
### from wx import BoxSizer, Button, CheckBox, Choice, Dialog, GridSizer, NewId, Panel, StaticLine, StaticText
### from wx import EVT_BUTTON, EVT_CHECKBOX, EVT_CHOICE, EVT_CLOSE, EVT_TEXT

import pdb
from .classPreferencesDialog import PreferencesDialog


class FoldsDialog(PreferencesDialog):
    """
    Creates a preferences dialog to setup data folds
    """
    DEACTIVATED_LBL = "Deactivated"
    AUTOMATIC_LBL = "Automatic"
    SOURCE_PARAM = "folds_col"
    button_types = [{"name": "cancel", "label": "Cancel", "funct": "self.onCancel"},
                    {"name": "rtod", "label": "ResetToDefault", "funct": "self.onResetToDefault"},
                    {"name": "prepare", "label": "Prepare", "funct": "self.onPrepare"},
                    {"name": "save_col", "label": "SaveToColumn", "funct": "self.onSaveToC"},
                    {"name": "apply", "label": "Apply", "funct": "self.onApply"}]

    def __init__(self, parent, pref_handle, conf_filter=None, tool=None):
        """
        Initialize the config dialog
        """
        wx.Dialog.__init__(self, parent, wx.ID_ANY, 'Folds setup')  # , size=(550, 300))
        self.SetLayoutAdaptationMode(wx.DIALOG_ADAPTATION_MODE_ENABLED)

        self.parent = parent
        self.pref_handle = pref_handle
        self.data_handle = pref_handle
        self.tool = tool
        self.info_box = None
        self.boxes_sizers = {}
        self.controls_map = {}
        self.objects_map = {}
        self.tabs = []

        self.sec_id = None
        self.no_problem = True

        self.cancel_change = False  # Tracks if we should cancel a page change

        self.folds_info = self.data_handle.getData().getFoldsInfo()
        self.cands_folds = self.data_handle.getData().findCandsFolds()
        self.source_cands = [self.DEACTIVATED_LBL, self.AUTOMATIC_LBL] + \
            [self.data_handle.getData().col(side, colid).getName() for (side, colid) in self.cands_folds]
        self.controls_map["add"] = {}

        secs = self.pref_handle.getPreferencesManager().getTopSections(conf_filter)
        if len(secs) == 1:
            section = secs[0]
            sec_id = wx.NewId()
            self.tabs.append(sec_id)
            self.controls_map[sec_id] = {"button": {}, "range": {},
                                         "open": {}, "boolean": {}, "single_options": {},
                                         "multiple_options": {}, "color_pick": {}}

            self.sec_id = sec_id
            # conf = wx.Panel(self.nb, -1)
            top_sizer = wx.BoxSizer(wx.VERTICAL)
            self.dispGUI(section, sec_id, self, top_sizer, exclude_items=[self.SOURCE_PARAM])
            self.dispInfo(self, top_sizer)
            self.makeButtons(sec_id, self, top_sizer)
            self.getFoldsIDS()
            self.makeAssignBoxes(self, top_sizer)
            self.SetSizer(top_sizer)
            self.top_sizer = top_sizer

            self.setSecValuesFromDict(sec_id, self.pref_handle.getPreferences(), exclude_items=[self.SOURCE_PARAM])
            self.controls_map[self.sec_id]["button"]["prepare"].Disable()
            self.controls_map[self.sec_id]["button"]["save_col"].Disable()

            for txtctrl in self.controls_map[sec_id]["open"].values():
                self.Bind(wx.EVT_TEXT, self.changeHappened, txtctrl)
            for txtctrl in self.controls_map[sec_id]["range"].values():
                self.Bind(wx.EVT_TEXT, self.changeHappened, txtctrl)
            for choix in self.controls_map[sec_id]["boolean"].values():
                self.Bind(wx.EVT_CHOICE, self.changeHappened, choix)
            for choix in self.controls_map[sec_id]["single_options"].values():
                self.Bind(wx.EVT_CHOICE, self.changeHappened, choix)
            for chkset in self.controls_map[sec_id]["multiple_options"].values():
                for chkbox in chkset.values():
                    self.Bind(wx.EVT_CHECKBOX, self.changeHappened, chkbox)
        self.setSelectedSource()

        self.top_sizer.Fit(self)
        self.Centre()
        # self.SetSize((700, -1))
        self.Bind(wx.EVT_CLOSE, self.onClose)

    def dispInfo(self, frame, top_sizer):
        sec_id = "add"

        # TITLE
        title_sizer = wx.BoxSizer(wx.HORIZONTAL)
        top_sizer.Add(wx.StaticLine(frame), 0, wx.EXPAND | wx.ALL, 5)
        title = wx.StaticText(frame, wx.ID_ANY, "--- %s ---" % "Assignments")
        title_sizer.Add(title, 0, wx.ALIGN_CENTER)
        top_sizer.Add(title_sizer, 0, wx.CENTER)

        # Sources
        so_sizer = wx.GridSizer(rows=1, cols=2, hgap=5, vgap=5)

        ctrl_id = wx.NewId()
        item_id = "source"
        label = wx.StaticText(frame, wx.ID_ANY, "Source:")
        self.controls_map[sec_id][item_id] = wx.Choice(frame, ctrl_id, choices=self.source_cands)
        self.objects_map[ctrl_id] = (sec_id, "single_options", item_id)
        self.Bind(wx.EVT_CHOICE, self.changeSource, self.controls_map[sec_id][item_id])

        so_sizer.Add(label, 0, wx.ALIGN_RIGHT)
        so_sizer.Add(self.controls_map[sec_id][item_id], 0)

        top_sizer.Add(so_sizer, 0,  wx.EXPAND | wx.ALL, 5)

        # ASSIGNMENTS
        mo_sizer = wx.GridSizer(rows=2, cols=2, hgap=5, vgap=5)
        for (item_id, lbl) in [("learn", "Learn"), ("test", "Test")]:

            label = wx.StaticText(frame, wx.ID_ANY, lbl+":")
            mo_sizer.Add(label, 0, wx.ALIGN_RIGHT)
            self.boxes_sizers[item_id] = wx.BoxSizer(wx.HORIZONTAL)
            self.controls_map[sec_id][item_id] = {}

            mo_sizer.Add(self.boxes_sizers[item_id], 0, wx.EXPAND | wx.RESERVE_SPACE_EVEN_IF_HIDDEN)
        top_sizer.Add(mo_sizer, 0, wx.EXPAND | wx.ALL, 5)

    def makeButtons(self, sec_id, frame, top_sizer):
        btn_sizer = wx.StdDialogButtonSizer()

        for button in self.button_types:
            btnId = wx.NewId()
            btn = wx.Button(frame, btnId, button["label"])
            frame.Bind(wx.EVT_BUTTON, eval(button["funct"]), btn)
            btn_sizer.Add(btn, 0)
            self.controls_map[sec_id]["button"][button["name"]] = btn
            self.objects_map[btnId] = (sec_id, "button", button["name"])

        top_sizer.Add(btn_sizer, 0, wx.ALIGN_CENTER_HORIZONTAL | wx.ALL, 5)  # wx.ALIGN_BOTTOM|

    def getFoldsIDS(self):
        if self.folds_info is None:
            self.stored_folds_ids = []
        else:
            self.stored_folds_ids = sorted(self.folds_info["fold_ids"].keys(), key=lambda x: self.folds_info["fold_ids"][x])

    def onPrepare(self, event):
        self.getDataFolds()
        self.getFoldsIDS()
        self.destroyAssignBoxes(self, self.top_sizer)
        self.makeAssignBoxes(self, self.top_sizer)
        self.controls_map[self.sec_id]["button"]["prepare"].Disable()
        if self.data_handle.getData().hasAutoFolds():
            self.controls_map[self.sec_id]["button"]["save_col"].Enable()

        # self.top_sizer.Fit(self)
        # self.SetSize((700, -1))

    def onApply(self, event):
        source_pos = self.controls_map["add"]["source"].GetCurrentSelection()
        vdict = self.getSecValuesDict(self.sec_id)
        if source_pos > 1:
            vdict[self.SOURCE_PARAM] = self.source_cands[source_pos]
        self.pref_handle.updatePreferences(vdict)
        if self.source_cands[source_pos] == self.DEACTIVATED_LBL:
            self.data_handle.assignLT()
        else:
            ids = {}
            for lt in ["learn", "test"]:
                ids[lt] = [self.stored_folds_ids[bid] for bid, box in self.controls_map["add"][lt].items() if box.IsChecked()]
            self.data_handle.assignLT(ids["learn"], ids["test"])
        self.EndModal(0)

    def makeAssignBoxes(self, frame, top_sizer, sec_id="add"):
        folds = self.stored_folds_ids
        checked = [("learn", []), ("test", [])]
        if len(self.data_handle.getData().getLTsids()) > 0:
            ltsids = self.data_handle.getData().getLTsids()
            checked = [(lbl, [self.folds_info["fold_ids"][kk] for kk in ltsids[lbl]]) for lbl in ["learn", "test"]]
        elif len(folds) == 1:
            checked = [("learn", [0]), ("test", [0])]
        elif len(folds) > 1:
            checked = [("learn", range(1, len(folds))), ("test", [0])]
        for (item_id, cck) in checked:
            for option_key, option_label in enumerate(folds):
                ctrl_id = wx.NewId()
                self.controls_map[sec_id][item_id][option_key] = wx.CheckBox(frame, ctrl_id, option_label, style=wx.ALIGN_RIGHT)
                self.controls_map[sec_id][item_id][option_key].SetValue(option_key in cck)
                self.objects_map[ctrl_id] = (sec_id, item_id, option_key)
                self.boxes_sizers[item_id].Add(self.controls_map[sec_id][item_id][option_key], 0)
        if len(folds) > 0:
            self.controls_map[self.sec_id]["button"]["apply"].Enable()
        else:
            self.controls_map[self.sec_id]["button"]["apply"].Disable()
        top_sizer.Layout()

    def destroyAssignBoxes(self, frame, top_sizer, sec_id="add"):
        for item_id in ["test", "learn"]:
            self.boxes_sizers[item_id].Clear()  # delete_windows=True)
            keys = list(self.controls_map[sec_id][item_id].keys())
            for key in keys:
                self.controls_map[sec_id][item_id][key].Destroy()
                del self.controls_map[sec_id][item_id][key]

    def changeHappened(self, event):
        source_pos = self.controls_map["add"]["source"].GetCurrentSelection()
        if self.source_cands[source_pos] == self.AUTOMATIC_LBL:
            self.controls_map[self.sec_id]["button"]["prepare"].Enable()
        # if event.GetId() in self.objects_map.keys():
        #     sec_id = self.objects_map[event.GetId()][0]
        #     self.controls_map[sec_id]["button"]["rtod"].Enable()

    def changeSource(self, event):
        if self.controls_map["add"]["source"].GetSelection() != 0:
            self.controls_map[self.sec_id]["button"]["prepare"].Enable()
        else:
            self.controls_map[self.sec_id]["button"]["prepare"].Disable()

    def onClose(self, event=None):
        self.EndModal(0)

    def onCancel(self, event):
        self.EndModal(0)

    def getDataFolds(self):
        source_pos = self.controls_map["add"]["source"].GetCurrentSelection()
        if self.source_cands[source_pos] == self.DEACTIVATED_LBL:
            pass
        elif self.source_cands[source_pos] == self.AUTOMATIC_LBL:
            vdict = self.getSecValuesDict(self.sec_id)
            self.pref_handle.updatePreferences(vdict)
            self.data_handle.getData().getFold(self.pref_handle.getPreference("nb_folds"),
                                               self.pref_handle.getPreference("coo_dim"),
                                               self.pref_handle.getPreference("grain"))
        else:
            (side, colid) = self.cands_folds[source_pos-2]
            self.data_handle.extractFolds(side, colid)
        self.folds_info = self.data_handle.getData().getFoldsInfo()
        self.setSelectedSource()

    def setSelectedSource(self):
        map_source = dict([(v, k) for (k, v) in enumerate(self.source_cands)])
        source_pref = self.pref_handle.getPreference(self.SOURCE_PARAM)
        if source_pref in map_source:
            source_name = source_pref
        elif self.folds_info is None:
            source_name = self.DEACTIVATED_LBL
        elif self.folds_info["source"] != "data":
            source_name = self.AUTOMATIC_LBL
        else:
            source_name = self.folds_info["parameters"]["colname"]
        source_pos = map_source.get(source_name, -1)
        self.controls_map["add"]["source"].Select(source_pos)
        self.changeSource(None)

    def onSaveToC(self, event=None):
        if self.data_handle.getData().hasAutoFolds():
            self.data_handle.addFoldsCol()
            self.controls_map[self.sec_id]["button"]["save_col"].Disable()
