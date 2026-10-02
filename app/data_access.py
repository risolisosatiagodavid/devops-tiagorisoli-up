from sqlalchemy import select

from app.database import ItemModel, SessionLocal
from app.schemas import Item


class InventoryRepository:
    def __init__(self) -> None:
        self.session_factory = SessionLocal

    @staticmethod
    def _to_item(item_model: ItemModel) -> Item:
        return Item(
            name=item_model.name,
            price=item_model.price,
            quantity=item_model.quantity,
        )

    def get_all(self) -> dict[int, Item]:
        with self.session_factory() as session:
            item_models = session.execute(
                select(ItemModel).order_by(ItemModel.id)
            ).scalars().all()

        return {
            item_model.id: self._to_item(item_model)
            for item_model in item_models
        }

    def get_by_id(self, item_id: int) -> Item | None:
        with self.session_factory() as session:
            item_model = session.get(ItemModel, item_id)
            if item_model is None:
                return None
            return self._to_item(item_model)

    def create(self, item: Item) -> int:
        with self.session_factory() as session:
            item_model = ItemModel(
                name=item.name,
                price=item.price,
                quantity=item.quantity,
            )
            session.add(item_model)
            session.commit()
            session.refresh(item_model)
            return item_model.id

    def update(self, item_id: int, changes: dict) -> Item | None:
        with self.session_factory() as session:
            item_model = session.get(ItemModel, item_id)
            if item_model is None:
                return None

            for field, value in changes.items():
                setattr(item_model, field, value)

            session.commit()
            session.refresh(item_model)
            return self._to_item(item_model)

    def delete(self, item_id: int) -> bool:
        with self.session_factory() as session:
            item_model = session.get(ItemModel, item_id)
            if item_model is None:
                return False

            session.delete(item_model)
            session.commit()
            return True

    def clear(self) -> None:
        with self.session_factory() as session:
            session.query(ItemModel).delete()
            session.commit()


