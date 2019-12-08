#!/usr/bin/env python

#CS456 Assignment #3 - Peer
#Daiyang Wang
#20646168

#Number of parameters: 3
#Parameter:
#    $1: <server_address>
#    $2: <n_port>
#    $3: <min time to live>

from socket import *
from threading import Thread, Lock
import sys, string, json, termios, tty, collections, os
from packet import packet
import time
import struct
import os

NUM_INPUTS = 3

# peer unique number
peer_num = 0
# ip address for this peer tcp
local_ip_addr = ''
# port number for this peer tcp
local_port_num = 0
# own file name
own_file_name = ''

# peer# : [ip_addr, port_num]
peer_dict = {}
# filename: [available peers]
file_dict = {}
# inactive means peer is not transfer data
inactive = True
# list of files name the peer has
local_file_list = []
# false when peer is new peer, true when it done first sync with everyone
is_old = False
# peer port
peer_port = 0
# flag to exit
EXIT = False

# tcpInitiation(server_address, n_port, req_code):
# Initiates a transaction with the <server_address> via TCP at <n_port> and sending the request code <req_code>.
# The server sends back the port needed for the transaction.
# Returns: r_port
def tcpInitiation(server_address, n_port):
    # Create client TCP socket
    TCPSocket = socket(AF_INET, SOCK_STREAM)
    try:
        TCPSocket.connect((server_address, n_port))
        return TCPSocket
    except error:
        print("Connection refused: please ensure the server is running")
        quit()
        return


def Create_Socket():
    global local_ip_addr, local_port_num
    testSocket = socket(AF_INET, SOCK_STREAM)
    testSocket.bind(('',0)) # match to dict addr and port number
    testSocket.listen(30)
    return testSocket			# Return the socket


# fetch information from tracker
def peerFetchInfo(tcpSocket, min_time_live):
    global peer_num, inactive, peer_dict, file_dict, local_file_list, local_ip_addr, local_port_num, own_file_name, server_tcp_socket, peer_port

    # peer initial own file name
    own_file_name = str(os.listdir("./Shared")[0])

    data_pak = build_data_package(own_file_name)

    # create data, and send to tracker
    filename_data = packet.get_tcp_data(packet.create_p_to_t(1, own_file_name + " " + str(len(data_pak))))
    tcpSocket.send(filename_data)
    # put into local file list
    local_file_list.append(str(own_file_name))

    server_tcp_socket = Create_Socket()
    trackerHost, peer_port = server_tcp_socket.getsockname()  # print TCP server port

    time.sleep(1)

    peer_port_data = packet.get_tcp_data(packet.create_p_to_t(3, str(peer_port)))
    tcpSocket.send(peer_port_data)


    lock = Lock()
    while True:
        # print("peerFetchInfo loop")
        tracker_pk = packet.parse_p2p_data(tcpSocket.recv(1024))
        if tracker_pk.type == 0:

            if tracker_pk.seq_num == 0:
                # print("seq_num = 0")
                print("PEER ", peer_num, " SHUTDOWN: HAS " + str(len(local_file_list)))
                for file in local_file_list:
                    print(peer_num, "    ", file)
                tcpSocket.close()
                server_tcp_socket.close()
                os._exit(os.EX_OK)
                break
            # seq_num = 1, tracker assigned a unique number to peer
            if tracker_pk.seq_num == 1:
                peer_num = int(tracker_pk.data)
            # seq_num = 2, tracker send dictionary of {peer_num: [ip_addr, port_num}
            if tracker_pk.seq_num == 2 and inactive:
                # print("seq_num = 2")
                raw_data = str(tracker_pk.data)
                lock.acquire()
                try:
                    peer_dict = converToDic(raw_data)
                finally:
                    lock.release()

                value = peer_dict.get(str(peer_num))
                local_ip_addr = value[0]
                local_port_num = value[1]

            # seq_num = 3, tacker send dictionary of {file: [peer1, peer2, ...}

            if tracker_pk.seq_num == 3 and inactive:
                # print("seq_num = 3")
                raw_data = str(tracker_pk.data)
                lock.acquire()
                try:
                    file_dict = converToDic(raw_data)
                finally:
                    lock.release()
                inactive = False  # which means it need update

                # once received all data from tracker, call sync files function
                p_to_p_th = Thread(target=peerSyncData, args=(server_tcp_socket,))
                p_to_p_th.start()




