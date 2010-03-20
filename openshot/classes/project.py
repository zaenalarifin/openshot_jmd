#	OpenShot Video Editor is a program that creates, modifies, and edits video files.
#   Copyright (C) 2009  Jonathan Thomas, TJ
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

import os, sys, locale
import gtk
import xml.dom.minidom as xml
from classes import profiles, files, thumbnail, open_project, save_project, state_project, restore_state, sequences, video

# init the foreign language
from language import Language_Init

########################################################################
class project():
	"""This is the main project class that contains all
	the details of a project, such as name, folder, timeline
	information, sequences, media files, etc..."""

	#----------------------------------------------------------------------
	def __init__(self, init_threads=True):
		"""Constructor"""
		
		# debug message/function control
		self.DEBUG = True
		
		# define common directories containing resources
		# get the base directory of the openshot installation for all future relative references
		# Note: don't rely on __file__ to be an absolute path. E.g., in the debugger (pdb) it will be
		# a relative path, so use os.path.abspath()
		self.BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
		self.GLADE_DIR = os.path.join(self.BASE_DIR, "openshot", "windows", "glade")
		self.IMAGE_DIR = os.path.join(self.BASE_DIR, "openshot", "images")
		self.LOCALE_DIR = os.path.join(self.BASE_DIR, "openshot", "locale")
		self.PROFILES_DIR = os.path.join(self.BASE_DIR, "openshot", "profiles")
		self.TRANSITIONS_DIR = os.path.join(self.BASE_DIR, "openshot", "transitions")
		self.EXPORT_PRESETS_DIR = os.path.join(self.BASE_DIR, "openshot", "export_presets")
		self.EFFECTS_DIR = os.path.join(self.BASE_DIR, "openshot", "effects")
		# location for per-session, per-user, files to be written/read to
		self.DESKTOP = os.path.join(os.path.expanduser("~"), "Desktop")
		self.USER_DIR = os.path.join(os.path.expanduser("~"), ".openshot")
		self.THEMES_DIR = os.path.join(self.BASE_DIR, "openshot", "themes")
		self.USER_PROFILES_DIR = os.path.join(self.USER_DIR, "user_profiles")

		# only run the following code if we are really using 
		# this project file... 
		if init_threads:

			# Add language support
			translator = Language_Init.Translator(self)
			_ = translator.lang.gettext
			
			# init the variables for the project
			from windows import preferences
			self.name = _("Default Project")
			self.folder = self.USER_DIR
			self.project_type = preferences.Settings.general["default_profile"]
			self.theme = preferences.Settings.general["default_theme"]
			self.canvas = None
			self.is_modified = False
			self.refresh_xml = True
			self.mlt_profile = None
			
			# reference to the main GTK form
			self.form = None
			
			# init the file / folder list (used to populate the tree)
			self.project_folder = files.OpenShotFolder(self)
	
			# ini the sequences collection
			self.sequences = [sequences.sequence(_("Default Sequence 1"), self)]		
	
			# init the tab collection
			self.tabs = [self.sequences[0]]	  # holds a refernce to the sequences, and the order of the tabs
	
			# clear temp folder
			self.clear_temp_folder()
			
			# create thumbnailer object
			self.thumbnailer = thumbnail.thumbnailer()
			self.thumbnailer.set_project(self)
			self.thumbnailer.start()

		
	def fps(self):
		# get the profile object
		if self.mlt_profile == None:
			self.mlt_profile = profiles.mlt_profiles(self).get_profile(self.project_type)

		# return the frames per second
		return self.mlt_profile.fps()
	
	

	def clear_temp_folder(self):
		"""This method deletes all files in the /openshot/temp folder."""
		path = os.path.join(self.USER_DIR)
		
		# get pid from lock file
		pidPath = os.path.join(path, "pid.lock")
		pid=int(open(pidPath, 'r').read().strip())
		
		# thumbnail path
		thumbnail_path = os.path.join(path, "thumbnail")

		# clear all files / folders recursively in the thumbnail folder
		if os.getpid() == pid:
			# only clear this folder for the primary instance of OpenShot
			self.remove_files(thumbnail_path)
		
		# create thumbnail folder (if it doesn't exist)
		if os.path.exists(thumbnail_path) == False:
			# create new thumbnail folder
			os.mkdir(thumbnail_path)


	def remove_files(self, path):

		# verify this folder exists
		if os.path.exists(path):
			
			# loop through all files in this folder
			for child_path in os.listdir(path):
				# get full child path
				child_path_full = os.path.join(path, child_path)
				
				if os.path.isdir(child_path_full) == True:
					# remove items in this folder
					self.remove_files(child_path_full)
					
					# remove folder
					os.removedirs(child_path_full)
				else:
					# remove file
					os.remove(child_path_full)
			
			
	#----------------------------------------------------------------------
	def __setstate__(self, state):
		""" This method is called when an OpenShot project file is un-pickled (i.e. opened).  It can
		    be used to update the structure of the old project class, to make old project files compatable with
		    newer versions of OpenShot. """
	
		# Check for missing DEBUG attribute (which means it's an old project format)
		#if 'DEBUG' not in state:
		# create empty new project class
		empty_project = project(init_threads=False)
		
		state['DEBUG'] = empty_project.DEBUG
		state['BASE_DIR'] = empty_project.BASE_DIR
		state['GLADE_DIR'] = empty_project.GLADE_DIR
		state['IMAGE_DIR'] = empty_project.IMAGE_DIR
		state['LOCALE_DIR'] = empty_project.LOCALE_DIR
		state['PROFILES_DIR'] = empty_project.PROFILES_DIR
		state['TRANSITIONS_DIR'] = empty_project.TRANSITIONS_DIR
		state['EXPORT_PRESETS_DIR'] = empty_project.EXPORT_PRESETS_DIR
		state['EFFECTS_DIR'] = empty_project.EFFECTS_DIR
		state['USER_DIR'] = empty_project.USER_DIR
		state['DESKTOP'] = empty_project.DESKTOP
		state['THEMES_DIR'] = empty_project.THEMES_DIR
		state['USER_PROFILES_DIR'] = empty_project.USER_PROFILES_DIR
		state['refresh_xml'] = True
		state['mlt_profile'] = None
		
		empty_project = None

		# update the state object with new schema changes
		self.__dict__.update(state)


	#----------------------------------------------------------------------
	def Render(self):
		"""This method recursively renders all the tracks and clips on the timeline"""
		
		# Render the timeline
		self.sequences[0].Render()
		
		# Render Play Head (and position line)
		self.sequences[0].RenderPlayHead()
		
		
	def GenerateXML(self, file_name):
		"""This method creates the MLT XML used by OpenShot"""
		
		# get locale info
		lc, encoding = locale.getdefaultlocale()

		# Create the XML document
		dom = xml.Document()
		dom.encoding = encoding

		# Add the root element
		westley_root = dom.createElement("mlt")
		dom.appendChild(westley_root)
		tractor1 = dom.createElement("tractor")
		tractor1.setAttribute("id", "tractor0")
		westley_root.appendChild(tractor1)
		
		# Add all the other timeline objects (such as sequences, clips, filters, and transitions)
		self.sequences[0].GenerateXML(dom, tractor1)
		
		# Save the XML dom
		f = open(file_name, "w")
		dom.writexml(f, encoding=encoding)
		f.close()
		
		# reset project as NOT modified
		self.refresh_xml = False


	#----------------------------------------------------------------------
	def RefreshXML(self):
		""" Generate a new MLT XML file (if needed).  This only creates a
		new XML file if the timeline has changed. """
		
		# has the project timeline been modified (i.e. new clips, re-arranged clips, etc...)
		if self.refresh_xml:
			
			# update cursor to "wait"
			self.form.timelinewindowRight.window.set_cursor(gtk.gdk.Cursor(150))
			self.form.timelinewindowRight.window.set_cursor(gtk.gdk.Cursor(150))
			
			# generate a new MLT XML file
			self.GenerateXML(os.path.join(self.USER_DIR, "sequence.mlt"))

			# ****************************
			# re-load the xml
			if self.form.MyVideo:
				# store current frame position
				prev_position = self.form.MyVideo.p.position()

				self.form.MyVideo.set_project(self, self.form, os.path.join(self.USER_DIR, "sequence.mlt"), mode="preview")
				self.form.MyVideo.load_xml()

				# restore position
				self.form.MyVideo.p.seek(prev_position)
				
				# refresh sdl
				self.form.MyVideo.c.set("refresh", 1)

			else:
				# create the video thread
				# Force SDL to write on our drawing area
				os.putenv('SDL_WINDOWID', str(self.form.videoscreen.window.xid))
				
				# We need to flush the XLib event loop otherwise we can't
				# access the XWindow which set_mode() requires
				gtk.gdk.flush()

				# play the video in it's own thread
				self.form.MyVideo = video.player(self, self.form, os.path.join(self.USER_DIR, "sequence.mlt"), mode="preview")
				self.form.MyVideo.start()
			# ****************************
			
			# update cursor to normal
			self.form.timelinewindowRight.window.set_cursor(None)
			
		else:
			pass

	
	#----------------------------------------------------------------------
	def Save(self, file_path):
		"""Call the save method of this project, which will 
		persist the project to the file system."""
		
		# get preferences to see whether to save in binary or ascii form
		from windows import preferences
		self.file_type = preferences.Settings.general["project_file_type"]
		
		# call the save method
		save_project.save_project(self, file_path)
		
	#----------------------------------------------------------------------
	def Open(self, file_path):
		"""Call the open method, which will open an existing
		project file from the file system."""
			
		# call the open method
		open_project.open_project(self, file_path)
		self.set_project_modified(is_modified=True, refresh_xml=False, type=_("Opened project"))	

		
	def set_project_modified(self, is_modified=False, refresh_xml=False, type=None):
		"""Set the modified status and accordingly the save button sensitivity"""
		self.is_modified = is_modified
		self.refresh_xml = refresh_xml

		if is_modified == True:
			self.form.tlbSave.set_sensitive(True)
			### test undo : debug
			if type:
				self.form.save_project_state(type)
		else:
			self.form.tlbSave.set_sensitive(False)
			
	
	def State(self):
		state = state_project.save_state(self)
		return state
	state = property(State)
	
	
	def restore(self, state):
		
		# Restore State
		restore_state.restore_project_state(self, state)
				
		