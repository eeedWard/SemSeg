import numpy as np
import cv2
import PIL.Image
label_png = 'label.png'
lbl = np.asarray(PIL.Image.open(label_png))
cv2.imwrite('cityscape_label.png',lbl)
