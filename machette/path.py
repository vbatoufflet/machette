# -*- coding: utf-8 -*-
#
# This file is a part of Machette.
#
# Copyright (c) 2010 Vincent Batoufflet <vincent@batoufflet.info>
# See LICENSE file for further details.
#
# $Id$

import os, sys
from machette import __cmdname__

def get_source_directory(name=None):
	"""
	Get a directory path when running from source
		str get_source_directory(directory name: str)
	"""

	# Get source base directory
	basedir = os.path.dirname(os.path.abspath(__file__))
	basedir = os.path.abspath(os.path.join(basedir, os.pardir))

	# Return directory path
	return os.path.join(basedir, name) if name else basedir

def get_config_directory():
	"""
	Get the user-specific configuration directory path
		str get_config_directory(void)
	"""

	# Get base configuration directory
	if sys.platform == 'win32':
		basedir = os.environ.get('APPDATA', os.path.expanduser('~'))
	else:
		basedir = os.environ.get('XDG_CONFIG_HOME', os.path.join(os.path.expanduser('~'), '.config'))

	# Return configuration directory path
	return os.path.abspath(os.path.join(basedir, __cmdname__))

# Define paths
CONF_DIR = get_config_directory()
DATA_DIR = get_source_directory()
LOCALE_DIR = get_source_directory('locale')
