import click
import json
from pathlib import Path
from .constants import RUNE_WEIGHT, I18N_FORMAT_CHAIN
from .singleton import Singleton

class Item:
    def __init__(self, id_, effects, prices):
        self.effects = effects
        self.price = prices[0]
        self.weight = sum([effects[effect].weight for effect in effects])
        item_reader = ItemReader()
        effect_reader = EffectReader()
        self.name = item_reader.get(id_)["nameId"]

        possible_effects = item_reader.get(id_)["possibleEffects"]
        for possible_effect in possible_effects:
            p_id = possible_effect["effectId"]
            p_max = max(possible_effect["diceNum"], possible_effect["diceSide"])
            diff = -p_max
            if p_id in self.effects.keys():
                self.effects[p_id].diff = self.effects[p_id].value - p_max
            else:
                self.effects[p_id] = Effect(70, p_id, 0, effect_reader.get(p_id)["descriptionId"])
                
                self.effects[p_id].diff = diff


    def __str__(self):
        string_effect = '\n'.join([str(effect) for effect in self.effects.values()])
        return "{}\n{}\nPrice : {:0,.0f}\nWeight: {}\n".format(self.name, string_effect, self.price, self.weight)

    def __eq__(self, other):
        return self.weight == other.weight

    def __lt__(self, other):
        return self.weight < other.weight

class Effect:
    def __init__(self, effect_category, effect_id, value, raw_description):
        self.effect_category = effect_category
        self.effect_id = effect_id
        self.value = value
        self.description = raw_description.replace(I18N_FORMAT_CHAIN, str(self.value))
        self.weight = 0
        self.diff = value
        if effect_category == 70:
            self.weight = RUNE_WEIGHT[effect_id] * value

    def __str__(self):
        colored_diff = "{:=+5d}".format(self.diff)
        if self.diff == 0:
            colored_diff = click.style(colored_diff, fg='green')
        elif self.diff < 0:
            colored_diff = click.style(colored_diff, fg='red')
        elif self.diff > 0:
            colored_diff = click.style(colored_diff, fg='blue')
            
        return "{:24}{}".format(self.description, colored_diff)

class ItemReader(metaclass=Singleton):
    def __init__(self):
        item_file = Path.home().joinpath(".xelor/data/Items.json")
        self.items = dict()
        with open(item_file) as f:
            self.items = json.load(f)

    def get(self, id_):
        return self.items[str(id_)]


class EffectReader(metaclass=Singleton):
    def __init__(self):
        effect_file = Path.home().joinpath(".xelor/data/Effects.json")
        self.effects = dict()
        with open(effect_file) as f:
            self.effects = json.load(f)

    def get(self, id_):
        return self.effects[str(id_)]
