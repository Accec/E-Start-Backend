from dataclasses import dataclass
from typing import Generic, TypeVar


Item = TypeVar("Item")


@dataclass(frozen=True, slots=True)
class PageResult(Generic[Item]):
    # Keep pagination metadata explicit so repositories and presentation code
    # do not have to rely on positional tuple contracts.
    items: list[Item]
    total_items: int
    total_pages: int
    page: int
    page_size: int


class Paginator:
    def __init__(self, query, page_size):
        self.query = query
        self.page_size = max(1, int(page_size))
        self._total_items = 0
        self._total_pages = 0
        self._items = []

    async def paginate(self, page: int = 1):
        self._total_items = await self.query.count()
        self.page = max(1, int(page))
        self._total_pages = (self._total_items + self.page_size - 1) // self.page_size
        start = (self.page - 1) * self.page_size
        self._items = await self.query.offset(start).limit(self.page_size).all()

    @property
    def items(self):
        return self._items

    @property
    def total_pages(self):
        return self._total_pages

    @property
    def total_items(self):
        return self._total_items


async def paginate_query(query, page: int, page_size: int):
    paginator = Paginator(query, page_size=page_size)
    await paginator.paginate(page)
    return PageResult(
        items=list(paginator.items),
        total_items=paginator.total_items,
        total_pages=paginator.total_pages,
        page=paginator.page,
        page_size=paginator.page_size,
    )
