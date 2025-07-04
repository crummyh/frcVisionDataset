from typing import Annotated

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse

from app.core.dependencies import get_current_active_user
from app.models.schemas import User

subapp = FastAPI()
origins = [ # TODO: UPDATE WITH ACTUAL URL
    "http://127.0.0.1:8000",
    "https://127.0.0.1:8000"
]
subapp.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

@subapp.post("/token")
def redirect_token():
    """
    Redirects requests from here to the main auth router
    """
    return RedirectResponse(url="/token", status_code=307)

@subapp.get("/example")
def test(
    # user: Annotated[
    #     User,
    #     Depends(require_role(UserRole.TEAM_LEADER, UserRole.ADMIN, UserRole.MODERATOR))
    # ]
    user: Annotated[User, Depends(get_current_active_user)]
):
    return User
