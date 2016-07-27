import Tkinter as tk

class MainWindow(tk.Frame):
    counter = 0
    def __init__(self, parent, *args, **kwargs):
        tk.Frame.__init__(self, *args, **kwargs)
        self.parent = parent
        
        # get screen width and height
        self.ws = parent.winfo_screenwidth() # width of the screen
        self.hs = parent.winfo_screenheight() # height of the screen
        
        self.w = self.ws/10
        self.h = self.hs/5


        # calculate x and y coordinates for the Tk root window
        self.x = 0# (ws/2) - (w/2)
        self.y = 0#(hs/2) - (h/2)

        # set the dimensions of the screen 
        # and where it is placed
        parent.geometry('%dx%d+%d+%d' % (self.w, self.h, self.x, self.y))
        
        b = tk.Button(text='shrink', command=self.shrink)
        b.pack()
        b = tk.Button(text='enlarge', command=self.enlarge)
        b.pack()
        b = tk.Button(text='move', command=self.move)
        b.pack()
        b = tk.Button(text='show all', command=self.show_all)
        b.pack()
        b = tk.Button(text='close all', command=self.close_all)
        b.pack()
        
        self.windowx, self.windowy = self.w,0
        self.button = tk.Button(self, text="Create new window", 
                                command=lambda: self.create_window(self.windowx,self.windowy))
        self.button.pack(side="top") 
        
        self.windows = []
        self.instances = []
        self.vacancies = []
        
    def shrink(self):
        self.w = self.w/2
        self.h = self.h/2
        self.parent.geometry('%dx%d+%d+%d' % (self.w, self.h, self.x, self.y))
        
    def enlarge(self):
        self.w = self.w*2
        self.h = self.h*2
        self.parent.geometry('%dx%d+%d+%d' % (self.w, self.h, self.x, self.y))
        
    def move(self):
        self.x += 10
        self.y += 10
        self.parent.geometry('%dx%d+%d+%d' % (self.w, self.h, self.x, self.y))
        
    def create_window(self, x, y):
        if len(self.vacancies) >= 1:
            x,y  = self.vacancies[0]
            self.counter += 1
            t = NewWindow(self, x, y)
            self.instances.append(t)
            self.vacancies.pop(0)
        else:
            if self.windowx+self.w < self.ws:
                self.windowx += self.w
            else:
                self.windowx = 0
                self.windowy += self.h + 30
            self.counter += 1
            t = NewWindow(self, x, y)
            self.instances.append(t)
        
    def show_all(self):
        for window in self.windows:
            try:
                window.state(newstate='normal')
                window.deiconify()
            except:
                print 'bad window!'
                pass
                
    def close_all(self):
        for window in self.instances:
            window.close()
        self.windowx, self.windowy = self.w, 0
        self.windows, self.instances, self.vacancies = [], [], []
                
class NewWindow():
    def __init__(self, parent, x, y):
        self.window = tk.Toplevel(parent)
        
        self.x, self.y = x, y
        self.w = self.w
        self.h = self.h
        
        self.windows = []
        self.instances = []
        self.vacancies = []
        
        self.window.geometry('%dx%d+%d+%d' % (self.w, self.h, self.x, self.y))
        
        self.window.wm_title("Window #%s" % self.counter)
        l = tk.Label(self.window, text="This is window #%s" % self.counter)
        l.pack(side="top", fill="both", expand=True, padx=100, pady=100)
        
        self.windows.append(self.window)
        self.window.protocol("WM_DELETE_WINDOW", self.close)
        
    def move(self):
        self.window.geometry('%dx%d+%d+%d' % (self.w, self.h, self.x, self.y))
        
    def close(self):
        # self.parent.instances.pop(self.parent.windows.index(self.window))
        # self.parent.windows.remove(self.window)
        self.vacancies.append((self.x, self.y))
        self.window.destroy()
        
class WebcamView(NewWindow):
    def __init__(self, parent, counter):
    
        self.parent = parent
        
        self.counter = counter

        # get screen width and height
        self.ws = parent.winfo_screenwidth() # width of the screen
        self.hs = parent.winfo_screenheight() # height of the screen
        
        self.w = self.ws/10
        self.h = self.hs/5
        # calculate x and y coordinates for the Tk root window
        self.x = 0# (ws/2) - (w/2)
        self.y = 0#(hs/2) - (h/2)
        
        NewWindow.__init__(self, parent, 0, 0)
