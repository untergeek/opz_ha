#!/usr/bin/env python

"""Wrapper for running opz_ha from source."""

from opz_ha.cli import cli

if __name__ == '__main__':
    try:
        # pylint: disable=E1120
        cli()
    except Exception as e:
        if type(e) == type(RuntimeError()):
            if 'ASCII' in str(e):
                print('{0}'.format(e))
                print(
'''

This program requires the locale to be unicode. Any of
the above unicode definitions are acceptable.

To set the locale to be unicode, try:

$ export LC_ALL=en_US.utf8
$ opz_ha [ARGS]

Alternately, you should be able to specify the locale on the command-line:

$ LC_ALL=en_US.utf8 opz_ha [ARGS]

Be sure to substitute your unicode variant for en_US.utf8

'''
            )
        else:
            import sys
            print('{0}'.format(e))
            sys.exit(1)