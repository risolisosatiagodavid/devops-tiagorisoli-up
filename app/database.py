from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

DATABASE_URL = "sqlite:///./inventory.db"

engine = create_engine(
	DATABASE_URL,
	connect_args={"check_same_thread": False},
)


class Base(DeclarativeBase):
	pass


SessionLocal = sessionmaker(
	autocommit=False,
	autoflush=False,
	bind=engine,
)


def get_db() -> Generator[Session, None, None]:
	db = SessionLocal()
	try:
		yield db
	finally:
		db.close()

