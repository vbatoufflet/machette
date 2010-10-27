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

__shortname__ = 'Machette'
__cmdname__ = 'machette'
__description__ = 'An interactive regular expression tester'
__version__ = '0.3'

__author__ = 'Vincent Batoufflet'
__email__ = 'vincent@batoufflet.info'
__copyright__ = 'Copyright © 2010 Vincent Batoufflet'
__license__ = 'gpl3'

__website__ = 'http://thonpy.com/machette/'

import gtk
import pygtk
import getopt
import gettext
import locale
import os
import re
import sys
from machette.config import MachetteConfig
from machette.module import *
from machette.path import DATA_DIR, LOCALE_DIR
from machette.ui.undostack import UndoStack

pygtk.require('2.0')


class Machette:
    def __init__(self):
        """
        Initialize Machette instance
            Machette __init__(void)
        """

        # Initialize i18n support
        gettext.install(__cmdname__, LOCALE_DIR)
        gettext.bindtextdomain(__cmdname__, LOCALE_DIR)
        locale.bindtextdomain(__cmdname__, LOCALE_DIR)

        # Parse command line arguments
        self.opt_safemode = False

        try:
            opts, args = getopt.getopt(sys.argv[1:], 'hsv',
                ['help', 'safe-mode', 'version'])
        except Exception, e:
            sys.stderr.write(_('Error: %s\n') % e)
            self.print_usage()
            sys.exit(1)

        for opt, arg in opts:
            if opt in ['-h', '--help']:
                self.print_usage()
                sys.exit(0)
            elif opt in ['-v', '--version']:
                self.print_version()
                sys.exit(0)
            elif opt in ['-s', '--safe-mode']:
                self.opt_safemode = True

        # Load widgets from UI file
        self.wtree = gtk.Builder()
        self.wtree.set_translation_domain(__cmdname__)
        self.wtree.add_from_file(os.path.join(DATA_DIR, 'ui', 'main.ui'))

        # Set instance attributes
        self.flags = 0
        self.limit = 1
        self.match = list()
        self.modules = dict()
        self.regex = None
        self.target = ''
        self.updating = False

        # Set window title
        self.wtree.get_object('window-main').set_title(__shortname__)

        # Initialize GtkTextBuffer buffers
        self.rbuffer = self.wtree.get_object('textview-regex').get_buffer()
        self.tbuffer = self.wtree.get_object('textview-target').get_buffer()

        # Connect signals
        self.rbuffer.connect('changed', self.check_pattern)
        self.tbuffer.connect('changed', self.check_pattern)
        self.wtree.get_object('checkbutton-option-g').connect('toggled',
            self.check_pattern)
        self.wtree.get_object('checkbutton-option-i').connect('toggled',
            self.check_pattern)
        self.wtree.get_object('checkbutton-option-l').connect('toggled',
            self.check_pattern)
        self.wtree.get_object('checkbutton-option-m').connect('toggled',
            self.check_pattern)
        self.wtree.get_object('checkbutton-option-s').connect('toggled',
            self.check_pattern)
        self.wtree.get_object('checkbutton-option-u').connect('toggled',
            self.check_pattern)
        self.wtree.get_object('checkbutton-option-x').connect('toggled',
            self.check_pattern)
        self.wtree.get_object('menuitem-edit-pref').connect('activate',
            self.show_pref_dialog)
        self.wtree.get_object('menuitem-file-export').connect('activate',
            self.export_to_file)
        self.wtree.get_object('menuitem-file-import').connect('activate',
            self.import_from_file)
        self.wtree.get_object('menuitem-file-quit').connect('activate',
            self.quit)
        self.wtree.get_object('menuitem-help-about').connect('activate',
            self.show_about_dialog)
        self.wtree.get_object('menuitem-view-extension').connect('toggled',
            self.update_extension_state)
        self.wtree.get_object('menuitem-view-statusbar').connect('toggled',
            self.update_statusbar_state)
        self.wtree.get_object('textview-regex').connect('key-press-event',
            self.switch_focus)
        self.wtree.get_object('textview-target').connect('key-press-event',
            self.switch_focus)
        self.wtree.get_object('window-main').connect('destroy', self.quit)
        self.wtree.get_object('window-main').connect('map', self.check_pattern)

        # Load and initialize additionnal modules
        options = list()

        for name in get_modules_list():
            self.modules[name] = load_module(name, ['classname', 'mandatory',
                                                    'options'])

            if hasattr(self.modules[name], 'options'):
                options.append(self.modules[name].options)

        # Load configuration
        self.config = MachetteConfig(options)

        # Get enabled modules
        for name in self.modules:
            # Skip disabled modules
            if (not hasattr(self.modules[name], 'mandatory') \
              or not self.modules[name].mandatory) \
              and (not name in self.config.get('module.enabled') \
              or self.opt_safemode):
                continue

            # Load module
            self.module_init(name)

    def check_pattern(self, source=None, event=None):
        """
        Check for regular expression pattern
            void check_pattern(event source: gtk.Object, event: gtk.gdk.Event)
        """

        # Stop if updating is active
        if self.updating:
            return

        # Hide error message
        self.wtree.get_object('label-regex-message').hide()

        # Check for regular expression flags
        self.flags = 0
        self.limit = 1
        self.match = list()

        if self.wtree.get_object('checkbutton-option-g').get_active():
            self.limit = 0
        if self.wtree.get_object('checkbutton-option-i').get_active():
            self.flags |= re.I
        if self.wtree.get_object('checkbutton-option-l').get_active():
            self.flags |= re.L
        if self.wtree.get_object('checkbutton-option-m').get_active():
            self.flags |= re.M
        if self.wtree.get_object('checkbutton-option-s').get_active():
            self.flags |= re.S
        if self.wtree.get_object('checkbutton-option-u').get_active():
            self.flags |= re.U
        if self.wtree.get_object('checkbutton-option-x').get_active():
            self.flags |= re.X

        # Check target string for pattern matching
        try:
            # Get regular expression iters
            self.regex = re.compile(self.rbuffer.get_text(
                self.rbuffer.get_start_iter(), self.rbuffer.get_end_iter()),
                self.flags)
            self.target = self.tbuffer.get_text(self.tbuffer.get_start_iter(),
                self.tbuffer.get_end_iter()).decode('utf-8', 'ignore')

            # Get MatchObject list
            for i in self.regex.finditer(self.target):
                self.match.append(i)

            # Update target GtkTextBuffer highlighting
            self.update_target_tags(source)
        except (IndexError, re.error), e:
            # Display error message
            self.wtree.get_object('label-regex-message').set_label(
                _('Error: %s') % e)
            self.wtree.get_object('label-regex-message').show()

    def export_to_file(self, source=None, event=None):
        """
        Export target string to a file
            void export_to_file(event source: gtk.Object, event: gtk.gdk.Event)
        """

        filepath = None

        # Create GtkFileChooserDialog
        dialog = gtk.FileChooserDialog(_('Export to file...'), None,
            gtk.FILE_CHOOSER_ACTION_SAVE, (
                gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL,
                gtk.STOCK_SAVE, gtk.RESPONSE_OK,
            ))

        dialog.set_default_response(gtk.RESPONSE_OK)

        action = dialog.run()
        if action == gtk.RESPONSE_OK:
            filepath = dialog.get_filename()
        dialog.destroy()

        if filepath:
            # Confirm if file already exists
            if os.path.exists(filepath):
                message = gtk.MessageDialog(None, 0, gtk.MESSAGE_WARNING,
                    gtk.BUTTONS_YES_NO)
                message.set_markup(_('The destination file already exists. '
                    'Are you sure?'))

                action = message.run()
                if action == gtk.RESPONSE_NO:
                    filepath = None
                message.destroy()

            if filepath:
                # Load target string from file
                fd = open(filepath, 'w')
                fd.write(self.tbuffer.get_text(self.tbuffer.get_start_iter(),
                    self.tbuffer.get_end_iter()))
                fd.close()

    def import_from_file(self, source=None, event=None):
        """
        Import target string from a file
            void import_from_file(event source: gtk.Object,
                                  event: gtk.gdk.Event)
        """

        filepath = None

        # Create GtkFileChooserDialog
        dialog = gtk.FileChooserDialog(_('Import from file...'), None,
            gtk.FILE_CHOOSER_ACTION_OPEN, (
                gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL,
                gtk.STOCK_OPEN, gtk.RESPONSE_OK,
        ))

        dialog.set_default_response(gtk.RESPONSE_OK)

        # Create filters
        filter = gtk.FileFilter()
        filter.set_name(_('Text files'))
        filter.add_mime_type('text/plain')
        dialog.add_filter(filter)

        filter = gtk.FileFilter()
        filter.set_name(_('All files'))
        filter.add_pattern('*')
        dialog.add_filter(filter)

        action = dialog.run()
        if action == gtk.RESPONSE_OK:
            filepath = dialog.get_filename()
        dialog.destroy()

        if filepath:
            # Confirm if buffer has data
            if self.tbuffer.get_char_count() != 0:
                message = gtk.MessageDialog(None, 0, gtk.MESSAGE_QUESTION,
                    gtk.BUTTONS_YES_NO)
                message.set_markup(_('Your are about to replace the existing '
                    'target string. Are you sure?'))

                action = message.run()
                if action == gtk.RESPONSE_NO:
                    filepath = None
                message.destroy()

            if filepath:
                # Load target string from file
                fd = open(filepath, 'r')
                self.tbuffer.set_text(fd.read())
                fd.close()

    def init_pref_dialog(self, source=None, event=None):
        """
        Initialize preferences window
            void init_pref_dialog(event source: gtk.Object,
                                  event: gtk.gdk.Event)
        """

        if hasattr(self, 'pref_dialog'):
            return

        # Initialize window
        self.wtree.add_from_file(os.path.join(DATA_DIR, 'ui', 'pref.ui'))
        self.pref_dialog = self.wtree.get_object('dialog-pref')
        self.pref_dialog.set_modal(True)
        self.pref_dialog.set_position(gtk.WIN_POS_CENTER_ON_PARENT)
        self.pref_dialog.set_type_hint(gtk.gdk.WINDOW_TYPE_HINT_DIALOG)

        # Initialize GtkTreeView
        treeview = self.wtree.get_object('treeview-module')

        render_toggle = gtk.CellRendererToggle()
        render_toggle.set_property('activatable', True)
        render_toggle.connect('toggled', self.toggle_module,
            treeview.get_model())
        render_text = gtk.CellRendererText()

        treeview.get_column(0).pack_start(render_toggle, False)
        treeview.get_column(0).add_attribute(render_toggle, 'active', 0)
        treeview.get_column(1).pack_start(render_text, False)
        treeview.get_column(1).add_attribute(render_text, 'markup', 2)

        # Connect signals
        self.wtree.get_object('notebook-pref').connect('switch-page',
            self.update_pref_dialog)
        self.wtree.get_object('treeview-module').connect('cursor-changed',
            self.update_pref_dialog, None, 1)

    def main(self):
        """
        Run the GTK main loop
            void main(void)
        """

        # Set updating flag
        self.updating = True

        # Restore last state
        self.rbuffer.set_text(self.config.get('data.textview-regex'))
        self.tbuffer.set_text(self.config.get('data.textview-target'))
        self.wtree.get_object('checkbutton-option-g').set_active(
            self.config.get('window.option-g-active'))
        self.wtree.get_object('checkbutton-option-i').set_active(
            self.config.get('window.option-i-active'))
        self.wtree.get_object('checkbutton-option-l').set_active(
            self.config.get('window.option-l-active'))
        self.wtree.get_object('checkbutton-option-m').set_active(
            self.config.get('window.option-m-active'))
        self.wtree.get_object('checkbutton-option-s').set_active(
            self.config.get('window.option-s-active'))
        self.wtree.get_object('checkbutton-option-u').set_active(
            self.config.get('window.option-u-active'))
        self.wtree.get_object('checkbutton-option-x').set_active(
            self.config.get('window.option-x-active'))
        self.wtree.get_object('menuitem-view-extension').set_active(
            self.config.get('window.show-extension'))
        self.wtree.get_object('menuitem-view-statusbar').set_active(
            self.config.get('window.show-statusbar'))
        self.wtree.get_object('notebook-extension').set_current_page(
            self.config.get('window.notebook-page'))
        self.wtree.get_object('vpaned1').set_position(
            self.config.get('window.pane-position1'))
        self.wtree.get_object('vpaned2').set_position(
            self.config.get('window.pane-position2'))
        self.wtree.get_object('window-main').set_default_size(
            self.config.get('window.width'), self.config.get('window.height'))

        # Initialize undo stacks
        UndoStack(self.wtree.get_object('textview-regex'))
        UndoStack(self.wtree.get_object('textview-target'))

        # Update view states
        self.update_extension_state()
        self.update_statusbar_state()

        # Reset updating flag
        self.updating = False

        # Initialize target tags
        self.set_target_tags()

        # Set main window visible
        self.wtree.get_object('window-main').show()

        # Update current tab if needed
        if self.config.get('window.show-extension'):
            notebook = self.wtree.get_object('notebook-extension')
            notebook.get_nth_page(notebook.get_current_page()).emit('map')

        # Enter GTK main loop
        gtk.main()

    def module_destroy(self, name):
        """
        Unload module by name
            void module_destroy(module name: str)
        """

        if not hasattr(self.modules[name], '__instance__'):
            return

        # Unregister and destroy requested module
        self.modules[name].__instance__.unregister()
        del self.modules[name].__instance__

    def module_init(self, name):
        """
        Load module by name
            void module_init(module name: str)
        """

        if hasattr(self.modules[name], '__instance__'):
            return

        # Load and register requested module
        self.modules[name].__instance__ = getattr(self.modules[name],
            self.modules[name].classname)(self)
        self.modules[name].__instance__.register()

    def print_usage(self):
        """
        Print program usage
            void print_usage(void)
        """

        print(_('Usage: %s [OPTION]...') % __cmdname__)
        print('')
        print(_('Options:'))
        print('   -h, --help       ' + _('display this help and exit'))
        print('   -s, --safe-mode  ' + _('disable modules load at startup'))
        print('   -v, --version    ' + _('display program version and exit'))

    def print_version(self):
        """
        Print program version
            void print_version(void)
        """

        print('machette ' + __version__)

    def quit(self, source=None, event=None):
        """
        Quit the GTK main loop
            void quit(event source: gtk.Object, event: gtk.gdk.Event)
        """

        # Save state
        if self.config.get('window.save-state'):
            self.config.set('data.textview-regex', self.rbuffer.get_text(
                self.rbuffer.get_start_iter(), self.rbuffer.get_end_iter()))
            self.config.set('data.textview-target', self.tbuffer.get_text(
                self.tbuffer.get_start_iter(), self.tbuffer.get_end_iter()))
            self.config.set('window.height',
                self.wtree.get_object('window-main').get_allocation().height)
            self.config.set('window.notebook-page',
                self.wtree.get_object('notebook-extension').get_current_page())
            self.config.set('window.option-g-active',
                self.wtree.get_object('checkbutton-option-g').get_active())
            self.config.set('window.option-i-active',
                self.wtree.get_object('checkbutton-option-i').get_active())
            self.config.set('window.option-l-active',
                self.wtree.get_object('checkbutton-option-l').get_active())
            self.config.set('window.option-m-active',
                self.wtree.get_object('checkbutton-option-m').get_active())
            self.config.set('window.option-s-active',
                self.wtree.get_object('checkbutton-option-s').get_active())
            self.config.set('window.option-u-active',
                self.wtree.get_object('checkbutton-option-u').get_active())
            self.config.set('window.option-x-active',
                self.wtree.get_object('checkbutton-option-x').get_active())
            self.config.set('window.pane-position1',
                self.wtree.get_object('vpaned1').get_position())
            self.config.set('window.pane-position2',
                self.wtree.get_object('vpaned2').get_position())
            self.config.set('window.show-extension',
                self.wtree.get_object('menuitem-view-extension').get_active())
            self.config.set('window.show-statusbar',
                self.wtree.get_object('menuitem-view-statusbar').get_active())
            self.config.set('window.width',
                self.wtree.get_object('window-main').get_allocation().width)

        # Unregister loaded modules
        for name in self.modules:
            self.module_destroy(name)

        # Save configuration options
        self.config.save()

        # Stop GTK main loop
        gtk.main_quit()

    def set_target_tags(self):
        """
        Set target GtkTextBuffer tags
            void set_target_tags(void)
        """

        for name in ['match-first', 'match-next']:
            # Create new tag if needed
            if not self.tbuffer.get_tag_table().lookup(name):
                self.tbuffer.create_tag(name)

            # Set background property
            self.tbuffer.get_tag_table().lookup(name).set_property(
                'background', gtk.gdk.color_parse(self.config.get('color.' +
                    name)))

    def show_about_dialog(self, source=None, event=None):
        """
        Create and/or display about window
            bool show_about_dialog(event source: gtk.Object,
                                   event: gtk.gdk.Event)
        """

        # Create GtkAboutDialog if needed
        if not hasattr(self, 'about_dialog'):
            # Create GtkAboutDialog
            self.about_dialog = gtk.AboutDialog()

            # Set base information
            self.about_dialog.set_name(__shortname__)
            self.about_dialog.set_version(__version__)
            self.about_dialog.set_comments(__description__)
            self.about_dialog.set_copyright(__copyright__)
            self.about_dialog.set_website(__website__)

            # Load information from external files
            try:
                fd = open('/usr/share/common-licenses/GPL-3')
                self.about_dialog.set_license(fd.read())
                fd.close()
            except IOError, e:
                self.about_dialog.set_license(
                    _('Error: unable to load LICENSE file'))

            try:
                fd = open(os.path.join(DATA_DIR, 'AUTHORS'))
                self.about_dialog.set_authors(fd.read().splitlines())
                fd.close()
            except IOError, e:
                self.about_dialog.set_authors(
                    [_('Error: unable to load AUTHORS file')])

            try:
                fd = open(os.path.join(DATA_DIR, 'TRANSLATORS'))
                self.about_dialog.set_translator_credits(fd.read())
                fd.close()
            except IOError, e:
                self.about_dialog.set_translator_credits(
                    [_('Error: unable to load TRANSLATORS file')])

        # Set dialog visible and wait for closing
        self.about_dialog.run()
        self.about_dialog.hide()

    def toggle_module(self, source=None, path=None, model=None):
        """
        """

        model[path][0] = not model[path][0]

    def show_pref_dialog(self, source=None, event=None):
        """
        Create and/or display preferences window
            bool show_pref_dialog(event source: gtk.Object,
                                  event: gtk.gdk.Event)
        """

        # Initialize window if needed
        if not hasattr(self, 'pref_dialog'):
            self.init_pref_dialog()

        # Update preferences window state
        self.wtree.get_object('checkbutton-window-save-state').set_active(
            self.config.get('window.save-state'))
        self.wtree.get_object('colorbutton-color-first').set_color(
            gtk.gdk.color_parse(self.config.get('color.match-first')))
        self.wtree.get_object('colorbutton-color-next').set_color(
            gtk.gdk.color_parse(self.config.get('color.match-next')))

        # Update modules list GtkListStore
        liststore = self.wtree.get_object('liststore-module')

        # Clear previous entries
        liststore.clear()

        for name in self.modules:
            module = load_module(name, ['classname', 'description',
                                        'mandatory', 'name', 'version'])

            # Skip mandatory modules
            if hasattr(module, 'mandatory') and module.mandatory:
                continue

            # Set version string if needed
            if not hasattr(module, 'version'):
                module.version = ''

            # Append module
            liststore.append([name in self.config.get('module.enabled'), name,
                '<b>%s</b> %s\n%s' % (
                    module.name if hasattr(module, 'name') else name,
                    module.version if module.version else __version__,
                    module.description if hasattr(module, 'description') \
                        else _('No description available.'),
                )])

        # Set dialog visible and wait for action
        action = None

        while not action:
            # Wait for action
            action = self.pref_dialog.run()

            if action == 2:
                # Update preferences window state with defaults
                self.wtree.get_object('checkbutton-window-save-state').\
                    set_active(self.config.get_default('window.save-state'))
                self.wtree.get_object('colorbutton-color-first').set_color(
                    gtk.gdk.color_parse(
                        self.config.get_default('color.match-first')))
                self.wtree.get_object('colorbutton-color-next').set_color(
                    gtk.gdk.color_parse(
                        self.config.get_default('color.match-next')))

                # Cancel action value
                action = None
            else:
                # Set new preferences values
                self.config.set('color.match-first', self.wtree.get_object(
                    'colorbutton-color-first').get_color().to_string())
                self.config.set('color.match-next', self.wtree.get_object(
                    'colorbutton-color-next').get_color().to_string())
                self.config.set('window.save-state', self.wtree.get_object(
                    'checkbutton-window-save-state').get_active())

                # Set enabled modules list
                enabled = list()

                for item in self.wtree.get_object('liststore-module'):
                    if item[0]:
                        # Append to enabled modules list
                        enabled.append(item[1])

                        # Initialize module
                        if not self.opt_safemode:
                            self.module_init(item[1])
                    else:
                        # Destroy loaded module
                        self.module_destroy(item[1])

                # Display safe-mode warning if needed
                if self.opt_safemode \
                  and enabled != self.config.get('module.enabled'):
                    message = gtk.MessageDialog(None, 0,
                        gtk.MESSAGE_WARNING, gtk.BUTTONS_OK)
                    message.set_markup(_('Safe mode is currently '
                        'active. Please relaunch %s to validate changes.')
                            % __cmdname__)

                    message.run()
                    message.destroy()

                self.config.set('module.enabled', enabled)

                # Update target GtkTextBuffer tags
                self.set_target_tags()

            if action:
                # Close preferences dialog
                self.pref_dialog.hide()

                # Perform a pattern check
                self.check_pattern()

    def switch_focus(self, source=None, event=None):
        """
        Switch focus between various GtkTextViews
            bool switch_focus(event source: gtk.Object, event: gtk.gdk.Event)
        """

        # Switch focus between GtkTextView
        if gtk.gdk.keyval_name(event.keyval) == 'Tab':
            # Do a normal swtch if <Control> is pressed
            if event.state & gtk.gdk.CONTROL_MASK:
                return

            # Move focus to the next widget
            source.get_toplevel().child_focus(gtk.DIR_TAB_FORWARD)

            # Continue if focused widget is not an editable GtkTextView
            focus = source.get_toplevel().get_focus()

            if focus.get_name() != 'GtkTextView' \
              or (hasattr(focus, 'get_editable') \
              and not focus.get_editable()):
                self.switch_focus(source, event)

            return True

    def update_extension_state(self, source=None, event=None):
        """
        Update extension panel state according to option
            void update_extension_state(event source: gtk.Object,
                                        event: gtk.gdk.Event)
        """

        # Get previous state
        previous = self.config.get('window.show-extension')

        # Update configuration option value
        self.config.set('window.show-extension', self.wtree.\
            get_object('menuitem-view-extension').get_active())

        # Resize window when status change
        if previous != self.config.get('window.show-extension'):
            self.wtree.get_object('window-main').resize(
                self.wtree.get_object('window-main').get_allocation().width,
                (self.wtree.get_object('window-main').get_allocation().height
                - self.wtree.get_object('notebook-extension').\
                    get_allocation().height),
            )

        # Update widgets visibility
        self.wtree.get_object('notebook-extension').set_visible(
            self.config.get('window.show-extension'))

    def update_pref_dialog(self, source=None, page=None, pagenum=None):
        """
        Update preferences dialog widgets
            void update_pref_dialog(event source: gtk.Object,
                                    page: gobject.GPointer, page index: int)
        """

        # Update module tab
        if pagenum == 1:
            model, treeiter = self.wtree.get_object('treeview-module').\
                get_selection().get_selected()

            if treeiter:
                name = model.get_value(treeiter, 1)
                module = load_module(name, ['authors', 'description', 'name',
                                            'version', 'website'])

                # Set defaults if needed
                if not hasattr(module, 'version'):
                    module.version = ''

                if not hasattr(module, 'website') or not module.website:
                    module.website = __website__

                # Update module information
                self.wtree.get_object('label-module-info').set_label(
                    '<big><b>%s</b></big> %s\n%s' % (
                        module.name if hasattr(module, 'name') else name,
                        module.version if module.version else __version__,
                        module.description if hasattr(module, 'description') \
                            else _('No description available.'),
                    ))

                self.wtree.get_object('label-module-author-value').set_label(
                    '\n'.join(module.authors if hasattr(module, 'authors') \
                        else __authors__))
                self.wtree.get_object('label-module-website-value').set_label(
                    '<a href="%s">%s</a>' % (module.website, module.website))

                # Display module information
                self.wtree.get_object('viewport-module').show()
            else:
                # Hide module information
                self.wtree.get_object('viewport-module').hide()

        # Set reset button sensitivity
        self.wtree.get_object('button-pref-reset').set_sensitive(pagenum == 0)

    def update_target_tags(self, source=None, event=None):
        """
        Update target GtkTextBuffer highlighting
            void update_target_tags(event source: gtk.Object,
                                    event: gtk.gdk.Event)
        """

        # Set updating flag and undo stack lock
        self.updating = True
        self.tbuffer.set_stack_lock(True)

        # Save selection or cursor position
        if self.tbuffer.get_has_selection():
            start, end = self.tbuffer.get_selection_bounds()
            saved = (start.get_offset(), end.get_offset())
        else:
            saved = self.tbuffer.get_iter_at_mark(self.tbuffer.get_insert()).\
                get_offset()

        # Reset target GtkTextBuffer text
        self.tbuffer.set_text('')

        # Check target chunks
        count = 0
        first = True
        last = None

        for m in self.match:
            # Skip empty chunks
            if m.start() == m.end():
                continue

            # Append begin chunk if needed
            if self.tbuffer.get_char_count() == 0 and m.start() != 0:
                self.tbuffer.insert(self.tbuffer.get_end_iter(),
                    self.target[:m.start()])

            # Append chunk present between two matches
            if m.start() == last:
                pass
            elif last:
                self.tbuffer.insert(self.tbuffer.get_end_iter(),
                    self.target[last:m.start()])

            # Append chunk with tags
            self.tbuffer.insert_with_tags_by_name(self.tbuffer.get_end_iter(),
                self.target[m.start():m.end()], 'match-first' if first \
                    else 'match-next')

            if first:
                first = False

            last = m.end()
            count += 1

            # Stop if limit reached
            if count == self.limit:
                break

        # Append end chunk if needed
        if last != len(self.target):
            self.tbuffer.insert(self.tbuffer.get_end_iter(),
                self.target[last:])

        # Restore selection or cursor position
        if type(saved) == tuple:
            self.tbuffer.select_range(self.tbuffer.get_iter_at_offset(
                saved[0]), self.tbuffer.get_iter_at_offset(saved[1]))
        else:
            self.tbuffer.place_cursor(self.tbuffer.get_iter_at_offset(saved))

        # Set statusbar matches count
        self.wtree.get_object('statusbar').pop(0)
        self.wtree.get_object('statusbar').push(0, gettext.dngettext(
            __cmdname__, '%d match found', '%d matches found', count) % count)

        # Reset updating flag and undo stack lock
        self.updating = False
        self.tbuffer.set_stack_lock(False)

    def update_statusbar_state(self, source=None, event=None):
        """
        Update statusbar state according to option
            void update_statusbar_state(event source: gtk.Object,
                                        event: gtk.gdk.Event)
        """

        # Update widget visibility
        self.wtree.get_object('statusbar').set_visible(self.wtree.get_object(
            'menuitem-view-statusbar').get_active())
