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

import gobject, gtk

class UndoStack:
	def __init__(self, textview, limit=256):
		"""
		Initialize UndoStack instance
			UndoStack __init__(textview instance: gtk.TextView)
		"""

		# Set instance attributes
		self.textview = textview
		self.limit = limit
		self.action = None
		self.buffer = textview.get_buffer()
		self.data = ''
		self.lastoffset = 0
		self.lock = False
		self.start = None
		self.timeout = None

		# Initialize stacks
		self.redostack = list()
		self.undostack = list()

		# Attach functions
		self.buffer.undo = self._undo
		self.buffer.redo = self._redo
		self.buffer.set_stack_lock = self._set_stack_lock

		# Connect signals
		self.textview.connect('key-press-event', self._handle_keybinding)
		self.buffer.connect('begin-user-action', self._start_timeout)
		self.buffer.connect('end-user-action', self._end_action)
		self.buffer.connect('delete-range', self._delete_range)
		self.buffer.connect('insert-text', self._insert_text)
		self.buffer.connect('redo-event', self._redo)
		self.buffer.connect('undo-event', self._undo)

	def _delete_range(self, source=None, start=None, end=None):
		"""
		Handle text range deletion
			void _delete_range(event source: gtk.Object, start iter: gtk.TextIter, end iter: gtk.TextIter)
		"""

		if self.lock:
			return

		if self.action and self.action != 'delete':
			self._stop_timeout()

		# Do deletion
		self.action = 'delete'

		if start.get_offset() == self.lastoffset-1:
			self.data = source.get_text(start, end) + self.data
		else:
			self.data += source.get_text(start, end)

		# Set start offset when needed
		if not self.start:
			self.start = start.get_offset()

		self.lastoffset = start.get_offset()
	
	def _end_action(self, source=None, event=None):
		"""
		End an user action
			void _end_action(event source: gtk.Object, event: gtk.gdk.Event)
		"""

		if self.timeout or self.start == None:
			return

		# Merge with last action if needed
		if len(self.undostack) > 0 and self.undostack[-1][0] == self.action and self.start == self.undostack[-1][1] + len(self.undostack[-1][2]):
			item = self.undostack.pop()
			self.start = item[1]
			self.data = item[2] + self.data

		# Append action to undo stack
		self.undostack.append([ self.action, self.start, self.data ])

		# Remove old action when stack limit is reached
		if len(self.undostack) > self.limit:
			self.undostack.pop(0)

		# Reset redo stack
		self.redostack = list()

		# Reset action data
		self.data = ''
		self.action = None
		self.start = None
	
	def _handle_keybinding(self, source=None, event=None):
		"""
		Register an user action
			void _handle_keybinding(event source: gtk.Object, event: gtk.gdk.Event)
		"""

		# Handle undo/redo keybindings
		if event.state & gtk.gdk.CONTROL_MASK:
			if gtk.gdk.keyval_name(event.keyval) == 'z':
				self.buffer.emit('undo-event')
			elif gtk.gdk.keyval_name(event.keyval) == 'y':
				self.buffer.emit('redo-event')

	def _insert_text(self, source=None, start=None, text=None, length=None):
		"""
		Handle text insertions
			void _insert_text(event source: gtk.Object, start iter: gtk.TextIter, inserted text: str, text length: int)
		"""

		if self.lock:
			return

		if self.action and self.action != 'insert':
			self._stop_timeout()

		# Do insertion
		self.action = 'insert'
		self.data += text

		# Set start offset when needed
		if self.start == None:
			self.start = start.get_offset()

	def _redo(self, source=None, event=None):
		"""
		Redo last action
			void redo(event source: gtk.Object, event: gtk.gdk.Event)
		"""

		if len(self.redostack) == 0:
			return

		self.lock = True

		# Get last action from stack
		item = self.redostack.pop()

		if item[0] == 'delete':
			self.buffer.delete(self.buffer.get_iter_at_offset(item[1]), self.buffer.get_iter_at_offset(item[1] + len(item[2])))
		elif item[0] == 'insert':
			self.buffer.insert(self.buffer.get_iter_at_offset(item[1]), item[2])

		# Append last action to undo stack
		self.undostack.append(item)

		self.lock = False
	
	def _set_stack_lock(self, lock):
		"""
		Set undo stack lock
			void set_stack_lock(lock flag: bool)
		"""

		# Set lock flag
		self.lock = lock
	
	def _start_timeout(self, source=None, event=None):
		"""
		Start user action timeout
			void _start_timeout(event source: gtk.Object, event: gtk.gdk.Event)
		"""

		# Relaunch existing timeout
		if self.timeout:
			gobject.source_remove(self.timeout)

		self.timeout = gobject.timeout_add(300, self._stop_timeout)

	def _stop_timeout(self, source=None, event=None):
		"""
		Stop user action timeout
			void _stop_timeout(event source: gtk.Object, event: gtk.gdk.Event)
		"""

		if self.timeout:
			gobject.source_remove(self.timeout)
			self.timeout = None

		self.buffer.emit('end-user-action')

	def _undo(self, source=None, event=None):
		"""
		Undo last action
			void undo(event source: gtk.Object, event: gtk.gdk.Event)
		"""

		if len(self.undostack) == 0:
			return

		self.lock = True

		# Get last action from stack
		item = self.undostack.pop()

		if item[0] == 'delete':
			self.buffer.insert(self.buffer.get_iter_at_offset(item[1]), item[2])
		elif item[0] == 'insert':
			self.buffer.delete(self.buffer.get_iter_at_offset(item[1]), self.buffer.get_iter_at_offset(item[1] + len(item[2])))

		# Append last action to redo stack
		self.redostack.append(item)

		self.lock = False

# Create new GtkTextBuffer signals
gobject.signal_new('redo-event', gtk.TextBuffer, gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE, ())
gobject.signal_new('undo-event', gtk.TextBuffer, gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE, ())
