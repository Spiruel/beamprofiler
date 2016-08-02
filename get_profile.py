#!/usr/bin/python
# -*- coding: latin-1 -*-
          
from utils.results import WorkspaceManager
from utils import analysis, output, interface

try:
    import ConfigParser
except ImportError:
    import configparser as ConfigParser

try:
    # for Python2
    import Tkinter as tk
    import ttk
    import tkFileDialog, tkMessageBox
except ImportError:
    # for Python3
    import tkinter as tk
    import tkinter.ttk as ttk
    from tkinter import messagebox as tkMessageBox
    from tkinter import filedialog as tkFileDialog

import cv2
from PIL import Image, ImageTk
import numpy as np
import time
import math

from mpl_toolkits.mplot3d import Axes3D
from scipy.optimize import curve_fit
from scipy.ndimage.interpolation import zoom
                
# import matplotlib
# matplotlib.use('TkAgg')

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2TkAgg
import matplotlib.pyplot as plt
from matplotlib.ticker import MultipleLocator, FormatStrFormatter

from functools import partial
from threading import Thread
from time import sleep

def clear_capture(capture):
    capture.release()
    cv2.destroyAllWindows()

def count_cameras():
    n = 0
    for i in range(7):
        try:
	    cap = cv2.VideoCapture(i)
	    ret, frame = cap.read()
	    cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
	    clear_capture(cap)
	    n += 1
        except:
	    clear_capture(cap)
	    break
    return n

def on_closing(controller):
    '''Closes the GUI.'''
    controller.parent.quit()
    controller.parent.destroy()
    clear_capture(controller.cap)

class SplashScreen(Thread): 
    def __init__(self, parent):
        self.parent = parent
        self.window = tk.Toplevel(parent)
        self.window.overrideredirect(True)
        self.setSplash() 
        self.setWindow()
        self.window.update()

    def close(self):
        self.window.destroy()

    def setSplash(self):
        if np.random.randint(1, 100) <= 1:
            self.picture = Image.open('images/bilbo.png')
        else:
            self.picture = Image.open('images/splash.png')
        self.imgSplash = ImageTk.PhotoImage(self.picture)

    def setWindow(self):
        width, height = self.picture.size 
        halfwidth = (self.parent.winfo_screenwidth()-width)//2 
        halfheight = (self.parent.winfo_screenheight()-height)//2
        self.window.geometry("%ix%i+%i+%i" %(width, height, halfwidth,halfheight))
        tk.Label(self.window, image=self.imgSplash).pack()
            
class Application: 
    def load_application(self):
        self.camera_count = count_cameras()

    def load(self):
        root = tk.Tk()

        splash_screen = SplashScreen(root)

        print("Loaded splashscreen")

        loader_thread = Thread(target = self.load_application)
        loader_thread.start()

        w, h = root.winfo_screenwidth(), root.winfo_screenheight()
        root.geometry("%dx%d+0+0" % (w, h))
        control = Controller(root)
        control.pack()

        root.bind('<space>', lambda e: control.profiler_active(option=True))
        root.protocol("WM_DELETE_WINDOW", partial(on_closing, control))

        loader_thread.join()
        print("Done loading stuff")

        if self.camera_count == 0:
            print('No webcam found!')
            raise SystemExit(0)

        control.init_camera() #initialise camera
        control.show_frame() #show video feed and update view with new information and refreshed plot etc

        control.load_camera_menu(self.camera_count)
        control.load_workspace()
        w, h = control.parent.winfo_screenwidth(), control.parent.winfo_screenwidth()
        control.parent.minsize(w,95)
        control.parent.geometry('%dx%d+%d+%d' % (2*w, 95, -6, 2)) #geometry of the main window
        
        print("Loaded application. Closing splashscreen")
        splash_screen.close()
        print('Showing main window and starting application loop')
        root.deiconify()
        root.mainloop()
        
