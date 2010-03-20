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

import os, sys, threading, time
from classes import files, profiles

try:
	import mlt
except ImportError:
	print "*** ERROR: MLT Python bindings failed to import ***"
	

class thumbnailer ( threading.Thread ):
	""" This class is designed to always be running during OpenShot.  It's a seperate thread that 
	is always waiting to inspect video and audio files, generate thumbnails, etc... """

	def set_project(self, project):
		 """ Associate the OpenShot project file with this threaded class. """
		 self.project = project
		 
	def GetFile(self, file_name, all_frames=False):
		 """ Use this method to generate an OpenShotFile object based on the URL (or file location)
		 of a video or audio file. Each time you call this method, it will lock this thread (and OpenShot's
		 main thread) until it has finished. """

		 try:
			 
			 # determine name and location of thumbnail image
			 self.file_name = file_name
			 self.thumbnail_path = ""
			 self.file_type = "video"
			 self.label = ""
			 project_path = self.project.folder
			 myPath = self.file_name
			 (dirName, fileName) = os.path.split(myPath)
			 (fileBaseName, fileExtension)=os.path.splitext(fileName)
			 fileExtension = fileExtension.replace(".", "")
			 actual_thumbnail_path = project_path + "/thumbnail/" + fileBaseName + "_" + fileExtension + "_1.png"

			 if all_frames == False:
			 	# just get 1 thumbnail frame
			 	self.thumbnail_path = project_path + "/thumbnail/" + fileBaseName + "_" + fileExtension + "_%d.png"
			 	
			 	# set the profile
			 	self.profile = mlt.Profile("quarter_ntsc")

			 else:
			 	# export all frames of the video
			 	self.thumbnail_path = dirName + "/" + fileBaseName + "/" + fileBaseName + "_%d.png"
			 	
			 	# set the profile
			 	self.profile = profiles.mlt_profiles(self.project).get_profile(self.project.project_type)

			 # re-init the mlt factory
			 mlt.Factory.init()
			 	
			 # Create the producer
			 self.p = mlt.Producer( self.profile, '%s' % self.file_name )
			 
			 # Check if clip is valid (otherwise a seg fault)
			 if self.p.is_valid() == False:
			 	return None
			 
		 	 # create the consumer
		 	 self.c = mlt.Consumer(self.profile, "avformat", self.thumbnail_path)

			 # set some consumer properties
			 self.c.set("real_time", 0)
			 self.c.set("vcodec", "png")

			 # determine length of clip in seconds
			 max_frames = float(self.p.get_length()) - 1.0
			 producer_fps = float(self.p.get_fps())
			 calculate_length = max_frames / producer_fps

			 # determine if this is an image
			 is_image = False
			 if self.p.get_length() == 15000:
			 	# images always have exactly 15000 frames
			 	is_image = True
			 	self.file_type = "image"
			 	
			 	# set the max length of the image to 300 seconds (i.e. 5 minutes)
			 	max_frames = producer_fps * 300
			 	
			 	# set the length to 300 seconds (i.e. 5 minutes)
			 	calculate_length = float(300)

			 height = 0
			 width = 0
			 if self.p.get("height"):
				  height = int(self.p.get("height"))
			 if self.p.get("width"):
				  width = int(self.p.get("width"))
		 

			 # set thumbnail image (if no height & width are detected)
			 if (height == False or width == False) and (is_image == False):
				  self.thumbnail_path = ""
				  self.file_type = "audio"
				  
			 # set size of images
			 if is_image:
			 	height = 1
			 	width = 1

			 # get the 1st frame (if not exporting all frames)
			 if all_frames == False:
			 	self.p = self.p.cut(1, 1)
			 else:
			 	# mark as image seq
			 	self.label = "Image Sequence"
			 	self.file_type = "image sequence"
			 
			 # connect the producer and consumer
			 self.c.connect( self.p )

			 # Start the consumer, and lock the thread until it's done (to prevent crazy seg fault errors)
			 # Only start if the media item has a thumbnail location (i.e. no audio thumbnails)
			 if self.thumbnail_path:
			 	self.c.run()

	
			 # create an openshot file object
			 newFile = files.OpenShotFile(self.project)
			 newFile.name = self.file_name
			 newFile.length = calculate_length
			 newFile.thumb_location = actual_thumbnail_path
			 newFile.videorate = (self.p.get_fps(), 0)
			 newFile.height = height
			 newFile.width = width
			 newFile.max_frames = max_frames
			 newFile.fps = producer_fps
			 newFile.file_type = self.file_type
			 newFile.label = self.label

			 # return the OpenShotFile object
			 return newFile
		
		 except Exception:
			print "Failed to import file: %s" % file_name



	def run ( self ):
		 """ This is the main method on this thread.  This method should not return anything, or the 
		 thread will no longer be active... and thus will no longer be able to inspect media files. """
		 
		 self.amAlive = True
		 self.file_name = ""
		 self.c = None
		 self.p = None

		 # init the factory, and load a small video size / profile
		 mlt.Factory().init()
		 self.profile = mlt.Profile("quarter_ntsc")

		 # this loop will continue as long as OpenShot is running
		 while self.amAlive:
			  time.sleep( 1 ) 

		 # clear all the MLT objects
		 self.p = None
		 self.c = None
		 self.profile = None
		 self.f = None
		 
	def get_thumb_at_frame(self, filename, frame=1):
		
		self.file_name = filename
		
		project_path = self.project.folder
		myPath = self.file_name
		(dirName, fileName) = os.path.split(myPath)
		(fileBaseName, fileExtension)=os.path.splitext(fileName)
		fileExtension = fileExtension.replace(".", "")
	
		mlt.Factory.init()
		
		# just get 1 thumbnail frame
		self.thumbnail_path = project_path + "/thumbnail/" + fileBaseName + "_" + fileExtension + "_%d.png"
					
		# set the profile
		self.profile = mlt.Profile("quarter_ntsc")
		
		# Create the producer
		self.p = mlt.Producer( self.profile, '%s' % self.file_name )
				 
		# Check if clip is valid (otherwise a seg fault)
		if self.p.is_valid() == False:
			return None
		
		# create the consumer
		self.c = mlt.Consumer(self.profile, "avformat", self.thumbnail_path)
	
		# set some consumer properties
		self.c.set("real_time", 0)
		self.c.set("vcodec", "png")
		
		#get the frame
		self.p = self.p.cut(frame, frame)
		
		# connect the producer and consumer
		self.c.connect( self.p )
	
		# Only start if the media item has a thumbnail location (i.e. no audio thumbnails)
		if self.thumbnail_path:
			self.c.run()
			
		 
