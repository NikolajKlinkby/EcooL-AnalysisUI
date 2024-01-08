# Wavelength calculation file

# Retrieve
saturation = float(self.satentry.get())
photon = float(self.photonentry.get())

# Background mask
back_mask = np.ones(len(self.root.histogram['edges'][:-1]), dtype=bool)
for back in self.container.windows.entries_back:
	if back[0]['text'] == self.back_det_men_var.get():
		back_mask = back_mask * (np.array(self.root.histogram['edges'])[:-1] > float(back[1].get())*1e+3) * (np.array(self.root.histogram['edges'][:-1]) < float(back[2].get())*1e+3)


for win in self.container.windows.entries:
	# Window masks
	window_mask = np.ones(len(self.root.histogram['edges'][:-1]), dtype=bool)
	window_mask = window_mask * (np.array(self.root.histogram['edges'][:-1]) > float(win[2].get())*1e+3) * (np.array(self.root.histogram['edges'][:-1]) < float(win[3].get())*1e+3)

	signal = []
	signal_err = []
	
	for step in np.unique(self.root.parameters[self.root.histogram['scan_key']]):
		print(time.strftime('%H:%M:%S', time.gmtime())+' '+self.root.histogram['scan_key']+f' step {step}')

		step_mask = (np.array(self.root.parameters[self.root.histogram['scan_key']]) == step)

		'''			Calculate			'''

		S = np.sum(np.array(self.root.histogram[win[5].get()+'_hist_1_'+str(step)])[window_mask])
		B = np.sum(np.array(self.root.histogram[self.back_det_men_var.get()+'_hist_1_'+str(step)])[back_mask])
		S0 = np.sum(np.array(self.root.histogram[win[5].get()+'_hist_0_'+str(step)])[window_mask])
		B0 = np.sum(np.array(self.root.histogram[self.back_det_men_var.get()+'_hist_0_'+str(step)])[back_mask])

		
		if B == 0:
			sig = S - S0
			variance = S + S0
		else:
			sig = (S - S0 * B0 / B) / B
			variance = S/B**2  + S**2/B**3 + 4 * (S0 * B0)**2 / B**5 + (S0 / B)**2 * B0 + (B0 / B)**2 * S0
		
		signal.append(sig)
		signal_err.append(variance)

	# Output
	self.root.calculations[win[5].get()+':'+win[0].get()] = [signal, signal_err];
