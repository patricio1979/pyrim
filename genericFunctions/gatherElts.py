import os
import re

# <----- HELPERS
def build_measure_patterns(accents, total_measures):
    # Sort by measure number just in case
    accents_sorted = sorted(accents, key=lambda x: x[0])
    
    result = []
    current_pattern = None
    next_accent_idx = 0  # Index in accents list
    
    for measure_num in range(total_measures):
        # If we have a defined accent at this measure, update the pattern
        if (next_accent_idx < len(accents_sorted) and 
            accents_sorted[next_accent_idx][0] == measure_num):
            current_pattern = accents_sorted[next_accent_idx][1]
            next_accent_idx += 1
        
        # Append the current (possibly carried) pattern
        if current_pattern is not None:
            result.append(current_pattern)
        else:
            # If no pattern yet, you might want [] or a default
            result.append([])  # or None, depending on your use case
    
    return result

# <----- MAIN
def gatherElts(els,fileName,instName,rhFig,default_speed,characters_str):
    metroList = []
    meas_nums = []                               # Useful if measure numbers were universally numbered if ommited, but no
    divisions = rhFig['quarter']                # Default division (denominator in time signature)
    accentsStr = []                             # Accent pattern in the form 'a ' + 'duration in denominators as 1,2,4,8,16...
    
    # ---> Get title of score
    # MuseScore 3.6.2
    workTitle = els.find('work/work-title')
    if workTitle is None or workTitle.text is None or not workTitle.text.strip():
        title = os.path.splitext(os.path.basename(fileName))[0]
    else:
        title = ''.join(e for e in workTitle.text if e.isalnum())

    # MuseScore 4.5.2
    for credit in els.findall('credit'):
        credit_type = credit.find('credit-type')
        credit_words = credit.find('credit-words')

        if (credit_type is not None and credit_type.text == 'title' and credit_words is not None and credit_words.text):
            title = ' '.join(credit_words.text.split())
            break

    # ---> Find the ID of the instrument (focusPart) in the score
    partId = None
    parts_available = []

    parts = els.findall('part-list/score-part')

    for part in parts:

        # Get part name safely
        part_name_elem = part.find('part-name')
        part_name = (
            part_name_elem.text.strip()
            if part_name_elem is not None and part_name_elem.text
            else ''
        )

        # Get instrument name safely
        instrument_name_elem = part.find('score-instrument/instrument-name')
        instrument_name = (
            instrument_name_elem.text.strip()
            if instrument_name_elem is not None and instrument_name_elem.text
            else ''
        )

        # Store available parts for possible warning/fallback
        parts_available.append(
            (part.attrib['id'], part_name, instrument_name)
        )

        # Compare with the requested instrument
        requested_name = instName.strip().lower()

        if (
            part_name.lower() == requested_name or
            instrument_name.lower() == requested_name
        ):
            partId = part.attrib['id']
            instName = part_name or instrument_name

    # ---------------------------------------------------------
    # If the requested instrument was not found
    # ---------------------------------------------------------

    if not parts_available:
        raise ValueError(
            f'No score-parts found in MusicXML file: {fileName}'
        )

    if partId is None:

        available_names = [
            part_name or instrument_name
            for _, part_name, instrument_name in parts_available
        ]

        print(
            f'----> Warning: The instrument name "{instName}" '
            f'does not exist in the score. '
            f'Available parts are: {available_names}. '
            f'Working on the first instrument.'
        )

        partId = parts_available[0][0]

        # Use the first available name
        instName = (
            parts_available[0][1]
            or parts_available[0][2]
        )
    
    # ---> Isolate the focusPart for gathering elements
    parts = els.findall('part')
    for part in parts:
        if (part.attrib['id'] == partId):
            focusPart = part

    # ---> Get divisions from the selected/focus part
    for measure in focusPart.findall('measure'):
        divisions_elem = measure.find('attributes/divisions')

        if divisions_elem is not None and divisions_elem.text:
            divisions = rhFig['quarter'] / float(divisions_elem.text)
            break
    
    # ---> Get number of staves in the part (even if the score hide one, this element appears only once)
    if(focusPart.findall('measure')[0].find('attributes/staves') is not None):
        nStaves = int(focusPart.findall('measure')[0].find('attributes/staves').text) # Number of staves in the score
    else:
        nStaves = 1

    # ---> Gather elements
    attributes = []
    measNum = 0
    
    meas_nums = list(range(len(focusPart.findall('measure'))))

    # Get measure numbers
    for elements in focusPart.iter():
        # a. attribute elements
        if(elements.tag == 'attributes'):
            attributes.append([elements,measNum-1])
        # b. Measure for indexing
        if(elements.tag == 'measure'):      # If measure numbers are important, fix this.
            measNum += 1
    
    # ---> Gather metronome elements
    partZero = parts[0] # The metronomic indication is on the first part (multiTempi not implemented yet)

    metroItems = [0.25, default_speed]

    for idx,elements in enumerate(partZero):
        
        # a. Search character indications in each measure (converted in the thesaurusCharacter.json)
        words = elements.findall('direction/direction-type/words')
        for i in words:
            if (i.text is not None):
                word = i.text.lower()
                if(word.startswith('a ')):
                    figures = []
                    # Match: digits followed by optional dots (e.g., '16', '16..', '8.')
                    matches = re.findall(r'(\d+)(\.*)', word)
                    for num_str, dots_str in matches:
                        base = int(num_str)
                        num_dots = len(dots_str)
                        # Compute dot multiplier: 1 + 1/2 + 1/4 + ... up to num_dots
                        dot_multiplier = 2 - (0.5 ** num_dots) if num_dots > 0 else 1.0
                        duration = (1 / base) * dot_multiplier
                        figures.append(duration)
                    accentsStr.append([measNum, figures])
                if(word in characters_str):
                    metroItems = [rhFig['quarter'],float(characters_str[word])]     # Assume is quarter equals Character's definition
            
        # b. Search metronome indications in each measure

        metronome = elements.find(
            'direction/direction-type/metronome'
        )

        if metronome is not None:

            beat_units = []
            dotted = False
            per_minute = None

            for i in metronome:

                if i.tag == 'beat-unit':
                    beat_units.append(i.text)

                elif i.tag == 'per-minute':
                    per_minute = float(i.text)

                elif i.tag == 'beat-unit-dot':
                    dotted = True

            # ========================================================
            # NORMAL METRONOME
            #
            # Example:
            # quarter = 100
            # ========================================================

            if len(beat_units) == 1 and per_minute is not None:

                metroItems = [
                    rhFig[beat_units[0]],
                    per_minute
                ]

                if dotted:
                    metroItems[0] *= 1.5

            # ========================================================
            # METRIC EQUIVALENCE
            #
            # Example:
            # quarter = eighth
            #
            # There is NO per-minute.
            # Keep the previous tempo and convert it.
            # ========================================================

            elif len(beat_units) == 2:

                first_value = rhFig[beat_units[0]]
                second_value = rhFig[beat_units[1]]

                if dotted:
                    second_value *= 1.5

                # IMPORTANT:
                # metroItems contains the PREVIOUS tempo.
                #
                # If:
                #     quarter = 100
                #
                # and we get:
                #     quarter = eighth
                #
                # then:
                #     100 * 1 / 0.5 = 200
                #
                new_tempo = (
                    metroItems[1]
                    * first_value
                    / second_value
                )

                metroItems = [
                    first_value,
                    new_tempo
                ]

        metroList.append(
            [meas_nums[idx], metroItems]
        )

    # print(metroList)
    # print(accentsStr)
    accents_pattern = build_measure_patterns(accentsStr,len(meas_nums))
    # print(accents_pattern)
    return title, nStaves, attributes, metroList, divisions, focusPart, meas_nums, instName, accents_pattern