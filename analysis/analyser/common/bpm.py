def calculate_bpm_from_drop(drop_start, drop_end):
    diff_minutes = (drop_end - drop_start)/60
    bpm_prev = 0
    bpm_prev_diff = 174

    for i in range(0, 100):
        bpm = 16*i/diff_minutes
        bpm_diff = abs(bpm - 174)

        if (bpm_prev_diff < bpm_diff):
            break
        else:
            bpm_prev = bpm
            bpm_prev_diff = bpm_diff

    return bpm_prev