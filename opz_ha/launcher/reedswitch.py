import logging
import threading
import OPi.GPIO as GPIO
from opz_ha.defaults import INTERVAL, QOS, RETAIN, RS_TOPIC_BASE
from opz_ha.devices  import ReedSwitch
from opz_ha.utils    import check_config, get_mode

logger = logging.getLogger(__name__)

def constructor(*a, **k):
    rs = ReedSwitch(*a, **k)

def launcher(mqttc, modestring, switches):
    """
    switches is an array of reed switch configuration data, 
    as extracted from this YAML:
    mode: SUNXI                                 # Must be one of BOARD, SUNXI, BCM
    reed_switches:
      - channel: PA12                           # Required value.  If mode is SUNXI, value should be in format of PnXX
        topic: opz2/reed_switches/freezer_door  # Default value is $HOSTNAME/reed_switches/$CHANNEL
        qos: 0                                  # Default is 2
        retain: true                            # Default is true
        meta: Upright refrigerator              # Optional metadata field to describe anything.  Does not get sent.
      - channel: PA11                           # Required value
        topic: opz2/reed_switches/garage_door   # Default value is $HOSTNAME/reed_switches/$CHANNEL
        ...
    """
    threadnum = 1
    threads = []
    mode = get_mode(modestring)
    for switch in switches:
        channel = check_config(switch, 'channel', msg='GPIO channel not configured for {0}'.format(switch))
        topic   = check_config(switch, 'topic', default='{0}/{1}'.format(RS_TOPIC_BASE, channel))
        qos     = check_config(switch, 'qos', default=QOS)
        retain  = check_config(switch, 'retain', default=RETAIN)
        logger.debug('Spawning thread to report state of channel "{0}" to topic {1}'.format(channel, topic))
        thread = threading.Thread(
            target=constructor, 
            args=(mqttc, modestring, channel, topic, qos, retain), 
            kwargs={},
            name='reedswitch-{0}'.format(threadnum)
        )
        thread.daemon = True
        thread.start()  
        threadnum += 1
        threads.append(thread)