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
#
#
#	   av_formats.py copyright (C) 2010 Andy Finch
#
#	   Can be used to determine which formats/codecs are installed	   


import subprocess
from classes import messagebox

# init the foreign language
from language import Language_Init


class formats:
	
	def __init__(self, melt_command="melt"):
		# init melt command
		self.melt_command = melt_command
		
	def get_vcodecs(self, format=None):
		#melt noise -consumer avformat vcodec=list
		command = [self.melt_command, "noise", "-consumer", "avformat", "vcodec=list"]
		output = ''
		
		vcodecs_raw=[]
		
		try:
			process = subprocess.Popen(args=command,stdout=subprocess.PIPE,
			stdin=subprocess.PIPE,stderr=subprocess.STDOUT)
			output = str(process.stdout.read(20000))	   
		except:
			return vcodecs_raw
			
		output_lines=output.split('\n')
		
		for line in output_lines:
			if " - " in line and "..." not in line and len(line.strip()) > 0:
				vcodecs_raw.append(line.lstrip('  - '))
		
		# sort list
		vcodecs_raw.sort()
		
		return vcodecs_raw
	
	
	def get_acodecs(self, format=None):
	
		#this is the equivalant of running this command in the terminal:
		#melt noise -consumer avformat acodec=list
		command = [self.melt_command, "noise", "-consumer", "avformat", "acodec=list"]
		output = ''
		
		acodecs_raw=[]
		
		try:
			process = subprocess.Popen(args=command,stdout=subprocess.PIPE,
			stdin=subprocess.PIPE,stderr=subprocess.STDOUT)
			output = str(process.stdout.read(20000))	   
		except:
			return acodecs_raw
			
		output_lines=output.split('\n')
		
		for line in output_lines:
			if " - " in line and "..." not in line and len(line.strip()) > 0:
				acodecs_raw.append(line.lstrip('  - '))
			
		# sort list
		acodecs_raw.sort()
	
		return acodecs_raw
	
	
	def get_formats(self, format=None):
	
		#this is the equivalant of running this command inthe terminal:
		#melt noise -consumer avformat f=list
		command = [self.melt_command, "noise", "-consumer", "avformat", "f=list"]
		output = ''
		
		formats_raw=[]
		
		try:
			process = subprocess.Popen(args=command,stdout=subprocess.PIPE,
			stdin=subprocess.PIPE,stderr=subprocess.STDOUT)
			output = str(process.stdout.read(20000))	   
		except:
			pass
			
		output_lines=output.split('\n')
		
		for line in output_lines:
			if " - " in line and "..." not in line and len(line.strip()) > 0:
				formats_raw.append(line.lstrip('  - '))

		# sort list
		formats_raw.sort()
		
		# Alert user that no formats were found (this is bad)
		if len(formats_raw) == 0:
			print _("No formats or codecs were found.  Please check the OpenShot preferences and configure the 'melt' command name.")
			messagebox.show(_("Error!"), _("No formats or codecs were found.  Please check the OpenShot preferences and configure the 'melt' command name."))
		
		return formats_raw