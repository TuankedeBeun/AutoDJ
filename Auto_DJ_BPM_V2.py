#%% Import and parameters

import os
import numpy as np
import matplotlib.pyplot as plt
import pydub
from pydub.effects import low_pass_filter, high_pass_filter
from scipy.signal import find_peaks, gaussian

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

def Power_history_alt(signal, audiorate, clustertime, resolution):
        
    # calculate the power history with a resolution
    blocksize = int(clustertime*audiorate)
    res_size = int(resolution*audiorate)
    Nblocks = int((np.size(signal) - blocksize)/res_size)
    unsummed = np.zeros((Nblocks, blocksize))
    
    signal_squared = signal**2
    
    for block in range(Nblocks):
        start = res_size*block
        end = res_size*block + blocksize
        section = signal_squared[start: end]
        section_weighted = gaussian(blocksize, int(blocksize/2))*section
        unsummed[block] = section_weighted
    
    power_hist = np.sum(unsummed, axis=1)
    power_hist = np.ravel(power_hist)
    
    return power_hist

def Droptime(signal, audiorate, clustertime):
    # detect start and end of the drop by first calculating the accumulative
    # power per 4 beats (~1.4s) and then looking where this value is suddenly
    # higher, above a threshold (upper 50 percentile).
    
    # clustertime is the length of power history block in seconds
    power_hist = Power_history(signal, audiorate, clustertime)
    
    #!!! compute power threshold by taking 90% of highest 20% Power History
    P_thres = 0.75*np.percentile(power_hist, 90)
    
    # find index of start of drop
    cond_Pthres = power_hist > P_thres
    
    # minimal drop length of 20 seconds
    drop_len_min = int(30/clustertime)
    
    cond_Pthres = cond_Pthres + np.roll(cond_Pthres, -1)
    cond_length = cond_Pthres.copy()
    for i in range(drop_len_min):
        cond_length = cond_length*np.roll(cond_Pthres, -i)
    
    drop_start = np.argmax(cond_length) + 1
    
    # find end of drop, at which the intensity is 80% lower than 20 second 
    # average for more than 1 index (outlier)
    # drop_len_min = int(20/clustertime)
    # drop_avg = np.average(power_hist[drop_start + 1: drop_start + 1 + drop_len_min])
    P_thres2 = 0.9*P_thres
    
    cond_Pthres2 = power_hist[drop_start + drop_len_min:] > P_thres2
    cond_length2 = cond_Pthres2 + np.roll(cond_Pthres2, -1)
    # if drop never stops, the end is at the end of the song
    if cond_length2.all():
        drop_end = cond_length.size - 3 + drop_start + drop_len_min
    else:
        drop_end = np.argmin(cond_length2) + drop_start + drop_len_min
    
    #convert to timestamps in seconds
    drop_time_start = drop_start*clustertime
    drop_time_end = drop_end*clustertime
    
    return power_hist, (P_thres, P_thres2), drop_time_start, drop_time_end

#%% Find BPM
    

def BPM_iteration(signal_AS, audiorate, BPM_guess, hpf, t_peak, peakheight, bars, clustertime, resolution):
    
    dt = 60/BPM_guess
    
    #take small segment around snare peak
    start = int(1000*(t_peak - 4*dt*bars - 1/3*dt))
    end = int(1000*(t_peak - 4*dt*bars + 1/3*dt))
    
    segment = signal_AS[start:end].high_pass_filter(hpf)
    array = To_numpy(segment)
    PH = Power_history_alt(array, audiorate, clustertime, resolution)
    
    difference = resolution*(np.argmax(PH) - len(PH)/2)
    bars_duration = 4*dt*bars - difference
    new_dt = bars_duration/(4*bars)
    BPM = round(60/new_dt, 2)
    
    PH_max = np.max(PH)
    reliable = (PH_max > 0.7*peakheight) and (PH_max < 2*peakheight)
    
    return BPM, PH, reliable

