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
    Organize notation events by MRU and calculate
    progressive empirical probability distributions.

    Returns:
        progressive_probs:
            P(value) accumulated progressively up to each MRU.

        progressive_counts:
            Accumulated counts up to each MRU.

        mru_counts:
            Counts belonging only to each individual MRU.
    """

    # ---------------------------------------------------------
    # 1. Assign events to their MRU
    # ---------------------------------------------------------

    mrus = [[] for _ in range(mru_count)]

    for i in range(len(histo)):

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

                if 'no' in label or 'add' in label:
                    continue

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

                if 0 <= mru_idx < mru_count:
                    mrus[mru_idx].append(value)

    # ---------------------------------------------------------
    # 2. Counts within each individual MRU
    # ---------------------------------------------------------

    mru_counts = []

    for mru_bin in mrus:
        mru_counts.append(dict(Counter(mru_bin)))

    # ---------------------------------------------------------
    # 3. Progressive cumulative counts and probabilities
    # ---------------------------------------------------------

    progressive_counts = []
    progressive_probs = []

    cumulative_counts = Counter()

    for i in range(mru_count):

        # Add current MRU to accumulated history
        cumulative_counts.update(mru_counts[i])

        counts_i = dict(cumulative_counts)

        progressive_counts.append(counts_i)

        total = sum(counts_i.values())

        if total == 0:
            probabilities_i = {}

        else:
            probabilities_i = {
                value: count / total
                for value, count in counts_i.items()
            }

        progressive_probs.append(probabilities_i)

    return progressive_probs, progressive_counts, mru_counts