#!/usr/bin/python
# -*- coding: latin-1 -*-
          
import ConfigParser

import Tkinter as tk
import ttk
import tkFileDialog, tkMessageBox

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
from matplotlib.ticker import MultipleLocator, FormatStrFormatter

from utils import analysis
from utils import output
from utils import interface

import threading

root = tk.Tk()
lmain = tk.Label(root)
lmain.pack()
             
class Controller(tk.Frame):
    def __init__(self, parent=root):
        '''Initialises basic variables and GUI elements.'''
        self.active = False #whether profiler is active or just looking at webcam view
        self.pause_delay = 0 #time delay for when profiler is inactive. cumulatively adds.
        self.last_pause = time.time() #last time profiler was inactive
        self.plot_time = self.last_pause  #various parameters ters used throughout the profiler are initialised here
        self.angle = 0.0 #setting initial angles, region of interest, exposure time etc
        self.roi = 1
        self.exp = -1
        self.logs = [] #system logs
        self.toolbarbuttons = [] #active buttons on the toolbar
        self.toolbaractions = {'x cross profile': ['x cross profile', tk.PhotoImage(file='images/x_profile.gif')], #accessible images for toolbarbuttons
                              'y cross profile': ['y cross profile', tk.PhotoImage(file='images/y_profile.gif')],
                              '2d profile': ['2d profile', tk.PhotoImage(file='images/2d_profile.gif')],
                              '2d surface': ['2d surface', tk.PhotoImage(file='images/3d_profile.gif')],
                              'plot positions': ['positions', tk.PhotoImage(file='images/positions.gif')],
                              'beam stability': ['beam stability', tk.PhotoImage(file='images/beam_stability.gif')],
                              'plot orientation': ['orientation', tk.PhotoImage(file='images/orientation.gif')],
                              'increase exposure': ['inc_exp', tk.PhotoImage(file='images/increase_exp.gif')],
                              'decrease exposure': ['dec_exp', tk.PhotoImage(file='images/decrease_exp.gif')],
                              'view log': ['view_log', tk.PhotoImage(file='images/log.gif')],
                               'clear windows': ['clear windows', tk.PhotoImage(file='images/clear_windows.gif')]
                               }
        self.toolbaroptions = ['x Cross Profile', 'y Cross Profile'] #initial choices for active buttons on toolbar
        self.camera_index = 0
        self.beam_width, self.beam_diameter = None, None
        self.centroid = None
        self.peak_cross = None
        self.power = np.nan
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
        self.pixel_scale = 5.6 #default pixel scale of webcam in um
        
        self.width, self.height  = 1,1
        # self.stream = output.SoundFeedback(self)
                
        self.analysis_frame = None
        self.analyse = analysis.Analyse(self) #creates instance for analysis routines
        self.analyse.start()
        
        self.raw_passfail = ['False'] * 6
        self.ellipse_passfail = ['False'] * 4   
                        
        self.info_frame = None
        self.config_frame = None
        self.passfail_frame = None
        self.systemlog_frame = None
        self.toolbarconfig_frame = None
        
        self.bg_frame = 0
        self.bg_subtract = 0

        frame = tk.Frame.__init__(self, parent,relief=tk.GROOVE,width=100,height=100,bd=1)
        self.parent = parent
        self.var = tk.IntVar()
        
        self.statusbar = tk.Frame(self.parent)
        self.progress = interface.Progress(self)
        
        self.read_config() #overwrite prev init values with new config #NO MORE INIT VALUES BEYOND THIS POINT

        # **** Status Bar ****
        self.status = tk.StringVar()
        status_string = "Profiler: " + str(self.TrueFalse(self.active)) + " | " + "Centroid: " + str(self.TrueFalse(self.centroid)) + " | Ellipse: " + str(self.TrueFalse(self.ellipse_angle)) + " | Peak Cross: " + str(self.TrueFalse(self.peak_cross) + '                  ' + 'Zoom Factor: ' + str(self.roi) + ' | Exposure: ' + str(self.exp) + ' | Rotation: ' + str(self.angle))
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
        submenu = tk.Menu(controlMenu, tearoff=1)
        camera_count = self.count_cameras()
        submenu.add_command(label='0', command= lambda: self.change_cam(0))
        if camera_count > 2: submenu.add_command(label='1', command= lambda: self.change_cam(1))
        if camera_count >= 3: submenu.add_command(label='2', command= lambda: self.change_cam(2))
        if camera_count >= 4: submenu.add_command(label='3', command= lambda: self.change_cam(3))
        if camera_count >= 5: submenu.add_command(label='4', command= lambda: self.change_cam(4))
        if camera_count >= 6: submenu.add_command(label='5', command= lambda: self.change_cam(5))
        if camera_count >= 7: submenu.add_command(label='6', command= lambda: self.change_cam(6))
        controlMenu.add_command(label="Edit Config", command=self.change_config)
        controlMenu.add_separator()
        controlMenu.add_command(label="Calibrate background subtraction", command=self.progress.calibrate_bg)
        controlMenu.add_command(label="Reset background subtraction", command=self.progress.reset_bg)
        controlMenu.add_separator()
        controlMenu.add_command(label="View Log", command= self.view_log)
        controlMenu.add_cascade(label='Change Camera', menu=submenu, underline=0)
        controlMenu.add_separator()
        controlMenu.add_command(label="Clear Windows", command= lambda: tkMessageBox.showerror("Not done", "This is a temporary message"))
        menubar.add_cascade(label="Control", menu=controlMenu)

        windowMenu = tk.Menu(menubar, tearoff=1)
        submenu = tk.Menu(windowMenu, tearoff=1)
        windowMenu.add_command(label="Calculation Results", command=self.calc_results)
        windowMenu.add_command(label="x Cross Profile", command=lambda: self.change_fig('x cross profile'))
        windowMenu.add_command(label="y Cross Profile", command=lambda: self.change_fig('y cross profile'))
        windowMenu.add_command(label="2D Profile", command=lambda: self.change_fig('2d profile'))
        windowMenu.add_command(label="2D Surface", command=lambda: self.change_fig('2d surface'))
        windowMenu.add_separator()
        windowMenu.add_command(label="Plot Positions", command=lambda: self.change_fig('positions'))
        windowMenu.add_command(label="Plot Power", command=lambda: self.change_fig('power'))
        windowMenu.add_command(label="Plot Orientation", command=lambda: self.change_fig('orientation'))
        windowMenu.add_separator()
        windowMenu.add_command(label="Beam Stability", command=lambda: self.change_fig('beam stability'))
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
        
        self.variable4 = tk.IntVar()
        self.pb = tk.Checkbutton(self.toolbar, text="Profiler Active (<space>)", variable=self.variable4, command=self.profiler_active)
        self.pb.pack(side=tk.LEFT, padx=2, pady=2)
        
        self.cog = tk.PhotoImage(file='images/cog.gif')
        insertButt = tk.Button(self.toolbar, image=self.cog, text="Customise Toolbar", command=self.change_toolbar)
        insertButt.pack(side=tk.LEFT, padx=(2, 20), pady=2)
        
        self.toolbar.pack(side=tk.TOP, fill=tk.X)
       
        labelframe = tk.Frame(self) #left hand frame for various sliders and tweakables for direct control
        labelframe.pack(side=tk.LEFT) #.grid(row=0, column=0) 
               
        # self.variable3 = tk.StringVar(labelframe)
        # self.variable3.set("x cross profile")
        # self.dropdown3 = tk.OptionMenu(labelframe, self.variable3, "x cross profile", "y cross profile", "2d profile","2d surface", "beam stability", "positions", "orientation", command = self.change_fig)
        # self.dropdown3.pack()
              
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
        
        # b = tk.Button(labelframe, text="Start Sound", command=lambda: self.stream.streamer.start_stream())
        # b.pack(fill=tk.BOTH)
        # b = tk.Button(labelframe, text="Stop Sound", command=lambda: self.stream.streamer.stop_stream())
        # b.pack(fill=tk.BOTH)
        
        b = tk.Button(labelframe, text="Show Webcam", command=self.view_webcam)
        b.pack(fill=tk.BOTH)
        
        newbuttons = [obj for obj in self.toolbaroptions if obj not in [i[1] for i in self.toolbarbuttons]]
        for button in newbuttons:
            self.update_toolbar(button)
        
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
        
        self.change_style(self.style_sheet, set=True)
        
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
                    self.log('Problem! Could not fit x gaussian!')
                
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
                    self.log('Problem! Could not fit x gaussian!')
                
                # plt.xlim(0,self.height)
                plt.ylim(0,255)
        elif self.fig_type == '2d profile':
            if self.peak_cross != None:
                if str(self.MA) != 'nan':
                    size = 2*int(self.MA)+10
                else:
                    size = 50
                x, y = self.peak_cross
                img = grayscale[y-size/2:y+size/2, x-size/2:x+size/2]
                # # # # # params = self.analyse.fit_gaussian(with_bounds=False)
                # # # # # # # # # self.analyse.plot_gaussian(plt.gca(), params)
                
                if self.colourmap is None:
                    cmap=plt.cm.BrBG
                elif self.colourmap == 2:
                    cmap=plt.cm.jet
                elif self.colourmap == 0:
                    cmap=plt.cm.autumn
                elif self.colourmap == 1:
                    cmap=plt.cm.bone
                elif self.colourmap == 12:
                    cmap=output.parula_cm
                plt.imshow(img, cmap=cmap, interpolation='nearest', origin='lower')
                
                xs = np.arange(size)
                ys_x = grayscale[self.peak_cross[1],:]
                ys_y = grayscale[:,self.peak_cross[0]]
                norm_factor = np.max(ys_x)/(0.25*size)

                try:
                    plt.plot(xs, size - (ys_x[self.peak_cross[0]-(size/2):self.peak_cross[0]+(size/2)]/norm_factor),'y-', lw=2)
                    plt.plot(ys_y[self.peak_cross[1]-(size/2):self.peak_cross[1]+(size/2)]/norm_factor, xs,'y-', lw=2)
                except:
                    return
                
                try:
                    popt,pcov = curve_fit(output.gauss,np.arange(self.width),ys_x,p0=[250,self.peak_cross[0],20], maxfev=50)
                    plt.plot(xs,size - output.gauss(np.arange(self.width),*popt)[self.peak_cross[0]-(size/2):self.peak_cross[0]+(size/2)]/norm_factor,'r-', lw=2)
                except:
                    self.log('Problem! Could not fit x gaussian!')
                    
                try:
                    popt,pcov = curve_fit(output.gauss,np.arange(self.height),ys_y,p0=[250,self.peak_cross[1],20], maxfev=50)
                    plt.plot(output.gauss(np.arange(self.height),*popt)[self.peak_cross[1]-(size/2):self.peak_cross[1]+(size/2)]/norm_factor,xs,'r-', lw=2)
                except:
                    self.log('Problem! Could not fit y gaussian!')
                
                if str(self.ellipse_angle) != 'nan':
                    x_displace, y_displace = self.peak_cross[0]-(size/2), self.peak_cross[1]-(size/2)
                    
                    pts = self.analyse.get_ellipse_coords(a=self.ma, b=self.MA, x=self.ellipse_x, y=self.ellipse_y, angle=-self.ellipse_angle)
                    plt.plot(pts[:,0] - (x_displace), pts[:,1] - (y_displace))
                    
                    MA_x, MA_y = self.ma*math.cos(self.ellipse_angle*(np.pi/180)), self.ma*math.sin(self.ellipse_angle*(np.pi/180))
                    ma_x, ma_y = self.MA*math.sin(self.ellipse_angle*(np.pi/180)), self.MA*math.cos(self.ellipse_angle*(np.pi/180))
                    MA_xtop, MA_ytop = int(self.ellipse_x + MA_x), int(self.ellipse_y + MA_y)
                    MA_xbot, MA_ybot = int(self.ellipse_x - MA_x), int(self.ellipse_y - MA_y)
                    ma_xtop, ma_ytop = int(self.ellipse_x + ma_x), int(self.ellipse_y + ma_y) #find corners of ellipse
                    ma_xbot, ma_ybot = int(self.ellipse_x - ma_x), int(self.ellipse_y - ma_y)
                    
                    plt.plot([MA_xtop - (x_displace), MA_xbot - (x_displace)], [MA_ytop - (y_displace), MA_ybot - (y_displace)], 'w-', lw=2)
                    plt.plot([ma_xtop - (x_displace), ma_xbot - (x_displace)], [ma_ybot - (y_displace), ma_ytop - (y_displace)], 'w:', lw=2)
                    
                plt.xlim(0, size)
                plt.ylim(size, 0)
                
                # majorLocator = MultipleLocator(10)
                # majorFormatter = FormatStrFormatter('%d')
                # minorLocator = MultipleLocator(1)

                # ax = plt.gca()
                # ax.xaxis.set_major_locator(majorLocator)
                # ax.xaxis.set_major_formatter(majorFormatter)

                # # for the minor ticks, use no labels; default NullFormatter
                # ax.xaxis.set_minor_locator(minorLocator)
                # ax.yaxis.set_minor_locator(minorLocator)
                
                # ax.tick_params(which='both', width=1.5, color='w')
                # ax.tick_params(which='major', length=8)
                # ax.tick_params(which='minor', length=4)
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
            plt.plot([0,0],'w.',label=''); plt.legend(frameon=False)
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
            if len(self.running_time) > 0:
                if self.graphs['ellipse_orientation']: plt.plot(self.running_time-self.running_time[0], self.ellipse_hist_angle, 'c-', label='ellipse orientation')
                if self.running_time[-1] - self.running_time[0] <= 60:
                    plt.xlim(0, 60)
                else:
                    index = np.searchsorted(self.running_time,[self.running_time[-1]-60,],side='right')[0]
                    plt.xlim(self.running_time[index]-self.running_time[0], self.running_time[-1]-self.running_time[0])
            plt.ylim(0,360)
            plt.plot([0,0],'w.',label=''); plt.legend(frameon=False)
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
            self.log('Changed fig ' + option)
            self.fig_type = option
            plt.cla()
            plt.clf()
            self.refresh_plot()
            
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
        self.width, self.height = 640, 360
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
            print 'camera index change, now updating view...', self.camera_index
            self.cap.release()
            self.init_camera()
            self.show_frame()
    
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
        
        # cv2.line(cv2image, (50, 50), (50+28*2, 50), 255, thickness=4)
        # cv2.putText(cv2image, str(round(((28*2*self.pixel_scale)/self.roi),2)) + ' um', (47, 45), cv2.FONT_HERSHEY_PLAIN, .8, (255,255,255))
        
        if self.active:

            peak_cross = self.analyse.find_peak()
            self.peak_cross = peak_cross
            
            if peak_cross != (np.nan, np.nan):
                cross_size = 10
                screen_peak_cross = peak_cross[0]*(self.width/640), peak_cross[1]*(self.height/360)
                cv2.line(cv2image, (int(screen_peak_cross[0])-cross_size, int(screen_peak_cross[1])), (int(screen_peak_cross[0])+cross_size, int(screen_peak_cross[1])), 255, thickness=1)
                cv2.line(cv2image, (int(screen_peak_cross[0]), int(screen_peak_cross[1])+cross_size), (int(screen_peak_cross[0]), int(screen_peak_cross[1])-cross_size), 255, thickness=1)
                    
            centroid = self.analyse.get_centroid()
            if centroid != (np.nan, np.nan):

                # #if centroid then peak cross can be calculated quickly
                # # i,j = self.analyse.get_max(alpha=10, size=10) #make sure not too intensive
                # if len(i) != 0 and len(j) != 0:
                    # peak_cross = (sum(i) / len(i), sum(j) / len(j)) #chooses the average point for the time being!!
                    # self.peak_cross = peak_cross
                # else:
                    # peak_cross = (np.nan, np.nan)
                    # self.peak_cross = None
                
                if centroid[0] < self.width or centroid[1] < self.height: #ensure centroid lies within correct regions
                    self.centroid = centroid
                    
                    cross_size = 20
                    cv2.line(cv2image, (int(centroid[0])-cross_size, int(centroid[1])), (int(centroid[0])+cross_size, int(centroid[1])), 255, thickness=1)
                    cv2.line(cv2image, (int(centroid[0]), int(centroid[1])+cross_size), (int(centroid[0]), int(centroid[1])-cross_size), 255, thickness=1)
                    
                else:
                    self.log('Problem! Centroid out of image region. ' + str(centroid[0]) + ' ' + str(centroid[1]))
                    self.centroid = None
            else:
                self.centroid = None
                # peak_cross = (np.nan, np.nan)
                # self.peak_cross = None
        
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
                
        status_string = "Profiler: " + str(self.TrueFalse(self.active)) + " | " + "Centroid: " + str(self.TrueFalse(self.centroid)) + " | Ellipse: " + str(self.TrueFalse(self.ellipse_angle)) + " | Peak Cross: " + str(self.TrueFalse(self.peak_cross) + '                  ' + 'Zoom Factor: ' + str(self.roi) + ' | Exposure: ' + str(self.exp) + ' | Rotation: ' + str(self.angle))
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
            if self.tick_counter > 2 and self.info_frame != None: #if 10 ticks passed update results window
                self.info_frame.refresh_frame() #need to fix this line. but how?
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
        if self.info_frame != None:
            self.info_frame.close()
        self.info_frame = interface.InfoFrame(self)
        
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
            if power is not None:
                if power == '-':
                    self.power = np.nan
                else:
                    self.power = power
            if angle is not None:
                self.angle = angle
                
    def view_log(self):
        '''Opens System Log'''
        if self.systemlog_frame != None:
            self.systemlog_frame.close()
        self.systemlog_frame = interface.SystemLog(self)
        
    def view_webcam(self):
        '''Opens System Log'''
        # if self.systemlog_frame != None:
            # self.systemlog_frame.close()
        from utils import results
        self.webcam_frame = results.WebcamView(self)
            
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
            if self.toolbaractions[button.lower()][0] in ['inc_exp', 'dec_exp', 'view_log', 'clear windows']:
                if self.toolbaractions[button.lower()][0] == 'view_log':
                    self.toolbarbuttons.append([tk.Button(self.toolbar, text=button, image=self.toolbaractions[button.lower()][1], command=self.view_log), button])
                elif self.toolbaractions[button.lower()][0] == 'clear windows':
                    self.toolbarbuttons.append([tk.Button(self.toolbar, text=button, image=self.toolbaractions[button.lower()][1], command= lambda: tkMessageBox.showerror("Not done", "This is a temporary message")), button])
                elif self.toolbaractions[button.lower()][0] == 'inc_exp':
                    self.toolbarbuttons.append([tk.Button(self.toolbar, text=button, image=self.toolbaractions[button.lower()][1], command= lambda: self.adjust_exp(1)), button])
                elif self.toolbaractions[button.lower()][0] == 'dec_exp':
                    self.toolbarbuttons.append([tk.Button(self.toolbar, text=button, image=self.toolbaractions[button.lower()][1], command= lambda: self.adjust_exp(-1)), button])
            else:
                self.toolbarbuttons.append([tk.Button(self.toolbar, text=button, image=self.toolbaractions[button.lower()][1], command= lambda: self.change_fig(self.toolbaractions[button.lower()][0])), button])
        else:
            self.toolbarbuttons.append([tk.Button(self.toolbar, text=button), button])
        self.toolbarbuttons[-1][0].pack(side=tk.LEFT, padx=2, pady=2)
        
    def pass_fail_testing(self):
        '''Sets off alarm if pass/fail test criteria are not met.'''
        for index in np.where(np.array(self.raw_passfail) == 'True')[0]:
            x_lower, x_upper = [float(i) if i.replace('.','').isdigit() else i for i in self.raw_xbounds[index]]
            if index == 0:
                if self.beam_width is not None:
                    y_lower, y_upper = [float(i[5:]) for i in self.raw_ybounds[index]]
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
                    y_lower, y_upper = [float(i[5:]) for i in self.raw_ybounds[index]]
                    if self.peak_cross[0]*self.pixel_scale <= float(x_lower[5:]) or self.peak_cross[0]*self.pixel_scale >= float(x_upper[5:]) or self.peak_cross[1]*self.pixel_scale <= y_lower or self.peak_cross[1]*self.pixel_scale >= y_upper:
                            self.alert("Pass/Fail Test", "Peak Position has failed to meet criteria!")
                            self.raw_passfail[index] = 'False' #reset value
                            self.info_frame.refresh_frame()
            if index == 4:
                if self.centroid is not None:
                    y_lower, y_upper = [float(i[5:]) for i in self.raw_ybounds[index]]
                    if self.centroid[0]*self.pixel_scale <= float(x_lower[5:]) or self.centroid[0]*self.pixel_scale >= float(x_upper[5:]) or self.centroid[1]*self.pixel_scale <= y_lower or self.centroid[1]*self.pixel_scale >= y_upper:
                            self.alert("Pass/Fail Test", "Centroid Position has failed to meet criteria!")
                            self.raw_passfail[index] = 'False' #reset value
                            self.info_frame.refresh_frame()
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
        print '\a'
        self.info_window(title, text)
        self.log(text)
        # tkMessageBox.showerror(title, text)
        
    def log(self, text):
        print text
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
            if config.has_option('Miscellaneous', 'fig_type'):
                self.fig_type = config.get('Miscellaneous', 'fig_type')
        
    def clear_capture(self, capture):
        capture.release()
        cv2.destroyAllWindows()

    def count_cameras(self):
        n = 0
        for i in range(7):
            try:
                cap = cv2.VideoCapture(i)
                ret, frame = cap.read()
                cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                self.clear_capture(cap)
                n += 1
            except:
                self.clear_capture(cap)
                break
        return n
            
    def TrueFalse(self, x):
        if x != (np.nan, np.nan) and x is not None and x and str(x) != 'nan' and x is not False:
            if self.active:
                return 'ACTIVE'
            else:
                return 'INACTIVE'
        else:
            return 'INACTIVE'
        
def on_closing():
        '''Closes the GUI.'''
        root.quit()
        root.destroy()
        control.cap.release()
        cv2.destroyAllWindows()
        
w, h = root.winfo_screenwidth(), root.winfo_screenheight()
root.geometry("%dx%d+0+0" % (w, h))
control = Controller(root)
control.pack()
root.bind('<space>', lambda e: control.profiler_active(option=True))
root.protocol("WM_DELETE_WINDOW", on_closing)
root.mainloop()