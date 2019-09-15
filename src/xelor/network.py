from subprocess import PIPE, Popen
import codecs
import struct

BIT_MASK = 3


def listen_packets(port):
    _filter = "tcp.port==" + str(port)
    command = ["tshark", "-Y", _filter, "-T", "fields", "-e", "data", "-l"]
    pipe = Popen(command, stdout=PIPE, stderr=None)

    for data in pipe.stdout:
        data = codecs.decode(data.strip(), "hex")
        if len(data) < 6:
            continue
        static_header = struct.unpack_from("!h", data)[0] >> 2

        data_size_category = compute_size_category(static_header)
        data_size, = struct.unpack_from(
            "!{}".format(data_size_category), data, offset=2
        )

        data = data[2 + (static_header & BIT_MASK):]
        yield static_header, data


def compute_size_category(static_header):
    _res = static_header & BIT_MASK
    if _res == 1:
        return "B"
    elif _res == 2:
        return "H"
    # TODO Add other masks
    return "B"

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
