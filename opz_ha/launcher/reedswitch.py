import time, threading, logging
import OPi.GPIO as GPIO
from ..devices import ReedSwitch

logger = logging.getLogger(__name__)


def constructor(*a, **k):
    rs = ReedSwitch(*a, **k)

def launcher(mqttc, switches, interval=120, refresh=0.1):
    """
    switches is an array of reed switch configuration data, 
    as extracted from this YAML:
      - topic: opz2/reed_switches/freezer_door
        sunxi_id: PA12
        board_pin: 3
        qos: 0
        retain: true
        interval: 120
        refresh: 0.1
      - topic: opz2/reed_switches/garage_door
        sunxi_id: PA11
        board_pin: 5
        qos: 0
        retain: true
        interval: 120
        refresh: 0.1
    """
    threadnum = 1
    threads = []
    for switch in switches:
        topic = '{0}'.format(switch['topic'])
        logger.debug('reedswitch topic: {0}'.format(topic))
        qos = switch['qos'] if 'qos' in switch else 0
        retain = switch['retain'] if 'retain' in switch else True
        pubinterval = switch['interval'] if 'interval' in switch else interval
        refresh = switch['refresh'] if 'refresh' in switch else refresh
        pin  = switch['board_pin'] if 'board_pin' in switch else None
        sunxi = switch['sunxi_id'] if 'sunxi_id' in switch else None
        if pin:
            mode = GPIO.BOARD
            channel = pin
        elif sunxi:
            mode = GPIO.SUNXI
            channel = sunxi_id
        else:
            raise RuntimeError('Unable to find GPIO channel for "{0}"'.format(topic))
        logger.debug('Spawning thread to report state of channel {0} to topic {1}'.format(channel, topic))
        thread = threading.Thread(
            target=constructor, 
            args=(mqttc, mode, channel, topic), 
            kwargs={ 'qos':qos, 'retain':retain, 'interval':pubinterval, 'refresh':refresh },
            name='reedswitch-{0}'.format(threadnum)
        )
        thread.daemon = True
        thread.start()  
        threadnum += 1
        threads.append(thread)