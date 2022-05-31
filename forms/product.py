from typing import List
from typing import Optional
from utils.update_card import update_card
from fastapi import Request
from utils.get_cards import get_cards
class ProductForm:
    def __init__(self, request: Request):
        self.request: Request = request
        self.errors: List = []
        self.messages: List = []
        self.cards = None
        self.name: Optional[str] = None

    async def load_data(self):
        form = await self.request.form()
        self.name = form.get("name").strip()
        self.token = form.get("token").strip()
        self.id = form.get("id")

    async def is_valid(self):
        self.cards = await get_cards(self.token)
        self.cards = self.cards['result']['cards']
        for card in self.cards:
            card['name'] = card['object']
            for _ in card['addin']:
                if _['type'] == 'Наименование':
                    card['name'] = _['params'][0]['value']
        for card in self.cards:
            if card['imtId'] == int(self.id):
                result = await update_card(self.token,card, self.name)
                if 'error' in result.keys():
                    self.errors.append(result['error'])
                    return False
                else:
                    self.messages.append('Успешно обновлено')
                card['object'] = self.name
                with open('3.json','w',encoding='utf-8') as f:
                    f.write(str(card))
                print(result)
        return True