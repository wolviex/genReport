import curses, curses.ascii, curses.textpad
import locale
import sqlite3
import sys
import array;

class SQLGui:

	SQL_Path = ""
	CustomText = ""
	SQLData = None
	screen = None
	infoField = None
	selectedField = [0,0]
	newMode = False
	editMode = False
	pauseMode = False
	deleteMode = False
	currentScroll = [0,0]

	def __init__2(self,SQLPath):
		global SQL_Path

		SQL_Path = SQLPath
		longestStr,names,data = self.SQLGetData()
		print("%d %d" % (len(longestStr),len(names)))


	def __init__(self,SQLPath):
		self.SQL_Path = SQLPath
		self.screen = curses.initscr();
		curses.cbreak()
		curses.noecho();
		self.screen.keypad(1)
		
		self.screen.refresh()
		self.SQLData = self.SQLGetData()
		self.createTable()
		self.createInfoField()
		try:
			self.ListenForKey()
		except KeyboardInterrupt:
			sys.exit()

	def ListenForKey(self):
		
		while True:
			if not self.pauseMode:
				c = self.screen.getch()
				if curses.keyname(c) == "KEY_DOWN":
					self.moveYCursor(1)
				elif curses.keyname(c) == "KEY_UP":
					self.moveYCursor(-1)
				elif curses.keyname(c) == "KEY_RIGHT":
					self.moveXCursor(1)
				elif curses.keyname(c) == "KEY_LEFT":
					self.moveXCursor(-1)

				if c == curses.KEY_ENTER or c == 10 or c == 13:
					if not self.editMode:
						self.editMode = True
					else:
						self.editMode = False

			if c == 330: #Delete key
				self.pauseMode = True
				self.deleteMode = True
			
			if c == 14:
				self.newMode = True

			self.createTable()
			self.createInfoField()
			


	def SQLGetTableNames(self):
		
		connection = sqlite3.connect(self.SQL_Path)
		cursor = connection.execute('SELECT * FROM harddrives')
		names = [description[0] for description in cursor.description]
		connection.close()
		return names

	def SQLSaveChanges(self,model,tableName,data):
		connection = sqlite3.connect(self.SQL_Path)
		cursor = connection.execute('UPDATE harddrives SET {}="{}" WHERE model="{}"'.format(tableName,data,model))
		connection.commit()
		connection.close()

	def SQLCreateRow(self,data):
		connection = sqlite3.connect(self.SQL_Path)
		cursor = connection.execute('INSERT INTO harddrives VALUES({})'.format(",".join(data)))
		connection.commit()
		connection.close()

	def SQLDeleteRow(self,model):
		connection = sqlite3.connect(self.SQL_Path)
		cursor = connection.execute('DELETE FROM harddrives WHERE model="{}"'.format(model))
		connection.commit()
		connection.close()

	def SQLGetData(self):
		

		
		connection = sqlite3.connect(self.SQL_Path)
		cursor = connection.execute('SELECT * FROM harddrives')
		HDData = cursor.fetchall()
		names = [description[0] for description in cursor.description]
		longestStr = [0 for description in cursor.description]

		for row in HDData:
			for i in range(0,len(row)):
				if len(row[i]) > longestStr[i]:
					longestStr[i] = len(row[i])+2
				
		connection.close()
		return longestStr,names,HDData

	def createInfoField(self):

		longestStr,names,data = self.SQLData
		y,x = self.selectedField
		border = curses.newwin(2,self.screen.getmaxyx()[1]-1,self.screen.getmaxyx()[0]-2,0)
		border.hline(0,0, curses.ascii.ascii("_"),self.screen.getmaxyx()[1])
		border.vline(0,0,curses.ascii.ascii("|"),2)
		border.refresh()
		self.infoField = curses.newwin(1,30,self.screen.getmaxyx()[0]-1,1)
		if self.editMode:
			self.infoField.addstr(0,0,data[y][x])
			tb = curses.textpad.Textbox(self.infoField)
			editText = tb.edit()
			

			if editText.rstrip() != data[y][x]:
				invalidSel = False
				while True:
					if invalidSel:
						border.addstr(1,len(editText)+3, "Invalid selection. Would you like to save changes? (y/n)")
					else:
						border.addstr(1,len(editText)+3, "Would you like to save changes? (y/n)")
					border.refresh()
					c = self.screen.getch()
					if curses.keyname(c).lower() == "y":
						modelIndex = names.index("model")
						self.SQLSaveChanges(data[y][modelIndex],names[x],editText.rstrip())
						self.SQLData = self.SQLGetData()
						self.editMode = False
						self.createTable()
						self.createInfoField()
						break
					elif curses.keyname(c).lower() == "n" or c == 27:

						self.editMode = False
						self.createTable()
						self.createInfoField()
						break
					else:
						invalidSel = True
			else:
				self.editMode = False
				self.createTable()
				self.createInfoField()
		
		elif self.deleteMode:
			invalidSel = False
			while True:
				if invalidSel:
					border.addstr(1,1,"Invalid selection. Do you want to delete the data for {}? (y/n)".format(data[y][names.index("model")]))
				else:
					border.addstr(1,1,"Do you want to delete the data for {}? (y/n)".format(data[y][names.index("model")]))
				border.refresh()
				c = self.screen.getch()
				if curses.keyname(c).lower() == "y":
					self.SQLDeleteRow(data[y][names.index("model")])
					self.pauseMode = False
					self.deleteMode = False
					self.SQLData = self.SQLGetData()
					self.createTable()
					self.createInfoField()
					break
				elif curses.keyname(c).lower() == "n":
					self.pauseMode = False
					self.deleteMode = False
					self.createTable()
					self.createInfoField()
					break
				else:
					invalidSel = True
		elif self.newMode:
			invalidSel = False
			dataFields = []
			for i in range(0,len(names)):
				newStr = "{}:".format(names[i])
				border.addstr(1,1,newStr)
				self.infoField.clear()
				self.infoField.mvwin(self.screen.getmaxyx()[0]-1,1+len(newStr))
				border.refresh()
				self.infoField.refresh()
				tb = curses.textpad.Textbox(self.infoField)
				info = tb.edit()
				info = info.rstrip()
				if info == "":
					info = "None"
				info = '"{}"'.format(info)
				dataFields.append(info)
			while True:
				if not invalidSel:
					border.addstr(1,1,"Are you sure you want to add model: {}? (y/n)".format(dataFields[names.index("model")]))
				else:
					border.addstr(1,1,"Invalid selection. Are you sure you want to add model: {}? (y/n)".format(dataFields[names.index("model")]))
				border.refresh()
				c = self.screen.getch()
				if curses.keyname(c).lower() == "y":
					self.SQLCreateRow(dataFields)
					self.SQLData = self.SQLGetData()
					self.newMode = False
					self.createTable()
					self.createInfoField()
					break
				elif curses.keyname(c).lower() == "n":
					self.newMode = False
					self.createTable()
					self.createInfoField()
					break
				else:
					invalidSel = True

		else:
			border.addstr(1,1,"Press enter to edit field")
			

		self.infoField.refresh()
		border.refresh()

		
		

	def createTable(self):

		try:
			totalWidth = 0
			totalHeight = 0

			longestStr,names,data = self.SQLData



			for i in range(0,len(longestStr)):
				if longestStr[i] < len(names[i]):
					longestStr[i] = len(names[i]) + 2
				totalWidth += longestStr[i]

				
			totalHeight = len(data) + 4

			if totalHeight < self.screen.getmaxyx()[0]:
				totalHeight = self.screen.getmaxyx()[0]

			mypad = curses.newpad(totalHeight+1,totalWidth+1)
			mypad.hline(1, 0, curses.ascii.ascii("-"), totalWidth)

			currLength = 0
			mypad.vline(0,currLength, curses.ascii.ascii("|"),totalHeight)
			for i in range(0,len(names)):
				currLength += longestStr[i]
				mypad.addstr(0,self.getMidPos(currLength,longestStr[i],names[i]),names[i])
				mypad.vline(0,currLength, curses.ascii.ascii("|"),totalHeight)
			self.populateTable(mypad)
			mypad.refresh(self.currentScroll[0],self.currentScroll[1],0,0,self.screen.getmaxyx()[0]-1,self.screen.getmaxyx()[1]-1)
		except Exception as e:
			curses.endwin()
			print(str(currLength) + " " +str(self.screen.getmaxyx()[1]))
			print(e)
	
	def moveXCursor(self, direction):
		longestStr,names,data = self.SQLData
		
		self.selectedField[1] += direction

		if self.selectedField[1] > len(data[self.selectedField[0]])-1:
			self.selectedField[1] = len(data[self.selectedField[0]])-1
		if self.selectedField[1] < 0:
			self.selectedField[1] = 0
		
		currLength = 0

		for i in range(0,self.selectedField[1]):
			currLength += longestStr[i]
		xScroll = self.currentScroll[1]
		if direction > 0:
			if currLength + len(data[self.selectedField[0]][self.selectedField[1]]) > self.screen.getmaxyx()[1]+self.currentScroll[1]:
				#xScroll = (currLength + len(data[self.selectedField[0]][self.selectedField[1]])) - self.screen.getmaxyx()[1]
				xScroll = (currLength + longestStr[self.selectedField[1]]) - self.screen.getmaxyx()[1]
			if xScroll < 0:
				xScroll = 0	
			#else:
			#	xScroll = (currLength + longestStr[self.selectedField[1]]) - self.screen.getmaxyx()[1]
			self.currentScroll[1] = xScroll
		else:
			if currLength < self.currentScroll[1]:
				self.currentScroll[1] = currLength

	def moveYCursor(self, direction):
		longestStr,names,data = self.SQLData
		
		self.selectedField[0] += direction

		if self.selectedField[0] > len(data)-1:
			self.selectedField[0] = len(data)-1
		if self.selectedField[0] < 0:
			self.selectedField[0] = 0
		
		currLength = 0
		yScroll = self.currentScroll[0]
		if direction > 0:
			if self.selectedField[0]+3 > (self.screen.getmaxyx()[0]-2)+self.currentScroll[0]:
				yScroll = (self.selectedField[0]+3) - (self.screen.getmaxyx()[0]-2) #Correcting for InfoEdit bar and the column names
			if yScroll < 0:
				yScroll = 0
		else:
			if (self.selectedField[0]+2) < self.currentScroll[0]:
				yScroll = (self.selectedField[0]+2)
			if self.selectedField[0] == 0:
				yScroll = 0
		self.currentScroll[0] = yScroll

		

	def populateTable(self, pad):

		longestStr,names,data = self.SQLData
		
		for i in range(0,len(data)):
			currLength = 0
			for i2 in range(0,len(data[i])):
				if i == self.selectedField[0] and i2 == self.selectedField[1]:
					pad.addstr(2+i,1+currLength,data[i][i2],curses.A_REVERSE)		
				else:
					pad.addstr(2+i,1+currLength,data[i][i2])
				
				currLength += longestStr[i2]

	def getMidPos(self,currLength, longestStr, name):
		x = currLength - (currLength-longestStr)
		midpos = (x/2) - (len(name)/2)
		return (currLength-longestStr) + midpos;