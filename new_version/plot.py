import matplotlib.pyplot as plt
from utils import tracks_list_to_df
import numpy as np

def create_lines_plot_for_tracks(tracks, filename):
    df = tracks_list_to_df(tracks)
    _,axis = plt.subplots()
    for song_data in tracks:
        axis.plot(df.columns[4:],
                  df.loc[df['song_id'] == song_data['song_id']].values[0][4:],
                  label=song_data['song_name']+ ', ' + song_data['artist_name'])
    plt.legend()
    # y axis could start at 0
    # axis.set_ylim(bottom=0)
    plt.savefig(filename)

def create_table_plot_for_tracks(tracks, columns, filename):
    df = tracks_list_to_df(tracks)
    df = df.drop(columns=[col for col in df.columns if col not in columns])
    df.drop('hottest', axis=1, inplace=True)
    df.drop('song_name', axis=1, inplace=True)
    df.drop('artist_name', axis=1, inplace=True)
    
    # fig, ax = plt.subplots()
    # ax.axis('off')
    # ax.table(cellText=df.values, colLabels=df.columns, cellLoc = 'center', loc='center')
    # fig.tight_layout()
    # plt.savefig(filename, dpi=900)
    print(df.values)
    vals = np.round(df.values,2)
    print(vals)
    norm = plt.Normalize(vals.min()-1, vals.max()+1)
    colours = plt.cm.hot(norm(vals))

    fig,ax = plt.subplots()

    the_table=plt.table(cellText=vals, rowLabels=df.index, colLabels=df.columns, 
                        colWidths = [0.03]*vals.shape[1], loc='center', 
                        cellColours=colours)
    plt.savefig(filename, dpi=900)