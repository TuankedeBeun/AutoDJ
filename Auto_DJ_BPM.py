#%% Import and parameters

import os
import numpy as np
import matplotlib.pyplot as plt
import pydub
from pydub.effects import low_pass_filter, high_pass_filter
from scipy.signal import find_peaks

#song = 'Makoto - YGMYC' #75 BPM = 87.1/174.2
#song = 'Maduk - How Could You' #69 BPM = 86.8/173.6
#song = 'Boxplot - Clouds Rest' #8 BPM = 87.3/174.6
#song = 'GLXY - Empty Love (Orig. Submotion Orchestra)' #43 BPM = 86.6/173.2
#song = 'NCT - Move On' #90 BPM = 87/174
#song = 'Matrix & Futurebound - Magnetic Eyes' #77 BPM = 87/174
#song = songs[77] #magnetic eyes

#%% Open song from mp3 to numpy array

def Read(song):
    #reads mp3 file and converts it into numpy string
    #output is (audiorate [Hz], signal [normalized], sample [lpf])
    
    if song[-4:] != '.mp3':
        song = song + '.mp3'
    
    audio_AS = pydub.AudioSegment.from_mp3(song) #open audiofile from mp3
    
    audio = np.array(audio_AS.get_array_of_samples()) #convert audio to numpy array
    if audio_AS.channels == 2:
        audio = audio.reshape((-1, 2)).transpose() #split stereo channels
        audio = audio[0,:] #!!! for now take only left channel
    audio = np.float32(audio) / 2**15 #normalize
    
    return song, audio, audio_AS, audio_AS.frame_rate


def Take_sample(signal, audiorate, start, end):
    #return slice of audiosignal indicated by start and end in seconds
    
    start = int(audiorate*start) #convert to array element
    end = int(audiorate*end)
    segment = signal[start:end] #slice sample segment
    
    return segment

def To_numpy(audio_AS):
    #convert to numpy array
    segment = np.array(audio_AS.get_array_of_samples()) #convert audio to numpy array
    if audio_AS.channels == 2:
        segment = segment.reshape((-1, 2)).transpose() #split stereo channels
        segment = segment[0,:]
    segment = np.float32(segment) / 2**15 #normalize
    
    return segment
    
#%% Processing functions for BPM

def Power_history(signal, audiorate, clustertime):
    # calculate the power history
    blocksize = int(clustertime*audiorate)
    Nblocks = int(np.size(signal)/blocksize)
    signal = signal[:blocksize*Nblocks].reshape(Nblocks, blocksize)
    power_hist = np.sum(signal**2, axis=1)
    power_hist = np.ravel(power_hist)
    
    return power_hist

def Droptime(signal, audiorate, clustertime):
    # detect start and end of the drop by first calculating the accumulative
    # power per 4 beats (~1.4s) and then looking where this value is suddenly
    # higher, above a threshold (upper 50 percentile).
    
    # clustertime is the length of power history block in seconds
    power_hist = Power_history(signal, audiorate, clustertime)
    
    # compute power threshold by taking 90% of highest 20% Power History
    P_thres = 0.9*np.percentile(power_hist, 80)
    
    # find index of start and end of first drop 
    power_thresh1 = power_hist > P_thres
    drop_start = np.argmax(power_thresh1)
    
    # find end of drop by checking where the intensity is 10% lower than during
    # the drop. Take 2*clustertime as averaging segment
    drop_len_min = int(13/clustertime) #minimal drop_length is 13 seconds
    drop_avg = np.average(power_hist[drop_start + 1: drop_start + 1 + drop_len_min])
    power_thresh2 = power_hist[drop_start + drop_len_min:] > 0.60*drop_avg
    drop_end = np.argmin(power_thresh2) + drop_start + drop_len_min
    
    #convert to timestamps in seconds
    drop_time_start = drop_start*clustertime
    drop_time_end = drop_end*clustertime
    
    return power_hist, P_thres, drop_time_start, drop_time_end


