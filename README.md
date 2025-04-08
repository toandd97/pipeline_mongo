# Hướng dẫn cài đặt và cấu hình hệ thống Pipeline

## Yêu cầu hệ thống
- Docker và Docker Compose
- ít nhất 8GB RAM
- ít nhất 20GB dung lượng ổ đĩa

## Cấu trúc thư mục
```
.
├── docker-compose.yml
├── config/
│   ├── connect-standalone.properties
│   └── connect-StarRocks-sink.properties
├── mongo-scripts/
│   ├── rs-init.sh
│   └── mongo-init.js
└── streaming_elasticsearch.config.toml
```

## Các bước cài đặt

### 1. Tạo cấu trúc thư mục
```bash
mkdir -p config mongo-scripts
```

### 2. Tạo file docker-compose.yml
Tạo file `docker-compose.yml` với nội dung sau:

```yaml
services:
  zookeeper:
    image: "bitnami/zookeeper:latest"
    container_name: zookeeper
    networks:
      - localnet
    ports:
      - "2181:2181"
    environment:
      - ALLOW_ANONYMOUS_LOGIN=yes
    restart: unless-stopped

  kafka:
    image: "bitnami/kafka:latest"
    container_name: kafka
    networks:
      - localnet
    ports:
      - "9092:9092"
    environment:
      - KAFKA_CFG_ZOOKEEPER_CONNECT=zookeeper:2181
      - KAFKA_CFG_ADVERTISED_LISTENERS=PLAINTEXT://kafka:9092
      - KAFKA_CFG_NODE_ID=0
      - KAFKA_CFG_PROCESS_ROLES=controller,broker
      - KAFKA_CFG_LISTENERS=PLAINTEXT://:9092,CONTROLLER://:9093
      - KAFKA_CFG_LISTENER_SECURITY_PROTOCOL_MAP=CONTROLLER:PLAINTEXT,PLAINTEXT:PLAINTEXT
      - KAFKA_CFG_CONTROLLER_QUORUM_VOTERS=0@kafka:9093
      - KAFKA_CFG_CONTROLLER_LISTENER_NAMES=CONTROLLER
    depends_on:
      - zookeeper
    restart: unless-stopped    

  elasticsearch:
    image: elasticsearch:7.17.6
    container_name: elasticsearch
    environment:
      - ELASTIC_PASSWORD=changeme
      - xpack.security.enabled=true
      - xpack.security.authc.api_key.enabled=true
      - discovery.type=single-node
      - cluster.name=es-docker
      - node.name=node1
      - bootstrap.memory_lock=true
      - "ES_JAVA_OPTS=-Xms2g -Xmx2g"
    ulimits:
      memlock:
        soft: -1
        hard: -1
      nofile:
        soft: 65536
        hard: 65536
    cap_add:
      - IPC_LOCK
    volumes:
      - elasticsearch-data:/usr/share/elasticsearch/data
    ports:
      - 9200:9200
      - 9300:9300
    networks:
      - localnet
    restart: unless-stopped

  mongo:
    image: mongo:latest
    container_name: mongo
    restart: always
    entrypoint: [ "/usr/bin/mongod", "--bind_ip_all", "--replSet", "rs0" ]
    volumes:
      - ./mongo-scripts/rs-init.sh:/scripts/rs-init.sh
      - ./mongo-scripts/mongo-init.js:/docker-entrypoint-initdb.d/mongo-init.js
    environment:
      MONGO_INITDB_ROOT_USERNAME: admin
      MONGO_INITDB_ROOT_PASSWORD: admin
    ports:
      - "27017:27017"
    networks:
      - localnet
    
  redis:
    image: redis:latest
    container_name: redis
    ports:
      - "6379:6379"
    networks:
      - localnet
    restart: always

  starrock:
    image: starrocks/allin1-ubuntu
    container_name: starrock
    restart: always
    ports:
    - "9030:9030" 
    - "8030:8030"
    - "8040:8040"
    healthcheck:
      test: 'mysql -u root -h starrock -P 9030 -e "show frontends\G" |grep "Alive: true"'
      interval: 10s
      timeout: 5s
      retries: 3
    networks:
      - localnet

  kafka-connect:
    image: confluentinc/cp-kafka-connect:7.2.0
    container_name: kafka-connect
    depends_on:
      - kafka
      - starrock
    networks:
      - localnet
    environment:
      CONNECT_BOOTSTRAP_SERVERS: kafka:9092
      CONNECT_REST_PORT: 8083
      CONNECT_GROUP_ID: connect-group
      CONNECT_CONFIG_STORAGE_TOPIC: connect-configs
      CONNECT_OFFSET_STORAGE_TOPIC: connect-offsets
      CONNECT_STATUS_STORAGE_TOPIC: connect-status
      CONNECT_KEY_CONVERTER: org.apache.kafka.connect.json.JsonConverter
      CONNECT_VALUE_CONVERTER: org.apache.kafka.connect.json.JsonConverter
      CONNECT_INTERNAL_KEY_CONVERTER: "org.apache.kafka.connect.json.JsonConverter"
      CONNECT_INTERNAL_VALUE_CONVERTER: "org.apache.kafka.connect.json.JsonConverter"
      CONNECT_REST_ADVERTISED_HOST_NAME: "kafka-connect"
      CONNECT_LOG4J_ROOT_LOGLEVEL: "INFO"
      CONNECT_LOG4J_LOGGERS: "org.apache.kafka.connect.runtime.rest=WARN,org.reflections=ERROR"
      CONNECT_PLUGIN_PATH: "/usr/share/java,/usr/share/confluent-hub-components"
    volumes:
      - ./starrocks-kafka-connector:/usr/share/confluent-hub-components/starrocks-kafka-connector
      - ./config:/etc/kafka-connect/
    ports:
      - "8083:8083"
    command: 
      - bash
      - -c 
      - |
        echo "Installing connector plugins"
        confluent-hub install --no-prompt confluentinc/kafka-connect-jdbc:10.7.4
        echo "Launching Kafka Connect worker"
        /etc/confluent/docker/run &
        sleep infinity

            monstache-profile:
    image: monstache_profile
    container_name: monstache_profile
                working_dir: /app
    command: -f ./streaming_elasticsearch.config.toml
                volumes:
                - ./streaming_elasticsearch.config.toml:/app/streaming_elasticsearch.config.toml
    environment:
      - INDEX_MAPPING=mobio-profiling-v16_3
    depends_on:
      - elasticsearch
      - mongo
    ports:
      - "8080:8080"
    networks:
      - localnet
    healthcheck:
      test: "wget -q -O - http://localhost:8080/healthz"
      interval: 10s
      timeout: 30s
      retries: 300
    restart: unless-stopped

volumes:
  elasticsearch-data:
    driver: local

networks:
  localnet:
    driver: bridge
```

