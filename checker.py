import pandas as pd

#reading
df = pd.read_csv('Book1.csv', ";")


df2 = pd.DataFrame()
for index, row in df.iterrows():
	l = row.tolist()[3:]
	if (l != sorted(l)):
		print(row['song'])
		print(l, sorted(l))
		df2 = df2.append(row)

if(len(df2) > 0):
	print(df2['song'])
else:
	print("Everything OK")