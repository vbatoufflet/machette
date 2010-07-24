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

import gtk
import pygtk
import os
import re
from machette.module import MachetteModule
from machette.path import DATA_DIR

pygtk.require('2.0')

# Set module class name
classname = 'MachetteModuleSplit'

# Set module information
mandatory = True

# Set configuration options list
options = {
    'window.split-delimiter': (int, 0),
}


class MachetteModuleSplit(MachetteModule):
    def register(self):
        """
        Register MachetteModuleSplit module
            void register(void)
        """

        # Load module UI file
        self.parent.wtree.add_from_file(os.path.join(DATA_DIR,
                                                     'ui/module/split.ui'))

        # Initialize split delimiter GtkComboBox
        for delim in ['|', '#', '@', unichr(0xb6), unichr(0x25a0)]:
            self.parent.wtree.get_object('combobox-split-delimiter').\
                append_text(delim)

        # Restore last state
        self.parent.wtree.get_object('combobox-split-delimiter').set_active(
            self.parent.config.get('window.split-delimiter'))

        # Attach UI to the parent window
        self.parent.wtree.get_object('notebook-extension').append_page(
            self.parent.wtree.get_object('vbox-split'), gtk.Label(_('Split')))

        # Connect signals
        self.parent.rbuffer.connect('changed', self.update_tab)
        self.parent.tbuffer.connect('changed', self.update_tab)
        self.parent.wtree.get_object('combobox-split-delimiter').\
            connect('changed', self.update_tab)
        self.parent.wtree.get_object('vbox-split').\
            connect('map', self.update_tab)

    def unregister(self):
        """
        Unregister MachetteModuleSplit module
            void unregister(void)
        """

        # Save state
        if self.parent.config.get('window.save-state'):
            self.parent.config.set('window.split-delimiter', self.parent.\
                wtree.get_object('combobox-split-delimiter').get_active())

    def update_tab(self, source=None, event=None):
        """
        Update split GtkNotebook tab
            void update_tab(event source: gtk.Object, event: gtk.gdk.Event)
        """

        # Reset buffer text
        self.parent.wtree.get_object('textview-split-result').get_buffer().\
            set_text('')

        # Stop if updating is active or regex not available
        if self.parent.updating or not self.parent.regex:
            return

        try:
            delimiter = self.parent.wtree.\
                get_object('combobox-split-delimiter').get_active_text()

            # Get split chunks
            regex = re.compile(self.parent.rbuffer.get_text(
                self.parent.rbuffer.get_start_iter(),
                self.parent.rbuffer.get_end_iter()), self.parent.flags)
            chunks = regex.split(self.parent.target, self.parent.limit)
            chunks = [a if a else '' for a in chunks]

            self.parent.wtree.get_object('textview-split-result').\
                get_buffer().set_text(delimiter.join(chunks))
        except (IndexError, re.error), e:
            pass
