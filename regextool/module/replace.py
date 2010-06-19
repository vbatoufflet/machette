# -*- coding: utf-8 -*-
#
# This file is a part of Regex Tool.
#
# Copyright (c) 2010 Vincent Batoufflet <vincent@batoufflet.info>
# See LICENSE file for further details.
#
# $Id$

import gtk, pygtk
import os, re
from regextool.module import RegexToolModule
from regextool.path import DATA_DIR

pygtk.require('2.0')

# Set module class name
classname = 'RegexToolModuleReplace'

# Set configuration options list
options = {
	'window': {
		'pane-position-replace':	( int, 0 ),
	},
	'data': {
		'textview-replace':		( str, '' ),
	},
}

class RegexToolModuleReplace(RegexToolModule):
	builtin = True

	def register(self):
		"""
		Register RegexToolModuleReplace module
			void register(void)
		"""

		# Load module UI file
		self.parent.wtree.add_from_file(os.path.join(DATA_DIR, 'ui/module/replace.ui'))

		# Initialize GtkTextBuffer
		self.replace_buffer = self.parent.wtree.get_object('textview-replace').get_buffer()

		# Restore last state
		self.parent.wtree.get_object('vpaned-replace').set_position(self.parent.config.get('window', 'pane-position-replace'))
		self.replace_buffer.set_text(self.parent.config.get('data', 'textview-replace'))

		# Attach UI to the parent window
		self.parent.wtree.get_object('notebook-extension').append_page(self.parent.wtree.get_object('vpaned-replace'), gtk.Label(_('Replace')))

		# Connect signals
		self.parent.regex_buffer.connect('changed', self.update_tab)
		self.parent.target_buffer.connect('changed', self.update_tab)
		self.parent.wtree.get_object('button-replace-result-apply').connect('clicked', self.apply_replace)
		self.parent.wtree.get_object('textview-replace').connect('key-press-event', self.parent.switch_focus)
		self.parent.wtree.get_object('vpaned-replace').connect('map', self.update_tab)
		self.replace_buffer.connect('changed', self.update_tab)

	def unregister(self):
		"""
		Unregister RegexToolModuleSplit module
			void unregister(void)
		"""

		# Save state
		if self.parent.config.get('window', 'save-state'):
			self.parent.config.set('data', 'textview-replace', self.replace_buffer.get_text(self.replace_buffer.get_start_iter(), self.replace_buffer.get_end_iter()))
			self.parent.config.set('window', 'pane-position-replace', self.parent.wtree.get_object('vpaned-replace').get_position())
	
	def apply_replace(self, source=None, event=None):
		"""
		Apply replacement to the target string
			void apply_replace(event source: gtk.Object, event: gtk.gdk.Event)
		"""

		# Update target string
		result_buffer = self.parent.wtree.get_object('textview-replace-result').get_buffer()
		self.parent.target_buffer.set_text(result_buffer.get_text(result_buffer.get_start_iter(), result_buffer.get_end_iter()))
	
	def update_tab(self, source=None, event=None):
		"""
		Update split GtkNotebook tab
			void update_tab(event source: gtk.Object, event: gtk.gdk.Event)
		"""

		# Stop if updating is active or regex not available
		if self.parent.updating or not self.parent.regex:
			return

		# Hide error message
		if hasattr(self, 'message_id'):
			self.parent.wtree.get_object('statusbar').remove_message(1, self.message_id)

		try:
			self.parent.wtree.get_object('textview-replace-result').get_buffer().set_text(self.parent.regex.sub(
				self.replace_buffer.get_text(self.replace_buffer.get_start_iter(), self.replace_buffer.get_end_iter()),
				self.parent.target,
				self.parent.limit,
			))
		except ( IndexError, re.error ), e:
			# Display error message in status bar
			self.message_id = self.parent.wtree.get_object('statusbar').push(1, _('Error: %s') % e)
