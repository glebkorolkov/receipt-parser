# Imports
import os
import json
import numpy as np
import pandas as pd

# Change working dir
PROJECT_FOLDER = '/home/gleb/Documents/Bootcamp/Projects/Foreceipt/playground/labeler'
os.chdir(PROJECT_FOLDER)
JSON_PATH = os.path.join(PROJECT_FOLDER, 'jsons')
RECEIPTS_CSV = os.path.join(PROJECT_FOLDER, 'data/receipts.csv')
WORDS_CSV = os.path.join(PROJECT_FOLDER, 'data/words.csv')

# Code for normalizing receipts
import receipt_normalizer as rn

# Helper functions

def read_json(filepath):
    """Function that open json file, decodes it and returns its content"""
    with open(filepath, 'r', encoding="utf-8") as f:
        content = f.read()
    return json.loads(content)


def parse_single_json(receipt_data):
    """
    Function that parses single json and returns two dataframes:
    the receipt and words.

    Parameters:
    -----------
    receipt_data: dict
        Dict with receipt data from parsed json

    Returns:
    --------
    (rdf, wdf): tuple with two DataFrames
        First df holding receipt data
        Second df holding receipt words
    """

    # Extract words
    receipt_words = receipt_data['textAnnotations'][1:]
    # Normalize
    norm_words, orientation = rn.normalize(receipt_words)
    # Get locales
    locales = None
    try:
        locales = receipt_data['fullTextAnnotation']['pages'][0]['property']\
            ['detectedLanguages']
    except:
        pass
    else:
        locales = "|".join([l['languageCode'] for l in locales])
    # Get width, height, and text
    rwidth = rn.get_dimensions(norm_words)['width']
    rheight = rn.get_dimensions(norm_words)['height']
    rtext = receipt_data['fullTextAnnotation']['text']
    # Get logo name if present
    logo = None
    if 'logoAnnotations' in receipt_data.keys():
        if len(receipt_data['logoAnnotations']) > 0:
            if 'description' in receipt_data['logoAnnotations'][0].keys():
                logo = receipt_data['logoAnnotations'][0]['description']
    # Put receipt info into dataframe
    rdf = pd.DataFrame(columns=['locales', 'width', 'height', 'text', 'logo', 'orient'], \
        data=[[locales, rwidth, rheight, rtext, logo, orientation]])
    # Get word data and wrap it into a dataframe
    receipt_words = []
    for word_data in norm_words:
        line = []
        line.append(None)
        try:
            line.append(word_data['description'])
            line.append(rn.get_topleft(word_data)['x'])
            line.append(rn.get_topleft(word_data)['y'])
            line.append(rn.get_dimensions(word_data)['width'])
            line.append(rn.get_dimensions(word_data)['height'])
        except:
            continue
        receipt_words.append(line)
    wdf = pd.DataFrame(columns=['rid', 'text', 'x1', 'y1', 'width', 'height'],\
        data = receipt_words)
    return (rdf, wdf)


def parse():
    """
    Function that iterates over available jsons, parses them and saves data
    into two csv files: one with receipt data, another one - with words.

    Parameters:
    -----------
    None

    Returns:
    --------
    None
    """
    # Iterate through json files parsing them
    json_list = os.listdir(JSON_PATH)
    counter = 0
    first_pass = True
    for json_name in json_list:
        # Skip if not .txt file
        if not os.path.splitext(json_name)[1] == '.txt':
            continue

        # Extract receipt id and code from filename: [id]_[code].txt
        rid = int(os.path.splitext(json_name)[0].split('_')[0])
        code = os.path.splitext(json_name)[0].split('_')[1]
        # Extract receipt and word data from json
        json_filepath = os.path.join(JSON_PATH, json_name)
        # Read json
        try:
            receipt_data = read_json(json_filepath)
            rdf, wdf = parse_single_json(receipt_data)
        except:
            print(f"Skipped file {json_name} due to read/parse issues!")
            counter += 1
            continue
        # Save (append) receipts to csv
        rdf['id'] = rid
        rdf['receipt_code'] = code
        rdf[['id', 'receipt_code', 'width', 'height']]\
            .to_csv(RECEIPTS_CSV, header=first_pass,\
            mode=('w' if first_pass else 'a'), index=False)

        # Save (append) words to csv
        wdf['rid'] = rid
        wdf.to_csv(WORDS_CSV, header=first_pass,\
        mode=('w' if first_pass else 'a'))
        first_pass = False
        counter += 1
        print(f" Processed {counter} json files. Current file: {json_name}", \
            end="\r")


def clean_up():
    """Function that opens resulting csvs, sorts them and modifies ids"""
    # Receipts
    receipts = pd.read_csv(RECEIPTS_CSV)
    receipts.sort_values(by='id', inplace=True)
    receipts.to_csv(RECEIPTS_CSV, index=False)
    # Words
    words = pd.read_csv(WORDS_CSV, index_col=0)
    words.reset_index(drop=True, inplace=True)
    words.rename_axis('id', inplace=True)
    words.reset_index(inplace=True)
    # Augment ids by 1, add empty date column and rearrange columns to comply
    # with django's table structure
    words['id'] = words['id'].astype(int) + 1
    words['date_add'] = np.nan
    words[['id', 'text', 'x1', 'y1', 'width', 'height', 'date_add', 'rid']]\
        .to_csv(WORDS_CSV, index=False)



# Program body -----------------------------------------------------------------

if __name__ == '__main__':
    parse()
    print("Done parsing. Cleaning up...")
    clean_up()
    print("Finished parsing!")
