import sys
import numpy as np
if sys.platform.startswith('win'):
    sys.path.append('../mathtools')
from mathtools.fit import *
from analysis import *
import pylab as plt
import seaborn as sns
import seaborn.xkcd_rgb as xkcd
from ipdb import set_trace as debug


def best_ylim(left, right):
    ''' Computes the best (shared) y axis limits between two plots.'''
    t = left['raw_t']
    t_idx = valid_range(t, 7.8, 10)
    dl = left['raw_d'][t_idx]
    dr = right['raw_d'][t_idx]
    max_left = max(dl)
    min_left = min(dl)

    max_right = max(dr)
    min_right = min(dr)

    ylm = [0, 0]
    ylm[0] = floor(min(min_right, min_left))
    ylm[1] = ceil(max(max_right, max_left))
    return ylm


def valid_range(vector, min_val, max_val):
    ''' Create indices in the given range.'''
    return nonzero( (vector>=min_val) * (vector<=max_val))[0]


def extract_plr_measurements(t, d):
    ''' Extract PLR measurements from (time, diameter) measurements.'''
    t_init = valid_range(t, 8.0, 8.5)
    d_ = d[t_init]
    d_init = max(d_)
    max_idx = argmax(d_) + t_init[0]
    t_max = t[max_idx]
    t_fill_to = t[max_idx]
    t_fill_idx = valid_range(t, 0.0 , t_fill_to)
    d[t_fill_idx] = d_init
    plt.plot(t,d)

    f = Fit(t, 100, basis_type='cubic-spline', reg_coefs=[0, 1e-2, 9e-3])
    r = f.fit(d)

    # Grab the latency time.
    t_lat_idx = valid_range(t, 8.0, 8.50)
    try:
        roc = 1/((2 + 1 + (r.dy)**2)**(3/2)/np.abs(r.d2y))
    except:
        roc = inf

    # Find the maximum curvature.
    max_curvature_idx = np.argmax(roc[t_lat_idx]) + t_lat_idx[0]
    min_curvature_idx = np.argmin(roc[t_lat_idx]) + t_lat_idx[0]
    min_curv_time = t[min_curvature_idx]

    # Actually shift left to 80% of the curvature peak.
    # This as a matter of definition.
    percent_max = 0.50 * roc[max_curvature_idx]
    t_max_curv = t[max_curvature_idx]
    t_lat_idx = valid_range(t, t_max_curv, 9.0)
    target = nonzero(roc[t_lat_idx]<= percent_max)[0] + t_lat_idx[0]
    max_curvature_idx = target[0]

    # Compute the latency.
    latency_in_ms = (r.x[max_curvature_idx] - 8.0) * 1000

    # Compute the constriction amplitude.
    t_end_idx = valid_range(t, 8.0, 16.0)
    starting_amplitude = r.y[t_end_idx[0]]
    min_amplitude = np.min(r.y[t_end_idx])
    min_idx = np.argmin(r.y[t_end_idx]) + t_end_idx[0]
    t_min = t[min_idx]
    amp_in_mm = starting_amplitude - min_amplitude

    # Compute average constriction velocity.
    ave_vel_in_mm_per_sec = amp_in_mm / (t_min - 8.0)

    # Find the 75% recovery time.
    t_after_min_idx = (t > t_min)
    t_after_min_idx = nonzero(t_after_min_idx)[0]
    threshold = starting_amplitude - 0.25 * amp_in_mm
    greater_than_75 = nonzero(r.y[t_after_min_idx] >=threshold)[0] + t_after_min_idx[0]
    if len(greater_than_75) == 0:
        recovery_idx = 0
        recovery_in_ms = 'N/A'
    else:
        recovery_idx = greater_than_75[0]
        recovery_in_ms = 1000*(t[recovery_idx] - 8.0)

    # Package up results.
    data = {}
    data['core'] = {}
    data['core']['latency_in_ms'] = round(latency_in_ms)
    data['core']['amp_in_mm'] = amp_in_mm
    data['core']['recovery_in_ms'] = recovery_in_ms
    data['core']['ave_vel_in_mm_per_sec'] = ave_vel_in_mm_per_sec
    data['indices'] = {}
    data['indices']['recovery'] = recovery_idx
    data['indices']['min'] = min_idx
    data['indices']['lat'] = max_curvature_idx
    data['fit'] = r
    data['raw_t'] = t
    data['raw_d'] = d

    # And we're done.
    return data


def plot_results(data, title='', ylm=None):
    r = data['fit']
    t = data['raw_t']
    lat = data['core']['latency_in_ms']
    recover_time = t[data['indices']['recovery']]
    t_idx = valid_range(t, 7.8, 10)
    plt.plot(r.x[t_idx], r.y[t_idx], linewidth=2)
    xlm = [7.5, 10]

    plt.xlim([7.8, xlm[1]])
    # plt.xlabel('Time (seconds)')
    # plot(data['t_fit'], data['d_fit'], '--', color=xkcd['deep red'])

    # Indicate latency.
    lat_strt = data['core']['latency_in_ms']/1000 + 8.0
    plot([8.0,8.0], [0,10], '-', color=xkcd['kelly green'], linewidth=3, \
            label='Flash')
    plot([lat_strt,lat_strt], [0,10], '-', color=xkcd['golden rod'], \
            linewidth=2, label='Latency: {:0.2f} ms'.format(lat))
    legend()
    plt.title(title)
    if ylm:
        plt.ylim(ylm)


def j6_analysis(data, scan):
    '''Process the raw data from the J6 scan'''
    scan_id = scan['_id']

    #  Extract raw pupil data.
    left, right = extract_pupil_data(data)

    # Extract left/right PLR parameters.
    data_left = extract_plr_measurements(left['t'], left['d'])
    data_right = extract_plr_measurements(right['t'], right['d'])
    ylm = best_ylim(data_left, data_right)

    # Plot this guy.
    plt.ioff()
    plt.close('all')
    plt.figure('PLR-SUMMARY')
    ax1 = plt.subplot('121')
    plot_results(data_left, title='LEFT EYE')

    plt.subplot('122', sharey=ax1)
    plot_results(data_right, title='RIGHT EYE', ylm=ylm)

    figname = '../dist/static/plots/{:s}.png'.format(scan_id)
    plt.savefig(figname)
    scan['left'] = data_left['core']
    scan['right'] = data_right['core']
    return scan


if __name__ == '__main__':

    # Load some example data!
    from mathtools.utils import Vessel
    data = Vessel('playground_3.dat')
    scan = j6_analysis(data.data, 'MJL_001')


