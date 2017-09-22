import time, threading, logging
from pyA20.gpio import gpio
from . import utils

gpio.init()
INTERVAL = 120
REFRESH = 0.1


class OneWire(object):
    def __init__(self, client, topics, interval=120):
        self.logger = logging.getLogger('opz_ha.devices.OneWire')
        # client is mqtt client
        self.mqttc = client
        # Start background realtime read/report daemon thread
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
        self.logger.debug('{0} will receive "{1}", with qos={2} and retain={3}'.format(topic, payload, qos, retain))
        tupleme = self.mqttc.publish(topic, payload, qos, retain)
        logger.debug('MQTT Response: {0}'.format(tupleme))


class ReedSwitch(object):
    def __init__(self, client, switch, topic, qos=0, retain=True, interval=INTERVAL, refresh=REFRESH):
        self.logger = logging.getLogger('opz_ha.devices.ReedSwitch')
        # client is mqtt client
        self.mqttc = client
        # switch is port.XX## or connector.gpio#p#
        self.switch = switch
        self.topic = topic
        self.qos = qos
        self.retain = retain
        self.interval = interval
        self.refresh = refresh
        # Set directions
        gpio.setcfg(switch, gpio.INPUT)
        # Enable pullup resistor
        gpio.pullup(switch, gpio.PULLUP)
        self.curr = None
        self.prev = None
        # Start background realtime read/report daemon thread
        read_state = threading.Thread(target=self.get_state, args=())
        read_state.daemon = True                            # Daemonize thread
        read_state.start()
        # Start background periodic publishing daemon thread
        at_interval = threading.Thread(target=self.publish, args=())
        at_interval.daemon = True                           # Daemonize thread
        at_interval.start()

    def get_state(self):
        while True:
            self.curr = gpio.input(self.switch)      # Read switch state
            if self.prev is None:
                self.prev = self.curr
                self.send_state()
            elif self.prev != self.curr:
                # We're only sending values here if they've changed
                self.send_state()
                self.prev = self.curr
            time.sleep(self.refresh)

    def publish(self):
        time.sleep(1) # Wait one second from initialization before continuing
        while True:
            self.logger.debug('Publish: sleeping for {0} seconds'.format(self.interval))
            time.sleep(self.interval)
            self.logger.debug('Publish: sending state...')
            self.send_state()

    def send_state(self):
        state = 'open' if self.curr else 'closed'
        self.logger.debug('{0} is {1}'.format(self.topic, state))
        if self.curr != None:
            tupleme = self.mqttc.publish(self.topic, payload=self.curr, qos=self.qos, retain=self.retain)
            self.logger.debug('MQTT Response: {0}'.format(tupleme))
