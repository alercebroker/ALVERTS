import abc


class Presenter(metaclass=abc.ABCMeta):
    @classmethod
    def __subclasshook__(cls, subclass):
        return (
            hasattr(subclass, "export_lag_report")
            and callable(subclass.export_lag_report)
            and hasattr(subclass, "export_db_report")
            and callable(subclass.export_db_report)
            and hasattr(subclass, "handle_client_error")
            and callable(subclass.handle_client_error)
            and hasattr(subclass, "handle_external_error")
            and callable(subclass.handle_external_error)
            and hasattr(subclass, "handle_parse_error")
            and callable(subclass.handle_parse_error)
            and hasattr(subclass, "handle_request_error")
            and callable(subclass.handle_request_error)
            or NotImplemented
        )

    @abc.abstractmethod
    def export_lag_report(self, report):
        raise NotImplementedError

    @abc.abstractmethod
    def export_db_report(self, report):
        raise NotImplementedError

    @abc.abstractmethod
    def handle_client_error(self, error: Exception):
        raise NotImplementedError

    @abc.abstractmethod
    def handle_external_error(self, error: Exception):
        raise NotImplementedError

    @abc.abstractmethod
    def handle_parse_error(self, error: Exception):
        raise NotImplementedError

    @abc.abstractmethod
    def handle_request_error(self, error: Exception):
        raise NotImplementedError
