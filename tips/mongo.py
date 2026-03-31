from pymongo import MongoClient

client = MongoClient("mongodb://localhost:27017/")
db = client["Seed"]        # your DB name
collection = db["tips"]       # your collection name

def get_random_tip():
    tip = list(collection.aggregate([{"$sample": {"size": 1}}]))  # true random
    if tip:
        tip[0].pop("_id", None)  # remove MongoDB _id
        return tip[0]
    return None