def DFT(signal, duration, f_range, Nbins, Nblocks):
    #carry out Fourier transform on the power history with a very narrow 
    #frequency scale. Nbins is the total number of tested frequencies.
    
    # Divide the sample into pieces of length 2048 elements. So a second of 
    # music (48000) corresponds to roughly 23.4 blocks
    blocksize = int(np.size(signal)/Nblocks)
    signal = signal[:blocksize*Nblocks].reshape(Nblocks, blocksize)
    power_hist = np.sum(signal**2, axis=1)
    power_hist = np.ravel(power_hist)
    
    t = np.linspace(0, duration, Nblocks)
    freq = np.linspace(*f_range, Nbins) #desired frequency range
    signal_dft = np.zeros(Nbins)
    
    for i, f in enumerate(freq):
        unsummed = power_hist*np.exp(-2j*np.pi*f*t) #F(ω) = ΣP(t)*exp(-iωt)
        summed = np.sum(unsummed)
        signal_dft[i] = np.abs(summed)
    
    return freq, power_hist, signal_dft


#%% Find BPM

def Find_BPM(signal, audiorate, song, plot=False, fft_analysis=False):
    
    duration = np.size(signal)/audiorate
    #determine drop region
    power_hist, P_thres, drop_start, drop_end = Droptime(signal, audiorate, 5)
    
    #determine to be analyzed drop segment
    #cut off buffer time at both ends of drop
    t_buffer = 2
    #drop segment duration has to be at least 60 seconds long
    drop_length = max([drop_end - drop_start, 60]) - 2*t_buffer
        
    #determine start and end times of segment
    seg_start = drop_start + t_buffer
    seg_end = seg_start + drop_length
    #take segment
    segment = Take_sample(signal, audiorate, seg_start, seg_end)
    
    #calculate DFT and plot
    Nblocks = 4096
    Nbins = 1000
    f_low = 2.6 #typical drum & bass speed is 2.9 Hz
    f_high = 3.0
    freq, power_hist_drop, segment_dft = DFT(segment, drop_length, 
                                             (f_low, f_high), Nbins, Nblocks)
    
    #calculate BPM by finding maxima
    indices, prop = find_peaks(segment_dft, 
                               height=0.6*segment_dft.max(),
                               distance=Nbins*(f_high - f_low)/8)
    '''
    #index where f > 170 BPM
    ind_thresh = int(Nbins*(170/60 - f_low)/(f_high - f_low))
    
    #preferably pick a BPM above 170
    if not (indices > ind_thresh).any():
        index = np.argmax(segment_dft)
    else:
        indices = indices[indices > ind_thresh]
        index = indices[np.argmax(segment_dft[indices])]
    '''
    index = np.argmax(segment_dft)
    freq_max = freq[index]
    BPM = np.round(60*freq_max, 1)
    
    if plot:
        #set up figure
        fig = plt.figure(num=1, figsize=(24,12))
        fig.suptitle(song, fontsize=30)
        ax1 = fig.add_subplot(2,2,1)
        ax2a = fig.add_subplot(4,2,2)
        fig.add_subplot(4,2,4)
        ax3 = fig.add_subplot(2,2,3)
        ax4a = fig.add_subplot(4,2,6)
        ax4b = fig.add_subplot(4,4,15)
        
        ax1.set_title('Global power history')
        ax2a.set_title('Beat/bar/drop detection')
        ax3.set_title('Tone spectrum')
        ax4a.set_title('DFT over typical DnB frequencies')
        
        #plot drop detection
        t_tot = np.linspace(0, duration, np.size(power_hist))
        ax1.plot(t_tot, power_hist)
        ax1.hlines(P_thres, 0, duration)
        ax1.vlines([drop_start, drop_end], 0, np.max(power_hist))
        ax1.set_xlim((0, signal.size/audiorate))
        
        ax4a.plot(freq, segment_dft)
        ax4a.set_xlim((f_low, f_high))
        ax4a.vlines(freq_max, 0, segment_dft.max())
        
        t_drop = np.linspace(drop_start + t_buffer, drop_end - t_buffer, power_hist_drop.size)
        ax4b.plot(t_drop, power_hist_drop)
    
    
    return BPM, drop_start, drop_end


