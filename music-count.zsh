#!/bin/zsh 

cd /Users/alex/AppsMine/music-stats/

/usr/bin/automator "/Users/alex/AppsMine/music-stats/exportCounts.workflow"

source env/bin/activate;
python3.12 write_data_to_db.py
status_python_script=$?
if [[ $status_python_script -ne 0 ]]; then
    osascript -e 'display notification "Could not run Music script!"';
    osascript -e 'beep 3';
    exit $status_python_script;
else
    osascript -e 'display notification "Music script ran successfully!"';
fi


# TODO: RUN CHECKS!!