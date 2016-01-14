import websocket
import prices
import jwtools
import numpy as np
import json
import os
import sys
import socket

def onConnect(usr):
	print "{} Connected".format(usr.address)
	
	



def onData(packet):
	pass

def onDisconnected(packet):
	global server
	print "Num clients: {}".format(len(server.connections))


def cmd_getEbayListings(packet):
	print "Sending ebay list"

	sendPacket = websocket.PacketHandler.Packet(packet.usr)
	sendPacket.decoded = "/updateEbayList {}".format(jwtools.mJoin("\n","\r",ebayTools.getAllListings()))
	packet.usr.send_packet = sendPacket

def cmd_getItemList(packet):
	print "Sending Component list to {}".format(packet.usr.address[0])
	sendPacket = websocket.PacketHandler.Packet(packet.usr)
	sendPacket.decoded = "/recvItemList {}".format(prices.getItemList())
	packet.usr.send_packet = sendPacket

server = websocket.Server("10.0.2.15",9999)

server.onConnect.append(onConnect)
server.onRecieve.append(onData)
server.onDisconnect.append(onDisconnected)
server.parent = sys.modules[__name__]


try:
	server.startServer()
except (socket.error, KeyboardInterrupt) as e:
	print e
	exc_type, exc_obj, exc_tb = sys.exc_info()
	fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
	print(exc_type, fname, exc_tb.tb_lineno)
	server.close()