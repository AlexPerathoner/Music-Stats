# some songs have a song_id that changes over time.
# This script:
# 1. finds all songs which have same name artist and album
# 2. shows them and asks if they should be merged
# 3. merges them

import os
import datetime
import subprocess
import sqlite3
import json
import pandas as pd
from utils import save_json, tracks_list_to_df, parse_date, date_to_str
from db import get_count_data, get_meta_data, build_data
from plot import create_lines_plot_for_tracks, create_table_plot_for_tracks

DB_FILE = 'music-play-count-db.sqlite3'

def get_ids_removed_from_db_internal(ids):
    # execute applescript to get ids of songs in db
    applescript = """
tell application "Music"
	set listOfIdsToCheck to """ + str(ids).replace('[', '{').replace(']', '}') + """
	
	set theString to ""
	repeat with s in (get every track)
		if database ID of s is in listOfIdsToCheck then
			set theString to theString & "" & (database ID of s & ";")
		end if
		
	end repeat
	return theString
end tell
"""
    # print(applescript)
    p = subprocess.Popen(['osascript', '-'], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = p.communicate(input=applescript.encode())
    ids_existing_in_db = stdout.decode().replace('\n', '').split(';')
    ids_existing_in_db = [id for id in ids_existing_in_db if id != '']
    ids_existing_in_db = [int(id) for id in ids_existing_in_db]
    return [id for id in ids if int(id) not in ids_existing_in_db]

def get_ids_removed_from_db(ids):
    # divide ids into chunks of 2000 and run get_ids_removed_from_db_internal on each chunk
    print("Dividing ids into chunks of 2000...")
    ids_chunks = [ids[i:i+2000] for i in range(0, len(ids), 2000)]
    ids_remo = []
    c = 0
    for ids_chunk in ids_chunks:
        c += 1
        print("Processing chunk %d of %d" % (c, len(ids_chunks)))
        ids_removed_chunk = get_ids_removed_from_db_internal(ids_chunk)
        ids_remo.extend(ids_removed_chunk)
    return ids_remo

def build_map_ids_to_duplicates(md, ids_remo):
    map_id_dupl = {}
    for row in md: # processing only songs still in library
        duplicates = []
        id = row[0]
        if id in ids_remo: # if id is still in library
            continue
        for row2 in md: # processing duplicates, not in library anymore
            # id is different, name artist and album are the same
            if row[0] != row2[0] and row[1] == row2[1] and row[2] == row2[2] and row[3] == row2[3]:
                dupl_id = row2[0]
                if dupl_id in ids_remo:
                    duplicates.append(row2)

        if len(duplicates) > 1:
            map_id_dupl[id] = duplicates
    return map_id_dupl

def override_min_date_added(md, map_id_dupl):
    for row in md:
        id = row[0]
        dupl = map_id_dupl.get(id, [])
        dates_added = [row[4] for row in dupl]
        if len(dates_added) > 0:
            date_added = min(dates_added)
            row[4] = date_added

    return md

if __name__ == '__main__':
    start_time = datetime.datetime.now()
    if not os.path.exists('out'):
        print('Creating out directory...')
        os.makedirs('out')

    print("Importing from DB...")
    # count_data = get_count_data(DB_FILE) # not needed for now
    meta_data = get_meta_data(DB_FILE)

    print("Getting removed songs from DB...")
    all_ids = list(set([row[0] for row in meta_data]))
    ids_removed = get_ids_removed_from_db(all_ids)
    print("Found %d removed songs in DB" % len(ids_removed))

    print("Building map of duplicates by id...")
    map_ids_to_duplicates = build_map_ids_to_duplicates(meta_data, ids_removed)
    
    # save map to json
    file_name = 'map_ids_to_duplicates.json'
    with open(file_name, 'w') as f:
        json.dump(map_ids_to_duplicates, f)

    print("Overriding min date added...")
    meta_data = override_min_date_added(meta_data, map_ids_to_duplicates)

    print("Overriding ")

