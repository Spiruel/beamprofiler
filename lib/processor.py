import Tkinter as tk

import cv2
from PIL import Image, ImageTk
import numpy as np

import matplotlib
matplotlib.use('TkAgg')

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2TkAgg
import matplotlib.pyplot as plt
from matplotlib.figure import Figure

import analysis

root = tk.Tk()
root.bind('<Escape>', lambda e: root.quit())
lmain = tk.Label(root)
lmain.pack()

class Controller(tk.Frame):
    def __init__(self, parent=root, camera_index=0):
        self.angle = 0
        self.camera_index = 2
        self.colourmap = None

        frame = tk.Frame.__init__(self, parent,relief=tk.GROOVE,width=100,height=100,bd=1)
        self.pack()
        self.parent = parent
        # tk.Label(self, text="Control Panel").pack()
        self.var = tk.IntVar()

        self.parent.title('Laser Beam Profiler')
        
        labelframe = tk.LabelFrame(parent, text="This is a LabelFrame")
        labelframe.pack(fill="both", expand="yes") #.grid(row=0, column=0) 
        
        # self.scale1 = tk.Scale(labelframe, label='exposure',
            # from_=1, to=10,
            # length=300, tickinterval=30,
            # showvalue='yes', 
            # orient='horizontal',
            # command = self.change_exp)
        # self.scale1.pack()
        
        # self.scale2 = tk.Scale(labelframe, label='gain',
            # from_=1, to=10,
            # length=300, tickinterval=30,
            # showvalue='yes', 
            # orient='horizontal',
            # command = self.change_gain)
        # self.scale2.pack()
        
        # self.scale3 = tk.Scale(labelframe, label='rotate',
            # from_=0, to=360,
            # length=300, tickinterval=30,
            # showvalue='yes', 
            # orient='horizontal',
            # command = self.set_angle)
        # self.scale3.pack()

        # self.variable = tk.StringVar(labelframe)
        # self.variable.set("0")
        # self.dropdown1 = tk.OptionMenu(labelframe, self.variable, "0", "1", "2", command = self.change_cam)
        # self.dropdown1.pack()
        
        # self.variable2 = tk.StringVar(labelframe)
        # self.variable2.set("normal")
        # self.dropdown2 = tk.OptionMenu(labelframe, self.variable2, "normal", "jet", command = self.change_colourmap)
        # self.dropdown2.pack()

        self.plot = tk.Button(labelframe, text = "Plot", command = self.refresh_plot)
        self.plot.pack()
        self.exit = tk.Button(labelframe, text = "Exit", command = self.close_window, compound = tk.BOTTOM)
        self.exit.pack()

        self.init_camera()
        self.show_frame() #initialise camera
        self.make_fig()
        
    def make_fig(self):
        self.fig = Figure(figsize=(4,4), dpi=100) 
        self.ax = self.fig.add_subplot(111) 

        canvas = FigureCanvasTkAgg(self.fig, self) 
        canvas.show() 
        canvas.get_tk_widget().pack(side=tk.BOTTOM, fill=tk.BOTH, expand=True) 

        toolbar = NavigationToolbar2TkAgg(canvas, self) 
        toolbar.update() 
        canvas._tkcanvas.pack(side=tk.BOTTOM, fill=tk.BOTH, expand=True)
        
    def refresh_plot(self):
        self.ax.plot(self.img[0])
        self.fig.canvas.draw() 
        self.ax.clear()
        print 'updated plot'
    
    def change_exp(self, option):
        exp = float(self.scale1.get())/1000000
        print 'changing exp to', exp
        self.cap.set(15, exp)
        
    def change_gain(self, option):
        gain = self.scale2.get()
        print 'changing gain to', gain*1000
        self.cap.set(14, gain)

    def init_camera(self):
        width, height = 400, 300
        self.cap = cv2.VideoCapture(self.camera_index)
        if not self.cap:
            raise Exception("Camera not accessible")
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
                  
    def change_cam(self, option):
        if self.camera_index != int(self.variable.get()):
            self.camera_index = int(self.variable.get())
            print 'camera index change, now to update view...', self.camera_index
            self.cap.release()
            self.init_camera()
            self.show_frame()
    
    def change_colourmap(self, option):
        print 'changed colourmap', option
        if option == 'jet':
            self.colourmap = cv2.COLORMAP_JET
        else:
            self.colourmap = None
    
    def show_frame(self):
        _, frame = self.cap.read()
        # frame = cv2.flip(frame, 1)
        if self.colourmap is None:
            cv2image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGBA)
        else:
            cv2image = cv2.applyColorMap(frame, self.colourmap)
        
        cv2.putText(cv2image,"Laser Beam profiler", (50,50), cv2.FONT_HERSHEY_SIMPLEX, 1, (255,255,255))
        dim = np.shape(cv2image)
        
        centroid = analysis.find_centroid(frame)
        if centroid != (None, None):
            cv2.circle(cv2image,centroid,10,255,thickness=10)

        img = Image.fromarray(cv2image)
        if self.angle != 0:
            img = self.rotate_image(img)
            
        imgtk = ImageTk.PhotoImage(image=img)
            
        lmain.imgtk = imgtk
        lmain.configure(image=imgtk)
        lmain.after(10, self.show_frame)
        
        self.img = frame
        
    def set_angle(self, option):
        self.angle = float(option)
        
    def rotate_image(self, image):
        return np.rot90(image, self.angle)
        image_centre = tuple(np.array(image.shape)/2)
        image_centre = (image_centre[0], image_centre[1])
        rot_mat = cv2.getRotationMatrix2D(image_centre,self.angle,1.0)
        result = cv2.warpAffine(image, rot_mat, (image.shape[0], image.shape[1]), flags=cv2.INTER_LINEAR)
        return result
  
    def close_window(self): 
        self.parent.quit()
        self.parent.destroy()
        