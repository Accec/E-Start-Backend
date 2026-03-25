import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from core.pagination import PageResult, paginate_query


class FakeQuery:
    def __init__(self, items):
        self.items = list(items)
        self._offset = 0
        self._limit = len(self.items)

    async def count(self):
        return len(self.items)

    def offset(self, offset):
        self._offset = offset
        return self

    def limit(self, limit):
        self._limit = limit
        return self

    async def all(self):
        return self.items[self._offset : self._offset + self._limit]


class PaginationTestCase(unittest.IsolatedAsyncioTestCase):
    async def test_paginate_query_returns_structured_page_result(self):
        page = await paginate_query(FakeQuery([1, 2, 3, 4, 5]), page=2, page_size=2)

        self.assertIsInstance(page, PageResult)
        self.assertEqual(page.items, [3, 4])
        self.assertEqual(page.total_items, 5)
        self.assertEqual(page.total_pages, 3)
        self.assertEqual(page.page, 2)
        self.assertEqual(page.page_size, 2)


if __name__ == "__main__":
    unittest.main()
