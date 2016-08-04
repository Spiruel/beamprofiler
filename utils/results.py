#!/usr/bin/python
# -*- coding: latin-1 -*-

try:
    # for Python2
    import Tkinter as tk
    import ttk
except ImportError:
    # for Python3
    import tkinter as tk
    import tkinter.ttk as ttk
    
try:
    import ConfigParser
except ImportError:
    import configparser as ConfigParser
    
import numpy as np
import math

from scipy.optimize import curve_fit
from scipy.ndimage.interpolation import zoom

from . import interface, output

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2TkAgg
import matplotlib.pyplot as plt
from matplotlib.ticker import MultipleLocator, FormatStrFormatter

figures = 0

class WorkspaceManager(tk.Frame):
    counter = 0
    def __init__(self, parent, *args, **kwargs):      
        tk.Frame.__init__(self, *args, **kwargs)
        self.parent = parent

        # get screen width and height
        self.ws = parent.winfo_screenwidth() # width of the screen
        self.hs = parent.winfo_screenheight() # height of the screen
        
        self.w = self.ws/3
        self.h = self.hs/2
        self.titlebar_width = 30

        # calculate x and y coordinates for the Tk root window
        self.x = 0# (ws/2) - (w/2)
        self.y = 0#(hs/2) - (h/2)

        # set the dimensions of the screen 
        # and where it is placed
        # # parent.geometry('%dx%d+%d+%d' % (self.w, self.h, self.x, self.y))
               
        self.windowx, self.windowy = self.w,0

        self.windows = []
        self.instances = []
        self.vacancies = []
        self.workspace = []
        
    def shrink(self):
        self.w = self.w/2
        self.h = self.h/2
        self.parent.geometry('%dx%d+%d+%d' % (self.w, self.h, self.x, self.y))
        
    def enlarge(self):
        self.w = self.w*2
        self.h = self.h*2+self.titlebar_width
        self.parent.geometry('%dx%d+%d+%d' % (self.w, self.h, self.x, self.y))
        
    def get_geometry(self):
        geometry = []
        for window, instance in zip(self.windows, self.instances):
            w, h, x, y  = [float(i) for i in window.geometry().replace('x','+').split('+')]
            if instance.windowtype == 'plot':
                geometry.append((w/self.ws, h/self.hs, x/self.ws, y/self.hs, instance.windowtype, instance.fig_type))
            else:
                geometry.append((w/self.ws, h/self.hs, x/self.ws, y/self.hs, instance.windowtype))
        return geometry
        
    def save_workspace(self):
        self.workspace = []
        self.workspace += self.get_geometry()
        
        if self.get_geometry() == []:
            self.log('No workspace to save!')
        else:
            config = ConfigParser.ConfigParser()
            if config.read("config.ini") != []:
                config.set('Miscellaneous', 'workspace', str(self.workspace)[1:-1])    
                with open('config.ini', 'w') as configfile:
                    config.write(configfile)
                self.log('Written workspace values to config.ini')
            else:
                self.log('Could not write to config file. Workspace saved for this session only!')
            self.log('Saved workspace!')
    
    def load_workspace(self, workspace=None):
        if workspace is None:
            workspace = self.workspace
            
        if workspace == []:
            self.log('No saved workspace found')
        elif workspace == self.get_geometry():
            self.log('Workspace already loaded!')
            self.show_all()
        else:
            self.close_all()
            for window in workspace:
                ws = self.parent.winfo_screenwidth()
                hs = self.parent.winfo_screenheight()
                if len(window) == 6:
                    w, h, x, y, windowtype, graphtype = window
                else:
                    w, h, x, y, windowtype = window
                geom = (w*ws, h*hs)
                self.counter += 1
                if windowtype == 'webcam':
                    t = WebcamView(self, x*ws, y*hs, geom=geom)
                    self.webcam_frame = t
                elif windowtype == 'graph':
                    t = GraphView(self, x*ws, y*hs, geom=geom)
                elif windowtype == 'info':
                    t = InfoView(self, x*ws, y*hs, geom=geom)
                    self.info_frame = t
                elif windowtype == 'logs':
                    t = SystemLog(self, x*ws, y*hs, geom=geom)
                    self.systemlog_frame = t
                elif windowtype == 'plot':
                    t = PlotView(self, x*ws, y*hs, geom=geom, graphtype=graphtype)
                    self.plot_frames.append(t)
                else:
                    self.log('Error couldnt find window to be opened! '+ windowtype)
                self.instances.append(t)
            self.show_all()
            self.log('Loaded workspace!')
        
    def create_window(self, windowtype):
        if len(self.vacancies) >= 1:
            w = self.w
            h = self.h
            x,y,self.w,self.h  = self.vacancies[0]
            self.counter += 1
            t = windowtype
            self.instances.append(t)
            self.vacancies.pop(0)
            self.w = w
            self.h = h
        else:
            if self.windowx+self.w < self.ws:
                self.windowx += self.w
            else:
                self.windowx = 0
                self.windowy += self.h + self.titlebar_width
            self.counter += 1
            t = windowtype
            self.instances.append(t)
            
        return t
        
    def show_all(self):
        for window in self.windows:
            window.state(newstate='normal')
            window.deiconify()
                
    def close_all(self):
        instances = list(self.instances)
        for window in instances:
            window.close()
    
        self.windowx, self.windowy = self.w, 0
        self.vacancies = []
        # self.log('Closed all windows.')
        
    def view(self, option, graphtype=None):
        if option == 'webcam':
            return self.create_window(WebcamView(self,self.windowx,self.windowy))
        elif option == 'graph':
            return self.create_window(GraphView(self,self.windowx,self.windowy))
        elif option == 'info':
            return self.create_window(InfoView(self,self.windowx,self.windowy))
        elif option == 'logs':
            return self.create_window(SystemLog(self,self.windowx,self.windowy))
        elif option == 'plot':
            return self.create_window(PlotView(self,self.windowx,self.windowy,graphtype=graphtype))
                
