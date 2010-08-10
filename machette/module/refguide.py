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
from machette import __shortname__
from machette.module import MachetteModule
from machette.path import DATA_DIR

pygtk.require('2.0')

# Set module class name
classname = 'MachetteModuleRefGuide'

# Set module information
name = _('Reference guide')
description = _('Python regular expression reference guide.')
version = re.__version__
authors = ['Vincent Batoufflet <vincent@batoufflet.info>']
website = None


class MachetteModuleRefGuide(MachetteModule):
    def close_guide(self, source=None, event=None):
        """
        Close reference guide window.
            void close_guide(event source: gtk.Object, event: gtk.gdk.Event)
        """

        # Hide window
        self.window.hide_all()
        return True

    def open_guide(self, source=None, event=None):
        """
        Open reference guide window.
            void open_guide(event source: gtk.Object, event: gtk.gdk.Event)
        """

        # Update modules list GtkListStore
        liststore = self.parent.wtree.get_object('liststore-refguide')
        liststore.clear()

        # Get documentation entries
        entries = re.findall(r'^ {4}(\S+)\s+(.+\n(?: {5,}.+\n)*)', re.__doc__,
            re.M)

        clean = re.compile(r'^\s+', re.M)

        for e in entries:
            # Skip unwanted entries
            if e[0] in re.__all__:
                continue

            liststore.append([e[0], clean.sub('', e[1])])

        # Show window
        self.window.show_all()

    def register(self):
        """
        Register MachetteModuleRefGuide module
            void register(void)
        """

        # Load module UI file
        self.parent.wtree.add_from_file(os.path.join(DATA_DIR,
            'ui/module/refguide.ui'))

        self.window = self.parent.wtree.get_object('window-refguide')
        self.window.set_title(__shortname__ + ' - ' + _('Reference guide'))

        # Initialize group GtkTreeView
        render = gtk.CellRendererText()

        treeview = self.parent.wtree.get_object('treeview-refguide')
        treeview.get_column(0).pack_start(render, False)
        treeview.get_column(0).add_attribute(render, 'text', 0)
        treeview.get_column(1).pack_start(render, False)
        treeview.get_column(1).add_attribute(render, 'text', 1)

        # Create documentation menu item
        self.separator = gtk.SeparatorMenuItem()
        self.separator.show()
        self.menuitem = gtk.ImageMenuItem(_('_Reference guide'))
        self.menuitem.show()

        self.parent.wtree.get_object('menuitem-help').get_submenu().\
            insert(self.separator, 0)
        self.parent.wtree.get_object('menuitem-help').get_submenu().\
            insert(self.menuitem, 0)

        # Connect signals
        self.menuitem.connect('activate', self.open_guide)
        self.parent.wtree.get_object('imagemenuitem-refguide-file-close').\
            connect('activate', self.close_guide)
        self.window.connect('delete-event', self.close_guide)

    def unregister(self):
        """
        Unregister MachetteModuleRefGuide module
            void unregister(void)
        """

        # Destroy items
        self.separator.destroy()
        self.menuitem.destroy()
        self.window.destroy()