def BPM_exact(signal_AS, audiorate, BPM_guess, drop_start, plot=False):
    
    bars = 4
    clustertime = 0.01
    dt = 60/BPM_guess
    
    #look for highest snare peak
    start_scan = int(1000*(drop_start + 4*dt))
    end_scan = int(1000*(drop_start + 8*dt))
    
    segment_scan = signal_AS[start_scan:end_scan].high_pass_filter(5000)
    array_scan= To_numpy(segment_scan)
    PH_scan = Power_history(array_scan, audiorate, clustertime)
    t_highest = drop_start + + 4*dt + clustertime*np.argmax(PH_scan)
    
    #take small segment around snare peak
    start1 = int(1000*(t_highest - 1/3*dt))
    end1 = int(1000*(t_highest + 1/3*dt))
    start2 = int(1000*(t_highest + 4*bars*dt - 1/3*dt))
    end2 = int(1000*(t_highest + 4*bars*dt + 1/3*dt))
    
    segment1 = signal_AS[start1:end1].high_pass_filter(5000)
    segment2 = signal_AS[start2:end2].high_pass_filter(5000)
    
    array1 = To_numpy(segment1)
    array2 = To_numpy(segment2)
    
    PH1 = Power_history(array1, audiorate, clustertime)
    PH2 = Power_history(array2, audiorate, clustertime)
    
    difference = clustertime*(np.argmax(PH2) - np.argmax(PH1))
    bars_duration = 4*dt*bars + difference
    new_dt = bars_duration/(4*bars)
    BPM = round(60/new_dt, 2)
    
    if plot:
        fig = plt.gcf()
        ax4c = fig.add_subplot(4,4,16)
        ax4c.plot(PH_scan)
        ax4c.plot(PH1)
        ax4c.plot(PH2)
    
    return BPM


#%% Processing functions for song characteristics

