import numpy as np
import json
import os, sys

class NumpyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return json.JSONEncoder.default(self, obj)
        
def flatten_list(listr):
    return np.array([item for sublist in listr for item in sublist])



# Write has structure [coinc_struct, coin_hist_struct, hist_struct]
def create_structs(runs, keys = ['TDC1.ESP_F','TDC1.HEX_B'], hist_keys = ['TDC1.ESP_F','TDC1.HEX_B', 'TDC1.HCH_B'], nr_bins=20000, coinc_analysis=False, coinc_time_int=[None], hist_time_int=[None], write=[None,None,None], overwrite=[False,False,False], channels_total = 1500000000, diff_channels_total = 2000000, photon_diag_file_format=False, ion_flags=[]):
    
    # Boolean keys
    loaded_hist_struct = False
    loaded_coinc_struct = False
    loaded_coinc_hist_struct = False
    
    #Structures
    hist_struct = {}
    coinc_struct = {}
    coinc_hist_struct = {}
    
    print('----------------------------------')
    if np.any(np.array(write) != None):
        print('-----Load Structs-------')
        try:
            if os.path.exists(write[0]) and not overwrite[0] and coinc_analysis:
                # Load coinc struct
                f = open(write[0], 'r')
                coinc_struct = json.loads(f.read())
                f.close()
                loaded_coinc_struct = True
                print('Coincidence JSON files found and read')
        except:
            pass
        
        try:        
            if os.path.exists(write[1]) and not overwrite[1]  and coinc_analysis:
                # Load Coincidence histogram
                f = open(write[1], 'r')
                coinc_hist_struct = json.loads(f.read())
                f.close()
                loaded_coinc_hist_struct = True
                print('Coincidence histogram JSON files found and read')
        except:
            pass
        
        try:    
            if os.path.exists(write[2]) and not overwrite[2]:
                # Load Histogram
                f = open(write[2], 'r')
                hist_struct = json.loads(f.read())
                f.close()
                loaded_hist_struct = True
                print('Histogram JSON files found and read')
        except:
            pass
        
        if loaded_hist_struct and loaded_coinc_struct and loaded_coinc_hist_struct and coinc_analysis:
            print('----------------------------------')
            return coinc_struct, coinc_hist_struct, hist_struct
        elif loaded_hist_struct and not coinc_analysis:
            print('----------------------------------')
            return hist_struct
    
    print('-----Create Structs-------')
    
    # Checking wether or not to make different binnings for the different structures.
    if isinstance(nr_bins, (list, tuple, np.ndarray)):
        hist_nr_bins = nr_bins[0]
        coinc_nr_bins = nr_bins[1]
    else:
        hist_nr_bins = nr_bins
        coinc_nr_bins = nr_bins
        
    # edges of bins
    if not loaded_coinc_hist_struct and coinc_analysis:
        coinc_hist_struct['edges'] = np.arange(0, channels_total+1/hist_nr_bins, channels_total/hist_nr_bins)
    if not loaded_coinc_struct and coinc_analysis:
        coinc_struct['edges'] = np.arange(0, diff_channels_total+1/coinc_nr_bins, diff_channels_total/coinc_nr_bins)
    if not loaded_hist_struct:
        hist_struct['edges'] = np.arange(0, channels_total+1/hist_nr_bins, channels_total/hist_nr_bins)
   
    TDC_res = 1
    
    # Keys to consider
    if coinc_analysis:
        trig_key = 'Coinc_'+keys[0]+'_'+keys[1]+'_trig'
        diff_key = 'Coinc_'+keys[0]+'_'+keys[1]+'_diff'
        trig_rand_key = 'Coinc_rand_'+keys[0]+'_'+keys[1]+'_trig'
        diff_rand_key = 'Coinc_rand_'+keys[0]+'_'+keys[1]+'_diff'
    
        load_keys = np.unique(np.concatenate((keys, hist_keys)))
        load_keys = np.concatenate((load_keys,[trig_key,diff_key,trig_rand_key,diff_rand_key]))
    else:
        load_keys = hist_keys
    
    # Loop over runs
    for run in runs:
        for filename in sorted(os.listdir(run[:run.rfind('/')])):
            if (run[run.rfind('/')+1:] in filename) and ('-dat-' in filename):
                
                if photon_diag_file_format:
                    # Load the needed keys
                    data = load_dat_file(run[:run.rfind('/')+1]+filename, keys=['Event','TDC.res','shutter control_ctr','WavE_AMO (eV)_ctr','G_temperature_C',*load_keys])
                    
                    ion_flag = ion_flags[np.argwhere(run == np.array(runs))[0,0]]
                    TDC_res = data['TDC.res']
                    
                    if not loaded_hist_struct:
                        if 'temperature_list' not in hist_struct.keys():
                            hist_struct['temperature_list'] = []
                    
                    # Checking uniqe wavelength values and adding them to struct
                    for wavelength in np.unique(flatten_list(data['WavE_AMO (eV)_ctr'])):
                
                        # Add to histogram struct if it does not exist
                        
                        if not loaded_coinc_struct and coinc_analysis:
                            if 'coinc_ion_1_shutter_0_'+str(wavelength) not in coinc_struct.keys():
                                coinc_struct['coinc_ion_0_shutter_0_'+str(wavelength)] = np.zeros(coinc_nr_bins)
                                coinc_struct['coinc_ion_0_shutter_1_'+str(wavelength)] = np.zeros(coinc_nr_bins)
                                coinc_struct['coinc_ion_1_shutter_0_'+str(wavelength)] = np.zeros(coinc_nr_bins)
                                coinc_struct['coinc_ion_1_shutter_1_'+str(wavelength)] = np.zeros(coinc_nr_bins)
                            
                                coinc_struct['coinc_rand_ion_0_shutter_0_'+str(wavelength)] = np.zeros(coinc_nr_bins)
                                coinc_struct['coinc_rand_ion_0_shutter_1_'+str(wavelength)] = np.zeros(coinc_nr_bins)
                                coinc_struct['coinc_rand_ion_1_shutter_0_'+str(wavelength)] = np.zeros(coinc_nr_bins)
                                coinc_struct['coinc_rand_ion_1_shutter_1_'+str(wavelength)] = np.zeros(coinc_nr_bins)
                                
                                # Number of coincidence events
                                coinc_struct['coinc_event_ion_0_shutter_0_'+str(wavelength)] = 0
                                coinc_struct['coinc_event_ion_0_shutter_1_'+str(wavelength)] = 0
                                coinc_struct['coinc_event_ion_1_shutter_0_'+str(wavelength)] = 0
                                coinc_struct['coinc_event_ion_1_shutter_1_'+str(wavelength)] = 0
                            
                                coinc_struct['coinc_rand_event_ion_0_shutter_0_'+str(wavelength)] = 0
                                coinc_struct['coinc_rand_event_ion_0_shutter_1_'+str(wavelength)] = 0
                                coinc_struct['coinc_rand_event_ion_1_shutter_0_'+str(wavelength)] = 0
                                coinc_struct['coinc_rand_event_ion_1_shutter_1_'+str(wavelength)] = 0
                            
                        if not loaded_coinc_hist_struct and coinc_analysis:
                            if 'coinc_ion_1_shutter_0_'+str(wavelength) not in coinc_hist_struct.keys():
                                
                                coinc_hist_struct['coinc_ion_0_shutter_0_'+str(wavelength)] = np.zeros(hist_nr_bins)
                                coinc_hist_struct['coinc_ion_0_shutter_1_'+str(wavelength)] = np.zeros(hist_nr_bins)
                                coinc_hist_struct['coinc_ion_1_shutter_0_'+str(wavelength)] = np.zeros(hist_nr_bins)
                                coinc_hist_struct['coinc_ion_1_shutter_1_'+str(wavelength)] = np.zeros(hist_nr_bins)
                            
                                coinc_hist_struct['coinc_rand_ion_0_shutter_0_'+str(wavelength)] = np.zeros(hist_nr_bins)
                                coinc_hist_struct['coinc_rand_ion_0_shutter_1_'+str(wavelength)] = np.zeros(hist_nr_bins)
                                coinc_hist_struct['coinc_rand_ion_1_shutter_0_'+str(wavelength)] = np.zeros(hist_nr_bins)
                                coinc_hist_struct['coinc_rand_ion_1_shutter_1_'+str(wavelength)] = np.zeros(hist_nr_bins)
                                
                                # Number of coincidence events
                                coinc_hist_struct['coinc_event_ion_0_shutter_0_'+str(wavelength)] = 0
                                coinc_hist_struct['coinc_event_ion_0_shutter_1_'+str(wavelength)] = 0
                                coinc_hist_struct['coinc_event_ion_1_shutter_0_'+str(wavelength)] = 0
                                coinc_hist_struct['coinc_event_ion_1_shutter_1_'+str(wavelength)] = 0
                            
                                coinc_hist_struct['coinc_rand_event_ion_0_shutter_0_'+str(wavelength)] = 0
                                coinc_hist_struct['coinc_rand_event_ion_0_shutter_1_'+str(wavelength)] = 0
                                coinc_hist_struct['coinc_rand_event_ion_1_shutter_0_'+str(wavelength)] = 0
                                coinc_hist_struct['coinc_rand_event_ion_1_shutter_1_'+str(wavelength)] = 0
                            
                        if not loaded_hist_struct:
                            # Add to histogram struct if it does not exist
                            for key in hist_keys:
                                if key+'_hist_ion_1_shutter_0_'+str(wavelength) not in hist_struct.keys():
                                    hist_struct[key+'_hist_ion_0_shutter_0_'+str(wavelength)] = np.zeros(hist_nr_bins)
                                    hist_struct[key+'_hist_ion_0_shutter_1_'+str(wavelength)] = np.zeros(hist_nr_bins)
                                    hist_struct[key+'_hist_ion_1_shutter_0_'+str(wavelength)] = np.zeros(hist_nr_bins)
                                    hist_struct[key+'_hist_ion_1_shutter_1_'+str(wavelength)] = np.zeros(hist_nr_bins)
                                    
                                    # Number of coincidence events
                                    hist_struct[key+'_hist_event_ion_0_shutter_0_'+str(wavelength)] = 0
                                    hist_struct[key+'_hist_event_ion_0_shutter_1_'+str(wavelength)] = 0
                                    hist_struct[key+'_hist_event_ion_1_shutter_0_'+str(wavelength)] = 0
                                    hist_struct[key+'_hist_event_ion_1_shutter_1_'+str(wavelength)] = 0
                
                    # Loop over events (copy of sort function)
                    for event in range(len(data['Event'])):
                        
                        try:
                            shutter_status = int(data['shutter control_ctr'][event][0])
                        
                            # coincidence structure
                            if not loaded_coinc_struct and coinc_analysis:
                                current_event = np.array(data[diff_key][event])
                                current_rand_event = np.array(data[diff_rand_key][event])
                        
                                if hist_time_int[0] != None:
                                    mask =  (np.array(data[trig_key][event]) > hist_time_int[0]/TDC_res) & (np.array(data[trig_key][event]) < hist_time_int[1]/TDC_res)
                                    current_event = current_event[mask]
                            
                                    mask =  (np.array(data[trig_rand_key][event]) > hist_time_int[0]/TDC_res) & (np.array(data[trig_rand_key][event]) < hist_time_int[1]/TDC_res)
                                    current_rand_event = current_rand_event[mask]
                            
                                # Normalization
                                coinc_struct[f'coinc_event_ion_{ion_flag}_shutter_{shutter_status}_'+str(data['WavE_AMO (eV)_ctr'][event][0])] += 1
                                coinc_struct[f'coinc_rand_event_ion_{ion_flag}_shutter_{shutter_status}_'+str(data['WavE_AMO (eV)_ctr'][event][0])] += 1
                        
                                # Add to histogram
                                coinc_struct[f'coinc_ion_{ion_flag}_shutter_{shutter_status}_'+str(data['WavE_AMO (eV)_ctr'][event][0])] = coinc_struct[f'coinc_ion_{ion_flag}_shutter_{shutter_status}_'+str(data['WavE_AMO (eV)_ctr'][event][0])] + np.histogram(current_event, coinc_struct['edges'])[0]
                                coinc_struct[f'coinc_rand_ion_{ion_flag}_shutter_{shutter_status}_'+str(data['WavE_AMO (eV)_ctr'][event][0])] = coinc_struct[f'coinc_rand_ion_{ion_flag}_shutter_{shutter_status}_'+str(data['WavE_AMO (eV)_ctr'][event][0])] + np.histogram(current_rand_event, coinc_struct['edges'])[0]
                        
                            # Coincidence histogram structure,
                            if not loaded_coinc_hist_struct and coinc_analysis:
                                current_event = np.array(data[trig_key][event])
                                current_rand_event = np.array(data[trig_rand_key][event])
                        
                                if coinc_time_int[0] != None:
                                    mask =  (np.array(data[diff_key][event]) > coinc_time_int[0]/TDC_res) & (np.array(data[diff_key][event]) < coinc_time_int[1]/TDC_res)
                                    current_event = current_event[mask]
                                
                                    mask =  (np.array(data[diff_rand_key][event]) > coinc_time_int[0]/TDC_res) & (np.array(data[diff_rand_key][event]) < coinc_time_int[1]/TDC_res)
                                    current_rand_event = current_rand_event[mask]
                        
                                # Normalization
                                coinc_hist_struct[f'coinc_event_ion_{ion_flag}_shutter_{shutter_status}_'+str(data['WavE_AMO (eV)_ctr'][event][0])] += 1
                                coinc_hist_struct[f'coinc_rand_event_ion_{ion_flag}_shutter_{shutter_status}_'+str(data['WavE_AMO (eV)_ctr'][event][0])] += 1
                        
                                # Add to histogram
                                coinc_hist_struct[f'coinc_ion_{ion_flag}_shutter_{shutter_status}_'+str(data['WavE_AMO (eV)_ctr'][event][0])] = coinc_hist_struct[f'coinc_ion_{ion_flag}_shutter_{shutter_status}_'+str(data['WavE_AMO (eV)_ctr'][event][0])] + np.histogram(current_event, coinc_hist_struct['edges'])[0]
                                coinc_hist_struct[f'coinc_rand_ion_{ion_flag}_shutter_{shutter_status}_'+str(data['WavE_AMO (eV)_ctr'][event][0])] = coinc_hist_struct[f'coinc_rand_ion_{ion_flag}_shutter_{shutter_status}_'+str(data['WavE_AMO (eV)_ctr'][event][0])] + np.histogram(current_rand_event, coinc_hist_struct['edges'])[0]
                        
                            # Histogram structure
                            if not loaded_hist_struct:
                                
                                hist_struct['temperature_list'].append(float(data['G_temperature_C'][event][0]))
                                current_event = [np.array(data[key][event]) for key in hist_keys]
                        
                                for key in range(len(current_event)):
                                
                                    # Normalization
                                    hist_struct[hist_keys[key]+f'_hist_event_ion_{ion_flag}_shutter_{shutter_status}_'+str(data['WavE_AMO (eV)_ctr'][event][0])] += 1
                            
                                    # Append to time structs
                                    hist_struct[hist_keys[key]+f'_hist_ion_{ion_flag}_shutter_{shutter_status}_'+str(data['WavE_AMO (eV)_ctr'][event][0])] = hist_struct[hist_keys[key]+f'_hist_ion_{ion_flag}_shutter_{shutter_status}_'+str(data['WavE_AMO (eV)_ctr'][event][0])] + np.histogram(current_event[key], hist_struct['edges'])[0]
                        except:
                            print(f'Error at event {data["Event"][event]} index {event} disregarded')
                    # Clear data
                    data.clear()
                else:
                    # Load the needed keys
                    data = load_dat_file(run[:run.rfind('/')+1]+filename, keys=['Event','TDC.res','ADCV.Ion_flag','shutter_status','WavE_AMO (eV)',*load_keys])
                    
                    TDC_res = data['TDC.res']
                    
                    # Checking uniqe wavelength values and adding them to struct
                    for wavelength in np.unique(flatten_list(data['WavE_AMO (eV)'])):
                
                        # Add to histogram struct if it does not exist
                        
                        if not loaded_coinc_struct and coinc_analysis:
                            if 'coinc_ion_1_shutter_0_'+str(wavelength) not in coinc_struct.keys():
                                coinc_struct['coinc_ion_0_shutter_0_'+str(wavelength)] = np.zeros(coinc_nr_bins)
                                coinc_struct['coinc_ion_0_shutter_1_'+str(wavelength)] = np.zeros(coinc_nr_bins)
                                coinc_struct['coinc_ion_1_shutter_0_'+str(wavelength)] = np.zeros(coinc_nr_bins)
                                coinc_struct['coinc_ion_1_shutter_1_'+str(wavelength)] = np.zeros(coinc_nr_bins)
                            
                                coinc_struct['coinc_rand_ion_0_shutter_0_'+str(wavelength)] = np.zeros(coinc_nr_bins)
                                coinc_struct['coinc_rand_ion_0_shutter_1_'+str(wavelength)] = np.zeros(coinc_nr_bins)
                                coinc_struct['coinc_rand_ion_1_shutter_0_'+str(wavelength)] = np.zeros(coinc_nr_bins)
                                coinc_struct['coinc_rand_ion_1_shutter_1_'+str(wavelength)] = np.zeros(coinc_nr_bins)
                                
                                # Number of coincidence events
                                coinc_struct['coinc_event_ion_0_shutter_0_'+str(wavelength)] = 0
                                coinc_struct['coinc_event_ion_0_shutter_1_'+str(wavelength)] = 0
                                coinc_struct['coinc_event_ion_1_shutter_0_'+str(wavelength)] = 0
                                coinc_struct['coinc_event_ion_1_shutter_1_'+str(wavelength)] = 0
                            
                                coinc_struct['coinc_rand_event_ion_0_shutter_0_'+str(wavelength)] = 0
                                coinc_struct['coinc_rand_event_ion_0_shutter_1_'+str(wavelength)] = 0
                                coinc_struct['coinc_rand_event_ion_1_shutter_0_'+str(wavelength)] = 0
                                coinc_struct['coinc_rand_event_ion_1_shutter_1_'+str(wavelength)] = 0
                            
                        if not loaded_coinc_hist_struct and coinc_analysis:
                            if 'coinc_ion_1_shutter_0_'+str(wavelength) not in coinc_hist_struct.keys():
                                
                                coinc_hist_struct['coinc_ion_0_shutter_0_'+str(wavelength)] = np.zeros(hist_nr_bins)
                                coinc_hist_struct['coinc_ion_0_shutter_1_'+str(wavelength)] = np.zeros(hist_nr_bins)
                                coinc_hist_struct['coinc_ion_1_shutter_0_'+str(wavelength)] = np.zeros(hist_nr_bins)
                                coinc_hist_struct['coinc_ion_1_shutter_1_'+str(wavelength)] = np.zeros(hist_nr_bins)
                            
                                coinc_hist_struct['coinc_rand_ion_0_shutter_0_'+str(wavelength)] = np.zeros(hist_nr_bins)
                                coinc_hist_struct['coinc_rand_ion_0_shutter_1_'+str(wavelength)] = np.zeros(hist_nr_bins)
                                coinc_hist_struct['coinc_rand_ion_1_shutter_0_'+str(wavelength)] = np.zeros(hist_nr_bins)
                                coinc_hist_struct['coinc_rand_ion_1_shutter_1_'+str(wavelength)] = np.zeros(hist_nr_bins)
                                
                                # Number of coincidence events
                                coinc_hist_struct['coinc_event_ion_0_shutter_0_'+str(wavelength)] = 0
                                coinc_hist_struct['coinc_event_ion_0_shutter_1_'+str(wavelength)] = 0
                                coinc_hist_struct['coinc_event_ion_1_shutter_0_'+str(wavelength)] = 0
                                coinc_hist_struct['coinc_event_ion_1_shutter_1_'+str(wavelength)] = 0
                            
                                coinc_hist_struct['coinc_rand_event_ion_0_shutter_0_'+str(wavelength)] = 0
                                coinc_hist_struct['coinc_rand_event_ion_0_shutter_1_'+str(wavelength)] = 0
                                coinc_hist_struct['coinc_rand_event_ion_1_shutter_0_'+str(wavelength)] = 0
                                coinc_hist_struct['coinc_rand_event_ion_1_shutter_1_'+str(wavelength)] = 0
                            
                        if not loaded_hist_struct:
                            # Add to histogram struct if it does not exist
                            for key in hist_keys:
                                if key+'_hist_ion_1_shutter_0_'+str(wavelength) not in hist_struct.keys():
                                    hist_struct[key+'_hist_ion_0_shutter_0_'+str(wavelength)] = np.zeros(hist_nr_bins)
                                    hist_struct[key+'_hist_ion_0_shutter_1_'+str(wavelength)] = np.zeros(hist_nr_bins)
                                    hist_struct[key+'_hist_ion_1_shutter_0_'+str(wavelength)] = np.zeros(hist_nr_bins)
                                    hist_struct[key+'_hist_ion_1_shutter_1_'+str(wavelength)] = np.zeros(hist_nr_bins)
                                    
                                    # Number of coincidence events
                                    hist_struct[key+'_hist_event_ion_0_shutter_0_'+str(wavelength)] = 0
                                    hist_struct[key+'_hist_event_ion_0_shutter_1_'+str(wavelength)] = 0
                                    hist_struct[key+'_hist_event_ion_1_shutter_0_'+str(wavelength)] = 0
                                    hist_struct[key+'_hist_event_ion_1_shutter_1_'+str(wavelength)] = 0
                
                    # Loop over events (copy of sort function)
                    for event in range(len(data['Event'])):
                        
                        try:
                            shutter_status = int(data['shutter_status'][event][0])
                            ion_flag = int(data['ADCV.Ion_flag'][event][0] > 100)
                        
                            # coincidence structure
                            if not loaded_coinc_struct and coinc_analysis:
                                current_event = np.array(data[diff_key][event])
                                current_rand_event = np.array(data[diff_rand_key][event])
                        
                                if hist_time_int[0] != None:
                                    mask =  (np.array(data[trig_key][event]) > hist_time_int[0]/TDC_res) & (np.array(data[trig_key][event]) < hist_time_int[1]/TDC_res)
                                    current_event = current_event[mask]
                            
                                    mask =  (np.array(data[trig_rand_key][event]) > hist_time_int[0]/TDC_res) & (np.array(data[trig_rand_key][event]) < hist_time_int[1]/TDC_res)
                                    current_rand_event = current_rand_event[mask]
                            
                                # Normalization
                                coinc_struct[f'coinc_event_ion_{ion_flag}_shutter_{shutter_status}_'+str(data['WavE_AMO (eV)'][event][0])] += 1
                                coinc_struct[f'coinc_rand_event_ion_{ion_flag}_shutter_{shutter_status}_'+str(data['WavE_AMO (eV)'][event][0])] += 1
                        
                                # Add to histogram
                                coinc_struct[f'coinc_ion_{ion_flag}_shutter_{shutter_status}_'+str(data['WavE_AMO (eV)'][event][0])] = coinc_struct[f'coinc_ion_{ion_flag}_shutter_{shutter_status}_'+str(data['WavE_AMO (eV)'][event][0])] + np.histogram(current_event, coinc_struct['edges'])[0]
                                coinc_struct[f'coinc_rand_ion_{ion_flag}_shutter_{shutter_status}_'+str(data['WavE_AMO (eV)'][event][0])] = coinc_struct[f'coinc_rand_ion_{ion_flag}_shutter_{shutter_status}_'+str(data['WavE_AMO (eV)'][event][0])] + np.histogram(current_rand_event, coinc_struct['edges'])[0]
                        
                            # Coincidence histogram structure,
                            if not loaded_coinc_hist_struct and coinc_analysis:
                                current_event = np.array(data[trig_key][event])
                                current_rand_event = np.array(data[trig_rand_key][event])
                        
                                if coinc_time_int[0] != None:
                                    mask =  (np.array(data[diff_key][event]) > coinc_time_int[0]/TDC_res) & (np.array(data[diff_key][event]) < coinc_time_int[1]/TDC_res)
                                    current_event = current_event[mask]
                                
                                    mask =  (np.array(data[diff_rand_key][event]) > coinc_time_int[0]/TDC_res) & (np.array(data[diff_rand_key][event]) < coinc_time_int[1]/TDC_res)
                                    current_rand_event = current_rand_event[mask]
                        
                                # Normalization
                                coinc_hist_struct[f'coinc_event_ion_{ion_flag}_shutter_{shutter_status}_'+str(data['WavE_AMO (eV)'][event][0])] += 1
                                coinc_hist_struct[f'coinc_rand_event_ion_{ion_flag}_shutter_{shutter_status}_'+str(data['WavE_AMO (eV)'][event][0])] += 1
                        
                                # Add to histogram
                                coinc_hist_struct[f'coinc_ion_{ion_flag}_shutter_{shutter_status}_'+str(data['WavE_AMO (eV)'][event][0])] = coinc_hist_struct[f'coinc_ion_{ion_flag}_shutter_{shutter_status}_'+str(data['WavE_AMO (eV)'][event][0])] + np.histogram(current_event, coinc_hist_struct['edges'])[0]
                                coinc_hist_struct[f'coinc_rand_ion_{ion_flag}_shutter_{shutter_status}_'+str(data['WavE_AMO (eV)'][event][0])] = coinc_hist_struct[f'coinc_rand_ion_{ion_flag}_shutter_{shutter_status}_'+str(data['WavE_AMO (eV)'][event][0])] + np.histogram(current_rand_event, coinc_hist_struct['edges'])[0]
                        
                            # Histogram structure
                            if not loaded_hist_struct:
                                current_event = [np.array(data[key][event]) for key in hist_keys]
                        
                                for key in range(len(current_event)):
                                
                                    # Normalization
                                    hist_struct[hist_keys[key]+f'_hist_event_ion_{ion_flag}_shutter_{shutter_status}_'+str(data['WavE_AMO (eV)'][event][0])] += 1
                            
                                    # Append to time structs
                                    hist_struct[hist_keys[key]+f'_hist_ion_{ion_flag}_shutter_{shutter_status}_'+str(data['WavE_AMO (eV)'][event][0])] = hist_struct[hist_keys[key]+f'_hist_ion_{ion_flag}_shutter_{shutter_status}_'+str(data['WavE_AMO (eV)'][event][0])] + np.histogram(current_event[key], hist_struct['edges'])[0]
                        except:
                            print(f'Error at event {data["Event"][event]} index {event} disregarded')
                    # Clear data
                    data.clear()
        
                print('----------------------------------')
    
    if not loaded_coinc_struct and coinc_analysis:
        coinc_struct['edges'] = coinc_struct['edges'] * TDC_res
    if not loaded_coinc_hist_struct and coinc_analysis:
        coinc_hist_struct['edges'] = coinc_hist_struct['edges'] * TDC_res
    if not loaded_hist_struct:
        hist_struct['edges'] = hist_struct['edges'] * TDC_res
    
    if np.any(np.array(write) != None):
    
        if not loaded_coinc_struct and coinc_analysis:
            # Write to file
            f = open(write[0], 'w')
            f.write(json.dumps(coinc_struct, cls=NumpyEncoder))
            f.close()
        
        if not loaded_hist_struct:
            # Write to file
            f = open(write[2], 'w')
            f.write(json.dumps(hist_struct, cls=NumpyEncoder))
            f.close()
        
        if not loaded_coinc_hist_struct and coinc_analysis:
            # Write to file
            f = open(write[1], 'w')
            f.write(json.dumps(coinc_hist_struct, cls=NumpyEncoder))
            f.close()
    print('----------------------------------')
    if coinc_analysis:
        return coinc_struct, coinc_hist_struct, hist_struct
    else:
        return hist_struct

def load_coincidence_struct(write):
    print('----------------------------------')
    print('-----Load Coincidence Struct-------')
    if os.path.exists(write):
        # Load coinc struct
        f = open(write, 'r')
        coinc_struct = json.loads(f.read())
        f.close()
        print('JSON file found and read')
        print('----------------------------------')
        return coinc_struct
    else:
        print('JSON file NOT found')

def load_coincidence_histogram_struct(write):
    print('----------------------------------')
    print('-----Load Coincidence Histogram Struct-------')
    if os.path.exists(write):
        # Load coinc struct
        f = open(write, 'r')
        coinc_struct = json.loads(f.read())
        f.close()
        print('JSON file found and read')
        print('----------------------------------')
        return coinc_struct
    else:
        print('JSON file NOT found')

def load_histogram_struct(write):
    print('----------------------------------')
    print('--------Load Histogram Struct-----------')
    if os.path.exists(write):
        # Load coinc struct
        f = open(write, 'r')
        coinc_struct = json.loads(f.read())
        f.close()
        print('JSON file found and read')
        print('----------------------------------')
        return coinc_struct
    else:
        print('JSON file NOT found')
