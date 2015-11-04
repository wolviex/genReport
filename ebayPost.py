import ebaysdk
import datetime
import jwjson
import sys
import os
import ast
import DLogReader as LogReader
from ebaysdk.utils import getNodeText
from ebaysdk.trading import Connection
from ebaysdk.connection import ConnectionError



def init():
	global APIcmds
	APIcmds = getAPICommandList()






failFlag = False

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
	pictureCfg = getConfig("default","PictureInfo")
	fileTypes = pictureCfg["FileTypes"].split(",")
	pictureList = []
	picPath = "{}/{}".format(pictureCfg["Path"],name)
	if os.path.isdir(picPath):
		files = os.listdir(picPath)
		for file in files:
			fname,ext = os.path.splitext(file)
			if ext.lower() in fileTypes:
				pictureList.append("{}/{}".format(picPath,file))
	return pictureList

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
					"PictureName": model
				}
			response = api.execute('UploadSiteHostedPictures', pictureData, files=files)
			pictureURLs.append(response.dict()['SiteHostedPictureDetails']['FullURL'])
		return pictureURLs
	except ConnectionError as e:
		print(e)
		print(e.response.dict())


def getAPICommandList():
	print getConfig("default","APICommandList")
	commandListFile = file(getConfig("default","APICommandList"),"r")
	commandList = ast.literal_eval(commandListFile.read())
	commandListFile.close()
	return commandList



def getConfig(model,varName=None):
	try:
		configFile = file(LogReader.getConfigValue("EbayConfig"),"r")
		cValues = jwjson.loadJSON(configFile.read())
		configFile.close()
		if cValues.has_key(model):
			if varName is None:
				return cValues[model]
			if cValues[model].has_key(varName):
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

def genInfo(fname):
	notes = getConfig(LogReader.getModel(fname),"SpecialNotes")
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

	mConfig = getConfig(model,"ItemSpecifics")
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
		for k,v in cfgValues.items():

			if k == "ItemSpecifics": #Skip item specifics so it doesn't overwrite the generated ones
				continue

			cmd = "Item.{}".format(k)
			if cmd in APIcmds:
				item["Item"][k] = v
		return item

	defaultCfg = getConfig("default")
	modelCfg  = getConfig(model)

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

def postItem(fname):  
	try:
		pictureURLs = uploadPicture(fname)
		model = LogReader.getModel(fname)
		postTitle = genTitle(fname)
		postInfo = genInfo(fname)


		template = file(os.path.join(dn,"template.html"),"r")
		htmlData = template.read().replace("{{ title }}", postTitle)
		htmlData += "<!---SERVICETAG={}-----!>".format(LogReader.getSerial(fname))

		if pictureURLs is not None:
			pictureHTML = ""
			for url in pictureURLs:
				pictureHTML += '<li><img src="{}"></li>'.format(url)
			htmlData = htmlData.replace("{{ image src }}",'<img src="{}">'.format(pictureURLs[0]))
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

		if VerifyFlag:
			printLine()
			print("TITLE:{}".format(postTitle))
			printLine()
			print("DESCRIPTION:\n{}".format(postInfo.replace("<br>","\n")))
			while True:
				print("Is this ok? (y/n)")
				line = sys.stdin.readline().rstrip()
				if line.lower() == "y" or line.lower() == "yes":
					break
				elif  line.lower() == "n" or line.lower() == "no":
					print("Skipping...")
					return
				else:
					print("Invalid input")




		d = api.execute('AddItem', myitem).dict()
		
		itemURL = getItemURL(d["ItemID"])

		printLine()
		print(itemURL)
		printLine()

		#print(d.dict()["User"]["UserID"])
		
	except ConnectionError as e:
		print(e)
		print(e.response.dict())

#endAllItems()

AbsolutePath = False
VerifyFlag = False
init()	

dn = os.path.dirname(os.path.realpath(__file__))
api = Connection(domain=getConfig("default","Domain"),config_file=os.path.join(dn,"ebay.yaml"))

for argc in sys.argv:
	if argc == sys.argv[0]: #Quick hack to stop it from getting the script name
		continue



	if argc == "-abs":
		AbsolutePath = True

	elif argc == "-endall":
		endAllItems()
	elif argc == "-v" or argc == "-verify":
		VerifyFlag = True
		
	else:
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
				continue

			postItem(logPath)
		else:
			print("Could not find file {}".format(str(logFile)))

