# SPDX-License-Identifier: GPL-2.0-or-later
#
#  nautilus-btrfs/nautilus-btrfs.py
#
#  Copyright (C) 2023 Marko Petrović <petrovicmarko2006@gmail.com>

import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Nautilus, GObject, Gio, Gtk, GLib
import subprocess
import os

"""
handler(addition, EntryList, response_id/entry):bool - function called when an
event in dialog occurs.
Parameters:
1) addition - handler-specific information initially passed to the class
              constructor. Can be None.
2) EntryList - List of all Gtk.Entries in the dialog
3) response_id/entry - identificator of the thing that caused handler to be
                       invoked.
Return value:
True  - Dialog should be destroyed after handler finishes execution
False - Dialog should remain open after handler finishes execution

Useful methods:
add_button(button_text, response_id)
add_new_entry()
"""
dialog_list = []
class DialogBox(Gtk.Dialog):
	def __init__(self, title:str, handler, addition):
		super().__init__(modal=True, title=title)
		self.handler = handler
		self.addition = addition
		self.entries = []
		self.connect("response", self._button_handle_signal)
		self._add_reference()

	def _add_reference(self):
		global dialog_list
		for i in range(len(dialog_list)):
			if dialog_list[i] == None:
				dialog_list[i] = self
				self.reference = i
				return
		dialog_list.append(self)
		self.reference = len(dialog_list)-1

	def add_new_entry(self):
		box = self.get_content_area()
		entry = Gtk.Entry()
		box.append(entry)
		self.entries.append(entry)
		entry.connect("activate", self._entry_handle_signal)

	def _button_handle_signal(self, dialog:Gtk.Dialog, response_id:int):
		if self.handler(self.addition, self.entries, response_id) == True:
			dialog_list[self.reference] = None
			self.destroy()
	
	def _entry_handle_signal(self, entry:Gtk.Entry):
		if self.handler(self.addition, self.entries, entry) == True:
			dialog_list[self.reference] = None
			self.destroy()

