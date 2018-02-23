import time, threading, logging
import OPi.GPIO as GPIO
from . import utils

INTERVAL = 120
REFRESH = 0.1

logger = logging.getLogger(__name__)


class GDORelay(object):
    def __init__(self, client, modestring, channel, topic, qos=2):
        self.logger = logging.getLogger('opz_ha.devices.GDORelay')
        self.logger.debug('Setting GPIO mode to: {0}'.format(modestring.upper()))
        GPIO.setmode(utils.get_mode(modestring))
        self.logger.debug('Setting up GPIO channel "{0}" as an output'.format(channel))
        GPIO.setup(channel, GPIO.OUT)
        # client is mqtt client
        self.mqttc = client
        self.channel = channel
        self.topic = topic
        self.qos = qos
        self.mqttc.on_message = self.on_message
        self.mqttc.on_connect = self.on_connect
        self.mqttc.on_disconnect = self.on_disconnect
        self.logger.debug('Starting the MQTT loop for the GDORelay...')
        # loop_start automatically does its own threading.  We just need a different
        # mqtt client here as we're subscribing to a topic, rather than 
        # publishing.  Maybe I could code around this, but this is easier to track.
        self.mqttc.loop_start()
        self.logger.debug('MQTT loop for the GDORelay has started...')

    def on_connect(self, client, userdata, flags, rc):
        self.logger.info('Connected to MQTT with result code: {0}'.format(rc))
        self.logger.debug('on_connect userdata: {0}'.format(userdata))
        self.logger.debug('on_connect flags: {0}'.format(flags))
        self.mqttc.subscribe(self.topic, self.qos)
        self.logger.debug('Subscribed to MQTT topic: {0} at QoS {1}'.format(self.topic, self.qos))

    def on_message(self, client, obj, m):
        self.logger.debug('topic: {0}, payload: {1}, qos: {2}, retain: {3}'.format(m.topic, m.payload, m.qos, m.retain))
        if m.topic == self.topic:
            if m.payload == b'OPEN' or m.payload == b'CLOSE' or m.payload == b'STOP':
                self.toggleRelay()

    def on_disconnect(self, client, userdata, rc):
        if rc != 0:
            self.logger.warn('Unexpected MQTT disconnection. Will attempt to auto-reconnect')

    def toggleRelay(self):
        GPIO.output(self.channel, GPIO.HIGH)
        time.sleep(0.5)
        GPIO.output(self.channel, GPIO.LOW)


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
            sleeptime = float(interval - (time.time() - starttime))
            if sleeptime > 0:
                time.sleep(float(interval - (time.time() - starttime)))

    def send_state(self, topic, payload, qos, retain):
        self.logger.debug('Topic {0} will receive payload "{1}", with qos={2} and retain={3}'.format(topic, payload, qos, retain))
        tupleme = self.mqttc.publish(topic, payload, qos, retain)
        self.logger.debug('MQTT Response tuple: {0}'.format(tupleme))


class ReedSwitch(object):
    def __init__(self, client, modestring, channel, topic, qos=0, retain=True, interval=INTERVAL, refresh=REFRESH):
        self.logger = logging.getLogger('opz_ha.devices.ReedSwitch')
        self.logger.debug('Setting GPIO mode to: {0}'.format(modestring.upper()))
        GPIO.setmode(utils.get_mode(modestring))
        self.logger.debug('Setting up GPIO channel "{0}" as an input'.format(channel))
        GPIO.setup(channel, GPIO.IN)
        # client is mqtt client
        self.mqttc = client
        self.topic = topic
        self.interval = interval
        self.qos = qos
        self.retain = retain
        self.channel = channel
        self.get_state()
        self.send_state()
        GPIO.add_event_detect(channel, GPIO.BOTH, callback=self._event_callback)
        # self.prev = self.curr
        # # Start background realtime read/report daemon thread
        # self.logger.info('Starting reed switch monitoring of channel {0} for topic "{1}"'.format(channel, topic))
        # read_state = threading.Thread(target=self.get_state, args=(channel, refresh))
        # read_state.daemon = True                            # Daemonize thread
        # read_state.start()
        # Start background periodic publishing daemon thread
        # self.logger.info('Start thread to publish current state of channel {0} to topic "{1}" every {2} seconds'.format(channel, topic, interval))
        # at_interval = threading.Thread(target=self.publish, args=())
        # at_interval.daemon = True                           # Daemonize thread
        # at_interval.start()

    def get_state(self):
        self.state = 'open' if GPIO.input(self.channel) else 'closed'

    def _event_callback(self, channel):
        self.get_state()
        self.logger.debug('{0} event detected on channel "{1}"'.format(self.state.upper(), channel))
        self.send_state()

    # def get_state(self, channel, refresh):
    #     while True:
    #         self.curr = GPIO.input(channel)      # Read channel state
    #         if self.prev is None:
    #             self.prev = self.curr
    #             self.send_state()
    #         elif self.prev != self.curr:
    #             # We're only sending values here if they've changed
    #             self.send_state()
    #             self.prev = self.curr
    #         time.sleep(refresh)

    # def publish(self):
    #     time.sleep(1) # Wait one second from initialization before continuing
    #     while True:
    #         self.logger.debug('Publish: sleeping for {0} seconds'.format(self.interval))
    #         time.sleep(self.interval)
    #         self.logger.debug('Publish: sending state...')
    #         self.send_state()

    def send_state(self):
        # state = 'open' if self.curr else 'closed'
        self.logger.debug('Reporting topic {0} as {1}'.format(self.topic, self.state))
        # if self.curr != None:
        tupleme = self.mqttc.publish(self.topic, payload=self.state, qos=self.qos, retain=self.retain)
        self.logger.debug('MQTT Response tuple: {0}'.format(tupleme))
