import math

# <----- HELPERS
def round_up(x, a):
    return math.ceil(x / a) * a

def assign_accent(time_signature_numerator):

    # Accents definitions
    accent_durs = []
    match time_signature_numerator:
        case 1:
            accent_durs = [1]
        case 2:
            accent_durs = [2]
        case 3:
            accent_durs = [3]
        case 4:
            accent_durs = [2,2]
        case 5:
            accent_durs = [3,2]
        case 6:
            accent_durs = [3,3]
        case 7:
            accent_durs = [3,2,2]
        case 8: 
            accent_durs = [3,3,2]
        case 9: 
            accent_durs = [3,3,3]
        case 10: 
            accent_durs = [3,2,2,3] # Zorziko's style
        case 11: 
            accent_durs = [2,2,2,2,3] # Greateful Dead' style
        case 12: 
            accent_durs = [3,3,3,3]
        case 13: 
            accent_durs = [2,2,2,3,2,2] # Balkans' style    
        case _:
            print(f"Time signatures accents are only implemented until 13 accents.")

    return accent_durs

def assign_mru(rh_meas, time_signatures, durs, tactus, accent_pattern=None):

    """
    Assign mru (container index) to each element based on tactus level.
    
    Args:
        rh_meas: [[[label, duration, measure_idx], ...], ...]
        time_signatures: list of [numerator, denominator] for each measure
        durs: list of measure durations in whole-note units
        tactus: 
            2 = measure-level (mru = measure index)
            1 = accent-level (mru based on per-measure accent_pattern, global timeline)
            0 = pulse-level (mru per beat unit: 1/denominator)
        accent_pattern: list of lists; accent_pattern[i] = list of container durations for measure i

    Modifies rh_meas in-place by appending mru index as 4th element.
    """

    def get_container_index(measure_idx, pos_in_measure):
        """Return (container_duration, local_mru_within_measure) for given measure and position."""
        if tactus == 2:
            return durs[measure_idx], 0  # container = full measure, local index = 0
        elif tactus == 1:
            if accent_pattern is None or measure_idx >= len(accent_pattern):
                return durs[measure_idx], 0
            pattern = accent_pattern[measure_idx]
            if not pattern:
                return durs[measure_idx], 0
            cycle_dur = sum(pattern)
            # Position within the repeating cycle
            pos_in_cycle = pos_in_measure % cycle_dur if cycle_dur > 0 else 0.0
            acc = 0.0
            for i, size in enumerate(pattern):
                acc += size
                if pos_in_cycle < acc:
                    return size, i
            return pattern[-1], len(pattern) - 1
        else:  # tactus == 0: pulse-level
            beat_unit = 1.0 / time_signatures[measure_idx][1]
            index = int(pos_in_measure / beat_unit)
            return beat_unit, index

    # Precompute global mru_offset for each measure (for tactus=1 and 0)
    # mru_offset[i] = total number of containers in measures 0 to i-1
    mru_offset = [0]
    running_mru = 0

    if tactus == 1:
        for m_idx in range(len(durs)):
            if m_idx < len(accent_pattern) and accent_pattern[m_idx]:
                pattern = accent_pattern[m_idx]
                cycle = sum(pattern)
                if cycle > 0:
                    # Number of full cycles in measure
                    n_cycles = durs[m_idx] / cycle
                    # Number of containers: each cycle has len(pattern), but partial cycle counts partial containers
                    containers_in_measure = 0
                    remaining = durs[m_idx]
                    while remaining > 0:
                        for size in pattern:
                            if remaining <= 0:
                                break
                            if size > 0:
                                containers_in_measure += 1
                                remaining -= size
                            else:
                                break
                    running_mru += containers_in_measure
            mru_offset.append(running_mru)
    elif tactus == 0:
        for m_idx in range(len(durs)):
            beat_unit = 1.0 / time_signatures[m_idx][1]
            containers = int(durs[m_idx] / beat_unit + 0.5)  # round to nearest
            running_mru += containers
            mru_offset.append(running_mru)
    else:  # tactus == 2: measure-level
        for m_idx in range(len(durs)):
            running_mru += 1
            mru_offset.append(running_mru)

    # Process each voice independently
    for staff in rh_meas:
        for voice in staff:
            global_pulse = 0.0
            current_measure = None
            pos_in_measure = 0.0

            # --- First pass: assign tentative mru ---
            for element in voice:
                label, duration, measure_idx = element[:3]

                # Handle measure change
                if measure_idx != current_measure:
                    current_measure = measure_idx
                    pos_in_measure = 0.0

                # Get container and local index within measure
                container_dur, local_mru = get_container_index(measure_idx, pos_in_measure)

                # Global MRU = offset for this measure + local index within measure
                if measure_idx < len(mru_offset):
                    mru_index = mru_offset[measure_idx] + local_mru
                else:
                    mru_index = local_mru  # fallback

                # Assign mru
                element.append(mru_index)

                # Advance timing only for non-grace notes
                if duration > 0:
                    global_pulse += duration
                    pos_in_measure += duration

            # --- Second pass: fix grace notes ---
            for k, element in enumerate(voice):
                if element[1] == 0:  # grace note
                    measure_idx = element[2]
                    new_mru = None

                    # Look forward: next non-grace in same measure
                    for future in voice[k+1:]:
                        if future[1] > 0 and future[2] == measure_idx:
                            new_mru = future[3]
                            break

                    # If not found, look backward
                    if new_mru is None:
                        for prev in reversed(voice[:k]):
                            if prev[1] > 0 and prev[2] == measure_idx:
                                new_mru = prev[3]
                                break

                    if new_mru is not None:
                        element[3] = new_mru
    return rh_meas

