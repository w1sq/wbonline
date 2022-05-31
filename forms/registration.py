from typing import List
from typing import Optional

from fastapi import Request
from utils.captcha import CaptchaController

class UserCreateForm:
    def __init__(self, request: Request):
        self.request: Request = request
        self.captcha_controller = None
        self.errors: List = []
        self.username: Optional[str] = None
        self.email: Optional[str] = None
        self.captcha: Optional[str] = None
        self.captcha_id: Optional[str] = None
        self.password1: Optional[str] = None
        self.password2: Optional[str] = None
        self.checkbox: Optional[bool] = None

    async def load_data(self):
        form = await self.request.form()
        self.email = form.get("email")
        self.captcha = form.get("captcha")
        self.captcha_id = form.get('captcha_id')
        self.checkbox = form.get('checkbox')
        self.password1 = form.get("password1")
        self.password2 = form.get("password2")

    async def is_valid(self):
        captcha_controller = CaptchaController()
        if not self.email or not (self.email.__contains__("@")):
            self.errors.append("Email необходим")
        if not self.password1 or not len(self.password1) >= 4:
            self.errors.append("Пароль должен содержать больше 4 символов")
        if self.password1 != self.password2:
            self.errors.append("Пароли должны совпадать")
        if not captcha_controller.check(self.captcha_id, self.captcha):
            self.errors.append('Неправильно введена капча')
        if self.checkbox != 'on':
            self.errors.append('Необходимо принять условия пользовательского соглашения')
        if not self.errors:
            return True
        return False