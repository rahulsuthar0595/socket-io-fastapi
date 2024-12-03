import json
from datetime import datetime, timezone
from typing import Any

import socketio
from fastapi import FastAPI

from config.config import settings
from logger.logger import logger
from src.api.v1.repository.mongo_core_repository import fetch_user_data, \
    get_chat_history, save_user_chats, get_direct_chat_for_user, create_user_chat_group, add_message_to_group_chat, \
    get_group_by_id, add_user_to_group, remove_user_to_group, get_direct_messages_list, fetch_group_data


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
        logger.info(f"on_connect => {sid}")

    @staticmethod
    async def on_disconnect(sid):
        logger.info(f"on_disconnect => {sid}")

    async def on_user_joined(self, sid: str, data: Any):
        logger.info(f"user_joined => {sid} - {data}")
        user_response = await fetch_user_data()
        group_response = await fetch_group_data()
        await self.emit("return_joined_data_list", {"users": user_response, "groups": group_response}, to=sid)

    async def on_broadcast(self, sid: str, data: Any):
        logger.info(f"broadcast_message => {sid} - {data}")
        await self.emit(
            "return_response", {"data": data["data"]},
            skip_sid=sid  # Not broadcast message to sender.
        )

    async def on_create_room(self, sid: str, data: Any):
        logger.info(f"on_create_room => {sid} - {data}")
        target_uuid = data["target_uuid"].upper()
        logged_in_uuid_code = data["logged_in_uuid_code"].upper()
        sorted_room_id = "".join(sorted([logged_in_uuid_code, target_uuid]))
        await self.enter_room(sid, sorted_room_id)
        await self.emit("room_created_success", {"room": sorted_room_id}, to=sid)

    async def on_fetch_history(self, sid: str, data: Any):
        logger.info(f"on_fetch_history => {sid} - {data}")
        room = data["room"]
        history = await get_chat_history(room)
        await self.emit("chat_history", {"history": history}, to=sid)

    async def on_send_message(self, sid, data):
        logger.info(f"on_send_message => {sid} - {data}")
        room = data["room"]
        message = data["message"]
        username = data["username"]
        await save_user_chats(room, username, message)
        await self.emit(
            "new_message", {"username": username, "message": message, "created_date": datetime.now().isoformat()},
            room=room
        )

    async def on_direct_message_to_user(self, sid: str, data: Any):
        logger.info(f"on_direct_message_to_user => {sid} - {data}")
        sender_uuid = data["sender_uuid"]
        receiver_uuid = data["receiver_uuid"]

        message = data["message"]

        await get_direct_chat_for_user(sender_uuid, receiver_uuid, message)
        await self.emit(
            event="new_message",
            data={
                "sender": sender_uuid,
                "recipient": receiver_uuid,
                "content": message,
                "timestamp": datetime.now(timezone.utc).isoformat()
            },
            room=receiver_uuid
        )

    async def on_direct_messages_history(self, sid: str, data: Any):
        logger.info(f"on_direct_messages_history => {sid} - {data}")
        sender_uuid = data["sender_uuid"]
        receiver_uuid = data["receiver_uuid"]
        chat = await get_direct_messages_list(sender_uuid, receiver_uuid)
        if chat:
            await self.emit("direct_messages", {"messages": chat["messages"]}, to=sid)

    async def on_chat_group_create(self, sid: str, data: Any):
        logger.info(f"on_chat_group_create => {sid} - {data}")
        group = data["group_name"]
        created_by_user_uuid = data["user_uuid"]  # UUID of user who created group
        group_id = await create_user_chat_group(group, created_by_user_uuid)
        await self.emit(
            event="group_created",
            data={"group_name": group, "group_id": str(group_id)},
            to=sid
        )

    async def on_group_chat_message(self, sid: str, data: Any):
        logger.info(f"on_group_chat_message => {sid} - {data}")
        sender_uuid = data["sender_uuid"]
        group_id = data["group_id"]
        message = data["message"]
        data = {
            "sender": sender_uuid,
            "message": message,
            "created_date": datetime.now(timezone.utc),
            "status": "sent"
        }
        response = await add_message_to_group_chat(group_id, data)
        if response:
            data = json.loads(json.dumps(data, default=str))
            await self.emit("group_message", data, room=group_id)

    async def on_user_group_joined(self, sid: str, data: Any):
        logger.info(f"on_user_group_joined => {sid} - {data}")
        user_uuid = data["user_uuid"]
        group_id = data["group_id"]
        group = await add_user_to_group(group_id, user_uuid)
        if group:
            await self.emit(
                event="group_updated",
                data={
                    "group_id": group_id, "user_uuid": user_uuid, "action": "joined"
                },
                room=group_id
            )

    async def on_user_group_leave(self, sid: str, data: Any):
        logger.info(f"on_user_group_leave => {sid} - {data}")
        user_uuid = data["user_uuid"]
        group_id = data["group_id"]

        group = await remove_user_to_group(group_id, user_uuid)
        if group:
            await self.emit(
                event="group_updated",
                data={
                    "group_id": group_id, "user_uuid": user_uuid, "action": "left"
                },
                room=group_id
            )

    async def on_group_chat_history(self, sid: str, data: Any):
        logger.info(f"on_group_chat_history => {sid} - {data}")
        group_id = data["group_id"]
        group = await get_group_by_id(group_id)
        if group:
            encoded_data = json.dumps(group.get("messages"), default=str)
            decoded_data = json.loads(encoded_data)
            await self.emit(
                event="group_chat_list",
                data={
                    "messages": decoded_data,
                },
                to=sid
            )
