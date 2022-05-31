from fast_captcha import iCaptcha
from io import BytesIO
from typing import Dict
import uuid
from time import time

def singleton(class_):
    instances = {}
    def getinstance(*args, **kwargs):
        if class_ not in instances:
            instances[class_] = class_(*args, **kwargs)
        return instances[class_]
    return getinstance

class Captcha:
    TTL = 86400
    def __init__(self) -> None:
        self.id = uuid.uuid4().hex
        self._timestamp = time()
        self.img, self.text = iCaptcha()
    
@singleton
class CaptchaController:
    def __init__(self) -> None:
        self._container:Dict[str, Captcha] = {}
    
    def generate(self) -> Captcha:
        for id in list(self._container.keys()):
            if time() - self._container[id]._timestamp > Captcha.TTL:
                del self._container[id]
        #Maler
        captcha = Captcha()
        self._container[captcha.id] = captcha
        return captcha
    
    def check(self, id:str, text) -> bool:
        if id not in self._container:
            return False
        captcha = self._container.pop(id)
        return captcha.text.lower() == text.lower()
    
    def get_image(self, id:str) -> BytesIO:
        if id not in self._container:
            raise ValueError(f'captcha with id {id} does not exists')
        return self._container[id].img