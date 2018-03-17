# mysql_binlog_kinesis_producer
Batch MySQL binary log records to AWS Kinesis Firehose.

NOTE: This app has not yet been used in a production environment.


## Getting Started

These instructions will get you a copy of the project up and running on your local machine for development and testing purposes. See deployment for notes on how to deploy the project on a live system.


### Prerequisites

You can use either python3 or pypy3 to run this app. You will also need virtualenv installed


### Installing and Running

1. You will need a connection to MySQL with replication enabled
```
[mysqld]
server-id		 = 1
log_bin			 = /var/log/mysql/mysql-bin.log
expire_logs_days = 10
max_binlog_size  = 100M
binlog-format    = row #Very important if you want to receive write, update and delete row events
```

2. Create a mysql user with the neccessary replication permissions
```sql
CREATE USER 'replicationuser'@'%' IDENTIFIED BY 'somelongandspecialpassword';
GRANT REPLICATION SLAVE ON *.* TO 'replicationuser'@'%';
GRANT REPLICATION CLIENT ON *.* TO 'replicationuser'@'%';
GRANT SELECT ON *.* TO 'replicationuser'@'%';
```

3. Rename example.env to .env. This project uses the dotenv library to read .env configuration files
```bash
mv example.env .env
```

4. Edit the .env file with the appropriate MySQL connection settings and AWS credentials and service configuration
```
MYSQL_HOST=0.0.0.0
MYSQL_PORT=3306
MYSQL_USER='root'
MYSQL_PASSWORD='pass'
MYSQL_CONN_LIMIT=1
MYSQL_CHARSET='UTF8_UNICODE_CI'
MYSQL_SLAVE_HEARTBEAT=2
AWS_ACCESS_KEY_ID='AKIAfakeaccesskeyid'
AWS_SECRET_ACCESS_KEY='wsomefakeawssecretaccesskeythatmeansnothing'
AWS_REGION='us-west-2'
AWS_S3_BUCKET='<S3_Bucket_to_save_binlog_checkpoint_state'
AWS_S3_STATE_FILE='checkpoint.json'
AWS_KINESIS_FIREHOSE_STREAM_NAME='Kinesis_firehose_stream_name'
AWS_KINESIS_FIREHOSE_FLUSH_INTERVAL=.01
AWS_S3_FLUSH_INTERVAL=3
MAX_WORKERS=50
BINLOG_STREAM_READER_SERVER_ID=100
BINLOG_STREAM_READER_RESUME_STREAM=True
BINLOG_STREAM_READER_BLOCKING=True
```

5. Setup your virtualenv environment under ~/.venvs/mysql_binlog_kinesis_producer
```bash
make env
```

6. Activate your virtual environment and run the app
```bash
make run
```


## Running the tests

TODO: write unit tests


## Deployment

TODO: Add additional notes about how to deploy this on a live system


## Built With

* [boto3](https://boto3.readthedocs.io/en/latest/) - The AWS SDK for Python
* [mysql-replication](https://github.com/noplay/python-mysql-replication) - Pure Python Implementation of MySQL replication protocol build on top of PyMYSQL. This allow you to receive event like insert, update, delete with their datas and raw SQL queries.


## Authors

* **[Josh Schell](https://github.com/jschell12)**


## License

This project is licensed under the MIT License - see the [LICENSE.md](LICENSE.md) file for details