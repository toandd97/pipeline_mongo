from pyspark.sql import SparkSession
from pyspark.sql.functions import col

# Khởi tạo Spark Session
spark = SparkSession.builder \
    .appName("MongoDB to StarRocks Sync") \
    .config("spark.mongodb.input.uri", "mongodb://mongo:27017/profiling.profile") \
    .config("spark.jars", "/opt/spark/jars/mongo-spark-connector_2.12-3.0.1.jar,/opt/spark/jars/starrocks-spark-connector-1.0.0.jar") \
    .getOrCreate()

# Đọc dữ liệu từ MongoDB bằng Structured Streaming
df = spark.readStream \
    .format("mongo") \
    .option("change.stream.publish.full.document", "updateLookup") \
    .load()

# Chuyển đổi dữ liệu để khớp schema của StarRocks
df_transformed = df.select(
    col("_id").cast("string").alias("id"),  # Chuyển ObjectId thành string
    col("name").alias("name"),
    col("age").cast("integer").alias("age"),
    col("email").alias("email")
)

# Hàm ghi từng batch vào StarRocks
def write_to_starrocks(batch_df, batch_id):
    batch_df.write \
        .format("starrocks") \
        .option("starrocks.fe.urls", "http://starrock:8030") \
        .option("starrocks.table.identifier", "profiling.profile") \
        .option("starrocks.username", "root") \
        .option("starrocks.password", "") \
        .option("starrocks.write.format", "csv") \
        .mode("append") \
        .save()

# Ghi dữ liệu vào StarRocks theo stream
query = df_transformed.writeStream \
    .foreachBatch(write_to_starrocks) \
    .option("checkpointLocation", "/tmp/checkpoint") \
    .start()

query.awaitTermination()