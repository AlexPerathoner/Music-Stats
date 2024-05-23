import json
import pandas as pd
import datetime

def parse_date(date_str):
    return datetime.datetime.strptime(date_str, '%Y-%m-%d').date()

def date_to_str(date):
    return date.strftime('%Y-%m-%d')

def save_json(data, filename):
    with open(filename, 'w') as f:
        f.write(json.dumps(data, indent=4))

def tracks_list_to_df(tracks):
    """Must have 'song_id', 'song_name', 'artist_name' in each track dict. Optionally 'play_counts' or 'hottest'""" # todo refactor: maybe could be refactored to not be needed anymore
    tracks_adj = []
    for song_data in tracks:
        track_dict = {
                'song_id': song_data['song_id'],
                'song_name': song_data['song_name'],
                'artist_name': song_data['artist_name']
            }
        optional_columns = ['days_since_added', 'play_counts', 'increase', 'hottest']
        for col in optional_columns:
            if col in song_data:
                track_dict[col] = song_data[col]
        tracks_adj.append(track_dict)
    df = pd.DataFrame(tracks_adj)
    # convert every date in count to a column
    for song_data in tracks:
        for date, count in song_data['count'].items():
            if date not in df:
                df[date] = 0
            df.loc[df['song_id'] == song_data['song_id'], date] = count
    return df