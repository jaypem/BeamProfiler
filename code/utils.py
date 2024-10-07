"""
Content:    on-screen keyboard and num-pad using tkinter
Author :    Jan-Philipp Praetorius

OnScreenApp constructor distinguish between keyboard (keyboard=True)
    and a num-Pad (keyboard=False)
"""

import numpy as np
import tkinter as tk
from tkinter import messagebox
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
from mpl_toolkits.axes_grid1.anchored_artists import AnchoredSizeBar


def drawLines(img):
    # draw lines for grid in image (1000µm=454.74px)
    lineIntensity = int(np.max(img)/5)
        
    # determine grid indices
    line_indices_x = np.arange(0, img.shape[1], 454.74)
    line_indices_y = np.arange(0, img.shape[0], 454.74)
           
    line_indices_x = np.array(list(np.round(line_indices_x).astype(np.int)))
    line_indices_y = np.array(list(np.round(line_indices_y).astype(np.int)))
        
    # change intensity values by corresponding rows and colums
    img[line_indices_y, :] = lineIntensity
    img[:, line_indices_x] = lineIntensity
        
    return img


def saveImage(root, img, width, height, std_w, std_h):
    # read specified value from keyboard
    filename = createUI(parentroot=root, keyboard=True)

    if filename is not None:
        # save image 
        fig, ax = plt.subplots()
        ax.imshow(img, cmap=plt.get_cmap('rainbow'))
            
        # draw scale-bar
        fontprops = fm.FontProperties(size=10, family='monospace')
        # scalebar: 1000µm * 1/2.2µm (chip-size/px) = 454.736 pixel 
        bar = AnchoredSizeBar(ax.transData,size=454.74, label='1000 µm', loc=4, 
            pad=0.1, borderpad=0.9, sep=1, frameon=True, color='black',
            label_top=False, fontproperties=fontprops)
        ax.add_artist(bar)
            
        # add grid, major ticks every 1000µm=454.74px, minor ticks every 1000µm=454.74px
        major_ticks_x = np.arange(0, img.shape[1], 454.74)
        minor_ticks_x = np.arange(0, img.shape[1], 227.37)
        major_ticks_y = np.arange(0, img.shape[0], 454.74)
        minor_ticks_y = np.arange(0, img.shape[0], 227.37)
            
        ax.set_xticks(major_ticks_x)
        ax.set_xticks(minor_ticks_x, minor=True)
        ax.set_yticks(major_ticks_y)
        ax.set_yticks(minor_ticks_y, minor=True)
            
        # turn off tick labels
        ax.set_yticklabels([]); ax.set_xticklabels([])
            
        ax.grid(which='major', alpha=0.3)    
        fig.tight_layout(pad=0)
        fig.show()
        #fig.savefig("/home/pi/.BeamProfiler/images/image_{}.png".format(filename))
        fig.savefig("~/BeamProfiler/images/{}.png".format(filename))
        
        # save info in textfile        
        with open("~/BeamProfiler/images/info_{}.txt".format(filename), "w") as text_file:
            print("Width: {0}\nHeight: {1}\nStandard-deviation-width: {2}\nStandard-deviation-height: {3}".format(width, height, std_w, std_h), file=text_file)
        
        messagebox.showinfo('Info', 'Save image and profil-info in {0}.png and {0}.txt'.format(filename))
    else:
        print("No file name was specified!")


def createUI(parentroot, keyboard):
    try:
        ui = OnScreenApp(parentroot, keyboard) 
        parentroot.wait_window(ui.app)
        print('GUI-value: ', ui.value)
        return ui.value
    except:
        print('ERROR by create and delete OnScreenApp-GUI object, return dafault value: img')
        if keyboard:
            return 'img'
        else:
            return 30
    

class OnScreenApp(tk.Frame):
    # constructor
    def __init__(self, master, keyboard, **kw):
        self.app = tk.Toplevel(master)
        
        if keyboard:
            self.app.title('Keyboard')
        else:
            self.app.title('NumPad')

        self.app.resizable(0,0)

        # define label and entry widget
        self.label = tk.Label(self.app, text='specify value by click in empty field', bd=5, font=("System", 11, 'bold')).grid(row=0,columnspan=15)

        self.entry = tk.Entry(self.app, width=48, bd=5, justify=tk.CENTER)
        self.entry.grid(row=1, columnspan=15)
       
        # distinguish for handling between keyboard and numPad
        if keyboard:
            self.entry.bind("<Button-1>", lambda e: self.keyboard())
        else:
            self.entry.bind("<Button-1>", lambda e: self.numPad())

    # destructor
    def __del__(self):
        print('Destructor called, OnScreenApp deleted')
        
    ######### Keyboard #########
    def keyboard(self):
        buttons = [
            'q', 'w', 'e', 'r', 't', 'z', 'u', 'i', 'o', 'p', 'DEL',
            'a', 's', 'd', 'f', 'g', 'h', 'j', 'k', 'l', '.', 'SPACE',
            'y', 'x', 'c', 'v', 'b', 'n', 'm', '-', '_', ',', 'SAVE',
            ]

        varRow = 2
        varColumn = 0

        for button in buttons:
            command = lambda x=button: self.click(x)
            
            if button == "SPACE" or button == "DEL" or button == "SAVE":
                tk.Button(self.app,text= button, height=5, width=10, bg="#3c4987", fg="#ffffff", font="System 10 bold",
                    activebackground = "#ffffff", activeforeground="#3c4987", relief='raised', padx=1,
                    pady=1, bd=1,command=command).grid(row=varRow,column=varColumn)

            else:
                tk.Button(self.app,text= button, height=5, width=8, bg="#3c4987", fg="#ffffff", font="System 10 bold",
                    activebackground = "#ffffff", activeforeground="#3c4987", relief='raised', padx=1,
                    pady=1, bd=1,command=command).grid(row=varRow,column=varColumn)

            varColumn +=1 
            if varColumn > 10 and varRow in [2,3,4]:
                varColumn = 0
                varRow+=1

    ######### numPad #########
    def numPad(self):
        buttons = ['7',  '8',  '9', '4',  '5',  '6',
                   '1',  '2',  '3', '0',  'SAVE',  'DEL']

        # position all buttons with a for-loop; r, c used for row, column grid values
        r = 2
        c = 0
        n = 0

        btn = []
        for label in buttons:
            # partial takes care of function and argument
            cmd = lambda x = label: self.click(x)
            # create the button
            cur = tk.Button(self.app, text=label, width=13, height=5, font="System 10 bold", anchor=tk.CENTER,
                bg="#3c4987", fg="#ffffff", activebackground = "#ffffff", activeforeground="#3c4987", command=cmd)
            btn.append(cur)
            # position the button
            btn[-1].grid(row=r, column=c)
            # increment button index
            n += 1
            # update row/column position
            c += 1
            if c == 3:
                c = 0
                r += 1

    def click(self, value):
        if value == 'DEL':
            self.entry.delete(len(self.entry.get())-1, tk.END)           
        elif value == "SPACE":
            self.entry.insert(tk.END, ' ')          
        elif value == 'SAVE':
            self.value = self.entry.get()
            self.app.destroy()
        else:
            self.entry.insert(tk.END,value)