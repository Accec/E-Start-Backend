import datetime

from sanic import response

class Paginator:
    def __init__(self, query, page_size):
        self.query = query
        self.page_size = max(1, int(page_size))  # 保证每页至少一条
        self._total_items = 0
        self._total_pages = 0
        self._items = []
        

    async def paginate(self, page:int=1):
        # 计算总条目数
        self._total_items = await self.query.count()
        self.page = max(1, int(page))  # 保证最小是第一页
        # 计算总页数
        self._total_pages = (self._total_items + self.page_size - 1) // self.page_size

        # 计算起始项
        start = (self.page - 1) * self.page_size
        # 获取当前页面的数据
        items = await self.query.offset(start).limit(self.page_size).all()

        self._items = items

    @property
    def items(self):
        return self._items
    
    @property
    def total_pages(self):
        return self._total_pages
    
    @property
    def total_items(self):
        return self._total_items

def http_response(code, msg='', result=None, status=200, **kwargs):
    output = {'code': code, 'msg': msg, 'results': result}
    if kwargs:
        output.update(kwargs)
    return response.json(output, status=status)

def get_timestamp():
    timestamp = int(datetime.datetime.utcnow().timestamp() * 1000)
    return timestamp