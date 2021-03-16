import abc


class ReportPresenter(metaclass=abc.ABCMeta):
    @classmethod
    def __subclasshook__(cls, subclass):
        return (
            hasattr(subclass, "export_lag_report")
            and callable(subclass.export_lag_report)
            and hasattr(subclass, "handle_client_error")
            and callable(subclass.handle_client_error)
            and hasattr(subclass, "handle_external_error")
            and callable(subclass.handle_external_error)
        )

    @abc.abstractmethod
    def export_lag_report(self, report):
        raise NotImplementedError

    @abc.abstractmethod
    def handle_client_error(self, error):
        raise NotImplementedError

    @abc.abstractmethod
    def handle_external_error(self, error):
        raise NotImplementedError
