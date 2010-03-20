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
from classes import messagebox, project, effect
from windows.SimpleGladeApp import SimpleGladeApp

# init the foreign language
from language import Language_Init

class frmAddEffect(SimpleGladeApp):

	def __init__(self, path="AddEffect.glade", root="frmAddEffect", domain="OpenShot", parent=None, form=None, project=None, **kwargs):
		SimpleGladeApp.__init__(self, os.path.join(project.GLADE_DIR, path), root, domain, **kwargs)

		# Add language support
		_ = Language_Init.Translator(project).lang.gettext

		self.form = form
		self.project = project
		self.parent = parent
		self.frmAddEffect.show_all()
		
		# Init List of Effects
		effect_list = self.form.effect_list
		
		# Add effects to dropdown
		for my_effect in effect_list:
			# add item
			self.cboEffects.append_text(my_effect.title)
		
		
		
	def on_btnCancel_clicked(self, widget, *args):
		print "on_btnCancel_clicked"
		self.frmAddEffect.destroy()
		
		
	def on_frmAddEffect_destroy(self, widget, *args):
		print "on_frmAddEffect_destroy"
		
	def on_frmAddEffect_close(self, widget, *args):
		print "on_frmAddEffect_close"
		self.frmAddEffect.destroy()
		
	def on_frmAddEffect_destroy(self, widget, *args):
		print "on_frmAddEffect_destroy"
		
	def on_frmAddEffect_response(self, widget, *args):
		print "on_frmAddEffect_response"
		
	def on_btnOk_clicked(self, widget, *args):
		print "on_btnOk_clicked"

		# get Service name
		effect_title = self.cboEffects.get_active_text()
		
		# Add the effect
		if effect_title:
			# get real effect object
			real_effect = self.parent.OSTreeEffects.get_real_effect(title=effect_title)
			
			# add effect
			if real_effect.audio_effect:
				# audio effect
				self.parent.copy_of_clip.Add_Effect("%s:%s" % (real_effect.service, real_effect.audio_effect))
			else:
				# service
				self.parent.copy_of_clip.Add_Effect(real_effect.service)
			
			# update effect tree
			self.parent.update_effects_tree()
		
		# close window
		self.frmAddEffect.destroy()


		
		
			
def main():
	frmImportImageSequence1 = frmImportImageSequence()
	frmImportImageSequence1.run()

if __name__ == "__main__":
	main()
