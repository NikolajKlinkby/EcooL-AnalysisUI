# Wavelength calculation file

# Retrieve
saturation = float(self.satentry.get())
photon = float(self.photonentry.get())

edges = np.array(self.root.histogram['edges'][:-1]) + (self.root.histogram['edges'][1] - self.root.histogram['edges'][0])/2

# Background mask
back_mask = np.ones(len(edges), dtype=bool)
for back in self.container.windows.entries_back:
	if back[0]['text'] == self.back_det_men_var.get():
		back_mask = back_mask * (edges > float(back[1].get())*1e+3) * (edges < float(back[2].get())*1e+3)

scan_key = self.root.histogram['scan_key']
all_scan_steps = np.array(self.root.parameters[self.root.histogram['scan_key']])
scan_steps = np.unique(all_scan_steps)
laser_pw = np.array(self.root.parameters['ADC.Laser_pw'])

for win in self.container.windows.entries:
	# Window masks
	window_mask = np.ones(len(edges), dtype=bool)
	window_mask = window_mask * (edges > float(win[2].get())*1e+3) * (edges < float(win[3].get())*1e+3)

	signal = []
	signal_err = []
	
	for step in scan_steps:
		print(time.strftime('%H:%M:%S', time.gmtime())+' '+scan_key+f' step {step}')

		step_mask = (all_scan_steps == step)

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
