import codecs
import struct
from os import getenv, popen
from pathlib import Path
from subprocess import PIPE, Popen

import click

from .datastore import D2oReader
from .message import ChatMessage, HDVMessage
from .network import listen_packets

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
@click.option("--contains", type=click.STRING)
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
                        print(message)
                        break
            else:
                print(message)


@cli.command()
@click.option("--port", required=True, type=int)
def raw(port):
    for header, data in listen_packets(port):
        data = codecs.encode(data, "hex")
        print("{} - {}".format(header, data))


@cli.command()
@click.option("--force", is_flag=True)
def load(force):
    dest_folder = Path.home().joinpath(".xelor/data")
    if not dest_folder.exists():
        dest_folder.mkdir(parents=True)
    dofus_source = getenv("DOFUS_PATH", "/opt/ankama/dofus")
    d2o_source = Path(dofus_source).joinpath("share/data/common")

    d2o_reader = D2oReader()
    for d2o_file in [
        filename for filename in d2o_source.iterdir() if filename.suffix == ".d2o"
    ]:
        dest_file = dest_folder.joinpath(d2o_file.name).with_suffix(".json")
        if not force and dest_file.exists():
            print("{} already exists. Use --force to overwrite it.".format(d2o_file))
            continue
        d2o_reader.load(d2o_file)
        with open(dest_file, "w") as f:
            print("Writing in {}".format(dest_file))
            f.write(d2o_reader.json)


@cli.command()
@click.option("--port", required=True, type=int)
def hdv(port):
    for header, data in listen_packets(port):
        if header == 5752:
            print(codecs.encode(data, 'hex'))
            h = HDVMessage(data)





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
