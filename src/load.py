import numpy as np
import json
import os, sys
import time

class NumpyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return json.JSONEncoder.default(self, obj)

def flatten_list(listr):
    return np.array([item for sublist in listr for item in sublist])

''' 
function: load_data(run_folder)

Reads all files in run_folder
containing the folder name,
and naming scheme
    <folder_name>-<file_number>.dat

run_folder
    folder position in os 
    ex. '/home/Run-001'
    
keys
    Specify keys to return
    ex. ['Event','TDC1.HEX_B']

ringing_keys
    Keys to remove ringings from
    
coinc_keys
    Keys to make coincidence analysis from
    given as (n,2) dim. list with
    [[<fast_trig>, <slow_trig>],.]
    ex. ['TDC1.ESP_F','TDC1.HEX_B']
    
time_window
    Specify time window for 
    coincidence analysis in ns
    
overwrite
    overwrites current JSON file
    
write_folder
    Folder to write to
    defaults to run_folder

memory_limit
    Limit of dictionary in
    memory before it is written
    to a file. Given in bytes.
    
    *The program uses more
    memory than this limit
    to load files, write files,
    and do analysis.

nr_triggers
    Number of triggers ac-
    ceptable for each event
    
proc_time
    Maximum process time,
    must not exceed master
    trigger time.

return
    data structure from file
    to see keys in dictionary
    use funciton
        print_keys_in_dict
'''
def load_data(run_folder, keys=[None], ringing_keys=[None], coinc_keys=[[None,None]], time_window=30000, silent=False, overwrite=False, write_folder=None, memory_limit=0.75E+9, nr_triggers=720, proc_time=300, ringing_time=[200,200,200], ringing_hist=False, ringing_hist_time=1000):
    print('-----------Load Run '+run_folder[-3:]+'-----------')
    if ringing_keys[0] == None and coinc_keys[0] != [None,None]:
        ringing_keys = flatten_list(coinc_keys)
    
    if write_folder == None:
        write_folder = run_folder
    
    # Check if load already exists    
    if os.path.exists(write_folder+'-dat-001.txt') and not overwrite:
        print('JSON file already exists')
        print('----------------------------------')
    else:
        # Dictionary to store all the data
        data = {}
        mode = 0 # Either reading an event or not
        header = 1 # Reading header
        
        retain_index = []
        retain_nr = 0
        
        # Memory tracking
        data_mem = 0
        dat_file = 1
        
        # Time tracking
        time_avg = 0.
        time_int = 0

        if ringing_keys[0] != None:
            # Make a key to show wich ringings have been removed
            data['ringing_keys'] = ringing_keys
            
            if ringing_hist:
                # Make a ringing histogram
                ringing_channels = 42000
                ringing_nr_bins = 2000
                data['ringing_edges'] = np.arange(0, ringing_channels+1/ringing_nr_bins, ringing_channels/ringing_nr_bins)
            
                for key in ringing_keys:
                    data[key+'_ringing_hist'] = np.zeros(ringing_nr_bins)
            

        # Go though all files in run_folder
        run_lst = os.listdir(run_folder)
        for filename in sorted(run_lst):
            t0 = time.time()
            # Making sure that the file in the folder has the correct naming scheme (is part of the run)
            if run_folder[-7:] == filename[:7]:

                if not silent:
                    print(f'Loading {filename[:7]} file {filename[8:11]}')
                file = os.path.join(run_folder, filename)

                # Making sure the program doesn't crash or corrupt
                if os.path.isfile(file):

                    # Read file line by line
                    with open(file) as file:
                        for line in file:

                            # Reading header if it doesn't exist
                            if header and 'header' not in data.keys():
                                # Check if we are at the end of header
                                if line == '%\n':
                                    data['header'] = 'read'
                                    data_mem += sys.getsizeof(data['header'])
                                    header = 0

                                elif line[0] != '%': # '%' means comment
                                    try:
                                        data[line.split('\t')[0]] = float(line.split('\t')[1])
                                        data_mem += sys.getsizeof(data[line.split('\t')[0]])
                                    except:
                                        data[line.split('\t')[0]] = line.split('\t')[1][:-1]
                                        data_mem += sys.getsizeof(data[line.split('\t')[0]])

                            # Start an event reading
                            elif line.split('\t')[0] == 'Event':
                                # append event number to list of events
                                if line.split('\t')[0] in data.keys():
                                
                                    mem = sys.getsizeof(data[line.split('\t')[0]])
                                    
                                    data[line.split('\t')[0]].append(int(line.split('\t')[1]))
                                    
                                    data_mem += sys.getsizeof(data[line.split('\t')[0]]) - mem + sys.getsizeof(1)
                                else:
                                    data[line.split('\t')[0]] = [int(line.split('\t')[1])]     
                                    data_mem += sys.getsizeof(data[line.split('\t')[0]])
                                # Change mode of reading
                                mode = 1

                            # Reading event mode
                            elif mode == 1:
                                
                                # Check if we are at the end of Event
                                if line == '%\n':
                                    mode = 0
                                    
                                    # End of event analysis
                                    # Switch to old storage
                                    try: 
                                        # Check for errors
                                        if sum(data['errors'][-1]) != 0 or len(data['TDC1.trigger'][-1]) != nr_triggers or sum(data['proc_time'][-1]) > proc_time: 
                                            # Detele event in case
                                            for key in data.keys():
                                                # Check if we are dealing with the header
                                                if not isinstance(data[key],(list,tuple,np.ndarray)):
                                                    pass
                                                elif len(data[key]) < len(data['Event']):
                                                    pass
                                                elif 'Coinc_' in key:
                                                    pass 
                                                # Check if it is the ringing keys
                                                elif 'ringing' in key:
                                                    pass
                                                # Else continue
                                                else:
                                                    del data[key][-1]
                                        
                                        else:
                                            # Remove ringings if requested
                                            if ringing_keys[0] != None:
                                                
                                                # Find events after ringing
                                                
                                                current_event = [np.array(data[key][-1]) for key in ringing_keys]
                                                if ringing_hist:
                                                    current_hist_event = [np.array(data[key][-1]) for key in ringing_keys]

                                                for key in range(len(ringing_keys)):
                                                    mem = sys.getsizeof(data[ringing_keys[key]][-1])
                                                    
                                                    ring_mask = np.diff(current_event[key]) < (ringing_time[key] / data['TDC.res'])
                                                    
                                                    if ringing_hist:
                                                        ring_hist_mask = np.diff(current_hist_event[key]) < (ringing_hist_time / data['TDC.res'])
                                                    
                                                        # Get the trigger times for histogram of ringings
                                                        while(np.any(ring_hist_mask)):
                                                            current_hist_event[key] = current_hist_event[key][np.invert(np.insert(ring_hist_mask,0,False))]
                                                            ring_hist_mask = np.diff(current_hist_event[key]) < (ringing_hist_time / data['TDC.res'])
                                                    
                                                        # Fill ringing histogram
                                                        hist_spikes, hist_times = np.meshgrid(current_hist_event[key],current_event[key])
                                                        
                                                        hist_diff = hist_times - hist_spikes
                                                        
                                                        # Comparision: slow comes after the fast signal and is withing a time window of the fast signal
                                                        ring_hist_mask = np.logical_and(np.sign(hist_diff) == 1, hist_diff < ringing_hist_time / data['TDC.res'])
                                                        
                                                        data[ringing_keys[key]+'_ringing_hist'] = data[ringing_keys[key]+'_ringing_hist'] + np.histogram(hist_diff[ring_hist_mask].flatten(), data['ringing_edges'])[0]
                                                    
                                                    # Remove ringings from current event
                                                    while(np.any(ring_mask)):
                                                        current_event[key] = current_event[key][np.invert(np.insert(ring_mask,0,False))]
                                                        ring_mask = np.diff(current_event[key]) < (ringing_time[key] / data['TDC.res'])
                                                        
                                                    data[ringing_keys[key]][-1] = current_event[key].tolist()
                                                    
                                                    data_mem += sys.getsizeof(data[ringing_keys[key]][-1]) - mem

                                            # Make coincidence analysis of given keys.
                                            if coinc_keys[0] != [None,None]:
                                                for fast_key, slow_key in coinc_keys:

                                                    # Keys to consider
                                                    trig_key = 'Coinc_'+fast_key+'_'+slow_key+'_trig'
                                                    diff_key = 'Coinc_'+fast_key+'_'+slow_key+'_diff'
                                                    trig_rand_key = 'Coinc_rand_'+fast_key+'_'+slow_key+'_trig'
                                                    diff_rand_key = 'Coinc_rand_'+fast_key+'_'+slow_key+'_diff'

                                                    # check if current event is being retained
                                                    if len(data['Event']) - 1 not in retain_index:

                                                        # If  prevoius event is retained first process this
                                                        if len(retain_index) > 0:

                                                            # Process previous event
                                                            for r_ind in range(len(retain_index)):

                                                                index = retain_index[r_ind - retain_nr]
                                                                del retain_index[r_ind - retain_nr]
                                                                retain_nr += 1

                                                                if data['WavE_AMO (eV)'][index] == data['WavE_AMO (eV)'][-1] and \
                                                                        data['shutter_status'][index][0] == \
                                                                        data['shutter_status'][-1][0] and \
                                                                        (data['ADCV.Ion_flag'][index][0] > 100) == (
                                                                        data['ADCV.Ion_flag'][-1][0] > 100):

                                                                    if trig_rand_key in data.keys():

                                                                        # compare current fast_trig to previous slow_trig
                                                                        mem = sys.getsizeof(
                                                                            data[trig_rand_key]) + sys.getsizeof(
                                                                            data[diff_rand_key])

                                                                        # Create mesgrid to compare
                                                                        fast_v, slow_v = np.meshgrid(data[fast_key][index],
                                                                                                    data[slow_key][-1])
                                                                        diff_mat = slow_v - fast_v  # time between each event

                                                                        # Comparision: slow comes after the fast signal and is withing a time window of the fast signal
                                                                        diff_mask = np.logical_and(np.sign(diff_mat) == 1,
                                                                                                diff_mat < time_window /
                                                                                                data['TDC.res'])

                                                                        # Append to output
                                                                        data[trig_rand_key][index] = fast_v[diff_mask].flatten()
                                                                        data[diff_rand_key][index] = diff_mat[
                                                                            diff_mask].flatten()

                                                                        data_mem += sys.getsizeof(
                                                                            data[trig_rand_key]) + sys.getsizeof(
                                                                            data[diff_rand_key]) - mem + sys.getsizeof(
                                                                            data[trig_rand_key][-1]) + sys.getsizeof(
                                                                            data[diff_rand_key][-1])

                                                                    else:
                                                                        # compare current fast_trig to previous slow_trig
                                                                        # Create mesgrid to compare
                                                                        fast_v, slow_v = np.meshgrid(data[fast_key][index],
                                                                                                    data[slow_key][-1])
                                                                        diff_mat = slow_v - fast_v  # time between each event

                                                                        # Comparision: slow comes after the fast signal and is withing a time window of the fast signal
                                                                        diff_mask = np.logical_and(np.sign(diff_mat) == 1,
                                                                                                diff_mat < time_window /
                                                                                                data['TDC.res'])

                                                                        # Append to output
                                                                        data[trig_rand_key] = [fast_v[diff_mask].flatten()]
                                                                        data[diff_rand_key] = [diff_mat[diff_mask].flatten()]

                                                                        data_mem += sys.getsizeof(
                                                                            data[trig_rand_key]) + sys.getsizeof(
                                                                            data[diff_rand_key]) - mem + sys.getsizeof(
                                                                            data[trig_rand_key][-1]) + sys.getsizeof(
                                                                            data[diff_rand_key][-1])

                                                                else:
                                                                    retain_index.append(index)

                                                            retain_nr = 0

                                                        # write to data struct
                                                        # Check if the flag is already in the data structure
                                                        if trig_key in data.keys():

                                                            mem = sys.getsizeof(data[trig_key]) + sys.getsizeof(data[diff_key])

                                                            # Create mesgrid to compare
                                                            fast_v, slow_v = np.meshgrid(data[fast_key][-1], data[slow_key][-1])
                                                            diff_mat = slow_v - fast_v # time between each event

                                                            # Comparision: slow comes after the fast signal and is withing a time window of the fast signal
                                                            diff_mask = np.logical_and(np.sign(diff_mat) == 1, diff_mat < time_window/data['TDC.res'])

                                                            # Append to output
                                                            data[trig_key].append(fast_v[diff_mask].flatten())
                                                            data[diff_key].append(diff_mat[diff_mask].flatten())

                                                            data_mem += sys.getsizeof(data[trig_key]) + sys.getsizeof(data[diff_key]) - mem + sys.getsizeof(data[trig_key][-1]) + sys.getsizeof(data[diff_key][-1])

                                                            # Process random events

                                                            # first check if it is the first event
                                                            if len(data['Event']) > 1:
                                                                if data['WavE_AMO (eV)'][-2] == data['WavE_AMO (eV)'][-1] and \
                                                                data['shutter_status'][-2][0] == data['shutter_status'][-1][0] and \
                                                                (data['ADCV.Ion_flag'][-2][0] > 100) == (data['ADC.Ion_Flag'][-1][0] > 1000):

                                                                    if trig_rand_key in data.keys():
                                                                        # compare current fast_trig to previous slow_trig
                                                                        mem = sys.getsizeof(data[trig_rand_key]) + sys.getsizeof(data[diff_rand_key])

                                                                        # Create mesgrid to compare
                                                                        fast_v, slow_v = np.meshgrid(data[fast_key][-1], data[slow_key][-2])
                                                                        diff_mat = slow_v - fast_v # time between each event

                                                                        # Comparision: slow comes after the fast signal and is withing a time window of the fast signal
                                                                        diff_mask = np.logical_and(np.sign(diff_mat) == 1, diff_mat < time_window/data['TDC.res'])

                                                                        # Append to output
                                                                        data[trig_rand_key].append(fast_v[diff_mask].flatten())
                                                                        data[diff_rand_key].append(diff_mat[diff_mask].flatten())

                                                                        data_mem += sys.getsizeof(data[trig_rand_key]) + sys.getsizeof(data[diff_rand_key]) - mem + sys.getsizeof(data[trig_rand_key][-1]) + sys.getsizeof(data[diff_rand_key][-1])

                                                                    else:
                                                                        # compare current fast_trig to previous slow_trig
                                                                        # Create mesgrid to compare
                                                                        fast_v, slow_v = np.meshgrid(data[fast_key][-1], data[slow_key][-2])
                                                                        diff_mat = slow_v - fast_v # time between each event

                                                                        # Comparision: slow comes after the fast signal and is withing a time window of the fast signal
                                                                        diff_mask = np.logical_and(np.sign(diff_mat) == 1, diff_mat < time_window/data['TDC.res'])

                                                                        # Append to output
                                                                        data[trig_rand_key] = [fast_v[diff_mask].flatten()]
                                                                        data[diff_rand_key] = [diff_mat[diff_mask].flatten()]

                                                                        data_mem += sys.getsizeof(data[trig_rand_key]) + sys.getsizeof(data[diff_rand_key]) - mem + sys.getsizeof(data[trig_rand_key][-1]) + sys.getsizeof(data[diff_rand_key][-1])

                                                                else:
                                                                    if trig_rand_key in data.keys():
                                                                        data[trig_rand_key].append(np.array([0]))
                                                                        data[diff_rand_key].append(np.array([0]))
                                                                        retain_index.append(len(data['Event'])-1)
                                                                    else:
                                                                        # Append to output
                                                                        data[trig_rand_key] = [np.array([0])]
                                                                        data[diff_rand_key] = [np.array([0])]
                                                                        retain_index.append(len(data['Event'])-1)
                                                            else:
                                                                if trig_rand_key in data.keys():
                                                                    data[trig_rand_key].append(np.array([0]))
                                                                    data[diff_rand_key].append(np.array([0]))
                                                                    retain_index.append(len(data['Event'])-1)
                                                                else:
                                                                    # Append to output
                                                                    data[trig_rand_key] = [np.array([0])]
                                                                    data[diff_rand_key] = [np.array([0])]
                                                                    retain_index.append(len(data['Event'])-1)

                                                        else:

                                                            # Create mesgrid to compare
                                                            fast_v, slow_v = np.meshgrid(data[fast_key][-1], data[slow_key][-1])
                                                            diff_mat = slow_v - fast_v # time between each event

                                                            # Comparision: slow comes after the fast signal and is withing a time window of the fast signal
                                                            diff_mask = np.logical_and(np.sign(diff_mat) == 1, diff_mat < time_window/data['TDC.res'])

                                                            # Append to output
                                                            data[trig_key] = [fast_v[diff_mask].flatten()]
                                                            data[diff_key] = [diff_mat[diff_mask].flatten()]

                                                            data_mem += sys.getsizeof(data[trig_key]) + sys.getsizeof(data[diff_key]) + sys.getsizeof(data[trig_key][-1]) + sys.getsizeof(data[diff_key][-1])

                                                            # Process random events on next event.
                                                            if trig_rand_key in data.keys():
                                                                data[trig_rand_key].append(np.array([0]))
                                                                data[diff_rand_key].append(np.array([0]))
                                                                retain_index.append(len(data['Event'])-1)
                                                            else:
                                                                # Append to output
                                                                data[trig_rand_key] = [np.array([0])]
                                                                data[diff_rand_key] = [np.array([0])]
                                                                retain_index.append(len(data['Event'])-1)

                                                    #We still need the analysis
                                                    else:
                                                        # write to data struct
                                                        # Check if the flag is already in the data structure
                                                        if trig_key in data.keys():

                                                            mem = sys.getsizeof(data[trig_key]) + sys.getsizeof(
                                                                data[diff_key])

                                                            # Create mesgrid to compare
                                                            fast_v, slow_v = np.meshgrid(data[fast_key][-1],
                                                                                        data[slow_key][-1])
                                                            diff_mat = slow_v - fast_v  # time between each event

                                                            # Comparision: slow comes after the fast signal and is withing a time window of the fast signal
                                                            diff_mask = np.logical_and(np.sign(diff_mat) == 1,
                                                                                    diff_mat < time_window / data[
                                                                                        'TDC.res'])

                                                            # Append to output
                                                            data[trig_key].append(fast_v[diff_mask].flatten())
                                                            data[diff_key].append(diff_mat[diff_mask].flatten())

                                                            data_mem += sys.getsizeof(data[trig_key]) + sys.getsizeof(
                                                                data[diff_key]) - mem + sys.getsizeof(
                                                                data[trig_key][-1]) + sys.getsizeof(data[diff_key][-1])

                                                            # Process random events

                                                            # Process random events on next event.
                                                            if trig_rand_key in data.keys():
                                                                data[trig_rand_key].append(np.array([0]))
                                                                data[diff_rand_key].append(np.array([0]))
                                                            else:
                                                                # Append to output
                                                                data[trig_rand_key] = [np.array([0])]
                                                                data[diff_rand_key] = [np.array([0])]

                                                        else:

                                                            # Create mesgrid to compare
                                                            fast_v, slow_v = np.meshgrid(data[fast_key][-1],
                                                                                        data[slow_key][-1])
                                                            diff_mat = slow_v - fast_v  # time between each event

                                                            # Comparision: slow comes after the fast signal and is withing a time window of the fast signal
                                                            diff_mask = np.logical_and(np.sign(diff_mat) == 1,
                                                                                    diff_mat < time_window / data[
                                                                                        'TDC.res'])

                                                            # Append to output
                                                            data[trig_key] = [fast_v[diff_mask].flatten()]
                                                            data[diff_key] = [diff_mat[diff_mask].flatten()]

                                                            data_mem += sys.getsizeof(data[trig_key]) + sys.getsizeof(
                                                                data[diff_key]) + sys.getsizeof(
                                                                data[trig_key][-1]) + sys.getsizeof(data[diff_key][-1])

                                                            # Process random events on next event.
                                                            if trig_rand_key in data.keys():
                                                                data[trig_rand_key].append(np.array([0]))
                                                                data[diff_rand_key].append(np.array([0]))
                                                            else:
                                                                # Append to output
                                                                data[trig_rand_key] = [np.array([0])]
                                                                data[diff_rand_key] = [np.array([0])]
                                    except:
                                        # Check for errors
                                        if sum(data['errors'][-1]) != 0 or len(data['TDC1.Trigger'][-1]) != nr_triggers or sum(data['proc_time'][-1]) > proc_time: 
                                            # Detele event in case
                                            for key in data.keys():
                                                # Check if we are dealing with the header
                                                if not isinstance(data[key],(list,tuple,np.ndarray)):
                                                    pass
                                                elif len(data[key]) < len(data['Event']):
                                                    pass
                                                elif 'Coinc_' in key:
                                                    pass 
                                                # Check if it is the ringing keys
                                                elif 'ringing' in key:
                                                    pass
                                                # Else continue
                                                else:
                                                    del data[key][-1]
                                        
                                        else:
                                            # Remove ringings if requested
                                            if ringing_keys[0] != None:
                                                
                                                # Find events after ringing
                                                
                                                current_event = [np.array(data[key][-1]) for key in ringing_keys]
                                                if ringing_hist:
                                                    current_hist_event = [np.array(data[key][-1]) for key in ringing_keys]

                                                for key in range(len(ringing_keys)):
                                                    mem = sys.getsizeof(data[ringing_keys[key]][-1])
                                                    
                                                    ring_mask = np.diff(current_event[key]) < (ringing_time[key] / data['TDC.res'])
                                                    
                                                    if ringing_hist:
                                                        ring_hist_mask = np.diff(current_hist_event[key]) < (ringing_hist_time / data['TDC.res'])
                                                    
                                                        # Get the trigger times for histogram of ringings
                                                        while(np.any(ring_hist_mask)):
                                                            current_hist_event[key] = current_hist_event[key][np.invert(np.insert(ring_hist_mask,0,False))]
                                                            ring_hist_mask = np.diff(current_hist_event[key]) < (ringing_hist_time / data['TDC.res'])
                                                    
                                                        # Fill ringing histogram
                                                        hist_spikes, hist_times = np.meshgrid(current_hist_event[key],current_event[key])
                                                        
                                                        hist_diff = hist_times - hist_spikes
                                                        
                                                        # Comparision: slow comes after the fast signal and is withing a time window of the fast signal
                                                        ring_hist_mask = np.logical_and(np.sign(hist_diff) == 1, hist_diff < ringing_hist_time / data['TDC.res'])
                                                        
                                                        data[ringing_keys[key]+'_ringing_hist'] = data[ringing_keys[key]+'_ringing_hist'] + np.histogram(hist_diff[ring_hist_mask].flatten(), data['ringing_edges'])[0]
                                                    
                                                    # Remove ringings from current event
                                                    while(np.any(ring_mask)):
                                                        current_event[key] = current_event[key][np.invert(np.insert(ring_mask,0,False))]
                                                        ring_mask = np.diff(current_event[key]) < (ringing_time[key] / data['TDC.res'])
                                                        
                                                    data[ringing_keys[key]][-1] = current_event[key].tolist()
                                                    
                                                    data_mem += sys.getsizeof(data[ringing_keys[key]][-1]) - mem

                                            # Make coincidence analysis of given keys.
                                            if coinc_keys[0] != [None,None]:
                                                for fast_key, slow_key in coinc_keys:

                                                    # Keys to consider
                                                    trig_key = 'Coinc_'+fast_key+'_'+slow_key+'_trig'
                                                    diff_key = 'Coinc_'+fast_key+'_'+slow_key+'_diff'
                                                    trig_rand_key = 'Coinc_rand_'+fast_key+'_'+slow_key+'_trig'
                                                    diff_rand_key = 'Coinc_rand_'+fast_key+'_'+slow_key+'_diff'

                                                    # check if current event is being retained
                                                    if len(data['Event']) - 1 not in retain_index:

                                                        # If  prevoius event is retained first process this
                                                        if len(retain_index) > 0:

                                                            # Process previous event
                                                            for r_ind in range(len(retain_index)):

                                                                index = retain_index[r_ind - retain_nr]
                                                                del retain_index[r_ind - retain_nr]
                                                                retain_nr += 1

                                                                if data['WavE_AMO (eV)_ctr'][index] == data['WavE_AMO (eV)_ctr'][-1] and \
                                                                        data['shutter control_ctr'][index][0] == \
                                                                        data['shutter control_ctr'][-1][0]:

                                                                    if trig_rand_key in data.keys():

                                                                        # compare current fast_trig to previous slow_trig
                                                                        mem = sys.getsizeof(
                                                                            data[trig_rand_key]) + sys.getsizeof(
                                                                            data[diff_rand_key])

                                                                        # Create mesgrid to compare
                                                                        fast_v, slow_v = np.meshgrid(data[fast_key][index],
                                                                                                    data[slow_key][-1])
                                                                        diff_mat = slow_v - fast_v  # time between each event

                                                                        # Comparision: slow comes after the fast signal and is withing a time window of the fast signal
                                                                        diff_mask = np.logical_and(np.sign(diff_mat) == 1,
                                                                                                diff_mat < time_window /
                                                                                                data['TDC.res'])

                                                                        # Append to output
                                                                        data[trig_rand_key][index] = fast_v[diff_mask].flatten()
                                                                        data[diff_rand_key][index] = diff_mat[
                                                                            diff_mask].flatten()

                                                                        data_mem += sys.getsizeof(
                                                                            data[trig_rand_key]) + sys.getsizeof(
                                                                            data[diff_rand_key]) - mem + sys.getsizeof(
                                                                            data[trig_rand_key][-1]) + sys.getsizeof(
                                                                            data[diff_rand_key][-1])

                                                                    else:
                                                                        # compare current fast_trig to previous slow_trig
                                                                        # Create mesgrid to compare
                                                                        fast_v, slow_v = np.meshgrid(data[fast_key][index],
                                                                                                    data[slow_key][-1])
                                                                        diff_mat = slow_v - fast_v  # time between each event

                                                                        # Comparision: slow comes after the fast signal and is withing a time window of the fast signal
                                                                        diff_mask = np.logical_and(np.sign(diff_mat) == 1,
                                                                                                diff_mat < time_window /
                                                                                                data['TDC.res'])

                                                                        # Append to output
                                                                        data[trig_rand_key] = [fast_v[diff_mask].flatten()]
                                                                        data[diff_rand_key] = [diff_mat[diff_mask].flatten()]

                                                                        data_mem += sys.getsizeof(
                                                                            data[trig_rand_key]) + sys.getsizeof(
                                                                            data[diff_rand_key]) - mem + sys.getsizeof(
                                                                            data[trig_rand_key][-1]) + sys.getsizeof(
                                                                            data[diff_rand_key][-1])

                                                                else:
                                                                    retain_index.append(index)

                                                            retain_nr = 0

                                                        # write to data struct
                                                        # Check if the flag is already in the data structure
                                                        if trig_key in data.keys():

                                                            mem = sys.getsizeof(data[trig_key]) + sys.getsizeof(data[diff_key])

                                                            # Create mesgrid to compare
                                                            fast_v, slow_v = np.meshgrid(data[fast_key][-1], data[slow_key][-1])
                                                            diff_mat = slow_v - fast_v # time between each event

                                                            # Comparision: slow comes after the fast signal and is withing a time window of the fast signal
                                                            diff_mask = np.logical_and(np.sign(diff_mat) == 1, diff_mat < time_window/data['TDC.res'])

                                                            # Append to output
                                                            data[trig_key].append(fast_v[diff_mask].flatten())
                                                            data[diff_key].append(diff_mat[diff_mask].flatten())

                                                            data_mem += sys.getsizeof(data[trig_key]) + sys.getsizeof(data[diff_key]) - mem + sys.getsizeof(data[trig_key][-1]) + sys.getsizeof(data[diff_key][-1])

                                                            # Process random events

                                                            # first check if it is the first event
                                                            if len(data['Event']) > 1:
                                                                if data['WavE_AMO (eV)_ctr'][-2] == data['WavE_AMO (eV)_ctr'][-1] and \
                                                                data['shutter control_ctr'][-2][0] == data['shutter control_ctr'][-1][0]:

                                                                    if trig_rand_key in data.keys():
                                                                        # compare current fast_trig to previous slow_trig
                                                                        mem = sys.getsizeof(data[trig_rand_key]) + sys.getsizeof(data[diff_rand_key])

                                                                        # Create mesgrid to compare
                                                                        fast_v, slow_v = np.meshgrid(data[fast_key][-1], data[slow_key][-2])
                                                                        diff_mat = slow_v - fast_v # time between each event

                                                                        # Comparision: slow comes after the fast signal and is withing a time window of the fast signal
                                                                        diff_mask = np.logical_and(np.sign(diff_mat) == 1, diff_mat < time_window/data['TDC.res'])

                                                                        # Append to output
                                                                        data[trig_rand_key].append(fast_v[diff_mask].flatten())
                                                                        data[diff_rand_key].append(diff_mat[diff_mask].flatten())

                                                                        data_mem += sys.getsizeof(data[trig_rand_key]) + sys.getsizeof(data[diff_rand_key]) - mem + sys.getsizeof(data[trig_rand_key][-1]) + sys.getsizeof(data[diff_rand_key][-1])

                                                                    else:
                                                                        # compare current fast_trig to previous slow_trig
                                                                        # Create mesgrid to compare
                                                                        fast_v, slow_v = np.meshgrid(data[fast_key][-1], data[slow_key][-2])
                                                                        diff_mat = slow_v - fast_v # time between each event

                                                                        # Comparision: slow comes after the fast signal and is withing a time window of the fast signal
                                                                        diff_mask = np.logical_and(np.sign(diff_mat) == 1, diff_mat < time_window/data['TDC.res'])

                                                                        # Append to output
                                                                        data[trig_rand_key] = [fast_v[diff_mask].flatten()]
                                                                        data[diff_rand_key] = [diff_mat[diff_mask].flatten()]

                                                                        data_mem += sys.getsizeof(data[trig_rand_key]) + sys.getsizeof(data[diff_rand_key]) - mem + sys.getsizeof(data[trig_rand_key][-1]) + sys.getsizeof(data[diff_rand_key][-1])

                                                                else:
                                                                    if trig_rand_key in data.keys():
                                                                        data[trig_rand_key].append(np.array([0]))
                                                                        data[diff_rand_key].append(np.array([0]))
                                                                        retain_index.append(len(data['Event'])-1)
                                                                    else:
                                                                        # Append to output
                                                                        data[trig_rand_key] = [np.array([0])]
                                                                        data[diff_rand_key] = [np.array([0])]
                                                                        retain_index.append(len(data['Event'])-1)
                                                            else:
                                                                if trig_rand_key in data.keys():
                                                                    data[trig_rand_key].append(np.array([0]))
                                                                    data[diff_rand_key].append(np.array([0]))
                                                                    retain_index.append(len(data['Event'])-1)
                                                                else:
                                                                    # Append to output
                                                                    data[trig_rand_key] = [np.array([0])]
                                                                    data[diff_rand_key] = [np.array([0])]
                                                                    retain_index.append(len(data['Event'])-1)

                                                        else:

                                                            # Create mesgrid to compare
                                                            fast_v, slow_v = np.meshgrid(data[fast_key][-1], data[slow_key][-1])
                                                            diff_mat = slow_v - fast_v # time between each event

                                                            # Comparision: slow comes after the fast signal and is withing a time window of the fast signal
                                                            diff_mask = np.logical_and(np.sign(diff_mat) == 1, diff_mat < time_window/data['TDC.res'])

                                                            # Append to output
                                                            data[trig_key] = [fast_v[diff_mask].flatten()]
                                                            data[diff_key] = [diff_mat[diff_mask].flatten()]

                                                            data_mem += sys.getsizeof(data[trig_key]) + sys.getsizeof(data[diff_key]) + sys.getsizeof(data[trig_key][-1]) + sys.getsizeof(data[diff_key][-1])

                                                            # Process random events on next event.
                                                            if trig_rand_key in data.keys():
                                                                data[trig_rand_key].append(np.array([0]))
                                                                data[diff_rand_key].append(np.array([0]))
                                                                retain_index.append(len(data['Event'])-1)
                                                            else:
                                                                # Append to output
                                                                data[trig_rand_key] = [np.array([0])]
                                                                data[diff_rand_key] = [np.array([0])]
                                                                retain_index.append(len(data['Event'])-1)

                                                    #We still need the analysis
                                                    else:
                                                        # write to data struct
                                                        # Check if the flag is already in the data structure
                                                        if trig_key in data.keys():

                                                            mem = sys.getsizeof(data[trig_key]) + sys.getsizeof(
                                                                data[diff_key])

                                                            # Create mesgrid to compare
                                                            fast_v, slow_v = np.meshgrid(data[fast_key][-1],
                                                                                        data[slow_key][-1])
                                                            diff_mat = slow_v - fast_v  # time between each event

                                                            # Comparision: slow comes after the fast signal and is withing a time window of the fast signal
                                                            diff_mask = np.logical_and(np.sign(diff_mat) == 1,
                                                                                    diff_mat < time_window / data[
                                                                                        'TDC.res'])

                                                            # Append to output
                                                            data[trig_key].append(fast_v[diff_mask].flatten())
                                                            data[diff_key].append(diff_mat[diff_mask].flatten())

                                                            data_mem += sys.getsizeof(data[trig_key]) + sys.getsizeof(
                                                                data[diff_key]) - mem + sys.getsizeof(
                                                                data[trig_key][-1]) + sys.getsizeof(data[diff_key][-1])

                                                            # Process random events

                                                            # Process random events on next event.
                                                            if trig_rand_key in data.keys():
                                                                data[trig_rand_key].append(np.array([0]))
                                                                data[diff_rand_key].append(np.array([0]))
                                                            else:
                                                                # Append to output
                                                                data[trig_rand_key] = [np.array([0])]
                                                                data[diff_rand_key] = [np.array([0])]

                                                        else:

                                                            # Create mesgrid to compare
                                                            fast_v, slow_v = np.meshgrid(data[fast_key][-1],
                                                                                        data[slow_key][-1])
                                                            diff_mat = slow_v - fast_v  # time between each event

                                                            # Comparision: slow comes after the fast signal and is withing a time window of the fast signal
                                                            diff_mask = np.logical_and(np.sign(diff_mat) == 1,
                                                                                    diff_mat < time_window / data[
                                                                                        'TDC.res'])

                                                            # Append to output
                                                            data[trig_key] = [fast_v[diff_mask].flatten()]
                                                            data[diff_key] = [diff_mat[diff_mask].flatten()]

                                                            data_mem += sys.getsizeof(data[trig_key]) + sys.getsizeof(
                                                                data[diff_key]) + sys.getsizeof(
                                                                data[trig_key][-1]) + sys.getsizeof(data[diff_key][-1])

                                                            # Process random events on next event.
                                                            if trig_rand_key in data.keys():
                                                                data[trig_rand_key].append(np.array([0]))
                                                                data[diff_rand_key].append(np.array([0]))
                                                            else:
                                                                # Append to output
                                                                data[trig_rand_key] = [np.array([0])]
                                                                data[diff_rand_key] = [np.array([0])]
                                    


                                                    
                                elif line[0] != '%': # '%' means comment
                                    # write to data struct
                                    # Check if the flag is already in the data structure
                                    if line.split('\t')[0] in data.keys():

                                        # Try to append float (int) values
                                        try:
                                            mem = sys.getsizeof(data[line.split('\t')[0]])
                                            
                                            # Check if the line is seperated values and append either a number or an array
                                            if len(line.split('\t')[1].split()) > 1:
                                                
                                                # Check if it is a float or int
                                                if '.' in line.split('\t')[1]:
                                                    data[line.split('\t')[0]].append([float(i) for i in line.split('\t')[1].split()])
                                                
                                                # It is an int
                                                else:
                                                    data[line.split('\t')[0]].append([int(i) for i in line.split('\t')[1].split()])
                                            
                                            else:

                                                # Check if it is a float or int
                                                if '.' in line.split('\t')[1]:
                                                    data[line.split('\t')[0]].append([float(line.split('\t')[1])])
                                                
                                                # It is an int
                                                else:
                                                    data[line.split('\t')[0]].append([int(line.split('\t')[1])])
                                                
                                            data_mem += sys.getsizeof(data[line.split('\t')[0]]) - mem + sys.getsizeof(data[line.split('\t')[0]][-1])

                                        # If that fails just append it as a string
                                        except:
                                            mem = sys.getsizeof(data[line.split('\t')[0]])
                                            
                                            data[line.split('\t')[0]].append(line.split('\t')[1][:-1])
                                            
                                            data_mem += sys.getsizeof(data[line.split('\t')[0]]) - mem + sys.getsizeof(data[line.split('\t')[0]][-1])
                                    else:
                                        # Try to create the flags in data struct as floats
                                        try:
                                            # Check if the line is seperated values and create either a number or an array
                                            if len(line.split('\t')[1].split()) > 1:
                                                
                                                # Check if it is a float or int
                                                if '.' in line.split('\t')[1]:
                                                    data[line.split('\t')[0]] = [[float(i) for i in line.split('\t')[1].split()]]
                                                
                                                # It is an int
                                                else:
                                                    data[line.split('\t')[0]] = [[int(i) for i in line.split('\t')[1].split()]]
                                            else:
                                                
                                                # Check if it is a float or int
                                                if '.' in line.split('\t')[1]:
                                                    data[line.split('\t')[0]] = [[float(line.split('\t')[1])]]
                                                
                                                # It is an int
                                                else:
                                                    data[line.split('\t')[0]] = [[int(line.split('\t')[1])]]
                                            
                                            data_mem += sys.getsizeof(data[line.split('\t')[0]]) + sys.getsizeof(data[line.split('\t')[0]][-1])

                                        # If that fails just create it as a string
                                        except:
                                            data[line.split('\t')[0]] = [line.split('\t')[1][:-1]]
                                            
                                            data_mem += sys.getsizeof(data[line.split('\t')[0]]) + sys.getsizeof(data[line.split('\t')[0]][-1])
                        
                        else:
                            
                            # End of event (and file) analysis
                            # Switch to old storage

                            try:
                                # Check for errors
                                if sum(data['errors'][-1]) != 0 or len(data['TDC1.trigger'][-1]) != nr_triggers or sum(data['proc_time'][-1]) > proc_time:
                                    # Detele event in case
                                    for key in data.keys():
                                        # Check if we are dealing with the header
                                        if not isinstance(data[key],(list,tuple,np.ndarray)):
                                            pass
                                        elif len(data[key]) < len(data['Event']):
                                            pass
                                        elif 'Coinc_' in key:
                                            pass
                                        # Check if it is the ringing keys
                                        elif 'ringing' in key:
                                            pass
                                        # Else continue
                                        else:
                                            del data[key][-1]
                                        
                                else:
                                                
                                    # Remove ringings if requested
                                    if ringing_keys[0] != None:
                                        current_event = [np.array(data[key][-1]) for key in ringing_keys]
                                        if ringing_hist:
                                            current_hist_event = [np.array(data[key][-1]) for key in ringing_keys]

                                        for key in range(len(ringing_keys)):
                                            mem = sys.getsizeof(data[ringing_keys[key]][-1])
                                                    
                                            ring_mask = np.diff(current_event[key]) < (ringing_time[key] / data['TDC.res'])
                                            
                                            if ringing_hist:
                                                ring_hist_mask = np.diff(current_hist_event[key]) < (ringing_hist_time / data['TDC.res'])
                                                    
                                                # Get the trigger times for histogram of ringings
                                                while(np.any(ring_hist_mask)):
                                                    current_hist_event[key] = current_hist_event[key][np.invert(np.insert(ring_hist_mask,0,False))]
                                                    ring_hist_mask = np.diff(current_hist_event[key]) < (ringing_hist_time / data['TDC.res'])
                                                    
                                                # Fill ringing histogram
                                                hist_spikes, hist_times = np.meshgrid(current_hist_event[key],current_event[key])
                                                        
                                                hist_diff = hist_times - hist_spikes
                                                        
                                                # Comparision: slow comes after the fast signal and is withing a time window of the fast signal
                                                ring_hist_mask = np.logical_and(np.sign(hist_diff) == 1, hist_diff < ringing_hist_time / data['TDC.res'])
                                                        
                                                data[ringing_keys[key]+'_ringing_hist'] = data[ringing_keys[key]+'_ringing_hist'] + np.histogram(hist_diff[ring_hist_mask].flatten(), data['ringing_edges'])[0]
                                                    
                                            # Remove ringings from current event
                                            while(np.any(ring_mask)):
                                                current_event[key] = current_event[key][np.invert(np.insert(ring_mask,0,False))]
                                                ring_mask = np.diff(current_event[key]) < (ringing_time[key] / data['TDC.res'])
                                                        
                                            data[ringing_keys[key]][-1] = current_event[key].tolist()
                                                            
                                            data_mem += sys.getsizeof(data[ringing_keys[key]][-1]) - mem
                                        
                                    # Make coincidence analysis of given keys.
                                    if coinc_keys[0] != [None,None]:
                                        for fast_key, slow_key in coinc_keys:

                                            # Keys to consider
                                            trig_key = 'Coinc_' + fast_key + '_' + slow_key + '_trig'
                                            diff_key = 'Coinc_' + fast_key + '_' + slow_key + '_diff'
                                            trig_rand_key = 'Coinc_rand_' + fast_key + '_' + slow_key + '_trig'
                                            diff_rand_key = 'Coinc_rand_' + fast_key + '_' + slow_key + '_diff'

                                            # check if current event is being retained
                                            if len(data['Event']) - 1 not in retain_index:

                                                # If  prevoius event is retained first process this
                                                if len(retain_index) > 0:

                                                    # Process previous event
                                                    for r_ind in range(len(retain_index)):

                                                        index = retain_index[r_ind - retain_nr]
                                                        del retain_index[r_ind - retain_nr]
                                                        retain_nr += 1

                                                        if data['WavE_AMO (eV)'][index] == data['WavE_AMO (eV)'][
                                                            -1] and \
                                                                data['shutter_status'][index][0] == \
                                                                data['shutter_status'][-1][0] and \
                                                                (data['ADCV.Ion_flag'][index][0] > 100) == (
                                                                data['ADCV.Ion_flag'][-1][0] > 100):

                                                            if trig_rand_key in data.keys():

                                                                # compare current fast_trig to previous slow_trig
                                                                mem = sys.getsizeof(
                                                                    data[trig_rand_key]) + sys.getsizeof(
                                                                    data[diff_rand_key])

                                                                # Create mesgrid to compare
                                                                fast_v, slow_v = np.meshgrid(data[fast_key][index],
                                                                                            data[slow_key][-1])
                                                                diff_mat = slow_v - fast_v  # time between each event

                                                                # Comparision: slow comes after the fast signal and is withing a time window of the fast signal
                                                                diff_mask = np.logical_and(np.sign(diff_mat) == 1,
                                                                                        diff_mat < time_window /
                                                                                        data['TDC.res'])

                                                                # Append to output
                                                                data[trig_rand_key][index] = fast_v[
                                                                    diff_mask].flatten()
                                                                data[diff_rand_key][index] = diff_mat[
                                                                    diff_mask].flatten()

                                                                data_mem += sys.getsizeof(
                                                                    data[trig_rand_key]) + sys.getsizeof(
                                                                    data[diff_rand_key]) - mem + sys.getsizeof(
                                                                    data[trig_rand_key][-1]) + sys.getsizeof(
                                                                    data[diff_rand_key][-1])

                                                            else:
                                                                # compare current fast_trig to previous slow_trig
                                                                # Create mesgrid to compare
                                                                fast_v, slow_v = np.meshgrid(data[fast_key][index],
                                                                                            data[slow_key][-1])
                                                                diff_mat = slow_v - fast_v  # time between each event

                                                                # Comparision: slow comes after the fast signal and is withing a time window of the fast signal
                                                                diff_mask = np.logical_and(np.sign(diff_mat) == 1,
                                                                                        diff_mat < time_window /
                                                                                        data['TDC.res'])

                                                                # Append to output
                                                                data[trig_rand_key] = [fast_v[diff_mask].flatten()]
                                                                data[diff_rand_key] = [
                                                                    diff_mat[diff_mask].flatten()]

                                                                data_mem += sys.getsizeof(
                                                                    data[trig_rand_key]) + sys.getsizeof(
                                                                    data[diff_rand_key]) - mem + sys.getsizeof(
                                                                    data[trig_rand_key][-1]) + sys.getsizeof(
                                                                    data[diff_rand_key][-1])

                                                        else:
                                                            retain_index.append(index)

                                                    retain_nr = 0

                                                # write to data struct
                                                # Check if the flag is already in the data structure
                                                if trig_key in data.keys():

                                                    mem = sys.getsizeof(data[trig_key]) + sys.getsizeof(
                                                        data[diff_key])

                                                    # Create mesgrid to compare
                                                    fast_v, slow_v = np.meshgrid(data[fast_key][-1],
                                                                                data[slow_key][-1])
                                                    diff_mat = slow_v - fast_v  # time between each event

                                                    # Comparision: slow comes after the fast signal and is withing a time window of the fast signal
                                                    diff_mask = np.logical_and(np.sign(diff_mat) == 1,
                                                                            diff_mat < time_window / data[
                                                                                'TDC.res'])

                                                    # Append to output
                                                    data[trig_key].append(fast_v[diff_mask].flatten())
                                                    data[diff_key].append(diff_mat[diff_mask].flatten())

                                                    data_mem += sys.getsizeof(data[trig_key]) + sys.getsizeof(
                                                        data[diff_key]) - mem + sys.getsizeof(
                                                        data[trig_key][-1]) + sys.getsizeof(data[diff_key][-1])

                                                    # Process random events

                                                    # first check if it is the first event
                                                    if len(data['Event']) > 1:
                                                        if data['WavE_AMO (eV)'][-2] == data['WavE_AMO (eV)'][-1] and \
                                                        data['shutter_status'][-2][0] == data['shutter_status'][-1][0] and \
                                                        (data['ADCV.Ion_flag'][-2][0] > 100) == (data['ADC.Ion_Flag'][-1][0] > 1000):

                                                            if trig_rand_key in data.keys():
                                                                # compare current fast_trig to previous slow_trig
                                                                mem = sys.getsizeof(
                                                                    data[trig_rand_key]) + sys.getsizeof(
                                                                    data[diff_rand_key])

                                                                # Create mesgrid to compare
                                                                fast_v, slow_v = np.meshgrid(data[fast_key][-1],
                                                                                            data[slow_key][-2])
                                                                diff_mat = slow_v - fast_v  # time between each event

                                                                # Comparision: slow comes after the fast signal and is withing a time window of the fast signal
                                                                diff_mask = np.logical_and(np.sign(diff_mat) == 1,
                                                                                        diff_mat < time_window /
                                                                                        data['TDC.res'])

                                                                # Append to output
                                                                data[trig_rand_key].append(
                                                                    fast_v[diff_mask].flatten())
                                                                data[diff_rand_key].append(
                                                                    diff_mat[diff_mask].flatten())

                                                                data_mem += sys.getsizeof(
                                                                    data[trig_rand_key]) + sys.getsizeof(
                                                                    data[diff_rand_key]) - mem + sys.getsizeof(
                                                                    data[trig_rand_key][-1]) + sys.getsizeof(
                                                                    data[diff_rand_key][-1])

                                                            else:
                                                                # compare current fast_trig to previous slow_trig
                                                                # Create mesgrid to compare
                                                                fast_v, slow_v = np.meshgrid(data[fast_key][-1],
                                                                                            data[slow_key][-2])
                                                                diff_mat = slow_v - fast_v  # time between each event

                                                                # Comparision: slow comes after the fast signal and is withing a time window of the fast signal
                                                                diff_mask = np.logical_and(np.sign(diff_mat) == 1,
                                                                                        diff_mat < time_window /
                                                                                        data['TDC.res'])

                                                                # Append to output
                                                                data[trig_rand_key] = [fast_v[diff_mask].flatten()]
                                                                data[diff_rand_key] = [
                                                                    diff_mat[diff_mask].flatten()]

                                                                data_mem += sys.getsizeof(
                                                                    data[trig_rand_key]) + sys.getsizeof(
                                                                    data[diff_rand_key]) - mem + sys.getsizeof(
                                                                    data[trig_rand_key][-1]) + sys.getsizeof(
                                                                    data[diff_rand_key][-1])

                                                        else:
                                                            if trig_rand_key in data.keys():
                                                                data[trig_rand_key].append(np.array([0]))
                                                                data[diff_rand_key].append(np.array([0]))
                                                                retain_index.append(len(data['Event']) - 1)
                                                            else:
                                                                # Append to output
                                                                data[trig_rand_key] = [np.array([0])]
                                                                data[diff_rand_key] = [np.array([0])]
                                                                retain_index.append(len(data['Event']) - 1)
                                                    else:
                                                        if trig_rand_key in data.keys():
                                                            data[trig_rand_key].append(np.array([0]))
                                                            data[diff_rand_key].append(np.array([0]))
                                                            retain_index.append(len(data['Event']) - 1)
                                                        else:
                                                            # Append to output
                                                            data[trig_rand_key] = [np.array([0])]
                                                            data[diff_rand_key] = [np.array([0])]
                                                            retain_index.append(len(data['Event']) - 1)

                                                else:

                                                    # Create mesgrid to compare
                                                    fast_v, slow_v = np.meshgrid(data[fast_key][-1],
                                                                                data[slow_key][-1])
                                                    diff_mat = slow_v - fast_v  # time between each event

                                                    # Comparision: slow comes after the fast signal and is withing a time window of the fast signal
                                                    diff_mask = np.logical_and(np.sign(diff_mat) == 1,
                                                                            diff_mat < time_window / data[
                                                                                'TDC.res'])

                                                    # Append to output
                                                    data[trig_key] = [fast_v[diff_mask].flatten()]
                                                    data[diff_key] = [diff_mat[diff_mask].flatten()]

                                                    data_mem += sys.getsizeof(data[trig_key]) + sys.getsizeof(
                                                        data[diff_key]) + sys.getsizeof(
                                                        data[trig_key][-1]) + sys.getsizeof(data[diff_key][-1])

                                                    # Process random events on next event.
                                                    if trig_rand_key in data.keys():
                                                        data[trig_rand_key].append(np.array([0]))
                                                        data[diff_rand_key].append(np.array([0]))
                                                        retain_index.append(len(data['Event']) - 1)
                                                    else:
                                                        # Append to output
                                                        data[trig_rand_key] = [np.array([0])]
                                                        data[diff_rand_key] = [np.array([0])]
                                                        retain_index.append(len(data['Event']) - 1)

                                            # We still need the analysis
                                            else:
                                                # write to data struct
                                                # Check if the flag is already in the data structure
                                                if trig_key in data.keys():

                                                    mem = sys.getsizeof(data[trig_key]) + sys.getsizeof(
                                                        data[diff_key])

                                                    # Create mesgrid to compare
                                                    fast_v, slow_v = np.meshgrid(data[fast_key][-1],
                                                                                data[slow_key][-1])
                                                    diff_mat = slow_v - fast_v  # time between each event

                                                    # Comparision: slow comes after the fast signal and is withing a time window of the fast signal
                                                    diff_mask = np.logical_and(np.sign(diff_mat) == 1,
                                                                            diff_mat < time_window / data[
                                                                                'TDC.res'])

                                                    # Append to output
                                                    data[trig_key].append(fast_v[diff_mask].flatten())
                                                    data[diff_key].append(diff_mat[diff_mask].flatten())

                                                    data_mem += sys.getsizeof(data[trig_key]) + sys.getsizeof(
                                                        data[diff_key]) - mem + sys.getsizeof(
                                                        data[trig_key][-1]) + sys.getsizeof(data[diff_key][-1])

                                                    # Process random events

                                                    # Process random events on next event.
                                                    if trig_rand_key in data.keys():
                                                        data[trig_rand_key].append(np.array([0]))
                                                        data[diff_rand_key].append(np.array([0]))
                                                    else:
                                                        # Append to output
                                                        data[trig_rand_key] = [np.array([0])]
                                                        data[diff_rand_key] = [np.array([0])]

                                                else:

                                                    # Create mesgrid to compare
                                                    fast_v, slow_v = np.meshgrid(data[fast_key][-1],
                                                                                data[slow_key][-1])
                                                    diff_mat = slow_v - fast_v  # time between each event

                                                    # Comparision: slow comes after the fast signal and is withing a time window of the fast signal
                                                    diff_mask = np.logical_and(np.sign(diff_mat) == 1,
                                                                            diff_mat < time_window / data[
                                                                                'TDC.res'])

                                                    # Append to output
                                                    data[trig_key] = [fast_v[diff_mask].flatten()]
                                                    data[diff_key] = [diff_mat[diff_mask].flatten()]

                                                    data_mem += sys.getsizeof(data[trig_key]) + sys.getsizeof(
                                                        data[diff_key]) + sys.getsizeof(
                                                        data[trig_key][-1]) + sys.getsizeof(data[diff_key][-1])

                                                    # Process random events on next event.
                                                    if trig_rand_key in data.keys():
                                                        data[trig_rand_key].append(np.array([0]))
                                                        data[diff_rand_key].append(np.array([0]))
                                                    else:
                                                        # Append to output
                                                        data[trig_rand_key] = [np.array([0])]
                                                        data[diff_rand_key] = [np.array([0])]

                            except:
                                # Check for errors
                                if sum(data['errors'][-1]) != 0 or len(data['TDC1.Trigger'][-1]) != nr_triggers or sum(data['proc_time'][-1]) > proc_time:
                                    # Detele event in case
                                    for key in data.keys():
                                        # Check if we are dealing with the header
                                        if not isinstance(data[key],(list,tuple,np.ndarray)):
                                            pass
                                        elif len(data[key]) < len(data['Event']):
                                            pass
                                        elif 'Coinc_' in key:
                                            pass
                                        # Check if it is the ringing keys
                                        elif 'ringing' in key:
                                            pass
                                        # Else continue
                                        else:
                                            del data[key][-1]
                                        
                                else:
                                                
                                    # Remove ringings if requested
                                    if ringing_keys[0] != None:
                                        current_event = [np.array(data[key][-1]) for key in ringing_keys]
                                        if ringing_hist:
                                            current_hist_event = [np.array(data[key][-1]) for key in ringing_keys]

                                        for key in range(len(ringing_keys)):
                                            mem = sys.getsizeof(data[ringing_keys[key]][-1])
                                                    
                                            ring_mask = np.diff(current_event[key]) < (ringing_time[key] / data['TDC.res'])
                                            
                                            if ringing_hist:
                                                ring_hist_mask = np.diff(current_hist_event[key]) < (ringing_hist_time / data['TDC.res'])
                                                    
                                                # Get the trigger times for histogram of ringings
                                                while(np.any(ring_hist_mask)):
                                                    current_hist_event[key] = current_hist_event[key][np.invert(np.insert(ring_hist_mask,0,False))]
                                                    ring_hist_mask = np.diff(current_hist_event[key]) < (ringing_hist_time / data['TDC.res'])
                                                    
                                                # Fill ringing histogram
                                                hist_spikes, hist_times = np.meshgrid(current_hist_event[key],current_event[key])
                                                        
                                                hist_diff = hist_times - hist_spikes
                                                        
                                                # Comparision: slow comes after the fast signal and is withing a time window of the fast signal
                                                ring_hist_mask = np.logical_and(np.sign(hist_diff) == 1, hist_diff < ringing_hist_time / data['TDC.res'])
                                                        
                                                data[ringing_keys[key]+'_ringing_hist'] = data[ringing_keys[key]+'_ringing_hist'] + np.histogram(hist_diff[ring_hist_mask].flatten(), data['ringing_edges'])[0]
                                                    
                                            # Remove ringings from current event
                                            while(np.any(ring_mask)):
                                                current_event[key] = current_event[key][np.invert(np.insert(ring_mask,0,False))]
                                                ring_mask = np.diff(current_event[key]) < (ringing_time[key] / data['TDC.res'])
                                                        
                                            data[ringing_keys[key]][-1] = current_event[key].tolist()
                                                            
                                            data_mem += sys.getsizeof(data[ringing_keys[key]][-1]) - mem
                                        
                                    # Make coincidence analysis of given keys.
                                    if coinc_keys[0] != [None,None]:
                                        for fast_key, slow_key in coinc_keys:

                                            # Keys to consider
                                            trig_key = 'Coinc_' + fast_key + '_' + slow_key + '_trig'
                                            diff_key = 'Coinc_' + fast_key + '_' + slow_key + '_diff'
                                            trig_rand_key = 'Coinc_rand_' + fast_key + '_' + slow_key + '_trig'
                                            diff_rand_key = 'Coinc_rand_' + fast_key + '_' + slow_key + '_diff'

                                            # check if current event is being retained
                                            if len(data['Event']) - 1 not in retain_index:

                                                # If  prevoius event is retained first process this
                                                if len(retain_index) > 0:

                                                    # Process previous event
                                                    for r_ind in range(len(retain_index)):

                                                        index = retain_index[r_ind - retain_nr]
                                                        del retain_index[r_ind - retain_nr]
                                                        retain_nr += 1

                                                        if data['WavE_AMO (eV)_ctr'][index] == data['WavE_AMO (eV)_ctr'][
                                                            -1] and \
                                                                data['shutter control_ctr'][index][0] == \
                                                                data['shutter control_ctr'][-1][0]:

                                                            if trig_rand_key in data.keys():

                                                                # compare current fast_trig to previous slow_trig
                                                                mem = sys.getsizeof(
                                                                    data[trig_rand_key]) + sys.getsizeof(
                                                                    data[diff_rand_key])

                                                                # Create mesgrid to compare
                                                                fast_v, slow_v = np.meshgrid(data[fast_key][index],
                                                                                            data[slow_key][-1])
                                                                diff_mat = slow_v - fast_v  # time between each event

                                                                # Comparision: slow comes after the fast signal and is withing a time window of the fast signal
                                                                diff_mask = np.logical_and(np.sign(diff_mat) == 1,
                                                                                        diff_mat < time_window /
                                                                                        data['TDC.res'])

                                                                # Append to output
                                                                data[trig_rand_key][index] = fast_v[
                                                                    diff_mask].flatten()
                                                                data[diff_rand_key][index] = diff_mat[
                                                                    diff_mask].flatten()

                                                                data_mem += sys.getsizeof(
                                                                    data[trig_rand_key]) + sys.getsizeof(
                                                                    data[diff_rand_key]) - mem + sys.getsizeof(
                                                                    data[trig_rand_key][-1]) + sys.getsizeof(
                                                                    data[diff_rand_key][-1])

                                                            else:
                                                                # compare current fast_trig to previous slow_trig
                                                                # Create mesgrid to compare
                                                                fast_v, slow_v = np.meshgrid(data[fast_key][index],
                                                                                            data[slow_key][-1])
                                                                diff_mat = slow_v - fast_v  # time between each event

                                                                # Comparision: slow comes after the fast signal and is withing a time window of the fast signal
                                                                diff_mask = np.logical_and(np.sign(diff_mat) == 1,
                                                                                        diff_mat < time_window /
                                                                                        data['TDC.res'])

                                                                # Append to output
                                                                data[trig_rand_key] = [fast_v[diff_mask].flatten()]
                                                                data[diff_rand_key] = [
                                                                    diff_mat[diff_mask].flatten()]

                                                                data_mem += sys.getsizeof(
                                                                    data[trig_rand_key]) + sys.getsizeof(
                                                                    data[diff_rand_key]) - mem + sys.getsizeof(
                                                                    data[trig_rand_key][-1]) + sys.getsizeof(
                                                                    data[diff_rand_key][-1])

                                                        else:
                                                            retain_index.append(index)

                                                    retain_nr = 0

                                                # write to data struct
                                                # Check if the flag is already in the data structure
                                                if trig_key in data.keys():

                                                    mem = sys.getsizeof(data[trig_key]) + sys.getsizeof(
                                                        data[diff_key])

                                                    # Create mesgrid to compare
                                                    fast_v, slow_v = np.meshgrid(data[fast_key][-1],
                                                                                data[slow_key][-1])
                                                    diff_mat = slow_v - fast_v  # time between each event

                                                    # Comparision: slow comes after the fast signal and is withing a time window of the fast signal
                                                    diff_mask = np.logical_and(np.sign(diff_mat) == 1,
                                                                            diff_mat < time_window / data[
                                                                                'TDC.res'])

                                                    # Append to output
                                                    data[trig_key].append(fast_v[diff_mask].flatten())
                                                    data[diff_key].append(diff_mat[diff_mask].flatten())

                                                    data_mem += sys.getsizeof(data[trig_key]) + sys.getsizeof(
                                                        data[diff_key]) - mem + sys.getsizeof(
                                                        data[trig_key][-1]) + sys.getsizeof(data[diff_key][-1])

                                                    # Process random events

                                                    # first check if it is the first event
                                                    if len(data['Event']) > 1:
                                                        if data['WavE_AMO (eV)_ctr'][-2] == data['WavE_AMO (eV)_ctr'][-1] and \
                                                        data['shutter control_ctr'][-2][0] == data['shutter control_ctr'][-1][0]:

                                                            if trig_rand_key in data.keys():
                                                                # compare current fast_trig to previous slow_trig
                                                                mem = sys.getsizeof(
                                                                    data[trig_rand_key]) + sys.getsizeof(
                                                                    data[diff_rand_key])

                                                                # Create mesgrid to compare
                                                                fast_v, slow_v = np.meshgrid(data[fast_key][-1],
                                                                                            data[slow_key][-2])
                                                                diff_mat = slow_v - fast_v  # time between each event

                                                                # Comparision: slow comes after the fast signal and is withing a time window of the fast signal
                                                                diff_mask = np.logical_and(np.sign(diff_mat) == 1,
                                                                                        diff_mat < time_window /
                                                                                        data['TDC.res'])

                                                                # Append to output
                                                                data[trig_rand_key].append(
                                                                    fast_v[diff_mask].flatten())
                                                                data[diff_rand_key].append(
                                                                    diff_mat[diff_mask].flatten())

                                                                data_mem += sys.getsizeof(
                                                                    data[trig_rand_key]) + sys.getsizeof(
                                                                    data[diff_rand_key]) - mem + sys.getsizeof(
                                                                    data[trig_rand_key][-1]) + sys.getsizeof(
                                                                    data[diff_rand_key][-1])

                                                            else:
                                                                # compare current fast_trig to previous slow_trig
                                                                # Create mesgrid to compare
                                                                fast_v, slow_v = np.meshgrid(data[fast_key][-1],
                                                                                            data[slow_key][-2])
                                                                diff_mat = slow_v - fast_v  # time between each event

                                                                # Comparision: slow comes after the fast signal and is withing a time window of the fast signal
                                                                diff_mask = np.logical_and(np.sign(diff_mat) == 1,
                                                                                        diff_mat < time_window /
                                                                                        data['TDC.res'])

                                                                # Append to output
                                                                data[trig_rand_key] = [fast_v[diff_mask].flatten()]
                                                                data[diff_rand_key] = [
                                                                    diff_mat[diff_mask].flatten()]

                                                                data_mem += sys.getsizeof(
                                                                    data[trig_rand_key]) + sys.getsizeof(
                                                                    data[diff_rand_key]) - mem + sys.getsizeof(
                                                                    data[trig_rand_key][-1]) + sys.getsizeof(
                                                                    data[diff_rand_key][-1])

                                                        else:
                                                            if trig_rand_key in data.keys():
                                                                data[trig_rand_key].append(np.array([0]))
                                                                data[diff_rand_key].append(np.array([0]))
                                                                retain_index.append(len(data['Event']) - 1)
                                                            else:
                                                                # Append to output
                                                                data[trig_rand_key] = [np.array([0])]
                                                                data[diff_rand_key] = [np.array([0])]
                                                                retain_index.append(len(data['Event']) - 1)
                                                    else:
                                                        if trig_rand_key in data.keys():
                                                            data[trig_rand_key].append(np.array([0]))
                                                            data[diff_rand_key].append(np.array([0]))
                                                            retain_index.append(len(data['Event']) - 1)
                                                        else:
                                                            # Append to output
                                                            data[trig_rand_key] = [np.array([0])]
                                                            data[diff_rand_key] = [np.array([0])]
                                                            retain_index.append(len(data['Event']) - 1)

                                                else:

                                                    # Create mesgrid to compare
                                                    fast_v, slow_v = np.meshgrid(data[fast_key][-1],
                                                                                data[slow_key][-1])
                                                    diff_mat = slow_v - fast_v  # time between each event

                                                    # Comparision: slow comes after the fast signal and is withing a time window of the fast signal
                                                    diff_mask = np.logical_and(np.sign(diff_mat) == 1,
                                                                            diff_mat < time_window / data[
                                                                                'TDC.res'])

                                                    # Append to output
                                                    data[trig_key] = [fast_v[diff_mask].flatten()]
                                                    data[diff_key] = [diff_mat[diff_mask].flatten()]

                                                    data_mem += sys.getsizeof(data[trig_key]) + sys.getsizeof(
                                                        data[diff_key]) + sys.getsizeof(
                                                        data[trig_key][-1]) + sys.getsizeof(data[diff_key][-1])

                                                    # Process random events on next event.
                                                    if trig_rand_key in data.keys():
                                                        data[trig_rand_key].append(np.array([0]))
                                                        data[diff_rand_key].append(np.array([0]))
                                                        retain_index.append(len(data['Event']) - 1)
                                                    else:
                                                        # Append to output
                                                        data[trig_rand_key] = [np.array([0])]
                                                        data[diff_rand_key] = [np.array([0])]
                                                        retain_index.append(len(data['Event']) - 1)

                                            # We still need the analysis
                                            else:
                                                # write to data struct
                                                # Check if the flag is already in the data structure
                                                if trig_key in data.keys():

                                                    mem = sys.getsizeof(data[trig_key]) + sys.getsizeof(
                                                        data[diff_key])

                                                    # Create mesgrid to compare
                                                    fast_v, slow_v = np.meshgrid(data[fast_key][-1],
                                                                                data[slow_key][-1])
                                                    diff_mat = slow_v - fast_v  # time between each event

                                                    # Comparision: slow comes after the fast signal and is withing a time window of the fast signal
                                                    diff_mask = np.logical_and(np.sign(diff_mat) == 1,
                                                                            diff_mat < time_window / data[
                                                                                'TDC.res'])

                                                    # Append to output
                                                    data[trig_key].append(fast_v[diff_mask].flatten())
                                                    data[diff_key].append(diff_mat[diff_mask].flatten())

                                                    data_mem += sys.getsizeof(data[trig_key]) + sys.getsizeof(
                                                        data[diff_key]) - mem + sys.getsizeof(
                                                        data[trig_key][-1]) + sys.getsizeof(data[diff_key][-1])

                                                    # Process random events

                                                    # Process random events on next event.
                                                    if trig_rand_key in data.keys():
                                                        data[trig_rand_key].append(np.array([0]))
                                                        data[diff_rand_key].append(np.array([0]))
                                                    else:
                                                        # Append to output
                                                        data[trig_rand_key] = [np.array([0])]
                                                        data[diff_rand_key] = [np.array([0])]

                                                else:

                                                    # Create mesgrid to compare
                                                    fast_v, slow_v = np.meshgrid(data[fast_key][-1],
                                                                                data[slow_key][-1])
                                                    diff_mat = slow_v - fast_v  # time between each event

                                                    # Comparision: slow comes after the fast signal and is withing a time window of the fast signal
                                                    diff_mask = np.logical_and(np.sign(diff_mat) == 1,
                                                                            diff_mat < time_window / data[
                                                                                'TDC.res'])

                                                    # Append to output
                                                    data[trig_key] = [fast_v[diff_mask].flatten()]
                                                    data[diff_key] = [diff_mat[diff_mask].flatten()]

                                                    data_mem += sys.getsizeof(data[trig_key]) + sys.getsizeof(
                                                        data[diff_key]) + sys.getsizeof(
                                                        data[trig_key][-1]) + sys.getsizeof(data[diff_key][-1])

                                                    # Process random events on next event.
                                                    if trig_rand_key in data.keys():
                                                        data[trig_rand_key].append(np.array([0]))
                                                        data[diff_rand_key].append(np.array([0]))
                                                    else:
                                                        # Append to output
                                                        data[trig_rand_key] = [np.array([0])]
                                                        data[diff_rand_key] = [np.array([0])]

            # Resetting
            mode = 0
            header = 1
            
            # Checking if memory is exceeded
            if data_mem > memory_limit:
            
                # Delete retained events not processed
                if len(retain_index) > 0:
                    retain_nr = 0
                    for index in retain_index:
                        # Detele event in case
                        for key in data.keys():
                            # Check if we are dealing with the header
                            if not isinstance(data[key],(list,tuple,np.ndarray)):
                                pass
                            elif len(data[key]) < len(data['Event']):
                               pass
                            # Check if it is the ringing keys
                            elif 'ringing' in key:
                                pass
                            # Else continue
                            else:
                                del data[key][index-retain_nr]
                        retain_nr += 1
                retain_index = []
                retain_nr = 0
                
                
                # Write to file
                f = open(write_folder+f'-dat-{dat_file:03}.txt', 'w')
                f.write(json.dumps(data, cls=NumpyEncoder))
                f.close()
                
                dat_file += 1
                
                # Resetting
                data = {}
                data_mem = 0
                
                if ringing_keys[0] != None:
                    # Make a key to show wich ringings have been removed
                    data['ringing_keys'] = ringing_keys
            
                    if ringing_hist:
                        # Make a ringing histogram
                        ringing_channels = 42000
                        ringing_nr_bins = 2000
                        data['ringing_edges'] = np.arange(0, ringing_channels+1/ringing_nr_bins, ringing_channels/ringing_nr_bins)
            
                        for key in ringing_keys:
                            data[key+'_ringing_hist'] = np.zeros(ringing_nr_bins)
                
            time_avg = (time_int*time_avg + time.time()-t0) / (time_int+1)
            time_int += 1   
            if not silent:
                print(f'Loading {filename[:7]} eta. {(len(run_lst)-time_int)*time_avg/60:.2f} min.')


        # Delete retained events not processed
        if len(retain_index) > 0:
            retain_nr = 0
            for index in retain_index:
                # Detele event in case
                for key in data.keys():
                    # Check if we are dealing with the header
                    if not isinstance(data[key],(list,tuple,np.ndarray)):
                        pass
                    elif len(data[key]) < len(data['Event']):
                       pass
                    # Check if it is the ringing keys
                    elif 'ringing' in key:
                        pass
                    # Else continue
                    else:
                        del data[key][index-retain_nr]
                retain_nr += 1
        retain_index = []
        retain_nr = 0
        
        # Write to file
        f = open(write_folder+f'-dat-{dat_file:03}.txt', 'w')
        f.write(json.dumps(data, cls=NumpyEncoder))
        f.close()

        if any(key != None for key in keys):
            data = { key: data[key]  for key in data if key in keys}
        print('----------------------------------')

