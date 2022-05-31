from email.policy import default
from textwrap import indent
from db.base_class import Base
from sqlalchemy import Boolean
from sqlalchemy import Column
from sqlalchemy import Integer
from sqlalchemy import String


class User(Base):
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    email = Column(String, nullable=False, unique=True, index=True)
    password = Column(String, nullable=False)
    token = Column(String, default='')
    is_superuser = Column(Boolean(), default=False)