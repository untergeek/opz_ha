import sys, time, logging, json

class LogstashFormatter(logging.Formatter):
    # The LogRecord attributes we want to carry over to the Logstash message,
    # mapped to the corresponding output key.
    WANTED_ATTRS = {'levelname': 'loglevel',
                    'funcName': 'function',
                    'lineno': 'linenum',
                    'message': 'message',
                    'name': 'name'}

    # def converter(self, timevalue):
    #     return time.gmtime(timevalue)

    def format(self, record):
        self.converter = time.gmtime
        timestamp = '%s.%03dZ' % (
            self.formatTime(record, datefmt='%Y-%m-%dT%H:%M:%S'), record.msecs)
        result = {'message': record.getMessage(),
                  '@timestamp': timestamp}
        for attribute in set(self.WANTED_ATTRS).intersection(record.__dict__):
            result[self.WANTED_ATTRS[attribute]] = getattr(record, attribute)
        return json.dumps(result, sort_keys=True)

class Whitelist(logging.Filter):
    def __init__(self, *whitelist):
        self.whitelist = [logging.Filter(name) for name in whitelist]

    def filter(self, record):
        return any(f.filter(record) for f in self.whitelist)

class Blacklist(Whitelist):
    def filter(self, record):
        return not Whitelist.filter(self, record)

class LogInfo(object):
    def __init__(self, loglevel='INFO', logfile=None, logformat='default'):
        self.numeric_log_level = getattr(logging, loglevel.upper(), None)
        self.format_string = '%(asctime)s %(levelname)-9s %(message)s'
        if not isinstance(self.numeric_log_level, int):
            raise ValueError('Invalid log level: {0}'.format(loglevel))

        self.handler = logging.StreamHandler(
            open(logfile, 'a') if logfile else sys.stdout
        )

        if self.numeric_log_level == 10: # DEBUG
            self.format_string = (
                '%(asctime)s %(levelname)-9s %(name)22s '
                '%(funcName)22s:%(lineno)-4d %(message)s'
            )

        if logformat == 'json' or logformat == 'logstash':
            self.handler.setFormatter(LogstashFormatter())
        else:
            self.handler.setFormatter(logging.Formatter(self.format_string))