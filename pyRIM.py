'''
pyRIM, an open-source software to quantify what is possible of the readability of musical scores.

TODO: 
* Implement all musicXML elements
* Implement MIDI version, and other music files
'''
import xml.etree.ElementTree as ET
import os
import platform
import ast
from tkinter import filedialog
import zipfile
import tempfile


from genericFunctions.gatherElts import * 
from genericFunctions.mru import *
from genericFunctions.hisToProb import *
from genericFunctions.organize import *
from genericFunctions.entropies import *
from genericFunctions.histoFifths import *
from genericFunctions.histoRhythm import *
from genericFunctions.pixelParsing import *
from genericFunctions.gui_generation import *
from genericFunctions.operationalization import * 
from genericFunctions.csv_function import *
from genericFunctions.regressionTree import *

# --- Helper PyInstaller path ---
import sys
import os
def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

# --- Main program starts here ---
current_version = 'pyRIM v0.08 beta_open'
# TEXT DEFINITIONS
dynWords = open(resource_path('textDefinitions/thesaurusDynamics.txt'), 'r')
exprWords = open(resource_path('textDefinitions/thesaurusExpression.txt'), 'r')
repWords = open(resource_path('textDefinitions/thesaurusRepetition.txt'), 'r')
alterWords = open(resource_path('textDefinitions/thesaurusAccidentals.txt'), 'r')
with open(resource_path('textDefinitions/thesaurusCharacter.json')) as f:
    data = f.read()
characters = ast.literal_eval(data)

# GLOBAL VARS and DICTIONARIES
results = []

# Rhythm configurations
fig = {'maxima': 8.0, 'long': 4.0, 'breve': 2.0, 'whole': 1.0, 'half': 0.5, 'quarter': 0.25, 'eighth': 0.125, '16th': 0.0625, '32nd': 0.03125, '64th': 0.015625, '128th': 0.0078125, '256th': 0.00390625, '512th': 0.001953125, '1024th': 0.0009765625}

# Define weights for notation classes (from Epistemus Journal)
weights = {
    'rhythmPond': 0.136,
    'pitchPond': 0.122,
    'rhythmIntPond': 0.191,
    'pitchIntPond': 0.191,
    'accidentalPond': 0.187,
    'dynamicPond': 0.217,
    'clefPond': 0.134,
    'restPond': 0.156,
    'dotPond': 0.175,
    'tiePond': 0.182,
    'slurPond': 0.210,
    'wedgePond': 0.185,
    'agogExpressPond': 0.208,
    'articPond':0.213,
    'ornamentPond': 0.214,
    'barlinePond': 0.162,
    'repetitionPond': 0.213,
    'octavePond': 0.171,
    'fermataPond': 0.196
}

start = gui()
# OUTPUT 0 selected_language[0], 1 selected_folder[0], 2 musical_instrument[0], 3 default_bpm[0], 4 tactus_level[0], 5 only_rhythm_pitch[0], 6 regression_tree[0]

dir = start[1]                      # Where the actual corpus for analysis is

directory = []

for root, dirs, files in os.walk(dir):
    for file in files:
        if file.lower().endswith(('.xml', '.musicxml', '.mxl')):
            directory.append(
                os.path.relpath(
                    os.path.join(root, file),
                    dir
                )
            )

directory.sort()


partName = start[2]                 # Remember to change this for the instrument you wish to analyse.
quarterDefaultSpeed = int(start[3]) # If there are not a tempo specification, a default one will be placed.
tactus = int(start[4]) - 1          # 0 is pulse, 1 accents, and 2 whole measure (minus one from the GUI)
defaultDyn = 'mp'                   # Default dynamics in case is not listed in the score.
# Classes to eval
if (start[5]):
    # Only 'Pitch' and 'Rhythm'
    classesToEval = ['y','y','n','n','n','n','n','n','n','n','n','n','n','n','n','n','n','n','n']
else:
    # All of the classes will be included in the calculation
    classesToEval = ['y','y','y','y','y','y','y','y','y','y','y','y','y','y','y','y','y','y','y']

