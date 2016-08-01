#!/usr/bin/python
# -*- coding: latin-1 -*-

try:
    # for Python2
    import Tkinter as tk
    import ttk
    import tkSimpleDialog, tkMessageBox
except ImportError:
    # for Python3
    import tkinter as tk
    import tkinter.ttk as ttk
    from tkinter import messagebox as tkMessageBox
    from tkinter import simpledialog as tkSimpleDialog
    
import numpy as np
import time
import threading

try:
    import ConfigParser
except ImportError:
    import configparser as ConfigParser
       
class Config(tkSimpleDialog.Dialog):
    def __init__(self, master):
        self.master = master
        tkSimpleDialog.Dialog.__init__(self, master)
        
    def body(self, master):
        tk.Label(master, text="Plot refresh rate /s:").grid(row=0)
        tk.Label(master, text="Pixel size (µm):").grid(row=1)
        tk.Label(master, text="Power (W):").grid(row=2)
        tk.Label(master, text="Angle (deg):").grid(row=3)

        self.e1 = tk.Entry(master)
        self.e2 = tk.Entry(master)
        self.e3 = tk.Entry(master)
        self.e4 = tk.Entry(master)
        
        self.e1.delete(0, tk.END)
        self.e1.insert(0, str(self.master.plot_tick))
        self.e2.delete(0, tk.END)
        self.e2.insert(0, str(self.master.pixel_scale))
        self.e3.delete(0, tk.END)
        if str(self.master.power) == 'nan':
            pow = '-'
        else:
            pow = self.master.power
        self.e3.insert(0, str(pow))
        self.e4.delete(0, tk.END)
        self.e4.insert(0, str(self.master.angle))

        self.e1.grid(row=0, column=1)
        self.e2.grid(row=1, column=1)
        self.e3.grid(row=2, column=1)
        self.e4.grid(row=3, column=1)
        
        self.rb = tk.Button(master, text="Reset to default", command=self.reset_values)
        self.rb.grid(row=4, columnspan=2)
        
        self.sc = tk.Button(master, text="Apply and save to config", command=self.save_config)
        self.sc.grid(row=5, columnspan=2)
        
        self.expscale = tk.Scale(master, label='exposure',
        from_=-15, to=-8,
        length=300, tickinterval=1,
        showvalue='yes', 
        orient='horizontal',
        command = self.master.change_exp)
        self.expscale.set(self.master.exp)
        self.expscale.grid(row=6, columnspan=2, sticky=tk.W)
                
        self.roiscale = tk.IntVar(master)
        self.roiscale.set(self.master.roi)
        self.dropdown5 = tk.OptionMenu(master, self.roiscale, 1, 2, 4, 8, 16, command = self.master.set_roi)
        roitext = tk.Label(master, text="zoom factor")
        roitext.grid(row=7, columnspan=2, sticky=tk.W)
        self.dropdown5.grid(row=8, columnspan=2, sticky=tk.W)

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
            power = self.e3.get()
            if power == '':
                power = None
            else:
                if power == '-':
                    power = power
                else:
                    power = float(power)
            angle = self.e4.get()
            if angle == '':
                angle = None
            else:
                angle = float(angle)
            self.result = plot_tick, pixel_scale, power, angle
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
        self.e2.insert(0, '5.6')
        self.e3.delete(0, tk.END)
        self.e3.insert(0, '-')
        self.e4.delete(0, tk.END)
        self.e4.insert(0, '0.0')
        
    def save_config(self):
        config = ConfigParser.ConfigParser()
        section = {
        'pixel_scale': 'WebcamSpecifications',
        'base_exp': 'WebcamSpecifications',
        'power': 'LaserSpecifications',
        'angle': 'LaserSpecifications',
        'plot_tick': 'Miscellaneous'
        }
        
        value = ['plot_tick', 'pixel_scale', 'power', 'angle']
        setting = [self.e1.get(), self.e2.get(), self.e3.get(), self.e4.get()]
        
        if self.validate():
            if config.read("config.ini") != []:
                for val, sett in zip(value, setting):
                    config.set(section[val], val, sett)    
                with open('config.ini', 'w') as configfile:
                    config.write(configfile)
                self.master.log('Written new config values to config.ini')

    def close(self):
        self.destroy()
                        
