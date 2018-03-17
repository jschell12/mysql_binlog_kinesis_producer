from collections import deque
import ujson
from botocore.exceptions import ClientError

class S3CheckpointWriter(object):
    def __init__(self, s3_client, s3_bucket, s3_key):
        self.s3_client = s3_client
        self.s3_bucket = s3_bucket
        self.s3_key = s3_key
        self.__buffer = deque()


    def append(self, item):
        self.__buffer.append(ujson.dumps(item).encode())


    def __buffer_count(self):
        return len(self.__buffer)

    def peek(self):
        if len(self.__buffer):
            return self.__buffer[0]
        return None

    def init(self, item):
        self.append(ujson.dumps(item).encode())
        self.flush()

    def flush(self):
        if self.__buffer_count():
            item = self.__buffer.pop()
            self.s3_client.put_object(Body=item, Bucket=self.s3_bucket, Key=self.s3_key)
            self.__buffer.clear()
            return True
        return False



class S3CheckpointReader(object):
    def __init__(self, s3_client, s3_bucket, s3_key):
        self.s3_client = s3_client
        self.s3_bucket = s3_bucket
        self.s3_key = s3_key


    def fetch(self):
        log_obj = {'log_file': None, 'log_pos': None}

        try:
            log_json=self.s3_client.get_object(    
                Bucket=self.s3_bucket,
                Key=self.s3_key
            )
            log_obj = ujson.loads(log_json['Body'].read())
            
            return log_obj
        except ClientError as ex:
            if ex.response['Error']['Code'] == 'NoSuchKey':
                print('No checkpoint saved', flush=True)
            else:
                raise ex
        
        return log_obj