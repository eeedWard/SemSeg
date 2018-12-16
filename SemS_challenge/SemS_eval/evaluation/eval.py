#!/usr/bin/env python
from __future__ import *

import logging
import math
import metrics
import numpy as np
from duckietown_challenges import wrap_evaluator, ChallengeEvaluator, InvalidSubmission
from demo import getinput
import os
logging.basicConfig()
logger = logging.getLogger('evaluator')
logger.setLevel(logging.DEBUG)



class Evaluator(ChallengeEvaluator):

    def prepare(self, cie):



        # for file in os.listdir('./challenge-evaluator/image'):
        #     print(file)


        #read test set and ground truth
        img_reader = getinput(19,'./challenge-evaluator') 

        #initialize empty test set list
        test_set_from_eval = list() 
        # ground_truth_from_eval =  list()

        #iterate over each data of test set / gt
        for i in range(img_reader.im_num):
            test_img, ground_truth = img_reader.send_img()

            test_set_from_eval.append(test_img)
            # ground_truth_from_eval.append(ground_truth)

        #test_set: list of np arrays of shape: (1024, 2048, 3)
        #ground_truth: list of np arrays of shape: (1, 1024, 2048)

        # test_set_from_eval = np.ones((1, 1024, 2048), int)
        cie.set_challenge_parameters({'test_set':test_set_from_eval})

    def score(self, cie):


        solution_output = cie.get_solution_output_dict()
        print('solution output (should be a dict)', solution_output)

        predicted_labels_set = solution_output['data'] #this should be the predicted labels --> check
        print('predicted label set', predicted_labels_set)
    	'''
    	Define here how scoring of a solution is done.
    	'''
        running_metrics_val  = metrics.runningScore(19) #19 is the number of the labels


        #read test set and ground truth
        img_reader = getinput(19,'./challenge-evaluator') #put in init?

        for i in range(len(predicted_labels_set)):
            test_img, ground_truth = img_reader.send_img() #put in init?
            # ground_truth_from_eval.append(ground_truth) # put in init?


            predicted_label = predicted_labels_set[i]
            print(predicted_label.shape)
            print(ground_truth.shape)
            # ground_truth = ground_truth_from_eval[i]
            running_metrics_val.update(predicted_label, ground_truth)

        # ground_truth = metrics.get_GT() #this gets an artificial ground truth

        
        score, class_iou = running_metrics_val.get_scores()

        score1 = score['Overall Acc: \t']
        score2 = score['Mean Acc : \t']
        score3 = score['FreqW Acc : \t']
        score4 = score['Mean IoU : \t']

        #these lines are from template
        # temp = solution_output['data']
    	# score = 2*temp


        cie.set_score('score1', score1, 'blurb')
        cie.set_score('score2', score2, 'blurb')
        cie.set_score('score3', score3, 'blurb')
        cie.set_score('score4', score4, 'blurb')


if __name__ == '__main__':
    wrap_evaluator(Evaluator())
