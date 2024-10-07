"""
Content:    on-screen keyboard and num-pad using tkinter
Author :    Jan-Philipp Praetorius
"""

from tkinter import *
import tkinter as tk


kb = tk.Tk()


buttons = [
'q', 'w', 'e', 'r', 't', 'z', 'u', 'i', 'o', 'p', 'BACK',
'a', 's', 'd', 'f', 'g', 'h', 'j', 'k', 'l','-', 'SHIFT',
'y', 'x', 'c', 'v', 'b', 'n', 'm', ',', '.','_', 'SPACE',
]

def select(value):
	if value == "BACK":
		entry.delete(len(entry.get())-1, tk.END)
	elif value == "SPACE":
		entry.insert(tk.END, ' ')
	else :
		entry.insert(tk.END,value)

def HosoPop():
	varRow = 2
	varColumn = 0

	for button in buttons:
		command = lambda x=button: select(x)
		
		if button == "SPACE" or button == "SHIFT" or button == "BACK":
			tk.Button(kb,text= button,width=6, bg="#3c4987", fg="#ffffff",
				activebackground = "#ffffff", activeforeground="#3c4987", relief='raised', padx=1,
				pady=1, bd=1,command=command).grid(row=varRow,column=varColumn)

		else:
			tk.Button(kb,text= button,width=4, bg="#3c4987", fg="#ffffff",
				activebackground = "#ffffff", activeforeground="#3c4987", relief='raised', padx=1,
				pady=1, bd=1,command=command).grid(row=varRow,column=varColumn)

		varColumn +=1 
		if varColumn > 10 and varRow == 2:
			varColumn = 0
			varRow+=1
		elif varColumn > 10 and varRow == 3:
			varColumn = 0
			varRow+=1
		elif varColumn > 10 and varRow == 4:
			varColumn = 0
			varRow+=1


def main():
	#kb = tk.Tk()
	kb.title("HosoKeys")
	kb.resizable(0,0)
	

	label1 = Label(kb,text='               ').grid(row=0,columnspan=15)

	global entry
	entry = Entry(kb,width=50)
	entry.grid(row=1,columnspan=15)
	# entry.pack()

	entry.bind("<Button-1>", lambda e: HosoPop())

	kb.mainloop()

main()