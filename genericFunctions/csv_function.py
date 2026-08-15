import csv
from datetime import datetime


def save_results_to_csv(info, res, regression=None):
    """
    Save results to CSV with metadata and data.

    Columns:

    File name
    Title
    MRU
    Ink Amount
    Fifths
    Bits per MRU
    Free Energy
    PCA ranking
    Zscore
    Ranking norm.
    Prediction from tree

    "Ranking norm." is ordinal 1–5.

    "Prediction from tree" is the continuous
    regression-tree prediction.
    """

    output_filename = info[4]
    instrument = info[1]
    corpus_folder = info[2]
    tactus = info[3] + 1
    loadings = info[5]
    var_explained = info[6] * 100
    app_version = info[7]

    generation_date = datetime.now().strftime(
        "%Y-%m-%d %H:%M:%S"
    )

    # ==========================================================
    # 1. IDIOMA
    # ==========================================================

    if info[0].lower() == 'en':

        fieldnames = [
            'File name',
            'Title',
            'MRU',
            'Ink Amount',
            'Fifths',
            'Bits per MRU',
            'Free Energy',
            'PCA ranking',
            'Zscore'
        ]

        if regression is not None:

            fieldnames.extend([
                'Ranking norm.',
                'Prediction from tree'
            ])

        meta_labels = {

            'rim_metadata':
                'RIM Metadata',

            'pca_metadata':
                'PCA Metadata',

            'corpus':
                'Corpus folder',

            'instrument':
                'Instrument',

            'tactus':
                'Tactus level',

            'loadings':
                'Loadings (MRU, Ink Amount, Fifths, Bits per MRU, Free Energy)',

            'variance':
                'Variance explained by PC1',

            'version':
                'App Version',

            'date':
                'Date',

            'regression_metadata':
                'Regression Tree metadata',

            'feature_importance':
                'Feature Importance (MRU, Ink Amount, Fifths, Bits per MRU, Free Energy)',

            'tree_object':
                'Decision Tree Regressor'
        }

    else:

        fieldnames = [
            'Nombre del archivo',
            'Título',
            'ULM',
            'Cantidad de Tinta',
            'Quintas',
            'Bits por ULM',
            'Energía Libre',
            'Orden PCA',
            'puntaje Z'
        ]

        if regression is not None:

            fieldnames.extend([
                'Orden norm.',
                'Predicción del árbol'
            ])

        meta_labels = {

            'rim_metadata':
                'Metadatos RIM',

            'pca_metadata':
                'Metadatos PCA',

            'corpus':
                'Carpeta del corpus',

            'instrument':
                'Instrumento',

            'tactus':
                'Nivel de Tactus',

            'loadings':
                'Pesos (ULM, Cantidad de Tinta, Quintas, Bits por ULM, Energía Libre)',

            'variance':
                'Varianza explicada por PC1',

            'version':
                'Versión de la aplicación',

            'date':
                'Fecha',

            'regression_metadata':
                'Metadatos del árbol de regresión',

            'feature_importance':
                'Importancia de características (ULM, Cantidad de Tinta, Quintas, Bits por ULM, Energía Libre)',

            'tree_object':
                'Árbol de decisión por regresión'
        }

    # ==========================================================
    # 2. MAPEAR RESULTADOS DEL ÁRBOL
    # ==========================================================

    filename_to_normalized = {}
    filename_to_prediction = {}

    if (
        regression is not None
        and 'dataframe' in regression
    ):

        regression_df = regression['dataframe']

        for _, row in regression_df.iterrows():

            piece_filename = str(
                row['filename']
            )

            filename_to_normalized[
                piece_filename
            ] = int(
                row['Orden_norm']
            )

            filename_to_prediction[
                piece_filename
            ] = float(
                row['Prediction_from_tree']
            )

    # ==========================================================
    # 3. ESCRIBIR CSV
    # ==========================================================

    with open(
        output_filename,
        'w',
        newline='',
        encoding='utf-8'
    ) as csvfile:

        writer = csv.writer(csvfile)

        # ======================================================
        # RIM METADATA
        # ======================================================

        writer.writerow([
            meta_labels['rim_metadata']
        ])

        writer.writerow([
            meta_labels['corpus'],
            corpus_folder
        ])

        writer.writerow([
            meta_labels['instrument'],
            instrument
        ])

        writer.writerow([
            meta_labels['tactus'],
            tactus
        ])

        writer.writerow([
            meta_labels['version'],
            app_version
        ])

        writer.writerow([
            meta_labels['date'],
            generation_date
        ])

        # ======================================================
        # PCA METADATA
        # ======================================================

        writer.writerow([])

        writer.writerow([
            meta_labels['pca_metadata']
        ])

        loadings_str = (
            '[' +
            ', '.join(
                [f"{w:.4f}" for w in loadings]
            ) +
            ']'
        )

        writer.writerow([
            meta_labels['loadings'],
            loadings_str
        ])

        writer.writerow([
            meta_labels['variance'],
            f"{var_explained:.1f}%"
        ])

        # ======================================================
        # REGRESSION METADATA
        # ======================================================

        if regression is not None:

            writer.writerow([])

            writer.writerow([
                meta_labels['regression_metadata']
            ])

            if info[0].lower() == 'en':

                writer.writerow([
                    'Samples',
                    regression['n']
                ])

                writer.writerow([
                    'Number of levels',
                    regression['n_levels']
                ])

                writer.writerow([
                    'Validation method',
                    regression['validation']
                ])

                writer.writerow([
                    'Repetitions',
                    regression['repetitions']
                ])

                writer.writerow([
                    'Test size',
                    regression['test_size']
                    if regression['test_size'] is not None
                    else 'N/A'
                ])

                writer.writerow([
                    'MAE',
                    f"{regression['MAE']:.4f}"
                ])

                writer.writerow([
                    'RMSE',
                    f"{regression['RMSE']:.4f}"
                ])

                writer.writerow([
                    'R²',
                    f"{regression['R2']:.4f}"
                ])

            else:

                writer.writerow([
                    'Muestras',
                    regression['n']
                ])

                writer.writerow([
                    'Número de niveles',
                    regression['n_levels']
                ])

                writer.writerow([
                    'Método de validación',
                    regression['validation']
                ])

                writer.writerow([
                    'Repeticiones',
                    regression['repetitions']
                ])

                writer.writerow([
                    'Tamaño de prueba',
                    regression['test_size']
                    if regression['test_size'] is not None
                    else 'N/A'
                ])

                writer.writerow([
                    'MAE',
                    f"{regression['MAE']:.4f}"
                ])

                writer.writerow([
                    'RMSE',
                    f"{regression['RMSE']:.4f}"
                ])

                writer.writerow([
                    'R²',
                    f"{regression['R2']:.4f}"
                ])

            # ==================================================
            # FEATURE IMPORTANCE
            # ==================================================

            importance_values = [
                f"{regression['feature_importance'].get(feature, 0.0):.4f}"
                for feature in [
                    'MRU',
                    'Ink_amount',
                    'Fifths',
                    'Bits_x_MRU',
                    'Free_energy'
                ]
            ]

            importance_str = (
                '[' +
                ', '.join(importance_values) +
                ']'
            )

            writer.writerow([
                meta_labels['feature_importance'],
                importance_str
            ])

            # ==================================================
            # TREE OBJECT
            # ==================================================

            tree_str = str(
                regression['tree']
            )

            if info[0].lower() == 'en':

                tree_str = tree_str.replace(
                    'DecisionTreeRegressor',
                    'Decision Tree Regressor '
                )

            else:

                tree_str = tree_str.replace(
                    'DecisionTreeRegressor',
                    'Árbol de decisión por regresión '
                )

            writer.writerow([
                meta_labels['tree_object'],
                tree_str
            ])

        # ======================================================
        # TABLA PRINCIPAL
        # ======================================================

        writer.writerow([])

        dict_writer = csv.DictWriter(
            csvfile,
            fieldnames=fieldnames
        )

        dict_writer.writeheader()

        # ======================================================
        # ESCRIBIR RESULTADOS
        # ======================================================

        for row in res:

            piece_filename = str(row[0])

            if info[0].lower() == 'en':

                data_row = {

                    'File name':
                        row[0],

                    'Title':
                        row[6],

                    'MRU':
                        round(row[1], 3),

                    'Ink Amount':
                        round(row[2], 3),

                    'Fifths':
                        round(row[3], 3),

                    'Bits per MRU':
                        round(row[4], 3),

                    'Free Energy':
                        round(row[5], 3),

                    'PCA ranking':
                        row[7],

                    'Zscore':
                        round(row[8], 4)
                }

                if regression is not None:

                    data_row[
                        'Ranking norm.'
                    ] = filename_to_normalized[
                        piece_filename
                    ]

                    data_row[
                        'Prediction from tree'
                    ] = round(
                        filename_to_prediction[
                            piece_filename
                        ],
                        4
                    )

                dict_writer.writerow(
                    data_row
                )

            else:

                data_row = {

                    'Nombre del archivo':
                        row[0],

                    'Título':
                        row[6],

                    'ULM':
                        round(row[1], 3),

                    'Cantidad de Tinta':
                        round(row[2], 3),

                    'Quintas':
                        round(row[3], 3),

                    'Bits por ULM':
                        round(row[4], 3),

                    'Energía Libre':
                        round(row[5], 3),

                    'Orden PCA':
                        row[7],

                    'puntaje Z':
                        round(row[8], 4)
                }

                if regression is not None:

                    data_row[
                        'Orden norm.'
                    ] = filename_to_normalized[
                        piece_filename
                    ]

                    data_row[
                        'Predicción del árbol'
                    ] = round(
                        filename_to_prediction[
                            piece_filename
                        ],
                        4
                    )

                dict_writer.writerow(
                    data_row
                )