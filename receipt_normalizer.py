import copy


def get_topleft(phrases):
    # Phrase can a word or wordgroup

    # Put phrase into a list if single phrase passed
    if not isinstance(phrases, list):
        phrases = [phrases]

    # Handle different keys
    bbname = 'boundingBox'
    if 'boundingBox' not in phrases[0].keys():
        bbname = 'boundingPoly'

    box = get_bbox([ph[bbname]['vertices'] for ph in phrases])
    return {'x': box[0]['x'], 'y': box[0]['y']}


def get_dimensions(phrases):
    # Phrase can a word or wordgroup

    # Put phrase into a list if single phrase passed
    if not isinstance(phrases, list):
        phrases = [phrases]

    # Handle different keys
    bbname = 'boundingBox'
    if 'boundingBox' not in phrases[0].keys():
        bbname = 'boundingPoly'

    box = get_bbox([ph[bbname]['vertices'] for ph in phrases])
    return {'width': box[2]['x'] - box[0]['x'],
            'height': box[2]['y'] - box[0]['y']}


def get_bbox(boxes):
    """
    Find coordinates of rectangular bounding box for a set of boxes.
    :param boxes: list of boxes
    :return: box [{'x': val, 'y': val},{},{},{}]
    """
    x_coords = []
    y_coords = []
    for box in boxes:
        for coord in box:
            x_coords.append(coord['x'])
            y_coords.append(coord['y'])

    max_y = max(y_coords)
    min_y = min(y_coords)
    max_x = max(x_coords)
    min_x = min(x_coords)

    return [{'x': min_x, 'y': min_y},
            {'x': max_x, 'y': min_y},
            {'x': max_x, 'y': max_y},
            {'x': min_x, 'y': max_y}]


def get_orientation(words):
    """
    Get orientation for a collection of words.
    :param words: list of words
    :return: char ('U' - upright, 'L' - left, 'R' - right, 'F' - flipped)
    """
    w_orient = []
    w_dir = []
    for word in words:
        # Find out if most words are orientated horizontally or vertically
        width = abs(word['boundingPoly']['vertices'][0]['x']\
            - word['boundingPoly']['vertices'][2]['x'])
        height = abs(word['boundingPoly']['vertices'][0]['y']\
            - word['boundingPoly']['vertices'][2]['y'])
        if width >= height:
            w_orient.append('H')
        else:
            w_orient.append('V')
        # Try to guess direction of each word (imperfect)
        if word['boundingPoly']['vertices'][0]['x'] - word['boundingPoly']['vertices'][1]['x'] < 0:
            w_dir.append('U')
        elif word['boundingPoly']['vertices'][0]['x'] - word['boundingPoly']['vertices'][1]['x'] > 0:
            w_dir.append('F')
        elif word['boundingPoly']['vertices'][0]['y'] - word['boundingPoly']['vertices'][1]['y'] < 0:
            w_dir.append('R')
        elif word['boundingPoly']['vertices'][0]['y'] - word['boundingPoly']['vertices'][1]['y'] > 0:
            w_dir.append('L')
    dir_vote = list(map(lambda x: sum(1 for o in w_dir if o == x), ['U', 'L', 'R', 'F']))
    orient_vote = list(map(lambda x: sum(1 for o in w_orient if o == x), ['H', 'V']))
    # Cross check direction identification results vs. orientation detection
    if orient_vote[0] >= orient_vote[1]:
        dir_vote[1] = dir_vote[2] = 0
    else:
        dir_vote[0] = dir_vote[3] = 0
    result = list(zip(['U', 'L', 'R', 'F'], dir_vote))
    result.sort(key=lambda x: -x[1])
    return result[0][0]


