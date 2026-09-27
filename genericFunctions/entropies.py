import math


def entropies_normalized(data):

    # --------------------------------------------------
    # DATA
    # --------------------------------------------------

    progressive_probs = data[0]
    progressive_counts = data[1]
    mru_counts = data[2]

    if not progressive_probs:
        return 0.0, 0.0, 0.0, 0.0


    # --------------------------------------------------
    # 1. INFORMATION CONTENT PROGRESIVO
    # --------------------------------------------------

    total_information_content = 0.0
    total_entropy = 0.0

    n_mrus = len(progressive_probs)


    for i, current_probs in enumerate(progressive_probs):

        # --------------------------------------------------
        # INFORMATION CONTENT
        # --------------------------------------------------

        mru_information_content = 0.0

        counts = mru_counts[i]

        for value, count in counts.items():

            if count > 0:

                # Probabilidad correspondiente a la
                # distribución progresiva de esta MRU
                p = current_probs.get(value, 0.0)

                if p > 0:

                    information = -math.log2(p)

                    mru_information_content += (
                        count * information
                    )

        total_information_content += (
            mru_information_content
        )


        # --------------------------------------------------
        # ENTROPY
        # --------------------------------------------------

        mru_entropy = 0.0

        for value, p in current_probs.items():

            if p > 0:

                mru_entropy -= (
                    p * math.log2(p)
                )

        total_entropy += mru_entropy


    # --------------------------------------------------
    # 2. NORMALIZACIONES
    # --------------------------------------------------

    mean_information_content = (
        total_information_content / n_mrus
    )

    mean_entropy = (
        total_entropy / n_mrus
    )


    # --------------------------------------------------
    # 3. COMPOSITE
    # --------------------------------------------------

    final_value = (
        mean_information_content
        + mean_entropy
    )


    return (
        mean_information_content,
        mean_entropy,
        0.0,       # Jensen-Shannon eliminado por ahora
        final_value
    )