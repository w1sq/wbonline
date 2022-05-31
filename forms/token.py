from typing import List
from typing import Optional

from fastapi import Request
from utils.get_cards import get_cards
class TokenForm:
    def __init__(self, request: Request):
        self.request: Request = request
        self.errors: List = []
        self.cards = None
        self.token: Optional[str] = None

    async def load_data(self):
        form = await self.request.form()
        self.token = form.get("token").strip()

    async def is_valid(self):
        cards = await get_cards(self.token)
        if not cards:
            self.errors.append('Вы ввели некорректный токен. Читайте ниже как правильно получить токен НОВОГО образца в кабинете селлера')
        elif 'error' in cards.keys():
            self.errors.append(cards['error']['message'])
            return False
        else:
            self.cards = cards['result']['cards']
            for card in self.cards:
                card['name'] = card['object']
                for _ in card['addin']:
                    if _['type'] == 'Наименование':
                        card['name'] = _['params'][0]['value']
        if not self.errors:
            return True
        return False