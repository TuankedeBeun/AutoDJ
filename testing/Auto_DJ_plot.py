#%% Import and parameters

import os
import subprocess
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import pydub
from scipy.fftpack import fft
from scipy.ndimage import gaussian_filter1d as gauss

os.chdir('C:/Users/tuank/Programming/Python/AutoDJ/testing')
musicFolderPath = 'C:/Users/tuank/Music/Drum & Bass/Drum & Bass 2/'
song = 'Maduk - Avalon (VIP)'

#%% Open & read song

def read_to_audiosegment(song):
    # reads mp3 file and converts it into pydub's AudioSegment datatype
    file = musicFolderPath + song + '.mp3'
    
    audiosegment = pydub.AudioSegment.from_mp3(file)
    return audiosegment

def audiosegment_to_nparray(audiosegment, normalized=False):
    audioNp = np.array(audiosegment.get_array_of_samples())
    audioNp = audioNp.reshape((-1, 2)).transpose()
    
    if normalized:
        audioNp = np.float32(audioNp) / 2**15
        
    time = np.linspace(0, audiosegment.duration_seconds, audioNp.shape[1])
    
    return time, audioNp

def get_properties(audiosegment):
    props = {
            'duration': audiosegment.duration_seconds,
            'audiorate': audiosegment.frame_rate,
            'max_possible': audiosegment.max_possible_amplitude
            }
    return props

#%% Make a spectral analysis (cumulative FFT) of music file
    
def fft_from_nparray(audioNp, audiorate, freq_low=20):
    # convert audio signal to Fourier by looking at the number of elements indicated by 'framesize'
    # outputs a 2D numpy array with time on the 0th axis and fft on the 1st
    
    # divide input signal into frames
    audioMono = np.sum(audioNp, axis=0)
    framesize = int(audiorate/freq_low)
    totalSize = audioMono.size
    Nframes = int(totalSize/framesize)
    audioReshaped = audioMono[:framesize*Nframes].reshape(Nframes, framesize)
    
    # do fft
    fft_signal = fft(audioReshaped)
    # discard upper half (mirroring)
    fft_signal = fft_signal[:, :(int(framesize/2))]
    # combine real and imaginary parts
    fft_signal = np.abs(fft_signal)
    
    # compute time array
    secondsPerFrame = framesize/audiorate
    time = np.arange(0, fft_signal.shape[0])*secondsPerFrame
    
    # compute frequency
    freq = freq_low*np.arange(fft_signal.shape[1])
    
    return time, freq, fft_signal

def calc_bass_mid_treb_from_fft(freq, fft_signal):
    pass

#%% plot some data over time

class Plotter():
    def __init__(self, time, data, description):
        self.Naxes = 0
        self.tdatasets = [time]
        self.ydatasets = [data]
        self.ytitles = [description]
        self.fig, axis = plt.subplots(1)
        self.axes = [axis]
        
    def add_plot(self, time, data, description):
        self.Naxes += 1
        self.axes = self.fig.subplots(nrows=self.Naxes, ncols=1, sharex=True)
        self.tdatasets.append(time)
        self.ydatasets.append(data)
        self.ytitles.append(description)
        
    def draw_plots(self, t_range=None):
        for axis, tdata, ydata, ytitle in zip(self.axes, self.tdatasets, self.ydatasets, self.ytitles):
            axis.clear()
            axis.set(ylabel = ytitle)
            axis.set_title(ytitle)
            
            if t_range:
                index_left = int(np.argwhere(tdata > t_range[0])[0])
                index_right = int(np.argwhere(tdata > t_range[1])[0])
                axis.plot(tdata[index_left: index_right],
                          ydata[index_left: index_right])
            else:
                axis.plot(tdata, ydata)
            
        axis.set(xlabel='time (s)')
        self.fig.show()

#%% animation func

class Animation_plotter():
    def __init__(self, time, xdata, ydata, xlabel, ylabel):
        self.fig = plt.figure()
        self.ax = self.fig.add_subplot(1,1,1)
        self.time = time
        self.xdata = xdata
        self.ydata = ydata
        self.single_plot(0)
        self.ax.set(xlabel=xlabel, ylabel=ylabel)
        self.textcoords = (0.9*self.xdata.max(), 0.9*self.ydata.max())
        
    def play(self):
        animation.FuncAnimation(self.fig, self.single_plot, interval=15)
        plt.show()
    
    def single_plot(self, i):
        self.ax.clear()
        self.ax.text(self.textcoords[0], self.textcoords[1], 'time: %.1f s' % self.time[i])
        self.ax.plot(self.xdata[i], self.ydata[i])
        self.ax.set_ylim(0,6e6)
