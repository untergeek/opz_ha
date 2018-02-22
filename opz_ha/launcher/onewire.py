import time, threading, logging
from ..devices import OneWire

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
    logger.debug('Spawning thread to report 1-Wire temperatures at {0} second intervals'.format(interval))
    topics = config['topics']
    thread = threading.Thread(
        target=constructor, 
        args=(mqttc, topics), 
        kwargs={ 'interval':interval },
        name='onewire'
    )
    thread.daemon = True
    thread.start()  