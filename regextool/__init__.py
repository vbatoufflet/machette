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
from regextool.path import DATA_DIR, LOCALE_DIR
from regextool.config import RegexToolConfig

pygtk.require('2.0')

class RegexTool:
	def __init__(self):
		"""
		Initialize RegexTool instance
			RegexTool __init__(void)
		"""

		# Initialize i18n support
		gettext.bindtextdomain(__shortname__, LOCALE_DIR)
		locale.bindtextdomain(__shortname__, LOCALE_DIR)

		__builtins__['_'] = gettext.gettext

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
		self.config = RegexToolConfig()
		self.flags = 0
		self.limit = 1
		self.match = list()
		self.target = ''
		self.updating = False

		# Initialize GtkTextBuffer buffers
		self.rbuffer = self.wtree.get_object('textview-regex').get_buffer()
		self.tbuffer = self.wtree.get_object('textview-target').get_buffer()
		self.set_target_tags()

		# Connect signals
		self.rbuffer.connect('changed', self.check_pattern)
		self.tbuffer.connect('changed', self.check_pattern)
		self.wtree.get_object('checkbutton-option-g').connect('toggled', self.check_pattern)
		self.wtree.get_object('checkbutton-option-i').connect('toggled', self.check_pattern)
		self.wtree.get_object('checkbutton-option-l').connect('toggled', self.check_pattern)
		self.wtree.get_object('checkbutton-option-m').connect('toggled', self.check_pattern)
		self.wtree.get_object('checkbutton-option-s').connect('toggled', self.check_pattern)
		self.wtree.get_object('checkbutton-option-u').connect('toggled', self.check_pattern)
		self.wtree.get_object('checkbutton-option-x').connect('toggled', self.check_pattern)
		self.wtree.get_object('combobox-split-delimiter').connect('changed', self.update_split_tab)
		self.wtree.get_object('menuitem-edit-pref').connect('activate', self.show_pref_dialog)
		self.wtree.get_object('menuitem-file-import').connect('activate', self.import_from_file)
		self.wtree.get_object('menuitem-file-quit').connect('activate', self.quit)
		self.wtree.get_object('menuitem-help-about').connect('activate', self.show_about_dialog)
		self.wtree.get_object('menuitem-view-advanced').connect('toggled', self.update_advanced_state)
		self.wtree.get_object('menuitem-view-statusbar').connect('toggled', self.update_statusbar_state)
		self.wtree.get_object('spinbutton-group-index').connect('value-changed', self.update_group_tab)
		self.wtree.get_object('textview-regex').connect('key-press-event', self.switch_focus)
		self.wtree.get_object('textview-replace-string').connect('key-press-event', self.switch_focus)
		self.wtree.get_object('textview-replace-string').get_buffer().connect('changed', self.update_replace_tab)
		self.wtree.get_object('textview-target').connect('key-press-event', self.switch_focus)
		self.wtree.get_object('vbox-group').connect('map', self.check_pattern)
		self.wtree.get_object('vbox-replace').connect('map', self.check_pattern)
		self.wtree.get_object('vbox-split').connect('map', self.check_pattern)
		self.wtree.get_object('window-main').connect('destroy', self.quit)
	
	def check_pattern(self, source=None, event=None):
		"""
		Check for regular expression pattern
			void check_pattern(event source: gtk.Object, event: gtk.gdk.Event)
		"""

		# Stop if updating is active
		if self.updating:
			return

		# Hide error message
		self.wtree.get_object('statusbar').pop(1)

		# Reset GtkTextBuffers texts
		self.wtree.get_object('textview-replace-result').get_buffer().set_text('')
		self.wtree.get_object('textview-split-result').get_buffer().set_text('')

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
			self.regex = re.compile(self.rbuffer.get_text(self.rbuffer.get_start_iter(), self.rbuffer.get_end_iter()), self.flags)
			self.target = self.tbuffer.get_text(self.tbuffer.get_start_iter(), self.tbuffer.get_end_iter())

			# Get MatchObject list
			for i in self.regex.finditer(self.target):
				self.match.append(i)

			# Update target GtkTextBuffer highlighting
			self.update_target_tags(source)

			# Check for additional updates
			if self.wtree.get_object('treeview-group').get_child_visible():
				# Update group tab
				self.update_group_tab(source, event)
			if self.wtree.get_object('vbox-replace').get_child_visible():
				# Update replace tab
				self.update_replace_tab(source, event)
			if self.wtree.get_object('vbox-split').get_child_visible():
				# Update split tab
				self.update_split_tab(source, event)
		except ( IndexError, re.error ), e:
			# Display error message in status bar
			self.wtree.get_object('statusbar').push(1, _('Error: %s') % e.message)

	def import_from_file(self, source=None, event=None):
		"""
		Import target string from a file
			void import_from_file(event source: gtk.Object, event: gtk.gdk.Event)
		"""

		filepath = None

		# Create GtkFileChooserDialog
		dialog = gtk.FileChooserDialog(_('Import data from file...'), None, gtk.FILE_CHOOSER_ACTION_OPEN, (
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

		# Confirm if buffer has data
		if filepath:
			if self.tbuffer.get_char_count() != 0:
				message = gtk.MessageDialog(None, 0, gtk.MESSAGE_QUESTION, gtk.BUTTONS_YES_NO)
				message.set_markup(_('Your are about to replace the existing target string. Are you sure?'))

				action = message.run()
				if action == gtk.RESPONSE_NO: filepath = None
				message.destroy()

			if filepath:
				# Load target string from file
				fd = open(filepath, 'r')
				self.tbuffer.set_text(fd.read())
				fd.close()

	def main(self):
		"""
		Run the GTK main loop
			void main(void)
		"""

		# Initialize group GtkTreeView
		render = gtk.CellRendererText()

		treeview = self.wtree.get_object('treeview-group')
		treeview.get_column(0).pack_start(render, False)
		treeview.get_column(0).add_attribute(render, 'text', 0)
		treeview.get_column(1).pack_start(render, False)
		treeview.get_column(1).add_attribute(render, 'text', 1)
		treeview.get_column(2).pack_start(render, False)
		treeview.get_column(2).add_attribute(render, 'text', 2)

		# Initialize split delimiter GtkComboBox
		for delim in [ '|', '#', '@', unichr(0xb6), unichr(0x25a0) ]:
			self.wtree.get_object('combobox-split-delimiter').append_text(delim)

		# Restore last state
		self.rbuffer.set_text(self.config.get('data', 'textview-regex'))
		self.tbuffer.set_text(self.config.get('data', 'textview-target'))
		self.wtree.get_object('checkbutton-option-g').set_active(self.config.get('window', 'option-g-active'))
		self.wtree.get_object('checkbutton-option-i').set_active(self.config.get('window', 'option-i-active'))
		self.wtree.get_object('checkbutton-option-l').set_active(self.config.get('window', 'option-l-active'))
		self.wtree.get_object('checkbutton-option-m').set_active(self.config.get('window', 'option-m-active'))
		self.wtree.get_object('checkbutton-option-s').set_active(self.config.get('window', 'option-s-active'))
		self.wtree.get_object('checkbutton-option-u').set_active(self.config.get('window', 'option-u-active'))
		self.wtree.get_object('checkbutton-option-x').set_active(self.config.get('window', 'option-x-active'))
		self.wtree.get_object('combobox-split-delimiter').set_active(self.config.get('window', 'split-delimiter'))
		self.wtree.get_object('menuitem-view-advanced').set_active(self.config.get('window', 'show-advanced'))
		self.wtree.get_object('menuitem-view-statusbar').set_active(self.config.get('window', 'show-statusbar'))
		self.wtree.get_object('vpaned1').set_position(self.config.get('window', 'pane-position1'))
		self.wtree.get_object('vpaned2').set_position(self.config.get('window', 'pane-position2'))
		self.wtree.get_object('window-main').set_default_size(self.config.get('window', 'width'), self.config.get('window', 'height'))

		# Update view states
		self.update_advanced_state()
		self.update_statusbar_state()

		# Set main window visible and enter GTK main loop
		self.wtree.get_object('window-main').show()
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
			self.config.set('data', 'textview-regex', self.rbuffer.get_text(self.rbuffer.get_start_iter(), self.rbuffer.get_end_iter()))
			self.config.set('data', 'textview-target', self.tbuffer.get_text(self.tbuffer.get_start_iter(), self.tbuffer.get_end_iter()))
			self.config.set('window', 'height', self.wtree.get_object('window-main').get_allocation().height)
			self.config.set('window', 'option-g-active', self.wtree.get_object('checkbutton-option-g').get_active())
			self.config.set('window', 'option-i-active', self.wtree.get_object('checkbutton-option-i').get_active())
			self.config.set('window', 'option-l-active', self.wtree.get_object('checkbutton-option-l').get_active())
			self.config.set('window', 'option-m-active', self.wtree.get_object('checkbutton-option-m').get_active())
			self.config.set('window', 'option-s-active', self.wtree.get_object('checkbutton-option-s').get_active())
			self.config.set('window', 'option-u-active', self.wtree.get_object('checkbutton-option-u').get_active())
			self.config.set('window', 'option-x-active', self.wtree.get_object('checkbutton-option-x').get_active())
			self.config.set('window', 'pane-position1', self.wtree.get_object('vpaned1').get_position())
			self.config.set('window', 'pane-position2', self.wtree.get_object('vpaned2').get_position())
			self.config.set('window', 'show-advanced', self.wtree.get_object('menuitem-view-advanced').get_active())
			self.config.set('window', 'show-statusbar', self.wtree.get_object('menuitem-view-statusbar').get_active())
			self.config.set('window', 'split-delimiter', self.wtree.get_object('combobox-split-delimiter').get_active())
			self.config.set('window', 'width', self.wtree.get_object('window-main').get_allocation().width)

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
			if not self.tbuffer.get_tag_table().lookup(name):
				self.tbuffer.create_tag(name)

			# Set background property
			self.tbuffer.get_tag_table().lookup(name).set_property('background', gtk.gdk.color_parse(self.config.get('color', name)))
	
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

	def update_advanced_state(self, source=None, event=None):
		"""
		Update advanced panel state according to option
			void update_advanced_state(event source: gtk.Object, event: gtk.gdk.Event)
		"""

		# Get previous state
		previous = self.config.get('window', 'show-advanced')

		# Update configuration option value
		self.config.set('window', 'show-advanced', self.wtree.get_object('menuitem-view-advanced').get_active())

		# Resize window when status change
		if previous != self.config.get('window', 'show-advanced'):
			self.wtree.get_object('window-main').resize(
				self.wtree.get_object('window-main').get_allocation().width,
				(self.wtree.get_object('window-main').get_allocation().height
				- self.wtree.get_object('notebook-advanced').get_allocation().height),
			)

		# Update widgets visibility
		self.wtree.get_object('notebook-advanced').set_visible(self.config.get('window', 'show-advanced'))

	def update_group_tab(self, source=None, event=None):
		"""
		Update group GtkNotebook tab
			void update_group_tab(event source: gtk.Object, event: gtk.gdk.Event)
		"""

		# Get GtkSpinButton
		spinbutton = self.wtree.get_object('spinbutton-group-index')

		# Update GtkSpinButton adjustment
		if type(source) != gtk.SpinButton:
			spinbutton.set_adjustment(gtk.Adjustment(1, 1, len(self.match), 1, 1, 0))

		# Get GtkListStore
		liststore = self.wtree.get_object('liststore-group')

		# Clear previous entries
		liststore.clear()

		# Append new groups
		count = 1
		groups = dict(map(lambda a: (a[1], a[0]), self.regex.groupindex.items()))
		index = int(spinbutton.get_value())-1

		# Stop if no match or groups
		if len(self.match) == 0 or not self.match[index].groups():
			spinbutton.set_sensitive(False)
			spinbutton.set_value(1)
			return
		else:
			spinbutton.set_sensitive(True)

		for g in self.match[index].groups():
			liststore.append([ count, groups[count] if count in groups else '', g ])
			count += 1

	def update_replace_tab(self, source=None, event=None):
		"""
		Update replace GtkNotebook tab
			void update_replace_tab(event source: gtk.Object, event: gtk.gdk.Event)
		"""

		cbuffer = self.wtree.get_object('textview-replace-string').get_buffer()

		# Stop if replacement string is empty
		if cbuffer.get_char_count() == 0:
			self.wtree.get_object('textview-replace-result').get_buffer().set_text(self.target)
			return

		try:
			self.wtree.get_object('textview-replace-result').get_buffer().set_text(self.regex.sub(
				cbuffer.get_text(cbuffer.get_start_iter(), cbuffer.get_end_iter()),
				self.target,
				self.limit,
			))
		except ( IndexError, re.error ), e:
			# Display error message in status bar
			self.wtree.get_object('statusbar').push(1, _('Error: %s') % e.message)
	
	def update_split_tab(self, source=None, event=None):
		"""
		Update split GtkNotebook tab
			void update_split_tab(event source: gtk.Object, event: gtk.gdk.Event)
		"""

		delimiter = self.wtree.get_object('combobox-split-delimiter').get_active_text()

		try:
			# Get split chunks
			regex = re.compile(self.rbuffer.get_text(self.rbuffer.get_start_iter(), self.rbuffer.get_end_iter()), self.flags)
			self.wtree.get_object('textview-split-result').get_buffer().set_text(delimiter.join(regex.split(self.target, self.limit)))
		except ( IndexError, re.error ), e:
			# Display error message in status bar
			self.wtree.get_object('statusbar').push(1, _('Error: %s') % e.message)
	
	def update_target_tags(self, source=None, event=None):
		"""
		Update target GtkTextBuffer highlighting
			void update_target_tags(event source: gtk.Object, event: gtk.gdk.Event)
		"""

		# Set updating flag
		self.updating = True

		# Save selection or cursor position
		if self.tbuffer.get_has_selection():
			start, end = self.tbuffer.get_selection_bounds()
			saved = ( start.get_offset(), end.get_offset() )
		else:
			saved = self.tbuffer.get_iter_at_mark(self.tbuffer.get_insert()).get_offset()

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
				self.tbuffer.insert(self.tbuffer.get_end_iter(), self.target[:m.start()])

			# Append chunk present between two matches
			if m.start() == last:
				pass
			elif last:
				self.tbuffer.insert(self.tbuffer.get_end_iter(), self.target[last:m.start()])

			# Append chunk with tags
			self.tbuffer.insert_with_tags_by_name(self.tbuffer.get_end_iter(), self.target[m.start():m.end()], 'match-first' if first else 'match-next')
			if first: first = False

			last = m.end()
			count += 1

			# Stop if limit reached
			if count == self.limit:
				break

		# Append end chunk if needed
		if last != len(self.target):
			self.tbuffer.insert(self.tbuffer.get_end_iter(), self.target[last:])

		# Restore selection or cursor position
		if type(saved) == tuple:
			self.tbuffer.select_range(self.tbuffer.get_iter_at_offset(saved[0]), self.tbuffer.get_iter_at_offset(saved[1]))
		else:
			self.tbuffer.place_cursor(self.tbuffer.get_iter_at_offset(saved))

		# Set statusbar matches count
		self.wtree.get_object('statusbar').push(0, gettext.dngettext(__shortname__, '%d match found', '%d matches found', count) % count)

		# Reset updating flag
		self.updating = False

	def update_statusbar_state(self, source=None, event=None):
		"""
		Update statusbar state according to option
			void update_statusbar_state(event source: gtk.Object, event: gtk.gdk.Event)
		"""

		# Update widget visibility
		self.wtree.get_object('statusbar').set_visible(self.wtree.get_object('menuitem-view-statusbar').get_active())
