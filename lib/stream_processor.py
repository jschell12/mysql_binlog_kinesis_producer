import ujson
from lib.set_interval import SetInterval
from lib.binlog_stream_reader_wrapper import EventType
from lib.utils import Utils
from lib.binlog_checkpoint import BinlogCheckpoint

class StreamProcessor(object):
    def __init__(self, binlog_stream_reader_wrapper, kinesis_firehose_stream_producer, s3_checkpoint_writer, kinesis_firehose_flush_interval, s3_flush_interval):
        self.__binlog_stream_reader_wrapper = binlog_stream_reader_wrapper
        self.__kinesis_firehose_stream_producer = kinesis_firehose_stream_producer
        self.__s3_checkpoint_writer = s3_checkpoint_writer
        self.__kinesis_firehose_flush_interval = kinesis_firehose_flush_interval
        self.__s3_flush_interval = s3_flush_interval
        self.__set_interval_kinesis_firehose_stream_producer = SetInterval(interval=self.__kinesis_firehose_flush_interval, action=self.__flush_events)
        self.__set_interval_s3_checkpoint_writer = SetInterval(interval=self.__s3_flush_interval, action=self.__flush_checkpoint)

    def start(self):
        self.__set_interval_kinesis_firehose_stream_producer.start()
        self.__set_interval_s3_checkpoint_writer.start()
        
        for event in self.__binlog_stream_reader_wrapper:
            binlog_checkpoint = BinlogCheckpoint(event['log_file'], event['log_pos'])
        
            self.__s3_checkpoint_writer.append(binlog_checkpoint)

            if event['event_type'] in [EventType.INSERT, EventType.UPDATE, EventType.DELETE, EventType.TABLE]:
                self.__kinesis_firehose_stream_producer.append(event)
            
        self.close()

    def __flush_events(self):
        self.__kinesis_firehose_stream_producer.flush()
        
    def __flush_checkpoint(self):
        self.__s3_checkpoint_writer.flush()

    def close(self):
        self.__binlog_stream_reader_wrapper.close()
        self.__set_interval_kinesis_firehose_stream_producer.cancel()
        self.__set_interval_s3_checkpoint_writer.cancel()