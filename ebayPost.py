import ebaysdk
import datetime
import jwjson
import sys
import os
import DLogReader as LogReader
from ebaysdk.utils import getNodeText
from ebaysdk.trading import Connection
from ebaysdk.connection import ConnectionError

dn = os.path.dirname(os.path.realpath(__file__))
api = Connection(domain='api.sandbox.ebay.com',config_file=os.path.join(dn,"ebay.yaml"),appid='RefurbNe-e7ae-4872-bce0-668642f631ba')

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

def uploadPicture(fname):
	try:
		model = LogReader.getModel(fname)
		picturePath = getConfig(model,"PicturePath")
		if picturePath is None:
			return None
		files = {'file': ('EbayImage', file(getConfig(model,"PicturePath"), 'rb'))}
		pictureData = {
				"WarningLevel": "High",
				"PictureName": model
			}
		response = api.execute('UploadSiteHostedPictures', pictureData, files=files)
		return response.dict()
	except ConnectionError as e:
		print(e)
		print(e.response.dict())

def getConfig(model,varName):
	try:
		configFile = file(LogReader.getConfigValue("EbayConfig"),"r")
		cValues = jwjson.loadJSON(configFile.read())
		configFile.close()
		if cValues.has_key(model):
			if cValues[model].has_key(varName):
				return cValues[model][varName]

		if cValues.has_key("default"):
			if cValues["default"].has_key(varName):
				return cValues["default"][varName]

		print("Error: Could not find any config for {}".format(varName))
		return None

	except Exception as e:
		print("ERROR: Could not load config file!")
		print(e)
		return None

def genInfo(fname):
    info = LogReader.genInfo(fname).replace(",\n","<br>");
    info += "<br>"
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

def postItem(fname):  
	try:
		dict = uploadPicture(fname)
		model = LogReader.getModel(fname)
		template = file(os.path.join(dn,"template.html"),"r")
		htmlData = template.read().replace("{{ title }}", genTitle(fname))
		if dict is not None:
			htmlData = htmlData.replace("{{ image src }}","<img src='"+dict['SiteHostedPictureDetails']['FullURL']+"'>")
		else:
			htmlData = htmlData.replace("{{ image src }}","")
		#htmlData = htmlData.replace("{{ image src }}","<img src='http://i.ebayimg.sandbox.ebay.com/00/s/OTAwWDE2MDA=/z/6FkAAOSwErpWHpfG/$_1.JPG?set_id=8800005007'>")
		
		htmlData = htmlData.replace("{{ description }}",genInfo(fname))   
		myitem = {
				"Item": {
					"Title": genTitle(fname),
					"Description": "<![CDATA["+htmlData+"]]>",
					"PrimaryCategory": {"CategoryID": "11211"},
					"StartPrice": getConfig(model,"StartPrice"),
					"CategoryMappingAllowed": "true",
					"Country": "CA",
					"ConditionID": "3000",
					"Currency": "USD",
					"DispatchTimeMax": "3",
					"ListingDuration": "Days_7",
					"ListingType": "English",
					"PaymentMethods": "PayPal",
					"PayPalEmailAddress": "jwatson.dev@gmail.com",
					"PostalCode": "V9L6W3",
					"ListingType": getConfig(model,"ListingType"),
					"Quantity": "1",
					"ItemSpecifics": genItemSpecifics(fname),
					"ReturnPolicy":getConfig(model, "ReturnPolicy"),
					"ShippingDetails":getConfig(model, "ShippingDetails"),
					"Site": "Canada"
				 }
			}
		global failFlag
		if failFlag:
			print("Something went wrong, skipping {}".format(fname))
			failFlag = False
			return

		if dict is not None:
			myitem["Item"]["PictureDetails"] = {"PictureURL": dict['SiteHostedPictureDetails']['FullURL']}
		

		d = api.execute('AddItem', myitem)
		#print(d.dict()["User"]["UserID"])
		
	except ConnectionError as e:
		print(e)
		print(e.response.dict())

#endAllItems()

AbsolutePath = False
	

for argc in sys.argv:
	if argc == sys.argv[0]: #Quick hack to stop it from getting the script name
		continue

	if argc == "-abs":
		AbsolutePath = True

	elif argc == "-endall":
		endAllItems()
		
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

