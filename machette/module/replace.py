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
classname = 'MachetteModuleReplace'

# Set module information
mandatory = True

# Set configuration options list
options = {
    'data.textview-replace': (str, ''),
    'window.pane-position-replace': (int, 0),
}


class MachetteModuleReplace(MachetteModule):
    def register(self):
        """
        Register MachetteModuleReplace module
            void register(void)
        """

        # Load module UI file
        self.parent.wtree.add_from_file(os.path.join(DATA_DIR,
            'ui/module/replace.ui'))

        # Initialize GtkTextBuffer
        self.rpbuffer = self.parent.wtree.get_object('textview-replace').\
            get_buffer()

        # Restore last state
        self.parent.wtree.get_object('vpaned-replace').set_position(
            self.parent.config.get('window.pane-position-replace'))
        self.rpbuffer.set_text(
            self.parent.config.get('data.textview-replace'))

        # Attach UI to the parent window
        self.parent.wtree.get_object('notebook-extension').append_page(
            self.parent.wtree.get_object('vpaned-replace'),
            gtk.Label(_('Replace')))

        # Connect signals
        self.parent.rbuffer.connect('changed', self.update_tab)
        self.parent.tbuffer.connect('changed', self.update_tab)
        self.parent.wtree.get_object('button-replace-result-apply').\
            connect('clicked', self.apply_replace)
        self.parent.wtree.get_object('textview-replace').\
            connect('key-press-event', self.parent.switch_focus)
        self.parent.wtree.get_object('vpaned-replace').\
            connect('map', self.update_tab)
        self.rpbuffer.connect('changed', self.update_tab)

    def unregister(self):
        """
        Unregister MachetteModuleReplace module
            void unregister(void)
        """

        # Save state
        if self.parent.config.get('window.save-state'):
            self.parent.config.set('data.textview-replace', self.rpbuffer.\
                get_text(self.rpbuffer.get_start_iter(),
                    self.rpbuffer.get_end_iter()))
            self.parent.config.set('window.pane-position-replace', self.\
                parent.wtree.get_object('vpaned-replace').get_position())

    def apply_replace(self, source=None, event=None):
        """
        Apply replacement to the target string
            void apply_replace(event source: gtk.Object, event: gtk.gdk.Event)
        """

        # Update target string
        rsbuffer = self.parent.wtree.get_object('textview-replace-result').\
            get_buffer()
        self.parent.tbuffer.set_text(rsbuffer.get_text(
            rsbuffer.get_start_iter(), rsbuffer.get_end_iter()))

    def update_tab(self, source=None, event=None):
        """
        Update replace GtkNotebook tab
            void update_tab(event source: gtk.Object, event: gtk.gdk.Event)
        """

        # Stop if updating is active or regex not available
        if self.parent.updating or not self.parent.regex:
            return

        # Hide error message
        self.parent.wtree.get_object('label-replace-message').hide()

        try:
            self.parent.wtree.get_object('textview-replace-result').\
                get_buffer().set_text(self.parent.regex.sub(
                    self.rpbuffer.get_text(self.rpbuffer.get_start_iter(),
                        self.rpbuffer.get_end_iter()),
                    self.parent.target,
                    self.parent.limit))
        except (IndexError, re.error), e:
             # Display error message
            self.parent.wtree.get_object('label-replace-message').set_label(
                _('Error: %s') % e)
            self.parent.wtree.get_object('label-replace-message').show()
