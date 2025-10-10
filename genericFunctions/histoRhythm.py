import math

def histoRhythm(nStaves,rhFig,divs,measNumList,focusPart):

    # === State Variables ===
    measNum = -1
    accum = [[0] * 4 for _ in range(nStaves)]  # [staff][voice]
    
    all_rh = [[[] for x in range(4)] for y in range(nStaves)]  # 4 voices
    rhythmMeas = [[[] for x in range(4)] for y in range(nStaves)]
    durations = [0.0] * len(measNumList)
    hide = ''
    
    # ---> Go thru all measures in part, and add elts
    for idi,i in enumerate(focusPart):
        forward_anacruxis = False
        measNum = int(measNumList[idi])
        # Check if it is a measure repeat
        # MuseScore version 3.6, the <repeat-measure> element does not exists, it puts a silence
        if (len(i.findall('note')) == 0 and i.find('forward')):
            durations.append( int(i.find('forward/duration').text) * divs )
        
        # got thru all elements[j] in measures[i]
        for idj,j in enumerate(i):
            # Select forward[j] in each measure[i]
            if (j.tag == 'forward'):
                duration = float(j.find('duration').text) * divs
                fw = False
                # Find forward elements for compensating lack of rests in other voices
                if (idj < len(i)-1):
                    if(i[idj+1].tag == 'note'):
                        fw = True
                        voice_id = 1
                        # print(i[idj+1].find("voice").text, j.find('duration').text, 'before')
                    if(i[idj-1].tag == 'note'):
                        fw = True
                        voice_id = -1
                        # print(i[idj-1].find("voice").text, j.find('duration').text, 'after')     
                else:
                    if (i[idj-1].tag == 'note'):
                        fw = True
                        voice_id = -1
                        # print(i[idj-1].find("voice").text, j.find('duration').text, 'after')
                if (fw):
                    hide = 'no' # TODO add this feature
                    # a. Assign voices
                    staff = int(math.ceil(int(i[idj+voice_id].find('voice').text)) / 4)
                    voice = (int(i[idj+voice_id].find('voice').text) - 1) % 4
                    if (voice == 0):
                        forward_anacruxis = True
                    if (forward_anacruxis is False):
                        # b. Accum for note index
                        accum[staff][voice] += 1
                        # c. Add to array
                        all_rh[staff][voice].append([ str(accum[staff][voice])+hide,duration,measNum ])
                        rhythmMeas[staff][voice].append([ str(accum[staff][voice])+hide,duration,measNum ])
                    hide = ''
                fw = False
                   
            # Select note[j] in each measure[i]
            if (j.tag == 'note'):
                # a. Assign voices
                staff = int(math.ceil(int(j.find('voice').text)) / 4)
                voice = (int(j.find('voice').text) - 1) % 4
                
                # b. Find notes that aren't part of a chord
                if (j.find('chord') is None):
                    # c. Accum for note index
                    accum[staff][voice] += 1
                    # d. Check if <dot> element is present
                    if (j.find('dot') is not None):
                        dots = len(j.findall('dot'))    # Each dot is separated
                        dot = ((0.5 ** dots) * (( 1 / (0.5 ** dots) ) - 1)) + 1
                    else:
                        dot = 1
                        
                    # e. Check if j is tuplet
                    if (j.find('time-modification') is not None):
                        tupl = float(j.find('time-modification/normal-notes').text) / float(j.find('time-modification/actual-notes').text)
                    else:
                        tupl = 1
                        
                    # f. Build note duration
                    if (j.find('type') is not None):
                        noteType = rhFig[j.find('type').text]
                    else:
                        if (j.find('rest').attrib['measure'] is not None):
                            #print('measure rest')
                            noteType = int(j.find('duration').text) * divs
                            
                    # g. If it is a grace note, zero duration (we do not know the outcome, as duration, of this type of information)
                    if (j.find('grace') is not None):
                        #print('grace, accaciatura, etc.')
                        noteType = 0
                        
                    # Add 'no' if note is hidden, latter it will be obliterated from evaluation
                    for k in j.items():
                        if k[0] == 'print-object':
                            hide = j.attrib['print-object']
                            
                    # h. Add to array
                    all_rh[staff][voice].append([ str(accum[staff][voice])+hide,dot*tupl*noteType,measNum])
                    rhythmMeas[staff][voice].append([ str(accum[staff][voice])+hide,dot*tupl*noteType,measNum])
                    
                    # i. Accum note durations only for voice one, and staff one. 
                    # This array shows differences between measure durations (e.g. anacruxis duration, time signatures duration)
                    if (j.find('voice').text == '1'):
                        # Inside loop
                        meas_index = idi  # or map measNum to index
                        if 0 <= meas_index < len(durations):
                            durations[meas_index] += dot * tupl * noteType
                    hide = ''
    
    # ---> We add rest measures for voices
    for i in range(len(rhythmMeas)): # Staves
        voiceOne = []
        voiceTwo = []
        voiceThree = []
        voiceFour = []
        for j in range(len(rhythmMeas[i])): # Voices
            for k in range(len(rhythmMeas[i][j])): # Elements
                # add whole measures rests to other voices
                if (j == 0):
                    voiceOne.append(rhythmMeas[i][j][k][2])
                if (j == 1):
                    voiceTwo.append(rhythmMeas[i][j][k][2])
                if (j == 2):
                    voiceThree.append(rhythmMeas[i][j][k][2])
                if (j == 3):
                    voiceFour.append(rhythmMeas[i][j][k][2])
        voiceOne = list(dict.fromkeys(voiceOne))   
        voiceOne = [x for x in measNumList if x not in voiceOne]
        voiceTwo = list(dict.fromkeys(voiceTwo))
        voiceTwo = [x for x in measNumList if x not in voiceTwo]
        voiceThree = list(dict.fromkeys(voiceThree))
        voiceThree = [x for x in measNumList if x not in voiceThree]
        voiceFour = list(dict.fromkeys(voiceFour))
        voiceFour = [x for x in measNumList if x not in voiceFour]

        if (len(measNumList) > len(voiceOne)):
            for j in range(len(voiceOne)):
                #all_rh[i][1].append(['add',durations[voiceOne[j]-1],voiceOne[j]])
                #all_rh[i][1].sort(key = lambda x: x[2])
                rhythmMeas[i][0].append(['add',durations[voiceOne[j]],voiceOne[j]])
                rhythmMeas[i][0].sort(key = lambda x: x[2])
        if (len(measNumList) > len(voiceTwo)):
            for j in range(len(voiceTwo)):
                #all_rh[i][1].append(['add',durations[voiceTwo[j]-1],voiceTwo[j]])
                #all_rh[i][1].sort(key = lambda x: x[2])
                rhythmMeas[i][1].append(['add',durations[voiceTwo[j]],voiceTwo[j]])
                rhythmMeas[i][1].sort(key = lambda x: x[2])
        if (len(measNumList) > len(voiceThree)):
            for j in range(len(voiceThree)):
                #all_rh[i][1].append(['add',durations[voiceTwo[j]-1],voiceTwo[j]])
                #all_rh[i][1].sort(key = lambda x: x[2])
                rhythmMeas[i][2].append(['add',durations[voiceThree[j]],voiceThree[j]])
                rhythmMeas[i][2].sort(key = lambda x: x[2])
        if (len(measNumList) > len(voiceFour)):
            for j in range(len(voiceFour)):
                #all_rh[i][1].append(['add',durations[voiceTwo[j]-1],voiceTwo[j]])
                #all_rh[i][1].sort(key = lambda x: x[2])
                rhythmMeas[i][3].append(['add',durations[voiceFour[j]],voiceFour[j]])
                rhythmMeas[i][3].sort(key = lambda x: x[2])       
    
    '''
    * all nStaves dimention array with 4 arrays for voices with all rhythmic 
        information [ [ [],[],[],[] ] ] note index, duration, measure-1
    * accum nStaves dimention array with 4 integers that enumerate the amount of notes in all fragment
    * rhythmMeas is the same as all, but adds measure rests for measures that do not have information
    * Durations is the sum of divisions in measure. E.g. in a 4/4 measure [1,1,1...]
    * repetition_symbol is an array of repetition elements in measure (will be joined with the class).
    '''
    return all_rh, rhythmMeas, durations