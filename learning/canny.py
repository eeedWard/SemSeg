#coding=utf-8
import cv2
import math
import numpy as np  

def hough_lines(img, rho, theta, threshold, min_line_len, max_line_gap,hight,lamda):
    lines = cv2.HoughLinesP(img, rho, theta, threshold, np.array([]), minLineLength=min_line_len, maxLineGap=max_line_gap)
    line_img = np.zeros((img.shape[0], img.shape[1], 3), dtype=np.uint8)  # 3-channel RGB image
    draw_lines(line_img, lines)
    dic_vector=findic(img, lines,hight,lamda)
    dic_vector=dic_vector/math.sqrt(dic_vector[0]**2+dic_vector[1]**2+dic_vector[2]**2)
    return line_img,dic_vector

def weighted_img(img, initial_img, a=0.8, b=1., c=0.):
    """
    `img` is the output of the hough_lines(), An image with lines drawn on it.
    Should be a blank image (all black) with lines drawn on it.
    
    `initial_img` should be the image before any processing.
    
    The result image is computed as follows:
    
    initial_img * α + img * β + λ
    NOTE: initial_img and img must be the same shape!
    """
    return cv2.addWeighted(initial_img, a, img, b, c)

def filter_colors(seg,orig):
    """
    Filter the image to include only yellow and white pixels
    """

    # Filter green pixels
    hsv = cv2.cvtColor(seg, cv2.COLOR_BGR2HSV)
    lower_purple = np.array([140,120,120])
    upper_purple = np.array([160,135,135])
    purple_mask = cv2.inRange(hsv, lower_purple, upper_purple)
    #green_mask = cv2.bitwise_not(green_mask, green_mask)
    purple_image = cv2.bitwise_and(orig, orig, mask=purple_mask)

    return purple_image



def draw_lines(img, lines, color=[255, 0, 0], thickness=10):
    """
    NOTE: this is the function you might want to use as a starting point once you want to 
    average/extrapolate the line segments you detect to map out the full
    extent of the lane (going from the result shown in raw-lines-example.mp4
    to that shown in P1_example.mp4).  
    
    Think about things like separating line segments by their 
    slope ((y2-y1)/(x2-x1)) to decide which segments are part of the left
    line vs. the right line.  Then, you can average the position of each of 
    the lines and extrapolate to the top and bottom of the lane.
    
    This function draws `lines` with `color` and `thickness`.   
    Lines are drawn on the image inplace (mutates the image).
    If you want to make the lines semi-transparent, think about combining
    this function with the weighted_img() function below
    """
    # In case of error, don't draw the line(s)
    if lines is None:
        return
    if len(lines) == 0:
        return
    draw_right = True
    draw_left = True
    
    # Find slopes of all lines
    # But only care about lines where abs(slope) > slope_threshold
    slope_threshold = 0.5
    slopes = []
    new_lines = []
    for line in lines:
        x1, y1, x2, y2 = line[0]  # line = [[x1, y1, x2, y2]]
        
        # Calculate slope
        if x2 - x1 == 0.:  # corner case, avoiding division by 0
            slope = 999.  # practically infinite slope
        else:
            slope = (y2 - y1) / (x2 - x1)
            
        # Filter lines based on slope
        if abs(slope) > slope_threshold:
            slopes.append(slope)
            new_lines.append(line)
        
    lines = new_lines
    
    # Split lines into right_lines and left_lines, representing the right and left lane lines
    # Right/left lane lines must have positive/negative slope, and be on the right/left half of the image
    right_lines = []
    left_lines = []
    for i, line in enumerate(lines):
        x1, y1, x2, y2 = line[0]
        img_x_center = img.shape[1] / 2  # x coordinate of center of image
        if slopes[i] > 0 and x1 > img_x_center and x2 > img_x_center:
            right_lines.append(line)
        elif slopes[i] < 0 and x1 < img_x_center and x2 < img_x_center:
            left_lines.append(line)
            
    # Run linear regression to find best fit line for right and left lane lines
    # Right lane lines
    right_lines_x = []
    right_lines_y = []
    
    for line in right_lines:
        x1, y1, x2, y2 = line[0]
        
        right_lines_x.append(x1)
        right_lines_x.append(x2)
        
        right_lines_y.append(y1)
        right_lines_y.append(y2)
        
    if len(right_lines_x) > 0:
        right_m, right_b = np.polyfit(right_lines_x, right_lines_y, 1)  # y = m*x + b
    else:
        right_m, right_b = 1, 1
        draw_right = False
        
    # Left lane lines
    left_lines_x = []
    left_lines_y = []
    
    for line in left_lines:
        x1, y1, x2, y2 = line[0]
        
        left_lines_x.append(x1)
        left_lines_x.append(x2)
        
        left_lines_y.append(y1)
        left_lines_y.append(y2)
        
    if len(left_lines_x) > 0:
        left_m, left_b = np.polyfit(left_lines_x, left_lines_y, 1)  # y = m*x + b
    else:
        left_m, left_b = 1, 1
        draw_left = False
    
    # Find 2 end points for right and left lines, used for drawing the line
    # y = m*x + b --> x = (y - b)/m
    y1 = img.shape[0]
    y2 = img.shape[0] * (1 - trap_height)
    
    right_x1 = (y1 - right_b) / right_m
    right_x2 = (y2 - right_b) / right_m
    
    left_x1 = (y1 - left_b) / left_m
    left_x2 = (y2 - left_b) / left_m
    
    # Convert calculated end points from float to int
    y1 = int(y1)
    y2 = int(y2)
    print right_x1
    right_x1 = int(right_x1)
    right_x2 = int(right_x2)
    left_x1 = int(left_x1)
    left_x2 = int(left_x2)
    
    # Draw the right and left lines on image
    if draw_right:
        cv2.line(img, (right_x1, y1), (right_x2, y2), color, thickness)
    if draw_left:
        cv2.line(img, (left_x1, y1), (left_x2, y2), color, thickness)

