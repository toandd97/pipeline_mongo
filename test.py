from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
from datetime import datetime

def insert_profile_data():
    try:
        # Kết nối đến MongoDB
        client = MongoClient(
            "mongodb://admin:admin@localhost:27017/admin?authSource=admin",
            serverSelectionTimeoutMS=5000
        )
        
        # Kiểm tra kết nối
        client.admin.command('ping')
        print("Connected to MongoDB successfully")

        db = client["admin"]
        collection = db["profile"]

        # Xóa dữ liệu cũ (tùy chọn)
        collection.delete_many({})
        print("Cleared existing data in admin.profile")

        # Dữ liệu mẫu
        profiles = [
            {"name": "Alice", "value": 100, "timestamp": datetime.now(), "active": True},
            {"name": "Bob", "value": 200, "timestamp": datetime.now(), "active": False},
            {"name": "Charlie", "value": 300, "timestamp": datetime.now(), "active": True}
        ]

        # Chèn dữ liệu
        result = collection.insert_many(profiles)
        print(f"Inserted {len(result.inserted_ids)} documents into admin.profile")

        # Kiểm tra dữ liệu
        print("Documents in admin.profile:")
        for doc in collection.find():
            print(doc)

    except ConnectionFailure as e:
        print(f"Connection error: {e}")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        client.close()
        print("MongoDB connection closed")

if __name__ == "__main__":
    insert_profile_data()