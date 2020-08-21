# Source: https://github.com/micropython/micropython-lib
from umqttsimple import MQTTClient as NotSoRobust
import utime

class MQTTClient(NotSoRobust):
    DELAY = 2
    DEBUG = True

    def reconnect(self):
        i = 0
        while 1:
            try:
                if self.sock:
                    self.poller_r.unregister(self.sock)
                    self.poller_w.unregister(self.sock)
                    self.sock.close()
                return super().connect(False)
            except OSError as e:
                print("Reconnect", i, e)
                i += 1
                utime.sleep(i)
            except Exception as e:
                print("OTHER ERROR", e)


    def publish(self, topic, msg, retain=False, qos=0):
        while 1:
            try:
                return super().publish(topic, msg, retain, qos)
            except OSError as e:
                print("Publish error", e)
            except Exception as e:
                print("OTHER ERROR", e)
            self.reconnect()

    def wait_msg(self):
        while 1:
            try:
                return super().wait_msg()
            except OSError as e:
                print("Wait error", e)
            self.reconnect()
