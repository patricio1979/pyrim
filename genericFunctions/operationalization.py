import numpy as np
import math
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA

def build_complexity_index(res):
    # Extract the 5 indicators (columns 4 to 8)
    # Each row: [MRU, Ink Amount, Fifths, Bits per MRU, Free Energy]
    data = np.array([[row[1], row[2], row[3], row[4], row[5]] for row in res])

    # Standardize using z-scores
    scaler = StandardScaler()
    data_z = scaler.fit_transform(data)  # Shape: (19, 5)

    # Apply PCA
    pca = PCA(n_components=1)  # We want the first principal component
    pc1_scores = pca.fit_transform(data_z)  # (19, 1) — the composite scores

    # Get PCA loadings (weights for each standardized indicator)
    loadings = pca.components_[0]  # Shape: (5,) — one weight per variable

    # Feature names for clarity
    feature_names = ['MRU', 'Ink Amount', 'Fifths', 'Bits per MRU', 'Free Energy']

    # # Print PCA loadings (these are the weights)
    # print("PCA Loadings (Weights) for PC1:")
    # print("-" * 40)
    # for name, weight in zip(feature_names, loadings):
    #     print(f"{name:<13} : {weight:7.3f}")

    # # Explained variance
    # print(f"\nVariance explained by PC1: {pca.explained_variance_ratio_[0]:.1%}")

    # Create ranking based on PC1 scores
    titles = [row[1] for row in res]  # Title = row[1]
    ranking_indices = np.argsort(-pc1_scores.flatten())  # Descending order

    # print("\nRanking (from most to least complex):")
    # print("-" * 40)
    new_ranking = []
    for rank, idx in enumerate(ranking_indices, 1):
        # print(f"{rank:2d}. {titles[idx]:2d} (PC1 = {pc1_scores[idx][0]:.3f})")
        r = int(rank)
        t = str(titles[idx])
        pc1 = float(pc1_scores[idx][0])
        new_ranking.append([r,t,pc1])

    if math.isnan(float(pca.explained_variance_ratio_[0])):
        percent = 0
    else:
        percent = float(pca.explained_variance_ratio_[0])

    return loadings.tolist(),percent,new_ranking