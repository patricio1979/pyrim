from collections import Counter

# -----> HELPERS
def frequency_count(values):
    """Return dict of {value: count} for list of values."""
    return dict(Counter(values))

def empirical_probabilities(values):
    """Return {value: probability} from list of values."""
    if not values:
        return {}
    counts = Counter(values)
    total = len(values)
    return {v: count / total for v, count in counts.items()}

def count_with_vocab(items, vocab_dict):
    """Count occurrences of items, using vocab_dict keys as full set."""
    counts = dict(vocab_dict)  # shallow copy of {key: 0, ...}
    for item in items:
        if item in counts:
            counts[item] += 1
    return counts

# ------> MAIN FUNCTION
def his_to_prob(mru_count, histo, rhythm_meas):
    """
    Prepare rhythmic distributions for later analysis (e.g., KL divergence).

    Args:
        mru_count: Number of MRU bins (int)
        histo: List of events [stave][voice][event] = [index, value, measure_num]
        rhythm_meas: Timing map [stave][voice][event] = [index, value, meas, mru_idx]

    Returns:
        (
            global_probs: {value: float},           # P(value) globally
            prob_bins:    List[List[float]],        # Per-MRU list of P(value)
            mru_counts:   List[Dict[value: int]]    # Count per MRU (KL-ready)
        )
    """
    # Step 1: Extract all valid values and assign to MRU bins
    all_values = []                    # All values across all events
    mrus = [[] for _ in range(mru_count)]  # One list per MRU bin

    for i in range(len(histo)):
        for j in range(len(histo[i])):
            # Skip empty voices
            if i >= len(rhythm_meas) or j >= len(rhythm_meas[i]):
                continue

            voice_histo = histo[i][j]
            voice_rhythm = rhythm_meas[i][j]

            for event in voice_histo:
                label = event[0]
                value = event[1]

                # Filter out hidden events
                if 'no' in label or 'add' in label:
                    continue

                # Find matching event in rhythm_meas to get MRU index
                matched = [item for item in voice_rhythm if item[0] == label]
                if not matched:
                    continue  # no timing info
                try:
                    mru_idx = int(matched[0][3])
                except (IndexError, ValueError):
                    continue

                if 0 <= mru_idx < mru_count:
                    all_values.append(value)
                    mrus[mru_idx].append(value)

    # Step 2: Compute global probabilities
    if not all_values:
        global_probs = {}
        vocab = []
    else:
        counter = Counter(all_values)
        total = len(all_values)
        global_probs = {v: count / total for v, count in counter.items()}
        vocab = list(counter.keys())

    # Step 3: Build prob_bins — replace each value with its global probability
    prob_bins = [
        [global_probs.get(val, 0.0) for val in mru_bin]
        for mru_bin in mrus
    ]

    # Step 4: Build mru_counts — frequency count per MRU, full vocabulary
    # Create template: {value: 0 for all values seen globally}
    empty_hist = {v: 0 for v in vocab} if vocab else {'no': 0}

    mru_counts = []
    for mru_bin in mrus:
        counts = dict(empty_hist)  # start with zeros
        for val in mru_bin:
            if val in counts:
                counts[val] += 1
        mru_counts.append(counts)

    return global_probs, prob_bins, mru_counts