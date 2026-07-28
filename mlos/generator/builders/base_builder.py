from abc import ABC, abstractmethod

from mlos.domain.models.decision import Decision
from mlos.domain.models.generated_code import GeneratedCode


class BaseBuilder(ABC):

    @abstractmethod
    def build(
        self,
        decision: Decision,
    ) -> GeneratedCode:
        pass
