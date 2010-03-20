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


import os, sys
import operator
import copy
import re
import gtk, gtk.glade
import goocanvas
import pango
import webbrowser
import shutil

import classes.effect as effect
from classes import files, lock, messagebox, open_project, project, timeline, tree, video, inputbox, av_formats
from windows import About, FileProperties, NewProject, OpenProject, preferences, Profiles
from windows.SimpleGladeApp import SimpleGladeApp
from windows import AddFiles, ClipProperties, ExportVideo, ImportImageSeq, Titles, TransitionProperties, TreeFiles, TreeTransitions, TreeEffects, TreeHistory

# init the foreign language
from language import Language_Init



# Main window of OpenShot
class frmMain(SimpleGladeApp):


	def __init__(self, path="Main.glade", root="frmMain", domain="OpenShot", project=None, version="0.0.0", **kwargs):
		"""Init the main window"""

		# Load the Glade form using the SimpleGladeApp module	
		SimpleGladeApp.__init__(self, os.path.join(project.GLADE_DIR, path), root, domain, **kwargs)

		# Add language support
		_ = Language_Init.Translator(project).lang.gettext
		self._ = _
		
		# project instance
		self.project = project
		self.project.form = self
		self.MyVideo = None
		self.version = version
		self.is_exiting = False
		self.is_edit_mode = False
		self.is_maximized = False
		
		# initializes history stack
		self.history_stack = []
		
		# determine the directory OpenShot is running in.  This is used 
		# to correctly load images, themes, etc...
		self.openshot_path = self.project.BASE_DIR

		# variable for timeline drag n drop
		self.dragging = False
		self.timeline_clip_y = 0
		
		# Init Effects List
		self.effect_list = effect.get_effects(self.project)
		
		# Init track variables
		self.AllTracks = []
		(self.CurrentTrack_X, self.CurrentTrack_Y) = 10, 10
		(self.Scroll_Vertical_Value, self.Scroll_Horizontal_Value) = 10, 10

		# Create the Canvas Widget
		hboxTimeline = self.scrolledwindow_Left
		isinstance(hboxTimeline, gtk.HBox)

		# Get reference to the window
		self.App1Window = self.frmMain
		isinstance(self.App1Window, gtk.Window)

		# Create new GooCanvas (and add to form)
		self.MyCanvas_Left = goocanvas.Canvas()
		self.MyCanvas_Left.connect("scroll-event", self.on_scrolledwindow_Left_scroll_event)
		self.MyCanvas_Left.set_size_request (160, 0)
		self.MyCanvas_Left.set_bounds (0, 0, 160, 5000)
		self.MyCanvas_Left.show()

		self.MyCanvas = goocanvas.Canvas()
		self.MyCanvas.connect("scroll-event", self.on_scrolledwindow_Right_scroll_event)
		self.MyCanvas.set_bounds (0, 0, 50000, 5000)
		hboxTimeline.set_border_width(0)
		self.MyCanvas.show()
		
		#canvas for the timeline
		self.TimelineCanvas_Left = goocanvas.Canvas()
		self.TimelineCanvas_Left.connect("scroll-event", self.on_scrolledwindow_Left_scroll_event)
		self.TimelineCanvas_Left.set_size_request (160, 0)
		self.TimelineCanvas_Left.set_bounds (0, 0, 50000, 80) #l, t, r, b
		self.TimelineCanvas_Left.show()
		
		self.TimelineCanvas_Right = goocanvas.Canvas()
		self.TimelineCanvas_Right.connect("scroll-event", self.on_scrolledwindow_Right_scroll_event)
		self.TimelineCanvas_Right.set_bounds (0, 0, 160, 5000)
		self.TimelineCanvas_Right.show()

		self.scrolled_win = self.scrolledwindow_Left
		self.scrolled_win.add(self.MyCanvas_Left)
		self.scrolled_win.show()	  

		self.scrolled_win_Right = self.scrolledwindow_Right
		self.scrolled_win_Right.add(self.MyCanvas)
		self.scrolled_win_Right.show()
		
		self.scrolled_win_timeline = self.timelineWindowLeft
		self.scrolled_win_timeline.add(self.TimelineCanvas_Left)
		self.scrolled_win_timeline.show()
		
		self.scrolled_win_timeline_right = self.timelinewindowRight
		self.scrolled_win_timeline_right.add(self.TimelineCanvas_Right)
		self.scrolled_win_timeline_right.show()

		# Add default node to the tree
		self.myTree = self.treeFiles
		treestore = gtk.TreeStore
		NoItemSelected = gtk.TreeIter

		#set multiple selection on the iconview
		self.icvFileIcons.set_selection_mode(gtk.SELECTION_MULTIPLE)

		# ---------------------------------
		self.drag_type = ""
		self.OSTreeFiles = TreeFiles.OpenShotTree(self.treeFiles, self.project)
		self.OSTreeTransitions = None	# this tree is inited in the nbFiles_switch_page signal
		self.OSTreeEffects = None 		# this tree is inited in the nbFiles_switch_page signal
		self.OSTreeHistory = TreeHistory.OpenShotTree(self.treeHistory, self.project)
		# ---------------------------------
		
		#Add a recent projects menu item
		manager = gtk.recent_manager_get_default()
		recent_menu_chooser = gtk.RecentChooserMenu(manager)
		recent_menu_chooser.set_limit(10)
		recent_menu_chooser.set_sort_type(gtk.RECENT_SORT_MRU)
		recent_menu_chooser.set_show_not_found(False)
		recent_menu_chooser.set_show_tips(True)
		filter = gtk.RecentFilter()
		filter.add_pattern("*.osp")
		recent_menu_chooser.add_filter(filter)
		recent_menu_chooser.connect('item-activated', self.recent_item_activated)

		mnurecent = self.mnuRecent
		mnurecent.set_submenu(recent_menu_chooser)

		###################
		
		#load the settings
		self.settings = preferences.Settings(self.project)
		self.settings.load_settings_from_xml()
		
		# limit for the history stack size
		self.max_history_size = int(self.settings.general["max_history_size"])		
		
		#set some application state settings
		x = int(self.settings.app_state["window_width"])
		y = int(self.settings.app_state["window_height"])
		is_max = self.settings.app_state["window_maximized"]

		# resize window		
		self.frmMain.resize(x, y)

		if is_max == "True":
			# maximize window
			self.frmMain.maximize()

		self.vpaned2.set_position(int(self.settings.app_state["vpane_position"]))
		self.hpaned2.set_position(int(self.settings.app_state["hpane_position"]))
		
		if self.settings.app_state["toolbar_visible"] == "True":
			self.tlbMain.show()
		else:
			self.mnuToolbar.set_active(False)
			self.tlbMain.hide()
		
		self.project.project_type = self.settings.general["default_profile"]
		self.project.theme = self.settings.general["default_theme"]
		
		#get the formats/codecs
		melt_command = self.settings.general["melt_command"]
		self.get_avformats(melt_command)
		
		# Show Window
		self.frmMain.show()

		# init the track menu
		self.mnuTrack1 = mnuTrack(None, None, form=self, project=self.project)
		
		# init the clip menu
		self.mnuClip1 = mnuClip(None, None, form=self, project=self.project)
		
		# init the marker menu
		self.mnuMarker1 = mnuMarker(None, None, form=self, project=self.project)
		
		# init the transition menu
		self.mnuTransition1 = mnuTransition(None, None, form=self, project=self.project)
		
		
		# init sub menus
		self.mnuFadeSubMenu1 = mnuFadeSubMenu(None, None, form=self, project=self.project)
		self.mnuAnimateSubMenu1 = mnuAnimateSubMenu(None, None, form=self, project=self.project)
		self.mnuPositionSubMenu1 = mnuPositionSubMenu(None, None, form=self, project=self.project)
		self.mnuClip1.mnuFade.set_submenu(self.mnuFadeSubMenu1.mnuFadeSubMenuPopup)
		self.mnuClip1.mnuAnimate.set_submenu(self.mnuAnimateSubMenu1.mnuAnimateSubMenuPopup)
		self.mnuClip1.mnuPosition.set_submenu(self.mnuPositionSubMenu1.mnuPositionSubMenuPopup)
		
		###################

		self.TARGET_TYPE_URI_LIST = 80
		dnd_list = [ ( 'text/uri-list', 0, self.TARGET_TYPE_URI_LIST ) ]	

		# Enable drag n drop on the Treeview and Canvas
		self.myTree.connect('drag_data_received', self.on_drag_data_received)
		self.myTree.connect("button_release_event", self.on_drop_clip_from_tree)
		self.tree_drag_context = None
		self.tree_drag_time = None
		self.myTree.drag_dest_set( gtk.DEST_DEFAULT_MOTION |
										 gtk.DEST_DEFAULT_HIGHLIGHT | gtk.DEST_DEFAULT_DROP,
								   dnd_list, gtk.gdk.ACTION_COPY)

		self.icvFileIcons.connect('drag_data_received', self.on_drag_data_received)
		self.icvFileIcons.drag_dest_set( gtk.DEST_DEFAULT_MOTION |
										 gtk.DEST_DEFAULT_HIGHLIGHT | gtk.DEST_DEFAULT_DROP,
										 dnd_list, gtk.gdk.ACTION_COPY)
		
		self.icvFileIcons.connect_after('drag_begin', self.on_treeFiles_drag_begin)
		
		
		self.icvFileIcons.enable_model_drag_source(gtk.DEST_DEFAULT_MOTION |
										 gtk.DEST_DEFAULT_HIGHLIGHT | gtk.DEST_DEFAULT_DROP,
										 dnd_list, gtk.gdk.ACTION_COPY)


		self.MyCanvas.drag_dest_set(0, [], 0)
		self.MyCanvas.connect('drag_motion', self.motion_cb)
		self.MyCanvas.connect('drag_drop', self.drop_cb)
		self.MyCanvas.connect('motion_notify_event', self.canvas_motion_notify)
		self.last_files_added = ""
		
		
		
		# track the cursor, and what position it was last changed
		self.current_cursor = [None, 0, 0, ""]  # Cursor Name, X, Y, Cursor Source

		
		# track when a dragged item reaches the goocanvas
		self.item_detected = False
		self.new_clip = None
		self.new_clip_object = None
		self.new_trans_object = None
		
		# Init modified status
		self.project.set_project_modified(is_modified=False, refresh_xml=True)
		
		# Refresh the MLT XML file
		# and INIT the video thread
		self.project.RefreshXML()
		
		# Check for files being passed into OpenShot
		self.check_args()

		
		# put initial event on history stack
		history_state = (_("Session started"), self.project.state)
		self.history_stack.append(history_state)
		self.history_index = 0
		
		# Start the /queue/ watcher thread
		self.queue_watcher = lock.queue_watcher()
		self.queue_watcher.set_form(self)
		self.queue_watcher.start()


	def get_avformats(self, melt_command):
		
		#populate the codecs
		formats = av_formats.formats(melt_command)
		#video codecs
		self.vcodecs = formats.get_vcodecs()
		#audio codecs	
		self.acodecs = formats.get_acodecs()
		#formats
		self.vformats = formats.get_formats()
		

	def	save_project_state(self, type):
		print "project modified: ", type
			
		# if history has changed in the middle of the stack (clear the rest of the stack)
		if self.history_index < (len(self.history_stack) - 1):
			
			# Clear the rest of the history stack
			remove_range = range(self.history_index + 1, len(self.history_stack))
			remove_range.reverse()

			for remove_index in remove_range:
				# remove history item
				self.history_stack.pop(remove_index)
		
		# Increment index
		self.history_index += 1
		
		# retrieves project state property (returns a StringIO object)
		state = self.project.state
		
		# builds a tuple with action description string and StringIO object
		history_state = (type, state)
		
		# appends to history stack
		self.history_stack.append(history_state)
		
		# if history stack is longer than the maximum allowed, it deletes oldest event
		if len(self.history_stack) > self.max_history_size:
			self.history_stack.pop(0)
			self.history_index -= 1
		
		# refreshes history tree in main window
		self.refresh_history()

	
	def refresh_history(self):
		# Tree History refresh
		
		# set the project reference
		self.OSTreeHistory.set_project(self.project)
		
		# repopulate tree
		self.OSTreeHistory.populate_tree(self.history_index)
		
		
	def undo_last(self):
		
		# check if there is something to undo
		if len(self.history_stack) >= 2 and self.history_index > 0:

			# gets last state in history stack
			self.history_index -= 1

			# Get last item in the history stack
			previous_state = self.history_stack[self.history_index]

			# restores project to previous state
			self.project.restore(previous_state[1])
			
			# refreshes history tree in main window and renders project
			self.refresh_history()
			self.refresh()
			

	def redo_last(self):
		
		# check if there is something to redo
		if (self.history_index + 1) <= (len(self.history_stack) - 1):
			
			# gets next state in history stack
			self.history_index += 1

			# Get last item in the history stack
			next_state = self.history_stack[self.history_index]
			
			# restores project to previous state
			self.project.restore(next_state[1])
			
			# refreshes history tree in main window and renders project
			self.refresh_history()
			self.refresh()
			
			
	# double-click signal for a file in the tree
	def on_treeHistory_row_activated(self, widget, *args):
		print "on_treeHistory_row_activated"
		
		# Get the selection
		selection = self.treeHistory.get_selection()
		# Get the selected path(s)
		rows, selected = selection.get_selected_rows()
		
		# Get index of selected history tree item
		if self.history_index != selected[0][0]:
			# get new index
			self.history_index = selected[0][0]
	
			# Get last item in the history stack
			new_state = self.history_stack[self.history_index]
			
			# restores project to previous state
			self.project.restore(new_state[1])
			
			# refreshes history tree in main window and renders project
			self.refresh_history()
			self.refresh()
			
	def on_nbFiles_switch_page(self, widget, *args):
		print "on_nbFiles_switch_page"
		
		# get translation object
		_ = self._
		
		# new page position
		new_page_pos = args[1]
		
		# get main widget in tab
		tabChild = widget.get_nth_page(new_page_pos)
		tabLabel = widget.get_tab_label(tabChild)
		tabLabelText = widget.get_tab_label_text(tabChild)
		
		# init transitions & effects (if needed)
		if tabLabelText == _("Transitions"):
			if not self.OSTreeTransitions:
				# change cursor to "please wait"
				tabLabel.window.set_cursor(gtk.gdk.Cursor(150))
				tabLabel.window.set_cursor(gtk.gdk.Cursor(150))
				
				# init transitions tab
				self.OSTreeTransitions = TreeTransitions.OpenShotTree(self.treeTransitions, self.project)
				print "Init Transitions tab"
				
				# set cursor to normal
				tabLabel.window.set_cursor(None)
			
		elif tabLabelText == _("Effects"):
			if not self.OSTreeEffects:
				# change cursor to "please wait"
				tabLabel.window.set_cursor(gtk.gdk.Cursor(150))
				tabLabel.window.set_cursor(gtk.gdk.Cursor(150))
				
				# init transitions tab
				self.OSTreeEffects = TreeEffects.OpenShotTree(self.treeEffects, self.project)
				print "Init Effects tab"
				
				# set cursor to normal
				tabLabel.window.set_cursor(None)

		
	def on_tlbUndo_clicked(self, widget, *args):
		print "on_tlbUndo_clicked"
		
		# Undo last action
		self.undo_last()
		
	def on_tlbRedo_clicked(self, widget, *args):
		print "on_tlRedo_clicked"
		
		# Undo last action
		self.redo_last()
		
		
	def on_hpanel2_size_allocate(self, widget, *args):
		#print "on_hpanel2_size_allocate"
		if self.MyVideo:
			# refresh sdl
			self.MyVideo.c.set("refresh", "1")


	def check_args(self):
		""" Loop through args collection passed to OpenShot, and look for media files,
		or project files """
		
		# ignore first arg (which is always the path of the python script)
		if len(sys.argv) > 1:

			# loop through the remaining args
			for arg in sys.argv[1:]:

				# is this a file?
				if os.path.exists(arg):

					# is project file?
					if ".osp" in arg:
						# project file, open this project
						open_project.open_project(self.project, arg)
					else:
						# a media file, add it to the project tree
						self.project.project_folder.AddFile(arg)
						self.project.set_project_modified(is_modified=True, refresh_xml=False)
						
			# refresh window
			self.refresh()


	def recent_item_activated(self, widget):
		"""Activated when an item from the recent projects menu is clicked"""
		import urllib
		
		uri = widget.get_current_item().get_uri()
		
		# clean path to video
		#uri = uri.replace("%20", " ")
		uri = urllib.unquote(uri)
		
		# Strip 'file://' from the beginning
		file_to_open = uri[7:]
		self.project.Open(file_to_open)
		
		# stop video
		self.project.form.MyVideo.pause()
		
		# set the profile settings in the video thread
		self.project.form.MyVideo.set_profile(self.project.project_type)
		self.project.form.MyVideo.set_project(self.project, self.project.form, os.path.join(self.project.USER_DIR, "sequence.mlt"), mode="preview")
		self.project.form.MyVideo.load_xml()
		
		# refresh sdl
		self.project.form.MyVideo.c.set("refresh", 1)

		# Update the main form
		self.refresh()


	def new(self):
		print "A new %s has been created" % self.__class__.__name__

	def update_icon_theme(self):
		""" Update the icons / buttons with the correct Theme paths """
		
		# be sure theme exists
		if os.path.exists(os.path.join(self.project.THEMES_DIR, self.project.theme)) == False:
			# default back to basic theme
			self.project.theme = "blue_glass"
		
		# all buttons that need their icon updated
		all_buttons = [(self.tlbPrevious, "previous.png"),
				 (self.tlbPreviousMarker, "previous_marker.png"),
				 (self.tlbSeekBackward, "seek_backwards.png"),
				 (self.tlbPlay, "play_big.png"),
				 (self.tlbSeekForward, "seek_forwards.png"),
				 (self.tlbNextMarker, "next_marker.png"),
				 (self.tlbNext, "next.png"),
				 (self.tlbAddTrack, "plus.png"),
				 (self.tlbArrow, "arrow.png"),
				 (self.tlbRazor, "razor.png"),
				 (self.tlbResize, "resize.png"),
				 (self.tlbSnap, "snap.png"),
				 (self.tlbAddMarker, "add_marker.png"),
				 (self.tlbSnapshot, "snapshot.png"),
				]
		
		# loop through buttons
		for button in all_buttons:
			# get themed icon
			theme_img = gtk.Image()
			theme_img.set_from_file(os.path.join(self.project.THEMES_DIR, self.project.theme, "icons", button[1]))
			theme_img.show()
			# set new icon image
			button[0].set_icon_widget(theme_img)


	def refresh(self):

		# get correct gettext method
		_ = self._

		"""Called when the Treeview is active"""
		# Set the title of the window
		self.frmMain.set_title("OpenShot - %s" % (self.project.name))
		
		# set icon theme
		self.update_icon_theme()
		
		#set the project reference
		self.OSTreeFiles.set_project(self.project)
		
		# Set the zoom scale
		self.hsZoom.set_value(self.project.sequences[0].scale)

		# Clear the file treeview
		self.OSTreeFiles.store.clear()

		# render timeline
		self.project.Render()

		#sort the list of items so parent folders are added before
		#the child items, otherwise files that belong to a folder won't get added.
		items = self.project.project_folder.items
		items.sort(key=operator.attrgetter('parent'))

		# Loop through the files, and add them to the project tree
		for item in items:
			if isinstance(item, files.OpenShotFile):
				#format the file length field
				milliseconds = item.length * 1000
				time = timeline.timeline().get_friendly_time(milliseconds)
	
				hours = time[2]
				mins = time[3]
				secs = time[4]
				milli = time[5]
	
				time_str =  "%02d:%02d:%02d" % (time[2], time[3], time[4])
	
				# get the thumbnail (or load default)
				pbThumb = item.get_thumbnail(51, 38)
				
				#find parent (if any)
				parent_name = item.parent
				if parent_name == None:
					match_iter = None
				else:
					match_iter = self.search_tree(self.OSTreeFiles.store, self.OSTreeFiles.store.iter_children(None), self.search_match, (1, "%s" % parent_name))

				# Add the file to the treeview
				(dirName, fileName) = os.path.split(item.name)
				(fileBaseName, fileExtension)=os.path.splitext(fileName)
				
				self.OSTreeFiles.store.append(match_iter, [pbThumb, fileName, time_str, item.label, item.unique_id])
			   
			elif isinstance(item, files.OpenShotFolder):
				#add folders
				pbThumb = gtk.gdk.pixbuf_new_from_file(os.path.join(self.project.IMAGE_DIR, "folder.png"))
				self.OSTreeFiles.store.append(None, [pbThumb, "%s" % item.name, None, None, None])
		
		# Check for NO files
		if self.project.project_folder.items.__len__() == 0:
			# Add the NO FILES message to the tree
			self.OSTreeFiles.store.append(None, [None, _("Choose a Video or Audio File to Begin"), "", "", ""])
			
		# Always sync the thumbnail view
		self.refresh_thumb_view("refresh")
		
			
	def search_tree(self,model, iter, func, data):
		while iter:
			if func(model, iter, data):
				return iter
			result = self.search_tree(model, model.iter_children(iter), func, data)
			if result: return result
			iter = model.iter_next(iter)
			
			
	def search_match(self,model, iter, data):
		column, key = data # data is a tuple containing column number, key
		value = model.get_value(iter, column)
		return value == key
	

	def refresh_thumb_view(self, mode=None):
		"""Called when the thumbnail view is active"""
		view = self.icvFileIcons
		store = gtk.ListStore(gtk.gdk.Pixbuf, str, str, str)
		for item in self.project.project_folder.items:
			#don't show folders in this view
			if isinstance(item, files.OpenShotFile):
				# get resized thumbnail image from the file object
				pbThumb = item.get_thumbnail(102, 76)

				# add to tree data
				store.append([pbThumb,item.name, item.label, item.unique_id])
	
			view.set_item_width(130)
			view.set_model(store)
			view.set_text_column(1)
			view.set_pixbuf_column(0)
			view.set_text_column(2)
			
		 # Check for NO files
		if mode == None and self.project.project_folder.items.__len__() == 0:
			#switch to the detail view
			mnu = mnuTree(None, None, form=self, project=self.project)
			mnu.on_mnuDetailView_activate(None)
			
	   
	def canvas_motion_notify(self, target, event):

		# update cursor variable
		if self.current_cursor[0] != None and self.current_cursor[3] == "canvas":
			# update cursor
			self.current_cursor = [None, int(event.x), int(event.y), ""]
		
			# reset the cursor icon
			self.MyCanvas.window.set_cursor(None)

		
		# update source of the cursor update
		self.current_cursor[3] = "canvas"
		
		
	def on_drop_clip_from_tree (self, wid, event):
		# always drop a clip item (no matter where the cursor is)
		if self.new_clip:
			self.drop_cb(self.new_clip, self.tree_drag_context, self.new_clip.get_bounds().x1, 0.0, self.tree_drag_time)
		
		
	#////////////////////
	def motion_cb(self, wid, context, x, y, time):
		
		# track context object
		self.tree_drag_context = context
		self.tree_drag_time = time

		# set the drag status
		context.drag_status(gtk.gdk.ACTION_COPY, time)
		
		if self.drag_type == "file":
			# call file drag method
			self.motion_file_drag(wid, context, x, y, time)
			
		elif self.drag_type == "transition":
			# call transition drag method
			self.motion_transition_drag(wid, context, x, y, time)
		
		return True


	def motion_file_drag(self, wid, context, x, y, time):
		
		# get the veritcal scrollbar value
		vertical_scroll_value = self.vscrollbar2.get_value()
		horizontal_scroll_value = self.hscrollbar2.get_value()

		# Add clip to canvas (upon the first event... but not subsequent events)
		if (self.item_detected == False):
			self.item_detected = True
			detail_view_visible = self.scrolledwindow1.get_property('visible')
			if detail_view_visible:
				# get the file info from the tree
				selection = self.myTree.get_selection()
				rows, selected = selection.get_selected_rows()
				iters = [rows.get_iter(path) for path in selected]
				# Loop through selected files
				for iter in iters:
					# get file name and id of each file
					file_name = self.myTree.get_model().get_value(iter, 1)
					unique_id = self.myTree.get_model().get_value(iter, 4)
					
					# get the actual file object
					file_object = self.project.project_folder.FindFileByID(unique_id)
					if file_object:
						file_length = file_object.length
					else:
						return
				
			else:
				#get the file info from the iconview
				selected = self.icvFileIcons.get_selected_items()
				if len(selected) > 1:
					return
				i = selected[0][0]
				model = self.icvFileIcons.get_model()
				# Get the name and id of the selected file
				file_name = model[i][1]
				unique_id = model[i][3]
				
				# Get the actual file object
				file_object = self.project.project_folder.FindFileByID(unique_id)
				if file_object:
					file_length = file_object.length
				else:
					return
		   
			# get a new track object
			self.new_clip_object = self.project.sequences[0].tracks[0].AddClip(file_name, "Gold", 0, float(0.0), float(file_length), file_object)

			# get pixels per second
			pixels_per_second = self.new_clip_object.parent.parent.get_pixels_per_second()
			self.new_clip_object.position_on_track = x / pixels_per_second
			
			# Render clip to timeline (at the current drag X coordinate)
			self.new_clip = self.new_clip_object.RenderClip()
			
			# Arrange canvas items
			self.project.sequences[0].raise_transitions()
			self.project.sequences[0].play_head.raise_(None)
			self.project.sequences[0].play_head_line.raise_(None)

		try:
			# get the x and y coordinate of the clip boundry
			new_x = x - self.new_clip.get_bounds().x1 + horizontal_scroll_value
			new_y = y - self.new_clip.get_bounds().y1 + vertical_scroll_value
	
			# don't allow the clip to slide past the beginning of the canvas
			total_x_diff = new_x - 40
			if (self.new_clip.get_bounds().x1 + total_x_diff < 0):
				total_x_diff = 0 - self.new_clip.get_bounds().x1
			
	
			# be sure that the clip is being dragged over a valid drop target (i.e. a track)
			if self.new_clip_object.is_valid_drop(self.new_clip.get_bounds().x1 + total_x_diff, self.new_clip.get_bounds().y1 + new_y - 25):
	
				# move the clip based on the event data
				self.new_clip.translate (total_x_diff, new_y - 25)
		
		except:
			# reset the drag n drop 
			self.item_detected = False
			self.new_clip_object = None
			
			
	def motion_transition_drag(self, wid, context, x, y, time):
		
		# get the veritcal scrollbar value
		vertical_scroll_value = self.vscrollbar2.get_value()
		horizontal_scroll_value = self.hscrollbar2.get_value()
		
		# get pixels per second
		pixels_per_second = self.project.sequences[0].get_pixels_per_second()
		
		transition_name = ""
		transition_desc = ""

		# Add clip to canvas (upon the first event... but not subsequent events)
		if (self.item_detected == False):
			self.item_detected = True

			# get the file info from the tree
			selection = self.treeTransitions.get_selection()
			rows, selected = selection.get_selected_rows()
			iters = [rows.get_iter(path) for path in selected]
			for iter in iters:
				transition_name = self.treeTransitions.get_model().get_value(iter, 1)
				transition_path = self.treeTransitions.get_model().get_value(iter, 2)


			# get a new transition object
			self.new_trans_object = self.project.sequences[0].tracks[0].AddTransition(transition_name, float(0.0), float(6.0), transition_path)

			# update the position as the user drags the transition around
			self.new_trans_object.position_on_track = x / pixels_per_second

			# Render clip to timeline (at the current drag X coordinate)
			self.new_transition = self.new_trans_object.Render()
			
			# Arrange canvas items
			self.project.sequences[0].raise_transitions()
			self.project.sequences[0].play_head.raise_(None)
			self.project.sequences[0].play_head_line.raise_(None)
	
		try:
			# get the x and y coordinate of the clip boundry
			new_x = x - self.new_transition.get_bounds().x1 + horizontal_scroll_value
			new_y = y - self.new_transition.get_bounds().y1 + vertical_scroll_value

			# don't allow the clip to slide past the beginning of the canvas
			total_x_diff = new_x - 40
			if (self.new_transition.get_bounds().x1 + total_x_diff < 0):
				total_x_diff = 0 - self.new_transition.get_bounds().x1
			
			# move the clip based on the event data
			self.new_transition.translate (total_x_diff, new_y - 25)
						
			# update the position as the user drags the transition around
			self.new_trans_object.position_on_track = self.new_transition.get_bounds().x1 / pixels_per_second
		
		except:
			# reset the drag n drop 
			self.item_detected = False
			self.new_trans_object = None



	def drop_cb(self, item, context, x, y, time):

		# complete the drag operation
		context.finish(True, False, time)

		# determine what cursor mode is enable (arrow, razor, snap, etc...)
		(isArrow, isRazor, isSnap, isResize) = self.get_toolbar_options()
		
		# Drop EFFECT
		if self.drag_type == "effect":
			
			horizontal_value = self.hscrollbar2.get_value()
			vertical_value = self.vscrollbar2.get_value()
			adjusted_y = y + vertical_value
			adjusted_x = x + horizontal_value

			# get new parent track
			drop_track = self.project.sequences[0].get_valid_track(adjusted_x, adjusted_y)
			
			if drop_track:

				# get pixel settings
				pixels_per_second = self.project.sequences[0].get_pixels_per_second()
				
				# find clip (if any)
				for clip in drop_track.clips:
					if adjusted_x >= (clip.position_on_track * pixels_per_second) and adjusted_x <= ((clip.position_on_track + clip.length()) * pixels_per_second):
						# Get Effect service name
						selection = self.treeEffects.get_selection()
						rows, selected = selection.get_selected_rows()
						iters = [rows.get_iter(path) for path in selected]
						for iter in iters:
							Name_of_Effect = self.treeEffects.get_model().get_value(iter, 1)
							Effect_Service = self.treeEffects.get_model().get_value(iter, 2)
							
							# Add Effect to Clip
							clip.Add_Effect(Effect_Service)
							self.project.Render()


		# Drop TRANSITION
		if self.new_trans_object:
			# get new parent track
			drop_track = self.new_trans_object.get_valid_drop(self.new_transition.get_bounds().x1, self.new_transition.get_bounds().y1)
			
			if drop_track == None:
				# keep old parent, if no track found
				drop_track = self.new_trans_object.parent
			
			# update the track_A (the primary track)
			if drop_track:
				self.new_trans_object.update_parent(drop_track)
				drop_track.reorder_transitions()

				# deterime the direction of the drag
				if isSnap:
					# get pixel settings
					pixels_per_second = self.project.sequences[0].get_pixels_per_second()
					distance_from_clip = self.new_trans_object.get_snap_difference(self.new_trans_object, self.new_transition)
					self.new_trans_object.position_on_track = float(self.new_transition.get_bounds().x1 + distance_from_clip) / pixels_per_second
				
				# re-render the transition
				parent = self.new_transition.get_parent()
				if parent:
					child_num = parent.find_child (self.new_transition)
					parent.remove_child (child_num)
					self.new_trans_object.Render()
					
					# mark project as modified
					self.project.set_project_modified(is_modified=True, refresh_xml=True, type="Added transition")
		
		
		if self.new_clip_object == None:
			self.item_detected = False
			self.new_trans_object = None
			return
		

		# get the track that the clip was dropped on		
		drop_track = self.new_clip_object.get_valid_drop(self.new_clip.get_bounds().x1, self.new_clip.get_bounds().y1)

		# update and reorder the clips on this track (in the object model)
		self.new_clip_object.update(self.new_clip.get_bounds().x1, self.new_clip.get_bounds().y1, drop_track)		 
		drop_track.reorder_clips()
		
		# Drop CLIP
		if drop_track:

			# deterime the direction of the drag
			if isSnap:
				distance_from_clip = self.new_clip_object.get_snap_difference(self.new_clip_object, self.new_clip)
			else:
				distance_from_clip = 0.0
			
			# move the clip object on the timeline to correct position (snapping to the y and x of the track)		
			self.new_clip.translate (distance_from_clip, float(drop_track.y_top) - float(self.new_clip.get_bounds().y1) + 2.0)
			
			# update clip's settings
			self.new_clip_object.update(self.new_clip.get_bounds().x1, self.new_clip.get_bounds().y1, drop_track) 
			
			# check if the timeline needs to be expanded
			self.expand_timeline(self.new_clip_object)
			
			# mark project as modified
			self.project.set_project_modified(is_modified=True, refresh_xml=True, type="Added clip")

		else:
			# Remove clip, because of invalid parent
			self.new_clip_object.parent.clips.remove(self.new_clip_object)
			parent = self.new_clip.get_parent()
			if parent:
				child_num = parent.find_child (self.new_clip)
				parent.remove_child (child_num)

		# reset the drag n drop 
		self.item_detected = False
		self.new_clip_object = None
		self.new_trans_object = None
		self.drag_type = None


		return False
	#////////////////////


	def expand_timeline(self, clip_object):
		""" Determine if the timeline needs to be expanded. """
		# get end time of dropped clip
		position = clip_object.position_on_track
		length = clip_object.length()
		end_of_clip = position + length
		
		# get length of timeline
		timeline_length = self.project.sequences[0].length
		
		# does timeline need to be extended?
		if end_of_clip > timeline_length:
			# update length of timeline
			self.project.sequences[0].length = end_of_clip
			
			# refresh timeline
			self.refresh()


	def on_frmMain_delete_event(self, widget, *args):
		
		# get correct gettext method
		_ = self._
		
		# pre-destroy event
		# prompt user to save (if needed)
		#if len(self.project.project_folder.items) > 0:
		if self.project.is_modified == True:
			messagebox.show("OpenShot", _("Would you like to save this project?"), gtk.BUTTONS_YES_NO, self.exit_openshot_with_save, self.exit_openshot_with_no_save)
		
			# don't end OpenShot (yet).  A callback from the messagebox will close OpenShot.
			return True
		else:
			# exit openshot
			self.frmMain.destroy()


	def exit_openshot_with_save(self):
		# mark as exiting
		self.is_exiting = True
		
		# call the save button
		self.on_tlbSave_clicked(None)
		
		
	def exit_openshot_with_no_save(self):
		# mark as exiting
		self.is_exiting = True
		
		# call the save button
		self.frmMain.destroy()
		
		
	def on_frmMain_window_state_event(self, widget, event, *args):
		""" determine if screen is maximized or un-maximized """
		#print "on_frmMain_window_state_event"

		if event.changed_mask & gtk.gdk.WINDOW_STATE_MAXIMIZED:
			if event.new_window_state & gtk.gdk.WINDOW_STATE_MAXIMIZED:
				# MAXIMIZED
				self.is_maximized = True
			else:
				# Un-Maximized
				self.is_maximized = False
				
		# refresh sdl on window resize
		if self.MyVideo:
			self.MyVideo.c.set("refresh", 1)


	def on_frmMain_destroy(self, widget, *args):
		print "on_frmMain_destroy"
		
		# kill the threads
		if self.MyVideo:
			self.MyVideo.amAlive = False
			
		if self.project.thumbnailer:
			self.project.thumbnailer.amAlive = False
			
		if self.queue_watcher:
			self.queue_watcher.amAlive = False
			
		# wait 1/2 second (for threads to stop)
		import time
		time.sleep(0.500)
		
		#get the main window size
		self.settings.app_state["window_maximized"] = str(self.is_maximized)
		self.settings.app_state["window_width"] = self.width
		self.settings.app_state["window_height"] = self.height
		
		#get the position of the dividers
		self.settings.app_state["vpane_position"] = self.vpaned2.get_position()
		self.settings.app_state["hpane_position"] = self.hpaned2.get_position()
				
		#save the settings
		self.settings.save_settings_to_xml()
		
		# Quit the main loop, and exit the program
		self.frmMain.destroy()
		self.quit()
		

	def on_frmMain_configure_event(self, widget, *args):
		#handles the resize event of the window
		(self.width, self.height) = self.frmMain.get_size()
		
		# refresh sdl on window resize
		if self.MyVideo:
			self.MyVideo.c.set("refresh", 1)
		
		

	def on_mnuNewProject_activate(self, widget, *args):
		print "on_mnuNewProject_activate called with self.%s" % widget.get_name()
		NewProject.frmNewProject(mode="new", project=self.project)



	def on_mnuOpenProject_activate(self, widget, *args):
		print "on_mnuOpenProject_activate called with self.%s" % widget.get_name()
		OpenProject.frmOpenProject(project=self.project)


	def on_tlbOpenProject_clicked(self, widget, *args):
		OpenProject.frmOpenProject(project=self.project)


	def on_mnuImportFiles_activate(self, widget, *args):
		print "on_mnuImportFiles_activate called with self.%s" % widget.get_name()
		
		# show import file dialog
		AddFiles.frmAddFiles(form=self, project=self.project)
		
		
	def on_mnuImportImageSequence_activate(self, widget, *args):
		print "on_mnuImportImageSequence_activate called with self.%s" % widget.get_name()
		
		# show import file dialog
		ImportImageSeq.frmImportImageSequence(form=self, project=self.project)


	def on_mnuSaveProject_activate(self, widget, *args):
		print "on_mnuSaveProject_activate called with self.%s" % widget.get_name()
		
		# call the save button
		self.on_tlbSave_clicked(widget)


	def on_mnuSaveProjectAs_activate(self, widget, *args):
		print "on_mnuSaveProjectAs_activate called with self.%s" % widget.get_name()
		NewProject.frmNewProject(mode="saveas", project=self.project)


	def on_mnuMakeMovie1_activate(self, widget, *args):
		print "on_mnuMakeMovie1_activate called with self.%s" % widget.get_name()

		# call toolbar button
		self.on_tlbMakeMovie_clicked(widget)

	def on_mnuQuit1_activate(self, widget, *args):
		print "on_mnuQuit1_activate called with self.%s" % widget.get_name()

		# Quit
		self.on_frmMain_delete_event(widget)
		

	def on_mnuPreferences_activate(self, widget, *args):
		print "on_mnuPreferences_activate called with self.%s" % widget.get_name()

		# get correct gettext method
		_ = self._

		# open preferences window
		preferences.PreferencesMgr(project=self.project, form=self)
		
		
	def on_mnuNewTitle_activate(self, widget, *args):
		print "on_mnuNewTitle_activate called with self.%s" % widget.get_name()
		Titles.frmNewTitle(form=self, project=self.project)


	def on_mnuNewSequence_activate(self, widget, *args):
		print "on_mnuNewSequence_activate called with self.%s" % widget.get_name()
		
		# get correct gettext method
		_ = self._
		
		# coming soon
		messagebox.show("Error!", _("This feature is still in development."))
		
	def on_mnuAbout_activate(self, widget, *args):
		print "on_mnuAbout_activate called with self.%s" % widget.get_name()

		# Open About Dialog
		About.frmAbout(version=self.version, project=self.project)

	def on_mnuHelpContents_activate(self, widget, *args):
		print "on_mnuHelpContents_activate called with self.%s" % widget.get_name()

		#show Help contents
		try:
			#need to use the relative path until we can get
			#yelp to properly index the file.
			#then we should be able to use:
			helpfile = "ghelp:openshot"
			screen = gtk.gdk.screen_get_default()
			gtk.show_uri(screen, helpfile, gtk.get_current_event_time())
		except:
			messagebox.show(_("Error!"), _("Unable to open the Help Contents. Please ensure the openshot-doc package is installed."))
		
			
	def on_mnuReportBug_activate(self, widget, *args):
		print "on_mnuReportBug_activate called with self.%s" % widget.get_name()
		
		#open the launchpad bug page with the users default browser
		try:
			webbrowser.open("https://bugs.launchpad.net/openshot/+filebug")
		except:
			messagebox.show(_("Error!"), _("Unable to open the Launchpad web page."))
			
	
	def on_mnuAskQuestion_activate(self, widget, *args):
		print "on_mnuAskQuestion_activate called with self.%s" % widget.get_name()
		
		#open the launchpad answers page with the users default browser
		try:
			webbrowser.open("https://answers.launchpad.net/openshot/+addquestion")
		except:
			messagebox.show(_("Error!"), _("Unable to open the Launchpad web page."))
			
	def on_mnuTranslate_activate(self, widget, *args):
		print "on_mnuTranslate_activate called with self.%s" % widget.get_name()
		
		#open the launchpad answers page with the users default browser
		try:
			webbrowser.open("https://translations.launchpad.net/openshot")
		except:
			messagebox.show(_("Error!"), _("Unable to open the Launchpad web page."))
			
			
	def on_mnuToolbar_toggled(self, widget, *args):
		print "on_mnuToolbar_toggled called with self.%s" % widget.get_name()
		
		if not self.mnuToolbar.get_active():
			self.tlbMain.hide()
			self.settings.app_state["toolbar_visible"] = "False"
		else:
			self.tlbMain.show()
			self.settings.app_state["toolbar_visible"] = "True"
			
	def on_mnuHistory_toggled(self, widget, *args):
		print "on_mnuHistory_toggled called with self.%s" % widget.get_name()
		
		if not self.mnuHistory.get_active():
			self.scrolledwindowHistory.hide()
			#self.settings.app_state["toolbar_visible"] = "False"
		else:
			self.scrolledwindowHistory.show()
			self.nbFiles.set_current_page(4)
			


	def on_tlbImportFiles_clicked(self, widget, *args):
		print "on_tlbImportFiles_clicked called with self.%s" % widget.get_name()
		
		# show import file dialog
		AddFiles.frmAddFiles(form=self, project=self.project)


	def on_tlbSave_clicked(self, widget, *args):
		#print "on_tlbSave_clicked called with self.%s" % widget.get_name()
		
		project_name = self.project.name
		project_folder = self.project.folder

		# determine if this project has been saved before
		if (project_folder != self.project.USER_DIR):

			# save file exists... so just save again
			self.project.Save("%s/%s.osp" % (project_folder, project_name))
			
			# Is openshot exiting?
			if self.is_exiting:
				self.frmMain.destroy()

		else:

			# save file doesn't exist, so open "save as" window
			NewProject.frmNewProject(mode="saveas", project=self.project)


	def on_tlbMakeMovie_clicked(self, widget, *args):
		print "on_tlbMakeMovie_clicked called with self.%s" % widget.get_name()
		
		# show frmExportVideo dialog
		self.frmExportVideo = ExportVideo.frmExportVideo(form=self, project=self.project)


	# double-click signal for a file in the tree
	def on_treeFiles_row_activated(self, widget, *args):
		print "on_treeFiles_row_activated"
		
		# Get the selection
		selection = self.treeFiles.get_selection()
		# Get the selected path(s)
		rows, selected = selection.get_selected_rows()

		# call the preview menu signal
		mnu = mnuTree(rows, selected, form=self, project=self.project)
		mnu.on_mnuPreview_activate(None)
		

	def on_treeFiles_drag_begin(self, widget, *args):
		context = args[0]
		
		# update drag type
		self.project.form.drag_type = "file"

		# Get the drag icon
		play_image = gtk.image_new_from_file(os.path.join(self.project.THEMES_DIR, self.project.theme, "icons", "plus.png"))
		pixbuf = play_image.get_pixbuf()
		context.set_icon_pixbuf(pixbuf, 15, 10)
		
		
	def on_canvas_drag_motion(self, wid, context, x, y, time):
		print " *** motion detected"


	def on_canvas_drag_drop(self, widget, *args):
		print " *** DROP detected"

	def on_hsVideoProgress_change_value(self, widget, *args):

		# get the percentage of the video progress 0 to 100
		video_progress_percent = float(self.hsVideoProgress.get_value()) / 100.0
		
		# Refresh the MLT XML file
		self.project.RefreshXML()
		
		# refresh sdl
		self.project.form.MyVideo.c.set("refresh", 1)

		# determine frame number
		new_frame = int(float(self.MyVideo.p.get_length() - 1) * video_progress_percent)

		# jump to this frame
		self.MyVideo.p.seek(new_frame)

	def on_hsVideoProgress_value_changed(self, widget, *args):
		#print "on_hsVideoProgress_value_changed called with self.%s" % widget.get_name()		
		pass

	
	def on_tlbSnapshot_clicked(self, widget, *args):
		print "on_tlbSnapshot_clicked"
		
		# get correct gettext method
		_ = self._
		
		# TODO: coming soon
		messagebox.show("Error!", _("This feature is still in development."))
		
	
	def on_tlbPreviousMarker_clicked(self, widget, *args):
		print "on_tlbPreviousMarker_clicked"
		
		# get the previous marker object (if any)
		playhead_position = self.project.sequences[0].play_head_position
		marker = self.project.sequences[0].get_marker("left", playhead_position)
		is_playing = False
		if self.MyVideo:
			is_playing = self.MyVideo.isPlaying
		
		if marker:
			# determine frame number
			frame = self.project.fps() * marker.position_on_track
			
			# seek to this time
			if self.MyVideo:
				# Refresh the MLT XML file
				self.project.RefreshXML()
				
				# Seek and refresh sdl
				self.MyVideo.p.seek(int(frame))
				self.MyVideo.c.set("refresh", 1)

				# check isPlaying
				if is_playing == False:
					self.MyVideo.pause()
				
			# move play-head
			self.project.sequences[0].move_play_head(marker.position_on_track)
		
	def on_tlbSeekBackward_clicked(self, widget, single_frame=False, *args):
		print "on_tlbSeekBackward_clicked"
		
		# get correct gettext method
		_ = self._

		# Refresh the MLT XML file
		self.project.RefreshXML()
		
		# get the current speed
		current_speed = self.MyVideo.p.get_speed()
		position = self.MyVideo.p.position()
		
		# check if frame-stepping or rewinding
		if single_frame == False:
			# SEEK BACKWARDS
			# calcualte new speed
			if current_speed >= 0:
				new_speed = -1
			else:
				new_speed = (current_speed * 2) 
			
			# set the new speed
			self.MyVideo.p.set_speed(new_speed)
			
			# update the preview tab label
			if new_speed == 1:
				self.lblVideoPreview.set_text(_("Video Preview"))
			else:
				self.lblVideoPreview.set_text(_("Video Preview (%sX)" % int(new_speed)))
		else:
			# STEP BACKWARDS 1 FRAME
			self.MyVideo.p.seek(position - 1)
			
			# refresh sdl
			self.MyVideo.c.set("refresh", 1)

			
	
	def on_tlbSeekForward_clicked(self, widget, single_frame=False, *args):
		print "on_tlbSeekForward_clicked"
		
		# get correct gettext method
		_ = self._
		
		# Refresh the MLT XML file
		self.project.RefreshXML()
		
		# get the current speed
		current_speed = self.MyVideo.p.get_speed()
		position = self.MyVideo.p.position()
		
		# check if frame-stepping or rewinding
		if single_frame == False:
			# SEEK FORWARD
			# calcualte new speed
			if current_speed <= 0:
				new_speed = 2
			else:
				new_speed = current_speed * 2
			
			# set the new speed
			self.MyVideo.p.set_speed(new_speed)
			
			# update the preview tab label
			if new_speed == 1:
				self.lblVideoPreview.set_text(_("Video Preview"))
			else:
				self.lblVideoPreview.set_text(_("Video Preview (%sX)" % int(new_speed)))
		else:
			# STEP FORWARD 1 FRAME
			self.MyVideo.p.seek(position + 1)
			
			# refresh sdl
			self.MyVideo.c.set("refresh", 1)
			
	
	def on_tlbNextMarker_clicked(self, widget, *args):
		print "on_tlbNextMarker_clicked"
		
		# get the previous marker object (if any)
		playhead_position = self.project.sequences[0].play_head_position
		marker = self.project.sequences[0].get_marker("right", playhead_position)
		is_playing = False
		if self.MyVideo:
			is_playing = self.MyVideo.isPlaying
		
		if marker:
			# determine frame number
			frame = self.project.fps() * marker.position_on_track
			
			# Refresh the MLT XML file
			self.project.RefreshXML()
			
			# seek and refresh sdl
			self.MyVideo.p.seek(int(frame))
			self.MyVideo.c.set("refresh", 1)

			# check isPlaying
			if is_playing == False:
				self.MyVideo.pause()
				
			# move play-head
			self.project.sequences[0].move_play_head(marker.position_on_track)
			
	
	def on_tlbAddMarker_clicked(self, widget, *args):
		print "on_tlbAddMarker_clicked"
		
		# get the current play_head position
		playhead_position = self.project.sequences[0].play_head_position
		
		# add a marker
		m = self.project.sequences[0].AddMarker("marker name", playhead_position)
		
		# refresh the screen
		if m:
			m.Render()
			
			# raise-play head
			self.project.sequences[0].move_play_head(playhead_position)
		
		
		
	def on_tlbPrevious_clicked(self, widget, *args):
		print "on_tlbPrevious_clicked called with self.%s" % widget.get_name()

		# get correct gettext method
		_ = self._

		# Refresh the MLT XML file
		self.project.RefreshXML()
		
		# seek to the first frame and reset the speed to 1X
		self.MyVideo.p.set_speed(1)
		self.MyVideo.p.seek(0)
		
		# refresh sdl
		self.MyVideo.c.set("refresh", 1)
		
		if self.MyVideo.isPlaying == False:
			self.MyVideo.p.set_speed(0)
		else:
			self.MyVideo.p.set_speed(1)
		
		# update video preview tab
		self.lblVideoPreview.set_text(_("Video Preview"))
			

	def on_tlbPlay_clicked(self, widget, *args):
		print "on_tlbPlay_clicked called with self.%s" % widget.get_name()
		
		# get correct gettext method
		_ = self._
		
		# Get the current speed
		current_speed = self.MyVideo.p.get_speed()
		
		# Refresh the MLT XML file
		self.project.RefreshXML()

		# is video stopped?
		if current_speed == 0:
			
			# start video
			self.MyVideo.play()
			
			# update video preview tab
			self.lblVideoPreview.set_text(_("Video Preview"))

		else:
			
			# stop video
			self.MyVideo.pause()
			
			# update video preview tab
			self.lblVideoPreview.set_text(_("Video Preview (Paused)"))


	def on_tlbNext_clicked(self, widget, *args):
		print "on_tlbNext_clicked called with self.%s" % widget.get_name()

		# get correct gettext method
		_ = self._

		# Refresh the MLT XML file
		self.project.RefreshXML()
		
		# seek to the last frame and reset the speed to 1X
		self.MyVideo.p.set_speed(1)
		self.MyVideo.p.seek(self.MyVideo.p.get_length())
		
		# refresh sdl
		self.MyVideo.c.set("refresh", 1)
		
		if self.MyVideo.isPlaying == False:
			self.MyVideo.p.set_speed(0)
		else:
			self.MyVideo.p.set_speed(1)
		
		# update video preview tab
		self.lblVideoPreview.set_text(_("Video Preview"))
			
			
	def on_tlbStop_clicked(self, widget, *args):
		print "on_tlbStop_clicked called with self.%s" % widget.get_name()
		
		# Refresh the MLT XML file
		self.project.RefreshXML()
		
		# stop thread from running
		self.MyVideo.pause()

		# refresh sdl
		self.MyVideo.c.set("refresh", 1)
		
		
	def on_frmMain_key_press_event(self, widget, event):
		print "on_frmMain_key_press_event"
		# Get the key name that was pressed
		keyname = str.lower(gtk.gdk.keyval_name(event.keyval))
		
		
		if keyname == "f1":
			#F1 key pressed 
			self.on_mnuHelpContents_activate(widget)
		
		if self.is_edit_mode == False:
			if keyname == "c":
				# Cut all tracks at this point (whereever the playhead is)
				self.cut_at_playhead()
				return True
			
			if keyname == "j":
				#print "J Key was Pressed"
				self.on_tlbSeekBackward_clicked(widget)
				return True
				
			elif keyname == "k" or keyname == "space":
				#print "K Key was Pressed"
				self.on_tlbPlay_clicked(widget)
				return True
				
			elif keyname == "l":
				#print "L Key was Pressed"
				self.on_tlbSeekForward_clicked(widget)
				return True
				
			elif keyname == "left":
				#print "LEFT Key was Pressed"
				self.on_tlbSeekBackward_clicked(widget, single_frame=True)
				return True
				
			elif keyname == "right":
				#print "RIGHT Key was Pressed"
				self.on_tlbSeekForward_clicked(widget, single_frame=True)
				return True
				
			elif keyname == "up":
				#print "UP Key was Pressed"
				self.on_tlbPreviousMarker_clicked(widget, event)
				return True
				
			elif keyname == "down":
				#print "DOWN Key was Pressed"
				self.on_tlbNextMarker_clicked(widget, event)
				return True
			
			elif keyname == "tab":
				# toggle the trim / arrow modes
				self.toggle_mode()
				return True
			
			elif keyname == "home":
				#go to the beginning of the clip
				if (event.state == gtk.gdk.CONTROL_MASK) or (event.state == gtk.gdk.CONTROL_MASK | gtk.gdk.MOD2_MASK):
					self.on_tlbPrevious_clicked(widget, event)
					
			elif keyname == "end":
				#go to the end of the clip
				if (event.state == gtk.gdk.CONTROL_MASK) or (event.state == gtk.gdk.CONTROL_MASK | gtk.gdk.MOD2_MASK):
					self.on_tlbNext_clicked(widget, event)
					
			elif keyname == "s":
				#go to the end of the clip
				if (event.state == gtk.gdk.CONTROL_MASK) or (event.state == gtk.gdk.CONTROL_MASK | gtk.gdk.MOD2_MASK):
					# call the save button
					self.on_tlbSave_clicked(widget)
					
			elif keyname == "y":
				#go to the end of the clip
				if (event.state == gtk.gdk.CONTROL_MASK) or (event.state == gtk.gdk.CONTROL_MASK | gtk.gdk.MOD2_MASK):
					# Undo last action
					self.redo_last()
					
			elif keyname == "z":
				#go to the end of the clip
				if (event.state == gtk.gdk.CONTROL_MASK) or (event.state == gtk.gdk.CONTROL_MASK | gtk.gdk.MOD2_MASK):
					# Undo last action
					self.undo_last()
			
		
	def toggle_mode(self):
		
		# determine what cursor mode is enable (arrow, razor, snap, etc...)
		(isArrow, isRazor, isSnap, isResize) = self.get_toolbar_options()
		
		# only execute code if button is toggled (i.e. this gets called on un-toggle event also)
		if isResize:
			# toggle to arrow
			self.tlbArrow.set_active(True)
		else:
			# toggle to razor
			self.tlbResize.set_active(True)
			
	def cut_at_playhead(self):
		""" Cut all clips and transitions at the current play head position """
		
		canvas_right = self.project.form.MyCanvas
		root_right = canvas_right.get_root_item()
		
		# Get playhead position
		current_position = self.project.sequences[0].play_head_position
		pixels_per_second = self.project.sequences[0].get_pixels_per_second()
		x = current_position * pixels_per_second
		
		# Loop through all tracks
		for track in self.project.sequences[0].tracks:
			# Loop through all clips on this track
			for clip in track.clips:
				# is playhead overlapping this clip
				if current_position > clip.position_on_track and current_position < (clip.position_on_track + clip.length()):
					# get the canvas object
					canvas_item = clip.get_canvas_child(root_right, clip.unique_id)
					# divide clip
					clip.divide_clip(x, canvas_item)
					
