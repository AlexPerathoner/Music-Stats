import pandas as pd
import numpy as np
import calmap
import matplotlib.pyplot as plt
import datetime


def dates_to_calmap_events(df):
    """
    Convert a list of dates into a Series suitable for calmap

    Args:
        dates: List of datetime objects or date strings

    Returns:
        pandas.Series: Index contains dates, values contain counts of events per day
    """
    # Convert to pandas datetime if they aren't already
    df["date_count"] = pd.to_datetime(df["date_count"])

    # Count events per day
    # events = pd.Series(1, index=dates).resample("D").count()
    # sum duration per day
    events = df.groupby("date_count")["duration"].sum()

    return events


def create_heatmap(cur, start_date, end_date):
    # reset plot
    plt.clf()
    rows = cur.execute(
        f"""
        select date_count, duration
        from play_counts p JOIN tracks ON p.hash = tracks.hash
        where date_count >= '{start_date}' and date_count <= '{end_date}'
        order by date_count
        """
    ).fetchall()
    df = pd.DataFrame(
        rows,
        columns=["date_count", "duration"],
    )

    events = dates_to_calmap_events(df)
    # filter out events  that are less than 1 day
    # > 1 day should not be possible, probably happens just because of sync with iPhone
    # events = events[events < 60 * 60 * 24]

    calmap.yearplot(events)

    # add title
    plt.title("Play Counts Heatmap")
    plt.savefig(f"out/heatmap_{start_date}_{end_date}.png")
