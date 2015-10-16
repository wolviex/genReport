import xlsxwriter
import re
import xlrd
import sys
import array;
import time;
import os;
from ftplib import FTP
import sqlite3;
import traceback;
from collections import OrderedDict

#Python version specific imports
try:
	import http.client as httplib;
except ImportError:
	import httplib;
	
Config = {}
	
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
	if re.search(r">(.*?)<", regex).group(1) == "Model":
		return model

	if search is not None:
		return search.group(g)
	else:
		infoField = re.search(r">(.*?)<", regex).group(1)


		print("%s: Could not find info for %s. Would you like to add? (y/n)" % (model,infoField) )
		line = sys.stdin.readline().rstrip().lower()
		if line == "y":
			print("Enter info for "+infoField)
			line = sys.stdin.readline().rstrip()
			return line
		
		return "Not found"

def enterHDInfo(model):
	print("Could not find info for %s. Would you like to add?" % model)
	line = sys.stdin.readline().rstrip().lower()
   # if line == "y":


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
		return hdData[4] + ", "+hdData[5] + ", " + hdData[7];
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
			infoFields = ("Brand","Series","Interface","Capacity","RPM","Cache","Form Factor")
			infoDict = OrderedDict((x, getREGEX(model,r">%s<.*?<dd>(.*?)</dd>" % x,res2,1)) for x in infoFields)
			c.execute("INSERT INTO harddrives VALUES ('{0}', '{1}', '{7}', '{2}','{3}', '{4}', '{5}', '{6}')".format(*(tuple(x for (k,x) in infoDict.items())+(model,))))
			db.commit();
			db.close();
			return '%s, %s, %s' % (infoDict['Capacity'], infoDict['RPM'], infoDict['Form Factor'])
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
	
	cpuDict = {}
	ret = "";
	lString = getRecentLog(serverlog.read());
	try:
		lString = re.search(r"Processor Information.*?System Information",lString,flags=re.MULTILINE | re.DOTALL).group(0);
		lString = re.findall(r"\nVersion.*?: (.*?)\n",lString);
		for x in lString:
			if x == "N/A":
				continue
			try:
				cpuDict[x] += 1
			except KeyError:
				cpuDict[x] = 1;
			
		for cpu, value in cpuDict.items():
			ret += str(cpu)+" x"+str(value);
	except AttributeError:
		ret = "CPU Info not found";
	serverlog.close();
	return " ".join(ret.split());

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
			print(k[0] + " "+k[1])
			hdStringArray.add(getRealHDBrand(str(k[1]),str(k[0])) +  " ("+getHDInfo(str(k[1]),fname)+") x"+str(v))
		rString = "\n".join(hdStringArray);
	except AttributeError:
		rString = "No HDDs";
	if len(lString) <= 0:
		rString = "No HDDs";
	return rString;
	
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
		return "Ram not found";
		
	dimmStr = ', '.join(['%sGB x%s' % (key, value) for (key, value) in dimms.items()])
	serverlog.close();
	
	ramStr = ""
	if ramSize >= 1000:
		ramStr = str(int(int(ramSize)/1000)) + "GB"
	else:
		ramStr = str(ramSize) + "MB"
	
	return ramStr +" "+ramType + " " +ramSpeed + " ("+dimmStr+")";
	
def formatXML(workbook,worksheet,rnum):
	cell_format = workbook.add_format({'bold': True});
	font_format = workbook.add_format();
	font_format.set_font_size(10);
	worksheet.set_column(0,2,15);
	worksheet.set_column(3,3,50,font_format);
	worksheet.set_column(4,4,40,font_format);
	worksheet.set_column(5,5,50,font_format);
	worksheet.set_row(0,20,cell_format)
	for x in range(1,rnum):
		worksheet.set_row(x,53);
		
	worksheet.write(0,0, "Service Tag");
	worksheet.write(0,1, "Asset");
	worksheet.write(0,2, "Model");
	worksheet.write(0,3, "Specs");
	worksheet.write(0,4, "Notes");
	worksheet.write(0,5, "Fails");
	
	return;
	
def genXML(rnum):
	workbook = xlsxwriter.Workbook(Config["XLPath"])
	worksheet = workbook.add_worksheet();
	formatXML(workbook,worksheet,rnum);
	return workbook;
	
def genInfo(fname):
	ret = getProcInfo(fname) + ",\n"
	ret += getTotalRam(fname) + ",\n"
	ret += getCtlr(fname) + ",\n"
	ret += getHarddrives(fname);
	
	return ret;
	
def addServer(workbook, fname, index):

	serial = getSerial(fname);
	index += 1;
	worksheet = workbook.worksheets()[0];
	worksheet.write(index,0, serial);
	worksheet.write(index,1, getAsset(serial));
	worksheet.write(index,2, getModel(fname));
	worksheet.write(index,3, genInfo(fname));
	worksheet.write(index,5, getFails(fname));

def loadGlobalVars():
	realpath = os.path.dirname(os.path.realpath(sys.argv[0]))
	cfile = open(realpath + "/config","r")
	conf = cfile.read()
	c = re.findall(r"(\w*)=(.*?);",conf)
	
	for x in c:
		Config[x[0]] = x[1]
	
loadGlobalVars()
assets = set();
index = 0;
print("Scan or type the serial numbers now. Return a blank line when finished")
while True:
    line = sys.stdin.readline();
    if line == '\n':
        break
    else:
        assets.add(line.rstrip() + ".txt");



workbook = genXML(len(assets));

for x in assets:
	try:
		logpath = getLogPath(x)
		addServer(workbook,logpath, index);
		index += 1;	
		
	except Exception:
		print(traceback.print_exc());
		print("Failed at S/N:"+x)
		

workbook.close()





