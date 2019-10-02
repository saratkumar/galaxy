#!/usr/bin/env python3

import sys
import json
import math
import os
import subprocess
import time
from shutil import copyfile

from segmentation_schema import SegmentationSchema

# Try to load, if it fails launch the virtual env. and re-execute the script
try:
	 from inaSpeechSegmenter import Segmenter
except ModuleNotFoundError as e:
	# can't find the module!
	if "VENV_ATTEMPT" in os.environ:
		# we must have failed the venv bootstrap.
		print("Cannot initialize the bootstrap")
		exit(1)
	# try to re-run ourselves
	os.environ["VENV_ATTEMPT"] = "1"
	os.chdir("/srv/amp/inaspeech")
	r = subprocess.run(["pipenv", "run", *sys.argv])
	exit(r.returncode)


def main():
	(input_file, input_segmentation_json, output_file) = sys.argv[1:4]

	# Turn segmentation json file into segmentation object
	with open(input_segmentation_json, 'r') as file:
		seg_data = SegmentationSchema().from_json(json.load(file))
	
	remove_silence(seg_data, input_file, output_file)
	exit(0)


# Given segmentation data, an audio file, and output file, remove silence
def remove_silence(seg_data, filename, output_file):

	start_block = -1 # Beginning of a speech segment
	previous_end = 0 # Last end of a speech segment
	segments = 0 # Num of speech segments

	# For each segment, calculate the blocks of speech segments
	for s in seg_data.segments:
		if s.label=="silence" or s.label=="music":
			# If we have catalogued speech, create a segment from that chunk
			if previous_end > 0:
				create_audio_part(filename, start_block, previous_end, segments)
				# Reset the variables
				start_block = -1
				previous_end = 0
				segments+=1
			else:
				start_block = s.end
		else:
			# If this is a new block, mark the start
			if start_block<0:      
				start_block = s.start
			previous_end = s.end

	# If we reached the end and still have an open block of speech, output it
	if previous_end > 0:
		create_audio_part(filename, start_block, previous_end, segments)

	# Concetenate each of the individual parts into one audio file of speech
	concat_files(segments, output_file)


# Given a start and end offset, create a segment of audio 
def create_audio_part(input_file, start, end, segment):
	# Create a temporary file name
	tmp_filename = "tmp_" + str(segment) + ".wav"

	# Convert the seconds to a timestamp
	start_str = time.strftime('%H:%M:%S', time.gmtime(start))

	# Calculate duration of segment convert it to a timestamp
	duration = end - start
	duration_str = time.strftime('%H:%M:%S', time.gmtime(duration))

	# Execute ffmpeg command to split of the segment
	ffmpeg_out = subprocess.Popen(['ffmpeg', '-i', input_file, '-ss', start_str, '-t', duration_str, '-acodec', 'copy', tmp_filename], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
	ffmpeg_out.wait()
	#stdout,stderr = ffmpeg_out.communicate()

# Take each of the individual parts, create one larger file and copy it to the destination file
def concat_files(segments, output_file):
	# Create the ffmpeg command, adding an input file for each segment created
	ffmpegCmd = ['ffmpeg']
	for s in range(0, segments):
		this_segment_name = "tmp_" + str(s) + ".wav"
		ffmpegCmd.append("-i")
		ffmpegCmd.append(this_segment_name)
	ffmpegCmd.extend(['-filter_complex',"[0:0][1:0][2:0]concat=n=" + str(segments) + ":v=0:a=1[out]", "-map", "[out]", "output.wav"])

	# Run ffmpeg 
	ffmpeg_out = subprocess.Popen(ffmpegCmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
	ffmpeg_out.wait()
	#stdout,stderr = ffmpeg_out.communicate()

	# Copy the temporary result to the final destination
	copyfile("output.wav", output_file)

	# Cleanup temp files
	cleanup_files(segments)

def cleanup_files(segments):
	# Remove concatenated temporary file
	if os.path.exists("output.wav"):
		os.remove("output.wav") 
	# Remove each individual part if it exists
	for s in range(0, segments):
		this_segment_name = "tmp_" + str(s) + ".wav"
		if os.path.exists(this_segment_name):
			os.remove(this_segment_name) 


if __name__ == "__main__":
	main()
