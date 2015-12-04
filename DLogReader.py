import sqlite3;
import array
import os
import sys
import re
import xlrd
import traceback
from collections import OrderedDict
from collections import Counter


#Python version specific imports
try:
	import http.client as httplib;
except ImportError:
	import httplib;
	
Config = {}

def getInfoFields():
	return ("Brand","Series","Interface","Capacity","RPM","Cache","Form Factor")

def hasDBTable(db):
	c = db.cursor();
	c.execute("SELECT count(*) FROM sqlite_master WHERE type = 'table' AND name = 'harddrives'")
	if c.fetchone()[0] == 1:
		return True;
		
	return False;
		
def createTable(db):
	c = db.cursor();
	c.execute("CREATE TABLE 'harddrives' (brand text, series text, model text, interface text, capacity text, speed text, cache text, formfactor text)")
	db.commit()
	
def getRecentLog(logStr):
	recent = logStr.split("NEWLOGSTART")[-1]
	
	return recent
	
def getREGEX(model,regex, string, g,replacementFields={}):

	infoField = re.search(r">(.*?)<", regex).group(1)
	if replacementFields.has_key(infoField):
		regex = re.sub(">.*?<",">{}<".format(replacementFields[infoField]),regex,1)

	
	search = re.search(regex,string)



	if search is not None:
		return search.group(g)



	return getManualInfo(model,infoField)
		
def getManualInfo(model, infoField):
	print("%s: Could not find info for %s. Would you like to add? (y/n)" % (model,infoField) )
	try:
		line = sys.stdin.readline().rstrip().lower()
		if line == "y":
			print("Enter info for "+infoField)
			line = sys.stdin.readline().rstrip()
			return line
		elif line == "n":
			return "None"
	except Exception:
			print("Invalid input")
			return getManualInfo(model,infoField)

def getHDInfoFromSite(site, model):
	
	def f(x,y):
		return x
	postProcess = f
	infoFields = getInfoFields()
	replacementFields = {}
	
	if site.lower() == "www.newegg.com":
		requestURL = "/Product/ProductList.aspx?Submit=ENE&DEPA=0&Order=BESTMATCH&Description={}&N=-1&isNodeId=1".format(model)
		linkRegEx = '<a.*?title="(.*?{0}.*?)".*?href="(.*?{0}.*?)"'.format(model)
		infoRegEx = ">{}<.*?<dd>(.*?)</dd>"
		linkIndex = 1
	elif site.lower() == "www.harddrivesdirect.com":
		requestURL = "http://www.harddrivesdirect.com/advanced_search_result.php?keywords={}".format(model)
		linkRegEx = r'>{}<[\S\s]*?href=".*?\.com(.*?)"[\S\s]*?<b>(.*?)</b>'.format(model)             #.{{0,100}}<a href="(.*?)".{{0,100}}<b>(.*?)</b>'.format(model)
		infoRegEx = r">{}<[\S\s]*?<td[\S\s]*?>([\S\s]*?)<"
		replacementFields["Brand"] = "Manufacturer"
		replacementFields["Series"] = "Category"
		replacementFields["RPM"] = "Spindle Speed"
		replacementFields["Interface"] = "Generation"
		linkIndex = 0
		def f(x,y):
			if y == "Form Factor":
				s = re.search("\d.\d",x)
				if s is not None:
					x = '{}"'.format(s.group(0))
			return x

		postProcess = f
			
	
	conn = httplib.HTTPConnection(site);
	conn.request("GET", requestURL);
	res = str(conn.getresponse().read()); 
	link = ""
	links = re.findall(linkRegEx, res,re.IGNORECASE)
	print(links)
	if len(links) > 1:
		print("Found more than 1 of the same HDD, looking for Enterprise edition...")
		enterprise = False
		for l in links:

			x = l[int((linkIndex != 1))]

			if x.lower().find("enterprise") >= 0:
				print("Found Enterprise edition")
				enterprise = True
				link = l[linkIndex]
				break
		if not enterprise:
			print("Enterprise edition not found. Using first link")
			link = links[0][linkIndex]
	elif len(links) == 1:
		link = links[0][linkIndex]
	elif len(links) == 0:
		return None

	
	conn.request("GET",link);
	res2 = str(conn.getresponse().read()); 			
	infoDict = OrderedDict((x, postProcess(getREGEX(model,infoRegEx.format(x),res2,1,replacementFields),x)) for x in infoFields)
	return infoDict


