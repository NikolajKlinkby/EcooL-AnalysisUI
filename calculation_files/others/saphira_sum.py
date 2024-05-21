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

		'''			Calculate			'''

		S1 = np.sum(np.array(self.root.histogram[win[5].get()+'_hist_1_1_'+str(step)])[window_mask])
		S2 = np.sum(np.array(self.root.histogram[win[5].get()+'_hist_0_1_'+str(step)])[window_mask])
		S3 = np.sum(np.array(self.root.histogram[win[5].get()+'_hist_1_0_'+str(step)])[window_mask])
		S4 = np.sum(np.array(self.root.histogram[win[5].get()+'_hist_0_0_'+str(step)])[window_mask])
		
		B1 = np.sum(np.array(self.root.histogram[self.back_det_men_var.get()+'_hist_1_1_'+str(step)])[back_mask])
		B2 = np.sum(np.array(self.root.histogram[self.back_det_men_var.get()+'_hist_0_1_'+str(step)])[back_mask])
		B3 = np.sum(np.array(self.root.histogram[self.back_det_men_var.get()+'_hist_1_0_'+str(step)])[back_mask])
		B4 = np.sum(np.array(self.root.histogram[self.back_det_men_var.get()+'_hist_0_0_'+str(step)])[back_mask])

		
		if B1 == 0:
			if B2 == 0:
				if B3 == 0:
					if B4 == 0:
						sig = S1 + S4 + S3 + S2
						variance = S1 + S2 + S3 + S4
					else:
						sig = S1 + S4/B4 + S3 + S2
						variance = S1 + S2 + S3 + S4/B4**2
				elif B4 == 0:
					sig = S1 + S4 + S3/B3 + S2
					variance = S1 + S2 + S3/B3**2 + S4
				else:
					sig = S1 + S4/B4 + S3/B3 + S2
					variance = S1 + S2 + S3/B3**2 + S4/B4**2
			elif B3 == 0:
				if B4 == 0:
					sig = S1 + S4 + S3 + S2/B2
					variance = S1 + S2/B2**3 + S3 + S4
				else:
					sig = S1 + S4/B4 + S3 + S2/B2
					variance = S1 + S2/B2**2 + S3 + S4/B4**2
			elif B4 == 0:
				sig = S1 + S4 + S3/B3 + S2/B2
				variance = S1 + S2/B2**2 + S3/B3**2 + S4
			else:
				sig = S1 + S4/B4 + S3/B3 + S2/B2
				variance = S1 + S2/B2**2 + S3/B3**2 + S4/B4**2
		elif B2 == 0:
			if B3 == 0:
				if B4 == 0:
					sig = S1/B1 + S4 + S3 + S2
					variance = S1/B1**2 + S2 + S3 + S4
				else:
					sig = S1/B1 + S4/B4 + S3 + S2
					variance = S1/B1**2 + S2 + S3 + S4/B4**2
			elif B4 == 0:
				sig = S1/B1 + S4 + S3/B3 + S2
				variance = S1/B1**2 + S2 + S3/B3**2 + S4
			else:
				sig = S1/B1 + S4/B4 + S3/B3 + S2
				variance = S1/B1**2 + S2 + S3/B3**2 + S4/B4**2
		else:
			sig = S1/B1 + S4/B4 + S3/B3 + S2/B2
			variance = S1/B1**2 + S2/B2**2 + S3/B3**2 + S4/B4**2
		
		signal.append(sig)
		signal_err.append(variance)

	# Output
	self.root.calculations[win[5].get()+':'+win[0].get()] = [signal, signal_err];
