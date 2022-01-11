import numpy as np
import pydub
from scipy.fftpack import fft

def to_nparray(audiosegment, normalized=False):
    audio_np = np.array(audiosegment.get_array_of_samples())
    audio_np = audio_np.reshape((-1, 2)).transpose()
    
    if normalized:
        audio_np = np.float32(audio_np) / 2**15
        
    time = np.linspace(0, audiosegment.duration_seconds, audio_np.shape[1])
    return time, audio_np

def segment_section(audiosegment, start, end):
    #return slice of audiosignal indicated by start and end in seconds
    segment = audiosegment[start*1000: end*1000]
    return segment

def audio_np_section(audiosegment, start, end):
    #return slice of audiosignal indicated by start and end in seconds
    audiosegment_section = segment_section(audiosegment, start, end)
    t, audio_np_section = to_nparray(audiosegment_section)
    return audio_np_section

class AudioReader():
    def __init__(self, song_directory, song_title):
        if(not (song_directory.endswith('\\') or song_directory.endswith('/'))):
            song_directory += '/'
        
        self.directory = song_directory
        self.song = song_title
        self.audiosegment = self.load_song(song_title)
    
    def load_song(self, song):
        # reads mp3 file and converts it into pydub's AudioSegment datatype
        song_path = self.directory + self.song
        if(not song_path.endswith('.mp3')):
            song_path += '.mp3'
        audiosegment = pydub.AudioSegment.from_mp3(song_path)
        return audiosegment
    
    def get_fft(self, freq_low=20):
        # convert audio signal to Fourier by looking at the number of elements indicated by 'framesize'
        # outputs a 2D numpy array with time on the 0th axis and fft on the 1st
        
        time, audio_np = to_nparray(self.audiosegment)
        
        # divide input signal into frames
        audioMono = np.sum(audio_np, axis=0)
        framesize = int(self.audiosegment.frame_rate/freq_low)
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
        secondsPerFrame = framesize/self.audiosegment.frame_rate
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
    
