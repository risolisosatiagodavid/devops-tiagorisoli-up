from collections.abc import Generator

from sqlalchemy import Float, Integer, String, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, sessionmaker

DATABASE_URL = "sqlite:////data/inventory.db"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
)


class Base(DeclarativeBase):
    pass


class ItemModel(Base):
    __tablename__ = "items"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    price: Mapped[float] = mapped_column(Float, nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)


SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


def init_db() -> None:
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as session:
        if session.query(ItemModel).count() == 0:
            session.add_all(
                [
                    ItemModel(name="Teclado Mecánico", price=75.5, quantity=10),
                    ItemModel(name="Mouse Inalámbrico", price=45.0, quantity=25),
					ItemModel(name="Monitor 24 pulgadas", price=150.0, quantity=5),
					ItemModel(name="Auriculares Gaming", price=60.0, quantity=15),
					ItemModel(name="Webcam HD", price=80.0, quantity=8),
					ItemModel(name="Disco Duro Externo 1TB", price=100.0, quantity=12),
					ItemModel(name="Memoria USB 32GB", price=15.0, quantity=30),
					ItemModel(name="Router Wi-Fi 6", price=120.0, quantity=7),
					ItemModel(name="Placa de Video", price=800.0, quantity=3),
                ]
            )
            session.commit()


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

