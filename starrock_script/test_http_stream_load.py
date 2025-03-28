import requests
# Cấu hình kết nối StarRocks
STARROCKS_HOST = "127.0.0.1"
STREAM_LOAD_URL = f"http://{STARROCKS_HOST}:8030/api/profiling/profile/_stream_load"
HEADERS = {
    "format": "json",
    "StarRocks-User": "root",
    "StarRocks-Passwd": "",
    "Expect": "",
}

# Dữ liệu mẫu gửi lên StarRocks
data = '{"id": 1, "name": "test", "age": 25, "email": "test@example.com"}'

try:
    response = requests.put(STREAM_LOAD_URL,
                            auth=("root", ""),
                            headers=HEADERS, 
                            data=data)
    
    if response.status_code == 200:
        print("✅ HTTP Stream Load API hoạt động tốt!")
    else:
        print(f"❌ HTTP Stream Load API thất bại! Mã lỗi: {response.status_code}")
        print(response.text)

except requests.exceptions.RequestException as e:
    print(f"❌ Lỗi khi gọi HTTP Stream Load API: {e}")
