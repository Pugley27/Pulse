import aiohttp
import httpx

class GuildAPI:
    def __init__(self, base_url, api_key):
        self.base_url = base_url
        self.headers = {"x-api-key": api_key}
        print(f"GuildAPI initialized with base URL: {self.base_url}")   

    async def call_api(method, url, data=None):
        async with httpx.AsyncClient() as client:
           if method == "GET":
              return await client.get(url)
           return await client.post(url, json=data)
        
    async def update_cruor(self, member_id: int, name: str, amount: int):
        url = f"{self.base_url}/currency/add-cruor/"
        print(f"Updating Cruor for member ID {member_id} by {amount}. URL: {url}")
        params = {"member_id": member_id, "display_name": name, "cruor_amount": amount}
        return await self._post(url, params)

    async def get_balance(self, member_id: int):
        url = f"{self.base_url}/currency/balance/{member_id}"
        print(f"Fetching balance for member ID {member_id}. URL: {url}")
        return await self._get(url)

    async def add_item(self, name: str, description: str):
        url = f"{self.base_url}/auctions/add-item"
        print(f"Adding item: {name}. URL: {url}")
        params = {"name": name, "description": description}
        return await self._post(url, params)

    async def add_auction(self, name: str, description: str, item_id: int):
        url = f"{self.base_url}/auctions/add-auction"
        print(f"Adding auction: {name}. URL: {url}")
        params = {"name": name, "description": description, "item_id": item_id}
        return await self._post(url, params)
    
    async def get_active_auctions(self):    
        url = f"{self.base_url}/auctions/active"
        print(f"Fetching active auctions. URL: {url}")
        return await self._get(url)     
    
    async def _get(self, url):
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=self.headers) as resp:
                resp = await resp.json()
                print(f"API Response: {resp}")
                return resp
            
    async def _post(self, url, params):
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=self.headers, json=params) as resp:
                resp = await resp.json()
                print(f"API Response: {resp}")
                return resp

