import xlsxwriter
import re
import xlrd
import xlwt;
import sys
import array;
import time;
import os;
import signal
import curses
import datetime
from collections import Counter
from ftplib import FTP

import traceback;

from sql_ui import SQLGui
import DLogReader as LogReader

serverList = []
masterServerList = []

def formatXML(workbook, worksheet,rnum):
	
	headerStyle = xlwt.Style.easyxf("font: bold on; align: wrap on, vert centre, horiz center")
	worksheet.col(0).width = 15 * 256
	worksheet.col(1).width = 15 * 256
	worksheet.col(2).width = 15 * 256
	worksheet.col(3).width = 50 * 256
	worksheet.col(4).width = 40 * 256
	worksheet.col(5).width = 50 * 256
	worksheet.row(0).height = 20 * 256
	worksheet.write(0,0, "Service Tag",headerStyle);
	worksheet.write(0,1, "Asset",headerStyle);
	worksheet.write(0,2, "Model",headerStyle);
	worksheet.write(0,3, "Specs",headerStyle);
	worksheet.write(0,4, "Notes",headerStyle);
	worksheet.write(0,5, "Fails",headerStyle);
	
	return


def setColWidth(worksheet, colFrom, colTo, width):
	for i in range(colFrom, colTo):
		worksheet.col(i).width = width * 256

def formatXML2(workbook,worksheet,rnum):
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
	worksheet.write(0,4, "Fails");
	worksheet.write(0,5, "Notes");
	
	return;
	
def genXML(rnum):
	workbook = xlwt.Workbook()
	worksheet = workbook.add_sheet("Servers");
	formatXML(workbook,worksheet,rnum);
	return workbook, worksheet;
	

	
def addServer(worksheet, fname, index):

	global serverList

	serial = LogReader.getSerial(fname);
	index += 1;

	serverList.append((serial,LogReader.getAsset(serial),LogReader.getModel(fname),LogReader.genInfo(fname),LogReader.getFails(fname)))

	#worksheet.write(index,0, serial);
	#worksheet.write(index,1, LogReader.getAsset(serial));
	#worksheet.write(index,2, LogReader.getModel(fname));
	#worksheet.write(index,3, LogReader.genInfo(fname),fontSize);
	#worksheet.write(index,5, LogReader.getFails(fname)); 

def getInfoFromXML():
	try:
		global masterServerList
		wb = xlrd.open_workbook(LogReader.Config["XLPath"])
		sh = wb.sheet_by_index(0)
		num_rows = sh.nrows
		for x in range(1,num_rows):
			masterServerList.append((sh.cell(x,0).value,sh.cell(x,1).value,sh.cell(x,2).value,sh.cell(x,3).value,sh.cell(x,4).value,sh.cell(x,5).value))
	except Exception:
		return
		


def addInfoToXML(worksheet):
	global serverList, masterServerList
	popList = []
	for info in masterServerList:
		serial = info[0]
		for info2 in serverList:
			if serial == info2[0]:
				masterServerList.pop(masterServerList.index(info))

	list = masterServerList + serverList;
	
	for i in range(1,len(list)+1):
		
		for x in range(0,len(list[i-1])):
			worksheet.write(i,x, list[i-1][x])

def genSingleXML():
	global serverList
	path = os.path.split(LogReader.Config["XLPath"])[0]
	workbook, worksheet = genXML(len(serverList))
	for i in range(1,len(serverList)+1):		
		for x in range(0,len(serverList[i-1])):
			worksheet.write(i,x, serverList[i-1][x])
	saveWorkBook(workbook, "{}/{}.xls".format(path,datetime.datetime.today().strftime("%d-%m-%y")))
		
def saveWorkBook(workbook, path):
	saveIndex = 0
	while True:
		filename, extension = os.path.splitext(path)
		p = filename + extension
		if saveIndex > 0:
			p = "{} ({}){}".format(filename,saveIndex,extension)
		try:
			workbook.save(p)
			print("Saved {}".format(p))
			break
		except Exception:
			pass
		saveIndex += 1

def makeSQLGui():
	
	try:
		scrn = SQLGui(LogReader.Config["DBPath"])
		
	except KeyboardInterrupt:
		curses.endwin()
		sys.exit(0)

	
	
assets = set()



for argc in sys.argv:
	if argc == sys.argv[0]: #Quick hack to stop it from getting the script name
		continue

	if argc == "-?":
		print("Usage: TODO "+argc)
	elif argc == "-sql":
		makeSQLGui()
		
	else:
		if argc.find(".txt") > 0:
			logFile = argc[0:argc.find(".txt")] + ".txt"
		else:
			logFile = argc + ".txt"
		print(logFile)
		assets.add(str(logFile))






index = 0;
if len(assets) <= 0:
	print("Scan or type the serial numbers now. Return a blank line when finished")
	while True:
		line = sys.stdin.readline();
		if line == '\n':
			break
		else:
			assets.add(line.rstrip() + ".txt");



workbook, ws = genXML(len(assets));

for x in assets:
	try:
		logpath = LogReader.getLogPath(x)

		if logpath is None:
			print("Error: {} not found.".format(x))
			continue
		
		addServer(ws,logpath, index);
		index += 1;	
		
	except Exception:
		print(traceback.print_exc());
		print("Failed at S/N:"+x)

getInfoFromXML()	
addInfoToXML(ws)
genSingleXML()
saveWorkBook(workbook,LogReader.Config["XLPath"])








