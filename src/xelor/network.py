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
