
import sys
sys.path.append("/usr/local/lib/python3.9/site-packages/")

import numpy as np
import matplotlib
matplotlib.use('Qt5Agg')
from pathlib import Path
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.cbook as cbook
from matplotlib import cm
import pandas as pd
import sys
from datetime import datetime
import PyQt5
import os
import matplotlib.ticker as plticker


def func(x):
	if x.first_valid_index() is None:
		return None
	else:
		return x[x.first_valid_index()]

def daysSinceAlive(x):
	if x.first_valid_index() is None:
		return None
	else:
		day = df.columns.tolist().index(x.first_valid_index())
		return len(REALTOTALDAYS) - day

def update_annot(ind):
	pos = sc.get_offsets()[ind["ind"][0]]
	annot.xy = pos
	text = "{}, {}".format(" ".join(list(map(str,ind["ind"]))), " ".join([names[n] for n in ind["ind"]]))
	annot.set_text(text)
	annot.get_bbox_patch().set_alpha(0.4)


def hover(event):
	vis = annot.get_visible()
	if event.inaxes == ax:
		cont, ind = sc.contains(event)
		if cont:
			update_annot(ind)
			annot.set_visible(True)
			fig.canvas.draw_idle()
		else:
			if vis:
				annot.set_visible(False)
				fig.canvas.draw_idle()

def getIncrease(x):
	if(df.transpose().index.tolist().index(x.first_valid_index()) > 1):
		return x[-1]
	else:
		return x[-1]-x[0]

today = datetime.today().strftime('%Y%m%d')
#arr = ["20201023","20201022","20201021"]
#for today in arr:
print("NOW DOING!!!! " + today)

years = mdates.YearLocator()# every year
months = mdates.MonthLocator()  # every month
years_fmt = mdates.DateFormatter('%Y')

#reading
df = pd.read_csv('out.csv')
df = df.replace(-1, np.nan)
#ordering
#firstRow = str(df.transpose().index.values[1])
lastRow = str(df.columns[-1]) #getting last day
####################
lastRow = today #for video it should be today
df = df.iloc[:, 0:df.transpose().index.tolist().index(lastRow)+1] #deleting columsn after last day
totalDays = len(df.transpose())
REALTOTALDAYS = df.columns.tolist()[1:]
ORDF = df
df2 = df.iloc[:, -30:] #getting last 30 days before last day
if(len(df.columns) > 30):
	df2.insert(0, 'name', df['name']) #getting names column

df = df2[pd.notnull(df2[lastRow])] #setting back to normal df, also deleting rows without any streams
####################

shouldShowCharts = len(sys.argv) != 4
Path("charts/topSongs").mkdir(parents=True, exist_ok=True)
Path("charts/chart").mkdir(parents=True, exist_ok=True)
############################################################################################################################################

n1 = int(sys.argv[1])
#df = df[-n1:] #getting last n added songs

firstValid = df.transpose()[1:].apply(func, axis=0)

increase = df[lastRow] - firstValid
mask = (increase > 5) | df[df.columns[1]].isnull()
df = df[mask]
increase = df.transpose()[1:].apply(getIncrease, axis=0) #calculating right increase (starting from 0 instead of first available value)
#percInc = increase / df[lastRow] * 100
#daysAlive = df.transpose()[1:].apply(daysSinceAlive, axis=0)
#df['percInc'] = percInc

temp = df
ORDF.transpose().filter(df.index).transpose()
df = ORDF
daysAlive = df.transpose()[1:].apply(daysSinceAlive, axis=0)
df = temp


df['worth'] = increase / daysAlive
df['daysAlive'] = daysAlive
df['increase'] = increase

df = df.sort_values(by=['worth'], ascending=False) #sorting by most liked
#print(df)
df = df[:30]

y = np.array(df[lastRow].tolist())
x = np.array(df['daysAlive'].tolist())
n = np.array(df['name'].tolist())

c = np.array(df['worth'].tolist())
fig,ax = plt.subplots(figsize=(45,25))

mask = (df['worth'] > df['worth'].max()/3) | (df[lastRow] > df[lastRow].max()/4*3) | (df[lastRow] > 70)
n[~mask] = ""



sc = plt.scatter(x,y,c=c, s=100, cmap=cm.viridis, vmin=0., vmax=6.)
cbar = plt.colorbar()
cbar.set_label("Worth (increase/daysAlive)")
#annot = ax.annotate("", xy=(0,0), xytext=(20,20),textcoords="offset points",bbox=dict(boxstyle="round", fc="w"),arrowprops=dict(arrowstyle="->"))
#annot.set_visible(False)

df = df.transpose()[:-2].transpose() #deleting support row
#df = df[:int(sys.argv[2])] #getting top liked 
#fig.canvas.mpl_connect("motion_notify_event", hover)
axes = plt.gca()
axes.set_ylim([0,250])
axes.set_xlim([0,365])
plt.title("Top songs")
plt.ylabel("Stream count")
plt.xlabel("Days since addded")
plt.gca().invert_xaxis()


plt.gca().legend(df['name'], loc=2)
for i, txt in enumerate(n):
	annot2 = ax.annotate(txt, (x[i], y[i]), textcoords="offset points", bbox=dict(boxstyle="round", fc="w"), xytext=(0,10))
	annot2.get_bbox_patch().set_alpha(0.4)

if(shouldShowCharts):
	plt.show()
else:
	path = "charts/topSongs/"+lastRow+"1_top.png"
	plt.savefig(path, dpi=200)
	
########################################################################################################################################################################################################################################################################################
fig,ax = plt.subplots(figsize=(20,12))
lines = []
	
df = df.sort_values(by=[lastRow], ascending=False)
#df = df.sort_values(by=[lastRow], ascending=False) #sorting by most heard
print(df)
minWorth = df['worth'].min()
maxWorth = df['worth'].max()
x = np.array(df.columns[1:].tolist()[:-1])
for index, row in df.iterrows():
	y = np.array(row.tolist()[1:-1])
	c = row.tolist()[-1]
	name = row['name']
	line, = plt.plot(x,y[-len(x):], marker="", label=name, c=cm.viridis(1/c))
	line.set_pickradius(5)
	#print(type(line))
	lines.append(line)


df = df.transpose()[:-1].transpose() #deleting support row
#names = np.array(df['name'].tolist())


top = df#[:20] #getting top 10
#print(top)
#-----------> get topNames ----- converting to list
topNames = top[top.columns[:1]]["name"].tolist()
#print(top)

#creating legend list -> names that are not in the top are labeled with "_hidden"
legendNames = pd.Series([], dtype=pd.StringDtype())

#getting all names
names = df[df.columns[0]]
for i in names:
	if i in topNames:
		legendNames = legendNames.append(pd.Series([i]))
	else:
		break

loc = plticker.MultipleLocator(base=5) # this locator puts ticks at regular intervals
ax.xaxis.set_major_locator(loc)

#color map for second graph
cmap = plt.get_cmap('viridis_r',len(x))
norm = matplotlib.colors.Normalize(vmin=minWorth,vmax=maxWorth)
sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
sm.set_array([])
cbar = plt.colorbar(sm)
cbar.set_label("Worth (increase/daysAlive)")

axes = plt.gca()
axes.set_ylim([0,250])
plt.title("Top songs")
plt.ylabel("Stream count")
plt.xlabel("Date")
plt.gca().legend(legendNames, loc=2)

if(shouldShowCharts):
	plt.show()
else:
	path = "charts/chart/"+lastRow+"1_chart.png"
	plt.savefig(path, dpi=300)


