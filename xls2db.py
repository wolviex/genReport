import inspect
import sys
import os
import sqlite3
import xlrd
import xlwt
import jwargs

exitFlag = False

def default(argName):

	if os.path.isfile(argName):
		xlsList.append(argName)

#Functions starting with m_ are callable from the commandline arguments.
#To call a function from the command line, it must begin with -
#It will get the number of arguments in a function automatically
#I.E: python xls2db.py -foo bar1 bar2 will call m_foo(bar1, bar2) if it exists
#If it doesn't exist, or if it doesn't have a -, it will call default(argument)
#~Jesse Watson


#Creates a spreadsheet from a database file. dbname is the database file and filename is the xls file to be generated
def m_r(dbname, filename):

	global exitFlag

	db = sqlite3.connect(dbname)
	c = db.cursor()
	query = "SELECT name FROM sqlite_master WHERE type = 'table'"
	c.execute(query)
	db.commit()
	tables = c.fetchone()
	c.close()
	for t in tables:
		query = "SELECT * FROM {}".format(t)
		cursor = db.cursor()
		cursor.execute(query)
		db.commit()
		rows = cursor.fetchall()
		cursor.close()
		names = [description[0] for description in cursor.description]
		data = []
		data.append(tuple(names))
		for row in rows:
			data.append(row)
		
	genXLS(data,filename)
	exitFlag = True


def m_dbname(name):
	global databaseName
	databaseName = name

def m_table(name):
	global tableName
	tableName = name

def hasDBTable(db,table):
	c = db.cursor();
	c.execute("SELECT count(*) FROM sqlite_master WHERE type = 'table' AND name = '{}'".format(table))
	if c.fetchone()[0] == 1:
		return True;	
	return False;

def createTable(db,table,colNames):
	colString = " text,".join(colNames)
	colString += " text"
	c = db.cursor();
	c.execute("CREATE TABLE '{}' ({})".format(table,colString))
	db.commit()

def getColWidths(data):
	colWidths = [0 for x in data[0]]
	for i in range(0,len(data)):
		for x in range(0,len(data[i])):
			if len(data[i][x]) > colWidths[x]:
				colWidths[x] = len(data[i][x])
	return colWidths

def genXLS(data,filename):

	global databaseName

	workbook = xlwt.Workbook()
	sheet = workbook.add_sheet("Database")
	colWidths = getColWidths(data)
	for y in range(0,len(colWidths)):
		sheet.col(y).width = (colWidths[y]) * 256

	for i in range(0,len(data)):
		headerStyle = xlwt.Style.easyxf("font: bold off")
		if i == 0:
			headerStyle = xlwt.Style.easyxf("font: bold on; align: wrap on, vert centre, horiz center")
			

		for x in range(0,len(data[i])):
				sheet.write(i,x,data[i][x],headerStyle)
	workbook.save(filename)
	print "Saved database as {}".format(filename)

def importXLS():
	global databaseName
	global tableName
	for path in xlsList:
		try:
			db_name = databaseName
			print db_name
			if db_name == "":
				db_name = "{}.db".format(os.path.splitext(path)[0])
			db = sqlite3.connect(db_name)
			c = db.cursor()
			workbook = xlrd.open_workbook(path)
			sheet = workbook.sheet_by_index(0)
			colCount = 0
			colNames = [sheet.cell(0,i).value for i in range(0,sheet.ncols)]

			if tableName == "":
				tableName = sheet.name
			
			

			if not hasDBTable(db,tableName):
				createTable(db,tableName,colNames)

			for y in range(1,sheet.nrows):
				rowData = ["'{}'".format(sheet.cell(y,x).value) for x in range(0,sheet.ncols)]
				queryString = ", ".join(rowData);
				query = "INSERT INTO {} VALUES ({})".format(tableName,queryString)
				try:
					c.execute(query);
				except Exception as e:

					print query

			db.commit()
			db.close()
				


			
			

		except xlrd.XLRDError as e:
			print "{}: {}".format(path, e.message)


xlsList = []
databaseName = ""
tableName = ""
jwargs.getArgs()
if exitFlag:
	sys.exit(0)

importXLS()
