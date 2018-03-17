import os
import sys
import signal
import boto3
from concurrent.futures import ThreadPoolExecutor

from dotenv import load_dotenv, find_dotenv

from lib.binlog_stream_reader_wrapper import EventType, BinLogStreamReaderWrapper
from lib.set_interval import SetInterval
from lib.s3_checkpoint import S3CheckpointReader, S3CheckpointWriter
from lib.mysql_checkpoint_reader import MySQLCheckpointReader
from lib.kinesis_firehose_stream_producer import KinesisFirehoseStreamProducer
from lib.stream_processor import StreamProcessor
from lib.binlog_checkpoint import BinlogCheckpoint


def handle_signals():
    for i in [x for x in dir(signal) if x.startswith("SIG")]:
        try:
            signum = getattr(signal, i)
            if signum.name.startswith("Signals"):
                signal.signal(signum, sighandler)
        except (OSError, RuntimeError) as m: #OSError for Python3, RuntimeError for 2
            print ("Skipping {}".format(i), flush=True)

def sighandler(signal, frame):
    print('Signal', signal, frame)
    sys.exit(0)

def main():
    kinesis_firehose_client = None
    s3_client = None
    s3_checkpoint_writer = None
    s3_checkpoint_reader = None
    mysql_checkpoint_reader = None
    master_checkpoint = None
    last_saved_binlog_checkpoint = None
    bsrw = None
    ksp = None
    sp = None
    log_file = None
    log_pos = None

    # Load environment configuration variables
    load_dotenv(find_dotenv(), override=True)
    mysql_host = os.environ.get('MYSQL_HOST')
    mysql_port = int(os.environ.get('MYSQL_PORT'))
    mysql_user = os.environ.get('MYSQL_USER')
    mysql_password = os.environ.get('MYSQL_PASSWORD')
    mysql_slave_heartbeat = int(os.environ.get('MYSQL_SLAVE_HEARTBEAT'))
    aws_access_key_id = os.environ.get('AWS_ACCESS_KEY_ID')
    aws_secret_access_key = os.environ.get('AWS_SECRET_ACCESS_KEY')
    region_name = os.environ.get('AWS_REGION')
    s3_bucket = os.environ.get('AWS_S3_BUCKET')
    s3_checkpoint_file = os.environ.get('AWS_S3_STATE_FILE')
    kinesis_firehose_stream_name = os.environ.get('AWS_KINESIS_FIREHOSE_STREAM_NAME')
    kinesis_firehose_flush_interval = float(os.environ.get('AWS_KINESIS_FIREHOSE_FLUSH_INTERVAL'))
    s3_flush_interval = float(os.environ.get('AWS_S3_FLUSH_INTERVAL'))
    max_workers = int(os.environ.get('MAX_WORKERS'))
    binlog_stream_reader_server_id = int(os.environ.get('BINLOG_STREAM_READER_SERVER_ID'))
    binlog_stream_reader_resume_stream = os.environ.get('BINLOG_STREAM_READER_RESUME_STREAM')
    binlog_stream_reader_blocking = os.environ.get('BINLOG_STREAM_READER_BLOCKING')


    handle_signals()
            
    kinesis_firehose_client = boto3.client(
        'firehose',
        aws_access_key_id=aws_access_key_id,
        aws_secret_access_key=aws_secret_access_key,
        region_name=region_name)

    s3_client = boto3.client(
        's3',
        aws_access_key_id=aws_access_key_id,
        aws_secret_access_key=aws_secret_access_key,
        region_name=region_name)

    s3_checkpoint_reader = S3CheckpointReader(
        s3_client, s3_bucket=s3_bucket, s3_key=s3_checkpoint_file)

    s3_checkpoint_writer = S3CheckpointWriter(
        s3_client, s3_bucket=s3_bucket, s3_key=s3_checkpoint_file)

    mysql_checkpoint_reader = MySQLCheckpointReader(
        host=mysql_host,
        port=mysql_port,
        user=mysql_user,
        password=mysql_password)


    
    master_checkpoint = BinlogCheckpoint(**mysql_checkpoint_reader.fetch_master_status())
    print('Master status log file', master_checkpoint.log_file, 'at log position', master_checkpoint.log_pos, flush=True)
    last_saved_binlog_checkpoint = BinlogCheckpoint(**s3_checkpoint_reader.fetch())
    print('S3 checkpoint status log file', last_saved_binlog_checkpoint.log_file, 'at log position', last_saved_binlog_checkpoint.log_pos, flush=True)
    
    
    log_file = last_saved_binlog_checkpoint.log_file
    log_pos = last_saved_binlog_checkpoint.log_pos
    if (last_saved_binlog_checkpoint.log_file is None or last_saved_binlog_checkpoint.log_pos is None) or last_saved_binlog_checkpoint.log_file != master_checkpoint.log_file:
        log_file = master_checkpoint.log_file
        log_pos = master_checkpoint.log_pos
    

    print('Starting from log file', log_file, 'at log position', log_pos, flush=True)

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        bsrw = BinLogStreamReaderWrapper(
            {
                'host': mysql_host,
                'port': mysql_port,
                'user': mysql_user,
                'passwd': mysql_password
            },
            server_id=binlog_stream_reader_server_id,
            resume_stream=binlog_stream_reader_resume_stream,
            blocking=binlog_stream_reader_blocking,
            log_file=log_file,
            log_pos=log_pos,
            slave_heartbeat=mysql_slave_heartbeat)


        kfsp = KinesisFirehoseStreamProducer(
            kinesis_firehose_client = kinesis_firehose_client, 
            stream_name = kinesis_firehose_stream_name, 
            thread_pool_executor = executor
        )

        sp = StreamProcessor(
            binlog_stream_reader_wrapper=bsrw,
            kinesis_firehose_stream_producer=kfsp,
            s3_checkpoint_writer=s3_checkpoint_writer,
            kinesis_firehose_flush_interval=kinesis_firehose_flush_interval,
            s3_flush_interval=s3_flush_interval)

        try:
            print('Starting processor', flush=True)
            sp.start()
        except Exception as e:
            print('Caught Exception:', e, flush=True)
        finally:
            sp.close()


if __name__ == '__main__':
    main()