from collections import deque
import threading
import itertools
import ujson

class KinesisFirehoseStreamProducer(object):
    def __init__(self, kinesis_firehose_client, stream_name, thread_pool_executor):
        self.__kinesis_firehose_client = kinesis_firehose_client
        self.__stream_name  = stream_name
        self.__buffer = deque()
        self.__lock = threading.Lock()
        self.__thread_pool_executor = thread_pool_executor


    def append(self, item):
        self.__buffer.append({
            'Data': ujson.dumps(item).encode()
        })


    def buffer_count(self):
        return len(self.__buffer)


    def flush(self):
        buffer_count = self.buffer_count()
        if buffer_count:
            items = self.__pop_slice(buffer_count if buffer_count <= 500 else 500)

            task = self.__thread_pool_executor.submit(self.__kinesis_firehose_client.put_record_batch, 
                DeliveryStreamName=self.__stream_name, 
                Records = list(items)
            )
            task.arg = len(items)
            task.add_done_callback(self.__done_callback)
            return True
       
        return False


    def __pop_slice(self, count):
        popped=deque()
        for i in range(count):
            popped.append(self.__buffer.popleft())
        return popped

    def __done_callback(self, fn):
        print(fn.arg, 'events flushed.', flush=True)
