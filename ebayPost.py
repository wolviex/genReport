﻿import ebaysdk
import datetime
import jwjson
import jwargs
import sqlite3
import sys
import os
import ast
import prices
import ebayTools
import DLogReader as LogReader
from ebaysdk.utils import getNodeText
from ebaysdk.trading import Connection
from ebaysdk.connection import ConnectionError



def init():
	global APIcmds
	APIcmds = getAPICommandList()





dynamicPrice = False
failFlag = False
LogURL = False
cfgOverride = {}
def dump(api, full=False):

	print("\n")

	if api.warnings():
		print("Warnings" + api.warnings())

	if api.response.content:
		print("Call Success: %s in length" % len(api.response.content))

	print("Response code: %s" % api.response_code())
	print("Response DOM1: %s" % api.response_dom()) # deprecated
	print("Response ETREE: %s" % api.response.dom())

	if full:
		print(api.response.content)
		print(api.response.json())
		print("Response Reply: %s" % api.response.reply)
	else:
		dictstr = "%s" % api.response.dict()
		print("Response dictionary: %s..." % dictstr[:150])
		replystr = "%s" % api.response.reply
		print("Response Reply: %s" % replystr[:150])

def getPictures(name):
	realpath = os.path.dirname(os.path.realpath(sys.argv[0]))
	pictureCfg = ebayTools.getConfig("default","PictureInfo")
	picPath = pictureCfg["Path"];
	fileTypes = pictureCfg["FileTypes"].split(",")
	pictureList = []
	
	if picPath[:2] == "./":
		picPath = "{}{}/{}".format(realpath,pictureCfg["Path"][1:],name)
	else:
		picPath = "{}/{}".format(picPath,name)
	if os.path.isdir(picPath):

		files = os.listdir(picPath)
		for file in files:
			fname,ext = os.path.splitext(file)
			if ext.lower() in fileTypes:
				pictureList.append("{}/{}".format(picPath,file))
	else:
		print("ERROR: picPath '%s' does not exist." % picPath)
	
	return pictureList

def mergeDictionary(dict1, dict2):

	global cfgOverride

	for k,v in dict2.items():
		if not dict1.has_key(k):
			if cfgOverride.has_key(k):
				dict1[k] = cfgOverride[k]
			else:
				dict1[k] = v;
		elif isinstance(v,dict):
			mergeDictionary(dict1[k],v)
		else:
			if cfgOverride.has_key(k):
				dict1[k] = cfgOverride[k]
			else:
				dict1[k] = v;

def uploadPicture(fname):
	try:
		model = LogReader.getModel(fname)
		pictureList = getPictures(LogReader.getSerial(fname))
		if len(pictureList) <= 0:
			pictureList = getPictures(model)
		pictureURLs = []
		if len(pictureList) <= 0:
			return None
		for picture in pictureList:
			files = {'file': ('EbayImage', file(picture, 'rb'))}
			pictureData = {
					"WarningLevel": "High",
					"PictureName": model,
					"PictureSet":"Supersize"
				}
			response = api.execute('UploadSiteHostedPictures', pictureData, files=files)
			pictureURLs.append(response.dict()['SiteHostedPictureDetails']['FullURL'])
		return pictureURLs
	except ConnectionError as e:
		print(e)
		print(e.response.dict())


def getAPICommandList():
	
	commandListFile = file(ebayTools.getConfig("default","APICommandList"),"r")
	commandList = ast.literal_eval(commandListFile.read())
	commandListFile.close()
	return commandList





def genInfo(fname):
	notes = ebayTools.getConfig(LogReader.getModel(fname),"SpecialNotes")
	info = LogReader.genInfo(fname).replace(",\n","<br>");
	info += "<br>"
	if notes is not None:
		info += "<br>{}".format(notes)
	return info



def genTitle(fname):
	ramInfo = LogReader.getTotalRam(fname)
	procInfo = LogReader.getProcInfo(fname)
	HDinfo = LogReader.getHarddrives(fname)
	
	global failFlag
	if procInfo is None:
		failFlag = True
		return "-1"

	procTitle = ", "+" ".join(["{} x{}".format(k,v) for k,v in procInfo.items()])
	procTitle = procTitle.replace("Intel(R)","")


	title = LogReader.getModel(fname)
	title += procTitle
	title += ", {} {}".format(ramInfo[0],ramInfo[1])
	if HDinfo is not None:
		title += ", "+LogReader.getNumHarddrives(HDinfo)
	return title

