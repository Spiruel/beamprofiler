#!/usr/bin/python
# -*- coding: latin-1 -*-

import Tkinter as tk
import ttk
import numpy as np
import tkSimpleDialog, tkMessageBox
import time
import threading
import ConfigParser
       
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
                self.master.log('Written new values to config.ini')

    def close(self):
        self.destroy()
        
class InfoFrame(tk.Frame):
    def __init__(self, parent):
        self.window = tk.Toplevel(parent)
        self.window.minsize(200,350)
        
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

        if parent.beam_width is None:
            parent.beam_width = (np.nan, np.nan)
        if parent.peak_cross is None: 
            parent.peak_cross = (np.nan, np.nan)
        if parent.centroid is None:
            parent.centroid = (np.nan, np.nan)
            
        self.pixel_scale = parent.pixel_scale #get pixel scale conversion
        self.raw_rows = ["Beam Width (D4σ)", "Beam Diameter (D4σ)", "Peak Pixel Value", "Peak Position", "Centroid Position", "Power Density"]
        self.raw_units = ["µm","µm"," ","µm","µm","W/µm²"]
        square = lambda x: x**2 if x is not None else np.nan
        self.raw_values = ['(' + self.info_format(parent.beam_width[0], convert=True) + ', ' + self.info_format(parent.beam_width[1], convert=True) + ')', self.info_format(parent.beam_diameter, convert=True), self.info_format(np.max(parent.analysis_frame)), '(' + self.info_format(parent.peak_cross[0], convert=True) + ', ' + self.info_format(parent.peak_cross[1], convert=True) + ')', '(' + self.info_format(parent.centroid[0], convert=True) + ', ' + self.info_format(parent.centroid[1], convert=True) + ')', "{:.2E}".format((255000/square(parent.beam_diameter))*parent.power)]
        self.ellipse_rows = ["Ellipse axes", "Ellipticity", "Eccentricity", "Orientation"]
        self.ellipse_units = ["µm", " ", " ", "deg"]
        self.ellipse_values = ['(' + self.info_format(parent.MA, convert=True) + ', ' + self.info_format(parent.ma, convert=True) + ')', self.info_format(parent.ellipticity), self.info_format(parent.eccentricity), self.info_format(parent.ellipse_angle)]
                          
        self.tree.insert("",iid="1", index="end",text="Raw Data Measurement")
        for i in range(len(self.raw_rows)):
            self.tree.insert("1",iid="1"+str(i), index="end", text=self.raw_rows[i], value=(self.raw_units[i], self.raw_values[i], parent.raw_passfail[i], parent.raw_xbounds[i][0], parent.raw_xbounds[i][1], parent.raw_ybounds[i][0], parent.raw_ybounds[i][1]))
        self.tree.see("14")
        self.tree.insert("",iid="2", index="end",text="Ellipse (fitted)")
        for i in range(len(self.ellipse_rows)):
            self.tree.insert("2",iid="2"+str(i), index="end", text=self.ellipse_rows[i], value=(self.ellipse_units[i], self.ellipse_values[i], parent.ellipse_passfail[i], parent.ellipse_xbounds[i][0], parent.ellipse_xbounds[i][1], parent.ellipse_ybounds[i][0], parent.ellipse_ybounds[i][1]))
        self.tree.see("23")
        
        self.tree.pack(expand=True,fill=tk.BOTH)
        
        button_refresh = tk.Button(self.window, text="refresh", command=lambda: self.refresh_frame(parent))
        button_refresh.pack(padx=5, pady=20, side=tk.LEFT)
        button_pf = tk.Button(self.window, text="toggle pass/fail test", command=lambda: self.pass_fail(parent))
        button_pf.pack(padx=5, pady=20, side=tk.LEFT)
        button_edit = tk.Button(self.window, text="edit", command=lambda: self.edit(parent))
        button_edit.pack(padx=5, pady=20, side=tk.LEFT)
        self.refresh_frame(parent)
    
    def refresh_frame(self, parent):

        self.curr_item = self.tree.focus()
        
        if parent.beam_width is None:
            parent.beam_width = (np.nan, np.nan)
        if parent.peak_cross is None: 
            parent.peak_cross = (np.nan, np.nan)
        if parent.centroid is None:
            parent.centroid = (np.nan, np.nan)
            
        square = lambda x: x**2 if x is not None else np.nan #3e-15 power dens before sat
        self.raw_values = ['(' + self.info_format(parent.beam_width[0], convert=True) + ', ' + self.info_format(parent.beam_width[1], convert=True) + ')', self.info_format(parent.beam_diameter, convert=True), self.info_format(np.max(parent.analysis_frame)), '(' + self.info_format(parent.peak_cross[0], convert=True) + ', ' + self.info_format(parent.peak_cross[1], convert=True) + ')', '(' + self.info_format(parent.centroid[0], convert=True) + ', ' + self.info_format(parent.centroid[1], convert=True) + ')', "{:.2E}".format((255000/square(parent.beam_diameter))*parent.power)]
        self.ellipse_values = ['(' + self.info_format(parent.MA, convert=True) + ', ' + self.info_format(parent.ma, convert=True) + ')', self.info_format(parent.ellipticity), self.info_format(parent.eccentricity), self.info_format(parent.ellipse_angle)]

        self.tree.delete(*self.tree.get_children())
        self.tree.insert("",iid="1", index="end",text="Raw Data Measurement")
        for i in range(len(self.raw_rows)):
            self.tree.insert("1",iid="1"+str(i), index="end", text=self.raw_rows[i], value=(self.raw_units[i], self.raw_values[i], parent.raw_passfail[i], parent.raw_xbounds[i][0], parent.raw_xbounds[i][1], parent.raw_ybounds[i][0], parent.raw_ybounds[i][1]))
        self.tree.see("14")
        self.tree.insert("",iid="2", index="end",text="Ellipse (fitted)")
        for i in range(len(self.ellipse_rows)):
            self.tree.insert("2",iid="2"+str(i), index="end", text=self.ellipse_rows[i], value=(self.ellipse_units[i], self.ellipse_values[i], parent.ellipse_passfail[i], parent.ellipse_xbounds[i][0], parent.ellipse_xbounds[i][1], parent.ellipse_ybounds[i][0], parent.ellipse_ybounds[i][1]))
        self.tree.see("23")

        self.tree.selection_set(self.curr_item)
        self.tree.focus(self.curr_item)
        
    def pass_fail(self, parent):
        selected_item = self.tree.selection()
        if len(selected_item) == 1:
            if len(str(selected_item[0])) == 2:
                index, row_num = map(int,str(selected_item[0]))
                print 'toggling pass/fail state'
                if index == 1:
                    if parent.raw_passfail[row_num] == 'True':
                        parent.raw_passfail[row_num] = 'False'
                    else:
                        parent.raw_passfail[row_num] = 'True'
                elif index == 2:
                    if parent.ellipse_passfail[row_num] == 'True':
                        parent.ellipse_passfail[row_num] = 'False'
                    else:
                        parent.ellipse_passfail[row_num] = 'True'
                self.refresh_frame(parent)
            
    def edit(self, parent):
        selected_item = self.tree.selection()
        if len(selected_item) == 1:
            if len(str(selected_item[0])) == 2:
                index, row_num = map(int,str(selected_item[0]))
                if index == 1:
                    if parent.raw_ybounds[row_num] != (' ', ' '):
                        print 'getting x and y bounds'
                        passfailbounds = self.change_pass_fail(parent, True, (parent.raw_xbounds[row_num], parent.raw_ybounds[row_num])) #get x and y bounds
                        if passfailbounds is not None:
                            parent.raw_xbounds[row_num] = (parent.raw_xbounds[row_num][0][:5] + passfailbounds[0], parent.raw_xbounds[row_num][1][:5] + passfailbounds[1])
                            parent.raw_ybounds[row_num] = (parent.raw_ybounds[row_num][0][:5] + passfailbounds[2], parent.raw_ybounds[row_num][1][:5] + passfailbounds[3])
                    else:
                        print 'getting x bounds'
                        passfailbounds = self.change_pass_fail(parent, False, parent.raw_xbounds[row_num]) #get just x bounds
                        if passfailbounds is not None:
                            parent.raw_xbounds[row_num] = passfailbounds[0], passfailbounds[1]
                elif index == 2:
                    if parent.ellipse_ybounds[row_num] != (' ', ' '):
                        print 'getting x and y bounds'
                        passfailbounds = self.change_pass_fail(parent, True, (parent.ellipse_xbounds[row_num], parent.ellipse_ybounds[row_num])) #get x and y bounds
                        if passfailbounds is not None:
                            parent.ellipse_xbounds[row_num] = (parent.ellipse_xbounds[row_num][0][:5] + passfailbounds[0], parent.ellipse_xbounds[row_num][1][:5] + passfailbounds[1])
                            parent.ellipse_ybounds[row_num] = (parent.ellipse_ybounds[row_num][0][:5] + passfailbounds[2], parent.ellipse_ybounds[row_num][1][:5] + passfailbounds[3])
                    else:
                        print 'getting x bounds'
                        passfailbounds = self.change_pass_fail(parent, False, parent.ellipse_xbounds[row_num]) #get just x bounds
                        if passfailbounds is not None:
                            parent.ellipse_xbounds[row_num] = (passfailbounds[0], passfailbounds[1])

                self.refresh_frame(parent)
                    
    def change_pass_fail(self, parent, manyopt, bounds):
        '''Opens passfail window'''
        if self.passfail_frame != None:
            self.passfail_frame.close()
        self.passfail_frame = PassFailDialogue(parent, manyopt, bounds)
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
        self.window.destroy()
                        
