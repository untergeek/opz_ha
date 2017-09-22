import time, threading, logging, sys
# import paho.mqtt.client as mqtt
from pyA20.gpio import gpio, connector, port
from ..devices import GDORelay

logger = logging.getLogger(__name__)

QOS = 2
GPIO_BUS = 'gpio1'
gpio.init()

def constructor(*a, **k):
    rs = GDORelay(*a, **k)

def get_gpio_func(kind, val):
    return getattr(sys.modules['pyA20.gpio.{0}'.format(kind)],val)

def launcher(relays, client_id, username, password, hostname, port, keepalive):
    """
    gdo_relay:
      - topic: opz1/gdo/main
        gpio_port: PG7
        gpio_pin: 10
        qos: 2
    """
    threadnum = 1
    threads = []
    for relay in relays:
        topic = '{0}'.format(relay['topic'])
        qos = relay['qos'] if 'qos' in relay else QOS
        pin  = relay['gpio_pin'] if 'gpio_pin' in relay else 'NOTFOUND'
        port = relay['gpio_port'] if 'gpio_port' in relay else 'NOTFOUND'
        pin_string = '{0}p{1}'.format(GPIO_BUS, pin)
        if pin_string in dir(connector):
            relay = get_gpio_func('connector', pin_string)
        elif port.upper() in dir(port):
            relay = get_gpio_func('port', port)
        else:
            raise RuntimeError('Unable to find GPIO interface for "{0}"'.format(topic))
        logger.debug('Spawning thread to read topic {0} and issue commands to relay at GPIO{1}'.format(topic, relay))
        thread = threading.Thread(
            target=constructor, 
            args=(relay, topic, client_id, username, password, hostname, port, keepalive), 
            kwargs={ 'qos':qos },
            name='gdorelay-{0}'.format(threadnum)
        )
        thread.daemon = True
        thread.start()  
        threadnum += 1
        threads.append(thread)