def getItemURL(itemID):
	itemRequest =	{
						"ItemID":itemID,
						"OutputSelector":"ViewItemURL"
					}

	request = api.execute("GetItem",itemRequest).dict()

	return request["Item"]["ListingDetails"]["ViewItemURL"]
	
										
					
					

def endAllItems():
	d = api.execute('GetUser', None)
	userID = d.dict()["User"]["UserID"]
	#YYYY-MM-DDTHH:MM:SS.SSSZ
	d = api.execute('GetSellerList',{"StartTimeFrom":"2015-10-01T00:00:00.000Z","StartTimeTo":"2015-10-30T00:00:00.000Z"})
	itemDict = d.dict()
	itemTuple = itemDict["ItemArray"]["Item"]
	for item in itemTuple:
		try:
			api.execute("EndItem", {"EndingReason":"Incorrect","ItemID":"{}".format(item["ItemID"])})
		except ConnectionError:
			print("Item already ended")
		
def addItemSpecific(name,value, specList):
	specList.append({"Name":"{}".format(name), "Value":"{}".format(value)})


def genItemSpecifics(fname):
	model = LogReader.getModel(fname)

	mConfig = ebayTools.getConfig(model,"ItemSpecifics")
	specList = []
	specDict = {}
	if mConfig is not None:
		for k,v in mConfig.items():
			addItemSpecific(k,v,specList)
	addItemSpecific("Memory (RAM) Capacity",LogReader.getTotalRam(fname)[0],specList)
	addItemSpecific("Model",model.split(" ")[-1],specList)
	addItemSpecific("Product Line",model.split(" ")[0],specList)
	addItemSpecific("MPN",model.split(" ")[-1],specList)
	addItemSpecific("CPU Cores",LogReader.getProcCores(fname),specList)
	addItemSpecific("Number of Processors",sum([v for k,v in LogReader.getProcInfo(fname).items()]),specList)
	addItemSpecific("Memory Type",LogReader.getTotalRam(fname)[1],specList)
	addItemSpecific("Processor Speed",LogReader.getProcSpeed(fname),specList)
	specDict["NameValueList"] = specList
	return specDict

def setItemConfig(model, item):
	#Get default config values first and then overwrite them with model specific values
	
	global APIcmds
	def f(cfgValues,item):
		tempDict = item
		cfgDict = {}
		for k,v in cfgValues.items():

			if k == "ItemSpecifics": #Skip item specifics so it doesn't overwrite the generated ones
				continue

			

			cmd = "Item.{}".format(k)
			if cmd in APIcmds:
				cfgDict[k] = v
				if cfgOverride.has_key(k):
					cfgDict[k] = cfgOverride[k]

		mergeDictionary(tempDict["Item"],cfgDict)
		return tempDict

	defaultCfg = ebayTools.getConfig("default")
	modelCfg  = ebayTools.getConfig(model)

	if defaultCfg is not None:
		item = f(defaultCfg,item)
	if modelCfg is not None:
		item = f(modelCfg,item)

	return item

def printLine():
	try:
		rows, columns = os.popen('stty size', 'r').read().split()
		print("-" * int(columns))
	except Exception as e:
		print("------------------------------")

def verifyPost(fname,postInfo,postTitle):

	model = LogReader.getModel(fname)
	pictures = getPictures(LogReader.getSerial(fname))
	if len(pictures) <= 0:
		pictures = getPictures(LogReader.getModel(fname))
	printLine()
	print("Picture #: {}".format(len(pictures)))
	print("TITLE:{}".format(postTitle))
	print "Buy It Now Price: ${}".format(ebayTools.getConfig(model,"BuyItNowPrice"))
	print "Starting Price: ${}".format(ebayTools.getConfig(model,"StartPrice"))
	printLine()
	print("DESCRIPTION:\n{}".format(postInfo.replace("<br>","\n")))
	while True:
		print("Is this ok? (y/n)")
		line = sys.stdin.readline().rstrip()
		if line.lower() == "y" or line.lower() == "yes":
			return
		elif  line.lower() == "n" or line.lower() == "no":
			print("Skipping...")
			return -1
		else:
			print("Invalid input")