### 3. Tạo file cấu hình Kafka Connect

Tạo file `config/connect-standalone.properties`:
```properties
bootstrap.servers=kafka:9092
key.converter=org.apache.kafka.connect.json.JsonConverter
value.converter=org.apache.kafka.connect.json.JsonConverter
key.converter.schemas.enable=true
value.converter.schemas.enable=false
offset.storage.file.filename=/tmp/connect.offsets
offset.flush.interval.ms=10000
plugin.path=/usr/share/java,/usr/share/confluent-hub-components
```

Tạo file `config/connect-StarRocks-sink.properties`:
```properties
name=starrocks-sink
connector.class=com.starrocks.connector.kafka.sink.StarRocksSinkConnector
tasks.max=1
topics=streaming
starrocks.jdbc.url=jdbc:mysql://starrock:9030
starrocks.jdbc.user=root
starrocks.jdbc.password=
starrocks.database=profiling
starrocks.table=profile
key.converter=org.apache.kafka.connect.json.JsonConverter
value.converter=org.apache.kafka.connect.json.JsonConverter
key.converter.schemas.enable=true
value.converter.schemas.enable=false
```

### 4. Tạo script khởi tạo MongoDB

Tạo file `mongo-scripts/rs-init.sh`:
```bash
#!/bin/bash
mongosh --eval "rs.initiate({
 _id: 'rs0',
 members: [{ _id: 0, host: 'localhost:27017' }]
})"
```

Tạo file `mongo-scripts/mongo-init.js`:
```javascript
db.createUser({
  user: 'admin',
  pwd: 'admin',
  roles: [
    {
      role: 'readWrite',
      db: 'admin'
    }
  ]
})
```

### 5. Tạo file cấu hình Monstache

Tạo file `streaming_elasticsearch.config.toml`:
```toml
[[mongo]]
uri = "mongodb://admin:admin@mongo:27017/admin?replicaSet=rs0"
direct-read-namespaces = ["profiling.profile"]

[[elasticsearch]]
urls = ["http://elasticsearch:9200"]
username = "elastic"
password = "changeme"
index-mapping = "mobio-profiling-v16_3"

[elasticsearch.bulk]
size = 1000
```

### 6. Khởi động hệ thống

1. Tạo các topic cần thiết cho Kafka Connect:
```bash
docker exec kafka /opt/bitnami/kafka/bin/kafka-topics.sh --create --topic connect-offsets --partitions 1 --replication-factor 1 --config cleanup.policy=compact --bootstrap-server kafka:9092
docker exec kafka /opt/bitnami/kafka/bin/kafka-topics.sh --create --topic connect-configs --partitions 1 --replication-factor 1 --config cleanup.policy=compact --bootstrap-server kafka:9092
docker exec kafka /opt/bitnami/kafka/bin/kafka-topics.sh --create --topic connect-status --partitions 1 --replication-factor 1 --config cleanup.policy=compact --bootstrap-server kafka:9092
```

