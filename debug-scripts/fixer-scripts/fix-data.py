import os
import datetime
import subprocess
import sqlite3
import json
import pandas as pd
from numpy import isnan
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
from utils import save_json, tracks_list_to_df, parse_date, date_to_str
from db import get_count_data, get_meta_data, build_data
from plot import create_lines_plot_for_tracks, create_table_plot_for_tracks

DB_FILE = 'music-play-count-db.sqlite3'
DB_FILE_BAK = '20240403-music-play-count-db.bak.sqlite3'

# old function needed to export play count to table
def create_pivoted_table_in_csv_from_db_play_count():
    count_data = get_count_data(DB_FILE)
    # df = pd.DataFrame(count_data, columns=['song_id', 'count', 'date_count'])
    # y axis is song id
    # x axis is date
    df = pd.DataFrame(count_data, columns=['song_id', 'play_count', 'date'])

    # Convert date column to datetime
    df['date'] = pd.to_datetime(df['date'])

    # Pivot the DataFrame to have song_id as index and date as columns
    pivoted_df = df.pivot(index='song_id', columns='date', values='play_count')
    pivoted_df = pivoted_df.loc[:, pivoted_df.columns >= '2024-01-01']

    # convert all nan to ""
    pivoted_df = pivoted_df.fillna(-1)
    pivoted_df = pivoted_df.astype(int)
    pivoted_df = pivoted_df.astype(str)
    pivoted_df = pivoted_df.replace("-1", '')
    

    pivoted_df.to_csv('count_data.csv', index=True)

# old function to check if all data in csv was consistently increasing
def check_if_all_values_increasing():
    # read csv test.csv
    df = pd.read_csv('test.csv', sep=';', encoding='utf-8')
    # for each row, go over all columns and check if value is greater than value in column before
    
    for row in df.iterrows():
        song_id = row[1][0]

        old_value = row[1][1]
        i = 1
        while isnan(old_value):
            old_value = row[1][i]
            i += 1

        while i < len(row[1]):
            new_value = row[1][i]
            if new_value < old_value:
                print(song_id, new_value, old_value)
            old_value = new_value
            i += 1

def replace_with_data_from_bak():
    meta_data_bak = get_meta_data(DB_FILE_BAK)
    df_meta_bak = pd.DataFrame(meta_data_bak, columns=['song_id', 'song_name', 'artist_name', 'album_name', 'date_added'])
    df_play_count = pd.read_csv('play-count-fixed.csv', sep=';', encoding='utf-8')

    meta_data = get_meta_data(DB_FILE)
    df_meta = pd.DataFrame(meta_data, columns=['hash', 'song_name', 'artist_name', 'album_name', 'date_added', 'path', 'present_in_bak', 'present_in_lib', 'song_id'])
    
    # filter present_in_bak = 0
    df_meta = df_meta[df_meta['present_in_bak'] == 0]
    df_meta = df_meta[df_meta['date_added'] <= '2024-04-02']

        
    conn = sqlite3.connect(DB_FILE)
    for row in df_meta.iterrows():
        song_id = ""
        song_name = row[1][1]
        artist_name = row[1][2]
        album_name = row[1][3]
        date_added = row[1][4]

        df_meta_filtered = df_meta_bak[df_meta_bak['song_name'] == song_name]
        if artist_name is not None:
            df_meta_filtered = df_meta_filtered[df_meta_filtered['artist_name'] == artist_name]
        if album_name is not None:
            df_meta_filtered = df_meta_filtered[df_meta_filtered['album_name'] == album_name]
        df_meta_filtered = df_meta_filtered[df_meta_filtered['date_added'] == date_added]

        if df_meta_filtered.empty:
            print("No match found", song_name, artist_name, album_name, date_added)
            continue

        song_id = str(df_meta_filtered['song_id'].values[0])
        print(song_name, " -> ", song_id)
        conn.execute("update tracks set song_id = ?, present_in_bak = 1 where song_name = ? and artist_name = ? and album_name = ? and date_added = ? and present_in_bak = 0;", (song_id, song_name, artist_name, album_name, date_added))
        conn.commit()

    # print("Closing...")

    conn.close()

def get_paths_and_meta():
    # execute applescript to get ids of songs in db
    applescript = """
    set theString to ""
    on formatDate(theDate)
        set year_ to year of theDate as string
        set month_ to text -2 thru -1 of ("0" & ((month of theDate) as integer))
        set day_ to text -2 thru -1 of ("0" & day of theDate)
        return year_ & "-" & month_ & "-" & day_
    end formatDate

    tell application "Music"
        set x to get every track
        repeat with s in x
            set trackPath to POSIX path of (get location of s)
            
            set theString to theString & "" & (database ID of s & ";" & (name of s) & ";" & (artist of s) & ";" & (album of s) & ";" & (my formatDate(date added of s)) & ";" & (trackPath) & "\r")
        end repeat
    end tell

    return theString
    """

    # p = subprocess.Popen(['osascript', '-'], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    # stdout, stderr = p.communicate(input=applescript.encode())
    # with open('temp.txt', 'w') as f:
    #     f.write(stdout.decode())
    df = pd.read_csv('temp.txt', sep=';', encoding='utf-8', header=None)
    df.columns = ['song_id', 'song_name', 'artist_name', 'album_name', 'date_added', 'track_path']
    # os.remove('temp.txt')
    return df


if __name__ == '__main__':
    replace_with_data_from_bak()