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

import interface

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2TkAgg
import matplotlib.pyplot as plt
from matplotlib.ticker import MultipleLocator, FormatStrFormatter

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
    
    def load_workspace(self):
        if self.workspace == []:
            self.log('No saved workspace found')
        elif self.workspace == self.get_geometry():
            self.log('Workspace already loaded!')
            self.show_all()
        else:
            self.close_all()
            for window in self.workspace:
                w, h, x, y, windowtype = window
                ws = self.parent.winfo_screenwidth()
                hs = self.parent.winfo_screenheight()
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
                    t = PlotView(self, x*ws, y*hs, geom=geom)
                    self.plot_frame = t
                else:
                    self.log('Error couldnt find window to be opened! '+ windowtype)
                self.instances.append(t)
        
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
        for window in self.instances:
            window.close()
        self.windowx, self.windowy = self.w, 0
        self.windows, self.instances, self.vacancies = [], [], []
        
    def view(self, option):
        if option == 'webcam':
            return self.create_window(WebcamView(self,self.windowx,self.windowy))
        elif option == 'graph':
            return self.create_window(GraphView(self,self.windowx,self.windowy))
        elif option == 'info':
            return self.create_window(InfoView(self,self.windowx,self.windowy))
        elif option == 'logs':
            return self.create_window(SystemLog(self,self.windowx,self.windowy))
        elif option == 'plot':
            return self.create_window(PlotView(self,self.windowx,self.windowy))
                
class NewWindow(tk.Frame):
    def __init__(self, parent, x, y, geom):
        self.parent = parent
        self.window = tk.Toplevel(self.parent)
        
        self.x, self.y = x, y
        self.w = self.parent.w
        self.h = self.parent.h
        
        if geom is not None:
            self.window.geometry('%dx%d+%d+%d' % (geom[0], geom[1], self.x, self.y))
        else:
            self.window.geometry('%dx%d+%d+%d' % (self.w, self.h, self.x, self.y))

        self.parent.windows.append(self.window)
        self.window.protocol("WM_DELETE_WINDOW", self.close_newwindow)
        
    def move(self):
        self.window.geometry('%dx%d+%d+%d' % (self.w, self.h, self.x, self.y))
        
    def close_newwindow(self):
        if self.window in self.parent.windows:
            self.parent.windows.remove(self.window)
        self.parent.vacancies.append((self.x, self.y, self.w, self.h))
        self.window.destroy()
      
