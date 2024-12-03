import socketio
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from config.config import settings
from src.api.v1.services.socket_io import SocketIOChatNamespace
from src.route.router import v1_router

app = FastAPI()
app.include_router(v1_router)

sio_redis_mgr = socketio.AsyncRedisManager(url=f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}/0")

sio = socketio.AsyncServer(
    async_mode="asgi",
    cors_allowed_origins="*",
    client_manager=sio_redis_mgr,
)

sio_app = socketio.ASGIApp(sio, socketio_path="/socket.io")

# sio.register_namespace(SocketIODefaultNamespace("/"))
# sio.register_namespace(SocketIOAdminNamespace("/admin"))
sio.register_namespace(SocketIOChatNamespace("/"))

app.mount("/socket.io", sio_app)
app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")
