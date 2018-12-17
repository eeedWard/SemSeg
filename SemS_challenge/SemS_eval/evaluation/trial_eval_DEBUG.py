import numpy as np
import metrics
# import myalgorithm_test
from demo import getinput
import os
import cv2


import myalgorithm_test	

myclass = myalgorithm_test.MyClass() #init class and load weights
ground_truth_set=list()
predicted_label_set = list()


img_reader = getinput(7,'.') 

        #initialize empty test set list
test_set_from_eval = list() 
        # ground_truth_from_eval =  list()

        #iterate over each data of test set / gt
for i in range(img_reader.im_num):
    test_img, ground_truth = img_reader.send_img()
    test_img = cv2.resize(test_img, (700, 500))
    test_set_from_eval.append(test_img)

    ground_truth_img = ground_truth[0, :, :]
    ground_truth_img_resize =  cv2.resize(ground_truth_img, (700, 500), interpolation=cv2.INTER_NEAREST) #this is only to use DT images on cityscape!
    ground_truth = ground_truth_img_resize[np.newaxis,:]
    ground_truth_set.append(ground_truth)
    

class_weights = np.array([0.05, 0.15, 0.35, 0.15, 0.1, 0.1, 0.1]) # sum of weights must be == 1
        # create object to evaluate the solution
running_metrics_val  = metrics.runningScore(7, class_weights) #19 is the number of the labels

i=0
for image in test_set_from_eval:

	label = myclass.run_my_code(image)
	print('label.shape', label.shape)
	predicted_label_set.append(label)


	running_metrics_val.update(label, ground_truth_set[i])
	i=i+1


score, class_iou = running_metrics_val.get_scores()


score, class_iou = running_metrics_val.get_scores()

score1 = score['Overall_Acc']
score2 = score['Mean_Weighted_Acc']
score3 = score['Mean_IoU']
score4 = score['Mean_Weighted_IoU']

print(score)




# ground_truth = np.ones((1, 120, 240))
# ground_truth_img = ground_truth[0, :, :]
# ground_truth_img_resize =  cv2.resize(ground_truth_img, (700, 500), interpolation=cv2.INTER_NEAREST) #this is only to use DT images on cityscape!
# ground_truth = ground_truth_img_resize[np.newaxis,:]
# print(ground_truth.shape)

# img = cv2.imread("./image/example3.jpg")
# test_img = cv2.resize(img, (700, 500)) #this is only to use DT images on cityscape!
# print(test_img.shape)

# acc = 12
# mean_acc_weightede = 1/0.1
# mean_iu = float('NaN')
# mean_iu_weighted = float('Inf')

# if (np.isnan(acc)) or np.isinf(acc):
#     acc = 0
# if (np.isnan(mean_acc_weightede)) or np.isinf(mean_acc_weightede):
#     mean_acc_weightede = 0
# if (np.isnan(mean_iu)) or np.isinf(mean_iu):
#     mean_iu = 0
# if (np.isnan(mean_iu_weighted)) or np.isinf(mean_iu_weighted):
#     mean_iu_weighted = 0

# print(acc, mean_iu, mean_acc_weightede, mean_iu_weighted)

# a = [1, 2, 3]
# print(np.dot(a, a))