#			# Loop through all transitions on this track
#		 	for trans in track.transitions:
#				# is playhead overlapping this transition
#				if current_position > trans.position_on_track and current_position < (trans.position_on_track + trans.length):
#					canvas_item = trans.get_canvas_child(root_right, trans.unique_id)
#					# divide transition
#					trans.divide_clip(x, canvas_item)

	def get_toolbar_options(self):
		""" return the options selected on the toolbar """
		
		isArrow = self.tlbArrow.get_active()
		isRazor = self.tlbRazor.get_active()
		isSnap = self.tlbSnap.get_active()
		isResize = self.tlbResize.get_active()
		
		# default to arrow mode
		if isRazor == False and isResize == False:
			isArrow = True
		
		return (isArrow, isRazor, isSnap, isResize)
	

	def on_tlbAddTrack_clicked(self, widget, *args):

		# get correct gettext method
		_ = self._

		# Add a new track to the timeline		
		self.project.sequences[0].AddTrack(_("Track %s") % str(len(self.project.sequences[0].tracks) + 1))
		self.project.Render()


	def on_tlbRemoveTrack_clicked(self, widget, *args):
		print "on_tlbRemoveTrack_clicked called with self.%s" % widget.get_name()


	def on_tlbRazor_toggled(self, widget, *args):
		print "on_tlbRazor_clicked called with self.%s" % widget.get_name()

		# determine what cursor mode is enable (arrow, razor, snap, etc...)
		(isArrow, isRazor, isSnap, isResize) = self.get_toolbar_options()
		
		# only execute code if button is toggled (i.e. this gets called on un-toggle event also)
		if self.tlbRazor.get_active():
			
			# un-toggle the other toggles
			self.tlbArrow.set_active(False)
			self.tlbResize.set_active(False)
			
			# get the razor line image
			imgRazorLine = gtk.image_new_from_file(os.path.join(self.project.THEMES_DIR, self.project.theme, "icons", "razor_line_with_razor.png"))
			pixRazorLine = imgRazorLine.get_pixbuf()
			
			# set cursor to normal
			self.MyCanvas.window.set_cursor(gtk.gdk.Cursor(gtk.gdk.display_get_default(), pixRazorLine, 0, 28))
			
			
		# Keep the arrow selected, if no other toggles are selected
		if isRazor == False and isResize == False:
			self.tlbArrow.set_active(True)
			
			

	def on_tlbArrow_toggled(self, widget, *args):
		print "on_tlbArrow_clicked called with self.%s" % widget.get_name()
		
		# determine what cursor mode is enable (arrow, razor, snap, etc...)
		(isArrow, isRazor, isSnap, isResize) = self.get_toolbar_options()
		
		# only execute code if button is toggled (i.e. this gets called on un-toggle event also)
		if self.tlbArrow.get_active():   
		
			# un-toggle the other toggles
			self.tlbResize.set_active(False)
			self.tlbRazor.set_active(False)		
			
			# set cursor to normal
			self.MyCanvas.window.set_cursor(None)
			
			# Get the root group of the canvas
			#root_right = self.MyCanvas.get_root_item ()
	
			# Add a translucent blue rectangle to the canvas
			#image1 = goocanvas.Rect (parent = root_right,
									  #x = 12,
									  #y = 11,
									  #width = 100,
									  #height = 165,
									  #fill_color_rgba = 1401402200,
									  #stroke_color_rgba = 1401402500)
									  

		# Keep the arrow selected, if no other toggles are selected
		if isRazor == False and isResize == False:
			self.tlbArrow.set_active(True)
			
			
	def on_btnZoomIn_clicked(self, widget, *args):
		print "on_btnZoomIn_clicked"
		
		# get the value of the zoom slider
		zoom_slider = self.hsZoom.get_value()
		
		# zoom slower if too close
		if zoom_slider > 10:
			
			# subtract 5 units
			self.hsZoom.set_value(zoom_slider - 5)
		
		elif zoom_slider <= 5:
			# Move the zoom slider to the left
			if zoom_slider - 1 > 0:
				# subtract 5 units
				self.hsZoom.set_value(zoom_slider - 1)
			else:
				# set to 0
				self.hsZoom.set_value(0)
		
		elif zoom_slider <= 10:

			# subtract 5 units
			self.hsZoom.set_value(zoom_slider - 2)

		

			
		
	def on_btnZoomOu_clicked(self, widget, *args):
		print "on_btnZoomOu_clicked"
		
		# get the value of the zoom slider
		zoom_slider = self.hsZoom.get_value()

		# zoom slower if too close
		if zoom_slider > 11:
			
			# Move the zoom slider to the left
			if zoom_slider + 5 < 115:
				# add 5 units
				self.hsZoom.set_value(zoom_slider + 5)
			else:
				# set to 0
				self.hsZoom.set_value(115)
		
		elif zoom_slider < 4:
			
				# add 1 units
				self.hsZoom.set_value(zoom_slider + 1)
		
		elif zoom_slider <= 11:

			# add 2 units
			self.hsZoom.set_value(zoom_slider + 2)
			
			
		
	def on_hsZoom_change_value(self, widget, *args):

		# get correct gettext method
		_ = self._
		
		# get current horizontal scroll position & time
		pixels_per_second = self.project.sequences[0].get_pixels_per_second()
		current_scroll_pixels = self.hscrollbar2.get_value()
		current_scroll_time = current_scroll_pixels / pixels_per_second

		# get the value of the zoom slider (this value represents the number of seconds 
		# between the tick marks on the timeline ruler
		new_zoom_value = widget.get_value()

		# set the scale
		self.project.sequences[0].scale = int(new_zoom_value)
		
		# update zoom label
		self.lblZoomDetail.set_text(_("%s seconds") % int(new_zoom_value))

		# re-render the timeline with the new scale
		self.project.Render()
		
		# scroll to last scroll position
		self.scroll_to_last(current_scroll_time)
		
		
	def scroll_to_last(self, current_scroll_time):
		# get position of play-head
		pixels_per_second = self.project.sequences[0].get_pixels_per_second()
		goto_pixel = current_scroll_time * pixels_per_second

		# scroll to last scroll position
		self.hscrollbar2.set_value(goto_pixel)

	
	def scroll_to_playhead(self):
		""" scroll the horizontal scroll if the playhead is playing, and moves
		past the center point of the screen. """ 
		
		if self.MyVideo.isPlaying:
			
			# get current scroll position
			current_scroll_pixels = self.hscrollbar2.get_value()
			
			# get playhead position
			pixels_per_second = self.project.sequences[0].get_pixels_per_second()
			playhead_time = self.project.sequences[0].play_head_position
			playhead_pixels = playhead_time * pixels_per_second
			
			# get the middle of the window
			screen_width = (self.width / 2) - 100
			
			if playhead_pixels > (current_scroll_pixels + screen_width):
				# scroll to last scroll position
				self.hscrollbar2.set_value(playhead_pixels - screen_width)

		
	def on_tlbResize_toggled(self, widget, *args):
		print "on_tlbResize_toggled called with self.%s" % widget.get_name()

		# determine what cursor mode is enable (arrow, razor, snap, etc...)
		(isArrow, isRazor, isSnap, isResize) = self.get_toolbar_options()  
		
		# only execute code if button is toggled (i.e. this gets called on un-toggle event also)
		if self.tlbResize.get_active():	
			
			# un-toggle the other toggles
			self.tlbArrow.set_active(False)
			self.tlbRazor.set_active(False)
			
		# Keep the arrow selected, if no other toggles are selected
		if isRazor == False and isResize == False:
			self.tlbArrow.set_active(True)
			
			
		
	def on_tlbSnap_toggled(self, widget, *args):
		print "on_tlbSnap_toggled called with self.%s" % widget.get_name()

		
		
		
	def on_drag_motion(self, wid, context, x, y, time):

		# Get the drag icon
		play_image = gtk.image_new_from_file(os.path.join(self.project.THEMES_DIR, self.project.theme, "icons", "plus.png"))
		pixbuf = play_image.get_pixbuf()

		# Set the drag icon
		context.set_icon_pixbuf(pixbuf, 0, 0)


	def on_drag_data_received(self, widget, context, x, y, selection, target_type, timestamp):

		# get the list of files that were dropped in the tree
		uri = selection.data.strip()
		uri_splitted = uri.split() # we may have more than one file dropped
		
		for uri in uri_splitted:
			# change cursor to "please wait"
			self.myTree.window.set_cursor(gtk.gdk.Cursor(150))
			
			# get the file path
			path = self.project.project_folder.get_file_path_from_dnd_dropped_uri(uri)
			
			# add file to current project
			self.project.project_folder.AddFile(path)

		# refresh the form (i.e. add new items to the treeview)
		self.refresh()
		
		# set cursor to normal
		self.myTree.window.set_cursor(None)



	def on_scrolledwindow_Left_scroll_event(self, widget, *args):
		# Don't bubble up the scroll event.  This prevents the scroll wheel from 
		# scrolling the individual canvas.
		self.on_scrolledwindow_Right_scroll_event(widget, *args)
		return True


	def on_scrolledwindow_Right_scroll_event(self, widget, *args):

		# Is the CTRL key pressed?
		if args[0].state & gtk.gdk.CONTROL_MASK:
			# CTRL Key - thus we need to zoom in or out
			if args[0].direction == gtk.gdk.SCROLL_DOWN:
				# Zoom Out
				self.on_btnZoomOu_clicked(widget)
			else:
				# Zoom In
				self.on_btnZoomIn_clicked(widget)
			
			
		else:
			
			# Regular scroll... scroll canvas vertical
			## Manually scroll the scrollbars
			if args[0].direction == gtk.gdk.SCROLL_DOWN:
				widget = self.vscrollbar2  
				vertical_value = widget.get_value() + 10
	
				# Update vertical scrollbar value
				widget.set_value(vertical_value)
	
				# Get horizontal value
				horizontal_scrollbar = self.hscrollbar2
				horizontal_value = horizontal_scrollbar.get_value()
	
				# scroll the canvases
				self.MyCanvas.scroll_to(horizontal_value, vertical_value)
				self.MyCanvas_Left.scroll_to(horizontal_value, vertical_value)
			else:
				widget = self.vscrollbar2	   
				vertical_value = widget.get_value() - 10
	
				# Update vertical scrollbar value
				widget.set_value(vertical_value)
	
				# Get horizontal value
				horizontal_scrollbar = self.hscrollbar2
				horizontal_value = horizontal_scrollbar.get_value()
	
				# scroll the canvases
				self.MyCanvas.scroll_to(horizontal_value, vertical_value)
				self.MyCanvas_Left.scroll_to(horizontal_value, vertical_value)



		# Don't bubble up the scroll event.  This prevents the scroll wheel from 
		# scrolling the individual canvas.   
		return True


	def on_vscrollbar2_value_changed(self, widget, *args):

		isinstance(widget, gtk.VScrollbar)		
		vertical_value = widget.get_value()

		# Get horizontal value
		horizontal_scrollbar = self.hscrollbar2
		horizontal_value = horizontal_scrollbar.get_value()

		# scroll the canvases
		self.MyCanvas.scroll_to(horizontal_value, vertical_value)
		self.MyCanvas_Left.scroll_to(horizontal_value, vertical_value)

	def on_treeFiles_button_press_event(self,treeview, event):
		"""This shows the right click menu"""
		#print "on_treeFiles_button_press_event"
		
		if (event.button == 3):
			# determine which item the user right clicked on
			# path, treecolumn, mouse_x, mouse_y = treeview.get_path_at_pos(int(event.x),int(event.y))
			# treeview.row_activated(path, treecolumn)
			
			# Get the selection
			selection = treeview.get_selection()
			# Get the selected path(s)
			rows, selected = selection.get_selected_rows()
		   
			mnu = mnuTree(rows, selected, form=self, project=self.project)
			mnu.showmnu(event, treeview)
				
			return True
		
	def on_icvFileIcons_button_press_event(self, widget, event):
		"""This shows the right click menu"""
		if (event.button == 3):
			#show the right click menu
			mnu = mnuTree(None, None, form=self, project=self.project)
			mnu.showmnu(event, widget)


	def on_hscrollbar2_value_changed(self, widget, *args):

		isinstance(widget, gtk.HScrollbar)		
		horizontal_value = widget.get_value()

		# Get vertical value
		vertical_scrollbar = self.vscrollbar2
		vertical_value = vertical_scrollbar.get_value()

		# scroll the canvases
		self.MyCanvas.scroll_to(horizontal_value, vertical_value)
		self.TimelineCanvas_Right.scroll_to(horizontal_value, 0.0)

		
		
