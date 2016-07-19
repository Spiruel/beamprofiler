import cv2
import numpy as np

import scipy.optimize as opt

import matplotlib.pyplot as plt
from matplotlib import cm
from matplotlib.patches import Circle
from scipy import ndimage

import copy

from PIL import Image
import threading

class Analyse(threading.Thread):
    def __init__(self, master):
        threading.Thread.__init__(self)
        self.master = master       
        
    def get_centroid(self):
        # function finds centroid of a white laserspot within a dark background
        # using fourier algorithm in a two dimensional grayscale image
        # Function translated from Matlab 
        # Credit: Rainer F., knallkopf66@uboot.com, Dec. 2004
        
        img = np.matrix(self.master.analysis_frame)
        rbnd, cbnd = img.shape

        i = np.matrix(np.arange(0, rbnd))
        sin_a = np.sin((i-1)*2*np.pi / (rbnd-1))
        cos_a = np.cos((i-1)*2*np.pi / (rbnd-1))

        j = np.matrix(np.arange(0, cbnd)).transpose()
        sin_b = np.sin((j-1)*2*np.pi / (cbnd-1))
        cos_b = np.cos((j-1)*2*np.pi / (cbnd-1))

        a = (cos_a * img).sum()
        b = (sin_a * img).sum()
        c = (img * cos_b).sum()
        d = (img * sin_b).sum()

        if a>0:
            if b>0:
                rphi = 0
            else:
                rphi = 2*np.pi
        else:
            rphi = np.pi

        if c>0:
            if d>0:
                cphi = 0
            else:
                cphi = 2*np.pi
        else:
            cphi = np.pi

        try:
            fract1 = b/a
            frac2 = d/c
        except RuntimeWarning:
            print 'Could not find centroid!'
            return (np.nan, np.nan)
            
        x = (np.arctan(b/a) + rphi) * (rbnd - 1)/(2*np.pi) + 1
        y = (np.arctan(d/c) + cphi) * (cbnd - 1)/(2*np.pi) + 1

        com = (y, x)
        return com
        
    def find_centroid(self):
        '''Takes greyscale cv2 image and finds one centroid position.'''
        kernel = np.ones((5,5),np.uint8)

        #These values work well 
        gmn = 240
        gmx = 255

        #initialise centroid variables for later in programme
        cx = 0
        cy = 0

        #apply thresholding to greyscale frames. 
        #inRange checks if array elements lie between the elements of two other arrays
        gthresh = cv2.inRange(np.array(self.master.analysis_frame),np.array(gmn),np.array(gmx))

        # Some morphological filtering
        dilation = cv2.dilate(self.master.analysis_frame,kernel,iterations = 2)
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
            cx = np.nan
            cy = np.nan
            
        centroid = (cx, cy)
        
        return centroid
        
    def find_ellipses(self):
            ellipses = np.array([])
            ret,thresh = cv2.threshold(self.master.analysis_frame,127,255,0)
            _,contours,hierarchy = cv2.findContours(thresh, 1, 2)
            
            if len(contours) != 0:
                for cont in contours:
                    if len(cont) < 5:
                        break
                    elps = cv2.fitEllipse(cont)
                    # ellipses = np.append(ellipses, elps)
                    return elps  #only returns one ellipse. Should it return more?
            return None
                            
    # 2D Gaussian model
    def func(self, xy, x0, y0, sigma, H):

        x, y = xy

        A = 1 / (2 * sigma**2)
        I = H * np.exp(-A * ( (x - x0)**2 + (y - y0)**2))
        return I
        
    def fit_gaussian(self, with_bounds):
        size = 50
        x, y = self.master.peak_cross
        self.crop_img = self.master.analysis_frame[y-size/2:y+size/2, x-size/2:x+size/2]
                
        # Prepare fitting
        x = np.arange(0, self.crop_img.shape[1], 1)
        y = np.arange(0, self.crop_img.shape[0], 1)
        xx, yy = np.meshgrid(x, y)

        # Guess initial parameters
        x0 = int(self.crop_img.shape[0])/2 # Middle of the image
        y0 = int(self.crop_img.shape[1])/2 # Middle of the image
        sigma = max(*self.crop_img.shape) * 0.1 # 10% of the image

        H = np.max(self.crop_img) # Maximum value of the image
        initial_guess = [x0, y0, sigma, H]

        # Constraints of the parameters
        if with_bounds:
            lower = [0, 0, 0, 0]
            upper = [self.crop_img.shape[0], self.crop_img.shape[1], self.crop_img(*self.crop_img.shape), self.crop_img.max() * 2]
            bounds = [lower, upper]
        else:
            bounds = [-np.inf, np.inf]

        try:
            pred_params, uncert_cov = opt.curve_fit(self.func, (xx.ravel(), yy.ravel()), self.crop_img.ravel(),
                                            p0=initial_guess, bounds=bounds)
        except:
            pred_params, uncert_cov = [[0,0,1], [0,0,1]]

        # Get residual
        predictions = self.func((xx, yy), *pred_params)
        rms = np.sqrt(np.mean((self.crop_img.ravel() - predictions.ravel())**2))

        # print("True params : ", true_parameters)
        # print("Predicted params : ", pred_params)
        # print("Residual : ", rms)

        return pred_params

    def plot_gaussian(self, ax, params):           
        if self.master.colourmap is None:
            cmap=plt.cm.BrBG
        elif self.master.colourmap == 2:
            cmap=plt.cm.jet
        elif self.master.colourmap == 0:
            cmap=plt.cm.autumn
        elif self.master.colourmap == 1:
            cmap=plt.cm.bone
        
        ax.imshow(self.crop_img, cmap=cmap, interpolation='nearest', origin='lower')

        # ax.scatter(params[0], params[1], s=100, c="red", marker="x")

        circle = Circle((params[0], params[1]), params[2], facecolor='none',
                edgecolor="red", linewidth=1, alpha=0.8)
        ax.add_patch(circle)
        
    def get_max(self, alpha=20,size=10):
        sigma = np.std(self.master.analysis_frame)
        i_out = []
        j_out = []
        image_temp = copy.deepcopy(self.master.analysis_frame)
        while True:
            k = np.argmax(image_temp)
            j,i = np.unravel_index(k, image_temp.shape)
            if(image_temp[j,i] >= alpha*sigma):
                i_out.append(i)
                j_out.append(j)
                x = np.arange(i-size, i+size)
                y = np.arange(j-size, j+size)
                xv,yv = np.meshgrid(x,y)
                image_temp[yv.clip(0,image_temp.shape[0]-1),
                                       xv.clip(0,image_temp.shape[1]-1) ] = 0
            else:
                break
        return i_out,j_out
        
    def get_ellipse_coords(self, a=0.0, b=0.0, x=0.0, y=0.0, angle=0.0, k=2):
        """ Draws an ellipse using (360*k + 1) discrete points; based on pseudo code
        given at http://en.wikipedia.org/wiki/Ellipse
        k = 1 means 361 points (degree by degree)
        a = major axis distance,
        b = minor axis distance,
        x = offset along the x-axis
        y = offset along the y-axis
        angle = clockwise rotation [in degrees] of the ellipse;
            * angle=0  : the ellipse is aligned with the positive x-axis
            * angle=30 : rotated 30 degrees clockwise from positive x-axis
        """
        pts = np.zeros((360*k+1, 2))

        beta = -angle * np.pi/180.0
        sin_beta = np.sin(beta)
        cos_beta = np.cos(beta)
        alpha = np.radians(np.r_[0.:360.:1j*(360*k+1)])
     
        sin_alpha = np.sin(alpha)
        cos_alpha = np.cos(alpha)
        
        pts[:, 0] = x + (a * cos_alpha * cos_beta - b * sin_alpha * sin_beta)
        pts[:, 1] = y + (a * cos_alpha * sin_beta + b * sin_alpha * cos_beta)

        return pts
        
    def get_beam_width(self, centroid):
        image = np.array(Image.fromarray(self.master.analysis_frame).convert('L')) #should be passed in grayscale as analysis frame. need to fix
        height, width = image.shape[0:2]
        
        if centroid is None: 
            return None
            
        cent_x, cent_y = centroid
        if cent_x >= width:
            return None
        if cent_y >= height:
            return None
            
        x = np.linspace(0, width, width)
        y = np.linspace(height, 0, height)
        xs, ys = np.meshgrid(x,y)
        
        sig_x = np.sqrt(np.sum((xs-centroid[0])**2 * image) / np.sum(image))
        sig_y = np.sqrt(np.sum((ys-centroid[1])**2 * image) / np.sum(image))

        return (4*sig_x, 4*sig_y)