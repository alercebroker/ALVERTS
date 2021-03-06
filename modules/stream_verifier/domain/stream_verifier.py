import abc


class IStreamVerifier(metaclass=abc.ABCMeta):
    @classmethod
    def __subclasshook__(cls, subclass):
        return (
            hasattr(subclass, "get_lag_report")
            and callable(subclass.get_lag_report)
            and hasattr(subclass, "get_message_report")
            and callable(subclass.get_message_report)
            or NotImplemented
        )

    @abc.abstractmethod
    def get_lag_report(self, request_model: object):
        """Load in the data set"""
        raise NotImplementedError

    @abc.abstractmethod
    def get_message_report(self, request_model: object):
        """Extract text from the data set"""
        raise NotImplementedError
