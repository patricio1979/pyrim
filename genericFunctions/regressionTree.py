import os
import numpy as np
import pandas as pd

import matplotlib
matplotlib.use('TkAgg')

from matplotlib import pyplot as plt

from sklearn.tree import (
    DecisionTreeRegressor,
    export_text
)

from sklearn.model_selection import (
    LeaveOneOut,
    ShuffleSplit
)

from sklearn.metrics import (
    mean_absolute_error,
    mean_squared_error,
    r2_score
)


# ==========================================================
# FUNCIÓN PRINCIPAL
# ==========================================================

def build_regression_tree(
    data,
    n_levels=5,
    loocv_threshold=20,
    repetitions=30,
    test_size=0.20,
    max_depth=3,
    min_samples_leaf=2,
    random_state=42
):
    """
    Construye un árbol de regresión para un corpus de partituras.

    INPUT
    -----
    data : lista de listas

        [
            [
                filename,
                MRU,
                Ink_amount,
                Fifths,
                Bits_x_MRU,
                Free_energy,
                title,
                PCA_ranking,
                zscore
            ],
            ...
        ]

    OUTPUT
    ------
    reporte : diccionario con:

        - MAE
        - RMSE
        - R2

        - pieces:
            [
                filename,
                title,
                PCA_ranking,
                Orden_norm,
                Prediction_from_tree
            ]

        - tree_rules
        - feature_importance
        - tree
        - features
        - dataframe

    IMPORTANTE
    ----------
    PCA_ranking se transforma a una escala ordinal 1–5:

        1 = mayor dificultad
        5 = menor dificultad

    El árbol aprende a predecir esta variable ordinal.

    La predicción del árbol se conserva como valor CONTINUO.
    """

    # ==========================================================
    # 1. COMPROBAR DATOS
    # ==========================================================

    if not data:
        raise ValueError(
            "La lista de datos está vacía."
        )

    for i, row in enumerate(data):

        if len(row) != 9:

            raise ValueError(
                f"La fila {i} tiene {len(row)} elementos. "
                "Se esperaban 9."
            )

    # ==========================================================
    # 2. CREAR DATAFRAME
    # ==========================================================

    df = pd.DataFrame(
        data,
        columns=[
            "filename",
            "MRU",
            "Ink_amount",
            "Fifths",
            "Bits_x_MRU",
            "Free_energy",
            "title",
            "PCA_ranking",
            "zscore"
        ]
    )

    # ----------------------------------------------------------
    # Texto
    # ----------------------------------------------------------

    df["filename"] = df["filename"].astype(str)

    df["title"] = df["title"].astype(str)

    # ----------------------------------------------------------
    # Variables numéricas
    # ----------------------------------------------------------

    numeric_columns = [
        "MRU",
        "Ink_amount",
        "Fifths",
        "Bits_x_MRU",
        "Free_energy",
        "PCA_ranking",
        "zscore"
    ]

    for column in numeric_columns:

        df[column] = pd.to_numeric(
            df[column],
            errors="raise"
        )

    # ==========================================================
    # 3. ORDENAR SEGÚN PCA
    # ==========================================================

    # PCA_ranking:
    #
    # 1 = mayor dificultad
    # valores mayores = menor dificultad

    df = df.sort_values(
        "PCA_ranking",
        ascending=True
    ).reset_index(
        drop=True
    )

    n = len(df)

    # ==========================================================
    # 4. GENERAR ORDEN NORMALIZADO 1–5
    # ==========================================================

    """
    Se transforma el ranking PCA, que puede ser:

        1 ... 19
        1 ... 28
        1 ... 100

    etc.,

    a una escala ordinal de 1 a 5.

        1 = mayor dificultad
        5 = menor dificultad

    Se utiliza np.array_split para distribuir
    aproximadamente de manera uniforme las piezas.
    """

    indices_por_nivel = np.array_split(
        np.arange(n),
        n_levels
    )

    orden_norm = np.empty(
        n,
        dtype=int
    )

    for nivel, indices_nivel in enumerate(
        indices_por_nivel,
        start=1
    ):

        orden_norm[indices_nivel] = nivel

    df["Orden_norm"] = orden_norm

    # ==========================================================
    # 5. VARIABLES PREDICTORAS
    # ==========================================================

    features = [
        "MRU",
        "Ink_amount",
        "Fifths",
        "Bits_x_MRU",
        "Free_energy"
    ]

    X = df[features]

    # ----------------------------------------------------------
    # VARIABLE OBJETIVO
    # ----------------------------------------------------------

    # El árbol aprende el orden normalizado 1–5.
    #
    # NO aprende PCA_ranking directamente.

    y = df["Orden_norm"]

    # ==========================================================
    # 6. VALIDACIÓN
    # ==========================================================

    if n < loocv_threshold:

        validation_method = "LOOCV"

        splitter = LeaveOneOut()

    else:

        validation_method = "80/20"

        splitter = ShuffleSplit(
            n_splits=repetitions,
            test_size=test_size,
            random_state=random_state
        )

    # ----------------------------------------------------------
    # Variables para almacenar predicciones
    # ----------------------------------------------------------

    y_true = []
    y_pred = []

    # ==========================================================
    # 7. EJECUTAR VALIDACIÓN
    # ==========================================================

    for train_index, test_index in splitter.split(X):

        X_train = X.iloc[
            train_index
        ]

        X_test = X.iloc[
            test_index
        ]

        y_train = y.iloc[
            train_index
        ]

        y_test = y.iloc[
            test_index
        ]

        # ------------------------------------------------------
        # Crear árbol
        # ------------------------------------------------------

        tree = DecisionTreeRegressor(

            max_depth=max_depth,

            min_samples_leaf=min_samples_leaf,

            random_state=random_state
        )

        # ------------------------------------------------------
        # Entrenar
        # ------------------------------------------------------

        tree.fit(
            X_train,
            y_train
        )

        # ------------------------------------------------------
        # Predecir
        # ------------------------------------------------------

        prediction = tree.predict(
            X_test
        )

        # ------------------------------------------------------
        # Guardar
        # ------------------------------------------------------

        y_true.extend(
            y_test.to_numpy()
        )

        y_pred.extend(
            prediction
        )

    # ==========================================================
    # 8. CONVERTIR A NUMPY
    # ==========================================================

    y_true = np.asarray(
        y_true
    )

    y_pred = np.asarray(
        y_pred
    )

    # ==========================================================
    # 9. MÉTRICAS
    # ==========================================================

    mae = mean_absolute_error(
        y_true,
        y_pred
    )

    rmse = np.sqrt(
        mean_squared_error(
            y_true,
            y_pred
        )
    )

    r2 = r2_score(
        y_true,
        y_pred
    )

    # ==========================================================
    # 10. ÁRBOL DEFINITIVO
    # ==========================================================

    final_tree = DecisionTreeRegressor(

        max_depth=max_depth,

        min_samples_leaf=min_samples_leaf,

        random_state=random_state
    )

    final_tree.fit(
        X,
        y
    )

    # ==========================================================
    # 11. PREDICCIÓN CONTINUA
    # ==========================================================

    tree_prediction = final_tree.predict(
        X
    )

    # ----------------------------------------------------------
    # MUY IMPORTANTE
    # ----------------------------------------------------------
    #
    # NO hacemos:
    #
    # np.rint()
    #
    # ni:
    #
    # astype(int)
    #
    # ni:
    #
    # np.clip()
    #
    # porque queremos conservar la predicción continua.
    #
    # Ejemplos:
    #
    # 1.00
    # 1.43
    # 2.17
    # 2.50
    # 3.82
    # 4.61
    # 5.00
    #
    # ----------------------------------------------------------

    df["Prediction_from_tree"] = (
        tree_prediction
    )

    # ==========================================================
    # 12. RESULTADOS POR PARTITURA
    # ==========================================================

    pieces = []

    for _, row in df.iterrows():

        pieces.append(
            [
                str(row["filename"]),

                str(row["title"]),

                int(row["PCA_ranking"]),

                int(row["Orden_norm"]),

                float(
                    row["Prediction_from_tree"]
                )
            ]
        )

    # ==========================================================
    # 13. REGLAS DEL ÁRBOL
    # ==========================================================

    tree_rules = export_text(
        final_tree,

        feature_names=features,

        decimals=3
    )

    # ==========================================================
    # 14. IMPORTANCIA DE VARIABLES
    # ==========================================================

    feature_importance = {}

    for feature, importance in zip(
        features,
        final_tree.feature_importances_
    ):

        feature_importance[feature] = (
            float(importance)
        )

    # ==========================================================
    # 15. REPORTE
    # ==========================================================

    reporte = {

        "n": n,

        "n_levels": n_levels,

        "validation": validation_method,

        "repetitions": (
            n
            if validation_method == "LOOCV"
            else repetitions
        ),

        "test_size": (
            None
            if validation_method == "LOOCV"
            else test_size
        ),

        "MAE": float(mae),

        "RMSE": float(rmse),

        "R2": float(r2),

        "pieces": pieces,

        "tree_rules": tree_rules,

        "feature_importance":
            feature_importance,

        "tree": final_tree,

        "features": features,

        "dataframe": df
    }

    return reporte