class mnuTrack(SimpleGladeApp):
	
	def __init__(self, rows, selected, path="Main.glade", root="mnuTrackPopup", domain="OpenShot", form=None, project=None, **kwargs):
		SimpleGladeApp.__init__(self, os.path.join(project.GLADE_DIR, path), root, domain, **kwargs)

		# Add language support
		_ = Language_Init.Translator(project).lang.gettext
		self._ = _
		
		self.form = form
		self.project = project
		
	def showmnu(self, event, widget):
		# show the popup menu
		self.mnuTrackPopup.show_all()
		self.mnuTrackPopup.popup( None, None, None, event.button, event.time)
		
		# selected track
		self.selected_track = widget


	def on_mnuAddTrackAbove_activate(self, event):
		print "on_mnuAddTrackAbove_activate clicked"
		
		# get correct gettext method
		_ = self._
		
		# remove this track from it's parent sequence
		self.project.sequences[0].AddTrack(_("Track %s") % str(len(self.project.sequences[0].tracks) + 1), position="above", existing_track=self.selected_track)
		
		# refresh the interface
		self.project.Render()

		
	def on_mnuAddTrackBelow_activate(self, event):
		print "on_mnuAddTrackBelow_activate clicked"
		
		# get correct gettext method
		_ = self._
		
		# remove this track from it's parent sequence
		self.project.sequences[0].AddTrack(_("Track %s") % str(len(self.project.sequences[0].tracks) + 1), position="below", existing_track=self.selected_track)
		
		# refresh the interface
		self.project.Render()
		
		
	def on_mnuRenameTrack_activate(self, event):
		print "on_mnuRenameTrack_activate clicked"
		
		# get correct gettext method
		_ = self._
		
		# get the new name of the track
		text = inputbox.input_box(title="Openshot", message=_("Please enter a track name."), default_text=self.selected_track.name)
		
		if text:
			# rename track
			self.project.sequences[0].rename_track(self.selected_track, text)
			
			#refresh the interface
			self.project.Render()
			
		
	def on_mnuRemoveTrack_activate(self, event):
		print "on_mnuRemoveTrack_activate clicked"
		
		# remove this track from it's parent sequence
		self.selected_track.parent.tracks.remove(self.selected_track)
		
		# mark project as modified
		self.project.set_project_modified(is_modified=True, refresh_xml=True, type = _("Removed track"))
		# refresh the interface
		self.form.refresh()
		
	def on_mnuMoveTrackUp_activate(self, event):
		print "on_mnuMoveTrackUp_activate clicked"
		
		# mark project as modified
		self.project.set_project_modified(is_modified=True, refresh_xml=True, type = _("Moved track up"))
		
		# get index of current track
		index_existing_track = self.selected_track.parent.tracks.index(self.selected_track)
		
		if index_existing_track > 0:
			# remove existing track
			self.selected_track.parent.tracks.remove(self.selected_track)
			
			# insert at new position
			self.selected_track.parent.tracks.insert(index_existing_track - 1, self.selected_track)
			
			# refresh the interface
			self.project.Render()
			
		
	def on_mnuMoveTrackDown_activate(self, event):
		print "on_mnuMoveTrackDown_activate clicked"
		
		# mark project as modified
		self.project.set_project_modified(is_modified=True, refresh_xml=True, type = _("Moved track down"))
		
		# get index of current track
		index_existing_track = self.selected_track.parent.tracks.index(self.selected_track)
		
		if index_existing_track < len(self.selected_track.parent.tracks) - 1:
			# remove existing track
			self.selected_track.parent.tracks.remove(self.selected_track)
			
			# insert at new position
			self.selected_track.parent.tracks.insert(index_existing_track + 1, self.selected_track)
			
			# refresh the interface
			self.project.Render()
		
