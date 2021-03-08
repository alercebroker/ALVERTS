from core.container import ApplicationContainer
from modules import stream_verifier
from dependency_injector.wiring import inject, Provide
import sys


class AlertSystem:
    def __init__(self):
        self.container = ApplicationContainer()
        self.container.wire([sys.modules[__name__], stream_verifier])

    @inject
    def _get_slack_controller(self, container=Provide[ApplicationContainer]):
        return container.verifiers_package.stream_verifier

    def get_controller(self, controller_name: str):
        getter = self.__getattribute__(f"_get_{controller_name}_controller")
        return getter()
