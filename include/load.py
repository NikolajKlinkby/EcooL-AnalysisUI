import numpy as np
import json
import os, sys
import time

class NumpyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        if isinstance(obj, np.floating):
            return float(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return json.JSONEncoder.default(self, obj)

def flatten_list(listr):
    try:
        return np.array([item for sublist in listr for item in sublist])
    except:
        return np.array([item for item in listr])

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
    
overwrite
    overwrites current JSON file

memory_limit
    Limit of dictionary in
    memory before it is written
    to a file. Given in bytes.
    
    *The program uses more
    memory than this limit
    to load files, write files,
    and do analysis.
    
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
def load_data(run_folder, keys=[None], silent=False, overwrite=False, memory_limit=0.75E+9, proc_time=1E+12):
    
    write_folder = run_folder+'/JSON/'+run_folder[-7:]
    if not os.path.exists(run_folder+'/JSON'):
        os.makedirs(run_folder+'/JSON')
    
    print(time.strftime('%H:%M:%S', time.gmtime())+' Load Run '+run_folder[-3:])
    
    # Check if load already exists
    if os.path.exists(write_folder+'-dat-001.txt') and not overwrite:
        print(time.strftime('%H:%M:%S', time.gmtime())+' JSON file already exists')

        # Check for parameters to check if one should update
        if os.path.exists(run_folder+'/PythonAnalysis/params.txt'):
            # Files that should be loaded
            files_to_load = []
            for filename in sorted(os.listdir(run_folder)):
                if run_folder[-7:] == filename[:7] and filename[-4:] == '.dat':
                    files_to_load.append(int(filename.split('-')[-1][:-4]))
            
            f = open(run_folder+'/PythonAnalysis/params.txt', 'r')
            files = json.loads(f.read())
            if 'File' in files.keys():
                files = files['File']
                f.close()

                files_loaded = []
                for file in np.unique(files):
                    for f in range(len(files_to_load)):
                        if file == files_to_load[f]:
                            files_loaded.append(f)
                for f in np.sort(files_loaded)[::-1]:
                    files_to_load.pop(f)
                
                if len(files_to_load) > 0:
                    return update_dat_file(run_folder, files_to_load, silent=silent, memory_limit=memory_limit, proc_time=proc_time)
                else:
                    return False, 1, 1
            else:
                f.close()
                print(time.strftime('%H:%M:%S', time.gmtime())+' Flag File not in file')
                print(time.strftime('%H:%M:%S', time.gmtime())+' To update please force')
                return False, 1, 1

        else:
            return False, 1, 1
    else:
        # Dictionary to store all the data
        data = {}
        mode = 0 # Either reading an event or not
        header = 1 # Reading header
        
        # Memory tracking
        data_mem = 0
        dat_file = 1
        
        # Time tracking
        time_avg = 0.
        time_int = 0         

        # Go though all files in run_folder
        run_lst = os.listdir(run_folder)
        for filename in sorted(run_lst):
            t0 = time.time()
            # Making sure that the file in the folder has the correct naming scheme (is part of the run)
            if run_folder[-7:] == filename[:7] and filename[-4:] == '.dat':

                if not silent:
                    print(time.strftime('%H:%M:%S', time.gmtime())+f' Loading {filename[:7]} file {int(filename.split("-")[-1][:-4]):03}')
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
                                    if sum(data['errors'][-1]) != 0 or sum(data['proc_time'][-1]) > proc_time: 
                                        # Detele event in case
                                        for key in data.keys():
                                            # Check if we are dealing with the header
                                            if not isinstance(data[key],(list,tuple,np.ndarray)):
                                                pass
                                            elif len(data[key]) < len(data['Event']):
                                                pass
                                            else:
                                                del data[key][-1]
                                                    
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
                            # Check for errors
                            if sum(data['errors'][-1]) != 0 or sum(data['proc_time'][-1]) > proc_time:
                                # Detele event in case
                                for key in data.keys():
                                    # Check if we are dealing with the header
                                    if not isinstance(data[key],(list,tuple,np.ndarray)):
                                        pass
                                    elif len(data[key]) < len(data['Event']):
                                        pass
                                    # Else continue
                                    else:
                                        del data[key][-1]
                                    
            # Resetting
            mode = 0
            header = 1
            
            # Checking if memory is exceeded
            if data_mem > memory_limit:
                
                # Rename old file format
                if 'Wavelength_crt' in data.keys():
                    data['Wavelength_ctr'] = data.pop('Wavelength_crt')
                if 'EKSPLA.Wavelength' in data.keys():
                    data['Wavelength_ctr'] = data.pop('EKSPLA.Wavelength')
                    data['Wavelength_mon'] = data['Wavelength_ctr']
                if 'GentecPulseEnergy(mJ)' in data.keys():
                    data['ADC.Laser_pw'] = data.pop('GentecPulseEnergy(mJ)')
                if 'LaserOn' in data.keys():
                    data['ADC.Laser_flag'] = [[i[0]*10000] for i in data.pop('LaserOn')]
                if 'ScanStep' in data.keys():
                    data['TCP_scan_step'] = data.pop('ScanStep')
                if 'ADC.bit' not in data.keys():
                    data['ADC.bit'] = 100000

                # Checking TCP type
                if 'Wavelength_ctr' in data.keys() and 'Wavelength_mon' in data.keys():
                    data['TCP_type'] = 'Wavelength_ctr'
                elif 'Delay (fs)_ctr' in data.keys() and 'Delay (fs)_mon' in data.keys():
                    data['TCP_type'] = 'Delay (fs)_ctr'
                elif 'Requested Transmission_ctr' in data.keys() and 'Requested Transmission_mon' in data.keys():
                    data['TCP_type'] = 'Requested Transmission_ctr'
                else:
                    data['TCP_type'] = 'TCP_scan_step'
                
                # Write to file
                f = open(write_folder+f'-dat-{dat_file:03}.txt', 'w')
                f.write(json.dumps(data, cls=NumpyEncoder))
                f.close()
                
                dat_file += 1
                
                # Resetting
                data = {}
                data_mem = 0
                
            time_avg = (time_int*time_avg + time.time()-t0) / (time_int+1)
            time_int += 1   
            if not silent:
                print(time.strftime('%H:%M:%S', time.gmtime())+f' Loading {filename[:7]} eta. {(len(run_lst)-time_int)*time_avg/60:.2f} min.')
        
        # Rename old file format
        if 'Wavelength_crt' in data.keys():
            data['Wavelength_ctr'] = data.pop('Wavelength_crt')
        if 'EKSPLA.Wavelength' in data.keys():
            data['Wavelength_ctr'] = data.pop('EKSPLA.Wavelength')
            data['Wavelength_mon'] = data['Wavelength_ctr']
        if 'GentecPulseEnergy(mJ)' in data.keys():
            data['ADC.Laser_pw'] = data.pop('GentecPulseEnergy(mJ)')
        if 'LaserOn' in data.keys():
            data['ADC.Laser_flag'] = [[i[0]*10000] for i in data.pop('LaserOn')]
        if 'ScanStep' in data.keys():
            data['TCP_scan_step'] = data.pop('ScanStep')
        if 'ADC.bit' not in data.keys():
            data['ADC.bit'] = 100000

        # Checking TCP type
        if 'Wavelength_ctr' in data.keys() and 'Wavelength_mon' in data.keys():
            data['TCP_type'] = 'Wavelength_ctr'
        elif 'Delay (fs)_ctr' in data.keys() and 'Delay (fs)_mon' in data.keys():
            data['TCP_type'] = 'Delay (fs)_ctr'
        elif 'Requested Transmission_ctr' in data.keys() and 'Requested Transmission_mon' in data.keys():
            data['TCP_type'] = 'Requested Transmission_ctr'
        else:
            data['TCP_type'] = 'TCP_scan_step'
        
        # Write to file
        f = open(write_folder+f'-dat-{dat_file:03}.txt', 'w')
        f.write(json.dumps(data, cls=NumpyEncoder))
        f.close()

        if any(key != None for key in keys):
            data = { key: data[key]  for key in data if key in keys}
        
        print(time.strftime('%H:%M:%S', time.gmtime())+' Data loaded')

        return True, 1, 1

def load_dat_file(filename, do_return=True, keys=[None], silent=False, overwrite=False, run_folder=None):
    print(time.strftime('%H:%M:%S', time.gmtime())+' Load Run '+filename[-15:-11]+filename[-7:-4])
    # Check if load already exists
    if os.path.exists(filename) and not overwrite:
        # Read
        f = open(filename, 'r')
        data = json.loads(f.read())
        f.close()
        
        # Only give back requested keys
        if any(key != None for key in keys):
            data = { key: data[key]  for key in data if key in keys}
            
        print(time.strftime('%H:%M:%S', time.gmtime())+' JSON file found and read')
        if do_return:
            return data
    elif run_folder != None:
        print(time.strftime('%H:%M:%S', time.gmtime())+' File Run '+filename[-12:-4]+'doesn\'t exist')
        load_data(run_folder=run_folder, keys=keys, silent=silent, overwrite=overwrite)
        print(time.strftime('%H:%M:%S', time.gmtime())+' Load Run '+filename[-12:-4])
        # Read
        f = open(filename, 'r')
        data = json.loads(f.read())
        f.close()
        
        # Only give back requested keys
        if any(key != None for key in keys):
            data = { key: data[key]  for key in data if key in keys}
            
        print(time.strftime('%H:%M:%S', time.gmtime())+' JSON file found and read')
        if do_return:
            return data
    else:
        print(time.strftime('%H:%M:%S', time.gmtime())+' JSON file not found')

def update_dat_file(run_folder, files_to_load, silent = False, memory_limit=0.75E+9, proc_time=300):
    
    write_folder = run_folder+'/JSON'
    dat_files_dir = sorted(os.listdir(write_folder))

    # Make a list of JSON files
    json_files = []
    for filename in dat_files_dir:
        if (run_folder[-7:] in filename) and ('-dat-' in filename):
            json_files.append(filename)
    
    dat_files = []
    
    # Check if any files are not loaded
    for filename in dat_files_dir[::-1]:
        if filename in json_files and len(files_to_load) > 0:
            # Load in the data from missing files
            if not silent:
                print(time.strftime('%H:%M:%S', time.gmtime())+' Update Run '+run_folder[-3:])

            data = load_dat_file(write_folder+'/'+filename)

            # Dictionary to store all the data
            mode = 0 # Either reading an event or not
            header = 1 # Reading header
            
            # Memory tracking
            data_mem = get_size(data)
            dat_file = int(filename[-7:-4])
            if data_mem > memory_limit:
                data = {}
                data_mem = 0
                dat_file += 1
            
            # Time tracking
            time_avg = 0.
            time_int = 0         

            # Go though all files in run_folder
            for file_number in files_to_load:
                t0 = time.time()

                if not silent:
                    print(time.strftime('%H:%M:%S', time.gmtime())+f' Loading {run_folder[-7:]} file {file_number:03}')
                file = os.path.join(run_folder, f'{run_folder[-7:]}-{file_number:03}.dat')

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
                                    if sum(data['errors'][-1]) != 0 or sum(data['proc_time'][-1]) > proc_time: 
                                        # Detele event in case
                                        for key in data.keys():
                                            # Check if we are dealing with the header
                                            if not isinstance(data[key],(list,tuple,np.ndarray)):
                                                pass
                                            elif len(data[key]) < len(data['Event']):
                                                pass
                                            else:
                                                del data[key][-1]
                                                    
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
                            # Check for errors
                            if sum(data['errors'][-1]) != 0 or sum(data['proc_time'][-1]) > proc_time:
                                # Detele event in case
                                for key in data.keys():
                                    # Check if we are dealing with the header
                                    if not isinstance(data[key],(list,tuple,np.ndarray)):
                                        pass
                                    elif len(data[key]) < len(data['Event']):
                                        pass
                                    # Else continue
                                    else:
                                        del data[key][-1]
                                    
                
                # Resetting
                mode = 0
                header = 1
                
                # Checking if memory is exceeded
                if data_mem > memory_limit:

                    # Rename old file format
                    if 'Wavelength_crt' in data.keys():
                        # Topoff
                        if 'Wavelength_ctr' in data.keys():
                            for i in data['Wavelength_crt']:
                                data['Wavelength_ctr'].append(i)
                            data.pop('Wavelength_crt')
                        else:
                            data['Wavelength_ctr'] = data.pop('Wavelength_crt')
                    if 'EKSPLA.Wavelength' in data.keys():
                        # Topoff
                        if 'Wavelength_ctr' in data.keys():
                            for i in data['EKSPLA.Wavelength']:
                                data['Wavelength_ctr'].append(i)
                            data.pop('EKSPLA.Wavelength')
                        else:
                            data['Wavelength_ctr'] = data.pop('EKSPLA.Wavelength')
                    if 'GentecPulseEnergy(mJ)' in data.keys():
                        # Topoff
                        if 'ADC.Laser_pw' in data.keys():
                            for i in data['GentecPulseEnergy(mJ)']:
                                data['ADC.Laser_pw'].append(i)
                            data.pop('GentecPulseEnergy(mJ)')
                        else:
                            data['ADC.Laser_pw'] = data.pop('GentecPulseEnergy(mJ)')
                    if 'LaserOn' in data.keys():
                        # Topoff
                        if 'ADC.Laser_flag' in data.keys():
                            for i in data['LaserOn']:
                                data['ADC.Laser_flag'].append(i*10000)
                            data.pop('LaserOn')
                        else:
                            data['ADC.Laser_flag'] = data.pop('LaserOn')*10000
                    if 'ScanStep' in data.keys():
                        # Topoff
                        if 'TCP_scan_step' in data.keys():
                            for i in data['ScanStep']:
                                data['TCP_scan_step'].append(i)
                            data.pop('ScanStep')
                        else:
                            data['TCP_scan_step'] = data.pop('ScanStep')
                    
                    # Checking TCP type
                    if 'Wavelength_ctr' in data.keys() and 'Wavelength_mon' in data.keys():
                        data['TCP_type'] = 'Wavelength_ctr'
                    elif 'Delay (fs)_ctr' in data.keys() and 'Delay (fs)_mon' in data.keys():
                        data['TCP_type'] = 'Delay (fs)_ctr'
                    elif 'Requested Transmission_ctr' in data.keys() and 'Requested Transmission_mon' in data.keys():
                        data['TCP_type'] = 'Requested Transmission_ctr'
                    else:
                        data['TCP_type'] = 'TCP_scan_step'
                    
                    # Write to file
                    f = open(write_folder+'/'+run_folder[-7:]+f'-dat-{dat_file:03}.txt', 'w')
                    f.write(json.dumps(data, cls=NumpyEncoder))
                    f.close()
                    dat_files.append(write_folder+'/'+run_folder[-7:]+f'-dat-{dat_file:03}.txt')
                    
                    dat_file += 1
                    
                    # Resetting
                    data = {}
                    data_mem = 0
                    
                time_avg = (time_int*time_avg + time.time()-t0) / (time_int+1)
                time_int += 1   
                if not silent:
                    print(time.strftime('%H:%M:%S', time.gmtime())+f' Loading {run_folder[-7:]} eta. {(len(files_to_load)-time_int)*time_avg/60:.2f} min.')
            
            # Rename old file format
            if 'Wavelength_crt' in data.keys():
                # Topoff
                if 'Wavelength_ctr' in data.keys():
                    for i in data['Wavelength_crt']:
                        data['Wavelength_ctr'].append(i)
                    data.pop('Wavelength_crt')
                else:
                    data['Wavelength_ctr'] = data.pop('Wavelength_crt')
            if 'EKSPLA.Wavelength' in data.keys():
                # Topoff
                if 'Wavelength_ctr' in data.keys():
                    for i in data['EKSPLA.Wavelength']:
                        data['Wavelength_ctr'].append(i)
                    data.pop('EKSPLA.Wavelength')
                else:
                    data['Wavelength_ctr'] = data.pop('EKSPLA.Wavelength')
            if 'GentecPulseEnergy(mJ)' in data.keys():
                # Topoff
                if 'ADC.Laser_pw' in data.keys():
                    for i in data['GentecPulseEnergy(mJ)']:
                        data['ADC.Laser_pw'].append(i)
                    data.pop('GentecPulseEnergy(mJ)')
                else:
                    data['ADC.Laser_pw'] = data.pop('GentecPulseEnergy(mJ)')
            if 'LaserOn' in data.keys():
                # Topoff
                if 'ADC.Laser_flag' in data.keys():
                    for i in data['LaserOn']:
                        data['ADC.Laser_flag'].append(i*10000)
                    data.pop('LaserOn')
                else:
                    data['ADC.Laser_flag'] = data.pop('LaserOn')*10000
            if 'ScanStep' in data.keys():
                # Topoff
                if 'TCP_scan_step' in data.keys():
                    for i in data['ScanStep']:
                        data['TCP_scan_step'].append(i)
                    data.pop('ScanStep')
                else:
                    data['TCP_scan_step'] = data.pop('ScanStep')
           
            # Checking TCP type
            if 'Wavelength_ctr' in data.keys() and 'Wavelength_mon' in data.keys():
                data['TCP_type'] = 'Wavelength_ctr'
            elif 'Delay (fs)_ctr' in data.keys() and 'Delay (fs)_mon' in data.keys():
                data['TCP_type'] = 'Delay (fs)_ctr'
            elif 'Requested Transmission_ctr' in data.keys() and 'Requested Transmission_mon' in data.keys():
                data['TCP_type'] = 'Requested Transmission_ctr'
            else:
                data['TCP_type'] = 'TCP_scan_step'
            
            # Write to file
            f = open(write_folder+'/'+run_folder[-7:]+f'-dat-{dat_file:03}.txt', 'w')
            f.write(json.dumps(data, cls=NumpyEncoder))
            f.close()
            dat_files.append(write_folder+'/'+run_folder[-7:]+f'-dat-{dat_file:03}.txt')

            print(time.strftime('%H:%M:%S', time.gmtime())+' Data updated')
            return True, files_to_load, dat_files

def old_load_histogram(runs, nr_bins=1000, write=None, overwrite=False, silent = False, scan_key = None, masks = [], threshold=1000, event_max=None):
    
    # Boolean keys
    loaded_hist_struct = False
    reading = False
    
    # Structures
    hist_struct = {}
    
    # Save masks
    hist_struct['masks'] = masks
    hist_struct['time_keys'] = []

    if write != None:
        if not silent:
            print(time.strftime('%H:%M:%S', time.gmtime())+' Load Histogram')
        try:    
            if os.path.exists(write) and not overwrite:
                # Load Histogram
                f = open(write, 'r')
                hist_struct = json.loads(f.read())
                f.close()
                loaded_hist_struct = True
                if not silent:
                    print(time.strftime('%H:%M:%S', time.gmtime())+' Histogram JSON files found and read')
                return hist_struct
        except:
            pass
    
    if not silent:
       print(time.strftime('%H:%M:%S', time.gmtime())+' Create Structs')
   
    TDC_res = 1

    # Time tracking
    time_avg = 0.
    time_int = 0
    
    # Loop over runs
    for run in runs:
        for filename in sorted(os.listdir(run[:run.rfind('/')])):
            if (run[run.rfind('/')+1:] in filename) and ('-dat-' in filename):
                
                # Load the needed keys
                data = load_dat_file(run[:run.rfind('/')+1]+filename, silent=silent)
                
                if event_max == None:
                    event_max = np.max(data['Event'])
                
                # Set default scan step
                if scan_key == None:
                    scan_key = data['TCP_type']
                hist_struct['scan_key'] = scan_key

                TDC_res = data['TDC.res']
                ADC_bit = data['ADC.bit']*50

                int_nr_bins = int(TDC_res*ADC_bit/nr_bins)

                # check the keys
                for key in data.keys():
                    # Dont add time to Parameters
                    if 'TDC1' in key and key not in hist_struct['time_keys']:
                        hist_struct['time_keys'].append(key)
                
                # Add to histogram struct if it does not exist 
                if not loaded_hist_struct:
                    
                    #edge of bins
                    hist_struct['edges'] = np.arange(0, ADC_bit*(1+1/int_nr_bins), ADC_bit/int_nr_bins)
                    
                    # Accumulated
                    if not reading:
                        for key in hist_struct['time_keys']:
                            if scan_key == 'Wavelength_ctr' or scan_key == 'Requested Transmission_ctr':
                                hist_struct[key+'_hist_0_acc'] = np.zeros(int_nr_bins)
                                hist_struct[key+'_hist_1_acc'] = np.zeros(int_nr_bins)
                            else:
                                hist_struct[key+'_hist_0_0_acc'] = np.zeros(int_nr_bins)
                                hist_struct[key+'_hist_0_1_acc'] = np.zeros(int_nr_bins)
                                hist_struct[key+'_hist_1_0_acc'] = np.zeros(int_nr_bins)
                                hist_struct[key+'_hist_1_1_acc'] = np.zeros(int_nr_bins)
                        reading = True

                    # Checking uniqe scan_steps values and adding them to struct
                    for scan_steps in np.unique(flatten_list(data[scan_key])):
                        
                        # Add to histogram struct if it does not exist
                        for key in hist_struct['time_keys']:

                            if scan_key == 'Wavelength_ctr' or scan_key == 'Requested Transmission_ctr':
                                if key+'_hist_0_'+str(scan_steps) not in hist_struct.keys():
                                    # individual
                                    hist_struct[key+'_hist_0_'+str(scan_steps)] = np.zeros(int_nr_bins)
                                    hist_struct[key+'_hist_1_'+str(scan_steps)] = np.zeros(int_nr_bins)
                                    
                                    # steps
                                    hist_struct[key+'_hist_0_event_'+str(scan_steps)] = 0
                                    hist_struct[key+'_hist_1_event_'+str(scan_steps)] = 0
                            else:
                                if key+'_hist_0_0_'+str(scan_steps) not in hist_struct.keys():
                                    # individual
                                    hist_struct[key+'_hist_0_0_'+str(scan_steps)] = np.zeros(int_nr_bins)
                                    hist_struct[key+'_hist_1_0_'+str(scan_steps)] = np.zeros(int_nr_bins)
                                    hist_struct[key+'_hist_0_1_'+str(scan_steps)] = np.zeros(int_nr_bins)
                                    hist_struct[key+'_hist_1_1_'+str(scan_steps)] = np.zeros(int_nr_bins)
                                    
                                    # steps
                                    hist_struct[key+'_hist_0_0_event_'+str(scan_steps)] = 0
                                    hist_struct[key+'_hist_1_0_event_'+str(scan_steps)] = 0
                                    hist_struct[key+'_hist_0_1_event_'+str(scan_steps)] = 0
                                    hist_struct[key+'_hist_1_1_event_'+str(scan_steps)] = 0
                        
                # Make masks for the different parameter keys
                if scan_key == 'Wavelength_ctr' or scan_key == 'Requested Transmission_ctr':
                    ADC_Laser_on = flatten_list(data['ADC.Laser_flag']) > threshold
                    ADC_Laser_off = flatten_list(data['ADC.Laser_flag']) <= threshold
                else:
                    ADC_Pump_on = flatten_list(data['ADC.ChopperProbe']) < threshold
                    ADC_Pump_off = flatten_list(data['ADC.ChopperProbe']) >= threshold
                    ADC_Probe_on = flatten_list(data['ADC.ChopperPump']) < threshold
                    ADC_Probe_off = flatten_list(data['ADC.ChopperPump']) >= threshold
                
                # Mask
                mask_index = np.array(range(len(data['Event'])))
                if scan_key == 'Wavelength_ctr' or scan_key == 'Requested Transmission_ctr':
                    mask = np.array([np.ones(len(mask_index), dtype=bool)* ADC_Laser_on,
                                     np.ones(len(mask_index), dtype=bool)* ADC_Laser_off])
                else:
                    mask = np.array([np.ones(len(mask_index), dtype=bool)* ADC_Probe_on * ADC_Pump_on,
                                     np.ones(len(mask_index), dtype=bool)* ADC_Probe_on * ADC_Pump_off,
                                     np.ones(len(mask_index), dtype=bool)* ADC_Probe_off * ADC_Pump_on,
                                     np.ones(len(mask_index), dtype=bool)* ADC_Probe_off * ADC_Pump_off])

                for m in masks:
                    if m[0] in data.keys():
                        if scan_key == 'Wavelength_ctr' or scan_key == 'Requested Transmission_ctr':
                            mask = [mask * (flatten_list(data[m[0]]) > float(m[1])) * (flatten_list(data[m[0]]) < float(m[2])) , 
                                    mask * (flatten_list(data[m[0]]) > float(m[3])) * (flatten_list(data[m[0]]) < float(m[4])) ] 
                        else:
                            mask = [mask * (flatten_list(data[m[0]]) > float(m[1])) * (flatten_list(data[m[0]]) < float(m[2])) , 
                                    mask * (flatten_list(data[m[0]]) > float(m[3])) * (flatten_list(data[m[0]]) < float(m[4])) ,
                                    mask * (flatten_list(data[m[0]]) > float(m[5])) * (flatten_list(data[m[0]]) < float(m[6])) ,
                                    mask * (flatten_list(data[m[0]]) > float(m[7])) * (flatten_list(data[m[0]]) < float(m[8])) ] 
                
                # Loop over events TODO These loops be slow!
                if scan_key == 'Wavelength_ctr' or scan_key == 'Requested Transmission_ctr':
                    # Histogram structure
                    if not loaded_hist_struct:
                        for event in mask_index[mask[0]]:
                            t0 = time.time()

                            current_event = [np.array(data[key][event]) for key in hist_struct['time_keys']]
                            laser = 1
                            
                            for key in range(len(current_event)):
                                
                                # Normalization
                                hist_struct[hist_struct['time_keys'][key]+f'_hist_{laser}_event_'+str(data[scan_key][event][0])] += 1
                            
                                # Append to time structs
                                hist_struct[hist_struct['time_keys'][key]+f'_hist_{laser}_'+str(data[scan_key][event][0])] = hist_struct[hist_struct['time_keys'][key]+f'_hist_{laser}_'+str(data[scan_key][event][0])] + np.histogram(current_event[key], hist_struct['edges'])[0]

                                hist_struct[hist_struct['time_keys'][key]+f'_hist_{laser}_acc'] = hist_struct[hist_struct['time_keys'][key]+f'_hist_{laser}_acc'] + np.histogram(current_event[key], hist_struct['edges'])[0]

                            # Time tracking
                            time_avg = (time_int*time_avg + time.time()-t0) / (time_int+1)
                            time_int += 1
                            if not silent and (time_int % 1000) == 0:
                                print(time.strftime('%H:%M:%S', time.gmtime())+f' Event {time_int} eta. {(event_max-time_int)*time_avg/60:.2f} min.')
                        
                        for event in mask_index[mask[1]]:
                            t0 = time.time()

                            current_event = [np.array(data[key][event]) for key in hist_struct['time_keys']]
                            laser = 0
                            
                            for key in range(len(current_event)):
                                
                                # Normalization
                                hist_struct[hist_struct['time_keys'][key]+f'_hist_{laser}_event_'+str(data[scan_key][event][0])] += 1
                            
                                # Append to time structs
                                hist_struct[hist_struct['time_keys'][key]+f'_hist_{laser}_'+str(data[scan_key][event][0])] = hist_struct[hist_struct['time_keys'][key]+f'_hist_{laser}_'+str(data[scan_key][event][0])] + np.histogram(current_event[key], hist_struct['edges'])[0]

                                hist_struct[hist_struct['time_keys'][key]+f'_hist_{laser}_acc'] = hist_struct[hist_struct['time_keys'][key]+f'_hist_{laser}_acc'] + np.histogram(current_event[key], hist_struct['edges'])[0]
                            
                            # Time tracking
                            time_avg = (time_int*time_avg + time.time()-t0) / (time_int+1)
                            time_int += 1
                            if not silent and (time_int % 1000) == 0:
                                print(time.strftime('%H:%M:%S', time.gmtime())+f' Event {time_int} eta. {(event_max-time_int)*time_avg/60:.2f} min.')
                        
                else:
                    # Histogram structure
                    if not loaded_hist_struct:
                        for event in mask_index[mask[0]]:
                            t0 = time.time()

                            current_event = [np.array(data[key][event]) for key in hist_struct['time_keys']]
                            probe = 1
                            pump = 1

                            for key in range(len(current_event)):
                                
                                # Normalization
                                hist_struct[hist_struct['time_keys'][key]+f'_hist_{probe}_{pump}_event_'+str(data[scan_key][event][0])] += 1
                            
                                # Append to time structs
                                hist_struct[hist_struct['time_keys'][key]+f'_hist_{probe}_{pump}_'+str(data[scan_key][event][0])] = hist_struct[hist_struct['time_keys'][key]+f'_hist_{probe}_{pump}_'+str(data[scan_key][event][0])] + np.histogram(current_event[key], hist_struct['edges'])[0]

                                hist_struct[hist_struct['time_keys'][key]+f'_hist_{probe}_{pump}_acc'] = hist_struct[hist_struct['time_keys'][key]+f'_hist_{probe}_{pump}_acc'] + np.histogram(current_event[key], hist_struct['edges'])[0]
                            # Time tracking
                            time_avg = (time_int*time_avg + time.time()-t0) / (time_int+1)
                            time_int += 1
                            if not silent and (time_int % 1000) == 0:
                                print(time.strftime('%H:%M:%S', time.gmtime())+f' Event {time_int} eta. {(event_max-time_int)*time_avg/60:.2f} min.')
                        
                        
                        for event in mask_index[mask[1]]:
                            t0 = time.time()

                            current_event = [np.array(data[key][event]) for key in hist_struct['time_keys']]
                            probe = 1
                            pump = 0
                            
                            for key in range(len(current_event)):
                                
                                # Normalization
                                hist_struct[hist_struct['time_keys'][key]+f'_hist_{probe}_{pump}_event_'+str(data[scan_key][event][0])] += 1
                            
                                # Append to time structs
                                hist_struct[hist_struct['time_keys'][key]+f'_hist_{probe}_{pump}_'+str(data[scan_key][event][0])] = hist_struct[hist_struct['time_keys'][key]+f'_hist_{probe}_{pump}_'+str(data[scan_key][event][0])] + np.histogram(current_event[key], hist_struct['edges'])[0]

                                hist_struct[hist_struct['time_keys'][key]+f'_hist_{probe}_{pump}_acc'] = hist_struct[hist_struct['time_keys'][key]+f'_hist_{probe}_{pump}_acc'] + np.histogram(current_event[key], hist_struct['edges'])[0]
                            
                            # Time tracking
                            time_avg = (time_int*time_avg + time.time()-t0) / (time_int+1)
                            time_int += 1
                            if not silent and (time_int % 1000) == 0:
                                print(time.strftime('%H:%M:%S', time.gmtime())+f' Event {time_int} eta. {(event_max-time_int)*time_avg/60:.2f} min.')
                        
                        for event in mask_index[mask[2]]:
                            t0 = time.time()

                            current_event = [np.array(data[key][event]) for key in hist_struct['time_keys']]
                            probe = 0
                            pump = 1
                            
                            for key in range(len(current_event)):
                                
                                # Normalization
                                hist_struct[hist_struct['time_keys'][key]+f'_hist_{probe}_{pump}_event_'+str(data[scan_key][event][0])] += 1
                            
                                # Append to time structs
                                hist_struct[hist_struct['time_keys'][key]+f'_hist_{probe}_{pump}_'+str(data[scan_key][event][0])] = hist_struct[hist_struct['time_keys'][key]+f'_hist_{probe}_{pump}_'+str(data[scan_key][event][0])] + np.histogram(current_event[key], hist_struct['edges'])[0]

                                hist_struct[hist_struct['time_keys'][key]+f'_hist_{probe}_{pump}_acc'] = hist_struct[hist_struct['time_keys'][key]+f'_hist_{probe}_{pump}_acc'] + np.histogram(current_event[key], hist_struct['edges'])[0]

                            # Time tracking
                            time_avg = (time_int*time_avg + time.time()-t0) / (time_int+1)
                            time_int += 1
                            if not silent and (time_int % 1000) == 0:
                                print(time.strftime('%H:%M:%S', time.gmtime())+f' Event {time_int} eta. {(event_max-time_int)*time_avg/60:.2f} min.')
                        
                        for event in mask_index[mask[3]]:
                            t0 = time.time()

                            current_event = [np.array(data[key][event]) for key in hist_struct['time_keys']]
                            probe = 0
                            pump = 0
                            
                            for key in range(len(current_event)):
                                
                                # Normalization
                                hist_struct[hist_struct['time_keys'][key]+f'_hist_{probe}_{pump}_event_'+str(data[scan_key][event][0])] += 1
                            
                                # Append to time structs
                                hist_struct[hist_struct['time_keys'][key]+f'_hist_{probe}_{pump}_'+str(data[scan_key][event][0])] = hist_struct[hist_struct['time_keys'][key]+f'_hist_{probe}_{pump}_'+str(data[scan_key][event][0])] + np.histogram(current_event[key], hist_struct['edges'])[0]

                                hist_struct[hist_struct['time_keys'][key]+f'_hist_{probe}_{pump}_acc'] = hist_struct[hist_struct['time_keys'][key]+f'_hist_{probe}_{pump}_acc'] + np.histogram(current_event[key], hist_struct['edges'])[0]
                            
                            # Time tracking
                            time_avg = (time_int*time_avg + time.time()-t0) / (time_int+1)
                            time_int += 1
                            if not silent and (time_int % 1000) == 0:
                                print(time.strftime('%H:%M:%S', time.gmtime())+f' Event {time_int} eta. {(event_max-time_int)*time_avg/60:.2f} min.')
                        
                # Clear data
                data.clear()
    
    if not loaded_hist_struct:
        hist_struct['edges'] = hist_struct['edges'] * TDC_res
    
    if write != None:
        
        if not loaded_hist_struct:
            if not os.path.exists(write[:write.rfind('/')]):
                os.makedirs(write[:write.rfind('/')])
            
            # Write to file
            f = open(write, 'w')
            f.write(json.dumps(hist_struct, cls=NumpyEncoder))
            f.close()

    print(time.strftime('%H:%M:%S', time.gmtime())+' Histogram created')

    return hist_struct

def load_histogram(runs, nr_bins=1000, write=None, overwrite=False, silent = False, scan_key = None, masks = [], threshold=1000, event_max=None, hist_limits=[0,None]):
    
    # Boolean keys
    loaded_hist_struct = False
    reading = False
    
    # Structures
    hist_struct = {}
    
    # Save masks
    hist_struct['masks'] = masks
    hist_struct['time_keys'] = []

    if write != None:
        if not silent:
            print(time.strftime('%H:%M:%S', time.gmtime())+' Load Histogram')
        try:    
            if os.path.exists(write) and not overwrite:
                # Load Histogram
                f = open(write, 'r')
                hist_struct = json.loads(f.read())
                f.close()
                loaded_hist_struct = True
                if not silent:
                    print(time.strftime('%H:%M:%S', time.gmtime())+' Histogram JSON files found and read')
                return hist_struct
        except:
            pass
    
    if not silent:
       print(time.strftime('%H:%M:%S', time.gmtime())+' Create Structs')
   
    TDC_res = 1

    # Time tracking
    time_avg = 0.
    time_int = 0
    
    # Loop over runs
    for run in runs:
        file_folder = os.listdir(run[:run.rfind('/')])
        for filename in sorted(file_folder):
            if (run[run.rfind('/')+1:] in filename) and ('-dat-' in filename):
                
                # Load the needed keys
                data = load_dat_file(run[:run.rfind('/')+1]+filename, silent=silent)
                
                # Set default scan step
                if scan_key == None:
                    scan_key = data['TCP_type']
                hist_struct['scan_key'] = scan_key

                TDC_res = data['TDC.res']
                unique_scan_steps = np.unique(flatten_list(data[scan_key]))
                
                if np.any(np.array(hist_limits) == None): 
                    # Manually modified variable to set histogram size if not given
                    ADC_bit = data['ADC.bit']*50 
                else:
                    ADC_bit = hist_limits[-1] + 1

                int_nr_bins = int(TDC_res*(ADC_bit-hist_limits[0])/nr_bins)

                # check the keys
                for key in data.keys():
                    # Dont add time to Parameters
                    if 'TDC1' in key and key not in hist_struct['time_keys']:
                        hist_struct['time_keys'].append(key)
                time_keys = hist_struct['time_keys']
                
                #edge of bins
                edges = np.arange(hist_limits[0], ADC_bit*(1+1/int_nr_bins), (ADC_bit-hist_limits[0])/int_nr_bins)
                hist_struct['edges'] = edges

                # Add to histogram struct if it does not exist 
                if not loaded_hist_struct:

                    # Accumulated
                    if not reading:
                        for key in time_keys:
                            if scan_key == 'Wavelength_ctr' or scan_key == 'Requested Transmission_ctr':
                                hist_struct[key+'_hist_0_acc'] = np.zeros(len(edges)-1)
                                hist_struct[key+'_hist_1_acc'] = np.zeros(len(edges)-1)
                            else:
                                hist_struct[key+'_hist_0_0_acc'] = np.zeros(len(edges)-1)
                                hist_struct[key+'_hist_0_1_acc'] = np.zeros(len(edges)-1)
                                hist_struct[key+'_hist_1_0_acc'] = np.zeros(len(edges)-1)
                                hist_struct[key+'_hist_1_1_acc'] = np.zeros(len(edges)-1)
                        reading = True

                    # Checking uniqe scan_steps values and adding them to struct
                    for scan_steps in unique_scan_steps:
                        
                        # Add to histogram struct if it does not exist
                        for key in time_keys:

                            if scan_key == 'Wavelength_ctr' or scan_key == 'Requested Transmission_ctr':
                                if key+'_hist_0_'+str(scan_steps) not in hist_struct.keys():
                                    # individual
                                    hist_struct[key+'_hist_0_'+str(scan_steps)] = np.zeros(len(edges)-1)
                                    hist_struct[key+'_hist_1_'+str(scan_steps)] = np.zeros(len(edges)-1)
                                    
                                    # steps
                                    hist_struct[key+'_hist_0_event_'+str(scan_steps)] = 0
                                    hist_struct[key+'_hist_1_event_'+str(scan_steps)] = 0
                            else:
                                if key+'_hist_0_0_'+str(scan_steps) not in hist_struct.keys():
                                    # individual
                                    hist_struct[key+'_hist_0_0_'+str(scan_steps)] = np.zeros(len(edges)-1)
                                    hist_struct[key+'_hist_1_0_'+str(scan_steps)] = np.zeros(len(edges)-1)
                                    hist_struct[key+'_hist_0_1_'+str(scan_steps)] = np.zeros(len(edges)-1)
                                    hist_struct[key+'_hist_1_1_'+str(scan_steps)] = np.zeros(len(edges)-1)
                                    
                                    # steps
                                    hist_struct[key+'_hist_0_0_event_'+str(scan_steps)] = 0
                                    hist_struct[key+'_hist_1_0_event_'+str(scan_steps)] = 0
                                    hist_struct[key+'_hist_0_1_event_'+str(scan_steps)] = 0
                                    hist_struct[key+'_hist_1_1_event_'+str(scan_steps)] = 0
                        
                # Make masks for the different parameter keys
                if scan_key == 'Wavelength_ctr' or scan_key == 'Requested Transmission_ctr':
                    ADC_Laser_on = flatten_list(data['ADC.Laser_flag']) > threshold
                    ADC_Laser_off = flatten_list(data['ADC.Laser_flag']) <= threshold
                else:
                    ADC_Pump_on = flatten_list(data['ADC.ChopperProbe']) < threshold
                    ADC_Pump_off = flatten_list(data['ADC.ChopperProbe']) >= threshold
                    ADC_Probe_on = flatten_list(data['ADC.ChopperPump']) < threshold
                    ADC_Probe_off = flatten_list(data['ADC.ChopperPump']) >= threshold
                
                # Mask
                mask_index = np.array(range(len(data['Event'])))
                if scan_key == 'Wavelength_ctr' or scan_key == 'Requested Transmission_ctr':
                    mask = np.array([np.ones(len(mask_index), dtype=bool)* ADC_Laser_on,
                                     np.ones(len(mask_index), dtype=bool)* ADC_Laser_off])
                else:
                    mask = np.array([np.ones(len(mask_index), dtype=bool)* ADC_Probe_on * ADC_Pump_on,
                                     np.ones(len(mask_index), dtype=bool)* ADC_Probe_on * ADC_Pump_off,
                                     np.ones(len(mask_index), dtype=bool)* ADC_Probe_off * ADC_Pump_on,
                                     np.ones(len(mask_index), dtype=bool)* ADC_Probe_off * ADC_Pump_off])

                for m in masks:
                    if m[0] in data.keys():
                        if scan_key == 'Wavelength_ctr' or scan_key == 'Requested Transmission_ctr':
                            mask = [mask[0] * (flatten_list(data[m[0]]) >= float(m[1])) * (flatten_list(data[m[0]]) <= float(m[2])) , 
                                    mask[1] * (flatten_list(data[m[0]]) >= float(m[3])) * (flatten_list(data[m[0]]) <= float(m[4])) ] 
                        else:
                            mask = [mask[0] * (flatten_list(data[m[0]]) >= float(m[1])) * (flatten_list(data[m[0]]) <= float(m[2])) , 
                                    mask[1] * (flatten_list(data[m[0]]) >= float(m[3])) * (flatten_list(data[m[0]]) <= float(m[4])) ,
                                    mask[2] * (flatten_list(data[m[0]]) >= float(m[5])) * (flatten_list(data[m[0]]) <= float(m[6])) ,
                                    mask[3] * (flatten_list(data[m[0]]) >= float(m[7])) * (flatten_list(data[m[0]]) <= float(m[8])) ] 
                
                scan_steps = flatten_list(data[scan_key])
                sort_index = np.argsort(scan_steps)
                scan_steps, start_index = np.unique(np.sort(scan_steps), return_index=True)

                if event_max == None:
                    event_max = len(scan_steps)*2*len(file_folder)
                
                # Loop over events 
                if scan_key == 'Wavelength_ctr' or scan_key == 'Requested Transmission_ctr':
                    # Histogram structure
                    if not loaded_hist_struct:
                        
                        for key in time_keys:

                            data_arr = np.array(data[key],dtype=object)

                            hist_struct[key+f'_hist_{1}_acc'] = hist_struct[key+f'_hist_{1}_acc'] + np.histogram(flatten_list(data_arr[mask_index[mask[0]]]), edges)[0]
                            hist_struct[key+f'_hist_{0}_acc'] = hist_struct[key+f'_hist_{0}_acc'] + np.histogram(flatten_list(data_arr[mask_index[mask[1]]]), edges)[0]
                            
                            for i in range(len(scan_steps)):
                                t0 = time.time()
                                
                                if i == len(scan_steps) - 1:
                                    
                                    hist_struct[key+f'_hist_{1}_'+str(scan_steps[i])] = hist_struct[key+f'_hist_{1}_'+str(scan_steps[i])] + np.histogram(flatten_list(data_arr[mask_index[sort_index][start_index[i]:][mask[0][sort_index][start_index[i]:]]]), edges)[0]
                                    hist_struct[key+f'_hist_{0}_'+str(scan_steps[i])] = hist_struct[key+f'_hist_{0}_'+str(scan_steps[i])] + np.histogram(flatten_list(data_arr[mask_index[sort_index][start_index[i]:][mask[1][sort_index][start_index[i]:]]]), edges)[0]

                                    hist_struct[key+'_hist_1_event_'+str(scan_steps[i])] += len(data_arr[mask_index[sort_index][start_index[i]:][mask[0][sort_index][start_index[i]:]]])
                                    hist_struct[key+'_hist_0_event_'+str(scan_steps[i])] += len(data_arr[mask_index[sort_index][start_index[i]:][mask[1][sort_index][start_index[i]:]]])

                                else:
                                    
                                    hist_struct[key+f'_hist_{1}_'+str(scan_steps[i])] = hist_struct[key+f'_hist_{1}_'+str(scan_steps[i])] + np.histogram(flatten_list(data_arr[mask_index[sort_index][start_index[i]:start_index[i+1]][mask[0][sort_index][start_index[i]:start_index[i+1]]]]), edges)[0]
                                    hist_struct[key+f'_hist_{0}_'+str(scan_steps[i])] = hist_struct[key+f'_hist_{0}_'+str(scan_steps[i])] + np.histogram(flatten_list(data_arr[mask_index[sort_index][start_index[i]:start_index[i+1]][mask[1][sort_index][start_index[i]:start_index[i+1]]]]), edges)[0]

                                    hist_struct[key+'_hist_1_event_'+str(scan_steps[i])] += len(data_arr[mask_index[sort_index][start_index[i]:start_index[i+1]][mask[0][sort_index][start_index[i]:start_index[i+1]]]])
                                    hist_struct[key+'_hist_0_event_'+str(scan_steps[i])] += len(data_arr[mask_index[sort_index][start_index[i]:start_index[i+1]][mask[1][sort_index][start_index[i]:start_index[i+1]]]])

                                # Time tracking
                                time_avg = (time_int*time_avg + time.time()-t0) / (time_int+1)
                                time_int += 1
                                if not silent and (time_int % (2*len(file_folder))) == 0:
                                    print(time.strftime('%H:%M:%S', time.gmtime())+f' Step {time_int/(2*len(file_folder))} eta. {(event_max-time_int)*time_avg/60:.2f} min.')
                            

                else:
                    # Histogram structure
                    if not loaded_hist_struct:
                        
                        for key in hist_struct['time_keys']:

                            data_arr = np.array(data[key],dtype=object)

                            hist_struct[key+f'_hist_1_1_acc'] = hist_struct[key+f'_hist_1_1_acc'] + np.histogram(flatten_list(data_arr[mask_index[mask[0]]]), edges)[0]
                            hist_struct[key+f'_hist_1_0_acc'] = hist_struct[key+f'_hist_1_0_acc'] + np.histogram(flatten_list(data_arr[mask_index[mask[1]]]), edges)[0]
                            hist_struct[key+f'_hist_0_1_acc'] = hist_struct[key+f'_hist_0_1_acc'] + np.histogram(flatten_list(data_arr[mask_index[mask[2]]]), edges)[0]
                            hist_struct[key+f'_hist_0_0_acc'] = hist_struct[key+f'_hist_0_0_acc'] + np.histogram(flatten_list(data_arr[mask_index[mask[3]]]), edges)[0]

                            for i in range(len(scan_steps)):
                                t0 = time.time()
                                
                                if i == len(scan_steps) - 1:
                                    
                                    hist_struct[key+f'_hist_1_1_'+str(scan_steps[i])] = hist_struct[key+f'_hist_1_1_'+str(scan_steps[i])] + np.histogram(flatten_list(data_arr[mask_index[sort_index][start_index[i]:][mask[0][sort_index][start_index[i]:]]]), edges)[0]
                                    hist_struct[key+f'_hist_1_0_'+str(scan_steps[i])] = hist_struct[key+f'_hist_1_0_'+str(scan_steps[i])] + np.histogram(flatten_list(data_arr[mask_index[sort_index][start_index[i]:][mask[1][sort_index][start_index[i]:]]]), edges)[0]
                                    hist_struct[key+f'_hist_0_1_'+str(scan_steps[i])] = hist_struct[key+f'_hist_0_1_'+str(scan_steps[i])] + np.histogram(flatten_list(data_arr[mask_index[sort_index][start_index[i]:][mask[2][sort_index][start_index[i]:]]]), edges)[0]
                                    hist_struct[key+f'_hist_0_0_'+str(scan_steps[i])] = hist_struct[key+f'_hist_0_0_'+str(scan_steps[i])] + np.histogram(flatten_list(data_arr[mask_index[sort_index][start_index[i]:][mask[3][sort_index][start_index[i]:]]]), edges)[0]

                                    hist_struct[key+'_hist_1_1_event_'+str(scan_steps[i])] += len(data_arr[mask_index[sort_index][start_index[i]:][mask[0][sort_index][start_index[i]:]]])
                                    hist_struct[key+'_hist_1_0_event_'+str(scan_steps[i])] += len(data_arr[mask_index[sort_index][start_index[i]:][mask[1][sort_index][start_index[i]:]]])
                                    hist_struct[key+'_hist_0_1_event_'+str(scan_steps[i])] += len(data_arr[mask_index[sort_index][start_index[i]:][mask[2][sort_index][start_index[i]:]]])
                                    hist_struct[key+'_hist_0_0_event_'+str(scan_steps[i])] += len(data_arr[mask_index[sort_index][start_index[i]:][mask[3][sort_index][start_index[i]:]]])

                                else:
                                    
                                    hist_struct[key+f'_hist_1_1_'+str(scan_steps[i])] = hist_struct[key+f'_hist_1_1_'+str(scan_steps[i])] + np.histogram(flatten_list(data_arr[mask_index[sort_index][start_index[i]:start_index[i+1]][mask[0][sort_index][start_index[i]:start_index[i+1]]]]), edges)[0]
                                    hist_struct[key+f'_hist_1_0_'+str(scan_steps[i])] = hist_struct[key+f'_hist_1_0_'+str(scan_steps[i])] + np.histogram(flatten_list(data_arr[mask_index[sort_index][start_index[i]:start_index[i+1]][mask[1][sort_index][start_index[i]:start_index[i+1]]]]), edges)[0]
                                    hist_struct[key+f'_hist_0_1_'+str(scan_steps[i])] = hist_struct[key+f'_hist_0_1_'+str(scan_steps[i])] + np.histogram(flatten_list(data_arr[mask_index[sort_index][start_index[i]:start_index[i+1]][mask[2][sort_index][start_index[i]:start_index[i+1]]]]), edges)[0]
                                    hist_struct[key+f'_hist_0_0_'+str(scan_steps[i])] = hist_struct[key+f'_hist_0_0_'+str(scan_steps[i])] + np.histogram(flatten_list(data_arr[mask_index[sort_index][start_index[i]:start_index[i+1]][mask[3][sort_index][start_index[i]:start_index[i+1]]]]), edges)[0]

                                    hist_struct[key+'_hist_1_1_event_'+str(scan_steps[i])] += len(data_arr[mask_index[sort_index][start_index[i]:start_index[i+1]][mask[0][sort_index][start_index[i]:start_index[i+1]]]])
                                    hist_struct[key+'_hist_1_0_event_'+str(scan_steps[i])] += len(data_arr[mask_index[sort_index][start_index[i]:start_index[i+1]][mask[1][sort_index][start_index[i]:start_index[i+1]]]])
                                    hist_struct[key+'_hist_0_1_event_'+str(scan_steps[i])] += len(data_arr[mask_index[sort_index][start_index[i]:start_index[i+1]][mask[2][sort_index][start_index[i]:start_index[i+1]]]])
                                    hist_struct[key+'_hist_0_0_event_'+str(scan_steps[i])] += len(data_arr[mask_index[sort_index][start_index[i]:start_index[i+1]][mask[3][sort_index][start_index[i]:start_index[i+1]]]])

                                # Time tracking
                                time_avg = (time_int*time_avg + time.time()-t0) / (time_int+1)
                                time_int += 1
                                if not silent and (time_int % (2*len(file_folder))) == 0:
                                    print(time.strftime('%H:%M:%S', time.gmtime())+f' Step {time_int/(2*len(file_folder))} eta. {(event_max-time_int)*time_avg/60:.2f} min.')
                            
                # Clear data
                data.clear()
    
    if not loaded_hist_struct:
        hist_struct['edges'] = edges * TDC_res
    
    if write != None:
        
        if not loaded_hist_struct:
            if not os.path.exists(write[:write.rfind('/')]):
                os.makedirs(write[:write.rfind('/')])
            
            # Write to file
            f = open(write, 'w')
            f.write(json.dumps(hist_struct, cls=NumpyEncoder))
            f.close()

    print(time.strftime('%H:%M:%S', time.gmtime())+' Histogram created')

    return hist_struct

def update_histogram(dat_files, files_to_load, write, nr_bins = 1000, silent = False, threshold = 1000, event_max = None, hist_limits=[0,None]):
    # Boolean keys
    loaded_hist_struct = False
    reading = False

    if not silent:
        print(time.strftime('%H:%M:%S', time.gmtime())+' Updating histogram')

    if os.path.exists(write):
        # Load Histogram
        f = open(write, 'r')
        hist_struct = json.loads(f.read())
        f.close()
        loaded_hist_struct = True
        if not silent:
            print(time.strftime('%H:%M:%S', time.gmtime())+' Histogram JSON files found and read')

        if not silent:
            print(time.strftime('%H:%M:%S', time.gmtime())+' Create Structs')
    
        TDC_res = 1
        scan_key = hist_struct['scan_key']
        masks = hist_struct['masks']

        # Time tracking
        time_avg = 0.
        time_int = 0
    
        # Loop over runs
        for filename in dat_files:
            if '-dat-' in filename:
                
                # Load the needed keys
                data = load_dat_file(filename, silent=silent)

                # File mask
                mask = np.zeros(len(data['Event']), dtype=bool)
                for f in files_to_load:
                    mask = mask + (flatten_list(data['File']) == f)

                TDC_res = data['TDC.res']
                if np.any(np.array(hist_limits) == None): 
                    # Manually modified variable to set histogram size if not given
                    ADC_bit = data['ADC.bit']*50 
                else:
                    ADC_bit = hist_limits[-1] + 1

                edges = np.array(hist_struct['edges']) / TDC_res
                hist_struct['edges'] = edges

                int_nr_bins = int(TDC_res*(ADC_bit-hist_limits[0])/nr_bins)

                # check the keys
                for key in data.keys():
                    # Dont add time to Parameters
                    if 'TDC1' in key and key not in hist_struct['time_keys']:
                        hist_struct['time_keys'].append(key)
                
                # Checking uniqe scan_steps values and adding them to struct
                for scan_steps in np.unique(flatten_list(data[scan_key])):
                    
                    # Add to histogram struct if it does not exist
                    for key in hist_struct['time_keys']:

                        if scan_key == 'Wavelength_ctr' or scan_key == 'Requested Transmission_ctr':
                            if key+'_hist_0_'+str(scan_steps) not in hist_struct.keys():
                                # individual
                                hist_struct[key+'_hist_0_'+str(scan_steps)] = np.zeros(len(edges)-1)
                                hist_struct[key+'_hist_1_'+str(scan_steps)] = np.zeros(len(edges)-1)
                                
                                # steps
                                hist_struct[key+'_hist_0_event_'+str(scan_steps)] = 0
                                hist_struct[key+'_hist_1_event_'+str(scan_steps)] = 0
                        else:
                            if key+'_hist_0_0_'+str(scan_steps) not in hist_struct.keys():
                                # individual
                                hist_struct[key+'_hist_0_0_'+str(scan_steps)] = np.zeros(len(edges)-1)
                                hist_struct[key+'_hist_1_0_'+str(scan_steps)] = np.zeros(len(edges)-1)
                                hist_struct[key+'_hist_0_1_'+str(scan_steps)] = np.zeros(len(edges)-1)
                                hist_struct[key+'_hist_1_1_'+str(scan_steps)] = np.zeros(len(edges)-1)
                                
                                # steps
                                hist_struct[key+'_hist_0_0_event_'+str(scan_steps)] = 0
                                hist_struct[key+'_hist_1_0_event_'+str(scan_steps)] = 0
                                hist_struct[key+'_hist_0_1_event_'+str(scan_steps)] = 0
                                hist_struct[key+'_hist_1_1_event_'+str(scan_steps)] = 0
                        
                # Make masks for the different parameter keys
                if scan_key == 'Wavelength_ctr' or scan_key == 'Requested Transmission_ctr':
                    ADC_Laser_on = flatten_list(data['ADC.Laser_flag']) > threshold
                    ADC_Laser_off = flatten_list(data['ADC.Laser_flag']) <= threshold
                else:
                    ADC_Pump_on = flatten_list(data['ADC.ChopperProbe']) < threshold
                    ADC_Pump_off = flatten_list(data['ADC.ChopperProbe']) >= threshold
                    ADC_Probe_on = flatten_list(data['ADC.ChopperPump']) < threshold
                    ADC_Probe_off = flatten_list(data['ADC.ChopperPump']) >= threshold
                
                # Mask
                mask_index = np.array(range(len(data['Event'])))
                if scan_key == 'Wavelength_ctr' or scan_key == 'Requested Transmission_ctr':
                    mask = np.array([mask * ADC_Laser_on,
                                     mask * ADC_Laser_off])
                else:
                    mask = np.array([mask * ADC_Probe_on * ADC_Pump_on,
                                     mask * ADC_Probe_on * ADC_Pump_off,
                                     mask * ADC_Probe_off * ADC_Pump_on,
                                     mask * ADC_Probe_off * ADC_Pump_off])
                
                for m in masks:
                    if m[0] in data.keys():
                        if scan_key == 'Wavelength_ctr' or scan_key == 'Requested Transmission_ctr':
                            mask = [mask[0] * (flatten_list(data[m[0]]) > float(m[1])) * (flatten_list(data[m[0]]) < float(m[2])) , 
                                    mask[1] * (flatten_list(data[m[0]]) > float(m[3])) * (flatten_list(data[m[0]]) < float(m[4])) ] 
                        else:
                            mask = [mask[0] * (flatten_list(data[m[0]]) > float(m[1])) * (flatten_list(data[m[0]]) < float(m[2])) , 
                                    mask[1] * (flatten_list(data[m[0]]) > float(m[3])) * (flatten_list(data[m[0]]) < float(m[4])) ,
                                    mask[2] * (flatten_list(data[m[0]]) > float(m[5])) * (flatten_list(data[m[0]]) < float(m[6])) ,
                                    mask[3] * (flatten_list(data[m[0]]) > float(m[7])) * (flatten_list(data[m[0]]) < float(m[8])) ] 
                
                scan_steps = flatten_list(data[scan_key])
                sort_index = np.argsort(scan_steps)
                scan_steps, start_index = np.unique(np.sort(scan_steps), return_index=True)

                if event_max == None:
                    event_max = len(scan_steps)*2
                
                # Loop over events 
                if scan_key == 'Wavelength_ctr' or scan_key == 'Requested Transmission_ctr':
                    # Histogram structure
                    for key in hist_struct['time_keys']:

                        data_arr = np.array(data[key],dtype=object)

                        hist_struct[key+f'_hist_{1}_acc'] = hist_struct[key+f'_hist_{1}_acc'] + np.histogram(flatten_list(data_arr[mask_index[mask[0]]]), edges)[0]
                        hist_struct[key+f'_hist_{0}_acc'] = hist_struct[key+f'_hist_{0}_acc'] + np.histogram(flatten_list(data_arr[mask_index[mask[1]]]), edges)[0]

                        for i in range(len(scan_steps)):
                            t0 = time.time()
                            
                            if i == len(scan_steps) - 1:
                                
                                hist_struct[key+f'_hist_{1}_'+str(scan_steps[i])] = hist_struct[key+f'_hist_{1}_'+str(scan_steps[i])] + np.histogram(flatten_list(data_arr[mask_index[sort_index][start_index[i]:][mask[0][sort_index][start_index[i]:]]]), edges)[0]
                                hist_struct[key+f'_hist_{0}_'+str(scan_steps[i])] = hist_struct[key+f'_hist_{0}_'+str(scan_steps[i])] + np.histogram(flatten_list(data_arr[mask_index[sort_index][start_index[i]:][mask[1][sort_index][start_index[i]:]]]), edges)[0]

                                hist_struct[key+'_hist_1_event_'+str(scan_steps[i])] += len(data_arr[mask_index[sort_index][start_index[i]:][mask[0][sort_index][start_index[i]:]]])
                                hist_struct[key+'_hist_0_event_'+str(scan_steps[i])] += len(data_arr[mask_index[sort_index][start_index[i]:][mask[1][sort_index][start_index[i]:]]])

                            else:
                                
                                hist_struct[key+f'_hist_{1}_'+str(scan_steps[i])] = hist_struct[key+f'_hist_{1}_'+str(scan_steps[i])] + np.histogram(flatten_list(data_arr[mask_index[sort_index][start_index[i]:start_index[i+1]][mask[0][sort_index][start_index[i]:start_index[i+1]]]]), edges)[0]
                                hist_struct[key+f'_hist_{0}_'+str(scan_steps[i])] = hist_struct[key+f'_hist_{0}_'+str(scan_steps[i])] + np.histogram(flatten_list(data_arr[mask_index[sort_index][start_index[i]:start_index[i+1]][mask[1][sort_index][start_index[i]:start_index[i+1]]]]), edges)[0]

                                hist_struct[key+'_hist_1_event_'+str(scan_steps[i])] += len(data_arr[mask_index[sort_index][start_index[i]:start_index[i+1]][mask[0][sort_index][start_index[i]:start_index[i+1]]]])
                                hist_struct[key+'_hist_0_event_'+str(scan_steps[i])] += len(data_arr[mask_index[sort_index][start_index[i]:start_index[i+1]][mask[1][sort_index][start_index[i]:start_index[i+1]]]])


                            # Time tracking
                            time_avg = (time_int*time_avg + time.time()-t0) / (time_int+1)
                            time_int += 1
                            if not silent and (time_int % (2)) == 0:
                                print(time.strftime('%H:%M:%S', time.gmtime())+f' Step {time_int/(2)} eta. {(event_max-time_int)*time_avg/60:.2f} min.')
                            

                else:
                    # Histogram structure
                    for key in hist_struct['time_keys']:

                        data_arr = np.array(data[key],dtype=object)

                        hist_struct[key+f'_hist_1_1_acc'] = hist_struct[key+f'_hist_1_1_acc'] + np.histogram(flatten_list(data_arr[mask_index[mask[0]]]), edges)[0]
                        hist_struct[key+f'_hist_1_0_acc'] = hist_struct[key+f'_hist_1_0_acc'] + np.histogram(flatten_list(data_arr[mask_index[mask[1]]]), edges)[0]
                        hist_struct[key+f'_hist_0_1_acc'] = hist_struct[key+f'_hist_0_1_acc'] + np.histogram(flatten_list(data_arr[mask_index[mask[2]]]), edges)[0]
                        hist_struct[key+f'_hist_0_0_acc'] = hist_struct[key+f'_hist_0_0_acc'] + np.histogram(flatten_list(data_arr[mask_index[mask[3]]]), edges)[0]

                        for i in range(len(scan_steps)):
                            t0 = time.time()
                            
                            if i == len(scan_steps) - 1:
                                
                                hist_struct[key+f'_hist_1_1_'+str(scan_steps[i])] = hist_struct[key+f'_hist_1_1_'+str(scan_steps[i])] + np.histogram(flatten_list(data_arr[mask_index[sort_index][start_index[i]:][mask[0][sort_index][start_index[i]:]]]), edges)[0]
                                hist_struct[key+f'_hist_1_0_'+str(scan_steps[i])] = hist_struct[key+f'_hist_1_0_'+str(scan_steps[i])] + np.histogram(flatten_list(data_arr[mask_index[sort_index][start_index[i]:][mask[1][sort_index][start_index[i]:]]]), edges)[0]
                                hist_struct[key+f'_hist_0_1_'+str(scan_steps[i])] = hist_struct[key+f'_hist_0_1_'+str(scan_steps[i])] + np.histogram(flatten_list(data_arr[mask_index[sort_index][start_index[i]:][mask[2][sort_index][start_index[i]:]]]), edges)[0]
                                hist_struct[key+f'_hist_0_0_'+str(scan_steps[i])] = hist_struct[key+f'_hist_0_0_'+str(scan_steps[i])] + np.histogram(flatten_list(data_arr[mask_index[sort_index][start_index[i]:][mask[3][sort_index][start_index[i]:]]]), edges)[0]

                                hist_struct[key+'_hist_1_1_event_'+str(scan_steps[i])] += len(data_arr[mask_index[sort_index][start_index[i]:][mask[0][sort_index][start_index[i]:]]])
                                hist_struct[key+'_hist_1_0_event_'+str(scan_steps[i])] += len(data_arr[mask_index[sort_index][start_index[i]:][mask[1][sort_index][start_index[i]:]]])
                                hist_struct[key+'_hist_0_1_event_'+str(scan_steps[i])] += len(data_arr[mask_index[sort_index][start_index[i]:][mask[2][sort_index][start_index[i]:]]])
                                hist_struct[key+'_hist_0_0_event_'+str(scan_steps[i])] += len(data_arr[mask_index[sort_index][start_index[i]:][mask[3][sort_index][start_index[i]:]]])

                            else:
                                
                                hist_struct[key+f'_hist_1_1_'+str(scan_steps[i])] = hist_struct[key+f'_hist_1_1_'+str(scan_steps[i])] + np.histogram(flatten_list(data_arr[mask_index[sort_index][start_index[i]:start_index[i+1]][mask[0][sort_index][start_index[i]:start_index[i+1]]]]), edges)[0]
                                hist_struct[key+f'_hist_1_0_'+str(scan_steps[i])] = hist_struct[key+f'_hist_1_0_'+str(scan_steps[i])] + np.histogram(flatten_list(data_arr[mask_index[sort_index][start_index[i]:start_index[i+1]][mask[1][sort_index][start_index[i]:start_index[i+1]]]]), edges)[0]
                                hist_struct[key+f'_hist_0_1_'+str(scan_steps[i])] = hist_struct[key+f'_hist_0_1_'+str(scan_steps[i])] + np.histogram(flatten_list(data_arr[mask_index[sort_index][start_index[i]:start_index[i+1]][mask[2][sort_index][start_index[i]:start_index[i+1]]]]), edges)[0]
                                hist_struct[key+f'_hist_0_0_'+str(scan_steps[i])] = hist_struct[key+f'_hist_0_0_'+str(scan_steps[i])] + np.histogram(flatten_list(data_arr[mask_index[sort_index][start_index[i]:start_index[i+1]][mask[3][sort_index][start_index[i]:start_index[i+1]]]]), edges)[0]

                                hist_struct[key+'_hist_1_1_event_'+str(scan_steps[i])] += len(data_arr[mask_index[sort_index][start_index[i]:start_index[i+1]][mask[0][sort_index][start_index[i]:start_index[i+1]]]])
                                hist_struct[key+'_hist_1_0_event_'+str(scan_steps[i])] += len(data_arr[mask_index[sort_index][start_index[i]:start_index[i+1]][mask[1][sort_index][start_index[i]:start_index[i+1]]]])
                                hist_struct[key+'_hist_0_1_event_'+str(scan_steps[i])] += len(data_arr[mask_index[sort_index][start_index[i]:start_index[i+1]][mask[2][sort_index][start_index[i]:start_index[i+1]]]])
                                hist_struct[key+'_hist_0_0_event_'+str(scan_steps[i])] += len(data_arr[mask_index[sort_index][start_index[i]:start_index[i+1]][mask[3][sort_index][start_index[i]:start_index[i+1]]]])


                            # Time tracking
                            time_avg = (time_int*time_avg + time.time()-t0) / (time_int+1)
                            time_int += 1
                            if not silent and (time_int % (2)) == 0:
                                print(time.strftime('%H:%M:%S', time.gmtime())+f' Step {time_int/(2)} eta. {(event_max-time_int)*time_avg/60:.2f} min.')
                            
                # Clear data
                data.clear()

        hist_struct['edges'] = hist_struct['edges'] * TDC_res

        # Write to file
        f = open(write, 'w')
        f.write(json.dumps(hist_struct, cls=NumpyEncoder))
        f.close()

        print(time.strftime('%H:%M:%S', time.gmtime())+' Histogram updated')

        return hist_struct
    else:
        print(time.strftime('%H:%M:%S', time.gmtime())+' Couldn\t update histogram')
        return hist_struct
    
def load_parameters(runs, write=None, overwrite=False, silent = False, threshold=1000):
    
    # Boolean keys
    loaded_param_struct = False
    
    # Structures
    param_struct = {}

    if write != None:
        if not silent:
            print(time.strftime('%H:%M:%S', time.gmtime())+' Load Parameters')
        try:    
            if os.path.exists(write) and not overwrite:
                # Load Parameters
                f = open(write, 'r')
                param_struct = json.loads(f.read())
                f.close()
                loaded_param_struct = True
                if not silent:
                    print(time.strftime('%H:%M:%S', time.gmtime())+' Parameter JSON files found and read')
                return param_struct
        except:
            pass
    
    if not silent:
       print(time.strftime('%H:%M:%S', time.gmtime())+' Create Structs')

    if not loaded_param_struct:
        param_struct['flags'] = []
        param_struct['TDC.min'] = np.array([0])
        param_struct['TDC.max'] = np.array([1])
    
    # Loop over runs
    for run in runs:
        for filename in sorted(os.listdir(run[:run.rfind('/')])):
            if (run[run.rfind('/')+1:] in filename) and ('-dat-' in filename):
                
                # Load the needed keys
                data = load_dat_file(run[:run.rfind('/')+1]+filename, silent=silent)
                
                # Set default scan step
                scan_key = data['TCP_type']
                param_struct['scan_key'] = scan_key

                time_keys = []
                
                # check the keys
                for key in data.keys():
                    try:
                        # Dont add time to Parameters
                        if 'TDC1' in key:
                            time_keys.append(key)

                            # Check for min max values
                            min = np.min(flatten_list(data[key]))
                            max = np.max(flatten_list(data[key]))
                            
                            if min < param_struct['TDC.min'][0]:
                                param_struct['TDC.min'] = np.array([min])
                            if max > param_struct['TDC.max'][0]:
                                param_struct['TDC.max'] = np.array([max])
                        
                        # Add key to flags (parameters in the experiment) TODO fix check (TCP flag not always written)
                        elif (len(data[key]),len(data[key][0])) == (len(data['TCP_scan_step']),len(data['TCP_scan_step'][0])) and (isinstance(data[key][0][0],float) or isinstance(data[key][0][0],int)) and (key not in param_struct['flags']):
                            param_struct['flags'].append(key)
                            param_struct[key] = flatten_list(data[key])
                    
                        elif (len(data[key]),len(data[key][0])) == (len(data['TCP_scan_step']),len(data['TCP_scan_step'][0])) and (isinstance(data[key][0][0],float) or isinstance(data[key][0][0],int)):
                            param_struct[key] = np.concatenate((param_struct[key],flatten_list(data[key])))
                    except:
                        if key == 'Event' and (key not in param_struct['flags']):
                            param_struct['flags'].append(key)
                            param_struct[key] = np.array(data[key])
                    
                        elif key == 'Event':
                            param_struct[key] = np.concatenate((param_struct[key],np.array(data[key])))

                        elif key == 'Time' and 'Time' not in param_struct.keys():
                            param_struct[key] = np.array(data[key])
                        
                        elif key == 'Time':
                            param_struct[key] = np.concatenate((param_struct[key],np.array(data[key])))

                # Count
                # Add to histogram struct if it does not exist 
                if not loaded_param_struct:                    
                    for key in time_keys:
                        if 'count'+key[4:] not in param_struct.keys():
                            param_struct['flags'].append('count'+key[4:])
                            param_struct['count'+key[4:]] = np.array([np.sum(i) for i in data[key]])
                        else:
                            param_struct['count'+key[4:]] = np.concatenate((param_struct['count'+key[4:]], np.array([np.sum(i) for i in data[key]])))

                # Clear data
                data.clear()
    
    # Make masks for the different parameter keys
    if scan_key == 'Wavelength_ctr' or scan_key == 'Requested Transmission_ctr':
        param_struct['ADC.Laser_on'] = np.array(param_struct['ADC.Laser_flag']) > threshold
        param_struct['ADC.Laser_off'] = np.array(param_struct['ADC.Laser_flag']) <= threshold
    else:
        param_struct['ADC.Pump_on'] = np.array(param_struct['ADC.ChopperProbe']) < threshold
        param_struct['ADC.Pump_off'] = np.array(param_struct['ADC.ChopperProbe']) >= threshold
        param_struct['ADC.Probe_on'] = np.array(param_struct['ADC.ChopperPump']) < threshold
        param_struct['ADC.Probe_off'] = np.array(param_struct['ADC.ChopperPump']) >= threshold
    
    if write != None:
        
        if not loaded_param_struct:
            if not os.path.exists(write[:write.rfind('/')]):
                os.makedirs(write[:write.rfind('/')])
            
            # Write to file
            f = open(write, 'w')
            f.write(json.dumps(param_struct, cls=NumpyEncoder))
            f.close()

    print(time.strftime('%H:%M:%S', time.gmtime())+' Parameters created')

    return param_struct

def get_size(obj, seen=None):
    """Recursively finds size of objects"""
    size = sys.getsizeof(obj)
    if seen is None:
        seen = set()
    obj_id = id(obj)
    if obj_id in seen:
        return 0
    # Important mark as seen *before* entering recursion to gracefully handle
    # self-referential objects
    seen.add(obj_id)
    if isinstance(obj, dict):
        size += sum([get_size(v, seen) for v in obj.values()])
        size += sum([get_size(k, seen) for k in obj.keys()])
    elif hasattr(obj, '__dict__'):
        size += get_size(obj.__dict__, seen)
    elif hasattr(obj, '__iter__') and not isinstance(obj, (str, bytes, bytearray)):
        size += sum([get_size(i, seen) for i in obj])
    return size