import codecs
import json
import struct
from pathlib import Path

from .datastore import EffectReader
from .constants import RUNE_WEIGHT, EFFECT_DESCRIPTION_KEY
from .items import Effect, Item, EffectInt, EffectString
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


class ItemMessage(NetworkReader):
    def __init__(self, data):
        super().__init__(data)
        self.data = data
        self.values = list()
        items = list()

        effect_reader = EffectReader()

        # Int value, we don't know what it is used for
        self.read_int()
        _item_len = self.read_short()
        print(_item_len)

        for _ in range(_item_len):
            # Read object data
            # The unique id generated for the item. This value is not used for the moment.
            self.read_var_short()
            # The id of the generic item which the current one is an instance of
            id_ = self.read_var_short()
            # Int value, we don't know what it is used for
            self.read_int()

            # Read effects data
            effects_int = dict()
            effects_str = dict()
            _effect_len = self.read_short()
            for _ in range(_effect_len):
                effect_category = self.read_short()
                effect_id = self.read_var_short()
                effect_value = 0
                effect_description = effect_reader.get(effect_id)[EFFECT_DESCRIPTION_KEY]
                if effect_category == 70:
                    effect_value = self.read_var_short()
                    effects_int[effect_id] = EffectInt(effect_id, effect_value, effect_description)
                elif effect_category == 74:
                    effect_value = self.read_utf()
                    effects_str[effect_id] = EffectString(effect_id, effect_value, effect_description)

            # read prices data
            prices = list()
            _price_len = self.read_short()
            for _ in range(_price_len):
                prices.append(self.read_var_int())

            item = Item(id_, effects_int, effects_str, prices)
            items.append(item)

        self.values = sorted(items, reverse=True)
