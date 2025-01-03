
from numpy.core.defchararray import encode


with open('outputAppleScriptCopia.csv', encoding='UTF-16') as namesFile:
    last = pd.read_csv(namesFile, sep=";")


with open('someData.csv', encoding='UTF-16') as namesFile:
    last = pd.read_csv(namesFile, sep=";")


with open('filledDataWoutEmptyRows.csv', encoding='UTF-16') as namesFile:
    added = pd.read_csv(namesFile, sep="\t")

with open('nomiCanzoni.csv', encoding='UTF-16') as namesFile:
    names = pd.read_csv(namesFile, sep="\t")


with open('FinalCorrectedCSV.txt', encoding='UTF-16') as namesFile:
    final = pd.read_csv(namesFile, sep="\t")

final[final[cols].duplicated()]


original = pd.read_csv("out2.csv", sep=",")

df = df.replace(np.nan, "")


other = pd.concat([actual, result], axis=1, join="inner")

other = pd.merge(result, last, on=["song", "artist","album"])


other.to_csv('joinedTest3.csv', index=False, encoding="UTF-16", sep="\t")

year = other[other[cols[0]] == -1]
year.to_csv('joinedtest.csv', index=False, encoding="UTF-16", sep="\t")

#move column
other = other[[c for c in other if c not in ['count']]  + ['count']]

merged = merged[['song','artist','album'] + [c for c in merged if c not in ['song','artist','album']]]

other[other["song"] == "Hooked"]
result[result["song"] == "Hooked"]
last[last["song"] == "Hooked"]



other = pd.merge(last, toAdd2, on=["song", "artist","album"], how="right")

#remove nan and to int
other[cols] = other[cols].replace(np.nan, -1)
other[cols] = other[cols].astype("int")


original[cols] = original[cols].replace(np.nan, -1)
original[cols] = original[cols].astype("int")

other[other[cols[0]] == -1]
result[result[cols[0]] == -1]



pd.merge(result, name, on=["song", "artist","album"], how="outer")

added[["song", "artist","album"]][~added[["song", "artist","album"]].isin(name)]


#find differences
pd.concat([added,result]).drop_duplicates(keep=False)




alreadyAdded = pd.concat([added[["song", "artist","album"]],name]).drop_duplicates(keep=False)

toAdd = pd.concat([added[["song", "artist","album"]],name]).drop_duplicates(keep=False)