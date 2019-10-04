import click

from .constants import RUNE_WEIGHT, FORMAT_CHAIN, ITEM_NAME_KEY
from .datastore import ItemReader, EffectReader


class Item:
    def __init__(self, id_, effects_int, effects_str, prices):
        self._effects_str = effects_str
        self.price = prices[0]
        self.weight = sum([effect.weight for _, effect in effects_int])
        item_reader = ItemReader()
        effect_reader = EffectReader()
        self._name = item_reader.get(id_)[ITEM_NAME_KEY]

        possible_effects = {effect['effectId']: EffectInt(effect['effectId'],
                                                          max(effect["diceNum"], effect["diceSide"]),
                                                          effect_reader.get(effect['effectId'])["descriptionId"]) for
                            effect in item_reader.get(id_)["possibleEffects"]}

        self._compared_effects = list()
        possible_ids = {effect['effectId'] for effect in possible_effects}
        present_ids = {effect.effect_id for effect in effects_int}

        # Compare possible and present effects
        for compared_id in possible_ids & present_ids:
            self._compared_effects.append(ComparedIntEffect(effects_int[compared_id], possible_effects[compared_id]))

        # Compare possible but not present effects
        for compared_id in possible_ids - present_ids:
            self._compared_effects.append(ComparedIntEffect(None, possible_effects[compared_id]))

        # Compare possible but not present effects
        for compared_id in present_ids - possible_ids:
            self._compared_effects.append(ComparedIntEffect(effects_int[compared_id], None))

    def __str__(self):
        effects_int = '\n'.join([str(effect) for effect in self._compared_effects])
        effects_str = '\n'.join([str(effect) for effect in self._effects_str])
        effects = effects_int + effects_str
        return "{}\n{}\nPrice : {:0,.0f}\nWeight: {}\n".format(self._name, effects, self.price, self.weight)

    def __eq__(self, other):
        return self.weight == other.weight

    def __lt__(self, other):
        return self.weight < other.weight


class Effect:
    def __init__(self, effect_id, value):
        self.effect_id = effect_id
        self.value = value
        self.description = ""


class EffectInt(Effect):
    def __init__(self, effect_id, value, raw_description):
        super().__init__(effect_id, value)
        self.weight = 0
        self.raw_description = raw_description
        self.description = raw_description.replace(FORMAT_CHAIN, str(self.value))
        self.weight = RUNE_WEIGHT[effect_id] * value

    def __str__(self):
        return "{:24}".format(self.description)


class EffectString(Effect):
    def __init__(self, effect_id, value, raw_description):
        super().__init__(effect_id, value)
        self.description = raw_description[:-2] + self.value

    def __str__(self):
        return self.description


class ComparedIntEffect:
    def __init__(self, base_effect, relative_effect):
        self.effect = base_effect
        self.diff = 0
        if base_effect is None:
            if relative_effect is None:
                raise ValueError("At least on effect must be specified")
            else:
                self.diff = - relative_effect.value
                self.effect = EffectInt(relative_effect.id, 0, relative_effect.raw_description)
        else:
            if relative_effect is None:
                self.diff = base_effect.value
            else:
                self.diff = relative_effect.value - base_effect.value
            self.effect = base_effect

    def __str__(self):
        return str(self.effect) + self.colored_diff()

    def colored_diff(self):
        colored_string = "{:=+5d}".format(self.diff)
        if self.diff == 0:
            return click.style(colored_string, fg='green')
        elif self.diff < 0:
            return click.style(colored_string, fg='red')
        elif self.diff > 0:
            return click.style(colored_string, fg='blue')