#sql order
# brand text, series text, model text, interface text, capacity text, speed text, cache text, formfactor text
def getHDInfo(model):


	
	
	addHDtoDB = False;
	db = sqlite3.connect(getConfigValue("DBPath"));
	infoFields = getInfoFields()
	
	if hasDBTable(db) == False:
		print("Harddrive table not found. Creating.")
		createTable(db);
	
	c = db.cursor();
	
	
	try:
		c.execute("SELECT * FROM harddrives WHERE model='"+model+"'");
		
		hdData = c.fetchone();
		return hdData[0], hdData[4],hdData[5],hdData[7];
	except Exception:
		print("Adding "+model+" to database.")
		addHDtoDB = True;

	if addHDtoDB:
		try:
			infoDict = getHDInfoFromSite("www.harddrivesdirect.com",model)
			if infoDict is None:
				print("Can't find Harddrive information from harddrivesdirect.com Trying newegg.com")
				infoDict = getHDInfoFromSite("www.newegg.com",model)

			if infoDict is not None:
				c.execute("INSERT INTO harddrives VALUES ('{0}', '{1}', '{7}', '{2}','{3}', '{4}', '{5}', '{6}')".format(*(tuple(x for (k,x) in infoDict.items())+(model,))))
				db.commit();
				db.close();
				return infoDict['Brand'], infoDict['Capacity'], infoDict['RPM'], infoDict['Form Factor']
			else:
				print("Info for {} not found. Would you like to add? (y/n)".format(model))
				while True:
					line = sys.stdin.readline().rstrip()
					if line.lower() == "y":
						infoDict = OrderedDict((x,getManualInfo(model,x)) for x in infoFields)
						c.execute("INSERT INTO harddrives VALUES ('{0}', '{1}', '{7}', '{2}','{3}', '{4}', '{5}', '{6}')".format(*(tuple(x for (k,x) in infoDict.items())+(model,))))
						db.commit();
						db.close();
						return infoDict['Brand'], infoDict['Capacity'], infoDict['RPM'], infoDict['Form Factor']
					elif line.lower() == "n":
						c.execute("INSERT INTO harddrives VALUES ('{0}', '{1}', '{7}', '{2}','{3}', '{4}', '{5}', '{6}')".format(*(("None Found",)*7+(model,))))
						db.commit();
						db.close();
						return ("No Info",)*4;
					else:
						print("Invalid selection")





			

			return infoDict['Brand'], infoDict['Capacity'], infoDict['RPM'], infoDict['Form Factor']
		except AttributeError as e:
			traceback.print_exc()
			db.close();
			return "No HDD Info found";
	
			
def getRealHDBrand(model,brand):
	try:
		db = sqlite3.connect(Config["DBPath"]);
		c = db.cursor();
		c.execute("SELECT * FROM harddrives WHERE model ='"+model+"'")
		hdData = c.fetchone();
		db.close();
		return hdData[0];
	except Exception:
		db.close();
		return brand;
	
def getSmallestStr(r):
	
	prd = r;
	longestStr = -1;
	prdSearch = re.findall(r"[\w\d]*",prd);
	for id in range(0,len(prdSearch)):
		if longestStr < 0:
			longestStr = id;
		else:
			if len(prdSearch[id]) > len(prdSearch[longestStr]):
				longestStr = id;
		
	if longestStr >= 0:
		prd = str(prdSearch[longestStr]);
			

