# -*- coding: utf-8 -*-
#
# This file is a part of Machette.
#
# Copyright (C) 2010 Vincent Batoufflet <vincent@batoufflet.info>
#
# This software is released under the terms of the GNU General Public License
# version 3 or any later version. See LICENSE file for further details.
#
# $Id$

import gtk, pygtk
import os
from machette.module import MachetteModule
from machette.path import DATA_DIR

pygtk.require('2.0')

# Set module class name
classname = 'MachetteModuleGroup'

# Set module information
mandatory = True

class MachetteModuleGroup(MachetteModule):
	def register(self):
		"""
		Register MachetteModuleGroup module
			void register(void)
		"""

		# Load module UI file
		self.parent.wtree.add_from_file(os.path.join(DATA_DIR, 'ui/module/group.ui'))

		# Initialize group GtkTreeView
		render = gtk.CellRendererText()

		treeview = self.parent.wtree.get_object('treeview-group')
		treeview.get_column(0).pack_start(render, False)
		treeview.get_column(0).add_attribute(render, 'text', 0)
		treeview.get_column(1).pack_start(render, False)
		treeview.get_column(1).add_attribute(render, 'text', 1)
		treeview.get_column(2).pack_start(render, False)
		treeview.get_column(2).add_attribute(render, 'text', 2)

		# Attach UI to the parent window
		self.parent.wtree.get_object('notebook-extension').append_page(self.parent.wtree.get_object('vbox-group'), gtk.Label(_('Group')))

		# Connect signals
		self.parent.regex_buffer.connect('changed', self.update_tab)
		self.parent.target_buffer.connect('changed', self.update_tab)
		self.parent.wtree.get_object('spinbutton-group-index').connect('value-changed', self.update_tab)
		self.parent.wtree.get_object('vbox-group').connect('map', self.update_tab)
	
	def update_tab(self, source=None, event=None):
		"""
		Update group GtkNotebook tab
			void update_tab(event source: gtk.Object, event: gtk.gdk.Event)
		"""

		# Stop if updating is active or regex not available
		if self.parent.updating or not self.parent.regex:
			return

		# Get GtkSpinButton
		spinbutton = self.parent.wtree.get_object('spinbutton-group-index')

		# Update GtkSpinButton adjustment
		if type(source) != gtk.SpinButton:
			spinbutton.set_adjustment(gtk.Adjustment(1, 1, len(self.parent.match), 1, 1, 0))

		# Get GtkListStore
		liststore = self.parent.wtree.get_object('liststore-group')

		# Clear previous entries
		liststore.clear()

		# Append new groups
		count = 1
		groups = dict(map(lambda a: (a[1], a[0]), self.parent.regex.groupindex.items()))
		index = int(spinbutton.get_value())-1

		# Stop if no match or groups
		if len(self.parent.match) == 0 or not self.parent.match[index].groups():
			spinbutton.set_sensitive(False)
			spinbutton.set_value(1)
			return
		else:
			spinbutton.set_sensitive(True)                                                                                                              

		for g in self.parent.match[index].groups():
			liststore.append([ count, groups[count] if count in groups else '', g ])
			count += 1
