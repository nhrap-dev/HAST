try:
    import Tkinter as tk
    from Tkinter import filedialog
except ImportError:
    import tkinter as tk
    from tkinter import filedialog

try:
    import tkinter.ttk
    py3 = False
except ImportError:
    import tkinter.ttk as ttk
    py3 = True

import csv, os, datetime
import xml.etree.ElementTree as ET
# from tkinter import PhotoImage

def popupmsg(msg, comm=None):
    global popup
    popup = tk.Toplevel()
    popup.configure(background="#bde6ff")

    popup.iconbitmap(os.path.abspath('Images/Hu_Symbol.ico'))
    # popup.iconbitmap('../Images/Hu_Symbol.ico')
    popup.wm_title("HAST")
    label = tk.Label(popup, text=msg,background="#bde6ff")
    label.pack(fill="x", pady=10, padx = 20)
    parent = tk.Frame(popup)#.configure(background='#97CFFC')
    parent.configure(background="#bde6ff")
    parent.pack()
    if comm != None:
        B1 = tk.Button(parent, text="Yes", command = comm,background="#bde6ff")
        B1.pack(fill='x', side = 'left', padx=20, pady=10)
        B1.configure(height=1, width=5)
        B2 = tk.Button(parent, text="Cancel", command = popup.destroy,background="#bde6ff")
        B2.pack(fill='x', side = 'left', padx=20)
        B2.configure(height=1, width=5)
        parent.pack(expand=1)
    else:
        B1 = tk.Button(parent, text="Okay", command = popup.destroy,background="#bde6ff")
        B1.pack(fill='x', side = 'left', padx=20, pady=10)
        B1.configure(height=1, width=5)
        parent.pack(expand=1)
    # Gets the requested values of the height and widht.
    windowWidth = popup.winfo_reqwidth()
    windowHeight = popup.winfo_reqheight()
     
    # Gets both half the screen width/height and window width/height
    positionRight = int(popup.winfo_screenwidth()/2 - windowWidth)
    positionDown = int(popup.winfo_screenheight()/2 - windowHeight)
     
    # Positions the window in the center of the page.
    popup.geometry("+{}+{}".format(positionRight, positionDown))
    
    
    #popup.mainloop()
    
    
def browse(rootCSV,rootFields,tree,tag,entryText,inDir,logging,fields,file_types):
    #print('HAST_support.WindfieldBrowse')
    logging.info(str(datetime.datetime.now())+' HAST_support.browse')
    #sys.stdout.flush()
    rootCSV = []
    rootFields = {key:''for key, value in fields.items()}
    #root.WindfieldValid = {}
    
    #print('FILE TYPES',*tuple([('type',item.text) for item in next(base.iter('GeneralSettings')).iter('InputFileTypes')])+("all files","*.*"))
    filename = filedialog.askopenfilename(initialdir = os.path.join(os.getcwd(),tree.find('.//'+inDir).text),title = "Select file",filetypes = file_types)# Gets input csv file from user
    # Gets field names from input csv file and makes a list
    try:
        with open(filename, "r+") as f:
            reader = csv.reader(f)
            rootCSV = next(reader)
            logging.debug(str(datetime.datetime.now())+' File Open: '+filename+' File Fields: '+ str(rootCSV))
            rootCSV = list(map(lambda x: x.upper(), rootCSV))
    except Exception as e:
        logging.debug(str(datetime.datetime.now())+' Failed to open input file. Message: '+str(e))
        return
    
    #Save the input file name and path to the Settings.xml - InputFileName (under this node)
    tree.getroot().find('.//'+tag).text = filename
    tree.write('settings.xml')
    entryText.set(filename)
    #w.WindfieldLabel.config(text = filename)
    print(filename,rootFields)
    return [rootFields, rootCSV]