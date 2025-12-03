from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class Database:
    def __init__(self, url: str = "sqlite:///news_database.db"):
        self.engine = create_engine(url)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        self._session: Session | None = None

    def create_tables(self):
        Base.metadata.create_all(self.engine)

    def get_session(self) -> Session:
        db = self.SessionLocal()
        try:
            yield db
        finally:
            db.close()

    @property
    def session(self) -> Session:
        if self._session is None:
            self._session = self.SessionLocal()
        return self._session

database = Database()
