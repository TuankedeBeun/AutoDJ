import numpy as np

def assign_score_to_offset(offset_seconds, bpm=174, short_long_ratio=3):
    beat_seconds = 60 / bpm
    bar_seconds = 4 * beat_seconds
    measure_seconds = 4 * bar_seconds
    durations = np.array([beat_seconds, bar_seconds, measure_seconds])
    weights = np.array([1, 1 / short_long_ratio, 1 / short_long_ratio ** 2])
    weights /= weights.sum()
    
    score_per_weight = weights[:, None] * np.exp( -1 * np.outer(1 / durations, offset_seconds) ** 2)

    total_score = score_per_weight.sum(axis = 0)
    return total_score