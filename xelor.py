import codecs
from os import popen
from subprocess import PIPE, Popen, check_output

import click


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
@click.option('--raw', is_flag=True)
def chat(port, contains, raw):
    if contains:
        contains = [word.lower() for word in contains.split("|")]
    _filter = "tcp.port==" + str(port)
    command = ["tshark", "-Y", _filter, "-T", "fields", "-e", "data", "-l"]
    pipe = Popen(command, stdout=PIPE, stderr=None)
    for item in pipe.stdout:
        item = item.strip()
        if len(item) > 0 and item[:3] == b"0dc":
            if raw:
                print(item)
            message = ChatMessage(item)
            if contains:
                for word in contains:
                    if word in message.message_content.lower():
                        print(message)
                        break
            else:
                print(message)


canals = {9: "Guilde", 2: "Privé", 6: "Recrutement", 5: "Commerce", 14: "FR", 0: "Général"}


def hexa_to_int(bytes_data):
    if not bytes_data:
        return 0
    return int(bytes_data.decode("utf8"), 16)


def hexa_to_ascii(bytes_data):
    try:
        return codecs.decode(bytes_data, "hex").decode("utf8")
    except:
        return "ERROR could not convert message {}".format(bytes_data)


class ChatMessage:
    def __init__(self, raw_packet):
        self.canal = hexa_to_int(raw_packet[6:8])
        _message_len = hexa_to_int(raw_packet[8:12]) * 2
        _message_end = 12 + _message_len
        self.message_content = hexa_to_ascii(raw_packet[12:_message_end])
        _timestamp_end = _message_end + 8
        self.timestamp = hexa_to_int(raw_packet[_message_end:_timestamp_end])
        _name_len_end = _timestamp_end + 2 + 38
        _name_len = hexa_to_int(raw_packet[_timestamp_end + 38 : _name_len_end])
        _name_end = _name_len_end + _name_len * 2
        self.name = hexa_to_ascii(raw_packet[_name_len_end:_name_end])

    def __repr__(self):
        if self.canal not in canals:
            return "ERROR Canal {} not found. Message content : {}".format(
                self.canal, self.message_content
            )

        else:
            return "({}) {} : {}".format(
                canals[self.canal], self.name, self.message_content
            )


if __name__ == "__main__":
    cli()
