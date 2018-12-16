#!/usr/bin/env python
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


        # to check what's inside the container, uncomment this below
        # for file in os.listdir('./challenge-evaluator/image'):
        #     print(file)


        # read test set
        img_reader = getinput(19,'./challenge-evaluator') 

        #initialize empty test set list
        test_set_from_eval = list() 

        #iterate over each data of test set 
        for i in range(img_reader.im_num):
            test_img, ground_truth = img_reader.send_img()

            test_set_from_eval.append(test_img)

        #test_set: list of np arrays of shape: (1024, 2048, 3)
        #ground_truth: list of np arrays of shape: (1, 1024, 2048)

        cie.set_challenge_parameters({'test_set':test_set_from_eval})

    def score(self, cie):

        # read predicted labes from solution
        solution_output = cie.get_solution_output_dict()
        predicted_labels_set = solution_output['data']

    	# create object to evaluate the solution
        running_metrics_val  = metrics.runningScore(19) #19 is the number of the labels

        # read ground truth
        img_reader = getinput(19,'./challenge-evaluator') # /challenge-evaluator is needed for a bug in the dockerfile
                                                          # when accessing folders

        for i in range(len(predicted_labels_set)):
            test_img, ground_truth = img_reader.send_img() 

            predicted_label = predicted_labels_set[i]
            running_metrics_val.update(ground_truth,predicted_label)

        #ground_truth: list of np arrays of shape: (1, 1024, 2048)

        
        score, class_iou = running_metrics_val.get_scores()

        score1 = score['Overall Acc: ']
        score2 = score['Mean Weighted Acc :']
        score3 = score['FreqW Acc : ']
        score4 = score['Mean IoU : ']

        cie.set_score('score1', score1, 'blurb')
        cie.set_score('score2', score2, 'blurb')
        cie.set_score('score3', score3, 'blurb')
        cie.set_score('score4', score4, 'blurb')


if __name__ == '__main__':
    wrap_evaluator(Evaluator())