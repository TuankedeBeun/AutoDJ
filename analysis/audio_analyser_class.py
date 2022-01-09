#%% Import and parameters

import os
import numpy as np
import matplotlib.pyplot as plt
import pydub
from pydub.effects import low_pass_filter, high_pass_filter
from scipy.signal import find_peaks, gaussian

### Revised version ###

def Power_history_res(signal, audiorate, clustertime, resolution=None):
    # calculate the power history with a resolution
    blocksize = int(clustertime*audiorate)
    signal_squared = signal**2
    
    if(resolution):
        res_size = int(resolution*audiorate)
        Nblocks = int((np.size(signal) - blocksize)/res_size)
        unsummed = np.zeros((Nblocks, blocksize))
        
        for block in range(Nblocks):
            start = res_size*block
            end = res_size*block + blocksize
            section = signal_squared[start: end]
            section_weighted = gaussian(blocksize, int(blocksize/2))*section
            unsummed[block] = section_weighted
        
    else:
        Nblocks = int(np.size(signal)/blocksize)
        unsummed = signal_squared[:blocksize*Nblocks].reshape(Nblocks, blocksize)
    
    power_hist = np.sum(unsummed, axis=1)
    power_hist = np.ravel(power_hist)
    
    return power_hist