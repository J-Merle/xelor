import codecs
import json
import struct
from pathlib import Path

from .network import NetworkReader

RUNE_WEIGHT = {753: 4, 115: 10, 428: 5}

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


class HDVMessage(NetworkReader):
    def __init__(self, data):
        super().__init__(data)
        dest_folder = Path.home().joinpath(".xelor/data/Effects.json")
        self.effect_dict = dict()
        with open(dest_folder) as f:
            self.effect_dict = json.load(f)

        dest_folder = Path.home().joinpath(".xelor/data/Items.json")
        # with open(dest_folder) as f:
        #    self.item = json.load(f)[context]
        #    print(json.dumps(self.item))

        self.data = data
        _len, = struct.unpack_from("!h", self.data)
        self.data = self.data[2:]
        print("{} items found".format(_len))
        for _ in range(_len):

            uid = self.readVarShort()
            _effect_len, = struct.unpack_from("!H", self.data)
            self.data = self.data[2:]
            for _ in range(_effect_len):
                effect_type, = struct.unpack_from("!H", self.data)
                self.data = self.data[2:]
                effect_id = self.readVarShort()
                total_weight = 0
                if effect_type == 70:
                    value = self.readVarShort()
                    # print(effect_id)
                    total_weight += RUNE_WEIGHT[effect_id]
                    print(
                        "{}".format(
                            self.effect_dict[str(effect_id)]["descriptionId"].replace(
                                "#1{~1~2 a }#2", str(value)
                            )
                        )
                    )
                elif effect_type == 74:
                    print(self.read_utf())
            _price_len, = struct.unpack_from("!H", self.data)
            self.data = self.data[2:]
            prices = []
            for _ in range(_price_len):
                prices.append(self.readVarInt())
            print(prices)
            print("Total weight : {}".format(total_weight))
            print("\n")
