#!/bin/zsh 

cd /Users/alex/AppsMine/music-stats/

/usr/bin/automator "/Users/alex/AppsMine/music-stats/exportCounts.workflow"

source env/bin/activate;
python3.12 music_stats_main_background_script.py


python3.12 music_stats_checks.py
status_python_script=$?
if [[ $status_python_script -ne 0 ]]; then
    osascript -e 'display notification "Music Stats: ERROR inserting data!"';
    osascript -e 'beep 3';
    exit $status_python_script;
else
    osascript -e 'display notification "Music Stats: Data inserted"';
fi