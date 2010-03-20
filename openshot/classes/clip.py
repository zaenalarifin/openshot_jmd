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

import effect
import os, locale, uuid
import xml.dom.minidom as xml
import gtk, goocanvas
from classes.keyframe import keyframe

########################################################################
class clip:
	"""This class represents a media clip on the timeline."""

	#----------------------------------------------------------------------
	def __init__(self, clip_name, color, position_on_track, start_time, end_time, parent_track, file_object):
		"""Constructor"""
		
		# init variables for clip object
		self.name = clip_name		   # the name of the clip
		self.color = color			  # the color of the clip, used to organize clips
		self.start_time = start_time	# the time in seconds where we start playing a clip
		self.end_time = end_time		# the time in seconds where we stop playing a clip
		self.speed = 1.0			# the rate of playback (this will change if you want to slow down or speed up the clip)
		self.max_length = self.length()		# this is the max length of the clip in seconds
		self.position_on_track = float(position_on_track)  # the time in seconds to start playing the clip relative to the track
		self.play_video = True
		self.play_audio = True
		self.fill = True
		self.distort = False
		self.composite = True
		self.halign = "centre"
		self.valign = "centre"
		self.reversed = False
		self.volume = 100.0
		self.audio_fade_in = False
		self.audio_fade_out = False
		self.audio_fade_amount = 2.0
		self.video_fade_in = False
		self.video_fade_out = False
		self.video_fade_amount = 2.0
		self.parent = parent_track	  # the parent track this clip lives on
		self.file_object = file_object  # the file object that this clip is linked to
		self.unique_id = str(uuid.uuid1())
		
		# init key-frame dictionary
		self.keyframes = {"start" : keyframe(0, 100.0, 100.0, 0.0, 0.0, 1.0),
						  "end" : keyframe(-1, 100.0, 100.0, 0.0, 0.0, 1.0)}
		
		# init effects dictionary
		self.effects = []
		
		# For example:  imagine a clip that is 30 seconds long.  If we wanted to only play a 10 second section (from 15 to 25 
		# second range) of this clip, and we wanted the 10 second section to start playing 3 seconds into the tracks timeline, 
		# here are the settings you would need on the clip:
		#
		# REMEMBER: All values are in seconds (of type float... and thus they contain decimals)
		# length = 10.0
		# start_time = 15.0
		# end_time = 25.0
		# position_on_track = 3.0
		

	def length(self):
		# calculate the length of this clip (in decimal seconds)
		length = self.end_time - self.start_time
		
		# return length
		return length
	
	def Add_Effect(self, service):
		# Add an effect (and it's default params) to the effect list
		# Only add an effect if it's not already on the clip

		# Get list of effects
		my_effects = self.parent.parent.project.form.effect_list
		
		# Look up default params
		for my_effect in my_effects:
			# find matching effect
			if my_effect.service == service or my_effect.service + ":" + my_effect.audio_effect == service:
				# get list of default params
				default_params = my_effect.get_default_params()
				
				# create new effect object
				new_effect = effect.effect(service, default_params)
				
				# ADD EFFECT TO CLIP
				self.effects.append(new_effect)
				self.parent.parent.project.set_project_modified(is_modified=True, refresh_xml=True, type = _("Added effect") + " " + service)

	
	def Remove_Effect(self, unique_id):
		# Remove an effect from the list
		
		# loop through clip's effects
		for my_effect in self.effects:
			# is effect already here?
			if my_effect.unique_id == unique_id:
				# remove from list
				self.effects.remove(my_effect)
				return

	def Move_Effect(self, unique_id, direction):
		# Move an effect UP or Down (if possible)
		
		# loop through clip's effects
		for my_effect in self.effects:
			# is effect already here?
			if my_effect.unique_id == unique_id:
				# get index of item
				my_index = self.effects.index(my_effect)
				
				# direction
				if direction == "up" and my_index > 0:
					# up
					self.effects.remove(my_effect)
					self.effects.insert(my_index-1, my_effect)
					return
					
				elif direction=="down" and my_index < len(self.effects) - 1:
					# down
					self.effects.remove(my_effect)
					self.effects.insert(my_index+1, my_effect)
					return


	
	def get_speed(self):
		# calculate the speed multiplier
		if self.speed < 0.0:
			return 1.0 / abs(self.speed)
		else:
			return self.speed

	
	def Render(self):

		# Render the clip to the timeline
		self.RenderClip()
		
	
	def GeneratePreviewXML(self, file_name):
		import track, files
		
		# get locale info
		lc, encoding = locale.getdefaultlocale()
		
		# get the project
		project = self.parent.parent.project
		
		# get frames per second
		fps = project.fps()

		#### PROJECT XML ####
		# Create the XML document
		dom = xml.Document()
		dom.encoding = encoding

		# Add the root element
		westley_root = dom.createElement("mlt")
		dom.appendChild(westley_root)
		tractor1 = dom.createElement("tractor")
		tractor1.setAttribute("id", "tractor0")
		westley_root.appendChild(tractor1)
		
		#### SEQUENCE XML ####
		multitrack = dom.createElement("multitrack")
		tractor1.appendChild(multitrack)
		
		# create fake background track (i.e. black background)
		parent_sequence = self.parent.parent
		bg_track = track.track("Background Track", parent_sequence)
		bg_track.parent = parent_sequence
		#bg_end_time = parent_sequence.Calculate_Length()
		bg_image = files.OpenShotFile(project)
		bg_image.name = os.path.join(project.IMAGE_DIR, "black.png")
		#bg_image.length = bg_end_time
		bg_image.length = self.length()
		bg_image.max_frames = round(bg_image.length * fps)
		bg_clip = clip("Background Clip", "Gold", 0.0, 0.0, bg_image.length, bg_track, bg_image)
		bg_clip.distort = True
		bg_clip.fill = True
		bg_track.clips.append(bg_clip)
		
		# add XML for background track
		bg_track.GenerateXML(dom, multitrack, fps=fps)
		
		#### TRACK XML ####
		#### needs to have the same # of the tracks as the real project ####
		# loop through each track, from the bottom up
		for MyTrack in reversed(parent_sequence.tracks):
			
			playlist = dom.createElement("playlist")
			playlist.setAttribute("id", MyTrack.name)
			multitrack.appendChild(playlist)

			#### CLIP XML ####
			if self.parent == MyTrack:
				self.GenerateXML(dom, playlist, current_frame=0, preview_mode=True, fps=fps)
		
		# Save the XML dom
		f = open(file_name, "w")
		dom.writexml(f, encoding=encoding)
		f.close()
	 
	 
	def GenerateXML(self, dom, xmlParentNode, current_frame=0, preview_mode=False, fps=None):

		# get the project
		project = self.parent.parent.project

		# init the frame offset
		frame_offset = 0
		
		# calculate what the new frame number is (and the size of the gap from the previous clip)
		new_frame = round(self.position_on_track * fps)
		
		# determine if frames overlap
		if current_frame != 0 and current_frame == new_frame:
			# prevent clips from overlapping (calculate offset)
			frame_offset = 1
		elif current_frame != 0 and new_frame < current_frame:
			# prevent small gaps
			frame_offset = (current_frame - new_frame) + 1
		else:
			frame_offset = 0
		
		# set the current frame (plus the offset, to prevent overlapping frames)
		if current_frame == 0:
			frame_gap = ((new_frame + frame_offset) - current_frame)
		else:
			frame_gap = ((new_frame + frame_offset) - current_frame) - 1
			
		current_frame = new_frame + frame_offset
		
		# get the root tractor node 
		tractor_node = dom.getElementsByTagName("tractor")[0]
		
		# determine how much blank space to insert (if any)
		if preview_mode == False:
			#blank = round(self.get_blank_space() * fps)
			blank = frame_gap

			if blank > 1:
				# add blank xml node
				blank_node = dom.createElement("blank")
				blank_node.setAttribute("length", str(blank))
				xmlParentNode.appendChild(blank_node)
		
		# calculate IN and OUT frames (based on the # of seconds)
		in_frame_number = round(self.start_time * fps)
		out_frame_number = round(self.end_time * fps) - 1

		# determine length of this clip
		ending_frame = current_frame + (out_frame_number - in_frame_number)
		#ending_frame = ending_frame - frame_offset

		#print "ending_frame: %s" % ending_frame
		#print "... calc position: %s" % round(self.position_on_track * fps)
		#print "... calc end: %s" % round((self.position_on_track + self.length()) * fps)

		# create the clip producer node
		producer = dom.createElement("producer")
		producer.setAttribute("id", self.name)
		producer.setAttribute("in", str(in_frame_number))
		producer.setAttribute("out", str(out_frame_number))
		
		# hide video (if needed)
		if self.play_video == False or self.parent.play_video == False:
			if self.file_object.file_type == "video":
				# hide video of this producer
				producer.setAttribute("video_index", "-1")
			elif self.file_object.file_type == "image" or self.file_object.file_type == "image sequence":
				# hide image
				blank_node = dom.createElement("blank")
				blank_node.setAttribute("length", str(ending_frame-current_frame))
				xmlParentNode.appendChild(blank_node)
				return ending_frame
		
		# image sequence options
		if self.file_object.file_type == "image sequence":
			producer.setAttribute("ttl", locale.str(self.file_object.ttl))
		xmlParentNode.appendChild(producer)
		
		# add the FRAMEBUFFER (IF NEEDED) to the producer node
		resource_name = self.file_object.name

		if self.get_speed() != 1.0 or self.reversed:
			# create frame buffer to speed up or down the video
			property = dom.createElement("property")
			property.setAttribute("name", "mlt_service")
			text = dom.createTextNode("framebuffer")
			property.appendChild(text)
			producer.appendChild(property)
			
			# append the speed to the resource name
			speed_string = locale.str(self.get_speed())
			
			# reverse video?
			if self.reversed:
				# add a negative sign
				speed_string = "-" + speed_string
				
			# update resource speed
			resource_name = resource_name + "?" + speed_string
		
		# Get the track index (i.e. track 0, 1, 2, 3, etc...)
		if self.parent.name != "Background Track":
			
			# add the RESOURCE to the producer node
			property = dom.createElement("property")
			property.setAttribute("name", "resource")
			text = dom.createTextNode(resource_name)
			property.appendChild(text)
			producer.appendChild(property)
			
			# get the current track #
			track_index = self.parent.parent.tracks.index(self.parent) + 1
			
			# Flip the index (since we want 0 on the bottom)
			track_index_flipped = (len(self.parent.parent.tracks) - track_index) + 1
			
		else:
			# set the background track index
			track_index = len(self.parent.parent.tracks)
			track_index_flipped = 0
			
			# create colour producer
			property = dom.createElement("property")
			property.setAttribute("name", "resource")
			text = dom.createTextNode(resource_name)
			property.appendChild(text)
			producer.appendChild(property)

		
		############################
		# Add VOLUME filter
		############################
	
		# Get clip index.  Subtract this from the IN / OUT frame.  This is
		# to correct a problem with the blank space (in the XML) getting offset from the composites
		# for some reason.  Not really sure, but this seems to fix it. =)
		#clip_index = self.parent.clips.index(self) + 1
	
		# get the IN / OUT frame for the Transistion (absolute frame # of the project)
		#trans_in_frame_number = round(self.position_on_track * fps) - 1 # + clip_index
		#trans_out_frame_number = trans_in_frame_number + round(self.length() * fps) #+ clip_index
		
		# determine all COMPOSITES that are needed
		#trans_in_frame_number = round(self.position_on_track * fps)
		#trans_out_frame_number = round((self.position_on_track + self.length()) * fps)
		trans_in_frame_number = current_frame
		trans_out_frame_number = ending_frame
		
		# don't allow 0 frame
		#if trans_in_frame_number <= 0:
		#	trans_in_frame_number = 1
			
		current_audio_frame = trans_in_frame_number
		
		
		if self.play_audio == False or self.parent.play_audio == False:
			# MUTE
			filter = dom.createElement("filter")
			filter.setAttribute("mlt_service", "volume")
			filter.setAttribute("in", str(trans_in_frame_number))
			filter.setAttribute("out", str(trans_out_frame_number))
			filter.setAttribute("track", str(track_index_flipped))
			filter.setAttribute("gain", locale.str(0))
			
			# add volume filter to tractor
			tractor_node.appendChild(filter)
		else:

			# any fade in?
			if self.audio_fade_in:
				
				# FADE IN
				filter = dom.createElement("filter")
				filter.setAttribute("mlt_service", "volume")
				filter.setAttribute("in", str(current_audio_frame))
				if current_audio_frame + (self.audio_fade_amount * fps) <= trans_out_frame_number:
					# ADD FADE AMOUNT
					current_audio_frame = current_audio_frame + round(self.audio_fade_amount * fps)
					filter.setAttribute("out", str(current_audio_frame))
				else:
					# ADJUST FADE AMOUNT TO FIT SMALLER TIME
					current_audio_frame = trans_out_frame_number
					filter.setAttribute("out", str(current_audio_frame))
				filter.setAttribute("track", str(track_index_flipped))
				filter.setAttribute("gain", locale.str(0))
				filter.setAttribute("end", locale.str(self.volume / 100))
				
				# add volume filter to tractor
				tractor_node.appendChild(filter)
				
				
			# SET REGULAR VOLUME (length between the 2 fade volume nodes)
			if self.audio_fade_out and current_audio_frame < (trans_out_frame_number - (self.audio_fade_amount * fps)):
				# MIDDLE TO FADE_OUT
				
				filter = dom.createElement("filter")
				filter.setAttribute("mlt_service", "volume")
				filter.setAttribute("in", str(current_audio_frame))
				current_audio_frame = trans_out_frame_number - round(self.audio_fade_amount * fps)
				filter.setAttribute("out", str(current_audio_frame))
				filter.setAttribute("track", str(track_index_flipped))
				filter.setAttribute("gain", locale.str(self.volume / 100))
				
				# add volume filter to tractor
				tractor_node.appendChild(filter)

				
			elif current_audio_frame < trans_out_frame_number:
				# MIDDLE TO END

				filter = dom.createElement("filter")
				filter.setAttribute("mlt_service", "volume")
				filter.setAttribute("in", str(current_audio_frame))
				current_audio_frame = trans_out_frame_number
				filter.setAttribute("out", str(current_audio_frame))
				filter.setAttribute("track", str(track_index_flipped))
				filter.setAttribute("gain", locale.str(self.volume / 100))
				
				# add volume filter to tractor
				tractor_node.appendChild(filter)

			
			# SET FADE OUT
			if self.audio_fade_out and current_audio_frame < trans_out_frame_number:

				# FADE OUT
				filter = dom.createElement("filter")
				filter.setAttribute("mlt_service", "volume")
				filter.setAttribute("in", str(current_audio_frame))
				current_audio_frame = trans_out_frame_number
				filter.setAttribute("out", str(current_audio_frame))
				filter.setAttribute("track", str(track_index_flipped))
				filter.setAttribute("gain", locale.str(self.volume / 100))
				filter.setAttribute("end", locale.str(0))
				
				# add volume filter to tractor
				tractor_node.appendChild(filter)



		# Add EFFECTS
		for my_effect in self.effects:
			# Generate XML for each effect
			my_effect.GenerateXML(dom, tractor_node, current_frame, ending_frame, track_index_flipped)

		
		
		if track_index_flipped > 0:
			##############################
			#         COMPOSITE
			#############################
			self.GenerateComposites(dom, current_frame, ending_frame, preview_mode, fps=fps)

			
			##############################
			#			 MIX
			##############################
			
			transition = dom.createElement("transition")
			transition.setAttribute("in", str(trans_in_frame_number))
			transition.setAttribute("out", str(trans_out_frame_number))
			
			property = dom.createElement("property")
			property.setAttribute("name", "mlt_service")
			text = dom.createTextNode("mix")
			property.appendChild(text)
			transition.appendChild(property)
			
			property = dom.createElement("property")
			property.setAttribute("name", "a_track")
			text = dom.createTextNode("0")
			property.appendChild(text)
			transition.appendChild(property)
			
			property = dom.createElement("property")
			property.setAttribute("name", "b_track")
			text = dom.createTextNode(str(track_index_flipped))
			property.appendChild(text)
			transition.appendChild(property)
			
			# These 2 properties combine the audio from 2 tracks equally
			property = dom.createElement("property")
			property.setAttribute("name", "combine")
			text = dom.createTextNode("1")
			property.appendChild(text)
			transition.appendChild(property)
			
			property = dom.createElement("property")
			property.setAttribute("name", "always_active")
			text = dom.createTextNode("1")
			property.appendChild(text)
			transition.appendChild(property)

			# add composite transition to tractor
			tractor_node.appendChild(transition)
			
			# return # of frames for this clip
			return ending_frame
			

	def GenerateComposites(self, dom, in_current_frame, in_ending_frame, preview_mode=False, fps=None):
		# get the project
		project = self.parent.parent.project
		
		overlapping_transitions = []
		has_left = None
		has_right = None
		has_entire = None
		has_inside = []	# list of inside transitions
		
		if preview_mode == False:
			# find transitions / masks that overlap this clip (on this track)
			for t in self.parent.transitions:
				
				# does transition overlap clip?
				overlap, part_of_clip = self.DoesTransitionOverlap(t)
	
				if overlap:
					# OVERLAPS
					# set flags
					if part_of_clip == "left":
						has_left = t
					elif part_of_clip == "right":
						has_right = t
					elif part_of_clip == "inside":
						has_inside.append(t)
					elif part_of_clip == "entire":
						has_entire = t
				
		# determine all COMPOSITES that are needed
		#current_frame = round(self.position_on_track * fps)
		#end_frame = round((self.position_on_track + self.length()) * fps)
		current_frame = in_current_frame 
		end_frame = in_ending_frame
		
		### IF ENTIRE CLIP IS OVERLAPPED, ADD JUST 1 TRANSITION
		if has_entire:
			# add just 1 transition (which is the length of the clip)
			self.CreateCompositeXML(dom, current_frame, end_frame, "entire", has_entire, fps=fps)
			
		else:
			# NOT OVERLAPPING THE ENTIRE CLIP
			####### ADD FADE IN / OR LEFT TRANSITION ######
			if has_left:
				# LEFT TRANSITION
				end = round((has_left.position_on_track + has_left.length) * fps)
				self.CreateCompositeXML(dom, current_frame, end, "left", has_left, fps=fps)
				current_frame = end
			elif self.video_fade_in:
				# LEFT FADE IN
				end = current_frame + round((self.video_fade_amount) * fps)
				if end > end_frame:
					end = end_frame
				self.CreateCompositeXML(dom, current_frame, end, "fade in", fps=fps)
				current_frame = end
	
				
				
			### LOOP THROUGH EACH INSIDE TRANSITION ###
			for t in has_inside:
				
				trans_begin_frame = round(t.position_on_track * fps)
				trans_end_frame = round((t.position_on_track + t.length) * fps)
				
				if current_frame < trans_begin_frame:
					# add filler
					self.CreateCompositeXML(dom, current_frame, trans_begin_frame, "filler", fps=fps)
				
				# add transition
				current_frame = trans_begin_frame
				end = trans_end_frame
				self.CreateCompositeXML(dom, current_frame, end, "inside", t, fps=fps)
				current_frame = end
	
	
	
			####### ADD FADE OUT / OR RIGHT TRANSITION ######
			if has_right:
				# RIGHT TRANSITION
				trans_begin_frame = round(has_right.position_on_track * fps)
				trans_end_frame = round((has_right.position_on_track + has_right.length) * fps)
				
				if current_frame < trans_begin_frame:
					# add filler
					self.CreateCompositeXML(dom, current_frame, trans_begin_frame, "filler", fps=fps)
	
				# add transition
				current_frame = trans_begin_frame
				end = end_frame
				self.CreateCompositeXML(dom, current_frame, end, "right", has_right, fps=fps)
				current_frame = end
	
			elif self.video_fade_out:
				# FADE OUT
				begin_of_fade_out = end_frame - round(self.video_fade_amount * fps)
				if current_frame < begin_of_fade_out:
					# add filler
					self.CreateCompositeXML(dom, current_frame, begin_of_fade_out, "filler", fps=fps)
				elif current_frame > begin_of_fade_out:
					# shorten the fade (if needed)
					begin_of_fade_out = current_frame
				
				current_frame = begin_of_fade_out
				end = end_frame
				self.CreateCompositeXML(dom, current_frame, end, "fade out", fps=fps)
				current_frame = end
				
				
			#### ADD FINAL FILLER, IF NEEDED ####
			if current_frame < end_frame:
				# add filler
				self.CreateCompositeXML(dom, current_frame, end_frame, "filler", fps=fps)
			
			
	def CreateCompositeXML(self, dom, current_frame, end_frame, comment, t = None, fps = None):

		# get the frames per second (from the project)
		project = self.parent.parent.project

		# dont' add composite for a "filler" (if requested)
		if self.composite == False and comment == "filler":
			return
		
		# get length and geometry key frames of clip (in frames)
		clip_length_frames = self.length() * fps
		kf_start = self.keyframes["start"]
		kf_end = self.keyframes["end"]

		h1, h2 = self.get_keyframe_values("height", current_frame, end_frame, fps, clip_length_frames, kf_start, kf_end)
		w1, w2 = self.get_keyframe_values("width", current_frame, end_frame, fps, clip_length_frames, kf_start, kf_end)
		x1, x2 = self.get_keyframe_values("x", current_frame, end_frame, fps, clip_length_frames, kf_start, kf_end)
		y1, y2 = self.get_keyframe_values("y", current_frame, end_frame, fps, clip_length_frames, kf_start, kf_end)
		a1, a2 = self.get_keyframe_values("alpha", current_frame, end_frame, fps, clip_length_frames, kf_start, kf_end)

		# get the root tractor node 
		tractor_node = dom.getElementsByTagName("tractor")[0]
		
		# get the IN / OUT frame for the Transistion (absolute frame # of the project)
		trans_in_frame_number = current_frame
		trans_out_frame_number = end_frame
		
		# Get the track index (i.e. track 0, 1, 2, 3, etc...)
		if self.parent.name != "Background Track":
			track_index = self.parent.parent.tracks.index(self.parent) + 1
			
			# Flip the index (since we want 0 on the bottom)
			track_index_flipped = (len(self.parent.parent.tracks) - track_index) + 1
		else:
			track_index = len(self.parent.parent.tracks)
			track_index_flipped = 0
		
		transition = dom.createElement("transition")
		transition.setAttribute("in", str(round(trans_in_frame_number)))
		transition.setAttribute("out", str(round(trans_out_frame_number)))
		
		property = dom.createElement("property")
		property.setAttribute("name", "mlt_service")
		text = dom.createTextNode("composite")
		property.appendChild(text)
		transition.appendChild(property)
		
		property = dom.createElement("property")
		property.setAttribute("name", "a_track")
		text = dom.createTextNode("0")
		property.appendChild(text)
		transition.appendChild(property)
		
		property = dom.createElement("property")
		property.setAttribute("name", "b_track")
		text = dom.createTextNode(str(track_index_flipped))
		property.appendChild(text)
		transition.appendChild(property)
		
		if t == None:
			# NOT A TRANSITION
			if comment == "fade in":
				a1 = 0.0
				#a2 = 1.0
			if comment == "fade out":
				#a1 = 1.0
				a2 = 0.0

		else:
			# TRANSITION
			if t.type == "transition":
				# TRANSITION
				if t.reverse:
					# DOWN
					a1 = 1.0
					a2 = 0.0
				else:
					# UP
					a1 = 0.0
					a2 = 1.0
			elif t.type == "mask":
				# MASK
				a1 = t.mask_value / 100
				a2 = t.mask_value / 100
		
		geometry_start = "%d=%s%%,%s%%:%s%%x%s%%:%s; " % (0, locale.str(x1), locale.str(y1), locale.str(w1), locale.str(h1), locale.str(a1 * 100.0))
		geometry_end = "%d=%s%%,%s%%:%s%%x%s%%:%s; " % (-1, locale.str(x2), locale.str(y2), locale.str(w2), locale.str(h2), locale.str(a2 * 100.0))
		geometry = geometry_start + geometry_end

		property = dom.createElement("property")
		property.setAttribute("name", "geometry")
		text = dom.createTextNode(geometry)
		property.appendChild(text)
		transition.appendChild(property)
		
		property = dom.createElement("property")
		property.setAttribute("name", "halign")
		text = dom.createTextNode(self.halign)
		property.appendChild(text)
		transition.appendChild(property)
		
		property = dom.createElement("property")
		property.setAttribute("name", "valign")
		text = dom.createTextNode(self.valign)
		property.appendChild(text)
		transition.appendChild(property)
		
		property = dom.createElement("property")
		property.setAttribute("name", "distort")
		text = None
		if self.distort:
			text = dom.createTextNode("1")
		else:
			text = dom.createTextNode("0")
		property.appendChild(text)
		transition.appendChild(property)

		property = dom.createElement("property")
		property.setAttribute("name", "fill")
		text = None
		if self.fill:
			text = dom.createTextNode("1")
		else:
			text = dom.createTextNode("0")
		property.appendChild(text)
		transition.appendChild(property)
		
		# Is this a transition?
		if t:
			property = dom.createElement("property")
			property.setAttribute("name", "luma")
			text = dom.createTextNode(t.resource)
			property.appendChild(text)
			transition.appendChild(property)
			
			property = dom.createElement("property")
			property.setAttribute("name", "softness")
			text = dom.createTextNode(locale.str(t.softness))
			property.appendChild(text)
			transition.appendChild(property)
		
		# add composite transition to tractor
		tractor_node.appendChild(transition)
				
				

	def get_keyframe_values(self, prop_name, current_frame, end_frame, fps, clip_length_frames, kf_start, kf_end):
		
		# get the frames per second (from the project)
		project = self.parent.parent.project
		
		if prop_name == "height":
			prop_start = kf_start.height
			prop_end = kf_end.height
		elif prop_name == "width":
			prop_start = kf_start.width
			prop_end = kf_end.width
		elif prop_name == "x":
			prop_start = kf_start.x
			prop_end = kf_end.x
		elif prop_name == "y":
			prop_start = kf_start.y
			prop_end = kf_end.y
		elif prop_name == "alpha":
			prop_start = kf_start.alpha
			prop_end = kf_end.alpha
			
		# get difference in values (if any)
		prop_diff = prop_end - prop_start
		
		if prop_diff != 0:
			# calculate height at this point in the clip
			units = prop_diff / clip_length_frames
			new_prop_start = prop_start + (current_frame - (self.position_on_track * fps)) * units
			new_prop_end =  prop_start + (end_frame - (self.position_on_track * fps)) * units
		else:
			new_prop_start = prop_start
			new_prop_end = prop_end
			
		return new_prop_start, new_prop_end
		

	def DoesTransitionOverlap(self, transition):
		""" Determine if a transition overlaps a clip """
		overlap = False
		part_of_clip = ""
		
		transition_left_edge = transition.position_on_track
		transition_right_edge = transition.position_on_track + transition.length
		clip_left_edge = self.position_on_track
		clip_right_edge = self.position_on_track + self.length()
		
		
		####### DOES TRANSITION OVERLAP ######

		# is the left edge of the transition inside the clip boundries?
		if transition_left_edge >= clip_left_edge and transition_left_edge <= clip_right_edge:
			overlap = True
			if transition_left_edge == clip_left_edge:
				part_of_clip = "left"
			if transition_right_edge >= clip_right_edge:
				part_of_clip = "right"
			
		# is the right edge of the transition inside the clip boundries?
		if transition_right_edge >= clip_left_edge and transition_right_edge <= clip_right_edge:
			overlap = True
			if transition_left_edge <= clip_left_edge:
				part_of_clip = "left"
			if transition_right_edge == clip_right_edge:
				part_of_clip = "right"
				
		# does the transition completely overlap the clip boundries?
		if transition_left_edge < clip_left_edge and transition_right_edge > clip_right_edge:
			overlap = True
			part_of_clip = "entire"
			
		# Default to 'inside' clip, if no match found
		if overlap==True and part_of_clip == "":
			part_of_clip = "inside"

		# return overlap decision
		return overlap, part_of_clip

	#----------------------------------------------------------------------
	def RenderClip(self, item = None, x_offset = 0, y_offset = 0):
		"""This adds a clip to the canvas with 3 images: a left, middle, and right.  If an goocanvas item is passed in,
		this method will simply re-size the inner images.  If no goocanvas item is passed in, it will create one. The reason
		this method is slightly complicated is due to the resize / trim clip feature, since it has to toggle between the small
		version of a clip and the 3 image version."""

		# get the previous track from the parent sequence (if any)
		pixels_per_second = self.parent.parent.get_pixels_per_second()
		x = float(self.position_on_track * pixels_per_second) + x_offset
		y = self.parent.y_top + 2 + y_offset

		# get a reference to the 2 main canvas objects & theme
		theme = self.parent.parent.project.theme

		# load clip images
		imgTrack_Middle = gtk.image_new_from_file("%s/openshot/themes/%s/Clip_Middle_%s.png" % (self.parent.parent.project.form.openshot_path, theme, self.color))
		imgTrack_Left = gtk.image_new_from_file("%s/openshot/themes/%s/Clip_Left_%s.png" % (self.parent.parent.project.form.openshot_path, theme, self.color))
		imgTrack_Right = gtk.image_new_from_file("%s/openshot/themes/%s/Clip_Right_%s.png" % (self.parent.parent.project.form.openshot_path, theme, self.color))
		
		# get height & width of left image
		imgTrack_Left_Height = imgTrack_Left.get_pixbuf().get_height()
		imgTrack_Left_Width = imgTrack_Left.get_pixbuf().get_width()
		imgTrack_Right_Width = imgTrack_Right.get_pixbuf().get_width()
		
		# Get Size of Window (to determine how wide the middle image should be streched)
		Size_Of_Middle = (self.length() * pixels_per_second) - (imgTrack_Left_Width + imgTrack_Right_Width) + 6
		total_pixel_length = int(self.length() * pixels_per_second) + 1
		has_small_images = False
		has_regular_images = False
		
		# Get the canvas group for this clip
		if item:
			# set the group object
			GroupClip = item
			
			# set the unique ID of the group
			GroupClip.set_data ("id", self.unique_id)
			
			if self.get_canvas_child(item, "small_middle"):
				has_small_images = True
				
			if self.get_canvas_child(item, "left"):
				has_regular_images = True
				
		else:
			# canvas group is not passed in
			# Get root group of the canvas
			canvas_right = self.parent.parent.project.form.MyCanvas
			root_right = canvas_right.get_root_item ()
			
			# Create the Group (for the clip)
			GroupClip = goocanvas.Group (parent = root_right)
			
			# set the unique ID of the group
			GroupClip.set_data ("id", self.unique_id)
			
			# connect drag n drop events to the new cavnas group
			GroupClip.connect ("motion_notify_event", self.on_motion_notify_x)
			GroupClip.connect ("button_press_event", self.on_button_press_x)
			GroupClip.connect ("button_release_event", self.on_button_release_x)
		
		

		# for clips that are too small to use the 3 image approach, just use
		# the middle image, and don't add a thumbnail
		if total_pixel_length < imgTrack_Left_Width + imgTrack_Right_Width + 60:

			# ///////////////////////////////////////////////////////
			# Add ONLY the MIDDLE Image to Group
			# ///////////////////////////////////////////////////////

			# Resize Middle pixbuf to be the entire length of the clip
			middlePixBuf = imgTrack_Middle.get_pixbuf()
			pixbuf_list = self.parent.parent.split_images(middlePixBuf, imgTrack_Left_Height, total_pixel_length)

			# Add Middle Image to Group (this can be multiple image tiled together
			pixbuf_x = 0.0
			for pixbuf in pixbuf_list:
				# get width of this pixbuf
				pixbuf_width = pixbuf.get_width()
				pixbuf_height = pixbuf.get_height()
				
				# Add the middle image
				if item == None or has_small_images == False:
					# Create the small image items (since they don't exist yet)
					# create middle canvas image object
					image2 = goocanvas.Image (parent = GroupClip,
										  pixbuf = pixbuf,
										  x = x + pixbuf_x,
										  y = y)  
					image2.set_data ("id", "small_middle")
					
					# Add a translucent blue rectab
					rec2 = goocanvas.Rect (parent = GroupClip,
										  x = x + pixbuf_x,
										  y = y,
										  width = pixbuf_width,
										  height = pixbuf_height,
										  line_width = 0.85,
										  stroke_color_rgba = 1401402500)
					rec2.set_data ("id", "small_rect")

					# create new canvas text object
					if has_regular_images == False:
						
						text_width = pixbuf_width
						if text_width - 8 <= 15:
							text_width = 1
						else:
							text_width = text_width - 8
						
						text1 = goocanvas.Text (parent = GroupClip,
											text = "%s" % self.name,
											font = "Sans 8",
											antialias = False,
											x = x + 8,
											y = y + 2,
											width = text_width,
											ellipsize = 3)
						text1.set_data ("id", "clip_name")
						
						# determine if text has enough width to be visible
						if text_width == 1:
							text1.set_properties(visibility = 1)
						
					else:
						# get existing text
						text1 = self.get_canvas_child(item, "clip_name")

						
				elif has_small_images:
					# resize existing canvas image object
					self.get_canvas_child(item, "small_middle").set_properties(visibility = 2)
					self.get_canvas_child(item, "small_middle").set_properties(pixbuf = pixbuf)
					self.get_canvas_child(item, "small_middle").set_properties(x = x + pixbuf_x)
					
					self.get_canvas_child(item, "small_rect").set_properties(visibility = 2)
					self.get_canvas_child(item, "small_rect").set_properties(x = x + pixbuf_x)
					self.get_canvas_child(item, "small_rect").set_properties(width = pixbuf_width)
					
					text_width = pixbuf_width
					if text_width - 8 <= 15:
						text_width = 1
						# hide clip name
						self.get_canvas_child(item, "clip_name").set_properties(visibility = 1)
					else:
						text_width = text_width - 8
						# show clip name
						self.get_canvas_child(item, "clip_name").set_properties(visibility = 2)
						
					# resize clip name
					self.get_canvas_child(item, "clip_name").set_properties(x = x + 8)
					self.get_canvas_child(item, "clip_name").set_properties(width = text_width)
				
				
				# hide the left, right, and middle, text, and thumbnail items (if any)
				if has_regular_images:
					self.get_canvas_child(item, "middle").set_properties(visibility = 1)
					self.get_canvas_child(item, "left").set_properties(visibility = 1)
					self.get_canvas_child(item, "right").set_properties(visibility = 1)
					self.get_canvas_child(item, "thumbnail").set_properties(visibility = 1)
					self.get_canvas_child(item, "clip_visible").set_properties(visibility = 1)
					self.get_canvas_child(item, "clip_speaker").set_properties(visibility = 1)
					#self.get_canvas_child(item, "clip_name").set_properties(visibility = 1)
					if self.effects:
						self.get_canvas_child(item, "effect").set_properties(visibility = 1)
					# raise the clip text (since it can get hidden by other clip-related layers)
					self.get_canvas_child(item, "clip_name").raise_(None)
					

				# increment the x
				pixbuf_x = pixbuf_x + pixbuf_width
			
		else:
			
			# hide the small version of the clip (if any)
			if has_small_images:
				
				# hide the smaller version, if it exists
				self.get_canvas_child(item, "small_middle").set_properties(visibility = 1)
				self.get_canvas_child(item, "small_rect").set_properties(visibility = 1)


			# ///////////////////////////////////////////////////////
			# Add MIDDLE Image to Group
			# ///////////////////////////////////////////////////////

			# Resize Middle pixbuf
			#if len(self.pixbuf_list)  == 0:
			middlePixBuf = imgTrack_Middle.get_pixbuf()
			pixbuf_list = self.parent.parent.split_images(middlePixBuf, imgTrack_Left_Height, int(Size_Of_Middle))

			
			# Remove OLD MIDDLE group
			if has_regular_images:
				# get existing object
				GroupMiddle = self.get_canvas_child(item, "middle")

				# remove old middle group
				parent = GroupMiddle.get_parent()
				child_num = parent.find_child (GroupMiddle)
				parent.remove_child (child_num)
			
			# create middle group (since there can be many tiled images)
			GroupMiddle = goocanvas.Group (parent = GroupClip)
			GroupMiddle.set_data ("id", "middle")
			GroupMiddle.lower(None)
			

			# Add Middle Image to Group (this can be multiple image tiled together
			pixbuf_x = 0
			for pixbuf in pixbuf_list:
				# get width of this pixbuf
				pixbuf_width = pixbuf.get_width()

				# create middle canvas image object
				image2 = goocanvas.Image (parent = GroupMiddle,
									  pixbuf = pixbuf,
									  x = (x + imgTrack_Left_Width - 3) + pixbuf_x,
									  y = y) 
				

				#image2.set_properties(x = (x + imgTrack_Left_Width - 3) + pixbuf_x)
				image2.set_properties(y = y)


				# increment the x
				pixbuf_x = pixbuf_x + pixbuf_width
					

				
			# ///////////////////////////////////////////////////////
			# Add LEFT Image to Group
			# ///////////////////////////////////////////////////////
			if has_regular_images == False:

				# create canvas image object
				imageLeft = goocanvas.Image (parent = GroupClip,
									  pixbuf = imgTrack_Left.get_pixbuf(),
									  x = x,
									  y = y)  

				imageLeft.set_data ("id", "left")
				
			else:
				# get existing object
				existing_item = self.get_canvas_child(item, "left")
				
				# resize existing canvas image object
				existing_item.set_properties(x = x)
				existing_item.set_properties(visibility = 2)
				
				

			# ///////////////////////////////////////////////////////
			# Add RIGHT Image to Group
			# ///////////////////////////////////////////////////////
			if has_regular_images == False:
				
				# create canvas image object
				imageRight = goocanvas.Image (parent = GroupClip,
									  pixbuf = imgTrack_Right.get_pixbuf(),
									  x = x + imgTrack_Left_Width + Size_Of_Middle - 5,
									  y = y)
				
				imageRight.set_data ("id", "right")
				
			else:
				# get existing object
				existing_item = self.get_canvas_child(item, "right")
				
				# resize existing canvas image object
				existing_item.set_properties(x = x + imgTrack_Left_Width + Size_Of_Middle - 5)
				existing_item.set_properties(visibility = 2)
				

				
			# ///////////////////////////////////////////////////////
			# Add THUMBNAIL Image to Group
			# ///////////////////////////////////////////////////////	 
			if has_regular_images == False:
				# get the thumbnail image
				pbThumb = self.file_object.get_thumbnail(38, 35)
				
				# create canvas image object
				imgThumb = goocanvas.Image (parent = GroupClip,
									pixbuf = pbThumb,
									x = x + 6,
									y = y + 16)
				
				imgThumb.set_data ("id", "thumbnail")
				
			else:
				# get existing object
				existing_item = self.get_canvas_child(item, "thumbnail")
				
				# re-position existing canvas image object
				existing_item.set_properties(x = x + 6)
				existing_item.set_properties(visibility = 2)
				
				
			# ///////////////////////////////////////////////////////
			# Add BUTTONS Image to Group
			# ///////////////////////////////////////////////////////	
			
			# *** VISIBLE BUTTONS
			if has_regular_images == False:
			
				# Load buttons
				if self.play_video:
					imgTrack_Visible = gtk.image_new_from_file("%s/openshot/themes/%s/visible_transparent.png" % (self.parent.parent.project.form.openshot_path, theme))
				else:
					imgTrack_Visible = gtk.image_new_from_file("%s/openshot/themes/%s/not_visible_transparent.png" % (self.parent.parent.project.form.openshot_path, theme))
					
				# Add Visible Image to Group
				image5 = goocanvas.Image (parent = GroupClip,
										  pixbuf = imgTrack_Visible.get_pixbuf(),
										  x = x + 46,
										  y = y + 18)  
				
				# Track the state of the hover over image
				image5.set_data ("id", "clip_visible")
				image5.connect ("button_press_event", self.on_visible_click)
				image5.connect ("button_release_event", self.on_clip_buttons_release)
				
				# Get the track index (i.e. track 0, 1, 2, 3, etc...)
				track_index = self.parent.parent.tracks.index(self.parent)
				
				# Flip the index (since we want 0 on the bottom)
				track_index_flipped = (len(self.parent.parent.tracks) - track_index) - 1

					
				
			else:
				# get existing object
				existing_item = self.get_canvas_child(item, "clip_visible")
				
				# resize existing canvas image object
				existing_item.set_properties(x = x + 46)
				existing_item.set_properties(visibility = 2)
				
				# Get the track index (i.e. track 0, 1, 2, 3, etc...)
				track_index = self.parent.parent.tracks.index(self.parent)
				
				# Flip the index (since we want 0 on the bottom)
				track_index_flipped = (len(self.parent.parent.tracks) - track_index) - 1

				
				
			# *** AUDIO BUTTONS
			if has_regular_images == False:
			
				# Load buttons
				if self.play_audio:
					imgTrack_Visible = gtk.image_new_from_file("%s/openshot/themes/%s/speaker_transparent.png" % (self.parent.parent.project.form.openshot_path, theme))
				else:
					imgTrack_Visible = gtk.image_new_from_file("%s/openshot/themes/%s/speaker_mute_transparent.png" % (self.parent.parent.project.form.openshot_path, theme))
					
				# Add Visible Image to Group
				image5 = goocanvas.Image (parent = GroupClip,
										  pixbuf = imgTrack_Visible.get_pixbuf(),
										  x = x + 66,
										  y = y + 18)  
				
				# Track the state of the hover over image
				image5.set_data ("id", "clip_speaker")
				image5.connect ("button_press_event", self.on_audio_click)
				image5.connect ("button_release_event", self.on_clip_buttons_release)
				
			else:
				# get existing object
				existing_item = self.get_canvas_child(item, "clip_speaker")
				
				# resize existing canvas image object
				existing_item.set_properties(x = x + 66)
				existing_item.set_properties(visibility = 2)


			# *** EFFECT IMAGE
			if has_regular_images == False:
			
				# Load buttons
				if self.effects:
					imgTrack_Visible = gtk.image_new_from_file("%s/openshot/themes/%s/effect.png" % (self.parent.parent.project.form.openshot_path, theme))
				
				# Add Visible Image to Group
					image5 = goocanvas.Image (parent = GroupClip,
										  pixbuf = imgTrack_Visible.get_pixbuf(),
										  x = x + 46,
										  y = y + 36)  
				
					# Track the state of the hover over image
					image5.set_data ("id", "effect")
					image5.connect ("button_press_event", self.on_effect_click)
				
			else:
				if self.effects:
					try:				
						# get existing object
						existing_item = self.get_canvas_child(item, "effect")
				
						# resize existing canvas image object
						existing_item.set_properties(x = x + 46)
						existing_item.set_properties(visibility = 2)	
					except:
						pass
	
	
	
	
	
	
				
			# ///////////////////////////////////////////////////////
			# Add TEXT Image to Group
			# ///////////////////////////////////////////////////////
			
			if item == None:
				# create new canvas text object
				text1 = goocanvas.Text (parent = GroupClip,
									text = "%s" % self.name,
									font = "Sans 8",
									antialias = False,
									x = x + 8,
									y = y + 2,
									width = Size_Of_Middle,
									ellipsize = 3)
				
				text1.set_data ("id", "clip_name")
				
			else:
				# get existing object
				existing_item = self.get_canvas_child(item, "clip_name")				
				
				# re-position existing canvas image object
				existing_item.set_properties(x = x + 8)
				existing_item.set_properties(visibility = 2)
				existing_item.set_properties(text = "%s (%s - %s)" % (self.name, round(self.start_time,2), round(self.end_time,2)))
				existing_item.set_properties(width = Size_Of_Middle)
				
		
		# return the clip... this is useful when a new clip is dropped onto the canvas
		return GroupClip
	

	
	def get_canvas_child(self, group, requested_child_id):
		"""this method loops though the children objects of this group looking 
		for the item with a specfic id."""
		
		for index in range(0, group.get_n_children()):
			child = group.get_child(index)
			child_id = child.get_data ("id")

			if child_id == requested_child_id:
				return child
			
		return None
	


	def on_motion_notify_x (self, item, target, event):
		"""this method allows the clip to be dragged and dropped on a track"""	  

		# get the new x,y coordinates from the mouse
		new_x = float(event.x)
		new_y = float(event.y)	
		
		# get the pixels per second from the parent sequence
		pixels_per_second = self.parent.parent.get_pixels_per_second()

		# determine end pixel of sequence
		end_of_timeline = self.parent.parent.length * pixels_per_second

		
		# determine what cursor mode is enable (arrow, razor, snap, etc...)
		(isArrow, isRazor, isSnap, isResize) = self.parent.parent.project.form.get_toolbar_options()
		
		# ARROW MODE
		if isArrow:
			
			# Move the clip based on the x, y of the mouse
			if (event.state & gtk.gdk.BUTTON1_MASK):

				# don't allow the clip to slide past the beginning of the canvas
				total_x_diff = new_x - self.drag_x 
				total_y_diff = new_y - self.drag_y
				if (item.get_bounds().x1 + total_x_diff < 0):
					total_x_diff = 0.0 - float(item.get_bounds().x1)
