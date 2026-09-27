# Diría que los cinco indicadores fueron robustamente estandarizados mediante mediana e IQR antes del PCA.

import numpy as np
import math
from sklearn.preprocessing import RobustScaler
from sklearn.decomposition import PCA

def build_complexity_index(res):

    # ---------------------------------------------------------
    # 1. Extract the five indicators
    # ---------------------------------------------------------

    data = np.array([
        [row[1], row[2], row[3], row[4], row[5]]
        for row in res
    ], dtype=float)

    feature_names = [
        'MRU',
        'Ink Amount',
        'Fifths',
        'Bits per MRU',
        'Free Energy'
    ]

    # ---------------------------------------------------------
    # 2. Robust standardization
    # ---------------------------------------------------------

    scaler = RobustScaler()
    data_z = scaler.fit_transform(data)

    # ---------------------------------------------------------
    # 3. PCA
    # ---------------------------------------------------------

    pca = PCA(n_components=1)

    pc1_scores = pca.fit_transform(data_z).flatten()

    loadings = pca.components_[0].copy()

    # ---------------------------------------------------------
    # 5. Orient the sign of PC1
    # ---------------------------------------------------------

    if np.sum(loadings) < 0:
        loadings = -loadings
        pc1_scores = -pc1_scores

    # ---------------------------------------------------------
    # 6. Ranking
    # ---------------------------------------------------------

    titles = [row[6] for row in res]

    ranking_indices = np.argsort(-pc1_scores)

    new_ranking = []

    for rank, idx in enumerate(ranking_indices, 1):

        r = int(rank)
        filename = str(res[idx][0])
        t = str(titles[idx])
        pc1 = float(pc1_scores[idx])

        new_ranking.append([
            r,
            filename,
            t,
            pc1
        ])

    # ---------------------------------------------------------
    # 7. Explained variance
    # ---------------------------------------------------------

    if math.isnan(float(pca.explained_variance_ratio_[0])):
        percent = 0.0
    else:
        percent = float(pca.explained_variance_ratio_[0])

    # ---------------------------------------------------------
    # 8. Return
    # ---------------------------------------------------------

    return loadings.tolist(), percent, new_ranking