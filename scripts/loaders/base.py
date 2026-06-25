from abc import ABC, abstractmethod


class BaseLoader(ABC):
    @abstractmethod
    def load_signals(self, record_id: str):
        ...

    @abstractmethod
    def load_annotations(self, record_id: str):
        ...

    @abstractmethod
    def load_metadata(self, record_id: str):
        ...
