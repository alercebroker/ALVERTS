import abc


class IsDBVerifier(metaclass=abc.ABCMeta):
    @classmethod
    def __subclasshook__(cls, subclass):
        return (
            hasattr(subclass, "get_db_report")
            and callable(subclass.get_db_report)
            or NotImplemented
        )

    @abc.abstractmethod
    def get_db_report(self, request_model: object):
        """Load in the data set"""
        raise NotImplementedError
