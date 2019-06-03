import codecs
import struct
from os import popen
from subprocess import PIPE, Popen

import click

BIT_MASK = 3


@click.group()
def cli():
    pass


@cli.command()
def scan():
    command = "netstat -op 2> /dev/null | grep Dofus.exe | grep personal-agent | awk '{print $4}' | awk -F':' '{print $2}'"
    with popen(command) as out:
        for line in out:
            print("Dofus is running on port : " + line.strip())


@cli.command()
@click.option("--port", required=True, type=int)
@click.option("--contains")
@click.option("--raw", is_flag=True)
def chat(port, contains, raw):
    if contains:
        contains = [word.lower() for word in contains.split("|")]
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
        if raw:
            print(codecs.encode(data, "hex"))
        data = data[2 + (static_header & BIT_MASK) :]
        if static_header == 881:
            message = ChatMessage(data)
            if contains:
                for word in contains:
                    if word in message.message:
                        print("J'ai matché" + word)
                        print(message)
                        break
            else:
                print(message)


def compute_size_category(static_header):
    _res = static_header & BIT_MASK
    if _res == 1:
        return "B"
    elif _res == 2:
        return "H"
    # TODO Add other masks
    return "B"


canals = {
    9: "Guilde",
    2: "Privé",
    6: "Recrutement",
    5: "Commerce",
    14: "FR",
    0: "Général",
}


class ChatMessage:
    def __init__(self, data):
        self.message = " "
        try:
            self.canal, _message_len = struct.unpack_from("!BH", data)
            self.message, self.timestamp, _fingerprint, _name_len = struct.unpack_from(
                "!{}si18sh".format(_message_len), data, offset=3
            )
            self.name, = struct.unpack_from(
                "!{}s".format(_name_len), data, offset=27 + _message_len
            )
            self.message = codecs.decode(self.message, "utf8")
            self.name = codecs.decode(self.name, "utf8")
        except Exception:
            print("Could not parse {}".format(data))

    def __repr__(self):
        if self.canal not in canals:
            return "ERROR Canal {} not found. Message content : {}".format(
                self.canal, self.message_content
            )

        else:
            return "({}) {} : {}".format(canals[self.canal], self.name, self.message)


if __name__ == "__main__":
    cli()