class mnuMarker(SimpleGladeApp):
	
	def __init__(self, rows, selected, path="Main.glade", root="mnuMarkerPopup", domain="OpenShot", form=None, project=None, **kwargs):
		SimpleGladeApp.__init__(self, os.path.join(project.GLADE_DIR, path), root, domain, **kwargs)

		# Add language support
		_ = Language_Init.Translator(project).lang.gettext
		self._ = _
		
		self.form = form
		self.project = project
		
		
	def showmnu(self, event, widget):
		# show the popup menu
		self.mnuMarkerPopup.show_all()
		self.mnuMarkerPopup.popup( None, None, None, event.button, event.time)
		
		# get selected widget
		self.selected_marker = widget
		
		
	def on_mnuRemoveMarker_activate(self, event):
		print "on_mnuRemoveMarker_activate clicked"
		
		# remove this marker
		self.selected_marker.parent.markers.remove(self.selected_marker)
		
		# mark project as modified
		self.project.set_project_modified(is_modified=True, refresh_xml=True)
		
		# refresh timeline
		self.form.refresh()
		
		
class mnuTransition(SimpleGladeApp):
	
	def __init__(self, rows, selected, path="Main.glade", root="mnuTransitionPopup", domain="OpenShot", form=None, project=None, **kwargs):
		SimpleGladeApp.__init__(self, os.path.join(project.GLADE_DIR, path), root, domain, **kwargs)

		# Add language support
		_ = Language_Init.Translator(project).lang.gettext
		self._ = _
		
		self.form = form
		self.project = project
		
		
	def showmnu(self, event, object, canvas_item):
		
		# get correct gettext method
		_ = self._
		
		if object.type == "transition":
			self.mnuMask.get_children()[0].set_label(_("Convert to Mask"))
			self.mnuRemoveTransition.get_children()[0].set_label(_("Remove Transition"))
			self.mnuReverseTransition.set_sensitive(True)
		elif object.type == "mask":
			self.mnuMask.get_children()[0].set_label(_("Convert to Transition"))
			self.mnuRemoveTransition.get_children()[0].set_label(_("Remove Mask"))
			self.mnuReverseTransition.set_sensitive(False)
		
		# show the popup menu
		self.mnuTransitionPopup.show_all()
		self.mnuTransitionPopup.popup( None, None, None, event.button, event.time)
		
		# get selected widget
		self.selected_transition = object
		self.selected_transition_item = canvas_item
		
		
	def on_mnuTransitionProperties_activate(self, event):
		print "on_mnuTransitionProperties_activate"
		
		# show frmExportVideo dialog
		self.frmTransitionProperties = TransitionProperties.frmTransitionProperties(form=self, project=self.project, current_transition=self.selected_transition)
		
		
		
	def on_mnuDuplicate_activate(self, event):
		print "on_mnuDuplicate_activate"
		
		# create new transition
		parent_track = self.selected_transition.parent
		new_trans = parent_track.AddTransition(self.selected_transition.name, self.selected_transition.position_on_track + 3, self.selected_transition.length, self.selected_transition.resource)
		new_trans.reverse = self.selected_transition.reverse
		new_trans.softness = self.selected_transition.softness
		new_trans.type = self.selected_transition.type
		new_trans.mask_value = self.selected_transition.mask_value
		
		# mark project as modified
		self.project.set_project_modified(is_modified=True, refresh_xml=True, type="Duplicated transition")
		
		# render to timeline
		new_trans.Render()

		
	def on_mnuMask_activate(self, event):
		print "on_mnuMask_activate"
		
		# get correct gettext method
		_ = self._
		
		# update type
		if self.selected_transition.type == "transition":
			self.selected_transition.type = "mask"

		elif self.selected_transition.type == "mask":
			self.selected_transition.type = "transition"
		
		# mark project as modified
		self.project.set_project_modified(is_modified=True, refresh_xml=True, type = _("Changed transition type"))
		
		# remove from canvas
		parent = self.selected_transition_item.get_parent()
		child_num = parent.find_child (self.selected_transition_item)
		parent.remove_child (child_num)
		
		# refresh timeline
		self.selected_transition.Render()
		
		
	def on_mnuRemoveTransition_activate(self, event):
		print "on_mnuRemoveTransition_activate clicked"
		
		# remove this clip (from the project)
		self.selected_transition.parent.transitions.remove(self.selected_transition)
		
		# remove from canvas
		parent = self.selected_transition_item.get_parent()
		child_num = parent.find_child (self.selected_transition_item)
		parent.remove_child (child_num)
		
		# mark project as modified
		self.project.set_project_modified(is_modified=True, refresh_xml=True, type = _("Removed transition"))

		
	def on_mnuShiftTransitions_activate (self, event):
		print "on_mnuShiftTransitions_activate clicked"
		
		shift = 0.0
		start_of_selected = float(self.selected_transition.position_on_track)
		
		# Get previous transition (if any)
		previous_transition = None
		transitions_on_track = self.selected_transition.parent.transitions
		index_of_selected_transition = transitions_on_track.index(self.selected_transition) - 1
		if index_of_selected_transition >= 0:
			previous_transition = transitions_on_track[index_of_selected_transition]

		# get correct gettext method
		_ = self._
		
		# get the amount of time the transitions are shifted
		text = inputbox.input_box(title="OpenShot", message=_("Please enter the # of seconds to shift the transitions:"), default_text="5.0")
		if text:
			# convert to peroid decimal
			text = text.replace(',', '.')
			try:
				# amount to shift
				shift = float(text)
				
				# is shift negative (i.e. shifting to the left)
				if shift < 0.0:
					# negative shift
					if previous_transition:
						end_of_previous = previous_transition.position_on_track + float(previous_transition.length)
						if shift + start_of_selected < end_of_previous:
							# get difference between previous clip, and selected clip
							shift = end_of_previous - start_of_selected
					
					else:
						# no previous clip, is clip going to start before timeline?
						if shift + start_of_selected < 0.0:
							# get difference between clip and beginning of timeline
							shift = 0.0 - start_of_selected
			except:
				# invalid shift amount... default to 0
				shift = 0.0
				
		if shift:
			# loop through clips, and shift
			for tr in self.selected_transition.parent.transitions:
				start = float(tr.position_on_track)
				if start >= start_of_selected:
					tr.position_on_track = start + shift

			# mark project as modified
			self.project.set_project_modified(is_modified=True, refresh_xml=True, type = _("Shifted transitions"))

			# render timeline
			self.form.refresh()



	def on_mnuReverseMarker_activate(self, event):
		print "on_mnuReverseMarker_activate clicked"
		
		# set the reverse property
		if self.selected_transition.reverse:
			self.selected_transition.reverse = False
		else:
			self.selected_transition.reverse = True
		
		# mark project as modified
		self.project.set_project_modified(is_modified=True, refresh_xml=True)
		
		# remove from canvas
		parent = self.selected_transition_item.get_parent()
		child_num = parent.find_child (self.selected_transition_item)
		parent.remove_child (child_num)
		
		# refresh timeline
		self.selected_transition.Render()
		
		
