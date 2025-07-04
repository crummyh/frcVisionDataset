from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, Request
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from app.api import auth_v1, internal_v1, public_v1, web
from app.db.database import init_db
from app.services import buckets


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    buckets.init()
    yield

description = """
Docs and stuff goes here!!!
"""

tags_metadata = [
    {
        "name": "Stats",
        "description": "Get *information* about the dataset",
    },
    {
        "name": "Public",
        "description": "Accessing these endpoints does not require an API key",
    },
    {
        "name": "Auth Required",
        "description": "An API key is needed to access these endpoints"
    }
]

app = FastAPI(
    title="Open FRC Vision",
    description=description,
    summary="Upload and download training data for FRC object detection.",
    version="0.0.1",
    terms_of_service="terms here",
    contact={
        "name": "Elijah Crum",
        "email": "elijah@crums.us"
    },
    license_info={
        "name": "MIT",
        "url": "https://github.com/crummyh/frcVisonDataset/blob/main/LICENSE"
    },
    openapi_tags=tags_metadata,
    lifespan=lifespan
)

app.mount("/static", StaticFiles(directory="app/web/static"), name="static")
app.mount("/internal", internal_v1.subapp) # TODO: Disable docs
app.include_router(public_v1.router, prefix="/api/v1")
app.include_router(web.router, include_in_schema=False)
app.include_router(auth_v1.router)

@app.get("/docs", include_in_schema=False)
async def swagger_ui_html(req: Request) -> HTMLResponse:
    root_path = req.scope.get("root_path", "").rstrip("/")
    openapi_url = root_path + app.openapi_url # type: ignore
    oauth2_redirect_url = app.swagger_ui_oauth2_redirect_url
    if oauth2_redirect_url:
        oauth2_redirect_url = root_path + oauth2_redirect_url
    return get_swagger_ui_html(
        openapi_url=openapi_url,
        title=app.title + " - Swagger UI",
        oauth2_redirect_url=oauth2_redirect_url,
        init_oauth=app.swagger_ui_init_oauth,
        swagger_favicon_url="/static/images/favicon.png",
        swagger_ui_parameters=app.swagger_ui_parameters,
    )

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
