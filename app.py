from fastapi import FastAPI, Request, HTTPException, status
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fast_captcha import iCaptcha
from utils.captcha import CaptchaController
from sqlalchemy.exc import IntegrityError
from fastapi import Depends
from fastapi.responses import StreamingResponse, RedirectResponse
from sqlalchemy.orm import Session
from db.session import engine
from db.session import get_db
from db.base import Base
from schemas.users import UserCreate
from forms.registration import UserCreateForm
from db.repository.login import get_user
from forms.login import LoginForm
from schemas.tokens import Token
from fastapi.security import OAuth2PasswordRequestForm
from db.repository.users import create_new_user
from datetime import timedelta
from utils.security import create_access_token
from fastapi.security import OAuth2PasswordBearer
from jose import jwt
from fastapi import Response
from jose import JWTError
from db.models.users import User
from fastapi.openapi.models import OAuthFlows as OAuthFlowsModel
from typing import Optional, Dict, Tuple
from fastapi.security.utils import get_authorization_scheme_param
from fastapi.security import OAuth2
from starlette.responses import FileResponse
from forms.token import TokenForm
from forms.product import ProductForm

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login/token")


app = FastAPI()
captcha_controller = CaptchaController()
Base.metadata.create_all(bind=engine)
app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")

@app.get('/favicon.ico')
async def favicon():
    return FileResponse('favicon.ico')

class OAuth2PasswordBearerWithCookie(OAuth2):
    def __init__(
        self,
        tokenUrl: str,
        scheme_name: Optional[str] = None,
        scopes: Optional[Dict[str, str]] = None,
        auto_error: bool = True,
    ):
        if not scopes:
            scopes = {}
        flows = OAuthFlowsModel(password={"tokenUrl": tokenUrl, "scopes": scopes})
        super().__init__(flows=flows, scheme_name=scheme_name, auto_error=auto_error)

    async def __call__(self, request: Request) -> Optional[str]:
        authorization: str = request.cookies.get(
            "access_token"
        )

        scheme, param = get_authorization_scheme_param(authorization)
        if not authorization or scheme.lower() != "bearer":
            if self.auto_error:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Not authenticated",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            else:
                return None
        return param

def get_current_user_from_token(
    token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
    )
    try:
        payload = jwt.decode(
            token, "SECRET_KEY", algorithms=["HS256"]
        )
        username: str = payload.get("sub")
        print("username/email extracted is ", username)
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    user = get_user(username=username, db=db)
    if user is None:
        raise credentials_exception
    return user


@app.get("/", response_class=HTMLResponse)
async def main(request: Request, db: Session = Depends(get_db)):
    token = request.cookies.get("access_token")
    if token:
        scheme, param = get_authorization_scheme_param(
            token
        ) 
        current_user: User = get_current_user_from_token(token=param, db=db)
        return templates.TemplateResponse("main.html",{"request": request, 'active_tab': 'main','user':current_user})
    return templates.TemplateResponse("main.html",{"request": request, 'active_tab': 'main','user':''})


@app.post("/", response_class=HTMLResponse)
async def main(request: Request, db: Session = Depends(get_db)):
    token = request.cookies.get("access_token")
    scheme, param = get_authorization_scheme_param(
            token
        )
    current_user: User = get_current_user_from_token(token=param, db=db)
    form = await request.form()
    if form.get('name'):
        form = ProductForm(request)
        await form.load_data()
        print(form.name)
        if await form.is_valid():
            return templates.TemplateResponse("main.html",{"request": request, 'active_tab': 'main','user':current_user, "cards": form.cards, "messages": form.messages, "token": form.token})
        return templates.TemplateResponse("main.html",{"request": request, 'active_tab': 'main','user':current_user, "cards": form.cards,"errors": form.errors , "token": form.token })
    else:
        form = TokenForm(request)
        await form.load_data()
        if await form.is_valid():
            print(len(form.cards))
            return templates.TemplateResponse("main.html",{"request": request, 'active_tab': 'main','user':current_user, "cards": form.cards, "token": form.token})
        return templates.TemplateResponse("main.html",{"request": request, 'active_tab': 'main','user':current_user, "errors": form.errors, "token": form.token})

