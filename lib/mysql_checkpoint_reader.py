import pymysql.cursors



class MySQLCheckpointReader(object):
    def __init__(self, host, port, user, password):
        self.__host=host
        self.__port=port
        self.__user=user
        self.__password=password
        self.__cursorclass=pymysql.cursors.DictCursor

    def fetch_master_status(self):
        __master_status = {
            'log_file': None,
            'log_pos': None
        }

        __connection = pymysql.connect(
            host=self.__host,
            port=self.__port,
            user=self.__user,
            password=self.__password,
            cursorclass=self.__cursorclass)

        try:
            with __connection.cursor() as cursor:
                # Read a single record
                sql = 'SHOW MASTER STATUS;'
                cursor.execute(sql)
                result = cursor.fetchone()
                if result is not(None):
                    __master_status = result
        finally:
            __connection.close()

        return {'log_file': __master_status['File'], 'log_pos': __master_status['Position']}
        
