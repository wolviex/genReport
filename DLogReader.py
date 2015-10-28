import sqlite3;
import array
import os
import sys
import re
import xlrd
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
	
def getREGEX(model,regex, string, g):
	search = re.search(regex,string)
	if search is not None:
		return search.group(g)
	else:
		infoField = re.search(r">(.*?)<", regex).group(1)

		return getManualInfo(model,infoField)
		
def getManualInfo(model, infoField):
	print("%s: Could not find info for %s. Would you like to add? (y/n)" % (model,infoField) )
	try:
		line = sys.stdin.readline().rstrip().lower()
		if line == "y":
			print("Enter info for "+infoField)
			line = sys.stdin.readline().rstrip()
			return line
	except Exception:
			print("Invalid input")
			return getManualInfo(model,infoField)




#sql order
# brand text, series text, model text, interface text, capacity text, speed text, cache text, formfactor text
def getHDInfo(model,fname):


	
	
	addHDtoDB = False;
	db = sqlite3.connect(Config["DBPath"]);
	
	if hasDBTable(db) == False:
		print("Harddrive table not found. Creating.")
		createTable(db);
	
	c = db.cursor();
	
	
	try:
		c.execute("SELECT * FROM harddrives WHERE model='"+model+"'");
		
		hdData = c.fetchone();
		return hdData[4],hdData[5],hdData[7];
	except Exception:
		print("Adding "+model+" to database.")
		addHDtoDB = True;

	if addHDtoDB:
		try:
			conn = httplib.HTTPConnection('www.newegg.com');
			conn.request("GET", "/Product/ProductList.aspx?Submit=ENE&DEPA=0&Order=BESTMATCH&Description="+model+"&N=-1&isNodeId=1");
			res = str(conn.getresponse().read()); 
			link = ""
			links = re.findall(r'<a.*?title="(.*?{0}.*?)".*?href="(.*?{0}.*?)"'.format(model), res,re.IGNORECASE)
			if len(links) > 1:
				print("Found more than 1 of the same HDD, looking for Enterprise edition...")
				enterprise = False
				for x,y in links:
					if x.lower().find("enterprise") >= 0:
						print("Found Enterprise edition")
						enterprise = True
						link = y
						break
				if not enterprise:
					print("Enterprise edition not found. Using first link")
					link = links[0][1]
			else:
				link = links[0][1]



			#Make sure the model is in the link
			re.search(model,link).group(0);
			conn.request("GET",link);
			res2 = str(conn.getresponse().read()); 			
			infoFields = getInfoFields()
			infoDict = OrderedDict((x, getREGEX(model,r">%s<.*?<dd>(.*?)</dd>" % x,res2,1)) for x in infoFields)
			c.execute("INSERT INTO harddrives VALUES ('{0}', '{1}', '{7}', '{2}','{3}', '{4}', '{5}', '{6}')".format(*(tuple(x for (k,x) in infoDict.items())+(model,))))
			db.commit();
			db.close();
			return infoDict['Capacity'], infoDict['RPM'], infoDict['Form Factor']
		except AttributeError:
			print(traceback.print_exc());
			return "No HDD Info found";
	db.close();
			
def getRealHDBrand(model,brand):
	try:
		db = sqlite3.connect("hdDatabase.db");
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
		return;
		
	return;

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
	
	
def getCtlr(fname):
	serverlog = open(fname, 'r');
	lString = getRecentLog(serverlog.read());
	try:
		lString = re.search(r"Ctlr\n-*?\n(.*?),",lString,re.MULTILINE | re.DOTALL).group(1);
	except AttributeError:
		lString = "Raid Controller not found"
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
	return lString;
	
def getProcInfo(fname):
	serverlog = open(fname, 'r');	
	lString = getRecentLog(serverlog.read());
	serverlog.close();
	try:
		lString = re.search(r"Processor Information.*?System Information",lString,flags=re.MULTILINE | re.DOTALL).group(0);
		lString = re.findall(r"\nVersion.*?: (.*?)\n",lString);
		lString = [" ".join(x.split()) for x in lString]
		count = dict(Counter(lString))
		if count.has_key("N/A"):
			count.remove("N/A")
		return count;
	except AttributeError:
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
		
			
	
	
def getHarddrives(fname):
	serverlog = open(fname, 'r');
	lString = getRecentLog(serverlog.read());

	lString = re.findall(r"\n\w*? [0-9\-]*? Disk\n.*?-*?\n.*?Encryption",lString,re.MULTILINE | re.DOTALL);
	
	rString = "";
	
	HDDS = {}
	hdTrays = array.array('i',(0 for i in range(0,20)))
	try:
		for x in lString:
			mnf = re.search(r"Manufacturer.*?: (.*?)\n", x,re.MULTILINE | re.DOTALL).group(1);
			prd = re.search(r"Product.*?: (.*?)\n", x,re.MULTILINE | re.DOTALL).group(1);
			tray = re.search(r"Target.*?: (.*?)\n", x,re.MULTILINE | re.DOTALL).group(1);
			
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
				
			
			
			hdTrays[int(tray)] += 1;

			if hdTrays[int(tray)] > 1:
				continue;

			#print(prd + " " +tray)
			
			try:
				HDDS[(mnf,prd)] += 1;
			except KeyError:
				HDDS[(mnf,prd)] = 1;
				
				
		hdStringArray = set();
		
		for k,v in HDDS.items():
			hdStringArray.add((getRealHDBrand(str(k[1]),str(k[0])),)+getHDInfo(str(k[1]),fname)+(str(v),))
		
	except AttributeError:
		return None
	if len(lString) <= 0:
		return None
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
						dimms[str(int(int(x)/1000))] += 1
					except KeyError:
						dimms[str(int(int(x)/1000))] = 1;
			except ValueError:
				continue;
	except AttributeError:
		return None
		
	dimmStr = ', '.join(['%sGB x%s' % (key, value) for (key, value) in dimms.items()])
	serverlog.close();
	
	ramStr = ""
	if ramSize >= 1000:
		ramStr = str(int(int(ramSize)/1000)) + "GB"
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
	return " ".join(["{} x{}".format(k,v) for k,v in HDdict.items()])

def getFullHDString(HDarray):
	HDset = []
	
	if HDarray is None:
		return "No HDD's"

	for HD in HDarray:
		HDset.append("{} ({}, {}, {}) x{}".format(*HD))

	return ",\n".join(HDset)

def genInfo(fname):

	ramInfo = getTotalRam(fname)
	procInfo = getProcInfo(fname)
	if procInfo is not None:
		ret =  ",\n".join(["{} x{}".format(k,v) for k,v in procInfo.items()])  + ",\n"
	else:
		ret = "CPU not found\n"
	if ramInfo is not None:
		ret += "{} {} {} ({}),\n".format(*ramInfo)
	else:
		ret += "No RAM Found\n"
	ret += getCtlr(fname) + ",\n"

	ret += getFullHDString(getHarddrives(fname))
	
	return ret;

def getConfigValue(name):
	if Config.has_key(name):
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