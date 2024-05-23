"""2024.03.22 by Alex Pera"""

import os
import datetime
from utils import save_json, tracks_list_to_df, parse_date, date_to_str
from db import get_count_data, get_meta_data, build_data
from plot import create_lines_plot_for_tracks, create_table_plot_for_tracks

DB_FILE = 'music-play-count-db.sqlite3'
INCREASE_DAYS = 30
EXTENSIVE_SAVE = False
CALCULATE_TOP_PLAYED = True
CALCULATE_HOTTEST = True # todo simplify a lot, create one report (look at spotify )

def get_top_played_tracks(data, limit=100):
    for song_id, song_data in data.items():
        song_data['song_id'] = song_id
        song_data['play_counts'] = max(song_data['count'].values())
    return sorted(data.values(), key=lambda x: x['play_counts'], reverse=True)[0:limit]

def calculate_days_since_added(data):
    today = datetime.date.today()
    for song_id, song_data in data.items():
        date_added = parse_date(song_data['date_added'])
        days_since_added = (today - date_added).days
        data[song_id]['days_since_added'] = days_since_added
    return data

def calculate_increase(data, days):
    today = datetime.date.today()
    days_ago = today - datetime.timedelta(days=days)
    for song_id, song_data in data.items():
        count_today = song_data['count'].get(date_to_str(today), 0) # get count for today, default to 0 (since script just ran we always have a value)
        # get next existing date in song_data['count'] that is newer than days_ago
        if days_ago in song_data['count']:
            count_days_ago = song_data['count'][str(days_ago)]
        else:
            # todo remove
            data[song_id]['increase'] = count_today
            continue
            # no count data for exaclt 30 days ago: find closest date that is newer than days_ago
            closest_date = min([parse_date(date) for date in song_data['count'] if parse_date(date) > days_ago], key=lambda x: abs(x - days_ago))
            count_days_ago = song_data['count'][date_to_str(closest_date)] # todo double check this
            if count_days_ago == 0:
                print('Warning: No count data found for ' + date_to_str(days_ago) + ' for song ' + song_data['song_name'])

        # increase = count_today - count_days_ago
        # data[song_id]['increase'] = increase
    return data

def calculate_hottest_tracks(tracks):
    """Ratio of increase to days since added"""
    hottest_tracks = []
    for song_id, song_data in tracks.items():
        increase = song_data.get('increase', 0)
        days_since_added = song_data.get('days_since_added', 0)
        if days_since_added == 0:
            print('Warning: days_since_added is 0 for song ' + song_data['song_name'])
            continue
        song_data['days_since_added'] = days_since_added
        song_data['play_counts'] = max(song_data['count'].values())
        song_data['increase'] = increase
        song_data['hottest'] = increase / days_since_added
        song_data['song_id'] = song_id
        hottest_tracks.append(song_data)

    return sorted(hottest_tracks, key=lambda x: x['hottest'], reverse=True)

if __name__ == '__main__':
    start_time = datetime.datetime.now()
    if not os.path.exists('out'):
        print('Creating out directory...')
        os.makedirs('out')

    print("Importing from DB...")
    count_data = get_count_data(DB_FILE)
    meta_data = get_meta_data(DB_FILE)
    print("Building data...")
    data = build_data(count_data, meta_data)
    print("Calculating days since added...")
    tracks = calculate_days_since_added(data)
    print("Calculating increase... " + str(INCREASE_DAYS) + " days")
    tracks = calculate_increase(tracks, INCREASE_DAYS)
    if CALCULATE_TOP_PLAYED:
        print("Calculating top played tracks...")
        top_tracks = get_top_played_tracks(tracks, 10)
        print("Saving plots...")
        create_lines_plot_for_tracks(top_tracks, 'out/top_tracks.png')
        create_table_plot_for_tracks(top_tracks, ['song_name', 'artist_name', 'play_counts'], 'out/top_tracks_table.png')
        if EXTENSIVE_SAVE:
            save_json(tracks, 'out/tracks.json')
            top_100_tracks = get_top_played_tracks(tracks, 100)
            top_tracks_df = tracks_list_to_df(top_100_tracks)
            top_tracks_df.to_csv('out/top_tracks.csv', index=False)
    if CALCULATE_HOTTEST:
        print("Calculating hottest tracks...")
        hottest_tracks = calculate_hottest_tracks(tracks)
        print("Saving plots...")
        create_table_plot_for_tracks(hottest_tracks[0:10], ['song_name', 'artist_name', 'days_since_added', 'plays_count', 'increase', 'hottest'], 'out/hottest_tracks.png')
        if EXTENSIVE_SAVE:
            save_json(hottest_tracks, 'out/hottest_tracks.json')

    print("Done in " + str(datetime.datetime.now() - start_time) + " s.")
