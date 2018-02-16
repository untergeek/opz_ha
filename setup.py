import os
import re
import sys
from setuptools import setup

# Utility function to read from file.
def fread(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

def get_version():
    VERSIONFILE="opz_ha/_version.py"
    verstrline = fread(VERSIONFILE).strip()
    vsre = r"^__version__ = ['\"]([^'\"]*)['\"]"
    mo = re.search(vsre, verstrline, re.M)
    if mo:
        VERSION = mo.group(1)
    else:
        raise RuntimeError("Unable to find version string in %s." % (VERSIONFILE,))
    build_number = os.environ.get('OPZ_HA_BUILD_NUMBER', None)
    if build_number:
        return VERSION + "b{}".format(build_number)
    return VERSION

def get_install_requires():
    return [
        'pyA20',
        'paho-mqtt',
        'click>=6.7',
        'pyyaml>=3.10',
    ]

def base_setup():
    return {
        "name":"opz_ha",
        "version": get_version(),
        "author": "Aaron Mildenstein",
        "description": "Tiny remote MQTT relay of GPIO data from Orange Pi Zero single-board computers",
        "long_description": fread('README.rst'),
        "url": "http://github.com/untergeek/opz_ha",
        "download_url": "https://github.com/untergeek/opz_ha/tarball/v" + get_version(),
        "license": "Apache License, Version 2.0",
        "install_requires": get_install_requires(),
        "keywords": "orangepi mqtt home automation",
        "packages": ["opz_ha"],
        "include_package_data": True,
        "entry_points": {
            "console_scripts": [
                "opz_ha_relay = opz_ha.cli:cli",
            ],
        },
        "classifiers": [
            "Topic :: Home Automation",
            "Intended Audience :: Developers",
            "License :: OSI Approved :: Apache Software License",
            "Programming Language :: Python :: 3.5",
            "Programming Language :: Python :: 3.6",
        ],
#        "test_suite": "test.run_tests.run_all",
#        "tests_require": ["mock", "nose", "coverage", "nosexcover"],
    }

base = 'Console'
### cx_freeze bits ###
icon = None
base = base_setup()
try:
    ### cx_Freeze ###
    from cx_Freeze import setup, Executable
    opz_ha_exe = Executable(
        "opz_ha.py",
        base=base,
        targetName = "opz_ha_relay",
    )
    buildOptions = dict(
        packages = [],
        excludes = [],
        include_files = [],
    )
    add_ons = {
        "options": {"build_exe" : buildOptions},
        "executables": [opz_ha_exe],
    }
    setup(**{**base, **add_ons})
except ImportError:
    setup(**base)

