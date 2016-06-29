# This program detects a laser and calculates the centroid coordinates in pixels.


import cv2
import numpy as np
# import cv2.cv as cv
#trying to stop program after 20 seconds
import time

kernel = np.ones((5,5),np.uint8)

# create video capture
cap = cv2.VideoCapture(2)

# Reduce the size of video to 320x240 so rpi can process faster
# cap.se=,480)

def nothing(x):
    pass
# Creating a windows for later use
# cv2.namedWindow('closing')
cv2.namedWindow('tracking')

# gr
#These values work well and are consistent with laser position.
gmn = 240
gmx = 255

#initialize centroid variables for later in program
cx = 0
cy = 0

start_time = time.time() #remember when we started
max_time = start_time + int(20)

while(1):#(max_time) > time.time()  :  #for infinite, set while(1):

    # read the frames
    _,frame = cap.read()

    # convert to grayscale
    tracking = cv2.cvtColor(frame,cv2.COLOR_BGR2GRAY)

    #apply thresholding to grayscale frames. 
    #inRange checks if array elements lie between the elements of two other arrays
    gthresh = cv2.inRange(np.array(tracking),np.array(gmn),np.array(gmx))

    # Some morpholigical filtering
    dilation = cv2.dilate(tracking,kernel,iterations = 2)
    closing = cv2.morphologyEx(dilation, cv2.MORPH_CLOSE, kernel)
    closing = cv2.Canny(closing, 50, 200)

    # find contours in the threshold image
    _,contours,hierarchy = cv2.findContours(closing,cv2.RETR_LIST,cv2.CHAIN_APPROX_TC89_L1)

    # finding contour with maximum area and store it as best_cnt
    max_area = 0
    for cnt in contours:
        area = cv2.contourArea(cnt)
        if area > max_area:
            max_area = area
            best_cnt = cnt
            
    
            # finding centroids of best_cnt and draw a circle there
            M = cv2.moments(best_cnt)
            cx,cy = int(M['m10']/M['m00']), int(M['m01']/M['m00'])
            cv2.circle(frame,(cx,cy),10,255,thickness=10)
            print cx, cy   #print centroid coordinates
            break
    else:
        cx = 'value not found'
        cy = 'value also not found'

    # Show it, if key pressed is 'Esc', exit the loop
    cv2.imshow('tracking',frame)
    # cv2.imshow('closing', closing)
    if cv2.waitKey(33)== 27:
        break

print cx

# Clean up everything before leaving
cv2.destroyAllWindows()
cap.release()