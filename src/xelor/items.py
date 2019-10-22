import click

from .constants import RUNE_WEIGHT, FORMAT_CHAIN, ITEM_NAME_KEY
from .datastore import ItemReader


class Item:
    def __init__(self, id_, effects_int, effects_str, prices):
        self._effects_str = effects_str
        self._effects_int = effects_int
        self.price = prices[0]
        self.weight = sum([effect.weight for _, effect in effects_int])
        self.item_reader = ItemReader()
        self._name = self.item_reader.get(id_)[ITEM_NAME_KEY]
        self.jet = self._evaluate_jet(id_, effects_int)

    def __str__(self):
        effects_int = '\n'.join([str(effect) + colored_diff(diff) for effect, diff in self.jet])
        effects_str = '\n'.join([str(effect) for effect in self._effects_str])
        return "{}\n{}{}\nPrice : {:0,.0f} K\nWeight: {}\n".format(self._name, effects_int, effects_str, self.price,
                                                                   self.weight)

    def __eq__(self, other):
        return self.weight == other.weight

    def __lt__(self, other):
        return self.weight < other.weight

    def _evaluate_jet(self, id_, effects_int):
        jet = list()
        base_effects = self.item_reader.effects_from_id(id_)
        possible_ids = {effect['effectId'] for effect in base_effects}
        present_ids = {effect.effect_id for effect in effects_int}

        # Compare possible and present effects
        for compared_id in possible_ids & present_ids:
            effect = effects_int[compared_id]
            possible_effect = base_effects[compared_id]
            jet.append((effects_int[compared_id], effect - possible_effect))

        # Effects not present
        for compared_id in possible_ids - present_ids:
            effect = base_effects[compared_id]
            diff = effect.value
            effect.value = 0
            jet.append((effect, -diff))

        # New effects
        for compared_id in present_ids - possible_ids:
            effect = effects_int[compared_id]
            jet.append((effect, effect.value))

        return jet


class Effect:
    def __init__(self, effect_id, value):
        self.effect_id = effect_id
        self.value = value
        self.description = ""

    def __str__(self):
        return "{:24}".format(self.description)

class EffectInt(Effect):
    def __init__(self, effect_id, value, raw_description):
        super().__init__(effect_id, value)
        self.weight = 0
        self.raw_description = raw_description
        self.description = raw_description.replace(FORMAT_CHAIN, str(self.value))
        self.weight = RUNE_WEIGHT[effect_id] * value

    def __sub__(self, other):
        return self.value - other.value


class EffectString(Effect):
    def __init__(self, effect_id, value, raw_description):
        super().__init__(effect_id, value)
        self.description = raw_description[:-2] + self.value


def colored_diff(value):
    colored_string = "{:=+5d}".format(value)
    if value == 0:
        return click.style(colored_string, fg='green')
    elif value < 0:
        return click.style(colored_string, fg='red')
    else:
        return click.style(colored_string, fg='blue')
