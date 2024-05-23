#!/bin/zsh 

cd /Users/alex/AppsMine/PythonTest\ Music

/usr/bin/automator "/Users/alex/AppsMine/PythonTest Music/exportCounts.workflow"
/usr/bin/automator "/Users/alex/AppsMine/PythonTest Music/exportMeta.workflow"
cd new_version
virtualenv env && source env/bin/activate;
#pip install pandas

# python3.7 write_data_to_db.py || osascript -e 'display notification "Could not run Music script!"'; # exit with output code of 
python3.12 write_data_to_db.py
status_python_script=$?
if [[ $status_python_script -ne 0 ]]; then
    osascript -e 'display notification "Could not run Music script!"';
    osascript -e 'beep 3';
    exit $status_python_script;
else
    osascript -e 'display notification "Music script ran successfully!"';
    osascript -e 'beep 3';
fi

#python3 "/Users/alex/AppsMine/PythonTest Music/plotcreator.py" 200 20 1
rm output_as_meta.txt
rm output_as_count.txt