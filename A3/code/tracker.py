#!/usr/bin/env python3

#CS456 Assignment #3 - Tracker
#Daiyang Wang
#20646168

#Parameters: None

from socket import *
from threading import Thread, Lock
import sys, string, random, signal, json, collections

from packet import packet
import time



TERMINATE = False
peer_dict = {}
file_dict = {}

mesgs = collections.OrderedDict()
# Function check_inputs(args):
# Parameters: 0


#Create_TCP:
#Returns a socket on the first random port available (> 1024)
def Create_Socket():
	testSocket = socket(AF_INET, SOCK_STREAM)
	# testSocket.bind((str(gethostbyname(host)), int(testSocket.getsockname()[1])))		#Choose a free port
	testSocket.bind(('',0)) #CHoose a free port
	return testSocket			#Return the socket


#tcpNegotiation():
#Waits for an initiation from the client on <n_socket> via the sending of a predefined request code, <42>.
#Once initialized, a socket is chosen at random for the transaction to be completed. This socket is sent back to the client. 
#Returns: r_socket
def tcpInitiation(n_socket):
	global peer_dict,  file_dict
	# set max number to 30
	n_socket.listen(30)
	waiting = 1
	count = 0
	while waiting:
		# peer socket and addr
		connectionSocket, addr = n_socket.accept()
		# add into multi thread
		t = Thread(target=peerInit, args=(connectionSocket, addr, count, ))
		t.start()
		time.sleep(5)

		count += 1
		if not peer_dict and count != 0:
			break



# init peer with assigning peer number and
def peerInit(connectionSocket, addr, peerNum):
	global peer_dict, file_dict
	# send back to assigned peer number
	# send peer num to peer
	peer_num_pk = packet.create_t_to_p(1, str(peerNum))
	data = packet.get_tcp_data(peer_num_pk)
	connectionSocket.send(data)

	# receive filename from peer
	filename_pk = packet.parse_p2p_data(connectionSocket.recv(1024))

	filename_data = filename_pk.data.split()
	filename = str(filename_data[0])
	# file trunk number
	file_trunk_num = str(filename_data[1])


	# time.sleep(1)

	# receive port number from peer
	port_pk = packet.parse_p2p_data(connectionSocket.recv(1024))
	port_num = int(port_pk.data)

# replace the port to sever peer port
	ip_addrs = addr[0]
	server_addr = (ip_addrs, port_num)

	peer_dict[peerNum] = [connectionSocket, server_addr]
	peerNums = file_dict.get(filename, [])
	peerNums.append(peerNum)
	file_dict[filename] = peerNums

	print("PEER ", peerNum, "CONNECT: OFFERS 1")
	print(peerNum, "    ", filename, " ", file_trunk_num)


	time.sleep(1)
	# once new peer connect, update list
	t = Thread(target=peersBrodcast, args=())
	t.start()

	# listen packet until peer exit
	while True:
		peer_pk = packet.parse_p2p_data(connectionSocket.recv(1024))
		if peer_pk.type == 2:
			if peer_pk.seq_num == 0: # peer want to exit
				# print("here: removing peers") #TODO
				peer_pk = peer_pk.data.split()
				peer_num = int(peer_pk[0])
				peer_file_name = peer_pk[1]
				num_files = peer_pk[2]
				print("PEER",  peer_num, peer_file_name)
				# remove peer from peer dict
				peer_dict.pop(peer_num, None)

				print("PEER ", peer_num, " DISCONNECT: RECEIVED ", num_files)
				for file_name, v in file_dict.items():
					print(peer_num, "    ", file_name)

				if len(peer_dict) == 0:
					# allow peer to exit
					connectionSocket.send(packet.get_tcp_data(packet.create_t_to_p(0, "")))
					return
				peerlist = list(peer_dict.keys())

				file_dict[peer_file_name] = peerlist

				# remove from file dict
				for k, v in file_dict.items():
					try:
						v.remove(str(peer_num))
					except:
						pass
				# allow peer to exit
				connectionSocket.send(packet.get_tcp_data(packet.create_t_to_p(0, "")))
				# update new list to all peers
				t1 = Thread(target=peersBrodcast, args=())
				t1.start()
				# peersBrodcast()
				return


# broadcast to peer
def peersBrodcast():
	# convert dictionary to string ready to send to peers
	peer_dict_str = DicToString(peer_dict)
	file_dict_str = DicToString(file_dict)
	for k,v in peer_dict.items():
		# send peer dictionary: peer_num (ipaddr, portnum)
		connectionSocket = v[0]
		connectionSocket.setsockopt(IPPROTO_TCP, TCP_NODELAY, 1)
		peer_data = packet.get_tcp_data(packet.create_t_to_p(2, peer_dict_str))
		connectionSocket.send(peer_data)
		time.sleep(1)
		# send file dictionary: file_name (peer1, peer2, etc.)
		files_data = packet.get_tcp_data(packet.create_t_to_p(3, file_dict_str))
		connectionSocket.send(files_data)


def DicToString(dic):
	dic_str = ""
	for keys, values in dic.items():
		if (isinstance(keys, int)):
			ip_addr, port_num = values[1]
			dic_str += str(keys) + ": " + str(ip_addr) + " " + str(port_num) + " ;"
		else:
			dic_str += str(keys) + ": "
			for i in values:
				dic_str += str(i) + " "
			dic_str += " ;"
	return dic_str

	
#Main
def main():
	tcp_socket = Create_Socket()
	# get the tcp
	trackerHost, neg_port = tcp_socket.getsockname() # print TCP server port

	# put port number into port.txt files
	port_to_write = open("port.txt", 'w')
	port_to_write.write(str(neg_port))
	port_to_write.close()

	# print("SERVER_PORT =", str(neg_port))

	tcpInitiation(tcp_socket) 			#Wait for initiation



main()
