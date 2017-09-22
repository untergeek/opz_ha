import time, threading, logging
# import paho.mqtt.client as mqtt
from pyA20.gpio import gpio, connector, port
from ..devices import OneWire

gpio.init()
logger = logging.getLogger(__name__)

def constructor(*a, **k):
    ow = OneWire(*a, **k)

def launcher(mqttc, config):
    """
    onewire:
      interval: 120
      topics:
        - topic_trunk: steiny/1wire
          devices: 
            - topic_leaf: house_front
              family: 28
              id: 0516a04747ff
              filename: w1_slave
              qos: 0
              retain: true
              temp_scale: F
    """
    interval = config['interval'] if 'interval' in config else 120
    topics = config['topics']
    thread = threading.Thread(
        target=constructor, 
        args=(mqttc, topics), 
        kwargs={ 'interval':interval },
        name='onewire'
    )
    thread.daemon = True
    thread.start()  