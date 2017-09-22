import time, threading, logging
# import paho.mqtt.client as mqtt
from pyA20.gpio import gpio, connector, port
from ..devices import OneWire, ReedSwitch

logger = logging.getLogger(__name__)

GPIO_BUS = 'gpio1'
gpio.init()

def constructor(*a, **k):
    rs = ReedSwitch(*a, **k)

def get_gpio_func(kind, val):
    return getattr(sys.modules['pyA20.gpio.{0}'.format(kind)],val)

def launcher(mqttc, switches, interval=120, refresh=0.1):
    """
    switches is an array of reed switch configuration data, 
    as extracted from this YAML:
      - topic: opz2/reed_switches/freezer_door
        gpio_port: PA12
        gpio_pin: 3
        qos: 0
        retain: true
        interval: 120
        refresh: 0.1
      - topic: opz2/reed_switches/garage_door
        gpio_port: PA11
        gpio_pin: 5
        qos: 0
        retain: true
        interval: 120
        refresh: 0.1
    """
    threadnum = 1
    threads = []
    for switch in switches:
        topic = '{0}'.format(switch['topic'])
        qos = switch['qos'] if 'qos' in switch else 0
        retain = switch['retain'] if 'retain' in switch else True
        pubinterval = switch['interval'] if 'interval' in switch else interval
        refresh = switch['refresh'] if 'refresh' in switch else refresh
        pin  = switch['gpio_pin'] if 'gpio_pin' in switch else 'NOTFOUND'
        port = switch['gpio_port'] if 'gpio_port' in switch else 'NOTFOUND'
        pin_string = '{0}p{1}'.format(GPIO_BUS, pin)
        if pin_string in dir(connector):
            switch = get_gpio_func('connector', pin_string)
        elif port.upper() in dir(port):
            switch = get_gpio_func('port', port)
        else:
            raise RuntimeError('Unable to find GPIO interface for "{0}"'.format(topic))
        thread = threading.Thread(
            target=constructor, 
            args=(mqttc, switch, topic), 
            kwargs={ 'qos':qos, 'retain':retain, 'interval':pubinterval, 'refresh':refresh },
            name='reedswitch-{0}'.format(threadnum)
        )
        thread.daemon = True
        thread.start()  
        threadnum += 1
        threads.append(thread)