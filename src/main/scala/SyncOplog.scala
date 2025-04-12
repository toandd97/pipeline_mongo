package com.example

import org.apache.spark.sql.SparkSession
import org.apache.spark.sql.functions.col

object SyncOplog {
  def main(args: Array[String]): Unit = {
    // Khởi tạo SparkSession
    val spark = SparkSession.builder()
      .appName("MongoDB Oplog to StarRocks")
      .config("spark.jars", "/opt/spark/jars/mongo-spark-connector_2.12-10.1.1.jar,/opt/spark/jars/starrocks-jdbc-driver.jar")
      .getOrCreate()

    // Đọc oplog từ MongoDB
    val oplogDF = spark.read
      .format("mongodb")
      .option("uri", "mongodb://sparkuser:sparkpassword@mongodb:27017/local.oplog.rs")
      .option("database", "local")
      .option("collection", "oplog.rs")
      .load()

    // Lọc và xử lý dữ liệu (chỉ lấy insert từ mydb.mycollection)
    val processedDF = oplogDF
      .filter(col("ns") === "mydb.mycollection" && col("op") === "i")
      .select(
        col("o._id").alias("id"),
        col("o.field1").alias("field1"),
        col("o.field2").alias("field2")
      )

    // Thông tin kết nối StarRocks
    val starrocksUrl = "jdbc:starrocks://starrocks_fe:9030/mydb?user=root&password="
    val tableName = "my_table"

    // Ghi dữ liệu vào StarRocks
    processedDF.write
      .format("jdbc")
      .option("url", starrocksUrl)
      .option("dbtable", tableName)
      .option("driver", "com.starrocks.jdbc.Driver")
      .mode("append")
      .save()

    // Dừng SparkSession
    spark.stop()
  }
}