# IN EACH FILE OF THE SAMPLE DIRECTORY...
for i in directory:

    # Define Indicator variables for each piece analyzed
    freeEnergy = 0
    entropy_per_MRU = {}
    KLdiv_per_MRU = {}
    totalentropy_per_MRU = {}
    te = 0
    bits_per_MRU = 0

    file_path = os.path.join(dir, i)

    # ---------------------------------------------------------
    # MXL
    # ---------------------------------------------------------
    if i.lower().endswith('.mxl'):
        print(f'Working on Piece: {i} (MXL file)')

        try:
            with tempfile.TemporaryDirectory() as tmp_dir:

                with zipfile.ZipFile(file_path, 'r') as zip_ref:

                    container_path = 'META-INF/container.xml'

                    if container_path not in zip_ref.namelist():
                        print(
                            f"⚠️ Invalid MXL file: "
                            f"{container_path} not found in {i}. Skipping."
                        )
                        continue

                    container_data = zip_ref.read(container_path)
                    container_root = ET.fromstring(container_data)

                    namespace = {
                        'c': 'urn:oasis:names:tc:opendocument:xmlns:container'
                    }

                    rootfile = container_root.find(
                        './/c:rootfile',
                        namespace
                    )

                    if rootfile is None:
                        rootfile = container_root.find('.//rootfile')

                    if rootfile is None:
                        print(
                            f"⚠️ No rootfile found in {i}. Skipping."
                        )
                        continue

                    xml_name = rootfile.get('full-path')

                    if not xml_name:
                        print(
                            f"⚠️ Rootfile has no full-path in {i}. Skipping."
                        )
                        continue

                    if xml_name not in zip_ref.namelist():
                        print(
                            f"⚠️ Rootfile '{xml_name}' not found "
                            f"inside {i}. Skipping."
                        )
                        continue

                    zip_ref.extract(xml_name, tmp_dir)

                    extracted_xml = os.path.join(
                        tmp_dir,
                        xml_name
                    )

                    tree = ET.parse(extracted_xml)
                    root = tree.getroot()

        except Exception as e:
            print(f"❌ Failed to process MXL file {i}: {e}")
            continue

    # ---------------------------------------------------------
    # XML / MusicXML
    # ---------------------------------------------------------
    if i.lower().endswith(('.xml', '.musicxml')):

        tree = ET.parse(file_path)
        root = tree.getroot()

        print('Working on Piece: ', i)

        # START
        print('1. Gathering header Information...')
        # 1. Gather escential elements.
        
        # INPUT: els, fileName, instName, rhFig, default_speed, characters_str
        elts = gatherElts(root,i,partName,fig,quarterDefaultSpeed,characters) 
        # OUTPUT: 0 title, 1 nStaves, 2 attributes, 3 metroList, 4 divisions, 5 focusPart, 6 measNums, 7 instName, 8 accents_pattern

        print('2. Make histograms for all notation classes...')
        # 2. Histograms for all classes
        
        # INPUT: focus_part, n_staves, alteration_file, dynamics_file, expression_file, repeat_file, default_dynamic, divisions, all_rhythm, meas_num_list, divs, rhFig
        notationClasses = organize(elts[5],elts[1],alterWords,dynWords,exprWords,repWords,defaultDyn,elts[4],elts[6],elts[4],fig)
        # OUTPUT: 0 all_rhythm, 1 all_pitch,
        # all_rInt, all_pInt, all_alter, all_dynamic, all_clefs, all_rest, all_dot, all_tie, all_slur, all_wedge, all_agogExpr, all_artic, all_ornam, all_barlines, all_repeat, all_octave, all_fermata,
        # 19 divisions
        
        print('3. Build MRU containers...')
        # 3. Build MRU containers
        # INPUT: durs, focusPart, metro_list, tactus, rhythm_meas, meas_num_list, divs, accent_pattern
        mruInfo = mru(notationClasses[20],elts[5],elts[3],tactus,notationClasses[0][1],elts[8])
        # OUTPUT: totalDur, mru_count, mruAvg, timeSigs, newMru, accent_pattern

        print('4. Generate the "Fifths" indicator...')
        # 4. Build fifths indicator
        # INPUT: attributes, measNums
        histoK = histoFifths(elts[2],elts[6])
        # GIVES: [round(fifths_indicator, 3)]

        print('5. Make distributions and entropy measurements...')
        # probRh = hisToProb(mruInfo[1],histoRh[0],mruInfo[4]) #0 probabilities, 1 histogram, 2 elementsPerMru
        for j in range(len(notationClasses)-2): # Last item in that variable is measure durations...

            if (classesToEval[j] == 'y'):
                # print(notationClasses[j][0]) # Name of current notation class
                htp = his_to_prob(mruInfo[1],notationClasses[j][1],mruInfo[4])
                etp = entropies_normalized(htp) #0 entropy in each MRU, 1 kullback entropy in each MRU, 2 TotalEntropy

                entropy_per_MRU[notationClasses[j][0].replace('Pond', '')] = etp[0]
                KLdiv_per_MRU[notationClasses[j][0].replace('Pond', '')] = etp[1]
                totalentropy_per_MRU[notationClasses[j][0].replace('Pond', '')] = [sum(x) * weights[notationClasses[j][0]] for x in zip(etp[0], etp[1])]
                te += etp[2] * weights[notationClasses[j][0]]
        bits_per_MRU = te / mruInfo[1]
        # carga informacional promedio por MRU, considerando la entropía de las clases de notación y la divergencia KL entre MRUs consecutivos, ponderadas según la relevancia de cada clase.

        # 780 - cuarto = 76.923076923076923
        # 1.360 - cuarto = 44.117647058823529
        # 2000 - cuarto = 30.0

        reference_reading_time = 0
        match tactus:
            case 0: # Basic
                reference_reading_time = 2000
            case 1: # Intermediate
                reference_reading_time = 1360
            case 2: # Expert
                reference_reading_time = 780
            case _:
                raise ValueError(f"Invalid tactus level: {tactus}")

        # Free Energy is operationalized as the information load per MRU weighted by the ratio between the reference reading time associated with the agent's expertise level and the mean reading time required by the musical material.
        freeEnergy = bits_per_MRU * (reference_reading_time / mruInfo[2]) # x milliseconds in each MRU

        current_os = platform.system()

        if current_os == "Windows":
            systemOs = 'windows'
        elif current_os == "Darwin":
            systemOs = 'macos'
        elif current_os == "Linux":
            systemOs = 'linux'
        else:
            raise RuntimeError(...)
            
        print('6. Pixel parsing calculations...')
        # Ink amount calculations
        # Input: score, mru_count, direc, part_id, resvg_path_num
        pixels = parse_pixels(i,mruInfo[1],dir,elts[7],systemOs)
        
        print('7. Reports')
        # 7. Reports
        results.append([ i, mruInfo[1], pixels, histoK[0], bits_per_MRU, freeEnergy, elts[0] ])

