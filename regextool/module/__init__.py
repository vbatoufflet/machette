# -*- coding: utf-8 -*-
#
# This file is a part of Regex Tool.
#
# Copyright (c) 2010 Vincent Batoufflet <vincent@batoufflet.info>
# See LICENSE file for further details.
#
# $Id$

import os
from regextool import __author__, __email__, __website__

__MODULES__ = list()

class RegexToolModule:
	def __init__(self, parent):
		"""
		Initialize RegexToolModule instance
			RegexToolModule __init__(parent instance: RegexTool)
		"""

		# Set instance attributes
		self.parent = parent

	def register(self):
		"""
		Register RegexToolModule module
			void register(void)
		"""

		pass

	def unregister(self):
		"""
		Unregister RegexToolModule module
			void unregister(void)
		"""

		pass

def get_modules_list():
	"""
	Get the list of available modules
		list get_modules_list(void)
	"""

	# Probe for available modules
	if len(__MODULES__) == 0:
		for name in os.listdir(os.path.dirname(__file__)):
			# Skip unwanted files
			if not name.endswith('.py') or name.startswith('.') or name.startswith('_'):
				continue

			# Append found module
			__MODULES__.append(os.path.splitext(name)[0])
	
	return __MODULES__

def load_module(name, fromlist=[]):
	"""
	Load a module by name
		object load_module(module name: str, from list: list)
	"""

	try:
		# Try to import the module
		return __import__('regextool.module.%s' % name, globals(), locals(), fromlist)
	except ImportError:
		# Return None on failure
		return None
