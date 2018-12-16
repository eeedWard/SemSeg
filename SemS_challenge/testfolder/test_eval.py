#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Created on Sun Dec 16 14:21:47 2018

@author: haliang
"""
#import __future__

import logging
import math
import metrics
import numpy as np
#from duckietown_challenges import wrap_evaluator, ChallengeEvaluator, InvalidSubmission
from demo import getinput
import os

#from duckietown_challenges import wrap_solution, ChallengeSolution, ChallengeInterfaceSolution
from myalgorithm import *

img_reader = getinput(19,'.') #change the dirctionary here
test_set_from_eval = list() 

for i in range(img_reader.im_num):
    test_img, ground_truth = img_reader.send_img()
    test_set_from_eval.append(test_img) 

myclass = MyClass()
predicted_label_set = list()

for image in test_set_from_eval:
    label = myclass.run_my_code(image)
    predicted_label_set.append(label)
    print(np.unique(label))

#	data = {'data': predicted_label_set}
    
running_metrics_val  = metrics.runningScore(19) #19 is the number of the labels

#read test set and ground truth
img_reader = getinput(19,'.') #put in init?

for i in range(len(predicted_label_set)):
    test_img, ground_truth = img_reader.send_img() #put in init?
    predicted_label = predicted_label_set[i]
    print(predicted_label.shape)
    print(ground_truth.shape)
    # ground_truth = ground_truth_from_eval[i]
    running_metrics_val.update(ground_truth,predicted_label)
    # ground_truth = metrics.get_GT() #this gets an artificial ground truth
score, class_iou = running_metrics_val.get_scores()   
print(score)



