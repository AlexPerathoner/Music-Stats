import pandas as pd
import datetime


def parse_date(date_str):
    return datetime.datetime.strptime(date_str, "%Y-%m-%d").date()


def date_to_str(date):
    return date.strftime("%Y-%m-%d")


def get_date_added(logger, hash_track, cur):
    sql_str = f"""
        select date_added
        from tracks
        where hash = '{hash_track}'
    """
    logger.debug(sql_str)
    cur.execute(sql_str)
    result = cur.fetchall()
    df = pd.DataFrame(
        result,
        columns=["date_added"],
    )
    if len(df) == 0:
        return "missing value"
    return parse_date(df["date_added"].values[0])
