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
import random
import re
from machette import __cmdname__
from machette.module import MachetteModule
from machette.path import DATA_DIR

pygtk.require('2.0')

# Set module class name
classname = 'MachetteModuleHlSelect'

# Set module information
name = _('Highlight selection')
description = _('Highlight target according to regular expression selection.')
version = None
authors = ['Vincent Batoufflet <vincent@batoufflet.info>']
website = None

# Set configuration options list
options = {
    'color.match-select': (str, '#ff9900'),
}


class MachetteModuleHlSelect(MachetteModule):
    def register(self):
        """
        Register MachetteModuleHlSelect module
            void register(void)
        """

        # Initialize window if needed
        if not hasattr(self.parent, 'pref_dialog'):
            self.parent.init_pref_dialog()

        # Update preference pane
        tablecolor = self.parent.wtree.get_object('table-color')
        tablecolor.resize(tablecolor.get_property('n-rows') + 1,
            tablecolor.get_property('n-columns'))

        self.label = gtk.Label(_('Selection match:'))
        self.label.set_property('xalign', 0)
        self.label.show()

        self.colorbutton = gtk.ColorButton(
            gtk.gdk.color_parse(self.parent.config.get('color.match-select')))
        self.colorbutton.show()

        tablecolor.attach(self.label, 0, 1, 2, 3, gtk.FILL, gtk.FILL)
        tablecolor.attach(self.colorbutton, 1, 2, 2, 3, gtk.FILL, gtk.FILL)

        # Create selection tag
        self.parent.tbuffer.create_tag('match-select',
            background=gtk.gdk.color_parse(
                self.parent.config.get('color.match-select')))

        # Connect signals
        self.handlers = dict()
        self.handlers['regex_buffer.mark-set'] = self.parent.rbuffer.connect(
            'mark-set', self.check_sub_pattern)
        self.handlers['target_buffer.changed'] = self.parent.tbuffer.connect(
            'changed', self.check_sub_pattern)
        self.handlers['button-pref-ok.clicked'] = self.parent.wtree.\
            get_object('button-pref-ok').connect('clicked', self.set_color)
        self.handlers['button-pref-reset.clicked'] = self.parent.wtree.\
            get_object('button-pref-reset').connect('clicked',
                self.reset_color)

    def check_sub_pattern(self, source=None, step=None, count=None,
                          extend=None):
        """
        Check for regular expression sub-pattern
            void check_sub_pattern(event source: gtk.Object,
                                   step: gtk.MovementStep, step count: int,
                                   selection extension flag: bool)
        """

        # Remove previous selection
        self.parent.tbuffer.remove_tag_by_name('match-select',
            self.parent.tbuffer.get_start_iter(),
            self.parent.tbuffer.get_end_iter())

        # Get regular expression selection bounds
        bounds = self.parent.rbuffer.get_selection_bounds()

        # Stop if no selection or match
        if len(bounds) == 0 or len(self.parent.match) == 0:
            return

        # Get regular expression and sub-target
        regex = self.parent.rbuffer.get_text(
            self.parent.rbuffer.get_start_iter(),
            self.parent.rbuffer.get_end_iter(),
        )

        target = self.parent.tbuffer.get_text(
            self.parent.tbuffer.get_iter_at_offset(
                self.parent.match[0].start()),
            self.parent.tbuffer.get_iter_at_offset(
                self.parent.match[0].end()),
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
            select = self.parent.rbuffer.get_text(bounds[0], bounds[1])

            if not s \
              or select.startswith('(') \
              and select.find(')') == -1 \
              or select.endswith(')') \
              and select.find('(') == -1:
                return

            # Update selection tag priority
            self.parent.tbuffer.get_tag_table().lookup('match-select').\
                set_priority(self.parent.tbuffer.get_tag_table().\
                    get_size() - 1)

            # Apply selection tag
            self.parent.tbuffer.apply_tag_by_name(
                'match-select',
                self.parent.tbuffer.get_iter_at_offset(
                    self.parent.match[0].start() + s.start(mid)),
                self.parent.tbuffer.get_iter_at_offset(
                    self.parent.match[0].start() + s.end(mid)),
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

        return '%s_%s' % (__cmdname__, mid)

    def reset_color(self, source=None):
        """
        Reset selection highlight color
            void reset_color(event source: gtk.Object)
        """

        # Set color to default
        self.colorbutton.set_color(gtk.gdk.color_parse(
            self.parent.config.get_default('color.match-select')))

    def set_color(self, source=None):
        """
        Set selection highlight color
            void set_color(event source: gtk.Object)
        """

        # Update color preference
        self.parent.config.set('color.match-select',
            self.colorbutton.get_color().to_string())

        # Update tag
        self.parent.tbuffer.get_tag_table().lookup('match-select').\
            set_property('background',
                gtk.gdk.color_parse(self.parent.config.\
                    get('color.match-select')),
        )

    def unregister(self):
        """
        Unregister MachetteModuleHlSelect module
            void unregister(void)
        """

        # Update preference pane
        tablecolor = self.parent.wtree.get_object('table-color')
        tablecolor.remove(self.label)
        tablecolor.remove(self.colorbutton)

        # Remove selection tag
        self.parent.tbuffer.get_tag_table().remove(
            self.parent.tbuffer.get_tag_table().lookup('match-select'))

        # Disconnect signals
        self.parent.rbuffer.disconnect(self.handlers['regex_buffer.mark-set'])
        self.parent.tbuffer.disconnect(self.handlers['target_buffer.changed'])
        self.parent.wtree.get_object('button-pref-ok').disconnect(
            self.handlers['button-pref-ok.clicked'])
        self.parent.wtree.get_object('button-pref-reset').disconnect(
            self.handlers['button-pref-reset.clicked'])
