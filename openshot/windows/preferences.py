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
import xml.dom.minidom as xml

from classes import profiles, project, messagebox, tree
from windows.SimpleGladeApp import SimpleGladeApp
from xdg.IconTheme import *

# init the foriegn language
import language.Language_Init as Language_Init

class PreferencesMgr(SimpleGladeApp):
	
	
	def __init__(self, path="Preferences.glade", root="frmPreferences", domain="OpenShot", form=None, project=None, **kwargs):
		SimpleGladeApp.__init__(self, os.path.join(project.GLADE_DIR, path), root, domain, **kwargs)
		
		# Add language support
		_ = Language_Init.Translator(project).lang.gettext
		self._ = _
		
		self.project = project
		self.form = form
		self.settings = Settings(self.project)

		if getIconPath("openshot"):
			self.frmPreferences.set_icon_from_file(getIconPath("openshot"))
		
		view = self.icvCategories
		self.model = gtk.ListStore(str, gtk.gdk.Pixbuf)
		
		#Populate the form with the preference category icons
		#General section
		pixbuf = view.render_icon(gtk.STOCK_PREFERENCES, size=gtk.ICON_SIZE_BUTTON, detail = None)
		self.model.append([_('General'), pixbuf])
		
		#Formats section
		pixbuf = view.render_icon(gtk.STOCK_INFO, size=gtk.ICON_SIZE_BUTTON, detail = None)
		self.model.append([_('AV Formats'), pixbuf])
		
		#Formats section
		pixbuf = view.render_icon(gtk.STOCK_INFO, size=gtk.ICON_SIZE_BUTTON, detail = None)
		self.model.append([_('Profiles'), pixbuf])
		
				
		# Connect the iconview with the model
		view.set_model(self.model)
		# Map model text and pixbuf columns to iconview
		view.set_text_column(0)
		view.set_pixbuf_column(1)
		
		#populate the combo boxes
		# init the list of possible project types / profiles
		self.profile_list = profiles.mlt_profiles(self.project).get_profile_list()
		
		# loop through each profile, and add it to the dropdown
		for file_name, p in self.profile_list:
			# append profile to list
			self.cmbProfiles.append_text(str(file_name))
			
		#populate the themes
		for dir in os.listdir(self.project.THEMES_DIR):
			self.cmbThemes.append_text(dir)
			
		# populate project file type combo
		for file_type in ["binary", "ascii"]:
			self.cmbFileType.append_text(file_type)
			
			
		#populate the codecs & formats
		
		self.VCodecList = gtk.ListStore(str)
		self.tvVCodecs.set_model(self.VCodecList)
		tree.treeviewAddGeneralTextColumn(self.tvVCodecs,_('Video Codecs'),0)
		
		self.ACodecList = gtk.ListStore(str)
		self.tvACodecs.set_model(self.ACodecList)
		tree.treeviewAddGeneralTextColumn(self.tvACodecs,_('Audio Codecs'),0)
		
		self.FormatsList = gtk.ListStore(str)
		self.tvFormats.set_model(self.FormatsList)
		tree.treeviewAddGeneralTextColumn(self.tvFormats,_('Formats'),0)	
		
		self.populate_codecs()
		
			
		#populate form objects
		self.txtImageLength.set_text(self.settings.general["imported_image_length"])
		self.txtHistoryStackSize.set_text(self.settings.general["max_history_size"])
		self.txtMeltCommandName.set_text(self.settings.general["melt_command"])		
		theme_name = self.settings.general["default_theme"]
		file_type = self.settings.general["project_file_type"]
		self.set_dropdown_values(theme_name, self.cmbThemes)
		self.set_dropdown_values(self.settings.general["default_profile"], self.cmbProfiles)
		self.set_dropdown_values(file_type, self.cmbFileType)
		#set the example theme icon
		self.load_theme_image(theme_name)
		
		#show the form
		self.frmPreferences.show_all()
		
	def populate_codecs(self):
		
		#populate the codecs
		
		#video codecs		
		for codec in self.form.vcodecs:
			self.VCodecList.append([codec])
		
		#audio codecs
		for acodec in self.form.acodecs:
			self.ACodecList.append([acodec])
		
		#formats
		for format in self.form.vformats:
			self.FormatsList.append([format])
			
	
	def on_btnReload_clicked(self, widget, *args):
		
		#clear the codecs from the form object
		#and repopulate the listviews
		
		self.VCodecList.clear()
		self.ACodecList.clear()
		self.FormatsList.clear()
		
		self.form.vcodecs[:] = []
		self.form.acodecs[:] = []
		self.form.vformats[:] = []
		
		melt_command = self.settings.general["melt_command"]
		self.form.get_avformats(melt_command)
		
		self.populate_codecs()
		
		
	def on_btnCancel_clicked(self, widget, *args):
		self.frmPreferences.destroy()
		
		
	def on_btnApply_clicked(self, widget, *args):
		#write the values from the form to the dictionary objects
		self.settings.general["imported_image_length"] = self.txtImageLength.get_text()
		self.settings.general["default_theme"] = self.cmbThemes.get_active_text()
		self.settings.general["default_profile"] = self.cmbProfiles.get_active_text()
		self.settings.general["project_file_type"] = self.cmbFileType.get_active_text()
		self.settings.general["max_history_size"] = self.txtHistoryStackSize.get_text()
		self.settings.general["melt_command"] = self.txtMeltCommandName.get_text()

		# save settings
		self.settings.save_settings_to_xml()
		
		# update theme on main form
		self.form.project.theme = self.settings.general["default_theme"]
		self.form.update_icon_theme()
		self.form.refresh()
		
		# close the window
		self.frmPreferences.destroy()
		
		
	def on_cmbThemes_changed(self, widget, *args):
		#reload the theme example image
		theme_name = self.cmbThemes.get_active_text()
		self.load_theme_image(theme_name)
		
		
	def load_theme_image(self, theme_name):
		#loads the preview image for the selected theme.
		themes_folder = os.path.join(self.project.THEMES_DIR, theme_name)
		self.imgTheme.set_from_file(os.path.join(themes_folder, "play.png"))
		
		
	def on_icvCategories_selection_changed(self, icon_view, model=None):
		
		_ = self._
		
		#sets the notebook page to view depending
		#on which category icon is selected.
		selected = icon_view.get_selected_items()
		if len(selected) == 0: return
		i = selected[0][0]
		category = self.model[i][0]
		if category == _("General"):
			self.nbPrefPages.set_current_page(0)
		#When adding extra categories,
		#include them in this 'If' statement
		elif category == _("AV Formats"):
			self.nbPrefPages.set_current_page(1)
		elif category == _("Profiles"):
			self.nbPrefPages.set_current_page(2)
			
	def on_btnManageProfiles_clicked(self, widget, *args):
		print "on_btnManageProfiles_clicked"
		from windows import Profiles
		Profiles.frmProfilesManager(form=self.form, project=self.project)
			
	
	def set_dropdown_values(self, value_to_set, combobox):
		
		model = combobox.get_model()
		iter = model.get_iter_first()
		while True:
			# get the value of each item in the dropdown
			value = model.get_value(iter, 0)
			
			# check for the matching value
			if value_to_set == value:			
				
				# set the item as active
				combobox.set_active_iter(iter)
				break
		
			# get the next item in the list
			iter = model.iter_next(iter)
			
			# break loop when no more dropdown items are found
			if iter is None:
				break
			
	
				

