import wx
# from wx import ALIGN_BOTTOM, ALIGN_CENTER, ALIGN_CENTER_HORIZONTAL, ALIGN_LEFT, ALIGN_RIGHT, ALL, BOTTOM, C2S_HTML_SYNTAX, CENTER, EXPAND, HORIZONTAL, RIGHT, TOP, VERTICAL, YES_DEFAULT, YES_NO
# from wx import BoxSizer, Button,  CheckBox, Choice, Colour, ColourPickerCtrl, Dialog, GridSizer, MessageDialog, NewId, Notebook, Panel, StaticLine, StaticText, TextCtrl
# from wx import EVT_BUTTON, EVT_CHECKBOX, EVT_CHOICE, EVT_NOTEBOOK_PAGE_CHANGED, EVT_NOTEBOOK_PAGE_CHANGING, EVT_TEXT
# from wx import ID_ANY, ID_CANCEL, ID_NO

import pdb

# USAGE this class provides a wx Modal dialog to modify a dictionary of preferences managed with the PreferenceManager
# It is launched with the following command:
# def OnPreferencesDialog(self, event):
# d = PreferencesDialog(main_frame, pref_handle)
# d.ShowModal()
# d.Destroy()
# where pref_handle provide access to the preference manager and a way to update the preference dictionary
# via the following three methods:
# pref_handle.updatePreferences(vdict)
# pref_handle.getPreferences()
# pref_handle.getPreferencesManager()


