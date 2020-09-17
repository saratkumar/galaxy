import configparser
import ffmpeg
import sys
import requests
import logging
import time
import json
import tempfile
import os
import datetime
from datetime import timedelta
from datetime import datetime
import math
import uuid
import subprocess
import shutil
from PIL import Image, ImageDraw, ImageFont

class ContactSheet:
	def __init__(self, input_file, output_file, ncols = 4, photow = 300, margin = 10, padding = 3):
		self.temporary_directory = tempfile.TemporaryDirectory()
		self.input_file = input_file
		self.output_file = output_file
		self.video_length = self.get_length(input_file)
		self.ncols = ncols # number of columns
		self.photow = photow # width of each thumbnail, in px
		self.marl, self.mart, self.marr, self.marb = margin, margin, margin, margin # margin around edge of contact sheet, in px
		self.padding = padding # space between each image, in px
		
	def create_time(self, frame_seconds):
		valid_input = self.validate_time(frame_seconds, self.video_length)
		if valid_input == False:
			exit(1)

		times, labels = self.getTimesInterval(self.video_length, frame_seconds)
		filenames = self.get_thumbs(self.input_file, times, self.temporary_directory.name)
		print(filenames)
		self.create_contact_sheet(filenames, labels)

	def create_quantity(self, frame_quantity):
		valid_input = self.validate_quantity(frame_quantity)
		if valid_input == False:
			exit(1)

		times, labels = self.getTimesQuantity(self.video_length, frame_quantity)
		filenames = self.get_thumbs(self.input_file, times, self.temporary_directory.name)
		print(filenames)
		self.create_contact_sheet(filenames, labels)

	def create_facial(self, amp_facial_recognition):
		valid_input = self.validate_facial(amp_facial_recognition)
		if valid_input == False:
			exit(1)
		exit(1)

	def create_shots(self, amp_shots):
		valid_input = self.validate_shots(amp_shots)
		if valid_input == False:
			exit(1)

		times, labels = self.getTimesShotDetection(amp_shots)
		# Get images
		filenames = self.get_thumbs(self.input_file, times, self.temporary_directory.name)
		print(filenames)
		self.create_contact_sheet(filenames, labels)

	def create_contact_sheet(self, filenames, labels):
		nrows = math.ceil(len(filenames)/self.ncols) # number of rows of images
		sample_image = Image.open(filenames[0]) # A sample image to get aspect ratio from
		width, height = sample_image.size
		ratio = height/width
		photoh = round(self.photow * ratio) # calculated height based on aspect ratio & set width

		filename = self.input_file.split('/')[-1] # Get filename for labelling purposes

		image = self.contact_sheet_assembly(filenames, labels, "file: %s\nLabel: %s" % (filename, 'AMP Contact Sheet'), nrows, photoh)

		temp_file = self.output_file + ".png"
		image.save(temp_file)
		shutil.copyfile(temp_file, self.output_file)
		if os.path.exists(temp_file):
			os.remove(temp_file)


	def contact_sheet_assembly(self, fnames, ftimes, headerInfo, nrows, photoh):
		"""\
		Make a contact sheet from a group of filenames:

		fnames       A list of names of the image files
		
		ncols        Number of columns in the contact sheet
		nrows        Number of rows in the contact sheet
		photow       The width of the photo thumbs in pixels
		photoh       The height of the photo thumbs in pixels

		marl         The left margin in pixels
		mart         The top margin in pixels
		marr         The right margin in pixels
		marl         The left margin in pixels

		padding      The padding between images in pixels

		returns a PIL image object.
		"""


		# Read in all images and resize appropriately
		imgs = [Image.open(fn).resize((self.photow, photoh)) for fn in fnames]

		for i, img in enumerate(imgs):
			d = ImageDraw.Draw(img)
			d.text((10,10), str(ftimes[i]), fill=(255,255,0))

			# Calculate the size of the output image, based on the
			#  photo thumb sizes, margins, and padding
			mart = self.mart+100
			marw = self.marl+self.marr
			marh = mart+self.marb

			padw = (self.ncols-1)*self.padding
			padh = (nrows-1)*self.padding
			isize = (self.ncols*self.photow+marw+padw, nrows*photoh+marh+padh)

			# Create the new image. The background doesn't have to be white
			white = (255,255,255)
			inew = Image.new('RGB',isize,white)

			# Write the header
			d = ImageDraw.Draw(inew).text((10,10), str(headerInfo), fill=(0,0,0))

		# Insert each thumb:
		for irow in range(nrows):
			for icol in range(self.ncols):
				left = self.marl + icol*(self.photow+self.padding)
				right = left + self.photow
				upper = mart + irow*(photoh+self.padding)
				lower = upper + photoh
				bbox = (left,upper,right,lower)
				try:
					img = imgs.pop(0)
				except:
					break
				inew.paste(img,bbox)
		return inew

	def get_length(self, input_video):
		result = subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'default=noprint_wrappers=1:nokey=1', input_video], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
		len = math.floor(float(result.stdout))
		return int(len)

	def getTimesInterval(self, videoLength, interval):
		times = [t for t in range(0, videoLength, interval)]
		labels = []
		for t in times:
			labels.append(str(timedelta(seconds=round(t))))
		return times, labels

	def getTimesQuantity(self, videoLength, numFrames):
		step = math.floor(videoLength/numFrames)
		return self.getTimesInterval(videoLength, step)

	def getTimesShotDetection(self, data):
		times = []
		labels = []
		
		for i, shot in enumerate(data["shots"]):
			if shot["type"] == "scene": # for Azure-- skip things labeled "scene"
				continue

			# Find the timestamp for the middle frame of the shot
			start = float(self.get_seconds_from_time_string(shot["start"]))
			end = float(self.get_seconds_from_time_string(shot["end"]))
			middle = str(timedelta(seconds=(end-start)/2 + start))
			times.append(middle)

			# Save a formatted time range for this shot in the list of times
			range = str(timedelta(seconds=round(start))) + " - " + str(timedelta(seconds=round(end)))
			labels.append(range)
		return times, labels
	def get_seconds_from_time_string(self, time_string):
		pt = datetime.strptime(time_string,'%H:%M:%S.%f')
		total_seconds = pt.second + pt.minute*60 + pt.hour*3600
		return total_seconds

	def validate_time(self, frame_seconds, video_length):
		if frame_seconds is None or frame_seconds <= 0:
			print("Invalid seconds input for time")
			return False
		if frame_seconds > video_length:
			print("Invalid seconds input for time.  Cannot be greater than video length")
			return False
		return True

	def validate_quantity(self, frame_quantity):
		if frame_quantity is None or frame_quantity <= 0:
			print("Invalid quantity input for quantity")
			return False
		return True

	def validate_shots(self, amp_shots):
		if amp_shots is None or 'shots' not in amp_shots.keys():
			print("Invalid shots json for shots")
			return False
		return True

	def validate_facial(self, amp_facial_recognition):
		if amp_facial_recognition is None or 'frames' not in amp_facial_recognition.keys():
			print("Invalid frames json for facial recognition")
			return False
		return True

	def get_thumbs(self, video, times, temporary_directory):
		fnames = []
		print(times)
		# For every shot...
		for i,t in enumerate(times):
			# Set the name for the temp image file, and add that to the list of filenames
			outname = os.path.join(temporary_directory, str(i) + ".jpg")
			fnames.append(outname)
			print(t)
			(
				ffmpeg
				.input(video, ss=t)
				.output(outname, vframes=1)
				.run()
			)
			print("  Saved thumbnail: %d/%d" % (i+1, len(times)))
		return fnames