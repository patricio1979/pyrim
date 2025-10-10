def histoFifths(attributes, measNums):

    """
    Compute the 'Fifths indicator': 
    weighted average of |fifths| (absolute number of accidentals) per measure.
    
    Key signatures persist until changed.
    """

    # Initialize: default key = C major (0 sharps/flats)
    current_fifths = 0
    # List to store the fifths value for each measure
    keys_per_measure = [''] * (len(measNums)-1)
    keys_per_measure.insert(0,0)    # In case the part do not have predeterminated fifths element

    # Traverse each attributes entry
    for attr_item in attributes:
        xml_elem = attr_item[0]     # <attributes> element
        measure_idx = attr_item[1]  # Corresponding measure index

        # Look for <key><fifths>...</fifths></key>
        fifths_elem = xml_elem.find('key/fifths')
        if fifths_elem is not None and fifths_elem.text is not None:
            current_fifths = int(fifths_elem.text)
            # Assign current key signature to this measure
            keys_per_measure[measure_idx] = current_fifths

    # Now propagate the key forward to subsequent measures
    for i in range(len(keys_per_measure)):
        if(type(keys_per_measure[i]) == float or type(keys_per_measure[i]) == int):
            fifths = abs(keys_per_measure[i])
        keys_per_measure[i] = fifths

    # Compute weighted average of |fifths| across all measures
    total_weighted_abs_fifths = sum(abs(k) for k in keys_per_measure)
    fifths_indicator = total_weighted_abs_fifths / len(measNums)

    return [round(fifths_indicator, 3)]