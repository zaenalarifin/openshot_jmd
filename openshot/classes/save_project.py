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

import sys, os
import shutil
import gtk
import cPickle as pickle
from classes import files

def save_project(project_object, file_path):
		project = project_object
			
		# create thumbnail folder (if it doesn't exist)
		if os.path.exists(os.path.join(project_object.folder, "thumbnail")) == False:
			# create new thumbnail folder
			os.mkdir(os.path.join(project_object.folder, "thumbnail"))
			
		# copy all temp thumbnails to this project's folder
		copy_files(os.path.join(project.USER_DIR, "thumbnail"), os.path.join(project_object.folder, "thumbnail"))

		# Loop through the files, and update the thumbnail location
		for item in project_object.project_folder.items:
			
			if isinstance(item, files.OpenShotFile):

				# split thumbnail file path
				(dirName, fname) = os.path.split(item.thumb_location)
				(fileBaseName, fileExtension)=os.path.splitext(fname)
	
				# update the thumbnail location
				item.thumb_location = os.path.join(project_object.folder, "thumbnail", fname)
				
				# UPDATE TITLES... so they move with the project
				# update the thumbnail location
				if ".svg" in item.name and "thumbnail" in item.name:
					(dirName, fname) = os.path.split(item.name)
					(fileBaseName, fileExtension)=os.path.splitext(fname)
					item.name = os.path.join(project_object.folder, "thumbnail", fname)


		# clear the following temporary properties which can't be pickeled
		old_form = project_object.form
		old_play_head = project_object.sequences[0].play_head
		old_ruler_time = project_object.sequences[0].ruler_time
		old_play_head_line = project_object.sequences[0].play_head_line
		old_thumbnailer = project_object.thumbnailer
		project_object.mlt_profile = None
		
		project_object.sequences[0].play_head = None
		project_object.sequences[0].ruler_time = None
		project_object.sequences[0].play_head_line = None
		project_object.form = None
		project_object.thumbnailer = None

		# check whether using binary or ascii file
		
		if project.file_type == "binary":
			file_is_binary = True
		else:
			file_is_binary = False
				
		# serialize the project object
		myFile = file(file_path, "wb")
		pickle.dump(project_object, myFile, file_is_binary)
		
		# re-attach some variables (that aren't pickleable)
		project_object.form = old_form
		project_object.sequences[0].play_head = old_play_head
		project_object.sequences[0].ruler_time = old_ruler_time
		project_object.sequences[0].play_head_line = old_play_head_line
		project_object.thumbnailer = old_thumbnailer
		
		# update the thumbnailer's project reference
		project_object.thumbnailer.set_project(project_object)
		
		# update project references in the menus
		project_object.form.mnuTrack1.project = project_object
		project_object.form.mnuClip1.project = project_object
		project_object.form.mnuMarker1.project = project_object
		project_object.form.mnuTransition1.project = project_object
		project_object.form.mnuFadeSubMenu1.project = project_object
		project_object.form.mnuAnimateSubMenu1.project = project_object
		project_object.form.mnuPositionSubMenu1.project = project_object
		
		# disable save button on form
		project_object.set_project_modified(is_modified=False, refresh_xml=True)
		
		manager = gtk.recent_manager_get_default()
		manager.add_item('file://' + file_path)
		
		# output the file path
		print "project saved! - %s" % (project_object.name)
			   


def copy_files(path, target_folder):

	# verify this folder exists
	if os.path.exists(path):
		
		# loop through all files in this folder
		for child_path in os.listdir(path):
			
			# get full child path
			source_path = os.path.join(path, child_path)
			target_path = os.path.join(target_folder, child_path)
			
			if os.path.isdir(source_path) == True:
				
				if os.path.exists(target_path) == False:
					# create the folder in the target folder
					os.mkdir(target_path)
					
				# copy all the files in this sub-folder
				copy_files(source_path, target_path)

			else:
				
				# copy the thumbnail to the new location (if it doesn't exit)
				if os.path.exists(target_path) == False:
					shutil.copyfile(source_path, target_path)
		
	#except IOError:
	#	# print error message
	#	print "*** error saving file ***"
		  
		  
