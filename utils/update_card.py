import aiohttp
from aiohttp.client_exceptions import ContentTypeError
async def get_card(token: str, itm_id: int) -> dict:
    payload =  {
        "id": "4cdf17da-5e7b-4c56-9531-7437d44a13fb",
        "jsonrpc": "2.0", 
        "params": {
            "imtID": itm_id   
        }
}
    headers = {'Authorization':token, "accept": "application/json",  "Content-Type": "application/json"}
    payload = str(payload)
    async with aiohttp.ClientSession(headers=headers) as session:
        async with session.post('https://suppliers-api.wildberries.ru/card/cardByImtID', headers=headers, data=payload.replace("'", '\"')) as data:
            try:
                all = await data.json()
                return all['result']['card']
            except ContentTypeError:
                return False

def prepare_card(card: dict) -> dict:
    keys = ['id', 'imtId', 'object','countryProduction', 'addin']
    new_card = {}
    for key in card.keys():
        if key in keys:
            new_card[key] = card[key]
        elif key == 'nomenclatures':
            new_numenclatures = []
            for i in range(len(card['nomenclatures'])):
                small_numenclature=card['nomenclatures'][i]
                new_small_numenclature = {}
                for small_key in small_numenclature.keys():
                    if small_key != 'variations':
                        new_small_numenclature[small_key] = card['nomenclatures'][i][small_key]
                    else:
                        new_small_numenclature['variations'] = []
                        for variation in card['nomenclatures'][i]['variations']:
                            variation.pop('errors')
                            new_small_numenclature['variations'].append(variation)
                new_numenclatures.append(new_small_numenclature)
            new_card['nomenclatures'] = new_numenclatures
    return new_card

async def update_card(token: str, card: dict, name: str) -> dict:
    card = prepare_card(card)
    for item in card['addin']:
        if item['type'] == 'Наименование':
            item['params'][0]['value'] = name
    payload =  {
  "params": {
    "card": card
  },
  "jsonrpc": "2.0",
  "id": "e7ba66f5-bdde-48b5-9e14-ea6a285bf57"
}
    headers = {'Authorization':token, "accept": "application/json",  "Content-Type": "application/json"}
    payload = str(payload)
    async with aiohttp.ClientSession(headers=headers) as session:
        async with session.post('https://suppliers-api.wildberries.ru/card/update', headers=headers, data=payload.replace("'", '\"')) as data:
            try:
                data = await data.json()
                with open('answer.json','w',encoding='utf-8') as f:
                    f.write(str(data))
                return data
            except ContentTypeError:
                return False