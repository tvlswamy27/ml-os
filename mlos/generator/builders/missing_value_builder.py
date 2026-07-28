from mlos.generator.builders.base_builder import BaseBuilder
from mlos.domain.models.decision import Decision
from mlos.domain.models.generated_code import GeneratedCode

class MissingValueBuilder(BaseBuilder):

    def build(
        self,
        decision: Decision,
    ) -> GeneratedCode:

        return GeneratedCode(
            title=decision.title,
            code="# Missing value code",
        )
