from pymongo import MongoClient

# Connect to MongoDB
client = MongoClient("mongodb://localhost:27017/")

# Select database
db = client["Seed"]   # 👈 replace with your DB name

# Select collection
plants_collection = db["disease"]

diseases_col = db["disease"]
users_col    = db["users"]
history_col  = db["detection_history"]
