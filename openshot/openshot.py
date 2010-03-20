#!/usr/bin/python
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

import os, sys
import gtk, locale
from classes import info

# ensure the openshot module directory is in the system path so relative 'import' statements work
base_path = os.path.dirname(os.path.abspath(__file__))
if sys.path.count(base_path) == 0:
	sys.path.insert(0, base_path)
	

# This method starts OpenShot
def main():
	""""Initialise common settings and check the operating environment before starting the application."""

	print "--------------------------------"
	print "   OpenShot (version %s)" % info.SETUP['version']
	print "--------------------------------"

	# only allow 1 instance of OpenShot to run
	from classes import lock
	lock.check_pid(os.path.join(os.path.expanduser("~"), ".openshot"))

	# import the locale, and set the locale. This is used for 
	# locale-aware number to string formatting
	locale.setlocale(locale.LC_ALL, '')

	# init threads - this helps support the 
	# multi-threaded architecture of mlt
	gtk.gdk.threads_init()
	gtk.gdk.threads_enter()

	# Create a default project object
	from classes import project
	current_project = project.project()

	# Create form object & refresh the data
	from windows import MainGTK
	form1 = MainGTK.frmMain(project=current_project, version=info.SETUP['version'])
	form1.refresh()

	# Main loop
	gtk.main()


if __name__ == '__main__':
	main()
