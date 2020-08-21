# License: Apache 2.0
# Based on the source: https://github.com/webworxshop/micropython-room-sensor/blob/master/hassnode.py
# Redone quite a bit.

import ujson as json


class _Base:
    def __init__(self, mqtt, component, object_id, node_id=None,
                 discovery_prefix="homeassistant"):
        self.mqtt = mqtt
        if node_id is not None:
            fields = [discovery_prefix, component, node_id, object_id]
        else:
            fields = [discovery_prefix, component, object_id]

        base = "/".join(fields)
        self.config_topic = base + "/config"
        self.state_topic = base + "/state"

    def _set_config(self, config):
        message = json.dumps(config).encode('utf-8')
        self.mqtt.publish(self.config_topic, message, True, 1)

    def set_value(self, message):
        self.mqtt.publish(self.state_topic, message.encode('utf-8'))


class BinarySensor(_Base):
    def __init__(self, mqtt, name, device_class, object_id, node_id=None, discovery_prefix="homeassistant"):
        super().__init__(mqtt, "binary_sensor", object_id, node_id, discovery_prefix)
        config = {
            "name": name,
            "device_class": device_class,
            "state_topic": self.state_topic
        }
        self._set_config(config)

    def on(self):
        self.set_value("ON")

    def off(self):
        self.set_value("OFF")


class Sensor(_Base):
    def __init__(self, mqtt, name, unit, device_class, object_id, node_id=None,
                 value_template=None, discovery_prefix="homeassistant"):
        super().__init__(mqtt, "sensor", object_id, node_id, discovery_prefix)

        config = {
            "name": name,
            "unit_of_measurement": unit,
            "device_class": device_class,
            "state_topic": self.state_topic,
        }
        if value_template is not None:
            config['value_template'] = value_template
        self._set_config(config)

    def update(self, state):
        cmd = json.dumps(state)
        self.set_value(cmd)


class Switch(_Base):
    def __init__(self, mqtt, name, callback, device_class, object_id, node_id=None,
                 value_template=None, discovery_prefix="homeassistant"):
        super().__init__(mqtt, "switch", object_id, node_id, discovery_prefix)

        config = {
            "name": name,
            "device_class": device_class,
            "state_topic": self.state_topic,
        }
        self._set_config(config)
        self.mqtt.subscribe(self.state_topic, callback)
