import os
import sys

def get_resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        if hasattr(sys, '_MEIPASS'):
            return os.path.join(sys._MEIPASS, relative_path)
    except Exception:
        pass
    
   
    base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    return os.path.join(base_path, relative_path)

def get_save_path(filename, folder_name="Cardflow"):
    """ Get absolute path to save data (e.g. database), stored in APPDATA for EXE """
    if hasattr(sys, '_MEIPASS'):
        # If running as EXE, use AppData
        appdata = os.getenv('APPDATA')
        if not appdata:
            # Fallback for non-windows or missing env
            appdata = os.path.expanduser("~")
        save_dir = os.path.join(appdata, folder_name)
    else:
        # In development, keep it in the project folder under 'python_prototype/db'
        save_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "db"))
    
    if not os.path.exists(save_dir):
        try:
            os.makedirs(save_dir)
        except:
            # Fallback to current directory if AppData is not writable
            save_dir = "."
        
    return os.path.join(save_dir, filename)