"""
handler(process:helper_subprocess, arg:str) - A function that is called each time when the subprocess writes something
                              				  to the stdout if the subprocess is started with the start_async().
		1) arg - string which subprocess wrote to stdout
		2) process - a handler to the calling instance of helper_subprocess class

Methods:
start_sync(cmd)  - Execute the command line given by the list of arguments, wait for it to finish and handle error codes
start_async(cmd) - Execute the command line given by the list of arguments, do not block but continue to execute the
				   main loop and execute the given handler to handle any output from the program (or it's termination)
Public Variables:
helper_subprocess.data - initialized to None, can be set to anything and used by external functions

Warning: DO NOT use start_async() if the output of the program is expected to be larger than default pipe buffer (4096)
		 in the single write(2) call. It can lead to deadlocks.
"""
# Keep async process' class from being destroyed by garbage collector
async_process_list = []
class helper_subprocess:
	def __init__(self, handler):
		self.handler = handler
		self.data = None
		self.active_dialog_list = []
		self.stdout_channel = None
		self.stderr_channel = None
		self.watch_stdout_id = None
		self.watch_stderr_id = None

	def _destroy_dialog(self, dialog:Gtk.Dialog, response_id:int, destroy_object:bool):
		dialog.destroy()
		if destroy_object:
			self._clean_object()

	def _handle_OSError(self, helper_name):
		dialog = Gtk.MessageDialog(
			modal=True,
			buttons=Gtk.ButtonsType.OK_CANCEL,
			message_type=Gtk.MessageType.ERROR,
			text="Failed to complete the operation",
			secondary_text="Cannot launch helper program " + helper_name
		)
		dialog.connect("response", self._destroy_dialog, True)
		dialog.show()
		self._add_dialog_reference(dialog)

	def _handle_CalledProcessError(self, e:subprocess.CalledProcessError):
		errstring = e.stderr.decode()
		dialog = Gtk.MessageDialog(
			modal=True,
			buttons=Gtk.ButtonsType.OK_CANCEL,
			message_type=Gtk.MessageType.ERROR,
			text="Failed to complete the operation.",
			secondary_text=errstring
		)
		dialog.connect("response", self._destroy_dialog, True)
		dialog.show()
		self._add_dialog_reference(dialog)

	def start_sync(self, cmd):
		self._add_reference()
		try:
			completedProcess = subprocess.run(cmd, capture_output=True)
			completedProcess.check_returncode()
		except OSError:
			self._handle_OSError(cmd[0])
		except subprocess.CalledProcessError as e:
			self._handle_CalledProcessError(e)
		except ValueError:
			print("Popen called with invalid arguments")
		self._clean_object()
	
	def _clean_object(self):
		if self.watch_stdout_id != None:
			GLib.source_remove(self.watch_stdout_id)
		if self.watch_stderr_id != None:
			GLib.source_remove(self.watch_stderr_id)
		#if self.stderr_channel != None:
			#self.stderr_channel.unref()
			#self.stderr_channel.shutdown(False)
		#if self.stdout_channel != None:
			#self.stdout_channel.unref()
			#self.stdout_channel.shutdown(False)
		global async_process_list
		async_process_list[self.reference] = None

	def _add_reference(self):
		global async_process_list
		for i in range(len(async_process_list)):
			if async_process_list[i] == None:
				async_process_list[i] = self
				self.reference = i
				return
		async_process_list.append(self)
		self.reference = len(async_process_list)-1

	def _add_dialog_reference(self, dialog):
		self.active_dialog_list.append(dialog)

	def _invoke_helper(self, channel:GLib.IOChannel, condition):
		# Always return True, _clean_object will remove the watches
		if (condition & GLib.IO_NVAL) or (condition & GLib.IO_HUP):
			self._clean_object()
			#return False
		if condition & GLib.IO_IN:
			try:
				pipefd = channel.unix_get_fd()
				bstr = os.read(pipefd, 4096)
				str = bstr.decode()
				print(str)
				if str == "":
					ret = self.process.wait()
					if ret != 0:
						raise subprocess.CalledProcessError(ret, None, None, self.process.stderr.read())
					self._clean_object()
					#return False
				else:
					self.handler(self, str)
			except GLib.Error:
				print("Error GLIB")
				self._clean_object()
				#return False
			except subprocess.CalledProcessError as e:
				self._handle_CalledProcessError(e)
				#return False
		return True

	def _error_async(self, channel:GLib.IOChannel, condition):
		if condition & GLib.IO_IN:
			ret = self.process.wait()
			err = subprocess.CalledProcessError(ret, None, None, self.process.stderr.read())
			self._handle_CalledProcessError(err)
		# _handle_CalledProcessError will close the watch
		return True

	def start_async(self, cmd):
		try:
			self.process = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
			pipefd = self.process.stderr.fileno()
			self.stderr_channel = GLib.IOChannel.unix_new(pipefd)
			self.watch_stderr_id = self.stderr_channel.add_watch(GLib.IO_IN | GLib.IO_NVAL | GLib.IO_HUP, self._error_async)

			pipefd = self.process.stdout.fileno()
			self.stdout_channel = GLib.IOChannel.unix_new(pipefd)
			self.watch_stdout_id = self.stdout_channel.add_watch(GLib.IO_IN | GLib.IO_NVAL | GLib.IO_HUP, self._invoke_helper)
		except OSError:
			# Keep reference until OSError dialog closes
			self._add_reference()
			self._handle_OSError(cmd[0])
		except ValueError:
			print("Popen called with invalid arguments")
		self._add_reference()

#-----------------------------------------------------------------------
helper_path = "/usr/local/bin/nautilus-btrfs"
#-----------------------------------------------------------------------
def do_create_subvolume(addition, EntryList, event):
	# if (Enter is pressed in Entry) or (OK button is clicked)
	if isinstance(event, Gtk.Entry) or event == Gtk.ResponseType.OK:
		name = EntryList[0].get_text()
		current_folder = Gio.File.new_for_uri(addition.get_uri())
		cwd = current_folder.get_path()
		new_process = helper_subprocess(None)
		new_process.start_sync([helper_path, "createsubvol", cwd, name])
	return True
def create_subvolume(menuitem, cwd):
	dialog = DialogBox("Enter Subvolume Name", do_create_subvolume, cwd)
	dialog.add_button("OK", Gtk.ResponseType.OK)
	dialog.add_button("CANCEL", Gtk.ResponseType.CANCEL)
	dialog.add_new_entry()
	dialog.show()
