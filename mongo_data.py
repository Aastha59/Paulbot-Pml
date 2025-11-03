from pymongo import MongoClient
import os
from dotenv import load_dotenv

# Load the .env variables
load_dotenv()
print("MONGODB_URI:", os.getenv("MONGODB_URI"))
print("DB_NAME:", os.getenv("DB_NAME"))
print("COLLECTION_NAME:", os.getenv("COLLECTION_NAME"))

# Connect to MongoDB
client = MongoClient(os.getenv("MONGODB_URI"))
db = client[os.getenv("DB_NAME")]
collection = db[os.getenv("COLLECTION_NAME")]

# Example insert
sample_data = {
    "conversation_id": "1",
    "role": "user",
    "message": "Hello, what is Paul Merchants?",
}

collection.insert_one(sample_data)
print("✅ Data inserted into MongoDB!")

# Example fetch
for doc in collection.find():
    print(doc)
