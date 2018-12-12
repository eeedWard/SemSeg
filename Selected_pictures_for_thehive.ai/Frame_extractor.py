from shutil import move, copy
import numpy
import os.path


#se the paths of the file and the destination folder for the selected frames

pathOrigin = os.path.join("C:/", "Duckietown", "SemSeg", "ROSBAGS", "ROSBAGS_22-11", "d_CR_educk")
pathOrigin = './Halved_not_uploaded'
pathDestination = os.path.join("C:/", "Users", "Edoardo", "Desktop", "Duckietown", "AA extracted", "bright_clean_run_extracted_250")
pathDestination = './4th'

#edit the second (total number of original frames in your folder) and third (number of selected frames) args of the linspace function 

iteration = 3

for fileOrigin in sorted(os.listdir(pathOrigin)):

	if iteration % 4 == 0:


		pathOriginFile = os.path.join(pathOrigin, fileOrigin)
		
		copy(pathOriginFile, pathDestination)


		print(fileOrigin + ' ...copied')

	iteration += 1

print('---> Job finished <--')