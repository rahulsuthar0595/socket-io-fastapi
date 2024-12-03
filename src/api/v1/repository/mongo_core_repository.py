import random
import string
import uuid
from datetime import datetime, timezone

from bson import ObjectId

from database.mongo_db_connection import MongoDBUnitOfWork


def generate_uuid_code(collection):
    while True:
        uuid_code = "".join(random.choices(string.ascii_letters + string.digits, k=4)).upper()
        if not collection.find_one({"uuid_code": uuid_code}):
            return uuid_code


async def get_mongo_db_collection(collection_name: str):
    client, db = MongoDBUnitOfWork().mdb_connection()
    collection = db[collection_name]
    return collection


async def retrieve_user_by_email(email: str):
    collection = await get_mongo_db_collection(collection_name="users")

    email = email.lower()
    return collection.find_one({"email": email})


async def insert_users_detail(data: dict):
    collection = await get_mongo_db_collection(collection_name="users")

    data.update({
        "_id": str(uuid.uuid4()),
        "created_date": datetime.now(timezone.utc),
    })
    user = collection.insert_one(data)
    return data


async def insert_user_chat(data: dict):
    try:
        collection = await get_mongo_db_collection(collection_name="chats")
        timestamp = datetime.now(timezone.utc)
        data.update({
            "created_date": timestamp,
            "_id": str(uuid.uuid4())
        })
        res = collection.insert_one(data)
        return data
    except Exception as e:
        raise Exception("Something went wrong.")


async def display_user_chats():
    collection = await get_mongo_db_collection(collection_name="chats")

    results = list(collection.find().sort("created_date", 1))
    response = []
    for res in results:
        response.append({
            "user_name": res["user"],
            "message": res["message"],
            "timestamp": res["created_date"]
        })
    return response


async def fetch_user_data():
    collection = await get_mongo_db_collection(collection_name="users")
    response = collection.find({}, {"_id": 1, "full_name": 1, "email": 1}).sort("created_date", -1)
    return list(response)


async def fetch_group_data():
    collection = await get_mongo_db_collection(collection_name="user_chats")

    response = collection.find({"is_group": True}, {"_id": 1, "group_name": 1}).sort("created_date", -1)
    data = [
        {**entry, "_id": str(entry["_id"])} if "_id" in entry else entry for entry in list(response)
    ]
    return data


async def get_chat_history(room_id: str):
    history = []
    collection = await get_mongo_db_collection(collection_name="chats")

    for msg in collection.find({"room_id": room_id}).sort("created_by", 1):
        history.append({
            "username": msg["username"],
            "message": msg["message"],
            "created_date": msg["created_date"].isoformat()
        })
    return history


async def save_user_chats(room: str, sender: str, message: str):
    collection = await get_mongo_db_collection(collection_name="chats")

    collection.insert_one({
        "room_id": room,
        "username": sender,
        "message": message,
        "created_date": datetime.now()
    })


async def get_direct_messages_list(sender_uuid: str, receiver_uuid: str):
    collection = await get_mongo_db_collection(collection_name="user_chats")
    all_participants = [sender_uuid, receiver_uuid]
    chat = collection.find_one({"participants": {"$eq": all_participants}, "is_group": False})
    return chat


async def get_direct_chat_for_user(sender_uuid: str, receiver_uuid: str, message: str):
    collection = await get_mongo_db_collection(collection_name="user_chats")
    chat = await get_direct_messages_list(sender_uuid, receiver_uuid)

    if chat:
        chat_id = chat["_id"]
    else:
        chat_id = collection.insert_one({
            "participants": [sender_uuid, receiver_uuid],
            "is_group": False,
            "group_name": None,
            "messages": [],
            "created_date": datetime.now(timezone.utc).isoformat(),
            "updated_date": datetime.now(timezone.utc).isoformat(),
        }).inserted_id

    collection.update_one(
        {"_id": ObjectId(chat_id)},
        {
            "$push": {
                "messages": {
                    "sender": sender_uuid,
                    "message": message,
                    "created_date": datetime.now(timezone.utc).isoformat(),
                    "status": "sent"
                }
            },
            "$set": {"updated_date": datetime.now(timezone.utc).isoformat()}
        }
    )


async def create_user_chat_group(group_name: str, created_by_user_uuid: str):
    collection = await get_mongo_db_collection(collection_name="user_chats")

    group_id = collection.insert_one({
        "group_name": group_name,
        "is_group": True,
        "created_by": created_by_user_uuid,
        "participants": [created_by_user_uuid],
        "messages": [],
        "created_date": datetime.now(timezone.utc),
        "updated_date": datetime.now(timezone.utc),
    }).inserted_id
    return group_id


async def get_group_by_id(group_id: str):
    collection = await get_mongo_db_collection(collection_name="user_chats")
    group = collection.find_one({"_id": ObjectId(group_id)})
    return group


async def add_message_to_group_chat(group_id: str, data: dict):
    collection = await get_mongo_db_collection(collection_name="user_chats")
    response = collection.update_one(
        {"_id": ObjectId(group_id), "is_group": True},
        {
            "$push": {"messages": data},
            "$set": {"updated_date": datetime.now(timezone.utc)}
        }
    )
    return response


async def add_user_to_group(group_id: str, user_uuid: str):
    collection = await get_mongo_db_collection(collection_name="user_chats")

    group = await get_group_by_id(group_id)
    if group:
        collection.update_one(
            {"_id": group_id, "is_group": True},
            {"$addToSet": {"participants": user_uuid}}
        )
        return True
    return False



async def remove_user_to_group(group_id: str, user_uuid: str):
    collection = await get_mongo_db_collection(collection_name="user_chats")

    group = await get_group_by_id(group_id)
    if group:
        collection.update_one(
            {"_id": group_id, "is_group": True},
            {"$pull": {"participants": user_uuid}}
        )
        return True
    return False
