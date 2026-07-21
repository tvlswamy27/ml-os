from abc import ABC, abstractmethod

class Storage(ABC):

    @abstractmethod
    def save(self):
        ...

    @abstractmethod
    def load(self):
        ...