class Settings:
	#set some initial values.
	#The first time Openshot is run, the settings file won't exist,
	#so use these default values.
	#When the settings are loaded from the config file, these default
	#values will be overwritten with the file values.
	general = {
		"imported_image_length" : "7",
		"default_theme" : "blue_glass",
		"default_profile" : "DV NTSC",
		"project_file_type" : "binary",
		"max_history_size" : "20",
		"melt_command" : "melt",
		}
	
	app_state = {
		"window_height" : "710",
		"window_width" : "900",
		"window_maximized" : "False",
		"import_folder" : "None",
		"toolbar_visible" : "True",
		"vpane_position" : "370",
		"hpane_position" : "450",
		"clip_property_window_width" : "635",
		"clip_property_window_height" : "345",
		"clip_property_window_maximized" : "False",
		"clip_property_hpane_position" : "260",
		
		}
	
	sections = {
		"general" : general,
		"app_state" : app_state
		
		}
	
	def __init__(self, project):
		"""Constructor"""
		
		# Add language support
		translator = Language_Init.Translator(project)
		_ = translator.lang.gettext
		
		self.project = project
	
	def load_settings_from_xml(self):
		settings_path = os.path.join(self.project.USER_DIR, "config.xml")
		
		#Load the settings from the config file, if it exists
		if os.path.exists(settings_path):
			
			try:
				xmldoc = xml.parse(settings_path)
			except xml.xml.parsers.expat.ExpatError:
				# Invalid or empty config file
				self.save_settings_to_xml()
				return
			#loop through each settings section and load the values
			#into the relevant dictionary
			for section, section_dict in self.sections.iteritems():
				for key, value in section_dict.iteritems():
					try:
						element = xmldoc.getElementsByTagName(key)
						section_dict[key] = element[0].childNodes[0].data
						
						# be sure theme exists
						if key == "default_theme":
							if os.path.exists(os.path.join(self.project.THEMES_DIR, section_dict[key])) == False:
								# DOES NOT EXIST, change to default
								section_dict[key] = "blue_glass"
						
					except IndexError:
						#the list index will go out of range if there is
						#an extra item in the dictionary which is
						#not in the config file.
						pass
		
		else:
			# no config file found, create one
			self.save_settings_to_xml()
			
	def save_settings_to_xml(self):
		settings_path = os.path.join(self.project.USER_DIR, "config.xml")
		
		#update each xml element with the current dictionary values
		if os.path.exists(settings_path):
			try:
				xmldoc = xml.parse(settings_path)
			except xml.xml.parsers.expat.ExpatError:
				# Invalid or empty config file, create new blank dom
				messagebox.show(_("OpenShot Warning"), _("Invalid or empty preferences file found, loaded default values"))
				xmldoc = xml.Document()
				root_node = xmldoc.createElement("settings")
				xmldoc.appendChild(root_node)
				
				# create a node for each section
				for section, section_dict in self.sections.iteritems():
					section_node = xmldoc.createElement(section)
					root_node.appendChild(section_node)
		else:
			# missing config file, create new blank dom
			xmldoc = xml.Document()
			root_node = xmldoc.createElement("settings")
			xmldoc.appendChild(root_node)
			
			# create a node for each section
			for section, section_dict in self.sections.iteritems():
				section_node = xmldoc.createElement(section)
				root_node.appendChild(section_node)
				
		
		for section, section_dict in self.sections.iteritems():
			for key, value in section_dict.iteritems():
				try:
					element = xmldoc.getElementsByTagName(key)
					if element:
						element[0].childNodes[0].data = section_dict[key]
					else:
						#there is no matching element in the xml, 
						#we need to add one
						new_element = xmldoc.createElement(key)
						parent = xmldoc.getElementsByTagName(section)
						parent[0].appendChild(new_element)
						txt = xmldoc.createTextNode(str(value))
						new_element.appendChild(txt)
						
				except IndexError:
					pass
	
		# save settings
		self.write_to_settings_file(xmldoc)
			
			
			
			
					
	def write_to_settings_file(self, xmldoc):
		#write the updated xml document to the config file
		filename = os.path.join(self.project.USER_DIR, "config.xml")
		
		try:
			file = open(filename, "wb") 
			file.write(xmldoc.toxml("UTF-8"))
			#xmldoc.writexml(file, indent='', addindent='    ', newl='', encoding='UTF-8')
			file.close()
		except IOError, inst:
			messagebox.show(_("OpenShot Error"), _("Unexpected Error '%s' while writing to '%s'." % (inst, filename)))
		
		
def main():
	frm_prefs = PreferencesMgr()
	frm_titles.run()

if __name__ == "__main__":
	main()