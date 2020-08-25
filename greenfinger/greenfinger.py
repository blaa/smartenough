# (C) 2020 by Tomasz bla Fortuna
# License: MIT

import utime as time
import gc
import network
# Import big modules early
from umqttrobust import MQTTClient
gc.collect()

from machine import Pin, I2C
import dht
import config as cfg
import ha_api

gc.collect()

from model import Entity
import ssd1306

gc.collect()
print("RAM 0:", gc.mem_free())

# import micropython
# micropython.alloc_emergency_exception_buf(100)


def connect():
    cli = network.WLAN(network.STA_IF)
    cli.active(True)
    cli.connect(cfg.WIFI_NAME, cfg.WIFI_PASS)
    sta = network.WLAN(network.AP_IF)
    sta.active(False)


class Display:
    def __init__(self, scl=13, sda=4):
        self.i2c = I2C(-1, scl=Pin(scl), sda=Pin(sda))
        self.oled = ssd1306.SSD1306_I2C(128, 32, self.i2c)
        self.oled.fill(0)
        self.oled.text("Initialized", 0, 0)
        self.oled.show()

    def refresh(self, uptime, entities, cur_air):
        "Given internal state, handle the UI"
        spacing = 8
        line = 0
        self.oled.fill(0)
        msg = "up={}".format(uptime)
        self.oled.text(msg, 0, 0)
        line += 1
        for entity in entities:
            msg = "{}: h{:.1f} w{}/{}"
            msg = msg.format(entity.eid,
                             entity.cnts["cur"],
                             entity.cnts["waterings"],
                             entity.cnts["triages"])
            self.oled.text(msg, 0, line * spacing)
            line += 1

        msg = "{}C {}%".format(cur_air['temp'], cur_air['humid'])
        self.oled.text(msg, 0, line * spacing)
        self.oled.show()


class AirState:
    UPDATE_CYCLE = 10
    def __init__(self, pin, offset_temp, offset_humid):
        self.pin = Pin(pin, Pin.OUT, Pin.PULL_UP)
        self.dht = dht.DHT11(self.pin)
        self.state = {
            'temp': -1,
            'humid': -1,
            'error': False,
        }
        self.offset_temp = offset_temp
        self.offset_humid = offset_humid
        self.last_read = 0

        # Warm-up
        self.dht.measure()

    def _update(self):
        try:
            self.dht.measure()
            self.state['temp'] = self.dht.temperature() + self.offset_temp
            self.state['humid'] = self.dht.humidity() + self.offset_humid
            self.state['error'] = False
        except OSError as e:
            print("Error while updating DHT", e)
            self.state['error'] = True

    def get(self):
        now = time.time()
        if now > self.last_read + self.UPDATE_CYCLE:
            self._update()
            self.last_read = now
        return self.state


class GreenFinger:
    "Tend to the flowers"
    MAIN_CYCLE = 10 * 60
    def __init__(self, mqtt, entities, air_state, display):
        self.entities = entities
        self.display = display
        self.air_state = air_state
        self.start = time.time()
        self.ts_last_triage = self.start

        self.ha_air_temp = ha_api.Sensor(mqtt, "Air temperature",
                                         unit="C",
                                         device_class="temperature",
                                         object_id="greenfinger_air_temp")

        self.ha_air_humidity = ha_api.Sensor(mqtt, "Air humidity",
                                             unit="%",
                                             device_class="humidity",
                                             object_id="greenfinger_air_humidity")

        #self.wdt = WDT(timeout=20000)

    def loop(self):
        i = 0
        while True:
            now = time.time()

            for entity in self.entities:
                entity.measure()

            if self.ts_last_triage + self.MAIN_CYCLE < now:
                for entity in self.entities:
                    entity.triage()
                self.ts_last_triage = now

            elapsed = now - self.start
            cur_air = self.air_state.get()
            self.display.refresh(elapsed, self.entities, cur_air)

            i += 1

            if i % 6 == 0:
                # TEMPORARY: Update each time
                self.ha_air_temp.update(cur_air['temp'])
                self.ha_air_humidity.update(cur_air['humid'])

            gc.collect()
            if i % 10 == 0:
                print("Free Mem: ", gc.mem_free())
            # self.wdt.feed()
            time.sleep(10)


def connect_mqtt():
    ip, port = cfg.MQTT_SERVER
    mqtt = MQTTClient(cfg.MQTT_CLIENT_ID, server=ip, port=port,
                      user=cfg.MQTT_USER, password=cfg.MQTT_PASS)
    # user="your_username", password="your_api_key",
    # mqtt.set_callback(sub_callback)
    mqtt.connect(clean_session=True)
    return mqtt


def run():
    connect()
    gc.collect()
    mqtt = connect_mqtt()
    gc.collect()

    entity_a = Entity("a", cfg.HUM_SENSOR_A, cfg.PUMP_A,
                      cfg.TARGET_MOISTURE_A, cfg.WATER_TIME_A)
    entity_b = Entity("b", cfg.HUM_SENSOR_B, cfg.PUMP_B,
                      cfg.TARGET_MOISTURE_B, cfg.WATER_TIME_B)
    entity_a.setup_homeassistant(mqtt)
    entity_b.setup_homeassistant(mqtt)

    air_state = AirState(pin=cfg.DHT_PIN, offset_temp=cfg.DHT_OFFSET_TEMP,
                         offset_humid=cfg.DHT_OFFSET_HUMID)
    display = Display(scl=cfg.DISPLAY_SCL, sda=cfg.DISPLAY_SDA)


    gf = GreenFinger(mqtt, [entity_a, entity_b], air_state, display)

    gc.collect()
    print("RAM AFTER SETUP:", gc.mem_free())
    gf.loop()
