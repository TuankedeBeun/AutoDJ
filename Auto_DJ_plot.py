#%% Import and parameters

import os
import subprocess
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import pydub
from scipy.fftpack import fft
from scipy.ndimage import gaussian_filter1d as gauss
import time

os.chdir('C:/Users/tuank/Music/Drum & Bass/Drum & Bass 2')
song = 'Maduk - Avalon (VIP)' 

#%% Open song from mp3 to numpy array

def Read(song, normalized=False):
    #reads mp3 file and converts it into numpy string
    #output is (rate, (left, right))
    #rate indicates the amount of elements read per second
    
    file = song + '.mp3'
    
    audio_f = pydub.AudioSegment.from_mp3(file)
    audio = np.array(audio_f.get_array_of_samples())
    if audio_f.channels == 2:
        audio = audio.reshape((-1, 2)).transpose()
    if normalized:
        audio = np.float32(audio) / 2**15
    return audio_f.frame_rate, audio

#%% Make a spectral analysis (cumulative FFT) of music file
    
def FFT(signal, audiorate, overlap=0, freq_low=20):
    #convert audio signal to Fourier by looking at the number of elements
    #indicated by 'chunksize'
    #the output is a 2D numpy array of size 'Number of frames x '
    
    chunksize = int(audiorate/freq_low)
    N = signal.size
    Nframes = int(N/chunksize)
    signal_fft = np.zeros((Nframes, int(chunksize/2)))
    
    #!!! maybe possible to do all segments at once (so without for-loop)
        
    for i in range(Nframes):
        segment = signal[chunksize*i:int(chunksize*(i + 1 + overlap))] #!!!
        segment_fft = fft(segment) #fft
        segment_fft = segment_fft[:int(chunksize/2)] #discard upper half (mirroring)
        signal_fft[i] = np.abs(segment_fft) #combine real and imaginary parts
    
    ##blurr signal in time
    #signal_fft = gauss(signal_fft, t_smooth, axis=0)
    
    #rescale to a scale from about 0 to 255
    #norm = 0.1*np.average(signal_fft)
    #signal_256 = np.clip(signal_fft/norm, 0, 255)
    
    #return np.uint8(signal_256)
    
    return signal_fft


#%% animation func
    
def animate(i):
    ax1.clear()
    global start, end
    if i == 0:
        start = time.time()
    elif i == 99:
        end = time.time()
    elif i > 99:
        ax1.text(1e4, 4e6, 'function takes %.3f seconds to run' % ((end-start)/100))
    
    ax1.text(1.5e4, 5e6, '%.1f s' % (i/fft_rate))
    ax1.plot(freqs[:1000],fft_temp[i%5500,:1000])
    plt.ylim(0,6e6)
    


#%% Run

start = end = 0
    
audiorate, (left,right) = Read(song)
fft_temp = FFT(left+right, audiorate)
Nframes, Nfreq = np.shape(fft_temp)
fft_rate = Nframes/275

if False:
    #plot audosignal
    playtime = np.arange(len(left))/audiorate/60
    plt.plot(playtime, left+right)
    plt.ylim(0,6e3)

if True:
    #plot fft signal
    #create axes
    fig = plt.figure()
    ax1 = fig.add_subplot(1,1,1)
    freqs = np.arange(Nfreq)*20
    
    ani = animation.FuncAnimation(fig, animate, interval=15 )
    plt.show()


