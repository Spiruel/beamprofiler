#!/usr/bin/python
# -*- coding: latin-1 -*-

import Tkinter as tk
import tkSimpleDialog, tkMessageBox
       
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