class mnuFadeSubMenu(SimpleGladeApp):
	
	def __init__(self, rows, selected, path="Main.glade", root="mnuFadeSubMenuPopup", domain="OpenShot", form=None, project=None, **kwargs):
		SimpleGladeApp.__init__(self, os.path.join(project.GLADE_DIR, path), root, domain, **kwargs)

		# Add language support
		_ = Language_Init.Translator(project).lang.gettext
		self._ = _
		
		self.form = form
		self.project = project

		
	def showmnu(self, event, object, canvas_item):
		# show the popup menu
		self.mnuFadeSubMenuPopup.show_all()
		self.mnuFadeSubMenuPopup.popup( None, None, None, event.button, event.time)
		
		# get selected widget
		self.selected_clip = None
		self.selected_clip_item = None
		
		
	def on_mnuFade_activate(self, event):
		print "on_mnuFade_activate"
		# get name of animation
		fade_name = event.get_name()
		
		if fade_name == "mnu_none":
			# remove fade from clip
			self.selected_clip.audio_fade_in = False
			self.selected_clip.audio_fade_out = False
			self.selected_clip.audio_fade_amount = 2.0
			self.selected_clip.video_fade_in = False
			self.selected_clip.video_fade_out = False
			self.selected_clip.video_fade_amount = 2.0
			
		elif fade_name == "mnu_fade_in_fast":
			# fade in (fast)
			self.selected_clip.audio_fade_in = True
			self.selected_clip.audio_fade_out = False
			self.selected_clip.audio_fade_amount = 2.0
			self.selected_clip.video_fade_in = True
			self.selected_clip.video_fade_out = False
			self.selected_clip.video_fade_amount = 2.0
			
		elif fade_name == "mnu_fade_out_fast":
			# fade out (fast)
			self.selected_clip.audio_fade_in = False
			self.selected_clip.audio_fade_out = True
			self.selected_clip.audio_fade_amount = 2.0
			self.selected_clip.video_fade_in = False
			self.selected_clip.video_fade_out = True
			self.selected_clip.video_fade_amount = 2.0
			
		elif fade_name == "mnu_fade_in_and_out_fast":
			# fade in and out (fast)
			self.selected_clip.audio_fade_in = True
			self.selected_clip.audio_fade_out = True
			self.selected_clip.audio_fade_amount = 2.0
			self.selected_clip.video_fade_in = True
			self.selected_clip.video_fade_out = True
			self.selected_clip.video_fade_amount = 2.0
			
		elif fade_name == "mnu_fade_in_slow":
			# fade in (slow)
			self.selected_clip.audio_fade_in = True
			self.selected_clip.audio_fade_out = False
			self.selected_clip.audio_fade_amount = 4.0
			self.selected_clip.video_fade_in = True
			self.selected_clip.video_fade_out = False
			self.selected_clip.video_fade_amount = 4.0
			
		elif fade_name == "mnu_fade_out_slow":
			# fade out (slow)
			self.selected_clip.audio_fade_in = False
			self.selected_clip.audio_fade_out = True
			self.selected_clip.audio_fade_amount = 4.0
			self.selected_clip.video_fade_in = False
			self.selected_clip.video_fade_out = True
			self.selected_clip.video_fade_amount = 4.0
			
		elif fade_name == "mnu_fade_in_and_out_slow":
			# fade in and out (slow)
			self.selected_clip.audio_fade_in = True
			self.selected_clip.audio_fade_out = True
			self.selected_clip.audio_fade_amount = 4.0
			self.selected_clip.video_fade_in = True
			self.selected_clip.video_fade_out = True
			self.selected_clip.video_fade_amount = 4.0
			
		# mark project as modified
		self.project.set_project_modified(is_modified=True, refresh_xml=True, type="Changed clip fade")
		
		
