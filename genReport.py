import xlsxwriter
import re
import xlrd
import sys
import array;
import time;
import os;
from ftplib import FTP

import traceback;

from sql_ui import SQLGui
import DLogReader as LogReader

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
	workbook = xlsxwriter.Workbook(LogReader.Config["XLPath"])
	worksheet = workbook.add_worksheet();
	formatXML(workbook,worksheet,rnum);
	return workbook;
	
def genInfo(fname):
	ret = LogReader.getProcInfo(fname) + ",\n"
	ret += LogReader.getTotalRam(fname) + ",\n"
	ret += LogReader.getCtlr(fname) + ",\n"
	ret += LogReader.getHarddrives(fname);
	
	return ret;
	
def addServer(workbook, fname, index):

	serial = LogReader.getSerial(fname);
	index += 1;
	worksheet = workbook.worksheets()[0];
	worksheet.write(index,0, serial);
	worksheet.write(index,1, LogReader.getAsset(serial));
	worksheet.write(index,2, LogReader.getModel(fname));
	worksheet.write(index,3, genInfo(fname));
	worksheet.write(index,5, LogReader.getFails(fname));



def makeSQLGui():
	scrn = SQLGui(LogReader.Config["DBPath"])
	
assets = set();



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



workbook = genXML(len(assets));

for x in assets:
	try:
		logpath = LogReader.getLogPath(x)

		if logpath is None:
			print("Error: {} not found.".format(x))
			continue
		
		addServer(workbook,logpath, index);
		index += 1;	
		
	except Exception:
		print(traceback.print_exc());
		print("Failed at S/N:"+x)
		

workbook.close()





