import abc
from typing import List


class Controller(metaclass=abc.ABCMeta):
    @classmethod
    def __subclasshook__(cls, subclass):
        return (
            hasattr(subclass, "get_stream_lag_report")
            and callable(subclass.get_stream_lag_report)
            and hasattr(subclass, "get_db_count_report")
            and callable(subclass.get_db_count_report)
            or NotImplemented
        )

    @abc.abstractmethod
    def get_stream_lag_report(self, request_data: List[dict]):
        raise NotImplementedError

    @abc.abstractmethod
    def get_db_count_report(self, request_model: object):
        raise NotImplementedError
