import os
import alembic.command
import alembic.config
from fastapi import FastAPI
from sqladmin import Admin, ModelView
from fastapi.staticfiles import StaticFiles
from config import config
from fastapi.middleware.cors import CORSMiddleware
from logging import getLogger
from utils.api import APIResponse
from utils.dbadmin import MyAuth
from repository.schema import *
from repository import engine
from cron import scheduler
from contextlib import asynccontextmanager
import logging
import alembic
import threading

from views import view

log = getLogger(__name__)

app = FastAPI(
    docs_url="/api/docs" if not config["PROD"] else None,
    redoc_url="/api/redoc" if not config["PROD"] else None,
    openapi_url="/api/openapi.json" if not config["PROD"] else None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=config["ALLOWED_ORIGINS"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

for file in os.listdir("routes"):
    if not file.startswith("_"):
        module_name, _ = os.path.splitext(file)
        module = __import__(f"routes.{module_name}", fromlist=[module_name])
        app.include_router(module.router, prefix=f"/api/{module_name}")

app.include_router(view)
app.mount("/static", StaticFiles(directory="views/static"), name="static")


class UserAdmin(ModelView, model=User):
    column_list = ("id", "display_name", "email", "is_admin")
    column_labels = {
        "id": "User ID",
        "display_name": "Display Name",
        "email": "Email Address",
        "is_admin": "Admin Status",
    }
    column_searchable_list = ("display_name", "email")
    column_filters = ("is_admin",)


class ChallengeAdmin(ModelView, model=Challenge):
    column_list = ("id", "title", "services", "connection_info", "players")
    column_labels = {
        "id": "Challenge ID",
        "title": "Challenge Title",
        "services": "Associated Services",
        "connection_info": "Connection Information",
        "players": "Players",
    }
    column_searchable_list = ("title",)
    column_filters = ("services",)


class ServiceAdmin(ModelView, model=Service):
    column_list = (
        "id",
        "name",
        "image",
        "challenge",
        "privileged",
        "cpu",
        "memory",
        "ports",
        "environment",
        "cap_add",
    )
    column_labels = {
        "id": "Service ID",
        "name": "Service Name",
        "image": "Image",
        "challenge": "Challenge",
        "privileged": "Privileged",
        "cpu": "CPU Allocation",
        "memory": "Memory Allocation",
        "ports": "Ports",
        "environment": "Environment Variables",
        "cap_add": "Capabilities Added",
    }
    column_searchable_list = ("name", "challenge")
    column_filters = ("privileged", "cpu", "memory")


admin = Admin(app, engine, authentication_backend=MyAuth(os.urandom(64).hex()))

admin.add_view(UserAdmin)
admin.add_view(ChallengeAdmin)
admin.add_view(ServiceAdmin)

configs = {
    "host": config["HOST"],
    "port": config["PORT"],
    "reload": not config["PROD"],
    "workers": config["workers"] if config["PROD"] else 1,
}


@app.exception_handler(Exception)
async def exception_handler(request, exc):
    log.error(exc)
    return APIResponse.as_json(
        code=500,
        status="Internal Server Error",
        detail=str(exc),
    )


@asynccontextmanager
async def lifespan(app: FastAPI):
    alembic.command.upgrade(alembic.config.Config("alembic.ini"), "head")
    yield
    scheduler.shutdown()


scheduler.start()
file_handler = logging.FileHandler("/tmp/app.log")
file_handler.setFormatter(
    logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
)
file_handler.setLevel(logging.DEBUG)
logging.basicConfig(level=logging.DEBUG, handlers=[file_handler])

__all__ = ["app", "scheduler", "lifespan"]
