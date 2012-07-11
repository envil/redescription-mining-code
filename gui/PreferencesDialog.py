from classSettings import Settings
import wx

conf = None

class MiningPanel(wx.Panel):
	def __init__(self, parent, dlg, conf):
		self.conf = conf
		self.parent = parent
		self.dlg = dlg
		
		wx.Panel.__init__(self, parent)

		self.txtcntrls = dict()
		self.choises = dict()
		self.chkboxcntrls = dict()

		title = wx.StaticText(self, wx.ID_ANY, 'Mining preferences')

		# Text controls
		nb_pairsText = wx.StaticText(self, wx.ID_ANY, 'nb_pairs')
		self.txtcntrls['nb_pairs'] = wx.TextCtrl(self, wx.ID_ANY, "")

		contributionText = wx.StaticText(self, wx.ID_ANY, 'contribution')
		self.txtcntrls['contribution'] = wx.TextCtrl(self, wx.ID_ANY, "")

		min_suppinText = wx.StaticText(self, wx.ID_ANY, 'min_suppin')
		self.txtcntrls['min_suppin'] = wx.TextCtrl(self, wx.ID_ANY, "")

		min_suppoutText = wx.StaticText(self, wx.ID_ANY, 'min_suppout')
		self.txtcntrls['min_suppout'] = wx.TextCtrl(self, wx.ID_ANY, "")

		min_scoreText = wx.StaticText(self, wx.ID_ANY, 'min_score')
		self.txtcntrls['min_score'] = wx.TextCtrl(self, wx.ID_ANY, "")

		max_pvalText = wx.StaticText(self, wx.ID_ANY, 'max_pval')
		self.txtcntrls['max_pval'] = wx.TextCtrl(self, wx.ID_ANY, "")

		coeff_pvqueryText = wx.StaticText(self, wx.ID_ANY, 'coeff_pvquery')
		self.txtcntrls['coeff_pvquery'] = wx.TextCtrl(self, wx.ID_ANY, "")

		coeff_pvredText = wx.StaticText(self, wx.ID_ANY, 'coeff_pvred')
		self.txtcntrls['coeff_pvred'] = wx.TextCtrl(self, wx.ID_ANY, "")

		min_improvementText = wx.StaticText(self, wx.ID_ANY, 'min_improvement')
		self.txtcntrls['min_improvement'] = wx.TextCtrl(self, wx.ID_ANY, "")

		for txtctrl in self.txtcntrls.itervalues():
			self.Bind(wx.EVT_TEXT, self.changeHappened, txtctrl)

		# Drop-down controls
		method_pairsText = wx.StaticText(self, wx.ID_ANY, 'method_pairs')
		self.choises['method_pairs'] = wx.Choice(self, wx.ID_ANY)
		self.choises['method_pairs'].AppendItems(strings=['alternate'])
		self.choises['method_pairs'].Select(n=0)

		for choise in self.choises.itervalues():
			self.Bind(wx.EVT_CHOICE, self.changeHappened, choise)

		# Checkboxes
		forbiddenQueriesText = wx.StaticText(self, wx.ID_ANY, 'Forbidden Queries')
		self.chkboxcntrls['forbid_nots'] = wx.CheckBox(self, wx.ID_ANY, 'Negations', style=wx.ALIGN_RIGHT)
		self.chkboxcntrls['forbid_ands'] = wx.CheckBox(self, wx.ID_ANY, 'Conjunctions', style=wx.ALIGN_RIGHT)
		self.chkboxcntrls['forbid_ors'] = wx.CheckBox(self, wx.ID_ANY, 'Disjunctions', style=wx.ALIGN_RIGHT)

		for chkbox in self.chkboxcntrls.itervalues():
			self.Bind(wx.EVT_CHECKBOX, self.changeHappened, chkbox)

		# Buttons
		self.cancelBtn = wx.Button(self, wx.ID_ANY, 'Cancel')
		self.resetBtn = wx.Button(self, wx.ID_ANY, 'Reset')
		self.resetToDefaultsBtn = wx.Button(self, wx.ID_ANY, 'Reset to defaults')
		self.applyBtn = wx.Button(self, wx.ID_ANY, 'Apply')
		self.okBtn = wx.Button(self, wx.ID_ANY, 'OK')
		self.Bind(wx.EVT_BUTTON, self.onCancel, self.cancelBtn)
		self.Bind(wx.EVT_BUTTON, self.onReset, self.resetBtn)
		self.Bind(wx.EVT_BUTTON, self.onResetToDefaults, self.resetToDefaultsBtn)
		self.Bind(wx.EVT_BUTTON, self.onApply, self.applyBtn)
		self.Bind(wx.EVT_BUTTON, self.onOK, self.okBtn)

		# Set the values -- this will send a ton of events
		self.setValuesFromConf()

		# Disable reset and apply
		self.resetBtn.Disable()
		self.applyBtn.Disable()

		# Sizers
		topSizer = wx.BoxSizer(wx.VERTICAL)
		titleSizer = wx.BoxSizer(wx.HORIZONTAL)
		textCtrlSizer = wx.GridSizer(rows=len(self.txtcntrls), cols=2, hgap=5, vgap=5)
		choiseSizer = wx.BoxSizer(wx.HORIZONTAL)
		chkboxTitleSizer = wx.BoxSizer(wx.HORIZONTAL)
		chkboxSizer = wx.BoxSizer(wx.HORIZONTAL)
		btnSizer = wx.BoxSizer(wx.HORIZONTAL)

		# Add title
		titleSizer.Add(title, 0, wx.ALIGN_CENTER)

		# Add stuff to textCtrlSizer
		textCtrlSizer.Add(nb_pairsText, 0, wx.ALIGN_RIGHT)
		textCtrlSizer.Add(self.txtcntrls['nb_pairs'], 0, wx.EXPAND)
		textCtrlSizer.Add(contributionText, 0, wx.ALIGN_RIGHT)
		textCtrlSizer.Add(self.txtcntrls['contribution'], 0, wx.EXPAND)
		textCtrlSizer.Add(min_suppinText, 0, wx.ALIGN_RIGHT)
		textCtrlSizer.Add(self.txtcntrls['min_suppin'], 0, wx.EXPAND)
		textCtrlSizer.Add(min_suppoutText, 0, wx.ALIGN_RIGHT)
		textCtrlSizer.Add(self.txtcntrls['min_suppout'], 0, wx.EXPAND)
		textCtrlSizer.Add(min_scoreText, 0, wx.ALIGN_RIGHT)
		textCtrlSizer.Add(self.txtcntrls['min_score'], 0, wx.EXPAND)
		textCtrlSizer.Add(max_pvalText, 0, wx.ALIGN_RIGHT)
		textCtrlSizer.Add(self.txtcntrls['max_pval'], 0, wx.EXPAND)
		textCtrlSizer.Add(coeff_pvqueryText, 0, wx.ALIGN_RIGHT)
		textCtrlSizer.Add(self.txtcntrls['coeff_pvquery'], 0, wx.EXPAND)
		textCtrlSizer.Add(coeff_pvredText, 0, wx.ALIGN_RIGHT)
		textCtrlSizer.Add(self.txtcntrls['coeff_pvred'], 0, wx.EXPAND)
		textCtrlSizer.Add(min_improvementText, 0, wx.ALIGN_RIGHT)
		textCtrlSizer.Add(self.txtcntrls['min_improvement'], 0, wx.EXPAND)

		# Add stuff to choiseSizer
		choiseSizer.Add(method_pairsText, 0, wx.ALIGN_RIGHT)
		choiseSizer.Add(self.choises['method_pairs'], 0)

		# Add stuff to chkboxTitleSizer
		chkboxTitleSizer.Add(forbiddenQueriesText, 0, wx.ALIGN_LEFT)

		# Add stuff to chkboxSizer
		chkboxSizer.Add(self.chkboxcntrls['forbid_nots'], 0)
		chkboxSizer.Add(self.chkboxcntrls['forbid_ands'], 0)
		chkboxSizer.Add(self.chkboxcntrls['forbid_ors'], 0)

		# Add stuff to btnSizer
		btnSizer.Add(self.cancelBtn, 0)
		btnSizer.Add(self.resetBtn, 0)
		btnSizer.Add(self.resetToDefaultsBtn, 0)
		btnSizer.Add(self.applyBtn, 0)
		btnSizer.Add(self.okBtn, 0)

		# Add stuff to top sizer
		topSizer.Add(titleSizer, 0, wx.CENTER)
		topSizer.Add(wx.StaticLine(self), 0, wx.EXPAND|wx.ALL, 5)
		topSizer.Add(textCtrlSizer, 0, wx.EXPAND|wx.ALL, 5)
		topSizer.Add(wx.StaticLine(self), 0, wx.EXPAND|wx.ALL, 5)
		topSizer.Add(choiseSizer, 0, wx.EXPAND|wx.ALL, 5)
		topSizer.Add(wx.StaticLine(self), 0, wx.EXPAND|wx.ALL, 5)
		topSizer.Add(chkboxTitleSizer, 0, wx.EXPAND|wx.ALL|wx.ALIGN_LEFT, 5)
		topSizer.Add(chkboxSizer, 0, wx.EXPAND|wx.ALL, 5)
		topSizer.Add(wx.StaticLine(self), 0, wx.EXPAND|wx.ALL, 5)
		topSizer.Add(btnSizer, 0, wx.ALIGN_RIGHT|wx.ALL, 5)

		self.SetSizer(topSizer)
		topSizer.Fit(self)
		# END OF __init__

	def onCancel(self, event):
		self.dlg.onClose()

	def onReset(self, event):
		# Resets all values
		self.setValuesFromConf()
		self.resetBtn.Disable()
		self.applyBtn.Disable()

	def onResetToDefaults(self, event):
		# Resets all values to defaults
		pass

	def onApply(self, event):
		# Writes all values to conf
		self.resetBtn.Disable()
		self.applyBtn.Disable()
	
	def onOK(self, event):
		# Writes all values to conf and exits
		self.dlg.onClose()

	def setValuesFromConf(self):
		# Some testing
		self.txtcntrls['coeff_pvred'].SetValue('0.01')
		self.txtcntrls['nb_pairs'].SetValue('100')

	def changeHappened(self, event):
		self.resetBtn.Enable()
		self.applyBtn.Enable()

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
		mining_p = MiningPanel(nb, self, conf)
		nb.AddPage(outlook_p, "Outlook")
		nb.AddPage(mining_p, "Mining")
		self.Centre()
		# Apparently for Windows (?)
		self.SetSize((500, 1000))
		
	def onClose(self):
		self.EndModal(0)

	


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
        