def load_dat_file(filename, do_return=True, keys=[None], ringing_keys=[None], coinc_keys=[[None,None]], time_window=30000, silent=False, overwrite=False, write_folder=None, run_folder=None):
    print('-----------Load Run '+filename[-15:-11]+filename[-7:-4]+'-----------')
    # Check if load already exists
    if os.path.exists(filename) and not overwrite:
        # Read
        f = open(filename, 'r')
        data = json.loads(f.read())
        f.close()
        
        # Only give back requested keys
        if any(key != None for key in keys):
            data = { key: data[key]  for key in data if key in keys}
            
        print('JSON file found and read')
        print('----------------------------------')
        if do_return:
            return data
    elif run_folder != None:
        print('File Run '+filename[-12:-4]+'doesn\'t exist')
        load_data(run_folder=run_folder, keys=keys, ringing_keys=ringing_keys, coinc_keys=coinc_keys, time_window=time_window, silent=silent, overwrite=overwrite, write_folder=write_folder)
        print('-----------Load Run '+filename[-12:-4]+'-----------')
        # Read
        f = open(filename, 'r')
        data = json.loads(f.read())
        f.close()
        
        # Only give back requested keys
        if any(key != None for key in keys):
            data = { key: data[key]  for key in data if key in keys}
            
        print('JSON file found and read')
        print('----------------------------------')
        if do_return:
            return data
    else:
        print('JSON file not found')
        print('----------------------------------')
