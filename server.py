#!/usr/bin/env python3

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
import sys, string, random, signal, json, collections

NUM_INPUTS = 1

TERMINATE = False

mesgs = collections.OrderedDict()
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
    # host = gethostname()
    # testSocket.setsockopt(SOL_SOCKET,SO_REUSEADDR,1)
    # testSocket.bind((str(gethostbyname(host)), int(testSocket.getsockname()[1])))		#Choose a free port
    testSocket.bind(('',0)) #CHoose a free port
    return testSocket			#Return the socket



#tcpNegotiation():
#Waits for an initiation from the client on <n_socket> via the sending of a predefined request code, <42>.
#Once initialized, a socket is chosen at random for the transaction to be completed. This socket is sent back to the client. 
#Returns: r_socket
def tcpInitiation(n_socket, req_code):
	n_socket.listen(5)
	waiting = 1
	list_sock = []
	while waiting:
		connectionSocket, addr = n_socket.accept()
		initiate = connectionSocket.recv(1024).decode()
		if int(initiate) == int(req_code):  # Validate request code
			r_socket = Create_Socket(SOCK_DGRAM)  # create udp

			connectionSocket.send(str(r_socket.getsockname()[1]).encode())
			return r_socket
		else:
			connectionSocket.send("0".encode())  # client should terminate
			connectionSocket.close()
			return 0




#udpTransaction(r_socket):
#Listens on <r_socket> for a message transmission from the client. 
#Once received, the message is reversed and send back to the client.

def udpTransaction(r_socket):
	global TERMINATE
	while(1):
		message, clientAddress = r_socket.recvfrom(2048)
		message = message.decode()

		if message == "GET":

			#send dictionary(recent message) to client
			encap_mesgs = json.dumps(mesgs).encode('utf-8')
			r_socket.sendto(encap_mesgs, clientAddress)
			r_socket.sendto("NO MSG.​".encode(), clientAddress)
		elif message == "TERMINATE":
			r_socket.close()
			TERMINATE = True
			return
		else:
			mesgs[clientAddress[1]] = str(message) # add to dictionary
			return

#Shutdown(sigId, frameID):
#Shuts the server down when a signal is triggers. The parameters are not used.

	
#Main
def main():
    if len(sys.argv) == 2:
        req_code = sys.argv[1]
        tcp_socket = Create_Socket(SOCK_STREAM)
        serverUDPHost, neg_port = tcp_socket.getsockname() # print TCP server port

        print ("SERVER_PORT =", str(neg_port))
        global TERMINATE

        while True:
            # tcp_socket = Create_Socket(SOCK_STREAM)
                # serverUDPHost, neg_port = tcp_socket.getsockname()  # print TCP server port
                # print("SERVER_PORT =", str(neg_port))

                if TERMINATE:
                    exit(0)
                r_socket = tcpInitiation(tcp_socket, req_code) 			#Wait for initiation
                if r_socket == 0:
                    continue
                t = Thread(target=udpTransaction, args=(r_socket, ))	#Complete transaction
                t.start()
                t.join()
                # udpTransaction(r_socket)
    else:
        print("Error: incorrecr parameters. <req_code> are required")
        quit()
main()
