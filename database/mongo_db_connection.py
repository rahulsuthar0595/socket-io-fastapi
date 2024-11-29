from pymongo import MongoClient

from config.config import settings


class MongoDBUnitOfWork:

    @staticmethod
    def mdb_connection(db_name: str | None = None):
        if not db_name:
            db_name = settings.MONGO_DB_NAME

        client = MongoClient(settings.MONGO_DB_HOST, settings.MONGO_DB_PORT)
        db = client[db_name]
        return client, db
