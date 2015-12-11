import websocket
import socket
import binascii
import re
global curPacketHandler

class Packet(object):
	length = 0
	l_bytes = 0
	mask = 0
	mask_key = ""
	encoded = ""
	decoded = ""
	opcode = 0
	fin = 0
	handler = None
	usr = None

	def newPacket(self):
		self.opcode = 1
		self.fin = 1
		self.mask = 1
		self.mask_key = "jwat"

	def __init__(self,usr,encoded=""):
		
		global curPacketHandler

		self.handler = curPacketHandler
		self.usr = usr

		if len(encoded) <= 0:
			self.newPacket()
			print "Creating new packet"
			return
		
		self.length,self.l_bytes = self.getPacketLength(encoded)
		
		
		self.encoded = encoded
		self.mask_key = encoded[2+self.l_bytes:6+self.l_bytes]
		self.mask = ord(encoded[1]) & 0x80
		self.opcode = ord(encoded[0]) & ((1<<4)-1)
		self.fin = ord(encoded[0]) & 0x80
		
		print "Packet initialized. Length: {}".format(self.length)

	def update(self):
		
		if self.length + 4 + self.l_bytes <= len(self.encoded):
			pos = 2 + self.l_bytes
			m = self.mask_key
			msg = ""
			
			for i in range(self.length):
				msg += chr(ord(self.encoded[pos+4+i]) ^ ord(m[i % 4]))
			if len(msg) > 0:
				self.decoded = msg
				self.handler.server.recievePacket(self)
			self.usr.packet = None

	def encode(self):
		self.encoded = ""
		self.encoded += chr((self.fin<<7)|self.opcode)

		self.length = len(self.decoded)
		l = self.length
		if self.length >= 126 and self.length <= 65535:
			l = 126
			self.encoded += chr(l)
			self.encoded += chr((self.length & (((1<<8)-1)<<8)) >> 8)
			self.encoded += chr((self.length & (((1<<8)-1)<<0)) >> 0)
		elif self.length > 65535:
			l = 127
			self.encoded += chr(l)
			self.encoded += chr((self.length & (((1<<8)-1)<<56)) >> 56)
			self.encoded += chr((self.length & (((1<<8)-1)<<48)) >> 48)
			self.encoded += chr((self.length & (((1<<8)-1)<<40)) >> 40)
			self.encoded += chr((self.length & (((1<<8)-1)<<32)) >> 32)
			self.encoded += chr((self.length & (((1<<8)-1)<<24)) >> 24)
			self.encoded += chr((self.length & (((1<<8)-1)<<16)) >> 16)
			self.encoded += chr((self.length & (((1<<8)-1)<<8)) >> 8)
			self.encoded += chr((self.length & (((1<<8)-1)<<0)) >> 0)
		else:
			self.encoded += chr(l)
		
		self.encoded += self.decoded
		


	def getPacketLength(self,data):

		

		length = ord(data[1]) & 0x7f
		bytes = 0
		l = length
		if length == 126:
			l = int(binascii.hexlify(data[2:4]),16)	
			bytes = 2
		elif length == 127:
			l = int(binascii.hexlify(data[2:6]),16)	
			bytes = 4
		return l,bytes



class PacketHandler(object):

	server = None

	def __init__(self,server):
		global curPacketHandler
		curPacketHandler = self
		self.server = server

	def handleData(self,usr):
		try:
			data = usr.s.recv(4096)
			
			if not usr.handshake:
				self.tryHandshake(usr,data)
			else:
				
				if len(data) > 0:
					if usr.packet is None:
						usr.packet = Packet(usr,data)
						
					else:
						usr.packet.encoded += data

					usr.packet.update()
		except socket.error:
			pass

	def sendData(self,usr):
		if usr.send_packet is not None:
			usr.send_packet.encode()
			usr.s.sendall(usr.send_packet.encoded)
			usr.send_packet = None

		
		

	def tryHandshake(self,usr,data):
		rekey = re.search(r"Sec-WebSocket-Key: (.*)",data)
		key = ""
		if rekey is not None:
			key = rekey.group(1)
			usr.key = key
			usr.genKey()
			hs = websocket.handshake.format(usr.magickey)
			try:
				usr.s.sendall(hs)
			except Exception as e:
				print "tryHandshake Error: {}".format(e)
			print usr.magickey
			usr.handshake = True

	

	def update(self):
		for usr in self.server.connections:
			self.handleData(usr)
			self.sendData(usr)
