#!/usr/bin/env python

#CS456 Assignment #1 - Client
#Daiyang Wang
#20646168

#Number of parameters: 4
#Parameter:
#    $1: <server_address>
#    $2: <n_port>
#    $3: <req_code>
#    $4: message
#Purpose: Initiate a TCP connection with the <server_address> at the <n_port> by sending an integer over the socket
#	  Using the port sent back by the server <r_port>, send back the <msg> over a UDP socket
#   	  Receive the message from the server and print it out

from socket import *
import sys, string


NUM_INPUTS = 4


#tcpInitiation(server_address, n_port, req_code):
#Initiates a transaction with the <server_address> via TCP at <n_port> and sending the request code <req_code>.
#The server sends back the port needed for the transaction.
#Returns: r_port
def tcpInitiation(server_address, n_port, req_code):
	# Create client TCP socket
	TCPSocket = socket(AF_INET, SOCK_STREAM)
	try:
		TCPSocket.connect((server_address, n_port))
	except error:
		print("Negotiation port unavailable: please ensure the server is running")
		quit()

	# sending request code
	TCPSocket.send(str(req_code).encode())
	r_port = int(TCPSocket.recv(1024).decode())

	print(r_port)

	if r_port == 0:
		TCPSocket.close()
		exit(0)
	else:
		TCPSocket.close()
		return r_port

#udpTransaction(sever_address, r_port, msg):
#Completes a transaction with the <server_address> via UDP at <r_port> by sending the string, <msg>. The server will
# receive recent messages and send message to server.
#Returns: ReversedString
def udpTransaction(server_address, r_port, msg):
	UDPSocket = socket(AF_INET, SOCK_DGRAM)
	UDPSocket.sendto("SEND".encode(), (server_address, r_port))
	while(1):
		print("HERE") # TODO dictionary format
		Message, serverAddress = UDPSocket.recvfrom(2048)
		if str(Message) == "NO MSG.​":
			break
		else:
			print(Message) # TODO dictionary format
	UDPSocket.sendto(msg, (server_address, r_port))
	UDPSocket.close()

#Main
def main():
	if len(sys.argv) == 5:							#Argument validation
		server_address = sys.argv[1]
		n_port = int(sys.argv[2])
		req_code = int(sys.argv[3])
		msg = sys.argv[4]


		r_port = tcpInitiation(server_address, n_port, req_code)	#Initiate the TCP connection with the server,
		#  receive the r_port
		udpTransaction(server_address, r_port, msg)	#Complete the transaction using UDP, receive the reversed message
	else:
		print("Error: incorrect parameters. <server_address> <n_port> and <msg> are required")
		quit()

main()