def Find_BPM(signal_AS, signal, audiorate, song, plot=False):
    # compute approximate droptime
    power_hist, thresholds, drop_start0, drop_end0 = Droptime(signal, audiorate, 4)
    
    # BPM guesses
    BPM_guesses = [174, 160, 150]
    BPM_i = 0
    
    # initial guess values
    clustertime = 0.005
    resolution = 0.001
    hpf = 2000
    scanning_point = drop_start0 + 12
    reliable = False
    
    while not reliable:
        #look for highest peak in scanning region
        start_scan = int(1000*(scanning_point))
        end_scan = int(1000*(scanning_point + 2*60/BPM_guesses[BPM_i]))
        segment_scan = signal_AS[start_scan:end_scan].high_pass_filter(hpf)
        array_scan = To_numpy(segment_scan)
        PH_scan = Power_history_alt(array_scan, audiorate, clustertime, resolution)
        t_snare = scanning_point + resolution*np.argmax(PH_scan)
        peakheight = np.max(PH_scan)
        
        bars = [1, 3.5, 9]
        PHs = []
        BPMs = [BPM_guesses[BPM_i]]
        
        # match other snare peaks
        for i, Nbars in enumerate(bars):
            BPM, PH, reliable = BPM_iteration(signal_AS, audiorate, BPMs[i], hpf,
                                          t_snare, peakheight, Nbars, clustertime, resolution)
            BPMs.append(BPM)
            PHs.append(PH)
            
            if not reliable:
                print('bad guess for BPM region')
                scanning_point += 6*60/BPM_guesses[BPM_i]
                BPM = BPM_guesses[BPM_i]              
                break
        
        # if no results, try other BPM guess
        if scanning_point > (drop_start0 + 50):
            # if all fails, set BPM to 174
            if BPM_i + 1 >= len(BPM_guesses):
                BPM = 174
                reliable = False
                print('BPM not found')
                break
            else:
                BPM_i += 1
                scanning_point = drop_start0 + 12
                print('bad BPM guess')
    
    if reliable:
        BPM = round(BPM*2)/2
        dt = 60/BPM
        t_bass = t_snare - dt
        drop_beat = t_bass - bars[-1]*4*dt
    else:
        drop_beat = drop_start0
    
    if plot:
        # set up figure
        fig = plt.figure(num=1, figsize=(24,12))
        fig.suptitle(song, fontsize=30)
        ax1 = fig.add_subplot(2,2,1)
        ax2 = fig.add_subplot(2,2,2)
        ax3 = fig.add_subplot(2,2,3)
        ax4 = fig.add_subplot(2,2,4)
        
        ax1.set_title('Global power history')
        ax2.set_title('Beat/bar/drop detection')
        ax3.set_title('Tone spectrum')
        ax4.set_title('BPM finder')
        
        # plot drop detection
        duration = np.size(signal)/audiorate
        t_tot = np.linspace(0, duration, np.size(power_hist))
        ax1.plot(t_tot, power_hist)
        ax1.hlines(thresholds, 0, duration, linestyle='--', label='thresholds')
        ax1.vlines([drop_start0, drop_end0], 0, np.max(power_hist), label='approximate droptime')
        ax1.vlines(t_snare, 0, np.max(power_hist), 'b', linestyle='--', linewidth=2, label='BPM point')
        ax1.set_xlim((0, signal.size/audiorate))
        
        # set estimates for drop start and end
        ax2.vlines(drop_beat, 0, 10000, 'g', linestyle='--', linewidth=2, label='drop beat')
        
        # plot BPM finder
        t_scan = np.linspace(scanning_point, scanning_point + 2*60/BPM_guesses[BPM_i] - clustertime, PH_scan.size)
        ax4.plot(t_scan, PH_scan, lw=1.5, c='k', label='scanning region')
        ax4.vlines(t_snare, *ax4.get_ylim(), color='r')
        if reliable:
            for i, Nbars in enumerate(bars):
                ax4.plot(np.linspace(t_snare-20/BPMs[i], t_snare+20/BPMs[i], PHs[i].size), 
                         PHs[i], alpha=0.8, label='%s bars' % Nbars)
        ax4.legend()
    
    return BPM, drop_start0, drop_end0, drop_beat, reliable


#%% Processing functions for song characteristics

