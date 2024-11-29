import json
from datetime import datetime
from typing import Any

import socketio
from fastapi import FastAPI

from config.config import settings
from logger.logger import logger
from src.api.v1.repository.mongo_core_repository import display_user_chats, insert_user_chat, fetch_user_data, \
    get_chat_history, save_user_chats


# NOTE: When using Namespace, the handler name must contain prefix 'on' keyword.


class SocketIODefaultNamespace(socketio.AsyncNamespace):

    @staticmethod
    def on_connect(sid, environ):
        logger.info(f"on_connect => {sid} - {environ}")

    async def on_disconnect(self, sid):
        logger.info(f"on_disconnect => {sid}")
        await self.server.shutdown()

    async def on_welcome_user(self, sid: str, data: Any):
        logger.info(f"welcome_user => {sid} - {data}")
        await self.emit("return_response", {"data": data.get("data")}, to=sid)

    async def on_room_chat(self, sid: str, data: Any):
        logger.info(f"room_chat => {sid} - {data}")
        await self.emit("return_response", {"data": data.get("data")}, room=data["room"], skip_sid=sid)

    async def on_join(self, sid: str, data: Any):
        logger.info(f"join_room => {sid} - {data}")
        room = data["room"]
        await self.enter_room(sid, room)
        await self.emit(
            "return_response", {"data": "Entered room: " + room},
            room=sid
        )

    async def on_leave(self, sid: str, data: Any):
        logger.info(f"leave_room => {sid} - {data}")
        room = data["room"]
        await self.leave_room(sid, room)
        await self.emit(
            "return_response", {"data": f"{sid} left room: {room}"},
            room=room
        )

    async def on_close_room(self, sid: str, data: Any):
        logger.info(f"close_room => {sid} - {data}")
        room = data["room"]
        await self.close_room(room)
        await self.emit(
            "return_response", {"data": "Close room: " + room},
            room=room
        )

    async def on_broadcast(self, sid: str, data: Any):
        logger.info(f"broadcast_message => {sid} - {data}")
        await self.emit(
            "return_response", {"data": data["data"]},
            skip_sid=sid  # Not broadcast message to sender.
        )

    async def on_list_rooms(self, sid: str, data: Any):
        logger.info(f"broadcast_message => {sid} - {data}")
        rooms = self.rooms(sid)
        await self.emit(
            "return_response", {"data": f"Rooms {rooms}"},
            to=sid  # Not return message to sender.
        )


class SocketIOAdminNamespace(socketio.AsyncNamespace):
    @staticmethod
    def on_connect(sid, environ):
        logger.info(f"on_connect admin => {sid} - {environ}")

    async def on_disconnect(self, sid):
        logger.info(f"on_disconnect admin => {sid}")
        await self.server.shutdown()

    async def on_welcome_user(self, sid: str, data: Any):
        logger.info(f"welcome_user admin => {sid} - {data}")
        await self.emit("return_response", {"data": data.get("data")}, to=sid)

    async def on_broadcast(self, sid: str, data: Any):
        logger.info(f"broadcast_message admin => {sid} - {data}")
        await self.emit(
            "return_response", {"data": data["data"]},
            skip_sid=sid  # Not broadcast message to sender.
        )


