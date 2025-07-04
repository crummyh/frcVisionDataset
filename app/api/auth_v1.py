from datetime import datetime, timedelta, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel import Session

from app.core import config
from app.core.dependencies import (
    authenticate_user,
    create_access_token,
    get_current_active_user,
    get_password_hash,
)
from app.db.database import get_session
from app.models.models import Token, UserRole
from app.models.schemas import User

router = APIRouter()

@router.post("/token")
def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    session: Annotated[Session, Depends(get_session)]
):

    user = authenticate_user(session=session, username=form_data.username, password=form_data.password) # type: ignore
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=config.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username, "role": user.role.name}, expires_delta=access_token_expires
    )
    return Token(access_token=access_token, token_type="bearer")

@router.get("/users/me")
async def read_users_me(
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    return current_user

@router.post("/test/create-user")
def create_user(
    username: str,
    email: str,
    password: str,
    role: UserRole,
    session: Annotated[Session, Depends(get_session)]
):
    user = User(
        username=username,
        email=email,
        password=get_password_hash(password),
        created_at=datetime.now(timezone.utc),
        team=None,
        role=role
    )
    try:
        session.add(user)
    except:
        session.rollback()
        raise
    else:
        session.commit()
