
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, Security
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from pydantic import UUID4
from sqlmodel import Session, asc, select
from starlette.status import HTTP_404_NOT_FOUND

from app.core.dependencies import RateLimiter, minimum_role, require_role
from app.core.helpers import (
    get_id_from_team_number,
    get_team_number_from_id,
    get_user_from_username,
)
from app.db.database import get_session
from app.models.models import (
    ImageReviewStatus,
    ReviewMetadata,
    UserRole,
    image_response,
)
from app.models.schemas import Image, LabelCategory, LabelSuperCategory, User
from app.services import buckets

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

@subapp.get("/review-image", dependencies=[Depends(RateLimiter(requests_limit=5, time_window=5))])
def get_image_for_review(
    current_user: Annotated[User, Security(minimum_role(UserRole.MODERATOR))],
    session: Annotated[Session, Depends(get_session)],
    target_status: ImageReviewStatus
) -> ReviewMetadata:

    statement = (
        select(Image).where(Image.review_status == target_status)
        .order_by(asc(Image.created_at)) # type: ignore
        .limit(1)
    )
    image = session.exec(statement).one()
    if not image:
        raise LookupError()

    assert image.id
    return ReviewMetadata(
        id=image.id,
        annotations=image.annotations,
        created_at=image.created_at,
        created_by=get_team_number_from_id(image.created_by, session),
        batch=image.batch,
        review_status=image.review_status
    )

@subapp.put("/review-image", dependencies=[Depends(RateLimiter(requests_limit=5, time_window=5))])
def update_image_review_status(
    new_data: ReviewMetadata,
    session: Annotated[Session, Depends(get_session)],
    current_user: Annotated[User, Security(minimum_role(UserRole.MODERATOR))],
    remove_image: bool = False
):
    image = session.get(Image, new_data.id)
    if not image:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail="Image not found"
        )

    if remove_image:
        session.delete(image)
        session.commit()
        return

    image.batch = new_data.batch
    image.created_at = new_data.created_at
    image.created_by = get_id_from_team_number(new_data.created_by, session)
    image.annotations = new_data.annotations
    image.review_status = new_data.review_status
    session.add(image)

    session.commit()

@subapp.get("/image/{image_id}", dependencies=[Depends(RateLimiter(requests_limit=5, time_window=5))])
def get_image(
    image_id: UUID4,
    current_user: Annotated[User, Security(minimum_role(UserRole.MODERATOR))]
):
    return image_response(buckets.get_image(image_id))

@subapp.post("/token", dependencies=[Depends(RateLimiter(requests_limit=10, time_window=5))])
def redirect_token():
    """
    Redirects requests from here to the main auth router
    """
    return RedirectResponse(url="/token", status_code=307)

@subapp.put("/change-user-role", dependencies=[Depends(RateLimiter(requests_limit=5, time_window=5))])
def change_user_role(
    username: str,
    new_role: UserRole,
    session: Annotated[Session, Depends(get_session)],
    current_user: Annotated[User, Security(require_role(UserRole.ADMIN))]
):
    user = get_user_from_username(username, session)
    user.role = new_role
    session.add(user)
    session.commit()

@subapp.put("/categories/super/create")
def create_label_super_category(
    category: LabelSuperCategory,
    session: Annotated[Session, Depends(get_session)],
    current_user: Annotated[User, Security(minimum_role(UserRole.MODERATOR))]
):
    session.add(category)
    session.commit()

@subapp.put("/categories/create")
def create_label_category(
    category: LabelCategory,
    session: Annotated[Session, Depends(get_session)],
    current_user: Annotated[User, Security(minimum_role(UserRole.MODERATOR))]
):
    session.add(category)
    session.commit()
