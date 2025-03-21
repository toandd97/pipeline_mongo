Hướng Dẫn Thiết Lập Hệ Thống Pipeline Dữ Liệu với MongoDB, StarRocks & Elasticsearch

1. Giới Thiệu

Tài liệu này hướng dẫn cách thiết lập hệ thống pipeline dữ liệu với MongoDB làm nguồn dữ liệu chính, sử dụng Monstache để streaming dữ liệu, PySpark để xử lý batch, và tích hợp Elasticsearch và StarRocks để lưu trữ và phân tích dữ liệu. Ngoài ra, hệ thống cũng bao gồm Airflow để quản lý pipeline và Prometheus + Grafana để giám sát.

2. Các Thành Phần Cần Cài Đặt

2.1. Cơ sở dữ liệu & Lưu trữ

✅ MongoDB → Lưu trữ dữ liệu gốc.✅ StarRocks → Lưu trữ dữ liệu phân tích.✅ Elasticsearch → Lưu trữ dữ liệu phục vụ tìm kiếm nhanh.

2.2. Streaming & Batch Processing

✅ Monstache → Streaming dữ liệu từ MongoDB → Elasticsearch & StarRocks.✅ PySpark → Batch processing dữ liệu từ MongoDB lên StarRocks.

2.3. Quản lý Workflow & Monitoring

✅ Airflow → Quản lý batch pipeline (chạy PySpark để xử lý MongoDB).✅ Prometheus + Grafana → Giám sát hiệu suất hệ thống và dữ liệu.✅ Loki (tuỳ chọn) → Logging tập trung cho monitoring.

2.4. Hỗ trợ Airflow

✅ PostgreSQL → Làm database backend cho Airflow.✅ Redis → Hỗ trợ scheduler của Airflow.

2.5. Công cụ hỗ trợ khác

✅ Docker → Để chạy tất cả các thành phần trong container.

3. Cài Đặt MongoDB với Replica Set

Bước 1: Xóa Container MongoDB Cũ (Nếu Có)

Nếu bạn đã có container MongoDB chạy mà không có Replica Set, hãy xóa nó trước:

docker rm -f mongo-rs

Bước 2: Chạy MongoDB với Replica Set

docker run -d --name mongo-rs \
  -p 27017:27017 \
  --restart unless-stopped \
  mongo:6.0 --replSet rs0

--replSet rs0: Kích hoạt chế độ Replica Set với tên rs0.

Bước 3: Khởi Tạo Replica Set

Truy cập vào MongoDB Shell trong container:

docker exec -it mongo-rs mongosh

Khởi tạo Replica Set:

rs.initiate()

Kiểm tra trạng thái Replica Set:

rs.status()

Nếu thấy ok: 1, Replica Set đã hoạt động thành công.

Bước 4: Kiểm Tra Oplog

Chuyển sang database local:

use local

Kiểm tra Oplog:

db.oplog.rs.find().limit(5).pretty()

Nếu thấy dữ liệu, Oplog đã hoạt động thành công.

4. Thiết Lập Monstache để Đồng Bộ MongoDB → StarRocks & Elasticsearch

Bước 1: Cài Đặt Monstache

(TBD)

Bước 2: Cấu Hình Monstache

(TBD)

5. Cài Đặt PySpark để Xử Lý Batch

(TBD)

6. Cài Đặt Airflow để Quản Lý Pipeline

(TBD)

7. Cài Đặt Prometheus + Grafana để Giám Sát

(TBD)

8. Kiểm Tra & Debug

(TBD)

9. Kết Luận

Sau khi thực hiện các bước trên, bạn sẽ có một hệ thống MongoDB chạy Replica Set, Monstache đồng bộ dữ liệu sang StarRocks và Elasticsearch, PySpark xử lý batch, Airflow quản lý pipeline, và Prometheus + Grafana giám sát hệ thống. Các bước tiếp theo sẽ tập trung vào tối ưu và mở rộng hệ thống.

