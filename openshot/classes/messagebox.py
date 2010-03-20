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

import gtk, os, sys
from xdg.IconTheme import *

# init the foreign language
from language import Language_Init

def get_response(*args):
	
	# hide message dialog
	args[0].destroy()

	if args[1] == gtk.RESPONSE_YES:
		# call callback function (if any)
		if args[2]:
			# call callback
			args[2]()
	else:
		# call callback function (if any)
		if args[3]:
			# call callback
			args[3]()
		

# show an error message (i.e. gtkDialog)
def show(title, error_message, buttons=gtk.BUTTONS_OK, yes_callback_function=None, no_callback_function=None):

	# create an error message dialog
	dialog = gtk.MessageDialog(
		parent		 = None,
		flags		  = gtk.DIALOG_MODAL,
		type		   = gtk.MESSAGE_INFO,
		buttons		= buttons,
		message_format = error_message)
	dialog.set_title(title)
	
	if getIconPath("openshot"):
		dialog.set_icon_from_file(getIconPath("openshot"))
		
	dialog.connect('response', get_response, yes_callback_function, no_callback_function)
	dialog.show()




