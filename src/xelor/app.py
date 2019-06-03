import codecs
import struct
from os import popen
from subprocess import PIPE, Popen

import click

from .message import ChatMessage

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


if __name__ == "__main__":
    cli()