class PreferencesDialog(wx.Dialog):
    """
    Creates a preferences dialog to change the settings
    """
    dialog_title = "Preferences"
    button_types = [{"name": "cancel", "label": "Cancel", "funct": "self.onCancel"},
                    {"name": "reset", "label": "Reset", "funct": "self.onReset"},
                    {"name": "rtod", "label": "ResetToDefault", "funct": "self.onResetToDefault"},
                    {"name": "apply", "label": "Apply", "funct": "self.onApply"},
                    {"name": "ok", "label": "OK", "funct": "self.onOK"}]
    buttons_up = ["reset", "apply"]
    apply_proceed_msg = 'Do you want to apply all changes or reset the values before proceeding?'
    apply_proceed_title = 'Unapplied changes'
    apply_proceed_lbl = 'Apply'

    @classmethod
    def suppress(tcl, item_id, exclude_items=None, only_items=None):
        return (exclude_items is not None and item_id in exclude_items) or (only_items is not None and item_id not in only_items)

    def __init__(self, parent, pref_handle, conf_filter=None):
        """
        Initialize the config dialog
        """
        wx.Dialog.__init__(self, parent, wx.ID_ANY, self.dialog_title, style=wx.RESIZE_BORDER | wx.DEFAULT_DIALOG_STYLE)  # , size=(550, 300))
        self.SetLayoutAdaptationMode(wx.DIALOG_ADAPTATION_MODE_ENABLED)

        self.nb = wx.Notebook(self, wx.ID_ANY, style=wx.NB_TOP)
        nb_sizer = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(nb_sizer)
        nb_sizer.Add(self.nb, 0, wx.EXPAND | wx.ALL, 5)

        self.pref_handle = pref_handle
        self.controls_map = {}
        self.objects_map = {}
        self.tabs = []

        self.cancel_change = False  # Tracks if we should cancel a page change

        for section in self.iterateSections(conf_filter):
            sec_id = wx.NewId()
            self.tabs.append(sec_id)
            self.controls_map[sec_id] = {"button": {}, "range": {},
                                         "open": {}, "boolean": {}, "single_options": {},
                                         "multiple_options": {}, "color_pick": {}}

            conf = wx.Panel(self.nb, -1)
            top_sizer = wx.BoxSizer(wx.VERTICAL)
            self.dispGUI(section, sec_id, conf, top_sizer)
            self.makeButtons(sec_id, conf, top_sizer)
            conf.SetSizer(top_sizer)

            self.setSecValuesFromDict(sec_id, self.pref_handle.getPreferences())
            self.bindSec(sec_id)

            self.nb.AddPage(conf, section.get("name"))
            top_sizer.Fit(conf)
        self.Bind(wx.EVT_NOTEBOOK_PAGE_CHANGING, self.onPageChanging)
        self.Bind(wx.EVT_NOTEBOOK_PAGE_CHANGED, self.onPageChanged)

        self.Centre()
        nb_sizer.Fit(self)

    def iterateSections(self, conf_filter):
        return self.pref_handle.getPreferencesManager().getTopSections(conf_filter)

    def dispGUI(self, parameters, sec_id, frame, top_sizer, exclude_items=None, only_items=None):
        if parameters.get("empty", False):
            return

        for ty in ["open", "range"]:
            # ADD TEXT PARAMETERS
            if len(parameters[ty]) > 0:
                item_ids = [i for i in parameters[ty] if not self.suppress(i, exclude_items, only_items)]
                text_sizer = wx.GridSizer(rows=len(item_ids), cols=2, hgap=5, vgap=5)
                for item_id in item_ids:

                    item = self.pref_handle.getPreferencesManager().getItem(item_id)
                    ctrl_id = wx.NewId()
                    label = wx.StaticText(frame, wx.ID_ANY, item.getLabel()+":")
                    self.controls_map[sec_id][ty][item_id] = wx.TextCtrl(frame, ctrl_id, "")
                    self.objects_map[ctrl_id] = (sec_id, ty, item_id)
                    text_sizer.Add(label, 0, wx.ALIGN_RIGHT)
                    text_sizer.Add(self.controls_map[sec_id][ty][item_id], 0, wx.EXPAND)

                top_sizer.Add(text_sizer, 0, wx.EXPAND | wx.ALL, 5)

        # ADD BOOLEAN PARAMETERS
        # so_sizer = wx.BoxSizer(wx.HORIZONTAL)
        if len(parameters["boolean"]) > 0:
            item_ids = [i for i in parameters["boolean"] if not self.suppress(i, exclude_items, only_items)]
            so_sizer = wx.GridSizer(rows=len(item_ids), cols=2, hgap=5, vgap=5)
            for item_id in item_ids:

                item = self.pref_handle.getPreferencesManager().getItem(item_id)
                ctrl_id = wx.NewId()
                label = wx.StaticText(frame, wx.ID_ANY, item.getLabel()+":")
                self.controls_map[sec_id]["boolean"][item_id] = wx.Choice(frame, ctrl_id, choices=item.getOptionsText())
                self.objects_map[ctrl_id] = (sec_id, "boolean", item_id)
                so_sizer.Add(label, 0, wx.ALIGN_RIGHT)
                so_sizer.Add(self.controls_map[sec_id]["boolean"][item_id], 0)

            top_sizer.Add(so_sizer, 0,  wx.EXPAND | wx.ALL, 5)

        # ADD SINGLE OPTIONS PARAMETERS
        # so_sizer = wx.BoxSizer(wx.HORIZONTAL)
        if len(parameters["single_options"]) > 0:
            item_ids = [i for i in parameters["single_options"] if not self.suppress(i, exclude_items, only_items)]
            so_sizer = wx.GridSizer(rows=len(item_ids), cols=2, hgap=5, vgap=5)
            for item_id in item_ids:

                item = self.pref_handle.getPreferencesManager().getItem(item_id)
                ctrl_id = wx.NewId()
                label = wx.StaticText(frame, wx.ID_ANY, item.getLabel()+":")
                self.controls_map[sec_id]["single_options"][item_id] = wx.Choice(frame, ctrl_id, choices=item.getOptionsText())
                self.objects_map[ctrl_id] = (sec_id, "single_options", item_id)
                so_sizer.Add(label, 0, wx.ALIGN_RIGHT)
                so_sizer.Add(self.controls_map[sec_id]["single_options"][item_id], 0)

            top_sizer.Add(so_sizer, 0,  wx.EXPAND | wx.ALL, 5)

        # ADD MULTIPLE OPTIONS PARAMETERS
        if len(parameters["multiple_options"]) > 0:
            item_ids = [i for i in parameters["multiple_options"] if not self.suppress(i, exclude_items, only_items)]
            mo_sizer = wx.GridSizer(rows=len(item_ids), cols=2, hgap=5, vgap=5)
            for item_id in item_ids:
                item = self.pref_handle.getPreferencesManager().getItem(item_id)

                # mo_sizer_t = wx.BoxSizer(wx.HORIZONTAL)
                label = wx.StaticText(frame, wx.ID_ANY, item.getLabel()+":")
                # mo_sizer_t.Add(label, 0, wx.ALIGN_LEFT)
                mo_sizer.Add(label, 0, wx.ALIGN_RIGHT)
                mo_sizer_v = wx.BoxSizer(wx.HORIZONTAL)
                self.controls_map[sec_id]["multiple_options"][item_id] = {}
                for option_key, option_label in enumerate(item.getOptionsText()):
                    ctrl_id = wx.NewId()
                    self.controls_map[sec_id]["multiple_options"][item_id][option_key] = wx.CheckBox(frame, ctrl_id, option_label, style=wx.ALIGN_RIGHT)
                    self.objects_map[ctrl_id] = (sec_id, "multiple_options", item_id, option_key)
                    mo_sizer_v.Add(self.controls_map[sec_id]["multiple_options"][item_id][option_key], 0)

                # top_sizer.Add(mo_sizer_t, 0, wx.EXPAND|wx.ALL, 5)
                # top_sizer.Add(mo_sizer_v, 0, wx.EXPAND|wx.ALL, 5)
                mo_sizer.Add(mo_sizer_v, 0, wx.EXPAND)
            top_sizer.Add(mo_sizer, 0, wx.EXPAND | wx.ALL, 5)

        # ADD COLOR PICK PARAMETERS
        if len(parameters["color_pick"]) > 0:
            item_ids = [i for i in parameters["color_pick"] if not self.suppress(i, exclude_items, only_items)]
            mo_sizer = wx.GridSizer(rows=len(item_ids), cols=2, hgap=5, vgap=5)
            for item_id in item_ids:
                item = self.pref_handle.getPreferencesManager().getItem(item_id)

                ctrl_id = wx.NewId()
                label = wx.StaticText(frame, wx.ID_ANY, item.getLabel()+":")
                mo_sizer.Add(label, 0, wx.ALIGN_RIGHT)
                self.controls_map[sec_id]["color_pick"][item_id] = wx.ColourPickerCtrl(frame, ctrl_id, style=wx.ALIGN_RIGHT)
                self.objects_map[ctrl_id] = (sec_id, "color_pick", item_id)
                mo_sizer.Add(self.controls_map[sec_id]["color_pick"][item_id], 0)

            top_sizer.Add(mo_sizer, 0, wx.EXPAND | wx.ALL, 5)

        for i, k in enumerate(parameters["subsections"]):

            # ADD SECTION TITLE
            title_sizer = wx.BoxSizer(wx.HORIZONTAL)
            if i > 0:
                top_sizer.Add(wx.StaticLine(frame), 0, wx.EXPAND | wx.ALL, 5)
            title = wx.StaticText(frame, wx.ID_ANY, "--- %s ---" % k.get("name", ""))
            title_sizer.Add(title, 0, wx.ALIGN_CENTER)

            top_sizer.Add(title_sizer, 0, wx.CENTER)

            sec_sizer = wx.BoxSizer(wx.VERTICAL)
            self.dispGUI(k, sec_id, frame, sec_sizer, exclude_items=exclude_items, only_items=only_items)
            top_sizer.Add(sec_sizer, 0,  wx.EXPAND | wx.ALL, 5)

    def makeButtons(self, sec_id, frame, top_sizer):
        btn_sizer = wx.StdDialogButtonSizer()

        for button in self.button_types:
            btnId = wx.NewId()
            btn = wx.Button(frame, btnId, button["label"])
            frame.Bind(wx.EVT_BUTTON, eval(button["funct"]), btn)
            btn_sizer.Add(btn, 0)
            self.controls_map[sec_id]["button"][button["name"]] = btn
            self.objects_map[btnId] = (sec_id, "button", button["name"])

        top_sizer.Add(btn_sizer, 0, flag=wx.ALIGN_CENTER | wx.ALL, border=5)  # wx.ALIGN_BOTTOM|wx.ALIGN_CENTER_HORIZONTAL|

    def onPageChanging(self, event):
        sec_id = self.tabs[event.GetOldSelection()]

        if self.detectedChange(sec_id):
            # TODO:: FOR NOW SIMPLY APPLY WITHOUT ASKING FOR CONFIRMATION
            # save_dlg = wx.MessageDialog(self.toolFrame, 'Do you want to apply changes before changing tab, otherwise they will be lost?', caption="Warning!", style=wx.YES_NO|wx.YES_DEFAULT)
            # if save_dlg.ShowModal() != wx.ID_NO:
            #     return
            # save_dlg.Destroy()

            dlg = ApplyResetCancelDialog(parent=self, title=self.apply_proceed_title, msg=self.apply_proceed_msg, apply_lbl=self.apply_proceed_lbl)
            res = dlg.ShowModal()
            dlg.Destroy()
            if res == 1:
                self._apply(sec_id)
            elif res == 2:
                self._reset(sec_id)
            else:
                self.cancel_change = True  # This tell onPageChanged to revert

    def onPageChanged(self, event):
        if self.cancel_change:
            self.nb.ChangeSelection(event.GetOldSelection())
        self.cancel_change = False

    def onCancel(self, event):
        self.EndModal(0)

    def onReset(self, event):
        if event.GetId() in self.objects_map:
            sec_id = self.objects_map[event.GetId()][0]
            self._reset(sec_id)

    def _reset(self, sec_id):
        self.setSecValuesFromDict(sec_id, self.pref_handle.getPreferences())
        self.upButtons(sec_id, on_action="off")

    def onResetToDefault(self, event):
        if event.GetId() in self.objects_map:
            sec_id = self.objects_map[event.GetId()][0]
            self.setSecValuesFromDict(sec_id, self.pref_handle.getPreferencesManager().getDefaultValues())

    def onApply(self, event):
        if event.GetId() in self.objects_map:
            sec_id = self.objects_map[event.GetId()][0]
            self._apply(sec_id)

    def _apply(self, sec_id):
        vdict = self.getSecValuesDict(sec_id)
        self.pref_handle.updatePreferences(vdict)
        self.setSecValuesFromDict(sec_id, self.pref_handle.getPreferences())
        self.upButtons(sec_id, on_action="off")

    def onOK(self, event):
        self.onApply(event)
        self.onClose()

    def changeHappened(self, event):
        if event.GetId() in self.objects_map:
            sec_id = self.objects_map[event.GetId()][0]
            self.upButtons(sec_id, on_action="on")

    def detectedChange(self, sec_id):
        return len(self.buttons_up) > 0 and self.controls_map[sec_id]["button"][self.buttons_up[0]].IsEnabled()

    def upButtons(self, sec_id, on_action="off"):
        if on_action is None:
            return
        for b in self.buttons_up:
            if on_action == "on":
                self.controls_map[sec_id]["button"][b].Enable()
            else:
                self.controls_map[sec_id]["button"][b].Disable()

    def onClose(self):
        self.EndModal(0)

    def setSecValuesFromDict(self, sec_id, vdict, exclude_items=None, only_items=None):
        for ty in ["open", "range"]:
            for item_id, ctrl_txt in self.controls_map[sec_id][ty].items():
                if not self.suppress(item_id, exclude_items, only_items):
                    v = self.pref_handle.getPreferencesManager().getItem(item_id).getParamText(vdict[item_id])
                    ctrl_txt.SetValue(v)

        for item_id, ctrl_bool in self.controls_map[sec_id]["boolean"].items():
            if not self.suppress(item_id, exclude_items, only_items):
                v = self.pref_handle.getPreferencesManager().getItem(item_id).getParamIndex(vdict[item_id])
                ctrl_bool.SetSelection(v)

        for item_id, ctrl_single in self.controls_map[sec_id]["single_options"].items():
            if not self.suppress(item_id, exclude_items, only_items):
                v = self.pref_handle.getPreferencesManager().getItem(item_id).getParamIndex(vdict[item_id])
                ctrl_single.SetSelection(v)

        for item_id, ctrl_multiple in self.controls_map[sec_id]["multiple_options"].items():
            if not self.suppress(item_id, exclude_items, only_items):
                v = self.pref_handle.getPreferencesManager().getItem(item_id).getParamIndex(vdict[item_id])
                for check_id, check_box in ctrl_multiple.items():
                    check_box.SetValue(check_id in v)

        for item_id, colour_txt in self.controls_map[sec_id]["color_pick"].items():
            if not self.suppress(item_id, exclude_items, only_items):
                colour_txt.SetColour(wx.Colour(*vdict[item_id]))

    def bindSec(self, sec_id):
        self.upButtons(sec_id, on_action="off")

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

    def getSecValuesDict(self, sec_id, exclude_items=None, only_items=None):
        vdict = {}
        for ty in ["open", "range"]:
            for item_id, ctrl_txt in self.controls_map[sec_id][ty].items():
                if not self.suppress(item_id, exclude_items, only_items):
                    pit = self.pref_handle.getPreferencesManager().getItem(item_id)
                    vdict[item_id] = pit.getParamValueOrDefault(ctrl_txt.GetValue())

        for item_id, ctrl_bool in self.controls_map[sec_id]["boolean"].items():
            if not self.suppress(item_id, exclude_items, only_items):
                pit = self.pref_handle.getPreferencesManager().getItem(item_id)
                vdict[item_id] = pit.getParamValueOrDefault(ctrl_bool.GetSelection())

        for item_id, ctrl_single in self.controls_map[sec_id]["single_options"].items():
            if not self.suppress(item_id, exclude_items, only_items):
                pit = self.pref_handle.getPreferencesManager().getItem(item_id)
                vdict[item_id] = pit.getParamValueOrDefault(ctrl_single.GetSelection())

        for item_id, ctrl_multiple in self.controls_map[sec_id]["multiple_options"].items():
            if not self.suppress(item_id, exclude_items, only_items):
                tmp_opts = [check_id for check_id, check_box in ctrl_multiple.items() if check_box.GetValue()]
                pit = self.pref_handle.getPreferencesManager().getItem(item_id)
                vdict[item_id] = pit.getParamValueOrDefault(tmp_opts)

        for item_id, ctrl_txt in self.controls_map[sec_id]["color_pick"].items():
            if not self.suppress(item_id, exclude_items, only_items):
                pit = self.pref_handle.getPreferencesManager().getItem(item_id)
                vdict[item_id] = pit.getParamValueOrDefault(ctrl_txt.GetColour().GetAsString(wx.C2S_HTML_SYNTAX))
        return vdict


