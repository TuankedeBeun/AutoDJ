# TO DO:
## General
- Clean up code structure -> library
- Revise up functions -> single responsibility
## Testing
- Create testmodule
- Function: See mp3 analysis of segment in a specified range
    - raw audio signal
    - fft signal
    - bass/med/treb functions
- Function: Play an mp3 within a specified range
    - switch for drop: softer before drop, louder at drop
    - switch for BPM: play metronome tick along with music
    - switch for key: play corresponding chord before music
- Function: Save droptime(s) of an mp3 in a storage file
- Function: Save BPM in a storage file
- Function: Save key in storage file
- Function: Test all songs in a folder for droptime/BPM/key and test against known values

### notes
```
min_ratio = PH[i+1:].min()/PH[:i].min()
        max_ratio = PH[i+1:].max()/PH[:i].max()
        instant_difference = PH[i] - PH[i-1]
        instant_increment = PH[i]/PH[i-1]
        criterium[i] = PH[i]*min_ratio*max_ratio*instant_difference
```

unreliable:
>3 - slower tempo
18 - second beat higher
19 - outlier in drop
>23 - Itro - Promises
25 - drop fluctuates
>36 - two beats high
>37 - two beats high (slower tempo)
39 - two beats high (one broad)
>41 - bass buildup
43 - three peaks (better with hpf 2000 --> 10000)
45 - bass buildup
>46 - WRLD - Hang Up (slower tempo)
