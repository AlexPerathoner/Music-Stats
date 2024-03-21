#!/bin/zsh 

cd /Users/alex/AppsMine/PythonTest\ Music
#rm "/Users/alex/AppsMine/PythonTest Music/output.txt"


nFiles4k=$( find /Users/alex/4kDownloads/*.mp3 | wc -l )
nFilesAutoScript=$( find /Users/alex/AppsMine/youtube-download-soon/mp3_files/*.mp3 | wc -l )

#only execute if 4kdownloads folder is empty
if (( $nFiles4k > 0)); then
    osascript -e 'display notification "Empty 4kDownloads folder to run the script"';
    osascript -e 'beep 3';
else
    if (( $nFilesAutoScript > 0)); then
        osascript -e 'display notification "Empty 4kDownloads folder to run the script"';
        osascript -e 'beep 3';
    else
        /usr/bin/automator "/Users/alex/AppsMine/PythonTest Music/exportCounts.workflow"
        /usr/bin/automator "/Users/alex/AppsMine/PythonTest Music/exportMeta.workflow"
        cd new_version
        virtualenv env && source env/bin/activate;
        python3 write_data_to_db.py || osascript -e 'display notification "Could not run Music script!"';
        #python3 "/Users/alex/AppsMine/PythonTest Music/plotcreator.py" 200 20 1
        rm output_as_meta.txt
        rm output_as_count.txt
    fi
fi