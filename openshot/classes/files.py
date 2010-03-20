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

from classes import messagebox
import os, sys, urllib, uuid
import gtk

# init the foreign language
from language import Language_Init

########################################################################
class OpenShotFile:
	"""The generic file object for OpenShot"""

	#----------------------------------------------------------------------
	def __init__(self, project=None):
		self.project = project
		
		"""Constructor"""
		
		
		# Add language support
		translator = Language_Init.Translator(self.project)
		_ = translator.lang.gettext

		# init the variables for the File Object
		self.name = ""			# short / friendly name of the file
		self.length = 0.0		# length in seconds
		self.videorate = (30,0)	# audio rate or video framerate
		self.file_type = ""		# video, audio, image, image sequence
		self.max_frames = 0.0
		self.fps = 0.0
		self.height = 0
		self.width = 0
		self.label = ""			 # user description of the file
		self.thumb_location = "" # file uri of preview thumbnail
		self.ttl = 1			 # time-to-live - only used for image sequence.  Represents the # of frames per image.
		
		self.unique_id = str(uuid.uuid1())	
		self.parent = None
		self.project = project	  # reference to project
		
		
	def get_thumbnail(self, width, height):
		"""Get and resize the pixbuf thumbnail for a file"""	
		
		# get the thumbnail (or load default)
		try:
			if self.thumb_location:
				pbThumb = gtk.gdk.pixbuf_new_from_file(self.thumb_location)
			else:
				# Load the No Thumbnail Picture
				pbThumb = gtk.gdk.pixbuf_new_from_file(os.path.join(self.project.IMAGE_DIR, "AudioThumbnail.png"))
		except:

				# Load the No Thumbnail Picture
				pbThumb = gtk.gdk.pixbuf_new_from_file(os.path.join(self.project.IMAGE_DIR, "AudioThumbnail.png"))

		# resize thumbnail
		return pbThumb.scale_simple(width, height, gtk.gdk.INTERP_BILINEAR)	
		

