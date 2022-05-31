import aiohttp
from aiohttp.client_exceptions import ContentTypeError

async def get_cards(token: str):
  payload =  {
  "params": {
    "query": {
      "limit": 50,
      "offset": 0
    },
    "filter": {
      "order": {
        "column": "createdAt",
        "order": "desc"
      },
      "find": [],
      "filter": []
    },
    "supplierId": "8514c619-cd8e-53a4-8d7a-afd08a42d08a"
  },
  "jsonrpc": "2.0",
  "id": "json-rpc_19"
} 
  headers = {'Authorization':token, "accept": "application/json",  "Content-Type": "application/json"}
  payload = str(payload)
  async with aiohttp.ClientSession(headers=headers) as session:
      async with session.post('https://suppliers-api.wildberries.ru/card/list', headers=headers, data=payload.replace("'", '\"')) as data:
          try:
              return await data.json()
          except ContentTypeError:
              return False