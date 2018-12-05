#coding=utf-8
import cv2
import numpy as np  

img = cv2.imread("/home/liu/internship/exm.jpg")
img = cv2.GaussianBlur(img,(3,3),0)
#cv2.imwrite('/home/liu/internship/gaussblur.jpg',img)
img = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
#xgrad=cv2.Sobel(img,cv2.CV_16SC1,1,0)
#cv2.imwrite('/home/liu/internship/soblex.jpg',xgrad)
#ygrad=cv2.Sobel(img,cv2.CV_16SC1,0,1)
#cv2.imwrite('/home/liu/internship/sobley.jpg',ygrad)
#gray_lap = cv2.Laplacian(img,cv2.CV_16S,ksize = 3)
lp = cv2.Laplacian(img,cv2.CV_16S,ksize = 5)
#cv2.imshow('Canny', canny)
cv2.imwrite('/home/liu/internship/resultl.jpg',lp)
#cv2.waitKey(0)
#cv2.destroyAllWindows()