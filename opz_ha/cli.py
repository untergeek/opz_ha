import os
import time
import logging
import click
import paho.mqtt.client as mqtt
import opz_ha.defaults as defaults
from opz_ha.launcher import gdorelay, onewire, reedswitch
from opz_ha._version import __version__
from opz_ha.utils    import TerminationCatcher, check_config, cleanup_channels, 
                            process_config, rm_pid, write_pid

if not os.getegid() == 0:
    sys.exit('opz_ha must be run as root')

def run(config):
    logger = logging.getLogger(__name__)

    logger.debug('Setting up MQTT publish client...')
    mode  = check_config(config, 'mode', msg='mode must be one of BOARD, SUNXI, BCM')
    host  = check_config(config['mqtt'], 'host', msg='No MQTT host provided.')
    port  = check_config(config['mqtt'], 'port', default=defaults.mqtt_port)
    ka    = check_config(config['mqtt'], 'keepalive', default=defaults.mqtt_keepalive)
    cid   = check_config(config['mqtt'], 'client_id', default=defaults.mqtt_client_id)
    mqttc = mqtt.Client(client_id=cid)
    if 'user' in config['mqtt'] and config['mqtt']['user'] is not None:
        anonymous = False
        logger.debug('Connecting to MQTT with username and provided password')
        try:
            mqttc.username_pw_set(config['mqtt']['user'], password=config['mqtt']['password'])
        except KeyError:
            raise KeyError('Password not provided for MQTT client')
    else:
        anonymous = True
        logger.info('No username provided.  Connect to MQTT anonymously.')
    logger.debug('Connecting to MQTT publish client...')
    mqttc.connect(host, port=port, keepalive=ka)
    logger.debug('Starting MQTT publish client loop...')
    mqttc.loop_start()
    if 'reed_switches' in config:
        logger.info('Starting Reed Switch monitoring and publishing thread(s)...')
        reedswitch.launcher(mqttc, mode, config)
    if 'onewire' in config:
        logger.info('Starting 1-wire protocol monitoring and publishing thread...')
        onewire.launcher(mqttc, config)
    if 'gdo_relays' in config:
        logger.debug('Setting up GDORelay MQTT subscribe client...')
        # Use a separate MQTT client connection for the GDO
        mqttGDO = mqtt.Client(client_id='{0}-GDO'.format(cid))
        if not anonymous:
            mqttGDO.username_pw_set(config['mqtt']['user'], password=config['mqtt']['password'])
        logger.debug('Establishing to GDORelay MQTT subscribe client object...')
        mqttGDO.connect(host, port=port, keepalive=ka)
        logger.info('Starting GDORelay MQTT subscribe thread...')
        gdorelay.launcher(mqttGDO, mode, config)
    return mqttc, mqttGDO


@click.command()
@click.argument('configuration_file', type=click.Path(exists=True))
@click.version_option(version=__version__)
def cli(configuration_file):
    """
    Orange Pi Zero for Home Assistant.

    Use 1-Wire and GPIO pins to monitor sensors and send data to
    Home Assistant via MQTT. 

    This version is Orange Pi Zero specific
    """
    termcatcher = TerminationCatcher()
    config = process_config(configuration_file)
    logger = logging.getLogger(__name__)
    logger.info('Starting OrangePi Zero GPIO/MQTT monitoring and publishing.')
    # This is a special case where I also have to check for a 'None'
    # otherwise I'd be using `config_check`
    pid_path = config['pid_path'] if 'pid_path' in config and config['pid_path'] is not None else defaults.pid_path()
    pid = os.getpid()
    logger.debug('Writing pid {0} to {1}'.format(pid, pid_path))
    write_pid(pid_path, '{0}\n'.format(pid))
    mqttc, mqttGDO = run(config)
    try:
        logger.info('OrangePi Zero GPIO/MQTT monitoring and publishing started.')
        while True:
            if termcatcher.kill_received:
                logger.info('Process terminated by signal...')
                break
            time.sleep(1) 
    except KeyboardInterrupt:
        print('Terminating on keyboard interrupt. Goodbye.')
        logger.info('Terminating on keyboard interrupt. Exiting...')
    # Stop both loops
    logger.info('Stopping publish client loop.')
    mqttc.loop_stop()
    logger.info('Stopping GDO subscribe client loop.')
    mqttGDO.loop_stop()
    logger.info('OrangePi Zero GPIO/MQTT monitoring and publishing halted.')
    # Cleanup GPIO Channels
    logger.info('Cleanup OrangePi Zero GPIO Channels.')
    cleanup_channels(config)
    logger.info('OrangePi Zero GPIO Channels cleaned up.')
    # Cleanup PID file
    logger.debug('Removing pid file {0}'.format(pid_path))
    rm_pid(pid_path)

