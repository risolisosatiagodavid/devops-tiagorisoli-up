from app.schemas import Item


class InventoryRepository:
    def __init__(self) -> None:
        self._items: dict[int, Item] = {
            1: Item(name="Teclado Mecánico", price=75.5, quantity=10),
            2: Item(name="Mouse Inalámbrico", price=45.0, quantity=25),
        }

    def get_all(self) -> dict[int, Item]:
        return self._items

    def get_by_id(self, item_id: int) -> Item | None:
        return self._items.get(item_id)

    def create(self, item: Item) -> int:
        new_id = max(self._items.keys(), default=0) + 1
        self._items[new_id] = item
        return new_id

    def delete(self, item_id) -> bool:
        bool deleted = self._items.pop(item_id, None)
        if deleted is None:
            return false
        return true

