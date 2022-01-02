

import os
from datetime import datetime
import sys
sys.path.append('/usr/local/lib/python3.7/site-packages/')
import pandas as pd
print("Success")
#getting current tracks' played count
text_file = open("output.txt", encoding='utf-16')
answer = text_file.read()
text_file.close()
today = datetime.today().strftime('%Y%m%d')



#dividing string in values
lists = answer.split("\n\n")[:-1]
i=0
for item in lists:
	lists[i] = item.split("\n")
	i+=1

firstDF = pd.DataFrame(lists).transpose().sort_values(by=[2, 0], ascending=True) #setting up like iTunes Library.xml - tracks added on the same day are order alphabetically

namesList = firstDF[0]
tracksCount = len(namesList)


# getting already created csv
data = {'name':[]}
df = pd.DataFrame(data)
if os.path.isfile('/Users/alex/AppsMine/PythonTest Music/out.csv'):
	df = pd.read_csv('/Users/alex/AppsMine/PythonTest Music/out.csv')

def getNewSongs(oldCount, newCount):
	theList = []
	for name in namesList:
		theList.append(name)
	print("Adding songs... ", (oldCount-newCount),newCount)
	return theList[(oldCount-newCount):newCount]


#checking if songs were added
savedLength = len(df.index)

#filling holes for new added tracks
if(savedLength < tracksCount):
	#df['name'] = getSongs()
	print("Found new songs!")
	#creating new rows for every new song that appeared
	for item in getNewSongs(savedLength, tracksCount):
		print("Adding " + item)
		s1 = pd.Series(item, index=df.columns[:1]) #name
		#-1 is value to ignore
		s2 = pd.Series(-1, index=df.columns[1:])
		df = df.append(pd.concat([s1, s2]), ignore_index=True)



df[today] = firstDF[1].tolist()




df.to_csv('/Users/alex/AppsMine/PythonTest Music/out.csv', index=False)







