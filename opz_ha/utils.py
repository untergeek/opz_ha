import yaml, os, re, sys, time, logging
from .logtools import LogInfo, Whitelist, Blacklist

logger = logging.getLogger(__name__)

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
        raise Exception(
            'Unable to read file {0}'.format(myfile)
        )

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
    return '{0}'.format(int(time.time()))

def read_sensor(path):
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
  if value > 55.0 or value < -55.0:
      return None
  return value

def _1wire_path(family, _id, filename):
    return '/sys/bus/w1/devices/{0}-{1}/{2}'.format(family, _id, filename)

def fahrtigrade(value, scale='C'):
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
    if log_dict['blacklist']:
        for bl_entry in ensure_list(log_dict['blacklist']):
            for handler in logging.root.handlers:
                handler.addFilter(Blacklist(bl_entry))

def process_config(yaml_file):
    config = get_yaml(yaml_file)
    set_logging(config['logging'])
    return config