#%% Import and parameters
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import pydub
from scipy.fftpack import fft

#%% Open & read song, get simple properties
class AudioReader():
    def __init__(self, song_directory, song_title):
        if(not (song_directory.endswith('\\') or song_directory.endswith('/'))):
            song_directory += '/'
        
        self.directory = song_directory
        self.song = song_title
        self.audiosegment = self.load_song(song_title)
    
    def load_song(self, song):
        # reads mp3 file and converts it into pydub's AudioSegment datatype
        song_path = self.directory + self.song + '.mp3'
        audiosegment = pydub.AudioSegment.from_mp3(song_path)
        return audiosegment
    
    def to_nparray(self, normalized=False):
        audio_np = np.array(self.audiosegment.get_array_of_samples())
        audio_np = audio_np.reshape((-1, 2)).transpose()
        
        if normalized:
            audio_np = np.float32(audio_np) / 2**15
            
        time = np.linspace(0, self.audiosegment.duration_seconds, audio_np.shape[1])
        
        self.time_np = time
        self.audio_np = audio_np
        return time, audio_np
    
    def get_properties(self):
        props = {
                'duration': self.audiosegment.duration_seconds,
                'audiorate': self.audiosegment.frame_rate,
                'max_possible': self.audiosegment.max_possible_amplitude
                }
        return props
    
    def get_fft(self, freq_low=20):
        # convert audio signal to Fourier by looking at the number of elements indicated by 'framesize'
        # outputs a 2D numpy array with time on the 0th axis and fft on the 1st
        
        time, audio_np = self.to_nparray()
        props = self.get_properties()
        
        # divide input signal into frames
        audioMono = np.sum(audio_np, axis=0)
        framesize = int(props['audiorate']/freq_low)
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
        secondsPerFrame = framesize/props['audiorate']
        time = np.arange(1, fft_signal.shape[0]+1)*secondsPerFrame
        
        # compute frequency
        freq = freq_low*np.arange(fft_signal.shape[1])
        
        return time, freq, fft_signal
    
    def get_bass_mid_treb(self):
        time, freq, fft_signal = self.get_fft()
        
        bass = np.sum((freq < 300) * fft_signal, axis=1)
        middle = np.sum((freq >= 300) * (freq < 4000) * fft_signal, axis=1)
        treble = np.sum((freq >= 4000) * fft_signal, axis=1)
        return time, bass, middle, treble
    

#%% plot some data over time

class Plotter():
    def __init__(self, figsize=(18,9)):
        self.Naxes = 0
        self.tdatasets = []
        self.ydatasets = []
        self.ytitles = []
        self.fig = plt.figure(figsize=figsize, 
                              facecolor='#333333',
                              clear=True)
        
    def add_plot(self, time, data, description):
        self.Naxes += 1
        self.axes = []
        self.axes.append(self.fig.subplots(nrows=self.Naxes, ncols=1, sharex=True))
        self.tdatasets.append(time)
        self.ydatasets.append(data)
        self.ytitles.append(description)
        
    def draw_plots(self, t_range=None):
        for axis, tdata, ydata, ytitle in zip(self.axes, self.tdatasets, self.ydatasets, self.ytitles):
            axis.clear()
            axis.set_ylabel(ytitle, fontsize=20, color='w')
            axis.set_facecolor('#111111')
            axis.tick_params(axis='both', colors='w', labelsize=15)
            for spine in axis.spines: axis.spines[spine].set_color('w')
            
            if t_range:
                index_left = int(np.argwhere(tdata > t_range[0])[0])
                index_right = int(np.argwhere(tdata > t_range[1])[0])
                axis.plot(tdata[index_left: index_right],
                          ydata[index_left: index_right],
                          linewidth=2)
            else:
                axis.plot(tdata, ydata)
            
        axis.set_xlabel('time (s)', fontsize=20, color='w')
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
