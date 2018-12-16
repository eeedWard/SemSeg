#!/usr/bin/env python
import logging
import math
import metrics
import numpy as np
from duckietown_challenges import wrap_evaluator, ChallengeEvaluator, InvalidSubmission
from demo import getinput
import os
# import cv2
logging.basicConfig()
logger = logging.getLogger('evaluator')
logger.setLevel(logging.DEBUG)



class Evaluator(ChallengeEvaluator):

    def prepare(self, cie):


        # to check what's inside the container, uncomment this below
        # for file in os.listdir('./challenge-evaluator/image'):
        #     print(file)


        # read test set
        img_reader = getinput(7,'./challenge-evaluator') 

        #initialize empty test set list
        test_set_from_eval = list() 

        #iterate over each data of test set 
        for i in range(img_reader.im_num):
            test_img, ground_truth = img_reader.send_img()


            test_img = cv2.resize(test_img, (2048, 1024)) #this is only to use DT images on cityscape!
            print()
            print()
            print()
            print()
            print('test_img.shape', test_img.shape)
            print()
            print()
            print()


            test_set_from_eval.append(test_img)

        #test_set: list of np arrays of shape: (1024, 2048, 3)
        #ground_truth: list of np arrays of shape: (1, 1024, 2048)

        cie.set_challenge_parameters({'test_set':test_set_from_eval})

    def score(self, cie):

        # read predicted labes from solution
        solution_output = cie.get_solution_output_dict()
        predicted_labels_set = solution_output['data']
        print()
        print()
        print()
        print()
        print('predicted label set', predicted_labels_set)
        print('predicted label set[0].shape', predicted_labels_set[0].shape)
        print()
        print()
        print()


    	# create object to evaluate the solution
        running_metrics_val  = metrics.runningScore(7) #19 is the number of the labels

        # read ground truth
        img_reader = getinput(7,'./challenge-evaluator') # /challenge-evaluator is needed for a bug in the dockerfile
                                                          # when accessing folders

        for i in range(len(predicted_labels_set)):
            test_img, ground_truth = img_reader.send_img() 


            ground_truth =  cv2.resize(ground_truth, (2048, 1024), interpolation=cv2.INTER_NEAREST) #this is only to use DT images on cityscape!
            print()
            print()
            print()
            print()
            print('ground_truth.shape', ground_truth.shape)
            print()
            print()
            print()
            predicted_label = predicted_labels_set[i]
            running_metrics_val.update(ground_truth,predicted_label)

        #ground_truth: list of np arrays of shape: (1, 1024, 2048)

        
        score, class_iou = running_metrics_val.get_scores()

        score1 = score['Overall_Acc']
        score2 = score['Mean_Weighted_Acc']
        score3 = score['Mean_IoU']
        score4 = score['Mean_Weighted_IoU']

        cie.set_score('Overall Acc', score1, 'blurb')
        cie.set_score('Mean Weighted Acc', score2, 'blurb')
        cie.set_score('Mean IoU', score3, 'blurb')
        cie.set_score('Mean Weighted IoU', score4, 'blurb')


if __name__ == '__main__':
    wrap_evaluator(Evaluator())