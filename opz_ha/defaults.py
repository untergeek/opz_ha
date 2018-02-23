import socket

hostname       = socket.gethostname()
qos            = 2
retain         = True
mqtt_port      = 1883
mqtt_keepalive = 30
mqtt_client_id = '{0}_ha'.format(hostname)
rs_topic_base  = '{0}/reed_switches'.format(hostname)
gdo_topic_base = '{0}/gdo'.format(hostname)
w1_topic_base  = '{0}/1wire'.format(hostname)
pid_path       = '/var/run/opz_ha.pid'
loglevel       = 'INFO'
logformat      = 'default'
w1family       = '28'
w1filename     = 'w1_slave'
w1tempscale    = 'C'
w1interval     = 120
w1devicewait   = 1.5