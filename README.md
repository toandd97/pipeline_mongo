Hướng Dẫn Thiết Lập Hệ Thống Pipeline Dữ Liệu với MongoDB, StarRocks & Elasticsearch
1. Giới Thiệu

Tài liệu này hướng dẫn cách thiết lập hệ thống pipeline dữ liệu với MongoDB làm nguồn dữ liệu chính, sử dụng Monstache để streaming dữ liệu, PySpark để xử lý batch, và tích hợp Elasticsearch và StarRocks để lưu trữ và phân tích dữ liệu. Ngoài ra, hệ thống cũng bao gồm Prometheus + Grafana để giám sát.
2. Các Thành Phần Cần Cài Đặt
2.1. Cơ sở dữ liệu & Lưu trữ

✅ MongoDB → Lưu trữ dữ liệu gốc.
✅ StarRocks → Lưu trữ dữ liệu phân tích.
✅ Elasticsearch → Lưu trữ dữ liệu phục vụ tìm kiếm nhanh.
2.2. Streaming & Batch Processing

✅ Monstache → Streaming dữ liệu từ MongoDB → Elasticsearch & StarRocks.
✅ PySpark → Batch processing dữ liệu từ MongoDB lên Elasticsearch & StarRocks.
2.3. Giám sát hệ thống

✅ Prometheus + Grafana → Giám sát hiệu suất hệ thống và dữ liệu.
✅ Loki (tuỳ chọn) → Logging tập trung cho monitoring.
2.4. Công cụ hỗ trợ khác

✅ Docker → Để chạy tất cả các thành phần trong container.

Bước 3: Truy cập vào MongoDB Shell trong container:

Nếu MongoDB không khởi tạo được cluster bằng script rs-init.sh, khởi tạo thủ công bằng cách sau:
```bash
$ docker-compose exec mongo bash
$ sh scripts/rs-init.sh
```

Nếu MongoDB không khởi tạo được user, sử dụng các command line sau đây để khởi tạo:
```bash
$ docker-compose exec mongo mongosh
$ use admin
$ db.createUser({user: "admin", pwd: "admin",roles:[{role: "userAdminAnyDatabase" , db:"admin"}]}) 
# docker-entrypoint-initdb.d/mongo-init.js
use local

    Kiểm tra Oplog:

db.oplog.rs.find().limit(5).pretty()

Nếu thấy dữ liệu, Oplog đã hoạt động thành công.

4. Thiết Lập Monstache để Đồng Bộ MongoDB → StarRocks & Elasticsearch (xử lý Streaming)
    4.1 Đồng bộ elasticsearch
        4.1.1 tạo image monstache cá nhân
        Do môi trường ở local và môi trường trong docker là khác nhau nên nếu build file .so ở local rồi mount vào docker thì trong docker không đọc được.
        chạy file dockerfile để tạo riêng 1 images: docker build -t monstache_profile 
        Kết quả: có file some_cases_plugin.go trong thư mục bin/profiling của container_name: monstacheprofile

        Thay image vừa build được từ Dockerfile vào image của Monstache

        Để sử dụng plugin ở nhiều nơi khác nhau thì copy file .so vừa build về local và gửi cho team devops để đẩy lên các máy: 
            docker cp <CONTAINER ID>:/bin/profiling/some_cases_plugin.so /<path>/some_cases_plugin.so

        4.1.2  Run lại để mount file so
            Có 2 cách là thêm command mapper-plugin-path file .so của images monstache, hoặc thêm key "mapper-plugin-path" trong file toml rồi chạy lại images
            -cách 1: file docker-compose
            monstache-profile:
                image: monstache_profile:latest
                container_name: monstacheprofile
                working_dir: /app
                command: -f ./monstache_profile.config.toml -mapper-plugin-path /bin/profiling/some_cases_plugin.so
                volumes:
                - ./monstache_profile.config.toml:/app/monstache_profile.config.toml
            -cách 2: file toml
            stats = true
            resume = true
            resume-strategy = 1
            resume-name="monstache-profiling-profile"

            mapper-plugin-path = "/bin/profiling/plugin_profile.so"

            [logs]
            error = "/dev/stderr"

        4.1.3 Kiểm tra có đồng bộ được không
    4.2 Đồng bộ Starrock

5. Cài Đặt PySpark để Xử Lý Batch
Bước 1: Cài Đặt PySpark

(TBD)
Bước 2: Batch Processing lên Elasticsearch & StarRocks

(TBD)
6. Cài Đặt Prometheus + Grafana để Giám Sát

(TBD)
7. Kiểm Tra & Debug

(TBD)
8. Kết Luận

Sau khi thực hiện các bước trên, bạn sẽ có một hệ thống MongoDB chạy Replica Set, Monstache đồng bộ dữ liệu sang StarRocks và Elasticsearch, PySpark xử lý batch lên cả hai, và Prometheus + Grafana giám sát hệ thống. Các bước tiếp theo sẽ tập trung vào tối ưu và mở rộng hệ thống.


