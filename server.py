#!/usr/bin/env python

#CS456 Assignment #1 - Server
#Daiyang Wang
#20646168

#Parameters: None
#Purpose: After client initiation, negotiate a transmission port <r_socket> via TCP.
#	  Wait for a message transmission via UDP on <r_socket>.
#	  Once received, reverse the message and send it back to the client. 
#	  The server will shutdown after a specified <runtime>

from socket import *
from threading import Thread
import sys, string, random, signal

NUM_INPUTS = 1

TERMINATE = False

mesgs = {}
# Function check_inputs(args):
# Parameters: 1
# Parameter:
#	$1: <args> - all command line arguments minus script name
def Check_Inputs(args):
	if len(args) != NUM_INPUTS:
		print("Improper number of arguments")
		exit(1)

	try:
		req_code = int(args[0])

	except:
		print("Improper formatting of argument", args)
		exit(1)

	return

#Create_TCP(sockType):
#Returns a socket on the first random port available (> 1024)
def Create_Socket(sockType):
	testSocket = socket(AF_INET, sockType)
	testSocket.bind(('', 0))		#Choose a free port
	return testSocket			#Return the socket


def on_new_client(connectionSocket, addr, req_code):
	global mesgs
	initiate = connectionSocket.recv(1024)
	if int(initiate) == req_code:  # Validate request code
		r_socket = Create_Socket(SOCK_DGRAM)  # create udp

		connectionSocket.send(str(r_socket.getsockname()[1])) #TODO send port num #send port to client for udp connection

		# r_socket.sendto(mesgs, addr) # TODO print list

		# get all message
		for meg in mesgs:
			r_socket.sendto(mesgs, addr) #TODO send message

		mesg = connectionSocket.recv(1024) # once all recieved
		if str(mesg) == "TERMINATE":
			global TERMINATE
			TERMINATE = True
		else:
			port_number = r_socket.getsockname()[1]
			mesgs[port_number] = str(mesg) #TODO server side udp name or ?

	else:
		connectionSocket.send("0") # client should terminate

#tcpNegotiation():
#Waits for an initiation from the client on <n_socket> via the sending of a predefined request code, <42>.
#Once initialized, a socket is chosen at random for the transaction to be completed. This socket is sent back to the client. 
#Returns: r_socket
def tcpInitiation(n_socket, req_code):
	n_socket.listen(1)
	waiting = 1
	list_sock = []
	while waiting:
		connectionSocket, addr = n_socket.accept()
		initiate = connectionSocket.recv(1024).decode()
		if int(initiate) == int(req_code):  # Validate request code
			r_socket = Create_Socket(SOCK_DGRAM)  # create udp

			connectionSocket.send(str(r_socket.getsockname()[1]).encode())
		else:
			connectionSocket.send("0")  # client should terminate
	# t = Thread(target=on_new_client, args=(connectionSocket, addr, req_code, ))
	#
	# 	t.start()
	# 	t.join()
		global TERMINATE
		if TERMINATE:
			connectionSocket.close()
			exit(0)

	return r_socket



#udpTransaction(r_socket):
#Listens on <r_socket> for a message transmission from the client. 
#Once received, the message is reversed and send back to the client.

def udpTransaction(r_socket):
	while(1):
		message, clientAddress = r_socket.recvfrom(2048)
                if message == "SEND":
                        print("SEND")
                        r_socket.sendto(message, clientAddress)  #TODO must have no msg. before terminate or send message
                        r_socket.sendto("NO MSG.​", clientAddress)  #TODO must have no msg. before terminate or send message

			for meg in mesgs:
				r_socket.sendto(meg, clientAddress) #TODO send message (???)
			r_socket.sendto("NO MSG.​", clientAddress)  #TODO must have no msg. before terminate or send message
		if str(message) == "TERMINATE":
			r_socket.close()
			global TERMINATE
			TERMINATE = True
		else:
			mesgs[clientAddress] = str(message) #TODO server side udp name or


#Shutdown(sigId, frameID):
#Shuts the server down when a signal is triggers. The parameters are not used.

	
#Main
def main():
	req_code = sys.argv[1]
	tcp_socket = Create_Socket(SOCK_STREAM)
	serverUDPHost, neg_port = tcp_socket.getsockname() # print TCP server port

	print ("SERVER_PORT =", str(neg_port))

	while True:
		r_socket = tcpInitiation(tcp_socket, req_code) 			#Wait for initiation
		t = Thread(target=udpTransaction, args=(r_socket, ))	#Complete transaction
		t.start()
		t.join()
main()
