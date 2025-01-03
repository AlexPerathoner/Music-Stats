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
import hashlib

DB_FILE = 'music-play-count-db.sqlite3'

def main():
    df = pd.read_csv('play-count-fixed.csv', sep=';', encoding='utf-8')
    # remove all rows with nan in song_id
    # print(df[df['song_id'].isna()])
    df = df[~df['song_id'].isna()]

    # song_id as int
    df['song_id'] = df['song_id'].astype(int)

    # convert all columns headers to iso format as str (yyyy-mm-dd)
    dates_cols = pd.to_datetime(df.columns[1:], format='%d-%m-%y').strftime('%Y-%m-%d')
    new_cols = [df.columns[0]] + dates_cols.tolist()
    df.columns = new_cols

    # filter out all columns < 2024-04-02
    df = df.loc[:, df.columns[df.columns > '2024-04-02']]

    conn = sqlite3.connect(DB_FILE)

    # iterate over each row
    c = 0
    tot = len(df)
    for row in df.iterrows():
        c += 1
        song_id = int(row[1][0])
        print("%d / %d - %s" % (c, tot, song_id))
        # get row
        song_data = df[df['song_id'] == song_id]
        # iterate over columns
        for col in song_data.columns[1:]: # each column is a date, skipping first column (song_id)
            # get column
            col_data = song_data[col]

            date_str = col
            # check if all values are nan
            if col_data.isna().all():
                print("all nan. skip")
                continue
            
            # as int
            play_count = int(col_data.astype(int).values[0])
            if isnan(play_count):
                continue
            if play_count == 0:
                continue
            
            # print(song_id, play_count, date_str)
            conn.execute("insert or replace into play_counts (song_id, count, date_count) values (?, ?, ?)", (song_id, play_count, date_str))
            conn.commit()

if __name__ == "__main__":
    main()