def getAsset(serial):

	try:
		assetList = xlrd.open_workbook("assets.xls");
		sh = assetList.sheet_by_index(0);
		num_rows = sh.nrows;
		for x in range(0,num_rows):
			if sh.cell(x,16).value == serial:
				return str(int(sh.cell(x,0).value));
	except Exception:
		return '';
		
	return '';



	

def getFails(fname):
	serverlog = open(fname, 'r');
	lString = getRecentLog(serverlog.read());
	try:
		lString = re.findall(r"\*\*[\s\S]*?Test Results.*",lString);
		fString = set()
		for x in lString:
			try:
				fString.add(re.search("\*\* (.*?) \*\*.*?Fail",x,re.DOTALL).group(1));
			except AttributeError:
				continue;
		
	except AttributeError:
		lString = "Fails not found";
	serverlog.close();
	return '\n'.join(fString);
	
def getSerial(fname):
	serverlog = open(fname, 'r');
	lString = getRecentLog(serverlog.read());
	try:
		lString = re.search(r"System Information.*?Serial Number.*?: (.*?)\n.*?Family Name",lString,re.MULTILINE | re.DOTALL).group(1);
	except AttributeError:
		lString = "Serial not found";
	serverlog.close();
	return lString;

def getLogPath(fname):
	for root, dirs, files in os.walk(Config["ServerPath"]):
		for file in files:
			if file.lower() == fname.lower():
				print(os.path.join(root, file));
				return os.path.join(root, file);	

def getHDSpeed(model):
	db = sqlite3.connect(getConfigValue("DBPath"))
	cur = db.cursor()
	query = "SELECT * FROM harddrives WHERE model = '{}'".format(model)
	cur.execute(query)
	db.commit()
	hd = cur.fetchone()
	names = [desc[0] for desc in cur.description]
	speedIndex = names.index("speed")
	speed = hd[speedIndex]
	s = re.search(r"(\d*)(?:\D|$)",speed)
	if s is not None:
		speed = s.group(1)
		ispeed = int(speed)
		if ispeed > 1000:
			s = float(ispeed)/1000
			if ispeed % 1000 == 0:
				return "{}k".format(int(s))
			elif int(s) == 10:
				return "{}k".format(int(s))
			else:
				return "{:.1f}k".format(float(ispeed)/1000)
	return speed
	
def getCtlr(fname,SFF=False):
	serverlog = open(fname, 'r');
	lString = getRecentLog(serverlog.read());
	try:
		lString = re.search(r"Ctlr\n-*?\n(.*?),",lString,re.MULTILINE | re.DOTALL).group(1);
		if SFF:
			split = lString.split(" ")[:2]
			if re.search(r"[[a-zA-Z]\d\d\d",split[-1]) is not None:
				lString = split[-1]
			else:
				lString = "".join(lString.split(" ")[:2])
	except AttributeError:
		lString = "No raid controller"
	serverlog.close();
	return lString;
	
def getModel(fname):
	serverlog = open(fname, 'r');
	lString = getRecentLog(serverlog.read());
	try:
		lString = re.search(r"System Information.*?Product Name.*?: (.*?)\n.*?Family Name",lString,re.MULTILINE | re.DOTALL).group(1);
	except AttributeError:
		lString = "Model name not found";
	serverlog.close();

	return " ".join(lString.split())
	
def getProcInfo(fname):
	serverlog = open(fname, 'r');	
	lString = getRecentLog(serverlog.read());
	serverlog.close();
	try:
		

		lString = re.search(r"Processor Information.*?System Information",lString,flags=re.MULTILINE | re.DOTALL).group(0);
		
		regEx = r"\nManufacturer.*?: (.*?)\n[\s\S]{0,90}\nVersion.*?: (.*?)\n"
		cpuList = re.findall(regEx,lString)
		
		infoList = [" ".join(x.split()) if y == "N/A" else " ".join(y.split()) for x,y in cpuList]

		for i in range(len(infoList)):
			search = re.search(r"CPU\s+?(\b.*?)\s",infoList[i])
			if search is not None:
				infoList[i] = search.group(1)


		count = dict(Counter(infoList))
		if count.has_key("N/A"):
			count.pop("N/A")
		return count;
	except AttributeError as e:
		print(e)
		
		return None



