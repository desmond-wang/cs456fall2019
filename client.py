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
import sys, string, json, termios, tty, collections


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
            print("Connection refused: please ensure the server is running")
            quit()

        # sending request code
        TCPSocket.send(str(req_code).encode())
        r_port = int(TCPSocket.recv(1024).decode())


        if r_port == 0:
            print("Invalid req_code.")
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
	UDPSocket.sendto("GET".encode(), (server_address, r_port))
	while(1):
		Message, serverAddress = UDPSocket.recvfrom(2048)

		if str(Message.decode()) == "NO MSG.​":
			print(Message.decode())
			break
		else:
			message_decode = json.loads(Message.decode('utf-8'), object_pairs_hook=collections.OrderedDict)
			for key, val in message_decode.items():
				print("[" + key + "]: " + val) #  dictionary format
	UDPSocket.sendto(msg.encode(), (server_address, r_port))

	stdinFileDesc = sys.stdin.fileno()  # store stdin's file descriptor
	oldStdinTtyAttr = termios.tcgetattr(stdinFileDesc)  # save stdin's tty attributes so I can reset it later
	try:
		print()
		print('Press any key to exit.')
		tty.setraw(
			stdinFileDesc)  # set the input mode of stdin so that it gets added to char by char rather than line by line
		sys.stdin.read(1)  # read 1 byte from stdin (indicating that a key has been pressed)
	finally:
		termios.tcsetattr(stdinFileDesc, termios.TCSADRAIN, oldStdinTtyAttr)  # reset stdin to its normal behavior
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
		print("Error: incorrect parameters. <server_address> <n_port> <req_code> and <msg> are required")
		quit()

main()
