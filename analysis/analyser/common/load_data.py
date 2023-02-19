from csv import DictReader

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