#------------------------------------------------------------------------
def do_create_snapshot(addition, EntryList, event):
	# if (Enter is pressed in Entry) or (OK button is clicked)
	if isinstance(event, Gtk.Entry) or event == Gtk.ResponseType.OK:
		name = EntryList[0].get_text()
		source_folder = Gio.File.new_for_uri(addition.get_uri())
		source_path = source_folder.get_path()
		cwd = source_folder.get_parent().get_path()
		new_process = helper_subprocess(None)
		new_process.start_sync([helper_path, "create", "-p", source_path, cwd+"/"+name])
	return True
def create_snapshot(menuitem, file):
	dialog = DialogBox("Enter Snapshot Name", do_create_snapshot, file)
	dialog.add_button("OK", Gtk.ResponseType.OK)
	dialog.add_button("CANCEL", Gtk.ResponseType.CANCEL)
	dialog.add_new_entry()
	dialog.show()
#------------------------------------------------------------------------
dialog_ref = []
def add_dialog_reference(dialog:Gtk.MessageDialog):
	global dialog_ref
	for i in range(len(dialog_ref)):
		if dialog_ref[i] == None:
			dialog_ref[i] = dialog
			return i
	dialog_ref.append(dialog)
	return len(dialog_ref)-1

def do_delete_handler(dialog:Gtk.MessageDialog, response_id:int, process:helper_subprocess, index:int):
	if response_id == 1:
		process.data = True
	pipefd = process.process.stdin.fileno()
	if (response_id == Gtk.ResponseType.YES) or process.data:
		os.write(pipefd, b'y\n')
	else:
		os.write(pipefd, b'n\n')
	dialog.destroy()
	global dialog_ref
	dialog_ref[index] = None

def delete_handler(process:helper_subprocess, arg:str):
	if arg[-9:] == "deleted.\n":
		return
	if process.data:
		pipefd = process.process.stdin.fileno()
		os.write(pipefd, b"y\n")
		return
	dialog = Gtk.MessageDialog(
			modal=True,
			buttons=Gtk.ButtonsType.YES_NO,
			message_type=Gtk.MessageType.WARNING,
			text="Confirm deletion",
			secondary_text=arg[:-8]
		)
	dialog.add_button("Yes to All", 1)
	index = add_dialog_reference(dialog)
	dialog.connect("response", do_delete_handler, process, index)
	dialog.show()

def do_delete_subvolume(dialog:Gtk.Dialog, response_id:int, files, index:int):
	if response_id == Gtk.ResponseType.OK:
		for file in files:
			subvol = Gio.File.new_for_uri(file.get_uri())
			new_process = helper_subprocess(delete_handler)
			new_process.start_async([helper_path, "delete", subvol.get_path()])
	dialog.destroy()
	global dialog_ref
	dialog_ref[index] = None

def delete_subvolume(menuitem, files):
	dialog = Gtk.MessageDialog(
		modal=True,
		buttons=Gtk.ButtonsType.OK_CANCEL,
		message_type=Gtk.MessageType.WARNING,
		text="Are you sure you want to delete this subvolume?",
		secondary_text="This action cannot be reverted."
	)
	index = add_dialog_reference(dialog)
	dialog.connect("response", do_delete_subvolume, files, index)
	dialog.show()

#------------------------------------------------------------------------
class BtrfsSnapshotExtension(GObject.GObject, Nautilus.MenuProvider):	
	def get_background_items(self, cwd):
		menuitem_create = Nautilus.MenuItem(
			name='BtrfsSnapshotExtension::create',
			label='Create New Btrfs Subvolume'
		)
		menuitem_create.connect('activate', create_subvolume, cwd)
		return [menuitem_create]

	def get_file_items(self, files):
		if len(files) == 0:
			return ()

		menuitem_delete = Nautilus.MenuItem(
			name='BtrfsSnapshotExtension::delete',
			label='Delete Btrfs Subvolume'
		)
		menuitem_delete.connect('activate', delete_subvolume, files)

		if len(files) == 1:
			menuitem_snapshot = Nautilus.MenuItem(
				name='BtrfsSnapshotExtension::snapshot',
				label='Create Btrfs Snapshot'
			)
			menuitem_snapshot.connect('activate', create_snapshot, files[0])
			return [menuitem_delete, menuitem_snapshot]
		return [menuitem_delete]
