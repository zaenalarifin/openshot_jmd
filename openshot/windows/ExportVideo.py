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

has_py_notify = False

try:
	import pynotify
	has_py_notify = True
except:
	has_py_notify = False
		
import os
import gtk, gtk.glade
import xml.dom.minidom as xml
import locale

from classes import messagebox, profiles, project, video
from windows.SimpleGladeApp import SimpleGladeApp

# init the foreign language
from language import Language_Init


class frmExportVideo(SimpleGladeApp):

	def __init__(self, path="ExportVideo.glade", root="frmExportVideo", domain="OpenShot", form=None, project=None, **kwargs):
		SimpleGladeApp.__init__(self, os.path.join(project.GLADE_DIR, path), root, domain, **kwargs)

		# Add language support
		_ = Language_Init.Translator(project).lang.gettext
		self._ = _

		self.form = form
		self.project = project
		self.frmExportVideo.show_all()
		
		self.invalid_codecs = []
		
		# init the project type properties
		self.init_properties(self.cmbProjectType.get_active_text())
		
		# set the export file name
		self.txtFileName.set_text(self.project.name)

		# set the export folder as the project folder (if any)
		if ".openshot" in self.project.folder:
			# This is the openshot default project (set the folder to 'DESKTOP')
			self.fileExportFolder.set_current_folder(self.project.DESKTOP)
		else:
			# Set project folder
			self.fileExportFolder.set_current_folder(self.project.folder)
		
		# init the list of possible project types / profiles
		self.profile_list = profiles.mlt_profiles(self.project).get_profile_list()
		
		# loop through each profile, and add it to the dropdown
		for file_name, p in self.profile_list:
			# append profile to list
			self.cmbProjectType.append_text(p.description())
			
					
		export_options = [_("Video & Audio"), _("Image Sequence")]
		# loop through export to options
		for option in export_options:
			# append profile to list
			self.cboExportTo.append_text(option)
			
		#populate the format/codec drop downs 
		#formats
		format_model = self.cboVIdeoFormat.get_model()
		format_model.clear()
		
		for format in self.form.vformats:
			self.cboVIdeoFormat.append_text(format)
			
		#video codecs
		vcodecs_model = self.cboVideoCodec.get_model()
		vcodecs_model.clear()
		
		for vcodec in self.form.vcodecs:
			self.cboVideoCodec.append_text(vcodec)
			
		#audio codecs
		acodecs_model = self.cboAudioCodec.get_model()
		acodecs_model.clear()
		
		for acodec in self.form.acodecs:
			self.cboAudioCodec.append_text(acodec)
			
			
		# set the dropdown boxes
		self.set_project_type_dropdown()
		self.set_export_to_dropdown()
		
		#load the simple project type dropdown
		presets = []
		for file in os.listdir(self.project.EXPORT_PRESETS_DIR):
			xmldoc = xml.parse(os.path.join(self.project.EXPORT_PRESETS_DIR,file))
			type = xmldoc.getElementsByTagName("type")
			presets.append(_(type[0].childNodes[0].data))
		#exclude duplicates
		presets = list(set(presets))
		for item in sorted(presets):
			self.cboSimpleProjectType.append_text(item)
		#indicate that exporting cancelled
		self.cancelled = False

		
	def set_project_type_dropdown(self):
		
		# get reference to gettext
		_ = self._
		
		# get the model and iterator of the project type dropdown box
		model = self.cmbProjectType.get_model()
		iter = model.get_iter_first()
		while True:
			# get the value of each item in the dropdown
			value = model.get_value(iter, 0)
			
			# check for the matching project type
			if self.project.project_type == value:			
				
				# set the item as active
				self.cmbProjectType.set_active_iter(iter)
		
			# get the next item in the list
			iter = model.iter_next(iter)
			
			# break loop when no more dropdown items are found
			if iter is None:
				break
			
	def on_expander_activate(self, widget, *args):
		#print "on_expander_activate"
		#self.frmExportVideo.set_size_request(0,0)
		pass
		
			
	def set_selection_dropdown(self):
		
		# get reference to gettext
		_ = self._
		
		# get the model and iterator of the project type dropdown box
		model = self.cboSelection.get_model()
		iter = model.get_iter_first()
		

		# set the item as active
		self.cboSelection.set_active_iter(iter)
		
	def set_export_to_dropdown(self):
		
		# get reference to gettext
		_ = self._
		
		# get the model and iterator of the project type dropdown box
		model = self.cboExportTo.get_model()
		iter = model.get_iter_first()

		# set the item as active
		self.cboExportTo.set_active_iter(iter)
		

	def on_cboSimpleProjectType_changed(self, widget, *args):
		#set the target dropdown based on the selected project type 
		#first clear the combo
		self.cboSimpleTarget.get_model().clear()
		
		# get reference to gettext
		_ = self._
		
		
		#parse the xml files and get targets that match the project type
		selected_project = self.cboSimpleProjectType.get_active_text()
		project_types = []
		for file in os.listdir(self.project.EXPORT_PRESETS_DIR):
			xmldoc = xml.parse(os.path.join(self.project.EXPORT_PRESETS_DIR,file))
			type = xmldoc.getElementsByTagName("type")
			
			if _(type[0].childNodes[0].data) == selected_project:
				titles = xmldoc.getElementsByTagName("title")
				for title in titles:
					project_types.append(_(title.childNodes[0].data))
		
		
		for item in sorted(project_types):
			self.cboSimpleTarget.append_text(item)
		
		if selected_project == _("All Formats"):
			# default to MP4 for this type
			self.set_dropdown_values(_("OGG (theora/vorbis)"), self.cboSimpleTarget)
		else:
			# choose first taret
			self.cboSimpleTarget.set_active(0)
		
		
	def on_cboSimpleTarget_changed(self, widget, *args):
		#set the profiles dropdown based on the selected target
		
		# get reference to gettext
		_ = self._
		
		self.cboSimpleVideoProfile.get_model().clear()
		self.cboSimpleQuality.get_model().clear()
		
		#don't do anything if the combo has been cleared
		if self.cboSimpleTarget.get_active_text():
			selected_target = self.cboSimpleTarget.get_active_text()
			profiles_list = []
			
			#parse the xml to return suggested profiles
			for file in os.listdir(self.project.EXPORT_PRESETS_DIR):
				xmldoc = xml.parse(os.path.join(self.project.EXPORT_PRESETS_DIR,file))
				title = xmldoc.getElementsByTagName("title")
				if _(title[0].childNodes[0].data) == selected_target:
					profiles = xmldoc.getElementsByTagName("projectprofile")
					
					#get the basic profile
					if profiles:
						# if profiles are defined, show them
						for profile in profiles:
							profiles_list.append(_(profile.childNodes[0].data))
					else:
						# show all profiles
						for profile_node in self.profile_list:
							profiles_list.append(_(profile_node[0]))
						
					
					#get the video bit rate(s)
					videobitrate = xmldoc.getElementsByTagName("videobitrate")
					for rate in videobitrate:
						v_l = rate.attributes["low"].value
						v_m = rate.attributes["med"].value
						v_h = rate.attributes["high"].value
						self.vbr = {_("Low"): v_l, _("Med"): v_m, _("High"): v_h}
						
						
					
					#get the audio bit rates
					audiobitrate = xmldoc.getElementsByTagName("audiobitrate")
					for audiorate in audiobitrate:
						a_l = audiorate.attributes["low"].value
						a_m = audiorate.attributes["med"].value
						a_h = audiorate.attributes["high"].value
						self.abr = {_("Low"): a_l, _("Med"): a_m, _("High"): a_h}
					
					#get the remaining values
					vf = xmldoc.getElementsByTagName("videoformat")
					self.videoformat = vf[0].childNodes[0].data
					vc = xmldoc.getElementsByTagName("videocodec")
					self.videocodec = vc[0].childNodes[0].data
					ac = xmldoc.getElementsByTagName("audiocodec")
					self.audiocodec = ac[0].childNodes[0].data
					sr = xmldoc.getElementsByTagName("samplerate")
					self.samplerate = sr[0].childNodes[0].data
					c = xmldoc.getElementsByTagName("audiochannels")
					self.audiochannels = c[0].childNodes[0].data
					
			# init the profiles combo
			for item in sorted(profiles_list):
				self.cboSimpleVideoProfile.append_text(item)
				
			# choose the default project type / profile (if it's listed)
			#self.set_dropdown_values(self.project.project_type, self.cboSimpleVideoProfile)

			#set the quality combo
			#only populate with quality settings that exist
			if v_l or a_l:
				self.cboSimpleQuality.append_text(_("Low"))
			if v_m or a_m:
				self.cboSimpleQuality.append_text(_("Med"))
			if v_h or a_h:
				self.cboSimpleQuality.append_text(_("High"))
			
		
	def on_cboSimpleVideoProfile_changed(self, widget, *args):
		
		# get reference to gettext
		_ = self._
		
		#don't do anything if the combo has been cleared
		if self.cboSimpleVideoProfile.get_active_text():
			profile = str(self.cboSimpleVideoProfile.get_active_text())
			
			#does this profile exist?
			p = profiles.mlt_profiles(self.project).get_profile(profile)
			
			if str(p.description()) != profile:
				messagebox.show(_("Error!"), _("%s is not a valid OpenShot profile. Profile settings will not be applied." % profile))
				
			self.init_properties(profile)
		
			#set the value of the project type dropdown on the advanced tab
			self.set_dropdown_values(profile,self.cmbProjectType)
		
	def on_cboSimpleQuality_changed(self, widget, *args):
		
		# get reference to gettext
		_ = self._
		
		#don't do anything if the combo has been cleared
		if self.cboSimpleQuality.get_active_text():
		
			# reset the invalid codecs list
			self.invalid_codecs = []
			
			# Get the quality
			quality = str(self.cboSimpleQuality.get_active_text())
			
			#set the attributes in the advanced tab
			#video format
			self.set_dropdown_values(self.videoformat, self.cboVIdeoFormat)
			
			#videocodec
			self.set_dropdown_values(self.videocodec, self.cboVideoCodec)
			
			#audiocode
			self.set_dropdown_values(self.audiocodec, self.cboAudioCodec)
			
			#samplerate
			self.set_dropdown_values(self.samplerate, self.cboSampleRate)
			
			#audiochannels
			self.set_dropdown_values(self.audiochannels, self.cboChannels)
			
			#video bit rate
			self.cboBitRate.insert_text(0,self.vbr[quality])
			self.cboBitRate.set_active(0)
			
			#audio bit rate
			self.cboAudioBitRate.insert_text(0,self.abr[quality])
			self.cboAudioBitRate.set_active(0)
			
			#check for any invalid codecs and disable
			#the export button if required.
			if self.invalid_codecs:
				missing_codecs = ""
				for codec in self.invalid_codecs:
					missing_codecs += codec + "\n"
					
				messagebox.show(_("Openshot Error"), _("The following formats/codecs are missing from your system:" + "\n\n" + "%s" % missing_codecs + "\nYou will not be able to use the selected export profile.  You will need to install the missing formats/codecs or choose a different export profile."))
				self.btnExportVideo.set_sensitive(False)
		
			
	def set_dropdown_values(self, value_to_set, combobox):
		
		# get reference to gettext
		_ = self._
		
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
			if iter is None and value_to_set not in self.invalid_codecs:
				self.invalid_codecs.append(value_to_set)
				break

	def init_properties(self, profile):
		
		# get correct gettext method
		_ = self._
		
		# get the mlt profile
		localType = profile 
		p = profiles.mlt_profiles(self.project).get_profile(localType)

		# populate the labels with values
		self.lblHeightValue.set_text(str(p.height()))
		self.lblWidthValue.set_text(str(p.width()))
		self.lblAspectRatioValue.set_text("%s:%s" % (p.display_aspect_num(), p.display_aspect_den()))
		self.lblFrameRateValue.set_text("%.2f" % float(p.fps()))
		self.lblPixelRatioValue.set_text("%s:%s" % (p.sample_aspect_num(), p.sample_aspect_den()))
		
		if p.progressive():
			self.lblProgressiveValue.set_text(_("Yes"))
		else:
			self.lblProgressiveValue.set_text(_("No"))
		
		
		


	def on_frmExportVideo_close(self, widget, *args):
		print "on_frmExportVideo_close"

		
	def on_frmExportVideo_destroy(self, widget, *args):
		print "on_frmExportVideo_destroy"
		self.cancelled = True
		
		# stop the export (if in-progress)
		if self.project.form.MyVideo:
			self.project.form.MyVideo.c.stop()
			
		# mark project as modified
		self.project.set_project_modified(is_modified=False, refresh_xml=True)

		
	def on_cboExportTo_changed(self, widget, *args):
		print "on_cboExportTo_changed"
		
		# get correct gettext method
		_ = self._
		
		# get the "export to" variable
		localcboExportTo = self.cboExportTo.get_active_text()
		localtxtFileName = str.strip(self.txtFileName.get_text())
		localtxtFileName = localtxtFileName.replace("_%d", "")
		
		if localcboExportTo == _("Image Sequence"):
			self.expander3.set_expanded(True)	# image sequence
			self.expander4.set_expanded(False)	# video settings
			self.expander5.set_expanded(False)	# audio settings
			
			# update filename
			self.txtFileName.set_text(localtxtFileName + "_%d") 
			
			
		elif localcboExportTo == _("Video & Audio"):
			self.expander3.set_expanded(False)	# image sequence
			self.expander4.set_expanded(True)	# video settings
			self.expander5.set_expanded(True)	# audio settings
			
			# update filename
			self.txtFileName.set_text(localtxtFileName) 
			
			
		
	def on_cboProjectType_changed(self, widget, *args):
		print "on_cboProjectType_changed"
		
		# init the project type properties
		self.init_properties(self.cmbProjectType.get_active_text())
		
		
		
	def on_btnCancel_clicked(self, widget, *args):
		print "on_btnCancel_clicked"
		self.cancelled=True
		self.frmExportVideo.destroy()
		
	def on_btnExportVideo_clicked(self, widget, *args):
		print "on_btnExportVideo_clicked"
		
		# get correct gettext method
		_ = self._
		
		# Get general settings
		localcboExportTo = self.cboExportTo.get_active_text()
		localfileExportFolder = str.strip(self.fileExportFolder.get_filename())
		localtxtFileName = str.strip(self.txtFileName.get_text())
		
		# get project type
		localcmbProjectType = self.cmbProjectType.get_active_text()
		
		# get Image Sequence settings
		localtxtImageFormat = str.strip(self.txtImageFormat.get_text())
		
		# get video settings
		localtxtVideoFormat = self.cboVIdeoFormat.get_active_text()
		localtxtVideoCodec = self.cboVideoCodec.get_active_text()
		localtxtBitRate = str.strip(self.txtBitRate.get_text())
		BitRateBytes = self.convert_to_bytes(localtxtBitRate)

		# get audio settings
		localtxtAudioCodec = self.cboAudioCodec.get_active_text()
		localtxtSampleRate = str.strip(self.txtSampleRate.get_text())
		localtxtChannels = str.strip(self.txtChannels.get_text())
		localtxtAudioBitRate = str.strip(self.txtAudioBitRate.get_text())
		AudioBitRateBytes = self.convert_to_bytes(localtxtAudioBitRate)
		
		# Validate the the form is valid
		if (len(localtxtFileName) == 0):
			# Show error message
			messagebox.show(_("Validation Error!"), _("Please enter a valid File Name."))

		elif self.notebook1.get_current_page() == 0 and self.cboSimpleProjectType.get_active_iter() == None:
			# Show error message
			messagebox.show(_("Validation Error!"), _("Please select a valid Project Type."))
		
		elif self.notebook1.get_current_page() == 0 and self.cboSimpleTarget.get_active_iter() == None:
			# Show error message
			messagebox.show(_("Validation Error!"), _("Please select a valid Target."))
		
		elif self.notebook1.get_current_page() == 0 and self.cboSimpleVideoProfile.get_active_iter() == None:
			# Show error message
			messagebox.show(_("Validation Error!"), _("Please select a valid Profile."))
			
		elif self.notebook1.get_current_page() == 0 and self.cboSimpleQuality.get_active_iter() == None:
			# Show error message
			messagebox.show(_("Validation Error!"), _("Please select a valid Quality."))
			
		elif (len(localtxtImageFormat) == 0):
			# Show error message
			messagebox.show(_("Validation Error!"), _("Please enter a valid Image Format."))
			
		elif (len(localtxtVideoFormat) == 0):
			# Show error message
			messagebox.show(_("Validation Error!"), _("Please enter a valid Video Format."))
			
		elif (len(localtxtVideoCodec) == 0):
			# Show error message
			messagebox.show(_("Validation Error!"), _("Please enter a valid Video Codec."))
			
		elif (len(BitRateBytes) == 0 or BitRateBytes == "0"):
			# Show error message
			messagebox.show(_("Validation Error!"), _("Please enter a valid Bit Rate."))
			
		elif (len(localtxtAudioCodec) == 0):
			# Show error message
			messagebox.show(_("Validation Error!"), _("Please enter a valid Audio Codec."))
			
		elif (len(localtxtSampleRate) == 0):
			# Show error message
			messagebox.show(_("Validation Error!"), _("Please enter a valid Sample Rate."))
			
		elif (len(localtxtChannels) == 0):
			# Show error message
			messagebox.show(_("Validation Error!"), _("Please enter a valid Audio Channels."))

		elif (len(AudioBitRateBytes) == 0 or AudioBitRateBytes == "0"):
			# Show error message
			messagebox.show(_("Validation Error!"), _("Please enter a valid Audio Bit Rate."))
			
		else:
			# VALID FORM
					
			# update the project's profile
			self.project.project_type = localcmbProjectType

			# Refresh the MLT XML file
			self.project.RefreshXML()
			
			# create dictionary of all options
			self.render_options = {}
			self.render_options["folder"] = localfileExportFolder
			self.render_options["file"] = localtxtFileName
			self.render_options["export_to"] = localcboExportTo
			
			if localcboExportTo == _("Image Sequence"):
				self.render_options["vcodec"] = localtxtImageFormat
				self.render_options["f"] = localtxtImageFormat
				
			elif localcboExportTo == _("Video & Audio"):
				self.render_options["vcodec"] = localtxtVideoCodec
				self.render_options["f"] = localtxtVideoFormat
				
			self.render_options["b"] = BitRateBytes
			self.render_options["acodec"] = localtxtAudioCodec
			self.render_options["ar"] = localtxtSampleRate
			self.render_options["ac"] = localtxtChannels
			self.render_options["ab"] = AudioBitRateBytes

			# get the complete path to the new file
			folder1 = self.render_options["folder"]
			file1 = self.render_options["file"]
			self.export_path = "%s.%s" % (os.path.join(folder1, file1), self.render_options["f"])

			#check for existing filename before export and confirm overwrite
			if os.path.exists(self.export_path):
				messagebox.show(_("Confirm Overwrite"), _("There is already a video file named %s.%s in the selected export folder. Would you like to overwrite it?") % (file1, self.render_options["f"]), gtk.BUTTONS_YES_NO, self.confirm_overwrite_yes)
			else:
				# no existing file, so export now
				self.do_export()
			     	
		
			 
	def do_export(self):
		render_options = self.render_options
		# flag that an export is in-progress
		self.export_in_progress = True
		# set window as MODAL (so they can't mess up the export)
		self.frmExportVideo.set_modal(True)
		
		# re-load the xml
		self.project.form.MyVideo.set_profile(self.project.project_type, load_xml=False)
		self.project.form.MyVideo.set_project(self.project, self.project.form, os.path.join(self.project.USER_DIR, "sequence.mlt"), mode="render", render_options=render_options)
		self.project.form.MyVideo.load_xml()
		

	def confirm_overwrite_yes(self):
		#user agrees to overwrite the file
		self.do_export()
			
	def update_progress(self, new_percentage):
		
		# get correct gettext method
		_ = self._

		# update the percentage complete
		self.progressExportVideo.set_fraction(new_percentage)
		
		# if progress bar is 100%, close window
		if new_percentage == 1 and self.export_in_progress:
			
			# remove the MODAL property from the window (sicne we are done)
			self.frmExportVideo.set_modal(False)
			if not self.cancelled:
				title = _("Export Complete")
				message = _("The video has been successfully exported to\n%s") % self.export_path
				
				# prompt user that export is completed
				if has_py_notify:
					# Use libnotify to show the message (if possible)
					if pynotify.init("OpenShot Video Editor"):
						n = pynotify.Notification(title, message)
						n.show()
				else:
					# use a GTK messagebox
					messagebox.show(title, message)
			
			# flag export as completed
			self.export_in_progress = False
			
			# close the window
			#self.frmExportVideo.destroy()
		

	def convert_to_bytes(self, BitRateString):
		bit_rate_bytes = 0
		
		# split the string into pieces
		s = BitRateString.lower().split(" ")
		measurement = "kb"
		
		try:
			# Get Bit Rate
			if len(s) >= 2:
				raw_number_string = s[0]
				raw_measurement = s[1]

				# convert string number to float (based on locale settings)
				raw_number = locale.atof(raw_number_string)

				if "kb" in raw_measurement:
					measurement = "kb"
					bit_rate_bytes = raw_number * 1000.0
					
				elif "mb" in raw_measurement:
					measurement = "mb"
					bit_rate_bytes = raw_number * 1000.0 * 1000.0
					
		except:
			pass

		# return the bit rate in bytes
		return str(int(bit_rate_bytes))
	
	def on_cboVIdeoFormat_changed(self, widget, *args):
		
		self.btnExportVideo.set_sensitive(True)
		
	
	def on_cboVideoCodec_changed(self, widget, *args):
		
		self.btnExportVideo.set_sensitive(True)
		
	
	def on_cboAudioCodec_changed(self, widget, *args):
		
		self.btnExportVideo.set_sensitive(True)
	
			
def main():
	frmExportVideo1 = frmExportVideo()
	frmExportVideo1.run()

if __name__ == "__main__":
	main()
