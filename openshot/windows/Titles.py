#    This file is part of OpenShot Video Editor (http://launchpad.net/openshot/).
#
#    OpenShot Video Editor is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    OpenShot Video Editor is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with OpenShot Video Editor.  If not, see <http://www.gnu.org/licenses/>.

###################################################################################     
#    The titles editor works by creating an svg image file from a 
#     selection of templates (stored in the templates folder).
#    After the user selects a template, a file is created with
#    the chosen name, and the xml of the svg template is parsed into the self.xmldoc
#    object.
#
#    As the user changes various attributes (background colour, font etc),
#    the self.xmldoc object is parsed for matching elements and updated with
#    the new attribute values and the file written to disk.
#
####################################################################################

import os, sys
import fnmatch
import gtk, gtk.glade
from xml.dom import minidom
from classes import files, messagebox, project, profiles
from windows.SimpleGladeApp import SimpleGladeApp
from windows import fontselector



# init the foriegn language
import language.Language_Init as Language_Init


class frmNewTitle(SimpleGladeApp):

	def __init__(self, path="titles.glade", root="frmTitles", domain="OpenShot", form=None, project=None, file=None, **kwargs):
		SimpleGladeApp.__init__(self, os.path.join(project.GLADE_DIR, path), root, domain, **kwargs)

		# Add language support
		_ = Language_Init.Translator(project).lang.gettext

		self.project = project
		self.form = form
		self.file = file

		#find path where openshot is running
		self.path = self.project.BASE_DIR

		self.cmbTemplate.set_sensitive(True)

		self.xmldoc = ""

		self.bg_color_code = ""
		self.font_color_code = "#ffffff"

		self.bg_style_string = ""
		self.title_style_string = ""
		self.subtitle_style_string = ""

		self.font_weight = 'normal'
		self.font_style = 'normal'

		self.new_title_text = ""
		self.sub_title_text = ""
		self.subTitle = False
		
		self.display_name = ""
		self.font_family = "Bitstream Vera Sans"

		# get the aspect ratio of the current project
		p = profiles.mlt_profiles(self.project).get_profile(self.project.project_type)
		
		# determine which ratio folder to get titles from
		self.ratio_folder = ""
		if p.display_aspect_num() == 4 and p.display_aspect_den() == 3:
			self.ratio_folder = "4_3"
		else:
			self.ratio_folder = "16_9"

		#load the template files
		self.template_dir = os.path.join(self.path, "openshot", "titles", self.ratio_folder)
		for file in sorted(os.listdir(self.template_dir)):
			#pretty up the filename for display purposes
			if fnmatch.fnmatch(file, '*.svg'):
				(fileName, fileExtension)=os.path.splitext(file)
			self.cmbTemplate.append_text(fileName.replace("_"," "))

		#add the changed event once the combo has been populated
		self.cmbTemplate.connect("changed", self.on_cmbTemplate_changed)

		if not self.file:
			self.cmbTemplate.grab_focus()
			# init dropdown
			self.set_template_dropdown()
		else:
			self.filename = self.file
			self.load_svg_template(self.file)
			#set edit button states
			self.btnEditText.set_sensitive(True)
			self.btnFont.set_sensitive(True)
			self.btnFontColor.set_sensitive(True)
			self.btnBackgroundColor.set_sensitive(True)
			self.btnAdvanced.set_sensitive(True)
			self.writeToFile(self.xmldoc)
			#show the text editor
			#if self.noTitles == False:
			#	self.on_btnEditText_clicked(widget)
			#preview the file
			self.set_img_pixbuf(self.filename)
			
			self.on_btnEditText_clicked(None)
			
			#turn off the create button once we have created the new file
			self.btnCreate.set_sensitive(False)
			self.cmbTemplate.set_sensitive(False)
			
			if self.noTitles == True:
				self.btnEditText.set_sensitive(False)
				self.btnFont.set_sensitive(False)
				self.btnFontColor.set_sensitive(False)
		
		
	def set_template_dropdown(self):
		# get the model and iterator of the project type dropdown box
		model = self.cmbTemplate.get_model()
		iter = model.get_iter_first()

		# set the item as active
		self.cmbTemplate.set_active_iter(iter)
		self.on_cmbTemplate_changed(self.cmbTemplate)
		


	def on_btnCreate_clicked(self,widget):
		#prompt the user for a file name
		self.filename = self.setTitleName()
		if self.filename == "":
			messagebox.show(_("OpenShot Error"), _("The Title name cannot be blank, the title file has not been created."))
			return
			
		#load the template doc to read xml
		self.load_svg_template(self.template_name)
		#set the new filename
		(fileBaseName, fileExtension)=os.path.splitext(self.template_name)
		self.filename = self.filename + fileExtension
		#write the new file
		self.writeToFile(self.xmldoc)
		#show the text editor
		if self.noTitles == False:
			if not self.on_btnEditText_clicked(widget): return
		#set edit button states
		self.btnEditText.set_sensitive(True)
		self.btnFont.set_sensitive(True)
		self.btnFontColor.set_sensitive(True)
		self.btnBackgroundColor.set_sensitive(True)
		self.btnAdvanced.set_sensitive(True)
		#preview the file
		self.set_img_pixbuf(self.filename)
		
		#turn off the create button once we have created the new file
		self.btnCreate.set_sensitive(False)
		self.cmbTemplate.set_sensitive(False)
		
		if self.noTitles == True:
			self.btnEditText.set_sensitive(False)
			self.btnFont.set_sensitive(False)
			self.btnFontColor.set_sensitive(False)

	def on_cmbTemplate_changed(self, widget):

		folder = os.path.join(self.path,self.template_dir)
		#reconstruct the filename from the modified display name 
		filename = self.cmbTemplate.get_active_text()
		self.template_name = filename.replace(" ", "_") + ".svg"
		self.set_img_pixbuf(os.path.join(folder,self.template_name))
		self.btnCreate.set_sensitive(True)

	def setTitleName(self):  
		#base this on a message dialog  
		dialog = gtk.MessageDialog(  
			None,  
			gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,  
			gtk.MESSAGE_QUESTION,  
			gtk.BUTTONS_OK,  
			None)  
		dialog.set_markup(_('Please enter a name for the new Title file:'))  
		#create the text input field  
		entry = gtk.Entry()  
		entry.set_text(_("New Title"))
		#allow the user to press enter as well as the OK button
		entry.connect("activate", self.ShowInputDialog, dialog, gtk.RESPONSE_OK)  
		hbox = gtk.HBox()  
		hbox.pack_start(gtk.Label("Name:"), False, 5, 5)  
		hbox.pack_end(entry)  
		#add it and show it  
		dialog.vbox.pack_end(hbox, True, True, 0)  
		dialog.show_all()  
		#show the dialog  
		if dialog.run() == gtk.RESPONSE_OK:
			text = entry.get_text()
		else: 
			text = ''
		dialog.destroy()
		return text

	def ShowInputDialog(self,entry, dialog, response):  
		dialog.response(response)    

	def load_svg_template(self,filename):
		self.svgname = os.path.join(self.template_dir,filename)
		#parse the svg object        
		self.xmldoc = minidom.parse(self.svgname)
		#get the text elements
		self.tspan_node = self.xmldoc.getElementsByTagName('tspan')
		self.text_fields = len(self.tspan_node)

		#if more than 1 text field there is a sub-title field
		if self.text_fields > 1:
			self.subTitle = True
		else:
			self.subTitle = False
			
		if self.text_fields == 0:
			self.noTitles = True
		else:
			self.noTitles = False
		self.text_node = self.xmldoc.getElementsByTagName('text')
		#get the rect element
		self.rect_node = self.xmldoc.getElementsByTagName('rect')


	def set_img_pixbuf(self, filename):
		'''displays the svg in the preview window'''
		pixbuf = gtk.gdk.pixbuf_new_from_file(filename)
		
		# resize based on aspect ratio
		if self.ratio_folder == "4_3":
			# 4_3
			pixbuf = pixbuf.scale_simple(504,378,gtk.gdk.INTERP_BILINEAR)
		else:
			# 16_9
			pixbuf = pixbuf.scale_simple(504,284,gtk.gdk.INTERP_BILINEAR)
		
		# set image
		image  = gtk.Image()
		self.image1.set_from_pixbuf(pixbuf)

	def on_btnCancel_clicked(self, widget):
		self.frmTitles.destroy()

	def on_btnAdvanced_clicked(self, widget):
		#use an external editor to edit the image
		try:
			prog = "inkscape"
			#check if inkscape is installed
			if os.system('which ' + prog + ' 2>/dev/null') == 0:
				# launch Inkscape
				os.system("%s '%s'" % (prog, self.filename))
			else:
				messagebox.show(_("OpenShot Error"), _("Please install %s to use this function." % (prog.capitalize())))
			
		except:
			messagebox.show(_("OpenShot Error"), _("There was an error opening '%s', is it installed?" % (prog)))


	def on_btnApply_clicked(self, widget):
		
		#import the file to the project.
		self.project.project_folder.AddFile(self.filename)
		self.project.thumbnailer.get_thumb_at_frame(self.filename)
		self.frmTitles.destroy()
		# refresh the main form
		self.form.refresh()

	def find_in_list(self, l, value):
		'''when passed a partial value, function will return the list index'''
		for item in l:
			if item.startswith(value):
				return l.index(item)


	def set_bg_style(self, color):
		'''sets the background color'''
		#
		#There must be a better way of doing this...
		#
		if self.rect_node:
			#split the node so we can access each part
			s = self.rect_node[0].attributes["style"].value
			ar = s.split(";")
			fill = self.find_in_list(ar, "fill:")
			if fill:
				ar[fill] = "fill:" + color
			else:
				ar.append("fill:" + color)
			
			opacity = self.find_in_list(ar, "opacity:")  
			if opacity:
				ar[opacity] = "opacity:" + str(self.bg_color_alpha)
			else:
				ar.append("opacity:" + str(self.bg_color_alpha))
			
			#rejoin the modifed parts
			t = ";"
			self.bg_style_string = t.join(ar)
			#set the node in the xml doc
			self.rect_node[0].setAttribute("style", self.bg_style_string)
			#write the file and preview the image
			self.writeToFile(self.xmldoc)
			self.set_img_pixbuf(self.filename)



	def set_font_style(self):	
		'''sets the font properties'''
		
		# Loop through each TEXT element
		for text_child in self.text_node:
		
			#set the style elements for the main text node
			s = text_child.attributes["style"].value
			#split the text node so we can access each part
			ar = s.split(";")
			#we need to find each element that we are changing, shouldn't assume
			#they are in the same position in any given template.
			fs = self.find_in_list(ar, "font-style:")
			fw = self.find_in_list(ar, "font-weight:")
			ff = self.find_in_list(ar, "font-family:")
			ar[fs] = "font-style:" + self.font_style
			ar[fw] = "font-weight:" + self.font_weight
			ar[ff] = "font-family:" + self.font_family
			#rejoin the modified parts
			t = ";"
			self.title_style_string = t.join(ar)
			
			#set the text node
			text_child.setAttribute("style", self.title_style_string)
			
			
		# Loop through each TSPAN
		for tspan_child in self.tspan_node:
			
			#set the style elements for the main text node
			s = tspan_child.attributes["style"].value
			#split the text node so we can access each part
			ar = s.split(";")
			#we need to find each element that we are changing, shouldn't assume
			#they are in the same position in any given template.
			fs = self.find_in_list(ar, "font-style:")
			fw = self.find_in_list(ar, "font-weight:")
			ff = self.find_in_list(ar, "font-family:")
			ar[fs] = "font-style:" + self.font_style
			ar[fw] = "font-weight:" + self.font_weight
			ar[ff] = "font-family:" + self.font_family
			#rejoin the modified parts
			t = ";"
			self.title_style_string = t.join(ar)
			
			#set the text node
			tspan_child.setAttribute("style", self.title_style_string)

				
		#write the file and preview the image
		self.writeToFile(self.xmldoc)
		self.set_img_pixbuf(self.filename)

	def set_font_color(self):
		self.set_font_color_elements()


	def set_font_color_elements(self):
		
		# Loop through each TEXT element
		for text_child in self.text_node:
			
			# SET TEXT PROPERTIES
			s = text_child.attributes["style"].value
			#split the text node so we can access each part
			ar = s.split(";")
			fill = self.find_in_list(ar, "fill:")
			if fill:
				ar[fill] = "fill:" + self.font_color_code
			else:
				ar.append("fill:" + self.font_color_code)
			
			opacity = self.find_in_list(ar, "opacity:")  
			if opacity:
				ar[opacity] = "opacity:" + str(self.font_color_alpha)
			else:
				ar.append("opacity:" + str(self.font_color_alpha))
			
			t = ";"
			text_child.setAttribute("style", t.join(ar))


			# Loop through each TSPAN
			for tspan_child in self.tspan_node:
				
				# SET TSPAN PROPERTIES
				s = tspan_child.attributes["style"].value
				#split the text node so we can access each part
				ar = s.split(";")
				fill = self.find_in_list(ar, "fill:")
				if fill:   
					ar[fill] = "fill:" + self.font_color_code
				else:
					ar.append("fill:" + self.font_color_code)
				t = ";"
				tspan_child.setAttribute("style", t.join(ar))


		#write the file and preview the image
		self.writeToFile(self.xmldoc)
		self.set_img_pixbuf(self.filename)

	def set_title_text(self):
		'''sets the title and subtitle text'''    
		#write the file and preview the image 
		self.writeToFile(self.xmldoc)
		self.set_img_pixbuf(self.filename)


	def writeToFile(self, xmldoc):
		'''writes a new svg file containing the user edited data'''
		project_path = os.path.join(self.project.folder, "thumbnail") 
		
		if not self.filename.endswith("svg"):
			self.filename = self.filename + ".svg"
		try:
			if self.filename.startswith(project_path) == False:
				file = open(os.path.join(project_path,self.filename), "wb") #wb needed for windows support
				self.filename = os.path.join(project_path, self.filename)
			else:
				file = open(self.filename, "wb") #wb needed for windows support
			file.write(xmldoc.toxml())
			file.close()
			#Now the file is ready to import into the project.
			self.btnApply.set_sensitive(True)
		except IOError, inst:
			messagebox.show(_("OpenShot Error"), _("Unexpected Error '%s' while writing to '%s'." % (inst, self.filename)))


	def on_btnEditText_clicked(self, widget):
		#just show the text editor window.        
		frm = frmEditText(self, number_of_text_boxes=self.text_fields, tspans=self.tspan_node, project=self.project)
		frm.frmEditText.run()
		return frm.accepted


	def html_color(self, color):
		'''converts the gtk color into html color code format'''
		return '#%02x%02x%02x' % (color.red/256, color.green/256, color.blue/256)


	def on_btnBackgroundColor_color_set(self, widget):
		self.bg_color_code = self.btnBackgroundColor.get_color()
		color_name = self.html_color(self.bg_color_code)
		
		# get background alpha
		raw_alpha = float(self.btnBackgroundColor.get_alpha())
		self.bg_color_alpha = raw_alpha / 65535.0
		
		#set the style element
		self.set_bg_style(color_name)


	def on_btnFontColor_color_set(self, widget):
		# get font color
		self.font_color_code = self.btnFontColor.get_color()
		self.font_color_code = self.html_color(self.font_color_code)

		# get font alpha
		raw_alpha = float(self.btnFontColor.get_alpha())
		self.font_color_alpha = raw_alpha / 65535.0
		
		#set the style element
		self.set_font_color()

	
	def on_btnFont_clicked(self, widget):
		frm = fontselector.frmFontProperties(self, project=self.project)


