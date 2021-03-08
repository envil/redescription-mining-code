import os.path
import wx 

import pdb

from .classPreferencesDialog import PreferencesDialog

class ExtensionsDialog(PreferencesDialog):
    """
    Creates a preferences dialog to change the settings
    """
    dialog_title = "Extensions"
    sections_skip = []
    button_types = [{"name":"cancel", "label":"Cancel", "funct": "self.onCancel"},
             {"name":"reset", "label":"Reset", "funct": "self.onReset"},
             {"name":"rtod", "label":"ResetToDefault", "funct": "self.onResetToDefault"},
             {"name":"apply", "label":"(Re)Init", "funct": "self.onApply"},
             {"name":"ok", "label":"OK", "funct": "self.onOK"}]
    buttons_up = ["reset"]
    apply_proceed_msg = 'Do you want to (re)init the extension or reset the values before proceeding?'
    apply_proceed_title = 'Unapplied changes'
    apply_proceed_lbl = '(Re)Init'

    open_dir = os.path.expanduser('~/')
    wcd = 'All files|*|CSV files|*.csv'

    def __init__(self, parent, pref_handle):
        PreferencesDialog.__init__(self, parent, pref_handle)
        self.loc_open_dir = self.open_dir
        self.files_changed = True
        
    def changeActivate(self, event):
        if event.GetId() in self.objects_map:
            sec_id = self.objects_map[event.GetId()][0]
            self.upButtons(sec_id, on_action=None)
    
    def detectedChange(self, sec_id):
        return self.controls_map[sec_id]["button"]["reset"].IsEnabled() and self.controls_map[sec_id]["activate"].IsChecked()
            
    def upButtons(self, sec_id, on_action="off"):
        PreferencesDialog.upButtons(self, sec_id, on_action)
        if self.controls_map[sec_id]["activate"].IsChecked() and on_action != "off": # and self.files_changed:
            self.controls_map[sec_id]["button"]["apply"].Enable()
        else:
            self.controls_map[sec_id]["button"]["apply"].Disable()
        
    
    def iterateSections(self):
        section_name = "Extensions"
        ti, topsection = self.pref_handle.getPreferencesManager().getSectionByName(section_name)
        available_exts = sorted(self.pref_handle.getData().getAvailableExtensionKeys())
        params_exts = dict([(sec.get("name"), sec) for sec in topsection.get("subsections", [])])
        for sec in available_exts:
            if sec in params_exts:
                yield params_exts[sec]
            else:
                yield {"name": sec, "empty": True}
    
    def dispGUI(self, parameters, sec_id, frame, top_sizer):

        sec_name = parameters.get("name")
        self.controls_map[sec_id]["ext_key"] = sec_name
        ########## ACTIVATION BOX
        sec_sizer= wx.BoxSizer(wx.VERTICAL)
        so_sizer = wx.GridSizer(rows=1, cols=2, hgap=5, vgap=5)
        ctrl_id = wx.NewId()
        label = wx.StaticText(frame, wx.ID_ANY, "Active :")
        self.controls_map[sec_id]["activate"] = wx.CheckBox(frame, ctrl_id, "", style=wx.ALIGN_RIGHT)
        self.controls_map[sec_id]["activate"].SetValue(self.pref_handle.getData().hasActiveExtension(sec_name))
        self.objects_map[ctrl_id]= (sec_id, "activate", None)        
        so_sizer.Add(label, 0, wx.ALIGN_RIGHT)
        so_sizer.Add(self.controls_map[sec_id]["activate"], 0)
        sec_sizer.Add(so_sizer, 0,  wx.EXPAND|wx.ALL, 5)        
        top_sizer.Add(sec_sizer, 0,  wx.EXPAND|wx.ALL, 5)

        ########## FILES
        files_dict = self.pref_handle.getData().getExtensionsFilesDict(exts=[sec_name])
        self.controls_map[sec_id]["files"] = {}
        if len(files_dict) > 0:
            self.files_changed = False
            top_sizer.Add(wx.StaticLine(frame), 0, wx.EXPAND|wx.ALL, 5)
            title_sizer = wx.BoxSizer(wx.HORIZONTAL)
            title = wx.StaticText(frame, wx.ID_ANY, "--- Files ---")
            title_sizer.Add(title, 0, wx.ALIGN_CENTER)
            top_sizer.Add(title_sizer, 0, wx.CENTER)
            
            text_sizer = wx.FlexGridSizer(rows=len(files_dict), cols=3, hgap=5, vgap=5)
            for item_id, fdn in files_dict.items():                
                ctrl_id = wx.NewId()
                btn_id = wx.NewId()
                label = wx.StaticText(frame, wx.ID_ANY, item_id.replace("extf_", "")+":")
                self.controls_map[sec_id]["files"][item_id] = {}
                self.controls_map[sec_id]["files"][item_id]["txt"] = wx.TextCtrl(frame, ctrl_id, "", size=(500,10), style=wx.TE_READONLY)
                self.controls_map[sec_id]["files"][item_id]["path"] = ""
                self.controls_map[sec_id]["files"][item_id]["btn"] = wx.Button(frame, btn_id, label='Choose', name=item_id)
                self.objects_map[ctrl_id]= (sec_id, "files", item_id)
                self.objects_map[btn_id]= (sec_id, "file_btn", item_id)
                text_sizer.AddMany([(label, 0, wx.ALIGN_RIGHT),
                                   (self.controls_map[sec_id]["files"][item_id]["txt"], 1, wx.EXPAND),
                                   (self.controls_map[sec_id]["files"][item_id]["btn"], 0)])
                
            top_sizer.Add(text_sizer, 0, wx.EXPAND|wx.ALL, 5)

        ########## PARAMETERS
        if not parameters.get("empty", False):
            top_sizer.Add(wx.StaticLine(frame), 0, wx.EXPAND|wx.ALL, 5)
            title_sizer = wx.BoxSizer(wx.HORIZONTAL)
            title = wx.StaticText(frame, wx.ID_ANY, "--- Parameters ---")
            title_sizer.Add(title, 0, wx.ALIGN_CENTER)
        
            top_sizer.Add(title_sizer, 0, wx.CENTER)
        
            sec_sizer= wx.BoxSizer(wx.VERTICAL)
            PreferencesDialog.dispGUI(self, parameters, sec_id, frame, sec_sizer)
            top_sizer.Add(sec_sizer, 0,  wx.EXPAND|wx.ALL, 5)

    def bindSec(self, sec_id):
        PreferencesDialog.bindSec(self, sec_id)
        self.Bind(wx.EVT_CHECKBOX, self.changeActivate, self.controls_map[sec_id]["activate"])
        for fk, fctrl in self.controls_map[sec_id]["files"].items():
            self.Bind(wx.EVT_BUTTON, self.onFileChoice, fctrl["btn"])

    def resetSpec(self, sec_id, reset_files=True):
        active = self.pref_handle.getData().hasActiveExtension(self.controls_map[sec_id]["ext_key"])
        self.controls_map[sec_id]["activate"].SetValue(active)
        self.setSecValuesFromDict(sec_id, self.pref_handle.getPreferences())
        if reset_files:
            for fk in self.controls_map[sec_id]["files"].keys():
                self.controls_map[sec_id]["files"][fk]["txt"].SetValue("")
                self.controls_map[sec_id]["files"][fk]["path"] = ""
            
    def _reset(self, sec_id):
        PreferencesDialog._reset(self, sec_id)
        self.resetSpec(sec_id, reset_files=self.files_changed)

    def onResetToDefault(self, event):
        PreferencesDialog.onResetToDefault(self, event)
        if event.GetId() in self.objects_map:
            sec_id = self.objects_map[event.GetId()][0]
            self.resetSpec(sec_id)
            
    def _apply(self, sec_id):
        if self.detectedChange(sec_id) or self.files_changed:
            PreferencesDialog._apply(self, sec_id)
            ext_key = self.controls_map[sec_id]["ext_key"]
            filenames = {}
            for fk, ctrl_txt in self.controls_map[sec_id]["files"].items():
                fn = ctrl_txt["path"].strip()
                if len(fn) > 0: 
                    filenames[fk] = fn
            pdb.set_trace()
            self.pref_handle.loadExtension(ext_key, filenames)
            self.resetSpec(sec_id, reset_files=False)
            self.files_changed = False
            self.upButtons(sec_id, on_action="off")

    def onFileChoice(self, e):
        if e.GetId() in self.objects_map:
            sec_id = self.objects_map[e.GetId()][0]

            button = e.GetEventObject()
            btnId = button.GetName()
            btnName = btnId.replace("extf_", "")
            wcd = self.wcd
            open_dlg = wx.FileDialog(self.nb, message="Choose "+btnName+" file",
                                 defaultDir=self.loc_open_dir, wildcard=wcd,
                                 style=wx.FD_OPEN|wx.FD_CHANGE_DIR)
            if open_dlg.ShowModal() == wx.ID_OK:
                path = open_dlg.GetPath()
                self.loc_open_dir = os.path.dirname(path)
                self.controls_map[sec_id]["files"][btnId]["path"] = path
                self.controls_map[sec_id]["files"][btnId]["txt"].ChangeValue(path)           
                self.files_changed = True
