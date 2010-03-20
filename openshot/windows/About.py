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

import os, gtk
import gtk, gtk.glade
from classes.project import project
from classes import messagebox, info
from windows.SimpleGladeApp import SimpleGladeApp

# init the foreign language
from language import Language_Init


class frmAbout(SimpleGladeApp):

	def __init__(self, path="About.glade", root="aboutdialog1", domain="OpenShot", version="0.0.0", project=None, **kwargs):
		SimpleGladeApp.__init__(self,  os.path.join(project.GLADE_DIR, path), root, domain, **kwargs)

		# Add language support
		_ = Language_Init.Translator(project).lang.gettext
		
		# set version from constructor
		self.aboutdialog1.set_version(version)
		
		# init authors
		authors = []
		for person in info.CREDITS['code']:
			name = person['name']
			email = person['email']
			authors.append("%s <%s>" % (name, email))
		self.aboutdialog1.set_authors(authors)
		
		# init documenters
		authors = []
		for person in info.CREDITS['documentation']:
			name = person['name']
			email = person['email']
			authors.append("%s <%s>" % (name, email))
		self.aboutdialog1.set_documenters(authors)
		
		# init translators
		self.aboutdialog1.set_translator_credits("Translation credits are located on LaunchPad:\nhttps://translations.launchpad.net/openshot")



	def new(self):
		print "A new %s has been created" % self.__class__.__name__


	def on_aboutdialog1_close(self, widget, *args):
		print "on_aboutdialog1_close called with self.%s" % widget.get_name()

		# close the window
		self.frmAbout.destroy()

	def on_aboutdialog1_response(self, widget, *args):
		print "on_aboutdialog1_close called with self.%s" % widget.get_name()

		# close the window
		self.aboutdialog1.destroy()

def main():
	aboutdialog1 = frmAbout()
	aboutdialog1.run()

if __name__ == "__main__":
	main()
