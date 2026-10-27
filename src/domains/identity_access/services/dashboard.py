from ..ports import UserRepositoryPort


class DashboardService:
    def __init__(self, *, users: UserRepositoryPort):
        self.users = users

    async def get_dashboard(self, user_id: int):
        return await self.users.collect_dashboard(user_id)
