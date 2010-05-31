# -*- coding: utf-8 -*-
#
# This file is a part of Regex Tool.
#
# Copyright (c) 2010 Vincent Batoufflet <vincent@batoufflet.info>
# See LICENSE file for further details.
#
# $Id$

import os, sys
from ConfigParser import RawConfigParser
from regextool import __shortname__
from regextool.path import CONF_DIR

# Set configuration options list
__OPTIONS__ = {
	'window': {
		'height':		( int, 1 ),
		'notebook-page':	( int, 0 ),
		'option-g-active':	( bool, False ),
		'option-i-active':	( bool, False ),
		'option-l-active':	( bool, False ),
		'option-m-active':	( bool, False ),
		'option-s-active':	( bool, False ),
		'option-u-active':	( bool, False ),
		'option-x-active':	( bool, False ),
		'pane-position1':	( int, -1 ),
		'pane-position2':	( int, -1 ),
		'save-state':		( bool, True ),
		'show-extension':	( bool, False ),
		'show-statusbar':	( bool, True ),
		'width':		( int, 1 ),
	},
	'color': {
		'match-first':		( str, '#ffff00' ),
		'match-next':		( str, '#66ff66' ),
	},
	'data': {
		'textview-regex':	( str, ''),
		'textview-target':	( str, ''),
	},
}

class RegexToolConfig:
	def __init__(self, options=dict()):
		"""
		Initialize RegexToolConfig instance
			RegexToolConfig __init__(additionnal options: dict)
		"""

		# Set instance attributes
		self.settings = dict()
		self.filepath = os.path.join(CONF_DIR, __shortname__ + 'rc')

		# Load options from file
		parser = RawConfigParser()
		parser.read(self.filepath)

		# Get full options list
		self.options = __OPTIONS__.copy()
		
		for opts in options:
			for section in opts:
				for option in opts[section]:
					if not section in self.options:
						self.options[section] = dict()

					self.options[section][option] = opts[section][option]

		for section in self.options:
			for option in self.options[section]:
				stype, default = self.options[section][option]

				# Initialize option section if needed
				if not section in self.settings:
					self.settings[section] = dict()

				if not parser.has_option(section, option):
					self.settings[section][option] = default
				elif stype == bool:
					self.settings[section][option] = parser.getboolean(section, option)
				elif stype == float:
					self.settings[section][option] = parser.getfloat(section, option)
				elif stype == int:
					self.settings[section][option] = parser.getint(section, option)
				else:
					self.settings[section][option] = parser.get(section, option)

		del parser

	def get(self, section, option):
		"""
		Get an option value by section and name
			mixed get(section name: str, option name: str)
		"""

		# Return option value
		if section in self.settings and option in self.settings[section]:
			return self.settings[section][option]
		else:
			return None

	def get_default(self, section, option):
		"""
		Get a default option value by section and name
			mixed get_default(section name: str, option name: str)
		"""

		# Return option value
		if section in self.options and option in self.options[section]:
			return self.options[section][option][1]
		else:
			return None

	def save(self):
		"""
		Save options to file
			bool save(void)
		"""

		try:
			# Parse for options
			parser = RawConfigParser()

			for section in self.settings:
				# Create new section
				parser.add_section(section)

				# Append options values
				for option in self.settings[section]:
					parser.set(section, option, self.settings[section][option])


			# Save options to file
			if not os.path.exists(os.path.dirname(self.filepath)):
				os.makedirs(os.path.dirname(self.filepath))

			fd = open(self.filepath, 'w')
			parser.write(fd)
			fd.close()

			return True
		except Exception, e:
			sys.stderr.write(_('Error: %s\n') % e)
			return False

	def set(self, section, option, value):
		"""
		Set an option value by section and name
			void set(section name: str, option name: str, option value: mixed)
		"""

		# Initialize option section if needed
		if not section in self.settings:
			self.settings[section] = dict()

		# Set option value
		self.settings[section][option] = value