class PassFailDialogue(tkSimpleDialog.Dialog):
    def __init__(self, master, manyopt, bounds):
        self.manyopt = manyopt
        self.bounds = bounds
        tkSimpleDialog.Dialog.__init__(self, master)
    
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

class SystemLog():  
    def __init__(self, parent):
        self.parent = parent
        self.window = tk.Toplevel(parent)
        self.window.minsize(200,350)
        
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
        self.window.destroy()
        
class ToolbarConfig(tkSimpleDialog.Dialog):
    def __init__(self, master):
        self.master = master
        self.dummies1 = []
        self.result = []
        self.options = ['x Cross Profile', 'y Cross Profile', '2D Profile', '2D Surface',
                  'Plot Positions', 'Plot Power', 'Plot Orientation', 'Beam Stability',
                  'Increase exposure', 'Decrease exposure', 'View log', 'Basic Workspace', 'Clear windows']
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
        
    def apply(self):
        self.result = self.dummies1
        
    def close(self):
        self.destroy()
        
class Progress(tk.Frame):
    def __init__(self, parent):
        self.parent = parent
        self.v = tk.DoubleVar()  
        self.progressbar = ttk.Progressbar(self.parent.statusbar, variable=self.v, orient=tk.HORIZONTAL, length=100, maximum=100, mode='determinate')
        self.progressbar.pack(side=tk.RIGHT, padx=5)
        
    def next_step(self):
        self.v.set(0)
        # Create a numpy array of floats to store the average (assume RGB images)
        arr = np.zeros(self.parent.frame.shape, np.float)
        for i in range(100):
            imarr = np.array(self.parent.frame,dtype=np.float)
            arr = arr+imarr/100
            self.progressbar.step(1)
            time.sleep(0.01)

        # Round values in array and cast as 16-bit integer
        self.parent.bg_frame = np.array(np.round(arr),dtype=np.uint8)

        self.parent.log('Background calibration complete')
        self.v.set(0)
        
    def calibrate_bg(self):
        t1=threading.Thread(target=self.next_step)
        t1.start()
        
    def reset_bg(self):
        self.parent.bg_frame = 0