import os
import csv
import numpy as np
from time import strftime, localtime
from tabulate import tabulate
from analyse.audio_analyser import AudioAnalyser
from player.songplayer import play_song
from common.load_data import load_data_from_csv
from common.bpm import calculate_bpm_from_drop
from common.key_conversion import from_key_to_circle_of_fifths

def analyse_folder(folder):
    # initialize dictionary csv writer
    last_folder = os.path.split(folder)[-1]
    csv_file_name = 'analysis_' + last_folder + strftime("%d%b%YT%H%M", localtime()) + '.csv'
    song_properties = ['nr','song','bpm','drop_start', 'drop_end', 'song_start', 'key', 'key_number', 'is_major']
    file = open(os.path.join(os.getcwd(), 'data', csv_file_name), newline='', mode='w')
    writer = csv.DictWriter(file, fieldnames=song_properties)
    writer.writeheader()
    
    # extract song properties for every song in the given folder
    songs = os.listdir(folder)
    for nr, song in enumerate(songs):
        print('analysing song number {nr} of {total}: {name}'.format(nr=nr, total=len(songs), name=song[:-4]))
        try:
            song_analyser = AudioAnalyser(folder, song, printing=False, plotting=False)
            properties = song_analyser.get_properties()
            key = properties['key']['note'] + (not properties['key']['is_major'])*'m'
            filtered_properties = {
                'nr': nr,
                'song': song,
                'bpm': properties['bpm']['value'],
                'drop_start': properties['drop_start']['value'],
                'drop_end': properties['drop_end']['value'],
                'song_start': properties['song_start']['value'],
                'key': key,
                'key_number': properties['key']['key_number'],
                'is_major': properties['key']['is_major']
            }
        except Exception as e:
            print(e)
            print('Setting properties to "NOT_FOUND"')
            filtered_properties = {
                'nr': nr,
                'song': song,
                'bpm': 'NOT_FOUND',
                'drop_start': 'NOT_FOUND',
                'drop_end': 'NOT_FOUND',
                'song_start': 'NOT_FOUND',
                'key': 'NOT_FOUND',
                'key_number': 'NOT_FOUND',
                'is_major': 'NOT_FOUND'
            }

        writer.writerow(filtered_properties)
        
    file.close()
    return

def analyse_song(folder, song, plotting=False, play_drop=False, printing=True):
    if type(song) == int:
        songlist = os.listdir(folder)
        song_file = songlist[song]
    elif song[-4:] != '.mp3':
        song_file = song + '.mp3'
    else:
        song_file = song
    
    song_analyser = AudioAnalyser(folder, song_file, printing=printing)
    properties = song_analyser.get_properties()
        
    if plotting:
        song_analyser.plotter.draw_axes()
    
    if play_drop: 
        start = properties['drop_start']['value'] - 4*60/(properties['bpm']['value'])
        end = start + 8*60/(properties['bpm']['value'])
        play_song(folder, song_analyser.reader.audiosegment, start=start, end=end)
    
    return properties

def load_csv_data(csv_file):
    # Reads the properties ("drop_start", "drop_end", "key") from a csv file
    # The output is a 2D numpy array with dimensions (Nsongs x 3)

    song_data = np.array([])

    with open(csv_file, 'r') as f:
        reader = csv.DictReader(f)

        drop_start_index = reader.fieldnames.index('drop_start')
        drop_end_index = reader.fieldnames.index('drop_end')
        key_index = reader.fieldnames.index('key')

        for row in reader:
            circle_of_fifths_nr = from_key_to_circle_of_fifths(row[key_index])
            song_data = np.append(song_data, np.array([row[drop_start_index], row[drop_end_index], circle_of_fifths_nr]))

        song_data = song_data.reshape(-1,3)

    return song_data

def data_analysis(csv_path_known, csv_path_computed):
    # for every property (drop start, drop end, key) measure the mean and the standard deviation
    # outputs the results in a dictionary

    results = {
        'song_start' : {
            'mean' : 0,
            'stdev' : 0
        },
        'song_end' : {
            'mean' : 0,
            'stdev' : 0
        },
        'key' : {
            'mean' : 0,
            'stdev' : 0
        }
    }

    data_known = load_csv_data(csv_path_known)
    data_computed = load_csv_data(csv_path_computed)

    # analyse drop_start
    drop_start_diff = data_computed[:, 0] - data_known[:, 0]
    results['song_start']['mean'] = np.mean(drop_start_diff)
    results['song_start']['stdev'] = np.std(drop_start_diff)
    
    # analyse drop_end
    drop_end_diff = data_computed[:, 1] - data_known[:, 1]
    results['song_start']['mean'] = np.mean(drop_end_diff)
    results['song_start']['stdev'] = np.std(drop_end_diff)

    # analyse key
    key_diff = data_computed[:, 2] - data_known[:,2]
    key_within_bounds = ((key_diff + 6) % 12) - 6
    results['key']['mean'] = np.mean(key_within_bounds)
    results['key']['stdev'] = np.std(key_within_bounds)

    return results