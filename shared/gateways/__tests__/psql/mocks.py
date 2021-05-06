class MockPsqlService:
    def __init__(self, state, report_type):
        self.state = state
        self.report_type = report_type

    def execute(self, sql: str, parser):
        
        if self.report_type == "detections_report":
            if self.state == "success":
                return parser([])
            if self.state == "check_fail":
                return parser([("oid1", 123), ("oid2", 456)])
            if self.state == "external_error":
                raise Exception("fail")
        
        if self.report_type == "stamp_classifications_report":
            if self.state == "success":
                return parser([("class1", 123), ("class2", 456)])
            if self.state == "check_fail":
                return parser([("class1", 123), ("class2", 456)])
            if self.state == "external_error":
                raise Exception("fail")

    def connect(self, db_url: str):
        return
