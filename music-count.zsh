#!/bin/zsh 

cd /Users/alex/AppsMine/music-stats/

source env/bin/activate;
python3.12.8 music_stats_main_background_script.py # 3.12.8 is the version of python in the env


# python3.12.8 music_stats_checks.py # should be done in another script, running weekly


# already handled in main python script

# status_python_script=$?
# if [[ $status_python_script -ne 0 ]]; then
#     osascript -e 'display notification "Music Stats: ERROR inserting data!"';
#     osascript -e 'beep 3';
#     exit $status_python_script;
# else
#     osascript -e 'display notification "Music Stats: Data inserted"';
# fi