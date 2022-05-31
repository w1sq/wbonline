from typing import List
from typing import Optional

from fastapi import Request
from utils.captcha import CaptchaController

class LoginForm:
    def __init__(self, request: Request):
        self.request: Request = request
        self.errors: List = []
        self.email: Optional[str] = None
        self.password: Optional[str] = None
        self.captcha: Optional[str] = None
        self.captcha_id: Optional[str] = None

    async def load_data(self):
        form = await self.request.form()
        self.email = form.get("email")
        self.captcha = form.get("captcha")
        self.captcha_id = form.get('captcha_id')
        self.password = form.get("password")

    async def is_valid(self):
        captcha_controller = CaptchaController()
        if not self.email or not (self.email.__contains__("@")):
            self.errors.append("Email is required")
        if not self.password or not len(self.password) >= 4:
            self.errors.append("A valid password is required")
        print(self.captcha_id, self.captcha)
        if not captcha_controller.check(self.captcha_id, self.captcha):
            print(1)
            self.errors.append('Неправильно введена капча')
        if not self.errors:
            return True
        return False