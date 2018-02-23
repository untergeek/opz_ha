import socket

HOSTNAME = socket.gethostname()

QOS = 2
RETAIN = True
MQTT_PORT = 1883
MQTT_KEEPALIVE = 30
MQTT_CLIENT_ID = '{0}_ha'.format(HOSTNAME)
RS_TOPIC_BASE = '{0}/reed_switches'.format(HOSTNAME)
GDO_TOPIC_BASE = '{0}/gdo'.format(HOSTNAME)
W1_TOPIC_BASE = '{0}/1wire'.format(HOSTNAME)
PID_PATH = '/var/run/opz_ha.pid'
LOGLEVEL = 'INFO'
LOGFORMAT = 'default'
W1FAMILY = '28'
W1FILENAME = 'w1_slave'
W1TEMPSCALE = 'C'
W1INTERVAL = 120
W1DEVICEWAIT = 1.5