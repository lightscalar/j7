import numpy as np
from ipdb import set_trace as debug
import pylab as plt
import seaborn as sns
from seaborn import xkcd_rgb as xkcd

def orange(a,b):
    '''One-indexed range.'''
    return list(range(a,b+1))


def taut_string(sig, epsilon):
    '''Implementation of the taut string filter.'''
    n = sig.shape[0]; a = np.concatenate((np.array([sig[0]]), sig))
    lmbda = 2 * epsilon
    b = np.zeros(n+1)
    c = np.zeros(n+1)
    i_max = 1
    i_min = 1
    for i in orange(2,n): # L1
        if a[i] > a[i_min]:
            i_min = i 
            if (a[i] > (a[i_max] + lmbda)): # L1: if_1
                i = i_max
                c[i] = -1
                for j in orange(1,i): # L1: if_2
                    b[j] = a[i_max]+lmbda
                # end L1: if_2
                break
            # end L1: if_1
        elif a[i] < a[i_max]: # L1: elif_1 
            i_max = i
            if (a[i_min] > a[i] + lmbda):
                i = i_min
                c[i] = 1
                for j in orange(1,i):
                    b[j] = a[i_min]
                # end for
                break
            # end if
        # end if
    # end for
    if (i < (n-1)):
        max_slope = a[i+1] + lmbda - b[i]
        min_slope = a[i+1] - b[i]
        j_max = i+1
        j_min = i+1
        j = i + 2
        while j <= n:
            new_max_slope = (a[j] + lmbda - b[i])/(j-i)
            new_min_slope = (a[j] - b[i])/(j-i)
            if new_max_slope<max_slope:
                max_slope = new_max_slope
                j_max = j
                if max_slope < min_slope:
                    for k in orange(i+1, j_min):
                        b[k] = (b[i]*(j_min-k) + a[j_min] * (k-i))/(j_min-i)
                    # end for
                    i = j_min
                    c[i] = 1
                    j_min = i+1
                    j_max = i+1
                    max_slope = a[i+1] + lmbda - b[i]
                    min_slope = a[i+1] - b[i]
                    j = i+1
                # end if
            # end if
            if (j>(i+1)) and (new_min_slope>min_slope):
                min_slope = new_min_slope
                j_min = j
                if min_slope > max_slope:
                    for k in orange(i+1,j_max):
                        b[k] = (b[i] * (j_max-k) + (a[j_max]+lmbda)*(k-i))/(j_max-i)
                    # end for
                    i = j_max
                    c[i] = -1
                    j_min = i+1
                    j_max = i+1
                    max_slope = a[i+1] + lmbda - b[i]
                    min_slope = a[i+1] - b[i]
                    j = i+1
                # end if
            # end if
            j = j+1
        if j == n+1:
            if max_slope < 0:
                for k in orange(i+1, j_max):
                    b[k] = (b[i] * (j_max-k) + (a[j_max]+lmbda)*(k-i))/(j_max-i)
                # end for
                i = j_max
                c[i] = -1
                if j_max<n:
                    j_min = i+1
                    j_max = i+1
                    max_slope = a[i+1]+lmbda - b[i]
                    min_slope = a[i+1] - b[i]
                    j = i+1
                # end if
            elif min_slope>0:
                for k in orange(i+1,j_min):
                    b[k] = (b[i]*(j_min-k) + a[j_min]*(k-i))/(j_min-i)
                # end for
                i = j_min
                c[i] = 1
                if j_min < n:
                    j_min = i+1
                    j_max = i+1
                    max_slope = a[i+1]+lmbda - b[i]
                    min_slope = a[i+1]-b[i]
                    j = i + 1
                # end if
            else:
                for k in orange(i+1,n):
                    b[k]=b[i]
                # end for
                j = n+1
            # end if
        # end if
    # end if
    b = b[1:]
    a = a[1:]
    b = b - np.sum(b-a)/n
    return b
# end function

        
if __name__ == '__main__':

    sns.set_context('talk')
    t = np.linspace(0,4*np.pi,1000)
    sig = np.sin(2 * np.pi* t/1.5)
    sig += np.sin(2 * np.pi * t/1.2)**2 + 0.00*np.random.randn(len(t))
    b = taut_string(sig, 0.1)

    plt.close('all')
    plt.ion()
    plt.figure(100, figsize=(15,5))
    plt.plot(t, sig, '.', alpha=0.5)
    plt.grid(True)
    plt.plot(t, b)
    plt.xlim(0, 4*np.pi)
    plt.title('Taut String Example')

    # plt.figure(200)
    # plt.plot(t, sig - b)

