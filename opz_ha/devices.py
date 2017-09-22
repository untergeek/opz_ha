import time, threading, logging
import paho.mqtt.client as mqtt
from pyA20.gpio import gpio
from . import utils

gpio.init()
INTERVAL = 120
REFRESH = 0.1

logger = logging.getLogger(__name__)


class GDORelay(object):
    def __init__(self, relay, topic, client_id, username, password, hostname, port, keepalive, qos=2):
        self.logger = logging.getLogger('opz_ha.devices.GDORelay')
        self.mqttc = mqtt.Client(client_id)
        self.mqttc.username_pw_set(username, password=password)
        self.mqttc.on_connect = self.on_connect
        self.mqttc.on_message = self.on_message
        self.hostname = hostname
        self.port = port
        self.keepalive = keepalive
        self.relay = relay
        self.topic = topic
        self.qos = qos
        # Start background realtime read/report daemon thread
        self.logger.info('Starting GDO relay monitoring thread')
        read_state = threading.Thread(target=self.get_state, args=())
        read_state.daemon = True                            # Daemonize thread
        read_state.start()

    def on_connect(self, client, obj, flags, rc):
        self.mqttc.subscribe(self.topic, self.qos)

    def on_message(self, client, userdata, message):
        try:
            self.logger.debug('message received: {0}'.format(message.payload))
            self.logger.debug('message topic: {0}'.format(message.topic))
            self.logger.debug('message qos: {0}'.format(message.qos))
            self.logger.debug('message retain flag: {0}'.format(message.retain))
        except Exception as e:
            self.logger.error('Exception: {0}'.format(e))

    def get_state(self):
        self.logger.info('Monitoring topic {0} for changes...'.format(self.topic))
        self.mqttc.connect(self.hostname, port=self.port, keepalive=self.keepalive)
        self.mqttc.loop_start()

    def buttonmash(self):
        gpio.output(self.relay, gpio.HIGH)
        time.sleep(0.5)
        gpio.output(self.relay, gpio.LOW)


class OneWire(object):
    def __init__(self, client, topics, interval=120):
        self.logger = logging.getLogger('opz_ha.devices.OneWire')
        # client is mqtt client
        self.mqttc = client
        # Start background realtime read/report daemon thread
        self.logger.info('Starting 1-wire monitoring thread, collecting values every {0} seconds'.format(interval))
        read_state = threading.Thread(target=self.get_state, args=(topics, interval))
        read_state.daemon = True                            # Daemonize thread
        read_state.start()

    def get_state(self, topics, interval):
        while True:
            starttime = time.time()
            for topic in topics:
                for device in topic['devices']:
                    rawtemp = utils.read_sensor(utils._1wire_path(device['family'], device['id'], device['filename'])) 
                    if rawtemp == None:
                        # In case we have a failure, or the device was removed, wait...
                        time.sleep(1.5)
                        continue
                    formatted_temp = utils.fahrtigrade(rawtemp, device['temp_scale'] if 'temp_scale' in device else 'C')
                    self.send_state(
                        '{0}/{1}'.format(topic['topic_trunk'], device['topic_leaf']), 
                        '{0:.2f}'.format(formatted_temp), 
                        device['qos'] if 'qos' in device else 0, 
                        device['retain'] if 'retain' in device else True
                    )
                    time.sleep(1.5)
            time.sleep(float(interval - (time.time() - starttime)))

    def send_state(self, topic, payload, qos, retain):
        self.logger.debug('Topic {0} will receive payload "{1}", with qos={2} and retain={3}'.format(topic, payload, qos, retain))
        tupleme = self.mqttc.publish(topic, payload, qos, retain)
        self.logger.debug('MQTT Response tuple: {0}'.format(tupleme))


class ReedSwitch(object):
    def __init__(self, client, switch, topic, qos=0, retain=True, interval=INTERVAL, refresh=REFRESH):
        self.logger = logging.getLogger('opz_ha.devices.ReedSwitch')
        # client is mqtt client
        self.mqttc = client
        # switch is port.XX## or connector.gpio#p#
        self.topic = topic
        self.interval = interval
        self.qos = qos
        self.retain = retain
        # Set directions
        gpio.setcfg(switch, gpio.INPUT)
        # Enable pullup resistor
        gpio.pullup(switch, gpio.PULLUP)
        self.curr = None
        self.prev = None
        # Start background realtime read/report daemon thread
        self.logger.info('Starting reed switch monitoring of GPIO{0} for topic "{1}"'.format(switch, topic))
        read_state = threading.Thread(target=self.get_state, args=(switch, refresh))
        read_state.daemon = True                            # Daemonize thread
        read_state.start()
        # Start background periodic publishing daemon thread
        self.logger.info('Start thread to publish current state of GPIO{0} to topic "{1}" every {2} seconds'.format(switch, topic, interval))
        at_interval = threading.Thread(target=self.publish, args=())
        at_interval.daemon = True                           # Daemonize thread
        at_interval.start()

    def get_state(self, switch, refresh):
        while True:
            self.curr = gpio.input(switch)      # Read switch state
            if self.prev is None:
                self.prev = self.curr
                self.send_state()
            elif self.prev != self.curr:
                # We're only sending values here if they've changed
                self.send_state()
                self.prev = self.curr
            time.sleep(refresh)

    def publish(self):
        time.sleep(1) # Wait one second from initialization before continuing
        while True:
            self.logger.debug('Publish: sleeping for {0} seconds'.format(self.interval))
            time.sleep(self.interval)
            self.logger.debug('Publish: sending state...')
            self.send_state()

    def send_state(self):
        state = 'open' if self.curr else 'closed'
        self.logger.debug('Reporting topic {0} as {1}'.format(self.topic, state))
        if self.curr != None:
            tupleme = self.mqttc.publish(self.topic, payload=self.curr, qos=self.qos, retain=self.retain)
            self.logger.debug('MQTT Response tuple: {0}'.format(tupleme))
