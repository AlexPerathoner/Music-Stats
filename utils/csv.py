# execute applescript to get path of each song and play count. add to db.

import os
import datetime
import subprocess
import pandas as pd
import logging
from utils.hash import get_hash
from utils.errors import AutomatorError, HashNotGeneratedError
from utils.db import get_paths_and_hashes_in_db


DB_FILE = "music-play-count-db.sqlite3"


def get_all_songs_from_apple_music(logger, output_path):

    if os.path.exists(output_path):
        logger.debug("Removing old tmp output file...")
        os.remove(output_path)

    logger.info("Running automator...")
    date_start = datetime.datetime.now()
    p = subprocess.Popen(
        ["automator", "/Users/alex/AppsMine/music-stats/exportMeta.workflow"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    p.wait()
    date_end = datetime.datetime.now()
    logger.info("Finished running automator in " + str(date_end - date_start) + " s.")
    if p.returncode != 0:
        logger.error(p.stderr.read().decode())
        raise AutomatorError("Automator returned with error code %d" % p.returncode)

    if not os.path.exists(output_path):
        raise AutomatorError("Output path does not exist. Automator failed?")

    logger.info("Converting to dataframe...")
    with open(output_path, "r", encoding="utf-16") as f:
        # read txt file
        lines = f.readlines()
        tracks = [line.strip() for line in lines]
        if len(tracks) == 0:
            raise Exception("No tracks found")
        tracks = [track.split(";") for track in tracks]
        df = pd.DataFrame(
            tracks,
            columns=[
                "song_id",
                "song_name",
                "artist_name",
                "album_name",
                "date_added",
                "track_path",
                "play_count",
                "duration",
                "cloud_status",
                "is_favorited",
                "",
            ],
        )
        df = df[df["song_id"] != "\n"]
        df = df.drop(
            df.columns[-1], axis=1
        )  # removing last empty column (artifact of having ; at the end of the line)
        # convert is_favorited to 0, 1
        df["is_favorited"] = df["is_favorited"].replace({"false": 0, "true": 1})

    return df


def export_hashes_and_counts_to_csv(logger, paths_set, output_csv_path):
    # todo refactor this
    """
    Converts applescript result to csv and calculates for each song the hashes
    """
    output_path = r"/Users/alex/AppsMine/music-stats/temp/play_count_export.txt"
    logger.info(f"Converting applescript result {output_path} to csv {output_csv_path}")

    df = get_all_songs_from_apple_music(logger, output_path)
    logger.info("Retrieved %d songs" % len(df))
    should_recalculate_hashes = False
    if paths_set is not None:
        new_paths_set = set()
        for path in df["track_path"]:
            new_paths_set.add(path)
        if new_paths_set == paths_set:
            logger.info(
                "All paths are already in db and nothing has changed. Skipping hashes generation. Importing from db instead."
            )
            paths_and_hashes_map = get_paths_and_hashes_in_db(logger, DB_FILE)
            df["hash"] = df["track_path"].map(paths_and_hashes_map)
            logger.info("Finished mapping hashes.")

        else:
            logger.info("Some paths changed. Recalculating hashes.")
            should_recalculate_hashes = True
    else:
        logger.info("No paths set. Recalculating hashes.")
        should_recalculate_hashes = True

    if should_recalculate_hashes:
        tot = len(df)
        logger.info(f"Calculating hash for {tot} songs...")
        start_time = datetime.datetime.now()
        # df['hash'] = df.apply(lambda row: get_hash(row['track_path']), axis=1) # do this in a loop
        i = 0
        for row in df.iterrows():
            track_path = row[1]["track_path"]
            track_hash = get_hash(logger, track_path)
            df.loc[row[0], "hash"] = track_hash
            i += 1
            if i % 50 == 0:
                logger.info(f"Processed {i} songs.")

        logger.info(
            "Finished calculating hash in "
            + str(datetime.datetime.now() - start_time)
            + " s."
        )
    # hash is None
    df_filtered_no_hash = df[df["hash"].isna()]
    logger.info("Found %d songs with no hash" % len(df_filtered_no_hash))
    if len(df_filtered_no_hash) > 0:
        logger.error("Found %d songs with no hash" % len(df_filtered_no_hash))
        raise HashNotGeneratedError(
            "Found %d songs with no hash" % len(df_filtered_no_hash)
        )

    logger.info("Exporting to csv...")

    df.to_csv(output_csv_path, index=False)


def main():
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    LOG_DATEFMT = "%Y-%m-%d %H:%M:%S"
    LOG_FORMAT = (
        "\n[%(levelname)s/%(name)s:%(lineno)d] %(asctime)s "
        + "(%(processName)s/%(threadName)s)\n> %(message)s"
    )
    FORMATTER = logging.Formatter(LOG_FORMAT, datefmt=LOG_DATEFMT)
    logging.getLogger("matplotlib.font_manager").disabled = True
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)  # or any other level
    ch.setFormatter(FORMATTER)
    logger.addHandler(ch)
    fh = logging.FileHandler(
        "logs/main-script-"
        + datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
        + ".log"
    )
    fh.setLevel(logging.DEBUG)  # or any level you want
    fh.setFormatter(FORMATTER)
    logger.addHandler(fh)
    todays_date = datetime.date.today().strftime("%Y-%m-%d")
    path_name = "count-data-while-fixing/play-count-export" + todays_date + ".csv"
    export_hashes_and_counts_to_csv(logger, None, path_name)


if __name__ == "__main__":
    main()
