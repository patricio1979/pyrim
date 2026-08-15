# Diría que los cinco indicadores fueron robustamente estandarizados mediante mediana e IQR antes del PCA.

import numpy as np
import math
from sklearn.preprocessing import RobustScaler
from sklearn.decomposition import PCA

def build_complexity_index(res):
    """
    Build a composite complexity index from five indicators:

        1. MRU
        2. Ink Amount
        3. Fifths
        4. Bits per MRU
        5. Free Energy

    Higher values of all five indicators represent greater
    informational/reading demand.

    Returns:
        loadings: PCA loadings for the five indicators
        percent: explained variance ratio of PC1
        new_ranking: ranking of pieces from most to least complex
    """

    # ---------------------------------------------------------
    # 1. Extract the five indicators
    # ---------------------------------------------------------
    # Each row of res:
    # [file_name, MRU, Ink Amount, Fifths, Bits per MRU, Free Energy, title]
    #
    # Indicators:
    # [MRU, Ink Amount, Fifths, Bits per MRU, Free Energy]

    data = np.array([
        [row[1], row[2], row[3], row[4], row[5]]
        for row in res
    ], dtype=float)


    # ---------------------------------------------------------
    # 2. Robust standardization
    # ---------------------------------------------------------
    # RobustScaler uses median and IQR, making the PCA less
    # sensitive to extreme values/outliers.

    scaler = RobustScaler()
    data_z = scaler.fit_transform(data)


    # ---------------------------------------------------------
    # 3. PCA
    # ---------------------------------------------------------
    pca = PCA(n_components=1)

    pc1_scores = pca.fit_transform(data_z).flatten()

    # PCA loadings for the five indicators
    loadings = pca.components_[0].copy()


    # ---------------------------------------------------------
    # 4. Orient the sign of PC1
    # ---------------------------------------------------------
    # The sign of a PCA component is mathematically arbitrary.
    #
    # We want:
    #
    #     higher PC1 = greater complexity/demand
    #
    # Since all five indicators are defined so that higher values
    # represent greater demand, we orient PC1 so that its loadings
    # point predominantly in the positive direction.

    if np.sum(loadings) < 0:
        loadings = -loadings
        pc1_scores = -pc1_scores


    # ---------------------------------------------------------
    # 5. Feature names
    # ---------------------------------------------------------

    feature_names = [
        'MRU',
        'Ink Amount',
        'Fifths',
        'Bits per MRU',
        'Free Energy'
    ]


    # ---------------------------------------------------------
    # 6. Ranking
    # ---------------------------------------------------------
    # Highest PC1 = greatest complexity

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