import threading
import time

class SetInterval(object):
    def __init__(self, interval, action):
        self.__interval = interval
        self.__action = action
        self.__stop_event = threading.Event()
        self.__thread = threading.Thread(target=self.__set_interval)

    def __set_interval(self):
        next_time = time.time() + self.__interval
        while not (self.__stop_event.wait(next_time - time.time())):
            next_time += self.__interval
            try:
                self.__action()
            except Exception as e: 
                print('SetInterval - Caught Exception:', e, flush=True)
                pass

    def start(self):
        self.__thread.start()

    def cancel(self):
        self.__stop_event.set()
        