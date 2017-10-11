import sys
sys.path.append('../mathtools')
from mathtools.utils import Vessel
from mathtools.fit import *
from processor import *
from gazepoint_parser import *
import pylab as plt
from taut_string import taut_string


def q(statement):
    # Return array indices where statement is true
    return nonzero(statement)[0]


def retrieve_series(package):
    # Return time, diameters, etc.
    flash_time = package[0]
    raw_flash_time = flash_time[1]
    raw_data = package[1]
    obs = parse_data(raw_data)
    tser = generate_time_series(obs)
    t = np.array(tser['time'])
    t = t - raw_flash_time + 1.0
    left = np.array(tser['left']['diameter'])
    right = np.array(tser['right']['diameter'])
    idx = q(t>0)
    t = t[idx]
    left = left[idx] * 1000
    right = right[idx] * 1000
    t_start = t.min()
    t -= t_start
    left = taut_string(left, 0.01)
    right = taut_string(right, 0.01)
    flash_time = flash_time[1] - t_start
    return t, flash_time, left, right


def extrema_in_range(t, v, mint, maxt):
    # Find time, index, and value.
    idx = q( (t>mint) * (t<maxt))
    t_ = t[idx]
    v_ = v[idx]
    idx_max = np.argmax(v_)
    idx_min = np.argmin(v_)
    t_min = t_[idx_min]
    t_max = t_[idx_max]
    v_max = v_.max()
    v_min = v_.min()
    idx_max += idx.min()
    idx_min += idx.min()
    return idx_min, idx_max, t_min, t_max, v_min, v_max


def process_raw_data(package, scan):
    # Process data to extract PLR parameters.
    flash_time = package[0]
    raw_data = package[1]
    scan['flash_time'] = flash_time[1]
    s = Vessel('data/raw/{}.dat'.format(scan['_id']))
    # Don't save raw data to database; save to Vessel on disk.
    s.raw_data = raw_data
    s.flash_time = flash_time[1]
    s.save()
    # Save diagnostic info on last scan.
    v = Vessel('diagnostics.dat')
    v.package = package
    v.scan = scan
    v.save()

    try:
        # Parse the raw data; extract time series.
        obs = parse_data(raw_data)
        tser = generate_time_series(obs)
        t = np.array(tser['time'])
        left = np.array(tser['left']['diameter'])
        right = np.array(tser['right']['diameter'])
        scan['left'] = extract_plr(t, left, flash_time, scan_id=scan['_id'], \
                which_eye='LEFT')
        scan['right'] = extract_plr(t, right, flash_time, scan_id=scan['_id'], \
                which_eye='RIGHT')
        scan['isSuccess'] = True
    except:
        print('Data Processing of Scan Failed')
        scan['isSuccess'] = False

    return scan


def extract_plr(t, dr, flash_time, scan_id='1234', which_eye='LEFT'):
    # Extract PLR parameters from provided time series.
    flash_time = flash_time[1]
    t = t - (flash_time - 1)
    flash_time = 1.0

    # Find valid points
    idx = q(t>0)
    t = t[idx]
    dr = dr[idx] * 1000
    t_start = t.min()
    t -= t_start
    dr = taut_string(dr, 0.01)
    
    # Fit with cubic splines
    t_mn = 0
    t_mx = 5

    idx = q( (t>t_mn) * (t<t_mx))
    t_ = t[idx]
    dr_ = dr[idx]
    f = Fit(t_, 100, basis_type='cubic-spline', reg_coefs=[0, 1e-2, 9e-3])
    r = f.fit(dr_)

    # Grab the latency time.
    try:
        roc = 1/((2 + 1 + (r.dy)**2)**(3/2)/np.abs(r.d2y))
    except:
        roc = inf

    roc = taut_string(roc, 0.10)
    g = Fit(t_, 100, basis_type='cubic-spline', reg_coefs=[0, 1e-2, 1e-3])
    rc = g.fit(roc)
    roc = rc.y


    peaks = []
    for itr, val in enumerate(roc):
        if (itr<1) or (itr==len(roc)-1):
            continue
        if val > roc[itr-1] and (val > roc[itr+1]):
            peaks.append(t_[itr])

    # Light flash time.
    closest_index = np.abs(r.x - flash_time)
    flash_idx = np.argmin(closest_index)

    # Starting amplitude.
    starting_amplitude = r.y[flash_idx]

    # Find the peak in the curvature.
    peaks = np.array(peaks)
    peaks -= flash_time
    peaks = peaks[peaks>0.150]
    peak_time = peaks[0] + flash_time
    med_amplitude = np.median(dr_)
    std_amplitude = dr_.std()
    roc -= mean(roc)
    roc = roc * roc.std() * std_amplitude/2
    roc += med_amplitude
    latency = peak_time - flash_time
    print('Latency is {:0.3f}'.format(latency))

    # Minimum amplitude.
    idx_min, idx_max, t_min, t_max, v_min, v_max =\
            extrema_in_range(r.x, r.y, t_mn, t_mx-2)
    minimum_amplitude = v_min
    minimum_time = t_min
    delta_amplitude = starting_amplitude - minimum_amplitude
    average_speed = (delta_amplitude)/(minimum_time - flash_time)

    # Find the recovery time.
    recovery_amplitude = 0.75 * delta_amplitude + minimum_amplitude
    idx_after_min = q(t>minimum_time)
    t_after_min = t[idx_after_min]
    amp_after_min = dr[idx_after_min]
    recovery_idx = q(amp_after_min >= recovery_amplitude)[0]
    if recovery_idx:
        recovery_time = t_after_min[recovery_idx] - flash_time
        time_of_recovery = t_after_min[recovery_idx]
    else:
        recovery_time = -1
        time_of_recovery = 5

    package = {}
    package['latency'] = latency
    package['starting_diameter'] = starting_amplitude
    package['minimum_diameter'] = minimum_amplitude
    package['absolute_diameter_change'] = delta_amplitude
    package['relative_diameter_change'] = delta_amplitude/starting_amplitude
    package['average_speed'] = average_speed
    package['recovery_time'] = recovery_time

    plt.ioff()
    plt.close('all')
    plt.plot(r.x, r.y, color='#c62828', linewidth=3)
    plt.plot(t_, roc, color='#305580', linewidth=3, alpha=0.5)
    y_lim = plt.ylim([med_amplitude-3*std_amplitude, med_amplitude + 2*std_amplitude])
    plt.plot([0, 5], [starting_amplitude, starting_amplitude], ':', color='#2f2f2f')
    plt.plot([0, 5], [minimum_amplitude, minimum_amplitude], ':', color='#2f2f2f')
    plt.plot([time_of_recovery, time_of_recovery], [0, 20], '--', color='#c62828')
    plt.plot([flash_time, flash_time], [0, 20], '--', color='#000000')
    plt.plot([peak_time, peak_time], [0, 20], '--', color='#4caf50')
    plt.xlim([t_mn, t_mx])
    plt.xlabel('Time (Seconds)')
    plt.ylabel('Pupil Diameter (mm)')
    location = './plots'
    plt.savefig('{}/{}_{}.png'.format(location, scan_id, which_eye))
    return package


if __name__ == '__main__':
    from pylab import *
    ion()
    close('all')

    # Run diagnostics on the last scan run.
    diagnostics = Vessel('diagnostics.dat')
    package = diagnostics.package
    diagnostics.scan['_id'] = 'DIAGNOSTICS'
    scan = diagnostics.scan
    scan = process_raw_data(package, scan)
    t, ft, left, right = retrieve_series(package)
