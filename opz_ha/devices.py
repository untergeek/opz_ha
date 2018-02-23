import logging
import threading
import time
import OPi.GPIO as GPIO
import opz_ha.defaults as defaults
from opz_ha.utils import check_config, fahrtigrade, get_1wire_path, get_mode, read_sensor

logger = logging.getLogger(__name__)

class GDORelay(object):
    def __init__(self, client, modestring, channel, topic, qos, retain):
        self.logger = logging.getLogger('opz_ha.devices.GDORelay')
        self.logger.debug('Setting GPIO mode to: {0}'.format(modestring.upper()))
        GPIO.setmode(get_mode(modestring))
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
            # Our simple GDO will "STOP" if you hit the button again, even though it's not a 
            # true "STOP" command.  We should still catch and/or accept it.
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
    def __init__(self, client, devices, interval):
        self.logger = logging.getLogger('opz_ha.devices.OneWire')
        # client is mqtt client
        self.mqttc = client
        # Start background realtime read/report daemon thread
        self.logger.info('Starting 1-wire monitoring thread, collecting values every {0} seconds'.format(interval))
        read_state = threading.Thread(target=self.get_state, args=(devices, interval))
        read_state.daemon = True                            # Daemonize thread
        read_state.start()

    def get_state(self, devices, interval):
        while True:
            starttime = time.time()
            for device in devices:
                serial     = check_config(device, 'serial', msg='No "serial" provided for {0}'.format(device))
                topic      = check_config(device, 'topic', default='{0}/{1}'.format(defaults.w1_topic_base, serial))
                family     = check_config(device, 'family', default=defaults.w1family)
                filename   = check_config(device, 'filename', default=W1FILENAME)
                temp_scale = check_config(device, 'temp_scale', default=defaults.w1tempscale)
                rawtemp = read_sensor(get_1wire_path(family, serial, filename)) 
                if rawtemp == None:
                    # In case we have a failure, or the device was removed, wait...
                    time.sleep(defaults.w1devicewait)
                    # Then try the next device... 
                    continue
                self.send_state(
                    topic, 
                    '{0:.2f}'.format(fahrtigrade(rawtemp, temp_scale)), # payload
                    check_config(device, 'qos', default=defaults.qos),           # qos
                    check_config(device, 'retain', default=defaults.retain)      # retain
                )
                time.sleep(defaults.w1devicewait)
            sleeptime = float(interval - (time.time() - starttime))
            if sleeptime > 0:
                time.sleep(sleeptime)

    def send_state(self, topic, payload, qos, retain):
        # QoS and Retain are set per device
        self.logger.debug('Topic {0} will receive payload "{1}", with qos={2} and retain={3}'.format(topic, payload, qos, retain))
        tupleme = self.mqttc.publish(topic, payload, qos, retain)
        self.logger.debug('MQTT Response tuple: {0}'.format(tupleme))


class ReedSwitch(object):
    def __init__(self, client, modestring, channel, topic, qos, retain):
        self.logger = logging.getLogger('opz_ha.devices.ReedSwitch')
        self.logger.debug('Setting GPIO mode to: {0}'.format(modestring.upper()))
        GPIO.setmode(get_mode(modestring))
        self.logger.debug('Setting up GPIO channel "{0}" as an input'.format(channel))
        GPIO.setup(channel, GPIO.IN)
        self.mqttc = client
        self.topic = topic
        self.interval = interval
        self.qos = qos
        self.retain = retain
        self.channel = channel
        self.get_state()
        self.send_state()
        GPIO.add_event_detect(channel, GPIO.BOTH, callback=self._event_callback)

    def get_state(self):
        self.state = 'open' if GPIO.input(self.channel) else 'closed'

    def _event_callback(self, channel):
        self.get_state()
        self.logger.debug('{0} event detected on channel "{1}"'.format(self.state.upper(), channel))
        self.send_state()

    def send_state(self):
        self.logger.debug('Reporting topic {0} as {1}'.format(self.topic, self.state))
        tupleme = self.mqttc.publish(self.topic, payload=self.state, qos=self.qos, retain=self.retain)
        self.logger.debug('MQTT Response tuple: {0}'.format(tupleme))
