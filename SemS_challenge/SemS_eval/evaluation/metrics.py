# Adapted from score written by wkentaro
# https://github.com/wkentaro/pytorch-fcn/blob/master/torchfcn/utils.py

import numpy as np


class runningScore(object):
    def __init__(self, n_classes, weights):
        self.n_classes = n_classes
        self.confusion_matrix = np.zeros((n_classes, n_classes))
        self.weights = weights

    def _fast_hist(self, label_true, label_pred, n_class):
        mask = (label_true >= 0) & (label_true < n_class)
        hist = np.bincount(
            n_class * label_true[mask].astype(int) + label_pred[mask],
            minlength=n_class ** 2,
        ).reshape(n_class, n_class)
        return hist

    def update(self, label_trues, label_preds):
        for lt, lp in zip(label_trues, label_preds):
            self.confusion_matrix += self._fast_hist(
                lt.flatten(), lp.flatten(), self.n_classes
            )

    def get_scores(self):
        """Returns accuracy score evaluation result.
            - overall accuracy
            - mean accuracy
            - mean IU
            - fwavacc
        """




        hist = self.confusion_matrix

        acc = np.diag(hist).sum() / hist.sum() # overall acc
        acc_cls = np.diag(hist) / hist.sum(axis=1) # accuracy for each single calss
        mean_acc = np.nanmean(acc_cls) #mean accuracy with equal weights
        mean_acc_weighted = np.dot(self.weights, acc_cls) # weighted accuracy


        iu = np.diag(hist) / (hist.sum(axis=1) + hist.sum(axis=0) - np.diag(hist))
        mean_iu = np.nanmean(iu)
        mean_iu_weighted = np.dot(self.weights, iu)


        freq = hist.sum(axis=1) / hist.sum()
        fwavacc = (freq[freq > 0] * iu[freq > 0]).sum()
        cls_iu = dict(zip(range(self.n_classes), iu))

        if (np.isnan(acc)) or np.isinf(acc):
            acc = 0
        if (np.isnan(mean_acc_weighted)) or np.isinf(mean_acc_weighted):
            mean_acc_weighted = 0
        if (np.isnan(mean_iu)) or np.isinf(mean_iu):
            mean_iu = 0
        if (np.isnan(mean_iu_weighted)) or np.isinf(mean_iu_weighted):
            mean_iu_weighted = 0


        return (
            {
                "Overall_Acc": acc,
                "Mean_Weighted_Acc": mean_acc_weighted,
                #"FreqW Acc : ": fwavacc,
                "Mean_IoU": mean_iu,
                "Mean_Weighted_IoU": mean_iu_weighted,
            },
            cls_iu,
        )

    def reset(self):
        self.confusion_matrix = np.zeros((self.n_classes, self.n_classes))



# class averageMeter(object):
#     """Computes and stores the average and current value"""
#     def __init__(self):
#         self.reset()

#     def reset(self):
#         self.val = 0
#         self.avg = 0
#         self.sum = 0
#         self.count = 0

#     def update(self, val, n=1):
#         self.val = val
#         self.sum += val * n
#         self.count += n
#         self.avg = self.sum / self.count