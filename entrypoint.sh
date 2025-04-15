#!/bin/bash

# Đảm bảo script dừng lại nếu có lỗi
set -e

echo "Starting Spark application..."
# Thực thi spark-submit với các tham số
exec /opt/spark/bin/spark-submit \
    --master spark://spark:7077 \
    --jars /opt/spark/jars/mongo-spark-connector_2.12-3.0.2.jar,/opt/spark/jars/starrocks-spark-connector-3.5_2.12-1.1.2.jar,/opt/spark/jars/mysql-connector-j-8.0.33.jar \
    /opt/spark-apps/sync_mongo_to_starrocks.py