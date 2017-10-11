import re
from numpy import *
from ipdb import set_trace as dbg


def xml_to_time(data):
    time_array = array([])
    time_rgx = r'TIME="\d+\.*\d*"'
    times = re.findall(time_rgx, data)
    for t in times:
        f = grab_float(t)
        if t:
            time_array = append(time_array, f) 
    if len(time_array)>0: 
        return median(time_array)    
    else: 
        return -1    

def parse_data(data):
    # Scan the XML to extract what we want.
    obs = []
    for line in data:
        d = data_dict()
        time_rgx = r'TIME="\d+\.*\d*"'
        left_rgx = r'LPUPILD="\d+\.*\d*"'
        right_rgx = r'RPUPILD="\d+\.*\d*"'
        lposx_rgx = r'LEYEX="\d+\.*\d*"'
        lposy_rgx = r'LEYEY="\d+\.*\d*"'
        rposx_rgx = r'REYEX="\d+\.*\d*"'
        rposy_rgx = r'REYEY="\d+\.*\d*"'
        d['left']['diameter'] = re.findall(left_rgx, line)
        d['right']['diameter'] = re.findall(right_rgx, line)
        d['time'] = re.findall(time_rgx, line)
        d['left']['x'] = re.findall(lposx_rgx, line)
        d['left']['y'] = re.findall(lposy_rgx, line)
        d['right']['x'] = re.findall(rposx_rgx, line)
        d['right']['y'] = re.findall(rposy_rgx, line)
        obs.append(d)
    return obs


def data_dict():
    data = {}
    data['time'] = []
    data['left'] = {}
    data['right'] = {}
    data['left']['x'] = []
    data['left']['y'] = []
    data['left']['diameter'] = []
    data['right']['x'] = []
    data['right']['y'] = []
    data['right']['diameter'] = []
    return data


def grab_float(string):
    # Extract a float in quotation marks.
    rgx = r'\d+\.*\d*'
    try:
        return float(re.findall(rgx, string)[0])
    except:
        return None
    

def generate_time_series(obs):
    
    # Loop through the parsed data to create a time series.
    data = data_dict()
    outer = ['right', 'left']
    inner = ['x', 'y', 'diameter']

    for el in obs:

        # Eye measurements.
        for out in outer:
            for inn in inner:
                try:
                    f = grab_float(el[out][inn][0])
                except:
                    f = -1
                if f: data[out][inn].append(f)

        # Time.
        try:
            f = grab_float(el['time'][0])
        except:
            f = -1
        if f: data['time'].append(f)


    # And we are done.
    return data

