import ebaysdk
import datetime
import DLogReader as LogReader
from ebaysdk.utils import getNodeText
from ebaysdk.trading import Connection
from ebaysdk.connection import ConnectionError

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

def uploadPicture(api):
    try:
        files = {'file': ('EbayImage', open("pe2950.jpg", 'rb'))}
        pictureData = {
                "WarningLevel": "High",
                "PictureName": "PE2950"
            }
        response = api.execute('UploadSiteHostedPictures', pictureData, files=files)
        return response.dict()
    except ConnectionError as e:
        print(e)
        print(e.response.dict())

def genInfo(fname):
    info = LogReader.genInfo(fname).replace(",\n","<br>");
    info += "<br>"
    return info

def genTitle(fname):
	ramInfo = LogReader.getTotalRam(fname)

	title = LogReader.getModel(fname)
	title += ", "+LogReader.getProcInfo(fname)
	title += ", {} {}".format(ramInfo[0],ramInfo[1])
	title += ", "+LogReader.getNumHarddrives(LogReader.getHarddrives(fname))

	return title



def postItem():        
    try:
        
        fname = "CV92BC1.txt"
        api = Connection(domain='api.sandbox.ebay.com',config_file="ebay.yaml",appid='JesseWat-67ba-4524-861d-4852beacadc1')
        #dict = uploadPicture(api)
        #-------- response = api.execute('findItemsAdvanced', {'keywords': 'legos'})
        template = open("template.html","r")
        htmlData = template.read().replace("{{ title }}", genTitle(fname))
        #htmlData = htmlData.replace("{{ image src }}","<img src='"+dict['SiteHostedPictureDetails']['FullURL']+"'>")
        htmlData = htmlData.replace("{{ image src }}","<img src='http://i.ebayimg.sandbox.ebay.com/00/s/OTAwWDE2MDA=/z/6FkAAOSwErpWHpfG/$_1.JPG?set_id=8800005007'>")
        
        htmlData = htmlData.replace("{{ description }}",genInfo(fname))
    
        myitem = {
                "Item": {
                    "Title": genTitle(fname),
                    "Description": "<![CDATA["+htmlData+"]]>",
                    "PrimaryCategory": {"CategoryID": "11211"},
                    "StartPrice": "1.0",
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
                    "ListingType": "Chinese",
                    "Quantity": "1",
                    "PictureDetails": {"PictureURL": 'http://i.ebayimg.sandbox.ebay.com/00/s/OTAwWDE2MDA=/z/6FkAAOSwErpWHpfG/$_1.JPG?set_id=8800005007'},
                    "ReturnPolicy": {
                        "ReturnsAcceptedOption": "ReturnsAccepted",
                        "RefundOption": "MoneyBack",
                        "ReturnsWithinOption": "Days_30",
                        "Description": "If you are not satisfied, return for refund.",
                        "ShippingCostPaidByOption": "Buyer"
                    },
                    "ShippingDetails": {
                        "ShippingType": "Flat",
                        "ShippingServiceOptions": {
                            "ShippingServicePriority": "1",
                            "ShippingService": "USPSMedia",
                            "ShippingServiceCost": "2.50"
                        }
                    },
                    "Site": "Canada"
                }
            }
        
        api.execute('VerifyAddItem', myitem)
        
    except ConnectionError as e:
        print(e)
        print(e.response.dict())
        
        
postItem()