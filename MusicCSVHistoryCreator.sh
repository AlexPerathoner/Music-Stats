#!/bin/zsh 

#cd /Users/alex/AppsMine/PythonTest\ Music 
#rm "/Users/alex/AppsMine/PythonTest Music/output.txt"

/usr/bin/automator "/Users/alex/AppsMine/PythonTest Music/exportLibrary.workflow"
python3 "/Users/alex/AppsMine/PythonTest Music/new_version/write_data.py"
#python3 "/Users/alex/AppsMine/PythonTest Music/plotcreator.py" 200 20 1