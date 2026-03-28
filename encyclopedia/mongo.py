from pymongo import MongoClient

# Connect to MongoDB
client = MongoClient("mongodb://localhost:27017/")

# Select database
db = client["Seed"]   # 👈 replace with your DB name

# Select collection
plants_collection = db["plant"]