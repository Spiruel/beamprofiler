#!/usr/bin/python
# -*- coding: latin-1 -*-
          
import Tkinter as tk
import ttk
import tkSimpleDialog, tkFileDialog, tkMessageBox

import cv2
from PIL import Image, ImageTk
import numpy as np
import time
import math

from mpl_toolkits.mplot3d import Axes3D
from scipy.ndimage.interpolation import zoom
from scipy.optimize import curve_fit
                
import matplotlib
matplotlib.use('TkAgg')

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2TkAgg
import matplotlib.pyplot as plt

from utils import analysis
from utils import output
from utils import interface

root = tk.Tk()
lmain = tk.Label(root)
lmain.pack()

class Config(tkSimpleDialog.Dialog):
    def body(self, master):
        tk.Label(master, text="Plot refresh rate /s:").grid(row=0)
        tk.Label(master, text="Pixel size (µm):").grid(row=1)
        tk.Label(master, text="Angle (deg):").grid(row=2)

        self.e1 = tk.Entry(master)
        self.e2 = tk.Entry(master)
        self.e3 = tk.Entry(master)
        
        self.e1.delete(0, tk.END)
        self.e1.insert(0, str(c.plot_tick))
        self.e2.delete(0, tk.END)
        self.e2.insert(0, str(c.pixel_scale))
        self.e3.delete(0, tk.END)
        self.e3.insert(0, str(c.angle))

        self.e1.grid(row=0, column=1)
        self.e2.grid(row=1, column=1)
        self.e3.grid(row=2, column=1)
        
        self.rb = tk.Button(master, text="Reset to default", command=self.reset_values)
        self.rb.grid(row=3, columnspan=2)
        
        self.expscale = tk.Scale(master, label='exposure',
        from_=-15, to=-8,
        length=300, tickinterval=1,
        showvalue='yes', 
        orient='horizontal',
        command = c.change_exp)
        self.expscale.grid(row=4, columnspan=2, sticky=tk.W)
                
        self.roiscale = tk.IntVar(master)
        self.roiscale.set(1)
        self.dropdown5 = tk.OptionMenu(master, self.roiscale, 1, 2, 4, 8, 16, command = c.set_roi)
        roitext = tk.Label(master, text="zoom factor")
        roitext.grid(row=5, columnspan=2, sticky=tk.W)
        self.dropdown5.grid(row=6, columnspan=2, sticky=tk.W)
        
        return self.e1 # initial focus
        
    def validate(self):
        try:
            plot_tick = self.e1.get()
            if plot_tick == 0: 
                raise ValueError
            pixel_scale = self.e2.get()
            if plot_tick == '':
                plot_tick = None
            else:
                plot_tick = float(plot_tick)
            if pixel_scale == '':
                pixel_scale = None
            else:
                pixel_scale = float(pixel_scale)
            angle = self.e3.get()
            if angle == '':
                angle = None
            else:
                angle = float(angle)
            self.result = plot_tick, pixel_scale, angle
            return 1
        except ValueError:
            tkMessageBox.showwarning(
                "Bad input",
                "Illegal values, please try again"
            )
            return 0
        
    def reset_values(self):
        self.e1.delete(0, tk.END)
        self.e1.insert(0, '0.1')
        self.e2.delete(0, tk.END)
        self.e2.insert(0, '2.8')
        self.e3.delete(0, tk.END)
        self.e3.insert(0, '0.0')
        
    def close(self):
        self.destroy()
              
