#	OpenShot Video Editor is a program that creates, modifies, and edits video files.
#   Copyright (C) 2009  Jonathan Thomas
#
#	This file is part of OpenShot Video Editor (http://launchpad.net/openshot/).
#
#	OpenShot Video Editor is free software: you can redistribute it and/or modify
#	it under the terms of the GNU General Public License as published by
#	the Free Software Foundation, either version 3 of the License, or
#	(at your option) any later version.
#
#	OpenShot Video Editor is distributed in the hope that it will be useful,
#	but WITHOUT ANY WARRANTY; without even the implied warranty of
#	MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#	GNU General Public License for more details.
#
#	You should have received a copy of the GNU General Public License
#	along with OpenShot Video Editor.  If not, see <http://www.gnu.org/licenses/>.

import os
import gtk, gtk.glade
from windows.SimpleGladeApp import SimpleGladeApp
from windows import preferences
from classes import project, messagebox

# init the foreign language
from language import Language_Init


class frmAddFiles(SimpleGladeApp):

	def __init__(self, path="AddFiles.glade", root="frmAddFiles", domain="OpenShot", form=None, project=None, **kwargs):
		SimpleGladeApp.__init__(self, os.path.join(project.GLADE_DIR, path), root, domain, **kwargs)

		# Add language support
		_ = Language_Init.Translator(project).lang.gettext

		self.frmAddFiles.set_action(gtk.FILE_CHOOSER_ACTION_OPEN)
		self.frmAddFiles.set_select_multiple(True)
		#if the video folder exists, default to this
		#video_dir = os.path.join(os.path.expanduser("~"), "Video")
		#if video_dir:
		#	self.frmAddFiles.set_current_folder(video_dir)

		self.form = form
		self.project = project
		
		#open the last used folder
		default_folder = preferences.Settings.app_state["import_folder"]
		if default_folder != "None":
			self.frmAddFiles.set_current_folder(preferences.Settings.app_state["import_folder"])
		
		self.frmAddFiles.show_all()


	def on_btnCancel_clicked(self, widget, *args):
		self.frmAddFiles.destroy()
		
	def on_btnAdd_clicked(self, widget, *args):
		files_to_add = self.frmAddFiles.get_filenames()
		try:
			for file in files_to_add:
				# add each file
				self.project.project_folder.AddFile(file)
			
			#set the project as modified
			self.project.set_project_modified(is_modified=True, refresh_xml=False)
				
			# refresh the main form
			self.form.refresh()
			
		except:
			messagebox.show(_("Error"), _("There was an error importing the selected files"))

		#set the last used folder
		preferences.Settings.app_state["import_folder"] = self.frmAddFiles.get_current_folder()
		
			
		self.frmAddFiles.destroy()
		
	def on_frmAddFiles_file_activated(self, widget, *args):
		#call the open project method when a file is double clicked
		self.on_btnAdd_clicked(widget, *args)
		
		
			
def main():
	frm_add_files = frmAddFiles()
	frm_add_files.run()

if __name__ == "__main__":
	main()
