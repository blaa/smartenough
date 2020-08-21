"""
Configuration template
"""

MQTT_CLIENT_ID = "greenfinger1"
MQTT_SERVER = ("IP.ADDRESS", 1883)
MQTT_USER = None
MQTT_PASS = None

DISPLAY_SCL = const(13)
DISPLAY_SDA = const(4)

DHT_PIN = const(2)
DHT_OFFSET_TEMP = const(-3)
DHT_OFFSET_HUMID = const(0)

HUM_SENSOR_A = const(16)
HUM_SENSOR_B = const(5)
PUMP_A = const(14)
PUMP_B = const(12)

TARGET_MOISTURE_A = const(5)
TARGET_MOISTURE_B = const(5)
WATER_TIME_A = const(5)
WATER_TIME_B = const(5)

WIFI_NAME = "NAME"
WIFI_PASS = "PASS"
