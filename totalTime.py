import os
from itunesLibrary import library
from datetime import datetime
import pandas as pd

path = os.path.join(os.getenv("HOME"),"Libreria.xml")


lib = library.parse(path)



#print (len(lib))

x = 0

for item in lib:
	#print(item.itunesAttibutes["Play Count"])
	x+=1
	if x > 20:
		break

total = 0

tdict = {}

def convertToHours(seconds):
	return round(seconds/3600, 1)

def roundToMinutes(seconds):
	return round(seconds)


for item in lib:
	res = item.getItunesAttribute('Play Count')
	time = int(item.getItunesAttribute("Total Time"))
	artist = item.artist
	if res != None:
		if(artist in tdict):
			tdict[artist] += (time/1000) * int(res)
		else:
			tdict[artist] = (time/1000) * int(res)


	if res != None:

		time = time/1000
		total += time * int(res)
'''


for item in lib.getPlaylist("Anime"):
	res = item.getItunesAttribute('Play Count')
	time = int(item.getItunesAttribute("Total Time"))
	if res != None:

		time = time/1000
		total += time * int(res)

'''


data = {'name':[]}
df = pd.DataFrame(data)
if os.path.isfile('/Users/alex/AppsMine/PythonTest Music/topArtists.csv'):
	df = pd.read_csv('/Users/alex/AppsMine/PythonTest Music/topArtists.csv')


dfN = pd.DataFrame.from_dict(tdict, orient='index')
namesList = dfN.index.tolist()


def getNewSongs(oldCount, newCount):
	theList = []
	for name in namesList:
		theList.append(name)
	print("Adding songs... ", (oldCount-newCount),newCount)
	return theList[(oldCount-newCount):newCount]


#printing top artists
topArtists = dfN.sort_values(by=0, ascending=False)[:50]
topArtists[0] = topArtists[0].apply(convertToHours)
print("Hai ascoltato musica per ", total, " seconds")
print("Artisti più ascoltati: \n",topArtists)

#adding updated data do csv

dfN[0] = dfN[0].apply(roundToMinutes)
#checking if songs were added
savedLength = len(df.index)
artistsCount = len(dfN[0])

#filling holes for new added tracks
if(savedLength < artistsCount):
	#df['name'] = getSongs()
	print("Found new songs!")
	#creating new rows for every new song that appeared
	for item in getNewSongs(savedLength, artistsCount):
		print("Adding " + str(item))
		s1 = pd.Series(item, index=df.columns[:1]) #name
		#-1 is value to ignore
		s2 = pd.Series(-1, index=df.columns[1:])
		df = df.append(pd.concat([s1, s2]), ignore_index=True)



today = datetime.today().strftime('%Y%m%d')

df[today] = (dfN[0]).tolist()



df.to_csv('/Users/alex/AppsMine/PythonTest Music/topArtists.csv', index=False)

