# pyRIM

> A Python implementation of the RIM (Readability Index for Music), a cognitive-mathematical model for measuring readability in written music.

[License: MIT]([https://img.shields.io/badge/License-GPLv3-blue.svg](https://opensource.org/license/mit))

## Description

This repository contains a Python implementation of the **Readability Index for Music (RIM)**, originally developed in the doctoral dissertation:

> Calatayud, P. F.; Padilla Longoria, P.; Galera-Núñez, M. del M.; Pérez-Acosta, G. (2024). *El ÍLeMus (Índice de Legibilidad Musical). Un nuevo modelo cognitivo matemático para la medición de la legibilidad en música escrita.* Doctoral dissertation. México: Music posgraduate program, UNAM.

Published in Spanish: [TesiUNAM](https://tesiunamdocumentos.dgb.unam.mx/ptd2024/ene_mar/0852222/Index.html)

Published in English: [Journal of Music, Technology & Education](https://intellectdiscover.com/content/journals/10.1386/jmte_00066_1#abstract_content)

For the sake of simplicity, the RIM quantifies musical readability by analyzing notation complexity across multiple dimensions including rhythm, pitch, dynamics, articulation, visual density (ink/pixels), and information entropy — then synthesizing results via PCA into a single readability score.

---

## Features

- Parses MusicXML files (primarily from MuseScore exports).
- Computes 18+ musical feature classes (pitch, rhythm, accidentals, dynamics, etc.).
- Builds histograms and calculates normalized entropies.
- Renders scores to PNG using Verovio + RESVG for pixel-based “ink” analysis.
- Generates MRUs (Metric Reference Units) based on time signature and tactus level.
- Outputs comprehensive CSV reports with PCA-derived readability rankings.
- Includes a simple Tkinter GUI for user configuration.

---

## Design

### Tech Stack
- **Language**: Python 3.10.6 ([Download](https://www.python.org/downloads/release/python-3106/))
- **Core Libraries**: `csv`, `datetime`, `math`, `os`, `re`, `xml.etree.ElementTree`, `ast`, `collections`, `tkinter`, `time`
- **Scientific/Data**: ([`numpy`](https://github.com/numpy/numpy)), ([`scikit-learn`](https://github.com/scikit-learn/scikit-learn))
- **Graphics**: `Pillow`
- **Music Rendering**: ([`verovio`](https://github.com/rism-digital/verovio)), external calls to an external app called ([`resvg`](https://github.com/linebender/resvg)). 

### GUI Controls
There is a small user interface in which the user chooses all possible options: 
- Two flag buttons to choose language (english and spanish)
- A dropdown menu for selecting our Operating System
- A button for loading the folder with the corpus
- A text field for input the name of the musical instrument to measure in the corpus
- Another text field for setting the default BPM of the corpus (if not explicit in the file)
- A dropdown menu for selecting the tactus (expertise) level
- A check box for choosing if the evaluation is only for rhythm and pitch
- And a final button for processing.

> Processing time varies significantly with score size and complexity — no duration prediction is available.

### Processing Pipeline
The process is automatic and it returns the RIM information for each score:
for each XML file in samples/:
│
├── 1. Parse XML → extract notes, directions, attributes (via `gatherElts`)
├── 2. Build all histograms for each notation class (`organize`)
├── 3. Generate the MRU (`mru`) — based on time signature, tactus level
├── 4. Compute "Fifths" indicator (`histoFifths`) — overall incidence of accidentals in Key Signatures
├── 5. Compute entropies for each class (`his_to_prob` → `entropies_normalized`) - Build probabilities and compare distributions
├── 6. Render score to PNG via Verovio (`parse_pixels`) - Count non-white pixels ("ink")
├── 7. PCA operationalization of results (`build_complexity_index`) - One new ranking.
└── 8. Build the CSV for report (`save_results_to_csv`) - Build a file with results.

---

## Requirements

- **Input Format**: It works with the implementation of MuseScore exporting musicXML. The last time I emailed the people of musicXML ([MakeMusic](https://www.makemusic.com/musicxml/)), they told me that they were working on another interchangeable music file called MXN. So its longevity is not garanteed.
- **Corpus Quality**: As with almost every model that uses MIR (Music Information Retrieval), we need to work with a very well suited corpus, organized in folders, reviewed for errors, and all pertinent cares.
- This implementation works fine with a well digitally written scores. Unfortunatedly, if you have vices like erasing silences or puting dynamics with the inappropiate text (e.g. *technique*, *lyrics*) it will give wrong results.
- If you put a Dynamic indication on silences or other that a neume, it will be obliterated.
- **Metronome Marks**: If the score do not have a metronome indication, a default will be setted.
- **Octave Shifts**: For octave changes we only implemented the `<octave-shift>` given in the MuseScore export. Single indications in the software are treated as the sequence `<direction-type>` octave-shift (info) -> note -> `<direction-type>` octave-shift (stop).
- **Text Recognition**: In this implementation we have a number of thesaurus that you need to update. This is, for recognising a certain type of text, it should be indicated in any of the thesaurus. I came up with this solution: You need to go thru the entire corpus and retrieve the types of text (accidentals, characters, dynamics, expression text, or repetition) and place them in the propper thesaurus. For example *sempre dolce e col canto* should go to thesaurusExpression.txt (if there are not already included in the file).
- Also for text. For ease, dots as in D.C., will be removed, and it will processed as dc (lower case). So if you want to update the thesaurus take that into account.

---

## Known issues & Limitations

- **MusicXML/MuseScore Quirks**:
- Metronomic equivalences (as quarter equals a dotted quarter) only works when comparing only two figures (new implementation required for three or more rhythmic comparissons).
- In the musicXML implementation, `<direction>` elements (elts.) appear before the note, and always on voice one. This means adding a number for indexing (take into account that perhaps we didn`t placed the indication in the right place, or that it needed to go on voice two).
- `<dynamics>` indications in musicXML do not account for voice. The solution is incomplete.
- MuseScore does not output information for the `<measure-repeat>` element. Instead it uses the `<forward>` element. MuseScore has no implementation for `<attributes><measure-style><measure-repeat>` it only has a `<forward>` element with a duration measured in divisions. So in our version the last is implemented.
- MuseScore uses the `<attributes>` `<print-object>` with the value 'no' for hidden objects. It has been reported as arbitrary.
- In MuseScore, if the `<barline>` definition is repeat start ('heavy-light' + `<repeat direction="forward>"/>` ) it will be assigned to the next measure... weird behaviour that perhaps is due to the fact that it affects the next...; do not know.
- As there are none indications for a *normal* barline, if the last barline is normal it will be identified as final ('ligth-heavy').
**Algorithmic Notes**:
- The pitch and rhythm interval are implemented as notes appear in the XML file. I.e., we go voice by voice (not interleaving notes), and in a chord the lowest note starts the *delta* distance.
- 'multimeasure' rests are not implemented yet. MuseScore exports each measure whole silence sepparatedly.
- If timeSignatures are hidden, MuseScore does not write them in the musicXML file.
- 'Measure Number' always starts from 0, and it obliterates pickUp measures (and its complement e.g., baroque pieces that show a reduced bar that complements the pickUp one). It also obliterates measure number change.
- We use the *Kullback Divergence* method because the ontological relationship between what we read, and what we have read is influential; mostly on memory. There are many equations for assesign how equal distributions are, you are invited to implement yours.
**Pixel Rendering Workaround**:
- The Pixel parsing implementation was first implemented with the Music21 library. This had to stop because the library needed to import an xml, convert it to a 'stream object', and then convert it back to xml. In this process much information was misplaced and complex rhythms aborted the process. So we headed back to basics, and built a command line for the terminal that directly convert the xml to png from the MuseScore CLI app. The problem with this is the path of the app. Getting the right path means locating the mscore app. In mac I found it, but you need to specify the item for each OS. Yet another problem emerged: The MuseScore CLI do not separate the parts, e.g., a flute in an orchestral piece, so we modified the xml file to extract the part, converted the part into an SVG with Verovio and convert the SVG to PNG with an external app called RESVG. Then the PNG is analyzed pixel by pixel. This was the easiest, and multi platform idoneus solution.
**MuseScore 4 Warning**:
- MuseScore 4 was apparently released before it was in a full alpha state, so many elements from MuseScore 3.6.2 were lost. Many new and unexpected bugs appeared.

---

## Class Definitions

All these definitions should be mirrored from the musicXML ones. We just looked for these in the xml file and evaluated.
All classes mirror MusicXML structure. Each extracted event has:
`[Event ID, Value, Measure Number, MRU Location]`
- The 'Event ID' is obtained from each staff and each voice separatedly.
- The 'value' is particular for each class, and its defined as: 
**Rhythm Duration** A sum of type, tuple, and dot elements.
**Pitch** A MIDI conversion from step, alteration, and octave elts.
**Rhythm Interval** As they appear, the delta values of Rhythm Duration are placed. We then delete the first item (as it relates to 0 and gives wrong numbers.)
**Pitch Interval** As they appear, the delta values of Pitch are placed. We then delete the first item (as it relates to 0 and gives wrong numbers.)
**Accidental** Two values are given here. The accidental element (in all its variants e.g. 'tuplet accidental'), and text values compared to the thesaurusAccidentals.txt in the textDefinitions folder.
**Dynamic** Two values are given here. The dynamic elt, and text values compared to the thesaurusDynamics.txt in the textDefinitions folder.
**Clef** The clef attribute, as it appears in the thesis, it is considered as 'header information'. This is a type of information that appears once, and conditions the subsequent information. So the values here are the indication when it appears, and an added 'T' for all subsequent, until a new one appears (eg. 'G2', 'G2T', 'G2T',...)
**Rest** A simple boolean that indicates the distributions of rests in the score.
**Dot** A simple boolean that indicates the distributions of dots in the score, the indication is accompanied with a number representing the number of dots in the event.
**Tie** A simple boolean that indicates the distributions of ties in the score.
**Slur** A simple boolean that indicates if the event is under a slur.
**Wedge** A simple boolean that indicates if the event is under a wedge.
**Agogic/Expression** A text value compared to the thesaurusExpression.txt in the textDefinitions folder.
**Articulation** The articulation element with its characteristics (e.g. type, direction)
**Ornament** The ornament element with its characteristics (e.g. type, direction)
**Barline** An indication of the type of barline that an MRU has. Can be 'none' when the tactus is 0 ('pulse') and the current MRU is in the first beat of a 4/4 measure.
**Repetition sign** Two values are given here. The sign of repetition elements implemented in musicXML,and text values compared to the thesaurusRepetition.txt in the textDefinitions folder. 
**Octave sign** A simple boolean that indicates if the event is under an octave sign.
**Fermata** The fermata element with its characteristics (e.g. type, direction)

Other classes defined in the PhD dissertation: **timeSignature**, **keySignature**, and **Tempo** (combining **Metronomic Indication** and **Character** defined in the thesaurusCharacter.js, in the textDefinitions folder), have complex implementations and are considered as *header Information*. Classes **timeSignature** and ***Tempo*** are used to build MRUs and putting information values in them. The **keySignature** is used to calculate the **Fifths** indicator for the RIM. All of these precautions are mentioned in the Dissetation, and int the published article.

---

## Version History

### v0.06 beta
- Extensive refactoring and optimization with assistance from Qwen AI.
- Improved generic functions and library integration.

### v0.05 pre-beta
- Fixed bug on part find in gatherElts.py
- Implemented accents tactus level. But it has a caviat. We have a default behaviour when entering from 1 to 13 beats (the socalled <divisions> element in the current musicXML implementation). So, if you want to owerwrite it, yo need to put a text element in the first note with this structure: letter ‘a’ and a list of numbers describing accent durations. E.g. in a 7/8 time signature, the first note on the measure must have a text item (any type of them) that reads ‘a 4 4. 4’ (a quarter note, a dotted quarter note, and a quarter note); with this text, the default behaviour (4., 4,  4) is overide. Note: The text can be hidden, as long as it is there, we do not need to see it.
- Implemented <forward> element to account for deleted rests. Do not know if it will affect voice one.
- Corrected MRU implementation.
- Corrected Barline class implementation.

### v0.04
- Fixed major bug when using tactus level 2 (whole measure).
- Bug fixed in small scores that have no part name.
- Bug fixed when hidden timeSignatures.
- Bug fixed when scores have normal barLine at the end.
- Bug fixed when allocating timeSignatures in MRU.
- There is a simple user input for choosing the default values for information missing in the scores.
- Added a MuseScore style file (.mss) to avoid all metaData that is not in the 'header' definition of the PhD thesis.

### v0.03
- Big bug solved. We forgot to include rhythm duration elements in the measure :()
- **Bits per MRU** and **Free Energy** are no longer divided by the number of MRUs. This is because entropy measures average information without needing it to be shared in each MRU.
- There is a simple user input for choosing the notation classes to be evaluated by the RIM.
- Regression values, outside Python, improved greatly. The RIM has a beta version.
- Improve class definitions, we need a real computer programmer for complete this.

### v0.02 
- Improve MRU locations.
- Improve histograms in each class. We erased the number in elements like slurs, wedges and lines in general.
- Text improvements. Looking for entire strings instead of some part of the string in the thesaurus.

### v0.01 
- Basically a translation and improvement of the javascript of the RIM version 0.12
- Changes from Javascript version:
    - There is no sound information from `<sound tempo>` element.
    - Implemented metronomic equivalences.
    - We do not convert the XML or musicXML to JSON. The sequence of elements is vital to the parsing process.
    - All functions needed to be merged due to the fact that we work with XML and index for `<direction>` `<attributes>` elts is not present. We avoid making an XML to JSON convertion.
    - Solved numerous small bugs and fixes.

---

## Roadmap / TODO

### Short Term
- [ ] Implement sub-beat tactus levels.

### Format Support
- [ ] Add importers for:
    - **ABC** ([abcnotation.com](https://abcnotation.com/))
    - **GUIDO** ([guidodoc.grame.fr](https://guidodoc.grame.fr/))
    - **MNX** ([w3c.github.io/mnx](https://w3c.github.io/mnx/docs/)) — *Note: MNX is still a draft specification*
    - **Humdrum** ([humdrum.org](https://www.humdrum.org/))
    - **MIDI**
  
> Current workaround: Convert other formats to MusicXML first:
> - ABC → XML: https://abc2xml.appspot.com/
> - GUIDO → XML: http://debussy.music.ubc.ca/NoteAbility/
> - Humdrum → XML: http://www.music-notation.info/en/software/hum2xml.html
> - MIDI → MusicXML: See [MIDI-Compatible Part Tutorial](https://www.w3.org/2021/06/musicxml40/tutorial/midi-compatible-part/)

---

## Installation

*(To be filled — example placeholder below)*

```bash
# Clone the repository
git clone https://github.com/yourusername/pyRIM.git
cd pyRIM

# Create and activate a virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate   # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Usage
- 1. Launch GUI: python3 pyRIM.py
- 2. Carefuly configure options (language, OS, corpus path, instrument, BPM, tactus, etc.)
- 3. Click "Process"
- 4. Wait for completion, a popup window will appear quering the location to save the CSV file with the results

## Contributing
Any contribution and feedback is welcome.
