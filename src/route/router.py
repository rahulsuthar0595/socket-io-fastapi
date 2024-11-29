from fastapi import APIRouter
from src.api.v1.views import socket_io, user_auth, user_chat

v1_router = APIRouter(prefix="/api/v1")

v1_router.include_router(socket_io.router, tags=["Socket IO API"])
v1_router.include_router(user_auth.router, tags=["User Auth API"])
v1_router.include_router(user_chat.router, tags=["User Chat Socket IO API"])