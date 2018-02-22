import time, threading, logging
import OPi.GPIO as GPIO
from ..devices import GDORelay

logger = logging.getLogger(__name__)

QOS = 2

def constructor(*a, **k):
    rs = GDORelay(*a, **k)

def launcher(mqttc, relays):
    """
    gdo_relay:
      - topic: opz1/gdo/main
        sunxi_id: PG7
        board_pin: 10
        qos: 2
    """
    threadnum = 1
    threads = []
    for relay in relays:
        topic = '{0}'.format(relay['topic'])
        qos = relay['qos'] if 'qos' in relay else QOS
        pin  = relay['board_pin'] if 'board_pin' in relay else None
        sunxi = relay['sunxi_id'] if 'sunxi_id' in relay else None
        if pin:
            mode = GPIO.BOARD
            channel = pin
        elif sunxi:
            mode = GPIO.SUNXI
            channel = sunxi_id
        else:
            raise RuntimeError('Unable to find GPIO channel for "{0}"'.format(topic))
        logger.debug('Spawning thread to read topic {0} and issue commands to channel {1}'.format(topic, channel))
        thread = threading.Thread(
            target=constructor, 
            args=(mqttc, mode, channel, topic), 
            kwargs={ 'qos':qos },
            name='gdorelay-{0}'.format(threadnum)
        )
        thread.daemon = True
        thread.start()  
        threadnum += 1
        threads.append(thread)