class PassFailDialogue(tkSimpleDialog.Dialog):
    def __init__(self, master, manyopt, bounds):
        self.master = master
        self.manyopt = manyopt
        self.bounds = bounds
        tkSimpleDialog.Dialog.__init__(self, self.master.info_frame.window)
    
    def body(self, master):
        if self.manyopt:
            tk.Label(master, text="x ≥ ").grid(row=0)
            tk.Label(master, text="x ≤ ").grid(row=1)
            tk.Label(master, text="y ≥ ").grid(row=2)
            tk.Label(master, text="y ≤ ").grid(row=3)
            
            self.e1 = tk.Entry(master)
            self.e2 = tk.Entry(master)
            self.e3 = tk.Entry(master)
            self.e4 = tk.Entry(master)

            self.e1.delete(0, tk.END)
            self.e1.insert(0, self.bounds[0][0][5:])
            self.e2.delete(0, tk.END)
            self.e2.insert(0, self.bounds[0][1][5:])
            self.e3.delete(0, tk.END)
            self.e3.insert(0, self.bounds[1][0][5:])
            self.e4.delete(0, tk.END)
            self.e4.insert(0, self.bounds[1][1][5:])

            self.e1.grid(row=0, column=1)
            self.e2.grid(row=1, column=1)
            self.e3.grid(row=2, column=1)
            self.e4.grid(row=3, column=1)
            return self.e1 # initial focus                  
        else:
            tk.Label(master, text="Min. ").grid(row=0)
            tk.Label(master, text="Max. ").grid(row=1)

            self.e1 = tk.Entry(master)
            self.e2 = tk.Entry(master)
            
            self.e1.delete(0, tk.END)
            self.e1.insert(0, self.bounds[0])
            self.e2.delete(0, tk.END)
            self.e2.insert(0, self.bounds[1])

            self.e1.grid(row=0, column=1)
            self.e2.grid(row=1, column=1)
            return self.e1 # initial focus

    def validate(self):
        try:
            if self.manyopt:
                first = '{0:.2f}'.format(round(float(self.e1.get()),2))
                second = '{0:.2f}'.format(round(float(self.e2.get()),2))
                third = '{0:.2f}'.format(round(float(self.e3.get()),2))
                fourth = '{0:.2f}'.format(round(float(self.e4.get()),2))
                self.result = first, second, third, fourth # or something
            else:
                first = '{0:.2f}'.format(round(float(self.e1.get()),2))
                second = '{0:.2f}'.format(round(float(self.e2.get()),2))
                self.result = first, second
            return 1
        except ValueError:
            tkMessageBox.showwarning(
                "Bad input",
                "Illegal values, please input numbers to 2 d.p."
            )
            return 0
        
    def close(self):
        self.destroy()
        
class ToolbarConfig(tkSimpleDialog.Dialog):
    def __init__(self, master):
        self.master = master
        self.dummies1 = []
        self.result = []
        self.options = ['x Cross Profile', 'y Cross Profile', '2D Profile', '2D Surface',
                  'Plot Positions', 'Plot Orientation', 'Beam Stability',
                  'Increase exposure', 'Decrease exposure', 'Calculation Results', 'View log', 'Basic Workspace',
                  'Clear windows', 'Show Windows', 'Load Workspace', 'Save Workspace', 'Show Webcam']
        tkSimpleDialog.Dialog.__init__(self, master)
        
    def body(self, master):
        tk.Label(self, text='Select choices for Toolbar buttons').pack()
        for i in self.options:
            dummy1 = tk.IntVar()
            if i.lower() in [a.lower() for a in self.master.toolbaroptions]:
                dummy1.set(1)
            else:
                dummy1.set(0)
            dummy2 = tk.Checkbutton(self, text=i, variable=dummy1).pack(side=tk.TOP, padx=2, pady=2)
            self.dummies1.append(dummy1)
        button_save = tk.Button(self, text="Save toolbar config", command=self.save_config)
        button_save.pack()
        
    def validate(self):
        self.result = self.dummies1
        return 1
        
    def save_config(self):
        config = ConfigParser.ConfigParser()
        
        if self.dummies1 is not None:
            choices = [self.options[i] for i,j in enumerate(self.dummies1) if j.get() == 1]
            if config.read("config.ini") != []:
                config.set('Toolbar', 'buttons', ', '.join(choices))    
                with open('config.ini', 'w') as configfile:
                    config.write(configfile)
                self.master.log('Written new toolbar values to config.ini')
        
    def close(self):
        self.destroy()
        
class Progress(tk.Frame):
    def __init__(self, parent):
        self.parent = parent
        self.v = tk.DoubleVar()  
        self.progressbar = ttk.Progressbar(self.parent.statusbar, variable=self.v, orient=tk.HORIZONTAL, length=100, maximum=100, mode='determinate')
        self.progressbar.pack(side=tk.RIGHT, padx=5)
        
    def next_step(self):
        if self.parent.bg_subtract == 1:
            self.v.set(0)
            # Create a numpy self.array of floats to store the average (assume RGB images)
            self.arr = np.zeros(self.parent.frame.shape, np.float)
        if self.parent.bg_subtract >= 1:   
            imarr = np.array(self.parent.frame,dtype=np.float)
            self.arr = self.arr+imarr/100
            self.progressbar.step(1)
            time.sleep(0.01)
            self.parent.bg_subtract += 1
        if self.parent.bg_subtract == 100:
            # Round values in self.array and cast as 16-bit integer
            self.parent.bg_frame = np.array(np.round(self.arr),dtype=np.uint8)

            self.parent.log('Background calibration complete')
            self.v.set(0)
            self.parent.bg_subtract = 0
        
    def calibrate_bg(self):
        self.parent.bg_subtract = 1
        
    def reset_bg(self):
        self.parent.bg_frame = 0