#				elif (item.get_bounds().x2 + total_x_diff > end_of_timeline):
#					total_x_diff = end_of_timeline - float(item.get_bounds().x2)
	
				# be sure that the clip is being dragged over a valid drop target (i.e. a track)
				if self.is_valid_drop(item.get_bounds().x1 + total_x_diff, item.get_bounds().y1 + total_y_diff):
					# mark project as modified
					self.parent.parent.project.set_project_modified(is_modified=True, refresh_xml=True)

					# move clip
					item.translate (total_x_diff, total_y_diff)
					
		# RESIZE MODE
		if isResize:
			
			
			# update cursor
			self.parent.parent.project.form.current_cursor[1] = int(event.x_root)
			self.parent.parent.project.form.current_cursor[2] = int(event.y_root)
			self.parent.parent.project.form.current_cursor[3] = "clip"
			
			if (event.state & gtk.gdk.BUTTON1_MASK):

				# get the direction from the cursor object
				direction = self.parent.parent.project.form.current_cursor[0]
				
			else:
				# only calculate LEFT or RIGHT when the mouse is not clicked.  Once the user starts resizing
				# a clip, we want to just use the direction in the cursor object.  In other words, we can't allow
				# the direction to change while we are resizing.
				# determine if user is resizing the LEFT or RIGHT side of the clip
				center_of_clip = (self.position_on_track * pixels_per_second) + ((self.length() * pixels_per_second) / 2)
				direction = "left"
				if event.x_root < center_of_clip:
					direction = "left"
				else:
					direction = "right"
				
				# if right, update the cursor the "right grab" icon
				if direction == "right":
					# update cursor variable
					if self.parent.parent.project.form.current_cursor[0] != "right":
	
						# change cursor to "right bar"
						self.parent.parent.project.form.current_cursor[0] = "right"
						self.parent.parent.project.form.MyCanvas.window.set_cursor(gtk.gdk.Cursor(gtk.gdk.RIGHT_SIDE)) 
	
				# if left, update the cursor the "left grab" icon
				if direction == "left":
					# update cursor variable
					if self.parent.parent.project.form.current_cursor[0] != "left":
						
						# change cursor to "left bar"
						self.parent.parent.project.form.current_cursor[0] = "left" 
						self.parent.parent.project.form.MyCanvas.window.set_cursor(gtk.gdk.Cursor(gtk.gdk.LEFT_SIDE))

				
				
			
			# Move the clip based on the x, y of the mouse (if the mouse button is pressed)
			if (event.state & gtk.gdk.BUTTON1_MASK):
				
				# Get side of clip that is being re-sized
				side = self.parent.parent.project.form.current_cursor[0]  # left or right
				
				# Get the x and y difference
				original_end_pos = (self.original_start_pos * pixels_per_second) + (self.original_length * pixels_per_second)
				x_offset = event.x - event.x_root
				y_offset = event.y - event.y_root
				

				if side == "left":
					# calculate new start position and length
					new_position = float(event.x_root) / float(pixels_per_second)
					new_length = float(original_end_pos - event.x_root) / pixels_per_second
					new_start_time = self.end_time - new_length

					# stop the clip from going too far to the left
					if new_start_time < 0:
						new_position = new_position - new_start_time
						new_length = self.end_time
						new_start_time = (self.end_time - new_length)

					# update the properties of this clip
					if new_position >= 0 and new_length >= 0 and new_length <= self.max_length and new_start_time >= 0:
						
						# mark project as modified
						self.parent.parent.project.set_project_modified(is_modified=True, refresh_xml=True)
						
						self.position_on_track = new_position
						self.start_time = new_start_time
						
						# adjust x for windows
						if os.name == 'nt':
							x_offset = x_offset - 2
							
						# re-render this clip to the canvas (passing the canvas group to the RenderClip method)
						self.RenderClip(item, x_offset, y_offset)
						
						# UPDATE VIDEO PREVIEW
						self.preview_seek("left")

				else:
					# RIGHT side
					# calculate the new clip length
					new_length = (event.x_root - (self.position_on_track * pixels_per_second)) / pixels_per_second
					new_end_time = self.start_time + new_length

					# prevent the clip from resizing too far to the right
					if self.start_time + new_length > self.max_length:
						new_end_time = self.max_length
						new_length = new_end_time - self.start_time

					# update the properties of this clip
					if new_length > 0 and new_end_time > 0 and new_length <= self.max_length and new_end_time <= self.max_length:
						self.end_time = new_end_time
						
						# mark project as modified
						self.parent.parent.project.set_project_modified(is_modified=True, refresh_xml=True)

						# re-render this clip to the canvas (passing the canvas group to the RenderClip method)
						self.RenderClip(item, x_offset, y_offset)

						# UPDATE VIDEO PREVIEW
						self.preview_seek("right")
				
		return True
	

	def update(self, x, y, parent_track):
			""" This method updates the x and y settings of the clip in the object model """			
			# get the pixels per second from the parent sequence
			pixels_per_second = self.parent.parent.get_pixels_per_second()

			# update the position of the clip   
			self.position_on_track = float(x) / float(pixels_per_second)

			# remove clip from current parent track (if new parent is different)
			if (parent_track != self.parent):
				# remove clip				
				self.parent.clips.remove(self)
				
				# add to new parent track
				parent_track.clips.append(self)
				self.parent = parent_track

	
	
	def on_button_press_x (self, item, target, event):
		""" This method initializes some variables needed for dragging and dropping a clip """
		# raise the group up to the top level
		item.raise_(None)
		self.parent.parent.raise_transitions()
		self.parent.parent.play_head.raise_(None)
		self.parent.parent.play_head_line.raise_(None)
		
		# set the x and y where the cursor started dragging from
		self.drag_x = float(event.x)
		self.drag_y = float(event.y)

		# only respond to the first mouse button
		if event.button == 1:
			# determine what cursor mode is enable (arrow, razor, snap, etc...)
			(isArrow, isRazor, isSnap, isResize) = self.parent.parent.project.form.get_toolbar_options()
			
			# ARROW MODE
			if isArrow:
				
				# CHECK FOR DOUBLE-CLICK
				if event.type == gtk.gdk._2BUTTON_PRESS: 
					# Load preview of clip
					# get the current frame
					self.timeline_current_position = self.parent.parent.project.form.MyVideo.p.position()
					self.show_preview = True

					# re-load the xml (if not an audio file)
					self.parent.parent.project.form.MyVideo.set_project(self.parent.parent.project, self.parent.parent.project.form, os.path.join(self.parent.parent.project.USER_DIR, "sequence.mlt"), mode="override", override_path=self.file_object.name)
					self.parent.parent.project.form.MyVideo.load_xml()
					
					# start and stop the video
					self.parent.parent.project.form.MyVideo.play()
				else:
					# don't show preview
					self.show_preview = False

					
				
				if event.state & gtk.gdk.SHIFT_MASK:
					# remove clip from goocanvas
					parent = item.get_parent()
					child_num = parent.find_child (item)
					parent.remove_child (child_num)
					
					# remove clip from parent track
					self.parent.clips.remove(self)
					
					# mark project as modified
					self.parent.parent.project.set_project_modified(is_modified=True, refresh_xml=True)
					
				else:
					# change the cursor for the drag n drop operation
					fleur = gtk.gdk.Cursor (gtk.gdk.FLEUR)
					canvas = item.get_canvas ()
					self.stored_x = item.get_bounds().x1
					self.stored_y = item.get_bounds().y1
					canvas.pointer_grab (item, gtk.gdk.POINTER_MOTION_MASK | gtk.gdk.BUTTON_RELEASE_MASK, fleur, event.time)

			
			# RAZOR MODE
			elif isRazor:
				# Divide the clip into 2 clips at the x position of the cursor
				self.divide_clip(event.x_root, item)
				pass

			# RESIZE MODE
			elif isResize:
				# switch video window to preview mode (i.e. override mode)
				self.set_preview_mode()
				
				# remember the original length and position before resizing starts
				self.original_length = self.length()
				self.original_start_pos = self.position_on_track
				self.original_clip_in = self.start_time
				self.original_clip_out = self.end_time
				pass

			# SNAP MODE
			elif isSnap:
				pass
			
		elif event.button == 3:
			# show the track popup menu
			self.parent.parent.project.form.mnuClip1.showmnu(event, self, item)
 
		return True
	
	
	def set_preview_mode(self):
		#print "set_preview_mode"
		# get the current frame
		self.timeline_current_position = self.parent.parent.project.form.MyVideo.p.position()

		# re-load the xml (if not an audio file)
		if (self.file_object.file_type == "video" or self.file_object.file_type == "image sequence") and self.speed == 1.0:
			self.parent.parent.project.form.MyVideo.set_project(self.parent.parent.project, self.parent.parent.project.form, os.path.join(self.parent.parent.project.USER_DIR, "sequence.mlt"), mode="override", override_path=self.file_object.name)
			self.parent.parent.project.form.MyVideo.load_xml()
			
			# start and stop the video
			self.parent.parent.project.form.MyVideo.play()
			self.parent.parent.project.form.MyVideo.pause()
		
		
	def set_view_mode(self):
		#print "set_view_mode"
		
		# update project as modified (to restore the timeline view)
		if (self.file_object.file_type == "video" or self.file_object.file_type == "image sequence") and self.speed == 1.0:
			self.parent.parent.project.set_project_modified(is_modified=True, refresh_xml=True)
	
			# Refresh the MLT XML file
			self.parent.parent.project.RefreshXML()
			
			# start and stop the video
			self.parent.parent.project.form.MyVideo.play()
			self.parent.parent.project.form.MyVideo.pause()
			
			# seek back to original position
			self.parent.parent.project.form.MyVideo.seek(int(self.timeline_current_position))

		
	def preview_seek(self, side):
		#print "preview_seek"
		
		# get the frames per second (from the project)
		if (self.file_object.file_type == "video" or self.file_object.file_type == "image sequence") and self.speed == 1.0:
			fps = self.parent.parent.project.fps()
	
			# calculate IN and OUT frames (based on the # of seconds)
			frame = 0
			if side=="left":
				frame = self.start_time * fps
			else:
				frame = self.end_time * fps
			
			# seek to the new frame
			self.parent.parent.project.form.MyVideo.seek(int(frame))
		
	
	def divide_clip(self, x, canvas_item):
		"""Divide a clip into to smaller clips at a specific x coordinate"""
		# get the pixels per second from the parent sequence
		pixels_per_second = self.parent.parent.get_pixels_per_second()
		seconds_for_x = x / pixels_per_second
		original_clip_length = self.length()
		original_end_time = self.end_time

		# remove clip from goocanvas
		parent = canvas_item.get_parent()
		child_num = parent.find_child (canvas_item)
		parent.remove_child (child_num)

		# Modify the 1st clip, and render it to the screen
		self.end_time = (seconds_for_x - self.position_on_track) + self.start_time
		self.RenderClip()

		# calculate the 2nd clip properties
		new_start_time = self.end_time
		new_end_time = original_end_time

		# Create the 2nd clip object
		SecondClip = self.parent.AddClip(self.name, self.color, seconds_for_x, new_start_time, new_end_time, self.file_object, record_to_history = None)
		SecondClip.max_length = self.max_length
		SecondClip.fill = self.fill
		SecondClip.distort = self.distort
		SecondClip.composite = self.composite
		SecondClip.speed = self.speed
		SecondClip.play_video = self.play_video
		SecondClip.play_audio = self.play_audio
		SecondClip.halign = self.halign
		SecondClip.valign = self.valign
		SecondClip.reversed = self.reversed
		SecondClip.volume = self.volume
		SecondClip.audio_fade_in = self.audio_fade_in
		SecondClip.audio_fade_out = self.audio_fade_out
		SecondClip.audio_fade_amount = self.audio_fade_amount
		SecondClip.video_fade_in = self.video_fade_in
		SecondClip.video_fade_out = self.video_fade_out
		SecondClip.video_fade_amount = self.video_fade_amount

		# render new clip
		SecondClip.RenderClip()
		
		# re-order clip objects on track (since they might be out of order now)
		self.parent.reorder_clips()
		
		# mark project as modified
		self.parent.parent.project.set_project_modified(is_modified=True, refresh_xml=True, type = _("Sliced clip"))
					

	def get_snap_difference(self, clip_object, canvas_item):
		"""Determine the number of pixels to shift this clip to snap to it's 
		closest neighbor clip (if any)"""

		# get the pixels per second from the parent sequence
		pixels_per_second = clip_object.parent.parent.get_pixels_per_second()
		old_x = clip_object.position_on_track * pixels_per_second  # get the old x coordinate of the clip (used to determine direction)

		# get the index of this clip (from the parent collection)
		clip_index = clip_object.parent.clips.index(clip_object)
		clip_length = clip_object.length() * pixels_per_second
		closest_clip = None
		distance_from_clip = 0.0
		distance_from_left_clip = 0.0
		distance_from_right_clip = 0.0
		distance_from_playhead = 0.0
		
		# determine the direction of the drag
		direction = ""
		if canvas_item.get_bounds().x1 < old_x:
			direction = "left"
		else:
			direction = "right"
		
		# if there is a clip to the left of this one, find the distance to it's edge
		if (clip_index - 1) >= 0 and (clip_index - 1) < len(clip_object.parent.clips):
			closest_clip = clip_object.parent.clips[clip_index - 1]
			clip_x = closest_clip.position_on_track * pixels_per_second
			closest_clip_length = closest_clip.length() * pixels_per_second
			closest_clip_position = clip_x + closest_clip_length
			distance_from_left_clip = closest_clip_position - canvas_item.get_bounds().x1

		# if there is a clip to the right of this one, find the distance to it's edge
		if (clip_index + 1) >= 0 and (clip_index + 1) < len(clip_object.parent.clips):
			closest_clip = clip_object.parent.clips[clip_index + 1]
			closest_clip_position = closest_clip.position_on_track * pixels_per_second
			distance_from_right_clip = closest_clip_position - (canvas_item.get_bounds().x1 + clip_length)
			
		# distance from the play-head
		playhead_time = clip_object.parent.parent.play_head_position
		playhead_pixels = playhead_time * pixels_per_second
		distance_from_playhead = playhead_pixels - canvas_item.get_bounds().x1
		

		# limit the left /right snapping to 10 pixels
		if distance_from_left_clip > 10 or distance_from_left_clip < -10:
			distance_from_left_clip = 0.0
		if distance_from_right_clip > 10 or distance_from_right_clip < -10:
			distance_from_right_clip = 0.0
		if distance_from_playhead > 10 or distance_from_playhead < -10:
			distance_from_playhead = 0.0

		# determine which direction and what clip to snap to (based on the direction the clip is moving)
		if direction == "left" and distance_from_left_clip != 0:
			distance_from_clip = distance_from_left_clip
		elif direction == "right" and distance_from_right_clip != 0:
			distance_from_clip = distance_from_right_clip
		elif distance_from_left_clip != 0:
			distance_from_clip = distance_from_left_clip
		elif distance_from_right_clip != 0:
			distance_from_clip = distance_from_right_clip
		elif distance_from_playhead != 0:
			distance_from_clip = distance_from_playhead

		# return the # of pixesl to snap the clip
		return distance_from_clip
	
	
	def get_blank_space(self):
		"""Determine the number of seconds between this clip and the nearest clip to the left."""
		
		blank_seconds = 0.0
		
		# Get clip info
		clip_index = self.parent.clips.index(self)
		clip_position = self.position_on_track
		clip_length = self.length()
		
		# is a clip to the left?
		if (clip_index - 1) >= 0:
			left_clip = self.parent.clips[clip_index - 1]
			left_clip_position = left_clip.position_on_track
			left_clip_length = left_clip.length()
			
			# difference between left clip and current position
			return clip_position - (left_clip_position + left_clip_length)
		
		else:
			# no left clip, so diff the beginning of timeline vs current position
			return clip_position
	

	def on_button_release_x (self, item, target, event):
		""" This method drops a clip, and snaps the clip to the nearest valid track """
		
		
		# get reference to the canvas, and stop dragging the item
		canvas = item.get_canvas()
		canvas.pointer_ungrab (item, event.time)
		
		# determine what cursor mode is enable (arrow, razor, snap, etc...)
		(isArrow, isRazor, isSnap, isResize) = self.parent.parent.project.form.get_toolbar_options()
		
		if isArrow:

			# get new parent track
			drop_track = self.get_valid_drop(item.get_bounds().x1, item.get_bounds().y1)
			
			# update clip's settings to reflect the new x, y position (and update the parent track)
			self.update(item.get_bounds().x1, item.get_bounds().y1, drop_track)
			drop_track.reorder_clips()  
	
			# deterime the direction of the drag
			if isSnap:
				distance_from_clip = self.get_snap_difference(self, item)
			else:
				distance_from_clip = 0.0
				
			# move the clip object on the timeline to correct position (snapping to the y and x of the track)		
			item.translate (distance_from_clip, drop_track.y_top - item.get_bounds().y1 + 2)
			
			# update clip's settings again (since the snapping could have moved them a bit)
			self.update(item.get_bounds().x1, item.get_bounds().y1, drop_track)
			
			# check if clip has been really moved or not
			if ((self.stored_x == item.get_bounds().x1) and (self.stored_y == item.get_bounds().y1)):
				type_of_event = None
			else:
				type_of_event = _("Moved clip")
			
			self.parent.parent.project.set_project_modified(is_modified=True, refresh_xml=True, type = type_of_event)
	
			
		elif isResize:
			
			# remove clip from goocanvas
			parent = item.get_parent()
			child_num = parent.find_child (item)
			parent.remove_child (child_num)			
			
			# re-render the clip at it's new size
			self.RenderClip()
			
			# switch video window back to 'view' mode (i.e. remove preview clip mode)
			self.set_view_mode()
			self.parent.parent.project.set_project_modified(is_modified=True, refresh_xml=True, type = _("Resized clip"))
				
		# check if the timeline needs to be expanded
		self.parent.parent.project.form.expand_timeline(self)
		
		# reset the cursor
		self.parent.parent.project.form.MyCanvas.window.set_cursor(None)

		
		
	def is_valid_drop(self, x1, y1):
		""" Check to see if the current position is a valid drop position """

		# loop through each track
		for track in self.parent.parent.tracks:

			# get the top y and bottom y of each track
			y_top = track.y_top
			y_bottom = track.y_bottom
			
			# get the middle of the clip
			half_height_of_clip = 26
			middle_position = half_height_of_clip + y1
			
			# determine if middle of clip is contained inside this track
			if middle_position > y_top and middle_position < y_bottom:
				return True

		# return false if no valid track found
		return False
	
	
	def get_valid_drop(self, x1, y1):
		""" A clip must be dropped on a track.  This method returns the track 
		object that is under the clip's current position """

		# loop through each track
		for track in self.parent.parent.tracks:
			# get the top y and bottom y of each track
			y_top = track.y_top
			y_bottom = track.y_bottom
			
			# get the middle of the clip
			half_height_of_clip = 26
			middle_position = half_height_of_clip + y1
			
			# determine if middle of clip is contained inside this track
			if middle_position > y_top and middle_position < y_bottom:
				return track
		
		# return false if no valid track found
		return None
		
		
	def on_visible_click (self, item, target, event):
		# get a reference to the 2 main canvas objects & theme
		theme = self.parent.parent.project.theme
		
		# get the parent left group
		parent_group = item.get_parent()
		canvas = parent_group.get_canvas()
		canvas.pointer_ungrab (item, event.time)
		
		if self.play_video == True:
			# Load Hover Over
			imgTrack_Visible = gtk.image_new_from_file("%s/openshot/themes/%s/not_visible_transparent.png" % (self.parent.parent.project.form.openshot_path, theme))
			item.set_properties(pixbuf = imgTrack_Visible.get_pixbuf())

			# update play video variable
			self.play_video = False
			
		else: 
			# Load normal image
			imgTrack_Visible = gtk.image_new_from_file("%s/openshot/themes/%s/visible_transparent.png" % (self.parent.parent.project.form.openshot_path, theme))
			item.set_properties(pixbuf = imgTrack_Visible.get_pixbuf())

			# update play video variable
			self.play_video = True

		# mark project as modified
		self.parent.parent.project.set_project_modified(is_modified=True, refresh_xml=True, type = _("Changed visibility of clip"))

		return False
	
	
	def on_audio_click (self, item, target, event):
		# get a reference to the 2 main canvas objects & theme
		theme = self.parent.parent.project.theme
		
		# get the parent left group
		parent_group = item.get_parent()
		canvas = parent_group.get_canvas()
		canvas.pointer_ungrab (item, event.time)
		
		if self.play_audio == True:
			# Load Hover Over
			imgTrack_Visible = gtk.image_new_from_file("%s/openshot/themes/%s/speaker_mute_transparent.png" % (self.parent.parent.project.form.openshot_path, theme))
			item.set_properties(pixbuf = imgTrack_Visible.get_pixbuf())
			
			# update play video variable
			self.play_audio = False
			
		else: 
			# Load normal image
			imgTrack_Visible = gtk.image_new_from_file("%s/openshot/themes/%s/speaker_transparent.png" % (self.parent.parent.project.form.openshot_path, theme))
			item.set_properties(pixbuf = imgTrack_Visible.get_pixbuf())
			
			# update play video variable
			self.play_audio = True

		# mark project as modified
		self.parent.parent.project.set_project_modified(is_modified=True, refresh_xml=True, type = _("Changed audio of clip"))

		return False
	
	def on_effect_click (self, item, target, event):
		pass
		#form1 = self.parent.parent.project.form
		#from windows import ClipProperties
		#form1.frmClipProperties = ClipProperties.frmClipProperties(form=form1, project=self.parent.parent.project, current_clip=self, current_clip_item=item)
		#return True
	
	def on_clip_buttons_release(self, item, target, event):
		return True
		
	#----------------------------------------------------------------------
	def __setstate__(self, state):
		""" This method is called when an OpenShot project file is un-pickled (i.e. opened).  It can
		    be used to update the structure of old clip classes, to make old project files compatable with
		    newer versions of OpenShot. """
	
		# Check for missing DEBUG attribute (which means it's an old project format)
		if 'effects' not in state:
			state['effects'] = []
			
		if 'speed' not in state:
			state['speed'] = 1.0

		# update the state object with new schema changes
		self.__dict__.update(state)
		
		
		
		
		
		
		
