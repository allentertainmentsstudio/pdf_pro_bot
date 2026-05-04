from pymongo import MongoClient
from config import MONGO_URI, DB_NAME

client = MongoClient(MONGO_URI)
db = client[DB_NAME]

users = db.users
banned = db.banned


# ---------- USERS ---------- #
def add_user(user_id, name):
    if not users.find_one({"user_id": user_id}):
        users.insert_one({"user_id": user_id, "name": name, "files": 0})


def inc_files(user_id):
    users.update_one({"user_id": user_id}, {"$inc": {"files": 1}})


def get_user_count():
    return users.count_documents({})


# ---------- BAN SYSTEM ---------- #
def ban_user(user_id):
    if not banned.find_one({"user_id": user_id}):
        banned.insert_one({"user_id": user_id})


def unban_user(user_id):
    banned.delete_one({"user_id": user_id})


def is_banned(user_id):
    return banned.find_one({"user_id": user_id}) is not None