class NewWindow(tk.Frame):
    def __init__(self, parent, x, y, geom):
        self.parent = parent
        self.window = tk.Toplevel(self.parent)
        self.window.bind('<space>', lambda e: self.parent.profiler_active(option=True)) #adds profiler hotkey to all windows
        
        self.x, self.y = x, y
        self.w = self.parent.w
        self.h = self.parent.h
        
        if geom is not None:
            self.window.geometry('%dx%d+%d+%d' % (geom[0], geom[1], self.x, self.y))
        else:
            self.window.geometry('%dx%d+%d+%d' % (self.w, self.h, self.x, self.y))

        self.parent.windows.append(self.window)
        # self.window.protocol("WM_DELETE_WINDOW", self.close_newwindow)
        
    def move(self):
        self.window.geometry('%dx%d+%d+%d' % (self.w, self.h, self.x, self.y))
        
    def close_newwindow(self, instance):
        self.parent.windows.remove(self.window)
        self.parent.instances.remove(instance)
        self.parent.vacancies.append((self.x, self.y, self.w, self.h))
        self.window.destroy()   

class PlotView(NewWindow, tk.Frame):
    def __init__(self, parent, x, y, geom=None, graphtype=None):
        self.parent = parent
        
        self.w = self.parent.ws/10
        self.h = self.parent.hs/5
        # calculate x and y coordinates for the Tk root window
        self.x = 0# (ws/2) - (w/2)
        self.y = 0#(hs/2) - (h/2)

        NewWindow.__init__(self, parent, x, y, geom)
        tk.Frame.__init__(self, parent)
        
        self.window.minsize(int(self.parent.ws/3),int(self.parent.hs/3))
        self.window.protocol("WM_DELETE_WINDOW", self.close)
        self.windowtype = 'plot'
        self.fig_type = graphtype
        self.window.wm_title(self.fig_type)
        self.init_frame()
        
    def init_frame(self):
        global figures

        '''Creates options menu and a matplotlib figure to be placed in the GUI.'''
        labelframe = tk.Frame(self.window) #left hand frame for various sliders and tweakables for direct control
        labelframe.pack(side=tk.LEFT)
        if self.fig_type == 'positions':
            self.var1 = tk.IntVar(self.parent.parent); self.var1.set(self.parent.graphs['centroid_x'])
            b = tk.Checkbutton(labelframe, text="Centroid x position", command=lambda: self.parent.toggle_graph('centroid_x'), variable=self.var1)
            b.pack(fill=tk.BOTH)
            self.var2 = tk.IntVar(self.parent.parent); self.var2.set(self.parent.graphs['centroid_y'])
            b = tk.Checkbutton(labelframe, text="Centroid y position", command=lambda: self.parent.toggle_graph('centroid_y'), variable=self.var2)
            b.pack(fill=tk.BOTH)
            self.var3 = tk.IntVar(self.parent.parent); self.var3.set(self.parent.graphs['peak_x'])
            b = tk.Checkbutton(labelframe, text="Peak x position", command=lambda: self.parent.toggle_graph('peak_x'), variable=self.var3)
            b.pack(fill=tk.BOTH)
            self.var4 = tk.IntVar(self.parent.parent); self.var4.set(self.parent.graphs['peak_y'])
            b = tk.Checkbutton(labelframe, text="Peak y position", command=lambda: self.parent.toggle_graph('peak_y'), variable=self.var4)
            b.pack(fill=tk.BOTH)
        elif self.fig_type == 'orientation':
            self.var5 = tk.IntVar(self.parent.parent); self.var5.set(self.parent.graphs['ellipse_orientation'])
            b = tk.Checkbutton(labelframe, text="Ellipse_orientation", command=lambda: self.parent.toggle_graph('ellipse_orientation'), variable=self.var5)
            b.pack(fill=tk.BOTH)
        elif self.fig_type == 'beam stability':
            self.var6 = tk.IntVar(self.parent.parent); self.var6.set(self.parent.graphs['centroid'])
            b = tk.Checkbutton(labelframe, text="Centroid", command=lambda: self.parent.toggle_graph('centroid'), variable=self.var6)
            b.pack(fill=tk.BOTH)
            self.var7 = tk.IntVar(self.parent.parent); self.var7.set(self.parent.graphs['peak cross'])
            b = tk.Checkbutton(labelframe, text="Peak Cross", command=lambda: self.parent.toggle_graph('peak cross'), variable=self.var7)
            b.pack(fill=tk.BOTH)
            
        #now create matplotlib figure
        plt.clf()
        plt.cla()
        
        self.fig_num = figures = figures + 1;
        #self.fig, self.ax = plt.subplots()
        self.fig = plt.figure(self.fig_num)
        self.ax = self.fig.add_subplot(111)

        canvas = FigureCanvasTkAgg(self.fig, master=self.window) 
        canvas.show() 
        canvas.get_tk_widget().pack(fill=tk.BOTH) 

        toolbar = NavigationToolbar2TkAgg(canvas, self.window) 
        toolbar.update() 
        canvas._tkcanvas.pack()
            
        self.parent.change_style(self.parent.style_sheet, set=True, verbose=False)
        self.refresh_frame()
        
    def refresh_frame(self):
        '''Updates the matplotlib figure with new data.'''
        fig = plt.figure(self.fig_num)
        self.ax = fig.gca()

        grayscale = self.parent.analysis_frame
        
        if self.fig_type == 'x cross profile':
            self.ax.set_xlabel('$position$ $/\mu m$'); self.ax.set_ylabel('$pixel$ $value$')
            if self.parent.peak_cross != None and self.parent.peak_cross != (np.nan, np.nan):
                if str(self.parent.MA) != 'nan':
                    size = 2*int(self.parent.MA)+10
                else:
                    size = 50
                xs = np.arange(self.parent.width)[int(self.parent.peak_cross[0]-size):int(self.parent.peak_cross[0]+size)]
                ys = grayscale[int(self.parent.peak_cross[1]),:]
                self.ax.plot(xs, ys[int(self.parent.peak_cross[0]-size):int(self.parent.peak_cross[0]+size)],'k-')
                try:
                    popt,pcov = curve_fit(output.gauss,np.arange(self.parent.width),ys,p0=[250,self.parent.peak_cross[0],size], maxfev=50)
                    self.ax.plot(xs,output.gauss(np.arange(self.parent.width),*popt)[self.parent.peak_cross[0]-size:self.parent.peak_cross[0]+size],'r-')
                except:
                    pass
                    # self.parent.log('Problem! Could not fit x gaussian!')
                
                # plt.xlim(0,self.parent.width)
                # plt.ylim(0,255)
                self.convert_axes(self.ax, x=True)
        elif self.fig_type == 'y cross profile':
            self.ax.set_xlabel('$position$ $/\mu m$'); self.ax.set_ylabel('$pixel$ $value$')
            if self.parent.peak_cross != None and self.parent.peak_cross != (np.nan, np.nan):
                if str(self.parent.MA) != 'nan':
                    size = 2*int(self.parent.MA)+10
                else:
                    size = 50
                xs = np.arange(self.parent.height)[int(self.parent.peak_cross[1]-size):int(self.parent.peak_cross[1]+size)]
                ys = grayscale[:,self.parent.peak_cross[0]]
                self.ax.plot(xs, ys[int(self.parent.peak_cross[1]-size):int(self.parent.peak_cross[1]+size)],'k-')
                try:
                    popt,pcov = curve_fit(output.gauss,np.arange(self.parent.height),ys,p0=[250,self.parent.peak_cross[1],size], maxfev=50)
                    self.ax.plot(xs,output.gauss(np.arange(self.parent.height),*popt)[self.parent.peak_cross[1]-size:self.parent.peak_cross[1]+size],'r-')
                except:
                    pass
                    # self.parent.log('Problem! Could not fit x gaussian!')
                
                # plt.xlim(0,self.parent.height)
                # plt.ylim(0,255)
                self.convert_axes(self.ax, x=True)
        elif self.fig_type == '2d profile':
            self.ax.set_xlabel('$position$ $/\mu m$'); self.ax.set_ylabel('$position$ $/\mu m$')
            if self.parent.peak_cross is not None and self.parent.peak_cross != (np.nan, np.nan):
                if self.parent.colourmap is None:
                    self.cmap=plt.cm.BrBG
                elif self.parent.colourmap == 2:
                    self.cmap=plt.cm.jet
                elif self.parent.colourmap == 0:
                    self.cmap=plt.cm.autumn
                elif self.parent.colourmap == 1:
                    self.cmap=plt.cm.bone
                elif self.parent.colourmap == 12:
                    self.cmap=output.parula_cm
                        
                if str(self.parent.MA) != 'nan':
                    size = 2*int(self.parent.MA)+10
                else:
                    size = 50
                        
                x, y = [int(i) for i in self.parent.peak_cross]
                img = grayscale[y-size/2:y+size/2, x-size/2:x+size/2]
                # # # # # params = self.parent.analyse.fit_gaussian(with_bounds=False)
                # # # # # # # # # self.parent.analyse.plot_gaussian(plt.gca(), params)
                
                self.ax.imshow(img, cmap=self.cmap, interpolation='nearest', origin='lower')
                
                xs = np.arange(size)
                ys_x = grayscale[self.parent.peak_cross[1],:]
                ys_y = grayscale[:,self.parent.peak_cross[0]]
                norm_factor = np.max(ys_x)/(0.25*size)

                try:
                    self.ax.plot(xs, size - (ys_x[self.parent.peak_cross[0]-(size/2):self.parent.peak_cross[0]+(size/2)]/norm_factor),'y-', lw=2)
                    self.ax.plot(ys_y[self.parent.peak_cross[1]-(size/2):self.parent.peak_cross[1]+(size/2)]/norm_factor, xs,'y-', lw=2)
                except:
                    return
                
                try:
                    popt,pcov = curve_fit(output.gauss,np.arange(self.parent.width),ys_x,p0=[250,self.parent.peak_cross[0],20], maxfev=50)
                    self.ax.plot(xs,size - output.gauss(np.arange(self.parent.width),*popt)[self.parent.peak_cross[0]-(size/2):self.parent.peak_cross[0]+(size/2)]/norm_factor,'r-', lw=2)
                except:
                    pass
                    # self.parent.log('Problem! Could not fit x gaussian!')
                    
                try:
                    popt,pcov = curve_fit(output.gauss,np.arange(self.parent.height),ys_y,p0=[250,self.parent.peak_cross[1],20], maxfev=50)
                    self.ax.plot(output.gauss(np.arange(self.parent.height),*popt)[self.parent.peak_cross[1]-(size/2):self.parent.peak_cross[1]+(size/2)]/norm_factor,xs,'r-', lw=2)
                except:
                    pass
                    # self.parent.log('Problem! Could not fit y gaussian!')
                
                if str(self.parent.ellipse_angle) != 'nan':
                    x_displace, y_displace = self.parent.peak_cross[0]-(size/2), self.parent.peak_cross[1]-(size/2)
                    
                    pts = self.parent.analyse.get_ellipse_coords(a=self.parent.ma, b=self.parent.MA, x=self.parent.ellipse_x, y=self.parent.ellipse_y, angle=-self.parent.ellipse_angle)
                    self.ax.plot(pts[:,0] - (x_displace), pts[:,1] - (y_displace))
                    
                    MA_x, MA_y = self.parent.ma*math.cos(self.parent.ellipse_angle*(np.pi/180)), self.parent.ma*math.sin(self.parent.ellipse_angle*(np.pi/180))
                    ma_x, ma_y = self.parent.MA*math.sin(self.parent.ellipse_angle*(np.pi/180)), self.parent.MA*math.cos(self.parent.ellipse_angle*(np.pi/180))
                    MA_xtop, MA_ytop = int(self.parent.ellipse_x + MA_x), int(self.parent.ellipse_y + MA_y)
                    MA_xbot, MA_ybot = int(self.parent.ellipse_x - MA_x), int(self.parent.ellipse_y - MA_y)
                    ma_xtop, ma_ytop = int(self.parent.ellipse_x + ma_x), int(self.parent.ellipse_y + ma_y) #find corners of ellipse
                    ma_xbot, ma_ybot = int(self.parent.ellipse_x - ma_x), int(self.parent.ellipse_y - ma_y)
                    
                    self.ax.plot([MA_xtop - (x_displace), MA_xbot - (x_displace)], [MA_ytop - (y_displace), MA_ybot - (y_displace)], 'w-', lw=2)
                    self.ax.plot([ma_xtop - (x_displace), ma_xbot - (x_displace)], [ma_ybot - (y_displace), ma_ytop - (y_displace)], 'w:', lw=2)
                    
                self.ax.set_xlim(0, size)
                self.ax.set_ylim(size, 0)
                
                self.convert_axes(self.ax, x=True, y=True)
                
                xlabels = np.array(self.ax.get_xticks().tolist())
                self.ax.set_xticklabels([int(i)+((self.parent.peak_cross[0]-(size/2))*self.parent.pixel_scale) for i in xlabels])
                ylabels = np.array(self.ax.get_yticks().tolist())
                self.ax.set_yticklabels([int(i)+((self.parent.peak_cross[1]-(size/2))*self.parent.pixel_scale) for i in ylabels])
        elif self.fig_type == 'beam stability':
            self.ax.set_xlabel('$position$ $/\mu m$'); self.ax.set_ylabel('$position$ $/\mu m$')
            if self.parent.graphs['centroid']: self.ax.plot(self.parent.centroid_hist_x, self.parent.centroid_hist_y, 'r-', label='centroid')
            if self.parent.graphs['peak cross']: self.ax.plot(self.parent.peak_hist_x, self.parent.peak_hist_y, 'b-', label='peak cross')
            self.ax.set_xlim(0, self.parent.width); self.ax.set_ylim(self.parent.height, 0)
            self.convert_axes(self.ax, x=True, y=True)
            self.ax.plot([0,0],'w.',label=''); self.ax.legend(frameon=False)
        elif self.fig_type == 'positions':
            self.ax.set_xlabel('$time$ $/s$'); self.ax.set_ylabel('$position$ $/\mu m$')
            if len(self.parent.running_time) > 0:
                if self.parent.graphs['centroid_x']: self.ax.plot(self.parent.running_time-self.parent.running_time[0], self.parent.centroid_hist_x, 'b-', label='centroid x coordinate')
                if self.parent.graphs['centroid_y']: self.ax.plot(self.parent.running_time-self.parent.running_time[0], self.parent.centroid_hist_y, 'r-', label='centroid y coordinate')
                if self.parent.graphs['peak_x']: self.ax.plot(self.parent.running_time-self.parent.running_time[0], self.parent.peak_hist_x, 'y-', label='peak x coordinate')
                if self.parent.graphs['peak_y']: self.ax.plot(self.parent.running_time-self.parent.running_time[0], self.parent.peak_hist_y, 'g-', label='peak y coordinate')
                if self.parent.running_time[-1] - self.parent.running_time[0] <= 60:
                    self.ax.set_xlim(0, 60)
                else:
                    index = np.searchsorted(self.parent.running_time,[self.parent.running_time[-1]-60,],side='right')[0]
                    self.ax.set_xlim(self.parent.running_time[index]-self.parent.running_time[0], self.parent.running_time[-1]-self.parent.running_time[0])
                self.convert_axes(self.ax, y=True)
                self.ax.plot([0,0],'w.',label=''); self.ax.legend(frameon=False)
        elif self.fig_type == 'orientation':
            self.ax.set_xlabel('$time$ $/s$'); self.ax.set_ylabel('$angle$ $/deg$')
            if len(self.parent.running_time) > 0:
                if self.parent.graphs['ellipse_orientation']: self.ax.plot(self.parent.running_time-self.parent.running_time[0], self.parent.ellipse_hist_angle, 'c-', label='ellipse orientation')
                if self.parent.running_time[-1] - self.parent.running_time[0] <= 60:
                    self.ax.set_xlim(0, 60)
                else:
                    index = np.searchsorted(self.parent.running_time,[self.parent.running_time[-1]-60,],side='right')[0]
                    self.ax.set_xlim(self.parent.running_time[index]-self.parent.running_time[0], self.parent.running_time[-1]-self.parent.running_time[0])
            self.ax.plot([0,0],'w.',label=''); self.ax.legend(frameon=False)
        else:
            self.parent.log('Fig type not found. ' + self.fig_type)
            
        # ax[0].hold(True)
        # ax[1].hold(True)
        fig.canvas.draw() 
        
        for axis in self.fig.get_axes():
            axis.clear()
            
    def convert_axes(self, ax, x=False, y=False):
        if x:
            xlabels = np.array(ax.get_xticks().tolist())*self.parent.pixel_scale
            ax.set_xticklabels([int(i) for i in xlabels])
        if y:
            ylabels = np.array(ax.get_yticks().tolist())*self.parent.pixel_scale
            ax.set_yticklabels([int(i) for i in ylabels])
        
    def close(self):
        fig = plt.figure(self.fig_num)
        for plot in self.parent.plot_frames:
            if plot.fig_type == self.fig_type:
                self.parent.plot_frames.remove(plot)
        fig.clf()
        self.close_newwindow(self)
        self.window.destroy()
        