# --- Function to save results to CSV ---
oper = build_complexity_index(results)

back = [
    start[0],
    partName,
    dir,
    tactus,
    'PyRIM_corpusName.csv',
    oper[0],
    oper[1],
    current_version
]

# ---------------------------------------------------------
# Añadir ranking PCA y PC1 a cada resultado
# haciendo la correspondencia por nombre de archivo.
# ---------------------------------------------------------

pca_by_filename = {
    str(filename): (rank, pc1)
    for rank, filename, _, pc1 in oper[2]
}

for result in results:

    filename = str(result[0])

    if filename in pca_by_filename:

        rank, pc1 = pca_by_filename[filename]

        result.extend([rank, pc1])

# ---------------------------------------------------------
# Ordenar resultados por PC1 (mayor → menor)
# ---------------------------------------------------------

results.sort(
    key=lambda row: row[8],
    reverse=True
)

# --- Function to build a Regression Tree ---
regressionData = None
if(start[6]):    
    regressionData = build_regression_tree(results)

# --- After processing all XML files ---
if results:
    print(f"✅ Successfully processed {len(results)} files.")

    # Crear una instancia raíz de Tkinter y ocultarla
    rootDos = tk.Tk()
    rootDos.withdraw()  # Oculta la ventana principal

    try:
        chosen_file = filedialog.asksaveasfilename(
            title="PyRIM_assessment of [corpus-name]",
            defaultextension=".csv",
            filetypes=[
                ("CSV Files", "*.csv"),
                ("Text Files", "*.txt"),
                ("All Files", "*.*")
            ],
            initialfile="PyRIM_assessment of [corpus-name].csv"
        )

        if chosen_file:

            try:
                with open(chosen_file, "w", encoding="utf-8", newline="") as f:
                    f.write("TEST\n")
                    f.write("Esto es una prueba\n")

                # print("✅ Python puede crear el archivo correctamente.")

            except Exception as e:
                print("❌ Python NO puede crear el archivo:")
                print(type(e).__name__, e)


            back[4] = chosen_file

            # print("📁 Ruta seleccionada:", chosen_file)
            # print("📊 Resultados:", len(results))
            # print("🌳 regressionData:", type(regressionData))

            save_results_to_csv(back, results, regressionData)

            # print(f"✅ Results saved to: {chosen_file}")

        else:
            print("🟡 Save operation cancelled by user.")

    finally:
        rootDos.destroy()

else:
    print("❌ No files were processed. Nothing to save.")

# Y después, cuando quieras mostrar/guardar el árbol:
if(start[6]):
    tree_image_path = os.path.splitext(chosen_file)[0] + "_regression_tree.png"

    save_regression_tree_image(
        regressionData,
        tree_image_path,
        back[0]
    )