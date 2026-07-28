

from mlos.generator.builders.missing_value_builder import MissingValueBuilder


class GeneratorEngine:

    def __init__(self):

        self.builders = [
            MissingValueBuilder(),
        ]

    def generate(
        self,
        decisions,
    ):

        generated = []

        for decision in decisions:

            for builder in self.builders:

                generated.append(builder.build(decision))

        return generated
