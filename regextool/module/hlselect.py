# -*- coding: utf-8 -*-
#
# This file is a part of Regex Tool.
#
# Copyright (c) 2010 Vincent Batoufflet <vincent@batoufflet.info>
# See LICENSE file for further details.
#
# $Id$

import gtk, pygtk
import os, random, re
from regextool import __shortname__
from regextool.module import RegexToolModule
from regextool.path import DATA_DIR

pygtk.require('2.0')

# Set module class name
classname = 'RegexToolModuleHlSelect'

# Set module information
name = 'Highlight selection'
description = 'Highlight sub-pattern according to regular expression current selection.'
version = None
authors = [ 'Vincent Batoufflet <vincent@batoufflet.info>' ]
website = None

# Set configuration options list
options = {
	'color': {
		'match-select':	( str, '#ff9900' ),
	},
}

class RegexToolModuleHlSelect(RegexToolModule):
	def register(self):
		"""
		Register RegexToolModuleHlSelect module
			void register(void)
		"""

		# Initialize window if needed
		if not hasattr(self.parent, 'pref_dialog'):
			self.parent.init_pref_dialog()

		# Update preference pane
		tablecolor = self.parent.wtree.get_object('table-color')
		tablecolor.resize(tablecolor.get_property('n-rows') + 1, tablecolor.get_property('n-columns'))

		self.label = gtk.Label(_('Selection match:'))
		self.label.set_property('xalign', 0)
		self.label.show()

		self.colorbutton = gtk.ColorButton(gtk.gdk.color_parse(self.parent.config.get('color', 'match-select')))
		self.colorbutton.show()

		tablecolor.attach(self.label, 0, 1, 2, 3, gtk.FILL, gtk.FILL)
		tablecolor.attach(self.colorbutton, 1, 2, 2, 3, gtk.FILL, gtk.FILL)

		# Create selection tag
		self.parent.target_buffer.create_tag('match-select', background=gtk.gdk.color_parse(self.parent.config.get('color', 'match-select')))

		# Connect signals
		self.parent.regex_buffer.connect('mark-set', self.check_sub_pattern)
		self.parent.target_buffer.connect('changed', self.check_sub_pattern)
		self.parent.wtree.get_object('button-pref-ok').connect('clicked', self.set_color)
		self.parent.wtree.get_object('button-pref-reset').connect('clicked', self.reset_color)
	
	def check_sub_pattern(self, source=None, step=None, count=None, extend=None):
		"""
		Check for regular expression sub-pattern
			void check_sub_pattern(event source: gtk.Object, step: gtk.MovementStep, step count: int, selection extension flag: bool)
		"""

		# Remove previous selection
		self.parent.target_buffer.remove_tag_by_name('match-select', self.parent.target_buffer.get_start_iter(), self.parent.target_buffer.get_end_iter())

		# Get regular expression selection bounds
		bounds = self.parent.regex_buffer.get_selection_bounds()

		# Stop if no selection or match
		if len(bounds) == 0 or len(self.parent.match) == 0:
			return

		# Get regular expression and sub-target
		regex = self.parent.regex_buffer.get_text(
			self.parent.regex_buffer.get_start_iter(),
			self.parent.regex_buffer.get_end_iter(),
		)

		target = self.parent.target_buffer.get_text(
			self.parent.target_buffer.get_iter_at_offset(self.parent.match[0].start()),
			self.parent.target_buffer.get_iter_at_offset(self.parent.match[0].end()),
		)

		try:
			# Generate match id
			mid = self.generate_match_id()

			while target.find(mid) != -1:
				mid = self.generate_match_id()

			# Update regex for sub-pattern match
			mstart = bounds[0].get_offset()
			mend = bounds[1].get_offset()

			regex = regex[:mend] + ')' + regex[mend:]
			regex = regex[:mstart] + '(?P<%s>' % mid + regex[mstart:]

			# Check for sub-pattern
			s = re.match(regex, target)

			# Get sub-pattern
			select = self.parent.regex_buffer.get_text(bounds[0], bounds[1])

			if not s or select.startswith('(') and select.find(')') == -1 or select.endswith(')') and select.find('(') == -1:
				return

			# Update selection tag priority
			self.parent.target_buffer.get_tag_table().lookup('match-select').set_priority(self.parent.target_buffer.get_tag_table().get_size()-1)

			# Apply selection tag
			self.parent.target_buffer.apply_tag_by_name(
				'match-select',
				self.parent.target_buffer.get_iter_at_offset(self.parent.match[0].start() + s.start(mid)),
				self.parent.target_buffer.get_iter_at_offset(self.parent.match[0].start() + s.end(mid)),
			)
		except re.error:
			pass

	def generate_match_id(self, length=8):
		"""
		Generate an unique match id
			str generate_match_id(identifier length: int)
		"""

		mid = ''

		while len(mid) < length:
			mid += chr(random.randint(65, 90))

		return '%s_%s' % (__shortname__, mid)

	def reset_color(self, source=None):
		"""
		Reset selection highlight color
			void reset_color(event source: gtk.Object)
		"""

		# Set color to default
		self.colorbutton.set_color(gtk.gdk.color_parse(self.parent.config.get_default('color', 'match-select')))
	
	def set_color(self, source=None):
		"""
		Set selection highlight color
			void set_color(event source: gtk.Object)
		"""

		# Update color preference
		self.parent.config.set('color', 'match-select', self.colorbutton.get_color().to_string())

		# Update tag
		self.parent.target_buffer.get_tag_table().lookup('match-select').set_property(
			'background',
			gtk.gdk.color_parse(self.parent.config.get('color', 'match-select')),
		)
