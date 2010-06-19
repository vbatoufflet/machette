# -*- coding: utf-8 -*-
#
# This file is a part of Regex Tool.
#
# Copyright (c) 2010 Vincent Batoufflet <vincent@batoufflet.info>
# See LICENSE file for further details.
#
# $Id$

__fullname__ = 'An interactive regular expression tester'
__shortname__ = 'regextool'
__version__ = '0.1'

__author__ = 'Vincent Batoufflet'
__email__ = 'vincent@batoufflet.info'
__copyright__ = 'Copyright © 2010 Vincent Batoufflet'
__license__ = 'gpl3'

__website__ = 'http://thonpy.com/regextool/'

import gtk, pygtk
import getopt, gettext, locale, os, re, sys
from regextool.config import RegexToolConfig
from regextool.module import *
from regextool.path import DATA_DIR, LOCALE_DIR
from regextool.ui.undostack import UndoStack

pygtk.require('2.0')

class RegexTool:
	def __init__(self):
		"""
		Initialize RegexTool instance
			RegexTool __init__(void)
		"""

		# Initialize i18n support
		gettext.install(__shortname__, LOCALE_DIR)
		gettext.bindtextdomain(__shortname__, LOCALE_DIR)
		locale.bindtextdomain(__shortname__, LOCALE_DIR)

		# Parse command line arguments
		try:
			opts, args = getopt.getopt(sys.argv[1:], 'hv', [ 'help', 'version' ])
		except Exception, e:
			sys.stderr.write(_('Error: %s\n') % e)
			self.print_usage()
			sys.exit(1)

		for opt, arg in opts:
			if opt in [ '-h', '--help' ]:
				self.print_usage()
				sys.exit(0)
			elif opt in [ '-v', '--version' ]:
				self.print_version()
				sys.exit(0)

		# Load widgets from UI file
		self.wtree = gtk.Builder()
		self.wtree.set_translation_domain(__shortname__)
		self.wtree.add_from_file(os.path.join(DATA_DIR, 'ui/main.ui'))

		# Set instance attributes
		self.flags = 0
		self.limit = 1
		self.match = list()
		self.modules = dict()
		self.regex = None
		self.target = ''
		self.updating = False

		# Initialize GtkTextBuffer buffers
		self.regex_buffer = self.wtree.get_object('textview-regex').get_buffer()
		self.target_buffer = self.wtree.get_object('textview-target').get_buffer()

		# Connect signals
		self.regex_buffer.connect('changed', self.check_pattern)
		self.target_buffer.connect('changed', self.check_pattern)
		self.wtree.get_object('checkbutton-option-g').connect('toggled', self.check_pattern)
		self.wtree.get_object('checkbutton-option-i').connect('toggled', self.check_pattern)
		self.wtree.get_object('checkbutton-option-l').connect('toggled', self.check_pattern)
		self.wtree.get_object('checkbutton-option-m').connect('toggled', self.check_pattern)
		self.wtree.get_object('checkbutton-option-s').connect('toggled', self.check_pattern)
		self.wtree.get_object('checkbutton-option-u').connect('toggled', self.check_pattern)
		self.wtree.get_object('checkbutton-option-x').connect('toggled', self.check_pattern)
		self.wtree.get_object('menuitem-edit-pref').connect('activate', self.show_pref_dialog)
		self.wtree.get_object('menuitem-file-export').connect('activate', self.export_to_file)
		self.wtree.get_object('menuitem-file-import').connect('activate', self.import_from_file)
		self.wtree.get_object('menuitem-file-quit').connect('activate', self.quit)
		self.wtree.get_object('menuitem-help-about').connect('activate', self.show_about_dialog)
		self.wtree.get_object('menuitem-view-extension').connect('toggled', self.update_extension_state)
		self.wtree.get_object('menuitem-view-statusbar').connect('toggled', self.update_statusbar_state)
		self.wtree.get_object('textview-regex').connect('key-press-event', self.switch_focus)
		self.wtree.get_object('textview-target').connect('key-press-event', self.switch_focus)
		self.wtree.get_object('window-main').connect('destroy', self.quit)
		self.wtree.get_object('window-main').connect('map', self.check_pattern)

		# Load and initialize additionnal modules
		options = list()

		for name in get_modules_list():
			module = load_module(name, [ 'classname', 'options' ])
			self.modules[name] = getattr(module, module.classname)(self)

			if hasattr(module, 'options'):
				options.append(module.options)

		# Load configuration
		self.config = RegexToolConfig(options)

		# Register loaded modules
		for name in self.modules:
			self.modules[name].register()
	
	def check_pattern(self, source=None, event=None):
		"""
		Check for regular expression pattern
			void check_pattern(event source: gtk.Object, event: gtk.gdk.Event)
		"""

		# Stop if updating is active
		if self.updating:
			return

		# Hide error message
		if hasattr(self, 'message_id'):
			self.wtree.get_object('statusbar').remove_message(1, self.message_id)

		# Check for regular expression flags
		self.flags = 0
		self.limit = 1
		self.match = list()

		if self.wtree.get_object('checkbutton-option-g').get_active(): self.limit = 0
		if self.wtree.get_object('checkbutton-option-i').get_active(): self.flags |= re.I
		if self.wtree.get_object('checkbutton-option-l').get_active(): self.flags |= re.L
		if self.wtree.get_object('checkbutton-option-m').get_active(): self.flags |= re.M
		if self.wtree.get_object('checkbutton-option-s').get_active(): self.flags |= re.S
		if self.wtree.get_object('checkbutton-option-u').get_active(): self.flags |= re.U
		if self.wtree.get_object('checkbutton-option-x').get_active(): self.flags |= re.X

		# Check target string for pattern matching
		try:
			# Get regular expression iters
			self.regex = re.compile(self.regex_buffer.get_text(self.regex_buffer.get_start_iter(), self.regex_buffer.get_end_iter()), self.flags)
			self.target = self.target_buffer.get_text(self.target_buffer.get_start_iter(), self.target_buffer.get_end_iter())

			# Get MatchObject list
			for i in self.regex.finditer(self.target):
				self.match.append(i)

			# Update target GtkTextBuffer highlighting
			self.update_target_tags(source)
		except ( IndexError, re.error ), e:
			# Display error message in status bar
			self.message_id = self.wtree.get_object('statusbar').push(1, _('Error: %s') % e)

	def export_to_file(self, source=None, event=None):
		"""
		Export target string to a file
			void export_to_file(event source: gtk.Object, event: gtk.gdk.Event)
		"""

		filepath = None

		# Create GtkFileChooserDialog
		dialog = gtk.FileChooserDialog(_('Export to file...'), None, gtk.FILE_CHOOSER_ACTION_SAVE, (
			gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL,
			gtk.STOCK_SAVE, gtk.RESPONSE_OK,
		))

		dialog.set_default_response(gtk.RESPONSE_OK)

		action = dialog.run()
		if action == gtk.RESPONSE_OK: filepath = dialog.get_filename()
		dialog.destroy()

		if filepath:
			# Confirm if file already exists
			if os.path.exists(filepath):
				message = gtk.MessageDialog(None, 0, gtk.MESSAGE_WARNING, gtk.BUTTONS_YES_NO)
				message.set_markup(_('The destination file already exists. Are you sure?'))

				action = message.run()
				if action == gtk.RESPONSE_NO: filepath = None
				message.destroy()

			if filepath:
				# Load target string from file
				fd = open(filepath, 'w')
				fd.write(self.target_buffer.get_text(self.target_buffer.get_start_iter(), self.target_buffer.get_end_iter()))
				fd.close()

	def import_from_file(self, source=None, event=None):
		"""
		Import target string from a file
			void import_from_file(event source: gtk.Object, event: gtk.gdk.Event)
		"""

		filepath = None

		# Create GtkFileChooserDialog
		dialog = gtk.FileChooserDialog(_('Import from file...'), None, gtk.FILE_CHOOSER_ACTION_OPEN, (
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
		if action == gtk.RESPONSE_OK: filepath = dialog.get_filename()
		dialog.destroy()

		if filepath:
			# Confirm if buffer has data
			if self.target_buffer.get_char_count() != 0:
				message = gtk.MessageDialog(None, 0, gtk.MESSAGE_QUESTION, gtk.BUTTONS_YES_NO)
				message.set_markup(_('Your are about to replace the existing target string. Are you sure?'))

				action = message.run()
				if action == gtk.RESPONSE_NO: filepath = None
				message.destroy()

			if filepath:
				# Load target string from file
				fd = open(filepath, 'r')
				self.target_buffer.set_text(fd.read())
				fd.close()

	def main(self):
		"""
		Run the GTK main loop
			void main(void)
		"""

		# Set updating flag
		self.updating = True

		# Restore last state
		self.regex_buffer.set_text(self.config.get('data', 'textview-regex'))
		self.target_buffer.set_text(self.config.get('data', 'textview-target'))
		self.wtree.get_object('checkbutton-option-g').set_active(self.config.get('window', 'option-g-active'))
		self.wtree.get_object('checkbutton-option-i').set_active(self.config.get('window', 'option-i-active'))
		self.wtree.get_object('checkbutton-option-l').set_active(self.config.get('window', 'option-l-active'))
		self.wtree.get_object('checkbutton-option-m').set_active(self.config.get('window', 'option-m-active'))
		self.wtree.get_object('checkbutton-option-s').set_active(self.config.get('window', 'option-s-active'))
		self.wtree.get_object('checkbutton-option-u').set_active(self.config.get('window', 'option-u-active'))
		self.wtree.get_object('checkbutton-option-x').set_active(self.config.get('window', 'option-x-active'))
		self.wtree.get_object('menuitem-view-extension').set_active(self.config.get('window', 'show-extension'))
		self.wtree.get_object('menuitem-view-statusbar').set_active(self.config.get('window', 'show-statusbar'))
		self.wtree.get_object('notebook-extension').set_current_page(self.config.get('window', 'notebook-page'))
		self.wtree.get_object('vpaned1').set_position(self.config.get('window', 'pane-position1'))
		self.wtree.get_object('vpaned2').set_position(self.config.get('window', 'pane-position2'))
		self.wtree.get_object('window-main').set_default_size(self.config.get('window', 'width'), self.config.get('window', 'height'))

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
		if self.config.get('window', 'show-extension'):
			self.wtree.get_object('notebook-extension').get_nth_page(self.wtree.get_object('notebook-extension').get_current_page()).emit('map')

		# Enter GTK main loop
		gtk.main()

	def print_usage(self):
		"""
		Print program usage
			void print_usage(void)
		"""

		print(_('Usage: %s [OPTION]...') % __shortname__)
		print('')
		print(_('Options:'))
		print('   -h, --help     ' + _('display this help and exit'))
		print('   -v, --version  ' + _('display program version and exit'))
		
	def print_version(self):
		"""
		Print program version
			void print_version(void)
		"""

		print('regextool ' + __version__)

	def quit(self, source=None, event=None):
		"""
		Quit the GTK main loop
			void quit(event source: gtk.Object, event: gtk.gdk.Event)
		"""

		# Save state
		if self.config.get('window', 'save-state'):
			self.config.set('data', 'textview-regex', self.regex_buffer.get_text(self.regex_buffer.get_start_iter(), self.regex_buffer.get_end_iter()))
			self.config.set('data', 'textview-target', self.target_buffer.get_text(self.target_buffer.get_start_iter(), self.target_buffer.get_end_iter()))
			self.config.set('window', 'height', self.wtree.get_object('window-main').get_allocation().height)
			self.config.set('window', 'notebook-page', self.wtree.get_object('notebook-extension').get_current_page())
			self.config.set('window', 'option-g-active', self.wtree.get_object('checkbutton-option-g').get_active())
			self.config.set('window', 'option-i-active', self.wtree.get_object('checkbutton-option-i').get_active())
			self.config.set('window', 'option-l-active', self.wtree.get_object('checkbutton-option-l').get_active())
			self.config.set('window', 'option-m-active', self.wtree.get_object('checkbutton-option-m').get_active())
			self.config.set('window', 'option-s-active', self.wtree.get_object('checkbutton-option-s').get_active())
			self.config.set('window', 'option-u-active', self.wtree.get_object('checkbutton-option-u').get_active())
			self.config.set('window', 'option-x-active', self.wtree.get_object('checkbutton-option-x').get_active())
			self.config.set('window', 'pane-position1', self.wtree.get_object('vpaned1').get_position())
			self.config.set('window', 'pane-position2', self.wtree.get_object('vpaned2').get_position())
			self.config.set('window', 'show-extension', self.wtree.get_object('menuitem-view-extension').get_active())
			self.config.set('window', 'show-statusbar', self.wtree.get_object('menuitem-view-statusbar').get_active())
			self.config.set('window', 'width', self.wtree.get_object('window-main').get_allocation().width)

		# Unregister loaded modules
		for name in self.modules:
			self.modules[name].unregister()

		# Save configuration options
		self.config.save()

		# Stop GTK main loop
		gtk.main_quit()
	
	def set_target_tags(self):
		"""
		Set target GtkTextBuffer tags
			void set_target_tags(void)
		"""

		for name in [ 'match-first', 'match-next' ]:
			# Create new tag if needed
			if not self.target_buffer.get_tag_table().lookup(name):
				self.target_buffer.create_tag(name)

			# Set background property
			self.target_buffer.get_tag_table().lookup(name).set_property('background', gtk.gdk.color_parse(self.config.get('color', name)))
	
	def show_about_dialog(self, source=None, event=None):
		"""
		Create and/or display about window
			bool show_about_dialog(event source: gtk.Object, event: gtk.gdk.Event)
		"""

		# Create GtkAboutDialog if needed
		if not hasattr(self, 'about_dialog'):
			# Create GtkAboutDialog
			self.about_dialog = gtk.AboutDialog()

			# Set base information
			self.about_dialog.set_name(__shortname__)
			self.about_dialog.set_version(__version__)
			self.about_dialog.set_comments(__fullname__)
			self.about_dialog.set_copyright(__copyright__)
			self.about_dialog.set_website(__website__)

			# Load information from external files
			try:
				fd = open(os.path.join(DATA_DIR, 'LICENSE'))
				self.about_dialog.set_license(fd.read())
				fd.close()
			except IOError, e:
				self.about_dialog.set_license(_('Error: unable to load LICENSE file'))

			try:
				fd = open(os.path.join(DATA_DIR, 'AUTHORS'))
				self.about_dialog.set_authors(fd.read().splitlines())
				fd.close()
			except IOError, e:
				self.about_dialog.set_authors([ _('Error: unable to load AUTHORS file') ])

			try:
				fd = open(os.path.join(DATA_DIR, 'TRANSLATORS'))
				self.about_dialog.set_translator_credits(fd.read())
				fd.close()
			except IOError, e:
				self.about_dialog.set_translator_credits([ _('Error: unable to load TRANSLATORS file') ])

		# Set dialog visible and wait for closing
		self.about_dialog.run()
		self.about_dialog.hide()
	
	def show_pref_dialog(self, source=None, event=None):
		"""
		Create and/or display preferences window
			bool show_pref_dialog(event source: gtk.Object, event: gtk.gdk.Event)
		"""

		# Load window if needed
		if not hasattr(self, 'pref_dialog'):
			self.wtree.add_from_file(os.path.join(DATA_DIR, 'ui/pref.ui'))
			self.pref_window = self.wtree.get_object('dialog-pref')
			self.pref_window.set_modal(True)
			self.pref_window.set_position(gtk.WIN_POS_CENTER_ON_PARENT)
			self.pref_window.set_resizable(False)
			self.pref_window.set_type_hint(gtk.gdk.WINDOW_TYPE_HINT_DIALOG)

		# Update preferences window state
		self.wtree.get_object('checkbutton-window-save-state').set_active(self.config.get('window', 'save-state'))
		self.wtree.get_object('colorbutton-color-first').set_color(gtk.gdk.color_parse(self.config.get('color', 'match-first')))
		self.wtree.get_object('colorbutton-color-next').set_color(gtk.gdk.color_parse(self.config.get('color', 'match-next')))

		# Set dialog visible and wait for action
		action = None

		while not action:
			# Wait for action
			action = self.pref_window.run()

			if action == 1:
				# Set new preferences values
				self.config.set('color', 'match-first', self.wtree.get_object('colorbutton-color-first').get_color().to_string())
				self.config.set('color', 'match-next', self.wtree.get_object('colorbutton-color-next').get_color().to_string())
				self.config.set('window', 'save-state', self.wtree.get_object('checkbutton-window-save-state').get_active())

				# Update target GtkTextBuffer tags
				self.set_target_tags()
			elif action == 2:
				# Cancel preferences changes
				pass
			elif action == 3:
				# Update preferences window state with defaults
				self.wtree.get_object('checkbutton-window-save-state').set_active(self.config.get_default('window', 'save-state'))
				self.wtree.get_object('colorbutton-color-first').set_color(gtk.gdk.color_parse(self.config.get_default('color', 'match-first')))
				self.wtree.get_object('colorbutton-color-next').set_color(gtk.gdk.color_parse(self.config.get_default('color', 'match-next')))

				# Cancel action value
				action = None

			# Close preferences dialog
			if action:
				self.pref_window.hide()

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

			if focus.get_name() != 'GtkTextView' or ( hasattr(focus, 'get_editable') and not focus.get_editable() ):
				self.switch_focus(source, event)

			return True

	def update_extension_state(self, source=None, event=None):
		"""
		Update extension panel state according to option
			void update_extension_state(event source: gtk.Object, event: gtk.gdk.Event)
		"""

		# Get previous state
		previous = self.config.get('window', 'show-extension')

		# Update configuration option value
		self.config.set('window', 'show-extension', self.wtree.get_object('menuitem-view-extension').get_active())

		# Resize window when status change
		if previous != self.config.get('window', 'show-extension'):
			self.wtree.get_object('window-main').resize(
				self.wtree.get_object('window-main').get_allocation().width,
				(self.wtree.get_object('window-main').get_allocation().height
				- self.wtree.get_object('notebook-extension').get_allocation().height),
			)

		# Update widgets visibility
		self.wtree.get_object('notebook-extension').set_visible(self.config.get('window', 'show-extension'))

	def update_target_tags(self, source=None, event=None):
		"""
		Update target GtkTextBuffer highlighting
			void update_target_tags(event source: gtk.Object, event: gtk.gdk.Event)
		"""

		# Set updating flag and undo stack lock
		self.updating = True
		self.target_buffer.set_stack_lock(True)

		# Save selection or cursor position
		if self.target_buffer.get_has_selection():
			start, end = self.target_buffer.get_selection_bounds()
			saved = ( start.get_offset(), end.get_offset() )
		else:
			saved = self.target_buffer.get_iter_at_mark(self.target_buffer.get_insert()).get_offset()

		# Reset target GtkTextBuffer text
		self.target_buffer.set_text('')

		# Check target chunks
		count = 0
		first = True
		last = None

		for m in self.match:
			# Skip empty chunks
			if m.start() == m.end():
				continue

			# Append begin chunk if needed
			if self.target_buffer.get_char_count() == 0 and m.start() != 0:
				self.target_buffer.insert(self.target_buffer.get_end_iter(), self.target[:m.start()])

			# Append chunk present between two matches
			if m.start() == last:
				pass
			elif last:
				self.target_buffer.insert(self.target_buffer.get_end_iter(), self.target[last:m.start()])

			# Append chunk with tags
			self.target_buffer.insert_with_tags_by_name(self.target_buffer.get_end_iter(), self.target[m.start():m.end()], 'match-first' if first else 'match-next')
			if first: first = False

			last = m.end()
			count += 1

			# Stop if limit reached
			if count == self.limit:
				break

		# Append end chunk if needed
		if last != len(self.target):
			self.target_buffer.insert(self.target_buffer.get_end_iter(), self.target[last:])

		# Restore selection or cursor position
		if type(saved) == tuple:
			self.target_buffer.select_range(self.target_buffer.get_iter_at_offset(saved[0]), self.target_buffer.get_iter_at_offset(saved[1]))
		else:
			self.target_buffer.place_cursor(self.target_buffer.get_iter_at_offset(saved))

		# Set statusbar matches count
		self.wtree.get_object('statusbar').push(0, gettext.dngettext(__shortname__, '%d match found', '%d matches found', count) % count)

		# Reset updating flag and undo stack lock
		self.updating = False
		self.target_buffer.set_stack_lock(False)

	def update_statusbar_state(self, source=None, event=None):
		"""
		Update statusbar state according to option
			void update_statusbar_state(event source: gtk.Object, event: gtk.gdk.Event)
		"""

		# Update widget visibility
		self.wtree.get_object('statusbar').set_visible(self.wtree.get_object('menuitem-view-statusbar').get_active())
