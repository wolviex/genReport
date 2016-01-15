import sqlite3
import jwtools
import jwjson
import DLogReader as LogReader
import re
import numpy as np
from collections import Counter

def getSpecificPrice(name):
	db = sqlite3.connect(LogReader.getConfigValue("PriceDB"))
	cur = db.cursor()
	query = "SELECT * FROM prices"

	cur.execute(query)
	db.commit()
	rows = cur.fetchall()
	names = [desc[0] for desc in cur.description]
	nameIndex = names.index("name")
	score = [0,""]
	for row in rows:
		d = jwtools.stringScore(name,row[nameIndex])
		if d > score[0]:
			score[0] = d
			score[1] = row[nameIndex]

	print "Best match for {} : {} with {}".format(name,score[1],score[0])

def isfloat(value):
  try:
    float(value)
    return True
  except ValueError:
    return False

def getPrice(fname):
	components = getComponentList(fname)
	componentCounter = dict(Counter(components))
	price = 0
	db = sqlite3.connect(LogReader.getConfigValue("PriceDB"))
	cur = db.cursor()
	query = "SELECT * FROM prices"

	cur.execute(query)
	db.commit()
	rows = cur.fetchall()
	names = [desc[0] for desc in cur.description]
	nameIndex = names.index("name")
	priceIndex = names.index("price")
	for i in range(len(rows)):
		rName = rows[i][nameIndex]
		if isfloat(rName):
			rName = str(int(float(rows[i][nameIndex])))
		for component in components:
			if tryMatch(component,rName.lower()):
				componentCounter[component] -= 1
				price += float(rows[i][priceIndex])

	for k,v in componentCounter.items():
		if v > 0:
			print "Price for {} not found.".format(k)

	return price

def tryMatch(component, string):

	if component == string:
		return True

	for i in range(len(component)):
		x = len(component)-1 - i #Start from the end of the string and replace spaces with dashes, testing match each replace
		if component[x] == " ":
			s = "{}{}{}".format(component[:x],"-",component[x+1:])
			if s == string:
				return True

	spl = re.split(" |-",component)

	for i in range(len(spl)):
		mstring = " ".join(spl[:len(spl)-1-i])
		if mstring == string:
			return True

	
	for i in range(len(spl)):
		mstring = ""
		if i == 0:
			mstring = " ".join(spl[1:])
		elif i == len(spl)-1:
			mstring = " ".join(spl[:-1])
		else:
			s = spl[:i] + spl[i+1:]
			mstring = " ".join(s)
			
		if mstring == string:
			return True
		elif mstring.replace(" ","-") == string:
			return True

	return False

def getComponentList(fname):
	components = []
	model = LogReader.getModel(fname).split(" ")[-1]
	cpus = LogReader.getProcInfo(fname)
	hdds = LogReader.getHarddrives(fname,True)
	ram = LogReader.getTotalRam(fname)
	ramAmt = "".join(ram[3].split(" ")).split(",")
	components.append(model)
	components.append(LogReader.getCtlr(fname,True))
	for k,v in cpus.items():
		for x in range(0,int(v)):
			components.append(k)
	for hd in hdds:
		for x in range(0,int(hd[-2])):
			ff = hd[3]
			if len(ff) > 3:
				ff = ff[:3]
			components.append("{} {}-{}".format(hd[1],LogReader.getHDSpeed(hd[-1]),ff))
	for r in ramAmt:
		rSplit = r.split("x")
		size = rSplit[0]
		amount = rSplit[1]
		for x in range(0,int(amount)):
			rString = "{}-{}".format(size,ram[1])
			components.append(rString)
			

  
	#Append a form factor to the model if we can get one off of a harddrive
	if len(hdds) > 0:
		ff = hdds[0][3]
		if len(ff) > 3:
			components[components.index(model)] = "{}-{}".format(model,ff[:3])

	for i in range(len(components)):
		components[i] = components[i].lower()
	return components

def getModelList():
	return jwjson.loadJSON(jwtools.getConfig("ServerIdentity"))

def getItemList(dict=False):
	ret = []
	

	sql = sqlite3.connect("itemDB.db")
	c = sql.cursor()
	c.execute("SELECT * FROM items")
	names = [[desc[0] for desc in c.description],]
	r = names+c.fetchall()
	rows = np.array(r)

	return rows


