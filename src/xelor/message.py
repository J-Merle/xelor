import codecs
import json
import struct
from pathlib import Path

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
                self.canal, self.message
            )

        else:
            return "({}) {} : {}".format(canals[self.canal], self.name, self.message)


class HDVMessage:
    def __init__(self, data):
        dest_folder = Path.home().joinpath(".xelor/data/Effects.json")
        self.effect_dict = dict()
        with open(dest_folder) as f:
            self.effect_dict = json.load(f)

        self.data = data
        print(self.readVarInt())
        _len, = struct.unpack_from("!H", self.data)
        self.data = self.data[2:]
        print("{} items found".format(_len))
        for _ in range(_len):
            uid = self.readVarShort()
            _effect_len, = struct.unpack_from("!H", self.data)
            self.data = self.data[2:]
            for _ in range(_effect_len):
                _type = struct.unpack_from("!H", self.data)
                self.data = self.data[2:]
                effect_id = self.readVarShort()
                value = self.readVarShort()
                print(
                    "{} {}".format(
                        value,
                        self.effect_dict[str(effect_id)]["descriptionId"].replace(
                            "#1{~1~2 a }#2 ", ""
                        ),
                    )
                )
            _price_len, = struct.unpack_from("!H", self.data)
            self.data = self.data[2:]
            prices = []
            for _ in range(_price_len):
                prices.append(self.readVarShort())
            print(prices)
            print("\n")

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
