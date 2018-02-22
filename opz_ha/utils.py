import yaml, os, re, sys, time, logging, signal
from .logtools import LogInfo, Whitelist, Blacklist
import OPi.GPIO as GPIO

logger = logging.getLogger(__name__)

class TerminationCatcher:
  kill_received = False
  def __init__(self):
    signal.signal(signal.SIGINT, self.exit_gracefully)
    signal.signal(signal.SIGTERM, self.exit_gracefully)

  def exit_gracefully(self, signum, frame):
    self.kill_received = True

def read_file(myfile):
    """
    Read a file and return the resulting data.

    :arg myfile: A file to read.
    :rtype: str
    """
    try:
        with open(myfile, 'r') as f:
            data = f.read()
        return data
    except IOError as e:
        raise Exception('Unable to read file {0}'.format(myfile))

def write_pid(mypath, pid):
    """
    Write pid to a file

    :arg mypath: The file to write the pid to.
    :arg pid: The pid to write 
    """
    basedir = os.path.dirname(mypath)
    if not os.path.exists(basedir):
        try:
            os.makedirs(basedir)
        except Exception:
            logger.critical('Unable to create path: {0}'.format(basedir))
    try:
        with open(mypath, 'w') as f:
            f.write('{0}'.format(pid))
    except IOError as e:
        raise Exception('Unable to write pid {0} to file {1}'.format(pid, mypath))

def rm_pid(mypath):
    """
    Delete pid file on clean exit

    :arg mypath: The pid file.
    """
    try:
        os.remove(mypath)
    except IOError:
        logger.error('Unable to delete pidfile "{0}"'.format(mypath))


def get_yaml(path):
    """
    Read the file identified by `path` and import its YAML contents.

    :arg path: The path to a YAML configuration file.
    :rtype: dict
    """
    # Set the stage here to parse single scalar value environment vars from
    # the YAML file being read
    single = re.compile( r'^\$\{(.*)\}$' )
    yaml.add_implicit_resolver ( "!single", single )
    def single_constructor(loader,node):
        value = loader.construct_scalar(node)
        proto = single.match(value).group(1)
        default = None
        if len(proto.split(':')) > 1:
            envvar, default = proto.split(':')
        else:
            envvar = proto
        return os.environ[envvar] if envvar in os.environ else default
    yaml.add_constructor('!single', single_constructor)

    raw = read_file(path)
    try:
        cfg = yaml.load(raw)
    except yaml.scanner.ScannerError as e:
        raise Exception(
            'Unable to parse YAML file. Error: {0}'.format(e))
    return cfg

def now():
    logger.debug('Function called.')
    return '{0}'.format(int(time.time()))

def read_sensor(path):
    logger.debug('Testing path "{0}"'.format(path))
    value = None
    try:
        f = open(path, "r")
        line = f.readline()
        if re.match(r"([0-9a-f]{2} ){9}: crc=[0-9a-f]{2} YES", line):
          line = f.readline()
          m = re.match(r"([0-9a-f]{2} ){9}t=([+-]?[0-9]+)", line)
          if m:
            value = float(m.group(2)) / 1000.0
        f.close()
    except IOError as e:
        logger.error('Unable to read: {0}.  Error: {1}'.format(path, e))
    # Since we are ostensibly reading regular human dwelling temperatures, 
    # and errors often read -69, this should help reduce the likelihood
    # of encountering those.
    logger.debug('value at path {0} = {1} ºC'.format(path, value))
    if value:
        if value > 55.0 or value < -55.0:
            return None
    return value

def _1wire_path(family, _id, filename):
    logger.debug('family = "{0}", _id = "{1}", filename = "{2}"'.format(family, _id, filename))
    return '/sys/bus/w1/devices/{0}-{1}/{2}'.format(family, _id, filename)

def fahrtigrade(value, scale='C'):
    logger.debug('Scale = {0}, value = {1}'.format(scale, value))
    if scale == 'C':
        return value
    else:
        return float(value * 9.0 / 5.0 + 32.0)

def set_logging(log_dict):
    # Set up logging
    loginfo = LogInfo(log_dict)
    logging.root.addHandler(loginfo.handler)
    logging.root.setLevel(loginfo.numeric_log_level)
    logger = logging.getLogger('opz_ha')
    # if log_dict['blacklist']:
    #     for bl_entry in ensure_list(log_dict['blacklist']):
    #         for handler in logging.root.handlers:
    #             handler.addFilter(Blacklist(bl_entry))

def process_config(yaml_file):
    config = get_yaml(yaml_file)
    set_logging(config['logging'])
    return config

def get_mode(modestring):
    try:
        return getattr(GPIO, modestring.upper())()
    except:
        raise ValueError('{0} is not an acceptable value for "mode"'.format(modestring))

def cleanup_channels(modestring, config):
    # Because we assign channels separately, we need to find them all to clean them en masse
    channels = []
    if 'reed_switches' in config:
        for switch in config['reed_switches']:
            channels.append(switch['channel'])
    if 'gdo_relays' in config:
        for gdo_relay in config['gdo_relays']:
            channels.append(gdo_relay['channel'])
    GPIO.cleanup(channels)
