import subprocess


def display_notification(title, message, beep_count=1):
    subprocess.run(
        [
            "osascript",
            "-e",
            f'display notification "{message}" with title "{title}"',
        ]
    )
    if beep_count > 0:
        subprocess.run(["osascript", "-e", f"beep {beep_count}"])
        subprocess.run(["afplay", "/System/Library/Sounds/Sosumi.aiff"])


def display_finish_notification(different_songs_updates_counter, plays_updates_counter):
    if different_songs_updates_counter > 0:
        display_notification(
            "Music Stats: Data inserted!",
            f"Data inserted: {different_songs_updates_counter} rows inserted (songs updated). {plays_updates_counter} plays added.",
            0,
        )
    else:
        display_notification("Music Stats", "Nothing changed.", 0)
    subprocess.run(["afplay", "/System/Library/Sounds/Glass.aiff"])


def display_warning_notification():
    display_notification(
        "Music Stats finished with warnings while inserting data!",
        "Music Stats: warning inserting data!",
        3,
    )


def display_error_notification():
    display_notification(
        "Music Stats: ERROR inserting data!", "Music Stats: ERROR inserting data!", 5
    )
