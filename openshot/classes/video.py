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

import os, sys, time 
import threading
import gobject
from classes import profiles

class player ( threading.Thread ):
	
	def __init__(self, project, main_form, file_name, mode=None):
		self.project = project
		self.main_form = main_form
		self.file_name = file_name
		
		# set the FPS
		self.fps = self.project.fps()
		
		# update mode
		if mode:
			# set the mode
			self.mode = mode

		# call base class
		threading.Thread.__init__(self)


	def set_project(self, project, main_form, file_name, mode=None, render_options = None, override_path = None):
		self.project = project
		self.main_form = main_form
		self.file_name = file_name
		self.render_options = render_options
		
		# set the FPS
		self.fps = self.project.fps()
		
		# update mode
		if mode:
			# set the mode
			self.mode = mode
			
		# override mode
		if override_path:
			self.override_path = override_path
		else:
			self.override_path = None
			
		
	def set_profile(self, profile_name, load_xml = True):

		# set the MLT profile object... specifiec in the project properties
		self.c.stop()
		self.profile = profiles.mlt_profiles(self.project).get_profile(profile_name)

		# set the FPS
		self.fps = self.project.fps()
		
		# re-load the mlt objects (i.e. the producer & consumer)
		if load_xml:
			self.load_xml()
		
		
	def load_xml(self):
		
		# Import required modules
		import time
		import sys
		import gobject
		
		try:
			import mlt
		except ImportError:
			print "*** ERROR: MLT Python bindings failed to import ***"
		
		# set the FPS
		self.fps = self.project.fps()
		
		# stop the consumer
		self.c.stop()
		
		# Create the producer
		if self.override_path:
			self.p = mlt.Producer( self.profile, self.override_path)
		else:
			self.p = mlt.Producer( self.profile, 'xml:%s' % self.file_name)
			
		# re-init the mlt factory
		mlt.Factory.init()

		# Create the consumer
		if self.mode == "render":
			# RENDER MOVIE mode

			# get export file path
			folder = self.render_options["folder"]
			file = self.render_options["file"]
			export_path = "%s.%s" % (os.path.join(folder, file), self.render_options["f"])
			
			# create consumer
			self.c = mlt.Consumer( self.profile, "avformat", export_path)
			
			# set some RENDER specific options
			self.c.set("real_time", -1)
			
			# set render options
			if self.render_options["export_to"] == "Image Sequence":
				# image seq
				self.c.set("vcodec" , self.render_options["vcodec"])
			else:
				# video & audio
				self.c.set("f" , self.render_options["f"])
				self.c.set("vcodec" , self.render_options["vcodec"])
				self.c.set("b" , self.render_options["b"])
				self.c.set("acodec" , self.render_options["acodec"])
				self.c.set("ar" , self.render_options["ar"])
				self.c.set("ac" , self.render_options["ac"])
				self.c.set("ab" , self.render_options["ab"])
			
				if self.render_options["vcodec"] == "libx264":
					self.c.set("minrate", "0")
					self.c.set("b_strategy", "1")
					self.c.set("subcmp", "2")
					self.c.set("cmp", "2")
					self.c.set("coder", "1")
					self.c.set("flags", "+loop")
					self.c.set("flags2", "dct8x8")
					self.c.set("qmax", "51")
					self.c.set("subq", "7")
					self.c.set("qmin", "10")
					self.c.set("qcomp", "0.6")
					self.c.set("qdiff", "4")
					self.c.set("trellis", "1")

		else:
			# PREVIEW mode
			self.c = mlt.Consumer( self.profile, "sdl_preview" )
			self.c.set("real_time", 1)

			# refresh sdl and pause video
			self.pause()

		# connect the producer and consumer
		self.c.connect( self.p )

		# start consumer
		self.c.start()


	def run ( self ):
		# FIXME: Is this relevant - doesn't seem to be used in this method?
		self.override_path = None
		self.alternate_progress_bar = None

		# Import required modules
		import time
		import sys
		import gobject
		
		try:
			import mlt
		except ImportError:
			print "*** ERROR: MLT Python bindings failed to import ***"

		# track wheather the thread is playing or not
		self.isPlaying = False 
		
		# track if this thread should die
		self.amAlive = True
		
		# Start the mlt system
		self.f = mlt.Factory().init( )
		
		# set the MLT profile object... specifiec in the project properties
		self.profile = profiles.mlt_profiles(self.project).get_profile(self.project.project_type)
		
		# Create the producer
		self.p = mlt.Producer( self.profile, 'xml:%s' % self.file_name)
		
		if self.p:
			# set speed to zero (i.e. pause)
			self.p.set_speed(0)
			
			# Create the consumer
			if self.mode == "render":
				# get export file path
				folder = self.render_options["folder"]
				file = self.render_options["file"]
				export_path = "%s.%s" % (os.path.join(folder, file), self.render_options["f"])
				
				# RENDER MOVIE mode
				self.c = mlt.Consumer( self.profile, "avformat", export_path)
				
				# set some RENDER specific options
				self.c.set("real_time", -1)
				
				# set render options
				self.c.set("f" , self.render_options["f"])
				self.c.set("vcodec" , self.render_options["vcodec"])
				self.c.set("b" , self.render_options["b"])
				self.c.set("acodec" , self.render_options["acodec"])
				self.c.set("ar" , self.render_options["ar"])
				self.c.set("ac" , self.render_options["ac"])
				self.c.set("ab" , self.render_options["ab"])

				if self.render_options["vcodec"] == "libx264":
					self.c.set("minrate", "0")
					self.c.set("b_strategy", "1")
					self.c.set("subcmp", "2")
					self.c.set("cmp", "2")
					self.c.set("coder", "1")
					self.c.set("flags", "+loop")
					self.c.set("flags2", "dct8x8")
					self.c.set("qmax", "51")
					self.c.set("subq", "7")
					self.c.set("qmin", "10")
					self.c.set("qcomp", "0.6")
					self.c.set("qdiff", "4")
					self.c.set("trellis", "1")
				
			else:
				# PREVIEW mode
				self.c = mlt.Consumer( self.profile, "sdl_preview" )
				self.c.set("real_time", 1)
		
			# Connect the producer to the consumer
			self.c.connect( self.p )
			
			# Start the consumer
			self.c.start()
			
			# Get the FPS
			self.fps = self.project.fps()
			
			# init the render percentage
			self.fraction_complete = 0.0
			
			# pause counter
			pause_counter = 0
			pause_frame = 0
			
			
			# Wait until the user stops the consumer
			while self.amAlive:
				
				# get current frame
				current_frame = self.p.position()

				# only calculate position / percentage when playing
				if self.c.is_stopped() == False:

					# move play head
					new_time = float(self.p.position()) / float(self.fps)
					
					if self.mode == "render":
						# update Export Dialog Progress Bar
						self.fraction_complete = (float(self.p.position()) / float(self.p.get_length() - 1))
						if self.project.form.frmExportVideo:
							gobject.idle_add(self.project.form.frmExportVideo.update_progress, self.fraction_complete)
						
					elif self.mode == "preview":
						
						if self.alternate_progress_bar:
							# update alternateive progress bar (if any) of video
							# this is used by the clip properties window 
							percentage_complete = (float(self.p.position()) / float(self.p.get_length() - 1)) * float(100)
							if self.alternate_progress_bar:
								gobject.idle_add(self.alternate_progress_bar.set_value, percentage_complete)
							
						else:
							# update play-head
							if self.project.sequences[0]:
								gobject.idle_add(self.project.sequences[0].move_play_head, new_time)
			
							# update progress bar of video 
							percentage_complete = (float(self.p.position()) / float(self.p.get_length() - 1)) * float(100)
							if self.main_form.hsVideoProgress:
								gobject.idle_add(self.main_form.hsVideoProgress.set_value, percentage_complete)
								gobject.idle_add(self.main_form.scroll_to_playhead)
								
							# pause video when 100%
							if percentage_complete == 100:
								self.pause()
						
						
					elif self.mode == "override":
						# update progress bar of video 
						percentage_complete = (float(self.p.position()) / float(self.p.get_length() - 1)) * float(100)
						if self.main_form.hsVideoProgress:
							gobject.idle_add(self.main_form.hsVideoProgress.set_value, percentage_complete)

					# wait 1/5 of a second
					time.sleep( 0.2 )

					
				else:
					if self.mode == "render":
						# update Export Dialog Progress Bar
						if self.fraction_complete > 0.0:
							# update progress bar to 100%
							if self.project.form.frmExportVideo:
								gobject.idle_add(self.project.form.frmExportVideo.update_progress, 1.0)
							
							# reset the fraction
							self.fraction_complete = 0.0

					# wait 1 second
					time.sleep( 1 )



			# clear all the MLT objects
			self.c.stop()
			self.p = None
			self.c = None
			self.profile = None
			self.f = None
			
		else:
			# Diagnostics
			print "ERROR WITH %s" % self.file_name

	def set_progress_bar(self, pbar):
		""" Set the progress bar that this thread should update """
		self.alternate_progress_bar = pbar

	def clear_progress_bar(self):
		""" Set the progress bar that this thread should update """
		self.alternate_progress_bar = None
		
	def get_progress_bar(self):
		""" Get the progress bar object """
		return self.alternate_progress_bar
	
	def close_window(self, window):
		""" Let this thread close a window """
		window.destroy()

	def move_play_head(self, new_time):
		# call this thread move the play_head
		gobject.idle_add(self.project.sequences[0].move_play_head, new_time)
		
		# refresh sdl
		#self.c.set("refresh", 1)

	def pause(self):
		# pause the video
		self.isPlaying = False
		self.p.set_speed(0)
		
			
	def play(self):
		# play the video
		self.isPlaying = True
		self.p.set_speed(1)


	def seek(self, frame_number):

		# pause frame (if the video is playing)
		if self.isPlaying:	
			# pause
			self.pause()
			
			# wait for 2/10ths of a second (for mlt to catch up to 
			# the correct seek position
			time.sleep(0.2)
			
		# seek to a specific frame 
		self.p.seek(frame_number) 
		
		# refresh sdl
		self.c.set("refresh", 1)
