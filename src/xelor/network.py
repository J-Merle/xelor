import binascii
import socket
import struct

BIT_MASK = 3
TCP_PROTOCOL = 0x06


def listen(port):
    sock = socket.socket(socket.PF_PACKET, socket.SOCK_RAW, socket.htons(0x800))

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
            static_header = struct.unpack_from("!h", data)[0] >> 2

            data_size_category = compute_size_category(static_header)
            if data_size_category != "":
                data_size, = struct.unpack_from(
                    "!{}".format(data_size_category), data, offset=2
                )

            data = data[2 + static_header & BIT_MASK :]
            yield static_header, data


def compute_size_category(static_header):
    _res = static_header & BIT_MASK
    if _res == 1:
        return "B"
    elif _res == 2:
        return "H"
    # TODO Add other masks
    return ""

class NetworkReader:
    def __init__(self, data):
        self.data = data

    def readVarShort(self):

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

    def readVarInt(self):
        offset = 0
        value = 0
        while True:
            b, = struct.unpack_from("!B", self.data)
            self.data = self.data[2:]
            has_next = (b & 128) == 128
            if offset > 0:
                value = value + ((b & 127) << offset)
            else:
                value = value + (b & 127)
            offset = offset + 7
            if not has_next:
                break
        return value