def getProcCores(fname):
	serverlog = open(fname, 'r');
	lString = serverlog.read()
	ret = ""
	try:
		lString = re.search(r"Processor Information.*?System Information",lString,flags=re.MULTILINE | re.DOTALL).group(0);
		lString = re.search(r"\CPU Cores Per Socket.*?: (.*?)\n",lString);
		ret = lString.group(1)
	except AttributeError:
		ret = "";
	serverlog.close()
	return ret

def getProcSpeed(fname):
	serverlog = open(fname, 'r');
	lString = serverlog.read()
	ret = ""
	try:
		lString = re.search(r"Processor Information.*?System Information",lString,flags=re.MULTILINE | re.DOTALL).group(0);
		lString = re.search(r"\Current Processor Speed.*?: (\d*)",lString);
		speed = float(lString.group(1)) / 1000.0
		ret = "{0:.2f}GHz".format(speed)
	except AttributeError:
		ret = "";
	serverlog.close()
	return ret

def getHDInterface(fname):
	serverlog = open(fname, 'r');
	lString = getRecentLog(serverlog.read());
	lString = re.search(r"\n(\w*?) [0-9\-]*? Disk\n.*?-*?\n.*?Encryption",lString,re.MULTILINE | re.DOTALL);
	return lString.group(1)
		
			
def getHarddrives(fname,includeModels=False):
	serverlog = open(fname, 'r');
	lString = getRecentLog(serverlog.read());

	regEx = r"\n\w{1,10} (?:[0-9\-]{0,10}|Disk) (?:[0-9\-]{0,10}|Disk)\n.*?-\n.*?\n\n"
	#r"\n\w*? [0-9\-]*? Disk\n.*?-*?\n.*?Encryption"
	infoFields = re.findall(regEx,lString,re.MULTILINE | re.DOTALL)

	hddList = []
	returnList = []
	for field in infoFields:
		modelSearch = re.search(r"Product.*?: (.*?)\n", field)
		if modelSearch is not None:
			model = modelSearch.group(1)
			modelStrip = re.search(r"(?:^|\s)(\S*?)(?:-|$)",model)
			if modelStrip is not None:
				model = modelStrip.group(1)
			hddList.append(model)
	
	hddDict = dict(Counter(hddList))

	for k,v in hddDict.items():
		HDInfo = getHDInfo(k) + (v,)
		if includeModels:
			HDInfo += (k,)
		returnList.append(HDInfo)

	return returnList
	
def getHarddrives2(fname):
	serverlog = open(fname, 'r');
	lString = getRecentLog(serverlog.read());

	regEx = r"\n\w{1,10} (?:[0-9\-]|Disk) (?:[0-9\-]|Disk)\n.*?\n\n\n" #.*?-*?\n.*?Encryption"
	#r"\n\w*? [0-9\-]*? Disk\n.*?-*?\n.*?Encryption"
	lString = re.findall(regEx,lString,re.MULTILINE | re.DOTALL);

	return lString;
	
	rString = "";
	
	HDDS = {}
	hdTrays = array.array('i',(0 for i in range(0,20)))
	try:
		for x in lString:
			#mnf = re.search(r"Manufacturer.*?: (.*?)\n", x,re.MULTILINE | re.DOTALL).group(1);
			prd = re.search(r"Product.*?: (.*?)\n", x,re.MULTILINE | re.DOTALL).group(1);
			#tray = re.search(r"Target.*?: (.*?)\n", x,re.MULTILINE | re.DOTALL).group(1);
				
			prd = prd.replace("ATA ", "")
			prd = prd.replace("SAMSUNG ", "")
			
			hdTrays[int(tray)] += 1;

			if hdTrays[int(tray)] > 1:
				continue;

			
			try:
				HDDS[(mnf,prd)] += 1;
			except KeyError:
				HDDS[(mnf,prd)] = 1;
				
				
		hdStringArray = set();
		
		for k,v in HDDS.items():
			
			HDInfo = getHDInfo(str(k[1]))
			
			hdStringArray.add((getRealHDBrand(str(k[1]),str(k[0])),)+HDInfo+(str(v),k[1]))
		
		
	except AttributeError:
		return None
	if len(lString) <= 0:
		return None

	print hdStringArray

	return hdStringArray;
	
