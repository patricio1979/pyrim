import csv
from datetime import datetime

def save_results_to_csv(info, res):
    """
    Save results to CSV with metadata and data.
    Uses csv.writer for metadata (Excel-safe), DictWriter for data.
    """
    filename = info[4]
    instrument = info[1]
    corpus_folder = info[2]
    tactus = info[3] + 1
    loadings = info[5]
    var_explained = info[6] * 100  # percentage
    app_version = info[7]
    generation_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Multilingual labels
    if info[0].lower() == 'en':
        fieldnames = [
            'File name', 'Title', 'MRU', 'Ink Amount', 'Fifths',
            'Bits per MRU', 'Free Energy', 'RIM ranking', 'Zscore'
        ]
        meta_labels = {
            'corpus': 'Corpus folder',
            'instrument': 'Instrument',
            'tactus': 'Tactus level',
            'loadings': 'PCA Loadings (MRU, Ink Amount, Fifths, Bits per MRU, Free Energy)',
            'variance': 'Variance explained by PC1',
            'version': 'App Version',
            'date': 'Date'
        }
    else:
        fieldnames = [
            'Nombre del archivo', 'Título', 'ULM', 'Cantidad de Tinta', 'Quintas',
            'Bits por ULM', 'Energía Libre', 'orden RIM', 'puntaje Z'
        ]
        meta_labels = {
            'corpus': 'Carpeta del corpus',
            'instrument': 'Instrumento',
            'tactus': 'Nivel de Tactus',
            'loadings': 'Pesos PCA (ULM, Cantidad de Tinta, Quintas, Bits por ULM, Energía Libre)',
            'variance': 'Varianza explicada por PC1',
            'version': 'Versión de la aplicación',
            'date': 'Fecha'
        }


    with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)

        # === Write Metadata Rows ===
        writer.writerow([f"{meta_labels['corpus']}", corpus_folder])
        writer.writerow([f"{meta_labels['instrument']}", instrument])
        writer.writerow([f"{meta_labels['tactus']}", tactus])
        writer.writerow([f"{meta_labels['loadings']}", loadings])
        # # Loadings row: label + values
        # loading_row = [f"{meta_labels['loadings']}"] + [f"{w:.4f}" for w in loadings]
        # # Truncate or pad to match fieldnames length if needed
        # while len(loading_row) < len(fieldnames):
        #     loading_row.append('')
        # writer.writerow(loading_row)
        writer.writerow([f"{meta_labels['variance']}", f"{var_explained:.1f}%"])
        writer.writerow([f"{meta_labels['version']}", app_version])
        writer.writerow([f"{meta_labels['date']}", generation_date])
        writer.writerow([])  # Empty row

        # === Now Write the Table Header and Data ===
        dict_writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        dict_writer.writeheader()

        for row in res:
            if info[0].lower() == 'en':
                dict_writer.writerow({
                    'File name': row[0],
                    'Title': row[6],
                    'MRU': round(row[1], 3),
                    'Ink Amount': round(row[2], 3),
                    'Fifths': round(row[3], 3),
                    'Bits per MRU': round(row[4], 3),
                    'Free Energy': round(row[5], 3),
                    'RIM ranking': row[7],
                    'Zscore': round(row[8], 4)
                })
            else:
                dict_writer.writerow({
                    'Nombre del archivo': row[0],
                    'Título': row[6],
                    'ULM': round(row[1], 3),
                    'Cantidad de Tinta': round(row[2], 3),
                    'Quintas': round(row[3], 3),
                    'Bits por ULM': round(row[4], 3),
                    'Energía Libre': round(row[5], 3),
                    'orden RIM': row[7],
                    'puntaje Z': round(row[8], 4)
                })