# Key-signature accidental load: mean absolute number of accidentals implied by the prevailing key signature across measures.

def histoFifths(attributes, measNums):
    """
    Compute the 'Fifths indicator':

    Mean absolute number of accidentals implied by the
    key signature, weighted by the number of measures.

    Key signatures persist until changed.

    Returns:
        [fifths_indicator]
    """

    # Default key signature: C major / A minor
    current_fifths = 0

    # One value for each measure.
    # None means that no new key signature was declared
    # in that measure.
    keys_per_measure = [None] * len(measNums)

    # Traverse all <attributes> elements
    for attr_item in attributes:

        xml_elem = attr_item[0]
        measure_idx = attr_item[1]

        # Look for <key><fifths>...</fifths></key>
        fifths_elem = xml_elem.find('key/fifths')

        if fifths_elem is not None and fifths_elem.text is not None:

            current_fifths = int(fifths_elem.text)

            if 0 <= measure_idx < len(keys_per_measure):
                keys_per_measure[measure_idx] = current_fifths

    # Propagate the current key signature forward
    current_fifths = 0

    for i in range(len(keys_per_measure)):

        if keys_per_measure[i] is not None:
            current_fifths = keys_per_measure[i]

        keys_per_measure[i] = abs(current_fifths)

    # Compute mean absolute fifths across measures
    if len(measNums) == 0:
        return [0.0]

    fifths_indicator = (
        sum(keys_per_measure) / len(measNums)
    )

    return [round(fifths_indicator, 3)]