"""
Generator Engine.

Generates executable Python code.

Author: Vikram Tanakala
License: MIT
"""

from mlos.generator.generators.missing_value_generator import (
    MissingValueGenerator,
)


class GeneratorEngine:

    def __init__(self):

        self.generators = [

            MissingValueGenerator(),

        ]

    def generate(
        self,
        decisions,
    ):

        generated = []

        for decision in decisions:

            for generator in self.generators:

                if generator.can_generate(
                    decision,
                ):

                    generated.append(
                        generator.generate(
                            decision,
                        )
                    )

                    break

        return generated