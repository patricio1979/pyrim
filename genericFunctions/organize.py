import math
import re
from collections import defaultdict

# <--------- HELPERS
def group_by_third_then_first(data):
    grouped = defaultdict(list)
    for item in data:
        grouped[item[2]].append(item[0])
    return [grouped[key] for key in sorted(grouped)]

def word_in_rules(word, rule_text):
    """Check if word (exact whole word) is in rule_text."""
    return re.search(r'\b' + re.escape(word.lower()) + r'\b', rule_text, re.MULTILINE)

# <--------- MAIN
def organize(
    focus_part,
    n_staves,
    alteration_file,
    dynamics_file,
    expression_file,
    repeat_file,
    default_dynamic,
    divisions,
    meas_num_list,
    divs,
    rhFig
):  
    #State variables
    staff = 0
    voice = 0
    hide = ''
    #Text definitions
    alterW = alteration_file.read()
    dynW = dynamics_file.read()
    exprW = expression_file.read()
    repeatW = repeat_file.read()
    #Elts variables
    PITCH_CLASS_MIDI = {'C': 0, 'D': 2, 'E': 4, 'F': 5, 'G': 7, 'A': 9, 'B': 11}
    ornament = ''
    alter = ''
    in_slur = [[ '0' for _ in range(4) ] for __ in range(n_staves)]
    dyn = default_dynamic
    dynBool = False
    wedge = '0'
    wedgy = False
    ae = 'none'
    octaveLine = '0'
    octavyLine = False
    # Repeat sign state
    in_repeat_box = False
    repeat_box_id = 0
    pending_repeat_sign = ''  # Accumulates signs like 'coda', 'segno', etc.
    # Clef tracking
    has_new_clef = False
    current_clef = ''  # e.g., 'G2' for treble
    # Previous pitch per staff/voice (for interval calculation)  
    prev_pitch = [[None for _ in range(4)] for __ in range(n_staves)]
    #Slots for elts
    accum = [[0] * 4 for _ in range(n_staves)]  # [staff][voice]
    
    all_rhythm = [[[] for x in range(4)] for y in range(n_staves)]
    all_pitch = [[[] for x in range(4)] for y in range(n_staves)]
    all_alter = [[[] for x in range(4)] for y in range(n_staves)]
    all_dot = [[[] for x in range(4)] for y in range(n_staves)]
    all_ornam = [[[] for x in range(4)] for y in range(n_staves)]
    all_rest = [[[] for x in range(4)] for y in range(n_staves)]
    all_tie = [[[] for x in range(4)] for y in range(n_staves)]
    all_fermata = [[[] for x in range(4)] for y in range(n_staves)]
    all_artic = [[[] for x in range(4)] for y in range(n_staves)]
    all_slur = [[[] for x in range(4)] for y in range(n_staves)]
    all_dynamic = [[[] for x in range(4)] for y in range(n_staves)]
    all_wedge = [[[] for x in range(4)] for y in range(n_staves)]
    all_agogExpr = [[[] for x in range(4)] for y in range(n_staves)]
    all_octave = [[[] for x in range(4)] for y in range(n_staves)]
    all_barlines = [[[] for x in range(4)] for y in range(n_staves)]
    all_repeat = [[[] for x in range(4)] for y in range(n_staves)]
    all_clefs = [[[] for x in range(4)] for y in range(n_staves)]
    all_pInt = [[[] for x in range(4)] for y in range(n_staves)]
    all_xy = [[[] for x in range(4)] for y in range(n_staves)]
    
    durations = [0.0] * len(meas_num_list)
    
    #1. Go thru the full content of measures in the score
    for idi,i in enumerate(focus_part):
        measNum = int(meas_num_list[idi])
        forward_anacruxis = False
        # Check if it is a measure repeat
        # MuseScore version 3.6, the <repeat-measure> element does not exists, it puts a silence
        if (len(i.findall('note')) == 0 and i.find('forward')):
            durations[idi] = int(i.find('forward/duration').text) * divs

        for idj,j in enumerate(i): # Go thru each element in the measure
            # ---> direction elements
            if (j.tag ==  'direction'):
                for child in j:
                    if child.tag != 'direction-type':
                        continue
                    
                    for elem in child:
                        tag = elem.tag
                        
                        # --- <words>: text-based instructions ---
                        if tag == 'words' and elem.text:
                            raw_text = elem.text.strip()
                            clean_text = re.sub(r'<[^>]+>', '', raw_text)  # Strip XML-like tags
                            for word in clean_text.split():
                                word_lower = word.strip('.:,;()').lower()
                                # Alteration words
                                if word_in_rules(word_lower, alterW):
                                    alter = word_lower
                                # Dynamic words
                                if word_in_rules(word_lower, dynW):
                                    dyn = word_lower
                                    dynBool = True
                                # Agogic / Expression words
                                if word_in_rules(word_lower, exprW):
                                    ae = word_lower
                                # Repeat signs
                                if word_in_rules(word_lower, repeatW):
                                    pending_repeat_sign = pending_repeat_sign + word_lower
                            
                        # --- <dynamics> ---
                        elif tag == 'dynamics':
                            for dyn_elem in elem:
                                dyn = dyn_elem.tag  # e.g., <mf>, <pp>
                                dynBool = True
                                    
                        # --- <wedge> (cresc./dim.) ---
                        elif tag == 'wedge':
                            wedge_type = elem.get('type')
                            if wedge_type != 'stop':
                                wedge = wedge_type
                                wedgy = True
                            else:
                                wedgy = False

                        # --- <octave-shift> ---
                        elif tag == 'octave-shift':
                            shift_type = elem.get('type')
                            size = elem.get('size', '8')
                            number = elem.get('number', '1')
                            if shift_type != 'stop':
                                octaveLine = f"{shift_type}_{size}_{number}"
                                octavyLine = True
                            else:
                                octavyLine = False

                        # --- Repeat signs: coda, segno ---
                        elif tag == 'coda':
                            pending_repeat_sign += 'coda_'
                        elif tag == 'segno':
                            pending_repeat_sign += 'segno_'
            
            # ---> forward elements (used for measure/beat repeats and voice alignment)
            if j.tag == 'forward':
                duration = float(j.find('duration').text) * divisions
                is_repeat_element = False

                # Case 1: Measure repeat (explicit)
                measure_repeat_elem = j.find('attributes/measure-style/measure-repeat')
                if measure_repeat_elem is not None and measure_repeat_elem.get('type') == 'start':
                    pending_repeat_sign += 'measureRepeat_'
                    is_repeat_element = True

                # Case 2: Beat repeat
                beat_repeat_elem = j.find('attributes/measure-style/beat-repeat')
                if beat_repeat_elem is not None and beat_repeat_elem.get('type') == 'start':
                    pending_repeat_sign += 'beatRepeat_'
                    is_repeat_element = True

                # Case 3: Silent measure heuristic (no notes in measure)
                # Note: this is MuseScore 3.6 fallback
                if len(i.findall('note')) == 0 and 'measureRepeat' not in pending_repeat_sign:
                    pending_repeat_sign += 'measureRepeat_'
                    is_repeat_element = True

                # Record if any repeat type was found
                if is_repeat_element:
                    # Use staff from context? Default to 0 if unsure
                    target_staff = 0  # Safe default; could infer from context
                    all_repeat[target_staff][0].append(['noNote', pending_repeat_sign.rstrip('_'), measNum])
            
            # ---> attributes (clef, key, time, etc.)
            if j.tag == 'attributes':
                for attr in j:
                    if attr.tag == 'clef':
                        sign_elem = attr.find('sign')
                        line_elem = attr.find('line')
                        if sign_elem is None or line_elem is None:
                            continue

                        sign = sign_elem.text
                        line = line_elem.text
                        clef_id = f"{sign}{line}"

                        # Check for octave shift (e.g., 8 below)
                        octave_change = attr.find('clef-octave-change')
                        if octave_change is not None and octave_change.text:
                            offset = int(octave_change.text)
                            clef_id += f"+{offset}" if offset > 0 else f"{offset}"  # e.g., G2-1

                        current_clef = clef_id
                        has_new_clef = True

            # ---> note elements
            # Previously, check if <forward> elements to account for deleted rests in voices and measures repeat
            if (j.tag == 'forward'):
                duration = float(j.find('duration').text) * divisions
                fw = False
                # Find forward elements for compensating lack of rests in other voices
                if (idj < len(i)-1):
                    if(i[idj+1].tag == 'note'):
                        fw = True
                        voice_id = 1
                    if(i[idj-1].tag == 'note'):
                        fw = True
                        voice_id = -1
                else:
                    if (i[idj-1].tag == 'note'):
                        fw = True
                        voice_id = -1
                if (fw):
                    hide = 'no'
                    # a. Assign voices
                    staff = int(math.ceil(int(i[idj+voice_id].find('voice').text)) / 4)
                    voice = (int(i[idj+voice_id].find('voice').text) - 1) % 4
                    if (voice == 0):
                        forward_anacruxis = True
                    if (forward_anacruxis is False):
                        # b. Accum for note index
                        accum[staff][voice] += 1
                        # c. Add to array
                        all_rhythm[staff][voice].append([str(accum[staff][voice]) + hide, duration, measNum])
                        all_pitch[staff][voice].append([str(accum[staff][voice]) + hide, duration, measNum])
                    hide = ''
                fw = False
            # Notes
            if (j.tag == 'note'):
                # Assign stave and voice locations
                voice_elem = j.find('voice')
                if voice_elem is None:
                    continue  # Skip note without voice
                try:
                    voice_num = int(voice_elem.text)
                except (ValueError, TypeError):
                    voice_num = 1

                staff = (voice_num - 1) // 4  # 4 voices per staff
                voice = (voice_num - 1) % 4
                
                # prev. add 'print-object' attribute
                hide = j.get('print-object', '')
                
                # b. Find notes that aren't part of a chord
                if (j.find('chord') is None):
                    accum[staff][voice] += 1
                    # Accum for note index
                    idx = str(accum[staff][voice])+hide

                    # This note's default-x and default-y positions. Warning: Rests do not have x or y positions in MuseScore 3.6.2 backwards. The best solution is to open the scores in a software that adds these positions to elts.
                    if (j.get('default-x') is not None or j.get('default-y') is not None):
                        dx = float(j.get('default-x'))
                        dy = float(j.get('default-y'))
                    else:
                        dx = 'noX'
                        dy = 'noY'

                    # d. Dots
                    if (j.find('dot') is not None):
                        dots = len(j.findall('dot'))    # Each dot is separated
                        dot = ((0.5 ** dots) * (( 1 / (0.5 ** dots) ) - 1)) + 1
                        all_dot[staff][voice].append([idx,1,measNum])
                    else:
                        dot = 1
                        all_dot[staff][voice].append([idx,0,measNum])
                    
                    # e. Check if j is tuplet
                    if (j.find('time-modification') is not None):
                        tupl = float(j.find('time-modification/normal-notes').text) / float(j.find('time-modification/actual-notes').text)
                    else:
                        tupl = 1
                    
                    # f. Build note duration
                    if (j.find('type') is not None):
                        noteType = rhFig[j.find('type').text]
                    else:
                        rest_elem = j.find('rest')
                        if rest_elem is not None and 'measure' in rest_elem.attrib:
                            # It's a measure rest
                            noteType = int(j.find('duration').text) * divs
                        else:
                            # Regular rest
                            noteType = rhFig.get(j.find('type').text, 0) if j.find('type') is not None else 0
                    
                    # g. If it is a grace note, zero duration (we do not know the outcome, as duration, of this type of information)
                    if (j.find('grace') is not None):
                        #print('grace, accaciatura, etc.')
                        noteType = 0
                    
                    # gBis. add 'no' if note is hidden, latter it will be obliterated from evaluation
                    for k in j.items():
                        if k[0] == 'print-object':
                            hide = j.attrib['print-object']
                    
                    # h. Add to array
                    all_rhythm[staff][voice].append([str(accum[staff][voice])+hide,dot*tupl*noteType,measNum])
                    all_xy[staff][voice].append([str(accum[staff][voice])+hide,[dx,dy],measNum])
                    
                    # i. Accum note durations only for voice one, and staff one. 
                    # This array shows differences between measure durations (e.g. anacruxis duration, time signatures duration)
                    if (j.find('voice').text == '1'):
                        # Inside loop
                        meas_index = idi  # or map measNum to index
                        if 0 <= meas_index < len(durations):
                            durations[meas_index] += dot * tupl * noteType
                    
                    # . Rests
                    if (j.find('rest') is not None):
                        all_rest[staff][voice].append([idx,1,measNum])
                    else:
                        all_rest[staff][voice].append([idx,0,measNum])
                    
                    # . Ornament and trills
                    current_ornament = 'none'

                    ornaments_elem = j.find('notations/ornaments')
                    if ornaments_elem is not None:
                        for orn in ornaments_elem:
                            orn_tag = orn.tag
                            orn_text = f": {orn.text}" if orn.text else ""
                            attrs = '_'.join(
                                f"{k}:{v}" for k, v in orn.items()
                                if k not in ['default-x','default-y','relative-x','relative-y']
                            )
                            current_ornament = orn_tag + orn_text + (('_' + attrs) if attrs else '')
                    else:
                        # Carry forward only if wavy-line_start without stop
                        if 'wavy-line_start' in ornament and 'wavy-line_stop' not in ornament:
                            current_ornament = ornament

                    # But if stop, force 'none'
                    if 'wavy-line_stop' in ornament:
                        current_ornament = 'none'

                    all_ornam[staff][voice].append([idx, current_ornament, measNum])
                    ornament = current_ornament  # update global state
                    
                    # . fermata
                    if(j.find('notations/fermata') is not None):
                        fermiType = j.find('notations/fermata').attrib['type']
                        if (j.find('notations/fermata').text is not None):
                            fermiType = fermiType + j.find('notations/fermata').text
                        all_fermata[staff][voice].append([idx,fermiType,measNum])
                    else:
                        all_fermata[staff][voice].append([idx,'none',measNum])
                    
                    # . articulation
                    articulations_elem = j.find('notations/articulations')
                    if articulations_elem is not None:
                        art_parts = []
                        for a in articulations_elem:
                            part = a.tag
                            if a.get('type'):
                                part += a.get('type')
                            art_parts.append(part)
                        art_val = ''.join(art_parts)
                    else:
                        art_val = 'none'
                    all_artic[staff][voice].append([idx, art_val, measNum])
                    
                    # . slur (the commented code is for indexing more that one slur on top of each other)
                    slur_elem = j.find('notations/slur')
                    slur_val = '0'

                    if slur_elem is not None:
                        slur_type = slur_elem.get('type')
                        if slur_type == 'start':
                            in_slur[staff][voice] = '1'  # Enter slur
                            slur_val = '1'
                        elif slur_type == 'stop':
                            slur_val = '1'               # Stop note is STILL under slur
                            in_slur[staff][voice] = '0'  # But end slur for next notes
                        else:
                            # Handle 'continue' if present
                            slur_val = in_slur[staff][voice]
                    else:
                        # No <slur> element → inherit current state
                        slur_val = in_slur[staff][voice]

                    all_slur[staff][voice].append([idx, slur_val, measNum])
                    
                    # . Wedge (from DIRECTION)
                    if wedgy:
                        all_wedge[staff][voice].append([idx,wedge,measNum])
                    else:
                        all_wedge[staff][voice].append([idx,'0',measNum])

                    # . Agog./Expr. (from DIRECTION)
                    all_agogExpr[staff][voice].append([idx,ae,measNum])

                    # . Octave-shift (from DIRECTION)
                    if octavyLine:
                        all_octave[staff][voice].append([idx,octaveLine,measNum])
                    else:
                        all_octave[staff][voice].append([idx,'0',measNum])
                    
                    # . Repeat signs (from DIRECTION, BARLINE, FORWARD)
                    if (in_repeat_box):
                        pending_repeat_sign = pending_repeat_sign + 'repeatBox' + repeat_box_id + '_'
                    if (voice == 0):
                        if (len(pending_repeat_sign) == 0):
                            all_repeat[staff][voice].append([idx,'none',measNum])
                        else:
                            all_repeat[staff][voice].append([idx,pending_repeat_sign,measNum])
                    
                    # . Clef (from ATTRIBUTES)
                    if has_new_clef:
                        all_clefs[staff][voice].append([idx,current_clef,measNum])
                    else:
                        all_clefs[staff][voice].append([idx,current_clef+'T',measNum])

                #if <chord> is None AND <rest> is None
                if (j.find('chord') is None and j.find('rest') is None):

                    # . Tie
                    if(j.find('tie') is not None and j.find('tie').attrib['type'] == 'start'):
                        all_tie[staff][voice].append([idx,1,measNum])
                    else:
                        all_tie[staff][voice].append([idx,0,measNum])

                    # . dynamic (from DIRECTION)
                    if (dynBool):
                        all_dynamic[staff][voice].append([idx,dyn,measNum])
                    else:
                        all_dynamic[staff][voice].append([idx,dyn+'T',measNum])

                #if <chord> is Ok AND <rest> is None
                if (j.find('rest') is None): 

                    # . Accidental
                    if(j.find('accidental') is not None):
                        all_alter[staff][voice].append([idx,alter+j.find('accidental').text,measNum])
                    else:
                        all_alter[staff][voice].append([idx,alter+'none',measNum])

                    # . Pitch
                    step = PITCH_CLASS_MIDI[j.find('pitch/step').text]
                    octave = int(j.find('pitch/octave').text) * 12
                    if (j.find('pitch/alter') is not None):
                        alterP = int(j.find('pitch/alter').text)
                    else:
                        alterP = 0
                    all_pitch[staff][voice].append([idx, step + octave + alterP, measNum])

                    # . Pitch Delta Interval
                    if prev_pitch[staff][voice] is not None:
                        interval = (step + octave + alterP) - prev_pitch[staff][voice]
                    else:
                        interval = 'none'  # No previous note

                    all_pInt[staff][voice].append([idx, interval, measNum])

                    # Update for next note
                    prev_pitch[staff][voice] = step + octave + alterP
                
                # after each chord
                alter = ''
                dynBool = False
                ae = 'none'
                hide = ''
                pending_repeat_sign = ''
                has_new_clef = False
    
    # rhythm_measures organized by its item in each measure
    rhythm_sorted = []
    for j in range(n_staves):
        rhythm_sorted_per_stave = []
        for k in range(4):
            staff = j
            voice = k
            rhythm_sorted_by_measure = group_by_third_then_first(all_rhythm[staff][voice])
            rhythm_sorted_per_stave.append(rhythm_sorted_by_measure)
        rhythm_sorted.append(rhythm_sorted_per_stave) 
    # print(rhythm_sorted)
    # Again, go thru the full content of measures in the score
    for idi,i in enumerate(focus_part):
        measNum = int(meas_num_list[idi])
        forward_anacruxis = False
        # <--- Barlines
        barlines = ['no','no']
        for j in i.iter('barline'): # Assuming that every measure has a barline (even hidden, or none).
            if(j.get('location') == 'left'):
                if(j.find('bar-style') is not None):
                    barlines[0] = j.find('bar-style').text
                if j.find('repeat') is not None:
                    barlines[0] = barlines[0] + j.find('repeat').get('direction')
            elif(j.get('location') == 'right'):
                if(j.find('bar-style') is not None):
                    barlines[1] = j.find('bar-style').text
                if j.find('repeat') is not None:
                    barlines[1] = barlines[1] + j.find('repeat').get('direction')
        
        for staff_idx in range(n_staves):           # In each stave
            if( len(rhythm_sorted[staff_idx]) > 0):
                for voice_idx in range(4):          # In each voice
                    # Skip if no data for this voice
                    if (staff_idx >= len(rhythm_sorted) or 
                        voice_idx >= len(rhythm_sorted[staff_idx]) or 
                        idi >= len(rhythm_sorted[staff_idx][voice_idx])):
                        continue

                    measure_notes = rhythm_sorted[staff_idx][voice_idx][idi]
                    if not measure_notes:
                        continue

                    first_note = measure_notes[0]
                    last_note = measure_notes[-1]

                    # Attach left barline to first note, right to last
                    all_barlines[staff_idx][voice_idx].append([first_note, barlines[0], measNum])
                    all_barlines[staff_idx][voice_idx].append([last_note, barlines[1], measNum])
    
    # ---> We add rest measures for voices
    for i in range(len(all_rhythm)): # Staves
        # Collect all measure numbers used in each voice
        existing_measures = [set() for _ in range(4)]  # One set per voice

        for voice_idx in range(4):
            for item in all_rhythm[i][voice_idx]:
                existing_measures[voice_idx].add(item[2])

        # Find missing measures for each voice
        missing_measures = [
            [m for m in meas_num_list if m not in existing_measures[voice_idx]]
            for voice_idx in range(4)
        ]

        # Add 'add' rests for missing measures
        for voice_idx in range(4):
            for m in missing_measures[voice_idx]:
                m_idx = meas_num_list.index(m)
                all_rhythm[i][voice_idx].append(['add', durations[m_idx], m])
            all_rhythm[i][voice_idx].sort(key=lambda x: x[2])  # Sort by measure
    
    all_rInt = [[[[filtered[i][0], filtered[i-1][1] - filtered[i][1], filtered[i][2]] for i in range(1, len(filtered))] for filtered in [[item for item in sub if 'no' not in item[0] and 'add' not in item[0]] for sub in inner]] for inner in all_rhythm]
           
    all_rhythm = ['rhythmPond'] + [all_rhythm]
    all_pitch = ['pitchPond'] + [all_pitch]
    all_rInt = ['rhythmIntPond'] + [all_rInt]
    all_pInt = ['pitchIntPond'] + [all_pInt]
    all_alter = ['accidentalPond'] + [all_alter]
    all_dynamic = ['dynamicPond'] + [all_dynamic]
    all_clefs = ['clefPond'] + [all_clefs]
    all_rest = ['restPond'] + [all_rest]
    all_dot = ['dotPond'] + [all_dot]
    all_tie = ['tiePond'] + [all_tie]
    all_slur = ['slurPond'] + [all_slur]
    all_wedge = ['wedgePond'] + [all_wedge]
    all_agogExpr = ['agogExpressPond'] + [all_agogExpr]
    all_artic = ['articPond'] + [all_artic]
    all_ornam = ['ornamentPond'] + [all_ornam]
    all_barlines = ['barlinePond'] + [all_barlines]
    all_repeat = ['repetitionPond'] + [all_repeat]
    all_octave = ['octavePond'] + [all_octave]
    all_fermata = ['fermataPond'] + [all_fermata]
    
    '''
    * all nStaves dimention array with 4 arrays for voices with all rhythmic 
        information [ [ [],[],[],[] ] ] note index, duration, measure-1
    * accum nStaves dimention array with 4 integers that enumerate the amount of notes in all fragment
    * rhythmMeas is the same as all, but adds measure rests for measures that do not have information
    * Durations is the sum of divisions in measure. E.g. in a 4/4 measure [1,1,1...]
    * repetition_symbol is an array of repetition elements in measure (will be joined with the class).
    '''
    # print(all_xy)
    return all_rhythm,all_pitch,all_rInt,all_pInt,all_alter,all_dynamic,all_clefs,all_rest,all_dot,all_tie,all_slur,all_wedge,all_agogExpr,all_artic,all_ornam,all_barlines,all_repeat,all_octave,all_fermata,all_xy,durations