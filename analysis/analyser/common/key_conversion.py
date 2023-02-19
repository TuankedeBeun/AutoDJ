TONES = ['A','Bb','B','C','C#','D','Eb','E','F','F#','G','G#']
CIRCLE_OF_FIFTHS_MAJOR = ['E','B','F#','C#','G#','Eb','Bb','F','C','G','D','A']
CIRCLE_OF_FIFTHS_MINOR = ['C#','G#','Eb','Bb','F','C','G','D','A','E','B','F#']

def from_key_to_keynumber(key):
    key_number = TONES.index(key.strip('m'))

    return key_number

def from_keynumber_to_key(key_number, is_major):
    key = TONES[key_number]
    if not is_major:
        key += 'm'

    return key

def from_key_to_circle_of_fifths(key):
    if key.endswith('m'):
        circle_number = CIRCLE_OF_FIFTHS_MINOR.index(key.strip('m'))
    else:
        circle_number = CIRCLE_OF_FIFTHS_MAJOR.index(key)

    return circle_number