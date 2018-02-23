import socket

HOSTNAME = socket.gethostname()

def qos():
    return 2

def retain():
    return True

def interval():
    return 120

def mqtt_port():      
    return 1883

def mqtt_keepalive(): 
    return 30

def mqtt_client_id(): 
    return '{0}_ha'.format(HOSTNAME)

def rs_topic_base():  
    return '{0}/reed_switches'.format(HOSTNAME)

def gdo_topic_base(): 
    return '{0}/gdo'.format(HOSTNAME)

def w1_topic_base():  
    return '{0}/1wire'.format(HOSTNAME)

def pid_path():       
    return '/var/run/opz_ha.pid'

def loglevel():       
    return 'INFO'

def logformat():      
    return 'default'

def w1family():       
    return '28'

def w1filename():     
    return 'w1_slave'

def w1tempscale():    
    return 'C'

def w1interval():     
    return 120

def w1devicewait():   
    return 1.5
