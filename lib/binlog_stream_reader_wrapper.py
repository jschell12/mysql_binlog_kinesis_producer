import datetime
from enum import Enum
from pymysqlreplication import BinLogStreamReader
from pymysqlreplication.row_event import (
    DeleteRowsEvent,
    UpdateRowsEvent,
    WriteRowsEvent,
    TableMapEvent
)
from pymysqlreplication.event import (
    BeginLoadQueryEvent,
    ExecuteLoadQueryEvent,
    QueryEvent,
    RotateEvent,
    HeartbeatLogEvent
)
from lib.utils import Utils
 
class EventType(Enum):
    LOG_STATE = 1
    INSERT = 2
    UPDATE = 3
    DELETE = 4
    TABLE = 5
    OTHER = 6


class BinLogStreamReaderWrapper(object):
    ''' Wrapper class for the python-mysql-replication library '''
    def __init__(self, mysql_settings,server_id=1,blocking=False, resume_stream=True, log_file=None, log_pos=None, slave_heartbeat=None):
        self.__stream = BinLogStreamReader(
            connection_settings = mysql_settings,
            server_id = server_id,
            blocking = blocking,
            resume_stream = resume_stream,
            only_events = [DeleteRowsEvent, WriteRowsEvent, UpdateRowsEvent, TableMapEvent,  BeginLoadQueryEvent, ExecuteLoadQueryEvent, QueryEvent], # RotateEvent, QueryEvent, HeartbeatLogEvent
            log_file=log_file, 
            log_pos=log_pos,
            slave_heartbeat=slave_heartbeat
        )

    def close(self):
        self.__stream.close()

    def fetch_event(self):
        return self.__parse_event(self.__stream.fetchone())

    def __iter__ (self):
        return iter(self.fetch_event, None)

    def __parse_event(self, binlogevent):
        event = {
            'event_type': self.__get_event_type(binlogevent),
            'pymysqlreplication_event_type': type(binlogevent).__name__,
            'timestamp': binlogevent.timestamp,
            'log_pos': binlogevent.packet.log_pos,
            'log_file': self.__stream.log_file
        }

        if self.__is_query_event(binlogevent):
            event['log_pos'] = binlogevent.packet.log_pos
            event['log_file'] = self.__stream.log_file
        elif self.__is_rotate_event(binlogevent):
            event['log_pos'] = binlogevent.position
            event['log_file'] = binlogevent.next_binlog
        elif self.__is_row_event(binlogevent) or self.__is_table_event(binlogevent):
            if binlogevent.schema != 'auth': # For security
                event['schema'] = binlogevent.schema
                event['table'] = binlogevent.table

                if self.__is_row_event(binlogevent):
                    for row in binlogevent.rows:
                        event['primary_key'] = binlogevent.primary_key
                        event['after_values'] = self.__get_before_values(binlogevent, row)
                        event['before_values'] = self.__get_after_values(binlogevent, row)
        elif self.__is_heartbeat_event(binlogevent):
            event['log_file'] = binlogevent.ident


        return event



    def __get_event_type(self, binlogevent):
        event_type = None

        if self.__is_heartbeat_event(binlogevent) or self.__is_rotate_event(binlogevent) or self.__is_heartbeat_event(binlogevent):
            event_type = EventType.LOG_STATE
        elif self.__is_delete_event(binlogevent):
            event_type = EventType.DELETE
        elif self.__is_update_event(binlogevent):
            event_type = EventType.UPDATE
        elif self.__is_insert_event(binlogevent):
            event_type = EventType.INSERT
        elif self.__is_table_event(binlogevent):
            event_type = EventType.TABLE
        else:
            event_type = EventType.OTHER
        
        return event_type
    
    def __get_before_values(self, binlogevent, row):
        before_values = None
        if isinstance(binlogevent, UpdateRowsEvent):
            before_values =  row['before_values']
        elif isinstance(binlogevent, DeleteRowsEvent):
            before_values =  row['values']
        
        return before_values
    
    def __get_after_values(self, binlogevent, row):
        after_values = None
        if isinstance(binlogevent, WriteRowsEvent):
            after_values = row['values']
        elif isinstance(binlogevent, UpdateRowsEvent):
            after_values =  row['after_values']
        
        return after_values

    def __is_row_event(self, binlogevent):
        return self.__is_insert_event(binlogevent) or self.__is_update_event(binlogevent) or self.__is_delete_event(binlogevent)

    def __is_delete_event(self, binlogevent):
        return isinstance(binlogevent, DeleteRowsEvent)

    def __is_update_event(self, binlogevent):
        return isinstance(binlogevent, UpdateRowsEvent)

    def __is_insert_event(self, binlogevent):
        return isinstance(binlogevent, WriteRowsEvent)

    def __is_table_event(self, binlogevent):
        return isinstance(binlogevent, (TableMapEvent))

    def __is_query_event(self, binlogevent):
        return isinstance(binlogevent, (QueryEvent))

    def __is_begin_query_event(self, binlogevent):
        return isinstance(binlogevent, (BeginLoadQueryEvent))

    def __is_load_query_event(self, binlogevent):
        return isinstance(binlogevent, (ExecuteLoadQueryEvent))

    def __is_rotate_event(self, binlogevent):
        return isinstance(binlogevent, (RotateEvent))

    def __is_heartbeat_event(self, binlogevent):
        return isinstance(binlogevent, (HeartbeatLogEvent))