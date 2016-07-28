import Tkinter as tk

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
    
    def load_workspace(self):
        if self.workspace == []:
            print 'No saved workspace found'
        elif self.workspace == self.get_geometry():
            print 'workspace already loaded!'
        else:
            self.close_all()
            for window in self.workspace:
                w, h, x, y, windowtype  = window
                ws = self.parent.winfo_screenwidth()
                hs = self.parent.winfo_screenheight()
                geom = (w*ws, h*hs)
                self.counter += 1
                if windowtype == 'webcam':
                    t = WebcamView(self, x*ws, y*hs, geom=geom)
                elif windowtype == 'graph':
                    t = GraphView(self, x*ws, y*hs, geom=geom)
                elif windowtype == 'info':
                    t = InfoView(self, x*ws, y*hs, geom=geom)
                elif windowtype == 'logs':
                    t = SystemLog(self, x*ws, y*hs, geom=geom)
                else:
                    print 'Error couldnt find window to be opened!'
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
        self.window.minsize(self.parent.width,self.parent.height)
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
        
<<<<<<< HEAD
class SystemLog(NewWindow):  
    def __init__(self, parent, x, y, geom=None):
        self.parent = parent
=======
class WebcamView(NewWindow):
    def __init__(self, parent, counter):
    
        self.parent = parent
        
        self.counter = counter
>>>>>>> 4d743e428d2f9cb676230e5543cf2ba85ade725e

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
        
<<<<<<< HEAD
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
=======
        NewWindow.__init__(self, parent, 0, 0)
>>>>>>> 4d743e428d2f9cb676230e5543cf2ba85ade725e
