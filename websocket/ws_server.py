import socket
import thread
import websocket
import time
import hashlib
import base64
import select
import sys
import re
from websocket.PacketHandler import Packet

class wsClient(object):
	s = None
	address = None
	handshake = None
	key = None
	magickey = None
	stillRecv = False
	ready = False
	packet = None
	send_packet = None
	appPage = None
	server = None

	def __init__(self,server,arg):
		self.s = arg[0]
		self.address = arg[1]
		self.server = server
		self.ready = True

	def fileno(self):
		return self.s.fileno()
	def genKey(self):
		hash = hashlib.sha1(self.key.rstrip() + websocket.MagicKey)
		self.magickey = base64.standard_b64encode(hash.digest())

	def addCommand(self,cmd,*args):
		if self.send_packet is None:
			self.send_packet = Packet(self)
		self.send_packet.addCommand(cmd,*args)
		try:
			self.server.toSend.index(self)
		except:
			self.server.toSend.append(self)
		


class Server(object):
	"""Hosts a websocket server"""

	logCommands = False

	s = None
	ip = None
	port = None
	acceptThread = None
	packetHandler = None
	parent = None
	connections = []
	toSend = []

	onConnect = []
	onDisconnect = []
	onRecieve = []

	def __init__(self,ip,port):

		self.ip = ip
		self.port = port

		self.packetHandler = websocket.PacketHandler.PacketHandler(self)

	def acceptConnections(self):
		try:
			c = self.s.accept()
			
			if c is not None:
				client = wsClient(self,c)
				c[0].setblocking(False)
				self.connections.append(client)
				for f in self.onConnect:
					f(client)
		except socket.error as e:
			pass

	def getData(self):
		for usr in self.connections:
			try:				
				self.packetHandler.handleData(usr)
			except socket.error:
				pass


	def startServer(self):
		self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)		
		self.s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		print self.s.fileno()
		self.s.bind((self.ip,self.port))
		self.s.setblocking(False)
		print "Server started"
		self.s.listen(20)
		while True:

			readable,writable = select.select([self.s]+self.connections,self.toSend,[])[:2]

			for r in readable:
				print(isinstance(r,socket.socket))
				if isinstance(r,socket.socket):
					self.acceptConnections()
				elif isinstance(r,wsClient):					
					self.packetHandler.handleData(r)
			for w in writable:
				self.packetHandler.sendData(w)
			#time.sleep(0.5)
	
	def clientDisconnect(self, packet):
		print "{} Disconnected".format(packet.usr.address[0])
		id = self.connections.index(packet.usr)
		packet.usr.s.close()
		try:
			self.toSend.index(packet.usr)
			self.toSend.pop(packet.usr)
			
		except Exception as e:
			pass
		packet.usr.ready = False
		self.connections.pop(id)
		
	def n_setAppPage(self,usr,page):
		if isinstance(page,str):
			pObj = getattr(websocket,page)
			if pObj is not None:
				usr.appPage = pObj(usr);
	def close(self):		
		self.s.shutdown(1)
		self.s.close()



