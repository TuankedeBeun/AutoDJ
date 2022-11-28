from analyser import analysis

if __name__ == '__main__':
    #properties = analysis.analyse_song("C:\\Users\\tuank\\Music\\Drum & Bass\\testfolder", 1, play_drop=False)
    analysis.compare_song_to_known_data(r"C:\Users\tuank\Programming\Python\AutoDJ\analysis\songtester\data\analysis_testfolder_20221123-165121.csv", 1)
