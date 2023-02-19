import numpy as np
from csv import DictReader
from common.key_conversion import from_key_to_circle_of_fifths

def load_data_from_csv(csv_path):
    csv_data = open(csv_path, mode='r')
    dict_reader = DictReader(csv_data, delimiter=';')
    songs = []

    for song_data in dict_reader:
        drop_start = float(song_data['drop start'])
        drop_end = float(song_data['drop end'])
        if song_data['key'] == 'None':
            key = None
        else:
            key = song_data['key']

        song = {
            'file': song_data['song'],
            'drop_start': drop_start,
            'drop_end': drop_end,
            'key': key
        }
        songs.append(song)

    return songs

def load_csv_data_to_nparray(csv_file):
    # Reads the properties ("drop_start", "drop_end", "key") from a csv file
    # The output is a 2D numpy array with dimensions (Nsongs x 3)

    song_data = np.array([])

    with open(csv_file, 'r') as f:
        reader = DictReader(f, delimiter=';')

        # drop_start_index = reader.fieldnames.index('drop_start')
        # drop_end_index = reader.fieldnames.index('drop_end')
        # key_index = reader.fieldnames.index('key')

        for row in reader:
            if row['key'] == 'NOT_FOUND':
                print('Song {title} has undetermined properties, so its properties will be set to "-1"'.format(title=row['song']))
                song_data = np.append(song_data, np.array([-1, -1, -1]))
                continue

            circle_of_fifths_nr = from_key_to_circle_of_fifths(row['key'])
            song_data = np.append(song_data, np.array([float(row['drop_start']), float(row['drop_end']), circle_of_fifths_nr]))

        song_data = song_data.reshape(-1,3)

    return song_data