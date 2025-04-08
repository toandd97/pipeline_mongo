import pymongo
import mysql.connector
import time
from bson.timestamp import Timestamp

# Kết nối đến MongoDB
mongo_client = pymongo.MongoClient(
    "mongodb://admin:admin@mongo:27017/",
    serverSelectionTimeoutMS=5000
)
mongo_db = mongo_client.local
oplog = mongo_db.oplog.rs

# Kết nối đến StarRocks
starrock_conn = mysql.connector.connect(
    host="starrock",
    port=9030,
    user="root",
    password="123",
    database="profiling"  # Thay đổi nếu cần
)
starrock_cursor = starrock_conn.cursor()

# Tìm timestamp mới nhất trong oplog
last_timestamp = oplog.find().sort('$natural', -1).limit(1).next()['ts']
print(f"Bắt đầu đồng bộ từ timestamp: {last_timestamp}")

# Các field cần đồng bộ
SYNC_FIELDS = ["_id", "name"]  # Chỉ đồng bộ _id và name, bạn có thể thay đổi

# Hàm chuyển đổi oplog thành câu lệnh SQL với các field cụ thể
def process_oplog_entry(entry):
    operation = entry["op"]
    namespace = entry["ns"]
    if namespace != "profiling.profile":  # Chỉ đồng bộ collection cụ thể
        return None

    if operation == "i":  # Insert
        data = entry["o"]
        # Lọc chỉ các field trong SYNC_FIELDS
        filtered_data = {k: data.get(k) for k in SYNC_FIELDS if k in data}
        if not filtered_data:
            return None
        columns = ", ".join(filtered_data.keys())
        values = ", ".join(f"'{v}'" for v in filtered_data.values())
        return f"INSERT INTO profile ({columns}) VALUES ({values})"
    
    elif operation == "u":  # Update
        condition = entry["o2"]
        update_data = entry["o"].get("$set", {})
        # Lọc chỉ các field trong SYNC_FIELDS
        filtered_update = {k: update_data.get(k) for k in SYNC_FIELDS if k in update_data}
        if not filtered_update:
            return None
        _id = condition.get("_id", "")
        set_clause = ", ".join(f"{k} = '{v}'" for k, v in filtered_update.items())
        return f"UPDATE profile SET {set_clause} WHERE _id = '{_id}'"
    
    elif operation == "d":  # Delete
        _id = entry["o"].get("_id", "")
        return f"DELETE FROM profile WHERE _id = '{_id}'"
    
    return None

# Vòng lặp theo dõi oplog
while True:
    query = {"ts": {"$gt": last_timestamp}}
    cursor = oplog.find(query, cursor_type=pymongo.CursorType.TAILABLE_AWAIT)
    
    try:
        for doc in cursor:
            sql = process_oplog_entry(doc)
            if sql:
                try:
                    print(f"Thực thi: {sql}")
                    starrock_cursor.execute(sql)
                    starrock_conn.commit()
                except mysql.connector.Error as e:
                    print(f"Lỗi khi thực thi SQL: {e}")
            last_timestamp = doc["ts"]
    except pymongo.errors.CursorNotFound:
        print("Cursor closed, retrying...")
        time.sleep(1)

# Đóng kết nối (không chạy đến đây vì vòng lặp vô hạn)
mongo_client.close()
starrock_conn.close()