def edge_lines(img, lines):
    #finding the edge lines of the img
    if lines is None:
        return
    if len(lines) == 0:
        return
    draw_right = True
    draw_left = True
    
    # Find slopes of all lines
    # But only care about lines where abs(slope) > slope_threshold
    slope_threshold = 0.5
    slopes = []
    new_lines = []
    for line in lines:
        x1, y1, x2, y2 = line[0]  # line = [[x1, y1, x2, y2]]
        
        # Calculate slope
        if x2 - x1 == 0.:  # corner case, avoiding division by 0
            slope = 999.  # practically infinite slope
        else:
            slope = (y2 - y1) / (x2 - x1)
            
        # Filter lines based on slope
        if abs(slope) > slope_threshold:
            slopes.append(slope)
            new_lines.append(line)
        
    lines = new_lines
    
    # Split lines into right_lines and left_lines, representing the right and left lane lines
    # Right/left lane lines must have positive/negative slope, and be on the right/left half of the image
    right_lines = []
    left_lines = []
    for i, line in enumerate(lines):
        x1, y1, x2, y2 = line[0]
        img_x_center = img.shape[1] / 2  # x coordinate of center of image
        if slopes[i] > 0 and x1 > img_x_center and x2 > img_x_center:
            right_lines.append(line)
        elif slopes[i] < 0 and x1 < img_x_center and x2 < img_x_center:
            left_lines.append(line)
            
    # Run linear regression to find best fit line for right and left lane lines
    # Right lane lines
    right_lines_x = []
    right_lines_y = []
    
    for line in right_lines:
        x1, y1, x2, y2 = line[0]
        
        right_lines_x.append(x1)
        right_lines_x.append(x2)
        
        right_lines_y.append(y1)
        right_lines_y.append(y2)
        back_right = True
        back_left = True

    if len(right_lines_x) > 0:
        right_m, right_b = np.polyfit(right_lines_x, right_lines_y, 1)  # y = m*x + b
    else:
        right_m, right_b = 1, 1
        back_right = False
        
    # Left lane lines
    left_lines_x = []
    left_lines_y = []
    
    for line in left_lines:
        x1, y1, x2, y2 = line[0]
        
        left_lines_x.append(x1)
        left_lines_x.append(x2)
        
        left_lines_y.append(y1)
        left_lines_y.append(y2)
        
    if len(left_lines_x) > 0:
        left_m, left_b = np.polyfit(left_lines_x, left_lines_y, 1)  # y = m*x + b
    else:
        left_m, left_b = 1, 1
        back_left = False
    if back_right and back_left:
        return right_m, right_b, left_m, left_b, True
    else:
        return right_m, right_b, left_m, left_b, False



def region_of_interest(img, vertices):
    mask = np.zeros_like(img)   
    
    #defining a 3 channel or 1 channel color to fill the mask with depending on the input image
    if len(img.shape) > 2:
        channel_count = img.shape[2]  # i.e. 3 or 4 depending on your image
        ignore_mask_color = (255,) * channel_count
    else:
        ignore_mask_color = 255
        
    #filling pixels inside the polygon defined by "vertices" with the fill color    
    cv2.fillPoly(mask, vertices, ignore_mask_color)
    
    #returning the image only where mask pixels are nonzero
    masked_image = cv2.bitwise_and(img, mask)
    return masked_image

def To3D(x,y,hight,lamda):
    Y=-hight#Y is the distance between the camera and ground
    Z=lamda*Y/y-lamda
    X=x/y*Y
    return X,Y,Z

def Tranto3D(x,y,hight,lamda,k):
    Y=-hight#Y is the distance between the camera and ground
    x=x/k
    y=y/k
    Z=lamda*Y/y-lamda
    X=x/y*Y
    return X,Y,Z


