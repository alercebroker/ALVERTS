from db_plugins.db.sql import SQLQuery

session_options = {
    "autocommit": False,
    "autoflush": False,
    "query_cls": SQLQuery,
}
