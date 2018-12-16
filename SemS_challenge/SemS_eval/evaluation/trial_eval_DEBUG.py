import numpy as np
import metrics
# import myalgorithm_test
from demo import getinput
import os


import myalgorithm	

myclass = myalgorithm.MyClass() #init class and load weights
ground_truth_set=list()
predicted_label_set = list()
img_reader = getinput(19,'.') 

        #initialize empty test set list
test_set_from_eval = list() 
        # ground_truth_from_eval =  list()

        #iterate over each data of test set / gt
for i in range(img_reader.im_num):
    test_img, ground_truth = img_reader.send_img()
    ground_truth_set.append(ground_truth)
    test_set_from_eval.append(test_img)
running_metrics_val  = metrics.runningScore(19) #19 is the number of the labels
i=0
for image in test_set_from_eval:

	label = myclass.run_my_code(image)
	print(label.shape)
	predicted_label_set.append(label)
	running_metrics_val.update(label, ground_truth_set[i])
	i=i+1


score, class_iou = running_metrics_val.get_scores()
data = {'data': predicted_label_set}
la = data['data']
print(score)
print(la)