class WebcamView(NewWindow):
    def __init__(self, parent, x, y, geom=None):
        self.parent = parent
        
        self.w = self.parent.ws/10
        self.h = self.parent.hs/5
        # calculate x and y coordinates for the Tk root window
        self.x = 0# (ws/2) - (w/2)
        self.y = 0#(hs/2) - (h/2)
        NewWindow.__init__(self, parent, x, y, geom)
        
        self.lmain2 = tk.Label(self.window)
        self.lmain2.pack(expand=1, fill=tk.BOTH)
        
        self.window.wm_title("Webcam View")
        self.window.minsize(int(self.parent.ws/3.),int(self.parent.hs/3.))
        self.window.protocol("WM_DELETE_WINDOW", self.close)
        self.windowtype = 'webcam'
        
        self.show_frame()
        
    def show_frame(self):
        self.lmain2.imgtk = self.parent.imgtk
        self.lmain2.configure(image=self.parent.imgtk)
        
    def close(self):
        self.parent.webcam_frame = None
        self.close_newwindow(self)
        self.window.destroy()
        
class SystemLog(NewWindow):  
    def __init__(self, parent, x, y, geom=None):
        self.parent = parent

        self.w = self.parent.ws/10
        self.h = self.parent.hs/5
        # calculate x and y coordinates for the Tk root window
        self.x = 0# (ws/2) - (w/2)
        self.y = 0#(hs/2) - (h/2)
        NewWindow.__init__(self, parent, x, y, geom)

        self.window.wm_title("System Log")
        self.window.minsize(int(self.parent.ws/9.6),int(self.parent.hs/3.))
        self.window.protocol("WM_DELETE_WINDOW", self.close)
        self.windowtype = 'logs'
        
        self.tex = tk.Text(master=self.window)
        self.tex.config(state=tk.DISABLED)
        self.tex.pack(side=tk.RIGHT)

        self.callback() #show values on start
        
    def cbc(self, id, tex):
        return lambda : self.callback(id, tex)

    def callback(self):
        self.tex.config(state=tk.NORMAL)
        self.tex.delete('1.0', tk.END)
        for error in self.parent.logs:
            self.tex.insert(tk.END, error+'\n')
        self.tex.see(tk.END)             # Scroll if necessary
        self.tex.config(state=tk.DISABLED)
        
    def close(self):
        self.parent.systemlog_frame = None
        self.close_newwindow(self)
        self.window.destroy()
        