class PlotView(NewWindow, tk.Frame):
    def __init__(self, parent, x, y, geom=None):
        self.parent = parent
        
        self.w = self.parent.ws/10
        self.h = self.parent.hs/5
        # calculate x and y coordinates for the Tk root window
        self.x = 0# (ws/2) - (w/2)
        self.y = 0#(hs/2) - (h/2)
        NewWindow.__init__(self, parent, x, y, geom)
        tk.Frame.__init__(self, parent)
        self.lmain2 = tk.Label(self.window)
        self.lmain2.pack(expand=1, fill=tk.BOTH)
        
        self.window.wm_title("Plot View")
        self.window.minsize(640,360)
        self.window.protocol("WM_DELETE_WINDOW", self.close)
        self.windowtype = 'plot'
        self.init_frame()
        self.refresh_frame()
        
    def init_frame(self):
        '''Creates a matplotlib figure to be placed in the GUI.'''
        plt.clf()
        plt.cla()
        
        self.fig = plt.figure(figsize=(16,9), dpi=100)
        self.ax = self.fig.add_subplot(111)

        canvas = FigureCanvasTkAgg(self.fig, self) 
        canvas.show() 
        canvas.get_tk_widget().pack() 

        toolbar = NavigationToolbar2TkAgg(canvas, self) 
        toolbar.update() 
        canvas._tkcanvas.pack()

        self.parent.fig_type = 'x cross profile'
        self.refresh_frame()
        # self.parent.change_style(self.parent.style_sheet, set=True)
        
    def refresh_frame(self):
        '''Updates the matplotlib figure with new data.'''
        grayscale = self.parent.analysis_frame

        self.ax.plot(range(50), range(1,51))
        # if self.parent.fig_type == 'x cross profile':
            # if self.parent.peak_cross != None:
                # size = 40 #self.beam_width[0]
                # xs = np.arange(self.width)[self.parent.peak_cross[0]-size:self.parent.peak_cross[0]+size]
                # ys = grayscale[self.parent.peak_cross[1],:]
                # self.ax.plot(xs, ys[self.parent.peak_cross[0]-size:self.parent.peak_cross[0]+size],'k-')
                # try:
                    # popt,pcov = curve_fit(output.gauss,np.arange(self.width),ys,p0=[250,self.parent.peak_cross[0],size], maxfev=50)
                    # self.ax.plot(xs,output.gauss(np.arange(self.width),*popt)[self.parent.peak_cross[0]-size:self.parent.peak_cross[0]+size],'r-')
                # except:
                    # pass
                    # # self.log('Problem! Could not fit x gaussian!')
                
                # # plt.xlim(0,self.width)
                # # plt.ylim(0,255)
        # elif self.parent.fig_type == 'y cross profile':
            # if self.parent.peak_cross != None:
                # size = 40 #self.beam_width[1]
                # xs = np.arange(self.height)[self.parent.peak_cross[1]-size:self.parent.peak_cross[1]+size]
                # ys = grayscale[:,self.parent.peak_cross[0]]
                # self.ax.plot(xs, ys[self.parent.peak_cross[1]-size:self.parent.peak_cross[1]+size],'k-')
                # try:
                    # popt,pcov = curve_fit(output.gauss,np.arange(self.height),ys,p0=[250,self.parent.peak_cross[1],size], maxfev=50)
                    # self.ax.plot(xs,output.gauss(np.arange(self.height),*popt)[self.parent.peak_cross[1]-size:self.parent.peak_cross[1]+size],'r-')
                # except:
                    # pass
                    # # self.log('Problem! Could not fit x gaussian!')
                
                # # plt.xlim(0,self.height)
                # # plt.ylim(0,255)
        # elif self.parent.fig_type == '2d profile':
            # if self.parent.peak_cross != None:
                # if str(self.parent.MA) != 'nan':
                    # size = 2*int(self.parent.MA)+10
                # else:
                    # size = 50
                # x, y = self.parent.peak_cross
                # img = grayscale[y-size/2:y+size/2, x-size/2:x+size/2]
                # # # # # # params = self.analyse.fit_gaussian(with_bounds=False)
                # # # # # # # # # # self.analyse.plot_gaussian(plt.gca(), params)
                
                # if self.colourmap is None:
                    # cmap=plt.cm.BrBG
                # elif self.colourmap == 2:
                    # cmap=plt.cm.jet
                # elif self.colourmap == 0:
                    # cmap=plt.cm.autumn
                # elif self.colourmap == 1:
                    # cmap=plt.cm.bone
                # elif self.colourmap == 12:
                    # cmap=output.parula_cm
                # self.ax.imshow(img, cmap=cmap, interpolation='nearest', origin='lower')
                
                # xs = np.arange(size)
                # ys_x = grayscale[self.parent.peak_cross[1],:]
                # ys_y = grayscale[:,self.parent.peak_cross[0]]
                # norm_factor = np.max(ys_x)/(0.25*size)

                # try:
                    # self.ax.plot(xs, size - (ys_x[self.parent.peak_cross[0]-(size/2):self.parent.peak_cross[0]+(size/2)]/norm_factor),'y-', lw=2)
                    # self.ax.plot(ys_y[self.parent.peak_cross[1]-(size/2):self.parent.peak_cross[1]+(size/2)]/norm_factor, xs,'y-', lw=2)
                # except:
                    # return
                
                # try:
                    # popt,pcov = curve_fit(output.gauss,np.arange(self.width),ys_x,p0=[250,self.parent.peak_cross[0],20], maxfev=50)
                    # self.ax.plot(xs,size - output.gauss(np.arange(self.width),*popt)[self.parent.peak_cross[0]-(size/2):self.parent.peak_cross[0]+(size/2)]/norm_factor,'r-', lw=2)
                # except:
                    # pass
                    # # self.log('Problem! Could not fit x gaussian!')
                    
                # try:
                    # popt,pcov = curve_fit(output.gauss,np.arange(self.height),ys_y,p0=[250,self.parent.peak_cross[1],20], maxfev=50)
                    # self.ax.plot(output.gauss(np.arange(self.height),*popt)[self.parent.peak_cross[1]-(size/2):self.parent.peak_cross[1]+(size/2)]/norm_factor,xs,'r-', lw=2)
                # except:
                    # pass
                    # # self.log('Problem! Could not fit y gaussian!')
                
                # if str(self.ellipse_angle) != 'nan':
                    # x_displace, y_displace = self.parent.peak_cross[0]-(size/2), self.parent.peak_cross[1]-(size/2)
                    
                    # pts = self.analyse.get_ellipse_coords(a=self.ma, b=self.MA, x=self.ellipse_x, y=self.ellipse_y, angle=-self.ellipse_angle)
                    # self.ax.plot(pts[:,0] - (x_displace), pts[:,1] - (y_displace))
                    
                    # MA_x, MA_y = self.ma*math.cos(self.ellipse_angle*(np.pi/180)), self.ma*math.sin(self.ellipse_angle*(np.pi/180))
                    # ma_x, ma_y = self.MA*math.sin(self.ellipse_angle*(np.pi/180)), self.MA*math.cos(self.ellipse_angle*(np.pi/180))
                    # MA_xtop, MA_ytop = int(self.ellipse_x + MA_x), int(self.ellipse_y + MA_y)
                    # MA_xbot, MA_ybot = int(self.ellipse_x - MA_x), int(self.ellipse_y - MA_y)
                    # ma_xtop, ma_ytop = int(self.ellipse_x + ma_x), int(self.ellipse_y + ma_y) #find corners of ellipse
                    # ma_xbot, ma_ybot = int(self.ellipse_x - ma_x), int(self.ellipse_y - ma_y)
                    
                    # self.ax.plot([MA_xtop - (x_displace), MA_xbot - (x_displace)], [MA_ytop - (y_displace), MA_ybot - (y_displace)], 'w-', lw=2)
                    # self.ax.plot([ma_xtop - (x_displace), ma_xbot - (x_displace)], [ma_ybot - (y_displace), ma_ytop - (y_displace)], 'w:', lw=2)
                    
                # self.ax.set_xlim(0, size)
                # self.ax.set_ylim(size, 0)
                
                # # majorLocator = MultipleLocator(10)
                # # majorFormatter = FormatStrFormatter('%d')
                # # minorLocator = MultipleLocator(1)

                # # ax = plt.gca()
                # # ax.xaxis.set_major_locator(majorLocator)
                # # ax.xaxis.set_major_formatter(majorFormatter)

                # # # for the minor ticks, use no labels; default NullFormatter
                # # ax.xaxis.set_minor_locator(minorLocator)
                # # ax.yaxis.set_minor_locator(minorLocator)
                
                # # ax.tick_params(which='both', width=1.5, color='w')
                # # ax.tick_params(which='major', length=8)
                # # ax.tick_params(which='minor', length=4)
        # elif self.parent.fig_type == 'beam stability':
            # self.ax.plot(self.centroid_hist_x, self.centroid_hist_y, 'r-', label='centroid')
            # self.ax.plot(self.peak_hist_x, self.peak_hist_y, 'b-', label='peak cross')
            # self.ax.xlim(0, self.width)
            # self.ax.ylim(self.height, 0)
            # self.ax.plot([0,0],'w.',label=''); self.ax.legend(frameon=False)
        # elif self.parent.fig_type == 'positions':
            # # plt.xlabel('$time$ $/s$'); plt.ylabel('$position$ $/\mu m$')
            # if self.graphs['centroid_x']: self.ax.plot(self.running_time-self.running_time[0], self.centroid_hist_x, 'b-', label='centroid x coordinate')
            # if self.graphs['centroid_y']: self.ax.plot(self.running_time-self.running_time[0], self.centroid_hist_y, 'r-', label='centroid y coordinate')
            # if self.graphs['peak_x']: self.ax.plot(self.running_time-self.running_time[0], self.peak_hist_x, 'y-', label='peak x coordinate')
            # if self.graphs['peak_y']: self.ax.plot(self.running_time-self.running_time[0], self.peak_hist_y, 'g-', label='peak y coordinate')
            # if self.running_time[-1] - self.running_time[0] <= 60:
                # self.ax.set_xlim(0, 60)
            # else:
                # index = np.searchsorted(self.running_time,[self.running_time[-1]-60,],side='right')[0]
                # self.ax.set_xlim(self.running_time[index]-self.running_time[0], self.running_time[-1]-self.running_time[0])
            # self.ax.set_ylim(0,self.width)
            # self.ax.plot([0,0],'w.'); self.ax.legend(frameon=False)
        # elif self.parent.fig_type == 'orientation':
            # if len(self.running_time) > 0:
                # if self.graphs['ellipse_orientation']: self.ax.plot(self.running_time-self.running_time[0], self.ellipse_hist_angle, 'c-', label='ellipse orientation')
                # if self.running_time[-1] - self.running_time[0] <= 60:
                    # self.ax.set_xlim(0, 60)
                # else:
                    # index = np.searchsorted(self.running_time,[self.running_time[-1]-60,],side='right')[0]
                    # self.ax.set_xlim(self.running_time[index]-self.running_time[0], self.running_time[-1]-self.running_time[0])
            # self.ax.set_ylim(0,360)
            # self.ax.plot([0,0],'w.',label=''); self.ax.legend(frameon=False)
        # else:
            # self.log 'fig type not found.', self.parent.fig_type
            
        # self.ax[0].hold(True)
        # self.ax[1].hold(True)
        self.fig.canvas.draw() 
        
        for axis in self.fig.get_axes():
            axis.clear()
        
    def close(self):
        self.parent.plot_frame = None
        self.close_newwindow()
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
        self.window.minsize(640,360)
        self.window.protocol("WM_DELETE_WINDOW", self.close)
        self.windowtype = 'webcam'
        
        self.show_frame()
        
    def show_frame(self):
        self.lmain2.imgtk = self.parent.imgtk
        self.lmain2.configure(image=self.parent.imgtk)
        
    def close(self):
        self.parent.webcam_frame = None
        self.close_newwindow()
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
        self.window.minsize(200,350)
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
        self.window.minsize(800,300)
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
                self.log('toggling pass/fail state')
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
                        self.log('getting x and y bounds')
                        passfailbounds = self.change_pass_fail(True, (self.raw_xbounds[row_num], self.raw_ybounds[row_num])) #get x and y bounds
                        if passfailbounds is not None:
                            self.raw_xbounds[row_num] = (self.raw_xbounds[row_num][0][:5] + passfailbounds[0], self.raw_xbounds[row_num][1][:5] + passfailbounds[1])
                            self.raw_ybounds[row_num] = (self.raw_ybounds[row_num][0][:5] + passfailbounds[2], self.raw_ybounds[row_num][1][:5] + passfailbounds[3])
                    else:
                        self.log('getting x bounds')
                        passfailbounds = self.change_pass_fail(False, self.raw_xbounds[row_num]) #get just x bounds
                        if passfailbounds is not None:
                            self.raw_xbounds[row_num] = passfailbounds[0], passfailbounds[1]
                elif index == 2:
                    if self.ellipse_ybounds[row_num] != (' ', ' '):
                        self.log('getting x and y bounds')
                        passfailbounds = self.change_pass_fail(True, (self.ellipse_xbounds[row_num], self.ellipse_ybounds[row_num])) #get x and y bounds
                        if passfailbounds is not None:
                            self.ellipse_xbounds[row_num] = (self.ellipse_xbounds[row_num][0][:5] + passfailbounds[0], self.ellipse_xbounds[row_num][1][:5] + passfailbounds[1])
                            self.ellipse_ybounds[row_num] = (self.ellipse_ybounds[row_num][0][:5] + passfailbounds[2], self.ellipse_ybounds[row_num][1][:5] + passfailbounds[3])
                    else:
                        self.log('getting x bounds')
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
        self.window.destroy()