def Droptime_exact(signal_AS, drop_start, drop_end, BPM, plot=False):
    # marking every beat (~44 BPM) and every phrase (~11 BPM) in an array.
    # the droptime is used to bootstrap the beat.
    
    ### DETECT BEAT AND BAR ###
    
    #time stamps
    dt = 60/BPM #duration of 1 beat in seconds
    Nbars = 8 #take segment of drop of N bars
    Ndivisions = 12 #number of PH points per beat
    start1 = drop_start + 16*dt #start 4 bars after estimated drop
    end1 = start1 + Nbars*4*dt #start plus N bars
    
    #take segment on interval, take bass and treble only and convert to numpy
    segment1 = signal_AS[1000*start1: 1000*end1]
    segment1_bass = To_numpy(segment1)
    
    ### fit standard dnb drum pattern on treble and bass (or without filter)    
    
    #compute power history
    PH1 = Power_history(segment1_bass, signal_AS.frame_rate, dt/Ndivisions)
    Nframes = 4*Nbars*Ndivisions
    
    #in case the number of frames is not right
    if PH1.size > Nframes:
        PH1 = PH1[:Nframes]
    elif PH1.size < Nframes:
        short = Nframes - PH1.size
        PH1 = np.append(PH1, np.zeros(short))
        
    #split bass into 4 beats = 1 bar and average
    bass_stack = np.reshape(PH1, (Nbars, 4*Ndivisions)) #split signal
    bass_avg = np.average(bass_stack, axis=0)
    
    #trying the 1 2 3e 4 pattern
    segment_rolled = (bass_avg + 
                      np.roll(bass_avg, int(1*Ndivisions)) + 
                      np.roll(bass_avg, int(1.5*Ndivisions)) +
                      np.roll(bass_avg, int(3*Ndivisions)))
    
    #search highest peak, which corresponds to first beat of the bar
    t_bar_ind = np.argmax(segment_rolled)
    t_bar = t_bar_ind*dt/Ndivisions
    t_beat = t_bar % dt

    
    ### DROP DETECTION ###
        
    #first cut a new segment and apply a low pass filter
    #width of detection zone
    Nbars2 = 12
    start2 = max([drop_start + t_bar - Nbars2*2*dt, 0])
    end2 = start2 + Nbars2*4*dt
    #!!! computationally the most costly
    segment2 = To_numpy(signal_AS[1000*start2: 1000*end2].low_pass_filter(150))
    
    #calculate power history per bar
    PH2 = Power_history(segment2, signal_AS.frame_rate, 4*dt)
    PH3 = Power_history(segment2, signal_AS.frame_rate, dt/Ndivisions) #purely informative
    Nframes2 = 4*Nbars2*Ndivisions
    
    #in case the number of frames is not right
    if PH2.size > Nbars2:
        PH2 = PH2[:Nbars2]
    elif PH2.size < Nbars2:
        short = Nbars2 - PH2.size
        PH2 = np.append(PH2, np.zeros(short))
        
    #in case the number of frames is not right
    if PH3.size > Nframes2:
        PH3 = PH3[:Nframes2]
    elif PH3.size < Nframes2:
        short = Nframes2 - PH3.size
        PH3 = np.append(PH3, np.zeros(short))
    
    #separate first and last beat of bar
    PH2a = PH2[np.arange(1, Nbars2, 1)]
    PH2b = PH2[np.arange(0, Nbars2-1, 1)]
    #compute criterium: intensity times the ratio of current to previous bar
    PH2_criterium = PH2a*PH2a/PH2b
    
    #highest peak in criterium indicates drop
    drop_ind = np.argmax(PH2_criterium)
    t_drop_start = start2 + 4*dt*(drop_ind + 1)
    
    #plotting everything
    if plot:
        fig = plt.gcf()
        (ax1, ax2a, ax2b) = fig.axes[0:3]
        
        #axis 1 for exact droptime
        ax1.vlines(t_drop_start, *ax1.get_ylim(), 'red')
        
        #axis 2a for beat/bar detection
        time2a = np.linspace(start1, end1, PH1.size)
        ax2a.plot(time2a, PH1)
        #plot bar averages
        time2a = np.linspace(start1-4*dt, start1-dt/Ndivisions, 4*Ndivisions)
        ax2a.vlines(start1-4*dt + t_beat + dt*np.arange(4 + 4*Nbars), 0 , PH1.max(), 'orange')
        ax2a.plot(time2a, bass_avg, 'blue')
        ax2a.plot(time2a, segment_rolled, 'black')
        ax2a.vlines(start1-4*dt + t_bar + 4*dt*np.arange(1 + Nbars), 0, PH1.max(), 'red')
        ax2a.grid()
        ax2a.set_xlim((start1-4*dt, end1))
        
        #axis 2b for drop detection
        time2b1 = np.linspace(start2, end2, PH2.size + 1)
        time2b2 = np.linspace(start2, end2, PH3.size)
        time2b3 = np.linspace(start2 + 4*dt, end2, PH2a.size + 1) 
        #ax2b.plot(time2b1, P_hist2)
        ax2b.hist(time2b1[:-1], time2b1, weights=PH2, histtype='step')
        ax2b.plot(time2b2, PH3*(PH2.max()/PH3.max()))
        ax2b.plot(time2b3[:-1], PH2_criterium*PH2.max()/PH2_criterium.max(),
                  'kx', markersize=6)
        #ax2b.hlines(P_thres, start2, end2, 'k')
        ax2b.vlines([t_drop_start], 0, PH2.max(), 'k')
        ax2b.set_xlim((start2, end2))
    
    return t_drop_start

def dropend_and_songstart(drop_start, drop_end, BPM, plot=False):
    
    dt = 60/BPM
    
    #compute end of drop
    Ndropbars = np.round((drop_end - drop_start)/(64*dt)) #average per 8 bars
    drop_end_new = drop_start + Ndropbars*64*dt
    
    #compute start of song
    Nintrobars = int(drop_start/(32*dt))
    song_start = drop_start - Nintrobars*32*dt
    
    if plot:
        fig = plt.gcf()
        ax1 = fig.axes[0]
        
        #axis 1 for exact droptime
        ax1.vlines(drop_end_new, *ax1.get_ylim(), 'red')
    
    return drop_end_new, song_start

