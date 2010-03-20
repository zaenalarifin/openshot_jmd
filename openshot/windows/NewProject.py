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
from classes import messagebox, profiles, project
from windows.SimpleGladeApp import SimpleGladeApp

# init the foreign language
from language import Language_Init


# This form is used to create new projects and save 
# existing projects
class frmNewProject(SimpleGladeApp):
	
	def __init__(self, mode="", path="NewProject.glade", root="frmNewProject", domain="OpenShot", project=None, **kwargs):
		print "init"
		SimpleGladeApp.__init__(self, os.path.join(project.GLADE_DIR, path), root, domain, **kwargs)

		# Add language support
		_ = Language_Init.Translator(project).lang.gettext

		# project instance
		self.project = project
		self.form = project.form

		# check the mode of the form (i.e. new project or save as screen)
		self.mode = mode
		
		# init the project type properties
		self.init_properties()
		
		# init the list of possible project types / profiles
		self.profile_list = profiles.mlt_profiles(self.project).get_profile_list()
		
		# loop through each profile, and add it to the dropdown
		for file_name, p in self.profile_list:
			# append profile to list
			self.cmbProjectType.append_text(p.description())

		
		# get the model and iterator of the project type dropdown box
		model = self.cmbProjectType.get_model()
		iter = model.get_iter_first()
		while True:
			# get the value of each item in the dropdown
			value = model.get_value(iter, 0)
			
			# check for the matching project type
			if self.project.project_type == value:			
				
				# set the item as active
				self.cmbProjectType.set_active_iter(iter)
		
			# get the next item in the list
			iter = model.iter_next(iter)
			
			# break loop when no more dropdown items are found
			if iter is None:
				break
			
		# SET THE SAVE FOLDER LOCATION
		if ".openshot" in self.project.folder:
			# This is the openshot default project (set the folder to 'DESKTOP')
			self.fileProjectFolder.set_current_folder(self.project.DESKTOP)
		
		elif len(self.project.folder) > 0:
			# set default folder (if there is a current folder)
			self.fileProjectFolder.set_current_folder(self.project.folder)
	
			
		if (self.mode == "saveas"):

			# init the values (based on the mode)
			self.txtProjectName.set_text(self.project.name)
			self.spinProjectLength.set_text(str(self.project.sequences[0].length / 60))



	def init_properties(self):
		# get the mlt profile
		localType = self.cmbProjectType.get_active_text()
		p = profiles.mlt_profiles(self.project).get_profile(localType)

		# populate the labels with values
		self.lblHeightValue.set_text(str(p.height()))
		self.lblWidthValue.set_text(str(p.width()))
		self.lblAspectRatioValue.set_text("%s:%s" % (p.display_aspect_num(), p.display_aspect_den()))
		self.lblFrameRateValue.set_text("%.2f" % float(p.fps()))
		self.lblPixelRatioValue.set_text("%s:%s" % (p.sample_aspect_num(), p.sample_aspect_den()))
		
		if p.progressive():
			self.lblProgressiveValue.set_text("Yes")
		else:
			self.lblProgressiveValue.set_text("No")
		

	def new(self):
		print "A new %s has been created" % self.__class__.__name__


	def on_frmNewProject_close(self, widget, *args):
		print "on_frmNewProject_close called with self.%s" % widget.get_name()



	def on_frmNewProject_destroy(self, widget, *args):
		print "on_frmNewProject_destroy called with self.%s" % widget.get_name()

		# Is openshot existing?
		if self.project.form.is_exiting:
			self.project.form.frmMain.destroy()
			

	def on_frmNewProject_response(self, widget, *args):
		print "on_frmNewProject_response called with self.%s" % widget.get_name()


	#def on_fileProjectFolder_selection_changed(self, widget, *args):
	#	print "on_fileProjectFolder_selection_changed called with self.%s" % widget.get_name()


	def on_cmbProjectType_changed(self, widget, *args):
		print "on_cmbProjectType_changed called with self.%s" % widget.get_name()

		# init the project type properties
		self.init_properties()

	def on_btnCancel_clicked(self, widget, *args):
		print "on_btnCancel_clicked called with self.%s" % widget.get_name()

		# close the window		
		self.frmNewProject.destroy()

	def on_btnCreateProject_clicked(self, widget, *args):
		print "on_btnCreateProject_clicked called with self.%s" % widget.get_name()

		localName = str.strip(self.txtProjectName.get_text())
		localFolder = str.strip(self.fileProjectFolder.get_filename())
		localType = self.cmbProjectType.get_active_text()
		localLength = str.strip(self.spinProjectLength.get_text())

		# Validate the the form is valid
		if (len(localName) == 0):
			# Show error message
			messagebox.show(_("Validation Error!"), _("Please enter a valid project name."))

		elif (localType == - 1):
			# Show error message
			messagebox.show(_("Validation Error!"), _("Please enter a valid project type."))

		else:

			
			# check if mode is 'New Project'
			if (self.mode == "new"):
				# Re-init / clear the current project object (to reset all exisint data)
				self.project = project.project()
				self.project.form = self.form
				self.project.form.project = self.project
				
				# clear history (since we are opening a new project)
				self.project.form.history_stack = []
				self.project.form.history_index = -1
				self.project.form.refresh_history()
				self.project.set_project_modified(is_modified=True, refresh_xml=False, type=_("New project"))
			
			# set the project properties
			self.project.name = localName
			self.project.project_type = localType
			self.project.folder = localFolder
			self.project.sequences[0].length = float(localLength) * 60  # convert to seconds
			self.project.set_project_modified(is_modified=False, refresh_xml=True)

			# stop video
			self.project.form.MyVideo.pause()

			# set the profile settings in the video thread
			self.project.form.MyVideo.set_project(self.project, self.project.form, os.path.join(self.project.USER_DIR, "sequence.mlt"), mode="preview")
			self.project.form.MyVideo.set_profile(localType)
			self.project.form.MyVideo.load_xml()

			# Save the project
			self.project.Save("%s/%s.osp" % (localFolder, localName))

			# Is openshot existing?
			if self.project.form.is_exiting:
				self.project.form.frmMain.destroy()

			# Update the main form
			self.project.form.refresh()

			# close the window
			self.frmNewProject.destroy()


def main():
	frm_new_project = Frmnewproject()
	frm_new_project.run()

if __name__ == "__main__":
	main()
