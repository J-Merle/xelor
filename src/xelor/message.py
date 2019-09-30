import codecs
import json
import struct
from pathlib import Path

from .constants import RUNE_WEIGHT
from .items import Effect, Item
from .network import NetworkReader

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
        self.data = data
        self.values = list()
        items = list()

        effect_file = Path.home().joinpath(".xelor/data/Effects.json")
        self.effect_dict = dict()
        with open(effect_file) as f:
            self.effect_dict = json.load(f)

        # print(codecs.encode(self.data, "hex"))

        self.read_int()  # Unknown data
        _item_len = self.read_short()
        print(_item_len)

        for _ in range(_item_len):
            # Read object data
            # The unique id generated for the item. Not that much useful
            self.read_var_short()
            # The id of the generic item which the current one is an instance of
            id_ = self.read_var_short()
            self.read_int()  # Unknown data

            # Read effects data
            effects = dict()
            _effect_len = self.read_short()
            for _ in range(_effect_len):
                effect_category = self.read_short()
                effect_id = self.read_var_short()
                effect_value = 0
                effect_description = ""

                if effect_category == 70:
                    effect_value = self.read_var_short()
                    effect_description = self.effect_dict[str(effect_id)][
                        "descriptionId"
                    ]
                elif effect_category == 74:
                    effect_description = self.read_utf()

                effects[effect_id] = Effect(
                    effect_category, effect_id, effect_value, effect_description
                )

            # read prices data
            prices = list()
            _price_len = self.read_short()
            for _ in range(_price_len):
                prices.append(self.read_var_int())

            item = Item(id_, effects, prices)
            items.append(item)

        self.values = sorted(items, reverse=True)