class mnuAnimateSubMenu(SimpleGladeApp):
	
	def __init__(self, rows, selected, path="Main.glade", root="mnuAnimateSubMenuPopup", domain="OpenShot", form=None, project=None, **kwargs):
		SimpleGladeApp.__init__(self, os.path.join(project.GLADE_DIR, path), root, domain, **kwargs)

		# Add language support
		_ = Language_Init.Translator(project).lang.gettext
		self._ = _
		
		self.form = form
		self.project = project

		
	def showmnu(self, event, object, canvas_item):
		# show the popup menu
		self.mnuAnimateSubMenuPopup.show_all()
		self.mnuAnimateSubMenuPopup.popup( None, None, None, event.button, event.time)
		
		# get selected widget
		self.selected_clip = None
		self.selected_clip_item = None
		
		
	def on_mnuAnimate_activate(self, event):
		print "on_mnuAnimate_activate"
		# get name of animation
		animation_name = event.get_name()
		
		# init vars
		start = self.selected_clip.keyframes["start"]
		end = self.selected_clip.keyframes["end"]
		#halign = self.selected_clip.halign
		#valign = self.selected_clip.valign
		halign = "centre"
		valign = "centre"
		
		# calculate the center coordinates (based on height & width)
		center_x = 0.0
		center_y = 0.0
		if start.width != 100:
			center_x = start.width / 2.0
		if start.height != 100:
			center_y = start.height / 2.0
		top = -100 + center_y
		bottom = 100 + center_y
		left = -100 + center_x
		right = 100 + center_x


		if animation_name == "mnu_none":
			start.set_all(100.0, 100.0, 0.0, 0.0, None)
			end.set_all(100.0, 100.0, 0.0, 0.0, None)



		######### ZOOM ...
		elif animation_name == "mnu_zoom_in_100_150":
			start.set_all(100.0, 100.0, 0.0, 0.0, None)
			end.set_all(150.0, 150.0, -25.0, -25.0, None)
			self.selected_clip.distort = True

		elif animation_name == "mnu_zoom_in_50_100":
			start.set_all(50.0, 50.0, 25.0, 25.0, None)
			end.set_all(100.0, 100.0, 0.0, 0.0, None)
			self.selected_clip.distort = True
			
		elif animation_name == "mnu_zoom_out_100_50":
			start.set_all(100.0, 100.0, 0.0, 0.0, None)
			end.set_all(50.0, 50.0, 25.0, 25.0, None)
			self.selected_clip.distort = True
			
		elif animation_name == "mnu_zoom_out_150_100":
			start.set_all(150.0, 150.0, -25.0, -25.0, None)
			end.set_all(100.0, 100.0, 0.0, 0.0, None)
			self.selected_clip.distort = True
			

		######### CENTER TO ...
		elif animation_name == "mnu_center_to_top":
			start.set_all(None, None, center_x, center_y, None)
			end.set_all(None, None, center_x, top, None)

		elif animation_name == "mnu_center_to_left":
			start.set_all(None, None, center_x, center_y, None)
			end.set_all(None, None, left, center_y, None)
			
		elif animation_name == "mnu_center_to_right":
			start.set_all(None, None, center_x, center_y, None)
			end.set_all(None, None, right, center_y, None)
			
		elif animation_name == "mnu_center_to_bottom":
			start.set_all(None, None, center_x, center_y, None)
			end.set_all(None, None, center_x, bottom, None)

		######### TO CENTER ...
		elif animation_name == "mnu_left_to_center":
			start.set_all(None, None, left, center_y, None)
			end.set_all(None, None, center_x, center_y, None)
			
		elif animation_name == "mnu_right_to_center":
			start.set_all(None, None, right, center_y, None)
			end.set_all(None, None, center_x, center_y, None)
			
		elif animation_name == "mnu_top_to_center":
			start.set_all(None, None, center_x, top, None)
			end.set_all(None, None, center_x, center_y, None)
			
		elif animation_name == "mnu_bottom_to_center":
			start.set_all(None, None, center_x, bottom, None)
			end.set_all(None, None, center_x, center_y, None)
			
		######### ACROSS
		elif animation_name == "mnu_left_to_right":
			start.set_all(None, None, left, center_y, None)
			end.set_all(None, None, right, center_y, None)

		elif animation_name == "mnu_right_to_left":
			start.set_all(None, None, right, center_y, None)
			end.set_all(None, None, left, center_y, None)

		elif animation_name == "mnu_top_to_bottom":
			start.set_all(None, None, center_x, top, None)
			end.set_all(None, None, center_x, bottom, None)

		elif animation_name == "mnu_bottom_to_top":
			start.set_all(None, None, center_x, bottom, None)
			end.set_all(None, None, center_x, top, None)


		# update clip properties
		self.selected_clip.halign = halign
		self.selected_clip.valign = valign
		
		# mark project as modified
		self.project.set_project_modified(is_modified=True, refresh_xml=True, type="Changed clip animation")
		


class mnuPositionSubMenu(SimpleGladeApp):
	
	def __init__(self, rows, selected, path="Main.glade", root="mnuPositionSubMenuPopup", domain="OpenShot", form=None, project=None, **kwargs):
		SimpleGladeApp.__init__(self, os.path.join(project.GLADE_DIR, path), root, domain, **kwargs)

		# Add language support
		_ = Language_Init.Translator(project).lang.gettext
		self._ = _
		
		self.form = form
		self.project = project

		
	def showmnu(self, event, object, canvas_item):
		# show the popup menu
		self.mnuPositionSubMenuPopup.show_all()
		self.mnuPositionSubMenuPopup.popup( None, None, None, event.button, event.time)
		
		# get selected widget
		self.selected_clip = None
		self.selected_clip_item = None
		
		
	def on_mnuPosition_activate(self, event):
		print "on_mnuPosition_activate"
		# get name of animation
		position_name = event.get_name()
		
		# init vars
		start = self.selected_clip.keyframes["start"]
		end = self.selected_clip.keyframes["end"]
		halign = "centre"
		valign = "centre"
		
		if position_name == "mnu_none":
			start.set_all(100.0, 100.0, 0.0, 0.0, None)
			end.set_all(100.0, 100.0, 0.0, 0.0, None)


		######### 1/4 Size
		elif position_name == "mnu_top_left_1_4":
			start.set_all(50.0, 50.0, 0.0, 0.0, None)
			end.set_all(50.0, 50.0, 0.0, 0.0, None)

		elif position_name == "mnu_top_right_1_4":
			start.set_all(50.0, 50.0, 50.0, 0.0, None)
			end.set_all(50.0, 50.0, 50.0, 0.0, None)

		elif position_name == "mnu_bottom_left_1_4":
			start.set_all(50.0, 50.0, 0.0, 50.0, None)
			end.set_all(50.0, 50.0, 0.0, 50.0, None)

		elif position_name == "mnu_bottom_right_1_4":
			start.set_all(50.0, 50.0, 50.0, 50.0, None)
			end.set_all(50.0, 50.0, 50.0, 50.0, None)

		elif position_name == "mnu_center_1_4":
			start.set_all(50.0, 50.0, 25.0, 25.0, None)
			end.set_all(50.0, 50.0, 25.0, 25.0, None)
			
		elif position_name == "mnu_show_all_stretch":
			# Show All Clips at the same time
			self.show_all_clips(stretch=True)
			
		elif position_name == "mnu_show_all_nostretch":
			# Show All Clips at the same time
			self.show_all_clips(stretch=False)

		# update clip properties
		self.selected_clip.halign = halign
		self.selected_clip.valign = valign
		
		# mark project as modified
		self.project.set_project_modified(is_modified=True, refresh_xml=True, type="Changed clip layout")
		
	def show_all_clips(self, stretch=False):
		""" Show all clips  """
		from math import sqrt
		
		# get starting position
		start_position = self.selected_clip.position_on_track
		available_clips = []
		
		# Get the number of clips that start near the start of this clip (on any track)
		for track in self.project.sequences[0].tracks:
			# loop through clips
			for clip in track.clips:
				# only look at images, videos, and image sequences
				if clip.file_object.file_type in ["image", "video", "image sequence"]:
					# only look at clips that start near this clip
					if clip.position_on_track >= (start_position - 0.5) and clip.position_on_track <= (start_position + 0.5):
						# add to list
						available_clips.append(clip)
						
		# Get the number of rows
		number_of_clips = len(available_clips)
		number_of_rows = int(sqrt(number_of_clips))
		max_clips_on_row = float(number_of_clips) / float(number_of_rows)
		
		# Determine how many clips per row
		if max_clips_on_row > float(int(max_clips_on_row)):
			max_clips_on_row = int(max_clips_on_row + 1)
		else:
			max_clips_on_row = int(max_clips_on_row)
			
		# Calculate Height & Width
		height = 100.0 / float(number_of_rows)
		width = 100.0 / float(max_clips_on_row)
		
		clip_index = 0
		
		# Loop through each row of clips
		for row in range(0, number_of_rows):

			# Loop through clips on this row
			column_string = " - - - "
			for col in range(0, max_clips_on_row):
				if clip_index < number_of_clips:
					# Calculate X & Y
					X = float(col) * width
					Y = float(row) * height
					
					# Modify clip layout settings
					selected_clip = available_clips[clip_index]
					selected_clip.halign = "centre"
					selected_clip.valign = "centre"
					
					if stretch:
						selected_clip.distort = True
						selected_clip.fill = True
					else:
						selected_clip.distort = False
						selected_clip.fill = True						
					
					start = selected_clip.keyframes["start"]
					end = selected_clip.keyframes["end"]
					start.set_all(height, width, X, Y, None)
					end.set_all(height, width, X, Y, None)
			
					# Increment Clip Index
					clip_index += 1
		
		
		
		
