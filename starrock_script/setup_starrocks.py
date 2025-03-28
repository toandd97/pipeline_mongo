import pymysql

# Cấu hình kết nối đến StarRocks
STARROCKS_HOST = "127.0.0.1"
STARROCKS_PORT = 9030
USER = "root"
PASSWORD = ""

# Câu lệnh SQL tạo database và bảng
CREATE_DATABASE_SQL = "CREATE DATABASE IF NOT EXISTS profiling;"
CREATE_TABLE_SQL = """
USE profiling;
CREATE TABLE IF NOT EXISTS profile (
    id INT NOT NULL,
    name STRING,
    age INT,
    email STRING
) ENGINE=OLAP
DUPLICATE KEY(`id`)
DISTRIBUTED BY HASH(`id`) BUCKETS 3
PROPERTIES (
    "replication_num" = "1"
);
"""

try:
    # Kết nối tới StarRocks
    connection = pymysql.connect(
        host=STARROCKS_HOST,
        port=STARROCKS_PORT,
        user=USER,
        password=PASSWORD,
        cursorclass=pymysql.cursors.DictCursor
    )
    
    with connection.cursor() as cursor:
        # Tạo database
        cursor.execute(CREATE_DATABASE_SQL)
        print("✅ Database 'profiling' đã được tạo!")

        # Tạo bảng
        cursor.execute(CREATE_TABLE_SQL)
        print("✅ Bảng 'profile' đã được tạo!")

    # Commit thay đổi
    connection.commit()

except pymysql.MySQLError as e:
    print(f"❌ Lỗi khi kết nối StarRocks: {e}")

finally:
    connection.close()