import logging
import threading
import OPi.GPIO as GPIO
from opz_ha.defaults import GDO_TOPIC_BASE, QOS, RETAIN
from opz_ha.devices import GDORelay
from opz_ha.utils import config_check, get_mode

logger = logging.getLogger(__name__)

def constructor(*a, **k):
    rs = GDORelay(*a, **k)

def launcher(mqttc, modestring, relays):
    """
    mode: BOARD                # Must be one of BOARD, SUNXI, or BCM
    gdo_relay:
      - channel: 10            # If mode is BOARD, this value should be an integer pin number as counted on the Orange Pi Zero Board
        topic: opz1/gdo/main   # Default is $HOSTNAME/gdo/$CHANNEL
        qos: 2                 # Default is 2
        retain: true           # Default is True
        meta: Main Door        # Optional metadata field to describe anything.  Does not get sent.
    """
    threadnum = 1
    threads = []
    for relay in relays:
        channel = check_config(relay, 'channel', msg='GPIO channel not configured for {0}'.format(relay))
        topic   = check_config(relay, 'topic', default='{0}/{1}'.format(GDO_TOPIC_BASE, channel))
        qos     = check_config(relay, 'qos', default=QOS)
        retain  = check_config(relay, 'retain', default=RETAIN)
        logger.debug('Spawning thread to read topic {0} and issue commands to channel {1}'.format(topic, channel))
        thread = threading.Thread(
            target=constructor, 
            args=(mqttc, modestring, channel, topic, qos, retain), 
            kwargs={},
            name='gdorelay-{0}'.format(threadnum)
        )
        thread.daemon = True
        thread.start()  
        threadnum += 1
        threads.append(thread)