class mnuClip(SimpleGladeApp):
	
	def __init__(self, rows, selected, path="Main.glade", root="mnuClipPopup", domain="OpenShot", form=None, project=None, **kwargs):
		SimpleGladeApp.__init__(self, os.path.join(project.GLADE_DIR, path), root, domain, **kwargs)

		# Add language support
		_ = Language_Init.Translator(project).lang.gettext
		self._ = _
		
		self.form = form
		self.project = project

		
	def showmnu(self, event, object, canvas_item):
		# show the popup menu
		self.mnuClipPopup.show_all()
		self.mnuClipPopup.popup( None, None, None, event.button, event.time)
		
		# get selected widget
		self.selected_clip = object
		self.selected_clip_item = canvas_item
		
		# update sub-menu references
		self.form.mnuFadeSubMenu1.selected_clip = object
		self.form.mnuFadeSubMenu1.selected_clip_item = canvas_item
		self.form.mnuAnimateSubMenu1.selected_clip = object
		self.form.mnuAnimateSubMenu1.selected_clip_item = canvas_item
		self.form.mnuPositionSubMenu1.selected_clip = object
		self.form.mnuPositionSubMenu1.selected_clip_item = canvas_item
		
		if ".svg" in self.selected_clip.name:
			self.mnuClipEditTitle.show()
		else:
			self.mnuClipEditTitle.hide()
		
		
	def on_mnuClipEditTitle_activate(self, event):
		#print "on_mnuClipEditTitle_activate"
		
		#edit a title using the title editor		
		Titles.frmNewTitle(form=self.form, project=self.project, file=os.path.join(self.project.folder, self.selected_clip.file_object.name))
		
		# mark project as modified
		self.project.set_project_modified(is_modified=True, refresh_xml=True, type = _("Edited title"))
		
		# render timeline
		self.form.refresh()
		
		
	def on_mnuClipProperties_activate(self, event):
		print "on_mnuClipProperties_activate"
				
		# show frmExportVideo dialog
		self.frmClipProperties = ClipProperties.frmClipProperties(form=self.form, project=self.project, current_clip=self.selected_clip, current_clip_item=self.selected_clip_item)
		

	def on_mnuRemoveClip_activate(self, event):
		print "on_mnuRemoveClip_activate clicked"
		
		# remove this clip
		self.selected_clip.parent.clips.remove(self.selected_clip)
		
		# remove from canvas
		parent = self.selected_clip_item.get_parent()
		child_num = parent.find_child (self.selected_clip_item)
		parent.remove_child (child_num)
		
		# mark project as modified
		self.project.set_project_modified(is_modified=True, refresh_xml=True, type = _("Removed clip"))
		
		
	def on_mnuShiftClips_activate (self, event):
		print "on_mnuShiftClips_activate clicked"
		
		shift = 0.0
		start_of_selected = float(self.selected_clip.position_on_track)
		
		# Get previous clip (if any)
		previous_clip = None
		clips_on_track = self.selected_clip.parent.clips
		index_of_selected_clip = clips_on_track.index(self.selected_clip) - 1
		if index_of_selected_clip >= 0:
			previous_clip = clips_on_track[index_of_selected_clip]

		# get correct gettext method
		_ = self._
		
		# get the amount of time the clips are shifted
		text = inputbox.input_box(title="OpenShot", message=_("Please enter the # of seconds to shift the clips:"), default_text="5.0")
		if text:
			# convert to peroid decimal
			text = text.replace(',', '.')
			try:
				# amount to shift
				shift = float(text)
				
				# is shift negative (i.e. shifting to the left)
				if shift < 0.0:
					# negative shift
					if previous_clip:
						end_of_previous_clip = previous_clip.position_on_track + float(previous_clip.length())
						if shift + start_of_selected < end_of_previous_clip:
							# get difference between previous clip, and selected clip
							shift = end_of_previous_clip - start_of_selected
					
					else:
						# no previous clip, is clip going to start before timeline?
						if shift + start_of_selected < 0.0:
							# get difference between clip and beginning of timeline
							shift = 0.0 - start_of_selected
			except:
				# invalid shift amount... default to 0
				shift = 0.0
				
		if shift:
			# loop through clips, and shift
			for cl in self.selected_clip.parent.clips:
				start = float(cl.position_on_track)
				if start >= start_of_selected:
					cl.position_on_track = start + shift

			# mark project as modified
			self.project.set_project_modified(is_modified=True, refresh_xml=True, type = _("Shifted clips"))

			# render timeline
			self.form.refresh()


	def on_mnuDuplicate_activate(self, event):
		print "on_mnuDuplicate_activate"
		
		# create new clip
		parent_track = self.selected_clip.parent
		is_title = False
		
		#if the file is a title, create a unique copy
		#to make each title unique and editable	
		if self.selected_clip.file_object.file_type == "image" and ".svg" in self.selected_clip.file_object.name:
			is_title = True
			(filepath, filename) = os.path.split(self.selected_clip.file_object.name)
			(shortname, extension) = os.path.splitext(filename)
		
			#add a number to the end of the shortname.
			#get the next available number for the file
			blnFind = True 
			intNum = 0
			while blnFind == True:
				intNum += 1
				blnFind = os.path.exists(os.path.join(filepath, shortname + str(intNum) + extension))
			
			#append the number to the filename 			
			shortname = shortname + str(intNum)
			#create a copy of the selected file with the new name
			shutil.copy(os.path.join(filepath, filename), os.path.join(filepath, shortname + extension))
			#Add the new file to the project so it shows up in the tree view
			self.project.project_folder.AddFile(os.path.join(filepath, shortname + extension))
			#Add the new file object to the timeline
			new_file_object = self.project.project_folder.FindFile(os.path.join(filepath, shortname + extension))
			
			# Duplidate title clip
			new_clip = parent_track.AddClip(shortname + extension, self.selected_clip.color, self.selected_clip.position_on_track + 3, self.selected_clip.start_time, self.selected_clip.end_time, new_file_object)
			
		else:
			# Not a title (i.e. regular videos, images, and audio)
			new_clip = parent_track.AddClip(self.selected_clip.name, self.selected_clip.color, self.selected_clip.position_on_track + 3, self.selected_clip.start_time, self.selected_clip.end_time, self.selected_clip.file_object)
		
		
		# set all properties from the clip on the new duplicated clip
		new_clip.max_length = self.selected_clip.max_length
		new_clip.fill = self.selected_clip.fill
		new_clip.distort = self.selected_clip.distort
		new_clip.composite = self.selected_clip.composite
		new_clip.speed = self.selected_clip.speed
		new_clip.play_video = self.selected_clip.play_video
		new_clip.play_audio = self.selected_clip.play_audio
		new_clip.halign = self.selected_clip.halign
		new_clip.valign = self.selected_clip.valign
		new_clip.reversed = self.selected_clip.reversed
		new_clip.volume = self.selected_clip.volume
		new_clip.audio_fade_in = self.selected_clip.audio_fade_in
		new_clip.audio_fade_out = self.selected_clip.audio_fade_out
		new_clip.audio_fade_amount = self.selected_clip.audio_fade_amount
		new_clip.video_fade_in = self.selected_clip.video_fade_in
		new_clip.video_fade_out = self.selected_clip.video_fade_out
		new_clip.video_fade_amount = self.selected_clip.video_fade_amount
		new_clip.keyframes = copy.deepcopy(self.selected_clip.keyframes)
		new_clip.effects = copy.deepcopy(self.selected_clip.effects)
		
		# mark project as modified
		self.project.set_project_modified(is_modified=True, refresh_xml=True, type="Duplicated clip")

		# render to timeline
		new_clip.RenderClip()
		
		# Refresh (if title was duplicated)
		if is_title:
			self.form.refresh()
		
		
	def on_mnuSliceandShuffle_activate(self, event):
		""" Cut a clip into many small pieces and shuffle them """
		print "on_mnuSliceandShuffle_activate"
		import random
		
		# get correct gettext method
		_ = self._
		
		# init the list of clips
		min_random_length = 2.0
		max_random_length = 2.0
		list_of_clips = []
		end_of_clip = False
		
		clip_start = self.selected_clip.start_time
		clip_length = self.selected_clip.length()
		clip_max_length = self.selected_clip.max_length
		total_length = float(clip_start)
		position_on_track = float(self.selected_clip.position_on_track)
		
		
		# check for the minimun length validation
		if clip_length <= max_random_length:
			# show error
			messagebox.show(_("Error!"), _("You must select a clip which is more than %s seconds long." % max_random_length))
			return
			
		# loop through the clip, in increments of 2 to 5 seconds
		while not end_of_clip:
						
			# random number between 2 and 5
			random_length = float(random.Random().randint(min_random_length, max_random_length))

			# add clip properties to list
			list_of_clips.append([self.selected_clip.name, self.selected_clip.color, total_length, total_length + random_length, self.selected_clip.file_object, clip_max_length, random_length])

			# increment running total 
			total_length = total_length + random_length

			# kill loop when we reach the end
			if total_length + max_random_length >= clip_length:
				end_of_clip = True

				# add clip properties to list
				list_of_clips.append([self.selected_clip.name, self.selected_clip.color, total_length, total_length + (clip_length - total_length), self.selected_clip.file_object, clip_max_length, random_length])
			
			
		# shuffle the list of clips
		random.shuffle(list_of_clips)
		
		# actually add the clips to the track
		for clip in list_of_clips:
			# add clip
			Clip1 = self.selected_clip.parent.AddClip(clip[0], clip[1], position_on_track, clip[2], clip[3], clip[4])
			Clip1.max_length = clip[5]
			
			# increment position_on_track
			position_on_track = position_on_track + clip[6]
			
		# remove original clip from the timeline
		self.selected_clip.parent.clips.remove(self.selected_clip)
		
		# mark project as modified
		self.project.set_project_modified(is_modified=True, refresh_xml=True, type = _("Sliced and shuffled clip"))

		# render timeline
		self.form.refresh()
		
		
	def on_mnuSliceandCut_activate(self, event):
		""" Cut a clip into many small pieces and shuffle them """
		print "on_mnuSliceandCut_activate"
		import random
		
		# get correct gettext method
		_ = self._
		
		# init the list of clips
		min_random_length = 2
		max_random_length = 2
		list_of_clips = []
		end_of_clip = False
		
		clip_start = self.selected_clip.start_time
		clip_length = self.selected_clip.length()
		clip_max_length = self.selected_clip.max_length
		total_length = float(clip_start)
		position_on_track = float(self.selected_clip.position_on_track)
		should_add = True
		
		# check for the minimun length validation
		if clip_length <= max_random_length:
			# show error
			messagebox.show(_("Error!"), _("You must select a clip which is more than %s seconds long." % max_random_length))
			return
			
		# loop through the clip, in increments of 2 to 5 seconds
		while not end_of_clip:
						
			# random number between 2 and 5
			#random_length = float(random.Random().randint(min_random_length, max_random_length))

			# add clip properties to list
			if should_add:
				random_length = 2
				list_of_clips.append([self.selected_clip.name, self.selected_clip.color, total_length, total_length + random_length, self.selected_clip.file_object, clip_max_length, random_length])
				should_add = False
			else:
				random_length = 4
				should_add = True

			# increment running total 
			total_length = total_length + random_length

			# kill loop when we reach the end
			if total_length + max_random_length >= clip_length:
				end_of_clip = True

				# add clip properties to list
				if should_add:
					list_of_clips.append([self.selected_clip.name, self.selected_clip.color, total_length, total_length + (clip_length - total_length), self.selected_clip.file_object, clip_max_length, random_length])
					should_add = False
				else:
					should_add = True
			

		# actually add the clips to the track
		for clip in list_of_clips:
			# add clip
			Clip1 = self.selected_clip.parent.AddClip(clip[0], clip[1], position_on_track, clip[2], clip[3], clip[4])
			Clip1.max_length = clip[5]
			
			# increment position_on_track
			position_on_track = position_on_track + clip[6]
			
		
		# remove original clip from the timeline
		self.selected_clip.parent.clips.remove(self.selected_clip)
		
		# mark project as modified
		self.project.set_project_modified(is_modified=True, refresh_xml=True, type = _("Sliced and cut clips"))

		# render timeline
		self.form.refresh()
		
		