def rotate_cw(words):
    """
    Rotate coordinates of a collection of words clockwise.
    :param words: list of words
    :return: list of words
    """
    rotated_words = copy.deepcopy(words)
    boundary = get_bbox([word['boundingPoly']['vertices']
                        for word in rotated_words])
    lw = boundary[2]['y'] - boundary[0]['y']
    for i, word in enumerate(words):
        rotated_words[i]['boundingPoly']['vertices'][0]['x'] \
            = lw - words[i]['boundingPoly']['vertices'][0]['y']
        rotated_words[i]['boundingPoly']['vertices'][1]['x'] \
            = lw - words[i]['boundingPoly']['vertices'][1]['y']
        rotated_words[i]['boundingPoly']['vertices'][2]['x'] \
            = lw - words[i]['boundingPoly']['vertices'][2]['y']
        rotated_words[i]['boundingPoly']['vertices'][3]['x'] \
            = lw - words[i]['boundingPoly']['vertices'][3]['y']
        rotated_words[i]['boundingPoly']['vertices'][0]['y'] \
            = words[i]['boundingPoly']['vertices'][0]['x']
        rotated_words[i]['boundingPoly']['vertices'][1]['y'] \
            = words[i]['boundingPoly']['vertices'][1]['x']
        rotated_words[i]['boundingPoly']['vertices'][2]['y'] \
            = words[i]['boundingPoly']['vertices'][2]['x']
        rotated_words[i]['boundingPoly']['vertices'][3]['y'] \
            = words[i]['boundingPoly']['vertices'][3]['x']

    return rotated_words


def clean_coords(words):
    """
    Filter out words with corrupted coordinates
    :param words: list of words
    :return: list of words with valid vertices' coordinates
    """
    correct = []

    for word in words:
        coords = word['boundingPoly']['vertices']
        x_missing = []
        y_missing = []
        for i, coord in enumerate(coords):
            if 'x' not in coord:
                x_missing.append(i)
            if 'y' not in coord:
                y_missing.append(i)
        if len(x_missing) == len(y_missing) == 0:
            correct.append(word)

    return correct


def put_upright(words, orientation):
    """
    Rotate a set of words (receipt) upright.
    :param words: list of words
    :param orientation: initial orientation
    :return: list of words
    """
    if orientation == 'U':
        return words
    elif orientation == 'L':
        return rotate_cw(words)
    elif orientation == 'F':
        return rotate_cw(rotate_cw(words))
    elif orientation == 'R':
        return rotate_cw(rotate_cw(rotate_cw(words)))

    return words


def flush_top_left(words):
    """
    Pull receipt to top left corner by subtracting coordinates of bbox's upper-left corner
    from all coordinates.
    :param words: list of words
    :return: list of words
    """
    boundary = get_bbox([word['boundingPoly']['vertices']
                        for word in words])

    min_x = boundary[0]['x']
    min_y = boundary[0]['y']

    nwords = copy.deepcopy(words)
    for i, nword in enumerate(nwords):
        for j, nw in enumerate(nword['boundingPoly']['vertices']):
            nwords[i]['boundingPoly']['vertices'][j]['x'] =\
                nwords[i]['boundingPoly']['vertices'][j]['x'] - min_x
            nwords[i]['boundingPoly']['vertices'][j]['y'] =\
                nwords[i]['boundingPoly']['vertices'][j]['y'] - min_y

    return nwords


def scale(words, w=300):
    """
    Scale word boxes based on receipt width.
    :param words: list of words
    :param w: int - desired width
    :return: list of words
    """
    boundary = get_bbox([word['boundingPoly']['vertices']
                        for word in words])
    width = boundary[2]['x'] - boundary[0]['x']
    scl = w / width

    nwords = copy.deepcopy(words)
    for i, nword in enumerate(nwords):
        for j, nw in enumerate(nword['boundingPoly']['vertices']):
            nwords[i]['boundingPoly']['vertices'][j]['x'] =\
                int(nwords[i]['boundingPoly']['vertices'][j]['x'] * scl)
            nwords[i]['boundingPoly']['vertices'][j]['y'] =\
                int(nwords[i]['boundingPoly']['vertices'][j]['y'] * scl)

    return nwords


def normalize(words):
    """
    Apply normalization (rotation, scaling, etc.) to words in a receipt.
    :param words: list of words
    :return: list of words
    """
    words = clean_coords(words)
    words = flush_top_left(words)
    orientation = get_orientation(words)
    words = put_upright(words, orientation)
    words = scale(words)
    return words, orientation
