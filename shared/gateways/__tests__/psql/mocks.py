class MockPsqlService:
    def __init__(self, state):
        self.state = state

    def execute(self, sql: str, parser):
        if self.state == "success":
            return parser([])
        if self.state == "check_fail":
            return parser([("oid1", 123), ("oid2", 456)])
        if self.state == "external_error":
            raise Exception("fail")
