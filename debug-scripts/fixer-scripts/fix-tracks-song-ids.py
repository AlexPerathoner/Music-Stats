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
DB_FILE_BAK = '20240403-music-play-count-db.bak.sqlite3'

def main():
    conn = sqlite3.connect(DB_FILE)
    meta_data = get_meta_data(DB_FILE_BAK)
    df_meta = pd.DataFrame(meta_data, columns=['song_id', 'song_name', 'artist_name', 'album_name', 'date_added'])

    # go over all tracks in conn, get song name, artist name, album name, date added and check if there is a matching track in conn_bak. get the song id and update the track in conn

    c = 0
    tot = len(df_meta)
    for row in df_meta.iterrows():
        c += 1
        print("%d / %d" % (c, tot))
        song_id = row[1][0]
        song_name = row[1][1]
        artist_name = row[1][2]
        album_name = row[1][3]
        date_added = row[1][4]
        print(song_name, artist_name, album_name, date_added)
        sql_str = "update tracks set song_id = ? where song_name = ? "
        if (artist_name is not None):
            sql_str += " and artist_name = ? "
            if (album_name is not None):
                sql_str += " and album_name = ? "
                sql_str += " and date_added = ? and present_in_bak = 1;"
                conn.execute(sql_str, (song_id, song_name, artist_name, album_name, date_added))
            else:
                sql_str += " and date_added = ? and present_in_bak = 1;"
                conn.execute(sql_str, (song_id, song_name, artist_name, date_added))

        else:
            if (album_name is not None):
                sql_str += " and album_name = ? "
                sql_str += " and date_added = ? and present_in_bak = 1;"
                conn.execute(sql_str, (song_id, song_name, album_name, date_added))
            else:
                sql_str += " and date_added = ? and present_in_bak = 1;"
                conn.execute(sql_str, (song_id, song_name, date_added))


            
        conn.commit()

    print("Closing...")
    conn.close()


if __name__ == "__main__":
    main()