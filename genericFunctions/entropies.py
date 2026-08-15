import math


def entropies_normalized(data):
    """
    Compute Shannon entropy and KL divergence for each MRU.

    Args:
        data = (
            global_probs,
            prob_bins,
            mru_counts
        )

        global_probs:
            Global probability distribution P(x).

        prob_bins:
            Probability distribution P(x | MRU)
            for each MRU.

        mru_counts:
            Frequency counts for each value in each MRU.

    Returns:
        entropy_mrus:
            Shannon entropy for each MRU, in bits.

        kl_mrus:
            KL divergence between consecutive MRUs, in bits.

        total_score:
            Sum of all entropy and KL values, in raw bits.
    """

    global_probs = data[0]
    prob_bins = data[1]
    mru_counts = data[2]

    if not mru_counts:
        return [], [], 0.0

    # ---------------------------------------------------------
    # 1. Vocabulary
    # ---------------------------------------------------------

    vocab = list(global_probs.keys())

    if not vocab:
        return (
            [0.0] * len(mru_counts),
            [0.0] * len(mru_counts),
            0.0
        )


    # ---------------------------------------------------------
    # 2. Shannon entropy per MRU
    # ---------------------------------------------------------

    entropy_mrus = []

    for probabilities in prob_bins:

        entropy = 0.0

        for p in probabilities.values():

            if p > 0:
                entropy -= p * math.log2(p)

        entropy_mrus.append(entropy)


    # ---------------------------------------------------------
    # 3. KL divergence between consecutive MRUs
    # ---------------------------------------------------------

    kl_mrus = [0.0]

    # Small smoothing value to avoid log(0)
    alpha = 1e-6


    def smoothed_dist(probabilities):

        # Add alpha to every vocabulary element
        smoothed = {
            k: probabilities.get(k, 0.0) + alpha
            for k in vocab
        }

        # Normalize so that probabilities sum to 1
        Z = sum(smoothed.values())

        return {
            k: value / Z
            for k, value in smoothed.items()
        }


    for i in range(1, len(prob_bins)):

        prev = smoothed_dist(prob_bins[i - 1])
        curr = smoothed_dist(prob_bins[i])

        kl = 0.0

        for k in vocab:

            if curr[k] > 0 and prev[k] > 0:

                kl += (
                    curr[k]
                    * math.log2(curr[k] / prev[k])
                )

        kl_mrus.append(kl)


    # ---------------------------------------------------------
    # 4. Total information score
    # ---------------------------------------------------------

    total_entropy = sum(entropy_mrus)

    total_kl = sum(kl_mrus)

    # Accumulated informational load
    total_score = total_entropy + total_kl


    return entropy_mrus, kl_mrus, total_score