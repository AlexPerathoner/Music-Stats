import subprocess
import os
import pydub
import hashlib
import librosa


def get_hash(logger, file_path, level=0):
    def recode_file(file_path):
        logger.debug("Recoding file...", file_path)
        p = subprocess.Popen(
            ["ffmpeg", "-i", file_path, "-acodec", "copy", f"{file_path}.tmp.mp3"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        p.wait()
        os.remove(file_path)
        os.rename(f"{file_path}.tmp.mp3", file_path)

    def load_audio(filepath):
        try:
            y, sr = librosa.load(filepath, mono=False, sr=22050, out=logger.debug)
            if (y.shape[0] == 2 and len(y[0]) == 0) or (y.shape[0] > 2 and len(y) == 0):
                logger.debug(f"Loading {filepath} with explicit duration")
                dur = int(pydub.utils.mediainfo(filepath)["duration"].split(".")[0])
                y, sr = librosa.load(filepath, mono=False, sr=22050, duration=dur)
            return y
        except Exception as e:
            logger.error(f"Error loading audio file {filepath}: {e}")
            return None

    # Load audio files
    logger.debug("Loading audio file... " + file_path)
    audio = load_audio(file_path)
    if level < 3:
        if audio is not None:
            bytes_data = audio.tobytes()
            # check if empty
            if len(bytes_data) == 0:
                logger.warning("Audio is empty. Trying to recode file.")
                recode_file(file_path)
                return get_hash(logger, file_path, level=level + 1)
        else:
            logger.warning("Audio is None. Trying to recode file.")
            recode_file(file_path)
            return get_hash(logger, file_path, level=level + 1)
    else:
        logger.error("FATAL ERROR. Recoding file did not help.")
        return None
    hash = hashlib.sha256(bytes_data).hexdigest()
    logger.debug(f"Calculated hash for {file_path}: {hash}")
    return hash


if __name__ == "__main__":
    import logging
    import datetime

    logging.getLogger("numba.core.byteflow").disabled = True
    logging.getLogger("numba.core.interpreter").disabled = True
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    LOG_DATEFMT = "%Y-%m-%d %H:%M:%S"
    LOG_FORMAT = (
        "\n[%(levelname)s/%(name)s:%(lineno)d] %(asctime)s "
        + "(%(processName)s/%(threadName)s)\n> %(message)s"
    )
    FORMATTER = logging.Formatter(LOG_FORMAT, datefmt=LOG_DATEFMT)
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    ch.setFormatter(FORMATTER)
    logger.addHandler(ch)
    fh = logging.FileHandler(
        "testlog-" + datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S") + ".log"
    )
    fh.setLevel(logging.DEBUG)  # FILE level
    fh.setFormatter(FORMATTER)
    logger.addHandler(fh)
    print(
        get_hash(
            logger,
            "/Users/alex/Music/Musica/Music/The Score/Pressure/Born For This.m4a",
        )
    )
