import time, threading, logging
import OPi.GPIO as GPIO
from ..devices import GDORelay
from ..utils import get_mode

logger = logging.getLogger(__name__)

QOS = 2

def constructor(*a, **k):
    rs = GDORelay(*a, **k)

def launcher(mqttc, modestring, relays):
    """
    mode: BOARD
    gdo_relay:
      - topic: opz1/gdo/main
        channel: 10
        qos: 2
    """
    threadnum = 1
    threads = []
    for relay in relays:
        topic = '{0}'.format(relay['topic'])
        qos = relay['qos'] if 'qos' in relay else QOS
        channel = relay['channel'] if 'channel' in relay else RaiseRuntimeError('GPIO channel not configured for {0}'.format(topic))
        logger.debug('Spawning thread to read topic {0} and issue commands to channel {1}'.format(topic, channel))
        thread = threading.Thread(
            target=constructor, 
            args=(mqttc, modestring, channel, topic), 
            kwargs={ 'qos':qos },
            name='gdorelay-{0}'.format(threadnum)
        )
        thread.daemon = True
        thread.start()  
        threadnum += 1
        threads.append(thread)