########################################################################
class OpenShotFolder:
	"""The generic folder object for OpenShot"""

	#----------------------------------------------------------------------
	def __init__(self, project=None):
		"""Constructor"""
		
		# Init the variables for the Folder Object
		self.name = ""		  # short / friendly name of the folder
		self.location = ""	  # file system location
		self.parent = None
		self.project = project
		
		# init the list of files & folders
		# this list can contain OpenShotFolder or OpenShotFile objects
		# the order of this list determines the order of the tree items
		self.items = []
		
		# this queue holds files that are currently being added. this prevents
		# duplicate files to be added at the same time
		self.queue = []


	#----------------------------------------------------------------------
	def AddFolder(self, folder_name, project=None):
		
		"""Add a new folder to the current folder"""
		#does this folder name already exist?
		if self.FindFolder(folder_name):
			messagebox.show(_("OpenShot Error"), _("The folder %s already exists in this project." % folder_name))
			return
		newFolder = OpenShotFolder(project)		
		newFolder.name = folder_name
		
		self.items.append(newFolder)
		
		#set the modified status
		self.project.set_project_modified(is_modified=True, refresh_xml=False, type=_("Added folder"))
		
		self.project.form.refresh()
		

	#----------------------------------------------------------------------
	def AddFile(self, file_name):
		"""Add a new file to the current folder"""
		
		import urllib
		
		# clean path to video
		file_name = urllib.unquote(file_name)
		
		# don't add a file that is alrady in this folder (i.e. dupe check)
		if self.file_exists_in_project(file_name):
			return
			
		# check if the path is a 'folder' and not a file
		if os.path.isdir(file_name):
			
			# loop through each sub-file (if any)
			for sub_file in os.listdir(file_name):
				sub_file_path = os.path.join(file_name, sub_file)
				
				# only add files
				if os.path.isfile(sub_file_path):
					
					# don't add a file that is alrady in this folder (i.e. dupe check)
					if self.file_exists_in_project(sub_file_path) == False:

						# inspect the media file and generate it's thumbnail image (if any)
						newFile = self.project.thumbnailer.GetFile(sub_file_path)
						
						# add to internal item collection
						if newFile:
							self.items.append(newFile)

		else:
			# inspect the media file and generate it's thumbnail image (if any)
			newFile = self.project.thumbnailer.GetFile(file_name)
		
			# add to internal item collection
			if newFile:
				self.items.append(newFile)

		# mark project as modified
		self.project.set_project_modified(is_modified=True, refresh_xml=False, type=_("Added file"))
		
		return newFile
	
	#----------------------------------------------------------------------
	def ConvertFileToImages(self, file_name):
		"""Add a new file to the current folder"""
		
		import urllib

		# clean path to video
		file_name = urllib.unquote(file_name)

		# check if this file is already in the project
		for item in self.items:
			if file_name in item.name and item.file_type == _("Image Sequence").lower():
				return True
			
		# inspect the media file and generate it's thumbnail image (if any)
		newFile = self.project.thumbnailer.GetFile(file_name, all_frames=True)
		
		# update the location
		if newFile:
			(dirName, fname) = os.path.split(file_name)
			(fileBaseName, fileExtension)=os.path.splitext(fname)
			newFile.name = os.path.join(dirName, fileBaseName, fileBaseName + "_%d.png")
	
			# add to internal item collection
			self.items.append(newFile)

		return


	def file_exists_in_project(self, file_name):
		""" Check if this file exists in this project """
		
		# don't add a file that is alrady in this folder (i.e. dupe check)
		for item in self.items:
			if file_name in item.name:
				return True
		
		# didn't find a match
		return False

	#----------------------------------------------------------------------
	def get_file_path_from_dnd_dropped_uri(self, uri):
		""""""

		path = uri
		#path = urllib.url2pathname(uri) # escape special chars
		path = path.strip('\r\n\x00') # remove \r\n and NULL
		
		if os.name == 'nt':
			path = path.replace("/", "\\")
			path = path.replace("%20", " ")

		# get the path to file
		if path.startswith('file:\\\\\\'): # windows
			path = path[8:] # 8 is len('file:///')
		elif path.startswith('file://'): # nautilus, rox
			path = path[7:] # 7 is len('file://')
		elif path.startswith('file:'): # xffm
			path = path[5:] # 5 is len('file:')
		return path


	def UpdateFileLabel(self, filename, value, refresh_tree=0):
		#this will only be called when the treeview mode is selected, not the thumbview 
		for item in self.items:
			if item.name.endswith(filename):
				item.label = value
				
		if refresh_tree == 1:
			# Update the main form
			self.project.form.refresh()
				
				
	def RemoveFile(self, filename):
		item = self.FindFile(filename)
		if item:
			# mark project as modified
			self.project.set_project_modified(is_modified=True, refresh_xml=True, type=_("Removed file"))
			
			# find clips that have this file object
			for track in self.project.sequences[0].tracks:
				for clip in reversed(track.clips):
					# does clip match file
					if clip.file_object == item:
						# delete clip
						track.clips.remove(clip)
			# remove from file collection
			self.items.remove(item)
		else:
			#is this a folder?
			item = self.FindFolder(filename)
			if item:
				# remove from file collection
				self.items.remove(item)

  
	#----------------------------------------------------------------------
	def FindFile(self, file_name):
		"""Pass the file system location of the item you 
		are looking for and this function will return the 
		reference to the OpenShot File that matches"""
		
		# loop through all files looking for the matching filename
		for file in self.items:
			if isinstance(file, OpenShotFile):
				name = file.name
				
				# check if file name matches this file
				if file_name == name:
					return file

				# split file name (if it's not found)
				(dirName, fileName) = os.path.split(name)
		
				# check if file name matches the basefile name
				if file_name == fileName:
					return file

		
		# No file found
		return None
	
	
	#----------------------------------------------------------------------
	def FindFileByID(self, unique_id):
		"""Pass the file system location of the item you 
		are looking for and this function will return the 
		reference to the OpenShot File that matches"""
		
		# loop through all files looking for the matching filename
		for file in self.items:
			if isinstance(file, OpenShotFile):

				# check if file name matches this file
				if unique_id == file.unique_id:
					return file

		# No file found
		return None

	
	def FindFolder(self, folder_name):
		"""Returns a reference to the OpenShotFolder
		 that matches the folder_name"""
		for folder in self.items:
			if isinstance(folder, OpenShotFolder):
				name = folder.name
				
				if folder_name == name:
					return folder
	
	def ListFolders(self):
		"""Return a list of any folders in the project"""
		
		folders = []
		for item in self.items:
			if isinstance(item, OpenShotFolder):
				folders.append(item.name)
		return folders
	
	def AddParentToFile(self, file_name, folder_name):
		file = self.FindFile(file_name)
		if file:
			file.parent = folder_name
			
			# mark project as modified
			self.project.set_project_modified(is_modified=True, refresh_xml=False, type=_("Moved to folder"))
			
	def RemoveParent(self, file_name, folder_name):
		file = self.FindFile(file_name)
		if file:
			print "REMOVE PARENT"
			file.parent = self.project.project_folder
			
			# mark project as modified
			self.project.set_project_modified(is_modified=True, refresh_xml=False, type=_("Removed from folder"))