class InfoView(NewWindow):
    def __init__(self, parent, x, y, geom=None):
        self.parent = parent

        self.w = self.parent.ws/10
        self.h = self.parent.hs/5
        # calculate x and y coordinates for the Tk root window
        self.x = 0# (ws/2) - (w/2)
        self.y = 0#(hs/2) - (h/2)
        NewWindow.__init__(self, parent, x, y, geom)

        self.window.wm_title("Calculation Results")
        self.window.minsize(int(self.parent.ws/2),int(self.parent.hs/3.5))
        self.window.protocol("WM_DELETE_WINDOW", self.close)
        self.windowtype = 'info'
                
        self.passfail_frame = None
        
        self.tree = ttk.Treeview(self.window,columns=("Unit","Value","Pass/Fail Test","Min.","Max.","Min.","Max."))
        self.tree.heading("#0", text='Parameter', anchor=tk.W)
        self.tree.column("#0", stretch=0)
        self.tree.heading("#1", text='Unit', anchor=tk.W)
        self.tree.column("#1",  minwidth=0, width=47, stretch=1)
        self.tree.heading("#2", text='Value', anchor=tk.W)
        self.tree.column("#2",  minwidth=0, width=150, stretch=1)
        self.tree.heading("#3", text='Pass/Fail Test', anchor=tk.W)
        self.tree.column("#3",  minwidth=0, width=80, stretch=1)
        self.tree.heading("#4", text='Min.', anchor=tk.W)
        self.tree.column("#4",  minwidth=0, width=65, stretch=1)
        self.tree.heading("#5", text='Max.', anchor=tk.W)
        self.tree.column("#5",  minwidth=0, width=65, stretch=1)
        self.tree.heading("#6", text='Min.', anchor=tk.W)
        self.tree.column("#6",  minwidth=0, width=65, stretch=1)
        self.tree.heading("#7", text='Max.', anchor=tk.W)
        self.tree.column("#7",  minwidth=0, width=65, stretch=1)

        if self.parent.beam_width is None:
            self.parent.beam_width = (np.nan, np.nan)
        if self.parent.peak_cross is None: 
            self.parent.peak_cross = (np.nan, np.nan)
        if self.parent.centroid is None:
            self.parent.centroid = (np.nan, np.nan)
            
        self.pixel_scale = self.parent.pixel_scale #get pixel scale conversion
        self.raw_rows = ["Beam Width (1/e²)", "Beam Diameter (1/e²)", "Peak Pixel Value", "Peak Position", "Centroid Position", "Power Density"]
        self.raw_units = ["µm","µm"," ","µm","µm","W/µm²"]
        square = lambda x: x**2 if x is not None else np.nan
        self.raw_values = ['(' + self.info_format(self.parent.beam_width[0], convert=True) + ', ' + self.info_format(self.parent.beam_width[1], convert=True) + ')', self.info_format(self.parent.beam_diameter, convert=True), self.info_format(np.max(self.parent.analysis_frame)), '(' + self.info_format(self.parent.peak_cross[0], convert=True) + ', ' + self.info_format(self.parent.peak_cross[1], convert=True) + ')', '(' + self.info_format(self.parent.centroid[0], convert=True) + ', ' + self.info_format(self.parent.centroid[1], convert=True) + ')', "{:.2E}".format((255000/square(self.parent.beam_diameter))*self.parent.power)]
        self.ellipse_rows = ["Ellipse axes", "Ellipticity", "Eccentricity", "Orientation"]
        self.ellipse_units = ["µm", " ", " ", "deg"]
        self.ellipse_values = ['(' + self.info_format(self.parent.MA, convert=True) + ', ' + self.info_format(self.parent.ma, convert=True) + ')', self.info_format(self.parent.ellipticity), self.info_format(self.parent.eccentricity), self.info_format(self.parent.ellipse_angle)]
                  
        self.raw_xbounds = [('x ≥ 0.00', 'x ≤ 0.00'), #for pass/fail testing
                        ('0.00', '0.00'),
                        ('0.00', '255.00'),
                        ('x ≥ 0.00', 'x ≤ ' + '{0:.2f}'.format(self.parent.width*self.parent.pixel_scale)),
                        ('x ≥ 0.00', 'x ≤ ' + '{0:.2f}'.format(self.parent.width*self.parent.pixel_scale)),
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
                        ('y ≥ 0.00', 'y ≤ ' + '{0:.2f}'.format(self.parent.height*self.parent.pixel_scale)),
                        ('y ≥ 0.00', 'y ≤ ' + '{0:.2f}'.format(self.parent.height*self.parent.pixel_scale)),
                        (' ', ' ')
                        ]
        self.ellipse_ybounds = [('m ≥ 0.00', 'm ≤ 0.00'),
                        (' ', ' '),
                        (' ', ' '),
                        (' ', ' ')
                        ]
                        
        self.tree.insert("",iid="1", index="end",text="Raw Data Measurement")
        for i in range(len(self.raw_rows)):
            self.tree.insert("1",iid="1"+str(i), index="end", text=self.raw_rows[i], value=(self.raw_units[i], self.raw_values[i], self.parent.raw_passfail[i], self.raw_xbounds[i][0], self.raw_xbounds[i][1], self.raw_ybounds[i][0], self.raw_ybounds[i][1]))
        self.tree.see("14")
        self.tree.insert("",iid="2", index="end",text="Ellipse (fitted)")
        for i in range(len(self.ellipse_rows)):
            self.tree.insert("2",iid="2"+str(i), index="end", text=self.ellipse_rows[i], value=(self.ellipse_units[i], self.ellipse_values[i], self.parent.ellipse_passfail[i], self.ellipse_xbounds[i][0], self.ellipse_xbounds[i][1], self.ellipse_ybounds[i][0], self.ellipse_ybounds[i][1]))
        self.tree.see("23")
        
        self.tree.pack(expand=True,fill=tk.BOTH)
        
        button_refresh = tk.Button(self.window, text="refresh", command=lambda: self.refresh_frame())
        button_refresh.pack(padx=5, pady=20, side=tk.LEFT)
        button_pf = tk.Button(self.window, text="toggle pass/fail test", command=lambda: self.pass_fail())
        button_pf.pack(padx=5, pady=20, side=tk.LEFT)
        button_edit = tk.Button(self.window, text="edit", command=lambda: self.edit())
        button_edit.pack(padx=5, pady=20, side=tk.LEFT)
        self.refresh_frame()
    
    def refresh_frame(self):
        self.curr_item = self.tree.focus() #problem because widget doesnt exist anymore
        
        if self.parent.beam_width is None:
            self.parent.beam_width = (np.nan, np.nan)
        if self.parent.peak_cross is None: 
            self.parent.peak_cross = (np.nan, np.nan)
        if self.parent.centroid is None:
            self.parent.centroid = (np.nan, np.nan)
            
        square = lambda x: x**2 if x is not None else np.nan #3e-15 power dens before sat
        self.raw_values = ['(' + self.info_format(self.parent.beam_width[0], convert=True) + ', ' + self.info_format(self.parent.beam_width[1], convert=True) + ')', self.info_format(self.parent.beam_diameter, convert=True), self.info_format(np.max(self.parent.analysis_frame)), '(' + self.info_format(self.parent.peak_cross[0], convert=True) + ', ' + self.info_format(self.parent.peak_cross[1], convert=True) + ')', '(' + self.info_format(self.parent.centroid[0], convert=True) + ', ' + self.info_format(self.parent.centroid[1], convert=True) + ')', "{:.2E}".format((255000/square(self.parent.beam_diameter))*self.parent.power)]
        self.ellipse_values = ['(' + self.info_format(self.parent.MA, convert=True) + ', ' + self.info_format(self.parent.ma, convert=True) + ')', self.info_format(self.parent.ellipticity), self.info_format(self.parent.eccentricity), self.info_format(self.parent.ellipse_angle)]

        self.tree.delete(*self.tree.get_children())
        self.tree.insert("",iid="1", index="end",text="Raw Data Measurement")
        for i in range(len(self.raw_rows)):
            self.tree.insert("1",iid="1"+str(i), index="end", text=self.raw_rows[i], value=(self.raw_units[i], self.raw_values[i], self.parent.raw_passfail[i], self.raw_xbounds[i][0], self.raw_xbounds[i][1], self.raw_ybounds[i][0], self.raw_ybounds[i][1]))
        self.tree.see("14")
        self.tree.insert("",iid="2", index="end",text="Ellipse (fitted)")
        for i in range(len(self.ellipse_rows)):
            self.tree.insert("2",iid="2"+str(i), index="end", text=self.ellipse_rows[i], value=(self.ellipse_units[i], self.ellipse_values[i], self.parent.ellipse_passfail[i], self.ellipse_xbounds[i][0], self.ellipse_xbounds[i][1], self.ellipse_ybounds[i][0], self.ellipse_ybounds[i][1]))
        self.tree.see("23")

        self.tree.selection_set(self.curr_item)
        self.tree.focus(self.curr_item)
        
    def pass_fail(self):
        selected_item = self.tree.selection()
        if len(selected_item) == 1:
            if len(str(selected_item[0])) == 2:
                index, row_num = map(int,str(selected_item[0]))
                self.parent.log('toggling pass/fail state')
                if index == 1:
                    if self.parent.raw_passfail[row_num] == 'True':
                        self.parent.raw_passfail[row_num] = 'False'
                    else:
                        self.parent.raw_passfail[row_num] = 'True'
                elif index == 2:
                    if self.parent.ellipse_passfail[row_num] == 'True':
                        self.parent.ellipse_passfail[row_num] = 'False'
                    else:
                        self.parent.ellipse_passfail[row_num] = 'True'
                self.refresh_frame()
            
    def edit(self):
        selected_item = self.tree.selection()
        if len(selected_item) == 1:
            if len(str(selected_item[0])) == 2:
                index, row_num = map(int,str(selected_item[0]))
                if index == 1:
                    if self.raw_ybounds[row_num] != (' ', ' '):
                        self.parent.log('getting x and y bounds')
                        passfailbounds = self.change_pass_fail(True, (self.raw_xbounds[row_num], self.raw_ybounds[row_num])) #get x and y bounds
                        if passfailbounds is not None:
                            self.raw_xbounds[row_num] = (self.raw_xbounds[row_num][0][:5] + passfailbounds[0], self.raw_xbounds[row_num][1][:5] + passfailbounds[1])
                            self.raw_ybounds[row_num] = (self.raw_ybounds[row_num][0][:5] + passfailbounds[2], self.raw_ybounds[row_num][1][:5] + passfailbounds[3])
                    else:
                        self.parent.log('getting x bounds')
                        passfailbounds = self.change_pass_fail(False, self.raw_xbounds[row_num]) #get just x bounds
                        if passfailbounds is not None:
                            self.raw_xbounds[row_num] = passfailbounds[0], passfailbounds[1]
                elif index == 2:
                    if self.ellipse_ybounds[row_num] != (' ', ' '):
                        self.parent.log('getting x and y bounds')
                        passfailbounds = self.change_pass_fail(True, (self.ellipse_xbounds[row_num], self.ellipse_ybounds[row_num])) #get x and y bounds
                        if passfailbounds is not None:
                            self.ellipse_xbounds[row_num] = (self.ellipse_xbounds[row_num][0][:5] + passfailbounds[0], self.ellipse_xbounds[row_num][1][:5] + passfailbounds[1])
                            self.ellipse_ybounds[row_num] = (self.ellipse_ybounds[row_num][0][:5] + passfailbounds[2], self.ellipse_ybounds[row_num][1][:5] + passfailbounds[3])
                    else:
                        self.parent.log('getting x bounds')
                        passfailbounds = self.change_pass_fail(False, self.ellipse_xbounds[row_num]) #get just x bounds
                        if passfailbounds is not None:
                            self.ellipse_xbounds[row_num] = (passfailbounds[0], passfailbounds[1])

                self.refresh_frame()
                    
    def change_pass_fail(self, manyopt, bounds):
        '''Opens passfail window'''
        if self.passfail_frame != None:
            self.passfail_frame.close()
        self.passfail_frame = interface.PassFailDialogue(self.parent, manyopt, bounds)
        if self.passfail_frame.result is not None:
            return self.passfail_frame.result
            
    def info_format(self, param, convert=False, dp=2):
        '''Format data to 2.d.p and converts from pixels to um if needed.'''
        if convert:
            convert_factor = float(self.pixel_scale)
        else:
            convert_factor = 1
            
        if str(param) == 'None':
            return '-'
        elif str(param) == 'nan':
            return '-'
        elif str(param) == '(nan, nan)':
            return '-'
        elif str(param) == '(-, -)':
            return '(-, -)'
        else:
            if type(param) == tuple:
                return str(round(param[0], int(dp))*convert_factor) + str(round(param[1], dp)*convert_factor)
            else:
                return str(round(param, int(dp))*convert_factor)
            
    def close(self):
        self.parent.info_frame = None
        self.close_newwindow(self)
        self.window.destroy()