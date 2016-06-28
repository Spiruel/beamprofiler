import Tkinter as tk

import cv2
from PIL import Image, ImageTk
import numpy as np

import matplotlib
matplotlib.use('TkAgg')

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2TkAgg
import matplotlib.pyplot as plt
from matplotlib.figure import Figure

root = tk.Tk()
root.bind('<Escape>', lambda e: root.quit())
lmain = tk.Label(root)
lmain.pack()

class Controller(tk.Frame):
    def __init__(self, parent=root, camera_index=0):
        self.camera_index = 2
        self.colourmap = None

        self.init_camera()
        self.show_frame() #initialise camera
        
        tk.Frame.__init__(self, parent)
        self.pack()
        self.parent = parent
        # tk.Label(self, text="Control Panel").pack()
        self.var = tk.IntVar()
        
        # self.scale1 = tk.Scale(self, label='exposure',
            # from_=1, to=10,
            # length=300, tickinterval=30,
            # showvalue='yes', 
            # orient='horizontal')
        # self.scale1.pack()
        # self.button1 = tk.Button(self, text = "Select", command = self.change_exp)
        # self.button1.pack()
        
        # self.scale2 = tk.Scale(self, label='gain',
            # from_=1, to=10,
            # length=300, tickinterval=30,
            # showvalue='yes', 
            # orient='horizontal')
        # self.scale2.pack()
        # self.button2 = tk.Button(self, text = "Select", command = self.change_gain)
        # self.button2.pack()

        self.variable = tk.StringVar(parent)
        self.variable.set("one")
        self.dropdown1 = tk.OptionMenu(parent, self.variable, "0", "1", "2")
        self.dropdown1.pack()
        self.button3 = tk.Button(self, text = "Select", command = self.change_cam)
        self.button3.pack()
        
        self.variable2 = tk.StringVar(parent)
        self.variable2.set("normal")
        self.dropdown2 = tk.OptionMenu(parent, self.variable2, "normal", "jet", command = self.change_colourmap)
        self.dropdown2.pack()

        self.parent.title('Laser Beam Profiler')
        
        self.plot = tk.Button(self, text = "Plot", command = self.refresh_plot)
        self.plot.pack()
        self.exit = tk.Button(self, text = "Exit", command = self.close_window, compound = tk.BOTTOM)
        self.exit.pack()

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
    
    def change_exp(self):
        exp = float(self.scale1.get())/1000000
        print 'changing exp to', exp
        cap.set(15, exp)
        
    def change_gain(self):
        gain = self.scale2.get()
        print 'changing gain to', gain*1000
        self.camera.set(14, gain)

    def init_camera(self):
        width, height = 400, 300
        self.cap = cv2.VideoCapture(self.camera_index)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
                  
    def change_cam(self):
        if self.camera_index != int(self.variable.get()):
            self.camera_index = int(self.variable.get())
            print 'camera index change, now to update view...', self.camera_index, type(self.camera_index)
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
        cv2.circle(cv2image, (dim[0]/2, dim[1]/2), 20, (255,255,255), thickness = 2)

        img = Image.fromarray(cv2image)
        imgtk = ImageTk.PhotoImage(image=img)
            
        lmain.imgtk = imgtk
        lmain.configure(image=imgtk)
        lmain.after(10, self.show_frame)
        
        self.img = frame
        
    def close_window(self): 
        self.parent.quit()
        self.parent.destroy()
        