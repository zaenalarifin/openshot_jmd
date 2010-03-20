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

import os, gtk
import gtk, gtk.glade
from classes import messagebox, project
from windows.SimpleGladeApp import SimpleGladeApp

# init the foriegn language
import language.Language_Init as Language_Init


class frmOpenProject(SimpleGladeApp):

	def __init__(self, path="OpenProject.glade", root="frmOpenProject", domain="OpenShot", project=None, **kwargs):
		SimpleGladeApp.__init__(self, os.path.join(project.GLADE_DIR, path), root, domain, **kwargs)

		self.project = project
		self.form = self.project.form

		# Add language support
		_ = Language_Init.Translator(project).lang.gettext

		# set a file type filter (to limit the files to only valid files)
		OSPfilter = gtk.FileFilter()
		OSPfilter.add_pattern("*.osp")
		OSPfilter.set_name(_("OpenShot Project (*.osp)"))
		self.frmOpenProject.add_filter(OSPfilter)



	def new(self):
		print "A new %s has been created" % self.__class__.__name__

	def on_frmOpenProject_response(self, widget, *args):
		#print "on_frmOpenProject_response called with self.%s" % widget.get_name()

		#if widget.get_name() == self.frmOpenProject:
		#	print "OPEN " % (self.frmOpenProject.get_filename())
		pass

	def on_btnCancel_clicked(self, widget, *args):
		#print "on_btnCancel_clicked called with self.%s" % widget.get_name()
		self.frmOpenProject.destroy()


	def on_btnOpenProject_clicked(self, widget, *args):
		#print "on_btnOpenProject_clicked called with self.%s" % widget.get_name()

		# Get selected file name
		file_to_open = self.frmOpenProject.get_filename()	

		try:
			# open the project (and re-serialize the project object)
			self.project.Open(file_to_open)

			# Update the main form
			self.project.form.refresh()
			
			# stop video
			self.project.form.MyVideo.pause()
			
			# set the profile settings in the video thread
			self.project.form.MyVideo.set_profile(self.project.project_type)
			self.project.form.MyVideo.set_project(self.project, self.project.form, os.path.join(self.project.USER_DIR, "sequence.mlt"), mode="preview")
			self.project.form.MyVideo.load_xml()
			
			# stop video
			self.project.form.MyVideo.play()
			self.project.form.MyVideo.pause()

			# close window
			self.frmOpenProject.destroy()

		except:
			# show the error message
			messagebox.show(_("Error!"), _("There was an error opening this project file.  Please be sure you open the correct *.osp file."))


	def on_frmOpenProject_file_activated(self, widget, *args):
		#call the open project method when a file is double clicked
		self.on_btnOpenProject_clicked(widget, *args)


def main():
	frm_open_project = frmOpenProject()
	frm_open_project.run()

if __name__ == "__main__":
	main()