class Controller(tk.Frame, WorkspaceManager):
    def __init__(self, parent):
        '''Initialises basic variables and GUI elements.'''
        parent.withdraw()

        self.lmain = tk.Label(parent)
        self.lmain.pack()
        
        self.profiler_state = tk.IntVar() #for profiler state
        self.active = False #whether profiler is active or just looking at webcam view
        self.logs = [] #system logs
        
        self.info_frame = None
        self.config_frame = None
        self.passfail_frame = None
        self.systemlog_frame = None
        self.toolbarconfig_frame = None
        self.webcam_frame = None
        self.plot_frames = []
        self.pause_delay = 0 #time delay for when profiler is inactive. cumulatively adds.
        self.last_pause = time.time() #last time profiler was inactive

        self.plot_time = self.last_pause  #various parameters ters used throughout the profiler are initialised here
        self.angle = 0.0 #setting initial angles, region of interest, exposure time etc
        self.roi = 1
        self.exp = -1
        self.toolbarbuttons = [] #active buttons on the toolbar
        self.toolbaractions = {'x cross profile': ['x cross profile', tk.PhotoImage(file='images/x_profile.gif').subsample(2, 2)], #accessible images for toolbarbuttons
                              'y cross profile': ['y cross profile', tk.PhotoImage(file='images/y_profile.gif').subsample(2, 2)],
                              '2d profile': ['2d profile', tk.PhotoImage(file='images/2d_profile.gif').subsample(2, 2)],
                              '2d surface': ['2d surface', tk.PhotoImage(file='images/3d_profile.gif').subsample(2, 2)],
                              'plot positions': ['positions', tk.PhotoImage(file='images/positions.gif').subsample(2, 2)],
                              'beam stability': ['beam stability', tk.PhotoImage(file='images/beam_stability.gif').subsample(2, 2)],
                              'plot orientation': ['orientation', tk.PhotoImage(file='images/orientation.gif').subsample(2, 2)],
                              'increase exposure': ['inc_exp', tk.PhotoImage(file='images/increase_exp.gif').subsample(2, 2)],
                              'decrease exposure': ['dec_exp', tk.PhotoImage(file='images/decrease_exp.gif').subsample(2, 2)],
                              'view log': ['view_log', tk.PhotoImage(file='images/log.gif').subsample(2, 2)],
                              'show windows': ['show windows', tk.PhotoImage(file='images/show_windows.gif').subsample(2, 2)],
                              'clear windows': ['clear windows', tk.PhotoImage(file='images/clear_windows.gif').subsample(2, 2)],
                              'basic workspace': ['basic workspace', tk.PhotoImage(file='images/basic_workspace.gif').subsample(2, 2)],
                              'load workspace': ['load workspace', tk.PhotoImage(file='images/load_workspace.gif').subsample(2, 2)],
                              'save workspace': ['save workspace', tk.PhotoImage(file='images/save_workspace.gif').subsample(2, 2)],
                              'show webcam': ['show webcam', tk.PhotoImage(file='images/show_webcam.gif').subsample(2, 2)],
                              'calculation results': ['calculation results', tk.PhotoImage(file='images/calc_results.gif').subsample(2, 2)]
                               }
        self.toolbaroptions = ['x Cross Profile', 'y Cross Profile'] #initial choices for active buttons on toolbar
        self.camera_index = 0
        self.beam_width, self.beam_diameter = None, None
        self.centroid = None
        self.peak_cross = None
        self.power = np.nan
        self.colourmap = None
        self.style_sheet = 'default'
        self.graphs = { #if graphs are shown or not
        'centroid_x':True,
        'centroid_y':True,
        'peak_x':True,
        'peak_y':True,
        'ellipse_orientation':True
        }
        self.running_time = np.array([]) #arrays for information logged throughout the running period
        self.centroid_hist_x, self.centroid_hist_y = np.array([]), np.array([])
        self.peak_hist_x, self.peak_hist_y = np.array([]), np.array([])
        self.ellipse_hist_angle = np.array([])
        self.MA, self.ma, self.ellipse_x, self.ellipse_y, self.ellipse_angle = np.nan, np.nan, np.nan, np.nan, None
        self.ellipticity, self.eccentricity = None, None
        self.tick_counter = 0
        self.plot_tick = 0.1 #refresh rate of plots in sec
        self.pixel_scale = 5.6 #default pixel scale of webcam in um
        
        self.basic_workspace = [(0.4166666666666667, 0.4166666666666667, 0.4127604166666667, 0.7314814814814815, 'plot', 'x cross profile'), (0.4166666666666667, 0.4166666666666667, 0.8307291666666666, 0.7314814814814815, 'plot', 'y cross profile'), (0.4166666666666667, 0.41898148148148145, -0.004557291666666667, 0.7280092592592593, 'webcam'), (1.2454427083333333, 0.5, -0.0032552083333333335, 0.1863425925925926, 'plot', 'positions')]
        self.workspace = []
        self.width, self.height  = 1,1
        # self.stream = output.SoundFeedback(self)
                
        self.analysis_frame = None
        self.analyse = analysis.Analyse(self) #creates instance for analysis routines
        self.analyse.start()
        
        self.raw_passfail = ['False'] * 6
        self.ellipse_passfail = ['False'] * 4   
                        
        self.bg_frame = 0
        self.bg_subtract = 0

        frame = tk.Frame.__init__(self, parent,relief=tk.GROOVE,width=100,height=100,bd=1)
        self.parent = parent
        self.var = tk.IntVar()
        
        WorkspaceManager.__init__(self, parent) #initialise workspace manager class for arrangment of windows
        self.read_config() #overwrite prev init values with new config #NO MORE INIT VALUES BEYOND THIS POINT
        
        self.statusbar = tk.Frame(self.parent)
        self.progress = interface.Progress(self)

        # **** Status Bar ****
        self.status = tk.StringVar()
        status_string = "Profiler: " + str(self.TrueFalse(self.active)) + " | " + "Centroid: " + str(self.TrueFalse(self.centroid)) + " | Peak Cross: " + str(self.TrueFalse(self.peak_cross) + " | Ellipse: " + str(self.TrueFalse(self.ellipse_angle)) + '                  ' + 'Zoom Factor: ' + str(self.roi) + ' | Exposure: ' + str(self.exp) + ' | Rotation: ' + str(self.angle))
        self.status.set(status_string)
        status_label = tk.Label(self.statusbar, textvariable=self.status, width = 65, pady = 5, anchor=tk.W)
        status_label.pack(side=tk.BOTTOM, fill=tk.X)
        self.statusbar.pack(side=tk.BOTTOM, fill=tk.X)

        self.parent.title('BiLBO')
        
        ###################################################################NAVBAR
        menubar = tk.Menu(self.parent)
        fileMenu = tk.Menu(menubar, tearoff=1)
        fileMenu.add_command(label="Export Data", command=self.save_csv)
        fileMenu.add_separator()
        fileMenu.add_command(label="Quit", command=self.close_window)
        menubar.add_cascade(label="File", menu=fileMenu)
        
        controlMenu = tk.Menu(menubar, tearoff=1)
        self.camera_menu = tk.Menu(controlMenu, tearoff=1)
        controlMenu.add_command(label="Edit Config", command=self.change_config)
        controlMenu.add_command(label="View System Log", command= self.view_log)
        controlMenu.add_separator()
        controlMenu.add_command(label="Calibrate background subtraction", command=self.progress.calibrate_bg)
        controlMenu.add_command(label="Reset background subtraction", command=self.progress.reset_bg)
        controlMenu.add_separator()
        controlMenu.add_cascade(label='Change Camera', menu=self.camera_menu, underline=0)
        controlMenu.add_separator()
        controlMenu.add_command(label="Show all windows", command= self.show_all)
        controlMenu.add_command(label="Close all windows", command= self.close_all)
        controlMenu.add_separator()
        controlMenu.add_command(label="Load Workspace", command= self.load_workspace)
        controlMenu.add_command(label="Save Workspace", command= self.save_workspace)
        menubar.add_cascade(label="Control", menu=controlMenu)

        windowMenu = tk.Menu(menubar, tearoff=1)
        submenu = tk.Menu(windowMenu, tearoff=1)
        windowMenu.add_command(label="Show Webcam Feed", command=self.view_webcam)
        windowMenu.add_separator()
        windowMenu.add_command(label="Calculation Results", command=self.calc_results)
        windowMenu.add_command(label="x Cross Profile", command=lambda: self.view_plot('x cross profile'))
        windowMenu.add_command(label="y Cross Profile", command=lambda: self.view_plot('y cross profile'))
        windowMenu.add_command(label="2D Profile", command=lambda: self.view_plot('2d profile'))
        windowMenu.add_command(label="2D Surface", command=lambda: self.view_plot('2d surface'))
        windowMenu.add_separator()
        windowMenu.add_command(label="Plot Positions", command=lambda: self.view_plot('positions'))
        windowMenu.add_command(label="Plot Orientation", command=lambda: self.view_plot('orientation'))
        windowMenu.add_separator()
        windowMenu.add_command(label="Beam Stability", command=lambda: self.view_plot('beam stability'))
        menubar.add_cascade(label="Windows", menu=windowMenu)
        
        imageMenu = tk.Menu(menubar, tearoff=1)       
        imageMenu.add_command(label="Take Screenshot", command=self.save_screenshot)
        imageMenu.add_command(label="Take Video /10 s", command=lambda: self.save_video(10))
        imageMenu.add_separator()
        submenu = tk.Menu(imageMenu, tearoff=1)
        submenu.add_command(label="Normal", command= lambda: self.change_colourmap('normal'))
        submenu.add_command(label="Jet", command= lambda: self.change_colourmap('jet'))
        submenu.add_command(label="Parula", command=lambda: self.change_colourmap('parula'))
        submenu.add_command(label="Autumn", command=lambda: self.change_colourmap('autumn'))
        submenu.add_command(label="Bone", command=lambda: self.change_colourmap('bone'))
        imageMenu.add_cascade(label='Change Colourmap', menu=submenu, underline=0)
        submenu = tk.Menu(imageMenu, tearoff=1)
        submenu.add_command(label='default', command=lambda: self.change_style('default'))
        submenu.add_command(label='bmh', command=lambda: self.change_style('bmh'))
        submenu.add_command(label='ggplot', command=lambda: self.change_style('ggplot'))
        submenu.add_command(label='fivethirtyeight', command=lambda: self.change_style('fivethirtyeight'))
        imageMenu.add_cascade(label='Change Plot Style', menu=submenu, underline=0)
        
        menubar.add_cascade(label="Image", underline=0, menu=imageMenu)        
        
        helpmenu = tk.Menu(menubar, tearoff=1)
        helpmenu.add_command(label="About", command=lambda: self.info_window("About", "BiLBO (Birmingham Laser Beam Observer) is a Laser Beam Profiler created by Samuel Bancroft \n Summer 2016 Internship Project \n Supervisor: Dr Jon Goldwin, Birmingham University", modal=True))
        menubar.add_cascade(label="Help", menu=helpmenu)

        self.parent.config(menu=menubar)
        ###################################################################NAVBAR
          
        # **** Tool Bar ****
        self.toolbar = tk.Frame(self.parent)

        self.pb = tk.Checkbutton(self.toolbar, text="Profiler Active (<space>)", variable=self.profiler_state, command=self.profiler_active)
        self.pb.pack(side=tk.LEFT, padx=2, pady=2)
        
        self.cog = tk.PhotoImage(file='images/cog.gif').subsample(2, 2)
        insertButt = tk.Button(self.toolbar, image=self.cog, width=32, height=32, text="Customise Toolbar", command=self.change_toolbar)
        insertButt.pack(side=tk.LEFT, padx=(2, 20), pady=2)
        
        self.toolbar.pack(side=tk.TOP, fill=tk.X)       
        # **** End of Tool Bar ****
        
        # b = tk.Button(labelframe, text="Start Sound", command=lambda: self.stream.streamer.start_stream())
        # b.pack(fill=tk.BOTH)
        # b = tk.Button(labelframe, text="Stop Sound", command=lambda: self.stream.streamer.stop_stream())
        # b.pack(fill=tk.BOTH)
        
        newbuttons = [obj for obj in self.toolbaroptions if obj not in [i[1] for i in self.toolbarbuttons]]
        for button in newbuttons:
            self.update_toolbar(button)

    def load_camera_menu(self, camera_count):
        for i in range(camera_count):
            self.camera_menu.add_command(label=str(i), command= lambda i=i: self.change_cam(i))
        
    def refresh_plot(self):
        if len(self.plot_frames) > 0:
            for plot in self.plot_frames:
                plot.refresh_frame()
            
    def change_style(self, option, set=False):
        '''Changes the style sheet used in the plot'''
        if self.style_sheet != option or set==True:
            self.log('Changed style sheet ' + option)
            self.style_sheet = option
            plt.style.use(option)
            plt.cla()
            plt.clf()
            self.refresh_plot()
            
    def set_exp(self):
        '''Sets the exposure time of the camera.'''
        self.log('Changing exposure to ' + str(self.exp))
        self.cap.set(15, self.exp)
        
    def adjust_exp(self, amount):
        '''Either raises or lowers the exposure of the camera by +/- 1'''
        self.exp = self.exp + amount
        self.log('Changing exposure to ' + str(self.exp))
        self.cap.set(15, self.exp)
        
    def change_exp(self, option):
        '''Changes the exposure time of the camera.'''
        self.exp = float(option)
        self.log('Changing exposure to ' + str(self.exp))
        self.cap.set(15, self.exp)
        
    def change_gain(self, option):
        '''Changes the gain of the camera.'''
        gain = float(option)
        self.log('Changing gain to ' + str(gain))
        self.cap.set(14, gain)

    def init_camera(self):
        '''Initialises the camera with a set resolution.'''
        self.width, self.height = 640*2, 360*2
        self.cap = cv2.VideoCapture(self.camera_index)
        if not self.cap:
            raise Exception("Camera not accessible")
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
        self.set_exp()
              
    def change_cam(self, option):
        '''Switches between camera_indexes and therefore different connected cameras.'''
        if self.camera_index != option and type(option) == int:
            self.camera_index = int(option)
            self.log('Camera index change, now updating view... ' + str(self.camera_index))
            self.cap.release()
            self.init_camera()
    
    def change_colourmap(self, option):
        '''Changes the colourmap used in the camera feed.'''
        if self.colourmap != option:
            self.log('Changed colourmap to ' + option)
            if option.lower() == 'jet':
                self.colourmap = cv2.COLORMAP_JET
            elif option.lower() == 'autumn':
                self.colourmap = cv2.COLORMAP_AUTUMN
            elif option.lower() == 'bone':
                self.colourmap = cv2.COLORMAP_BONE
            elif option.lower() == 'parula':
                self.colourmap = cv2.COLORMAP_PARULA
            else:
                self.colourmap = None
            
    def show_frame(self):
        '''Shows camera view with relevant labels and annotations included.'''
        _, frame = self.cap.read() #read camera input

        self.frame = frame
        
        if self.bg_subtract > 0:
            self.progress.next_step()
            
        frame = cv2.subtract(frame, self.bg_frame)
         
        # frame = np.asarray(Image.open("output.png"))
        # frame = cv2.flip(frame, 1)
        if self.roi != 1: #apply region of interest scaling
            size = self.width/self.roi, self.height/self.roi
            analysis_frame = frame[(self.height/2)-(size[1]/2):(self.height/2)+(size[1]/2), (self.width/2)-(size[0]/2):(self.width/2)+(size[0]/2)]
            frame = cv2.resize(analysis_frame,None,fx=self.width/size[0], fy=self.height/size[1], interpolation = cv2.INTER_CUBIC)
        else:
            analysis_frame = frame
            frame = cv2.resize(frame,None,fx=640./float(self.width), fy=360./float(self.height), interpolation = cv2.INTER_CUBIC)
            
        if self.colourmap is None: #apply colourmap change
            cv2image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGBA)
        else:
            cv2image = cv2.applyColorMap(frame, self.colourmap)
            
        if self.angle != 0: #apply rotation
            cv2image = self.rotate_image(cv2image)
        
        self.analysis_frame = cv2.cvtColor(analysis_frame,cv2.COLOR_BGR2GRAY) # convert to greyscale

        if self.active:

            peak_cross = self.analyse.find_peak()
            self.peak_cross = peak_cross
            
            if peak_cross != (np.nan, np.nan):
                cross_size = 10
                screen_peak_cross = peak_cross[0]*(640./self.width), peak_cross[1]*(360./self.height)
                cv2.line(cv2image, (int(screen_peak_cross[0])-cross_size, int(screen_peak_cross[1])), (int(screen_peak_cross[0])+cross_size, int(screen_peak_cross[1])), 255, thickness=1)
                cv2.line(cv2image, (int(screen_peak_cross[0]), int(screen_peak_cross[1])+cross_size), (int(screen_peak_cross[0]), int(screen_peak_cross[1])-cross_size), 255, thickness=1)
                    
            centroid = self.analyse.get_centroid()
            if centroid != (np.nan, np.nan):               
                if centroid[0] < self.width or centroid[1] < self.height: #ensure centroid lies within correct regions
                    self.centroid = centroid
                    
                    cross_size = 20
                    screen_centroid = centroid[0]*(640./self.width), centroid[1]*(360./self.height)
                    cv2.line(cv2image, (int(screen_centroid[0])-cross_size, int(screen_centroid[1])), (int(screen_centroid[0])+cross_size, int(screen_centroid[1])), 255, thickness=1)
                    cv2.line(cv2image, (int(screen_centroid[0]), int(screen_centroid[1])+cross_size), (int(screen_centroid[0]), int(screen_centroid[1])-cross_size), 255, thickness=1)
                else:
                    # self.log('Problem! Centroid out of image region. ' + str(centroid[0]) + ' ' + str(centroid[1]))
                    self.centroid = None
            else:
                self.centroid = None
        
            ellipses = self.analyse.find_ellipses() #fit ellipse and print data to screen
            if ellipses != None:
                (x,y),(ma,MA),angle = ellipses
                self.MA, self.ma, self.ellipse_x, self.ellipse_y, self.ellipse_angle = MA, ma, x, y, angle
                self.ellipticity, self.eccentricity = 1-(self.ma/self.MA), np.sqrt(1-(self.ma/self.MA)**2)
                fix_x, fix_y = (640./self.width), (360./self.height)
                screen_ellipses = (x*fix_x, y*fix_y), (ma*fix_x, MA*fix_x), angle #hope the aspect ratio kept same for fix_x, fix_y. should do properly with trig
                cv2.ellipse(cv2image,screen_ellipses,(0,255,0),1)
            else:
                self.MA, self.ma, self.ellipse_x, self.ellipse_y, self.ellipse_angle = np.nan, np.nan, np.nan, np.nan, np.nan
                self.ellipticity, self.eccentricity = np.nan, np.nan

            #record data that should be logged throughout time
            self.centroid_hist_x, self.centroid_hist_y = np.append(self.centroid_hist_x, centroid[0]), np.append(self.centroid_hist_y, centroid[1])
            self.peak_hist_x, self.peak_hist_y = np.append(self.peak_hist_x, peak_cross[0]), np.append(self.peak_hist_y, peak_cross[1])
            self.ellipse_hist_angle = np.append(self.ellipse_hist_angle, self.ellipse_angle)
            self.running_time = np.append(self.running_time, time.time()-self.pause_delay) #making sure to account for time that pause has been active

            if self.info_frame != None:
                self.pass_fail_testing()
            
            self.beam_width = self.analyse.get_e2_width(self.peak_cross)
            if self.beam_width is not None:
                self.beam_diameter = np.mean(self.beam_width)
            else:
                self.beam_diameter = None
                
        status_string = "Profiler: " + str(self.TrueFalse(self.active)) + " | " + "Centroid: " + str(self.TrueFalse(self.centroid)) + " | Peak Cross: " + str(self.TrueFalse(self.peak_cross) + " | Ellipse: " + str(self.TrueFalse(self.ellipse_angle)) + '                  ' + 'Zoom Factor: ' + str(self.roi) + ' | Exposure: ' + str(self.exp) + ' | Rotation: ' + str(self.angle))
        self.status.set(status_string)
                
        self.imgtk = ImageTk.PhotoImage(image=Image.fromarray(cv2image))

        if self.webcam_frame is not None:
            self.webcam_frame.show_frame()
        self.lmain.after(10, self.show_frame)
              
        self.img = frame
        curr_time = time.time()
        if curr_time - self.plot_time > self.plot_tick and self.active: #if tickrate period elapsed, update the plot with new data
            self.refresh_plot()
            self.tick_counter += 1
            if self.tick_counter > 2 and self.info_frame != None: #if 10 ticks passed update results window
                self.info_frame.refresh_frame()
                self.tick_counter = 0
            self.plot_time = time.time() #update plot time info
            
    def set_angle(self, option):
        '''Sets the rotation angle.'''
        self.log('Changed angle to ' + str(option))
        self.angle = float(option)
        
    def set_roi(self, option):
        '''Sets the region of interest size'''
        self.log('Changed roi to ' + str(option))
        self.roi = int(option)
        
    def profiler_active(self, option=False):
        '''Turns profiling mode on or off'''
        if option: #toggle box state if using key binding to toggle. if using box then sets correct box state, ticked or not ticked
            if self.profiler_state.get() == 1:
                box = False
            else:
                box = True
        else:
            if self.profiler_state.get() == 1:
                box = True
            else:
                box = False
                
        if box and not self.active:
            self.log('Profiler ACTIVE')
            self.pause_delay += time.time()-self.last_pause
            self.active = True
            self.pb.select()
        elif not box and self.active:
            self.log('Profiler INACTIVE')
            self.last_pause = time.time()
            self.active = False
            self.pb.deselect()
        
    def rotate_image(self, image):
        '''Rotates the given array by the rotation angle, returning as an array.'''
        image_height, image_width = image.shape[0:2]
        
        image_rotated = output.rotate_image(image, self.angle)
        image_rotated_cropped = output.crop_around_centre(
            image_rotated,
            *output.largest_rotated_rect(
                image_width,
                image_height,
                math.radians(self.angle)
            )
        )
        return image_rotated_cropped
  
    def close_window(self):
        on_closing(self)
        
    def info_window(self, title, info, modal=False):
        t = tk.Toplevel(self)
        t.wm_title(title)
        l = tk.Label(t, text=info)
        l.pack(side="top", fill="both", expand=True, padx=100, pady=100)
        if modal:
            l.focus_set()                                                        
            l.grab_set()  
       
    def save_screenshot(self):
        cv2.imwrite('output.png', self.img)
        self.log('Written output.png to disk.')
        
    def save_video(self, wait):
        self.log('Writing video to disk, of length ' + str(wait) + ' seconds.')
        video  = cv2.VideoWriter('output.avi', -1, 25, (self.width, self.height));
        start = time.time()
        while time.time() - start < wait:
           f,img = self.cap.read()
           video.write(img)
        self.log('Video capture completed successfully.')
        video.release()  
            
    def save_csv(self):
        '''Saves .csv file of recorded data in columns.'''
        f = tkFileDialog.asksaveasfile(mode='w', initialfile='output.csv', defaultextension=".csv")
        if f is None: # asksaveasfile return `None` if dialog closed with "cancel".
            return
        output = np.column_stack((self.running_time.flatten(),self.centroid_hist_x.flatten(),self.centroid_hist_y.flatten(),self.peak_hist_x.flatten(),self.peak_hist_y.flatten()))
        np.savetxt('output.csv',output,delimiter=',',header='BiLBO Data Export. \n running time, centroid_hist_x, centroid_hist_y, peak_hist_x, peak_hist_y')
    
    def calc_results(self):
        '''Opens calculation results window'''
        if self.info_frame is None:
            self.info_frame = self.view('info')
        else:
            # self.log('Calculation results already loaded')
            self.info_frame.window.lift()
            self.info_frame.window.deiconify()
            
    def view_plot(self, graph):
        '''Opens plot view'''
        if graph not in [i.fig_type for i in self.plot_frames]:
            self.plot_frames.append(self.view('plot', graphtype=graph))
        else:
            # self.log('Plot view already loaded')
            for plot in self.plot_frames:
               if plot.fig_type == graph:
                   plot.window.lift()
                   plot.window.deiconify()
        
    def change_config(self):
        '''Opens configuration window'''
        if self.config_frame != None:
            self.config_frame.close()
        self.config_frame = interface.Config(self)
        if self.config_frame.result is not None:
            plot_tick, pixel_scale, power, angle = self.config_frame.result
            if plot_tick is not None:
                self.plot_tick = plot_tick
            if pixel_scale is not None:
                self.pixel_scale = pixel_scale
                if self.info_frame is not None:
                        self.info_frame.raw_xbounds = [('x ≥ 0.00', 'x ≤ 0.00'), #refresh this to reflect change in pixel scale
                        ('0.00', '0.00'),
                        ('0.00', '255.00'),
                        ('x ≥ 0.00', 'x ≤ ' + '{0:.2f}'.format(self.width*self.pixel_scale)),
                        ('x ≥ 0.00', 'x ≤ ' + '{0:.2f}'.format(self.width*self.pixel_scale)),
                        ('0.00', '0.00')
                        ]
                        self.info_frame.raw_ybounds = [('y ≥ 0.00', 'y ≤ 0.00'),
                        (' ', ' '),
                        (' ', ' '),
                        ('y ≥ 0.00', 'y ≤ ' + '{0:.2f}'.format(self.height*self.pixel_scale)),
                        ('y ≥ 0.00', 'y ≤ ' + '{0:.2f}'.format(self.height*self.pixel_scale)),
                        (' ', ' ')
                        ]
                        self.info_frame.refresh_frame()
            if power is not None:
                if power == '-':
                    self.power = np.nan
                else:
                    self.power = power
            if angle is not None:
                self.angle = angle
                
    def view_log(self):
        '''Opens System Log'''
        if self.systemlog_frame is None:
            self.systemlog_frame = self.view('logs')
        else:
            # self.log('System logs already loaded')
            self.systemlog_frame.window.lift()
            self.systemlog_frame.deiconify()
        
    def view_webcam(self):
        '''Opens Webcam Feed'''
        if self.webcam_frame is None:
            self.webcam_frame = self.view('webcam')
        else:
            # self.log('Webcam window already loaded')
            self.webcam_frame.window.lift()
            self.webcam_frame.deiconify()
            
    def change_toolbar(self):
        '''Opens Toolbar Settings'''
        if self.toolbarconfig_frame != None:
            self.toolbarconfig_frame.close()
        self.toolbarconfig_frame = interface.ToolbarConfig(self)

        #now remove the buttons that have been unchecked in the config
        if self.toolbarconfig_frame.result is not None:
            self.toolbaroptions = [self.toolbarconfig_frame.options[i] for i,j in enumerate(self.toolbarconfig_frame.result) if j.get() == 1]
            removedbuttons = [obj for obj in self.toolbarbuttons if obj[1] not in self.toolbaroptions]
            for button in removedbuttons:
                button[0].destroy()
                self.toolbarbuttons.remove(button)
        newbuttons = [obj for obj in self.toolbaroptions if obj not in [i[1] for i in self.toolbarbuttons]]
        for button in newbuttons: #need for loop or commands get overwritten..?
            self.update_toolbar(button) #now add buttons that have been requested
                
    def update_toolbar(self, button):
        '''Adds buttons to the toolbar that have been chosen'''
        if button.lower() in self.toolbaractions.keys():
            if self.toolbaractions[button.lower()][0] in ['inc_exp', 'dec_exp', 'view_log', 'calculation results', 'show windows', 'clear windows', 'save workspace', 'load workspace', 'show webcam', 'basic workspace']:
                if self.toolbaractions[button.lower()][0] == 'view_log':
                    self.toolbarbuttons.append([tk.Button(self.toolbar, text=button, height=32, width=32, image=self.toolbaractions[button.lower()][1], command=self.view_log), button])
                elif self.toolbaractions[button.lower()][0] == 'clear windows':
                    self.toolbarbuttons.append([tk.Button(self.toolbar, text=button, height=32, width=32, image=self.toolbaractions[button.lower()][1], command= self.close_all), button])
                elif self.toolbaractions[button.lower()][0] == 'inc_exp':
                    self.toolbarbuttons.append([tk.Button(self.toolbar, text=button, height=32, width=32, image=self.toolbaractions[button.lower()][1], command= lambda: self.adjust_exp(1)), button])
                elif self.toolbaractions[button.lower()][0] == 'dec_exp':
                    self.toolbarbuttons.append([tk.Button(self.toolbar, text=button, height=32, width=32, image=self.toolbaractions[button.lower()][1], command= lambda: self.adjust_exp(-1)), button])
                elif self.toolbaractions[button.lower()][0] == 'load workspace':
                    self.toolbarbuttons.append([tk.Button(self.toolbar, text=button, height=32, width=32, image=self.toolbaractions[button.lower()][1], command= self.load_workspace), button])
                elif self.toolbaractions[button.lower()][0] == 'save workspace':
                    self.toolbarbuttons.append([tk.Button(self.toolbar, text=button, height=32, width=32, image=self.toolbaractions[button.lower()][1], command= self.save_workspace), button])
                elif self.toolbaractions[button.lower()][0] == 'show webcam':
                    self.toolbarbuttons.append([tk.Button(self.toolbar, text=button, height=32, width=32, image=self.toolbaractions[button.lower()][1], command= self.view_webcam), button])
                elif self.toolbaractions[button.lower()][0] == 'show windows':
                    self.toolbarbuttons.append([tk.Button(self.toolbar, text=button, height=32, width=32, image=self.toolbaractions[button.lower()][1], command= self.show_all), button])
                elif self.toolbaractions[button.lower()][0] == 'calculation results':
                    self.toolbarbuttons.append([tk.Button(self.toolbar, text=button, height=32, width=32, image=self.toolbaractions[button.lower()][1], command= self.calc_results), button])
                elif self.toolbaractions[button.lower()][0] == 'basic workspace':
                    self.toolbarbuttons.append([tk.Button(self.toolbar, text=button, height=32, width=32, image=self.toolbaractions[button.lower()][1], command= lambda: self.load_workspace(workspace=self.basic_workspace)), button])
            else:
                self.toolbarbuttons.append([tk.Button(self.toolbar, text=button, height=32, width=32, image=self.toolbaractions[button.lower()][1], command= lambda: self.view_plot(self.toolbaractions[button.lower()][0])), button])
        else:
            self.toolbarbuttons.append([tk.Button(self.toolbar, text=button), button])
        self.toolbarbuttons[-1][0].pack(side=tk.LEFT, padx=2, pady=2)
        
    def pass_fail_testing(self):
        '''Sets off alarm if pass/fail test criteria are not met.'''
        for index in np.where(np.array(self.raw_passfail) == 'True')[0]:
            x_lower, x_upper = [float(i) if i.replace('.','').isdigit() else i for i in self.info_frame.raw_xbounds[index]]
            if index == 0:
                if self.beam_width is not None:
                    y_lower, y_upper = [float(i[5:]) for i in self.info_frame.raw_ybounds[index]]
                    if self.beam_width[0]*self.pixel_scale <= float(x_lower[5:]) or self.beam_width[0]*self.pixel_scale >= float(x_upper[5:]) or self.beam_width[1]*self.pixel_scale <= y_lower or self.beam_width[1]*self.pixel_scale >= y_upper:
                        self.alert("Pass/Fail Test", "Beam Width has failed to meet criteria!")
                        self.raw_passfail[index] = 'False' #reset value
                        self.info_frame.refresh_frame()
            if index == 1:
                if self.beam_diameter is not None:
                    if self.beam_diameter*self.pixel_scale <= x_lower or self.beam_diameter*self.pixel_scale >= x_upper:
                        self.alert("Pass/Fail Test", "Beam Diameter has failed to meet criteria!")
                        self.raw_passfail[index] = 'False' #reset value
                        self.info_frame.refresh_frame()
            if index == 2:
                if np.max(self.analysis_frame) >= x_upper or np.max(self.analysis_frame) <= x_lower:
                    self.alert("Pass/Fail Test", "Peak Pixel Value has failed to meet criteria!")
                    self.raw_passfail[index] = 'False' #reset value
                    self.info_frame.refresh_frame()
            if index == 3:
                if self.peak_cross is not None:
                    y_lower, y_upper = [float(i[5:]) for i in self.info_frame.raw_ybounds[index]]
                    if self.peak_cross[0]*self.pixel_scale <= float(x_lower[5:]) or self.peak_cross[0]*self.pixel_scale >= float(x_upper[5:]) or self.peak_cross[1]*self.pixel_scale <= y_lower or self.peak_cross[1]*self.pixel_scale >= y_upper:
                            self.alert("Pass/Fail Test", "Peak Position has failed to meet criteria!")
                            self.raw_passfail[index] = 'False' #reset value
                            self.info_frame.refresh_frame()
            if index == 4:
                if self.centroid is not None:
                    y_lower, y_upper = [float(i[5:]) for i in self.info_frame.raw_ybounds[index]]
                    if self.centroid[0]*self.pixel_scale <= float(x_lower[5:]) or self.centroid[0]*self.pixel_scale >= float(x_upper[5:]) or self.centroid[1]*self.pixel_scale <= y_lower or self.centroid[1]*self.pixel_scale >= y_upper:
                            self.alert("Pass/Fail Test", "Centroid Position has failed to meet criteria!")
                            self.raw_passfail[index] = 'False' #reset value
                            self.info_frame.refresh_frame()
            if index == 5:
                print('check total power')
                               
        for index in np.where(np.array(self.ellipse_passfail) == 'True')[0]:
            x_lower, x_upper = [float(i) if i.replace('.','').isdigit() else i for i in self.info_frame.ellipse_xbounds[index]]
            if index == 0:
                if self.ma <= float(x_lower[5:]) or self.ma >= float(x_upper[5:]):
                    y_lower, y_upper = [float(i[5:]) for i in self.info_frame.ellipse_ybounds[index]]
                    if self.MA <= y_lower or self.MA >= y_upper:
                        self.alert("Pass/Fail Test", "Ellipse axes have failed to meet criteria!")
                        self.ellipse_passfail[index] = 'False'
                        self.info_frame.refresh_frame()
            if index == 1:
                if self.ellipticity <= x_lower or self.ellipticity >= x_upper:
                    self.alert("Pass/Fail Test", "Ellipticity has failed to meet criteria!")
                    self.ellipse_passfail[index] = 'False'
                    self.info_frame.refresh_frame()
            if index == 2:
                if self.eccentricity <= x_lower or self.eccentricity >= x_upper:
                    self.alert("Pass/Fail Test", "Eccentricity has failed to meet criteria!")
                    self.ellipse_passfail[index] = 'False'
                    self.info_frame.refresh_frame()
            if index == 3:
                if self.ellipse_angle <= x_lower or self.ellipse_angle >= x_upper:
                    self.alert("Pass/Fail Test", "Ellipse orientation has failed to meet criteria!")
                    self.ellipse_passfail[index] = 'False'
                    self.info_frame.refresh_frame()

    def alert(self, title, text):
        '''Makes a sound and shows alert window'''
        print('\a')
        self.info_window(title, text)
        self.log(text)
        # tkMessageBox.showerror(title, text)
        
    def log(self, text):
        print(text)
        timestamp = time.strftime("%H:%M:%S", time.localtime())
        self.logs.append(timestamp + ' ' + text)
        if self.systemlog_frame != None:
            self.systemlog_frame.callback() #refresh log window with new info
        
    def toggle_graph(self, option):
        if self.graphs[option]:
            self.graphs[option] = False
        elif not self.graphs[option]:
            self.graphs[option] = True
        else:
            'Error. Something went wrong.'
        self.refresh_plot()
        
    def read_config(self):
        '''Reads config file on startup and sets chosen configuration'''
        config = ConfigParser.ConfigParser()
        if config.read("config.ini") != []:
            if config.has_option('WebcamSpecifications', 'pixel_scale'):
                self.pixel_scale = float(config.get('WebcamSpecifications', 'pixel_scale'))
            if config.has_option('WebcamSpecifications', 'base_exp'):
                self.exp = float(config.get('WebcamSpecifications', 'base_exp')) #then set exp
                
            if config.has_option('LaserSpecifications', 'power'):
                power = (config.get('LaserSpecifications', 'power'))
                if power == '-' or not power.isdigit():
                    self.power = np.nan
                else:
                    self.power = float(power)
            if config.has_option('LaserSpecifications', 'angle'):
                self.angle = float(config.get('LaserSpecifications', 'angle'))
                
            if config.has_option('Toolbar', 'buttons'):
                self.toolbaroptions = config.get('Toolbar', 'buttons').replace(', ',',').split(',')
                
            if config.has_option('Miscellaneous', 'plot_tick'):
                self.plot_tick = float(config.get('Miscellaneous', 'plot_tick'))
            if config.has_option('Miscellaneous', 'colourmap'):
                self.change_colourmap(config.get('Miscellaneous', 'colourmap'))
            if config.has_option('Miscellaneous', 'camera_index'):
                self.camera_index = int(config.get('Miscellaneous', 'camera_index'))
            if config.has_option('Miscellaneous', 'style_sheet'):
                self.style_sheet = config.get('Miscellaneous', 'style_sheet')
            if config.has_option('Miscellaneous', 'workspace'):
                windows = config.get('Miscellaneous', 'workspace').replace(', ',',').split('),')
                self.workspace = []
                for window in windows:
                    window_params = window[1:-1].split(',')
                    if len(window_params) == 6:
                        w, h, x, y, windowtype, graphtype = window[1:-1].split(',')
                        windowtype = windowtype.replace('\'','')
                        graphtype = graphtype.replace('\'','').replace('"','')
                        self.workspace.append((float(w), float(h), float(x), float(y), windowtype, graphtype))
                    elif len(window_params) == 5:
                        w, h, x, y, windowtype = window[1:-1].split(',')
                        windowtype = windowtype.replace('\'','')
                        self.workspace.append((float(w), float(h), float(x), float(y), windowtype))
                    else:
                        self.log('Could not find workspace details.')
                        
    def TrueFalse(self, x):
        if x != (np.nan, np.nan) and x is not None and x and str(x) != 'nan' and x is not False:
            if self.active:
                return 'ACTIVE'
            else:
                return 'INACTIVE'
        else:
            return 'INACTIVE'
    
app = Application()
app.load()