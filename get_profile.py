import Tkinter as tk

import cv2
from PIL import Image, ImageTk
import numpy as np
import time
import sys

import matplotlib
matplotlib.use('TkAgg')

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2TkAgg
import matplotlib.pyplot as plt
from matplotlib.figure import Figure

from lib import analysis
from lib import output

root = tk.Tk()
lmain = tk.Label(root)
lmain.pack()

class Controller(tk.Frame):
    def __init__(self, parent=root, camera_index=0):
        '''Initialises basic variables and GUI elements.'''
        self.running_time = np.array([])
        self.plot_time = time.time()
        self.angle = 0
        self.camera_index = 0
        self.centroid = None
        self.colourmap = None
        self.fig_type = 'cross profile'
        self.counter = 0
        self.centroid_hist_x, self.centroid_hist_y = np.array([]), np.array([])

        frame = tk.Frame.__init__(self, parent,relief=tk.GROOVE,width=100,height=100,bd=1)
        self.parent = parent
        self.var = tk.IntVar()

        self.parent.title('Laser Beam Profiler')
        
        ###################################################################NAVBAR
        menubar = tk.Menu(self.parent)
        fileMenu = tk.Menu(menubar, tearoff=0)
        fileMenu.add_command(label="Export Data", command=self.save_csv)
        fileMenu.add_separator()
        fileMenu.add_command(label="Quit", command=self.close_window)
        menubar.add_cascade(label="File", menu=fileMenu)
        
        controlMenu = tk.Menu(menubar, tearoff=0)
        submenu = tk.Menu(controlMenu, tearoff=0)
        submenu.add_command(label="0", command= lambda: self.change_cam(0))
        submenu.add_command(label="1", command= lambda: self.change_cam(1))
        submenu.add_command(label="2", command= lambda: self.change_cam(2))
        controlMenu.add_cascade(label='Change Camera', menu=submenu, underline=0)
        controlMenu.add_separator()
        controlMenu.add_command(label="Clear Windows")
        menubar.add_cascade(label="Control", menu=controlMenu)

        imageMenu = tk.Menu(menubar, tearoff=0)       
        imageMenu.add_command(label="Take Screenshot", command=self.save_screenshot)
        imageMenu.add_command(label="Take Video /10 s", command=lambda: self.save_video(10))
        imageMenu.add_separator()
        submenu = tk.Menu(imageMenu, tearoff=0)
        submenu.add_command(label="Normal", command= lambda: self.change_colourmap('normal'))
        submenu.add_command(label="Jet", command= lambda: self.change_colourmap('jet'))
        submenu.add_command(label="Autumn", command=lambda: self.change_colourmap('autumn'))
        submenu.add_command(label="Bone", command=lambda: self.change_colourmap('bone'))
        imageMenu.add_cascade(label='Change Colourmap', menu=submenu, underline=0)
        
        menubar.add_cascade(label="Image", underline=0, menu=imageMenu)        
        
        helpmenu = tk.Menu(menubar, tearoff=0)
        helpmenu.add_command(label="About", command=lambda: self.info_window("Laser Beam Profiler created by Samuel Bancroft \n Summer 2016 Internship Project \n Supervisor: Dr Jon Goldwin, Birmingham University"))
        menubar.add_cascade(label="Help", menu=helpmenu)

        self.parent.config(menu=menubar)
        ###################################################################NAVBAR

        self.colourmap = None
        
        labelframe = tk.Frame(self)
        labelframe.pack(side=tk.LEFT) #.grid(row=0, column=0) 
        
        self.scale1 = tk.Scale(labelframe, label='exposure',
            from_=-1000000000, to=-10000,
            length=300, tickinterval=10000,
            showvalue='yes', 
            orient='horizontal',
            command = self.change_exp)
        self.scale1.pack()
        
        self.scale2 = tk.Scale(labelframe, label='gain',
            from_=-10000, to=10000,
            length=300, tickinterval=1,
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
        
        self.variable3 = tk.StringVar(labelframe)
        self.variable3.set("cross profile")
        self.dropdown3 = tk.OptionMenu(labelframe, self.variable3, "cross profile", "2d gaussian fit", "beam stability", "centroid time", command = self.change_fig)
        self.dropdown3.pack()
        
        b = tk.Button(labelframe, text="Sound", command=lambda: output.main())
        b.pack(fill=tk.BOTH)

        self.make_fig()
        self.init_camera()
        self.show_frame() #initialise camera

    def make_fig(self):
        '''Creates a matplotlib figure to be placed in the GUI.'''
        plt.clf()
        plt.cla()
        
        if self.fig_type == 'cross profile':
            self.fig, self.ax = plt.subplots(1,2, gridspec_kw = {'width_ratios':[16, 9]})
        elif self.fig_type == '2d gaussian fit':
            self.fig = Figure(figsize=(4,4), dpi=100)
        elif self.fig_type == 'beam stability':
            self.fig = Figure(figsize=(4,4), dpi=100)
        elif self.fig_type == 'centroid_time':
            self.fig = Figure(figsize=(4,4), dpi=100)

        # self.ax.set_ylim(0,255)
        canvas = FigureCanvasTkAgg(self.fig, self) 
        canvas.show() 
        canvas.get_tk_widget().pack() 

        toolbar = NavigationToolbar2TkAgg(canvas, self) 
        toolbar.update() 
        canvas._tkcanvas.pack()
        
    def refresh_plot(self):
        '''Updates the matplotlib figure with new data.'''
        grayscale = np.array(Image.fromarray(self.img).convert('L'))
        
        if self.fig_type == 'cross profile':
            if self.centroid != None:
                print 'beam width:', 4*np.std(grayscale[self.centroid[1],:]),4*np.std(grayscale[:,self.centroid[0]])
                self.ax[0].plot(range(self.width), grayscale[self.centroid[1],:],'k-')
                self.ax[1].plot(grayscale[:,self.centroid[0]], range(self.height),'k-')
                
                self.ax[0].set_xlim(0,self.width)
                self.ax[0].set_ylim(0,255)
                
                self.ax[1].set_xlim(0,255)
                self.ax[1].set_ylim(self.height,0)              
        elif self.fig_type == '2d gaussian fit':
            if self.centroid != None:
                size = 50
                x, y = self.centroid
                img = grayscale[y-size/2:y+size/2, x-size/2:x+size/2]
                params = analysis.fit_gaussian(img, with_bounds=False)
                analysis.plot_gaussian(plt.gca(), img, params)
        elif self.fig_type == 'beam stability':
            plt.plot(self.centroid_hist_x, self.centroid_hist_y)
            plt.xlim(0, self.width)
            plt.ylim(self.height, 0)
        elif self.fig_type == 'centroid time':
            plt.plot(self.running_time-self.running_time[0], self.centroid_hist_x, 'y-', label='centroid x coordinate')
            plt.plot(self.running_time-self.running_time[0], self.centroid_hist_y, 'r-', label='centroid y coordinate')
            if self.running_time[-1] - self.running_time[0] <= 60:
                plt.xlim(0, 60)
            else:
                index = np.searchsorted(self.running_time,[self.running_time[-1]-60,],side='right')[0]
                plt.xlim(self.running_time[index]-self.running_time[0], self.running_time[-1]-self.running_time[0])
            plt.legend(frameon=False)
            
        # self.ax[0].hold(True)
        # self.ax[1].hold(True)
        self.fig.canvas.draw() 
        
        for axis in self.fig.get_axes():
            axis.clear()
    
    def change_fig(self, option):
        '''Changes the fig used.'''
        if self.fig_type != option:
            print 'changed fig', option
            self.fig_type = option
            plt.cla()
            plt.clf()
            
    def change_exp(self, option):
        '''Changes the exposure time of the camera.'''
        exp = float(option)
        print 'changing exp to', exp
        self.cap.set(15, exp)
        
    def change_gain(self, option):
        '''Changes the gain of the camera.'''
        gain = float(option)
        print 'changing gain to', gain
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
        if self.camera_index != option and type(option) == int:
            self.camera_index = int(option)
            print 'camera index change, now to update view...', self.camera_index
            self.cap.release()
            self.init_camera()
            self.show_frame()
    
    def change_colourmap(self, option):
        '''Changes the colourmap used in the camera feed.'''
        if self.colourmap != option:
            print 'changed colourmap', option
            if option.lower() == 'jet':
                self.colourmap = cv2.COLORMAP_JET
            elif option.lower() == 'autumn':
                self.colourmap = cv2.COLORMAP_AUTUMN
            elif option.lower() == 'bone':
                self.colourmap = cv2.COLORMAP_BONE
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
        
        cv2.putText(cv2image,"Laser Beam profiler", (10,40), cv2.FONT_HERSHEY_PLAIN, 1, (255,255,255))
        dim = np.shape(cv2image)
        
        # convert to greyscale
        tracking = cv2.cvtColor(frame,cv2.COLOR_BGR2GRAY)
        
        # too intensive at the moment...
        # cv2.putText(cv2image,'Peak Value: ' + str(np.max(tracking)) + str(analysis.get_max(tracking,3)), (10,325), cv2.FONT_HERSHEY_PLAIN, 1, (255,255,255))
        
        cv2.putText(cv2image,'Peak Value: ' + str(np.max(tracking)), (10,325), cv2.FONT_HERSHEY_PLAIN, 1, (255,255,255))
        
        centroid = analysis.find_centroid(tracking)
        if centroid[0] < self.width or centroid[1] < self.height:
            if centroid != (None, None):
                # cv2.circle(cv2image,centroid,10,255,thickness=10)
                cv2.putText(cv2image,'Centroid position: ' + str(centroid), (10,310), cv2.FONT_HERSHEY_PLAIN, 1, (255,255,255))
                self.centroid = centroid
                
                cv2.line(cv2image, (0, centroid[1]), (self.width, centroid[1]), 255, thickness=1)
                cv2.line(cv2image, (centroid[0], 0), (centroid[0], self.height), 255, thickness=1)
                
            else:
                self.centroid = None
            self.centroid_hist_x, self.centroid_hist_y = np.append(self.centroid_hist_x, centroid[0]), np.append(self.centroid_hist_y, centroid[1])
            self.running_time = np.append(self.running_time, time.time())
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
        if time.time() - self.plot_time > 1:
            self.refresh_plot()
            self.plot_time = time.time()
        
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
        on_closing()
        
    def info_window(self, info):
        self.counter += 1
        t = tk.Toplevel(self)
        t.wm_title("Window #%s" % self.counter)
        l = tk.Label(t, text=info)
        # l = tk.Label(t, text="This is window #%s" % self.counter)
        l.pack(side="top", fill="both", expand=True, padx=100, pady=100)
       
    def save_screenshot(self):
        cv2.imwrite('output.png', self.img)
        
    def save_video(self, wait):
        start = time.time()
        fourcc = cv2.VideoWriter_fourcc('X', 'V', 'I', 'D')
        while wait < time.time() - start:
            video_writer = cv2.VideoWriter("output.avi", fourcc, 20, (680, 480))
        video_writer.release()
        
    def save_csv(self):
        output = np.column_stack((self.running_time.flatten(),self.centroid_hist_x.flatten(),self.centroid_hist_y.flatten()))
        np.savetxt('output.dat',output,delimiter=',')
        
c = Controller(root)
c.pack()

def on_closing():
        '''Closes the GUI.'''
        root.quit()
        root.destroy()
        c.cap.release()
        cv2.destroyAllWindows()
        
root.protocol("WM_DELETE_WINDOW", on_closing)
root.mainloop()