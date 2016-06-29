import cv2
import numpy as np

def find_centroid(frame):
    
    kernel = np.ones((5,5),np.uint8)

    #These values work well 
    gmn = 240
    gmx = 255

    #initialise centroid variables for later in programme
    cx = 0
    cy = 0

    # convert to greyscale
    tracking = cv2.cvtColor(frame,cv2.COLOR_BGR2GRAY)

    #apply thresholding to greyscale frames. 
    #inRange checks if array elements lie between the elements of two other arrays
    gthresh = cv2.inRange(np.array(tracking),np.array(gmn),np.array(gmx))

    # Some morphological filtering
    dilation = cv2.dilate(tracking,kernel,iterations = 2)
    closing = cv2.morphologyEx(dilation, cv2.MORPH_CLOSE, kernel)
    closing = cv2.Canny(closing, 50, 200)

    # find contours in the threshold image
    _,contours,hierarchy = cv2.findContours(closing,cv2.RETR_LIST,cv2.CHAIN_APPROX_TC89_L1)

    # finding contour with maximum area and store it as best_cent
    max_area = 0

    for cent in contours:
        area = cv2.contourArea(cent)
        if area > max_area:
            max_area = area
            best_cent = cent

            # finding centroids of best_cent and draw a circle there
            M = cv2.moments(best_cent)
            cx,cy = int(M['m10']/M['m00']), int(M['m01']/M['m00'])
            break
    else:
        cx = None
        cy = None
        
    centroid = (cx, cy)

    return centroid