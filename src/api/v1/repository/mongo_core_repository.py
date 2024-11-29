import random
import string
import uuid
from datetime import datetime, timezone

from database.mongo_db_connection import MongoDBUnitOfWork


def generate_uuid_code(collection):
    while True:
        uuid_code = "".join(random.choices(string.ascii_letters + string.digits, k=4)).upper()
        if not collection.find_one({"uuid_code": uuid_code}):
            return uuid_code


async def retrieve_user_by_email(email: str):
    collection_name = "users"
    client, db = MongoDBUnitOfWork().mdb_connection()
    collection = db[collection_name]

    email = email.lower()
    return collection.find_one({"email": email})


async def insert_users_detail(data: dict):
    collection_name = "users"
    client, db = MongoDBUnitOfWork().mdb_connection()
    collection = db[collection_name]
    uuid_code = generate_uuid_code(collection)

    data.update({
        "_id": str(uuid.uuid4()),
        "uuid_code": uuid_code,
        "created_date": datetime.now(timezone.utc),
    })
    user = collection.insert_one(data)
    return data


async def insert_user_chat(data: dict):
    try:
        collection_name = "chats"
        client, db = MongoDBUnitOfWork().mdb_connection()
        collection = db[collection_name]
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
    collection_name = "chats"
    client, db = MongoDBUnitOfWork().mdb_connection()
    collection = db[collection_name]

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
    collection_name = "users"
    client, db = MongoDBUnitOfWork().mdb_connection()
    collection = db[collection_name]

    response = collection.find({}, {"_id": 0, "uuid_code": 1, "full_name": 1, "email": 1}).sort("created_date", -1)
    return list(response)


async def get_chat_history(room_id: str):
    history = []
    collection_name = "chats"
    client, db = MongoDBUnitOfWork().mdb_connection()
    collection = db[collection_name]

    for msg in collection.find({"room_id": room_id}).sort("created_by", 1):
        history.append({
            "username": msg["username"],
            "message": msg["message"],
            "created_date": msg["created_date"].isoformat()
        })
    return history


async def save_user_chats(room: str, sender: str, message: str):
    collection_name = "chats"
    client, db = MongoDBUnitOfWork().mdb_connection()
    collection = db[collection_name]

    collection.insert_one({
        "room_id": room,
        "username": sender,
        "message": message,
        "created_date": datetime.now()
    })
