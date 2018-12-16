# coding=utf-8
__version__ = '3.0.93'

import logging

logging.basicConfig()

cslogger = logging.getLogger('dtcs')
cslogger.setLevel(logging.DEBUG)

from .main_entry_point import main
