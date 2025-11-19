# from pymongo import MongoClient
# import os
# from dotenv import load_dotenv
# import certifi 

# # Load the .env variables
# load_dotenv()
# print("MONGODB_URI:", os.getenv("MONGODB_URI"))
# print("DB_NAME:", os.getenv("DB_NAME"))
# print("COLLECTION_NAME:", os.getenv("COLLECTION_NAME"))

# # Connect to MongoDB
# client = MongoClient(os.getenv("MONGODB_URI"))
# db = client[os.getenv("DB_NAME")]
# collection = db[os.getenv("COLLECTION_NAME")]

# # Example insert
# sample_data = {
#     "conversation_id": "1",
#     "role": "user",
#     "message": "Hello, what is Paul Merchants?",
# }

# collection.insert_one(sample_data)
# print("✅ Data inserted into MongoDB!")

# # Example fetch
# for doc in collection.find():
#     print(doc)



from pymongo import MongoClient
import os
from dotenv import load_dotenv
import certifi  # ✅ add this

# Load the .env variables
load_dotenv()
print("MONGODB_URI:", os.getenv("MONGODB_URI"))
print("DB_NAME:", os.getenv("DB_NAME"))
print("COLLECTION_NAME:", os.getenv("COLLECTION_NAME"))

# ✅ Ensure your URI includes `tls=true` or `ssl=true`
MONGODB_URI = os.getenv("MONGODB_URI")
if "tls=" not in MONGODB_URI and "ssl=" not in MONGODB_URI:
    if "?" in MONGODB_URI:
        MONGODB_URI += "&tls=true"
    else:
        MONGODB_URI += "?tls=true"

# ✅ Connect to MongoDB with SSL certificate verification
client = MongoClient(
    MONGODB_URI,
    tls=True,
    tlsCAFile=certifi.where()
)

# Database and collection
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