# convert string to dictionary
def converToDic(raw_data):
    dict = {}
    each_k_v = raw_data.split(";")
    for i in each_k_v:
        k_v = i.split(":")
        if (len(k_v) < 2):
            break
        key = k_v[0]
        key.strip()
        values = k_v[1].split()
        v_list = []
        for v in values:
            v_list.append(str(v).strip())
        dict[str(key)] = v_list
    return dict

# separate single file into multiple blocks
def build_data_package(file_name):
    # divide files into packets
    divided_packets = []
    f = open("./Shared/" + file_name, 'rb')
    content = f.read()
    n = packet.MAX_DATA_LENGTH
    divided_content = [content[i:i+n] for i in range(0, len(content)+1, n)]
    new_divided_content = [len(divided_content)]
    new_divided_content.extend(divided_content)

    # print("data separation: ", len(content), len(divided_content), divided_content[-1])
    # print("total packets #: ", len(new_divided_content))

    return new_divided_content

# send data message
def send_msg(peer_tCP, divided_packets):
    # Prefix each message with a 4-byte length (network byte order)
    data = struct.pack('>I', divided_packets[0])
    peer_tCP.send(data)
    for i in range(1, len(divided_packets)):
        data = struct.pack('>I', len(divided_packets[i])) + divided_packets[i]
        peer_tCP.send(data)
    return

# receive data message
def recv_msg(sock, file_to_write):
    raw_blocklen = recvall(sock, 4)
    if not raw_blocklen:
        return None
    blocklen = struct.unpack('>I', raw_blocklen)[0]
    for i in range(0, blocklen):
    # Read message length and unpack it into an integer
        raw_msglen = recvall(sock, 4)
        if not raw_msglen:
            return None
        msglen = struct.unpack('>I', raw_msglen)[0]
        # Read the message data
        data = recvall(sock, msglen)
        file_to_write.write(data)
    file_to_write.close()
    return

# helper function for receive message
def recvall(sock, n):
    # Helper function to recv n bytes or return None if EOF is hit
    data = bytearray()
    while len(data) < n:
        packet = sock.recv(n - len(data))
        if not packet:
            return None
        data.extend(packet)
    return data



