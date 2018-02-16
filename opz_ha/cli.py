#!/usr/bin/env python3

import os
import time
import logging
import click
import paho.mqtt.client as mqtt
from . import utils
from .launcher import gdorelay, onewire, reedswitch
from ._version import __version__

INTERVAL = 120
REFRESH = 0.1

if not os.getegid() == 0:
    sys.exit('opz_ha must be run as root')

def run(config):
    logger = logging.getLogger(__name__)
    logger.debug('Setting up MQTT publish client...')
    mqttc = mqtt.Client(client_id=config['mqtt']['client_id'])
    mqttc.username_pw_set(config['mqtt']['user'], password=config['mqtt']['password'])
    logger.debug('Connecting to MQTT publish client...')
    mqttc.connect(config['mqtt']['host'], port=config['mqtt']['port'], keepalive=config['mqtt']['keepalive'])
    logger.debug('Starting MQTT publish client loop...')
    mqttc.loop_start()
    if 'reed_switches' in config:
        i = config['reed_switches']['interval'] if 'interval' in config['reed_switches'] else INTERVAL
        r = config['reed_switches']['refresh'] if 'refresh' in config['reed_switches'] else REFRESH
        logger.info('Starting Reed Switch monitoring and publishing thread(s)...')
        reedswitch.launcher(mqttc, config['reed_switches'], interval=i, refresh=r)
    if 'onewire' in config:
        logger.info('Starting 1-wire protocol monitoring and publishing thread...')
        onewire.launcher(mqttc, config['onewire'])
    if 'gdo_relays' in config:
        logger.debug('Setting up GDORelay MQTT subscribe client...')
        # Use a separate MQTT client connection for the GDO
        mqttGDO = mqtt.Client(client_id='{0}-GDO'.format(config['mqtt']['client_id']))
        mqttGDO.username_pw_set(config['mqtt']['user'], password=config['mqtt']['password'])
        logger.debug('Establishing to GDORelay MQTT subscribe client object...')
        mqttGDO.connect(config['mqtt']['host'], port=config['mqtt']['port'], keepalive=config['mqtt']['keepalive'])
        logger.info('Starting GDORelay MQTT subscribe thread...')
        gdorelay.launcher(mqttGDO, config['gdo_relays'])
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
    config = utils.process_config(configuration_file)
    logger = logging.getLogger(__name__)
    logger.info('Starting OrangePi Zero GPIO/MQTT monitoring and publishing.')
    mqttc, mqttGDO = run(config)
    try:
        logger.info('OrangePi Zero GPIO/MQTT monitoring and publishing started.')
        while True:
            time.sleep(1) 
    except (KeyboardInterrupt, Exception):
        print('Goodbye.')
    # Stop both loops
    logger.info('Stopping publish client loop.')
    mqttc.loop_stop()
    logger.info('Stopping GDO subscribe client loop.')
    mqttGDO.loop_stop()
    logger.info('OrangePi Zero GPIO/MQTT monitoring and publishing halted.')

