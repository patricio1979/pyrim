import math

def entropies_normalized(data):
    """
    Compute true Shannon entropy and KL divergence in raw bits (not normalized).
    
    Args:
        data = (global_probs, prob_bins, mru_counts)
        
    Returns:
        entropy_mrus: List[float] – true entropy per MRU (in bits)
        kl_mrus:      List[float] – D_KL(MRU_i || MRU_{i-1}) (in bits)
        total_score:  float       – sum(entropy_mrus) + sum(kl_mrus) [raw bits]
    """
    mru_counts = data[2]
    if not mru_counts:
        return [], [], 0.0
    
    vocab = list(data[0].keys()) if data[0] else ['no']
    n_classes = len(vocab)
    
    # === 1. True Shannon Entropy per MRU (in bits) ===
    def entropy_from_counts(count_dict):
        total = sum(count_dict.values())
        if total == 0:
            return 0.0
        probs = [c / total for c in count_dict.values()]
        return -sum(p * math.log2(p) for p in probs if p > 0)
    
    entropy_mrus = [entropy_from_counts(counts) for counts in mru_counts]
    
    # Max theoretical entropy (kept only for potential use — not used in output)
    max_H = math.log2(n_classes) if n_classes > 1 else 1.0
    
    # === 2. KL Divergence Between Consecutive MRUs (in bits) ===
    kl_mrus = [0.0]  # No prior for first MRU
    alpha = 1e-6     # Smoothing to avoid zero probabilities
    
    def smoothed_dist(count_dict):
        Z = sum(count_dict.get(k, 0) + alpha for k in vocab)
        return {k: (count_dict.get(k, 0) + alpha) / Z for k in vocab}
    
    for i in range(1, len(mru_counts)):
        prev = smoothed_dist(mru_counts[i-1])
        curr = smoothed_dist(mru_counts[i])
        
        kl = 0.0
        for k in vocab:
            if curr[k] > 0 and prev[k] > 0:
                kl += curr[k] * math.log2(curr[k] / prev[k])
        kl_mrus.append(kl)
    
    # === 3. Total Score = Sum of All Bits (Entropy + KL) ===
    total_entropy = sum(entropy_mrus)
    total_kl = sum(kl_mrus)
    total_score = total_entropy + total_kl  # Now in raw bits, e.g., 154.671

    return entropy_mrus, kl_mrus, total_score