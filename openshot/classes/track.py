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

import uuid
import gtk, goocanvas
from classes import clip, files, transition

# init the foreign language
from language import Language_Init

class track:
	"""The track class contains a simple grouping of clips on the same layer (aka track)."""

	#----------------------------------------------------------------------
	def __init__(self, track_name, parent_sequence):
		"""Constructor"""
		
		# Add language support
		translator = Language_Init.Translator(parent_sequence.project)
		_ = translator.lang.gettext
		
		# init variables for sequence
		self.name = track_name
		self.x = 10		 # left x coordinate to start the track
		self.y_top = 0	  # top y coordinate of this track
		self.y_bottom = 0   # bottom y coordinate of this track
		self.parent = parent_sequence   # reference to parent sequence object
		self.play_video = True
		self.play_audio = True
		self.unique_id = str(uuid.uuid1())

		# init the tracks on the sequence
		self.clips = []

		# init transitions
		self.transitions = []
		
		
	
	def AddClip(self, clip_name, color, position_on_track, start_time, end_time, file_object, record_to_history = True):
		# Create new clip object and append to list
		NewClip = clip.clip(clip_name, color, position_on_track, start_time, end_time, self, file_object)
		
		# Adjust default length of images (all images default to 300 seconds.. i.e. 5 minutes)
		# But since nobody wants an image to default to 5 minutes long, we adjust it to the default image length.
		if NewClip.length() == 300.0:
			from windows import preferences
			NewClip.end_time = NewClip.start_time + float(preferences.Settings.general["imported_image_length"])#7.0
		
		# Add clip to track's clip list
		self.clips.append(NewClip)		
		
		# return the new clip
		return NewClip
			
			
	def AddTransition(self, transition_name, position_on_track, length, resource):
		
		# create a new transition object
		new_transition = transition.transition(transition_name, position_on_track, length, resource, self)
		
		# insert new transition
		self.transitions.append(new_transition)	
		
		return new_transition
		 
	
	
	def Render(self):

		# Render this track
		self.RenderTrack()
		
		# loop through each track
		for MyClip in self.clips:
			
			# Render track			
			MyClip.Render()				
		
			
			
			
	def GenerateXML(self, dom, xmlParentNode, fps=None):
		
		playlist = dom.createElement("playlist")
		playlist.setAttribute("id", self.name)
		xmlParentNode.appendChild(playlist)
		
		current_frame = 0
		
		# loop through each track
		for MyClip in self.clips:
			
			# Render track			
			current_frame = MyClip.GenerateXML(dom, playlist, current_frame, fps=fps)


			
	#----------------------------------------------------------------------
	def RenderTrack(self):
		"""This adds a track to the canvas with 3 images: a left, middle, and right"""

		# get the pixels per second from the parent sequence
		pixels_per_second = self.parent.get_pixels_per_second()
		
		# get the previous track from the parent sequence (if any)
		previous_track_index = self.parent.tracks.index(self) - 1
		previous_track = None
		previous_y_top = 0
		previous_y_bottom = 0
		
		if (previous_track_index >= 0):
			previous_track = self.parent.tracks[previous_track_index]
			previous_y_top = previous_track.y_top
			previous_y_bottom = previous_track.y_bottom
		
		# set the top coordinate of this track to the bottom coordinate of the last track
		self.y_top = previous_y_bottom + 6
		
		# get a reference to the 2 main canvas objects & theme
		theme = self.parent.project.theme
		canvas_left = self.parent.project.form.MyCanvas_Left
		canvas_right = self.parent.project.form.MyCanvas
		
		# Add an item to the goocanvas
		root_left = canvas_left.get_root_item ()
		root_right = canvas_right.get_root_item ()

		# Load all 3 images
		imgTrack_Left = gtk.image_new_from_file("%s/openshot/themes/%s/Track_Left.png" % (self.parent.project.form.openshot_path, theme))
		imgTrack_Middle = gtk.image_new_from_file("%s/openshot/themes/%s/Track_Middle.png" % (self.parent.project.form.openshot_path, theme))
		imgTrack_Right = gtk.image_new_from_file("%s/openshot/themes/%s/Track_Right.png" % (self.parent.project.form.openshot_path, theme))	   		

		# Get Height and Width of Images 
		imgTrack_Left_Height = imgTrack_Left.get_pixbuf().get_height()
		imgTrack_Left_Width = imgTrack_Left.get_pixbuf().get_width()
		imgTrack_Right_Width = imgTrack_Right.get_pixbuf().get_width()		

		# Get Size of Window (to determine how wide the middle image should be streched)
		Size_Of_Middle = int(pixels_per_second * self.parent.length)

		# Resize Middle pixbuf
		middlePixBuf = imgTrack_Middle.get_pixbuf()
		pixbuf_list = self.parent.split_images(middlePixBuf, imgTrack_Left_Height, Size_Of_Middle)	  
		
		# Create Group (for the track)
		GroupTrack = goocanvas.Group (parent = root_right)
		GroupTrack_Left = goocanvas.Group (parent = root_left)
		
		# set the unique ID of the group
		GroupTrack.set_data ("id", self.unique_id)

		# Add Left Image to Group
		image1 = goocanvas.Image (parent = GroupTrack_Left,
								  pixbuf = imgTrack_Left.get_pixbuf(),
								  x = self.x,
								  y = self.y_top)

		# Track the state of the hover over image
		image1.set_data ("id", "normal")
		image1.connect ("button_press_event", self.on_focus_in)
 
		
		# Add Middle Image to Group (this can be multiple image tiled together
		pixbuf_x = 0
		for pixbuf in pixbuf_list:
			# get width of this pixbuf
			pixbuf_width = pixbuf.get_width()
			
			image2 = goocanvas.Image (parent = GroupTrack,
									  pixbuf = pixbuf,
									  x = pixbuf_x,
									  y = self.y_top)  
			
			# increment the x
			pixbuf_x = pixbuf_x + pixbuf_width

		# Add Middle Image to Group
		image3 = goocanvas.Image (parent = GroupTrack,
								  pixbuf = imgTrack_Right.get_pixbuf(),
								  x = Size_Of_Middle - 1,
								  y = self.y_top)	
		
		# Add Text to the Track
		text1 = goocanvas.Text (parent = GroupTrack_Left,
								text = "%s" % self.name,
								font = "Sans 9",
								antialias = False,
								x = self.x + 8,
								y = self.y_top + 7)
		
		# Load buttons
		if self.play_video:
			imgTrack_Visible = gtk.image_new_from_file("%s/openshot/themes/%s/visible.png" % (self.parent.project.form.openshot_path, theme))
		else:
			imgTrack_Visible = gtk.image_new_from_file("%s/openshot/themes/%s/not_visible.png" % (self.parent.project.form.openshot_path, theme))
		if self.play_audio:
			imgTrack_Audio = gtk.image_new_from_file("%s/openshot/themes/%s/speaker.png" % (self.parent.project.form.openshot_path, theme))
		else:
			imgTrack_Audio = gtk.image_new_from_file("%s/openshot/themes/%s/speaker_mute.png" % (self.parent.project.form.openshot_path, theme))
		
		# Add Visible Image to Group
		image4 = goocanvas.Image (parent = GroupTrack_Left,
								  pixbuf = imgTrack_Visible.get_pixbuf(),
								  x = self.x + 7,
								  y = self.y_top + 27)  
		
		# Track the state of the hover over image
		image4.connect ("button_press_event", self.on_visible_click)
		
		# Add Visible Image to Group
		image5 = goocanvas.Image (parent = GroupTrack_Left,
								  pixbuf = imgTrack_Audio.get_pixbuf(),
								  x = self.x + 28,
								  y = self.y_top + 27)  
		
		# Track the state of the hover over image
		image5.connect ("button_press_event", self.on_audio_click)
		
		# Increment the Y cooridinate (by the height of the left image)
		self.y_bottom = self.y_top + imgTrack_Left_Height
		

		

	def on_visible_click (self, item, target, event):

		# get the parent left group
		parent_group = item.get_parent()
		

		if self.play_video == True:
			# Load Hover Over
			imgTrack_Left_Hover = gtk.image_new_from_file("%s/openshot/themes/%s/not_visible.png" % (self.parent.project.form.openshot_path, self.parent.project.theme))
			item.set_properties(pixbuf = imgTrack_Left_Hover.get_pixbuf())
			
			# update play video variable
			self.play_video = False
			
		else: 
			# Load normal image
			imgTrack_Left_Hover = gtk.image_new_from_file("%s/openshot/themes/%s/visible.png" % (self.parent.project.form.openshot_path, self.parent.project.theme))
			item.set_properties(pixbuf = imgTrack_Left_Hover.get_pixbuf())

			# update play video variable
			self.play_video = True

		# mark project as modified
		self.parent.project.set_project_modified(is_modified=True, refresh_xml=True, type=_("Changed visibility of track"))


		return False
	
	
	def on_audio_click (self, item, target, event):

		# get the parent left group
		parent_group = item.get_parent()
		

		if self.play_audio == True:
			# Load Hover Over
			imgTrack_Left_Hover = gtk.image_new_from_file("%s/openshot/themes/%s/speaker_mute.png" % (self.parent.project.form.openshot_path, self.parent.project.theme))
			item.set_properties(pixbuf = imgTrack_Left_Hover.get_pixbuf())
			
			# update play audio variable
			self.play_audio = False
			
		else: 
			# Load normal image
			imgTrack_Left_Hover = gtk.image_new_from_file("%s/openshot/themes/%s/speaker.png" % (self.parent.project.form.openshot_path, self.parent.project.theme))
			item.set_properties(pixbuf = imgTrack_Left_Hover.get_pixbuf())
			
			# update play audio variable
			self.play_audio = True

		# mark project as modified
		self.parent.project.set_project_modified(is_modified=True, refresh_xml=True, type=_("Changed audio of track"))

		return False

		
	def on_focus_in (self, item, target, event):
		isinstance(item, goocanvas.Image)		
		id = item.get_data ("id")
		
		if event.button == 3:
			# show the track popup menu
			self.parent.project.form.mnuTrack1.showmnu(event, self)

		if id == "normal":
			# Load Hover Over
			imgTrack_Left_Hover = gtk.image_new_from_file("%s/openshot/themes/%s/Track_Left_Hover.png" % (self.parent.project.form.openshot_path, self.parent.project.theme))
			item.set_properties(pixbuf = imgTrack_Left_Hover.get_pixbuf())
			item.set_data("id", "hover")
		else: 
			# Load normal image
			imgTrack_Left_Hover = gtk.image_new_from_file("%s/openshot/themes/%s/Track_Left.png" % (self.parent.project.form.openshot_path, self.parent.project.theme))
			item.set_properties(pixbuf = imgTrack_Left_Hover.get_pixbuf())
			item.set_data("id", "normal")


		return False
	
	
	def reorder_clips(self):
		# get a list of all clips on this track
		self.clips.sort(self.compare_clip)
		
		
	def compare_clip(self, MyClip1, MyClip2):
		if MyClip1.position_on_track > MyClip2.position_on_track:
			return 1
		elif MyClip1.position_on_track == MyClip2.position_on_track:
			return 0
		else:
			return -1

		
	def reorder_transitions(self):
		# get a list of all clips on this track
		self.transitions.sort(self.compare_transitions)
		
		
	def compare_transitions(self, MyClip1, MyClip2):
		if MyClip1.position_on_track > MyClip2.position_on_track:
			return 1
		elif MyClip1.position_on_track == MyClip2.position_on_track:
			return 0
		else:
			return -1