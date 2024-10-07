# -*- coding: utf-8 -*-
"""
Created on Mon Nov  5 15:26:31 2018

@author: Jan-Philipp Praetorius
"""

import numpy as np
import cv2
import matplotlib.pyplot as plt
import tkinter as tk, threading
from tkinter import messagebox
from PIL import ImageTk, Image
import time
import utils 

from pypylon import pylon


class App:
    def __init__(self):
        self.root = tk.Tk()                                             # create window 
        self.root.wm_title("BeamProfiler pd2©")  # window title # copyright mit shift+altgr+c
        self.root.config(background = "#FFFFFF")                        # window-background-color
        
        # maximize window
        w, h = self.root.winfo_screenwidth(), self.root.winfo_screenheight()-35
        self.root.geometry("%dx%d+0+0" % (w, h))
        # define thread list, center-dict
        self.threads = {}
        self.diameters = {} # width ('w'); height ('h')
        # number over which the average is calcualted {calibrate / 2, measure}
        self.cmap = plt.get_cmap('rainbow') 
         
        ############ elements of the LEFT frame #############
        left_width = int(w * 0.04)
        leftFrame = tk.Frame(self.root, width=left_width, height = h)  
        leftFrame.grid(row=0, column=0, padx=(1,1), pady=(1,1))     
        
        # label for left frame
        tk.Label(leftFrame, text="Beam Profiler pd1").grid(row=0, column=0, padx=(1,1), pady=1)
         
        ######## button/widget frame #########                  
        self.B_run_stop = tk.Button(leftFrame, text="Run", font=(12), bg="lawn green", width=12, height=2, command=lambda:self.startThread("run_stop"))
        self.B_run_stop.grid(row=0, column=0, padx=(1,1), pady=(1,1))
        
        self.B_live = tk.Button(leftFrame, text="Live & Measure", font=(12), bg="cyan", width=12, height=2, command=lambda:self.startThread("live"))
        self.B_live.grid(row=1, column=0, padx=(1,1), pady=(1,1))
        
        self.B_calibrate = tk.Button(leftFrame, text="Calibration", font=(12), bg="yellow", width=12, height=2, command=lambda:self.startThread("calibrate"))
        self.B_calibrate.grid(row=2, column=0, padx=(1,1), pady=(1,1))        
        
        self.B_measure = tk.Button(leftFrame, text="Measure (1/e\u00b2)", font=(12), bg="red", width=12, height=2, state=tk.DISABLED, command=lambda:self.startThread("measure"))
        self.B_measure.grid(row=3, column=0, padx=(1,1), pady=(1,1))
            
        tk.Label(leftFrame, text="Width[µm] ; Height[µm]").grid(row=4, column=0, padx=(1,1), pady=(1,1))
        
        self.E_d = tk.Entry(leftFrame, bd=5, width=17)
        self.E_d.grid(row=5, column=0, padx=(1,1), pady=(1,1))
        
        B_exit = tk.Button(leftFrame, text="Exit", font=(12), bg="mediumpurple", width=12, height=2, command=self.exit)
        B_exit.grid(row=6, column=0, padx=(1,1), pady=(1,1)) 

        ############ elements of the RIGHT frame ############
        rightFrame = tk.Frame(self.root, width=w-left_width, height = h)
        rightFrame.grid(row=0, column=1, padx=(1,1), pady=(1,1))
        
        ############ init camera ############
        self.camera = pylon.InstantCamera(pylon.TlFactory.GetInstance().CreateFirstDevice())  
        # Print the model name of the camera.
        print("Using device ", self.camera.GetDeviceInfo().GetModelName())
        self.camera.MaxNumBuffer = 20
        # init background value
        self.background = []
 
        ######## assign (zero) image #########    
        self.shape = (w-left_width-132, h-60)    # aligned height, width # caution: opencv
        self.img = np.zeros((self.shape[1], self.shape[0]))              
        
        imageEx = ImageTk.PhotoImage(image=Image.fromarray(self.img))        
        self.IMG = tk.Label(rightFrame, image=imageEx)
        self.IMG.grid(row=0, column=0, padx=(1,1), pady=(1,1))
                        
        self.mystr = ""

        ### update GUI ###
        self.root.mainloop() 

    
    def startThread(self, dist):
        print('selected button: ', dist)
        for k, v in self.threads.items():
            try:
                v.join(2)
            except:
                continue
        if self.camera.IsGrabbing():
            self.camera.StopGrabbing()
                             
        if dist == 'run_stop':            
            if self.B_run_stop.cget('text') == 'Run':
                self.B_run_stop.config(text='Stop')
                self.B_run_stop.config(bg='red')
                self.threads['run'] = threading.Thread(target=self.run)
                self.threads['run'].deamon = 1
                self.threads['run'].start()
            elif self.B_run_stop.cget('text') == 'Stop':
                self.B_run_stop.config(text='Run')
                self.B_run_stop.config(bg='lawn green')
                self.stop()
            else:
                print('invalid value: startThread-Run-Stop')
        elif dist == 'calibrate':
            messagebox.showinfo('Info', 'Please specify number of accumulations.')
            # ask for number of measurements
            self.N = utils.createUI(self.root, keyboard=True)
            print('Number of selected accumulations:', self.N)            
            self.threads['calibrate'] = threading.Thread(target=self.calibrate)
            self.threads['calibrate'].deamon = 1
            self.threads['calibrate'].start()
        elif dist == 'measure':
            # ask for number of measurements
            self.threads['measure'] = threading.Thread(target=self.measure)
            self.threads['measure'].deamon = 1
            self.threads['measure'].start()
        elif dist == 'live':
            self.threads['live'] = threading.Thread(target=self.live)
            self.threads['live'].deamon = 1
            self.threads['live'].start()
        else:
            print('no valid assignment')
                
    def exit(self):
        for k, v in self.threads.items():
            try:
                v.join(2)
            except:
                continue
        self.threads.clear()
        # if self.camera.IsGrabbing():
        #     self.camera.StopGrabbing()
        self.root.destroy()
        
    def run(self):
        # Grabing Continusely (video) with minimal delay
        self.camera.StartGrabbing(pylon.GrabStrategy_LatestImageOnly) 
        
        while self.camera.IsGrabbing():          
            grabResult = self.camera.RetrieveResult(5000, pylon.TimeoutHandling_ThrowException)
            
            # if thread stopped, exception occur    
            try:
                if grabResult.GrabSucceeded():
                    # grab image without conversion
                    self.img = grabResult.Array
                    self.img = utils.drawLines(self.img)
                                        
                    # reduce size accordingly
                    self.img = cv2.resize(self.img, self.shape)
                    
                    # convert image into heatmap, choose colormap: self.cmap
                    self.img = self.cmap(self.img)
                    self.img = np.delete(self.img, 3, 2)
                    #imageEx = ImageTk.PhotoImage(image=Image.fromarray(np.uint8(self.img)))
                    imageEx = ImageTk.PhotoImage(image=Image.fromarray(np.uint8(self.img*255.999))) 
                    # update image and input box
                    self.IMG.config(image=imageEx)
                    self.IMG.image = imageEx
            except:
                print('run-stop: error occur')
                continue
                                               
            grabResult.Release()
    
        # Releasing the resource    
        self.camera.StopGrabbing()
        
    def stop(self):
        try:
            if self.camera.IsGrabbing():
                self.camera.StopGrabbing()
            imageEx = ImageTk.PhotoImage(image=Image.fromarray(self.img))     
            self.IMG.image = imageEx
            self.IMG.config(image=imageEx)
        except:
            return
                        
    def calibrate(self):
        # clear exisiting list
        self.background.clear()
        messagebox.showwarning('Warning', 'Laser off ?!\n\nWait a moment for calibration!')
        # deactivate appropriate buttons, change cursor
        self.root.config(relief=tk.RAISED, cursor="watch")
        self.B_run_stop.configure(state=tk.DISABLED)
        self.B_measure.config(state=tk.DISABLED)
        self.B_calibrate.config(state=tk.DISABLED)
        # Grab specified number of images
        numberOfImagesToGrab = self.N
        self.camera.StartGrabbingMax(numberOfImagesToGrab)
        #self.root.config(cursor="wait")
        
        while self.camera.IsGrabbing():
            grabResult = self.camera.RetrieveResult(5000, pylon.TimeoutHandling_ThrowException)

            if grabResult.GrabSucceeded():
                # grab image without conversion
                img = grabResult.Array 
                # convert image to float with values between [0,1]
                img = (img/np.max(img)).astype(np.float32)
                self.background.append(np.mean(img))
               
            grabResult.Release()
    
        # Releasing the resource, change cursor back
        self.camera.StopGrabbing()
        self.B_measure.config(state="normal")
        self.B_run_stop.configure(state="normal")
        self.B_calibrate.config(state="normal")
        self.root.config(relief=tk.RAISED, cursor="arrow")
        #br = np.around(np.mean(self.background), decimals=4)
        messagebox.showinfo('Info', ' Calibration finished! ') #\nBackground:\n{0}'.format(br))
                            
    def measure(self):
        # deactivate appropriate buttons, change cursor, reset variables
        self.root.config(relief=tk.RAISED, cursor="watch")
        self.diameters.clear()
        # Grabing Continusely (video) with minimal delay
        self.camera.StartGrabbing(pylon.GrabStrategy_LatestImageOnly) 
        c = 0
        while self.camera.IsGrabbing():          
            grabResult = self.camera.RetrieveResult(5000, pylon.TimeoutHandling_ThrowException)
            # if error occur => exception printed
            try: 
                if grabResult.GrabSucceeded():
                    # grab image without conversion
                    self.img = grabResult.Array
                    img_temp = self.img.copy()
                    # fit Gaussian
                    self.img, d_w, d_h = self.fitGaussian(self.img)
                   
                    # save diameters of width (w) and height (h)
                    if len(self.diameters) == 0:
                        self.diameters['w'] = np.array([], np.float32)
                        self.diameters['h'] = np.array([], np.float32)       
                    self.diameters['w'] = np.append(self.diameters['w'], values=d_w)
                    self.diameters['h'] = np.append(self.diameters['h'], values=d_h)
                                       
                    # update image and input box
                    imageEx = ImageTk.PhotoImage(image=Image.fromarray(np.uint8(self.img*255.999))) 
                    #imageEx = ImageTk.PhotoImage(image=Image.fromarray(self.img))              
                    self.IMG.image = imageEx
                    self.IMG.config(image=imageEx)
                    
                    self.E_d.delete(0, tk.END)
                    self.E_d.insert(0, ' {0}\t;   {1}'.format(np.around(d_w, decimals=1), np.around(d_h, decimals=1)))
                    
                    # if self.N reached => finish measuerement and give info to user
                    if c == self.N or c == 200:
                        m_dw = np.around(np.mean(self.diameters['w']), decimals=1)
                        m_dh = np.around(np.mean(self.diameters['h']), decimals=1)
                        
                        # compute standard-deviation above all width and height values 
                        std_w = np.std(self.diameters['std_w'])
                        std_h = np.std(self.diameters['std_h']) 

                        msg = 'Measurement finished!\n\nDiameter after {0} measurements:\n\nWidth:  {1} µm \nHeight: {2} µm' \
                            .format(self.N, np.around(m_dw, decimals=3), np.around(m_dh, decimals=3))
                        messagebox.showinfo('Info', msg)
                        
                        # check if beam-profil shall be saved, version 2: save standard-deviation of width(s) and height(s)
                        MsgBox = tk.messagebox.askyesno ('Save image','Do you want to save beam profile?')
                        if MsgBox == 'yes':
                            utils.saveImage(self.root, img_temp, m_dw, m_dh, std_w, std_h)                
                                
                        # release the resource, change cursor back  
                        grabResult.Release()                        
                        self.camera.StopGrabbing()
                        self.root.config(relief=tk.RAISED, cursor="arrow")
                        return                    
            except:
                print('measure: grab skipped')
                continue
               
            grabResult.Release()
            c += 1
            
    def live(self):
        # Grabing Continusely (video) with minimal delay
        self.camera.StartGrabbing(pylon.GrabStrategy_LatestImageOnly) 
        
        while self.camera.IsGrabbing():          
            grabResult = self.camera.RetrieveResult(5000, pylon.TimeoutHandling_ThrowException)
            # if error occur => exception printed
            try: 
                if grabResult.GrabSucceeded():
                    # grab image without conversion and fit gaussian
                    self.img = grabResult.Array                     
                    self.img, d_w, d_h = self.fitGaussian(self.img)
                    
                    # update image and input box
                    imageEx = ImageTk.PhotoImage(image=Image.fromarray(np.uint8(self.img*255.999))) 
                    self.IMG.image = imageEx
                    self.IMG.config(image=imageEx)
                    
                    self.E_d.delete(0, tk.END)
                    self.E_d.insert(0, ' {0}\t;   {1}'.format(np.around(d_w, decimals=1), np.around(d_h, decimals=1)))
            except:
                print('live: grab skipped')
                continue
               
            grabResult.Release()
                
        # release the resource, change cursor back  
        self.camera.StopGrabbing()
          
    def fitGaussian(self, img):
        # convert image to float with values between [0,1]
        img = (img/np.max(img)).astype(np.float32)           
                
        # subtract background
        if len(self.background) == 0:
            img[img < 0.15] = 0.
        else:
            img = img - np.mean(self.background)
            img[img < 0] = 0.  
                
        # coordinate of cut-off-intensity
        cut_off = np.around(1/np.square(np.exp(1)), decimals=4)    
        
        # find x0, x1
        max_x = np.max(img, axis=0)
        diff_x = np.abs(max_x - cut_off)
        
        # ensure enough values close 0 with some discepancy(1%) are found
        x_pos = np.where( diff_x < np.min(diff_x)+.01 )[0]
        center_x = np.argmax(max_x)
        if len(x_pos) == 0 or len(x_pos) > 300:
            return img, 0.0, 0.0 
                
        x0 = np.max(x_pos[np.where( center_x > x_pos )])
        x1 = np.min(x_pos[np.where( center_x < x_pos )])
        
        # find y0, y1
        max_y = np.max(img, axis=1)
        diff_y = np.abs(max_y - cut_off)
                
        # ensure enough values close 0 with some discepancy(1%) are found
        y_pos = np.where( diff_y < np.min(diff_y)+.01 )[0]
        center_y = np.argmax(max_y)
                
        y0 = np.max(y_pos[np.where( center_y > y_pos )])
        y1 = np.min(y_pos[np.where( center_y < y_pos )])
            
        cx = int(np.mean([x0, x1]))
        cy = int(np.mean([y0, y1]))
        
        # calcualte radius for opencv ellipse
        r_width = int(np.abs(x0 - x1) / 2)
        r_height = int(np.abs(y0 - y1) / 2)         
        
        # draw ellipse with opencv into image
        img = cv2.cvtColor(img, cv2.COLOR_GRAY2RGB)
        cv2.ellipse(img, (cx,cy), (r_width, r_height),360,0,360,color=(255,0,0),thickness=6)
        
        # reduce size accordingly
        img = cv2.resize(img, self.shape)
        
        # return diameter and add chip-size: 2.2µm * 2.2µm
        return img, np.abs(x0 - x1) * 2.2, np.abs(y0 - y1) * 2.2 

      

if __name__ == '__main__':
    app = App()
    # TODO: abstürzen beim speichern des Bildes eventuell durch Thread-Aktivitäten,
    #   mögliche Lösung:
    # self.root.wait_window(app)
    