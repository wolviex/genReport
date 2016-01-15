from websocket import HTML5App
from websocket.PacketHandler import Packet
import prices
import jwtools
import numpy as np
class serverBuilder(HTML5App):

	itemList = None
	modelList = None
	attrib = {}
	usr = None

	def __init__(self,usr):
		self.usr = usr
		self.modelList = prices.getModelList()
		self.itemList = prices.getItemList()
		
		self.updateList()
		self.setAttribs()


	def updateList(self):
		li = jwtools.filterArray(self.itemList,"Description","Type","Internal")
		descIndex = np.where(li[0]=="Description")[0][0]
		typeIndex = np.where(li[0]=="Type")[0][0]
		codeIndex = np.where(li[0]=="Internal")[0][0]
		if self.usr is not None:
			self.usr.addCommand("updateNetElems","select",li,descIndex,typeIndex,codeIndex)

	def setAttribs(self):
		li = [[self.modelList[k]["Description"].encode("utf-8"),k.encode("utf-8")] for k,v in self.modelList.items()]
		self.usr.addCommand("updateNetElem","Model",li)

	def n_sbSelUpdate(self,usr,selected):
		sellIndex = np.where(self.itemList[0] == "Sell")[0][0]
		sell = 0
		d = np.array(selected)
		for i in range(len(selected)):
			try:
				idx = np.where(self.itemList==selected[i])[0][0]
				sell += float(self.itemList[idx][sellIndex])
			except:
				pass

		print "Total sell price {}".format(sell)
		self.usr.addCommand("updateNetElem","sQuote",sell)
					

		