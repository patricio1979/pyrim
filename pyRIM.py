'''
pyRIM, an open-source software to quantify what is possible of the readability of musical scores.

TODO: 
* Implement all musicXML elements
* Implement MIDI version, and other music files
'''
import xml.etree.ElementTree as ET
import os
import ast
from tkinter import filedialog

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
current_version = 'pyRIM v0.07 beta_closed'
# TEXT DEFINITIONS
open(resource_path('textDefinitions/thesaurusDynamics.txt'), 'r')

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
fig = {'whole': 1.0, 'half': 0.5, 'quarter': 0.25, 'eighth': 0.125, '16th': 0.0625, '32nd': 0.03125, '64th': 0.015625, '128th': 0.0078125}

# Define weights for notation classes (from Epistemus Journal)
weigths = {
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
# OUTPUT selected_language[0], selected_folder[0], musical_instrument[0], default_bpm[0], tactus_level[0], only_rhythm_pitch[0], OS_option[0]

dir = start[1]                      # Where the actual corpus for analysis is
directory = os.listdir(dir)
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

    # Avoid any other file type (in case of txt or md files in the corpus)
    if ( (i.endswith('.xml')) or (i.endswith('.musicxml')) ):
        tree = ET.parse(os.path.join(dir, i))
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
                totalentropy_per_MRU[notationClasses[j][0].replace('Pond', '')] = [sum(x) * weigths[notationClasses[j][0]] for x in zip(etp[0], etp[1])]
                te += etp[2] * weigths[notationClasses[j][0]]
        #bits_per_MRU = te / mruInfo[1] #averagin bits in each MRU
        bits_per_MRU = te # Without averaging (the hypothesis is that the entropy measure already averages...)
        freeEnergy = bits_per_MRU * (1000/mruInfo[2]) # 1000 milliconds in each MRU        

        print('6. Pixel parsing calculations...')
        # Ink amount calculations
        # Input: score, mru_count, direc, part_id, resvg_path_num
        pixels = parse_pixels(i,mruInfo[1],dir,elts[7],start[6])
        
        print('7. Reports')
        # 7. Reports
        results.append([ i, mruInfo[1], pixels, histoK[0], bits_per_MRU, freeEnergy, elts[0] ])
        

# --- Function to save results to CSV ---
oper = build_complexity_index(results)
back = [start[0],partName,dir,tactus,'RIM_corpusName.csv',oper[0],oper[1],current_version]
[results[i].extend([item[0], item[2]]) for item in oper[2] for i in range(len(results)) if results[i][1] == int(item[1])]

# --- After processing all XML files ---
if results:
    print(f"✅ Successfully processed {len(results)} files.")

    chosen_file = filedialog.asksaveasfilename(
        title="RIM_corpus",
        defaultextension=".csv",
        filetypes=[
            ("CSV Files", "*.csv"),
            ("Text Files", "*.txt"),
            ("All Files", "*.*")
        ],
        initialfile="RIM_corpus.csv"
    )

    if chosen_file:
        # ✅ Update back[4] with the user-selected path
        back[4] = chosen_file

        # ✅ Now call your function — no changes needed
        save_results_to_csv(back, results)

        print(f"📁 Results saved to: {chosen_file}")
    else:
        print("🟡 Save operation cancelled by user.")
else:
    print("❌ No files were processed. Nothing to save.")