'''
    # ==========================================================
    # 16. INFORMACIÓN EN CONSOLA
    # ==========================================================

    print()

    print(
        "========== ÁRBOL DE REGRESIÓN =========="
    )

    print(
        f"Corpus       : {n} partituras"
    )

    print(
        f"Niveles      : {n_levels}"
    )

    print(
        f"Validación   : {validation_method}"
    )

    if validation_method == "LOOCV":

        print(
            f"Repeticiones : {n}"
        )

    else:

        print(
            f"Repeticiones : {repetitions}"
        )

        print(
            f"Test         : {test_size * 100:.0f}%"
        )

    print()

    print(
        "========== VARIABLE OBJETIVO =========="
    )

    print(
        "Orden normalizado: 1–5"
    )

    print(
        "1 = mayor dificultad"
    )

    print(
        "5 = menor dificultad"
    )

    print()

    print(
        "========== VALIDACIÓN =========="
    )

    print(
        f"MAE  : {mae:.3f}"
    )

    print(
        f"RMSE : {rmse:.3f}"
    )

    print(
        f"R²   : {r2:.3f}"
    )

    print()

    print(
        "========== ÁRBOL DEFINITIVO =========="
    )

    print(
        tree_rules
    )

    print()

    print(
        "========== IMPORTANCIA DE VARIABLES =========="
    )

    for feature, importance in (
        feature_importance.items()
    ):

        print(
            f"{feature:20s}: "
            f"{importance:.3f}"
        )

    print()

    print(
        "========== RESULTADOS =========="
    )

    print(
        "[filename, title, PCA ranking, "
        "Orden norm., Prediction from tree]"
    )

    for piece in pieces:

        print(
            piece
        )
'''
    


