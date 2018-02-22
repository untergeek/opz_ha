import time, threading, logging
import OPi.GPIO as GPIO
from ..devices import ReedSwitch
from ..utils import get_mode

logger = logging.getLogger(__name__)


def constructor(*a, **k):
    rs = ReedSwitch(*a, **k)

def launcher(mqttc, modestring, switches, interval=120, refresh=0.1):
    """
    switches is an array of reed switch configuration data, 
    as extracted from this YAML:
    mode: SUNXI
    reed_switches:
      - topic: opz2/reed_switches/freezer_door
        sunxi_id: PA12
        qos: 0
        retain: true
        interval: 120
        refresh: 0.1
      - topic: opz2/reed_switches/garage_door
        sunxi_id: PA11
        qos: 0
        retain: true
        interval: 120
        refresh: 0.1
    """
    threadnum = 1
    threads = []
    mode = get_mode(modestring)
    for switch in switches:
        topic = '{0}'.format(switch['topic'])
        logger.debug('reedswitch topic: {0}'.format(topic))
        qos = switch['qos'] if 'qos' in switch else 0
        retain = switch['retain'] if 'retain' in switch else True
        pubinterval = switch['interval'] if 'interval' in switch else interval
        refresh = switch['refresh'] if 'refresh' in switch else refresh
        channel = switch['channel'] if 'channel' in switch else RaiseRuntimeError('GPIO channel not configured for {0}'.format(switch))
        logger.debug('Spawning thread to report state of channel "{0}" to topic {1}'.format(channel, topic))
        thread = threading.Thread(
            target=constructor, 
            args=(mqttc, modestring, channel, topic), 
            kwargs={ 'qos':qos, 'retain':retain, 'interval':pubinterval, 'refresh':refresh },
            name='reedswitch-{0}'.format(threadnum)
        )
        thread.daemon = True
        thread.start()  
        threadnum += 1
        threads.append(thread)