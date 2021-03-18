class MockPsqlService:
    def __init__(self, state):
        self.state == state

    def _execute(self, sql: str, parser):
        if self.state == "success":
            return parser([("oid1", 123), ("oid2", 456)])
