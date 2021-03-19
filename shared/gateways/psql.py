from contextlib import contextmanager, AbstractContextManager
from typing import Callable
import logging

from sqlalchemy import create_engine, orm
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session


class PsqlService:
    def __init__(self) -> None:
        self._init_log()
        self.db_url = ""

    def connect(self, db_url: str):
        if self.db_url != db_url:
            self.db_url = db_url
            self._engine.dispose()
            self._engine = create_engine(db_url, echo=True)
            self._session_factory = orm.scoped_session(
                orm.sessionmaker(
                    autocommit=False,
                    autoflush=False,
                    bind=self._engine,
                ),
            )

    def _init_log(self, logger=None) -> None:
        self.logger = logger or logging.getLogger(self.__class__.__name__)
        self.logger.setLevel(logging.INFO)

    def execute(self, sql: str, parser: Callable):
        with self.session() as sess:
            res = sess.execute(sql).fetchall()
            return parser(res)

    @contextmanager
    def session(self):
        session: Session = self._session_factory()
        try:
            yield session
        except Exception as e:
            logger.exception("Session rollback because of exception")
            session.rollback()
            raise e
        finally:
            session.close()
