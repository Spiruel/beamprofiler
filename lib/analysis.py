import cv2
import numpy as np

def find_centroid(frame):
    
    kernel = np.ones((5,5),np.uint8)

    # gr
    #These values work well and are consistent with laser position.
    gmn = 240
    gmx = 255

    #initialize centroid variables for later in program
    cx = 0
    cy = 0

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
            # cv2.circle(frame,(cx,cy),10,255,thickness=10)
            break
    else:
        cx = None
        cy = None
        
    centroid = (cx, cy)

    return centroid