class SocketIOManager:

    def __init__(
            self, app: FastAPI, mount_location: str = "/socket.io", async_mode: str = "asgi",
            cors_allowed_origins: list['str'] | str = "*", namespace: str | None = None, **kwargs
    ):
        sio_redis_mgr = socketio.AsyncRedisManager(url=f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}/0")
        self.sio = socketio.AsyncServer(
            async_mode=async_mode,
            cors_allowed_origins=cors_allowed_origins,
            client_manager=sio_redis_mgr,
            **kwargs
        )
        self.sio_app = socketio.ASGIApp(self.sio, socketio_path=mount_location)
        app.mount(mount_location, self.sio_app)

        # To set up the admin dashboard, use instrument method and configured parameters.
        auth, mode = False, "development"
        if settings.SOCKET_IO_AUTH_ENABLED:
            auth, mode = {
                "username": settings.SOCKET_IO_ADMIN_USERNAME,
                "password": settings.SOCKET_IO_ADMIN_PASSWORD
            }, "production"

        self.sio.instrument(
            auth=auth, mode=mode,
            server_id=settings.SOCKET_IO_SERVER_ID,
        )

        self.sio.on("connect", self.on_connect, namespace)
        self.sio.on("disconnect", self.on_disconnect, namespace)
        self.sio.on("room_chat", self.room_chat, namespace)
        self.sio.on("join", self.join_room, namespace)
        self.sio.on("leave", self.leave_room, namespace)
        self.sio.on("close_room", self.close_room, namespace)
        self.sio.on("broadcast", self.broadcast_message, namespace)
        self.sio.on("list_rooms", self.list_rooms, namespace)
        self.sio.on("*", self.handle_any_event,
                    namespace)  # Here event defined as *, so it will any catch-all event handler.

    @staticmethod
    def on_connect(sid: str, environ: dict):
        logger.info(f"on_connect => {sid} - {environ}")

    async def on_disconnect(self, sid: str):
        logger.info(f"on_disconnect => {sid}")
        await self.sio.shutdown()

    async def handle_any_event(self, namespace: str, sid: str, data: Any):
        logger.info(f"handle_any_event => {namespace} - {sid} - {data}")
        await self.sio.emit("return_response", {"data": data.get("data")}, to=sid)

    async def room_chat(self, sid: str, data: Any):
        logger.info(f"room_chat => {sid} - {data}")
        await self.sio.emit("return_response", {"data": data.get("data")}, room=data["room"], skip_sid=sid)

    async def join_room(self, sid: str, data: Any):
        logger.info(f"join_room => {sid} - {data}")
        room = data["room"]
        await self.sio.enter_room(sid, room)
        await self.sio.emit(
            "return_response", {"data": "Entered room: " + room},
            room=sid
        )

    async def leave_room(self, sid: str, data: Any):
        logger.info(f"leave_room => {sid} - {data}")
        room = data["room"]
        await self.sio.leave_room(sid, room)
        await self.sio.emit(
            "return_response", {"data": f"{sid} left room: {room}"},
            room=room
        )

    async def close_room(self, sid: str, data: Any):
        logger.info(f"close_room => {sid} - {data}")
        room = data["room"]
        await self.sio.close_room(room)
        await self.sio.emit(
            "return_response", {"data": "Close room: " + room},
            room=room
        )

    async def broadcast_message(self, sid: str, data: Any):
        logger.info(f"broadcast_message => {sid} - {data}")
        await self.sio.emit(
            "return_response", {"data": data["data"]},
            skip_sid=sid  # Not broadcast message to sender.
        )

    async def list_rooms(self, sid: str, data: Any):
        logger.info(f"broadcast_message => {sid} - {data}")
        rooms = self.sio.rooms(sid)
        await self.sio.emit(
            "return_response", {"data": f"Rooms {rooms}"},
            to=sid  # Not return message to sender.
        )


class SocketIOChatNamespace(socketio.AsyncNamespace):
    @staticmethod
    def on_connect(sid, environ):
        logger.info(f"on_connect chat => {sid}")

    @staticmethod
    async def on_disconnect(sid):
        logger.info(f"on_disconnect chat => {sid}")

    async def on_user_joined(self, sid: str, data: Any):
        logger.info(f"user_joined chat => {sid} - {data}")
        response = await fetch_user_data()
        await self.emit("return_fetched_users", response, to=sid)

    async def on_broadcast(self, sid: str, data: Any):
        logger.info(f"broadcast_message chat => {sid} - {data}")
        await self.emit(
            "return_response", {"data": data["data"]},
            skip_sid=sid  # Not broadcast message to sender.
        )

    async def on_joined_list_messages(self, sid: str, data: Any):
        response = await display_user_chats()
        response = json.loads(json.dumps(response, default=str))
        await self.emit("chat_history", {"data": response}, to=sid)

    async def on_broadcast_message(self, sid: str, data: Any):
        user = data.get("user")
        message = data.get("message")
        if not user or not message:
            return
        response = await insert_user_chat({
            "user": user,
            "message": message,
        })
        response = json.loads(json.dumps(response, default=str))
        await self.emit(
            "new_chat",
            {"user_name": user, "message": message, "created_date": response.get("created_date")},
        )

    async def on_create_room(self, sid: str, data: Any):
        target_uuid = data["target_uuid"].upper()
        logged_in_uuid_code = data["logged_in_uuid_code"].upper()
        sorted_room_id = "".join(sorted([logged_in_uuid_code, target_uuid]))
        await self.enter_room(sid, sorted_room_id)
        await self.emit("room_created_success", {"room": sorted_room_id}, to=sid)

    async def on_fetch_history(self, sid: str, data: Any):
        room = data["room"]
        history = await get_chat_history(room)
        await self.emit("chat_history", {"history": history}, to=sid)

    async def on_send_message(self, sid, data):
        room = data["room"]
        message = data["message"]
        username = data["username"]
        await save_user_chats(room, username, message)
        await self.emit(
            "new_message", {"username": username, "message": message, "created_date": datetime.now().isoformat()},
            room=room
        )
