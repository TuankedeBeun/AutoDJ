from analyser.analysis import analyse_song

if __name__ == '__main__':
    properties = analyse_song("C:\\Users\\tuank\\Music\\Drum & Bass\\testfolder", 0, play_drop=False)
    print(properties)