import aiohttp

class GuildAPI:
    def __init__(self, base_url, api_key):
        self.base_url = base_url
        self.headers = {"x-api-key": api_key}

    async def update_cruor(self, member_id: int, amount: int):
        url = f"{self.base_url}/add-cruor/"
        params = {"user_id": member_id, "amount": amount}
        return await self._post(url, params)

    async def _post(self, url, params):
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=self.headers, params=params) as resp:
                return await resp.json()

