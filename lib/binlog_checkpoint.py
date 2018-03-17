
class BinlogCheckpoint(object):
    def __init__(self, log_file = None, log_pos = None):
        self.log_file = log_file
        self.log_pos = log_pos