2. Khởi động toàn bộ hệ thống:
```bash
docker-compose up -d
```

3. Kiểm tra trạng thái các container:
```bash
docker-compose ps
```

4. Kiểm tra Kafka Connect REST API:
```bash
curl http://localhost:8083/
```

5. Kiểm tra danh sách connector plugins:
```bash
curl http://localhost:8083/connector-plugins
```

## Đồng bộ MongoDB lên StarRocks

### Phương án: Sử dụng Debezium + Kafka + Kafka Streams + StarRocks Connector

Phương án này cho phép:
- Đồng bộ realtime từ MongoDB lên StarRocks
- Transform dữ liệu trước khi lưu vào StarRocks
- Xử lý các trường hợp đặc biệt như thêm trường mới, chuyển đổi kiểu dữ liệu
- Dễ dàng mở rộng logic xử lý dữ liệu

#### 1. Cài đặt Debezium MongoDB Connector
```bash
# Tải Debezium MongoDB Connector
wget https://repo1.maven.org/maven2/io/debezium/debezium-connector-mongodb/1.9.7.Final/debezium-connector-mongodb-1.9.7.Final-plugin.tar.gz

# Giải nén
tar -xzf debezium-connector-mongodb-1.9.7.Final-plugin.tar.gz

# Copy vào thư mục plugins của Kafka Connect
docker cp debezium-connector-mongodb-1.9.7.Final-plugin.tar.gz kafka-connect:/usr/share/confluent-hub-components/
```

#### 2. Cấu hình Debezium MongoDB Connector
```json
{
    "name": "mongo-connector",
    "config": {
        "connector.class": "io.debezium.connector.mongodb.MongoDbConnector",
        "mongodb.hosts": "rs0/mongo:27017",
        "mongodb.name": "mongo",
        "mongodb.user": "admin",
        "mongodb.password": "admin",
        "database.include.list": "profiling",
        "collection.include.list": "profiling.profile",
        "transforms": "unwrap",
        "transforms.unwrap.type": "io.debezium.transforms.ExtractNewDocumentState",
        "transforms.unwrap.drop.tombstones": "true",
        "key.converter": "org.apache.kafka.connect.json.JsonConverter",
        "value.converter": "org.apache.kafka.connect.json.JsonConverter",
        "key.converter.schemas.enable": "true",
        "value.converter.schemas.enable": "false"
    }
}
```

#### 3. Tạo connector
```bash
curl -X POST -H "Content-Type: application/json" --data @mongo-connector.json http://localhost:8083/connectors
```

#### 4. Tạo project Maven
```xml
<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0"
         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 http://maven.apache.org/xsd/maven-4.0.0.xsd">
    <modelVersion>4.0.0</modelVersion>

    <groupId>com.example</groupId>
    <artifactId>mongo-starrocks-sync</artifactId>
    <version>1.0-SNAPSHOT</version>

    <properties>
        <maven.compiler.source>8</maven.compiler.source>
        <maven.compiler.target>8</maven.compiler.target>
        <kafka.streams.version>3.3.1</kafka.streams.version>
        <jackson.version>2.13.0</jackson.version>
    </properties>

    <dependencies>
        <dependency>
            <groupId>org.apache.kafka</groupId>
            <artifactId>kafka-streams</artifactId>
            <version>${kafka.streams.version}</version>
        </dependency>
        <dependency>
            <groupId>com.fasterxml.jackson.core</groupId>
            <artifactId>jackson-databind</artifactId>
            <version>${jackson.version}</version>
        </dependency>
    </dependencies>

    <build>
        <plugins>
            <plugin>
                <groupId>org.apache.maven.plugins</groupId>
                <artifactId>maven-assembly-plugin</artifactId>
                <version>3.3.0</version>
                <configuration>
                    <descriptorRefs>
                        <descriptorRef>jar-with-dependencies</descriptorRef>
                    </descriptorRefs>
                    <archive>
                        <manifest>
                            <mainClass>com.example.MongoTransformStream</mainClass>
                        </manifest>
                    </archive>
                </configuration>
                <executions>
                    <execution>
                        <phase>package</phase>
                        <goals>
                            <goal>single</goal>
                        </goals>
                    </execution>
                </executions>
            </plugin>
        </plugins>
    </build>
</project>
```

