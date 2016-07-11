import Tkinter as tk
import tkSimpleDialog, tkMessageBox
       
class PassFailDialogue(tkSimpleDialog.Dialog):
    def body(self, master, manyopt=True):
        if manyopt:
            self.manyopt = True
        else:
            self.manyopt = False
            
        if self.manyopt:
            tk.Label(master, text="x > ").grid(row=0)
            tk.Label(master, text="x < ").grid(row=1)
            tk.Label(master, text="y > ").grid(row=2)
            tk.Label(master, text="y < ").grid(row=3)
            
            self.e1 = tk.Entry(master)
            self.e2 = tk.Entry(master)
            self.e3 = tk.Entry(master)
            self.e4 = tk.Entry(master)

            self.e1.delete(0, tk.END)
            self.e1.insert(0, '0.00')
            self.e2.delete(0, tk.END)
            self.e2.insert(0, '0.00')
            self.e3.delete(0, tk.END)
            self.e3.insert(0, '0.00')
            self.e4.delete(0, tk.END)
            self.e4.insert(0, '0.00')

            self.e1.grid(row=0, column=1)
            self.e2.grid(row=1, column=1)
            self.e3.grid(row=2, column=1)
            self.e4.grid(row=3, column=1)
            return self.e1 # initial focus                  
        else:
            tk.Label(master, text="min ").grid(row=0)
            tk.Label(master, text="max ").grid(row=1)

            self.e1 = tk.Entry(master)
            self.e2 = tk.Entry(master)
            
            self.e1.delete(0, tk.END)
            self.e1.insert(0, '0.00')
            self.e2.delete(0, tk.END)
            self.e2.insert(0, '0.00')

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