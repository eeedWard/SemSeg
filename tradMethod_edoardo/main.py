from line_detector_DT import LineDetectorHSV
import os
import cv2
from plotter import plotterDET

def image_cutter(frame):
    cut_off_height = 160
    # print('Initial size: ')
    # print(frame.shape)
    frame = frame[cut_off_height:, :, :]
    # print('Resized to: ')
    # print(frame.shape)
    return frame



if __name__ == '__main__':


	#detector opbject
	detector = LineDetectorHSV()
	test_img_dir = './test_images'

	iteration = 0

	for test_img in os.listdir(test_img_dir):

		iteration += 1


		frame = cv2.imread(os.path.join(test_img_dir, test_img))
		frame = image_cutter(frame)

		detector.setImage(frame) #put image into detector machine

		bw, edge_color = detector._colorFilter('white')

		Detections = detector.detectLines('white')

		print('Frame dims: ', frame.shape)

		print('Detection number: ', iteration)
		print()
		# print(Detections)

		result = plotterDET(frame, Detections.lines, (0, 255, 0), Detections.centers, Detections.normals)
		# plotterDET(bgr, lines, paint, centers, normals, area_white, area_red, area_yellow)

		cv2.imwrite('./output_images/{}'.format(test_img), bw)
		cv2.imshow("thresholded{}".format(test_img), result)
		cv2.waitKey(0)
		cv2.destroyAllWindows()
 