class frmEditText(SimpleGladeApp):

	def __init__(self, instance, path="titles.glade", root="frmEditText", domain="OpenShot", number_of_text_boxes=0, tspans=None, project=None, **kwargs):
		SimpleGladeApp.__init__(self, os.path.join(project.GLADE_DIR, path), root, domain, **kwargs)

		# Add language support
		_ = Language_Init.Translator(project).lang.gettext
		
		self.frmTitles = instance
		self.tspans = tspans
		self.number_of_text_boxes = number_of_text_boxes
		self.accepted = False

		for i in range(0, self.number_of_text_boxes):
			# get text in SVG
			SVG_Text = ""
			if len(tspans[i].childNodes) > 0:
				SVG_Text = tspans[i].childNodes[0].data
				
			
			# create textbox & add to window
			tbox = gtk.Entry(max=0)
			tbox.set_text(SVG_Text)
			self.vbox3.pack_start(tbox, expand=True, fill=False)

		self.frmEditText.show_all()

	def on_btnApply_clicked(self, widget):
		
		for i in range(0, self.number_of_text_boxes):
			# get textbox
			tbox = self.vbox3.get_children()[i]
			tbox_text = tbox.get_text()

			# update the SVG file
			new_text_node = self.frmTitles.xmldoc.createTextNode(tbox_text)
			
			# replace textnode (if any)
			if len(self.tspans[i].childNodes) > 0:
				old_text_node = self.tspans[i].childNodes[0]
				self.tspans[i].removeChild(old_text_node)
			
			# add new text node
			self.tspans[i].appendChild(new_text_node)

		self.frmEditText.destroy()
		self.frmTitles.set_title_text()
		self.accepted = True


	def on_btnCancel_clicked(self, widget):
		self.frmEditText.destroy()



def main():
	frm_titles = frmNewTitle()
	frm_titles.run()

if __name__ == "__main__":
	main()
