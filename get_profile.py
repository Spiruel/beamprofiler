import Tkinter as tk

import cv2
from PIL import Image, ImageTk
import numpy as np
import time

import matplotlib
matplotlib.use('TkAgg')

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2TkAgg
import matplotlib.pyplot as plt
from matplotlib.figure import Figure

from lib import analysis

root = tk.Tk()
root.bind('<Escape>', lambda e: root.quit())
lmain = tk.Label(root)
lmain.pack()

class Controller(tk.Frame):
    def __init__(self, parent=root, camera_index=0):
        '''Initialises basic variables and GUI elements.'''
        self.start_time = time.time()
        self.angle = 0
        self.camera_index = 0
        self.colourmap = None
        self.centroid = None

        frame = tk.Frame.__init__(self, parent,relief=tk.GROOVE,width=100,height=100,bd=1)
        self.parent = parent
        self.var = tk.IntVar()

        self.parent.title('Laser Beam Profiler')

        labelframe = tk.Frame(self)
        labelframe.pack(side=tk.LEFT) #.grid(row=0, column=0) 
        
        # self.scale1 = tk.Scale(labelframe, label='exposure',
            # from_=1, to=10,
            # length=300, tickinterval=30,
            # showvalue='yes', 
            # orient='horizontal',
            # command = self.change_exp)
        # self.scale1.pack()
        
        self.scale2 = tk.Scale(labelframe, label='gain',
            from_=1, to=10,
            length=300, tickinterval=30,
            showvalue='yes', 
            orient='horizontal',
            command = self.change_gain)
        self.scale2.pack()
        
        self.scale3 = tk.Scale(labelframe, label='rotate',
            from_=0, to=360,
            length=300, tickinterval=30,
            showvalue='yes', 
            orient='horizontal',
            command = self.set_angle)
        self.scale3.pack()

        self.variable = tk.StringVar(labelframe)
        self.variable.set("0")
        self.dropdown1 = tk.OptionMenu(labelframe, self.variable, "0", "1", "2", command = self.change_cam)
        self.dropdown1.pack()
        
        self.variable2 = tk.StringVar(labelframe)
        self.variable2.set("normal")
        self.dropdown2 = tk.OptionMenu(labelframe, self.variable2, "normal", "jet", command = self.change_colourmap)
        self.dropdown2.pack()

        self.exit = tk.Button(labelframe, text = "Exit", command = self.close_window, compound = tk.BOTTOM)
        self.exit.pack()
        
        self.make_fig()
        self.init_camera()
        self.show_frame() #initialise camera

    def make_fig(self):
        '''Creates a matplotlib figure to be placed in the GUI.'''
        # self.fig = Figure(figsize=(4,4), dpi=100) 
        self.fig, self.ax = plt.subplots(2)
        # self.ax.set_ylim(0,255)
        canvas = FigureCanvasTkAgg(self.fig, self) 
        canvas.show() 
        canvas.get_tk_widget().pack() 

        toolbar = NavigationToolbar2TkAgg(canvas, self) 
        toolbar.update() 
        canvas._tkcanvas.pack()
        
    def refresh_plot(self):
        '''Updates the matplotlib figure with new data.'''
        # test = analysis.fix_saturation(self.img)
        
        grayscale = np.array(Image.fromarray(self.img).convert('L'))
        if self.centroid != None:
            self.ax[0].plot(grayscale[self.centroid[1]])
            self.ax[1].plot(grayscale[self.centroid[1]])
        
        # params = analysis.fit_gaussian(grayscale, with_bounds=False)
        # analysis.plot_gaussian(grayscale, params)
        
        # self.ax.set_ylim(0,255)
        self.fig.canvas.draw() 
        self.ax[0].clear()
        self.ax[1].clear()
    
    def change_exp(self, option):
        '''Changes the exposure time of the camera.'''
        exp = float(self.scale1.get())/10000000000000000000000000000000
        print 'changing exp to', exp
        self.cap.set(15, exp)
        
    def change_gain(self, option):
        '''Changes the gain of the camera.'''
        gain = self.scale2.get()
        print 'changing gain to', gain*1000
        self.cap.set(14, gain)

    def init_camera(self):
        '''Initialises the camera with a set resolution.'''
        self.width, self.height = 640, 360
        self.cap = cv2.VideoCapture(self.camera_index)
        if not self.cap:
            raise Exception("Camera not accessible")
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
                  
    def change_cam(self, option):
        '''Switches between camera_indexes and therefore different connected cameras.'''
        if self.camera_index != int(self.variable.get()):
            self.camera_index = int(self.variable.get())
            print 'camera index change, now to update view...', self.camera_index
            self.cap.release()
            self.init_camera()
            self.show_frame()
    
    def change_colourmap(self, option):
        '''Changes the colourmap used in the camera feed.'''
        print 'changed colourmap', option
        if option == 'jet':
            self.colourmap = cv2.COLORMAP_JET
        else:
            self.colourmap = None
    
    def show_frame(self):
        '''Shows camera view with relevant labels and annotations included.'''
        _, frame = self.cap.read()
        # frame = cv2.flip(frame, 1)
        if self.colourmap is None:
            cv2image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGBA)
        else:
            cv2image = cv2.applyColorMap(frame, self.colourmap)
        
        cv2.putText(cv2image,"Laser Beam profiler", (35,40), cv2.FONT_HERSHEY_SIMPLEX, .5, (255,255,255))
        dim = np.shape(cv2image)
        
        # convert to greyscale
        tracking = cv2.cvtColor(frame,cv2.COLOR_BGR2GRAY)
        
        centroid = analysis.find_centroid(tracking)
        if centroid[0] < self.width or centroid[1] < self.height:
            if centroid != (None, None):
                cv2.circle(cv2image,centroid,10,255,thickness=10)
                cv2.putText(cv2image,'Centroid position: ' + str(centroid), (10,310), cv2.FONT_HERSHEY_SIMPLEX, .4, (255,255,255))
                self.centroid = centroid
        else:
            self.centroid = None

        # ellipse = analysis.find_ellipse(tracking)
        # if ellipse != None:
            # print 'ellipse success'
            # cv2.ellipse(cv2image,ellipse,(0,255,0),20)
            
        if self.angle != 0:
            img = self.rotate_image(cv2image)
        else:
            img = Image.fromarray(cv2image)
            
        imgtk = ImageTk.PhotoImage(image=img)
            
        lmain.imgtk = imgtk
        lmain.configure(image=imgtk)
        lmain.after(10, self.show_frame)
        
        self.img = frame
        if time.time() - self.start_time > 1:
            self.refresh_plot()
            self.start_time = time.time()
        
    def set_angle(self, option):
        '''Sets the rotation angle.'''
        self.angle = float(option)
        
    def rotate_image(self, image):
        '''Rotates the given array by the rotation angle, returning as a PIL image.'''
        image_centre = tuple(np.array(image.shape)/2)
        image_centre = (image_centre[0], image_centre[1])
        rot_mat = cv2.getRotationMatrix2D(image_centre,self.angle,1.0)
        result = cv2.warpAffine(image, rot_mat, (image.shape[0], image.shape[1]), flags=cv2.INTER_LINEAR)
        return Image.fromarray(result)
  
    def close_window(self):
        '''Closes the GUI.'''
        self.parent.quit()
        self.parent.destroy()
        
c = Controller(root)
c.pack()
root.mainloop()