import sys
sys.path.append('../mathtools/')
from mathtools.fit import *
from mathtools.vanity import *
from mathtools.utils import Vessel
from numpy import *
from ipdb import set_trace as debug
from pylab import semilogy


def extract_pupil_data(data):
    t = array(data['time'])
    rd = array(data['right']['diameter'])
    ld = array(data['left']['diameter'])
    ridx = (t>=0) * (rd>0)
    lidx = (t>=0) * (ld>0)

    tr = t[ridx] - min(t[ridx])
    tl = t[lidx] - min(t[lidx])
    right_pupil = rd[ridx] * 1000
    left_pupil = ld[lidx] * 1000
    left = {}
    right = {}
    left['t'] = tl
    left['d'] = left_pupil
    right['t'] = tr
    right['d'] = right_pupil

    return (left, right)


def process_raw_data(data, scan_id):

    # Process the raw scanner data.
    t = array(data['time'])
    rd = array(data['right']['diameter'])
    ld = array(data['left']['diameter'])
    ridx = (t>=0) * (rd>0)
    lidx = (t>=0) * (ld>0)

    tr = t[ridx] - min(t[ridx])
    tl = t[lidx] - min(t[lidx])
    right_pupil = rd[ridx] * 1000
    left_pupil = ld[lidx] * 1000

    # filepath = 'scan_plots/'
    filepath = './scan_plots'
    # filepath = '../aperture/public/scan_plots/'
    file_right = filepath + scan_id + '_right.png'
    file_left = filepath + scan_id + '_left.png'

    left_summary = analyze_standard_scan(tl, left_pupil, filename=file_left)
    right_summary = analyze_standard_scan(tr, right_pupil, filename=file_right)

    return left_summary, right_summary


def knee_finder(x,y):

    lx = len(x)
    knee_positions = arange(10, lx-10)
    penalty = []
    for k, kp in enumerate(knee_positions):

        x1 = x[:kp]
        y1 = y[:kp]
        x2 = x[kp:]
        y2 = y[kp:]

        p1 = polyfit(x1,y1,1)
        p2 = polyfit(x2,y2,1)
        
        penalty.append(sum( (y1 - polyval(p1, x1))**2) + sum((y2 - polyval(p2, x2))**2 ))

    return x[knee_positions], penalty


def find_max_slope(x,y,start_x,end_x):

    test_range = nonzero((x>start_x) & (x<end_x))[0]
    min_slope = 0
    x_star = None
    slopes = []
    for midpt in test_range:
        xt = x[midpt-10:midpt+10]
        yt = y[midpt-10:midpt+10]
        p = polyfit(xt,yt,1)
        slopes.append((x[midpt], p[0])) 
        if p[0] < min_slope:
            x_star = x[midpt]
            min_slope = p[0]
    return (slopes, min_slope, x_star)


def analyze_standard_scan(t, y, filename='latest_run.png'):

    # Compute a regularized fit of the data.
    f = Fit(t, 100, basis_type='cubic-spline', reg_coefs=[0, 1e-3, 5e-3])
    r = f.fit(y)
    
    
    # Extract the relevant region.
    idx = (r.x>7.5) * (r.x<10.0)
    ft = r.x[idx]
    fd = r.y[idx] 
    if True:
        ignition = argmin( abs(ft-8.0))
        init_period = (ft>=8.0) * (ft<8.5)
        maxval = max(fd[init_period])
        pt = argmin( abs(fd - maxval))
        fd[ft<ft[pt]] = maxval

    # Find the maximum constriction speed.
    slopes, min_slope, max_vel = find_max_slope(ft, fd, 8, 10)

    # Here is position of maximum constriction velocity.
    mvidx = argmin( abs(max_vel - ft) )

    # For now, we define latency as time required to achieve 70% of maximum constriction speed.
    # for slp in slopes:
    #     if slp[1]/min_slope >= 0.70:
    #         latency = slp[0] - 8.0
    #         break

    # Find the constriction amplitude.
    min_time = ft[argmin(fd)]
    med_start_ampl = median(fd[(ft>7.5) * (ft<8.0)])
    min_ampl = min(fd)
    amplitude = med_start_ampl - min_ampl

    # Estimate the 75% recovery time.
    recovery_amplitude = min_ampl + 0.75 * amplitude
    recovery_idx = nonzero((ft > min_time) * (fd >= recovery_amplitude))[0]
    try:
        recovery_time = ft[recovery_idx[0]]
    except:
        recovery_time = 9.6
    time_to_recovery = recovery_time - 8.0

    # Compute constriction start time.
    # constriction_start = 8.0 + latency
    kidx = (r.x>7.5) * (r.x<ft[mvidx])
    kt = r.x[kidx]
    kd = r.y[kidx]
    kp, s = knee_finder(kt, kd)
    constriction_start = kp[argmin(s)]
    latency = constriction_start - 8.0

    # Plot the processed trace.
    setup_plotting()
    ioff()
    figure('Standard Eye Scan', figsize=(13,7))
    # plot(t,d,'.',color=asbestos)
    plot(ft,fd,'-',linewidth=4)
    yl = ylim()
    plot([8,8], yl, '--', color=alizarin, linewidth=5)
    xlim([7.5,10])
    grid(True)

    # Plot the 75% recovery time.
    plot([recovery_time, recovery_time], yl, '--', color=emerald, linewidth=5)

    # Plot the point of maximum constriction velocity.
    plot(ft[mvidx], fd[mvidx], 'o', markersize=12) 
    plot([constriction_start, constriction_start], yl, '--', color=pumpkin, linewidth=4)

    # Plot the maximum velocity fit.
    st = ft[mvidx-10:mvidx+10]
    stt = ft[mvidx-25:mvidx+25]
    sd = fd[mvidx-10:mvidx+10]
    p = polyfit(st, sd, 1)
    y_fit = polyval(p, stt)
    plot(stt, y_fit, '--', linewidth=4, color=wet_asphalt)

    # Add title to the plot.
    # title('Latency: {0:.2f} ms; Amplitude is {1:.2f}; 
    # Velocity: {2:.2f}'.format(latency*1000, amplitude, p[0]))
    # grid(True)
    ylim(yl)
    xlabel('Time (seconds)')
    ylabel('Pupil Diameter (mm)')
    savefig(filename)

    # ion()
    # figure(200)
    # plot(kp, s)

    # Package up all the data.
    data = {}
    data['latency'] = latency*1000
    data['constriction_amplitude'] = amplitude
    data['time_to_recovery'] = time_to_recovery
    data['constriction_velocity'] = p[0]
    return data

            
if __name__ == '__main__':

    v = Vessel('scan.dat')
    t = v.t
    y = v.d * 1000
    data = analyze_standard_scan(t, y)
    

