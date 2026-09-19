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

    def update(self, item_id: int, changes: dict) -> Item | None:
        item = self._items.get(item_id)
        if item is None:
            return None

        updated_item = item.model_copy(update=changes)
        self._items[item_id] = updated_item
        return updated_item

    def delete(self, item_id) -> bool:
        return self._items.pop(item_id, None) is not None