class Controller(tk.Frame):
    def __init__(self, parent=root):
        '''Initialises basic variables and GUI elements.'''
        self.active = False
        self.pause_delay = 0 #time delay for when profiler is inactive. cumulatively adds.
        self.last_pause = time.time() #last time profiler was inactive
        self.plot_time = self.last_pause  #various parameters ters used throughout the profiler are initialised here
        self.angle = 0
        self.roi = 1
        self.camera_index = 0
        self.beam_width, self.beam_diameter = None, None
        self.centroid = None
        self.peak_cross = None
        self.colourmap = None
        self.fig_type = 'x cross profile'
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
        self.pixel_scale = 2.8 #default pixel scale of webcam in um
        
        self.analysis_frame = None
        self.analyse = analysis.Analyse(self) #creates instance for analysis routines
        
        self.raw_passfail = ['False'] * 6
        self.ellipse_passfail = ['False'] * 4
        self.raw_xbounds = [('x ≥ 0.00', 'x ≤ 0.00'), #for pass/fail testing
                        ('0.00', '0.00'),
                        ('0.00', '0.00'),
                        ('x ≥ 0.00', 'x ≤ 0.00'),
                        ('x ≥ 0.00', 'x ≤ 0.00'),
                        ('0.00', '0.00')
                        ]
        self.ellipse_xbounds = [('M ≥ 0.00', 'M ≤ 0.00'),
                        ('0.00', '1.00'),
                        ('0.00', '1.00'),
                        ('0.00', '360.00')
                        ]
        self.raw_ybounds = [('y ≥ 0.00', 'y ≤ 0.00'),
                        (' ', ' '),
                        (' ', ' '),
                        ('y ≥ 0.00', 'y ≤ 0.00'),
                        ('y ≥ 0.00', 'y ≤ 0.00'),
                        (' ', ' ')
                        ]
        self.ellipse_ybounds = [('m ≥ 0.00', 'm ≤ 0.00'),
                        (' ', ' '),
                        (' ', ' '),
                        (' ', ' ')
                        ]
                        
        self.info_frame = None
        self.config_frame = None
        self.passfail_frame = None

        frame = tk.Frame.__init__(self, parent,relief=tk.GROOVE,width=100,height=100,bd=1)
        self.parent = parent
        self.var = tk.IntVar()

        self.parent.title('Laser Beam Profiler')
        
        ###################################################################NAVBAR
        menubar = tk.Menu(self.parent)
        fileMenu = tk.Menu(menubar, tearoff=1)
        fileMenu.add_command(label="Export Data", command=self.save_csv)
        fileMenu.add_separator()
        fileMenu.add_command(label="Quit", command=self.close_window)
        menubar.add_cascade(label="File", menu=fileMenu)
        
        controlMenu = tk.Menu(menubar, tearoff=1)
        submenu = tk.Menu(controlMenu, tearoff=1)
        submenu.add_command(label="0", command= lambda: self.change_cam(0))
        submenu.add_command(label="1", command= lambda: self.change_cam(1))
        submenu.add_command(label="2", command= lambda: self.change_cam(2))
        controlMenu.add_command(label="Edit Config", command=self.change_config)
        controlMenu.add_cascade(label='Change Camera', menu=submenu, underline=0)
        controlMenu.add_separator()
        controlMenu.add_command(label="Clear Windows", command= lambda: tkMessageBox.showerror("Not done", "This is a temporary message"))
        menubar.add_cascade(label="Control", menu=controlMenu)

        windowMenu = tk.Menu(menubar, tearoff=1)
        submenu = tk.Menu(windowMenu, tearoff=1)
        windowMenu.add_command(label="Calculation Results", command=self.calc_results)
        windowMenu.add_command(label="x Cross Profile", command=lambda: self.change_fig('x cross profile'))
        windowMenu.add_command(label="y Cross Profile", command=lambda: self.change_fig('y cross profile'))
        windowMenu.add_command(label="2D Gaussian", command=lambda: self.change_fig('2d gaussian fit'))
        windowMenu.add_command(label="2D Surface", command=lambda: self.change_fig('2d surface'))
        windowMenu.add_separator()
        windowMenu.add_command(label="Plot Positions", command=lambda: self.change_fig('positions'))
        windowMenu.add_command(label="Plot Power", command=lambda: self.change_fig('power'))
        windowMenu.add_command(label="Plot Orientation", command=lambda: self.change_fig('orientation'))
        windowMenu.add_separator()
        windowMenu.add_command(label="Beam Stability", command=lambda: self.change_fig('beam stability'))
        windowMenu.add_command(label="Ellipse Fit", command=lambda: self.change_fig('ellipse fit'))
        menubar.add_cascade(label="Windows", menu=windowMenu)
        
        imageMenu = tk.Menu(menubar, tearoff=1)       
        imageMenu.add_command(label="Take Screenshot", command=self.save_screenshot)
        imageMenu.add_command(label="Take Video /10 s", command=lambda: self.save_video(10))
        imageMenu.add_separator()
        submenu = tk.Menu(imageMenu, tearoff=1)
        submenu.add_command(label="Normal", command= lambda: self.change_colourmap('normal'))
        submenu.add_command(label="Jet", command= lambda: self.change_colourmap('jet'))
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
        helpmenu.add_command(label="About", command=lambda: self.info_window("About", "Laser Beam Profiler created by Samuel Bancroft \n Summer 2016 Internship Project \n Supervisor: Dr Jon Goldwin, Birmingham University", modal=True))
        menubar.add_cascade(label="Help", menu=helpmenu)

        self.parent.config(menu=menubar)
        ###################################################################NAVBAR
          
        # **** Tool Bar ****
        toolbar = tk.Frame(self.parent)
        
        self.variable4 = tk.IntVar()
        self.pb = tk.Checkbutton(toolbar, text="Profiler Active (<space>)", variable=self.variable4, command=self.profiler_active)
        self.pb.pack(side=tk.LEFT, padx=2, pady=2)
        
        self.cog = tk.PhotoImage(file='cog.gif')
        insertButt = tk.Button(toolbar, image=self.cog, text="Customise Toolbar")
        insertButt.pack(side=tk.LEFT, padx=2, pady=2)
        
        toolbar.pack(side=tk.TOP, fill=tk.X)
        
        # **** Status Bar ****
        self.status = tk.StringVar()
        status_string = "Profiler: " + str(TrueFalse(self.active)) + " | " + "Centroid: " + str(TrueFalse(self.centroid)) + " | Ellipse: " + str(TrueFalse(self.ellipse_angle)) + " | Peak Cross: " + str(TrueFalse(self.peak_cross))
        self.status.set(status_string)
        status_label = tk.Label(self.parent, textvariable=self.status, width = 65, pady = 5, anchor=tk.W)
        status_label.pack(side=tk.BOTTOM, fill=tk.X)
       
        labelframe = tk.Frame(self) #left hand frame for various sliders and tweakables for direct control
        labelframe.pack(side=tk.LEFT) #.grid(row=0, column=0) 
               
        self.variable3 = tk.StringVar(labelframe)
        self.variable3.set("x cross profile")
        self.dropdown3 = tk.OptionMenu(labelframe, self.variable3, "x cross profile", "y cross profile", "2d gaussian fit","2d surface", "beam stability", "positions", "ellipse fit", "orientation", command = self.change_fig)
        self.dropdown3.pack()
              
        # self.scale2 = tk.Scale(labelframe, label='ROI',
            # from_=1, to=50,
            # length=300, tickinterval=5,
            # showvalue='yes', 
            # orient='horizontal',
            # command = self.set_roi)
        # self.scale2.pack()
               
        # self.scale2 = tk.Scale(labelframe, label='gain',
            # from_=-10000, to=10000,
            # length=300, tickinterval=1,
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
        
        self.var1 = tk.IntVar(root); self.var1.set(1)
        b = tk.Checkbutton(labelframe, text="Centroid x position", command=lambda: self.toggle_graph('centroid_x'), variable=self.var1)
        b.pack(fill=tk.BOTH)
        self.var2 = tk.IntVar(root); self.var2.set(1)
        b = tk.Checkbutton(labelframe, text="Centroid y position", command=lambda: self.toggle_graph('centroid_y'), variable=self.var2)
        b.pack(fill=tk.BOTH)
        self.var3 = tk.IntVar(root); self.var3.set(1)
        b = tk.Checkbutton(labelframe, text="Peak x position", command=lambda: self.toggle_graph('peak_x'), variable=self.var3)
        b.pack(fill=tk.BOTH)
        self.var4 = tk.IntVar(root); self.var4.set(1)
        b = tk.Checkbutton(labelframe, text="Peak y position", command=lambda: self.toggle_graph('peak_y'), variable=self.var4)
        b.pack(fill=tk.BOTH)
        self.var5 = tk.IntVar(root); self.var5.set(1)
        b = tk.Checkbutton(labelframe, text="Ellipse_orientation", command=lambda: self.toggle_graph('ellipse_orientation'), variable=self.var5)
        b.pack(fill=tk.BOTH)
        
        b = tk.Button(labelframe, text="Sound", command=lambda: output.WavePlayerLoop(freq=440.*(self.peak_cross[0]/640.), length=10., volume=0.5).start())
        b.pack(fill=tk.BOTH)

        self.make_fig() #make figure environment
        self.init_camera() #initialise camera
        self.show_frame() #show video feed and update view with new information and refreshed plot etc

    def make_fig(self):
        '''Creates a matplotlib figure to be placed in the GUI.'''
        plt.clf()
        plt.cla()
        
        self.fig = plt.figure(figsize=(16,9), dpi=100)
        if self.fig_type == '2d surface':
            self.fig = Figure(figsize=(16,9), projection='3d', dpi=100)

        canvas = FigureCanvasTkAgg(self.fig, self) 
        canvas.show() 
        canvas.get_tk_widget().pack() 

        toolbar = NavigationToolbar2TkAgg(canvas, self) 
        toolbar.update() 
        canvas._tkcanvas.pack()
        
    def refresh_plot(self):
        '''Updates the matplotlib figure with new data.'''
        grayscale = self.analysis_frame #np.array(Image.fromarray(self.img).convert('L'))
        
        if self.fig_type == 'x cross profile':
            if self.peak_cross != None:
                xs = np.arange(self.width)[self.peak_cross[0]-20:self.peak_cross[0]+20]
                ys = grayscale[self.peak_cross[1],:]
                plt.plot(xs, ys[self.peak_cross[0]-20:self.peak_cross[0]+20],'k-')
                try:
                    popt,pcov = curve_fit(output.gauss,np.arange(self.width),ys,p0=[250,self.peak_cross[0],20], maxfev=50)
                    plt.plot(xs,output.gauss(np.arange(self.width),*popt)[self.peak_cross[0]-20:self.peak_cross[0]+20],'r-')
                except:
                    print 'Problem! Could not fit x gaussian!'
                
                # plt.xlim(0,self.width)
                plt.ylim(0,255)
        elif self.fig_type == 'y cross profile':
            if self.peak_cross != None:
                xs = np.arange(self.height)[self.peak_cross[1]-20:self.peak_cross[1]+20]
                ys = grayscale[:,self.peak_cross[0]]
                plt.plot(xs, ys[self.peak_cross[1]-20:self.peak_cross[1]+20],'k-')
                try:
                    popt,pcov = curve_fit(output.gauss,np.arange(self.height),ys,p0=[250,self.peak_cross[1],20], maxfev=50)
                    plt.plot(xs,output.gauss(np.arange(self.height),*popt)[self.peak_cross[1]-20:self.peak_cross[1]+20],'r-')
                except:
                    print 'Problem! Could not fit y gaussian!'
                
                # plt.xlim(0,self.height)
                plt.ylim(0,255)
        elif self.fig_type == '2d gaussian fit':
            if self.peak_cross != None:
                size = 50
                x, y = self.peak_cross
                img = grayscale[y-size/2:y+size/2, x-size/2:x+size/2]
                params = self.analyse.fit_gaussian(with_bounds=False)
                # # # # # # # # # # # # # # # self.analyse.plot_gaussian(plt.gca(), params)
                
                if self.colourmap is None:
                    cmap=plt.cm.BrBG
                elif self.colourmap == 2:
                    cmap=plt.cm.jet
                elif self.colourmap == 0:
                    cmap=plt.cm.autumn
                elif self.colourmap == 1:
                    cmap=plt.cm.bone
                plt.imshow(img, cmap=cmap, interpolation='nearest', origin='lower')
                
                xs = np.arange(50)
                ys_x = grayscale[self.peak_cross[1],:]
                ys_y = grayscale[:,self.peak_cross[0]]
                plt.plot(xs, 50 - (ys_x[self.peak_cross[0]-25:self.peak_cross[0]+25]/16),'y-', lw=2)
                plt.plot(ys_y[self.peak_cross[1]-25:self.peak_cross[1]+25]/16, xs,'y-', lw=2)
                   
                plt.xlim(0, size)
                plt.ylim(size, 0)
        elif self.fig_type == '2d surface':
            ax = self.fig.add_subplot(1,1,1,projection='3d')
            z = np.asarray(grayscale)[100:250,250:400]
            z = zoom(z, 0.25)
            mydata = z[::1,::1]
            x,y = np.mgrid[:mydata.shape[0],:mydata.shape[1]]
            ax.plot_surface(x,y,mydata,cmap=plt.cm.jet,rstride=1,cstride=1,linewidth=0.,antialiased=False)
            ax.set_zlim3d(0,255)
        elif self.fig_type == 'beam stability':
            plt.plot(self.centroid_hist_x, self.centroid_hist_y, 'r-', label='centroid')
            plt.plot(self.peak_hist_x, self.peak_hist_y, 'b-', label='peak cross')
            plt.xlim(0, self.width)
            plt.ylim(self.height, 0)
            plt.plot([0,0],'w.'); plt.legend(frameon=False)
        elif self.fig_type == 'positions':
            # plt.xlabel('$time$ $/s$'); plt.ylabel('$position$ $/\mu m$')
            if self.graphs['centroid_x']: plt.plot(self.running_time-self.running_time[0], self.centroid_hist_x, 'b-', label='centroid x coordinate')
            if self.graphs['centroid_y']: plt.plot(self.running_time-self.running_time[0], self.centroid_hist_y, 'r-', label='centroid y coordinate')
            if self.graphs['peak_x']: plt.plot(self.running_time-self.running_time[0], self.peak_hist_x, 'y-', label='peak x coordinate')
            if self.graphs['peak_y']: plt.plot(self.running_time-self.running_time[0], self.peak_hist_y, 'g-', label='peak y coordinate')
            if self.running_time[-1] - self.running_time[0] <= 60:
                plt.xlim(0, 60)
            else:
                index = np.searchsorted(self.running_time,[self.running_time[-1]-60,],side='right')[0]
                plt.xlim(self.running_time[index]-self.running_time[0], self.running_time[-1]-self.running_time[0])
            plt.ylim(0,self.width)
            plt.plot([0,0],'w.'); plt.legend(frameon=False)
        elif self.fig_type == 'orientation':
            if self.graphs['ellipse_orientation']: plt.plot(self.running_time-self.running_time[0], self.ellipse_hist_angle, 'c-', label='ellipse orientation')
            if self.running_time[-1] - self.running_time[0] <= 60:
                plt.xlim(0, 60)
            else:
                index = np.searchsorted(self.running_time,[self.running_time[-1]-60,],side='right')[0]
                plt.xlim(self.running_time[index]-self.running_time[0], self.running_time[-1]-self.running_time[0])
            plt.ylim(0,360)
            plt.plot([0,0],'w.'); plt.legend(frameon=False)
        elif self.fig_type == 'ellipse fit':
            if str(self.ellipse_angle) != 'nan':
                pts = self.analyse.get_ellipse_coords(a=self.ma, b=self.MA, x=self.ellipse_x, y=self.ellipse_y, angle=-self.ellipse_angle)
                plt.plot(pts[:,0], pts[:,1])
                
                MA_x, MA_y = self.ma*math.cos(self.ellipse_angle*(np.pi/180)), self.ma*math.sin(self.ellipse_angle*(np.pi/180))
                ma_x, ma_y = self.MA*math.sin(self.ellipse_angle*(np.pi/180)), self.MA*math.cos(self.ellipse_angle*(np.pi/180))
                MA_xtop, MA_ytop = int(self.ellipse_x + MA_x), int(self.ellipse_y + MA_y)
                MA_xbot, MA_ybot = int(self.ellipse_x - MA_x), int(self.ellipse_y - MA_y)
                ma_xtop, ma_ytop = int(self.ellipse_x + ma_x), int(self.ellipse_y + ma_y) #find corners of ellipse
                ma_xbot, ma_ybot = int(self.ellipse_x - ma_x), int(self.ellipse_y - ma_y)
                
                plt.plot(MA_xtop, MA_ytop, 'ro')
                plt.plot(MA_xbot, MA_ybot, 'bo')
                plt.plot(ma_xtop, ma_ybot, 'rx')
                plt.plot(ma_xbot, ma_ytop, 'bx')
                
                plt.xlim(0, self.width)
                plt.ylim(self.height, 0)
        else:
            print 'fig type not found.', self.fig_type
            
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
            self.refresh_plot()
            
    def change_style(self, option):
        '''Changes the style sheet used in the plot'''
        print self.style_sheet, option
        if self.style_sheet != option:
            print 'changed style sheet', option
            self.style_sheet = option
            plt.style.use(option)
            plt.cla()
            plt.clf()
            self.refresh_plot()
            
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
            print 'camera index change, now updating view...', self.camera_index
            self.cap.release()
            self.init_camera()
            self.show_frame()
    
    def change_colourmap(self, option):
        '''Changes the colourmap used in the camera feed.'''
        if self.colourmap != option:
            print 'changed colourmap to ', option
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
        _, frame = self.cap.read() #read camera input
        # frame = cv2.flip(frame, 1)
        
        if self.roi != 1: #apply region of interest scaling
            size = self.width/self.roi, self.height/self.roi
            analysis_frame = frame[(self.height/2)-(size[1]/2):(self.height/2)+(size[1]/2), (self.width/2)-(size[0]/2):(self.width/2)+(size[0]/2)]
            frame = cv2.resize(analysis_frame,None,fx=self.width/size[0], fy=self.height/size[1], interpolation = cv2.INTER_CUBIC)
        else:
            analysis_frame = frame
            
        if self.colourmap is None: #apply colourmap change
            cv2image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGBA)
        else:
            cv2image = cv2.applyColorMap(frame, self.colourmap)
            
        if self.angle != 0: #apply rotation
            cv2image = self.rotate_image(cv2image)
        
        # dim = np.shape(cv2image)
        
        self.analysis_frame = cv2.cvtColor(analysis_frame,cv2.COLOR_BGR2GRAY)
        
        cv2.line(cv2image, (50, 50), (50+28*2, 50), 255, thickness=4)
        cv2.putText(cv2image, str(round(((28*2*self.pixel_scale)/self.roi),2)) + ' um', (47, 45), cv2.FONT_HERSHEY_PLAIN, .8, (255,255,255))
        
        if self.active:
            # convert to greyscale
            # tracking = cv2.cvtColor(frame,cv2.COLOR_BGR2GRAY) #this should be analysis frame soon

            centroid = self.analyse.find_centroid()

            if centroid != (np.nan, np.nan):
            
                #if centroid then peak cross can be calculated quickly
                i,j = self.analyse.get_max(alpha=10, size=10) #make sure not too intensive
                if len(i) != 0 and len(j) != 0:
                    peak_cross = (sum(i) / len(i), sum(j) / len(j)) #chooses the average point for the time being!!
                    self.peak_cross = peak_cross
                else:
                    peak_cross = (np.nan, np.nan)
                    self.peak_cross = None
                 
                #less intensive to calculate on the cropped frame.
                # cv2.putText(cv2image,'Average Power: ' + str(round(np.mean(analysis_frame),2)), (10,255), cv2.FONT_HERSHEY_PLAIN, 1, (255,0,0)) #NEEDS WAY MORE WORK
                # cv2.putText(cv2image,'Total Power: ' + str(round(np.sum(analysis_frame),2)), (10,270), cv2.FONT_HERSHEY_PLAIN, 1, (255,0,0)) #masking, thresholding, correct units required
                
                # cv2.putText(cv2image,'Min Value: ' + str(np.min(analysis_frame)), (10,340), cv2.FONT_HERSHEY_PLAIN, 1, (255,255,255))
                
                # if peak_cross != (np.nan, np.nan):
                    # cv2.putText(cv2image,'Max Value: ' + str(np.max(analysis_frame)) + ' at (' + str(int(peak_cross[0]))+ ', ' + str(int(peak_cross[1])) + ')', (10,325), cv2.FONT_HERSHEY_PLAIN, 1, (255,255,255))
                    # cv2.circle(cv2image,(int(peak_cross[0]), int(peak_cross[1])),10,255,thickness=3)
                
                if centroid[0] < self.width or centroid[1] < self.height: #ensure centroid lies within correct regions
                    # cv2.circle(cv2image,centroid,10,255,thickness=10)
                    # cv2.putText(cv2image,'Centroid position: ' + str(centroid), (10,310), cv2.FONT_HERSHEY_PLAIN, 1, (255,255,255))
                    self.centroid = centroid
                    
                    cross_size = 20
                    cv2.line(cv2image, (centroid[0]-cross_size, centroid[1]), (centroid[0]+cross_size, centroid[1]), 255, thickness=1)
                    cv2.line(cv2image, (centroid[0], centroid[1]+cross_size), (centroid[0], centroid[1]-cross_size), 255, thickness=1)
                    
                else:
                    print 'Problem! Centroid out of image region.', centroid[0], centroid[1]
                    self.centroid = None
            else:
                self.centroid = None
                peak_cross = (np.nan, np.nan)
                self.peak_cross = None
        
            ellipses = self.analyse.find_ellipses() #fit ellipse and print data to screen
            if ellipses != None:
                (x,y),(ma,MA),angle = ellipses
                self.MA, self.ma, self.ellipse_x, self.ellipse_y, self.ellipse_angle = MA, ma, x, y, angle
                self.ellipticity, self.eccentricity = 1-(self.ma/self.MA), np.sqrt(1-(self.ma/self.MA)**2)
                cv2.ellipse(cv2image,ellipses,(0,255,0),1)
            else:
                self.MA, self.ma, self.ellipse_x, self.ellipse_y, self.ellipse_angle = np.nan, np.nan, np.nan, np.nan, np.nan
                self.ellipticity, self.eccentricity = np.nan, np.nan

            #record data that should be logged throughout time
            self.centroid_hist_x, self.centroid_hist_y = np.append(self.centroid_hist_x, centroid[0]), np.append(self.centroid_hist_y, centroid[1])
            self.peak_hist_x, self.peak_hist_y = np.append(self.peak_hist_x, peak_cross[0]), np.append(self.peak_hist_y, peak_cross[1])
            self.ellipse_hist_angle = np.append(self.ellipse_hist_angle, self.ellipse_angle)
            self.running_time = np.append(self.running_time, time.time()-self.pause_delay) #making sure to account for time that pause has been active

            self.pass_fail_testing()
            
            self.beam_width = self.analyse.get_beam_width(self.centroid)
            if self.beam_width is not None:
                self.beam_diameter = np.mean(self.beam_width)
            else:
                self.beam_diameter = None
                
        status_string = "Profiler: " + str(TrueFalse(self.active)) + " | " + "Centroid: " + str(TrueFalse(self.centroid)) + " | Peak Cross: " + str(TrueFalse(self.peak_cross) + " | Ellipse: " + str(TrueFalse(self.ellipse_angle)))
        self.status.set(status_string)
                
        imgtk = ImageTk.PhotoImage(image=Image.fromarray(cv2image))
            
        lmain.imgtk = imgtk
        lmain.configure(image=imgtk)
        lmain.after(10, self.show_frame)
        
        self.img = frame
        
        curr_time = time.time()
        if curr_time - self.plot_time > self.plot_tick and self.active: #if tickrate period elapsed, update the plot with new data
            self.refresh_plot()
            self.tick_counter += 1
            # if self.tick_counter > 10 and self.info_frame != None: #if 10 ticks passed update results window
                # self.info_frame.refresh_frame(self)
                # self.tick_counter = 0
            self.plot_time = time.time() #update plot time info
            
    def set_angle(self, option):
        '''Sets the rotation angle.'''
        self.angle = float(option)
        
    def set_roi(self, option):
        '''Sets the region of interest size'''
        print 'changed roi to', option
        self.roi = int(option)
        
    def profiler_active(self, option=False):
        '''Turns profiling mode on or off'''
        if option: #toggle box state if using key binding to toggle. if using box then sets correct box state, ticked or not ticked
            if self.variable4.get() == 1:
                box = False
            else:
                box = True
        else:
            if self.variable4.get() == 1:
                box = True
            else:
                box = False
                
        if box and not self.active:
            print 'Profiler ACTIVE'
            self.pause_delay += time.time()-self.last_pause
            self.active = True
            self.pb.select()
        elif not box and self.active:
            print 'Profiler INACTIVE'
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
        on_closing()
        
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
        
    def save_video(self, wait):
        start = time.time()
        # zeros array
        fourcc = cv2.VideoWriter_fourcc(*"MJPG")
        writer = None
        (h, w) = (None, None)
        zeros = None
        # loop over frames from the video stream
        while wait > time.time() - start:
            # grab the frame from the video stream and resize it to have a
            # maximum width of 300 pixels
            _, frame = self.cap.read()
            # check if the writer is None
            if writer is None:
                # store the image dimensions, initialzie the video writer,
                # and construct the zeros array
                (h, w) = (self.height, self.width)
                writer = cv2.VideoWriter("output.avi", fourcc, 30,
                    (w * 2, h * 2), True)
                zeros = np.zeros((h, w), dtype="uint8")
        
                # break the image into its RGB components, then construct the
                # RGB representation of each frame individually
                B, G, R = cv2.split(frame)
                R = cv2.merge([zeros, zeros, R])
                G = cv2.merge([zeros, G, zeros])
                B = cv2.merge([B, zeros, zeros])
             
                # construct the final output frame, storing the original frame
                # at the top-left, the red channel in the top-right, the green
                # channel in the bottom-right, and the blue channel in the
                # bottom-left
                output = np.zeros((h * 2, w * 2, 3), dtype="uint8")
                output[0:h, 0:w] = frame
                output[0:h, w:w * 2] = R
                output[h:h * 2, w:w * 2] = G
                output[h:h * 2, 0:w] = B
             
                # write the output frame to file
                writer.write(output)
            
    def save_csv(self):
        '''Saves .csv file of recorded data in columns.'''
        f = tkFileDialog.asksaveasfile(mode='w', initialfile='output.csv', defaultextension=".csv")
        if f is None: # asksaveasfile return `None` if dialog closed with "cancel".
            return
        output = np.column_stack((self.running_time.flatten(),self.centroid_hist_x.flatten(),self.centroid_hist_y.flatten()))
        np.savetxt('output.csv',output,delimiter=',',header='Laser Beam Profiler Data Export. \n running time, centroid_hist_x, centroid_hist_y')
    
    def calc_results(self):
        '''Opens calculation results window'''
        if self.info_frame != None:
            self.info_frame.close()
        self.info_frame = interface.InfoFrame(self)
        
    def change_config(self):
        '''Opens configuration window'''
        if self.config_frame != None:
            self.config_frame.close()
        self.config_frame = Config(self)
        if self.config_frame.result is not None:
            plot_tick, pixel_scale, angle = self.config_frame.result
            if plot_tick is not None:
                self.plot_tick = plot_tick
            if pixel_scale is not None:
                self.pixel_scale = pixel_scale
            if angle is not None:
                self.angle = angle
                
    def pass_fail_testing(self):
        '''Sets off alarm if pass/fail test criteria are not met.'''
        for index in np.where(np.array(self.raw_passfail) == 'True')[0]:
            x_lower, x_upper = [float(i) if i.replace('.','').isdigit() else i for i in self.raw_xbounds[index]]
            if index == 0:
                if self.beam_width is not None:
                    y_lower, y_upper = [float(i[5:]) for i in self.raw_ybounds[index]]
                    if self.beam_width[0] <= float(x_lower[5:]) or self.beam_width[0] >= float(x_upper[5:]) or self.beam_width[1] <= y_lower or self.beam_width[1] >= y_upper:
                        self.alert("Pass/Fail Test", "Beam Width has failed to meet criteria!")
                        self.raw_passfail[index] = 'False' #reset value
                        self.info_frame.refresh_frame(self)
            if index == 1:
                if self.beam_diameter is not None:
                    if self.beam_diameter <= x_lower or self.beam_diameter >= x_upper:
                        self.alert("Pass/Fail Test", "Beam Diameter has failed to meet criteria!")
                        self.raw_passfail[index] = 'False' #reset value
                        self.info_frame.refresh_frame(self)
            if index == 2:
                print 'check eff. beam diameter'
            if index == 3:
                if self.peak_cross is not None:
                    y_lower, y_upper = [float(i[5:]) for i in self.raw_ybounds[index]]
                    if self.peak_cross[0] <= float(x_lower[5:]) or self.peak_cross[0] >= float(x_upper[5:]) or self.peak_cross[1] <= y_lower or self.peak_cross[1] >= y_upper:
                            self.alert("Pass/Fail Test", "Peak Position has failed to meet criteria!")
                            self.raw_passfail[index] = 'False' #reset value
                            self.info_frame.refresh_frame(self)
            if index == 4:
                if self.centroid is not None:
                    y_lower, y_upper = [float(i[5:]) for i in self.raw_ybounds[index]]
                    if self.centroid[0] <= float(x_lower[5:]) or self.centroid[0] >= float(x_upper[5:]) or self.centroid[1] <= y_lower or self.centroid[1] >= y_upper:
                            self.alert("Pass/Fail Test", "Centroid Position has failed to meet criteria!")
                            self.raw_passfail[index] = 'False' #reset value
                            self.info_frame.refresh_frame(self)
            if index == 5:
                print 'check total power'
                               
        for index in np.where(np.array(self.ellipse_passfail) == 'True')[0]:
            x_lower, x_upper = [float(i) if i.replace('.','').isdigit() else i for i in self.ellipse_xbounds[index]]
            if index == 0:
                if self.ma <= float(x_lower[5:]) or self.ma >= float(x_upper[5:]):
                    y_lower, y_upper = [float(i[5:]) for i in self.ellipse_ybounds[index]]
                    if self.MA <= y_lower or self.MA >= y_upper:
                        self.alert("Pass/Fail Test", "Ellipse axes have failed to meet criteria!")
                        self.ellipse_passfail[index] = 'False'
                        self.info_frame.refresh_frame(self)
            if index == 1:
                if self.ellipticity <= x_lower or self.ellipticity >= x_upper:
                    self.alert("Pass/Fail Test", "Ellipticity has failed to meet criteria!")
                    self.ellipse_passfail[index] = 'False'
                    self.info_frame.refresh_frame(self)
            if index == 2:
                if self.eccentricity <= x_lower or self.eccentricity >= x_upper:
                    self.alert("Pass/Fail Test", "Eccentricity has failed to meet criteria!")
                    self.ellipse_passfail[index] = 'False'
                    self.info_frame.refresh_frame(self)
            if index == 3:
                if self.ellipse_angle <= x_lower or self.ellipse_angle >= x_upper:
                    self.alert("Pass/Fail Test", "Ellipse orientation has failed to meet criteria!")
                    self.ellipse_passfail[index] = 'False'
                    self.info_frame.refresh_frame(self)

    def alert(self, title, text):
        '''Makes a sound and shows alert window'''
        print '\a'
        self.info_window(title, text)
        # tkMessageBox.showerror(title, text)
        
    def toggle_graph(self, option):
        if self.graphs[option]:
            self.graphs[option] = False
        elif not self.graphs[option]:
            self.graphs[option] = True
        else:
            'Error. Something went wrong.'
        self.refresh_plot()
        
def on_closing():
        '''Closes the GUI.'''
        root.quit()
        root.destroy()
        c.cap.release()
        cv2.destroyAllWindows()
        
def TrueFalse(x):
    if x != (np.nan, np.nan) and x is not None and x and str(x) != 'nan':
        return 'ACTIVE'
    else:
        return 'INACTIVE'
        
c = Controller(root)
c.pack()
root.bind('<space>', lambda e: c.profiler_active(option=True))
root.protocol("WM_DELETE_WINDOW", on_closing)
root.mainloop()
