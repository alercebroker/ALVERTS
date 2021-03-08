import abc


class UseCase(metaclass=abc.ABCMeta):
    @classmethod
    def __subclasshook__(cls, subclass):
        return hasattr(subclass, "execute") and callable(subclass.execute)

    @abc.abstractmethod
    def execute(self, request, callbacks: dict):
        raise NotImplementedError