def findic(img, lines,hight,lamda):
    right_m, right_b, left_m, left_b, flag=edge_lines(img, lines)
    if flag:
        y1 = img.shape[0]
        y2 = img.shape[0] * 0.9

        right_x1 = (y1 - right_b) / right_m
        right_x2 = (y2 - right_b) / right_m
        left_x1 = (y1 - left_b) / left_m
        left_x2 = (y2 - left_b) / left_m
        print right_x1,right_x2,y1,y2
        center_x=int(img.shape[1]/2)
        center_y=int(img.shape[0]/2)
        left_X1,left_Y1,left_Z1=To3D(left_x1-center_x,y1-center_y,hight,lamda)
        print "points"
        print left_X1,left_Y1,left_Z1
        left_X2,left_Y2,left_Z2=To3D(left_x2-center_x,y2-center_y,hight,lamda)
        print "points"
        print left_X1,left_Y1,left_Z1
        right_X1,right_Y1,right_Z1=To3D(-center_x+right_x1,-center_y+y1,hight,lamda)
        right_X2,right_Y2,right_Z2=To3D(-center_x+right_x2,-center_y+y2,hight,lamda)
        left_vector1=np.array([left_X1,-hight,left_Z1])
        left_vector2=np.array([left_X2,-hight,left_Z2])
        right_vector1=np.array([right_X1,-hight,right_Z1])
        right_vector2=np.array([right_X2,-hight,right_Z2])
        print "vectors"
        print left_vector1,left_vector2,right_vector1,right_vector2
        left_n=np.cross(left_vector2,left_vector1)
        right_n=np.cross(right_vector1,right_vector2)
        print "ns"
        print left_n,right_n
        dic_vector=np.cross(left_n, right_n)
        return dic_vector 
    else:
        return np.array([0,0,0])

def tranaxis(dic,points):
    #align the Zr axis to vector dic
    theta=math.atan(dic_vector[0]/dic_vector[2])
    pothen=math.atan(dic_vector[1]/math.sqrt(dic_vector[2]**2+dic_vector[0]**2))
    Cy=np.array([math.cos(theta),0,math.sin(theta),0],[0,1,0,0],[-math.sin(theta),0,math.cos(theta),0],[0,0,0,1])
    Cx=np.array([1,0,0,0],[0,math.cos(pothen),-math.sin(pothen),0],[0,math.sin(pothen),math.cos(pothen),0],[0,0,0,1])
    C=Cy*Cx
    P=points
    for point in P:
        temp=np.array([point[0],point[1],point[2],0])
        temp=temp*C
        point=temp[0:2]
    return points




seg = cv2.imread("seg1.jpg")
img = cv2.imread("orig1.jpg")
initial_image = img.astype('uint8')
img = filter_colors(seg,img)
#img=cv2.addWeighted(img, 1., img, 1, 0.)
#cv2.imwrite('/home/liu/internship/lighter.jpg',img)
cv2.imwrite('colorfilter.jpg',img)
img = cv2.GaussianBlur(img,(7,7),0)
cv2.imwrite('/home/liu/internship/gaussblur.jpg',img)
img = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
xgrad=cv2.Sobel(img,cv2.CV_16SC1,1,0)
cv2.imwrite('/home/liu/internship/soblex.jpg',xgrad)
ygrad=cv2.Sobel(img,cv2.CV_16SC1,0,1)
cv2.imwrite('/home/liu/internship/sobley.jpg',ygrad)
canny = cv2.Canny(xgrad, ygrad,50, 150)
cv2.imwrite('/home/liu/internship/canny.jpg',canny)

trap_bottom_width = 0.95  # width of bottom edge of trapezoid, expressed as percentage of image width
trap_top_width = 0.6  # ditto for top edge of trapezoid
trap_height = 0.35  # height of the trapezoid expressed as percentage of image height
trap_line = 0.1
imshape = img.shape
vertices = np.array([[\
    (0, imshape[0]*0.97),\
    (0,imshape[0]*(1-trap_line)),\
    ((imshape[1] * (1 - trap_top_width)) // 2,imshape[0] - imshape[0] * trap_height),\
    (imshape[1] - (imshape[1] * (1 - trap_top_width)) // 2, imshape[0] - imshape[0] * trap_height),\
    (imshape[1], imshape[0]*(1-trap_line)),\
    (imshape[1], imshape[0]*0.97)]], dtype=np.int32)

maskedpic=region_of_interest(canny, vertices)
cv2.imwrite('/home/liu/internship/muskedpic.jpg',maskedpic)
#cv2.imshow('Canny', canny)
rho = 3 # distance resolution in pixels of the Hough grid
theta = 0.5 * np.pi/180 # angular resolution in radians of the Hough grid
threshold = 10   # minimum number of votes (intersections in Hough grid cell)
min_line_length = 5 #minimum number of pixels making up a line
max_line_gap = 50   # maximum gap in pixels between connectable line segments

line_image,dic_vector = hough_lines(maskedpic, rho, theta, threshold, min_line_length, max_line_gap,1,3)
cv2.imwrite('/home/liu/internship/line_image.jpg',line_image)
print dic_vector
print math.atan(dic_vector[0]/dic_vector[2])/math.pi*180, math.atan(dic_vector[1]/math.sqrt(dic_vector[2]**2+dic_vector[0]**2))/math.pi*180

annotated_image = weighted_img(line_image, initial_image)
cv2.imwrite('/home/liu/internship/annotated_image.jpg',annotated_image)
#cv2.waitKey(0)
#cv2.destroyAllWindows()