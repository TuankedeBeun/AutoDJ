from helper.plotter import Plotter
from helper.audioreader import AudioReader, to_nparray, audio_np_section
import numpy as np
from pydub.effects import low_pass_filter, high_pass_filter
from scipy.signal import find_peaks, gaussian

### Revised version ###
def power_history(signal, audiorate, clustertime, resolution=None):
    # calculate the power history with a resolution
    if signal.ndim == 2:
        signal = np.average(signal, axis=0)
    signal_squared = signal**2
    blocksize = int(clustertime*audiorate)
    
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
    
    if resolution:
        time = resolution*np.arange(power_hist.size)
    else:
        time = clustertime*np.arange(power_hist.size)
    
    return time, power_hist

class AudioAnalyser():
    def __init__(self, song_directory, song_title):
        self.reader = AudioReader(song_directory, song_title)
        self.plotter = Plotter(song_title, figsize=(16,9), sharex=False)
        
    def get_properties(self):
        drop_start_estimate, drop_end_estimate = self.estimate_droptime()
        bpm_props = self.find_bpm(drop_start_estimate, drop_end_estimate)
        bpm, bpm_reliable, dropbeat, beat_reliable = bpm_props
        drop_start, drop_start_reliable = self.get_dropstart(dropbeat, bpm)
        drop_end = self.get_dropend(drop_start, drop_end_estimate, bpm)
        song_start = self.get_songstart(drop_start, bpm)
        key_number, is_major, method = self.find_key(drop_start, bpm)
        tones = ['A','Bb','B','C','C#','D','Eb','E','F','F#','G','G#']
        note = tones[key_number]
        properties = {'bpm': {'value': bpm, 'reliable': bpm_reliable},
                      'drop_start': {'value': drop_start, 'estimate': drop_start_estimate, 'reliable': drop_start_reliable},
                      'drop_end': {'value': drop_end, 'estimate': drop_end_estimate},
                      'song_start': {'value': song_start},
                      'key': {'note': note, 'key_number': key_number, 'is_major': is_major, 'method': method}
                      }
        return properties
        
    def estimate_droptime(self, minimal_droplength=30, clustertime=8, resolution=1):
        # clustertime is the length of a power history block in seconds
        t, audio_np = to_nparray(self.reader.audiosegment)
        audiorate = self.reader.audiosegment.frame_rate
        time_ph, power_hist = power_history(audio_np, audiorate, clustertime, resolution)
        
        # condition 1: threshold slightly lower than highest 20% of power history
        P_thres = 0.8*np.percentile(power_hist, 90)
        # find index of start of drop
        cond_Pthres = power_hist > P_thres
        cond_Pthres = cond_Pthres + np.roll(cond_Pthres, -1)
        
        # condition 2: drop is 'minimal_droplength' seconds long
        minimal_droplength = int(minimal_droplength/resolution)
        cond_length = cond_Pthres.copy()
        for i in range(minimal_droplength):
            cond_length *= np.roll(cond_Pthres, -i)
        
        # drop starts at first index where both conditions satisfy
        drop_start = np.argmax(cond_length) + 1
        
        # find end of drop, at which the intensity is x% lower after minimum drop length
        P_thres2 = 0.9*P_thres
        
        cond_Pthres2 = power_hist[drop_start + minimal_droplength:] > P_thres2
        cond_length2 = cond_Pthres2 + np.roll(cond_Pthres2, -1)
        # if drop never stops, the end is at the end of the song
        if cond_length2.all():
            drop_end = cond_length.size - 3 + drop_start + minimal_droplength
        else:
            drop_end = np.argmin(cond_length2) + drop_start + minimal_droplength
        
        # convert to timestamps in seconds
        drop_start = drop_start*resolution
        drop_end = drop_end*resolution
        
        # plotting
        axis = self.plotter.add_axis('time (s)', 'Global Power')
        axis.add_plot(time_ph, power_hist, 'plot', 'power history')
        axis.add_plot( (0, self.reader.audiosegment.duration_seconds), P_thres, 'hline', 'threshold start')
        axis.add_plot( (0, self.reader.audiosegment.duration_seconds), P_thres2, 'hline', 'threshold end')
        axis.add_plot( drop_start, (0, power_hist.max()), 'vline', 'drop start estimate')
        axis.add_plot( drop_end, (0, power_hist.max()), 'vline', 'drop end estimate')
        
        return drop_start, drop_end

            
    def find_bpm(self, drop_start_guess, drop_end_guess, Nbars = 7, clustertime = 0.015, resolution = 0.001, hpf = 10000):
        audiorate = self.reader.audiosegment.frame_rate
        BPM_reliable = beat_reliable = True
        scanning_point = drop_start_guess + (drop_end_guess - drop_start_guess)/3
        
        # take a scanning region
        start_scan = int(1000*(scanning_point))
        end_scan = int(1000*(scanning_point + Nbars*4*60/160))
        segment_scan = self.reader.audiosegment[start_scan:end_scan].high_pass_filter(hpf)
        t, array_scan = to_nparray(segment_scan)
        t, powerhistory_scan = power_history(array_scan, audiorate, clustertime, resolution)
        
        # calculate resonance of BPM
        resonance_BPMs = np.arange(165, 178)
        resonance_vals = np.zeros_like(resonance_BPMs, dtype=np.float64)
        PHs = []
        
        for i, BPM_try in enumerate(resonance_BPMs):
            halfbar_length = 2*60/BPM_try
            PH_section_length = int(halfbar_length/resolution)
            PH_halfbar_stack = powerhistory_scan[:Nbars*PH_section_length].reshape(7,-1)
            PH_halfbar_avg = np.average(PH_halfbar_stack, axis=0)
            resonance = PH_halfbar_avg.max()
            
            resonance_vals[i] = resonance
            PHs.append(PH_halfbar_avg)
        
        # highest resonance indicates BPM
        resonance_vals -= resonance_vals.min()
        BPM_ind = np.argmax(resonance_vals)
        BPM = resonance_BPMs[BPM_ind]
        PH = PHs[BPM_ind]
        # if more than one BPM peak present, it is not reliable
        BPM_peaks, _ = find_peaks(resonance_vals, height=0.5*resonance_vals.max())
        if BPM_peaks.size > 1:
            BPM_reliable = False
            
        # time signatures
        t_snare = scanning_point + resolution*np.argmax(PH)
        # if more than one high beat peak present, it is not reliable
        PH_max = PH.max()
        distance_apart = PH.size/10
        beat_peaks, _ = find_peaks(PH, height=0.9*PH_max, distance=distance_apart)
        if beat_peaks.size > 1:
            beat_reliable = False
            
        # find drop beat
        dt = 60/BPM
        drop_snare = t_snare - round((t_snare - drop_start_guess)/(2*dt))*2*dt
        snare_hit = False
        while not snare_hit:
            start_snare = int(1000*(drop_snare - dt/4))
            end_snare = int(1000*(drop_snare + dt/4))
            segment_snare = self.reader.audiosegment[start_snare:end_snare].high_pass_filter(hpf)
            t, array_snare = to_nparray(segment_snare)
            t, PH_snare = power_history(array_snare, audiorate, clustertime, resolution)
            snare_hit = PH_snare.max() > 0.6*PH_max
            if not snare_hit:
                drop_snare += 3*4*dt
        
        beat_time = drop_snare + dt
        
        # plotting
        axis = self.plotter.add_axis('BPM', 'resonance')
        axis.add_plot(resonance_BPMs, resonance_vals, 'plot', 'resonance')
        axis.add_plot(resonance_BPMs[BPM_peaks], resonance_vals[BPM_peaks]*PH.max()/resonance_vals.max(), 'plot', 'peaks')
        
        return BPM, BPM_reliable, beat_time, beat_reliable
    
    def get_dropstart(self, drop_beat, bpm, plot=False):
    
        dt = 60/bpm
        drop_reliable = True
        audiorate = self.reader.audiosegment.frame_rate
        
        # first cut a new segment and apply a low pass filter
        Nbars = 16
        start = max([drop_beat - round(1/2*Nbars)*4*dt, drop_beat % dt])
        end = start + Nbars*4*dt
        audiosegment_bass = self.reader.audiosegment[1000*start: 1000*end].low_pass_filter(200)
        t, bass_np = to_nparray(audiosegment_bass)
        
        # calculate power history per half bar
        time_bass, powerhistory_bass = power_history(bass_np, audiorate, 2*dt)
        
        # in case the number of frames is not right
        if powerhistory_bass.size > 2*Nbars:
            powerhistory_bass = powerhistory_bass[:2*Nbars]
        elif powerhistory_bass.size < 2*Nbars:
            short = 2*Nbars - powerhistory_bass.size
            powerhistory_bass = np.append(powerhistory_bass, np.zeros(short))
        
        #!!! can be optimized still
        criterium = np.zeros_like(powerhistory_bass)
        for i in range(1, criterium.size - 1):
            min_ratio = powerhistory_bass[i+1:].min() / powerhistory_bass[:i].min()
            max_ratio = powerhistory_bass[i+1:].max() / powerhistory_bass[:i].max()
            instant_difference = powerhistory_bass[i] - powerhistory_bass[i-1]
            instant_increment = powerhistory_bass[i] / powerhistory_bass[i-1]
            criterium[i] = (powerhistory_bass[i] * 
                             min_ratio *
                             max_ratio *
                             instant_difference)
        
        # highest peak in criterium indicates drop
        drop_ind = np.argmax(criterium)
        t_drop_start = start + 2*dt*drop_ind
        if np.sum(criterium > 0.85*criterium.max()) > 1:
            drop_reliable = False
            
        # plotting
        Ndivisions = 8
        time_bass_division, powerhistory_bass_division = power_history(bass_np, audiorate, dt/Ndivisions)
        Nframes2 = 4*Nbars*Ndivisions
        # in case the number of frames is not right
        if powerhistory_bass_division.size > Nframes2:
            powerhistory_bass_division = powerhistory_bass_division[:Nframes2]
        elif powerhistory_bass_division.size < Nframes2:
            short = Nframes2 - powerhistory_bass_division.size
            powerhistory_bass_division = np.append(powerhistory_bass_division, np.zeros(short))
        
        axis = self.plotter.add_axis('time (s)', 'bass')
        axis.add_plot(start + time_bass, powerhistory_bass, 'plot', 'bass')
        
        ph_bass_div_norm = powerhistory_bass_division*(powerhistory_bass.max()/powerhistory_bass_division.max())
        axis.add_plot(start + time_bass_division, ph_bass_div_norm, 'plot', 'bass div')
        
        time_criterium = np.linspace(start, end, criterium.size + 1)
        criterium_norm = criterium*powerhistory_bass.max()/criterium.max()
        axis.add_plot(time_criterium[:-1], criterium_norm, 'histogram', 'criterium')
        
        axis.add_plot(t_drop_start, (0, 1), 'vline', 'start exact')
        
        # plotting in global axis
        global_axis = self.plotter.axis_objects[0]
        global_axis.add_plot(t_drop_start, (0, 1), 'vline', 'start exact')

        return t_drop_start, drop_reliable

    def get_dropend(self, drop_start, drop_end_guess, bpm):
        dt = 60/bpm
        Ndropbars = np.round((drop_end_guess - drop_start)/(64*dt)) #average per 8 bars
        drop_end = drop_start + Ndropbars*64*dt
        
        # plotting
        global_axis = self.plotter.axis_objects[0]
        global_axis.add_plot(drop_end, (0, 1), 'vline', 'end exact')
        return drop_end
    
    def get_songstart(self, drop_start, bpm):
        dt = 60/bpm
        Nintrobars = int(drop_start/(32*dt))
        song_start = drop_start - Nintrobars*32*dt
        return song_start
        
    def find_key(self, start, bpm, Noctaves=4, A_low=110, bars=1):
        # finding the key of the song by looking at the Fourier transform on the
        # drop. The frequency of the bass should be between 40 and 80 Hz. Probably
        # use a DFT. Finally round up to the nearest tone.

        # extract snippet of drop region
        sample_length = 8*bars*60/bpm
        end = start + sample_length #take exactly one phrase worth of music 
        phrase = audio_np_section(self.reader.audiosegment, start, end)
        phrase = np.sum(phrase, axis=0)
        
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
        method = 'perfect'
        key_number = False
        options = np.array([], dtype=np.int)
        key_pattern = np.array([1,0,1,0,1,1,0,1,0,1,0,1])
        for shift in range(12):
            scale_shifted = np.roll(scale, -shift)
            check = np.sum(key_pattern*scale_shifted)
            if check == 7:
                key_number = shift
                break
            elif check == 6:
                options = np.append(options, shift)
        
        ### METHOD 2: 6-note match ###
        if not key_number and len(options) > 0:
            method = '6-note'
            
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
        
        ### METHOD 3: chord match ###
        if isinstance(key_number, bool) and len(options) == 0:
            method = 'chord'
            
            def chord_match(shift):
                key_pattern = np.array([1,0,0,0,1,0,0,1,0,1,0,0])
                values = np.roll(key_pattern, shift)*dft_summed
                value = np.sum(values)
                return value
            
            opt_vals = np.zeros(12)
            for opt in range(12):
                opt_vals[opt] = chord_match(opt)
            
            key_number = np.argmax(opt_vals)
                
        ### REPORTING KEY ###
        # check if major or minor
        major_chord = np.array([1,0,0,0,1,0,0,1,0,0,0,0])
        minor_chord = np.array([1,0,0,1,0,0,0,1,0,0,0,0])
        major_val = np.sum(np.roll(major_chord, key_number)*dft_summed)
        minor_val = np.sum(np.roll(minor_chord, key_number-3)*dft_summed)
        major = (major_val > minor_val)
        
        # plotting
        axis = self.plotter.add_axis('tone', 'intensity')
        axis.add_plot(tones, dft_summed, 'tones', 'summed')
        for i in range(Noctaves):
            axis.add_plot(tones, dft_stack[i], 'tones', 'octave %d' % i)
        
        return key_number, major, method