# current peer sync data with others by using the peers_dict and files_dict
def peerSyncData(server_tcp_socket):
    global inactive, peer_dict, file_dict, local_file_list, peer_num,is_old
    # go though files_list, if does not have, then check file_dict to estabilish connection and get files.
    # set to false to prevent timeout

    # print("--newPeerSyncData---")
    # new peer, ask old peer files [receive files]
    for file, peers in file_dict.items():
        # get it from others
        if file not in local_file_list:
            # print("----HERE------:", file)
            # old peer unique number
            first_peer = peers[0]
            # search this peer info
            peer_info = peer_dict.get(str(first_peer), [])
            ip_addr = peer_info[0]
            port_num = peer_info[1]

            # print(ip_addr, port_num)

            # connect to other peer
            old_peer_tcp = tcpInitiation(ip_addr, int(port_num))

            old_peer_tcp.setsockopt(IPPROTO_TCP, TCP_NODELAY, 1)

            # send request file name to target old peer
            # time.sleep(1)
            file_name_pk = packet.create_p_to_p(1, file)
            file_name_data = packet.get_tcp_data(file_name_pk)
            old_peer_tcp.send(file_name_data)

            # print("old_peer_tcp SEND")
            # thread join, receive the file then call send to sent own file, and terminate
            # receive
            file_to_write = open("./Shared/" + file, 'ab')

            # new_peer_receive = Thread(target=receive_data, args=(old_peer_tcp, file_to_write,))
            # new_peer_receive.start()
            # new_peer_receive.join()
            recv_msg(old_peer_tcp, file_to_write)
            local_file_list.append(file)

            # receive_data(old_peer_tcp, file_to_write)

            time.sleep(1)
            # print("NEW PEER START SENT")
            # send request file name to target old peer
            own_file_name_pk = packet.create_p_to_p(3, own_file_name)
            own_file_name_data = packet.get_tcp_data(own_file_name_pk)
            old_peer_tcp.send(own_file_name_data)

            # check if it is ready to receive
            while True:
                # print("WAIT NEW PACKAGE")
                receiver_ready_pk = packet.parse_p2p_data(old_peer_tcp.recv(1024))
                # already have this package
                if receiver_ready_pk.seq_num == 6:
                    break
                # do not have this package
                if receiver_ready_pk.seq_num == 5:
                    ## send itself to old peer
                    data_packages = build_data_package(own_file_name)
                    # send_data(old_peer_tcp, data_packages)

                    new_peer_sent = Thread(target=send_msg, args=(old_peer_tcp, data_packages,))
                    new_peer_sent.start()
                    # send_msg(old_peer_tcp, data_packages)
                    break

            time.sleep(1)
            # TODO terminate when send and receive finish
            # receive seq_3 for receiver exit message to close connection
            receiver_exit_pk = packet.parse_p2p_data(old_peer_tcp.recv(1024))
            if receiver_exit_pk.seq_num == 0:
                old_peer_tcp.close()

    is_old = True
    # it became old and wait for share it files to new peers
    # (don't care list dict update, send files and receive new one)
    # print("---OLD--")
    while(is_old):
        # peer socket and addr
        inactive = True
        new_peer_tcp, addr = server_tcp_socket.accept()
        # new_peer_tcp.setsockopt(IPPROTO_TCP, TCP_NODELAY, 1)
        inactive = False

        file_name_pkt = packet.parse_p2p_data(new_peer_tcp.recv(1024))

        if file_name_pkt.seq_num == 1:
            # get file name and build data package
            file_name = file_name_pkt.data
            # print("THE NEW peer want", file_name)

            # old_peer_sent = Thread(target=send_data, args=(new_peer_tcp, data_packages,))
            # old_peer_sent.start()
            data_packages = build_data_package(file_name)
            # send_data(new_peer_tcp,data_packages)
            send_msg(new_peer_tcp, data_packages)


        # receive new peer data, check if old peer alrady have or not
        new_file_name_pkt = packet.parse_p2p_data(new_peer_tcp.recv(1024))
        if new_file_name_pkt.seq_num == 3:
            new_file_name = str(new_file_name_pkt.data)
            if new_file_name in local_file_list:
                # already has it
                already_have_pk = packet.create_p_to_p(6, '')
                already_have_data = packet.get_tcp_data(already_have_pk)
                new_peer_tcp.send(already_have_data)
            else:
                # please send it
                please_send_pk = packet.create_p_to_p(5, '')
                please_send_data = packet.get_tcp_data(please_send_pk)
                new_peer_tcp.send(please_send_data)

                # print("NEW PEER FILE NAME:", new_file_name)

                file_to_write = open("./Shared/" + new_file_name, 'ab')
                # old_peer_receive = Thread(target=receive_data, args=(new_peer_tcp, file_to_write, ))
                # old_peer_receive.start()
                recv_msg(new_peer_tcp,file_to_write)
                local_file_list.append(new_file_name)
            # receive_data(new_peer_tcp, file_to_write)

        # you may exit
        you_may_exit_pk = packet.create_p_to_p(0, '')
        you_may_exit_data = packet.get_tcp_data(you_may_exit_pk)
        new_peer_tcp.send(you_may_exit_data)






# check if peer is timeout or not, if so, it will send to tracker update info
def check_timeout(tcpsocket ,timeout):
    global EXIT, local_file_list, own_file_name, peer_num
    while (time.time() < timeout or not inactive):
        continue
    # send exit request to tracker with some information
    close_request = packet.get_tcp_data(packet.create_p_to_t(0, str(peer_num) + " " + own_file_name + " " + str(len(local_file_list))))
    tcpsocket.send(close_request)


#Main
def main():
    global peer_num, inactive, timeout
    if len(sys.argv) == 4:							#Argument validation
        server_address = sys.argv[1]
        n_port = int(sys.argv[2])
        min_time_live = int(sys.argv[3])

        # while (min_time_live and ) # TODO time left + inactive
        trackerTCP = tcpInitiation(server_address, n_port)	#Initiate the TCP connection with the tracker
        timeout = time.time() + min_time_live
        # TODO solve timeout issue
        check_time = Thread(target=check_timeout, args=(trackerTCP, timeout,))
        check_time.start()
        t_to_p_th = Thread(target=peerFetchInfo, args=(trackerTCP, min_time_live, ))
        t_to_p_th.start()


    # receive the r_port
    # udpTransaction(server_address, r_port, msg)	#Complete the transaction using UDP, receive the reversed message
    else:
        print("Error: incorrect parameters. <server_address> <n_port> and <min_time_live> are required")
        quit()

main()
