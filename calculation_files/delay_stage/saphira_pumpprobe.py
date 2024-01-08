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
			sig = S1 + (S4 - S3 - S2)
			variance = S1 + S2 + S3 + S4
		else:
			sig = S1 + (S4*B4 - S3*B3 - S2*B2) / B1
			variance = S1 + (S4*B4 - S3*B3 - S2*B2)**2 / B1**3 + (S4**2*B4 + S4*B4**2 + S3**2*B3 + S3*B3**2 + S2**2*B2 + S2*B2**2) / B1**2
		
		signal.append(sig)
		signal_err.append(variance)

	# Output
	self.root.calculations[win[5].get()+':'+win[0].get()] = [signal, signal_err];
