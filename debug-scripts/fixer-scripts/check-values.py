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
from db import get_count_data, get_meta_data, build_data, get_count_data_for_ids
from visualize_some_songs import visualize_song_time_series
from plot import create_lines_plot_for_tracks, create_table_plot_for_tracks


def main(DB_FILE):
    count_data = get_count_data_for_ids(DB_FILE, [])
    df = pd.DataFrame(count_data, columns=['song_id', 'count', 'date_count', 'hash', 'last_played_count', 'song_name'])
    # group by hash
    grouped = df.groupby('song_id')
    song_errors_count = 0
    errors_count = 0
    errors_dates = []
    ids = []
    for (song_id, group) in grouped:
        # order by date_count
        group = group.sort_values(by='date_count')
        old_count = 0
        error_found = False
        for row in group.iterrows():
            count = row[1][1]
            # print(count)
            song_name = row[1][5]
            date_count = row[1][2]

            if count < old_count:
                print(f"count got lower {song_name} ({song_id}) on {date_count}. {old_count} -> {count} ")
                errors_dates.append(date_count)
                if song_id not in ids:
                    ids.append(song_id)
                errors_count += 1
                error_found = True

            old_count = count
            last_played_count = row[1][4]
        
        if not isnan(last_played_count):
            if int(last_played_count) < old_count:
                print(f"last_played_count got lower {song_name} ({song_id}) on {date_count}. {old_count} -> {last_played_count} ")
                if song_id not in ids:
                    ids.append(song_id)
                errors_count += 1
                error_found = True
            if int(last_played_count) > old_count + 10:
                print(f"last_played_count got higher by a lot {song_name} ({song_id}) on {date_count}. {old_count} -> {last_played_count} ")
                if song_id not in ids:
                    ids.append(song_id)
                errors_count += 1
                error_found = True

        if error_found:
            song_errors_count += 1

    print(f"Found {song_errors_count} songs with errors")
    print(f"Found {errors_count} errors")

    errorsdates = set(errors_dates)
    print(f"Found {len(errorsdates)} errors dates: {errorsdates}")

    # optional part to visualize those songs in graph
    count_data = get_count_data_for_ids(DB_FILE, ids)
    df = pd.DataFrame(count_data, columns=['song_id', 'count', 'date_count', 'hash', 'last_played_count', 'song_name'])
    # count_data = get_count_data_for_ids_from_backup(DB_FILE, ids)
    # df = pd.DataFrame(count_data, columns=['song_id', 'count', 'date_count', 'song_name'])

    visualize_song_time_series(df)

if __name__ == '__main__':
    # main('music-play-count-db.sqlite3')
    main('music-play-count-db-fixed.sqlite3')