# ==============================================================
# FUNCIÓN PARA GENERAR LA IMAGEN DEL ÁRBOL
# ==============================================================

def save_regression_tree_image(
    reporte,
    image_path="regression_tree.png",
    language="en"
):
    """
    Genera y guarda manualmente la imagen del árbol
    de regresión.

    La predicción mostrada en las hojas es CONTINUA.

    Parameters
    ----------
    reporte :
        Diccionario generado por build_regression_tree()

    image_path :
        Ruta donde se guardará la imagen.

    language :
        'en' para inglés.
        Cualquier otro valor para español.
    """

    # ==========================================================
    # 1. IDIOMA
    # ==========================================================

    if language.lower() == "en":

        title = (
            "RIM's Regression Tree for the corpus"
        )

        prediction_label = (
            "Prediction"
        )

        samples_label = (
            "Samples"
        )

    else:

        title = (
            "Árbol de regresión RIM para el corpus"
        )

        prediction_label = (
            "Predicción"
        )

        samples_label = (
            "Muestras"
        )

    # ==========================================================
    # 2. OBTENER ÁRBOL
    # ==========================================================

    tree = reporte["tree"]

    features = reporte["features"]

    tree_structure = tree.tree_

    n_nodes = tree_structure.node_count

    # ==========================================================
    # 3. CREAR FIGURA
    # ==========================================================

    fig, ax = plt.subplots(
        figsize=(14, 8)
    )

    ax.axis("off")

    # ==========================================================
    # 4. CALCULAR PROFUNDIDAD
    # ==========================================================

    depths = np.zeros(
        n_nodes,
        dtype=int
    )

    def calculate_depth(
        node,
        depth
    ):

        depths[node] = depth

        left = (
            tree_structure.children_left[node]
        )

        right = (
            tree_structure.children_right[node]
        )

        if left != -1:

            calculate_depth(
                left,
                depth + 1
            )

        if right != -1:

            calculate_depth(
                right,
                depth + 1
            )

    calculate_depth(
        0,
        0
    )

    max_depth_tree = depths.max()

    # ==========================================================
    # 5. CALCULAR POSICIONES
    # ==========================================================

    positions = {}

    leaf_counter = [0]

    def calculate_positions(
        node
    ):

        left = (
            tree_structure.children_left[node]
        )

        right = (
            tree_structure.children_right[node]
        )

        # ------------------------------------------------------
        # HOJA
        # ------------------------------------------------------

        if (
            left == -1
            and right == -1
        ):

            x = leaf_counter[0]

            leaf_counter[0] += 1

            positions[node] = x

            return x

        # ------------------------------------------------------
        # NODO DE DECISIÓN
        # ------------------------------------------------------

        left_x = calculate_positions(
            left
        )

        right_x = calculate_positions(
            right
        )

        x = (
            left_x + right_x
        ) / 2

        positions[node] = x

        return x

    calculate_positions(
        0
    )

    n_leaves = max(
        leaf_counter[0],
        1
    )

    # ==========================================================
    # 6. COLORES
    # ==========================================================

    left_line_color = "#808080"

    right_line_color = "#B45F5F"

    decision_face_color = "#CFE2F3"

    decision_edge_color = "#1155CC"

    leaf_face_color = "#D9EAD3"

    leaf_edge_color = "#38761D"

    # ==========================================================
    # 7. DIBUJAR CONEXIONES
    # ==========================================================

    for node in range(n_nodes):

        left = (
            tree_structure.children_left[node]
        )

        right = (
            tree_structure.children_right[node]
        )

        x_parent = positions[node]

        y_parent = -depths[node]

        # ------------------------------------------------------
        # Rama izquierda
        # ------------------------------------------------------

        if left != -1:

            x_child = positions[left]

            y_child = -depths[left]

            ax.plot(
                [x_parent, x_child],
                [y_parent, y_child],
                color=left_line_color,
                linewidth=2
            )

        # ------------------------------------------------------
        # Rama derecha
        # ------------------------------------------------------

        if right != -1:

            x_child = positions[right]

            y_child = -depths[right]

            ax.plot(
                [x_parent, x_child],
                [y_parent, y_child],
                color=right_line_color,
                linewidth=2
            )

    # ==========================================================
    # 8. DIBUJAR NODOS
    # ==========================================================

    for node in range(n_nodes):

        x = positions[node]

        y = -depths[node]

        left = (
            tree_structure.children_left[node]
        )

        right = (
            tree_structure.children_right[node]
        )

        # ------------------------------------------------------
        # Determinar si es hoja
        # ------------------------------------------------------

        is_leaf = (
            left == -1
            and right == -1
        )

        # ======================================================
        # NODO DE DECISIÓN
        # ======================================================

        if not is_leaf:

            feature_index = (
                tree_structure.feature[node]
            )

            threshold = (
                tree_structure.threshold[node]
            )

            feature_name = (
                features[feature_index]
            )

            text = (
                f"{feature_name}\n"
                f"≤ {threshold:.2f}"
            )

            bbox = dict(
                boxstyle="round,pad=0.5",
                facecolor=decision_face_color,
                edgecolor=decision_edge_color,
                linewidth=1.8
            )

        # ======================================================
        # HOJA
        # ======================================================

        else:

            samples = (
                tree_structure.n_node_samples[node]
            )

            prediction = (
                tree_structure.value[node][0][0]
            )

            # --------------------------------------------------
            # IMPORTANTE:
            #
            # prediction NO se redondea.
            # --------------------------------------------------

            text = (
                f"{prediction_label} = "
                f"{prediction:.2f}\n"
                f"{samples_label}: {samples}"
            )

            bbox = dict(
                boxstyle="round,pad=0.5",
                facecolor=leaf_face_color,
                edgecolor=leaf_edge_color,
                linewidth=1.8
            )

        # ======================================================
        # DIBUJAR NODO
        # ======================================================

        ax.text(
            x,
            y,
            text,
            ha="center",
            va="center",
            fontsize=10,
            bbox=bbox
        )

    # ==========================================================
    # 9. LOGO
    # ==========================================================

    logo_path = os.path.join(
        "imgs",
        "pyRIM_logo.png"
    )

    if os.path.exists(
        logo_path
    ):

        logo = plt.imread(
            logo_path
        )

        # ------------------------------------------------------
        # Logo grande
        # ------------------------------------------------------

        logo_ax = fig.add_axes(
            [
                0.02,
                0.78,
                0.20,
                0.20
            ]
        )

        logo_ax.imshow(
            logo
        )

        logo_ax.axis(
            "off"
        )

    else:

        print(
            f"⚠️ Logo not found: {logo_path}"
        )

    # ==========================================================
    # 10. TÍTULO
    # ==========================================================

    ax.set_title(
        title,
        fontsize=16,
        pad=20
    )

    # ==========================================================
    # 11. LÍMITES
    # ==========================================================

    ax.set_xlim(
        -0.8,
        max(
            n_leaves - 1,
            0
        ) + 0.8
    )

    ax.set_ylim(
        -max_depth_tree - 0.7,
        0.7
    )

    # ==========================================================
    # 12. GUARDAR
    # ==========================================================

    # NO usar tight_layout().
    #
    # El logo está en un segundo Axes y
    # tight_layout() produce el warning:
    #
    # "This figure includes Axes that are not compatible
    # with tight_layout"

    plt.savefig(
        image_path,
        dpi=300,
        bbox_inches="tight"
    )

    # ==========================================================
    # 13. CERRAR
    # ==========================================================

    plt.close(
        fig
    )

    print(
        f"🌳 Regression tree image saved to: "
        f"{image_path}"
    )

    return image_path