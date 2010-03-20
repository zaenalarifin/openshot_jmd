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
import gtk, gobject, pango
from classes import project

# init the foreign language
from language import Language_Init


class OpenShotTree:
	
	def __init__(self, treeview, project):
	
		# Add language support
		self._ = Language_Init.Translator(project).lang.gettext
		_ = self._
	
		# init vars
		self.treeview = treeview
		self.project = project
		
		# create a TreeStore
		self.store = gtk.TreeStore(gtk.gdk.Pixbuf, str, str)
	
		# Set the treeview's data model
		self.treeview.set_model(self.store)
		self.treeviewAddGeneralPixbufColumn(self.treeview, _("Thumb"), 0, resizable=False, reorderable=False, project=self.project)
		self.treeviewAddGeneralTextColumn(self.treeview, _("Name"), 1, resizable=False, reorderable=True, editable=False, visible=True, elipses=False, autosize=True, project=self.project)
		self.treeviewAddGeneralTextColumn(self.treeview, "path", 2, resizable=True, reorderable=True, editable=False, visible=False, project=self.project)

		# ADD DEFAULT TRANSITIONS
		file_path = os.path.join(self.project.TRANSITIONS_DIR, "sand.svg")
		
		# get the pixbuf
		pbThumb = gtk.gdk.pixbuf_new_from_file(file_path)

		# resize thumbnail
		pbThumb = pbThumb.scale_simple(80, 62, gtk.gdk.INTERP_BILINEAR)	
		
		# add transition to tree
		item = self.store.append(None)
		self.store.set_value(item, 0, pbThumb)
		self.store.set_value(item, 1, _("Dissolve"))
		self.store.set_value(item, 2, "")

		# get a list of files in the OpenShot /transitions directory
		file_list = os.listdir(self.project.TRANSITIONS_DIR)

		for fname in sorted(file_list):
			(dirName, file_name) = os.path.split(fname)
			(fileBaseName, fileExtension)=os.path.splitext(file_name)
			
			file_path = os.path.join(self.project.TRANSITIONS_DIR, fname)
			
			# get the pixbuf
			pbThumb = gtk.gdk.pixbuf_new_from_file(file_path)

			# resize thumbnail
			pbThumb = pbThumb.scale_simple(80, 62, gtk.gdk.INTERP_BILINEAR)
			
			# get name of transition
			trans_name = fileBaseName.replace("_", " ").capitalize()

			# add transition to tree
			item = self.store.append(None)
			self.store.set_value(item, 0, pbThumb)
			self.store.set_value(item, 1, _(trans_name))
			self.store.set_value(item, 2, file_path)
			
		
		# connect signals
		self.treeview.connect_after('drag_begin', self.on_treeTransition_drag_begin)
		
	
	def on_treeTransition_drag_begin(self, widget, *args):
		context = args[0]
		
		# update drag type
		self.project.form.drag_type = "transition"
	
		# Get the drag icon
		play_image = gtk.image_new_from_file(os.path.join(self.project.THEMES_DIR, self.project.theme, "icons", "plus.png"))
		pixbuf = play_image.get_pixbuf()
		context.set_icon_pixbuf(pixbuf, 15, 10)
		
	
	def treeviewAddGeneralTextColumn(self, treeview, name, pos = 0, resizable=True, reorderable=False, editable=False, visible=True, elipses=False, autosize=False, project=None):
		'''Add a new text column to the model'''
	
		cell = gtk.CellRendererText()
		cell.set_property('editable', editable)
		if (elipses):
			cell.set_property("ellipsize", pango.ELLIPSIZE_END)
		col = gtk.TreeViewColumn(name, cell, markup = pos)
		if (autosize):
			col.set_sizing(gtk.TREE_VIEW_COLUMN_AUTOSIZE)
			col.set_expand(False)
		col.set_resizable(resizable)
		col.set_reorderable(reorderable)
		col.set_visible(visible)
		treeview.append_column(col)
		treeview.set_headers_clickable(True)
		
		if (editable):
			model = treeview.get_model()
			cell.connect('edited', self.cell_edited,model, project)
		
		if (reorderable):
			col.set_sort_column_id(pos)
	
		return cell, col
	
	def treeviewAddGeneralPixbufColumn(self, treeview, name, pos = 0, resizable=True, reorderable=False, project=None):
		
		'''Add a new gtk.gdk.Pixbuf column to the model'''
		cell = gtk.CellRendererPixbuf()
		col = gtk.TreeViewColumn(name, cell, pixbuf = pos)
		col.set_resizable(resizable)
		col.set_reorderable(reorderable)
		col.set_alignment(0.0)
		treeview.append_column(col)
		treeview.set_headers_clickable(True)
	
		if (reorderable):
			col.set_sort_column_id(pos)
	
		return cell, col
	
	
	def cell_edited(self, cell, row, new_text, model, project=None):
		
		##Fired when the editable label cell is edited
		#get the row that was edited
		iter = model.get_iter_from_string(row)
		column = cell.get_data(_("Label"))
		#set the edit in the model
		model.set(iter,3,new_text)
		#update the file object with the label edit
		filename = model.get_value(iter, 1)
		project.project_folder.UpdateFileLabel(filename, new_text, 0)