def Key(signal, audiorate, start, BPM, Noctaves=4, A_low=110, bars=1, plot=False):
    # finding the key of the song by looking at the Fourier transform on the
    # drop. The frequency of the bass should be between 40 and 80 Hz. Probably
    # use a DFT. Finally round up to the nearest tone.
    
    # extract snippet of drop region
    sample_length = 8*bars*60/BPM
    end = start + sample_length #take exactly one phrase worth of music 
    phrase = Take_sample(signal, audiorate, start, end)
    
    tones = ['A','Bb','B','C','C#','D','Eb','E','F','F#','G','G#']
    tone_freqs = A_low* (2**(1/12))**np.arange(12*Noctaves) #from 55-1760 Hz for 5 octaves
    
    #performing DFT on all specific frequencies
    signal_dft = np.zeros_like(tone_freqs)
    t = np.linspace(0, sample_length, np.size(phrase))
    for i, f in enumerate(tone_freqs):
        unsummed = phrase*np.exp(-2j*np.pi*f*t) #F(ω) = ΣP(t)*exp(-iωt)
        summed = np.sum(unsummed)
        signal_dft[i] = np.abs(summed)
    
    #stacking by tone
    dft_stack = signal_dft.reshape(Noctaves,12)
        
    #summing all octaves per tone and plot with x
    dft_summed = np.average(dft_stack, axis=0)
    
    ### METHOD 1: perfect match ###
    #looking for highest 7 notes belonging in the scale
    threshold = np.percentile(dft_summed, 40, interpolation='midpoint')
    scale = 1*(dft_summed > threshold)
    
    #comparing with scale starting with the first element
    #if the scales don't match, the investigated array is rolled to the left
    #and again it is compared untill it matches. The number of shifts leads
    #to the key
    key_number = False
    options = np.array([], dtype=np.int)
    key_pattern = np.array([1,0,1,0,1,1,0,1,0,1,0,1])
    for shift in range(12):
        scale_shifted = np.roll(scale, -shift)
        check = np.sum(key_pattern*scale_shifted)
        if check == 7:
            print('\nFound perfect scale match')
            key_number = shift
            break
        elif check == 6:
            options = np.append(options, shift)
    
    ### METHOD 2: 6-note match ###
    if not key_number and len(options) > 0:
        print('\nLooking for best 6-note scale match')
        
        def scale_match(shift):
            key_pattern = np.array([1,0,0.6,0,1,0.6,0,1,0,1,0,0.6])
            values = np.roll(key_pattern, shift)*dft_summed
            value = np.sum(values)
            return value
    
        opt_vals = np.zeros_like(options)
        for i, opt in enumerate(options):
            opt_vals[i] = scale_match(opt)
        
        opt_nr = np.argmax(opt_vals)
        key_number = options[opt_nr]
        print('key options:\t', options)
        print('values:\t\t', opt_vals)
    
    ### METHOD 3: chord match ###
    if isinstance(key_number, bool) and len(options) == 0:
        print('\nLooking for best chord match')
        
        def chord_match(shift):
            key_pattern = np.array([1,0,0,0,1,0,0,1,0,1,0,0])
            values = np.roll(key_pattern, shift)*dft_summed
            value = np.sum(values)
            return value
        
        opt_vals = np.zeros(12)
        for opt in range(12):
            opt_vals[opt] = chord_match(opt)
        
        key_number = np.argmax(opt_vals)
        candidates = opt_vals.argsort()
        print('Best candidates:', candidates[-3:][::-1])
            
    ### REPORTING KEY ###
    #check if major or minor
    major_chord = np.array([1,0,0,0,1,0,0,1,0,0,0,0])
    minor_chord = np.array([1,0,0,1,0,0,0,1,0,0,0,0])
    major_val = np.sum(np.roll(major_chord, key_number)*dft_summed)
    minor_val = np.sum(np.roll(minor_chord, key_number-3)*dft_summed)
    major = (major_val > minor_val)
    if major:
        key = tones[key_number]
    else:
        key = tones[key_number-3] + 'm'
    
    #report key
    print('Key = %s' % key)
    
    #plotting everything in axis 3
    if plot:
        fig = plt.gcf()
        ax3 = fig.axes[3]
        for octave in range(Noctaves):
            ax3.hist(np.arange(12), np.arange(13), weights=dft_stack[octave,:],
                     histtype='step', lw=2, label='octave %d' % octave)
        
        ax3.hist(np.arange(12), np.arange(13), weights=dft_summed, color='k',
                     histtype='step', lw=2.5, label='total per tone')
        ax3.set_xlim((0, 12))
        ax3.set_xticks(np.arange(12) + 0.5)
        ax3.set_xticklabels(tones)
        ax3.legend()
        
        fifths = [9, 2, 7, 0, 5, 10, 3, 8, 1, 6, 11, 4, 9]
        print('fifths =', fifths)
    
    return key_number, major, scale