def count_mru_containers(durs, accent_pattern):
    total_mru = 0
    for i, dur in enumerate(durs):
        if i >= len(accent_pattern) or not accent_pattern[i]:
            # No pattern defined → treat as one container?
            containers = 1 if dur > 0 else 0
            total_mru += containers
            continue

        pattern = accent_pattern[i]
        cycle = sum(pattern)
        containers = 0
        t = 0.0

        # If measure has zero duration
        if dur <= 0:
            continue

        # Use pattern in cycle until we cover the measure duration
        while t < dur:
            size = pattern[containers % len(pattern)]
            if size <= 0:
                break  # avoid infinite loop
            t += size
            containers += 1

        total_mru += containers
    return total_mru

# -----> MAIN
#where the MRU fun starts. Inputs durs,<xmlElement>,array of metros,tactusLevel,array of Rhythms,ternary
def mru(durs, focusPart, metro_list, tactus, rhythm_meas, accent_pattern):
    
    # print(rhythm_meas[0][0][0])
    time_signatures = []
    speeds_per_measure = []

    # Gather first Time Signature
    if(focusPart[0].find('attributes/time')) is None:
        print("Warning! There's no Time Signature on first measure. Do not trust RIM indicators.")

    # Go thru all measures
    for idx,i in enumerate(focusPart):
        # a. Time signatures
        if (i.find('attributes/time') is not None):
            numerator = float(i.find('attributes/time/beats').text)
            denominator = float(i.find('attributes/time/beat-type').text)
            time_signature = [numerator, denominator]
        time_signatures.append(time_signature)
        if(len(accent_pattern[idx]) == 0):
            accent_pattern[idx] = assign_accent(time_signature[0])

    newMru = assign_mru(rhythm_meas, time_signatures, durs, tactus, accent_pattern)
    # print(newMru)
    # print(durs)

    match tactus:

        case 0:
            mru_count = 0
            for i in range(len(time_signatures)):
                num = round_up(durs[i], 1 / time_signatures[i][1]) # Anacruxis bug
                mru_count += int(num / (1 / time_signatures[i][1]))
        case 1:
            mru_count = count_mru_containers(durs, accent_pattern)
        case 2:
            mru_count = len(time_signatures)
        case _:
            print('no definition for such tactus value...')

        

    # Speed in each measure
    speed = 1000
    metros_old = []
    bpm = [0,0]
    
    # Define the speed in each measure
    for id,i in enumerate(metro_list): 
        dots = 0
        equals = []
        idx = -1
        # Check for metronomic equivalences.
        for j in i[1]:
            if isinstance(j,(int, float)):
                idx += 1
            equals.append([idx,j])
        metros = [[] for x in range(equals[len(equals)-1][0]+1)]
        for j in equals:
            metros[j[0]].append(j[1])
        # Check for dot notation in metronomic indication
        for j in range(len(metros)):
            dots = metros[j].count('dot')
            dot = ((0.5 ** dots) * (( 1 / (0.5 ** dots) ) - 1)) + 1
            metros[j] = metros[j][0] * dot
  
        # At the moment we only verify the 'three complex rule' on the first two metronome indications
        if(metros_old != metros):
            if ((metros[0] <= 1.0) and (metros[1] <= 1.0)): # If both sides of equivalence are notation
                # print(metros)
                if (metros[0] != metros[1]):
                    factor = metros[0] / metros[1]
                    speed = speed / factor
                    bpm[0] = metros[0]
                    bpm[1] = metros[1]
            else:
                # print(metros)
                for j in metros:
                    if j <= 8.0: # If it is notation
                        bpm[0] = j
                    if j > 8.0: # If it is BPM (does not work for BPMs less than 8)
                        bpm[1] = j
                speed = (0.25 / bpm[0]) * (60000 / bpm[1])
        metros_old = metros
        metro_list[id].append([bpm[0],speed])

    # Calculate speed in each measure
    current_speed = 0
    for i in range(len(focusPart)):
        note_factor = 1/(time_signatures[i][1])
        speed_factor = note_factor / metro_list[i][2][0]    # Relationship betwee timeSignature and Metronomic indication
        pulses_per_measure = durs[i] / note_factor          # How many pulses there are in the measure
        current_speed = speed_factor * metro_list[i][2][1] * pulses_per_measure
        speeds_per_measure.append(current_speed)
    
    totalDur = sum(speeds_per_measure)
    mru_avg = totalDur / mru_count
    # print(mru_count)
    # print(time_signatures)
    return totalDur, mru_count, mru_avg, time_signatures, newMru, accent_pattern