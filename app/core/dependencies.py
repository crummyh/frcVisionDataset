from datetime import datetime, timedelta, timezone
from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, Request, Security, status
from fastapi.security import APIKeyHeader, OAuth2PasswordBearer
from jwt.exceptions import InvalidTokenError
from passlib.context import CryptContext
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlmodel import Session, select

from app.core import config
from app.db.database import get_session
from app.models.models import TokenData
from app.models.schemas import Team, User

# ==========={ Database }=========== #

SessionDep = Annotated[Session, Depends(get_session)]

# ==========={ Security }=========== #

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# ==========={ API Keys }=========== #

api_key_scheme = APIKeyHeader(name="x-api-key")

async def handle_api_key(req: Request, db: SessionDep, key: str = Security(api_key_scheme)):
    res = db.exec(
        select(Team).where(Team.api_key == key).where(not Team.disabled)
    )

    api_key_data = res.one()

    # No API key found:
    if not api_key_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid API key"
        )

    yield api_key_data

# ==========={ Passwords }=========== #

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def authenticate_user(
    session: Annotated[Session, Depends(get_session)],
    username: str,
    password: str
) -> User | None:
    user = session.exec(select(User).where(User.username == username)).one()
    if not user:
        return None
    assert user.password
    if not verify_password(password, user.password):
        return None
    return user

def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode,
        config.JWT_SECRET_TOKEN,
        algorithm=config.SECURE_ALGORITHM
    )
    return encoded_jwt

def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    session: Annotated[Session, Depends(get_session)]
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(
            token,
            config.JWT_SECRET_TOKEN,
            algorithms=[config.SECURE_ALGORITHM]
        )
        username = payload.get("sub")
        if username is None:
            raise credentials_exception

        token_data = TokenData(username=username)

    except InvalidTokenError:
        raise credentials_exception

    user = session.exec(select(User).where(User.username == token_data.username)).one()
    if user is None:
        raise credentials_exception

    return user

def get_current_active_user(
    current_user: Annotated[User, Depends(get_current_user)],
):
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

limiter = Limiter(key_func=get_remote_address)