class ApplyResetCancelDialog(wx.Dialog):
    """Shows a dialog with three buttons: Apply, Reset, and Cancel.
    Returns 1 for apply, 2 for reset, and -1 for cancel"""

    def __init__(self, parent, title="", msg="", apply_lbl="Apply"):
        super(ApplyResetCancelDialog, self).__init__(parent=parent, title=title)  # , size=(300, 150))

        top_sizer = wx.BoxSizer(wx.VERTICAL)

        txt = wx.StaticText(self, label=msg)
        txt.Wrap(300)
        # txt = self.CreateTextSizer(msg)

        btn_sizer = wx.StdDialogButtonSizer()

        applyBtn = wx.Button(self, id=wx.ID_ANY, label=apply_lbl)
        resetBtn = wx.Button(self, id=wx.ID_ANY, label="Reset")
        cancelBtn = wx.Button(self, id=wx.ID_CANCEL, label="Cancel")

        btn_sizer.Add(cancelBtn, flag=wx.ALIGN_LEFT | wx.RIGHT, border=20)
        btn_sizer.Add(resetBtn, flag=wx.ALIGN_RIGHT)
        btn_sizer.Add(applyBtn, flag=wx.ALIGN_RIGHT)

        top_sizer.Add(txt, flag=wx.ALL | wx.ALIGN_CENTER, border=20)
        top_sizer.Add(btn_sizer, flag=wx.ALIGN_CENTER | wx.TOP | wx.BOTTOM, border=5)

        self.SetSizer(top_sizer)
        top_sizer.Fit(self)

        applyBtn.Bind(wx.EVT_BUTTON, self.onApply)
        resetBtn.Bind(wx.EVT_BUTTON, self.onReset)
        cancelBtn.Bind(wx.EVT_BUTTON, self.onCancel)

    def onApply(self, e):
        self.EndModal(1)

    def onReset(self, e):
        self.EndModal(2)

    def onCancel(self, e):
        self.EndModal(-1)
