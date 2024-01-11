# Wavelength calculation file

# Retrieve
saturation = float(self.satentry.get())
photon = float(self.photonentry.get())

edges = np.array(self.root.histogram['edges'][:-1]) + (self.root.histogram['edges'][1] + self.root.histogram['edges'][0])/2

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
	signal_dep = []
	signal_dep_err = []

	background = []
	background_err = []
	background_dep = []
	background_dep_err = []
	
	for step in scan_steps:
		print(time.strftime('%H:%M:%S', time.gmtime())+' '+scan_key+f' step {step}')

		step_mask = (all_scan_steps == step)

		'''			Calculate			'''
        
		# Without depletion

		S = np.sum(np.array(self.root.histogram[win[5].get()+'_hist_1_'+str(step)])[window_mask])/(self.root.histogram[win[5].get()+'_hist_1_event_'+str(step)]+1)
		B = np.sum(np.array(self.root.histogram[self.back_det_men_var.get()+'_hist_1_'+str(step)])[back_mask])/(self.root.histogram[self.back_det_men_var.get()+'_hist_1_event_'+str(step)]+1)
		S0 = np.sum(np.array(self.root.histogram[win[5].get()+'_hist_0_'+str(step)])[window_mask])/(self.root.histogram[win[5].get()+'_hist_0_event_'+str(step)]+1)
		B0 = np.sum(np.array(self.root.histogram[self.back_det_men_var.get()+'_hist_0_'+str(step)])[back_mask])/(self.root.histogram[self.back_det_men_var.get()+'_hist_0_event_'+str(step)]+1)

		sig = S - S0
		variance = S/(self.root.histogram[win[5].get()+'_hist_1_event_'+str(step)]+1) + S0/(self.root.histogram[win[5].get()+'_hist_0_event_'+str(step)]+1)
		
		preSignal = np.abs(sig)**(1/photon) * np.sign(sig)
		variance = np.abs(sig)**(2/photon-2)/photon**2 * variance

		# Saturation
		if saturation > 0:
			powerCor = saturation * (1 - np.exp( - np.mean(laser_pw[step_mask]) / saturation))
			var_powcor = np.var(laser_pw[step_mask]) * np.exp( - 2 * np.mean(laser_pw[step_mask]) / saturation)
		else:
			powerCor = np.mean(laser_pw[step_mask])
			var_powcor = np.var(laser_pw[step_mask])/(len(laser_pw[step_mask]))

		if powerCor == 0:
			sig = 0
			variance = 0
		else:
			sig = preSignal/(powerCor*float(step))
			variance = variance/(powerCor*float(step))**2 + (preSignal/float(step))**2 * var_powcor/powerCor**4

		signal.append(sig)
		signal_err.append(variance)
		background.append(B-B0)
		background_err.append(B/(self.root.histogram[self.back_det_men_var.get()+'_hist_1_event_'+str(step)]+1)+B0/(self.root.histogram[self.back_det_men_var.get()+'_hist_0_event_'+str(step)]+1))

		# With depletion

		S = np.sum(np.array(self.root.histogram_deplete[win[5].get()+'_hist_1_'+str(step)])[window_mask])/(self.root.histogram_deplete[win[5].get()+'_hist_1_event_'+str(step)]+1)
		B = np.sum(np.array(self.root.histogram_deplete[self.back_det_men_var.get()+'_hist_1_'+str(step)])[back_mask])/(self.root.histogram_deplete[self.back_det_men_var.get()+'_hist_1_event_'+str(step)]+1)
		S0 = np.sum(np.array(self.root.histogram_deplete[win[5].get()+'_hist_0_'+str(step)])[window_mask])/(self.root.histogram_deplete[win[5].get()+'_hist_0_event_'+str(step)]+1)
		B0 = np.sum(np.array(self.root.histogram_deplete[self.back_det_men_var.get()+'_hist_0_'+str(step)])[back_mask])/(self.root.histogram_deplete[self.back_det_men_var.get()+'_hist_0_event_'+str(step)]+1)

		sig = S - S0
		variance = S/(self.root.histogram_deplete[win[5].get()+'_hist_1_event_'+str(step)]+1) + S0/(self.root.histogram_deplete[win[5].get()+'_hist_0_event_'+str(step)]+1)
		
		preSignal = np.abs(sig)**(1/photon) * np.sign(sig)
		variance = np.abs(sig)**(2/photon-2)/photon**2 * variance

		# Saturation
		if saturation > 0:
			powerCor = saturation * (1 - np.exp( - np.mean(laser_pw[step_mask]) / saturation))
			var_powcor = np.var(laser_pw[step_mask]) * np.exp( - 2 * np.mean(laser_pw[step_mask]) / saturation)
		else:
			powerCor = np.mean(laser_pw[step_mask])
			var_powcor = np.var(laser_pw[step_mask])/(len(laser_pw[step_mask]))

		if powerCor == 0:
			sig = 0
			variance = 0
		else:
			sig = preSignal/(powerCor*float(step))
			variance = variance/(powerCor*float(step))**2 + (preSignal/float(step))**2 * var_powcor/powerCor**4
		
		signal_dep.append(sig)
		signal_dep_err.append(variance)
		background_dep.append(B-B0)
		background_dep_err.append(B/(self.root.histogram_deplete[self.back_det_men_var.get()+'_hist_1_event_'+str(step)]+1)+B0/(self.root.histogram_deplete[self.back_det_men_var.get()+'_hist_0_event_'+str(step)]+1))

	# Output
	self.root.calculations[win[5].get()+':'+win[0].get()+':Yb/k'] = [np.array(signal_dep)/np.array(signal), np.array(signal_dep_err)/np.array(signal)**2+np.array(signal_err)*np.array(signal_dep)**2/np.array(signal)**4];
	self.root.calculations[win[5].get()+':'+win[0].get()+':k'] = [np.array(background)/np.array(background_dep), np.array(background_err)/np.array(background_dep)**2+np.array(background_dep_err)*np.array(background)**2/np.array(background_dep)**4];