@app.get("/logout")
async def logout(request: Request, response: Response):
    response = templates.TemplateResponse("main.html", {"request": request, 'active_tab': 'main','user':''})
    response.delete_cookie("access_token")
    return response

@app.get('/captcha/{id}')
async def captcha_img(id:str):
    try:
        img = captcha_controller.get_image(id)
        return StreamingResponse(content=img, media_type='image/jpeg')
    except ValueError:
        raise HTTPException(status_code=404, detail="Captcha not found")

@app.get("/login", response_class=HTMLResponse)
async def read_item(request: Request):
    captcha = captcha_controller.generate()
    return templates.TemplateResponse("login.html",{"request": request, 'active_tab': 'log', 'captcha_id': captcha.id})

@app.post("/login", response_class=HTMLResponse)
async def login(request: Request, db: Session = Depends(get_db)):
    form = LoginForm(request)
    await form.load_data()
    if await form.is_valid():
        try:
            response= RedirectResponse(
                "/", status_code=status.HTTP_302_FOUND
            )
            login_for_access_token(response=response, form_data=form, db=db)
            return response
        except HTTPException:
            form.__dict__.update(msg="")
            form.__dict__.get("errors").append("Incorrect Email or Password")

    captcha = captcha_controller.generate()
    form.__dict__.update(active_tab='log')
    form.__dict__.update(captcha_id=captcha.id)
    return templates.TemplateResponse("login.html", form.__dict__)


def authenticate_user(username: str, password: str, db: Session = Depends(get_db)):
    user = get_user(username=username, db=db)
    if not user:
        return False
    if not password == user.password:
        return False
    return user


@app.post("/token", response_model=Token)
def login_for_access_token(
    response: Response,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    user = authenticate_user(form_data.email, form_data.password, db)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )
    access_token_expires = timedelta(minutes=1440)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    response.set_cookie(
        key="access_token", value=f"Bearer {access_token}", httponly=True
    )
    return {"access_token": access_token, "token_type": "bearer"}


@app.get("/signup", response_class=HTMLResponse)
async def read_item(request: Request):
    captcha = captcha_controller.generate()
    return templates.TemplateResponse("signup.html",{"request": request, 'active_tab': 'reg', 'captcha_id': captcha.id})

@app.post("/signup", response_class=HTMLResponse)
async def register(request: Request, db: Session = Depends(get_db)):
    form = UserCreateForm(request)
    await form.load_data()
    form.__dict__.update(active_tab='reg')
    if await form.is_valid():
        user = UserCreate(
            email=form.email, password=form.password1
        )
        try:
            user = create_new_user(user=user, db=db)
            return RedirectResponse(
                "/", status_code=status.HTTP_302_FOUND
            )
        except IntegrityError:
            captcha = captcha_controller.generate()
            form_dict = form.__dict__
            form.__dict__.update(captcha_id=captcha.id)
            form.__dict__.get("errors").append("Duplicate username or email")
            return templates.TemplateResponse("signup.html", form.__dict__)
    captcha = captcha_controller.generate()
    form.__dict__.update(captcha_id=captcha.id)
    return templates.TemplateResponse("signup.html", form_dict)

@app.get("/reviews", response_class=HTMLResponse)
async def read_item(request: Request):
    return templates.TemplateResponse("reviews.html",{"request": request})

@app.get("/terms-of-service", response_class=HTMLResponse)
async def read_item(request: Request, db: Session = Depends(get_db)):
    token = request.cookies.get("access_token")
    if token:
        scheme, param = get_authorization_scheme_param(
            token
        ) 
        current_user: User = get_current_user_from_token(token=param, db=db)
        return templates.TemplateResponse("terms-of-service.html",{"request": request, 'active_tab': '','user':current_user})
    return templates.TemplateResponse("terms-of-service.html",{"request": request, 'active_tab': '','user':''})