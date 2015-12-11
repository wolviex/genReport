import ebaysdk
import jwjson
import jwtools
import datetime
import os
import sys
from ebaysdk.trading import Connection
import DLogReader as LogReader

from ebaysdk.connection import ConnectionError

def getConfig(model,varName=None):
	try:
		configFile = file(LogReader.getConfigValue("EbayConfig"),"r")
		cValues = jwjson.loadJSON(configFile.read())
		configFile.close()
		#if cfgOverride.has_key(varName):
		#	return cfgOverride[varName]
		if cValues.has_key(model):
			if varName is None:
				return cValues[model]
			if cValues[model].has_key(varName):
				print(cValues[model][varName])
				if type(cValues[model][varName]) is str or type(cValues[model][varName]) is unicode:
					
					if cValues[model][varName][:2] == "./":
						realpath = os.path.dirname(os.path.realpath(sys.argv[0]))
						
						return realpath + cValues[model][varName][1:]

				return cValues[model][varName]

		if cValues.has_key("default"):
			if varName is None:
				return cValues["default"]
			if cValues["default"].has_key(varName):
				if type(cValues["default"][varName]) is str or type(cValues["default"][varName]) is unicode:
					
					if cValues["default"][varName][:2] == "./":
						realpath = os.path.dirname(os.path.realpath(sys.argv[0]))
						return realpath + cValues["default"][varName][1:]

				return cValues["default"][varName]

		print("Warning: Could not find any config for {}".format(varName))
		return None

	except Exception as e:
		print("Warning: Could not load config file!")
		print(e)
		return None

def ebayTime(d):
	return "{}.000".format(d.strftime("%Y-%m-%dT%H:%M:%S"))

def getTimeFilter():

	r = 1
	d = {}
	ret = []
	for i in range(-r,r):
		t = datetime.date.today()
		t2 = datetime.date.today()
		t += datetime.timedelta(days=119*i)
		t2 += datetime.timedelta(days=119*(i+1))
		ret.append({"StartTimeFrom":ebayTime(t),"StartTimeTo":ebayTime(t2),"GranularityLevel":"Coarse","Pagination":{"EntriesPerPage":200},"OutputSelector":["ViewItemURL","Title","ItemID"]})

	return ret


def getAllListings():
	
	dn = os.path.dirname(os.path.realpath(__file__))
	api = Connection(domain=getConfig("default","Domain"),config_file=os.path.join(dn,"ebay.yaml"))
	timeFilters = getTimeFilter()
	query = [api.execute('GetSellerList',f).dict() for f in timeFilters]
	f = False
	f2 = False
	ret = []
	for listing in query:
		for item in listing["ItemArray"]["Item"]:
			if type(item) is not str:
				ret.append([item["Title"],item["ListingDetails"]["ViewItemURL"],item["ItemID"]])
	return ret
