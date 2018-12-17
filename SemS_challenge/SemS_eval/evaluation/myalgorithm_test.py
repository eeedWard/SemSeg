import numpy as np
# import tensorflow as tf
# import cv2


# # from tqdm import trange
# from config import Config
# from model import ICNet, ICNet_BN


class MyClass():
	def __init__(self):
		self.label1 = 4

	def run_my_code(self, image):

		# pred_label_img = np.ones((1, 1024, 2048), int)
		#pred_label_img = self.test_set_from_eval * self.label1
		pred_label_img = np.ones((1,image.shape[0],image.shape[1]), int)

		return pred_label_img


# class InferenceConfig(Config):
#     def __init__(self, dataset, is_training, filter_scale):
#         Config.__init__(self, dataset, is_training, filter_scale)
    
#     # You can choose different model here, see "model_config" dictionary. If you choose "others", 
#     # it means that you use self-trained model, you need to change "filter_scale" to 2.
#     model_type = 'trainval'

#     # Set pre-trained weights here (You can download weight from Google Drive) 
#     model_weight = '/challenge-solution/icnet_cityscapes_trainval_90k.npy'
    
#     # Define default input size here
#     INFER_SIZE = (1024, 2048, 3)
                  

# class MyClass():
# 	def __init__(self):
# 		model_config = {'train': ICNet, 'trainval': ICNet, 'train_bn': ICNet_BN, 'trainval_bn': ICNet_BN, 'others': ICNet_BN}
# 		dataset = 'cityscapes'
# 		filter_scale = 1
# 		cfg = InferenceConfig(dataset, is_training=False, filter_scale=filter_scale)
# 		self.label1 = 4
# 		self.label2 = 5
# 		# Create graph here 
# 		model = model_config[cfg.model_type]
# 		net = model(cfg=cfg, mode='inference')
# 		# Create session & restore weight!
# 		net.create_session()
# 		net.restore(cfg.model_weight)
# 		self.net=net
# 		self.cfg=cfg

# 	def run_my_code(self,im1):
# 		cfg=self.cfg
# 		if im1.shape != cfg.INFER_SIZE:
# 			im1 = cv2.resize(im1, (cfg.INFER_SIZE[1], cfg.INFER_SIZE[0]))
# 		results1=self.net.predict(im1)

# 		return results1