#### 5. Tạo Kafka Streams Application
```java
package com.example;

import org.apache.kafka.streams.StreamsBuilder;
import org.apache.kafka.streams.StreamsConfig;
import org.apache.kafka.streams.kstream.KStream;
import org.apache.kafka.streams.KeyValue;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.util.Properties;

public class MongoTransformStream {
    public static void main(String[] args) {
        StreamsBuilder builder = new StreamsBuilder();
        
        // Đọc dữ liệu từ topic mongo_changes
        KStream<String, JsonNode> source = builder.stream("mongo_changes");
        
        // Transform dữ liệu
        KStream<String, JsonNode> transformed = source.map((key, value) -> {
            ObjectNode transformedValue = (ObjectNode) value.deepCopy();
            
            // Thêm trường mới
            transformedValue.put("processed_at", System.currentTimeMillis());
            
            // Transform dữ liệu
            if (value.has("age")) {
                int age = value.get("age").asInt();
                String ageGroup = calculateAgeGroup(age);
                transformedValue.put("age_group", ageGroup);
            }
            
            // Xử lý các trường hợp đặc biệt
            if (value.has("status")) {
                String status = value.get("status").asText();
                transformedValue.put("is_active", "ACTIVE".equals(status));
            }
            
            return KeyValue.pair(key, transformedValue);
        });
        
        // Ghi vào topic mới
        transformed.to("transformed_data");
        
        // Khởi động ứng dụng
        KafkaStreams streams = new KafkaStreams(builder.build(), getStreamsConfig());
        streams.start();
        
        // Thêm shutdown hook
        Runtime.getRuntime().addShutdownHook(new Thread(streams::close));
    }
    
    private static String calculateAgeGroup(int age) {
        if (age < 18) return "minor";
        if (age < 30) return "young";
        if (age < 50) return "middle";
        return "senior";
    }
    
    private static Properties getStreamsConfig() {
        Properties props = new Properties();
        props.put(StreamsConfig.APPLICATION_ID_CONFIG, "mongo-transform-stream");
        props.put(StreamsConfig.BOOTSTRAP_SERVERS_CONFIG, "localhost:9092");
        props.put(StreamsConfig.DEFAULT_KEY_SERDE_CLASS_CONFIG, "org.apache.kafka.common.serialization.Serdes$StringSerde");
        props.put(StreamsConfig.DEFAULT_VALUE_SERDE_CLASS_CONFIG, "org.apache.kafka.common.serialization.Serdes$StringSerde");
        return props;
    }
}
```

#### 6. Cấu hình StarRocks Connector cho topic đã transform
```properties
name=starrocks-sink
connector.class=com.starrocks.connector.kafka.sink.StarRocksSinkConnector
tasks.max=1
topics=transformed_data
starrocks.jdbc.url=jdbc:mysql://starrock:9030
starrocks.jdbc.user=root
starrocks.jdbc.password=
starrocks.database=profiling
starrocks.table=profile
key.converter=org.apache.kafka.connect.json.JsonConverter
value.converter=org.apache.kafka.connect.json.JsonConverter
key.converter.schemas.enable=true
value.converter.schemas.enable=false
```

#### 7. Chạy ứng dụng
```bash
# Build project
        mvn clean package

# Chạy ứng dụng
java -jar target/mongo-starrocks-sync-1.0-SNAPSHOT-jar-with-dependencies.jar
```

#### 8. Kiểm tra luồng dữ liệu
1. Kiểm tra topic mongo_changes:
```bash
docker exec kafka /opt/bitnami/kafka/bin/kafka-console-consumer.sh --bootstrap-server kafka:9092 --topic mongo_changes --from-beginning
```

2. Kiểm tra topic transformed_data:
```bash
docker exec kafka /opt/bitnami/kafka/bin/kafka-console-consumer.sh --bootstrap-server kafka:9092 --topic transformed_data --from-beginning
```

3. Kiểm tra dữ liệu trong StarRocks:
```sql
SELECT * FROM profiling.profile LIMIT 10;
```

## Kiểm tra hệ thống

1. Kiểm tra MongoDB:
```bash
docker exec -it mongo mongosh -u admin -p admin
```

2. Kiểm tra Elasticsearch:
```bash
curl -u elastic:changeme http://localhost:9200
```

3. Kiểm tra StarRocks:
```bash
mysql -h localhost -P 9030 -u root
```

4. Kiểm tra Redis:
```bash
docker exec -it redis redis-cli
```

## Xử lý sự cố

1. Nếu Kafka Connect không khởi động được:
- Kiểm tra logs: `docker logs kafka-connect`
- Đảm bảo các topic cần thiết đã được tạo
- Kiểm tra cấu hình trong các file properties

2. Nếu MongoDB không kết nối được:
- Kiểm tra replica set đã được khởi tạo chưa
- Kiểm tra credentials trong mongo-init.js

3. Nếu Elasticsearch không khởi động được:
- Kiểm tra logs: `docker logs elasticsearch`
- Đảm bảo đủ RAM cho container

4. Nếu StarRocks không khởi động được:
- Kiểm tra logs: `docker logs starrock`
- Đảm bảo các port không bị conflict