def Droptime_exact(signal_AS, drop_beat, BPM, plot=False):
    
    dt = 60/BPM
    
    # first cut a new segment and apply a low pass filter
    # width of detection zone
    
    Nbars = 16
    start = max([drop_beat - round(1/2*Nbars)*4*dt, drop_beat % dt])
    end = start + Nbars*4*dt
    segment = To_numpy(signal_AS[1000*start: 1000*end].low_pass_filter(200))
    
    # calculate power history per half bar
    PH = Power_history(segment, signal_AS.frame_rate, 2*dt)
    
    # in case the number of frames is not right
    if PH.size > 2*Nbars:
        PH = PH[:2*Nbars]
    elif PH.size < 2*Nbars:
        short = 2*Nbars - PH.size
        PH = np.append(PH, np.zeros(short))
    
    # separate first and second half of the bar
    PH2before = PH[np.arange(0, 2*Nbars-3)]
    PH1before = PH[np.arange(1, 2*Nbars-2)]
    PHdrop = PH[np.arange(2, 2*Nbars-1)]
    PH1after = PH[np.arange(3, 2*Nbars)]
    # compute criterium: intensity times the ratio of current to previous bar
    PH_criterium = PHdrop*PH1after*(PHdrop-PH1before)*(PHdrop-PH2before)/PH1before
    
    # highest peak in criterium indicates drop
    drop_ind = np.argmax(PH_criterium)
    t_drop_start = start + 2*dt*(drop_ind + 2)
    
    # plotting everything
    if plot:
        # purely informative detailed bass graph
        Ndivisions = 8
        PH3 = Power_history(segment, signal_AS.frame_rate, dt/Ndivisions)
        Nframes2 = 4*Nbars*Ndivisions
        # in case the number of frames is not right
        if PH3.size > Nframes2:
            PH3 = PH3[:Nframes2]
        elif PH3.size < Nframes2:
            short = Nframes2 - PH3.size
            PH3 = np.append(PH3, np.zeros(short))
        
        fig = plt.gcf()
        (ax1, ax2) = fig.axes[0:2]
        
        # axis 1 for exact droptime
        ax1.vlines(t_drop_start, *ax1.get_ylim(), 'red')
        
        # axis 2b for drop detection
        time2b1 = np.linspace(start, end, PH.size + 1)
        time2b2 = np.linspace(start, end, PH3.size)
        time2b3 = np.linspace(start + 4*dt, end - 2*dt, PHdrop.size + 1)
        ax2.hist(time2b1[:-1], time2b1, weights=PH, histtype='step')
        ax2.plot(time2b2, PH3*(PH.max()/PH3.max()))
        ax2.plot(time2b3[:-1], PH_criterium*PH.max()/PH_criterium.max(),
                 'kx', markersize=6, label='weighted increment')
        ax2.vlines(t_drop_start, 0, PH.max(), 'k', label='drop start')
        ax2.set_xlim((start, end))
        ax2.set_ylim((0, 1.1*PH.max()))
        ax2.legend(loc=4)
    
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
        ax1.vlines(drop_end_new, *ax1.get_ylim(), 'red', label='exact droptime')
        ax1.legend(loc=4)
    
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
        ax3 = fig.axes[2]
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
    
def Data(folder):
    #compute BPM, key and dropstart/end of each song in the folder
    os.chdir(folder)
    songs = os.listdir()
    
    #check if there already is a music data file
    if 'Music_data.npy' in songs:
        print('Folder already has a music data file')
        overwrite = input('Do you wish to delete it?\n(yes/no)\t')
        if overwrite == 'yes':
            os.remove('Music_data.npy')
            songs.remove('Music_data.npy')
        else:
            return
    
    Nsongs = len(songs)
    data = np.zeros((Nsongs, 7)) #[framerate, BPM, dropstart, dropend, key]
    #loop for every song
    for i, song in enumerate(songs):
        print('')
        
        #read song
        song, signal, signal_AS, audiorate = Read(song)
        print('\nMusic data: of %s\n' %song[:-4] + '-'*60)
        
        # find bpm
        props = Find_BPM(signal_AS, signal, audiorate, song)
        BPM, drop_start0, drop_end0, drop_beat, reliable = props
        print('BPM =\t\t', BPM)
        
        # find exact timestamps of start and end of drop
        drop_start = Droptime_exact(signal_AS, drop_beat, BPM)
        print('drop start =\t', drop_start)
        
        # find songstart and dropend
        drop_end, song_start = dropend_and_songstart(drop_start, drop_end0, BPM)
        print('drop end =\t', drop_end)
        print('song start =\t', song_start)
        
        # find key
        key, major, scale = Key(signal, audiorate, drop_start, BPM, bars=2)
        print('key =\t\t', key)
        
        #fill data array
        data[i] = np.array([audiorate, BPM, song_start, drop_start, drop_end, key, reliable])
    
    np.save('Music_data.npy', data)
    return


def check(folder, song_nr, plot=True):
    os.chdir(folder)
    songs = os.listdir()
    if 'Music_data.npy' in songs:
        songs.remove('Music_data.npy')
    song = songs[song_nr]
    
    #try close figure
    fig = plt.gcf()
    plt.close(fig)
    
    #read song
    song, signal, signal_AS, audiorate = Read(song)
    print('\nMusic data: of %s\n' %song[:-4] + '-'*60)
    print('framerate =\t', audiorate)
    
    # find bpm
    props = Find_BPM(signal_AS, signal, audiorate, song, plot=plot)
    BPM, drop_start0, drop_end0, drop_beat, reliable = props
    print('BPM =\t\t', BPM)
    print('drop start  ~\t', drop_start0)
    print('drop end  ~\t', drop_end0)
    
    # find exact timestamps of start and end of drop
    drop_start = Droptime_exact(signal_AS, drop_beat, BPM, plot=plot)
    print('drop start =\t', drop_start)
    
    # find songstart and dropend
    drop_end, song_start = dropend_and_songstart(drop_start, drop_end0, BPM, plot=plot)
    print('drop end =\t', drop_end)
    print('song start =\t', song_start)
    
    # find key
    key, major, scale = Key(signal, audiorate, drop_start, BPM, bars=2, plot=plot)
    print('key =\t\t', key)
    
    plt.show()
    
    return audiorate, BPM, song_start, drop_start, drop_end, key