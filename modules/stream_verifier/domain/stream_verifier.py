import abc


class IStreamVerifier(metaclass=abc.ABCMeta):
    @classmethod
    def __subclasshook__(cls, subclass):
        return (
            hasattr(subclass, "get_lag_report")
            and callable(subclass.get_lag_report)
            or NotImplemented
        )

    @abc.abstractmethod
    def get_lag_report(self, request_model: object):
        """Load in the data set"""
        raise NotImplementedError
