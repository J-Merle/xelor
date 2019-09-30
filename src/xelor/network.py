import binascii
import codecs
import socket
import struct

BIT_MASK = 3
TCP_PROTOCOL = 0x06


def listen(port):
    sock = socket.socket(socket.PF_PACKET, socket.SOCK_RAW, socket.htons(0x800))

    data_to_process = b""
    message_len = 0
    while True:
        data = sock.recvfrom(65565)[0]
        storeobj = struct.unpack_from("!6s6sH", data)
        data = data[14:]

        # Ethernet header
        destination_mac = binascii.hexlify(storeobj[0])
        source_mac = binascii.hexlify(storeobj[1])
        eth_protocol = storeobj[2]

        # IP Header
        storeobj = struct.unpack_from("!BBHHHBBH4s4s", data)
        data = data[20:]
        _protocol = storeobj[6]
        _source_address = socket.inet_ntoa(storeobj[8])
        _destination_address = socket.inet_ntoa(storeobj[9])

        if _protocol != TCP_PROTOCOL:
            continue

        # TCP
        storeobj = struct.unpack_from("!HHLLBBHHH", data)
        data = data[20:]
        _source_port = storeobj[0]
        _destination_port = storeobj[1]

        if _destination_port == port and len(data) > 2:
            big = message_len > len(data_to_process)
            if data_to_process == b"":

                reader = NetworkReader(data)
                static_header = reader.read_short()
                BYTE_LEN_DYNAMIQUE_HEADER = static_header & BIT_MASK
                message_id = static_header >> 2
                message_len = 0
                if len(reader.data) >= (BYTE_LEN_DYNAMIQUE_HEADER):
                    if BYTE_LEN_DYNAMIQUE_HEADER == 1:
                        message_len = reader.read_byte()
                    elif BYTE_LEN_DYNAMIQUE_HEADER == 2:
                        message_len = reader.read_short()
                    elif BYTE_LEN_DYNAMIQUE_HEADER == 3:
                        message_len = (
                            ((reader.read_byte() & 0xFF) << 16)
                            + ((reader.read_byte() & 0xFF) << 8)
                            + (reader.read_byte() & 0xFF)
                        )
                data_to_process = reader.data
            else:
                data_to_process += data

            if big:
                continue
            else:
                yield message_id, data_to_process
                data_to_process = b""


class NetworkReader:
    def __init__(self, data):
        self.data = data

    def read_short(self):
        res = struct.unpack_from("!h", self.data)[0]
        self.data = self.data[2:]
        return res

    def read_int(self):
        res = struct.unpack_from("!i", self.data)[0]
        self.data = self.data[4:]
        return res

    def read_byte(self):
        res = struct.unpack_from("!B", self.data)[0]
        self.data = self.data[1:]
        return res

    def read_utf(self):
        _size = self.read_short()
        text = self.data[:_size].decode("utf-8")
        self.data = self.data[_size:]
        return text

    def read_var_short(self):
        offset = 0
        value = 0
        while True:
            b, = struct.unpack_from("!B", self.data)
            self.data = self.data[1:]
            has_next = (b & 128) == 128
            if offset > 0:
                value = value + ((b & 127) << offset)
            else:
                value = value + (b & 127)
            offset = offset + 7
            if not has_next:
                break
        if value > 32767:
            value = value - 65536
        return value

    def read_var_int(self):
        offset = 0
        value = 0
        while True:
            b, = struct.unpack_from("!B", self.data)
            self.data = self.data[1:]
            has_next = (b & 128) == 128
            if offset > 0:
                value = value + ((b & 127) << offset)
            else:
                value = value + (b & 127)
            offset = offset + 7
            if not has_next:
                break
        return value
