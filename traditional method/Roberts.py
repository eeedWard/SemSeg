#coding=utf-8
import cv2
import numpy as np  

def RobertsOperator(roi):
    operator_first = np.array([[-1,0],[0,1]])
    operator_second = np.array([[0,-1],[1,0]])
    return np.abs(np.sum(roi*operator_first))+np.abs(np.sum(roi[1:,1:]*operator_second))
def RobertsAlogrithm(image):
    image = cv2.copyMakeBorder(image,1,1,1,1,cv2.BORDER_DEFAULT)
    for i in range(1,image.shape[0]):
        for j in range(1,image.shape[1]):
            image[i,j] = RobertsOperator(image[i-1:i+1,j-1:j+1])
    return image[1:image.shape[0],1:image.shape[1]]

img = cv2.imread("/home/liu/internship/exm.jpg")
img = cv2.GaussianBlur(img,(3,3),0)
img = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
#Robert_img = RobertsAlogrithm(img)
img = cv2.copyMakeBorder(img,1,1,1,1,cv2.BORDER_DEFAULT)
cv2.imwrite('/home/liu/internship/resultr.jpg',img)
result=np.ones([img.shape[0]-1,img.shape[1]-1])
for i in range(0,img.shape[0]-1):
    for j in range(0,img.shape[1]-1):
        #img[i,j] = RobertsOperator(img[i-1:i+1,j-1:j+1])
        roi=img[i:i+2,j:j+2]
        #print roi
        operator_first = np.array([[-1,0],[0,1]])
        operator_second = np.array([[0,-1],[1,0]])
        result[i,j] = np.sqrt(np.abs(np.sum(roi*operator_first))**2+np.abs(np.sum(roi*operator_second))**2)
        print result[i,j]
Robert_img=result[1:img.shape[0]-1,1:img.shape[1]-1]


#xgrad=cv2.Sobel(img,cv2.CV_16SC1,1,0)
#cv2.imwrite('/home/liu/internship/soblex.jpg',xgrad)
#ygrad=cv2.Sobel(img,cv2.CV_16SC1,0,1)
#cv2.imwrite('/home/liu/internship/sobley.jpg',ygrad)
#canny = cv2.Canny(xgrad, ygrad,30, 90)
#cv2.imshow('Canny', canny)
cv2.imwrite('/home/liu/internship/resultr.jpg',Robert_img)