import aiohttp

class GuildAPI:
    def __init__(self, base_url, api_key):
        self.base_url = base_url
        self.headers = {"x-api-key": api_key}
        print(f"GuildAPI initialized with base URL: {self.base_url}")   

    async def update_cruor(self, member_id: int, amount: int):
        url = f"{self.base_url}/currency/add-cruor/"
        print(f"Updating Cruor for member ID {member_id} by {amount}. URL: {url}")
        params = {"member_id": member_id, "cruor_amount": amount}
        return await self._post(url, params)

    async def _post(self, url, params):
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=self.headers, json=params) as resp:
                resp = await resp.json()
                print(f"API Response: {resp}")
                return resp

