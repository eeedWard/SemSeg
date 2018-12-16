import numpy as np
import cv2
from metrics import runningScore, averageMeter
import os

class getinput(object):
    def __init__(self, n_classes,root_path):
        self.n_classes = n_classes
        self.image_path=os.path.join(root_path, 'image')
        self.gt_path=os.path.join(root_path,'groundtruth')
        #self.image_path=os.path.join('.','challenge-evaluator', 'image')
        #self.gt_path=os.path.join('.','challenge-evaluator','groundtruth')
        imls=os.listdir(self.image_path)
        imls.sort()
        gtls=os.listdir(self.gt_path)
        gtls.sort()
        self.imlist=imls
        self.gtlist=gtls
        self.im_num=len(self.imlist)
        assert self.im_num==len(self.gtlist)
        self.idx=0

    def send_img(self):
        imp=os.path.join(self.image_path,self.imlist[self.idx])
        gtp=os.path.join(self.gt_path,self.gtlist[self.idx])
        self.idx=(self.idx+1)%self.im_num
        gt=cv2.imread(gtp,cv2.IMREAD_GRAYSCALE)
        gt=gt[np.newaxis,:]
        return cv2.imread(imp),gt
    def send_just_img(self):
        img,self.gt=self.send_img()
        return img
    def compute_score(self,lb_pred,gt):
        running_metrics_val = runningScore(self.n_classes)
        running_metrics_val.update(lb_pred, gt)
        score, class_iou = running_metrics_val.get_scores()
        return score
