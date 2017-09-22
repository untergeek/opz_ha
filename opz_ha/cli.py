#!/usr/bin/env python3

import logging
import click
import daemon
import paho.mqtt.client as mqtt
from . import utils
from .launcher import onewire, reedswitch
from ._version import __version__

INTERVAL = 120
REFRESH = 0.1

if not os.getegid() == 0:
    sys.exit('opz_ha must be run as root')

def foreground(func):
    def wrapper():
        print('Press CTRL+C to exit')
        func()
        try:
            while True:
                time.sleep(1) 
        except KeyboardInterrupt:
            print ('Goodbye.')
    return wrapper

def run(config):
    mqttc = mqtt.Client(client_id=config['mqtt']['client_id'])
    mqttc.username_pw_set(config['mqtt']['user'], password=config['mqtt']['password'])
    mqttc.connect(config['mqtt']['host'], port=config['mqtt']['port'], keepalive=config['mqtt']['keepalive'])
    mqttc.loop_start()
    if 'reed_switches' in config:
        i = config['reed_switches']['interval'] if 'interval' in config['reed_switches'] else INTERVAL
        r = config['reed_switches']['refresh'] if 'refresh' in config['reed_switches'] else REFRESH
        reedswitch.launcher(mqttc, config['reed_switches'], interval=i, refresh=r)
    if 'onewire' in config:
        onewire.launcher(mqttc, config['onewire'])
    return mqttc


@click.command()
@click.argument('configuration_file',
    help="Path to YAML configuration file.",
    type=click.Path(exists=True)
)
@click.option('--daemonize', is_flag=True)
@click.version_option(version=__version__)
def cli(configuration_file, daemonize):
    """
    Orange Pi Zero for Home Assistant.

    Use 1-Wire and GPIO pins to monitor sensors and send data to
    Home Assistant via MQTT. 

    This version is Orange Pi Zero specific
    """
    config = utils.process_config(configuration_file)
    logger = logging.getLogger(__name__)
    if daemonize:
        logger.info('Daemonizing process...')
        with daemon.DaemonContext():
            mqttc = run(config)
    else:
        logger.info('Running in foreground...')
        mqttc = foreground(run(config))
    mqttc.loop_stop()