def postItem(fname):  
	try:
		global cfgOverride
		model = LogReader.getModel(fname)
		postTitle = genTitle(fname)
		postInfo = genInfo(fname)
		if dynamicPrice:
			price = prices.getPrice(fname)
			
			if ebayTools.getConfig(model,"ListingType") == "FixedPriceItem":
				
				cfgOverride["StartPrice"] = int(price)
			else:
				cfgOverride["BuyItNowPrice"] = int(price)
				cfgOverride["StartPrice"] = int(price / 7)
		if VerifyFlag:
			if verifyPost(fname,postInfo,postTitle) is not None:
				return
		pictureURLs = uploadPicture(fname)
		template = file(os.path.join(dn,"template.html"),"r")
		htmlData = template.read().replace("{{ title }}", postTitle)
		htmlData += "<!---SERVICETAG={}-----!>".format(LogReader.getSerial(fname))

		if pictureURLs is not None:
			pictureHTML = ""
			for url in pictureURLs:
				pictureHTML += '<img src="{}" style="display:none;">'.format(url)
			htmlData = htmlData.replace("{{ image src }}",'{}'.format(pictureHTML))
		else:
			htmlData = htmlData.replace("{{ image src }}","")
		#htmlData = htmlData.replace("{{ image src }}","<img src='http://i.ebayimg.sandbox.ebay.com/00/s/OTAwWDE2MDA=/z/6FkAAOSwErpWHpfG/$_1.JPG?set_id=8800005007'>")
		
		htmlData = htmlData.replace("{{ description }}",postInfo)   
		myitem = {
				"Item": {
					"Title": genTitle(fname),
					"Description": "<![CDATA["+htmlData+"]]>",
					"ItemSpecifics": genItemSpecifics(fname),
				 }
			}
		global failFlag
		if failFlag:
			print("Something went wrong, skipping {}".format(fname))
			failFlag = False
			return

		if pictureURLs is not None:
			myitem["Item"]["PictureDetails"] = {"PictureURL": [x for x in pictureURLs]}

		
		
		myitem = setItemConfig(model,myitem)

		d = api.execute('AddItem', myitem).dict()
		
		itemURL = getItemURL(d["ItemID"])

		if LogURL:
			urlLog = file("urlLog.txt","w")
			#urlLog.write()
			urlLog.close()
		printLine()
		print(itemURL)
		printLine()
		
	except ConnectionError as e:
		print(e)
		print(e.response.dict())

#endAllItems()

AbsolutePath = False
VerifyFlag = False
init()	

dn = os.path.dirname(os.path.realpath(__file__))
api = Connection(domain=ebayTools.getConfig("default","Domain"),config_file=os.path.join(dn,"ebay.yaml"))

#Ends all active items.. WARNING
def m_endall():
	endAllItems()
#Dynamic pricing based off the prices in Prices.db
def m_p():
	global dynamicPrice
	dynamicPrice = True
#Verifies listing before posting
def m_v():
	global VerifyFlag
	VerifyFlag = True
#Changes the listing type
def m_lt(listingType):
	global cfgOverride
	cfgOverride["ListingType"] = listingType
def default(argc):
		if argc.find(".txt") > 0:
			logFile = argc[0:argc.find(".txt")] + ".txt"
		else:
			logFile = argc + ".txt"
		if not AbsolutePath:
			logPath = LogReader.getLogPath(str(logFile))
		else:
			logPath = argc
		if logPath is not None:
			if LogReader.getProcInfo(logPath) is None or LogReader.getTotalRam(logPath) is None:
				print("Something went wrong with {}. Skipping".format(logPath))
			postItem(logPath)
		else:
			print("Could not find file {}".format(str(logFile)))


jwargs.getArgs()
#for argc in sys.argv:
#	if argc == sys.argv[0]: #Quick hack to stop it from getting the script name
#		continue



#	if argc == "-abs":
#		AbsolutePath = True
#	elif argc == "-?" or argc == "-h":
#		print("-v Verify posting before uploading")
#		print("-lt Force ListingType of item")
#	elif argc == "-endall":
#		endAllItems()
#	elif argc == "-v" or argc == "-verify":
#		VerifyFlag = True
#	elif argc[:3] == "-lt":
#		listingType = argc.split("=")[-1]
#		cfgOverride["ListingType"] = listingType
#	else:
#		if argc.find(".txt") > 0:
#			logFile = argc[0:argc.find(".txt")] + ".txt"
#		else:
#			logFile = argc + ".txt"
#		if not AbsolutePath:
#			logPath = LogReader.getLogPath(str(logFile))
#		else:
#			logPath = argc
#		if logPath is not None:

#			if LogReader.getProcInfo(logPath) is None or LogReader.getTotalRam(logPath) is None:
#				print("Something went wrong with {}. Skipping".format(logPath))
#				continue

#			postItem(logPath)
#		else:
#			print("Could not find file {}".format(str(logFile)))