def getTotalRam(fname):
	serverlog = open(fname, 'r');
	lString = getRecentLog(serverlog.read());
	try:
		lString = re.search(r"Memory Information \*\*.*?\*\*",lString,re.MULTILINE | re.DOTALL).group(0);
		
		ramType = re.search(r"DDR\d", lString).group(0);
		ramSpeed = re.search(r"\d*MHz",lString).group(0);
		
		rString = re.findall(r"Size.*?: (\d*).*?\n",lString);
		dimms = {}
		
		ramSize = 0;
		
		for x in rString:
			try:
				ramSize += int(x);
				if int(x) > 0:
					try:
						dimms[str(int(int(x)/1024))] += 1
					except KeyError:
						dimms[str(int(int(x)/1024))] = 1;
			except ValueError:
				continue;
	except AttributeError:
		return None
		
	dimmStr = ', '.join(['%sGB x%s' % (key, value) for (key, value) in dimms.items()])
	serverlog.close();
	
	ramStr = ""
	if ramSize >= 1024:
		ramStr = str(int(int(ramSize)/1024)) + "GB"
	else:
		ramStr = str(ramSize) + "MB"
	
	return ramStr,ramType,ramSpeed,dimmStr;
	
def getNumHarddrives(HDarray):
	HDdict = {}

	for HD in HDarray:
		if HDdict.has_key(HD[1]):
			HDdict[HD[1]] += int(HD[4])
		else:
			HDdict[HD[1]] = int(HD[4])
	return " ".join(["{} HDD x{}".format(k,v) for k,v in HDdict.items()])

def getFullHDString(HDarray):
	HDset = []
	
	if HDarray is None:
		return "No HDD's"
	for HD in HDarray:
		HDset.append("{} ({}, {}, {}) x{}".format(*HD))
	return ",\n".join(HDset)

def genInfo(fname,returnList=False):
	ramInfo = getTotalRam(fname)
	procInfo = getProcInfo(fname)
	if procInfo is not None:
		procString =  ",\n".join(["{} x{}".format(k,v) for k,v in procInfo.items()])


	else:
		procString = "CPU not found"
	if ramInfo is not None:
		ramString = "{} {} {} ({})".format(*ramInfo)
	else:
		ramString = "No RAM Found"

	ctrl = getCtlr(fname)

	

	hdds = getFullHDString(getHarddrives(fname))

	li = [procString, ramString, ctrl, hdds]

	if returnList:
		return li
	
	
	return ",\n".join(li)

def getConfigValue(name):
	if Config.has_key(name):

		#Quick hack to make sure local files are pointed to the script directory and not working directory
		if len(Config[name]) >= 2:
			directory = Config[name][:2]
			if directory == "./":
				realpath = os.path.dirname(os.path.realpath(sys.argv[0]))
				Config[name] = realpath + Config[name][1:]
				print(Config[name])


		return Config[name]
	else:
		return None

def loadGlobalVars():
	realpath = os.path.dirname(os.path.realpath(sys.argv[0]))
	cfile = open(realpath + "/config","r")
	conf = cfile.read()
	c = re.findall(r"(\w*)=(.*?);",conf)
	
	for x in c:
		Config[x[0]] = x[1]


loadGlobalVars()