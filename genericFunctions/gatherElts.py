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
    partId = []
    meas_nums = []                               # Useful if measure numbers were universally numbered if ommited, but no
    divisions = rhFig['quarter']                # Default division (denominator in time signature)
    accentsStr = []                             # Accent pattern in the form 'a ' + 'duration in denominators as 1,2,4,8,16...
    
    # ---> Get title of score
    # MuseScore 3.6.2
    workTitle = els.find('work')
    if workTitle is None:
        title = os.path.splitext(fileName)[0]   # If the file has no title, the fileName will be used
    else:
        title = els.find('work/work-title').text
    # MuseScore 4.5.2
    workTitle = els.find('credit')
    if workTitle is not None:
        if (els.find('credit/credit-type').text == 'title'):
            title = els.find('credit/credit-words').text
    # print(workTitle)

    # ---> Find the ID of the instrument (focusPart) in the score
    partId = ''
    parts_available = []
    available = True
    parts = els.findall('part-list/score-part')
    for part in parts:
        if (part.find('part-name').text is not None and part.find('score-instrument/instrument-name').text.lower()) == instName.lower(): # Not case sensitive
            partId = part.attrib['id']
        else:
            available = False
        parts_available.append(part.find('score-instrument/instrument-name').text.lower()) 
    # I have this mistake always. Naming instruments is perhaps the most difficult thing in building a musical corpus.
    if available == False:
        print(f'---->Warning: The instrument name "{instName}" does not exist in the file. Available parts are: {parts_available}. Working on the first instrument.')
        partId = part.attrib['id']
        instName = parts[0].find('score-instrument/instrument-name').text
    
    # ---> Isolate the focusPart for gathering elements
    parts = els.findall('part')
    for part in parts:
        if (part.attrib['id'] == partId):
            focusPart = part
            
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

        # ---> Gather 'divisions' element (the smallest duration in the score, a sort of quantization unit)
        if( elements.find('attributes/divisions') is not None ):
            divisions = rhFig['quarter'] / float(elements.find('attributes/divisions').text)
        
        # b. Search character indications in each measure (converted in the thesaurusCharacter.json)
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
            
        # b bis. Search metronome indications in each measure
        if(elements.find('direction/direction-type/metronome') is not None):    #If there is a metronome indication
            metroItems = [0,0]
            for i in elements.find('direction/direction-type/metronome'):
                if (i.tag == 'beat-unit'):
                    metroItems[0] = rhFig[i.text]                               # Important. Divisions is the float of a quarter, divs is the amount of divisions of a quarter
                if (i.tag == 'per-minute'):
                    metroItems[1] = float(i.text)
                if (i.tag == 'beat-unit-dot'):
                    metroItems[0].append('dot')
        
        metroList.append([meas_nums[idx],metroItems])

    # print(metroList)
    # print(accentsStr)
    accents_pattern = build_measure_patterns(accentsStr,len(meas_nums))
    # print(accents_pattern)
    return title, nStaves, attributes, metroList, divisions, focusPart, meas_nums, instName, accents_pattern