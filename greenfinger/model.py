import time
from machine import Pin, ADC
import ha_api

class MoistureSensor:
    def __init__(self, pin):
        self.pin = pin
        self.adc = ADC(0)
        self._power_off()

    def measure(self):
        try:
            val_0 = self.adc.read()
            self._power_high()
            time.sleep(0.05)
            val_1 = self.adc.read()
            self._power_low()
            time.sleep(0.05)
            val_2 = self.adc.read()
        finally:
            self._power_off()
            time.sleep(0.05)
        # Simple denoising
        measured = max(0, (val_1 - val_0) - (val_2 - val_0))
        measured = 100 * measured / 1023
        return measured

    def _power_high(self):
        p = Pin(self.pin, Pin.OUT)
        p.value(1)

    def _power_low(self):
        p = Pin(self.pin, Pin.OUT)
        p.value(0)

    def _power_off(self):
        Pin(self.pin, Pin.IN)


class Pump:
    def __init__(self, pin):
        self.pin = Pin(pin, Pin.OUT)
        self.pin.value(0)

    def enable(self, seconds):
        try:
            # enable
            self.pin.value(1)
            time.sleep(seconds)
        finally:
            # Disable
            self.pin.value(0)


class Entity:
    """
    Sensor + Pump + Support
    """
    def __init__(self, eid, sensor_pin, pump_pin, target_moisture, water_time):
        self.eid = eid
        self.sensor = MoistureSensor(sensor_pin)
        self.pump = Pump(pump_pin)
        self.target_moisture = target_moisture
        self.water_time = water_time
        self.ha_pump = None
        self.ha_sensor = None
        self.cnts = {
            "cnt": 0,
            "sum": 0.0,
            "min": 65535,
            "max": 0,
            "cur": -1.0,
            "waterings": 0,
            "triages": 0,
        }

    def setup_homeassistant(self, mqtt):
        self.ha_pump = ha_api.BinarySensor(mqtt, "Pump: " + self.eid,
                                           device_class="motion",
                                           object_id="greenfinger_pump_" + self.eid)

        self.ha_sensor = ha_api.Sensor(mqtt, "Moisture: " + self.eid,
                                       unit="%",
                                       device_class="humidity",
                                       object_id="greenfinger_moisture_" + self.eid)

    def measure(self):
        value = self.sensor.measure()
        self.cnts['cnt'] += 1
        self.cnts['sum'] += value
        self.cnts['cur'] = value
        self.cnts['min'] = min(self.cnts['min'], value)
        self.cnts['max'] = max(self.cnts['max'], value)

    def triage(self):
        "Should we water the plant, or not?"
        avg_moisture = self.cnts['sum'] / self.cnts['cnt']
        if avg_moisture < self.target_moisture:
            # Water.
            try:
                self.ha_pump.on()
                self.pump.enable(seconds=self.water_time)
            finally:
                self.ha_pump.off()
            self.cnts['waterings'] += 1
        self.cnts['triages'] += 1

        self.cnts['min'] = 65535
        self.cnts['max'] = 0
        self.cnts['cnt'] = 0
        self.cnts['sum'] = 0.0

        if self.ha_sensor:
            self.ha_sensor.update(avg_moisture)

        return avg_moisture
