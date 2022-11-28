tones = ['A','Bb','B','C','C#','D','Eb','E','F','F#','G','G#']

def from_key_to_keynumber(key):
    key_number = tones.index(key.strip('m'))

    return key_number

def from_keynumber_to_key(key_number, is_major):
    key = tones[key_number]
    if not is_major:
        key += 'm'

    return key