#%% Data collection function
    
def Data(folder, overwrite=False):
    #compute BPM, key and dropstart/end of each song in the folder
    os.chdir(folder)
    songs = os.listdir()
    
    #check if there already is a music data file
    if 'Music_data.npy' in songs and not overwrite:
        print('Folder already has a music data file')
        return
    
    Nsongs = len(songs)
    data = np.zeros((Nsongs, 6)) #[framerate, BPM, dropstart, dropend, key]
    #loop for every song
    for i, song in enumerate(songs):
        print('')
        
        #read song
        song, signal, signal_AS, audiorate = Read(song)
        print('\nMusic data: of %s\n' %song[:-4] + '-'*60)
        
        # find bpm
        BPM, drop_start0, drop_end0  = Find_BPM(signal, audiorate, song)
        
        # find exact timestamps of start and end of drop
        drop_start = Droptime_exact(signal_AS, drop_start0, drop_end0, BPM)
        print('drop start =\t', drop_start)
        
        # BPM correction
        BPM_corr = BPM_exact(signal_AS, audiorate, BPM, drop_start)
        print('BPM =\t\t', BPM_corr)
        
        # find songstart and dropend
        drop_end, song_start = dropend_and_songstart(drop_start, drop_end0, BPM_corr)
        print('song start =\t', song_start)
        print('drop end =\t', drop_end)
    
        # find key
        key, major, scale = Key(signal, audiorate, drop_start, BPM, bars=2)
        
        #fill data array
        data[i] = np.array([audiorate, BPM_corr, song_start, drop_start, drop_end, key])
    
    np.save('Music_data.npy', data)
    return


def check(folder, song_nr, plot=True):
    os.chdir(folder)
    songs = os.listdir()
    song = songs[song_nr]
    
    #try close figure
    fig = plt.gcf()
    plt.close(fig)
    
    #read song
    song, signal, signal_AS, audiorate = Read(song)
    print('\nMusic data: of %s\n' %song[:-4] + '-'*60)
    print('framerate =\t', audiorate)
    
    # find bpm
    BPM, drop_start0, drop_end0  = Find_BPM(signal, audiorate, song, plot=plot)
    print('BPM =\t\t', BPM)
    print('drop start  ~\t', drop_start0)
    print('drop end  ~\t', drop_end0)
    
    # find exact timestamps of start and end of drop
    drop_start= Droptime_exact(signal_AS, drop_start0, drop_end0, BPM, plot=plot)
    print('drop start =\t', drop_start)
    
    # BPM correction
    BPM_corr = BPM_exact(signal_AS, audiorate, BPM, drop_start, plot=plot)
    print('BPM corrected =\t', BPM_corr)
    
    # find songstart and dropend
    drop_end, song_start = dropend_and_songstart(drop_start, drop_end0, BPM_corr, plot=plot)
    print('song start =\t', song_start)
    print('drop end =\t', drop_end)
    
    # find key
    key, major, scale = Key(signal, audiorate, drop_start, BPM, bars=2, plot=plot)
    print('key =\t\t', key)
    
    plt.show()
    
    return audiorate, BPM, song_start, drop_start, drop_end, key