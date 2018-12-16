import numpy as np
import metrics
# import myalgorithm_test
from demo import getinput
import os
import cv2


# import myalgorithm	

# myclass = myalgorithm.MyClass() #init class and load weights
# ground_truth_set=list()
# predicted_label_set = list()
# img_reader = getinput(19,'.') 

#         #initialize empty test set list
# test_set_from_eval = list() 
#         # ground_truth_from_eval =  list()

#         #iterate over each data of test set / gt
# for i in range(img_reader.im_num):
#     test_img, ground_truth = img_reader.send_img()
#     ground_truth_set.append(ground_truth)
#     test_set_from_eval.append(test_img)
# running_metrics_val  = metrics.runningScore(19) #19 is the number of the labels
# i=0
# for image in test_set_from_eval:

# 	label = myclass.run_my_code(image)
# 	print(label.shape)
# 	predicted_label_set.append(label)
# 	running_metrics_val.update(label, ground_truth_set[i])
# 	i=i+1


# score, class_iou = running_metrics_val.get_scores()
# data = {'data': predicted_label_set}
# la = data['data']
# print(score)
# print(la)

ground_truth = np.ones((1, 120, 240))
ground_truth_img = ground_truth[0, :, :]
ground_truth_img_resize =  cv2.resize(ground_truth_img, (700, 500), interpolation=cv2.INTER_NEAREST) #this is only to use DT images on cityscape!
ground_truth = ground_truth_img_resize[np.newaxis,:]
print(ground_truth.shape)

img = cv2.imread("./image/example3.jpg")
test_img = cv2.resize(img, (700, 500)) #this is only to use DT images on cityscape!
print(test_img.shape)

acc = 12
mean_acc_weightede = 1/0.1
mean_iu = float('NaN')
mean_iu_weighted = float('Inf')

if (np.isnan(acc)) or np.isinf(acc):
    acc = 0
if (np.isnan(mean_acc_weightede)) or np.isinf(mean_acc_weightede):
    mean_acc_weightede = 0
if (np.isnan(mean_iu)) or np.isinf(mean_iu):
    mean_iu = 0
if (np.isnan(mean_iu_weighted)) or np.isinf(mean_iu_weighted):
    mean_iu_weighted = 0

print(acc, mean_iu, mean_acc_weightede, mean_iu_weighted)

a = [1, 2, 3]
print(np.dot(a, a))

imp=os.path.join(self.image_path,self.imlist[self.idx])
gtp=os.path.join(self.gt_path,self.gtlist[self.idx])
self.idx=(self.idx+1)%self.im_num
gt=cv2.imread(gtp,cv2.IMREAD_GRAYSCALE)
gt=gt[np.newaxis,:]
a = cv2.imread(imp),

print(gt[0, : , :])