class mnuTree(SimpleGladeApp):

	def __init__(self, rows, selected, path="Main.glade", root="mnuTreePopUp", domain="OpenShot", form=None, project=None, **kwargs):
		SimpleGladeApp.__init__(self, os.path.join(project.GLADE_DIR, path), root, domain, **kwargs)

		# Add language support
		_ = Language_Init.Translator(project).lang.gettext
		self._ = _

		self.mnuTree  = self.mnuTreePopUp
		self.model = rows
		self.selected = selected
		self.form = form
		self.project = project


	def showmnu(self, event, widget):

		# get correct gettext method
		_ = self._
		
		#Show the right click menu.
		#dynamically show menu items depending on tree contents.
		#The Add Folder & Add File items are in the glade file - we always want them.
		name = widget.get_name()
		
		if self.project.project_folder.items.__len__() != 0:
			
			is_video_selected = False
			is_svg_selected = False
			
			# Preview File
			mnuPreview = gtk.ImageMenuItem(gtk.STOCK_MEDIA_PLAY)
			mnuPreview.get_children()[0].set_label(_("Preview File"))
			mnuPreview.connect('activate',self.on_mnuPreview_activate)
			self.mnuTree.add(mnuPreview)
			
			mnuSeparator = gtk.SeparatorMenuItem()
			self.mnuTree.add(mnuSeparator)
			
			#View options depend on what view is active
			if name == "treeFiles":
				
				iters = [self.model.get_iter(path) for path in self.selected]
				for iter in iters:
					# remove from the file object
					filename = self.model.get_value(iter, 1)
					unique_id = self.model.get_value(iter, 4)
					
					# get file object
					f = self.project.project_folder.FindFileByID(unique_id)
					if f:
						if f.file_type == "video":
							is_video_selected = True
						if f.file_type == "image" and ".svg" in f.name:
							is_svg_selected = True

				# show convert to image sequence (if video is selected)
				if is_video_selected:
					mnuConvertToImages = gtk.ImageMenuItem(gtk.STOCK_CONVERT)
					mnuConvertToImages.get_children()[0].set_label(_("Convert To Image Sequence"))
					mnuConvertToImages.connect('activate',self.on_mnuConvertToImages_activate)
					self.mnuTree.add(mnuConvertToImages)
				
				# add thumbnail option
				mnuThumbView = gtk.ImageMenuItem(gtk.STOCK_FULLSCREEN)
				mnuThumbView.get_children()[0].set_label(_("Thumbnail view"))
				mnuThumbView.connect('activate',self.on_mnuThumbView_activate)
				self.mnuTree.add(mnuThumbView)
				
				#Move Files to folder
				mnuMoveFile = gtk.ImageMenuItem(gtk.STOCK_GO_FORWARD)
				mnuMoveFile.get_children()[0].set_label(_("Move File(s) to Folder"))
				self.mnuTree.add(mnuMoveFile)
				
				folders =  self.project.project_folder.ListFolders()
				mnuSubMenu = gtk.Menu()
				
				#populate the sub menu with available folders
				for folder in folders:
					item = gtk.ImageMenuItem(gtk.STOCK_OPEN)
					item.get_children()[0].set_label(folder)					
					item.connect("activate", self.move_file_to_folder, folder)
					mnuSubMenu.add(item)
					
				#add remove from folder
				if folders:
					mnuSeparator = gtk.SeparatorMenuItem()
					mnuSubMenu.add(mnuSeparator)
					
					item = gtk.ImageMenuItem(gtk.STOCK_REMOVE)
					item.get_children()[0].set_label(_("Remove from Folder"))					
					item.connect("activate", self.move_file_to_folder, _("Remove from Folder"))
					mnuSubMenu.add(item)
				
				# add sub-menu to menu
				mnuMoveFile.set_submenu(mnuSubMenu)
			else:
				# add detail view toggle
				mnuDetailView = gtk.ImageMenuItem(gtk.STOCK_LEAVE_FULLSCREEN)
				mnuDetailView.get_children()[0].set_label(_("Detail view"))
				mnuDetailView.connect('activate',self.on_mnuDetailView_activate)
				self.mnuTree.add(mnuDetailView)

			mnuSeparator = gtk.SeparatorMenuItem()
			self.mnuTree.add(mnuSeparator)
					
			if is_svg_selected:
				mnuEditTitle = gtk.ImageMenuItem(gtk.STOCK_EDIT)
				mnuEditTitle.get_children()[0].set_label(_("Edit Title (Simple)"))
				mnuEditTitle.connect('activate',self.on_mnuEditTitle_activate, "simple")
				self.mnuTree.add(mnuEditTitle)
				
				mnuEditTitle1 = gtk.ImageMenuItem(gtk.STOCK_EDIT)
				mnuEditTitle1.get_children()[0].set_label(_("Edit Title (Inkscape)"))
				mnuEditTitle1.connect('activate',self.on_mnuEditTitle_activate, "advanced")
				self.mnuTree.add(mnuEditTitle1)

			#Remove File
			mnuRemoveFile = gtk.ImageMenuItem(gtk.STOCK_DELETE)
			mnuRemoveFile.get_children()[0].set_label(_("Remove File(s)"))
			mnuRemoveFile.connect('activate',self.on_mnuRemoveFile_activate)
			self.mnuTree.add(mnuRemoveFile)

			mnuSeparator = gtk.SeparatorMenuItem()
			self.mnuTree.add(mnuSeparator)

			#File properties
			mnuFileProperties = gtk.ImageMenuItem(gtk.STOCK_PROPERTIES)
			mnuFileProperties.get_children()[0].set_label(_("File Properties"))
			mnuFileProperties.connect('activate', self.on_FileProperties_activate)
			self.mnuTree.add(mnuFileProperties)

			self.mnuTree.show_all()

		self.mnuTree.popup( None, None, None, event.button, event.time)

		
	def move_file_to_folder(self, widget, folder):
		frm = self.form
		iters = [self.model.get_iter(path) for path in self.selected]
		for iter in iters:
			filename = self.model.get_value(iter, 1)
			
			if folder == _("Remove from Folder"):
				self.project.project_folder.RemoveParent(filename, folder)
			else:
				self.project.project_folder.AddParentToFile(filename, folder)
				
		frm.refresh() 
			
	def on_mnuPreview_activate(self, event):
		print "on_mnuPreview_activate"
		
		# get translation method
		_ = self._
		
		detail_view = self.form.scrolledwindow1.get_property('visible')
		if detail_view == True:

			# loop through all selected files
			iters = [self.model.get_iter(path) for path in self.selected]
			if iters:
				for iter in iters:

					# get the file object
					unique_id = self.model.get_value(iter, 4)
					f = self.project.project_folder.FindFileByID(unique_id)

					if f:
						
						# get file name, path, and extention
						if not os.path.isfile(f.name) and f.file_type != "image sequence":
							messagebox.show("OpenShot", _("The following file(s) no longer exist.") + "\n\n" + f.name)
							break
						
						(dirName, filename) = os.path.split(f.name)
						(fileBaseName, fileExtension)=os.path.splitext(filename)
						
						# ****************************
						# re-load the xml
						if self.form.MyVideo:
							self.form.MyVideo.set_project(self.project, self.form, os.path.join(self.project.USER_DIR, "sequence.mlt"), mode="override", override_path=f.name)
							self.form.MyVideo.load_xml()
						
						# start and stop the video
						self.project.form.MyVideo.play()
								
						# refresh sdl
						self.project.form.MyVideo.c.set("refresh", 1)
						break
		else:
			# thumbnail view
			#get the file info from the iconview
			selected = self.form.icvFileIcons.get_selected_items()
			model = self.form.icvFileIcons.get_model()
			
			# loop through all selected files
			iters = [model.get_iter(path) for path in selected]
			if iters:
				for iter in iters:
			
					# get the file object
					unique_id = model.get_value(iter, 3)
					f = self.project.project_folder.FindFileByID(unique_id)

					if f:
						# get file name, path, and extention
						if not os.path.isfile(f.name) and file_type != "image sequence":
							messagebox.show("OpenShot", _("The following file(s) no longer exist.") + "\n\n" + f.name)
							break
						
						# get file name, path, and extention
						(dirName, filename) = os.path.split(f.name)
						(fileBaseName, fileExtension)=os.path.splitext(filename)
						
						# ****************************
						# re-load the xml
						if self.form.MyVideo:
							self.form.MyVideo.set_project(self.project, self.form, os.path.join(self.project.USER_DIR, "sequence.mlt"), mode="override", override_path=f.name)
							self.form.MyVideo.load_xml()
						
						# start and stop the video
						self.project.form.MyVideo.play()
						
						# refresh sdl
						self.project.form.MyVideo.c.set("refresh", 1)
						break
		
			
	def on_mnuConvertToImages_activate(self, event):
		print "on_mnuConvertToImages_activate"
		
		# FIXME: (TJ) is thumbnail actually used in this method?
		# find the thumbnail folder location
		# FIXME: (TJ) Is this 'thumbnail/' per-project directory supposed to be ~/.openshot/thumbnail ?
		project_path = self.project.folder
		thumbnail_path = os.path.join(project_path, "thumbnail")
		
		# change cursor to "please wait"
		self.form.myTree.window.set_cursor(gtk.gdk.Cursor(150))
		self.form.myTree.window.set_cursor(gtk.gdk.Cursor(150))
		
		# loop through all selected files
		iters = [self.model.get_iter(path) for path in self.selected]
		for iter in iters:
			
			# get the file object
			unique_id = self.model.get_value(iter, 4)
			f = self.project.project_folder.FindFileByID(unique_id)
			
			# get file name, path, and extention
			(dirName, filename) = os.path.split(f.name)
			(fileBaseName, fileExtension)=os.path.splitext(filename)
			
			# if file is a video or image
			if f.file_type == "video":
				# create a new folder for this file (inside the thumbnail folder)
				new_folder_path = os.path.join(dirName, fileBaseName)
				
				# create thumbnail folder (if it doesn't exist)
				# FIXME: (TJ) This doesn't use thumbnail_path - should it?
				if os.path.exists(new_folder_path) == False:
					# create new thumbnail folder
					os.mkdir(new_folder_path)
				
				# convert to image sequence
				self.project.project_folder.ConvertFileToImages(f.name)
				
		#mark the project as modified
		self.project.set_project_modified(is_modified=True, refresh_xml=True)
				
		# refresh the form (i.e. add new items to the treeview)
		self.form.refresh()
				
		# set cursor to normal
		self.form.myTree.window.set_cursor(None)
				
			
	def on_mnuAddFile_activate(self, event):
		AddFiles.frmAddFiles(form=self.form, project=self.project)

	def on_mnuAddNewFolder_activate(self, event):
		frm = frmFolders(form=self.form, project=self.project)
		frm.show()
		
		
	def on_mnuEditTitle_activate(self, event, mode="simple"):
		print "on_mnuEditTitle_activate"
		prog = "inkscape"
		
		# get correct gettext method
		_ = self._
		
		#use an external editor to edit the image
		try:
			
			# find selected file
			frm = self.form
			detail_view = frm.scrolledwindow1.get_property('visible')
			
			if detail_view == True:
				iters = [self.model.get_iter(path) for path in self.selected]
				for iter in iters:
					# get file name and unique id
					filename = self.model.get_value(iter, 1)
					unique_id = self.model.get_value(iter, 4)
					
					file_item = self.project.project_folder.FindFileByID(unique_id)
					if file_item and mode == "advanced":
						# ADVANCED EDIT MODE
						# launch Inkscape
						#check if inkscape is installed
						if os.system('which ' + prog + ' 2>/dev/null') == 0:
							# launch Inkscape
							os.system("%s '%s'" % (prog, file_item.name))
							# Update thumbnail
							self.project.thumbnailer.get_thumb_at_frame(file_item.name)
							self.form.refresh()
						else:
							messagebox.show(_("OpenShot Error"), _("Please install %s to use this function." % (prog.capitalize())))
							
					if file_item and mode == "simple":
						# SIMPLE EDIT MODE
						#edit a title using the title editor		
						Titles.frmNewTitle(form=self.form, project=self.project, file=os.path.join(self.project.folder, file_item.name))
						
						# Update thumbnail
						self.project.thumbnailer.get_thumb_at_frame(file_item.name)
						self.form.refresh()
		
					#mark the project as modified
					self.project.set_project_modified(is_modified=True, refresh_xml=True)
			
		except:
			messagebox.show(_("OpenShot Error"), _("There was an error opening '%s', is it installed?" % (prog)))

		

	def on_mnuRemoveFile_activate(self, event):
		"""Removes a file from the treeview & project"""
		frm = self.form
		detail_view = frm.scrolledwindow1.get_property('visible')
		if detail_view == True:
			iters = [self.model.get_iter(path) for path in self.selected]
			for iter in iters:
				#remove from the file object
				filename = self.remove_markup(self.model.get_value(iter, 1))
				self.model.remove(iter)
				self.project.project_folder.RemoveFile(filename)
								
			frm.refresh()		
		else:
			#iconview is active
			selected = frm.icvFileIcons.get_selected_items()
			for item in selected:
				i = item[0]
				model = frm.icvFileIcons.get_model()
				filename = model[i][1]

				#remove the item from the project items list	
				self.project.project_folder.RemoveFile(filename)
				
			frm.refresh_thumb_view()
			
		#mark the project as modified
		self.project.set_project_modified(is_modified=True, refresh_xml=True)

	def remove_markup(self,data):
		p = re.compile(r'<[^<]*?/?>')
		return p.sub('', data)		

	def on_FileProperties_activate(self, event):
		#show the file properties window
		frm = self.form
		
		detail_view = frm.scrolledwindow1.get_property('visible')
		if detail_view == True:
			if len(self.selected) > 1:
				#if more than 1 row selected, don't try and show the dialog
				return
			if len(self.selected) > 0:
				iters = [self.model.get_iter(path) for path in self.selected]
				for iter in iters:
					file = self.model.get_value(iter, 1)
					unique_id = self.model.get_value(iter, 4)
			else: #nothing selected
				return
			
		else:
			#iconview is active
			selected = frm.icvFileIcons.get_selected_items()
			if len(selected) > 1:
				#more than 1 row selected, don't show the dialog
				return
			if len(selected) > 0:
				i = selected[0][0]
				model = frm.icvFileIcons.get_model()
				file = model[i][1]
				unique_id = model[i][3]
			else: #nothing selected
				return
			
		#pass the file item to the file properties window
		file_item = self.project.project_folder.FindFileByID(unique_id)
		if file_item:
			FileProperties.frmFileproperties(file_item, form=self, project=self.project)
			
		

	def on_mnuThumbView_activate(self, event):
		"""switch the view to the thumbnail view"""
		frm = self.form
		frm.scrolledwindow1.set_property('visible', False)
		child = frm.scrFileIcons
		frm.nbFiles.reorder_child(child, 0)
		frm.scrFileIcons.set_property('visible', True)
		frm.icvFileIcons.set_property('visible', True)
		frm.nbFiles.set_current_page(0)
		frm.refresh_thumb_view()
		
		# resize the icon window so the icons don't all spread out
		frm.icvFileIcons.resize_children()
		frm.scrFileIcons.resize_children()
		frm.icvFileIcons.set_reallocate_redraws(True)
		frm.scrFileIcons.set_reallocate_redraws(True)
		

	def on_mnuDetailView_activate(self, event):
		"""switch the view to the treeview"""
		frm = self.form
		frm.scrFileIcons.set_property('visible', False)
		child = frm.scrolledwindow1
		frm.nbFiles.reorder_child(child, 0)
		frm.scrolledwindow1.set_property('visible', True)
		frm.myTree.set_property('visible', True)
		frm.nbFiles.set_current_page(0)
		frm.refresh()
	 
	#can't use this when treeview is in Multiple select mode	
	#def get_current_row(self):
	#	"""returns the current row from the treeview"""
	#	frm = current_main_form
	#	selection = frm.myTree.get_selection()
	#	model, iter = frm.myTree.get_selection().get_selected()
	#	return model, iter
		
class frmFolders(SimpleGladeApp):

	def __init__(self, path="Main.glade", root="frmFolder", domain="OpenShot", form=None, project=None, **kwargs):
		SimpleGladeApp.__init__(self, os.path.join(project.GLADE_DIR, path), root, domain, **kwargs)
		
		# Add language support
		_ = Language_Init.Translator(project).lang.gettext
		self._ = _
		
		self.FolderDlg  = self.frmFolder
		self.form = form
		self.project = project
		
	def show(self):
		self.FolderDlg.run()
		
	def on_btnCancel_clicked(self, widget, *args):
		self.FolderDlg.destroy()
		
	def on_btnOK_clicked(self, widget, *args):
		if self.txtFolderName.get_text() != "":
			folder_name = self.txtFolderName.get_text()
			self.project.project_folder.AddFolder(folder_name)		
		self.FolderDlg.destroy()




def main():
	frm_main = frmMain()
	frm_main.run()
	

if __name__ == "__main__":
	main()
