import logging
import threading
from opz_ha.devices  import OneWire
from opz_ha.defaults import INTERVAL
from opz_ha.utils    import check_config

logger = logging.getLogger(__name__)

def constructor(*a, **k):
    ow = OneWire(*a, **k)

def launcher(mqttc, config):
    """
    onewire:
      interval: 120              # Default value is 120
      devices: 
        family: 28               # Default is 28
        serial: 0516a04747ff     # Required value
        filename: w1_slave       # Default is w1_slave
        topic:                   # Default value is $HOSTNAME/1wire/$SERIAL
        qos: 0                   # Default is 2
        retain: true             # Default is true
        temp_scale: F            # Default is C
        meta: House Front Temp   # Optional metadata field to describe anything.  Does not get sent.
    """
    interval = check_config(config, 'interval', default=INTERVAL)
    devices  = check_config(config, 'devices', msg='No 1-Wire devices in configuration: {0}'.format(config))
    logger.debug('Spawning thread to report 1-Wire temperatures at {0} second intervals'.format(interval))
    thread = threading.Thread(
        target=constructor, 
        args=(mqttc, devices, interval),
        kwargs={},
        name='onewire'
    )
    thread.daemon = True
    thread.start()  