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
from classes import messagebox, project
from windows.SimpleGladeApp import SimpleGladeApp

# init the foreign language
from language import Language_Init

class frmImportImageSequence(SimpleGladeApp):

	def __init__(self, path="ImportImageSeq.glade", root="frmImportImageSequence", domain="OpenShot", form=None, project=None, **kwargs):
		SimpleGladeApp.__init__(self, os.path.join(project.GLADE_DIR, path), root, domain, **kwargs)

		# Add language support
		_ = Language_Init.Translator(project).lang.gettext

		self.form = form
		self.project = project
		self.frmImportImageSequence.show_all()
		
	def on_btnCancel_clicked(self, widget, *args):
		print "on_btnCancel_clicked"
		self.frmImportImageSequence.destroy()
		
	def on_btnImport1_clicked(self, widget, *args):
		print "on_btnImport1_clicked"
		
		txtFileName1 = str.strip(self.txtFileName.get_text())
		txtFramesPerImage1 = str.strip(self.txtFramesPerImage.get_text())
		folder_location1 = str.strip(self.folder_location.get_filename())
		
		# Validate the the form is valid
		if len(txtFileName1) == 0 or txtFileName1.count("%") == 0:
			# Show error message
			messagebox.show(_("Validation Error!"), _("Please enter a valid file name.  The file name must have a %d (or %04d) where the number section of the file name is supposed to be.  For example:  MyFile_%d.png."))

		elif len(txtFramesPerImage1) == 0:
			# Show error message
			messagebox.show(_("Validation Error!"), _("Please enter an integer in the Frames per Image textbox."))

		else:
		
			# is this file a match?
			wildcard_position = txtFileName1.find("%")
			beginning_of_filename = txtFileName1[0:wildcard_position]
			number_of_matches = 0
			number_of_non_matches = 0
			first_match_path = ""
			
			# loop through a range of files (and be sure at least 2 matches are found)
			for x in range(0, 50000):
				# parse filename
				full_file_name = txtFileName1 % x
				
				# check if file exists
				if os.path.exists(os.path.join(folder_location1, full_file_name)):

					# increment counter 
					number_of_matches = number_of_matches + 1
					number_of_non_matches = 0

					# record first match
					if number_of_matches == 1:
						first_match_path = os.path.join(folder_location1, full_file_name)

				elif number_of_matches > 1:

					# non matching file pattern
					number_of_non_matches = number_of_non_matches + 1
					
					if number_of_non_matches >= 100:
						break

			if number_of_matches <= 1:
				# Show error message
				messagebox.show(_("Validation Error!"), _("At least 2 images must match the file name pattern in the selected folder."))
			
			else: 
							
				# create OpenShotFile (and thumbnail) of the first match
				full_file_path = os.path.join(folder_location1, first_match_path)

				# add file to current project
				f = self.project.project_folder.AddFile(full_file_path)
				
				# Update the file properties (since it's added as an image)
				# We need to make it look like a video
				f.label = _("Image Sequence")
				f.fps = self.project.fps()
				f.max_frames = number_of_matches
				f.ttl = int(txtFramesPerImage1)
				f.length = float(f.max_frames * f.ttl) / float(f.fps)
				f.file_type = "image sequence"
				f.name = os.path.join(folder_location1, txtFileName1)

				# refresh the main form
				self.form.refresh()
				self.frmImportImageSequence.destroy()
		
		
			
def main():
	frmImportImageSequence1 = frmImportImageSequence()
	frmImportImageSequence1.run()

if __name__ == "__main__":
	main()
