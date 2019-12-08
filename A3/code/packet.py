#!/usr/bin/env python

#CS456 Assignment #3 - Packet
#Daiyang Wang
#20646168

class packet:
    MAX_DATA_LENGTH = 511988 # 512000 - 12 byes
    SEQ_NUM_MODULO = 32

    def __init__(self, type, seq_num, data):
        if len(data) > self.MAX_DATA_LENGTH:
            raise Exception("Data too large (max 512 kilo char): ", len(data))

        self.type = type
        self.seq_num = seq_num % self.SEQ_NUM_MODULO
        self.data = data

    def get_tcp_data(self):
        array = bytearray()
        array.extend(self.type.to_bytes(length=4, byteorder="big"))
        array.extend(self.seq_num.to_bytes(length=4, byteorder="big"))
        array.extend(len(self.data).to_bytes(length=4, byteorder="big"))
        array.extend(self.data.encode())
        return array

    @staticmethod
    def create_t_to_p(seq_num, data):
        # tracker to peer message, if seq_num = 0, tracker ack peer to exit, seq_num = 1, tracker send assign number,
        # seq_num = 2, tracker send dictionary of [peers : [addr, port];
        # seq_num = 3, tacker send dictionary of [file: [peer1, peer2, ...]
        if (seq_num == 0):
            return packet(0, seq_num, "")
        else:
            return packet(0, seq_num, data)

    @staticmethod
    def create_p_to_p(seq_num, data):
        # peer to peer data transfer
        # seq_num = 0, file finished transfer

        # seq_num = 1, request file name
        # seq_num = 2, data
        # seq_num = 3, own file name

        # seq_num = 4, receiver to sender exit
        # seq_num = 5, ready to send
        # seq_num = 6, already has dont send
        if seq_num == 1 or seq_num == 2 or seq_num == 3:
            return packet(1, seq_num, data)
        else:
            return packet(1, seq_num, "")

    @staticmethod
    def create_p_to_t(seq_num, data):
        # peer to tracker message, if seq_num = 0, peer want to exit, seq_num = 1, peer send filename,
        # seq_num = 2 tell tracker all the file that I have
        # seq_num = 3 tell tracker the port number as server side

        return packet(2, seq_num, data)

    @staticmethod
    def parse_p2p_data(TCPdata):
        type = int.from_bytes(TCPdata[0:4], byteorder="big")
        seq_num = int.from_bytes(TCPdata[4:8], byteorder="big")
        length = int.from_bytes(TCPdata[8:12], byteorder="big")
        if type == 0:
            TCPdata = TCPdata[12:12 + length].decode()
            return packet.create_t_to_p(seq_num, TCPdata)
        elif type == 2:
            TCPdata = TCPdata[12:12 + length].decode()
            return packet.create_p_to_t(seq_num, TCPdata)
        else:
            TCPdata = TCPdata[12:12 + length].decode()
            return packet.create_p_to_p(seq_num, TCPdata)