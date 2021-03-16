import abc


class RequestModelCreator(metaclass=abc.ABCMeta):
    @classmethod
    def __subclasshook__(cls, subclass):
        return hasattr(subclass, "to_request_model") and callable(
            subclass.to_request_model
        )

    @abc.abstractmethod
    def to_request_model(self, request, report):
        raise NotImplementedError
