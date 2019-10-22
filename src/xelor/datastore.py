import json
import struct
from collections import namedtuple
from pathlib import Path

from .singleton import Singleton
from .items import EffectInt

Class = namedtuple("Class", "name package fields")

NULL_IDENTIFIER = -1431655766


def read_bytes(stream, pattern, size):
    return struct.unpack(pattern, stream.read(size))[0]


def read_int(stream):
    return read_bytes(stream, "!i", 4)


def read_uint(stream):
    return read_bytes(stream, "!I", 4)


def read_bool(stream):
    return read_bytes(stream, "!?", 1)


def read_short(stream):
    return read_bytes(stream, "!H", 2)


def read_double(stream):
    return read_bytes(stream, "!d", 8)


def read_utf(stream):
    _size = read_short(stream)
    return stream.read(_size).decode("utf-8")


class D2iReader(metaclass=Singleton):
    def __init__(self):
        self.file_path = r"/opt/ankama/dofus/share/data/i18n/i18n_fr.d2i"
        self.indexes = dict()
        with open(self.file_path, "rb") as f:
            data_size = read_int(f)
            f.seek(data_size, 0)
            index_size = read_int(f)
            while f.tell() < index_size + data_size:
                id = read_int(f)
                dial = read_bool(f)
                str_pointer = read_int(f)
                dial_data = 0
                if dial:
                    dial_data = read_int(f)
                self.indexes[id] = (dial, str_pointer, dial_data)

    def translate(self, id):
        try:
            with open(self.file_path, "rb") as f:
                f.seek(self.indexes[id][2])
                return read_utf(f)
        except:
            return ""


class D2oReader:
    def __init__(self):
        self.d2i_reader = D2iReader()
        self.class_dict = dict()
        self.type_dict = {
            -1: read_int,
            -2: read_bool,
            -3: read_utf,
            -4: read_double,
            -6: read_uint,
            -5: self.read_i18n,
            -99: self.read_list,
        }
        self.json = ""

    def read_i18n(self, stream):
        message_id = read_int(stream)
        return self.d2i_reader.translate(message_id)

    def read_list(self, stream, deque_type):
        length = read_uint(stream)
        return [self.read_from_type(stream, deque_type) for _ in range(length)]

    def read_field_type(self, stream):
        fields = []
        field_type = read_int(stream)
        fields.append(field_type)
        while field_type == -99:
            read_utf(stream)
            field_type = read_int(stream)
            fields.append(field_type)
        return fields

    def read_from_type(self, stream, data_type):
        current_type = data_type[0]
        if current_type != -99:
            if current_type > 0:
                return self.extract_class(stream)
            return self.type_dict[current_type](stream)
        else:
            return self.type_dict[current_type](stream, data_type[1:])

    def extract_class(self, stream):
        class_id = read_int(stream)
        if class_id == NULL_IDENTIFIER:
            return {}
        current_class = self.class_dict[class_id]

        o = dict()

        for item in current_class.fields:
            o[item[0]] = self.read_from_type(stream, item[1])
        return o

    def load(self, path):
        with open(path, "rb") as f:
            key, pointer = 0, 0
            headers = f.read(3)
            # TODO implement the non-d2o header case
            indexes = dict()
            content_offset = 0

            f.seek(content_offset + read_int(f))
            indexes_length = read_int(f)
            i = 0
            while i * 8 < indexes_length:
                key = read_int(f)
                pointer = read_int(f)
                indexes[key] = content_offset + pointer
                i += 1
            self.class_dict = dict()
            classes_count = read_int(f)

            for _ in range(classes_count):
                _class_identifier = read_int(f)
                _class_name = read_utf(f)
                _package_name = read_utf(f)
                _fields_count = read_int(f)
                _fields = [
                    (read_utf(f), self.read_field_type(f)) for _ in range(_fields_count)
                ]
                self.class_dict[_class_identifier] = Class(
                    _class_name, _package_name, _fields
                )

            global_json = dict()
            for key, value in indexes.items():
                f.seek(value)
                current_class = self.class_dict[read_int(f)]

                o = dict()
                for item in current_class.fields:
                    o[item[0]] = self.read_from_type(f, item[1])
                global_json[key] = o
            self.json = json.dumps(global_json)


class JsonReader:
    def __init__(self, filename):
        # TODO change the path by the solution adopted in issue #13
        item_file = Path.home().joinpath(".xelor/data").joinpath(filename)
        self.json = dict()
        with open(item_file) as f:
            self.json = json.load(f)

    def get(self, id_):
        return self.json[str(id_)]


class EffectReader(metaclass=Singleton):
    def __init__(self):
        self.reader = JsonReader("Effects.json")

    def get(self, id_):
        return self.reader.get(id_)


class ItemReader(metaclass=Singleton):
    def __init__(self):
        self.reader = JsonReader("Items.json")

    def get(self, id_):
        return self.reader.get(id_)

    def effects_from_id(self, id_):
        effect_reader = EffectReader()
        return {effect['effectId']: EffectInt(effect['effectId'],
                                              max(effect["diceNum"], effect["diceSide"]),
                                              effect_reader.get(effect['effectId'])["descriptionId"]) for
                effect in self.get(id_)["possibleEffects"]}
