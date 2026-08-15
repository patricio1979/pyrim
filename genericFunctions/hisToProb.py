from collections import Counter


# -----> HELPERS

def frequency_count(values):
    """Return dict of {value: count} for list of values."""
    return dict(Counter(values))


def empirical_probabilities(values):
    """Return {value: probability} from a list of values."""
    if not values:
        return {}

    counts = Counter(values)
    total = len(values)

    return {
        value: count / total
        for value, count in counts.items()
    }


def count_with_vocab(items, vocab_dict):
    """Count occurrences of items using vocab_dict keys as full vocabulary."""
    counts = dict(vocab_dict)

    for item in items:
        if item in counts:
            counts[item] += 1

    return counts


# ------> MAIN FUNCTION

def his_to_prob(mru_count, histo, rhythm_meas):
    """
    Organize notation events by MRU and calculate their
    empirical probability distributions.

    Args:
        mru_count:
            Number of MRU bins.

        histo:
            List of events:
            [stave][voice][event] = [index, value, measure_num]

        rhythm_meas:
            Timing map:
            [stave][voice][event] = [index, value, measure_num, mru_idx]

    Returns:
        global_probs:
            Dictionary containing P(value) globally.

        prob_bins:
            List of dictionaries containing P(value | MRU).

        mru_counts:
            List of dictionaries containing frequency counts
            for each value in each MRU.
    """

    # ---------------------------------------------------------
    # 1. Collect values and assign them to their MRU
    # ---------------------------------------------------------

    all_values = []

    # One list of values for each MRU
    mrus = [[] for _ in range(mru_count)]

    for i in range(len(histo)):

        # Avoid index mismatch between histo and rhythm_meas
        if i >= len(rhythm_meas):
            continue

        for j in range(len(histo[i])):

            if j >= len(rhythm_meas[i]):
                continue

            voice_histo = histo[i][j]
            voice_rhythm = rhythm_meas[i][j]

            for event in voice_histo:

                label = event[0]
                value = event[1]

                # Ignore hidden/artificial events
                if 'no' in label or 'add' in label:
                    continue

                # Find the corresponding rhythmic event
                matched = [
                    item
                    for item in voice_rhythm
                    if item[0] == label
                ]

                if not matched:
                    continue

                try:
                    mru_idx = int(matched[0][3])
                except (IndexError, ValueError, TypeError):
                    continue

                # Make sure the MRU exists
                if 0 <= mru_idx < mru_count:

                    all_values.append(value)
                    mrus[mru_idx].append(value)


    # ---------------------------------------------------------
    # 2. Global vocabulary and global probabilities
    # ---------------------------------------------------------

    if all_values:

        global_counter = Counter(all_values)

        total = len(all_values)

        global_probs = {
            value: count / total
            for value, count in global_counter.items()
        }

        vocab = list(global_counter.keys())

    else:

        global_probs = {}
        vocab = []


    # ---------------------------------------------------------
    # 3. Frequency distribution for every MRU
    # ---------------------------------------------------------

    empty_hist = {
        value: 0
        for value in vocab
    }

    mru_counts = []

    for mru_bin in mrus:

        counts = dict(empty_hist)

        for value in mru_bin:

            if value in counts:
                counts[value] += 1

        mru_counts.append(counts)


    # ---------------------------------------------------------
    # 4. Probability distribution for every MRU
    # ---------------------------------------------------------

    prob_bins = []

    for counts in mru_counts:

        total = sum(counts.values())

        if total == 0:

            probabilities = {
                value: 0.0
                for value in vocab
            }

        else:

            probabilities = {
                value: count / total
                for value, count in counts.items()
            }

        prob_bins.append(probabilities)


    return global_probs, prob_bins, mru_counts